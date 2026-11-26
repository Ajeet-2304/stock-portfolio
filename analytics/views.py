# from django.shortcuts import render
#
# # Create your views here.
# from decimal import Decimal
# from django.db.models import Sum, Avg, F, Window
# from django.db.models.functions import RowRange
# from django.utils.dateparse import parse_date
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.exceptions import NotFound, ValidationError
# from portfolios.models import Portfolio
# from portfolios.services import cash_balance
# from trading.models import TaxLot, LotConsumption, Order
# from market_data.models import DailyPrice, Instrument, Exchange
#
# def owned_portfolio(user, pk):
#     try: return Portfolio.objects.get(pk=pk,user=user)
#     except Portfolio.DoesNotExist: raise NotFound("Portfolio not found.")
#
# class HoldingsView(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request,portfolio_id):
#         p=owned_portfolio(request.user,portfolio_id)
#         lots=TaxLot.objects.filter(portfolio=p,remaining_quantity__gt=0).values("instrument_id","instrument__ticker","instrument__name").annotate(
#             quantity=Sum("remaining_quantity"),cost_basis=Sum(F("remaining_quantity")*F("unit_cost")))
#         result=[]
#         for row in lots:
#             latest=DailyPrice.objects.filter(instrument_id=row["instrument_id"]).order_by("-trading_date").first()
#             price=latest.close if latest else Decimal("0")
#             qty=row["quantity"]; basis=row["cost_basis"]; mv=qty*price
#             result.append({"instrument":row["instrument__ticker"],"name":row["instrument__name"],
#                 "quantity":str(qty),"average_cost":str(basis/qty if qty else 0),"latest_price":str(price),
#                 "market_value":str(mv),"unrealized_pnl":str(mv-basis)})
#         total=sum((Decimal(x["market_value"]) for x in result),Decimal("0"))
#         for item in result:
#             item["portfolio_percentage"]=str(Decimal(item["market_value"])/total*100 if total else 0)
#         return Response(result)
#
# class PortfolioValueView(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request,portfolio_id):
#         p=owned_portfolio(request.user,portfolio_id)
#         as_of=parse_date(request.query_params.get("as_of",""))
#         if not as_of: raise ValidationError({"as_of":"Use YYYY-MM-DD."})
#         # Historical lot reconstruction is based on BUY lots and SELL lot consumption dated by execution.
#         lots=TaxLot.objects.filter(portfolio=p,acquired_at__date__lte=as_of)
#         total=Decimal("0")
#         for lot in lots:
#             consumed=lot.consumptions.filter(sell_execution__executed_at__date__lte=as_of).aggregate(v=Sum("quantity"))["v"] or Decimal("0")
#             qty=lot.original_quantity-consumed
#             if qty<=0: continue
#             price=DailyPrice.objects.filter(instrument=lot.instrument,trading_date__lte=as_of).order_by("-trading_date").first()
#             if price: total+=qty*price.close
#         cash=CashLedgerAmount(p,as_of)
#         return Response({"as_of":str(as_of),"market_value":str(total),"cash_balance":str(cash),"total_value":str(total+cash)})
#
# def CashLedgerAmount(portfolio,as_of):
#     from portfolios.models import CashLedgerEntry
#     return CashLedgerEntry.objects.filter(portfolio=portfolio,created_at__date__lte=as_of).aggregate(v=Sum("amount"))["v"] or Decimal("0")
#
# class RealizedPnLView(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request,portfolio_id):
#         p=owned_portfolio(request.user,portfolio_id)
#         start=parse_date(request.query_params.get("start_date","")); end=parse_date(request.query_params.get("end_date",""))
#         if not start or not end or start>end: raise ValidationError("Provide valid start_date and end_date.")
#         rows=LotConsumption.objects.filter(lot__portfolio=p,sell_execution__executed_at__date__gte=start,sell_execution__executed_at__date__lte=end).values(
#             "lot__instrument__ticker").annotate(realized_pnl=Sum("realized_pnl"),quantity=Sum("quantity"))
#         return Response(list(rows))
#
# class TopMoversView(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request,exchange_id):
#         start=parse_date(request.query_params.get("start_date","")); end=parse_date(request.query_params.get("end_date",""))
#         if not start or not end: raise ValidationError("Provide start_date and end_date.")
#         instruments=Instrument.objects.filter(exchange_id=exchange_id,orders__executions__executed_at__date__gte=start,
#             orders__executions__executed_at__date__lte=end).distinct()
#         rows=[]
#         for instrument in instruments:
#             a=DailyPrice.objects.filter(instrument=instrument,trading_date__lte=start).order_by("-trading_date").first()
#             b=DailyPrice.objects.filter(instrument=instrument,trading_date__lte=end).order_by("-trading_date").first()
#             if a and b and a.close:
#                 rows.append({"ticker":instrument.ticker,"start_close":str(a.close),"end_close":str(b.close),
#                     "change_percent":str((b.close-a.close)/a.close*100)})
#         rows.sort(key=lambda x:Decimal(x["change_percent"]),reverse=True)
#         return Response(rows[:10])
#
# class MovingAverageView(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request,instrument_id):
#         qs=DailyPrice.objects.filter(instrument_id=instrument_id).annotate(
#             moving_average=Window(expression=Avg("close"),order_by=F("trading_date").asc(),frame=RowRange(start=-19,end=0))
#         ).order_by("trading_date")
#         return Response([{"date":str(x.trading_date),"close":str(x.close),"moving_average":str(x.moving_average)} for x in qs])
