import csv
from decimal import Decimal, InvalidOperation
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from market_data.models import Instrument, DailyPrice

class Command(BaseCommand):
    help = "Bulk load daily OHLCV CSV data. Expected columns: ticker,date,open,high,low,close,volume"
    def add_arguments(self, parser):
        parser.add_argument("csv_path")
        parser.add_argument("--batch-size",type=int,default=5000)
    def handle(self,*args,**opts):
        path=opts["csv_path"]; batch_size=opts["batch_size"]
        instruments={f"{x.exchange.code}:{x.ticker}":x for x in Instrument.objects.select_related("exchange").all()}
        instruments.update({x.ticker:x for x in Instrument.objects.select_related("exchange").all()})
        batch=[]; errors=[]; processed=0
        with open(path,newline="",encoding="utf-8-sig") as f:
            reader=csv.DictReader(f)
            for line,row in enumerate(reader,start=2):
                try:
                    instrument=instruments.get(row["ticker"].strip())
                    if not instrument: raise ValueError("Unknown ticker")
                    d=date.fromisoformat(row["date"])
                    vals={k:Decimal(row[k]) for k in ("open","high","low","close","volume")}
                    if min(vals[k] for k in ("open","high","low","close"))<=0: raise ValueError("Prices must be positive")
                    if vals["low"]>min(vals["open"],vals["close"]) or vals["high"]<max(vals["open"],vals["close"]): raise ValueError("Invalid OHLC range")
                    if vals["volume"]<0: raise ValueError("Negative volume")
                    batch.append(DailyPrice(instrument=instrument,trading_date=d,**vals))
                except Exception as exc:
                    errors.append({"line":line,"reason":str(exc),"row":row})
                if len(batch)>=batch_size:
                    self.upsert(batch); processed+=len(batch); batch=[]
        if batch: self.upsert(batch); processed+=len(batch)
        if errors:
            out=path+".errors.csv"
            with open(out,"w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=["line","reason","row"]); w.writeheader(); w.writerows(errors)
            self.stdout.write(self.style.WARNING(f"{len(errors)} rejected rows: {out}"))
        self.stdout.write(self.style.SUCCESS(f"Loaded/upserted {processed} rows; rejected {len(errors)}"))
    @staticmethod
    def upsert(batch):
        DailyPrice.objects.bulk_create(batch,batch_size=5000,update_conflicts=True,
            unique_fields=["instrument","trading_date"],update_fields=["open","high","low","close","volume"])
