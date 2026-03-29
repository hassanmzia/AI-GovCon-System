from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ArchitectureDiagramViewSet,
    ProposalSectionViewSet,
    ProposalTemplateViewSet,
    ProposalViewSet,
    ReviewCommentViewSet,
    ReviewCycleViewSet,
    SolutionValidationReportViewSet,
    SourcesSoughtResponseViewSet,
    SubmissionEmailViewSet,
    TechnicalSolutionViewSet,
)

router = DefaultRouter()
router.register(r"proposal-templates", ProposalTemplateViewSet, basename="proposal-template")
router.register(r"proposals", ProposalViewSet, basename="proposal")
router.register(r"proposal-sections", ProposalSectionViewSet, basename="proposal-section")
router.register(r"review-cycles", ReviewCycleViewSet, basename="review-cycle")
router.register(r"review-comments", ReviewCommentViewSet, basename="review-comment")
router.register(r"sources-sought", SourcesSoughtResponseViewSet, basename="sources-sought")
router.register(r"submission-emails", SubmissionEmailViewSet, basename="submission-email")
router.register(r"technical-solutions", TechnicalSolutionViewSet, basename="technical-solution")
router.register(r"architecture-diagrams", ArchitectureDiagramViewSet, basename="architecture-diagram")
router.register(r"validation-reports", SolutionValidationReportViewSet, basename="validation-report")

urlpatterns = [
    path("", include(router.urls)),
]
