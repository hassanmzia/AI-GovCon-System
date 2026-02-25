from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class FARClause(BaseModel):
    """Federal Acquisition Regulation clause reference."""

    CATEGORY_CHOICES = [
        ("general", "General"),
        ("procurement", "Procurement"),
        ("labor", "Labor"),
        ("security", "Security"),
        ("reporting", "Reporting"),
        ("small_business", "Small Business"),
        ("other", "Other"),
    ]

    clause_number = models.CharField(
        max_length=20,
        unique=True,
        help_text='FAR clause number, e.g. "52.204-21"',
    )
    title = models.CharField(max_length=500)
    full_text = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    is_mandatory = models.BooleanField(default=False)
    applicability_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Dollar threshold above which this clause applies.",
    )
    related_dfars = models.JSONField(
        default=list,
        blank=True,
        help_text="List of related DFARS clause numbers.",
    )
    plain_language_summary = models.TextField(blank=True)
    compliance_checklist = models.JSONField(
        default=list,
        blank=True,
        help_text="List of checklist items for compliance verification.",
    )
    last_updated = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["clause_number"]
        verbose_name = "FAR Clause"
        verbose_name_plural = "FAR Clauses"

    def __str__(self):
        return f"{self.clause_number} - {self.title}"


class RegulatoryRequirement(BaseModel):
    """Regulatory requirement from FAR, DFARS, or other sources."""

    REGULATION_SOURCE_CHOICES = [
        ("FAR", "FAR"),
        ("DFARS", "DFARS"),
        ("agency_specific", "Agency Specific"),
        ("OMB", "OMB"),
        ("executive_order", "Executive Order"),
    ]

    regulation_source = models.CharField(max_length=20, choices=REGULATION_SOURCE_CHOICES)
    reference_number = models.CharField(max_length=50)
    title = models.CharField(max_length=500)
    description = models.TextField()
    compliance_criteria = models.JSONField(
        default=list,
        blank=True,
        help_text="List of criteria that must be met for compliance.",
    )
    applicable_contract_types = models.JSONField(
        default=list,
        blank=True,
        help_text="Contract types this applies to: FFP, T&M, CPFF, CPAF, IDIQ.",
    )
    applicable_set_asides = models.JSONField(
        default=list,
        blank=True,
        help_text="Set-aside categories this applies to.",
    )
    penalty_description = models.TextField(blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["regulation_source", "reference_number"]
        verbose_name = "Regulatory Requirement"
        verbose_name_plural = "Regulatory Requirements"

    def __str__(self):
        return f"[{self.regulation_source}] {self.reference_number} - {self.title}"


class ComplianceAssessment(BaseModel):
    """Compliance assessment for a deal against FAR/DFARS requirements."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    RISK_LEVEL_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="compliance_assessments",
    )
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="compliance_assessments",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    far_compliance_score = models.FloatField(default=0.0)
    dfars_compliance_score = models.FloatField(default=0.0)
    overall_risk_level = models.CharField(
        max_length=10, choices=RISK_LEVEL_CHOICES, default="low"
    )
    findings = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    clauses_reviewed = models.ManyToManyField(
        FARClause,
        blank=True,
        related_name="compliance_assessments",
    )
    non_compliant_items = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Compliance Assessment"
        verbose_name_plural = "Compliance Assessments"

    def __str__(self):
        return f"Compliance Assessment for {self.deal} [{self.status}]"


class LegalRisk(BaseModel):
    """Legal risk identified for a deal."""

    RISK_TYPE_CHOICES = [
        ("contractual", "Contractual"),
        ("regulatory", "Regulatory"),
        ("ip", "Intellectual Property"),
        ("liability", "Liability"),
        ("teaming", "Teaming"),
        ("subcontracting", "Subcontracting"),
        ("conflict_of_interest", "Conflict of Interest"),
        ("organizational_conflict", "Organizational Conflict"),
    ]

    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    PROBABILITY_CHOICES = [
        ("unlikely", "Unlikely"),
        ("possible", "Possible"),
        ("likely", "Likely"),
        ("certain", "Certain"),
    ]

    STATUS_CHOICES = [
        ("identified", "Identified"),
        ("mitigating", "Mitigating"),
        ("mitigated", "Mitigated"),
        ("accepted", "Accepted"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="legal_risks",
    )
    risk_type = models.CharField(max_length=30, choices=RISK_TYPE_CHOICES)
    title = models.CharField(max_length=500)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="low")
    probability = models.CharField(
        max_length=10, choices=PROBABILITY_CHOICES, default="possible"
    )
    mitigation_strategy = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="identified")
    identified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="identified_legal_risks",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Legal Risk"
        verbose_name_plural = "Legal Risks"

    def __str__(self):
        return f"[{self.severity}] {self.title} ({self.deal})"


class ContractReviewNote(BaseModel):
    """Review note on a specific section of a contract/solicitation."""

    NOTE_TYPE_CHOICES = [
        ("concern", "Concern"),
        ("suggestion", "Suggestion"),
        ("approval", "Approval"),
        ("question", "Question"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("addressed", "Addressed"),
        ("dismissed", "Dismissed"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="contract_review_notes",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="contract_review_notes",
    )
    section = models.CharField(max_length=200)
    note_text = models.TextField()
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default="concern")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    response = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contract Review Note"
        verbose_name_plural = "Contract Review Notes"

    def __str__(self):
        return f"[{self.note_type}] {self.section} - {self.deal}"
