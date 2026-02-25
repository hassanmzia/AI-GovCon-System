import uuid

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class ResearchProject(BaseModel):
    """A research project initiated for a deal, covering various research types."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    RESEARCH_TYPE_CHOICES = [
        ("market_analysis", "Market Analysis"),
        ("competitive_intel", "Competitive Intelligence"),
        ("agency_analysis", "Agency Analysis"),
        ("technology_trends", "Technology Trends"),
        ("incumbent_analysis", "Incumbent Analysis"),
        ("regulatory_landscape", "Regulatory Landscape"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="research_projects",
    )
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    research_type = models.CharField(
        max_length=30, choices=RESEARCH_TYPE_CHOICES
    )
    parameters = models.JSONField(default=dict, blank=True)
    findings = models.JSONField(default=dict, blank=True)
    executive_summary = models.TextField(blank=True)
    sources = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {url, title, relevance_score, snippet}",
    )
    ai_agent_trace_id = models.UUIDField(null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="research_projects",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["deal", "research_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title[:80]}"


class ResearchSource(BaseModel):
    """An individual source fetched and analyzed during a research project."""

    SOURCE_TYPE_CHOICES = [
        ("web", "Web"),
        ("government_db", "Government Database"),
        ("news", "News"),
        ("academic", "Academic"),
        ("industry_report", "Industry Report"),
    ]

    project = models.ForeignKey(
        ResearchProject,
        on_delete=models.CASCADE,
        related_name="research_sources",
    )
    url = models.URLField(max_length=2000)
    title = models.CharField(max_length=500)
    source_type = models.CharField(
        max_length=20, choices=SOURCE_TYPE_CHOICES
    )
    content = models.TextField(blank=True)
    relevance_score = models.FloatField(default=0.0)
    extracted_data = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-relevance_score"]

    def __str__(self):
        return f"[{self.get_source_type_display()}] {self.title[:80]}"


class CompetitorProfile(BaseModel):
    """Profile of a competitor in the government contracting space."""

    name = models.CharField(max_length=255)
    cage_code = models.CharField(max_length=20, blank=True)
    duns_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(max_length=500, blank=True)
    naics_codes = models.JSONField(default=list, blank=True)
    contract_vehicles = models.JSONField(default=list, blank=True)
    key_personnel = models.JSONField(default=list, blank=True)
    revenue_range = models.CharField(max_length=100, blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    past_performance_summary = models.TextField(blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    win_rate = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["cage_code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class MarketIntelligence(BaseModel):
    """A piece of market intelligence relevant to government contracting."""

    CATEGORY_CHOICES = [
        ("budget_trends", "Budget Trends"),
        ("policy_changes", "Policy Changes"),
        ("technology_shifts", "Technology Shifts"),
        ("procurement_patterns", "Procurement Patterns"),
        ("workforce_trends", "Workforce Trends"),
    ]

    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=500)
    summary = models.TextField()
    detail = models.JSONField(default=dict, blank=True)
    impact_assessment = models.TextField(blank=True)
    affected_naics = models.JSONField(default=list, blank=True)
    affected_agencies = models.JSONField(default=list, blank=True)
    source_url = models.URLField(max_length=2000, blank=True)
    published_date = models.DateField(null=True, blank=True)
    relevance_window_days = models.IntegerField(default=90)

    class Meta:
        ordering = ["-published_date"]
        verbose_name_plural = "Market intelligence"
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["published_date"]),
        ]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title[:80]}"
