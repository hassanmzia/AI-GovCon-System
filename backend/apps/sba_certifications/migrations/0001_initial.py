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
            name="SBACertification",
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
                    "cert_type",
                    models.CharField(
                        choices=[
                            ("sb", "Small Business (SB)"),
                            ("sdb", "Small Disadvantaged Business (SDB)"),
                            ("8a", "8(a) Business Development"),
                            ("wosb", "Women-Owned Small Business (WOSB)"),
                            ("edwosb", "Economically Disadvantaged WOSB (EDWOSB)"),
                            ("vosb", "Veteran-Owned Small Business (VOSB)"),
                            ("sdvosb", "Service-Disabled Veteran-Owned (SDVOSB)"),
                            ("hubzone", "HUBZone"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("not_applicable", "Not Applicable"),
                            ("eligible", "Eligible"),
                            ("in_progress", "In Progress"),
                            ("applied", "Applied"),
                            ("under_review", "Under Review"),
                            ("certified", "Certified"),
                            ("expired", "Expired"),
                            ("denied", "Denied"),
                        ],
                        default="not_applicable",
                        max_length=20,
                    ),
                ),
                ("certification_number", models.CharField(blank=True, default="", max_length=100)),
                ("application_date", models.DateField(blank=True, null=True)),
                ("certification_date", models.DateField(blank=True, null=True)),
                ("expiration_date", models.DateField(blank=True, null=True)),
                ("renewal_date", models.DateField(blank=True, null=True)),
                (
                    "application_steps",
                    models.JSONField(
                        default=list,
                        help_text="List of dicts: [{name, completed, notes}] tracking application steps.",
                    ),
                ),
                (
                    "documents_uploaded",
                    models.JSONField(
                        default=list,
                        help_text="List of document references uploaded for this certification.",
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                ("requirements", models.TextField(blank=True, default="")),
                ("notes", models.TextField(blank=True, default="")),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sba_certifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["cert_type"],
            },
        ),
        migrations.AddIndex(
            model_name="sbacertification",
            index=models.Index(fields=["owner"], name="sba_cert_owner_idx"),
        ),
        migrations.AddIndex(
            model_name="sbacertification",
            index=models.Index(fields=["cert_type"], name="sba_cert_type_idx"),
        ),
        migrations.AddIndex(
            model_name="sbacertification",
            index=models.Index(fields=["status"], name="sba_cert_status_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="sbacertification",
            unique_together={("owner", "cert_type")},
        ),
        migrations.CreateModel(
            name="NAICSCode",
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
                ("code", models.CharField(max_length=10)),
                ("title", models.CharField(max_length=500)),
                ("size_standard", models.CharField(blank=True, default="", max_length=100)),
                ("is_primary", models.BooleanField(default=False)),
                ("qualifies_small", models.BooleanField(default=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="naics_codes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-is_primary", "code"],
            },
        ),
        migrations.AddIndex(
            model_name="naicscode",
            index=models.Index(fields=["owner"], name="naics_owner_idx"),
        ),
        migrations.AddIndex(
            model_name="naicscode",
            index=models.Index(fields=["code"], name="naics_code_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="naicscode",
            unique_together={("owner", "code")},
        ),
    ]
