import logging
from decimal import Decimal, InvalidOperation

from django.apps import apps
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import BusinessPolicy, PolicyEvaluation, PolicyException
from .serializers import (
    BusinessPolicySerializer,
    PolicyEvaluationSerializer,
    PolicyExceptionSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal policy engine helpers
# ---------------------------------------------------------------------------

def _resolve_field(obj, field_path: str):
    """
    Resolve a dot-notation field path against an object or dict.

    Examples:
        _resolve_field(deal, "contract_value")
        _resolve_field(deal, "metadata.risk_score")
    """
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


def _coerce(value, reference):
    """Try to coerce *value* to the same type as *reference* for comparison."""
    if value is None:
        return None
    try:
        if isinstance(reference, (int, float, Decimal)):
            return Decimal(str(value))
        if isinstance(reference, bool):
            return str(value).lower() in ("true", "1", "yes")
    except (InvalidOperation, ValueError):
        pass
    return str(value)


def _evaluate_rule(rule, deal) -> dict:
    """
    Evaluate a single PolicyRule against a deal instance.

    Returns a dict describing the result::

        {
            "rule_id": str,
            "rule_name": str,
            "passed": bool,
            "is_blocking": bool,
            "message": str,
        }
    """
    field_value = _resolve_field(deal, rule.field_path)
    operator = rule.operator
    passed = False

    try:
        if operator in ("gt", "lt", "eq", "gte", "lte"):
            threshold = Decimal(str(rule.threshold_value))
            coerced = _coerce(field_value, threshold)
            if coerced is None:
                passed = False
            elif operator == "gt":
                passed = Decimal(str(coerced)) > threshold
            elif operator == "lt":
                passed = Decimal(str(coerced)) < threshold
            elif operator == "eq":
                passed = Decimal(str(coerced)) == threshold
            elif operator == "gte":
                passed = Decimal(str(coerced)) >= threshold
            elif operator == "lte":
                passed = Decimal(str(coerced)) <= threshold

        elif operator == "in":
            allowed = rule.threshold_json or []
            passed = field_value in allowed

        elif operator == "not_in":
            disallowed = rule.threshold_json or []
            passed = field_value not in disallowed

        elif operator == "contains":
            container = rule.threshold_json if rule.threshold_json is not None else rule.threshold_value
            if isinstance(field_value, (list, str)):
                passed = container in field_value
            elif isinstance(field_value, dict):
                passed = container in field_value
            else:
                passed = False

    except (InvalidOperation, TypeError, ValueError) as exc:
        logger.warning(
            "Rule evaluation error for rule %s on deal %s: %s",
            rule.id,
            deal.pk,
            exc,
        )
        passed = False

    message = ""
    if not passed:
        message = rule.error_message if rule.is_blocking else rule.warning_message

    return {
        "rule_id": str(rule.id),
        "rule_name": rule.rule_name,
        "field_path": rule.field_path,
        "field_value": str(field_value) if field_value is not None else None,
        "operator": operator,
        "passed": passed,
        "is_blocking": rule.is_blocking,
        "message": message,
    }


def _run_policy_against_deal(policy: BusinessPolicy, deal) -> PolicyEvaluation:
    """
    Run all rules for *policy* against *deal*, persist a PolicyEvaluation, and return it.
    """
    rules = list(policy.rules.all())
    triggered = []
    overall_outcome = "pass"

    for rule in rules:
        result = _evaluate_rule(rule, deal)
        triggered.append(result)
        if not result["passed"]:
            if result["is_blocking"]:
                overall_outcome = "fail"
            elif overall_outcome != "fail":
                overall_outcome = "warn"

    # Build recommendations for non-pass outcomes
    recommendations = []
    for result in triggered:
        if not result["passed"] and result.get("message"):
            recommendations.append(result["message"])

    evaluation = PolicyEvaluation.objects.create(
        policy=policy,
        deal=deal,
        evaluated_at=timezone.now(),
        outcome=overall_outcome,
        triggered_rules=triggered,
        recommendations=recommendations,
    )
    return evaluation


# ---------------------------------------------------------------------------
# ViewSets
# ---------------------------------------------------------------------------

class BusinessPolicyViewSet(viewsets.ModelViewSet):
    """
    CRUD for business policies plus an inline evaluate action.

    POST /api/policies/{id}/evaluate/?deal_id=<uuid>
    """

    queryset = BusinessPolicy.objects.select_related("created_by").prefetch_related("rules").order_by("priority", "name")
    serializer_class = BusinessPolicySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filter params
        policy_type = self.request.query_params.get("policy_type")
        scope = self.request.query_params.get("scope")
        is_active = self.request.query_params.get("is_active")

        if policy_type:
            qs = qs.filter(policy_type=policy_type)
        if scope:
            qs = qs.filter(scope=scope)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ("true", "1"))
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="evaluate")
    def evaluate(self, request, pk=None):
        """
        POST /api/policies/{id}/evaluate/?deal_id=<uuid>

        Runs this policy against the specified deal and returns the evaluation result.
        """
        policy = self.get_object()
        deal_id = request.query_params.get("deal_id") or request.data.get("deal_id")

        if not deal_id:
            return Response(
                {"detail": "deal_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Deal = apps.get_model("deals", "Deal")
        try:
            deal = Deal.objects.get(pk=deal_id)
        except Deal.DoesNotExist:
            return Response(
                {"detail": f"Deal with id '{deal_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not policy.is_active:
            return Response(
                {"detail": "This policy is not active.", "outcome": "skip"},
                status=status.HTTP_200_OK,
            )

        if not policy.is_effective():
            return Response(
                {"detail": "This policy is not within its effective date range.", "outcome": "skip"},
                status=status.HTTP_200_OK,
            )

        evaluation = _run_policy_against_deal(policy, deal)
        serializer = PolicyEvaluationSerializer(evaluation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PolicyEvaluationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to policy evaluation records.

    Supports filtering by: deal, policy, outcome
    """

    queryset = PolicyEvaluation.objects.select_related("policy", "deal", "resolved_by").order_by("-evaluated_at")
    serializer_class = PolicyEvaluationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        deal_id = self.request.query_params.get("deal")
        policy_id = self.request.query_params.get("policy")
        outcome = self.request.query_params.get("outcome")

        if deal_id:
            qs = qs.filter(deal_id=deal_id)
        if policy_id:
            qs = qs.filter(policy_id=policy_id)
        if outcome:
            qs = qs.filter(outcome=outcome)
        return qs


class PolicyExceptionViewSet(viewsets.ModelViewSet):
    """
    CRUD for policy exceptions, plus approve and reject workflow actions.

    POST /api/exceptions/{id}/approve/
    POST /api/exceptions/{id}/reject/
    """

    queryset = PolicyException.objects.select_related(
        "policy", "deal", "approved_by", "requested_by"
    ).order_by("-created_at")
    serializer_class = PolicyExceptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        deal_id = self.request.query_params.get("deal")
        policy_id = self.request.query_params.get("policy")
        exc_status = self.request.query_params.get("status")

        if deal_id:
            qs = qs.filter(deal_id=deal_id)
        if policy_id:
            qs = qs.filter(policy_id=policy_id)
        if exc_status:
            qs = qs.filter(status=exc_status)
        return qs

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """
        POST /api/exceptions/{id}/approve/

        Approve a pending policy exception. Only allowed if the exception is
        currently in 'pending' status.
        """
        exception = self.get_object()

        if exception.status != "pending":
            return Response(
                {"detail": f"Cannot approve an exception with status '{exception.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exception.status = "approved"
        exception.approved_by = request.user
        exception.approved_at = timezone.now()
        exception.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

        serializer = self.get_serializer(exception)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        """
        POST /api/exceptions/{id}/reject/

        Reject a pending policy exception.
        """
        exception = self.get_object()

        if exception.status not in ("pending",):
            return Response(
                {"detail": f"Cannot reject an exception with status '{exception.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exception.status = "rejected"
        exception.approved_by = request.user
        exception.approved_at = timezone.now()
        exception.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

        serializer = self.get_serializer(exception)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Standalone evaluate-deal endpoint
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def evaluate_deal(request):
    """
    POST /api/policies/evaluate-deal/?deal_id=<uuid>

    Run ALL active, in-effect policies against the specified deal.
    Returns a summary of every evaluation result.
    """
    deal_id = request.query_params.get("deal_id") or request.data.get("deal_id")

    if not deal_id:
        return Response(
            {"detail": "deal_id query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    Deal = apps.get_model("deals", "Deal")
    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        return Response(
            {"detail": f"Deal with id '{deal_id}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    today = timezone.now().date()
    policies = BusinessPolicy.objects.filter(is_active=True).prefetch_related("rules").filter(
        models.Q(effective_date__isnull=True) | models.Q(effective_date__lte=today)
    ).filter(
        models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gte=today)
    ).order_by("priority")

    # Re-import models.Q properly
    from django.db.models import Q
    policies = BusinessPolicy.objects.filter(is_active=True).prefetch_related("rules").filter(
        Q(effective_date__isnull=True) | Q(effective_date__lte=today)
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
    ).order_by("priority")

    results = []
    overall = "pass"

    for policy in policies:
        evaluation = _run_policy_against_deal(policy, deal)
        results.append(PolicyEvaluationSerializer(evaluation).data)
        if evaluation.outcome == "fail":
            overall = "fail"
        elif evaluation.outcome == "warn" and overall != "fail":
            overall = "warn"

    return Response(
        {
            "deal_id": str(deal.pk),
            "overall_outcome": overall,
            "policies_evaluated": len(results),
            "evaluations": results,
        },
        status=status.HTTP_200_OK,
    )
