from django.contrib import admin

from .models import CompanyStrategy, PortfolioSnapshot, StrategicGoal, StrategicScore


class StrategicGoalInline(admin.TabularInline):
    model = StrategicGoal
    extra = 0
    fields = (
        "name",
        "category",
        "metric",
        "current_value",
        "target_value",
        "deadline",
        "weight",
        "status",
    )


@admin.register(CompanyStrategy)
class CompanyStrategyAdmin(admin.ModelAdmin):
    list_display = (
        "version",
        "effective_date",
        "is_active",
        "target_revenue",
        "target_win_rate",
        "target_margin",
        "max_concurrent_proposals",
        "created_at",
    )
    list_filter = ("is_active", "effective_date")
    search_fields = ("mission_statement", "vision_3_year")
    ordering = ("-version",)
    inlines = [StrategicGoalInline]
    fieldsets = (
        (None, {
            "fields": ("version", "effective_date", "is_active"),
        }),
        ("Strategic Positioning", {
            "fields": (
                "mission_statement",
                "vision_3_year",
                "target_revenue",
                "target_win_rate",
                "target_margin",
            ),
        }),
        ("Market Focus", {
            "fields": (
                "target_agencies",
                "target_domains",
                "target_naics_codes",
                "growth_markets",
                "mature_markets",
                "exit_markets",
            ),
        }),
        ("Competitive Strategy", {
            "fields": (
                "differentiators",
                "win_themes",
                "pricing_philosophy",
                "teaming_strategy",
            ),
        }),
        ("Capacity Constraints", {
            "fields": (
                "max_concurrent_proposals",
                "available_key_personnel",
                "clearance_capacity",
            ),
        }),
    )


@admin.register(StrategicGoal)
class StrategicGoalAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "strategy",
        "category",
        "metric",
        "current_value",
        "target_value",
        "deadline",
        "weight",
        "status",
    )
    list_filter = ("category", "status", "deadline")
    search_fields = ("name", "metric", "notes")
    ordering = ("-weight", "deadline")


@admin.register(PortfolioSnapshot)
class PortfolioSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "snapshot_date",
        "active_deals",
        "total_pipeline_value",
        "weighted_pipeline",
        "capacity_utilization",
        "strategic_alignment_score",
        "strategy",
    )
    list_filter = ("snapshot_date",)
    ordering = ("-snapshot_date",)
    readonly_fields = (
        "id",
        "snapshot_date",
        "active_deals",
        "total_pipeline_value",
        "weighted_pipeline",
        "deals_by_agency",
        "deals_by_domain",
        "deals_by_stage",
        "deals_by_size",
        "capacity_utilization",
        "concentration_risk",
        "strategic_alignment_score",
        "ai_recommendations",
        "strategy",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StrategicScore)
class StrategicScoreAdmin(admin.ModelAdmin):
    list_display = (
        "opportunity",
        "strategic_score",
        "composite_score",
        "bid_recommendation",
        "scored_at",
    )
    list_filter = ("bid_recommendation", "scored_at")
    search_fields = ("opportunity__title", "opportunity__notice_id", "strategic_rationale")
    ordering = ("-strategic_score",)
    readonly_fields = (
        "id",
        "opportunity",
        "strategy",
        "strategic_score",
        "composite_score",
        "agency_alignment",
        "domain_alignment",
        "growth_market_bonus",
        "portfolio_balance",
        "revenue_contribution",
        "capacity_fit",
        "relationship_value",
        "competitive_positioning",
        "bid_recommendation",
        "strategic_rationale",
        "opportunity_cost",
        "portfolio_impact",
        "resource_impact",
        "scored_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
