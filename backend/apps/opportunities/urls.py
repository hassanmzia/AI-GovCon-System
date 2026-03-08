from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CompanyProfileViewSet,
    DailyDigestViewSet,
    NAICSCodeViewSet,
    OpportunityViewSet,
    SAMRegistrationViewSet,
    SBACertificationViewSet,
)

# Secondary viewsets only — OpportunityViewSet is mounted manually below
# so that its list/detail sit at /api/opportunities/ rather than the
# double-nested /api/opportunities/opportunities/.
router = DefaultRouter()
router.register(r"company-profiles", CompanyProfileViewSet, basename="company-profile")
router.register(r"digests", DailyDigestViewSet, basename="daily-digest")
router.register(r"sam-registrations", SAMRegistrationViewSet, basename="sam-registration")
router.register(r"naics-codes", NAICSCodeViewSet, basename="naics-code")
router.register(r"sba-certifications", SBACertificationViewSet, basename="sba-certification")

urlpatterns = [
    # /api/opportunities/             → list
    path("", OpportunityViewSet.as_view({"get": "list"}), name="opportunity-list"),
    # /api/opportunities/<uuid>/      → retrieve
    path("<uuid:pk>/", OpportunityViewSet.as_view({"get": "retrieve"}), name="opportunity-detail"),
    # /api/opportunities/filters/     → distinct values for filter dropdowns
    path("filters/", OpportunityViewSet.as_view({"get": "filters"}), name="opportunity-filters"),
    # /api/opportunities/trigger_scan/ → custom action
    path("trigger_scan/", OpportunityViewSet.as_view({"post": "trigger_scan"}), name="trigger-scan"),
    # /api/opportunities/company-profiles/ and /api/opportunities/digests/
    path("", include(router.urls)),
]
