import uuid
from django.db import models
from pgvector.django import VectorField
from apps.core.models import BaseModel


class CompanyStrategy(BaseModel):
    """Living strategic plan maintained by strategy agent + leadership."""
    version = models.IntegerField(default=1)
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)

    # Strategic positioning
    mission_statement = models.TextField(blank=True)
    vision_3_year = models.TextField(blank=True)
    target_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    target_win_rate = models.FloatField(default=0.40)
    target_margin = models.FloatField(default=0.12)

    # Market focus
    target_agencies = models.JSONField(default=list)
    target_domains = models.JSONField(default=list)
    target_naics_codes = models.JSONField(default=list)
    growth_markets = models.JSONField(default=list)
    mature_markets = models.JSONField(default=list)
    exit_markets = models.JSONField(default=list)

    # Competitive strategy
    differentiators = models.JSONField(default=list)
    win_themes = models.JSONField(default=list)
    pricing_philosophy = models.TextField(blank=True)
    teaming_strategy = models.TextField(blank=True)

    # Capacity constraints
    max_concurrent_proposals = models.IntegerField(default=5)
    available_key_personnel = models.JSONField(default=list)
    clearance_capacity = models.JSONField(default=dict)

    # Embedding for semantic matching
    strategy_embedding = VectorField(dimensions=1536, null=True)

    class Meta:
        ordering = ['-version']
        verbose_name_plural = 'Company Strategies'

    def __str__(self):
        return f"Strategy v{self.version} ({self.effective_date})"


class StrategicGoal(BaseModel):
    """Quantified strategic objectives that drive agent behavior."""
    strategy = models.ForeignKey(CompanyStrategy, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=[
        ('revenue', 'Revenue Growth'),
        ('market_entry', 'New Market Entry'),
        ('market_share', 'Market Share Defense'),
        ('capability', 'Capability Building'),
        ('relationship', 'Client Relationship'),
        ('portfolio', 'Portfolio Balance'),
        ('profitability', 'Profitability'),
    ])
    metric = models.CharField(max_length=100)
    current_value = models.FloatField(default=0.0)
    target_value = models.FloatField()
    deadline = models.DateField()
    weight = models.FloatField(default=1.0)
    status = models.CharField(max_length=20, choices=[
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('behind', 'Behind'),
        ('achieved', 'Achieved'),
    ], default='on_track')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-weight', 'deadline']

    def __str__(self):
        return f"{self.name} ({self.category})"


class PortfolioSnapshot(BaseModel):
    """Periodic snapshot of pipeline portfolio health."""
    snapshot_date = models.DateField()
    active_deals = models.IntegerField(default=0)
    total_pipeline_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    weighted_pipeline = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deals_by_agency = models.JSONField(default=dict)
    deals_by_domain = models.JSONField(default=dict)
    deals_by_stage = models.JSONField(default=dict)
    deals_by_size = models.JSONField(default=dict)
    capacity_utilization = models.FloatField(default=0.0)
    concentration_risk = models.JSONField(default=dict)
    strategic_alignment_score = models.FloatField(default=0.0)
    ai_recommendations = models.JSONField(default=list)
    strategy = models.ForeignKey(CompanyStrategy, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"Portfolio Snapshot {self.snapshot_date}"


class StrategicScore(BaseModel):
    """Strategic alignment score for an opportunity."""
    opportunity = models.OneToOneField(
        'opportunities.Opportunity', on_delete=models.CASCADE, related_name='strategic_score'
    )
    strategy = models.ForeignKey(CompanyStrategy, on_delete=models.CASCADE)

    # Overall
    strategic_score = models.FloatField(default=0.0)  # 0-100
    composite_score = models.FloatField(default=0.0)  # Combined with fit score

    # Factor scores
    agency_alignment = models.FloatField(default=0.0)
    domain_alignment = models.FloatField(default=0.0)
    growth_market_bonus = models.FloatField(default=0.0)
    portfolio_balance = models.FloatField(default=0.0)
    revenue_contribution = models.FloatField(default=0.0)
    capacity_fit = models.FloatField(default=0.0)
    relationship_value = models.FloatField(default=0.0)
    competitive_positioning = models.FloatField(default=0.0)

    # Recommendation
    bid_recommendation = models.CharField(max_length=20, choices=[
        ('bid', 'BID'),
        ('no_bid', 'NO BID'),
        ('conditional_bid', 'CONDITIONAL BID'),
    ], default='conditional_bid')
    strategic_rationale = models.TextField(blank=True)
    opportunity_cost = models.TextField(blank=True)
    portfolio_impact = models.TextField(blank=True)
    resource_impact = models.TextField(blank=True)

    scored_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-strategic_score']

    def __str__(self):
        return f"Strategic Score {self.strategic_score:.1f} for {self.opportunity}"
