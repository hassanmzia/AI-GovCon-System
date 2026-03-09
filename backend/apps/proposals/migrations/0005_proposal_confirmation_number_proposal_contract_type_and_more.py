import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proposals", "0004_redteamfinding_submissionchecklist"),
    ]

    operations = [
        # --- SourcesSoughtResponse ---
        migrations.CreateModel(
            name="SourcesSoughtResponse",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=500)),
                ("solicitation_number", models.CharField(blank=True, max_length=255)),
                ("deal_name", models.CharField(blank=True, default="", max_length=500)),
                ("company_overview", models.TextField(blank=True)),
                ("relevant_experience", models.TextField(blank=True)),
                ("technical_approach_summary", models.TextField(blank=True)),
                ("capability_gaps", models.TextField(blank=True)),
                ("questions_for_government", models.JSONField(blank=True, default=list)),
                ("interest_level", models.CharField(
                    choices=[
                        ("strongly_interested", "Strongly Interested"),
                        ("moderately_interested", "Moderately Interested"),
                        ("low_interest", "Low Interest"),
                        ("info_only", "Information Only"),
                    ],
                    default="moderately_interested",
                    max_length=30,
                )),
                ("status", models.CharField(
                    choices=[
                        ("draft", "Draft"),
                        ("in_review", "In Review"),
                        ("submitted", "Submitted"),
                        ("no_response", "No Response"),
                    ],
                    default="draft",
                    max_length=20,
                )),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        # --- Proposal new fields ---
        migrations.AddField(
            model_name="proposal",
            name="confirmation_number",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="proposal",
            name="contract_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ffp", "Firm-Fixed-Price"),
                    ("t_and_m", "Time & Materials"),
                    ("cpff", "Cost-Plus-Fixed-Fee"),
                    ("cpaf", "Cost-Plus-Award-Fee"),
                    ("idiq", "Indefinite Delivery / Indefinite Quantity"),
                    ("bpa", "Blanket Purchase Agreement"),
                    ("other", "Other"),
                ],
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="proposal",
            name="evaluation_method",
            field=models.CharField(
                choices=[
                    ("lpta", "Lowest Price Technically Acceptable"),
                    ("best_value", "Best Value Trade-Off"),
                    ("price_evaluation", "Price Evaluation"),
                    ("not_specified", "Not Specified"),
                ],
                default="not_specified",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="proposal",
            name="issuing_agency",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="proposal",
            name="project_title",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="proposal",
            name="solicitation_number",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="proposal",
            name="submission_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="submission_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="proposal",
            name="submission_method",
            field=models.CharField(
                blank=True,
                choices=[
                    ("email", "Email"),
                    ("portal", "Online Portal"),
                    ("mail", "Physical Mail"),
                ],
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="proposal",
            name="submission_portal_url",
            field=models.URLField(blank=True, max_length=2000),
        ),
        migrations.AddField(
            model_name="proposal",
            name="submitted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # --- SubmissionEmail ---
        migrations.CreateModel(
            name="SubmissionEmail",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("email_type", models.CharField(
                    choices=[
                        ("proposal", "Proposal Submission"),
                        ("rfq", "RFQ Response"),
                        ("sources_sought", "Sources Sought Response"),
                        ("capability_statement", "Capability Statement"),
                    ],
                    max_length=30,
                )),
                ("recipient_email", models.EmailField(blank=True, max_length=254)),
                ("recipient_name", models.CharField(blank=True, max_length=300)),
                ("subject_line", models.CharField(max_length=500)),
                ("body", models.TextField()),
                ("attachments_list", models.JSONField(blank=True, default=list)),
                ("is_sent", models.BooleanField(default=False)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("proposal", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="submission_emails",
                    to="proposals.proposal",
                )),
                ("sources_sought", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="submission_emails",
                    to="proposals.sourcessoughtresponse",
                )),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
