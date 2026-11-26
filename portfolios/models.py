# from django.conf import settings
# from django.db import models
#
#
# class Portfolio(models.Model):
#
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.PROTECT,
#         related_name="portfolios"
#     )
# 
#     name = models.CharField(max_length=100)
#
#     base_currency = models.CharField(
#         max_length=3,
#         default="INR"
#     )
#
#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )
#
#     updated_at = models.DateTimeField(
#         auto_now=True
#     )
#
#     def __str__(self):
#         return f"{self.name} - {self.user.username}"


from django.conf import settings
from django.db import models
from django.db.models import Q

class Portfolio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="portfolios")
    name = models.CharField(max_length=100)
    base_currency = models.CharField(max_length=3, default="INR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]
    def __str__(self): return f"{self.name} ({self.user})"

class CashLedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        DEPOSIT="DEPOSIT","Deposit"
        WITHDRAWAL="WITHDRAWAL","Withdrawal"
        BUY="BUY","Buy"
        SELL="SELL","Sell"
        DIVIDEND="DIVIDEND","Dividend"
        FEE="FEE","Fee"
        REVERSAL="REVERSAL","Reversal"
    portfolio = models.ForeignKey(Portfolio, on_delete=models.PROTECT, related_name="ledger_entries")
    entry_type = models.CharField(max_length=12, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=22, decimal_places=4)
    reference = models.CharField(max_length=120, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta:
        indexes = [models.Index(fields=["portfolio", "created_at"])]
        constraints = [models.CheckConstraint(condition=~Q(amount=0), name="ledger_amount_nonzero")]
