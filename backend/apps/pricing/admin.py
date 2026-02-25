from django.contrib import admin

from apps.pricing.models import (
    ConsultantProfile,
    CostModel,
    LOEEstimate,
    PricingApproval,
    PricingIntelligence,
    PricingScenario,
    RateCard,
)


@admin.register(RateCard)
class RateCardAdmin(admin.ModelAdmin):
    list_display = [
        "labor_category",
        "internal_rate",
        "gsa_rate",
        "proposed_rate",
        "is_active",
        "effective_date",
    ]
    list_filter = ["is_active", "clearance_required"]
    search_fields = ["labor_category", "gsa_equivalent", "gsa_sin"]


@admin.register(ConsultantProfile)
class ConsultantProfileAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "labor_category",
        "hourly_cost",
        "clearance_level",
        "years_experience",
        "is_available",
        "is_key_personnel",
    ]
    list_filter = ["is_available", "is_key_personnel", "clearance_level"]
    search_fields = ["name", "bio"]


@admin.register(LOEEstimate)
class LOEEstimateAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "version",
        "estimation_method",
        "total_hours",
        "total_ftes",
        "duration_months",
        "confidence_level",
    ]
    list_filter = ["estimation_method"]
    search_fields = ["deal__title"]


@admin.register(CostModel)
class CostModelAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "version",
        "direct_labor",
        "overhead",
        "ga_expense",
        "total_cost",
    ]
    search_fields = ["deal__title"]


@admin.register(PricingScenario)
class PricingScenarioAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "deal",
        "strategy_type",
        "total_price",
        "margin_pct",
        "probability_of_win",
        "expected_value",
        "is_recommended",
    ]
    list_filter = ["strategy_type", "is_recommended"]
    search_fields = ["name", "deal__title"]


@admin.register(PricingIntelligence)
class PricingIntelligenceAdmin(admin.ModelAdmin):
    list_display = [
        "source",
        "labor_category",
        "agency",
        "rate_low",
        "rate_median",
        "rate_high",
        "data_date",
    ]
    list_filter = ["source"]
    search_fields = ["labor_category", "agency"]


@admin.register(PricingApproval)
class PricingApprovalAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "scenario",
        "requested_by",
        "approved_by",
        "status",
        "decided_at",
    ]
    list_filter = ["status"]
    search_fields = ["deal__title"]
