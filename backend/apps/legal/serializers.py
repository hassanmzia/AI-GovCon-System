from rest_framework import serializers

from apps.legal.models import (
    ComplianceAssessment,
    ContractReviewNote,
    FARClause,
    LegalRisk,
    RegulatoryRequirement,
)


# ── FAR Clause ──────────────────────────────────────────


class FARClauseSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = FARClause
        fields = [
            "id",
            "clause_number",
            "title",
            "full_text",
            "category",
            "category_display",
            "is_mandatory",
            "applicability_threshold",
            "related_dfars",
            "plain_language_summary",
            "compliance_checklist",
            "last_updated",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Regulatory Requirement ──────────────────────────────


class RegulatoryRequirementSerializer(serializers.ModelSerializer):
    regulation_source_display = serializers.CharField(
        source="get_regulation_source_display", read_only=True
    )

    class Meta:
        model = RegulatoryRequirement
        fields = [
            "id",
            "regulation_source",
            "regulation_source_display",
            "reference_number",
            "title",
            "description",
            "compliance_criteria",
            "applicable_contract_types",
            "applicable_set_asides",
            "penalty_description",
            "effective_date",
            "expiration_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Compliance Assessment ───────────────────────────────


class ComplianceAssessmentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    overall_risk_level_display = serializers.CharField(
        source="get_overall_risk_level_display", read_only=True
    )

    class Meta:
        model = ComplianceAssessment
        fields = [
            "id",
            "deal",
            "assessed_by",
            "status",
            "status_display",
            "far_compliance_score",
            "dfars_compliance_score",
            "overall_risk_level",
            "overall_risk_level_display",
            "findings",
            "recommendations",
            "clauses_reviewed",
            "non_compliant_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Legal Risk ──────────────────────────────────────────


class LegalRiskSerializer(serializers.ModelSerializer):
    risk_type_display = serializers.CharField(source="get_risk_type_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    probability_display = serializers.CharField(
        source="get_probability_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LegalRisk
        fields = [
            "id",
            "deal",
            "risk_type",
            "risk_type_display",
            "title",
            "description",
            "severity",
            "severity_display",
            "probability",
            "probability_display",
            "mitigation_strategy",
            "status",
            "status_display",
            "identified_by",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Contract Review Note ────────────────────────────────


class ContractReviewNoteSerializer(serializers.ModelSerializer):
    note_type_display = serializers.CharField(
        source="get_note_type_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ContractReviewNote
        fields = [
            "id",
            "deal",
            "reviewer",
            "section",
            "note_text",
            "note_type",
            "note_type_display",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
