from rest_framework import serializers

from .models import (
    CompanyProfile,
    DailyDigest,
    Opportunity,
    OpportunityScore,
    OpportunitySource,
)


class OpportunitySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunitySource
        fields = [
            "id",
            "name",
            "source_type",
            "base_url",
            "is_active",
            "scan_frequency_hours",
            "last_scan_at",
            "last_scan_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OpportunityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityScore
        fields = [
            "id",
            "total_score",
            "recommendation",
            "naics_match",
            "psc_match",
            "keyword_overlap",
            "capability_similarity",
            "past_performance_relevance",
            "value_fit",
            "deadline_feasibility",
            "set_aside_match",
            "competition_intensity",
            "risk_factors",
            "score_explanation",
            "ai_rationale",
            "scored_at",
        ]
        read_only_fields = fields


class OpportunityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    source_name = serializers.CharField(source="source.name", read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)
    score = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            "id",
            "notice_id",
            "title",
            "agency",
            "naics_code",
            "set_aside",
            "notice_type",
            "posted_date",
            "response_deadline",
            "days_until_deadline",
            "estimated_value",
            "status",
            "is_active",
            "source_name",
            "source_url",
            "score",
            "place_state",
            "keywords",
        ]

    def get_score(self, obj):
        try:
            score = obj.score
            return {
                "total_score": score.total_score,
                "recommendation": score.recommendation,
            }
        except OpportunityScore.DoesNotExist:
            return None


class OpportunityDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views."""
    source = OpportunitySourceSerializer(read_only=True)
    score = OpportunityScoreSerializer(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)

    class Meta:
        model = Opportunity
        fields = [
            "id",
            "notice_id",
            "source",
            "source_url",
            "title",
            "description",
            "agency",
            "sub_agency",
            "office",
            "notice_type",
            "sol_number",
            "naics_code",
            "naics_description",
            "psc_code",
            "set_aside",
            "classification_code",
            "posted_date",
            "response_deadline",
            "archive_date",
            "days_until_deadline",
            "estimated_value",
            "award_type",
            "place_of_performance",
            "place_city",
            "place_state",
            "status",
            "is_active",
            "incumbent",
            "keywords",
            "attachments",
            "contacts",
            "score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            "id",
            "name",
            "uei_number",
            "cage_code",
            "naics_codes",
            "psc_codes",
            "set_aside_categories",
            "capability_statement",
            "core_competencies",
            "past_performance_summary",
            "key_personnel",
            "certifications",
            "clearance_levels",
            "contract_vehicles",
            "target_agencies",
            "target_value_min",
            "target_value_max",
            "is_primary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DailyDigestListSerializer(serializers.ModelSerializer):
    """Lightweight digest serializer for list views."""
    class Meta:
        model = DailyDigest
        fields = [
            "id",
            "date",
            "total_scanned",
            "total_new",
            "total_scored",
            "is_sent",
            "created_at",
        ]
        read_only_fields = fields


class DailyDigestDetailSerializer(serializers.ModelSerializer):
    """Full digest serializer with nested opportunities."""
    opportunities = OpportunityListSerializer(many=True, read_only=True)

    class Meta:
        model = DailyDigest
        fields = [
            "id",
            "date",
            "opportunities",
            "total_scanned",
            "total_new",
            "total_scored",
            "summary",
            "is_sent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
