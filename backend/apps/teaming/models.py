from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class TeamingPartnership(BaseModel):
    """Teaming partnership for dealing opportunities."""

    STATUS_CHOICES = [
        ("prospect", "Prospect"),
        ("negotiating", "Negotiating"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("terminated", "Terminated"),
    ]

    RELATIONSHIP_TYPE_CHOICES = [
        ("prime_contractor", "Prime Contractor"),
        ("subcontractor", "Subcontractor"),
        ("joint_venture", "Joint Venture"),
        ("mentor", "Mentor"),
        ("protege", "Protege"),
        ("strategic_partner", "Strategic Partner"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="teaming_partnerships",
    )
    partner_company = models.CharField(max_length=500)
    partner = models.ForeignKey(
        "TeamingPartner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partnerships",
        help_text="Link to partner directory entry",
    )
    partner_contact_name = models.CharField(max_length=255, blank=True)
    partner_contact_email = models.EmailField(blank=True)
    partner_contact_phone = models.CharField(max_length=20, blank=True)
    relationship_type = models.CharField(
        max_length=50, choices=RELATIONSHIP_TYPE_CHOICES
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="prospect"
    )
    description = models.TextField(blank=True)
    responsibilities = models.JSONField(default=list, blank=True)
    revenue_share_percentage = models.FloatField(null=True, blank=True)
    percentage_of_work = models.FloatField(null=True, blank=True)  # % of total work scope
    signed_agreement = models.BooleanField(default=False)
    agreement_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    terms_and_conditions = models.TextField(blank=True)

    # Partner capabilities (per The Vault Ch. VII)
    partner_naics_codes = models.JSONField(default=list, blank=True)
    partner_certifications = models.JSONField(default=list, blank=True)  # SBA certs
    partner_clearance_level = models.CharField(max_length=50, blank=True)
    partner_past_performance = models.JSONField(default=list, blank=True)  # [{project, agency, relevance}]
    partner_key_personnel = models.JSONField(default=list, blank=True)  # [{name, role, qualifications}]

    # Teaming agreement specifics (per The Vault Ch. VII)
    disclosure_sections = models.JSONField(default=list, blank=True)  # NDA/disclosure items
    exclusivity = models.BooleanField(default=False)
    ip_ownership = models.CharField(max_length=200, blank=True)
    dispute_resolution = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_partnerships",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Teaming Partnership"
        verbose_name_plural = "Teaming Partnerships"

    def __str__(self):
        return f"{self.partner_company} - {self.deal} [{self.get_relationship_type_display()}]"


class TeamingPartner(BaseModel):
    """Reusable partner company directory entry — independent of any specific deal."""

    CLEARANCE_CHOICES = [
        ("none", "None"),
        ("public_trust", "Public Trust"),
        ("secret", "Secret"),
        ("top_secret", "Top Secret"),
        ("ts_sci", "TS/SCI"),
    ]

    PERFORMANCE_CHOICES = [
        ("excellent", "Excellent"),
        ("very_good", "Very Good"),
        ("good", "Good"),
        ("satisfactory", "Satisfactory"),
        ("marginal", "Marginal"),
        ("unsatisfactory", "Unsatisfactory"),
        ("unknown", "Unknown"),
    ]

    RISK_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    # Identity
    name = models.CharField(max_length=500)
    uei = models.CharField(max_length=20, unique=True, help_text="Unique Entity Identifier (SAM.gov)")
    cage_code = models.CharField(max_length=10, blank=True)
    duns_number = models.CharField(max_length=15, blank=True)

    # Capabilities
    naics_codes = models.JSONField(default=list, blank=True)
    capabilities = models.JSONField(default=list, blank=True)
    contract_vehicles = models.JSONField(default=list, blank=True, help_text="e.g. GSA MAS, SEWP V, OASIS")
    labor_categories = models.JSONField(default=list, blank=True)

    # Small Business certifications
    sb_certifications = models.JSONField(default=list, blank=True, help_text="e.g. SBA, 8A, WOSB, SDVOSB, HUBZone")
    is_small_business = models.BooleanField(default=False)

    # Security
    clearance_level = models.CharField(max_length=20, choices=CLEARANCE_CHOICES, default="none")

    # Performance & reliability
    performance_history = models.CharField(max_length=20, choices=PERFORMANCE_CHOICES, default="unknown")
    reliability_score = models.FloatField(default=5.0, help_text="0-10 scale")
    has_cpars_issues = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default="low")

    # Financials
    past_revenue = models.BigIntegerField(default=0, help_text="Annual revenue in USD")
    employee_count = models.IntegerField(default=0)

    # Relationships
    primary_agencies = models.JSONField(default=list, blank=True, help_text="Agencies this partner works with")
    headquarters = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)

    # Contact
    primary_contact_name = models.CharField(max_length=255, blank=True)
    primary_contact_email = models.EmailField(blank=True)
    primary_contact_phone = models.CharField(max_length=20, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Co-sell / channel partner fields
    is_channel_partner = models.BooleanField(default=False, help_text="Co-sell / referral partner")
    referral_fee_pct = models.FloatField(null=True, blank=True, help_text="Referral fee percentage for co-sell")
    co_sell_opportunities = models.IntegerField(default=0)
    co_sell_wins = models.IntegerField(default=0)

    # Mentor-Protege
    mentor_protege_role = models.CharField(max_length=20, blank=True, help_text="mentor, protege, or blank")
    mentor_protege_program = models.CharField(max_length=100, blank=True, help_text="e.g. SBA All Small Mentor-Protege")
    mentor_protege_start = models.DateField(null=True, blank=True)
    mentor_protege_end = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Teaming Partner"
        verbose_name_plural = "Teaming Partners"

    def __str__(self):
        return f"{self.name} ({self.uei})"


class TeamingAgreement(BaseModel):
    """Tracks agreement documents and their lifecycle for a partnership."""

    AGREEMENT_TYPE_CHOICES = [
        ("nda", "Non-Disclosure Agreement"),
        ("loi", "Letter of Intent"),
        ("teaming", "Teaming Agreement"),
        ("subcontract", "Subcontract Agreement"),
        ("jv_agreement", "Joint Venture Agreement"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent for Signature"),
        ("under_review", "Under Review"),
        ("signed", "Signed"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("terminated", "Terminated"),
    ]

    partnership = models.ForeignKey(
        TeamingPartnership,
        on_delete=models.CASCADE,
        related_name="agreements",
    )
    agreement_type = models.CharField(max_length=20, choices=AGREEMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    title = models.CharField(max_length=500, blank=True)

    # Document
    document = models.FileField(upload_to="teaming_agreements/", blank=True)
    document_text = models.TextField(blank=True, help_text="Generated agreement text")

    # Dates
    sent_date = models.DateField(null=True, blank=True)
    signed_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Terms
    exclusivity = models.BooleanField(default=False)
    work_scope = models.TextField(blank=True)
    work_share_pct = models.FloatField(null=True, blank=True)
    ip_ownership = models.CharField(max_length=200, blank=True)

    # Signatories
    our_signatory = models.CharField(max_length=255, blank=True)
    partner_signatory = models.CharField(max_length=255, blank=True)

    # Outcome (for won/lost tracking)
    outcome = models.CharField(max_length=20, blank=True, help_text="won, lost, no_bid, pending")

    # Owner
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Teaming Agreement"
        verbose_name_plural = "Teaming Agreements"

    def __str__(self):
        return f"{self.get_agreement_type_display()} — {self.partnership.partner_company}"
