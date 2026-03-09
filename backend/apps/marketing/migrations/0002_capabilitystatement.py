import uuid

import django.db.models.deletion
from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ("opportunities", "0001_initial"),
        ("marketing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CapabilityStatement",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(default="Capability Statement", max_length=300)),
                ("version", models.IntegerField(default=1)),
                ("is_primary", models.BooleanField(default=False)),
                ("company_overview", models.TextField(blank=True)),
                ("core_competencies", models.JSONField(blank=True, default=list)),
                ("differentiators", models.JSONField(blank=True, default=list)),
                ("past_performance_highlights", models.JSONField(blank=True, default=list)),
                ("duns_number", models.CharField(blank=True, max_length=20)),
                ("uei_number", models.CharField(blank=True, max_length=20)),
                ("cage_code", models.CharField(blank=True, max_length=10)),
                ("naics_codes", models.JSONField(blank=True, default=list)),
                ("psc_codes", models.JSONField(blank=True, default=list)),
                ("certifications", models.JSONField(blank=True, default=list)),
                ("contract_vehicles", models.JSONField(blank=True, default=list)),
                ("contact_name", models.CharField(blank=True, max_length=300)),
                ("contact_title", models.CharField(blank=True, max_length=200)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("contact_phone", models.CharField(blank=True, max_length=50)),
                ("website", models.URLField(blank=True)),
                ("target_agency", models.CharField(blank=True, max_length=500)),
                ("target_naics", models.CharField(blank=True, max_length=10)),
                ("content_embedding", pgvector.django.VectorField(dimensions=1536, null=True)),
                ("company_profile", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="capability_statements",
                    to="opportunities.companyprofile",
                )),
            ],
            options={
                "ordering": ["-version"],
                "verbose_name": "Capability Statement",
            },
        ),
    ]
