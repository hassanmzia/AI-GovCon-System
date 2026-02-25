from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.deals.views import (
    ActivityViewSet,
    AgencyContactViewSet,
    AgencyInteractionViewSet,
    ApprovalViewSet,
    CommentViewSet,
    DealViewSet,
    GateReviewCriteriaViewSet,
    StakeholderViewSet,
    TaskTemplateViewSet,
    TaskViewSet,
)

router = DefaultRouter()
router.register(r"deals", DealViewSet, basename="deal")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"task-templates", TaskTemplateViewSet, basename="task-template")
router.register(r"approvals", ApprovalViewSet, basename="approval")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"activities", ActivityViewSet, basename="activity")
router.register(r"agency-contacts", AgencyContactViewSet, basename="agency-contact")
router.register(r"agency-interactions", AgencyInteractionViewSet, basename="agency-interaction")
router.register(r"stakeholders", StakeholderViewSet, basename="stakeholder")
router.register(r"gate-criteria", GateReviewCriteriaViewSet, basename="gate-criteria")

urlpatterns = [
    path("", include(router.urls)),
]
