from django.db import migrations


def seed_fpds_source(apps, schema_editor):
    OpportunitySource = apps.get_model("opportunities", "OpportunitySource")
    OpportunitySource.objects.get_or_create(
        name="FPDS.gov",
        defaults={
            "source_type": "fpds",
            "base_url": "https://www.fpds.gov/ezsearch/fpdsportal",
            "is_active": True,
            "scan_frequency_hours": 12,
        },
    )


def reverse_seed(apps, schema_editor):
    pass  # leave the row; harmless to keep


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0008_naicscode_opportunityscore_entry_strategy_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_fpds_source, reverse_seed),
    ]
