from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.marketing.views import MarketingCampaignViewSet

router = DefaultRouter()
router.register(r"campaigns", MarketingCampaignViewSet, basename="campaign")

app_name = "marketing"

urlpatterns = [
    path("", include(router.urls)),
]
