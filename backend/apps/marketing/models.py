from django.conf import settings
from django.db import models
from pgvector.django import VectorField

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


class CapabilityStatement(BaseModel):
    """One-page capability statement per Bidvantage Capability Statement Guide."""
    company_profile = models.ForeignKey(
        'opportunities.CompanyProfile', on_delete=models.CASCADE,
        related_name='capability_statements'
    )
    title = models.CharField(max_length=300, default='Capability Statement')
    version = models.IntegerField(default=1)
    is_primary = models.BooleanField(default=False)

    # Core sections (per Bidvantage Guide)
    company_overview = models.TextField(blank=True)  # Brief company description
    core_competencies = models.JSONField(default=list, blank=True)  # List of competency strings
    differentiators = models.JSONField(default=list, blank=True)  # What sets company apart
    past_performance_highlights = models.JSONField(default=list, blank=True)  # [{project, agency, summary}]

    # Company data section
    duns_number = models.CharField(max_length=20, blank=True)
    uei_number = models.CharField(max_length=20, blank=True)
    cage_code = models.CharField(max_length=10, blank=True)
    naics_codes = models.JSONField(default=list, blank=True)
    psc_codes = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)  # SBA certifications list
    contract_vehicles = models.JSONField(default=list, blank=True)  # GSA, SEWP, etc.

    # Contact info
    contact_name = models.CharField(max_length=300, blank=True)
    contact_title = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)

    # Target customization
    target_agency = models.CharField(max_length=500, blank=True)
    target_naics = models.CharField(max_length=10, blank=True)

    # Embedding for similarity matching
    content_embedding = VectorField(dimensions=1536, null=True)

    class Meta:
        ordering = ['-version']
        verbose_name = 'Capability Statement'

    def __str__(self):
        return f"{self.title} v{self.version} - {self.company_profile.name}"
