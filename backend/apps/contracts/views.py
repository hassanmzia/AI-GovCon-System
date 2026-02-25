from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.contracts.models import (
    Contract,
    ContractClause,
    ContractTemplate,
    ContractVersion,
)
from apps.contracts.serializers import (
    ContractClauseSerializer,
    ContractDetailSerializer,
    ContractListSerializer,
    ContractTemplateSerializer,
    ContractVersionSerializer,
)


class ContractTemplateViewSet(viewsets.ModelViewSet):
    """CRUD for contract templates."""
    queryset = ContractTemplate.objects.all()
    serializer_class = ContractTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["template_type", "is_active"]
    search_fields = ["name", "content"]
    ordering_fields = ["name", "template_type", "created_at"]


class ContractClauseViewSet(viewsets.ModelViewSet):
    """CRUD for FAR/DFARS clause library."""
    queryset = ContractClause.objects.all()
    serializer_class = ContractClauseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["source", "risk_level", "is_mandatory", "flow_down_required", "category"]
    search_fields = ["clause_number", "title", "full_text"]
    ordering_fields = ["clause_number", "risk_level", "created_at"]


class ContractViewSet(viewsets.ModelViewSet):
    """CRUD for contracts linked to deals."""
    queryset = Contract.objects.select_related("deal", "template").all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["deal", "status", "contract_type"]
    search_fields = ["title", "contract_number"]
    ordering_fields = ["title", "status", "total_value", "executed_date", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ContractListSerializer
        return ContractDetailSerializer


class ContractVersionViewSet(viewsets.ModelViewSet):
    """CRUD for contract version history with redlines."""
    queryset = ContractVersion.objects.select_related("contract", "changed_by").all()
    serializer_class = ContractVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["contract"]
    ordering_fields = ["version_number", "created_at"]

    def perform_create(self, serializer):
        serializer.save(changed_by=self.request.user)
