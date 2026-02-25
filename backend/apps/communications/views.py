from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ClarificationAnswer,
    ClarificationQuestion,
    CommunicationThread,
    Message,
    QAImpactMapping,
    ThreadParticipant,
)
from .serializers import (
    ClarificationAnswerSerializer,
    ClarificationQuestionSerializer,
    CommunicationThreadSerializer,
    MessageSerializer,
    QAImpactMappingSerializer,
    SendMessageSerializer,
    ThreadParticipantSerializer,
)


class CommunicationThreadViewSet(viewsets.ModelViewSet):
    """ViewSet for communication threads."""

    queryset = CommunicationThread.objects.all()
    serializer_class = CommunicationThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            CommunicationThread.objects.prefetch_related(
                "thread_participants", "messages"
            )
            .select_related("deal")
            .all()
        )

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """Send a message to this communication thread."""
        thread = self.get_object()
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parent = None
        parent_id = serializer.validated_data.get("parent")
        if parent_id:
            try:
                parent = Message.objects.get(id=parent_id, thread=thread)
            except Message.DoesNotExist:
                return Response(
                    {"detail": "Parent message not found in this thread."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        message = Message.objects.create(
            thread=thread,
            sender=request.user,
            content=serializer.validated_data["content"],
            message_type=serializer.validated_data.get("message_type", "text"),
            attachments=serializer.validated_data.get("attachments", []),
            parent=parent,
        )

        return Response(
            MessageSerializer(message).data, status=status.HTTP_201_CREATED
        )


class ThreadParticipantViewSet(viewsets.ModelViewSet):
    """ViewSet for thread participants."""

    queryset = ThreadParticipant.objects.all()
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ThreadParticipant.objects.select_related("thread", "user").all()


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for messages."""

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.select_related("thread", "sender", "parent").all()

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class ClarificationQuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for clarification questions."""

    queryset = ClarificationQuestion.objects.all()
    serializer_class = ClarificationQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClarificationQuestion.objects.prefetch_related("answers").all()


class ClarificationAnswerViewSet(viewsets.ModelViewSet):
    """ViewSet for clarification answers."""

    queryset = ClarificationAnswer.objects.all()
    serializer_class = ClarificationAnswerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClarificationAnswer.objects.select_related("question").all()


class QAImpactMappingViewSet(viewsets.ModelViewSet):
    """ViewSet for Q&A impact mappings."""

    queryset = QAImpactMapping.objects.all()
    serializer_class = QAImpactMappingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QAImpactMapping.objects.select_related("answer", "assigned_to").all()
