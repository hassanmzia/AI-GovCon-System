"""
Celery tasks for the policies app.

These tasks are designed to be called either directly (e.g. from views or
signals) or scheduled via Celery Beat for periodic maintenance.
"""
import logging
from decimal import Decimal, InvalidOperation

from django.apps import apps
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional Celery integration — gracefully degrade if Celery is not installed.
# ---------------------------------------------------------------------------
try:
    from celery import shared_task  # type: ignore

    _celery_available = True
except ImportError:  # pragma: no cover
    _celery_available = False

    def shared_task(*args, **kwargs):  # type: ignore
        """Fallback decorator that turns the function into a plain callable."""
        def decorator(func):
            return func
        if args and callable(args[0]):
            return args[0]
        return decorator


# ---------------------------------------------------------------------------
# Helper: run a single policy against a deal (mirrors logic in views.py but
# kept here to avoid circular imports from the tasks layer).
# ---------------------------------------------------------------------------

def _resolve_field(obj, field_path: str):
    parts = field_path.split(".")
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


def _evaluate_rule_simple(rule, deal) -> dict:
    """Lightweight rule evaluator used by background tasks."""
    field_value = _resolve_field(deal, rule.field_path)
    operator = rule.operator
    passed = False

    try:
        if operator in ("gt", "lt", "eq", "gte", "lte"):
            threshold = Decimal(str(rule.threshold_value))
            coerced = Decimal(str(field_value)) if field_value is not None else None
            if coerced is None:
                passed = False
            elif operator == "gt":
                passed = coerced > threshold
            elif operator == "lt":
                passed = coerced < threshold
            elif operator == "eq":
                passed = coerced == threshold
            elif operator == "gte":
                passed = coerced >= threshold
            elif operator == "lte":
                passed = coerced <= threshold

        elif operator == "in":
            passed = field_value in (rule.threshold_json or [])

        elif operator == "not_in":
            passed = field_value not in (rule.threshold_json or [])

        elif operator == "contains":
            container = rule.threshold_json if rule.threshold_json is not None else rule.threshold_value
            passed = container in field_value if field_value else False

    except (InvalidOperation, TypeError, ValueError) as exc:
        logger.warning("Rule %s evaluation error: %s", rule.id, exc)
        passed = False

    return {
        "rule_id": str(rule.id),
        "rule_name": rule.rule_name,
        "passed": passed,
        "is_blocking": rule.is_blocking,
        "message": rule.error_message if (not passed and rule.is_blocking) else (
            rule.warning_message if not passed else ""
        ),
    }


def _run_policy(policy, deal):
    """
    Run all rules of *policy* against *deal* and return a (outcome, triggered_rules,
    recommendations) tuple without persisting anything.
    """
    rules = list(policy.rules.all())
    triggered = []
    outcome = "pass"

    for rule in rules:
        result = _evaluate_rule_simple(rule, deal)
        triggered.append(result)
        if not result["passed"]:
            if result["is_blocking"]:
                outcome = "fail"
            elif outcome != "fail":
                outcome = "warn"

    recommendations = [r["message"] for r in triggered if not r["passed"] and r.get("message")]
    return outcome, triggered, recommendations


# ---------------------------------------------------------------------------
# Task 1: evaluate_deal_policies
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    name="policies.evaluate_deal_policies",
    max_retries=3,
    default_retry_delay=60,
)
def evaluate_deal_policies(self, deal_id: str) -> dict:
    """
    Run ALL active, in-effect policies against a single deal and persist
    a PolicyEvaluation record for each one.

    Args:
        deal_id: Primary key (UUID string) of the deal to evaluate.

    Returns:
        A summary dict with counts of each outcome type.
    """
    from .models import BusinessPolicy, PolicyEvaluation  # noqa: PLC0415

    logger.info("evaluate_deal_policies: starting for deal_id=%s", deal_id)

    Deal = apps.get_model("deals", "Deal")
    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("evaluate_deal_policies: deal %s not found", deal_id)
        return {"error": f"Deal {deal_id} not found"}
    except Exception as exc:
        logger.exception("evaluate_deal_policies: unexpected error fetching deal %s", deal_id)
        raise self.retry(exc=exc)

    today = timezone.now().date()
    policies = (
        BusinessPolicy.objects.filter(is_active=True)
        .prefetch_related("rules")
        .filter(
            Q(effective_date__isnull=True) | Q(effective_date__lte=today)
        )
        .filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
        )
        .order_by("priority")
    )

    counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0}
    evaluations_created = []

    for policy in policies:
        try:
            outcome, triggered, recommendations = _run_policy(policy, deal)
            evaluation = PolicyEvaluation.objects.create(
                policy=policy,
                deal=deal,
                evaluated_at=timezone.now(),
                outcome=outcome,
                triggered_rules=triggered,
                recommendations=recommendations,
            )
            counts[outcome] += 1
            evaluations_created.append(str(evaluation.id))
            logger.debug(
                "evaluate_deal_policies: policy=%s deal=%s outcome=%s",
                policy.name,
                deal_id,
                outcome,
            )
        except Exception as exc:
            logger.exception(
                "evaluate_deal_policies: error running policy %s against deal %s",
                policy.id,
                deal_id,
            )
            counts["skip"] += 1

    summary = {
        "deal_id": str(deal_id),
        "policies_evaluated": len(evaluations_created),
        "outcome_counts": counts,
        "evaluation_ids": evaluations_created,
    }
    logger.info("evaluate_deal_policies: completed for deal_id=%s summary=%s", deal_id, counts)
    return summary


