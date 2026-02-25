from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CompanyProfileViewSet, DailyDigestViewSet, OpportunityViewSet

router = DefaultRouter()
router.register(r"opportunities", OpportunityViewSet, basename="opportunity")
router.register(r"company-profiles", CompanyProfileViewSet, basename="company-profile")
router.register(r"digests", DailyDigestViewSet, basename="daily-digest")

urlpatterns = [
    path("trigger_scan/", OpportunityViewSet.as_view({"post": "trigger_scan"}), name="trigger-scan"),
    path("", include(router.urls)),
]
