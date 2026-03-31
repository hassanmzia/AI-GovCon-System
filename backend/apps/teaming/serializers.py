from rest_framework import serializers

from apps.teaming.models import TeamingPartnership, TeamingPartner, TeamingAgreement


class TeamingPartnershipSerializer(serializers.ModelSerializer):
    deal_name = serializers.CharField(source="deal.title", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = TeamingPartnership
        fields = [
            "id",
            "deal",
            "deal_name",
            "partner_company",
            "partner",
            "partner_contact_name",
            "partner_contact_email",
            "partner_contact_phone",
            "relationship_type",
            "status",
            "description",
            "responsibilities",
            "revenue_share_percentage",
            "percentage_of_work",
            "signed_agreement",
            "agreement_date",
            "start_date",
            "end_date",
            "terms_and_conditions",
            "partner_naics_codes",
            "partner_certifications",
            "partner_clearance_level",
            "partner_past_performance",
            "partner_key_personnel",
            "disclosure_sections",
            "exclusivity",
            "ip_ownership",
            "dispute_resolution",
            "owner",
            "owner_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TeamingPartnerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamingPartner
        fields = [
            "id", "name", "uei", "cage_code", "naics_codes", "capabilities",
            "sb_certifications", "is_small_business", "clearance_level",
            "performance_history", "reliability_score", "risk_level",
            "past_revenue", "employee_count", "primary_agencies",
            "headquarters", "contract_vehicles", "is_active",
            "is_channel_partner", "co_sell_opportunities", "co_sell_wins",
            "mentor_protege_role", "tags", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TeamingPartnerDetailSerializer(TeamingPartnerListSerializer):
    partnerships_count = serializers.SerializerMethodField()

    class Meta(TeamingPartnerListSerializer.Meta):
        fields = TeamingPartnerListSerializer.Meta.fields + [
            "duns_number", "labor_categories", "has_cpars_issues",
            "website", "primary_contact_name", "primary_contact_email",
            "primary_contact_phone", "notes",
            "referral_fee_pct", "mentor_protege_program",
            "mentor_protege_start", "mentor_protege_end",
            "partnerships_count", "updated_at",
        ]

    def get_partnerships_count(self, obj):
        return obj.partnerships.count()


class TeamingAgreementSerializer(serializers.ModelSerializer):
    partnership_name = serializers.CharField(
        source="partnership.partner_company", read_only=True
    )
    deal_name = serializers.CharField(
        source="partnership.deal.title", read_only=True
    )

    class Meta:
        model = TeamingAgreement
        fields = [
            "id", "partnership", "partnership_name", "deal_name",
            "agreement_type", "status", "title",
            "document", "document_text",
            "sent_date", "signed_date", "effective_date", "expiry_date",
            "exclusivity", "work_scope", "work_share_pct", "ip_ownership",
            "our_signatory", "partner_signatory", "outcome",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
