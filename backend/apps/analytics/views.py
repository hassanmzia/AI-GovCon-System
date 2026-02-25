import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, DecimalField, Q, Sum
from django.db.models.functions import Cast
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import (
    AgentPerformanceMetric,
    DealVelocityMetric,
    KPISnapshot,
    RecommendationMetric,
    RevenueForecast,
    WinLossAnalysis,
)
from apps.analytics.serializers import (
    AgentPerformanceMetricSerializer,
    DealVelocityMetricSerializer,
    KPISnapshotSerializer,
    RecommendationMetricSerializer,
    RevenueForecastSerializer,
    WinLossAnalysisSerializer,
)

logger = logging.getLogger(__name__)

ACTIVE_STAGES = [
    "intake", "qualify", "bid_no_bid", "capture_plan",
    "proposal_dev", "red_team", "final_review", "submit",
    "post_submit", "award_pending", "contract_setup", "delivery",
]


# ---------------------------------------------------------------------------
# ViewSets
# ---------------------------------------------------------------------------


class KPISnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to historical KPI snapshots with date filtering."""

    serializer_class = KPISnapshotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["date"]

    def get_queryset(self):
        qs = KPISnapshot.objects.all()
        days = self.request.query_params.get("days", 90)
        try:
            cutoff = date.today() - timedelta(days=int(days))
            qs = qs.filter(date__gte=cutoff)
        except (ValueError, TypeError):
            pass
        return qs

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Return current live KPI summary computed from the database."""
        from apps.deals.models import Deal
        from apps.proposals.models import Proposal
        from apps.opportunities.models import Opportunity

        active_deals = Deal.objects.filter(stage__in=ACTIVE_STAGES)
        pipeline_value = active_deals.aggregate(
            total=Sum("estimated_value")
        )["total"] or Decimal("0")

        closed_won = Deal.objects.filter(stage="closed_won").count()
        closed_lost = Deal.objects.filter(stage="closed_lost").count()
        closed_total = closed_won + closed_lost
        win_rate = round((closed_won / closed_total) * 100, 1) if closed_total else None

        open_proposals = Proposal.objects.exclude(status="submitted").count()
        total_opportunities = Opportunity.objects.filter(is_active=True).count()

        stage_dist = {
            stage: Deal.objects.filter(stage=stage).count()
            for stage in ACTIVE_STAGES
        }

        from apps.deals.models import Approval
        pending_approvals = Approval.objects.filter(status="pending").count()

        week_ago = date.today() - timedelta(days=7)
        new_deals_week = Deal.objects.filter(created_at__date__gte=week_ago).count()

        return Response({
            "active_deals": active_deals.count(),
            "pipeline_value": str(pipeline_value),
            "open_proposals": open_proposals,
            "win_rate": win_rate,
            "closed_won": closed_won,
            "closed_lost": closed_lost,
            "total_opportunities": total_opportunities,
            "pending_approvals": pending_approvals,
            "new_deals_this_week": new_deals_week,
            "stage_distribution": stage_dist,
        })

    @action(detail=False, methods=["get"], url_path="trends")
    def trends(self, request):
        """Return 30/60/90-day trend data from KPI snapshots."""
        days = int(request.query_params.get("days", 30))
        cutoff = date.today() - timedelta(days=days)
        snapshots = KPISnapshot.objects.filter(date__gte=cutoff).order_by("date")
        serializer = KPISnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)


class DealVelocityMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """Deal stage velocity metrics (read-only)."""

    serializer_class = DealVelocityMetricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["deal", "stage"]

    def get_queryset(self):
        qs = DealVelocityMetric.objects.select_related("deal").all()
        deal_id = self.request.query_params.get("deal")
        if deal_id:
            qs = qs.filter(deal_id=deal_id)
        return qs

    @action(detail=False, methods=["get"], url_path="avg-by-stage")
    def avg_by_stage(self, request):
        """Average days spent per pipeline stage across all deals."""
        data = (
            DealVelocityMetric.objects.exclude(days_in_stage__isnull=True)
            .values("stage")
            .annotate(avg_days=Avg("days_in_stage"), deal_count=Count("deal", distinct=True))
            .order_by("stage")
        )
        return Response(list(data))


