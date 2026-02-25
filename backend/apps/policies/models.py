import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class BusinessPolicy(models.Model):
    POLICY_TYPE_CHOICES = [
        ("bid_threshold", "Bid Threshold"),
        ("approval_gate", "Approval Gate"),
        ("risk_limit", "Risk Limit"),
        ("compliance_requirement", "Compliance Requirement"),
        ("teaming_rule", "Teaming Rule"),
        ("pricing_constraint", "Pricing Constraint"),
    ]

    SCOPE_CHOICES = [
        ("global", "Global"),
        ("deal_type", "Deal Type"),
        ("naics_code", "NAICS Code"),
        ("agency", "Agency"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    policy_type = models.CharField(
        max_length=50, choices=POLICY_TYPE_CHOICES, db_index=True
    )
    scope = models.CharField(
        max_length=50, choices=SCOPE_CHOICES, default="global", db_index=True
    )
    conditions = models.JSONField(
        default=dict,
        help_text=(
            "Conditions that must be met for this policy to apply, "
            "e.g. {'deal_type': 'IDIQ', 'min_value': 100000}"
        ),
    )
    actions = models.JSONField(
        default=dict,
        help_text=(
            "Actions to take when policy is triggered, "
            "e.g. {'notify': ['manager'], 'block_submission': true}"
        ),
    )
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(
        default=100,
        help_text="Lower number = higher priority. Policies are evaluated in ascending priority order.",
    )
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_policies",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Business Policy"
        verbose_name_plural = "Business Policies"
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["is_active", "policy_type"]),
            models.Index(fields=["scope", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def is_effective(self):
        """Return True if the policy is currently within its effective date range."""
        today = timezone.now().date()
        if self.effective_date and today < self.effective_date:
            return False
        if self.expiry_date and today > self.expiry_date:
            return False
        return True


class PolicyRule(models.Model):
    OPERATOR_CHOICES = [
        ("gt", "Greater Than"),
        ("lt", "Less Than"),
        ("eq", "Equal To"),
        ("gte", "Greater Than or Equal To"),
        ("lte", "Less Than or Equal To"),
        ("in", "In List"),
        ("not_in", "Not In List"),
        ("contains", "Contains"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(
        BusinessPolicy, on_delete=models.CASCADE, related_name="rules"
    )
    rule_name = models.CharField(max_length=255)
    field_path = models.CharField(
        max_length=255,
        help_text=(
            "Dot-notation path to the field on the deal object, "
            "e.g. 'contract_value' or 'metadata.risk_score'"
        ),
    )
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES)
    threshold_value = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Scalar threshold for simple comparisons (gt, lt, eq, gte, lte).",
    )
    threshold_json = models.JSONField(
        null=True,
        blank=True,
        help_text="Structured threshold for list-based operators (in, not_in, contains).",
    )
    error_message = models.TextField(
        blank=True,
        default="",
        help_text="Message shown to the user when this rule produces a blocking failure.",
    )
    warning_message = models.TextField(
        blank=True,
        default="",
        help_text="Message shown to the user when this rule produces a non-blocking warning.",
    )
    is_blocking = models.BooleanField(
        default=True,
        help_text=(
            "If True, a rule violation will produce a 'fail' outcome. "
            "If False, it will produce a 'warn' outcome."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Policy Rule"
        verbose_name_plural = "Policy Rules"
        ordering = ["policy", "rule_name"]

    def __str__(self):
        return f"{self.policy.name} — {self.rule_name}"


class PolicyEvaluation(models.Model):
    OUTCOME_CHOICES = [
        ("pass", "Pass"),
        ("warn", "Warn"),
        ("fail", "Fail"),
        ("skip", "Skip"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(
        BusinessPolicy, on_delete=models.CASCADE, related_name="evaluations"
    )
    deal = models.ForeignKey(
        "deals.Deal", on_delete=models.CASCADE, related_name="policy_evaluations"
    )
    evaluated_at = models.DateTimeField(default=timezone.now, db_index=True)
    outcome = models.CharField(
        max_length=10, choices=OUTCOME_CHOICES, db_index=True
    )
    triggered_rules = models.JSONField(
        default=list,
        help_text=(
            "List of rule evaluation details that contributed to the outcome, "
            "e.g. [{'rule_id': '...', 'rule_name': '...', 'passed': false, 'message': '...'}]"
        ),
    )
    recommendations = models.JSONField(
        default=list,
        help_text="List of recommended actions to resolve warnings or failures.",
    )
    auto_resolved = models.BooleanField(
        default=False,
        help_text="True if the evaluation outcome was resolved automatically without human intervention.",
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_evaluations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Policy Evaluation"
        verbose_name_plural = "Policy Evaluations"
        ordering = ["-evaluated_at"]
        indexes = [
            models.Index(fields=["deal", "outcome"]),
            models.Index(fields=["policy", "evaluated_at"]),
            models.Index(fields=["deal", "policy", "-evaluated_at"]),
        ]

    def __str__(self):
        return f"{self.policy.name} / {self.deal} — {self.outcome} @ {self.evaluated_at:%Y-%m-%d %H:%M}"


class PolicyException(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(
        BusinessPolicy, on_delete=models.CASCADE, related_name="exceptions"
    )
    deal = models.ForeignKey(
        "deals.Deal", on_delete=models.CASCADE, related_name="policy_exceptions"
    )
    reason = models.TextField(help_text="Justification provided by the requester for the exception.")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_policy_exceptions",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If set, the exception automatically becomes inactive after this datetime.",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_policy_exceptions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Policy Exception"
        verbose_name_plural = "Policy Exceptions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["deal", "policy", "status"]),
        ]

    def __str__(self):
        return f"Exception: {self.policy.name} / {self.deal} — {self.status}"

    def is_valid(self):
        """Return True if this exception is approved and not yet expired."""
        if self.status != "approved":
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True
