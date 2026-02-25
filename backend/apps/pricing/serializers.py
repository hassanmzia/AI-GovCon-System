from rest_framework import serializers

from apps.pricing.models import (
    ConsultantProfile,
    CostModel,
    LOEEstimate,
    PricingApproval,
    PricingIntelligence,
    PricingScenario,
    RateCard,
)


# ── RateCard ────────────────────────────────────────────


class RateCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateCard
        fields = [
            "id",
            "labor_category",
            "gsa_equivalent",
            "gsa_sin",
            "internal_rate",
            "gsa_rate",
            "proposed_rate",
            "market_low",
            "market_median",
            "market_high",
            "education_requirement",
            "experience_years",
            "clearance_required",
            "is_active",
            "effective_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── ConsultantProfile ──────────────────────────────────


class ConsultantProfileSerializer(serializers.ModelSerializer):
    labor_category_name = serializers.CharField(
        source="labor_category.labor_category", read_only=True
    )

    class Meta:
        model = ConsultantProfile
        fields = [
            "id",
            "user",
            "name",
            "labor_category",
            "labor_category_name",
            "hourly_cost",
            "skills",
            "certifications",
            "clearance_level",
            "years_experience",
            "availability_date",
            "utilization_pct",
            "is_key_personnel",
            "is_available",
            "resume_file",
            "bio",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── LOEEstimate ────────────────────────────────────────


class LOEEstimateSerializer(serializers.ModelSerializer):
    estimation_method_display = serializers.CharField(
        source="get_estimation_method_display", read_only=True
    )

    class Meta:
        model = LOEEstimate
        fields = [
            "id",
            "deal",
            "version",
            "wbs_elements",
            "total_hours",
            "total_ftes",
            "duration_months",
            "staffing_plan",
            "key_personnel",
            "estimation_method",
            "estimation_method_display",
            "confidence_level",
            "assumptions",
            "risks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── CostModel ──────────────────────────────────────────


class CostModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostModel
        fields = [
            "id",
            "deal",
            "loe",
            "version",
            "direct_labor",
            "fringe_benefits",
            "overhead",
            "odcs",
            "subcontractor_costs",
            "travel",
            "materials",
            "ga_expense",
            "total_cost",
            "fringe_rate",
            "overhead_rate",
            "ga_rate",
            "labor_detail",
            "odc_detail",
            "travel_detail",
            "sub_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── PricingScenario ────────────────────────────────────


class PricingScenarioSerializer(serializers.ModelSerializer):
    strategy_type_display = serializers.CharField(
        source="get_strategy_type_display", read_only=True
    )

    class Meta:
        model = PricingScenario
        fields = [
            "id",
            "deal",
            "cost_model",
            "name",
            "strategy_type",
            "strategy_type_display",
            "total_price",
            "profit",
            "margin_pct",
            "probability_of_win",
            "expected_value",
            "competitive_position",
            "sensitivity_data",
            "is_recommended",
            "rationale",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── PricingIntelligence ────────────────────────────────


class PricingIntelligenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingIntelligence
        fields = [
            "id",
            "source",
            "labor_category",
            "agency",
            "rate_low",
            "rate_median",
            "rate_high",
            "data_date",
            "raw_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── PricingApproval ────────────────────────────────────


class PricingApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingApproval
        fields = [
            "id",
            "deal",
            "scenario",
            "requested_by",
            "approved_by",
            "status",
            "notes",
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
