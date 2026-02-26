from django.db import migrations


def seed_samgov_source(apps, schema_editor):
    OpportunitySource = apps.get_model("opportunities", "OpportunitySource")
    OpportunitySource.objects.get_or_create(
        name="SAM.gov",
        defaults={
            "source_type": "samgov",
            "base_url": "https://api.sam.gov/opportunities/v2",
            "is_active": True,
        },
    )


def reverse_seed(apps, schema_editor):
    pass  # leave the row; harmless to keep


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0003_opportunity_source_url_max_length"),
    ]

    operations = [
        migrations.RunPython(seed_samgov_source, reverse_seed),
    ]
