from django.contrib import admin

from .models import (
    ClarificationAnswer,
    ClarificationQuestion,
    CommunicationThread,
    Message,
    QAImpactMapping,
    ThreadParticipant,
)


@admin.register(CommunicationThread)
class CommunicationThreadAdmin(admin.ModelAdmin):
    list_display = ("subject", "thread_type", "status", "priority", "deal", "created_at")
    list_filter = ("thread_type", "status", "priority")
    search_fields = ("subject", "deal__title")


@admin.register(ThreadParticipant)
class ThreadParticipantAdmin(admin.ModelAdmin):
    list_display = ("thread", "user", "role", "joined_at", "last_read_at")
    list_filter = ("role",)
    search_fields = ("thread__subject", "user__email")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "sender", "message_type", "is_edited", "created_at")
    list_filter = ("message_type", "is_edited")
    search_fields = ("content", "sender__email", "thread__subject")


@admin.register(ClarificationQuestion)
class ClarificationQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "question_number",
        "question_text_short",
        "deal",
        "status",
        "source",
        "is_government_question",
        "due_date",
    )
    list_filter = ("status", "source", "is_government_question")
    search_fields = ("question_text", "rfp_section", "deal__title")

    @admin.display(description="Question")
    def question_text_short(self, obj):
        return obj.question_text[:80]


@admin.register(ClarificationAnswer)
class ClarificationAnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "answered_by", "answered_at", "impacts_proposal")
    list_filter = ("impacts_proposal",)
    search_fields = ("answer_text", "answered_by", "question__question_text")


@admin.register(QAImpactMapping)
class QAImpactMappingAdmin(admin.ModelAdmin):
    list_display = ("proposal_section", "answer", "status", "assigned_to", "created_at")
    list_filter = ("status",)
    search_fields = ("proposal_section", "impact_description", "action_required")
