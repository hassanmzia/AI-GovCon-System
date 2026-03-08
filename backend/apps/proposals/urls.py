from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProposalSectionViewSet,
    ProposalTemplateViewSet,
    ProposalViewSet,
    ReviewCommentViewSet,
    ReviewCycleViewSet,
    SourcesSoughtResponseViewSet,
    SubmissionEmailViewSet,
)

router = DefaultRouter()
router.register(r"proposal-templates", ProposalTemplateViewSet, basename="proposal-template")
router.register(r"proposals", ProposalViewSet, basename="proposal")
router.register(r"proposal-sections", ProposalSectionViewSet, basename="proposal-section")
router.register(r"review-cycles", ReviewCycleViewSet, basename="review-cycle")
router.register(r"review-comments", ReviewCommentViewSet, basename="review-comment")
router.register(r"sources-sought", SourcesSoughtResponseViewSet, basename="sources-sought")
router.register(r"submission-emails", SubmissionEmailViewSet, basename="submission-email")

urlpatterns = [
    path("", include(router.urls)),
]
