import uuid

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    """Abstract base model with UUID primary key and timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLog(BaseModel):
    """Tracks user and system actions for compliance and debugging."""

    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("view", "View"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=255)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(
                fields=["entity_type", "entity_id"],
                name="idx_audit_entity",
            ),
            models.Index(
                fields=["user", "timestamp"],
                name="idx_audit_user_ts",
            ),
        ]

    def __str__(self):
        user_display = self.user.email if self.user else "system"
        return f"{user_display} {self.action} {self.entity_type}:{self.entity_id}"


class AITraceLog(BaseModel):
    """Records every AI agent action for observability and approval workflows."""

    APPROVAL_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("auto", "Auto-approved"),
    ]

    agent_name = models.CharField(max_length=100)
    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_traces",
    )
    action = models.CharField(max_length=255)
    prompt = models.TextField()
    tool_calls = models.JSONField(default=list)
    retrieved_sources = models.JSONField(default=list)
    output = models.TextField()
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default="pending",
    )
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
    )
    latency_ms = models.IntegerField(null=True, blank=True)
    model_name = models.CharField(max_length=100, blank=True, default="")
    trace_id = models.CharField(max_length=255, blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.agent_name} - {self.action} @ {self.timestamp}"


class Notification(BaseModel):
    """User-facing notifications for deal events and AI actions."""

    TYPE_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("success", "Success"),
        ("error", "Error"),
        ("ai_action", "AI Action"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="info",
    )
    entity_type = models.CharField(max_length=100, blank=True, default="")
    entity_id = models.CharField(max_length=255, blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.user}"
