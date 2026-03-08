from rest_framework import serializers

from .models import (
    CompanyProfile,
    DailyDigest,
    NAICSCode,
    Opportunity,
    OpportunityScore,
    OpportunitySource,
    SAMRegistration,
    SBACertification,
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
            "purchase_category",
            "small_business_set_aside",
            "set_aside_eligible",
            "has_relevant_past_performance",
            "within_size_standard",
            "entry_strategy",
            "entry_strategy_rationale",
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
            "sol_number",
            "naics_code",
            "set_aside",
            "notice_type",
            "posted_date",
            "created_at",
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
                "purchase_category": score.purchase_category,
                "entry_strategy": score.entry_strategy,
            }
        except OpportunityScore.DoesNotExist:
            return None


class OpportunityDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views."""
    source = OpportunitySourceSerializer(read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)
    score = OpportunityScoreSerializer(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)

    class Meta:
        model = Opportunity
        fields = [
            "id",
            "notice_id",
            "source",
            "source_name",
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
    sam_registration = serializers.SerializerMethodField()
    sba_certifications = serializers.SerializerMethodField()

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
            "search_keywords",
            "sam_registration",
            "sba_certifications",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_sam_registration(self, obj):
        try:
            reg = obj.sam_registration
            return SAMRegistrationSerializer(reg).data
        except SAMRegistration.DoesNotExist:
            return None

    def get_sba_certifications(self, obj):
        certs = obj.sba_certifications.all()
        return SBACertificationSerializer(certs, many=True).data


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


# ── SAM Registration ─────────────────────────────────────────────────────────

class SAMRegistrationSerializer(serializers.ModelSerializer):
    validation_checklist_score = serializers.FloatField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)

    class Meta:
        model = SAMRegistration
        fields = [
            "id",
            "company_profile",
            "legal_business_name",
            "physical_address",
            "mailing_address",
            "taxpayer_id_type",
            "taxpayer_id_last_four",
            "entity_type",
            "ownership_details",
            "banking_verified",
            "registration_status",
            "registration_date",
            "expiration_date",
            "tracking_number",
            "renewal_reminder_sent",
            "name_matches_irs",
            "address_matches_irs",
            "ein_verified",
            "bank_info_business_account",
            "correct_entity_type",
            "naics_codes_added",
            "reps_certs_complete",
            "pocs_added",
            "all_sections_complete",
            "admin_poc",
            "gov_business_poc",
            "validation_checklist_score",
            "is_expiring_soon",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "validation_checklist_score", "is_expiring_soon"]


# ── NAICS Code ────────────────────────────────────────────────────────────────

class NAICSCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NAICSCode
        fields = [
            "id",
            "code",
            "title",
            "description",
            "size_standard",
            "size_standard_type",
            "sector",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ── SBA Certification ────────────────────────────────────────────────────────

class SBACertificationSerializer(serializers.ModelSerializer):
    certification_type_display = serializers.CharField(
        source="get_certification_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = SBACertification
        fields = [
            "id",
            "company_profile",
            "certification_type",
            "certification_type_display",
            "status",
            "status_display",
            "certification_date",
            "expiration_date",
            "certification_number",
            "eligibility_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
