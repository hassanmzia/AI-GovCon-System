from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.sba_certifications.views import NAICSCodeViewSet, SBACertificationViewSet

router = DefaultRouter()
router.register(r"certifications", SBACertificationViewSet, basename="sba-certification")
router.register(r"naics-codes", NAICSCodeViewSet, basename="naics-code")

urlpatterns = [
    path("", include(router.urls)),
]
