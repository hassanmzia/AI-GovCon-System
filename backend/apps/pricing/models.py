import uuid
from django.conf import settings
from django.db import models
from apps.core.models import BaseModel


class RateCard(BaseModel):
    """Labor category rate cards."""
    labor_category = models.CharField(max_length=255)
    gsa_equivalent = models.CharField(max_length=255, blank=True)
    gsa_sin = models.CharField(max_length=50, blank=True)

    # Rates
    internal_rate = models.DecimalField(max_digits=10, decimal_places=2)
    gsa_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    market_low = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    market_median = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    market_high = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Metadata
    education_requirement = models.CharField(max_length=100, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    clearance_required = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['labor_category']

    def __str__(self):
        return f"{self.labor_category} (${self.internal_rate}/hr)"


class ConsultantProfile(BaseModel):
    """Individual consultant for staffing."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=300)
    labor_category = models.ForeignKey(RateCard, on_delete=models.SET_NULL, null=True, blank=True)
    hourly_cost = models.DecimalField(max_digits=10, decimal_places=2)
    skills = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    clearance_level = models.CharField(max_length=50, blank=True)
    years_experience = models.IntegerField(default=0)
    availability_date = models.DateField(null=True, blank=True)
    utilization_pct = models.FloatField(default=0.0)
    is_key_personnel = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    resume_file = models.FileField(upload_to='resumes/', blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LOEEstimate(BaseModel):
    """Level of Effort estimate derived from solution architecture."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE, related_name='loe_estimates')
    version = models.IntegerField(default=1)

    # WBS structure
    wbs_elements = models.JSONField(default=list)
    # [{wbs_id, name, labor_category, hours_optimistic, hours_likely, hours_pessimistic, hours_estimated}]

    total_hours = models.IntegerField(default=0)
    total_ftes = models.FloatField(default=0.0)
    duration_months = models.IntegerField(default=12)

    # Staffing plan
    staffing_plan = models.JSONField(default=dict)  # {month: {labor_cat: hours}}
    key_personnel = models.JSONField(default=list)

    estimation_method = models.CharField(max_length=50, choices=[
        ('analogous', 'Analogous'),
        ('parametric', 'Parametric'),
        ('three_point', 'Three-Point'),
        ('wbs_bottom_up', 'WBS Bottom-Up'),
    ], default='three_point')

    confidence_level = models.FloatField(default=0.7)
    assumptions = models.JSONField(default=list)
    risks = models.JSONField(default=list)

    class Meta:
        ordering = ['-version']

    def __str__(self):
        return f"LOE v{self.version} for {self.deal}"


class CostModel(BaseModel):
    """Detailed cost build-up for a deal."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE, related_name='cost_models')
    loe = models.ForeignKey(LOEEstimate, on_delete=models.SET_NULL, null=True, blank=True)
    version = models.IntegerField(default=1)

    # Cost components
    direct_labor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fringe_benefits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    overhead = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    odcs = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Other Direct Costs
    subcontractor_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    travel = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    materials = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ga_expense = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # G&A
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Rates
    fringe_rate = models.FloatField(default=0.30)
    overhead_rate = models.FloatField(default=0.40)
    ga_rate = models.FloatField(default=0.10)

    # Detail breakdowns
    labor_detail = models.JSONField(default=list)  # [{category, hours, rate, total}]
    odc_detail = models.JSONField(default=list)
    travel_detail = models.JSONField(default=list)
    sub_detail = models.JSONField(default=list)

    class Meta:
        ordering = ['-version']

    def __str__(self):
        return f"Cost Model v{self.version}: ${self.total_cost}"


class PricingScenario(BaseModel):
    """Pricing scenario with P(win) and expected value analysis."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE, related_name='pricing_scenarios')
    cost_model = models.ForeignKey(CostModel, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)  # Max Profit, Competitive, Aggressive, etc.
    strategy_type = models.CharField(max_length=50, choices=[
        ('max_profit', 'Maximum Profit'),
        ('value_based', 'Value-Based'),
        ('competitive', 'Competitive'),
        ('aggressive', 'Aggressive'),
        ('incumbent_match', 'Incumbent Match'),
        ('budget_fit', 'Budget Fit'),
        ('floor', 'Floor'),
    ])

    # Pricing
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    profit = models.DecimalField(max_digits=15, decimal_places=2)
    margin_pct = models.FloatField()

    # Analysis
    probability_of_win = models.FloatField(default=0.0)
    expected_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    competitive_position = models.CharField(max_length=50, blank=True)  # Below market, At market, Above market

    # Monte Carlo results
    sensitivity_data = models.JSONField(default=dict)

    is_recommended = models.BooleanField(default=False)
    rationale = models.TextField(blank=True)

    class Meta:
        ordering = ['-expected_value']

    def __str__(self):
        return f"{self.name}: ${self.total_price} ({self.margin_pct:.1f}% margin)"


class PricingIntelligence(BaseModel):
    """Market pricing intelligence."""
    source = models.CharField(max_length=100)  # GSA, FPDS, salary.com, etc.
    labor_category = models.CharField(max_length=255, blank=True)
    agency = models.CharField(max_length=255, blank=True)
    rate_low = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate_median = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate_high = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_date = models.DateField(null=True, blank=True)
    raw_data = models.JSONField(default=dict)

    class Meta:
        ordering = ['-data_date']


class PricingApproval(BaseModel):
    """HITL gate for pricing decisions."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE, related_name='pricing_approvals')
    scenario = models.ForeignKey(PricingScenario, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='pricing_requests')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pricing_approvals')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
