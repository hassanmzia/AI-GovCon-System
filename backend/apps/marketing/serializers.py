from rest_framework import serializers

from apps.marketing.models import CapabilityStatement, MarketingCampaign


class MarketingCampaignSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = MarketingCampaign
        fields = [
            "id",
            "name",
            "description",
            "channel",
            "status",
            "target_audience",
            "start_date",
            "end_date",
            "budget",
            "owner",
            "owner_username",
            "goals",
            "metrics",
            "related_deals",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CapabilityStatementSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company_profile.name", read_only=True)

    class Meta:
        model = CapabilityStatement
        fields = [
            "id",
            "company_profile",
            "company_name",
            "title",
            "version",
            "is_primary",
            "company_overview",
            "core_competencies",
            "differentiators",
            "past_performance_highlights",
            "duns_number",
            "uei_number",
            "cage_code",
            "naics_codes",
            "psc_codes",
            "certifications",
            "contract_vehicles",
            "contact_name",
            "contact_title",
            "contact_email",
            "contact_phone",
            "website",
            "target_agency",
            "target_naics",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
