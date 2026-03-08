from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.marketing.models import CapabilityStatement, MarketingCampaign
from apps.marketing.serializers import CapabilityStatementSerializer, MarketingCampaignSerializer


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


class CapabilityStatementViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for capability statements."""
    serializer_class = CapabilityStatementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "company_profile": ["exact"],
        "is_primary": ["exact"],
        "target_agency": ["exact", "icontains"],
    }
    search_fields = ["title", "company_overview", "target_agency"]
    ordering_fields = ["version", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return CapabilityStatement.objects.select_related("company_profile").all()
