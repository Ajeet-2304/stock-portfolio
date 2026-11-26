from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PortfolioViewSet, HoldingsView, PortfolioValueView

router=DefaultRouter()
router.register("", PortfolioViewSet, basename="portfolio")
# router.register("<int:portfolioId>/holdings", HoldingsView)
# router.register("<int:portfolioId>/value", PortfolioValueView, basename="portfolio-value")
router.register("<int:portfolioId>/realized-pnl", PortfolioViewSet, basename="portfolio-realized-pnl")
# router.register("", PortfolioViewSet, basename="portfolio")
urlpatterns=router.urls

urlpatterns += [
    path(
        'holdings/',
        HoldingsView.as_view(),
        name='holdings'
    ),
    path(
        '<int:portfolioId>/value',
        PortfolioValueView.as_view(),
        name='portfolio-value'
    ),
]