from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class SBACertification(BaseModel):
    """Tracks an SBA certification for the user's organization."""

    CERT_TYPE_CHOICES = [
        ("sb", "Small Business (SB)"),
        ("sdb", "Small Disadvantaged Business (SDB)"),
        ("8a", "8(a) Business Development"),
        ("wosb", "Women-Owned Small Business (WOSB)"),
        ("edwosb", "Economically Disadvantaged WOSB (EDWOSB)"),
        ("vosb", "Veteran-Owned Small Business (VOSB)"),
        ("sdvosb", "Service-Disabled Veteran-Owned (SDVOSB)"),
        ("hubzone", "HUBZone"),
    ]

    STATUS_CHOICES = [
        ("not_applicable", "Not Applicable"),
        ("eligible", "Eligible"),
        ("in_progress", "In Progress"),
        ("applied", "Applied"),
        ("under_review", "Under Review"),
        ("certified", "Certified"),
        ("expired", "Expired"),
        ("denied", "Denied"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sba_certifications",
    )

    cert_type = models.CharField(max_length=20, choices=CERT_TYPE_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="not_applicable"
    )

    # Certification details
    certification_number = models.CharField(max_length=100, blank=True, default="")
    application_date = models.DateField(null=True, blank=True)
    certification_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)

    # Application tracking
    application_steps = models.JSONField(
        default=list,
        help_text="List of dicts: [{name, completed, notes}] tracking application steps.",
    )
    documents_uploaded = models.JSONField(
        default=list,
        help_text="List of document references uploaded for this certification.",
    )

    # Description and notes
    description = models.TextField(blank=True, default="")
    requirements = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["cert_type"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["cert_type"]),
            models.Index(fields=["status"]),
        ]
        unique_together = [["owner", "cert_type"]]

    def __str__(self):
        return f"{self.get_cert_type_display()} - {self.get_status_display()}"


class NAICSCode(BaseModel):
    """NAICS codes associated with the user's business for SBA certifications."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="naics_codes",
    )

    code = models.CharField(max_length=10)
    title = models.CharField(max_length=500)
    size_standard = models.CharField(max_length=100, blank=True, default="")
    is_primary = models.BooleanField(default=False)
    qualifies_small = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_primary", "code"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["code"]),
        ]
        unique_together = [["owner", "code"]]

    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.code} - {self.title}{primary}"

    def save(self, *args, **kwargs):
        # If setting as primary, unset other primaries for this owner
        if self.is_primary:
            NAICSCode.objects.filter(owner=self.owner, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)
        super().save(*args, **kwargs)
