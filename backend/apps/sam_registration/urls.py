from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.sam_registration.views import SAMContactViewSet, SAMRegistrationViewSet

router = DefaultRouter()
router.register(r"registrations", SAMRegistrationViewSet, basename="sam-registration")
router.register(r"contacts", SAMContactViewSet, basename="sam-contact")

urlpatterns = [
    path("", include(router.urls)),
]
