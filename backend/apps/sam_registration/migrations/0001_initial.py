import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SAMRegistration",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uei_number", models.CharField(blank=True, default="", max_length=20)),
                ("cage_code", models.CharField(blank=True, default="", max_length=10)),
                (
                    "tracking_number",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("ein_number", models.CharField(blank=True, default="", max_length=20)),
                (
                    "legal_business_name",
                    models.CharField(blank=True, default="", max_length=500),
                ),
                ("physical_address", models.TextField(blank=True, default="")),
                (
                    "entity_type",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("not_started", "Not Started"),
                            ("in_progress", "In Progress"),
                            ("submitted", "Submitted"),
                            ("active", "Active"),
                            ("expired", "Expired"),
                        ],
                        default="not_started",
                        max_length=20,
                    ),
                ),
                ("registration_date", models.DateField(blank=True, null=True)),
                ("expiration_date", models.DateField(blank=True, null=True)),
                ("submitted_date", models.DateField(blank=True, null=True)),
                (
                    "steps_completed",
                    models.JSONField(
                        default=list,
                        help_text="List of 10 booleans indicating completion of each registration step.",
                    ),
                ),
                (
                    "validation_items",
                    models.JSONField(
                        default=dict,
                        help_text="Dict mapping validation item IDs to checked status.",
                    ),
                ),
                ("notes", models.TextField(blank=True, default="")),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sam_registrations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="samregistration",
            index=models.Index(fields=["owner"], name="sam_registr_owner_i_idx"),
        ),
        migrations.AddIndex(
            model_name="samregistration",
            index=models.Index(fields=["status"], name="sam_registr_status_idx"),
        ),
        migrations.CreateModel(
            name="SAMContact",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("admin_poc", "Admin POC"),
                            ("gov_business_poc", "Gov Business POC"),
                            ("electronic_business_poc", "Electronic Business POC"),
                            ("past_performance_poc", "Past Performance POC"),
                        ],
                        max_length=30,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("title", models.CharField(blank=True, default="", max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, default="", max_length=30)),
                (
                    "registration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contacts",
                        to="sam_registration.samregistration",
                    ),
                ),
            ],
            options={
                "ordering": ["role"],
            },
        ),
    ]
