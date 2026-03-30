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
    AIAgentRun,
    AgentPerformanceMetric,
    DealVelocityMetric,
    KPISnapshot,
    RecommendationMetric,
    RevenueForecast,
    WinLossAnalysis,
)
from apps.analytics.serializers import (
    AIAgentRunSerializer,
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


# ---------------------------------------------------------------------------
# AI Agent Run observability endpoints
# ---------------------------------------------------------------------------


class AIAgentRunViewSet(viewsets.ModelViewSet):
    """
    CRUD + list for AI agent execution records.

    GET  /api/analytics/agent-runs/          — list (supports ?limit, ?days, ?agent_name, ?deal_id, ?status)
    POST /api/analytics/agent-runs/          — create (called by the AI orchestrator to record a run)
    GET  /api/analytics/agent-runs/{id}/     — retrieve single run
    PATCH/PUT /api/analytics/agent-runs/{id}/ — update (e.g. mark completed, add cost/tokens)

    Query parameters
    ----------------
    days        : only return runs started within the last N days (default: all)
    limit       : max results per page (uses DRF pagination; max PAGE_SIZE still applies)
    agent_name  : filter by agent_name (exact match)
    deal_id     : filter by deal_id
    status      : filter by status (running | completed | failed | cancelled)
    """

    serializer_class = AIAgentRunSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["agent_name", "deal_id", "status"]

    def get_queryset(self):
        qs = AIAgentRun.objects.select_related("user").order_by("-started_at")

        days = self.request.query_params.get("days")
        if days:
            try:
                cutoff = date.today() - timedelta(days=int(days))
                qs = qs.filter(started_at__date__gte=cutoff)
            except (ValueError, TypeError):
                pass

        # NOTE: Do NOT slice the queryset here with [:limit].
        # DjangoFilterBackend applies AFTER get_queryset(), and Django
        # raises AssertionError if you filter a sliced queryset.
        # Use DRF pagination (?page_size=N) or override list() instead.

        return qs

    def list(self, request, *args, **kwargs):
        """Override list to support ?limit as a hard result cap."""
        response = super().list(request, *args, **kwargs)
        limit = request.query_params.get("limit")
        if limit and response.data and "results" in response.data:
            try:
                response.data["results"] = response.data["results"][: int(limit)]
            except (ValueError, TypeError):
                pass
        return response

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """
        GET /api/analytics/agent-runs/summary/

        Returns aggregate health metrics across all (or recent) agent runs.
        Useful for the AI Command Center overview dashboard.
        """
        days = int(request.query_params.get("days", 7))
        cutoff = date.today() - timedelta(days=days)
        qs = AIAgentRun.objects.filter(started_at__date__gte=cutoff)

        total = qs.count()
        completed = qs.filter(status="completed").count()
        failed = qs.filter(status="failed").count()
        running = qs.filter(status="running").count()

        avg_latency = qs.exclude(latency_ms__isnull=True).aggregate(
            avg=Avg("latency_ms")
        )["avg"]
        total_cost = qs.exclude(cost_usd__isnull=True).aggregate(
            total=Sum("cost_usd")
        )["total"]
        overrides = qs.filter(override=True).count()
        hallucinations = qs.aggregate(total=Sum("hallucination_flags"))["total"] or 0

        by_agent = list(
            qs.values("agent_name")
            .annotate(runs=Count("id"), failures=Count("id", filter=Q(status="failed")))
            .order_by("-runs")[:10]
        )

        return Response({
            "period_days": days,
            "total_runs": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "success_rate": round((completed / total) * 100, 1) if total else None,
            "avg_latency_ms": round(avg_latency, 1) if avg_latency else None,
            "total_cost_usd": str(total_cost) if total_cost else "0",
            "human_overrides": overrides,
            "hallucination_flags": hallucinations,
            "top_agents": by_agent,
        })


class RevenueForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to revenue forecast records.

    GET /api/analytics/forecast/         — list forecasts (most recent forecast_date first)
    GET /api/analytics/forecast/{id}/    — single forecast record

    The latest forecast can be obtained with ?ordering=-forecast_date&limit=1
    or via the /latest/ custom action.
    """

    serializer_class = RevenueForecastSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = RevenueForecast.objects.order_by("-forecast_date", "quarter")
        forecast_date = self.request.query_params.get("forecast_date")
        if forecast_date:
            qs = qs.filter(forecast_date=forecast_date)
        return qs

    @action(detail=False, methods=["get"], url_path="latest")
    def latest(self, request):
        """
        GET /api/analytics/forecast/latest/

        Returns all quarters of the most recently generated forecast.
        """
        latest_date = (
            RevenueForecast.objects.order_by("-forecast_date")
            .values_list("forecast_date", flat=True)
            .first()
        )
        if not latest_date:
            return Response({"detail": "No forecasts available."}, status=status.HTTP_404_NOT_FOUND)

        records = RevenueForecast.objects.filter(forecast_date=latest_date).order_by("quarter")
        serializer = self.get_serializer(records, many=True)
        return Response({"forecast_date": str(latest_date), "quarters": serializer.data})
