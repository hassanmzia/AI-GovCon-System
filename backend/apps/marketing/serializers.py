from rest_framework import serializers

from apps.marketing.models import MarketingCampaign


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
