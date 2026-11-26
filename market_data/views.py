from decimal import Decimal

from django.db.models import Sum, Window, Avg, F, RowRange
from django.shortcuts import render
from django.utils.dateparse import parse_date

# Create your views here.
from rest_framework import viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import LotConsumption
from portfolios.models import Portfolio
from .models import Exchange, Instrument, DailyPrice, CorporateAction, ExchangeHoliday
from .serializers import ExchangeSerializer, InstrumentSerializer, DailyPriceSerializer, CorporateActionSerializer, ExchangeHolidaySerializer

class ReadOnlyOrAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            from rest_framework.permissions import IsAdminUser
            return [IsAdminUser()]
        return super().get_permissions()

class ExchangeViewSet(ReadOnlyOrAdminViewSet):
    queryset=Exchange.objects.all()
    serializer_class=ExchangeSerializer
class InstrumentViewSet(ReadOnlyOrAdminViewSet):
    queryset=Instrument.objects.select_related("exchange").all()
    serializer_class=InstrumentSerializer
class DailyPriceViewSet(ReadOnlyOrAdminViewSet):
    queryset=DailyPrice.objects.select_related("instrument").all()
    serializer_class=DailyPriceSerializer
class CorporateActionViewSet(ReadOnlyOrAdminViewSet):
    queryset=CorporateAction.objects.select_related("instrument").all()
    serializer_class=CorporateActionSerializer
class ExchangeHolidayViewSet(ReadOnlyOrAdminViewSet):
    queryset=ExchangeHoliday.objects.select_related("exchange").all()
    serializer_class=ExchangeHolidaySerializer



def owned_portfolio(user, pk):
    try: return Portfolio.objects.get(pk=pk,user=user)
    except Portfolio.DoesNotExist: raise NotFound("Portfolio not found.")

class RealizedPnLView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,portfolio_id):
        p=owned_portfolio(request.user,portfolio_id)
        start=parse_date(request.query_params.get("start_date","")); end=parse_date(request.query_params.get("end_date",""))
        if not start or not end or start>end: raise ValidationError("Provide valid start_date and end_date.")
        rows=LotConsumption.objects.filter(lot__portfolio=p,sell_execution__executed_at__date__gte=start,sell_execution__executed_at__date__lte=end).values(
            "lot__instrument__ticker").annotate(realized_pnl=Sum("realized_pnl"),quantity=Sum("quantity"))
        return Response(list(rows))

class TopMoversView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,exchange_id):
        start=parse_date(request.query_params.get("start_date","")); end=parse_date(request.query_params.get("end_date",""))
        if not start or not end: raise ValidationError("Provide start_date and end_date.")
        instruments=Instrument.objects.filter(exchange_id=exchange_id,orders__executions__executed_at__date__gte=start,
            orders__executions__executed_at__date__lte=end).distinct()
        rows=[]
        for instrument in instruments:
            a=DailyPrice.objects.filter(instrument=instrument,trading_date__lte=start).order_by("-trading_date").first()
            b=DailyPrice.objects.filter(instrument=instrument,trading_date__lte=end).order_by("-trading_date").first()
            if a and b and a.close:
                rows.append({"ticker":instrument.ticker,"start_close":str(a.close),"end_close":str(b.close),
                    "change_percent":str((b.close-a.close)/a.close*100)})
        rows.sort(key=lambda x:Decimal(x["change_percent"]),reverse=True)
        return Response(rows[:10])

class MovingAverageView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,instrument_id):
        qs=DailyPrice.objects.filter(instrument_id=instrument_id).annotate(
            moving_average=Window(expression=Avg("close"),order_by=F("trading_date").asc(),frame=RowRange(start=-19,end=0))
        ).order_by("trading_date")
        return Response([{"date":str(x.trading_date),"close":str(x.close),"moving_average":str(x.moving_average)} for x in qs])
