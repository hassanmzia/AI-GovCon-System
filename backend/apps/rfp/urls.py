from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AmendmentViewSet,
    ComplianceMatrixViewSet,
    RFPDocumentViewSet,
    RFPRequirementViewSet,
)

app_name = "rfp"

router = DefaultRouter()
router.register(r"documents", RFPDocumentViewSet, basename="rfp-document")
router.register(r"requirements", RFPRequirementViewSet, basename="rfp-requirement")
router.register(r"compliance-matrix", ComplianceMatrixViewSet, basename="compliance-matrix")
router.register(r"amendments", AmendmentViewSet, basename="amendment")

urlpatterns = [
    path("", include(router.urls)),
]
