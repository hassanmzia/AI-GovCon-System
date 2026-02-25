# Generated migration for rfp app
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import pgvector.django
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('deals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RFPDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=500)),
                ('document_type', models.CharField(choices=[('rfp', 'RFP'), ('rfi', 'RFI'), ('rfq', 'RFQ'), ('sources_sought', 'Sources Sought'), ('amendment', 'Amendment'), ('qa_response', 'Q&A Response'), ('attachment', 'Attachment'), ('other', 'Other')], max_length=50)),
                ('file', models.FileField(upload_to='rfp_documents/')),
                ('file_name', models.CharField(max_length=500)),
                ('file_size', models.IntegerField(default=0)),
                ('file_type', models.CharField(blank=True, max_length=50)),
                ('extraction_status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('extracted_text', models.TextField(blank=True)),
                ('page_count', models.IntegerField(blank=True, null=True)),
                ('extracted_dates', models.JSONField(default=dict)),
                ('extracted_page_limits', models.JSONField(default=dict)),
                ('submission_instructions', models.TextField(blank=True)),
                ('evaluation_criteria', models.JSONField(default=list)),
                ('required_forms', models.JSONField(default=list)),
                ('required_certifications', models.JSONField(default=list)),
                ('version', models.IntegerField(default=1)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rfp_documents', to='deals.deal')),
                ('parent_document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rfp.rfpdocument')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RFPRequirement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('requirement_id', models.CharField(max_length=50)),
                ('requirement_text', models.TextField()),
                ('section_reference', models.CharField(blank=True, max_length=200)),
                ('requirement_type', models.CharField(choices=[('mandatory', 'Mandatory'), ('desirable', 'Desirable'), ('informational', 'Informational')], default='mandatory', max_length=30)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('evaluation_weight', models.FloatField(blank=True, null=True)),
                ('requirement_embedding', pgvector.django.VectorField(dimensions=1536, null=True)),
                ('rfp_document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requirements', to='rfp.rfpdocument')),
            ],
            options={
                'ordering': ['requirement_id'],
            },
        ),
        migrations.CreateModel(
            name='Amendment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amendment_number', models.IntegerField()),
                ('title', models.CharField(blank=True, max_length=500)),
                ('file', models.FileField(blank=True, upload_to='rfp_amendments/')),
                ('summary', models.TextField(blank=True)),
                ('changes', models.JSONField(default=list)),
                ('is_material', models.BooleanField(default=False)),
                ('requires_compliance_update', models.BooleanField(default=False)),
                ('detected_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed', models.BooleanField(default=False)),
                ('rfp_document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amendments', to='rfp.rfpdocument')),
            ],
            options={
                'ordering': ['amendment_number'],
            },
        ),
        migrations.CreateModel(
            name='ComplianceMatrixItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('proposal_section', models.CharField(blank=True, max_length=200)),
                ('proposal_page', models.CharField(blank=True, max_length=50)),
                ('response_status', models.CharField(choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('drafted', 'Drafted'), ('reviewed', 'Reviewed'), ('final', 'Final')], default='not_started', max_length=20)),
                ('ai_draft_response', models.TextField(blank=True)),
                ('human_final_response', models.TextField(blank=True)),
                ('compliance_status', models.CharField(choices=[('compliant', 'Compliant'), ('partial', 'Partially Compliant'), ('non_compliant', 'Non-Compliant'), ('not_assessed', 'Not Assessed')], default='not_assessed', max_length=20)),
                ('compliance_notes', models.TextField(blank=True)),
                ('evidence_references', models.JSONField(default=list)),
                ('requirement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compliance_items', to='rfp.rfprequirement')),
                ('response_owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('rfp_document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compliance_items', to='rfp.rfpdocument')),
            ],
            options={
                'ordering': ['requirement__requirement_id'],
            },
        ),
    ]
