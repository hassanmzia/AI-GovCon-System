import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("opportunities", "0007_companyprofile_search_keywords"),
    ]

    operations = [
        # --- NAICSCode ---
        migrations.CreateModel(
            name="NAICSCode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=6, unique=True)),
                ("title", models.CharField(max_length=300)),
                ("description", models.TextField(blank=True)),
                ("size_standard", models.CharField(blank=True, max_length=100)),
                ("size_standard_type", models.CharField(blank=True, choices=[("revenue", "Revenue"), ("employees", "Employees")], max_length=20)),
                ("sector", models.CharField(blank=True, max_length=2)),
            ],
            options={
                "ordering": ["code"],
                "verbose_name": "NAICS Code",
            },
        ),
        # --- SAMRegistration ---
        migrations.CreateModel(
            name="SAMRegistration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("legal_business_name", models.CharField(max_length=500)),
                ("physical_address", models.JSONField(default=dict)),
                ("mailing_address", models.JSONField(blank=True, default=dict)),
                ("taxpayer_id_type", models.CharField(blank=True, choices=[("ein", "EIN"), ("ssn", "SSN")], max_length=10)),
                ("taxpayer_id_last_four", models.CharField(blank=True, max_length=4)),
                ("entity_type", models.CharField(blank=True, max_length=100)),
                ("ownership_details", models.JSONField(blank=True, default=dict)),
                ("banking_verified", models.BooleanField(default=False)),
                ("registration_status", models.CharField(choices=[("not_started", "Not Started"), ("in_progress", "In Progress"), ("submitted", "Submitted"), ("active", "Active"), ("expired", "Expired")], default="not_started", max_length=20)),
                ("registration_date", models.DateField(blank=True, null=True)),
                ("expiration_date", models.DateField(blank=True, null=True)),
                ("tracking_number", models.CharField(blank=True, max_length=100)),
                ("renewal_reminder_sent", models.BooleanField(default=False)),
                ("name_matches_irs", models.BooleanField(default=False)),
                ("address_matches_irs", models.BooleanField(default=False)),
                ("ein_verified", models.BooleanField(default=False)),
                ("bank_info_business_account", models.BooleanField(default=False)),
                ("correct_entity_type", models.BooleanField(default=False)),
                ("naics_codes_added", models.BooleanField(default=False)),
                ("reps_certs_complete", models.BooleanField(default=False)),
                ("pocs_added", models.BooleanField(default=False)),
                ("all_sections_complete", models.BooleanField(default=False)),
                ("admin_poc", models.JSONField(blank=True, default=dict)),
                ("gov_business_poc", models.JSONField(blank=True, default=dict)),
                ("company_profile", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="sam_registration", to="opportunities.companyprofile")),
            ],
            options={
                "verbose_name": "SAM Registration",
            },
        ),
        # --- SBACertification ---
        migrations.CreateModel(
            name="SBACertification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("certification_type", models.CharField(choices=[("sb", "Small Business"), ("sdb", "Small Disadvantaged Business"), ("8a", "8(a) Business Development"), ("wosb", "Woman-Owned Small Business"), ("edwosb", "Economically Disadvantaged WOSB"), ("vosb", "Veteran-Owned Small Business"), ("sdvosb", "Service-Disabled Veteran-Owned"), ("hubzone", "HUBZone")], max_length=20)),
                ("status", models.CharField(choices=[("not_applicable", "Not Applicable"), ("eligible", "Eligible"), ("applied", "Applied"), ("certified", "Certified"), ("expired", "Expired")], default="not_applicable", max_length=20)),
                ("certification_date", models.DateField(blank=True, null=True)),
                ("expiration_date", models.DateField(blank=True, null=True)),
                ("certification_number", models.CharField(blank=True, max_length=100)),
                ("eligibility_notes", models.TextField(blank=True)),
                ("company_profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sba_certifications", to="opportunities.companyprofile")),
            ],
            options={
                "ordering": ["certification_type"],
                "verbose_name": "SBA Certification",
                "unique_together": {("company_profile", "certification_type")},
            },
        ),
        # --- OpportunityScore new fields ---
        migrations.AddField(
            model_name="opportunityscore",
            name="entry_strategy",
            field=models.CharField(
                blank=True,
                choices=[
                    ("prime", "Bid as Prime"),
                    ("sub", "Pursue as Subcontractor"),
                    ("team", "Form Teaming Arrangement"),
                    ("jv", "Form Joint Venture"),
                    ("sources_sought", "Respond to Sources Sought"),
                    ("no_bid", "No Bid"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="entry_strategy_rationale",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="has_relevant_past_performance",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="purchase_category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("micro", "Micro-Purchase (< $10K)"),
                    ("simplified", "Simplified Acquisition ($10K-$250K)"),
                    ("commercial", "Commercial Items (< $10M)"),
                    ("full_open", "Full & Open Competition"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="set_aside_eligible",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="small_business_set_aside",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="within_size_standard",
            field=models.BooleanField(default=False),
        ),
    ]
