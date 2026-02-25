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
