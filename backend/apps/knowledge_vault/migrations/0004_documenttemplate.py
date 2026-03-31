import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("knowledge_vault", "0003_rename_kv_chunk_vault_idx_knowledge_v_vault_i_c14849_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=500)),
                ("description", models.TextField(blank=True)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("proposal", "Proposal Template"),
                            ("capability_statement", "Capability Statement"),
                            ("past_performance", "Past Performance"),
                            ("email", "Email Template"),
                            ("contract", "Contract Template"),
                            ("checklist", "Checklist"),
                            ("pitch_deck", "Pitch Deck"),
                            ("guide", "Guide / Reference"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "file_format",
                    models.CharField(
                        choices=[
                            ("docx", "Word Document (.docx)"),
                            ("pdf", "PDF (.pdf)"),
                            ("pptx", "PowerPoint (.pptx)"),
                            ("xlsx", "Excel (.xlsx)"),
                            ("txt", "Plain Text"),
                        ],
                        default="docx",
                        max_length=10,
                    ),
                ),
                ("file", models.FileField(blank=True, upload_to="templates/")),
                (
                    "file_size",
                    models.IntegerField(
                        default=0, help_text="File size in bytes"
                    ),
                ),
                (
                    "variables",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text='List of variable dicts: [{"name": "company_name", "label": "Company Name", "default": ""}]',
                    ),
                ),
                ("version", models.CharField(default="1.0", max_length=50)),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        help_text="Origin e.g. 'Bidvantage', 'Custom', 'FAR Library'",
                        max_length=100,
                    ),
                ),
                ("tags", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Default template for its category",
                    ),
                ),
                ("usage_count", models.IntegerField(default=0)),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="uploaded_templates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Document Template",
                "verbose_name_plural": "Document Templates",
                "ordering": ["category", "name"],
            },
        ),
    ]
