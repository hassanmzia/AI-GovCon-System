import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EXECUTIVE = "executive", "Executive"
        CAPTURE_MANAGER = "capture_manager", "Capture Manager"
        PROPOSAL_MANAGER = "proposal_manager", "Proposal Manager"
        PRICING_MANAGER = "pricing_manager", "Pricing Manager"
        WRITER = "writer", "Writer"
        REVIEWER = "reviewer", "Reviewer"
        CONTRACTS_MANAGER = "contracts_manager", "Contracts Manager"
        VIEWER = "viewer", "Viewer"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.VIEWER,
    )
    is_mfa_enabled = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    title = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    skills = models.JSONField(default=list, blank=True)
    clearances = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.FileField(upload_to="avatars/", blank=True, null=True)
    notification_preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
