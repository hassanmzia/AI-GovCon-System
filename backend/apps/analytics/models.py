import uuid

from django.conf import settings
from django.db import models
from apps.core.models import BaseModel


class KPISnapshot(BaseModel):
    """Daily snapshot of pipeline KPIs for historical trending."""
    date = models.DateField(unique=True)
    active_deals = models.IntegerField(default=0)
    pipeline_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    open_proposals = models.IntegerField(default=0)
    win_rate = models.FloatField(null=True, blank=True)
    avg_fit_score = models.FloatField(null=True, blank=True)
    closed_won = models.IntegerField(default=0)
    closed_lost = models.IntegerField(default=0)
    total_opportunities = models.IntegerField(default=0)
    pending_approvals = models.IntegerField(default=0)
    new_deals_this_week = models.IntegerField(default=0)
    # Pipeline stage breakdown {stage: count}
    stage_distribution = models.JSONField(default=dict, blank=True)
    # Proposal status breakdown {status: count}
    proposal_distribution = models.JSONField(default=dict, blank=True)
    # Revenue by contract type {type: value}
    revenue_by_type = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "KPI Snapshot"
        verbose_name_plural = "KPI Snapshots"

    def __str__(self):
        return f"KPI Snapshot {self.date} — pipeline ${self.pipeline_value}"


class DealVelocityMetric(BaseModel):
    """Tracks how long deals spend in each pipeline stage."""
    deal = models.ForeignKey("deals.Deal", on_delete=models.CASCADE, related_name="velocity_metrics")
    stage = models.CharField(max_length=50)
    entered_at = models.DateTimeField()
    exited_at = models.DateTimeField(null=True, blank=True)
    days_in_stage = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["entered_at"]
        unique_together = [["deal", "stage"]]

    def __str__(self):
        return f"{self.deal} — {self.stage} ({self.days_in_stage:.1f}d)" if self.days_in_stage else f"{self.deal} — {self.stage}"


class WinLossAnalysis(BaseModel):
    """Stores win/loss analysis data for closed deals."""
    deal = models.OneToOneField("deals.Deal", on_delete=models.CASCADE, related_name="win_loss_analysis")
    outcome = models.CharField(max_length=20, choices=[("won", "Won"), ("lost", "Lost"), ("no_bid", "No Bid")])
    close_date = models.DateField()
    final_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    # Reasons categorized
    primary_loss_reason = models.CharField(max_length=100, blank=True)
    competitor_name = models.CharField(max_length=300, blank=True)
    competitor_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    our_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    # Qualitative analysis (AI or human)
    lessons_learned = models.TextField(blank=True)
    win_themes = models.JSONField(default=list, blank=True)
    loss_factors = models.JSONField(default=list, blank=True)
    ai_analysis = models.TextField(blank=True)
    # Meta
    recorded_by = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-close_date"]

    def __str__(self):
        return f"{self.deal} — {self.outcome} ({self.close_date})"


class AgentPerformanceMetric(BaseModel):
    """Tracks AI agent performance metrics over time."""
    agent_name = models.CharField(max_length=100)
    date = models.DateField()
    total_runs = models.IntegerField(default=0)
    successful_runs = models.IntegerField(default=0)
    failed_runs = models.IntegerField(default=0)
    avg_duration_seconds = models.FloatField(null=True, blank=True)
    avg_tokens_used = models.IntegerField(null=True, blank=True)
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    user_feedback_positive = models.IntegerField(default=0)
    user_feedback_negative = models.IntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        unique_together = [["agent_name", "date"]]

    def __str__(self):
        return f"{self.agent_name} metrics — {self.date}"


class RecommendationMetric(BaseModel):
    """Tracks recommendation quality (Precision@K) over time."""
    date = models.DateField()
    metric_type = models.CharField(max_length=50, choices=[
        ('precision_at_10', 'Precision@10'),
        ('precision_at_win', 'Precision@Win'),
        ('recall_at_10', 'Recall@10'),
    ])
    recommended_count = models.IntegerField(default=0)
    pursued_count = models.IntegerField(default=0)
    won_count = models.IntegerField(default=0)
    precision_score = models.FloatField(default=0.0)
    recommended_ids = models.JSONField(default=list)
    pursued_ids = models.JSONField(default=list)
    won_ids = models.JSONField(default=list)

    class Meta:
        ordering = ["-date"]
        unique_together = [["date", "metric_type"]]

    def __str__(self):
        return f"{self.metric_type}: {self.precision_score:.2f} on {self.date}"


