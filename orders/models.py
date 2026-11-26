from django.db import models

# Create your models here.
from django.db import models
from django.db.models import Q
from portfolios.models import Portfolio
from market_data.models import Instrument

class Order(models.Model):
    class Side(models.TextChoices): BUY="BUY","Buy"; SELL="SELL","Sell"
    class Type(models.TextChoices): MARKET="MARKET","Market"; LIMIT="LIMIT","Limit"
    class Status(models.TextChoices):
        PENDING="PENDING","Pending"; PARTIALLY_FILLED="PARTIALLY_FILLED","Partially filled"
        FILLED="FILLED","Filled"; CANCELLED="CANCELLED","Cancelled"; REJECTED="REJECTED","Rejected"
    portfolio=models.ForeignKey(Portfolio,on_delete=models.PROTECT,related_name="orders")
    instrument=models.ForeignKey(Instrument,on_delete=models.PROTECT,related_name="orders")
    side=models.CharField(max_length=4,choices=Side.choices)
    order_type=models.CharField(max_length=6,choices=Type.choices)
    quantity=models.DecimalField(max_digits=20,decimal_places=4)
    limit_price=models.DecimalField(max_digits=20,decimal_places=6,null=True,blank=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING)
    reserved_cash=models.DecimalField(max_digits=22,decimal_places=4,default=0)
    reserved_quantity=models.DecimalField(max_digits=20,decimal_places=4,default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=Q(quantity__gt=0),name="order_quantity_positive"),
            models.CheckConstraint(condition=(Q(order_type="LIMIT",limit_price__isnull=False) | Q(order_type="MARKET",limit_price__isnull=True)),name="order_limit_price_rule"),
            models.CheckConstraint(condition=Q(limit_price__gt=0) | Q(limit_price__isnull=True),name="order_limit_price_positive"),
        ]
        indexes=[models.Index(fields=["portfolio","status"])]

class Execution(models.Model):
    order=models.ForeignKey(Order,on_delete=models.PROTECT,related_name="executions")
    external_execution_id=models.CharField(max_length=120,unique=True)
    quantity=models.DecimalField(max_digits=20,decimal_places=4)
    price=models.DecimalField(max_digits=20,decimal_places=6)
    executed_at=models.DateTimeField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=Q(quantity__gt=0),name="execution_qty_positive"),
            models.CheckConstraint(condition=Q(price__gt=0),name="execution_price_positive"),
        ]
        indexes=[models.Index(fields=["order","executed_at"])]

class TaxLot(models.Model):
    portfolio=models.ForeignKey(Portfolio,on_delete=models.PROTECT,related_name="tax_lots")
    instrument=models.ForeignKey(Instrument,on_delete=models.PROTECT,related_name="tax_lots")
    buy_execution=models.OneToOneField(Execution,on_delete=models.PROTECT,related_name="created_lot")
    acquired_at=models.DateTimeField()
    original_quantity=models.DecimalField(max_digits=20,decimal_places=4)
    remaining_quantity=models.DecimalField(max_digits=20,decimal_places=4)
    unit_cost=models.DecimalField(max_digits=20,decimal_places=6)
    class Meta:
        constraints=[
            models.CheckConstraint(condition=Q(original_quantity__gt=0),name="lot_original_positive"),
            models.CheckConstraint(condition=Q(remaining_quantity__gte=0),name="lot_remaining_nonnegative"),
            models.CheckConstraint(condition=Q(unit_cost__gt=0),name="lot_cost_positive"),
        ]
        indexes=[models.Index(fields=["portfolio","instrument","acquired_at","id"])]

class LotConsumption(models.Model):
    lot=models.ForeignKey(TaxLot,on_delete=models.PROTECT,related_name="consumptions")
    sell_execution=models.ForeignKey(Execution,on_delete=models.PROTECT,related_name="lot_consumptions")
    quantity=models.DecimalField(max_digits=20,decimal_places=4)
    cost_basis=models.DecimalField(max_digits=22,decimal_places=4)
    proceeds=models.DecimalField(max_digits=22,decimal_places=4)
    realized_pnl=models.DecimalField(max_digits=22,decimal_places=4)
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(quantity__gt=0),name="consumption_qty_positive")]
        indexes=[models.Index(fields=["sell_execution"]),models.Index(fields=["sell_execution","lot"])]
