import logging
from datetime import date
from decimal import Decimal

from celery import shared_task

logger = logging.getLogger(__name__)

ACTIVE_STAGES = [
    "intake", "qualify", "bid_no_bid", "capture_plan",
    "proposal_dev", "red_team", "final_review", "submit",
    "post_submit", "award_pending", "contract_setup", "delivery",
]


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def compute_daily_kpi_snapshot(self):
    """
    Compute and persist today's KPI snapshot.
    Should be scheduled via Celery Beat once daily at midnight.
    """
    from django.db.models import Sum
    from apps.analytics.models import KPISnapshot
    from apps.deals.models import Deal, StageApproval
    from apps.proposals.models import Proposal
    from apps.opportunities.models import Opportunity

    today = date.today()

    if KPISnapshot.objects.filter(date=today).exists():
        logger.info("KPI snapshot for %s already exists — skipping", today)
        return {"date": str(today), "status": "already_exists"}

    try:
        active_deals = Deal.objects.filter(stage__in=ACTIVE_STAGES)
        pipeline_value = active_deals.aggregate(total=Sum("estimated_value"))["total"] or Decimal("0")
        closed_won = Deal.objects.filter(stage="closed_won").count()
        closed_lost = Deal.objects.filter(stage="closed_lost").count()
        closed_total = closed_won + closed_lost
        win_rate = round((closed_won / closed_total) * 100, 1) if closed_total else None

        stage_dist = {stage: Deal.objects.filter(stage=stage).count() for stage in ACTIVE_STAGES}

        proposal_qs = Proposal.objects.all()
        proposal_dist = {}
        for p in proposal_qs.values("status"):
            proposal_dist[p["status"]] = proposal_dist.get(p["status"], 0) + 1

        from datetime import timedelta
        week_ago = date.today() - timedelta(days=7)

        snapshot = KPISnapshot.objects.create(
            date=today,
            active_deals=active_deals.count(),
            pipeline_value=pipeline_value,
            open_proposals=Proposal.objects.exclude(status="submitted").count(),
            win_rate=win_rate,
            closed_won=closed_won,
            closed_lost=closed_lost,
            total_opportunities=Opportunity.objects.filter(is_active=True).count(),
            pending_approvals=StageApproval.objects.filter(status="pending").count(),
            new_deals_this_week=Deal.objects.filter(created_at__date__gte=week_ago).count(),
            stage_distribution=stage_dist,
            proposal_distribution=proposal_dist,
        )

        logger.info("KPI snapshot created for %s: pipeline=$%s, active_deals=%d",
                    today, pipeline_value, active_deals.count())
        return {"date": str(today), "snapshot_id": str(snapshot.id)}

    except Exception as exc:
        logger.error("compute_daily_kpi_snapshot failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def record_deal_velocity(self, deal_id: str, stage: str, action: str):
    """
    Record when a deal enters or exits a stage for velocity tracking.
    action: 'enter' | 'exit'
    """
    from django.utils import timezone
    from apps.analytics.models import DealVelocityMetric
    from apps.deals.models import Deal

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("record_deal_velocity: deal %s not found", deal_id)
        return

    now = timezone.now()

    if action == "enter":
        DealVelocityMetric.objects.get_or_create(
            deal=deal,
            stage=stage,
            defaults={"entered_at": now},
        )
    elif action == "exit":
        metric = DealVelocityMetric.objects.filter(deal=deal, stage=stage, exited_at__isnull=True).first()
        if metric:
            metric.exited_at = now
            delta = (now - metric.entered_at).total_seconds() / 86400
            metric.days_in_stage = round(delta, 2)
            metric.save(update_fields=["exited_at", "days_in_stage", "updated_at"])

    logger.info("Deal %s velocity recorded: stage=%s action=%s", deal_id, stage, action)
    return {"deal_id": deal_id, "stage": stage, "action": action}


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def analyze_win_loss(self, deal_id: str):
    """
    Run AI win/loss analysis for a recently closed deal and persist results.
    """
    from apps.analytics.models import WinLossAnalysis
    from apps.deals.models import Deal

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("analyze_win_loss: deal %s not found", deal_id)
        return

    if deal.stage not in ("closed_won", "closed_lost", "no_bid"):
        logger.warning("analyze_win_loss: deal %s is not closed (stage=%s)", deal_id, deal.stage)
        return

    outcome_map = {"closed_won": "won", "closed_lost": "lost", "no_bid": "no_bid"}
    outcome = outcome_map[deal.stage]

    WinLossAnalysis.objects.get_or_create(
        deal=deal,
        defaults={
            "outcome": outcome,
            "close_date": deal.updated_at.date(),
            "final_value": deal.estimated_value,
            "lessons_learned": "",
            "win_themes": deal.win_themes if hasattr(deal, "win_themes") else [],
        },
    )

    logger.info("Win/loss record created for deal %s: %s", deal_id, outcome)
    return {"deal_id": deal_id, "outcome": outcome}
