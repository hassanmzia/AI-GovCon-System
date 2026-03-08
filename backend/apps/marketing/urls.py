from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.marketing.views import CapabilityStatementViewSet, MarketingCampaignViewSet

router = DefaultRouter()
router.register(r"campaigns", MarketingCampaignViewSet, basename="campaign")
router.register(r"capability-statements", CapabilityStatementViewSet, basename="capability-statement")

app_name = "marketing"

urlpatterns = [
    path("", include(router.urls)),
]
