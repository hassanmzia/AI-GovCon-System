import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("deals", "0001_initial"),
        ("opportunities", "0001_initial"),
        ("proposals", "0005_proposal_confirmation_number_proposal_contract_type_and_more"),
    ]

    operations = [
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
        migrations.AddField(
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
        migrations.AddField(
            model_name="sourcessoughtresponse",
            name="opportunity",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sources_sought_responses",
                to="opportunities.opportunity",
            ),
        ),
    ]
