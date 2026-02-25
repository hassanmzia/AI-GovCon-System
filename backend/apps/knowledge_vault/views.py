from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.knowledge_vault.models import KnowledgeDocument
from apps.knowledge_vault.serializers import KnowledgeDocumentSerializer


class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    """Knowledge vault documents management."""

    queryset = KnowledgeDocument.objects.all()
    serializer_class = KnowledgeDocumentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set author to current user on creation."""
        serializer.save(author=self.request.user)

    def get_queryset(self):
        """Filter by public documents or documents authored by user."""
        queryset = KnowledgeDocument.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status="approved") & (
                queryset.filter(is_public=True) | queryset.filter(author=self.request.user)
            )
        return queryset
