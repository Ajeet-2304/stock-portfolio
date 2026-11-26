from decimal import Decimal
from django.db import transaction, IntegrityError
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from portfolios.models import CashLedgerEntry
from portfolios.services import cash_balance
from .models import Order, Execution, TaxLot, LotConsumption

def _filled(order):
    return order.executions.aggregate(v=Sum("quantity"))["v"] or Decimal("0")

def available_shares(portfolio, instrument):
    return TaxLot.objects.filter(portfolio=portfolio,instrument=instrument).aggregate(v=Sum("remaining_quantity"))["v"] or Decimal("0")

@transaction.atomic
def place_order(*, portfolio, instrument, side, order_type, quantity, limit_price=None):
    portfolio=type(portfolio).objects.select_for_update().get(pk=portfolio.pk)
    quantity=Decimal(quantity)
    if quantity <= 0: raise ValidationError("Quantity must be positive.")
    if order_type == "LIMIT" and (limit_price is None or Decimal(limit_price)<=0):
        raise ValidationError("LIMIT order requires a positive limit_price.")
    if order_type == "MARKET" and limit_price is not None:
        raise ValidationError("MARKET order must not have limit_price.")
    if side == "BUY":
        if order_type == "LIMIT":
            reserve=quantity*Decimal(limit_price)
        else:
            latest=instrument.prices.order_by("-trading_date").first()
            if not latest: raise ValidationError("Cannot reserve market order without a reference price.")
            reserve=quantity*latest.close*Decimal("1.10")
        already=Order.objects.filter(portfolio=portfolio,side="BUY",status__in=["PENDING","PARTIALLY_FILLED"]).aggregate(v=Sum("reserved_cash"))["v"] or Decimal("0")
        if cash_balance(portfolio)-already < reserve: raise ValidationError("Insufficient unreserved cash.")
        reserved_cash=reserve
        reserved_qty=Decimal("0")
    else:
        already=Order.objects.filter(portfolio=portfolio,instrument=instrument,side="SELL",status__in=["PENDING","PARTIALLY_FILLED"]).aggregate(v=Sum("reserved_quantity"))["v"] or Decimal("0")
        if available_shares(portfolio,instrument)-already < quantity: raise ValidationError("Insufficient unreserved shares.")
        reserved_cash=Decimal("0")
        reserved_qty=quantity
    return Order.objects.create(portfolio=portfolio,instrument=instrument,side=side,order_type=order_type,
        quantity=quantity,limit_price=limit_price,reserved_cash=reserved_cash,reserved_quantity=reserved_qty)

@transaction.atomic
def record_execution(*, order_id, external_execution_id, quantity, price, executed_at=None):
    # Lock portfolio first: all order/fill flows for a portfolio serialize on this row.
    order0=Order.objects.select_related("portfolio").get(pk=order_id)
    portfolio=type(order0.portfolio).objects.select_for_update().get(pk=order0.portfolio_id)
    order=Order.objects.select_for_update().get(pk=order_id,portfolio=portfolio)
    if Execution.objects.filter(external_execution_id=external_execution_id).exists():
        return Execution.objects.get(external_execution_id=external_execution_id), False
    if order.status not in ["PENDING","PARTIALLY_FILLED"]: raise ValidationError("Order is not executable.")
    qty, price=Decimal(quantity), Decimal(price)
    if qty<=0 or price<=0: raise ValidationError("Execution quantity and price must be positive.")
    if _filled(order)+qty > order.quantity: raise ValidationError("Execution exceeds remaining order quantity.")
    if order.order_type=="LIMIT":
        if order.side=="BUY" and price>order.limit_price: raise ValidationError("BUY fill exceeds limit price.")
        if order.side=="SELL" and price<order.limit_price: raise ValidationError("SELL fill is below limit price.")
    execution=Execution.objects.create(order=order,external_execution_id=external_execution_id,
        quantity=qty,price=price,executed_at=executed_at or timezone.now())
    gross=qty*price
    if order.side=="BUY":
        CashLedgerEntry.objects.create(portfolio=portfolio,entry_type="BUY",amount=-gross,
            reference=external_execution_id,description="Stock purchase")
        TaxLot.objects.create(portfolio=portfolio,instrument=order.instrument,buy_execution=execution,
            acquired_at=execution.executed_at,original_quantity=qty,remaining_quantity=qty,unit_cost=price)
        order.reserved_cash=max(Decimal("0"),order.reserved_cash-gross)
    else:
        remaining=qty
        lots=TaxLot.objects.select_for_update().filter(portfolio=portfolio,instrument=order.instrument,remaining_quantity__gt=0).order_by("acquired_at","id")
        for lot in lots:
            take=min(remaining,lot.remaining_quantity)
            if take:
                basis=take*lot.unit_cost
                proceeds=take*price
                LotConsumption.objects.create(lot=lot,sell_execution=execution,quantity=take,
                    cost_basis=basis,proceeds=proceeds,realized_pnl=proceeds-basis)
                lot.remaining_quantity-=take
                lot.save(update_fields=["remaining_quantity"])
                remaining-=take
            if remaining==0: break
        if remaining>0: raise ValidationError("Insufficient shares at execution time.")
        CashLedgerEntry.objects.create(portfolio=portfolio,entry_type="SELL",amount=gross,
            reference=external_execution_id,description="Stock sale")
        order.reserved_quantity=max(Decimal("0"),order.reserved_quantity-qty)
    total=_filled(order)
    order.status="FILLED" if total==order.quantity else "PARTIALLY_FILLED"
    if order.status=="FILLED":
        order.reserved_cash=Decimal("0")
        order.reserved_quantity=Decimal("0")
    order.save(update_fields=["status","reserved_cash","reserved_quantity"])
    return execution, True

@transaction.atomic
def cancel_order(order_id, portfolio):
    p=type(portfolio).objects.select_for_update().get(pk=portfolio.pk)
    order=Order.objects.select_for_update().get(pk=order_id,portfolio=p)
    if order.status not in ["PENDING","PARTIALLY_FILLED"]: raise ValidationError("Order cannot be cancelled.")
    order.status="CANCELLED"; order.reserved_cash=0; order.reserved_quantity=0
    order.save(update_fields=["status","reserved_cash","reserved_quantity"])
    return order