# ---------------------------------------------------------------------------
# Task 2: cleanup_expired_exceptions
# ---------------------------------------------------------------------------

@shared_task(
    name="policies.cleanup_expired_exceptions",
    max_retries=2,
    default_retry_delay=120,
)
def cleanup_expired_exceptions() -> dict:
    """
    Periodic maintenance task (recommended: run every hour via Celery Beat).

    Finds all PolicyException records that:
      - Have status='approved'
      - Have an expires_at value that is now in the past

    and transitions them to status='rejected'.

    Returns:
        A dict with the count of exceptions updated.
    """
    from .models import PolicyException  # noqa: PLC0415

    now = timezone.now()
    expired_qs = PolicyException.objects.filter(
        status="approved",
        expires_at__isnull=False,
        expires_at__lt=now,
    )

    count = expired_qs.count()
    if count == 0:
        logger.info("cleanup_expired_exceptions: no expired exceptions found")
        return {"updated": 0}

    updated = expired_qs.update(status="rejected", updated_at=now)
    logger.info("cleanup_expired_exceptions: marked %d exception(s) as rejected", updated)
    return {"updated": updated}


# ---------------------------------------------------------------------------
# Task 3: evaluate_bid_threshold
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    name="policies.evaluate_bid_threshold",
    max_retries=3,
    default_retry_delay=30,
)
def evaluate_bid_threshold(self, deal_id: str) -> dict:
    """
    Targeted evaluation of all active 'bid_threshold' policies against a deal.

    This task is intended to be triggered immediately when a deal's contract
    value is updated, providing fast feedback without re-running every policy.

    Args:
        deal_id: Primary key (UUID string) of the deal to check.

    Returns:
        A dict summarising threshold checks: pass/warn/fail counts and any
        breach details.
    """
    from .models import BusinessPolicy, PolicyEvaluation  # noqa: PLC0415

    logger.info("evaluate_bid_threshold: starting for deal_id=%s", deal_id)

    Deal = apps.get_model("deals", "Deal")
    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("evaluate_bid_threshold: deal %s not found", deal_id)
        return {"error": f"Deal {deal_id} not found"}
    except Exception as exc:
        logger.exception("evaluate_bid_threshold: error fetching deal %s", deal_id)
        raise self.retry(exc=exc)

    today = timezone.now().date()
    threshold_policies = (
        BusinessPolicy.objects.filter(is_active=True, policy_type="bid_threshold")
        .prefetch_related("rules")
        .filter(
            Q(effective_date__isnull=True) | Q(effective_date__lte=today)
        )
        .filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
        )
        .order_by("priority")
    )

    if not threshold_policies.exists():
        logger.info("evaluate_bid_threshold: no active bid_threshold policies found")
        return {"deal_id": str(deal_id), "policies_evaluated": 0, "outcome_counts": {}}

    counts = {"pass": 0, "warn": 0, "fail": 0}
    breaches = []
    evaluation_ids = []

    for policy in threshold_policies:
        try:
            outcome, triggered, recommendations = _run_policy(policy, deal)
            evaluation = PolicyEvaluation.objects.create(
                policy=policy,
                deal=deal,
                evaluated_at=timezone.now(),
                outcome=outcome,
                triggered_rules=triggered,
                recommendations=recommendations,
            )
            counts[outcome] = counts.get(outcome, 0) + 1
            evaluation_ids.append(str(evaluation.id))

            if outcome in ("warn", "fail"):
                failing_rules = [r for r in triggered if not r["passed"]]
                breaches.append({
                    "policy_id": str(policy.id),
                    "policy_name": policy.name,
                    "outcome": outcome,
                    "failing_rules": failing_rules,
                    "recommendations": recommendations,
                })

            logger.debug(
                "evaluate_bid_threshold: policy=%s deal=%s outcome=%s",
                policy.name,
                deal_id,
                outcome,
            )
        except Exception as exc:
            logger.exception(
                "evaluate_bid_threshold: error running policy %s against deal %s",
                policy.id,
                deal_id,
            )

    summary = {
        "deal_id": str(deal_id),
        "policies_evaluated": len(evaluation_ids),
        "outcome_counts": counts,
        "breaches": breaches,
        "evaluation_ids": evaluation_ids,
    }
    logger.info(
        "evaluate_bid_threshold: completed for deal_id=%s counts=%s breaches=%d",
        deal_id,
        counts,
        len(breaches),
    )
    return summary
