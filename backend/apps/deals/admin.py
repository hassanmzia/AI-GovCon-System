from django.contrib import admin

from apps.deals.models import (
    Activity,
    Approval,
    Comment,
    Deal,
    DealStageHistory,
    Task,
    TaskTemplate,
)


class DealStageHistoryInline(admin.TabularInline):
    model = DealStageHistory
    extra = 0
    readonly_fields = [
        "from_stage",
        "to_stage",
        "transitioned_by",
        "reason",
        "duration_in_previous_stage",
        "created_at",
    ]
    ordering = ["-created_at"]


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ["title", "status", "assigned_to", "priority", "due_date", "stage"]
    ordering = ["priority", "due_date"]


class ApprovalInline(admin.TabularInline):
    model = Approval
    extra = 0
    fields = [
        "approval_type",
        "status",
        "requested_by",
        "requested_from",
        "decided_at",
    ]
    readonly_fields = ["decided_at"]
    ordering = ["-created_at"]


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ["author", "content", "is_ai_generated", "created_at"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "stage",
        "priority",
        "owner",
        "estimated_value",
        "win_probability",
        "composite_score",
        "due_date",
        "outcome",
        "created_at",
    ]
    list_filter = ["stage", "priority", "outcome", "owner"]
    search_fields = ["title", "notes", "opportunity__title", "opportunity__notice_id"]
    readonly_fields = ["id", "stage_entered_at", "created_at", "updated_at"]
    list_select_related = ["opportunity", "owner"]
    raw_id_fields = ["opportunity", "owner"]
    filter_horizontal = ["team"]
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {
            "fields": (
                "id",
                "title",
                "opportunity",
                "owner",
                "team",
            ),
        }),
        ("Pipeline", {
            "fields": (
                "stage",
                "stage_entered_at",
                "priority",
                "due_date",
            ),
        }),
        ("Scores", {
            "fields": (
                "estimated_value",
                "win_probability",
                "fit_score",
                "strategic_score",
                "composite_score",
                "ai_recommendation",
            ),
        }),
        ("Dates", {
            "fields": (
                "bid_decision_date",
                "submission_date",
                "award_date",
            ),
        }),
        ("Outcome", {
            "fields": (
                "outcome",
                "outcome_notes",
            ),
        }),
        ("Notes", {
            "fields": ("notes",),
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    inlines = [
        DealStageHistoryInline,
        TaskInline,
        ApprovalInline,
        CommentInline,
    ]


@admin.register(DealStageHistory)
class DealStageHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "from_stage",
        "to_stage",
        "transitioned_by",
        "duration_in_previous_stage",
        "created_at",
    ]
    list_filter = ["from_stage", "to_stage"]
    search_fields = ["deal__title", "reason"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "transitioned_by"]
    date_hierarchy = "created_at"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "deal",
        "status",
        "assigned_to",
        "priority",
        "due_date",
        "stage",
        "is_ai_generated",
        "completed_at",
    ]
    list_filter = ["status", "priority", "stage", "is_ai_generated", "is_auto_completable"]
    search_fields = ["title", "description", "deal__title"]
    readonly_fields = ["id", "completed_at", "created_at", "updated_at"]
    raw_id_fields = ["deal", "assigned_to"]
    date_hierarchy = "created_at"


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "stage",
        "default_priority",
        "days_until_due",
        "is_required",
        "is_auto_completable",
        "order",
    ]
    list_filter = ["stage", "is_required", "is_auto_completable"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["stage", "order"]


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "approval_type",
        "status",
        "requested_by",
        "requested_from",
        "ai_confidence",
        "decided_at",
        "created_at",
    ]
    list_filter = ["approval_type", "status"]
    search_fields = ["deal__title", "decision_rationale", "ai_recommendation"]
    readonly_fields = ["id", "decided_at", "created_at", "updated_at"]
    raw_id_fields = ["deal", "requested_by", "requested_from"]
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["deal", "author", "content_preview", "is_ai_generated", "created_at"]
    list_filter = ["is_ai_generated"]
    search_fields = ["content", "deal__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "author"]
    date_hierarchy = "created_at"

    @admin.display(description="Content")
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "actor",
        "action",
        "description_preview",
        "is_ai_action",
        "created_at",
    ]
    list_filter = ["action", "is_ai_action"]
    search_fields = ["description", "deal__title", "action"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "actor"]
    date_hierarchy = "created_at"

    @admin.display(description="Description")
    def description_preview(self, obj):
        return obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
