from rest_framework import serializers

from .models import (
    ClarificationAnswer,
    ClarificationQuestion,
    CommunicationThread,
    Message,
    QAImpactMapping,
    ThreadParticipant,
)


class ThreadParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadParticipant
        fields = [
            "id",
            "thread",
            "user",
            "role",
            "joined_at",
            "last_read_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "joined_at", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "thread",
            "sender",
            "content",
            "message_type",
            "attachments",
            "is_edited",
            "edited_at",
            "parent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "sender", "is_edited", "edited_at", "created_at", "updated_at"]


class CommunicationThreadSerializer(serializers.ModelSerializer):
    thread_participants = ThreadParticipantSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationThread
        fields = [
            "id",
            "deal",
            "subject",
            "thread_type",
            "thread_participants",
            "status",
            "priority",
            "tags",
            "message_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()


class SendMessageSerializer(serializers.Serializer):
    """Serializer for the send_message action on CommunicationThread."""

    content = serializers.CharField()
    message_type = serializers.ChoiceField(
        choices=Message.MESSAGE_TYPE_CHOICES, default="text"
    )
    attachments = serializers.JSONField(default=list, required=False)
    parent = serializers.UUIDField(required=False, allow_null=True)


class ClarificationQuestionSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()

    class Meta:
        model = ClarificationQuestion
        fields = [
            "id",
            "deal",
            "rfp_section",
            "question_text",
            "question_number",
            "submitted_by",
            "submitted_at",
            "due_date",
            "status",
            "is_government_question",
            "source",
            "answers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_answers(self, obj):
        return ClarificationAnswerSerializer(obj.answers.all(), many=True).data


class ClarificationAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClarificationAnswer
        fields = [
            "id",
            "question",
            "answer_text",
            "answered_by",
            "answered_at",
            "impacts_proposal",
            "amendment_reference",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class QAImpactMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = QAImpactMapping
        fields = [
            "id",
            "answer",
            "proposal_section",
            "impact_description",
            "action_required",
            "status",
            "assigned_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
