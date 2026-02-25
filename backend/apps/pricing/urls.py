from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.pricing.views import (
    ConsultantProfileViewSet,
    CostModelViewSet,
    LOEEstimateViewSet,
    PricingApprovalViewSet,
    PricingScenarioViewSet,
    RateCardViewSet,
)

router = DefaultRouter()
router.register(r"rate-cards", RateCardViewSet, basename="ratecard")
router.register(r"consultants", ConsultantProfileViewSet, basename="consultantprofile")
router.register(r"loe-estimates", LOEEstimateViewSet, basename="loeestimate")
router.register(r"cost-models", CostModelViewSet, basename="costmodel")
router.register(r"scenarios", PricingScenarioViewSet, basename="pricingscenario")
router.register(r"approvals", PricingApprovalViewSet, basename="pricingapproval")

urlpatterns = [
    path("", include(router.urls)),
]
