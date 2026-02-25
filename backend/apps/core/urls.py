from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

urlpatterns = [
    path("", views.health_check, name="health-check"),
    path("core/", include(router.urls)),
]
