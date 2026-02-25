from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.security_compliance.views import (
    ComplianceRequirementViewSet,
    SecurityComplianceReportViewSet,
    SecurityControlMappingViewSet,
    SecurityControlViewSet,
    SecurityFrameworkViewSet,
)

router = DefaultRouter()
router.register(r"frameworks", SecurityFrameworkViewSet, basename="framework")
router.register(r"controls", SecurityControlViewSet, basename="control")
router.register(r"control-mappings", SecurityControlMappingViewSet, basename="control-mapping")
router.register(r"reports", SecurityComplianceReportViewSet, basename="report")
router.register(r"requirements", ComplianceRequirementViewSet, basename="requirement")

app_name = "security_compliance"

urlpatterns = [
    path("", include(router.urls)),
]
