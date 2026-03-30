from rest_framework import serializers

from .models import (
    ArchitectureDiagram,
    Proposal,
    ProposalSection,
    ProposalTemplate,
    ReviewComment,
    ReviewCycle,
    SolutionValidationReport,
    SourcesSoughtResponse,
    SubmissionEmail,
    TechnicalSolution,
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
            "solicitation_number",
            "evaluation_method",
            "contract_type",
            "submission_date",
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
    sections = ProposalSectionDetailSerializer(many=True, read_only=True)
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
            "solicitation_number",
            "project_title",
            "issuing_agency",
            "submission_date",
            "evaluation_method",
            "contract_type",
            "win_themes",
            "discriminators",
            "executive_summary",
            "total_requirements",
            "compliant_count",
            "compliance_percentage",
            "submission_method",
            "submission_email",
            "submission_portal_url",
            "submitted_at",
            "confirmation_number",
            "sections",
            "reviews",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Sources Sought ────────────────────────────────────────────────────────────

class SourcesSoughtResponseSerializer(serializers.ModelSerializer):
    interest_level_display = serializers.CharField(
        source="get_interest_level_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = SourcesSoughtResponse
        fields = [
            "id",
            "deal",
            "deal_name",
            "opportunity",
            "title",
            "solicitation_number",
            "company_overview",
            "relevant_experience",
            "technical_approach_summary",
            "capability_gaps",
            "questions_for_government",
            "interest_level",
            "interest_level_display",
            "status",
            "status_display",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Submission Email ──────────────────────────────────────────────────────────

class SubmissionEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionEmail
        fields = [
            "id",
            "proposal",
            "sources_sought",
            "email_type",
            "recipient_email",
            "recipient_name",
            "subject_line",
            "body",
            "attachments_list",
            "is_sent",
            "sent_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Solution Architecture ─────────────────────────────────────────────────────

class TechnicalSolutionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for technical solution list views."""
    deal_title = serializers.CharField(source="deal.title", read_only=True)

    class Meta:
        model = TechnicalSolution
        fields = [
            "id",
            "deal",
            "deal_title",
            "iteration_count",
            "selected_frameworks",
            "architecture_pattern",
            "deployment_model",
            "created_at",
        ]


class TechnicalSolutionDetailSerializer(serializers.ModelSerializer):
    """Full serializer that returns data in the ArchitectureResult shape
    expected by the frontend (nested technical_solution / technical_volume)."""
    deal_title = serializers.CharField(source="deal.title", read_only=True)
    deal_id = serializers.UUIDField(source="deal.id", read_only=True)
    opportunity_id = serializers.SerializerMethodField()
    technical_solution = serializers.SerializerMethodField()

    class Meta:
        model = TechnicalSolution
        fields = [
            "id",
            "deal",
            "deal_id",
            "deal_title",
            "opportunity_id",
            "iteration_count",
            "selected_frameworks",
            "requirement_analysis",
            "technical_solution",
            "technical_volume",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_opportunity_id(self, obj):
        return str(obj.deal.opportunity_id) if obj.deal.opportunity_id else ""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Wrap flat technical_volume dict into the shape the frontend expects:
        # { sections: {...}, diagram_count: N, word_count: N }
        tv = data.get("technical_volume") or {}
        if isinstance(tv, dict) and "sections" not in tv:
            word_count = sum(len(str(v).split()) for v in tv.values()) if tv else 0
            diagram_count = instance.diagrams.count() if hasattr(instance, "diagrams") else 0
            data["technical_volume"] = {
                "sections": tv,
                "diagram_count": diagram_count,
                "word_count": word_count,
            }
        return data

    def get_technical_solution(self, obj):
        """Nest flat model fields into the technical_solution dict the frontend expects."""
        return {
            "executive_summary": obj.executive_summary or "",
            "architecture_pattern": obj.architecture_pattern or "",
            "core_components": obj.core_components if isinstance(obj.core_components, str) else str(obj.core_components) if obj.core_components else "",
            "integration_approach": (obj.integration_points if isinstance(obj.integration_points, str) else str(obj.integration_points)) if obj.integration_points else "",
            "data_architecture": "",
            "security_architecture": obj.security_architecture or "",
            "infrastructure": "",
            "ai_ml_components": "",
            "devops_cicd": "",
            "monitoring_observability": "",
            "disaster_recovery": "",
            "scalability": obj.scalability_approach or "",
            "compliance_implementation": "",
            "innovation_differentiators": "",
            "risk_mitigation": "",
            "loe_estimates": "",
            "technology_stack": obj.technology_stack if isinstance(obj.technology_stack, str) else str(obj.technology_stack) if obj.technology_stack else "",
        }


class ArchitectureDiagramSerializer(serializers.ModelSerializer):
    """Serializer for architecture diagrams."""
    diagram_type_display = serializers.CharField(
        source="get_diagram_type_display", read_only=True
    )

    class Meta:
        model = ArchitectureDiagram
        fields = [
            "id",
            "technical_solution",
            "title",
            "diagram_type",
            "diagram_type_display",
            "mermaid_code",
            "d2_code",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SolutionValidationReportSerializer(serializers.ModelSerializer):
    """Serializer for solution validation reports."""
    overall_quality_display = serializers.CharField(
        source="get_overall_quality_display", read_only=True
    )

    class Meta:
        model = SolutionValidationReport
        fields = [
            "id",
            "technical_solution",
            "overall_quality",
            "overall_quality_display",
            "score",
            "passed",
            "issues",
            "suggestions",
            "compliance_gaps",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
