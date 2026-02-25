from rest_framework import serializers

from apps.research.models import (
    CompetitorProfile,
    MarketIntelligence,
    ResearchProject,
    ResearchSource,
)


class ResearchSourceSerializer(serializers.ModelSerializer):
    """Serializer for individual research sources."""

    source_type_display = serializers.CharField(
        source="get_source_type_display", read_only=True
    )

    class Meta:
        model = ResearchSource
        fields = [
            "id",
            "project",
            "url",
            "title",
            "source_type",
            "source_type_display",
            "content",
            "relevance_score",
            "extracted_data",
            "fetched_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ResearchProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing research projects."""

    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    research_type_display = serializers.CharField(
        source="get_research_type_display", read_only=True
    )
    source_count = serializers.SerializerMethodField()

    class Meta:
        model = ResearchProject
        fields = [
            "id",
            "deal",
            "title",
            "status",
            "status_display",
            "research_type",
            "research_type_display",
            "requested_by",
            "source_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_source_count(self, obj):
        return obj.research_sources.count()


class ResearchProjectDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for research projects."""

    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    research_type_display = serializers.CharField(
        source="get_research_type_display", read_only=True
    )
    research_sources = ResearchSourceSerializer(many=True, read_only=True)

    class Meta:
        model = ResearchProject
        fields = [
            "id",
            "deal",
            "title",
            "description",
            "status",
            "status_display",
            "research_type",
            "research_type_display",
            "parameters",
            "findings",
            "executive_summary",
            "sources",
            "ai_agent_trace_id",
            "requested_by",
            "research_sources",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "findings",
            "executive_summary",
            "sources",
            "ai_agent_trace_id",
            "created_at",
            "updated_at",
        ]


class CompetitorProfileSerializer(serializers.ModelSerializer):
    """Serializer for competitor profiles."""

    class Meta:
        model = CompetitorProfile
        fields = [
            "id",
            "name",
            "cage_code",
            "duns_number",
            "website",
            "naics_codes",
            "contract_vehicles",
            "key_personnel",
            "revenue_range",
            "employee_count",
            "past_performance_summary",
            "strengths",
            "weaknesses",
            "win_rate",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MarketIntelligenceSerializer(serializers.ModelSerializer):
    """Serializer for market intelligence entries."""

    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    class Meta:
        model = MarketIntelligence
        fields = [
            "id",
            "category",
            "category_display",
            "title",
            "summary",
            "detail",
            "impact_assessment",
            "affected_naics",
            "affected_agencies",
            "source_url",
            "published_date",
            "relevance_window_days",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
