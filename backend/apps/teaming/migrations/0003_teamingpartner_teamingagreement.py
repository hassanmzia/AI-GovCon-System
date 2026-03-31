import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("teaming", "0002_teamingpartnership_disclosure_sections_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamingPartner",
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
                # Identity
                ("name", models.CharField(max_length=500)),
                (
                    "uei",
                    models.CharField(
                        help_text="Unique Entity Identifier (SAM.gov)",
                        max_length=20,
                        unique=True,
                    ),
                ),
                ("cage_code", models.CharField(blank=True, max_length=10)),
                ("duns_number", models.CharField(blank=True, max_length=15)),
                # Capabilities
                ("naics_codes", models.JSONField(blank=True, default=list)),
                ("capabilities", models.JSONField(blank=True, default=list)),
                (
                    "contract_vehicles",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="e.g. GSA MAS, SEWP V, OASIS",
                    ),
                ),
                ("labor_categories", models.JSONField(blank=True, default=list)),
                # Small Business certifications
                (
                    "sb_certifications",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="e.g. SBA, 8A, WOSB, SDVOSB, HUBZone",
                    ),
                ),
                ("is_small_business", models.BooleanField(default=False)),
                # Security
                (
                    "clearance_level",
                    models.CharField(
                        choices=[
                            ("none", "None"),
                            ("public_trust", "Public Trust"),
                            ("secret", "Secret"),
                            ("top_secret", "Top Secret"),
                            ("ts_sci", "TS/SCI"),
                        ],
                        default="none",
                        max_length=20,
                    ),
                ),
                # Performance & reliability
                (
                    "performance_history",
                    models.CharField(
                        choices=[
                            ("excellent", "Excellent"),
                            ("very_good", "Very Good"),
                            ("good", "Good"),
                            ("satisfactory", "Satisfactory"),
                            ("marginal", "Marginal"),
                            ("unsatisfactory", "Unsatisfactory"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=20,
                    ),
                ),
                (
                    "reliability_score",
                    models.FloatField(default=5.0, help_text="0-10 scale"),
                ),
                ("has_cpars_issues", models.BooleanField(default=False)),
                (
                    "risk_level",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("critical", "Critical"),
                        ],
                        default="low",
                        max_length=10,
                    ),
                ),
                # Financials
                (
                    "past_revenue",
                    models.BigIntegerField(
                        default=0, help_text="Annual revenue in USD"
                    ),
                ),
                ("employee_count", models.IntegerField(default=0)),
                # Relationships
                (
                    "primary_agencies",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Agencies this partner works with",
                    ),
                ),
                ("headquarters", models.CharField(blank=True, max_length=200)),
                ("website", models.URLField(blank=True)),
                # Contact
                ("primary_contact_name", models.CharField(blank=True, max_length=255)),
                ("primary_contact_email", models.EmailField(blank=True, max_length=254)),
                ("primary_contact_phone", models.CharField(blank=True, max_length=20)),
                # Status
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("tags", models.JSONField(blank=True, default=list)),
                # Co-sell / channel partner
                (
                    "is_channel_partner",
                    models.BooleanField(
                        default=False, help_text="Co-sell / referral partner"
                    ),
                ),
                (
                    "referral_fee_pct",
                    models.FloatField(
                        blank=True,
                        null=True,
                        help_text="Referral fee percentage for co-sell",
                    ),
                ),
                ("co_sell_opportunities", models.IntegerField(default=0)),
                ("co_sell_wins", models.IntegerField(default=0)),
                # Mentor-Protege
                (
                    "mentor_protege_role",
                    models.CharField(
                        blank=True,
                        help_text="mentor, protege, or blank",
                        max_length=20,
                    ),
                ),
                (
                    "mentor_protege_program",
                    models.CharField(
                        blank=True,
                        help_text="e.g. SBA All Small Mentor-Protege",
                        max_length=100,
                    ),
                ),
                ("mentor_protege_start", models.DateField(blank=True, null=True)),
                ("mentor_protege_end", models.DateField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Teaming Partner",
                "verbose_name_plural": "Teaming Partners",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="TeamingAgreement",
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
                    "agreement_type",
                    models.CharField(
                        choices=[
                            ("nda", "Non-Disclosure Agreement"),
                            ("loi", "Letter of Intent"),
                            ("teaming", "Teaming Agreement"),
                            ("subcontract", "Subcontract Agreement"),
                            ("jv_agreement", "Joint Venture Agreement"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("sent", "Sent for Signature"),
                            ("under_review", "Under Review"),
                            ("signed", "Signed"),
                            ("active", "Active"),
                            ("expired", "Expired"),
                            ("terminated", "Terminated"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=500)),
                # Document
                (
                    "document",
                    models.FileField(blank=True, upload_to="teaming_agreements/"),
                ),
                (
                    "document_text",
                    models.TextField(
                        blank=True, help_text="Generated agreement text"
                    ),
                ),
                # Dates
                ("sent_date", models.DateField(blank=True, null=True)),
                ("signed_date", models.DateField(blank=True, null=True)),
                ("effective_date", models.DateField(blank=True, null=True)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                # Terms
                ("exclusivity", models.BooleanField(default=False)),
                ("work_scope", models.TextField(blank=True)),
                ("work_share_pct", models.FloatField(blank=True, null=True)),
                ("ip_ownership", models.CharField(blank=True, max_length=200)),
                # Signatories
                ("our_signatory", models.CharField(blank=True, max_length=255)),
                ("partner_signatory", models.CharField(blank=True, max_length=255)),
                # Outcome
                (
                    "outcome",
                    models.CharField(
                        blank=True,
                        help_text="won, lost, no_bid, pending",
                        max_length=20,
                    ),
                ),
                # Foreign keys
                (
                    "partnership",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agreements",
                        to="teaming.teamingpartnership",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Teaming Agreement",
                "verbose_name_plural": "Teaming Agreements",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="teamingpartnership",
            name="partner",
            field=models.ForeignKey(
                blank=True,
                help_text="Link to partner directory entry",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="partnerships",
                to="teaming.teamingpartner",
            ),
        ),
    ]
