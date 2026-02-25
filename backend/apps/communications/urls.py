from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClarificationAnswerViewSet,
    ClarificationQuestionViewSet,
    CommunicationThreadViewSet,
    MessageViewSet,
    QAImpactMappingViewSet,
    ThreadParticipantViewSet,
)

router = DefaultRouter()
router.register(r"threads", CommunicationThreadViewSet, basename="thread")
router.register(r"participants", ThreadParticipantViewSet, basename="participant")
router.register(r"messages", MessageViewSet, basename="message")
router.register(r"questions", ClarificationQuestionViewSet, basename="question")
router.register(r"answers", ClarificationAnswerViewSet, basename="answer")
router.register(r"impact-mappings", QAImpactMappingViewSet, basename="impact-mapping")

urlpatterns = [
    path("", include(router.urls)),
]
