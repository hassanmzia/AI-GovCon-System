from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.deals.views import (
    ActivityViewSet,
    ApprovalViewSet,
    CommentViewSet,
    DealViewSet,
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

urlpatterns = [
    path("", include(router.urls)),
]
