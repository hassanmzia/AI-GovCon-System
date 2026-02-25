from rest_framework import serializers

from apps.contracts.models import (
    Contract,
    ContractClause,
    ContractTemplate,
    ContractVersion,
)


# ── ContractTemplate ───────────────────────────────────


class ContractTemplateSerializer(serializers.ModelSerializer):
    template_type_display = serializers.CharField(
        source="get_template_type_display", read_only=True
    )

    class Meta:
        model = ContractTemplate
        fields = [
            "id",
            "name",
            "template_type",
            "template_type_display",
            "content",
            "variables",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── ContractClause ─────────────────────────────────────


class ContractClauseSerializer(serializers.ModelSerializer):
    source_display = serializers.CharField(
        source="get_source_display", read_only=True
    )
    risk_level_display = serializers.CharField(
        source="get_risk_level_display", read_only=True
    )

    class Meta:
        model = ContractClause
        fields = [
            "id",
            "clause_number",
            "title",
            "full_text",
            "source",
            "source_display",
            "risk_level",
            "risk_level_display",
            "negotiation_guidance",
            "flow_down_required",
            "is_mandatory",
            "category",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Contract ───────────────────────────────────────────


class ContractListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    contract_type_display = serializers.CharField(
        source="get_contract_type_display", read_only=True
    )

    class Meta:
        model = Contract
        fields = [
            "id",
            "deal",
            "title",
            "contract_number",
            "contract_type",
            "contract_type_display",
            "status",
            "status_display",
            "executed_date",
            "total_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ContractDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer including contract details."""
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    contract_type_display = serializers.CharField(
        source="get_contract_type_display", read_only=True
    )
    version_count = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "deal",
            "template",
            "title",
            "contract_number",
            "contract_type",
            "contract_type_display",
            "status",
            "status_display",
            "total_value",
            "period_of_performance_start",
            "period_of_performance_end",
            "option_years",
            "contracting_officer",
            "contracting_officer_email",
            "cor_name",
            "awarded_date",
            "executed_date",
            "notes",
            "version_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_version_count(self, obj):
        return obj.versions.count()


# ── ContractVersion ────────────────────────────────────


class ContractVersionSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(
        source="changed_by.email", read_only=True
    )

    class Meta:
        model = ContractVersion
        fields = [
            "id",
            "contract",
            "version_number",
            "content",
            "change_summary",
            "changed_by",
            "changed_by_email",
            "redlines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "changed_by", "created_at", "updated_at"]
