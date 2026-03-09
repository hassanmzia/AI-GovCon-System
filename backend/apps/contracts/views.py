from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.contracts.models import (
    Contract,
    ContractClause,
    ContractMilestone,
    ContractModification,
    ContractTemplate,
    ContractVersion,
    OptionYear,
)
from apps.contracts.serializers import (
    ContractClauseSerializer,
    ContractDetailSerializer,
    ContractListSerializer,
    ContractMilestoneSerializer,
    ContractModificationSerializer,
    ContractTemplateSerializer,
    ContractVersionSerializer,
    OptionYearSerializer,
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


class ContractMilestoneViewSet(viewsets.ModelViewSet):
    """CRUD for contract milestones and deliverables."""
    queryset = ContractMilestone.objects.select_related("contract", "assigned_to").all()
    serializer_class = ContractMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["contract", "milestone_type", "status"]
    search_fields = ["title", "deliverable_description"]
    ordering_fields = ["due_date", "status", "created_at"]
    ordering = ["due_date"]


class ContractModificationViewSet(viewsets.ModelViewSet):
    """CRUD for contract modifications."""
    queryset = ContractModification.objects.select_related(
        "contract", "requested_by", "approved_by"
    ).all()
    serializer_class = ContractModificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["contract", "modification_type", "status"]
    search_fields = ["modification_number", "description"]
    ordering_fields = ["created_at", "effective_date"]
    ordering = ["-created_at"]


class OptionYearViewSet(viewsets.ModelViewSet):
    """CRUD for contract option years."""
    queryset = OptionYear.objects.select_related("contract").all()
    serializer_class = OptionYearSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["contract", "status"]
    ordering_fields = ["year_number", "decision_deadline"]
    ordering = ["year_number"]
