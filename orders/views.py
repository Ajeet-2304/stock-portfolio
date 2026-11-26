from django.shortcuts import render

# Create your views here.
from decimal import Decimal
from django.db.models import Sum, Avg, F, Window
from django.db.models import RowRange
from django.utils.dateparse import parse_date
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError

from orders.serializers import OrderSerializer, ExecutionSerializer
from orders.services import place_order, record_execution, cancel_order
from portfolios.models import Portfolio
from portfolios.services import cash_balance
from orders.models import TaxLot, LotConsumption, Order
from market_data.models import DailyPrice, Instrument, Exchange



class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class=OrderSerializer
    permission_classes=[permissions.IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(portfolio__user=self.request.user).select_related("portfolio","instrument")
    def perform_create(self, serializer):
        data=serializer.validated_data
        portfolio_id=self.request.data.get("portfolio")
        try: portfolio=Portfolio.objects.get(pk=portfolio_id,user=self.request.user)
        except Portfolio.DoesNotExist: raise NotFound("Portfolio not found.")
        order=place_order(portfolio=portfolio,instrument=data["instrument"],side=data["side"],
            order_type=data["order_type"],quantity=data["quantity"],limit_price=data.get("limit_price"))
        self.created_order=order
    def create(self, request, *args, **kwargs):
        response=super().create(request,*args,**kwargs)
        response.data=OrderSerializer(self.created_order).data
        return response

class ExecutionCreateView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self,request,order_id):
        serializer=ExecutionSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        try: order=Order.objects.get(pk=order_id,portfolio__user=request.user)
        except Order.DoesNotExist: raise NotFound("Order not found.")
        execution,created=record_execution(order_id=order.id,**serializer.validated_data)
        return Response({"execution_id":execution.id,"created":created,"order_status":execution.order.status},status=201 if created else 200)

class CancelOrderView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self,request,order_id):
        try: order=Order.objects.get(pk=order_id,portfolio__user=request.user)
        except Order.DoesNotExist: raise NotFound("Order not found.")
        order=cancel_order(order.id,order.portfolio)
        return Response(OrderSerializer(order).data)





