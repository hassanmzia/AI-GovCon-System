from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.analytics.views import (
    AgentPerformanceMetricViewSet,
    DealVelocityMetricViewSet,
    KPISnapshotViewSet,
    WinLossAnalysisViewSet,
)

router = DefaultRouter()
router.register(r"kpi-snapshots", KPISnapshotViewSet, basename="kpisnapshot")
router.register(r"win-loss", WinLossAnalysisViewSet, basename="winloss")
router.register(r"velocity", DealVelocityMetricViewSet, basename="dealvelocity")
router.register(r"agent-metrics", AgentPerformanceMetricViewSet, basename="agentmetric")

app_name = "analytics"

urlpatterns = [
    path("", include(router.urls)),
]
