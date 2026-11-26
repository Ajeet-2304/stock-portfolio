from django.db.models import Avg, F, Window
from django.db.models.functions import RowRange

prices = DailyPrice.objects.filter(
    instrument_id=instrument_id
).annotate(
    moving_average=Window(
        expression=Avg("close"),
        order_by="trading_date",
        frame=RowRange(start=-19, end=0)
    )
)