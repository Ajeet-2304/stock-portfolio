from django.db import models

# Create your models here.
from django.db import models
from django.db.models import Q, F

class Exchange(models.Model):
    code = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=120)
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    currency = models.CharField(max_length=3, default="INR")
    def __str__(self): return self.code

class Instrument(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.PROTECT, related_name="instruments")
    ticker = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    isin = models.CharField(max_length=12, unique=True)
    sector = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["exchange", "ticker"], name="uq_exchange_ticker")]
        indexes = [models.Index(fields=["exchange", "ticker"])]
    def __str__(self): return f"{self.exchange.code}:{self.ticker}"

class DailyPrice(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT, related_name="prices")
    trading_date = models.DateField()
    open = models.DecimalField(max_digits=20, decimal_places=6)
    high = models.DecimalField(max_digits=20, decimal_places=6)
    low = models.DecimalField(max_digits=20, decimal_places=6)
    close = models.DecimalField(max_digits=20, decimal_places=6)
    volume = models.DecimalField(max_digits=24, decimal_places=4, default=0)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["instrument", "trading_date"], name="uq_instrument_price_date"),
            models.CheckConstraint(condition=Q(open__gt=0) & Q(high__gt=0) & Q(low__gt=0) & Q(close__gt=0), name="price_positive"),
            models.CheckConstraint(condition=Q(low__lte=F("open")) & Q(low__lte=F("close")) & Q(high__gte=F("open")) & Q(high__gte=F("close")), name="ohlc_valid"),
            models.CheckConstraint(condition=Q(volume__gte=0), name="volume_nonnegative"),
        ]
        indexes = [models.Index(fields=["instrument", "trading_date"]), models.Index(fields=["trading_date", "instrument"])]

class CorporateAction(models.Model):
    class Type(models.TextChoices):
        SPLIT = "SPLIT", "Stock split"
        DIVIDEND = "DIVIDEND", "Cash dividend"
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT, related_name="corporate_actions")
    action_type = models.CharField(max_length=12, choices=Type.choices)
    ex_date = models.DateField()
    numerator = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    denominator = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    dividend_per_share = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["instrument", "action_type", "ex_date"], name="uq_corporate_action_date")]

class ExchangeHoliday(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.PROTECT, related_name="holidays")
    date = models.DateField()
    description = models.CharField(max_length=160, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["exchange", "date"], name="uq_exchange_holiday")]
