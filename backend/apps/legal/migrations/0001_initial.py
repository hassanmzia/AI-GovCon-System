# Generated migration for legal app
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
            name='FARClause',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('clause_number', models.CharField(max_length=20, unique=True)),
                ('title', models.CharField(max_length=500)),
                ('full_text', models.TextField()),
                ('category', models.CharField(choices=[('general', 'General'), ('procurement', 'Procurement'), ('labor', 'Labor'), ('security', 'Security'), ('reporting', 'Reporting'), ('small_business', 'Small Business'), ('other', 'Other')], default='general', max_length=20)),
                ('is_mandatory', models.BooleanField(default=False)),
                ('applicability_threshold', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('related_dfars', models.JSONField(blank=True, default=list)),
                ('plain_language_summary', models.TextField(blank=True)),
                ('compliance_checklist', models.JSONField(blank=True, default=list)),
                ('last_updated', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'FAR Clause',
                'verbose_name_plural': 'FAR Clauses',
                'ordering': ['clause_number'],
            },
        ),
        migrations.CreateModel(
            name='RegulatoryRequirement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('regulation_source', models.CharField(choices=[('FAR', 'FAR'), ('DFARS', 'DFARS'), ('agency_specific', 'Agency Specific'), ('OMB', 'OMB'), ('executive_order', 'Executive Order')], max_length=20)),
                ('reference_number', models.CharField(max_length=50)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField()),
                ('compliance_criteria', models.JSONField(blank=True, default=list)),
                ('applicable_contract_types', models.JSONField(blank=True, default=list)),
                ('applicable_set_asides', models.JSONField(blank=True, default=list)),
                ('penalty_description', models.TextField(blank=True)),
                ('effective_date', models.DateField(blank=True, null=True)),
                ('expiration_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Regulatory Requirement',
                'verbose_name_plural': 'Regulatory Requirements',
                'ordering': ['regulation_source', 'reference_number'],
            },
        ),
        migrations.CreateModel(
            name='LegalRisk',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('risk_type', models.CharField(choices=[('contractual', 'Contractual'), ('regulatory', 'Regulatory'), ('ip', 'Intellectual Property'), ('liability', 'Liability'), ('teaming', 'Teaming'), ('subcontracting', 'Subcontracting'), ('conflict_of_interest', 'Conflict of Interest'), ('organizational_conflict', 'Organizational Conflict')], max_length=30)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField()),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='low', max_length=10)),
                ('probability', models.CharField(choices=[('unlikely', 'Unlikely'), ('possible', 'Possible'), ('likely', 'Likely'), ('certain', 'Certain')], default='possible', max_length=10)),
                ('mitigation_strategy', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('identified', 'Identified'), ('mitigating', 'Mitigating'), ('mitigated', 'Mitigated'), ('accepted', 'Accepted')], default='identified', max_length=20)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legal_risks', to='deals.deal')),
                ('identified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='identified_legal_risks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Legal Risk',
                'verbose_name_plural': 'Legal Risks',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ComplianceAssessment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('far_compliance_score', models.FloatField(default=0.0)),
                ('dfars_compliance_score', models.FloatField(default=0.0)),
                ('overall_risk_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='low', max_length=10)),
                ('findings', models.JSONField(blank=True, default=list)),
                ('recommendations', models.JSONField(blank=True, default=list)),
                ('non_compliant_items', models.JSONField(blank=True, default=list)),
                ('assessed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compliance_assessments', to=settings.AUTH_USER_MODEL)),
                ('clauses_reviewed', models.ManyToManyField(blank=True, related_name='compliance_assessments', to='legal.farclause')),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compliance_assessments', to='deals.deal')),
            ],
            options={
                'verbose_name': 'Compliance Assessment',
                'verbose_name_plural': 'Compliance Assessments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContractReviewNote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('section', models.CharField(max_length=200)),
                ('note_text', models.TextField()),
                ('note_type', models.CharField(choices=[('concern', 'Concern'), ('suggestion', 'Suggestion'), ('approval', 'Approval'), ('question', 'Question')], default='concern', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10)),
                ('status', models.CharField(choices=[('open', 'Open'), ('addressed', 'Addressed'), ('dismissed', 'Dismissed')], default='open', max_length=20)),
                ('response', models.TextField(blank=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contract_review_notes', to='deals.deal')),
                ('reviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contract_review_notes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Contract Review Note',
                'verbose_name_plural': 'Contract Review Notes',
                'ordering': ['-created_at'],
            },
        ),
    ]
