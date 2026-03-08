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
    source_url = models.URLField(max_length=2000, blank=True)
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

    # Purchase threshold intelligence (per The Vault Ch. III)
    purchase_category = models.CharField(max_length=20, choices=[
        ('micro', 'Micro-Purchase (< $10K)'),
        ('simplified', 'Simplified Acquisition ($10K-$250K)'),
        ('commercial', 'Commercial Items (< $10M)'),
        ('full_open', 'Full & Open Competition'),
    ], blank=True)
    small_business_set_aside = models.BooleanField(default=False)
    set_aside_eligible = models.BooleanField(default=False)
    has_relevant_past_performance = models.BooleanField(default=False)
    within_size_standard = models.BooleanField(default=False)

    # Entry strategy recommendation (per The Vault Ch. VII)
    entry_strategy = models.CharField(max_length=20, choices=[
        ('prime', 'Bid as Prime'), ('sub', 'Pursue as Subcontractor'),
        ('team', 'Form Teaming Arrangement'), ('jv', 'Form Joint Venture'),
        ('sources_sought', 'Respond to Sources Sought'), ('no_bid', 'No Bid'),
    ], blank=True)
    entry_strategy_rationale = models.TextField(blank=True)

    # Explanation
    score_explanation = models.JSONField(default=dict)
    ai_rationale = models.TextField(blank=True)

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
    # SAM.gov keyword search groups.  Each item is a list of terms that are
    # joined into one `q=` query per SAM.gov API call.
    # Example: [["agentic AI"], ["software development", "IT services"]]
    search_keywords = models.JSONField(default=list, blank=True)

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


class SAMRegistration(BaseModel):
    """SAM.gov registration tracking and compliance per Bidvantage SAM Registration Guide."""
    company_profile = models.OneToOneField(CompanyProfile, on_delete=models.CASCADE, related_name='sam_registration')

    # Core registration data (per SAM Guide Steps 1-7)
    legal_business_name = models.CharField(max_length=500)
    physical_address = models.JSONField(default=dict)  # {street, city, state, zip}
    mailing_address = models.JSONField(default=dict, blank=True)
    taxpayer_id_type = models.CharField(max_length=10, choices=[
        ('ein', 'EIN'), ('ssn', 'SSN'),
    ], blank=True)
    taxpayer_id_last_four = models.CharField(max_length=4, blank=True)
    entity_type = models.CharField(max_length=100, blank=True)  # LLC, Corp, etc.
    ownership_details = models.JSONField(default=dict, blank=True)
    banking_verified = models.BooleanField(default=False)

    # Registration status
    registration_status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'), ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'), ('active', 'Active'), ('expired', 'Expired'),
    ], default='not_started')
    registration_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    renewal_reminder_sent = models.BooleanField(default=False)

    # Validation checklist (per The Vault SAM.gov Tips)
    name_matches_irs = models.BooleanField(default=False)
    address_matches_irs = models.BooleanField(default=False)
    ein_verified = models.BooleanField(default=False)
    bank_info_business_account = models.BooleanField(default=False)
    correct_entity_type = models.BooleanField(default=False)
    naics_codes_added = models.BooleanField(default=False)
    reps_certs_complete = models.BooleanField(default=False)
    pocs_added = models.BooleanField(default=False)
    all_sections_complete = models.BooleanField(default=False)

    # Points of Contact (per SAM Guide Step 7)
    admin_poc = models.JSONField(default=dict, blank=True)
    gov_business_poc = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'SAM Registration'

    def __str__(self):
        return f"SAM: {self.legal_business_name} ({self.registration_status})"

    @property
    def is_expiring_soon(self):
        if not self.expiration_date:
            return False
        from django.utils import timezone
        delta = self.expiration_date - timezone.now().date()
        return 0 < delta.days <= 30

    @property
    def validation_checklist_score(self):
        checks = [
            self.name_matches_irs, self.address_matches_irs, self.ein_verified,
            self.bank_info_business_account, self.correct_entity_type,
            self.naics_codes_added, self.reps_certs_complete, self.pocs_added,
            self.all_sections_complete,
        ]
        return round(sum(checks) / len(checks) * 100, 1)


class NAICSCode(BaseModel):
    """NAICS code reference data per The Vault Ch. II."""
    code = models.CharField(max_length=6, unique=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    size_standard = models.CharField(max_length=100, blank=True)
    size_standard_type = models.CharField(max_length=20, choices=[
        ('revenue', 'Revenue'), ('employees', 'Employees'),
    ], blank=True)
    sector = models.CharField(max_length=2, blank=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'NAICS Code'

    def __str__(self):
        return f"{self.code} - {self.title}"


class SBACertification(BaseModel):
    """SBA certification tracking per The Vault Ch. II (8 categories)."""
    company_profile = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='sba_certifications')
    certification_type = models.CharField(max_length=20, choices=[
        ('sb', 'Small Business'), ('sdb', 'Small Disadvantaged Business'),
        ('8a', '8(a) Business Development'), ('wosb', 'Woman-Owned Small Business'),
        ('edwosb', 'Economically Disadvantaged WOSB'), ('vosb', 'Veteran-Owned Small Business'),
        ('sdvosb', 'Service-Disabled Veteran-Owned'), ('hubzone', 'HUBZone'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('not_applicable', 'Not Applicable'), ('eligible', 'Eligible'),
        ('applied', 'Applied'), ('certified', 'Certified'), ('expired', 'Expired'),
    ], default='not_applicable')
    certification_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    certification_number = models.CharField(max_length=100, blank=True)
    eligibility_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['certification_type']
        unique_together = ['company_profile', 'certification_type']
        verbose_name = 'SBA Certification'

    def __str__(self):
        return f"{self.get_certification_type_display()} - {self.get_status_display()}"


class OpportunityAmendment(BaseModel):
    """Tracks amendments and changes to tracked opportunities."""
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='amendments')
    amendment_number = models.IntegerField(default=1)
    change_type = models.CharField(max_length=50, choices=[
        ('deadline_extended', 'Deadline Extended'),
        ('deadline_shortened', 'Deadline Shortened'),
        ('scope_modified', 'Scope Modified'),
        ('set_aside_changed', 'Set-Aside Changed'),
        ('evaluation_criteria_changed', 'Evaluation Criteria Changed'),
        ('cancelled', 'Cancelled'),
        ('reissued', 'Reissued'),
        ('qa_posted', 'Q&A Posted'),
        ('attachment_added', 'Attachment Added'),
        ('other', 'Other'),
    ])
    summary = models.TextField(blank=True)
    old_value = models.JSONField(default=dict, blank=True)
    new_value = models.JSONField(default=dict, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    is_material = models.BooleanField(default=True)
    impact_assessment = models.TextField(blank=True)
    requires_rescore = models.BooleanField(default=False)

    class Meta:
        ordering = ['-detected_at']
        unique_together = ['opportunity', 'amendment_number']

    def __str__(self):
        return f"Amendment #{self.amendment_number} ({self.change_type}) for {self.opportunity.notice_id}"
