from django.urls import path
from .views import OrderListCreateView, ExecutionCreateView, CancelOrderView
urlpatterns=[
    path("",OrderListCreateView.as_view(),name='order-list'),
    path("<int:order_id>/executions/",ExecutionCreateView.as_view(),name='order-execution'),
    path("<int:order_id>/cancel/",CancelOrderView.as_view(),name='order-cancel')
]
