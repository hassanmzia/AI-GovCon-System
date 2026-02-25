import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel


class Deal(BaseModel):
    """Core deal entity tracking an opportunity through the capture pipeline."""
    STAGES = [
        ('intake', 'Intake'),
        ('qualify', 'Qualify'),
        ('bid_no_bid', 'Bid/No-Bid Decision'),
        ('capture_plan', 'Capture Planning'),
        ('proposal_dev', 'Proposal Development'),
        ('red_team', 'Red Team Review'),
        ('final_review', 'Final Review'),
        ('submit', 'Submission'),
        ('post_submit', 'Post-Submission'),
        ('award_pending', 'Award Pending'),
        ('contract_setup', 'Contract Setup'),
        ('delivery', 'Delivery/Execution'),
        ('closed_won', 'Closed - Won'),
        ('closed_lost', 'Closed - Lost'),
        ('no_bid', 'No-Bid'),
    ]

    PRIORITIES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    ]

    # Relationships
    opportunity = models.ForeignKey(
        'opportunities.Opportunity', on_delete=models.CASCADE, related_name='deals'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='owned_deals'
    )
    team = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='deal_team', blank=True
    )

    # Core fields
    title = models.CharField(max_length=500)
    stage = models.CharField(max_length=30, choices=STAGES, default='intake')
    priority = models.IntegerField(choices=PRIORITIES, default=3)
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    win_probability = models.FloatField(default=0.0)
    fit_score = models.FloatField(default=0.0)
    strategic_score = models.FloatField(default=0.0)
    composite_score = models.FloatField(default=0.0)
    ai_recommendation = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    stage_entered_at = models.DateTimeField(default=timezone.now)
    bid_decision_date = models.DateTimeField(null=True, blank=True)
    submission_date = models.DateTimeField(null=True, blank=True)
    award_date = models.DateTimeField(null=True, blank=True)

    # Outcome
    outcome = models.CharField(max_length=20, blank=True, choices=[
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('no_bid', 'No Bid'),
        ('cancelled', 'Cancelled'),
    ])
    outcome_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['owner']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"[{self.stage}] {self.title[:80]}"


class DealStageHistory(BaseModel):
    """Log of all stage transitions for a deal."""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='stage_history')
    from_stage = models.CharField(max_length=30, blank=True)
    to_stage = models.CharField(max_length=30)
    transitioned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    reason = models.TextField(blank=True)
    duration_in_previous_stage = models.DurationField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.deal} : {self.from_stage} -> {self.to_stage}"


class Task(BaseModel):
    """Task assigned within a deal."""
    STATUSES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]

    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tasks'
    )
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    priority = models.IntegerField(default=3)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    stage = models.CharField(max_length=30, blank=True)  # Which pipeline stage this belongs to
    is_ai_generated = models.BooleanField(default=False)
    is_auto_completable = models.BooleanField(default=False)  # Can AI auto-complete

    class Meta:
        ordering = ['priority', 'due_date']

    def __str__(self):
        return f"[{self.status}] {self.title[:60]}"


class TaskTemplate(BaseModel):
    """Template for auto-generating tasks per pipeline stage."""
    stage = models.CharField(max_length=30)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    default_priority = models.IntegerField(default=3)
    days_until_due = models.IntegerField(default=7)
    is_required = models.BooleanField(default=True)
    is_auto_completable = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['stage', 'order']

    def __str__(self):
        return f"[{self.stage}] {self.title}"


class Approval(BaseModel):
    """HITL approval gate for critical decisions."""
    TYPES = [
        ('bid_no_bid', 'Bid/No-Bid Decision'),
        ('pricing', 'Pricing Approval'),
        ('proposal_final', 'Final Proposal Approval'),
        ('submission', 'Submission Authorization'),
        ('contract_terms', 'Contract Terms Approval'),
    ]

    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='approvals')
    approval_type = models.CharField(max_length=30, choices=TYPES)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='approvals_requested'
    )
    requested_from = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='approvals_pending'
    )
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    ai_recommendation = models.TextField(blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    decision_rationale = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.status}] {self.approval_type} for {self.deal}"


class Comment(BaseModel):
    """Comments/notes on a deal."""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    content = models.TextField()
    is_ai_generated = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.deal}"


class Activity(BaseModel):
    """Activity log entry for a deal (auto-generated)."""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=100)  # stage_changed, task_completed, comment_added, etc.
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    is_ai_action = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on {self.deal} by {self.actor}"