class RevenueForecast(BaseModel):
    """Revenue forecast snapshot by quarter."""
    forecast_date = models.DateField()
    quarter = models.CharField(max_length=10)
    pipeline_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    weighted_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    expected_wins = models.IntegerField(default=0)
    confidence_low = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    confidence_high = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    deal_details = models.JSONField(default=list)

    class Meta:
        ordering = ["-forecast_date", "quarter"]
        unique_together = [["forecast_date", "quarter"]]

    def __str__(self):
        return f"Forecast {self.quarter}: ${self.weighted_value:,.0f}"


# ---------------------------------------------------------------------------
# AI Agent Observability models
# ---------------------------------------------------------------------------


class AIAgentRun(models.Model):
    """
    One record per AI agent execution.

    Captures latency, token usage, cost, quality signals, and autonomy metadata
    so the platform can monitor agent health and compliance over time.
    """

    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_name = models.CharField(max_length=255, db_index=True)
    deal_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    action = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="running",
        db_index=True,
    )
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Performance
    latency_ms = models.IntegerField(null=True, blank=True)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    # Token usage
    input_tokens = models.IntegerField(null=True, blank=True)
    output_tokens = models.IntegerField(null=True, blank=True)
    # Quality signals
    success = models.BooleanField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    hallucination_flags = models.IntegerField(default=0)
    citations_present = models.BooleanField(null=True, blank=True)
    # HITL / human feedback signals
    human_edit_delta = models.FloatField(
        null=True,
        blank=True,
        help_text="Fraction (0–1) of agent output that was changed by a human reviewer.",
    )
    override = models.BooleanField(
        default=False,
        help_text="True if a human rejected or overrode the agent's output.",
    )
    # Autonomy context
    risk_score = models.FloatField(null=True, blank=True)
    autonomy_level = models.IntegerField(null=True, blank=True)
    # Error details
    error_message = models.TextField(blank=True, default="")
    # Requesting user (may be None for fully autonomous runs)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_runs",
    )

    class Meta:
        verbose_name = "AI Agent Run"
        verbose_name_plural = "AI Agent Runs"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.agent_name} [{self.status}] @ {self.started_at:%Y-%m-%d %H:%M}"


class AIAgentMetric(models.Model):
    """
    Flexible key-value metric attached to a single AIAgentRun.

    Allows arbitrary per-run metrics without schema changes, e.g.:
        {"metric_name": "precision_at_10", "metric_value": 0.82, "metric_unit": "ratio"}
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(
        AIAgentRun,
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    metric_name = models.CharField(max_length=255)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        verbose_name = "AI Agent Metric"
        verbose_name_plural = "AI Agent Metrics"
        unique_together = [("run", "metric_name")]

    def __str__(self) -> str:
        return f"{self.metric_name}={self.metric_value}{self.metric_unit} [{self.run_id}]"


class AIEvaluation(models.Model):
    """
    Human scoring of an AI agent's output on a 1–5 star scale.

    Evaluators can score overall quality, factual accuracy, and usefulness
    independently, plus leave free-form comments.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(
        AIAgentRun,
        on_delete=models.CASCADE,
        related_name="evaluations",
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_evaluations",
    )
    # Scores (1–5)
    quality_score = models.IntegerField(
        help_text="Overall output quality, 1 (very poor) to 5 (excellent)."
    )
    accuracy_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Factual accuracy of the output, 1–5.",
    )
    usefulness_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Practical usefulness of the output, 1–5.",
    )
    comments = models.TextField(blank=True, default="")
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Evaluation"
        verbose_name_plural = "AI Evaluations"
        ordering = ["-evaluated_at"]

    def __str__(self) -> str:
        evaluator_display = (
            self.evaluator.get_full_name() or self.evaluator.username
            if self.evaluator
            else "anonymous"
        )
        return f"Eval by {evaluator_display}: quality={self.quality_score}/5 [{self.run_id}]"
