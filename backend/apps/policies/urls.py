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
router.register(r"enforcement-logs", PolicyEnforcementLogViewSet, basename="enforcement-logs")
router.register(r"incidents", AIIncidentViewSet, basename="incidents")

urlpatterns = [
    path("", include(router.urls)),
    # Standalone endpoint to run all active policies against a single deal.
    # POST /api/policies/evaluate-deal/?deal_id=<uuid>
    path("evaluate-deal/", evaluate_deal, name="evaluate-deal"),
    # Risk assessment endpoint.
    # POST /api/policies/assess-risk/
    path("assess-risk/", assess_risk_view, name="assess-risk"),
]
