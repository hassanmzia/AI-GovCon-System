"""
Migration: update the `agency` field for existing national-lab opportunities
so they use the real parent agency ("U.S. Department of Energy") instead of
repeating the source / lab name.

This keeps the Agencies filter dropdown distinct from the Sources dropdown.
"""
from django.db import migrations

# Lab source names whose opportunities need their agency field corrected.
LAB_SOURCE_NAMES = [
    "Oak Ridge National Laboratory",
    "Brookhaven National Laboratory",
    "Sandia National Laboratories",
    "Kansas City National Security Campus",
]


def fix_lab_agencies(apps, schema_editor):
    Opportunity = apps.get_model("opportunities", "Opportunity")
    # Only touch records where agency still mirrors the source name.
    updated = (
        Opportunity.objects
        .filter(
            source__name__in=LAB_SOURCE_NAMES,
            agency__in=LAB_SOURCE_NAMES,
        )
        .update(agency="U.S. Department of Energy")
    )
    print(f"  Updated agency to 'U.S. Department of Energy' for {updated} lab opportunities.")


def reverse_fix(apps, schema_editor):
    # Reverting would require knowing the original per-lab name; leave as-is.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0004_seed_samgov_source"),
    ]

    operations = [
        migrations.RunPython(fix_lab_agencies, reverse_fix),
    ]
