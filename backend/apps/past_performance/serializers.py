from rest_framework import serializers

from .models import PastPerformance, PastPerformanceMatch


class PastPerformanceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    class Meta:
        model = PastPerformance
        fields = [
            "id",
            "project_name",
            "contract_number",
            "client_agency",
            "naics_codes",
            "domains",
            "start_date",
            "end_date",
            "contract_value",
            "contract_type",
            "performance_rating",
            "cpars_rating",
            "on_time_delivery",
            "within_budget",
            "is_active",
            "created_at",
        ]


class PastPerformanceDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail/create/update views."""

    class Meta:
        model = PastPerformance
        fields = [
            "id",
            "project_name",
            "contract_number",
            "client_agency",
            "client_name",
            "client_email",
            "client_phone",
            "description",
            "relevance_keywords",
            "naics_codes",
            "technologies",
            "domains",
            "start_date",
            "end_date",
            "contract_value",
            "contract_type",
            "performance_rating",
            "cpars_rating",
            "on_time_delivery",
            "within_budget",
            "key_achievements",
            "metrics",
            "narrative",
            "lessons_learned",
            "is_active",
            "last_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PastPerformanceMatchSerializer(serializers.ModelSerializer):
    """Serializer for past performance matches (read-only)."""
    past_performance = PastPerformanceListSerializer(read_only=True)
    opportunity_title = serializers.CharField(
        source="opportunity.title", read_only=True
    )

    class Meta:
        model = PastPerformanceMatch
        fields = [
            "id",
            "opportunity",
            "opportunity_title",
            "past_performance",
            "relevance_score",
            "match_rationale",
            "matched_keywords",
            "created_at",
        ]
        read_only_fields = fields
