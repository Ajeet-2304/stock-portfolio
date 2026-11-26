from decimal import Decimal

from django.db.models import Sum, Window, Avg, RowRange, F
from django.shortcuts import render
from django.utils.dateparse import parse_date

# Create your views here.
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.views import APIView

from market_data.models import DailyPrice, Instrument
from market_data.views import owned_portfolio
from orders.models import TaxLot, LotConsumption
from .models import Portfolio
from .serializers import PortfolioSerializer
from .services import cash_balance, post_cash_entry

class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class=PortfolioSerializer
    permission_classes=[permissions.IsAuthenticated]
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        p=self.get_object()
        return Response({"cash_balance": str(cash_balance(p)), "currency": p.base_currency})
    @action(detail=True, methods=["post"])
    def deposit(self, request, pk=None):
        p=self.get_object()
        try: entry=post_cash_entry(p.id, "DEPOSIT", request.data["amount"], "Cash deposit")
        except KeyError: raise ValidationError({"amount":"This field is required."})
        return Response({"id":entry.id,"balance":str(cash_balance(p))}, status=201)
    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        p=self.get_object()
        try: entry=post_cash_entry(p.id, "WITHDRAWAL", -abs(float(request.data["amount"])), "Cash withdrawal")
        except KeyError: raise ValidationError({"amount":"This field is required."})
        return Response({"id":entry.id,"balance":str(cash_balance(p))}, status=201)



class HoldingsView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,portfolio_id):
        p=owned_portfolio(request.user,portfolio_id)
        lots=TaxLot.objects.filter(portfolio=p,remaining_quantity__gt=0).values("instrument_id","instrument__ticker","instrument__name").annotate(
            quantity=Sum("remaining_quantity"),cost_basis=Sum(F("remaining_quantity")*F("unit_cost")))
        result=[]
        for row in lots:
            latest=DailyPrice.objects.filter(instrument_id=row["instrument_id"]).order_by("-trading_date").first()
            price=latest.close if latest else Decimal("0")
            qty=row["quantity"]; basis=row["cost_basis"]; mv=qty*price
            result.append({"instrument":row["instrument__ticker"],"name":row["instrument__name"],
                "quantity":str(qty),"average_cost":str(basis/qty if qty else 0),"latest_price":str(price),
                "market_value":str(mv),"unrealized_pnl":str(mv-basis)})
        total=sum((Decimal(x["market_value"]) for x in result),Decimal("0"))
        for item in result:
            item["portfolio_percentage"]=str(Decimal(item["market_value"])/total*100 if total else 0)
        return Response(result)

def cash_ledger_amount(portfolio,as_of):
    from portfolios.models import CashLedgerEntry
    return CashLedgerEntry.objects.filter(portfolio=portfolio,created_at__date__lte=as_of).aggregate(v=Sum("amount"))["v"] or Decimal("0")


class PortfolioValueView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,portfolio_id):
        p=owned_portfolio(request.user,portfolio_id)
        as_of=parse_date(request.query_params.get("as_of",""))
        if not as_of: raise ValidationError({"as_of":"Use YYYY-MM-DD."})
        # Historical lot reconstruction is based on BUY lots and SELL lot consumption dated by execution.
        lots=TaxLot.objects.filter(portfolio=p,acquired_at__date__lte=as_of)
        total=Decimal("0")
        for lot in lots:
            consumed=lot.consumptions.filter(sell_execution__executed_at__date__lte=as_of).aggregate(v=Sum("quantity"))["v"] or Decimal("0")
            qty=lot.original_quantity-consumed
            if qty<=0: continue
            price=DailyPrice.objects.filter(instrument=lot.instrument,trading_date__lte=as_of).order_by("-trading_date").first()
            if price: total+=qty*price.close
        cash=cash_ledger_amount(p,as_of)
        return Response({"as_of":str(as_of),"market_value":str(total),"cash_balance":str(cash),"total_value":str(total+cash)})

