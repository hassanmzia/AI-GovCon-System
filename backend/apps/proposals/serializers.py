from rest_framework import serializers

from .models import (
    Proposal,
    ProposalSection,
    ProposalTemplate,
    ReviewComment,
    ReviewCycle,
)


class ProposalTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalTemplate
        fields = [
            "id",
            "name",
            "description",
            "volumes",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProposalSectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for section list views."""
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = ProposalSection
        fields = [
            "id",
            "proposal",
            "volume",
            "section_number",
            "title",
            "order",
            "status",
            "assigned_to",
            "assigned_to_name",
            "word_count",
            "page_limit",
            "created_at",
        ]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.email
        return None


class ProposalSectionDetailSerializer(serializers.ModelSerializer):
    """Full serializer for section detail/create/update views."""
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = ProposalSection
        fields = [
            "id",
            "proposal",
            "volume",
            "section_number",
            "title",
            "order",
            "ai_draft",
            "human_content",
            "final_content",
            "status",
            "assigned_to",
            "assigned_to_name",
            "word_count",
            "page_limit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.email
        return None


class ReviewCommentSerializer(serializers.ModelSerializer):
    """Serializer for review comments."""
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = ReviewComment
        fields = [
            "id",
            "review",
            "section",
            "reviewer",
            "reviewer_name",
            "comment_type",
            "content",
            "is_resolved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_reviewer_name(self, obj):
        if obj.reviewer:
            return obj.reviewer.get_full_name() or obj.reviewer.email
        return None


class ReviewCycleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for review cycle list views."""
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ReviewCycle
        fields = [
            "id",
            "proposal",
            "review_type",
            "status",
            "scheduled_date",
            "completed_date",
            "overall_score",
            "comment_count",
            "created_at",
        ]


class ReviewCycleDetailSerializer(serializers.ModelSerializer):
    """Full serializer for review cycle detail views."""
    comments = ReviewCommentSerializer(many=True, read_only=True)

    class Meta:
        model = ReviewCycle
        fields = [
            "id",
            "proposal",
            "review_type",
            "status",
            "scheduled_date",
            "completed_date",
            "overall_score",
            "summary",
            "reviewers",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProposalListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for proposal list views."""
    deal_title = serializers.CharField(source="deal.title", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    section_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Proposal
        fields = [
            "id",
            "deal",
            "deal_title",
            "template",
            "template_name",
            "title",
            "version",
            "status",
            "total_requirements",
            "compliant_count",
            "compliance_percentage",
            "section_count",
            "created_at",
        ]


class ProposalDetailSerializer(serializers.ModelSerializer):
    """Full serializer for proposal detail/create/update views."""
    deal_title = serializers.CharField(source="deal.title", read_only=True)
    template_name = serializers.CharField(
        source="template.name", read_only=True, default=None
    )
    sections = ProposalSectionListSerializer(many=True, read_only=True)
    reviews = ReviewCycleListSerializer(many=True, read_only=True)

    class Meta:
        model = Proposal
        fields = [
            "id",
            "deal",
            "deal_title",
            "template",
            "template_name",
            "title",
            "version",
            "status",
            "win_themes",
            "discriminators",
            "executive_summary",
            "total_requirements",
            "compliant_count",
            "compliance_percentage",
            "sections",
            "reviews",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
