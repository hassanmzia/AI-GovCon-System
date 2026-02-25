from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CompanyStrategyViewSet,
    PortfolioSnapshotViewSet,
    StrategicGoalViewSet,
    StrategicScoreViewSet,
)

router = DefaultRouter()
router.register(r"strategies", CompanyStrategyViewSet, basename="strategy")
router.register(r"portfolio-snapshots", PortfolioSnapshotViewSet, basename="portfolio-snapshot")
router.register(r"strategic-scores", StrategicScoreViewSet, basename="strategic-score")
router.register(r"strategic-goals", StrategicGoalViewSet, basename="strategic-goal")

app_name = "strategy"

urlpatterns = [
    path("", include(router.urls)),
    # Nested goals under a specific strategy
    path(
        "strategies/<uuid:strategy_pk>/goals/",
        StrategicGoalViewSet.as_view({"get": "list", "post": "create"}),
        name="strategy-goals-list",
    ),
    path(
        "strategies/<uuid:strategy_pk>/goals/<uuid:pk>/",
        StrategicGoalViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="strategy-goals-detail",
    ),
]
