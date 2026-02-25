from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from apps.deals.models import (
    Activity,
    Approval,
    Comment,
    Deal,
    DealStageHistory,
    Task,
    TaskTemplate,
)

User = get_user_model()


# ── Lightweight nested serializers ───────────────────────


class UserMinimalSerializer(serializers.ModelSerializer):
    """Compact user representation for nested use."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = fields


class OpportunityMinimalSerializer(serializers.Serializer):
    """Read-only opportunity summary embedded in deal responses."""

    id = serializers.UUIDField(read_only=True)
    notice_id = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    agency = serializers.CharField(read_only=True)
    notice_type = serializers.CharField(read_only=True)
    response_deadline = serializers.DateTimeField(read_only=True)
    estimated_value = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    status = serializers.CharField(read_only=True)


# ── Deal ─────────────────────────────────────────────────


class DealListSerializer(serializers.ModelSerializer):
    """Lightweight serializer used in list views."""

    owner_name = serializers.SerializerMethodField()
    opportunity_title = serializers.CharField(
        source="opportunity.title", read_only=True
    )
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    task_count = serializers.SerializerMethodField()
    pending_approval_count = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = [
            "id",
            "title",
            "stage",
            "stage_display",
            "priority",
            "priority_display",
            "estimated_value",
            "win_probability",
            "composite_score",
            "owner",
            "owner_name",
            "opportunity",
            "opportunity_title",
            "due_date",
            "outcome",
            "task_count",
            "pending_approval_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_owner_name(self, obj):
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip() or obj.owner.username
        return None

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_pending_approval_count(self, obj):
        return obj.approvals.filter(status="pending").count()


class DealDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer with nested relationships."""

    opportunity_detail = OpportunityMinimalSerializer(
        source="opportunity", read_only=True
    )
    owner_detail = UserMinimalSerializer(source="owner", read_only=True)
    team_detail = UserMinimalSerializer(source="team", many=True, read_only=True)
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = Deal
        fields = [
            "id",
            # Relationships
            "opportunity",
            "opportunity_detail",
            "owner",
            "owner_detail",
            "team",
            "team_detail",
            # Core fields
            "title",
            "stage",
            "stage_display",
            "priority",
            "priority_display",
            "estimated_value",
            "win_probability",
            "fit_score",
            "strategic_score",
            "composite_score",
            "ai_recommendation",
            "notes",
            # Dates
            "due_date",
            "stage_entered_at",
            "bid_decision_date",
            "submission_date",
            "award_date",
            # Outcome
            "outcome",
            "outcome_notes",
            # Timestamps
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "stage_entered_at",
            "created_at",
            "updated_at",
        ]


class DealCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new deal."""

    class Meta:
        model = Deal
        fields = [
            "opportunity",
            "owner",
            "team",
            "title",
            "priority",
            "estimated_value",
            "notes",
            "due_date",
        ]

    def create(self, validated_data):
        team_members = validated_data.pop("team", [])
        deal = Deal.objects.create(**validated_data)
        if team_members:
            deal.team.set(team_members)

        # Log the creation activity
        Activity.objects.create(
            deal=deal,
            actor=self.context.get("request", None) and self.context["request"].user,
            action="deal_created",
            description=f"Deal '{deal.title}' created in intake stage",
            metadata={"stage": deal.stage},
        )
        return deal


# ── Stage transition ─────────────────────────────────────


class DealTransitionSerializer(serializers.Serializer):
    """Input serializer for the transition action."""

    target_stage = serializers.ChoiceField(choices=Deal.STAGES)
    reason = serializers.CharField(required=False, default="", allow_blank=True)


# ── DealStageHistory ─────────────────────────────────────


class DealStageHistorySerializer(serializers.ModelSerializer):
    transitioned_by_detail = UserMinimalSerializer(
        source="transitioned_by", read_only=True
    )

    class Meta:
        model = DealStageHistory
        fields = [
            "id",
            "deal",
            "from_stage",
            "to_stage",
            "transitioned_by",
            "transitioned_by_detail",
            "reason",
            "duration_in_previous_stage",
            "created_at",
        ]
        read_only_fields = fields


# ── Task ─────────────────────────────────────────────────


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_detail = UserMinimalSerializer(
        source="assigned_to", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "deal",
            "title",
            "description",
            "assigned_to",
            "assigned_to_detail",
            "status",
            "status_display",
            "priority",
            "due_date",
            "completed_at",
            "stage",
            "is_ai_generated",
            "is_auto_completable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "completed_at",
            "is_ai_generated",
            "created_at",
            "updated_at",
        ]

    def update(self, instance, validated_data):
        new_status = validated_data.get("status", instance.status)
        # Auto-set completed_at when status transitions to completed
        if new_status == "completed" and instance.status != "completed":
            validated_data["completed_at"] = timezone.now()
        # Clear completed_at when moving away from completed
        elif new_status != "completed" and instance.status == "completed":
            validated_data["completed_at"] = None

        task = super().update(instance, validated_data)

        # Log the activity
        if new_status != instance.status:
            Activity.objects.create(
                deal=task.deal,
                actor=self.context.get("request", None)
                and self.context["request"].user,
                action="task_status_changed",
                description=(
                    f"Task '{task.title}' status changed to {new_status}"
                ),
                metadata={
                    "task_id": str(task.id),
                    "old_status": instance.status,
                    "new_status": new_status,
                },
            )
        return task


# ── TaskTemplate ─────────────────────────────────────────


class TaskTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTemplate
        fields = [
            "id",
            "stage",
            "title",
            "description",
            "default_priority",
            "days_until_due",
            "is_required",
            "is_auto_completable",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Approval ─────────────────────────────────────────────


class ApprovalSerializer(serializers.ModelSerializer):
    requested_by_detail = UserMinimalSerializer(
        source="requested_by", read_only=True
    )
    requested_from_detail = UserMinimalSerializer(
        source="requested_from", read_only=True
    )

    class Meta:
        model = Approval
        fields = [
            "id",
            "deal",
            "approval_type",
            "requested_by",
            "requested_by_detail",
            "requested_from",
            "requested_from_detail",
            "status",
            "ai_recommendation",
            "ai_confidence",
            "decision_rationale",
            "decided_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "requested_by",
            "decided_at",
            "created_at",
            "updated_at",
        ]


class ApprovalDecisionSerializer(serializers.Serializer):
    """Input serializer for approve/reject actions."""

    status = serializers.ChoiceField(choices=["approved", "rejected"])
    decision_rationale = serializers.CharField(
        required=False, default="", allow_blank=True
    )


# ── Comment ──────────────────────────────────────────────


class CommentSerializer(serializers.ModelSerializer):
    author_detail = UserMinimalSerializer(source="author", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "deal",
            "author",
            "author_detail",
            "content",
            "is_ai_generated",
            "created_at",
        ]
        read_only_fields = ["id", "author", "is_ai_generated", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["author"] = request.user
        comment = super().create(validated_data)

        # Log comment activity
        Activity.objects.create(
            deal=comment.deal,
            actor=comment.author,
            action="comment_added",
            description=f"Comment added by {comment.author}",
            metadata={"comment_id": str(comment.id)},
        )
        return comment


# ── Activity ─────────────────────────────────────────────


class ActivitySerializer(serializers.ModelSerializer):
    actor_detail = UserMinimalSerializer(source="actor", read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id",
            "deal",
            "actor",
            "actor_detail",
            "action",
            "description",
            "metadata",
            "is_ai_action",
            "created_at",
        ]
        read_only_fields = fields
