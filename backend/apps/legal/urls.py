from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.legal.views import (
    ComplianceAssessmentViewSet,
    ContractReviewNoteViewSet,
    FARClauseViewSet,
    LegalRiskViewSet,
    RegulatoryRequirementViewSet,
)

router = DefaultRouter()
router.register(r"far-clauses", FARClauseViewSet, basename="far-clause")
router.register(
    r"regulatory-requirements",
    RegulatoryRequirementViewSet,
    basename="regulatory-requirement",
)
router.register(
    r"compliance-assessments",
    ComplianceAssessmentViewSet,
    basename="compliance-assessment",
)
router.register(r"legal-risks", LegalRiskViewSet, basename="legal-risk")
router.register(
    r"contract-review-notes",
    ContractReviewNoteViewSet,
    basename="contract-review-note",
)

urlpatterns = [
    path("", include(router.urls)),
]
