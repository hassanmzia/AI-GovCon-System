import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("deals", "0001_initial"),
        ("opportunities", "0001_initial"),
        ("proposals", "0004_redteamfinding_submissionchecklist"),
    ]

    operations = [
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
                ("owner", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="sources_sought_responses",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("deal", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="sources_sought_responses",
                    to="deals.deal",
                )),
                ("opportunity", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="sources_sought_responses",
                    to="opportunities.opportunity",
                )),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
