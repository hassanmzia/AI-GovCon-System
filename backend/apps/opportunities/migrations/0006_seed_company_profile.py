"""
Seed or update the primary CompanyProfile with target NAICS and PSC codes.

NAICS codes:
  513210  Software Publishing
  541511  Custom Computer Programming Services
  518210  Computing Infrastructure / Data Processing / Web Hosting
  611420  Computer Training
  541714  R&D in Biotechnology (except Nanobiotechnology)

PSC codes (broad + specific):
  D   IT and Telecom
  A   Research and Development
  U   Education and Training
  7A  IT and Telecom - Applications
  7B  IT and Telecom - Compute
  7J  IT and Telecom - Security and Compliance
  7H  IT and Telecom - Platform
  7F  IT and Telecom - IT Management
  AJ11  General Science and Technology R&D Services, Basic Research
  AJ12  Applied Research
  AJ13  Experimental Development
  DA01  IT - Business App / App Development Support Services (Labor)
  DA10  IT - Business App / App Development SaaS
  DJ01  IT - Security and Compliance Support Services (Labor)
  DJ10  IT - Security and Compliance as a Service
  DH01  IT - Platform Support Service: DB, Mainframe, Middleware (Labor)
  DH10  IT - Platform as a Service: DB, Mainframe, Middleware
  DF01  IT - IT Management Support Services (Labor)
  DF10  IT - IT Management as a Service
"""
from django.db import migrations

NAICS_CODES = [
    "513210",
    "541511",
    "518210",
    "611420",
    "541714",
]

PSC_CODES = [
    # Broad categories (used for prefix matching in scorer)
    "D",
    "A",
    "U",
    "7A",
    "7B",
    "7J",
    "7H",
    "7F",
    # Specific codes
    "AJ11",
    "AJ12",
    "AJ13",
    "DA01",
    "DA10",
    "DJ01",
    "DJ10",
    "DH01",
    "DH10",
    "DF01",
    "DF10",
]


def seed_profile(apps, schema_editor):
    CompanyProfile = apps.get_model("opportunities", "CompanyProfile")
    profile = CompanyProfile.objects.filter(is_primary=True).first()
    if profile:
        profile.naics_codes = NAICS_CODES
        profile.psc_codes = PSC_CODES
        profile.save(update_fields=["naics_codes", "psc_codes"])
    else:
        CompanyProfile.objects.create(
            is_primary=True,
            name="Primary Company",
            naics_codes=NAICS_CODES,
            psc_codes=PSC_CODES,
        )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0005_fix_lab_agency_names"),
    ]

    operations = [
        migrations.RunPython(seed_profile, reverse),
    ]
