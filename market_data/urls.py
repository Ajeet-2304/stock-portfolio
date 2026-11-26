from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ExchangeViewSet, InstrumentViewSet, DailyPriceViewSet, CorporateActionViewSet, \
    ExchangeHolidayViewSet, TopMoversView, MovingAverageView

# urlpatterns=[
#     path("exchanges", ExchangeViewSet.as_view({'get':'list'}), name='Exchanges'),
#     path("<int:exchangeId>/top-movers", TopMoversView.as_view(), name='Top-Movers'),
#     path("instruments", InstrumentViewSet.as_view(), name='Instruments'),
#     path("<int:instrumentId>/moving-average", MovingAverageView.as_view(), name='Moving-Average'),
#     path("prices", DailyPriceViewSet.as_view(), name='Prices'),
#     path("corporate-actions", CorporateActionViewSet.as_view(), name='Corporate-Actions'),
#     path("holidays", ExchangeHolidayViewSet.as_view(), name='Exchange-Holidays')
# ]

router=DefaultRouter()
router.register("exchanges", ExchangeViewSet)
router.register("instruments", InstrumentViewSet)
router.register("prices", DailyPriceViewSet)
router.register("corporate-actions", CorporateActionViewSet)
router.register("holidays", ExchangeHolidayViewSet)
# router.register("<int:instrumentId>/moving-average", MovingAverageView, basename='moving-average'),
# router.register("<int:exchangeId>/top-movers", TopMoversView, basename='top-movers'),
urlpatterns=router.urls

urlpatterns += [
    path("instruments/<int:instrument_id>/moving-average", MovingAverageView.as_view(), name='moving-average'),
    path("<int:exchangeId>/top-movers", TopMoversView.as_view(), name='top-movers'),

]

# router=DefaultRouter()
# ("exchanges", ExchangeViewSet, basename='Exchanges')
# ("<int:exchangeId>/top-movers", TopMoversView, basename='Top-Movers')
# ("instruments", InstrumentViewSet, basename='Instruments')
# ("<int:instrumentId>/moving-average", MovingAverageView, basename='Moving-Average')
# ("prices", DailyPriceViewSet,basename='Prices')
# ("corporate-actions", CorporateActionViewSet,basename='Corporate-Actions')
# ("holidays", ExchangeHolidayViewSet,basename='Exchange-Holidays')
# urlpatterns=router.urls
