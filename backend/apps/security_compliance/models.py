from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class SecurityFramework(BaseModel):
    """A security/compliance framework such as NIST 800-53, FedRAMP, CMMC, etc."""

    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    control_families = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "version"]
        unique_together = [["name", "version"]]

    def __str__(self):
        return f"{self.name} v{self.version}"


class SecurityControl(BaseModel):
    """An individual control within a security framework (e.g. AC-1, SC-7)."""

    PRIORITY_CHOICES = [
        ("P1", "P1 - High"),
        ("P2", "P2 - Moderate"),
        ("P3", "P3 - Low"),
    ]

    BASELINE_IMPACT_CHOICES = [
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ]

    framework = models.ForeignKey(
        SecurityFramework,
        on_delete=models.CASCADE,
        related_name="controls",
    )
    control_id = models.CharField(max_length=50)
    title = models.CharField(max_length=500)
    description = models.TextField()
    family = models.CharField(max_length=255)
    priority = models.CharField(max_length=2, choices=PRIORITY_CHOICES)
    baseline_impact = models.CharField(
        max_length=10, choices=BASELINE_IMPACT_CHOICES
    )
    implementation_guidance = models.TextField(blank=True)
    assessment_procedures = models.JSONField(default=list)
    related_controls = models.JSONField(default=list)

    class Meta:
        ordering = ["framework", "control_id"]
        unique_together = [["framework", "control_id"]]

    def __str__(self):
        return f"{self.framework.name} - {self.control_id}: {self.title}"


class SecurityControlMapping(BaseModel):
    """Maps a security control to a specific deal with implementation status."""

    IMPLEMENTATION_STATUS_CHOICES = [
        ("planned", "Planned"),
        ("partial", "Partially Implemented"),
        ("implemented", "Implemented"),
        ("not_applicable", "Not Applicable"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="security_control_mappings",
    )
    control = models.ForeignKey(
        SecurityControl,
        on_delete=models.CASCADE,
        related_name="deal_mappings",
    )
    implementation_status = models.CharField(
        max_length=20,
        choices=IMPLEMENTATION_STATUS_CHOICES,
        default="planned",
    )
    responsible_party = models.CharField(max_length=255, blank=True)
    implementation_description = models.TextField(blank=True)
    evidence_references = models.JSONField(default=list)
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_assessments",
    )
    assessment_date = models.DateField(null=True, blank=True)
    gap_description = models.TextField(blank=True)
    remediation_plan = models.TextField(blank=True)
    target_completion = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["deal", "control"]
        unique_together = [["deal", "control"]]

    def __str__(self):
        return (
            f"{self.deal} - {self.control.control_id} "
            f"[{self.get_implementation_status_display()}]"
        )


class SecurityComplianceReport(BaseModel):
    """A compliance report generated for a deal against a specific framework."""

    REPORT_TYPE_CHOICES = [
        ("gap_analysis", "Gap Analysis"),
        ("readiness_assessment", "Readiness Assessment"),
        ("poam", "Plan of Action & Milestones"),
        ("ssp_section", "SSP Section"),
        ("authorization_package", "Authorization Package"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_review", "In Review"),
        ("final", "Final"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="compliance_reports",
    )
    framework = models.ForeignKey(
        SecurityFramework,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft"
    )
    overall_compliance_pct = models.FloatField(default=0.0)
    controls_implemented = models.IntegerField(default=0)
    controls_partial = models.IntegerField(default=0)
    controls_planned = models.IntegerField(default=0)
    controls_na = models.IntegerField(default=0)
    gaps = models.JSONField(default=list)
    findings = models.JSONField(default=list)
    poam_items = models.JSONField(default=list)
    generated_by = models.CharField(max_length=255, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_compliance_reports",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.deal} - {self.framework.name} "
            f"{self.get_report_type_display()} [{self.get_status_display()}]"
        )


class ComplianceRequirement(BaseModel):
    """A compliance requirement identified for a deal from source documents."""

    CATEGORY_CHOICES = [
        ("security_clearance", "Security Clearance"),
        ("facility_clearance", "Facility Clearance"),
        ("data_handling", "Data Handling"),
        ("encryption", "Encryption"),
        ("access_control", "Access Control"),
        ("audit", "Audit"),
        ("incident_response", "Incident Response"),
        ("training", "Training"),
        ("physical_security", "Physical Security"),
    ]

    PRIORITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    STATUS_CHOICES = [
        ("compliant", "Compliant"),
        ("gap", "Gap"),
        ("in_progress", "In Progress"),
        ("not_assessed", "Not Assessed"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="compliance_requirements",
    )
    source_document = models.CharField(max_length=500, blank=True)
    requirement_text = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    current_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="not_assessed"
    )
    gap_description = models.TextField(blank=True)
    remediation_cost_estimate = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.deal} - {self.get_category_display()} "
            f"[{self.get_current_status_display()}]"
        )
