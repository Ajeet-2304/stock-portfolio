from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from market_data.models import CorporateAction
from portfolios.models import CashLedgerEntry
from orders.models import TaxLot

class Command(BaseCommand):
    help = "Apply unprocessed corporate actions whose ex_date is on or before today."
    def handle(self,*args,**opts):
        actions=CorporateAction.objects.filter(processed_at__isnull=True,ex_date__lte=timezone.localdate()).order_by("ex_date","id")
        for action in actions:
            with transaction.atomic():
                action=CorporateAction.objects.select_for_update().get(pk=action.pk)
                if action.processed_at: continue
                if action.action_type=="SPLIT":
                    if not action.numerator or not action.denominator or action.denominator==0:
                        self.stderr.write(f"Invalid split action {action.pk}"); continue
                    factor=action.numerator/action.denominator
                    lots=TaxLot.objects.select_for_update().filter(instrument=action.instrument,remaining_quantity__gt=0)
                    for lot in lots:
                        lot.original_quantity*=factor
                        lot.remaining_quantity*=factor
                        lot.unit_cost/=factor
                        lot.save(update_fields=["original_quantity","remaining_quantity","unit_cost"])
                elif action.action_type=="DIVIDEND":
                    if action.dividend_per_share is None: continue
                    # Eligibility uses open lots on ex-date; production systems should define market cut-off/timezone policy.
                    lots=TaxLot.objects.filter(instrument=action.instrument,acquired_at__date__lt=action.ex_date,remaining_quantity__gt=0)
                    from django.db.models import Sum
                    holdings={}
                    for row in lots.values("portfolio_id").annotate(q=Sum("remaining_quantity")):
                        holdings[row["portfolio_id"]]=row["q"]
                    for pid,qty in holdings.items():
                        CashLedgerEntry.objects.create(portfolio_id=pid,entry_type="DIVIDEND",
                            amount=qty*action.dividend_per_share,reference=f"CA-{action.pk}",
                            description=f"Dividend {action.instrument.ticker}")
                action.processed_at=timezone.now()
                action.save(update_fields=["processed_at"])
                self.stdout.write(f"Applied corporate action {action.pk}")
