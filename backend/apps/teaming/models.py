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
    signed_agreement = models.BooleanField(default=False)
    agreement_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    terms_and_conditions = models.TextField(blank=True)
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
