from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.teaming.models import TeamingPartnership
from apps.teaming.serializers import TeamingPartnershipSerializer


class TeamingPartnershipViewSet(viewsets.ModelViewSet):
    """Teaming partnerships management."""

    queryset = TeamingPartnership.objects.all()
    serializer_class = TeamingPartnershipSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set owner to current user on creation."""
        serializer.save(owner=self.request.user)
