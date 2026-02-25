# Generated migration for security_compliance app
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('deals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityFramework',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('version', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('control_families', models.JSONField(default=list)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name', 'version'],
                'unique_together': {('name', 'version')},
            },
        ),
        migrations.CreateModel(
            name='SecurityControl',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('control_id', models.CharField(max_length=50)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField()),
                ('family', models.CharField(max_length=255)),
                ('priority', models.CharField(choices=[('P1', 'P1 - High'), ('P2', 'P2 - Moderate'), ('P3', 'P3 - Low')], max_length=2)),
                ('baseline_impact', models.CharField(choices=[('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High')], max_length=10)),
                ('implementation_guidance', models.TextField(blank=True)),
                ('assessment_procedures', models.JSONField(default=list)),
                ('related_controls', models.JSONField(default=list)),
                ('framework', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='controls', to='security_compliance.securityframework')),
            ],
            options={
                'ordering': ['framework', 'control_id'],
                'unique_together': {('framework', 'control_id')},
            },
        ),
        migrations.CreateModel(
            name='SecurityControlMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('implementation_status', models.CharField(choices=[('planned', 'Planned'), ('partial', 'Partially Implemented'), ('implemented', 'Implemented'), ('not_applicable', 'Not Applicable')], default='planned', max_length=20)),
                ('responsible_party', models.CharField(blank=True, max_length=255)),
                ('implementation_description', models.TextField(blank=True)),
                ('evidence_references', models.JSONField(default=list)),
                ('assessment_date', models.DateField(blank=True, null=True)),
                ('gap_description', models.TextField(blank=True)),
                ('remediation_plan', models.TextField(blank=True)),
                ('target_completion', models.DateField(blank=True, null=True)),
                ('assessed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='security_assessments', to=settings.AUTH_USER_MODEL)),
                ('control', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deal_mappings', to='security_compliance.securitycontrol')),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='security_control_mappings', to='deals.deal')),
            ],
            options={
                'ordering': ['deal', 'control'],
                'unique_together': {('deal', 'control')},
            },
        ),
        migrations.CreateModel(
            name='SecurityComplianceReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('report_type', models.CharField(choices=[('gap_analysis', 'Gap Analysis'), ('readiness_assessment', 'Readiness Assessment'), ('poam', 'Plan of Action & Milestones'), ('ssp_section', 'SSP Section'), ('authorization_package', 'Authorization Package')], max_length=30)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('in_review', 'In Review'), ('final', 'Final')], default='draft', max_length=20)),
                ('overall_compliance_pct', models.FloatField(default=0.0)),
                ('controls_implemented', models.IntegerField(default=0)),
                ('controls_partial', models.IntegerField(default=0)),
                ('controls_planned', models.IntegerField(default=0)),
                ('controls_na', models.IntegerField(default=0)),
                ('gaps', models.JSONField(default=list)),
                ('findings', models.JSONField(default=list)),
                ('poam_items', models.JSONField(default=list)),
                ('generated_by', models.CharField(blank=True, max_length=255)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_compliance_reports', to=settings.AUTH_USER_MODEL)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compliance_reports', to='deals.deal')),
                ('framework', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='security_compliance.securityframework')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ComplianceRequirement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source_document', models.CharField(blank=True, max_length=500)),
                ('requirement_text', models.TextField()),
                ('category', models.CharField(choices=[('security_clearance', 'Security Clearance'), ('facility_clearance', 'Facility Clearance'), ('data_handling', 'Data Handling'), ('encryption', 'Encryption'), ('access_control', 'Access Control'), ('audit', 'Audit'), ('incident_response', 'Incident Response'), ('training', 'Training'), ('physical_security', 'Physical Security')], max_length=30)),
                ('priority', models.CharField(choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], default='medium', max_length=10)),
                ('current_status', models.CharField(choices=[('compliant', 'Compliant'), ('gap', 'Gap'), ('in_progress', 'In Progress'), ('not_assessed', 'Not Assessed')], default='not_assessed', max_length=20)),
                ('gap_description', models.TextField(blank=True)),
                ('remediation_cost_estimate', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('notes', models.TextField(blank=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compliance_requirements', to='deals.deal')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
