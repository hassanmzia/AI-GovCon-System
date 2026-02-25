from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BusinessPolicyViewSet,
    PolicyEvaluationViewSet,
    PolicyExceptionViewSet,
    evaluate_deal,
)

app_name = "policies"

router = DefaultRouter()
router.register(r"business-policies", BusinessPolicyViewSet, basename="business-policies")
router.register(r"evaluations", PolicyEvaluationViewSet, basename="evaluations")
router.register(r"exceptions", PolicyExceptionViewSet, basename="exceptions")

urlpatterns = [
    path("", include(router.urls)),
    # Standalone endpoint to run all active policies against a single deal.
    # POST /api/policies/evaluate-deal/?deal_id=<uuid>
    path("evaluate-deal/", evaluate_deal, name="evaluate-deal"),
]
