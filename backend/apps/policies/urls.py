from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AIAutonomyPolicyViewSet,
    AIIncidentViewSet,
    BusinessPolicyViewSet,
    PolicyEnforcementLogViewSet,
    PolicyEvaluationViewSet,
    PolicyExceptionViewSet,
    assess_risk_view,
    evaluate_deal,
)

app_name = "policies"

router = DefaultRouter()
router.register(r"business-policies", BusinessPolicyViewSet, basename="business-policies")
router.register(r"evaluations", PolicyEvaluationViewSet, basename="evaluations")
router.register(r"exceptions", PolicyExceptionViewSet, basename="exceptions")
router.register(r"autonomy-policies", AIAutonomyPolicyViewSet, basename="autonomy-policies")
# Canonical plural form (frontend dashboard)
router.register(r"enforcement-logs", PolicyEnforcementLogViewSet, basename="enforcement-logs")
router.register(r"incidents", AIIncidentViewSet, basename="incidents")

# The AI orchestrator posts to /enforcement-log/ (singular — no trailing 's').
# Register explicit aliases so both paths resolve to the same ViewSet.
_log_list = PolicyEnforcementLogViewSet.as_view({"get": "list", "post": "create"})
_log_detail = PolicyEnforcementLogViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("", include(router.urls)),
    # Singular alias for the AI orchestrator
    path("enforcement-log/", _log_list, name="enforcement-log-list"),
    path("enforcement-log/<pk>/", _log_detail, name="enforcement-log-detail"),
    # Standalone endpoint to run all active policies against a single deal.
    # POST /api/policies/evaluate-deal/?deal_id=<uuid>
    path("evaluate-deal/", evaluate_deal, name="evaluate-deal"),
    # Risk assessment endpoint.
    # POST /api/policies/assess-risk/
    path("assess-risk/", assess_risk_view, name="assess-risk"),
]
