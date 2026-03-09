from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contracts", "0002_alter_contracttemplate_options_and_more"),
    ]

    operations = [
        # ── ContractTemplate: rename fields ──
        migrations.RenameField(
            model_name="contracttemplate",
            old_name="contract_type",
            new_name="template_type",
        ),
        migrations.RenameField(
            model_name="contracttemplate",
            old_name="template_content",
            new_name="content",
        ),
        migrations.RemoveField(model_name="contracttemplate", name="required_clauses"),
        migrations.RemoveField(model_name="contracttemplate", name="optional_clauses"),
        migrations.RemoveField(model_name="contracttemplate", name="version"),
        migrations.AddField(
            model_name="contracttemplate",
            name="variables",
            field=models.JSONField(default=list),
        ),
        # ── ContractClause: rename / replace fields ──
        migrations.RenameField(
            model_name="contractclause",
            old_name="clause_text",
            new_name="full_text",
        ),
        migrations.RemoveField(model_name="contractclause", name="clause_type"),
        migrations.RemoveField(model_name="contractclause", name="is_negotiable"),
        migrations.RemoveField(model_name="contractclause", name="notes"),
        migrations.AddField(
            model_name="contractclause",
            name="source",
            field=models.CharField(
                choices=[
                    ("far", "FAR"),
                    ("dfars", "DFARS"),
                    ("agency", "Agency Specific"),
                    ("custom", "Custom"),
                ],
                default="far",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="contractclause",
            name="is_mandatory",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="contractclause",
            name="flow_down_required",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="contractclause",
            name="negotiation_guidance",
            field=models.TextField(blank=True),
        ),
        # ── ContractVersion: rename / replace fields ──
        migrations.RenameField(
            model_name="contractversion",
            old_name="description",
            new_name="content",
        ),
        migrations.RenameField(
            model_name="contractversion",
            old_name="created_by",
            new_name="changed_by",
        ),
        migrations.RemoveField(model_name="contractversion", name="changes"),
        migrations.RemoveField(model_name="contractversion", name="document_file"),
        migrations.AddField(
            model_name="contractversion",
            name="change_summary",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="contractversion",
            name="redlines",
            field=models.JSONField(default=dict),
        ),
    ]
