from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.analytics.views import (
    AgentPerformanceMetricViewSet,
    DealVelocityMetricViewSet,
    ExecutiveDashboardView,
    KPISnapshotViewSet,
    PipelineLoadView,
    RecommendationMetricViewSet,
    WinLossAnalysisViewSet,
)

router = DefaultRouter()
router.register(r"kpi-snapshots", KPISnapshotViewSet, basename="kpisnapshot")
router.register(r"win-loss", WinLossAnalysisViewSet, basename="winloss")
router.register(r"velocity", DealVelocityMetricViewSet, basename="dealvelocity")
router.register(r"agent-metrics", AgentPerformanceMetricViewSet, basename="agentmetric")
router.register(r"recommendations", RecommendationMetricViewSet, basename="recommendationmetric")

app_name = "analytics"

urlpatterns = [
    path("", include(router.urls)),
    path("executive-dashboard/", ExecutiveDashboardView.as_view(), name="executive-dashboard"),
    path("pipeline-load/", PipelineLoadView.as_view(), name="pipeline-load"),
]
