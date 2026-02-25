from rest_framework import serializers

from .models import CompanyStrategy, PortfolioSnapshot, StrategicGoal, StrategicScore


class StrategicGoalSerializer(serializers.ModelSerializer):
    progress_pct = serializers.SerializerMethodField()

    class Meta:
        model = StrategicGoal
        fields = [
            "id",
            "strategy",
            "name",
            "category",
            "metric",
            "current_value",
            "target_value",
            "deadline",
            "weight",
            "status",
            "notes",
            "progress_pct",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_progress_pct(self, obj) -> float:
        if obj.target_value == 0:
            return 0.0
        return round((obj.current_value / obj.target_value) * 100, 1)


class CompanyStrategyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    goal_count = serializers.SerializerMethodField()

    class Meta:
        model = CompanyStrategy
        fields = [
            "id",
            "version",
            "effective_date",
            "is_active",
            "mission_statement",
            "target_revenue",
            "target_win_rate",
            "target_margin",
            "max_concurrent_proposals",
            "goal_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_goal_count(self, obj) -> int:
        return obj.goals.count()


class CompanyStrategyDetailSerializer(serializers.ModelSerializer):
    """Full serializer with nested goals for detail/create/update views."""
    goals = StrategicGoalSerializer(many=True, read_only=True)

    class Meta:
        model = CompanyStrategy
        fields = [
            "id",
            "version",
            "effective_date",
            "is_active",
            # Strategic positioning
            "mission_statement",
            "vision_3_year",
            "target_revenue",
            "target_win_rate",
            "target_margin",
            # Market focus
            "target_agencies",
            "target_domains",
            "target_naics_codes",
            "growth_markets",
            "mature_markets",
            "exit_markets",
            # Competitive strategy
            "differentiators",
            "win_themes",
            "pricing_philosophy",
            "teaming_strategy",
            # Capacity constraints
            "max_concurrent_proposals",
            "available_key_personnel",
            "clearance_capacity",
            # Nested
            "goals",
            # Timestamps
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PortfolioSnapshotSerializer(serializers.ModelSerializer):
    strategy_version = serializers.IntegerField(
        source="strategy.version", read_only=True, default=None
    )

    class Meta:
        model = PortfolioSnapshot
        fields = [
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
            "strategy_version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class StrategicScoreSerializer(serializers.ModelSerializer):
    opportunity_title = serializers.CharField(
        source="opportunity.title", read_only=True
    )
    opportunity_notice_id = serializers.CharField(
        source="opportunity.notice_id", read_only=True
    )

    class Meta:
        model = StrategicScore
        fields = [
            "id",
            "opportunity",
            "opportunity_title",
            "opportunity_notice_id",
            "strategy",
            # Overall
            "strategic_score",
            "composite_score",
            # Factor scores
            "agency_alignment",
            "domain_alignment",
            "growth_market_bonus",
            "portfolio_balance",
            "revenue_contribution",
            "capacity_fit",
            "relationship_value",
            "competitive_positioning",
            # Recommendation
            "bid_recommendation",
            "strategic_rationale",
            "opportunity_cost",
            "portfolio_impact",
            "resource_impact",
            # Timestamps
            "scored_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
