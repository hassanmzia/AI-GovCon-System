from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.research.views import (
    CompetitorProfileViewSet,
    MarketIntelligenceViewSet,
    ResearchProjectViewSet,
    ResearchSourceViewSet,
)

router = DefaultRouter()
router.register(r"projects", ResearchProjectViewSet, basename="research-project")
router.register(r"sources", ResearchSourceViewSet, basename="research-source")
router.register(r"competitors", CompetitorProfileViewSet, basename="competitor-profile")
router.register(
    r"market-intelligence",
    MarketIntelligenceViewSet,
    basename="market-intelligence",
)

urlpatterns = [
    path("", include(router.urls)),
]
