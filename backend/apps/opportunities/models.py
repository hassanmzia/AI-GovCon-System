import uuid
from django.db import models
from pgvector.django import VectorField
from apps.core.models import BaseModel


class OpportunitySource(BaseModel):
    """Configuration for each opportunity data source."""
    name = models.CharField(max_length=200)  # SAM.gov, ORNL, BNL, etc.
    source_type = models.CharField(max_length=50, choices=[
        ('samgov', 'SAM.gov API'),
        ('web_scrape', 'Web Scrape'),
        ('fpds', 'FPDS'),
        ('usaspending', 'USASpending'),
        ('manual', 'Manual Entry'),
    ])
    base_url = models.URLField(blank=True)
    api_key_env_var = models.CharField(max_length=100, blank=True)  # env var name
    is_active = models.BooleanField(default=True)
    scan_frequency_hours = models.IntegerField(default=4)
    last_scan_at = models.DateTimeField(null=True, blank=True)
    last_scan_status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class Opportunity(BaseModel):
    """Normalized opportunity from any source."""
    # Identity
    notice_id = models.CharField(max_length=255, unique=True)
    source = models.ForeignKey(OpportunitySource, on_delete=models.CASCADE, related_name='opportunities')
    source_url = models.URLField(blank=True)
    raw_data = models.JSONField(default=dict)  # Original API response

    # Core fields
    title = models.CharField(max_length=1000)
    description = models.TextField(blank=True)
    agency = models.CharField(max_length=500, blank=True)
    sub_agency = models.CharField(max_length=500, blank=True)
    office = models.CharField(max_length=500, blank=True)

    # Classification
    notice_type = models.CharField(max_length=100, blank=True)  # Presolicitation, Combined, Sources Sought, etc.
    sol_number = models.CharField(max_length=255, blank=True)  # Solicitation number
    naics_code = models.CharField(max_length=10, blank=True)
    naics_description = models.CharField(max_length=500, blank=True)
    psc_code = models.CharField(max_length=10, blank=True)
    set_aside = models.CharField(max_length=200, blank=True)  # SBA, 8(a), HUBZone, etc.
    classification_code = models.CharField(max_length=50, blank=True)

    # Dates
    posted_date = models.DateTimeField(null=True, blank=True)
    response_deadline = models.DateTimeField(null=True, blank=True)
    archive_date = models.DateTimeField(null=True, blank=True)

    # Value
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    award_type = models.CharField(max_length=100, blank=True)  # FFP, T&M, CPFF, etc.

    # Location
    place_of_performance = models.CharField(max_length=500, blank=True)
    place_city = models.CharField(max_length=200, blank=True)
    place_state = models.CharField(max_length=100, blank=True)

    # Status
    status = models.CharField(max_length=50, default='active', choices=[
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
        ('awarded', 'Awarded'),
        ('archived', 'Archived'),
    ])
    is_active = models.BooleanField(default=True)

    # Enrichment
    incumbent = models.CharField(max_length=500, blank=True)
    keywords = models.JSONField(default=list)
    attachments = models.JSONField(default=list)  # [{name, url, size}]
    contacts = models.JSONField(default=list)  # [{name, email, phone, type}]

    # Embedding for similarity search
    description_embedding = VectorField(dimensions=1536, null=True)

    class Meta:
        ordering = ['-posted_date']
        indexes = [
            models.Index(fields=['notice_id']),
            models.Index(fields=['agency']),
            models.Index(fields=['naics_code']),
            models.Index(fields=['status']),
            models.Index(fields=['response_deadline']),
            models.Index(fields=['posted_date']),
        ]

    def __str__(self):
        return f"{self.notice_id}: {self.title[:80]}"

    @property
    def days_until_deadline(self):
        if not self.response_deadline:
            return None
        from django.utils import timezone
        delta = self.response_deadline - timezone.now()
        return delta.days


class OpportunityScore(BaseModel):
    """AI-generated fit score for an opportunity."""
    opportunity = models.OneToOneField(Opportunity, on_delete=models.CASCADE, related_name='score')

    # Overall
    total_score = models.FloatField(default=0.0)  # 0-100
    recommendation = models.CharField(max_length=20, choices=[
        ('strong_bid', 'Strong Bid'),
        ('bid', 'Bid'),
        ('consider', 'Consider'),
        ('no_bid', 'No Bid'),
    ], default='consider')

    # Factor scores (0-100 each)
    naics_match = models.FloatField(default=0.0)
    psc_match = models.FloatField(default=0.0)
    keyword_overlap = models.FloatField(default=0.0)
    capability_similarity = models.FloatField(default=0.0)
    past_performance_relevance = models.FloatField(default=0.0)
    value_fit = models.FloatField(default=0.0)
    deadline_feasibility = models.FloatField(default=0.0)
    set_aside_match = models.FloatField(default=0.0)
    competition_intensity = models.FloatField(default=0.0)  # Higher = worse
    risk_factors = models.FloatField(default=0.0)  # Higher = worse

    # Explanation
    score_explanation = models.JSONField(default=dict)  # Per-factor explanations
    ai_rationale = models.TextField(blank=True)  # LLM-generated summary

    scored_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_score']

    def __str__(self):
        return f"Score {self.total_score:.1f} for {self.opportunity.notice_id}"


class CompanyProfile(BaseModel):
    """Company capability statement for matching."""
    name = models.CharField(max_length=255)
    uei_number = models.CharField(max_length=20, blank=True)
    cage_code = models.CharField(max_length=10, blank=True)
    naics_codes = models.JSONField(default=list)
    psc_codes = models.JSONField(default=list)
    set_aside_categories = models.JSONField(default=list)
    capability_statement = models.TextField(blank=True)
    capability_embedding = VectorField(dimensions=1536, null=True)
    core_competencies = models.JSONField(default=list)
    past_performance_summary = models.TextField(blank=True)
    key_personnel = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    clearance_levels = models.JSONField(default=list)
    contract_vehicles = models.JSONField(default=list)
    target_agencies = models.JSONField(default=list)
    target_value_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    target_value_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class DailyDigest(BaseModel):
    """Daily Top 10 opportunity digest."""
    date = models.DateField(unique=True)
    opportunities = models.ManyToManyField(Opportunity, related_name='digests')
    total_scanned = models.IntegerField(default=0)
    total_new = models.IntegerField(default=0)
    total_scored = models.IntegerField(default=0)
    summary = models.TextField(blank=True)  # AI-generated summary
    is_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Digest {self.date}"
