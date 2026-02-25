from rest_framework import serializers

from apps.security_compliance.models import (
    ComplianceRequirement,
    SecurityComplianceReport,
    SecurityControl,
    SecurityControlMapping,
    SecurityFramework,
)


# ── SecurityFramework ───────────────────────────────────


class SecurityFrameworkSerializer(serializers.ModelSerializer):
    control_count = serializers.SerializerMethodField()

    class Meta:
        model = SecurityFramework
        fields = [
            "id",
            "name",
            "version",
            "description",
            "control_families",
            "is_active",
            "control_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_control_count(self, obj):
        return obj.controls.count()


# ── SecurityControl ─────────────────────────────────────


class SecurityControlSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(
        source="framework.name", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    baseline_impact_display = serializers.CharField(
        source="get_baseline_impact_display", read_only=True
    )

    class Meta:
        model = SecurityControl
        fields = [
            "id",
            "framework",
            "framework_name",
            "control_id",
            "title",
            "description",
            "family",
            "priority",
            "priority_display",
            "baseline_impact",
            "baseline_impact_display",
            "implementation_guidance",
            "assessment_procedures",
            "related_controls",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── SecurityControlMapping ──────────────────────────────


class SecurityControlMappingSerializer(serializers.ModelSerializer):
    control_detail = SecurityControlSerializer(
        source="control", read_only=True
    )
    implementation_status_display = serializers.CharField(
        source="get_implementation_status_display", read_only=True
    )

    class Meta:
        model = SecurityControlMapping
        fields = [
            "id",
            "deal",
            "control",
            "control_detail",
            "implementation_status",
            "implementation_status_display",
            "responsible_party",
            "implementation_description",
            "evidence_references",
            "assessed_by",
            "assessment_date",
            "gap_description",
            "remediation_plan",
            "target_completion",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── SecurityComplianceReport ────────────────────────────


class SecurityComplianceReportSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(
        source="framework.name", read_only=True
    )
    report_type_display = serializers.CharField(
        source="get_report_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = SecurityComplianceReport
        fields = [
            "id",
            "deal",
            "framework",
            "framework_name",
            "report_type",
            "report_type_display",
            "status",
            "status_display",
            "overall_compliance_pct",
            "controls_implemented",
            "controls_partial",
            "controls_planned",
            "controls_na",
            "gaps",
            "findings",
            "poam_items",
            "generated_by",
            "approved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── ComplianceRequirement ───────────────────────────────


class ComplianceRequirementSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    current_status_display = serializers.CharField(
        source="get_current_status_display", read_only=True
    )

    class Meta:
        model = ComplianceRequirement
        fields = [
            "id",
            "deal",
            "source_document",
            "requirement_text",
            "category",
            "category_display",
            "priority",
            "priority_display",
            "current_status",
            "current_status_display",
            "gap_description",
            "remediation_cost_estimate",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Action serializers ──────────────────────────────────


class ComplianceMappingRequestSerializer(serializers.Serializer):
    """Input serializer for the map-requirements action."""

    framework_id = serializers.UUIDField()


class GapAnalysisRequestSerializer(serializers.Serializer):
    """Input serializer for the assess-gaps action."""

    deal_id = serializers.UUIDField(required=False, help_text="Defaults to the deal in the URL.")


class POAMRequestSerializer(serializers.Serializer):
    """Input serializer for the generate-poam action."""

    deal_id = serializers.UUIDField(required=False, help_text="Defaults to the deal in the URL.")
