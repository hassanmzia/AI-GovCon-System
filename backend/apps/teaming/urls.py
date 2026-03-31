from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.teaming.views import TeamingPartnershipViewSet, TeamingPartnerViewSet, TeamingAgreementViewSet

router = DefaultRouter()
router.register(r"partnerships", TeamingPartnershipViewSet, basename="partnership")
router.register(r"partners", TeamingPartnerViewSet, basename="partner")
router.register(r"agreements", TeamingAgreementViewSet, basename="agreement")

app_name = "teaming"

urlpatterns = [
    path("", include(router.urls)),
]
