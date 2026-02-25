from rest_framework import serializers

from apps.teaming.models import TeamingPartnership


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
            "partner_contact_name",
            "partner_contact_email",
            "partner_contact_phone",
            "relationship_type",
            "status",
            "description",
            "responsibilities",
            "revenue_share_percentage",
            "signed_agreement",
            "agreement_date",
            "start_date",
            "end_date",
            "terms_and_conditions",
            "owner",
            "owner_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