class WinLossAnalysisViewSet(viewsets.ModelViewSet):
    """Full CRUD for win/loss analysis on closed deals."""

    serializer_class = WinLossAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["outcome", "competitor_name"]

    def get_queryset(self):
        qs = WinLossAnalysis.objects.select_related("deal").all()
        outcome = self.request.query_params.get("outcome")
        if outcome:
            qs = qs.filter(outcome=outcome)
        return qs

    @action(detail=False, methods=["get"], url_path="aggregate")
    def aggregate(self, request):
        """Aggregate win/loss stats by primary reason, competitor, etc."""
        qs = WinLossAnalysis.objects.all()
        by_outcome = qs.values("outcome").annotate(count=Count("id"))
        by_reason = (
            qs.exclude(primary_loss_reason="")
            .values("primary_loss_reason")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        by_competitor = (
            qs.exclude(competitor_name="")
            .values("competitor_name")
            .annotate(count=Count("id"), avg_price=Avg("competitor_price"))
            .order_by("-count")[:10]
        )
        return Response({
            "by_outcome": list(by_outcome),
            "top_loss_reasons": list(by_reason),
            "top_competitors": list(by_competitor),
        })


class RecommendationMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to recommendation quality metrics."""

    serializer_class = RecommendationMetricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["metric_type", "date"]

    def get_queryset(self):
        qs = RecommendationMetric.objects.all()
        days = self.request.query_params.get("days", 90)
        try:
            cutoff = date.today() - timedelta(days=int(days))
            qs = qs.filter(date__gte=cutoff)
        except (ValueError, TypeError):
            pass
        return qs


class AgentPerformanceMetricViewSet(viewsets.ModelViewSet):
    """AI agent performance tracking."""

    serializer_class = AgentPerformanceMetricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["agent_name", "date"]

    def get_queryset(self):
        qs = AgentPerformanceMetric.objects.all()
        agent = self.request.query_params.get("agent")
        if agent:
            qs = qs.filter(agent_name=agent)
        days = self.request.query_params.get("days", 30)
        try:
            cutoff = date.today() - timedelta(days=int(days))
            qs = qs.filter(date__gte=cutoff)
        except (ValueError, TypeError):
            pass
        return qs

    @action(detail=False, methods=["get"], url_path="leaderboard")
    def leaderboard(self, request):
        """Rank agents by success rate and usage."""
        agents = (
            AgentPerformanceMetric.objects.values("agent_name")
            .annotate(
                total_runs=Sum("total_runs"),
                successful_runs=Sum("successful_runs"),
                total_cost=Sum("total_cost_usd"),
            )
            .order_by("-total_runs")
        )
        result = []
        for a in agents:
            total = a["total_runs"] or 0
            success = a["successful_runs"] or 0
            result.append({
                **a,
                "success_rate": round((success / total) * 100, 1) if total else None,
            })
        return Response(result)


# ---------------------------------------------------------------------------
# Standalone API Views
# ---------------------------------------------------------------------------


class ExecutiveDashboardView(APIView):
    """
    GET /analytics/executive-dashboard/

    Returns a unified executive dashboard payload by calling
    kpi_calculator service functions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.analytics.services.kpi_calculator import (
            compute_executive_summary,
            compute_pipeline_funnel,
            compute_revenue_forecast,
            compute_win_rate_trend,
        )

        months = int(request.query_params.get("months", 12))

        try:
            summary = compute_executive_summary()
            funnel = compute_pipeline_funnel()
            forecast = compute_revenue_forecast()
            win_trend = compute_win_rate_trend(months=months)
        except Exception as exc:
            logger.exception("Executive dashboard computation failed")
            return Response(
                {"error": "Failed to compute dashboard metrics.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            "summary": summary,
            "pipeline_funnel": funnel,
            "revenue_forecast": forecast,
            "win_rate_trend": win_trend,
        })


class PipelineLoadView(APIView):
    """
    GET /analytics/pipeline-load/

    Returns pipeline load analysis from the pipeline_analytics service.
    Falls back to a basic computation if the service is unavailable.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.analytics.services.pipeline_analytics import get_pipeline_load
            data = get_pipeline_load()
        except ImportError:
            # Fallback: compute basic pipeline load from deal counts
            data = self._compute_basic_pipeline_load()
        except Exception as exc:
            logger.exception("Pipeline load computation failed")
            return Response(
                {"error": "Failed to compute pipeline load.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(data)

    @staticmethod
    def _compute_basic_pipeline_load() -> dict:
        """Basic pipeline load calculation when full service is unavailable."""
        from apps.deals.models import Deal

        total_active = Deal.objects.filter(stage__in=ACTIVE_STAGES).count()
        by_stage = {}
        for stage_code in ACTIVE_STAGES:
            by_stage[stage_code] = Deal.objects.filter(stage=stage_code).count()

        # Identify bottlenecks (stages with above-average count)
        avg_count = total_active / len(ACTIVE_STAGES) if ACTIVE_STAGES else 0
        bottlenecks = [
            {"stage": s, "count": c, "ratio": round(c / avg_count, 2) if avg_count else 0}
            for s, c in by_stage.items()
            if c > avg_count and avg_count > 0
        ]

        return {
            "total_active_deals": total_active,
            "by_stage": by_stage,
            "bottlenecks": bottlenecks,
            "avg_per_stage": round(avg_count, 1),
        }
