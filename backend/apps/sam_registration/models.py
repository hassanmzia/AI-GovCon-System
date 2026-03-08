from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class SAMRegistration(BaseModel):
    """Tracks a SAM.gov registration for the user's organization."""

    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("active", "Active"),
        ("expired", "Expired"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sam_registrations",
    )

    # Registration identifiers
    uei_number = models.CharField(max_length=20, blank=True, default="")
    cage_code = models.CharField(max_length=10, blank=True, default="")
    tracking_number = models.CharField(max_length=100, blank=True, default="")
    ein_number = models.CharField(max_length=20, blank=True, default="")

    # Entity info
    legal_business_name = models.CharField(max_length=500, blank=True, default="")
    physical_address = models.TextField(blank=True, default="")
    entity_type = models.CharField(max_length=100, blank=True, default="")

    # Status and dates
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="not_started"
    )
    registration_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    submitted_date = models.DateField(null=True, blank=True)

    # Step completion (stored as JSON list of booleans)
    steps_completed = models.JSONField(
        default=list,
        help_text="List of 10 booleans indicating completion of each registration step.",
    )

    # Validation checklist (stored as JSON dict of id->bool)
    validation_items = models.JSONField(
        default=dict,
        help_text="Dict mapping validation item IDs to checked status.",
    )

    # Notes
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"SAM Registration - {self.legal_business_name or 'Unnamed'} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Ensure steps_completed has 10 entries
        if not self.steps_completed or len(self.steps_completed) != 10:
            existing = self.steps_completed if isinstance(self.steps_completed, list) else []
            self.steps_completed = (existing + [False] * 10)[:10]
        super().save(*args, **kwargs)


class SAMContact(BaseModel):
    """Point of contact associated with a SAM registration."""

    ROLE_CHOICES = [
        ("admin_poc", "Admin POC"),
        ("gov_business_poc", "Gov Business POC"),
        ("electronic_business_poc", "Electronic Business POC"),
        ("past_performance_poc", "Past Performance POC"),
    ]

    registration = models.ForeignKey(
        SAMRegistration,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, default="")

    class Meta:
        ordering = ["role"]

    def __str__(self):
        return f"{self.get_role_display()}: {self.name}"
