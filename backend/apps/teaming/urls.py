from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.teaming.views import TeamingPartnershipViewSet

router = DefaultRouter()
router.register(r"partnerships", TeamingPartnershipViewSet, basename="partnership")

app_name = "teaming"

urlpatterns = [
    path("", include(router.urls)),
]
