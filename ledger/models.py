from django.db import models
from portfolios.models import Portfolio

class CashLedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        DEPOSIT = "DEPOSIT"
        WITHDRAWAL = "WITHDRAWAL"
        BUY = "BUY"
        SELL = "SELL"
        DIVIDEND = "DIVIDEND"
        FEE = "FEE"

    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.PROTECT
    )
    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=4
    )
    reference_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)