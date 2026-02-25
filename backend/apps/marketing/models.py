from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class MarketingCampaign(BaseModel):
    """Marketing campaign for deal opportunities."""

    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("social_media", "Social Media"),
        ("webinar", "Webinar"),
        ("trade_show", "Trade Show"),
        ("direct_outreach", "Direct Outreach"),
        ("advertising", "Advertising"),
        ("partnership", "Partnership"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    channel = models.CharField(max_length=50, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planning")
    target_audience = models.CharField(max_length=500, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marketing_campaigns",
    )
    goals = models.JSONField(default=list, blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    related_deals = models.ManyToManyField(
        "deals.Deal", blank=True, related_name="marketing_campaigns"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Marketing Campaign"
        verbose_name_plural = "Marketing Campaigns"

    def __str__(self):
        return f"{self.name} [{self.get_channel_display()}]"
