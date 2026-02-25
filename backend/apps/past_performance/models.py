import uuid
from django.conf import settings
from django.db import models
from pgvector.django import VectorField
from apps.core.models import BaseModel


class PastPerformance(BaseModel):
    """Past performance record for proposal references."""
    # Project info
    project_name = models.CharField(max_length=500)
    contract_number = models.CharField(max_length=100, blank=True)
    client_agency = models.CharField(max_length=500)
    client_name = models.CharField(max_length=300, blank=True)
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=50, blank=True)

    # Details
    description = models.TextField()
    relevance_keywords = models.JSONField(default=list)
    naics_codes = models.JSONField(default=list)
    technologies = models.JSONField(default=list)
    domains = models.JSONField(default=list)  # AI/ML, Cloud, Cyber, etc.

    # Performance
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    contract_type = models.CharField(max_length=50, blank=True)  # FFP, T&M, CPFF
    performance_rating = models.CharField(max_length=50, blank=True)  # Exceptional, Very Good, Satisfactory
    cpars_rating = models.CharField(max_length=50, blank=True)

    # Metrics
    on_time_delivery = models.BooleanField(default=True)
    within_budget = models.BooleanField(default=True)
    key_achievements = models.JSONField(default=list)
    metrics = models.JSONField(default=dict)  # {kpi: value}

    # Narrative (pre-written for proposals)
    narrative = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)

    # Embedding for RAG matching
    description_embedding = VectorField(dimensions=1536, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    last_verified = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-end_date']
        verbose_name_plural = 'Past Performance Records'

    def __str__(self):
        return f"{self.project_name} ({self.client_agency})"


class PastPerformanceMatch(BaseModel):
    """AI-matched past performance for an opportunity/deal."""
    opportunity = models.ForeignKey(
        'opportunities.Opportunity', on_delete=models.CASCADE, related_name='past_perf_matches'
    )
    past_performance = models.ForeignKey(PastPerformance, on_delete=models.CASCADE)
    relevance_score = models.FloatField()  # 0-100
    match_rationale = models.TextField(blank=True)
    matched_keywords = models.JSONField(default=list)

    class Meta:
        ordering = ['-relevance_score']
        unique_together = ['opportunity', 'past_performance']
