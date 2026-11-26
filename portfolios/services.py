from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from .models import Portfolio, CashLedgerEntry

def cash_balance(portfolio):
    return portfolio.ledger_entries.aggregate(total=Sum("amount"))["total"] or Decimal("0")

@transaction.atomic
def post_cash_entry(portfolio_id, entry_type, amount, description="", reference=""):
    portfolio = Portfolio.objects.select_for_update().get(pk=portfolio_id)
    amount = Decimal(amount)
    if entry_type == CashLedgerEntry.EntryType.DEPOSIT and amount <= 0:
        raise ValidationError("Deposit amount must be positive.")
    if entry_type == CashLedgerEntry.EntryType.WITHDRAWAL:
        if amount >= 0: raise ValidationError("Withdrawal amount must be negative.")
        if cash_balance(portfolio) + amount < 0:
            raise ValidationError("Insufficient cash.")
    return CashLedgerEntry.objects.create(portfolio=portfolio, entry_type=entry_type,
        amount=amount, description=description, reference=reference)
