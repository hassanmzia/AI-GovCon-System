from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsExecutiveOrAbove, ReadOnly

from .models import CompanyStrategy, PortfolioSnapshot, StrategicGoal, StrategicScore
from .serializers import (
    CompanyStrategyDetailSerializer,
    CompanyStrategyListSerializer,
    PortfolioSnapshotSerializer,
    StrategicGoalSerializer,
    StrategicScoreSerializer,
)


class CompanyStrategyViewSet(viewsets.ModelViewSet):
    """
    CRUD for company strategies.

    - List / Retrieve: any authenticated user.
    - Create / Update / Delete: admin or executive only.
    - ``current`` action returns the single active strategy.
    """

    queryset = CompanyStrategy.objects.all()
    permission_classes = [IsAuthenticated, IsExecutiveOrAbove | ReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return CompanyStrategyListSerializer
        return CompanyStrategyDetailSerializer

    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        """Return the currently active strategy."""
        strategy = CompanyStrategy.objects.filter(is_active=True).first()
        if not strategy:
            return Response(
                {"detail": "No active strategy found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CompanyStrategyDetailSerializer(strategy)
        return Response(serializer.data)


class StrategicGoalViewSet(viewsets.ModelViewSet):
    """
    CRUD for strategic goals, nested under a strategy.

    - List / Retrieve: any authenticated user.
    - Create / Update / Delete: admin or executive only.
    """

    serializer_class = StrategicGoalSerializer
    permission_classes = [IsAuthenticated, IsExecutiveOrAbove | ReadOnly]

    def get_queryset(self):
        strategy_pk = self.kwargs.get("strategy_pk")
        if strategy_pk:
            return StrategicGoal.objects.filter(strategy_id=strategy_pk)
        return StrategicGoal.objects.all()

    def perform_create(self, serializer):
        strategy_pk = self.kwargs.get("strategy_pk")
        if strategy_pk:
            serializer.save(strategy_id=strategy_pk)
        else:
            serializer.save()


class PortfolioSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to portfolio snapshots.
    """

    queryset = PortfolioSnapshot.objects.select_related("strategy").all()
    serializer_class = PortfolioSnapshotSerializer
    permission_classes = [IsAuthenticated]


class StrategicScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to strategic scores.

    Supports filtering by ``bid_recommendation`` query parameter.
    """

    serializer_class = StrategicScoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = StrategicScore.objects.select_related(
            "opportunity", "strategy"
        ).all()
        recommendation = self.request.query_params.get("recommendation")
        if recommendation:
            qs = qs.filter(bid_recommendation=recommendation)
        return qs
