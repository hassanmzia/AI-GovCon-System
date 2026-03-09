import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("proposals", "0004_redteamfinding_submissionchecklist"),
    ]

    operations = [
        # Add owner field
        migrations.AddField(
            model_name="sourcessoughtresponse",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sources_sought_responses",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Add deal_name field
        migrations.AddField(
            model_name="sourcessoughtresponse",
            name="deal_name",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        # Make deal FK optional
        migrations.AlterField(
            model_name="sourcessoughtresponse",
            name="deal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sources_sought_responses",
                to="deals.deal",
            ),
        ),
        # Update interest_level choices and max_length
        migrations.AlterField(
            model_name="sourcessoughtresponse",
            name="interest_level",
            field=models.CharField(
                choices=[
                    ("strongly_interested", "Strongly Interested"),
                    ("moderately_interested", "Moderately Interested"),
                    ("low_interest", "Low Interest"),
                    ("info_only", "Information Only"),
                ],
                default="moderately_interested",
                max_length=30,
            ),
        ),
        # Update status choices
        migrations.AlterField(
            model_name="sourcessoughtresponse",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("in_review", "In Review"),
                    ("submitted", "Submitted"),
                    ("no_response", "No Response"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
    ]
