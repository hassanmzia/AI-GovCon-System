from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("opportunities", "0007_companyprofile_search_keywords"),
    ]

    operations = [
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
            name="small_business_set_aside",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="set_aside_eligible",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="has_relevant_past_performance",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="opportunityscore",
            name="within_size_standard",
            field=models.BooleanField(default=False),
        ),
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
    ]
