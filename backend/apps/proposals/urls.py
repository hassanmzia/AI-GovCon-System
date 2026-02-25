from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProposalSectionViewSet,
    ProposalTemplateViewSet,
    ProposalViewSet,
    ReviewCommentViewSet,
    ReviewCycleViewSet,
)

router = DefaultRouter()
router.register(r"proposal-templates", ProposalTemplateViewSet, basename="proposal-template")
router.register(r"proposals", ProposalViewSet, basename="proposal")
router.register(r"proposal-sections", ProposalSectionViewSet, basename="proposal-section")
router.register(r"review-cycles", ReviewCycleViewSet, basename="review-cycle")
router.register(r"review-comments", ReviewCommentViewSet, basename="review-comment")

urlpatterns = [
    path("", include(router.urls)),
]
