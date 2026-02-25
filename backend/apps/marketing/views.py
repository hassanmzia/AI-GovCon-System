from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.marketing.models import MarketingCampaign
from apps.marketing.serializers import MarketingCampaignSerializer


class MarketingCampaignViewSet(viewsets.ModelViewSet):
    """Marketing campaigns management."""

    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set owner to current user on creation."""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Filter campaigns by user if not admin."""
        queryset = MarketingCampaign.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(owner=self.request.user)
        return queryset
