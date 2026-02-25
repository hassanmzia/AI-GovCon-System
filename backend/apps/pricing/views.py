from django.utils import timezone
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.pricing.models import (
    ConsultantProfile,
    CostModel,
    LOEEstimate,
    PricingApproval,
    PricingScenario,
    RateCard,
)
from apps.pricing.serializers import (
    ConsultantProfileSerializer,
    CostModelSerializer,
    LOEEstimateSerializer,
    PricingApprovalSerializer,
    PricingScenarioSerializer,
    RateCardSerializer,
)


class RateCardViewSet(viewsets.ModelViewSet):
    """CRUD for labor-category rate cards."""
    queryset = RateCard.objects.all()
    serializer_class = RateCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "clearance_required"]
    search_fields = ["labor_category", "gsa_equivalent", "gsa_sin"]
    ordering_fields = ["labor_category", "internal_rate", "created_at"]


class ConsultantProfileViewSet(viewsets.ModelViewSet):
    """CRUD for consultant profiles used in staffing plans."""
    queryset = ConsultantProfile.objects.select_related("labor_category").all()
    serializer_class = ConsultantProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_available", "is_key_personnel", "clearance_level"]
    search_fields = ["name", "bio", "skills"]
    ordering_fields = ["name", "hourly_cost", "years_experience", "created_at"]


class LOEEstimateViewSet(viewsets.ModelViewSet):
    """List and detail views for Level of Effort estimates."""
    queryset = LOEEstimate.objects.select_related("deal").all()
    serializer_class = LOEEstimateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["deal", "estimation_method"]
    ordering_fields = ["version", "total_hours", "created_at"]


class CostModelViewSet(viewsets.ModelViewSet):
    """List and detail views for cost models."""
    queryset = CostModel.objects.select_related("deal", "loe").all()
    serializer_class = CostModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["deal"]
    ordering_fields = ["version", "total_cost", "created_at"]


class PricingScenarioViewSet(viewsets.ModelViewSet):
    """CRUD for pricing scenarios with expected-value analysis."""
    queryset = PricingScenario.objects.select_related("deal", "cost_model").all()
    serializer_class = PricingScenarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["deal", "strategy_type", "is_recommended"]
    search_fields = ["name", "rationale"]
    ordering_fields = ["expected_value", "margin_pct", "total_price", "created_at"]


class PricingApprovalViewSet(viewsets.ModelViewSet):
    """CRUD for pricing approval HITL gates."""
    queryset = PricingApproval.objects.select_related(
        "deal", "scenario", "requested_by", "approved_by"
    ).all()
    serializer_class = PricingApprovalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["deal", "status"]
    ordering_fields = ["status", "created_at"]

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        new_status = serializer.validated_data.get("status", instance.status)
        extra = {}
        if new_status in ("approved", "rejected") and instance.status == "pending":
            extra["approved_by"] = self.request.user
            extra["decided_at"] = timezone.now()
        serializer.save(**extra)
