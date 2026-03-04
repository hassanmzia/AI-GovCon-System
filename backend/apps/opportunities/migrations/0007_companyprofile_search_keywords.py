"""
Add search_keywords to CompanyProfile and seed a default set that includes
agentic-AI-specific terms alongside the existing keyword groups.

Each inner list is joined into a single SAM.gov `q=` query parameter,
so one API call is made per group.
"""
from django.db import migrations, models

DEFAULT_SEARCH_KEYWORDS = [
    # Agentic / autonomous AI — the new high-priority category
    ["agentic AI"],
    ["AI agents", "autonomous agents"],
    ["multi-agent system"],
    # Existing broad categories
    ["software development", "IT services"],
    ["cybersecurity", "information security"],
    ["cloud computing", "hosting", "platform"],
    ["research and development", "R&D"],
    ["training", "education services"],
    ["artificial intelligence", "machine learning"],
]


def seed_search_keywords(apps, schema_editor):
    CompanyProfile = apps.get_model("opportunities", "CompanyProfile")
    CompanyProfile.objects.filter(is_primary=True).update(
        search_keywords=DEFAULT_SEARCH_KEYWORDS
    )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0006_seed_company_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="companyprofile",
            name="search_keywords",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(seed_search_keywords, reverse),
    ]
