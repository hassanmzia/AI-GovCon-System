"""Seed DocumentTemplate records for the Bidvantage reference templates
shipped in GovCon-Policies/."""

from django.db import migrations


BIDVANTAGE_TEMPLATES = [
    {
        "name": "Bidvantage Proposal Template",
        "description": (
            "Complete government proposal template with cover page, table of contents, "
            "technical approach, management approach, past performance, and pricing volumes. "
            "Ready-to-use for federal RFP responses."
        ),
        "category": "proposal",
        "file_format": "docx",
        "source": "Bidvantage",
        "tags": ["bidvantage", "proposal", "rfp", "federal"],
        "variables": [
            {"name": "company_name", "label": "Company Name", "default": ""},
            {"name": "solicitation_number", "label": "Solicitation Number", "default": ""},
            {"name": "project_title", "label": "Project Title", "default": ""},
            {"name": "issuing_agency", "label": "Issuing Agency", "default": ""},
            {"name": "submission_date", "label": "Submission Date", "default": ""},
            {"name": "cage_code", "label": "CAGE Code", "default": ""},
            {"name": "duns_number", "label": "DUNS / UEI Number", "default": ""},
        ],
        "is_default": True,
        "file_ref": "Bidvantage Proposal Template.docx",
    },
    {
        "name": "Bidvantage Past Performance & Experience Template",
        "description": (
            "Template for documenting past performance and relevant experience "
            "for government contract proposals. Includes contract reference format, "
            "performance metrics, and relevance mapping."
        ),
        "category": "past_performance",
        "file_format": "docx",
        "source": "Bidvantage",
        "tags": ["bidvantage", "past-performance", "experience", "cpars"],
        "variables": [
            {"name": "company_name", "label": "Company Name", "default": ""},
            {"name": "contract_number", "label": "Contract Number", "default": ""},
            {"name": "agency_name", "label": "Agency Name", "default": ""},
            {"name": "contract_value", "label": "Contract Value", "default": ""},
            {"name": "period_of_performance", "label": "Period of Performance", "default": ""},
        ],
        "is_default": True,
        "file_ref": "Bidvantage Past Performance and Experience Template.docx",
    },
    {
        "name": "Bidvantage Email Proposal Submission Templates",
        "description": (
            "Pre-written email templates for submitting proposals, RFQ responses, "
            "and capability statements via email. Includes subject lines and body text."
        ),
        "category": "email",
        "file_format": "docx",
        "source": "Bidvantage",
        "tags": ["bidvantage", "email", "submission", "rfq"],
        "variables": [
            {"name": "company_name", "label": "Company Name", "default": ""},
            {"name": "solicitation_number", "label": "Solicitation Number", "default": ""},
            {"name": "contracting_officer", "label": "Contracting Officer Name", "default": ""},
            {"name": "submission_date", "label": "Submission Date", "default": ""},
        ],
        "is_default": True,
        "file_ref": "Bidvantage Email Proposal Submission Templates.docx",
    },
    {
        "name": "Bidvantage Capability Statement Guide",
        "description": (
            "Reference guide for creating effective one-page capability statements "
            "for government contracting. Covers layout, core competencies, past "
            "performance highlights, and company data sections."
        ),
        "category": "guide",
        "file_format": "pdf",
        "source": "Bidvantage",
        "tags": ["bidvantage", "capability-statement", "guide", "marketing"],
        "variables": [],
        "is_default": False,
        "file_ref": "Bidvantage Capability Statement Guide.pdf",
    },
    {
        "name": "Bidvantage Capability Statement Example",
        "description": (
            "Example capability statement showing best practices for layout, "
            "branding, core competencies display, and government data formatting."
        ),
        "category": "capability_statement",
        "file_format": "pdf",
        "source": "Bidvantage",
        "tags": ["bidvantage", "capability-statement", "example"],
        "variables": [],
        "is_default": True,
        "file_ref": "Bidvantage Capability Statement Example.pdf",
    },
    {
        "name": "Bidvantage Proposal Submission Checklist",
        "description": (
            "Pre-submission checklist covering content completeness, formatting, "
            "compliance verification, and administrative requirements for "
            "government proposals."
        ),
        "category": "checklist",
        "file_format": "pdf",
        "source": "Bidvantage",
        "tags": ["bidvantage", "checklist", "submission", "compliance"],
        "variables": [],
        "is_default": True,
        "file_ref": "Bidvantage Proposal Submission Checklist.pdf",
    },
    {
        "name": "Bidvantage SAM Registration Guide",
        "description": (
            "Step-by-step guide for registering on SAM.gov, including entity "
            "validation, CAGE code, NAICS codes, and maintaining active status."
        ),
        "category": "guide",
        "file_format": "pdf",
        "source": "Bidvantage",
        "tags": ["bidvantage", "sam.gov", "registration", "guide"],
        "variables": [],
        "is_default": False,
        "file_ref": "Bidvantage SAM Registration Guide.pdf",
    },
    {
        "name": "The Vault Government Contracting eBook",
        "description": (
            "Comprehensive eBook covering government contracting fundamentals: "
            "registration, opportunity identification, proposal writing, pricing "
            "strategies, contract types, and post-award management."
        ),
        "category": "guide",
        "file_format": "pdf",
        "source": "Bidvantage",
        "tags": ["bidvantage", "ebook", "govcon", "training", "reference"],
        "variables": [],
        "is_default": False,
        "file_ref": "The Vault Government Contracting eBook.pdf",
    },
]


def seed_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model("knowledge_vault", "DocumentTemplate")
    for tmpl in BIDVANTAGE_TEMPLATES:
        file_ref = tmpl.pop("file_ref")
        DocumentTemplate.objects.update_or_create(
            name=tmpl["name"],
            defaults={
                **tmpl,
                # Store the relative path; actual file will be copied to
                # MinIO storage by a management command or manual upload.
                "file": f"templates/{file_ref}",
                "file_size": 0,  # Will be updated when file is uploaded
            },
        )


def remove_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model("knowledge_vault", "DocumentTemplate")
    DocumentTemplate.objects.filter(source="Bidvantage").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_vault", "0004_documenttemplate"),
    ]

    operations = [
        migrations.RunPython(seed_templates, remove_templates),
    ]
