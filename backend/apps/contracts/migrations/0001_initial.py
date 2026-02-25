# Generated migration for contracts app
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
            name='ContractTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=300)),
                ('contract_type', models.CharField(choices=[('FFP', 'Firm Fixed Price'), ('T&M', 'Time & Materials'), ('CPFF', 'Cost Plus Fixed Fee'), ('CPAF', 'Cost Plus Award Fee'), ('CPIF', 'Cost Plus Incentive Fee'), ('IDIQ', 'Indefinite Delivery/Indefinite Quantity'), ('BPA', 'Blanket Purchase Agreement')], max_length=10)),
                ('description', models.TextField(blank=True)),
                ('template_content', models.TextField()),
                ('required_clauses', models.JSONField(default=list)),
                ('optional_clauses', models.JSONField(default=list)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContractClause',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('clause_number', models.CharField(max_length=50)),
                ('title', models.CharField(max_length=500)),
                ('clause_text', models.TextField()),
                ('clause_type', models.CharField(choices=[('standard', 'Standard'), ('special', 'Special'), ('custom', 'Custom'), ('far_reference', 'FAR Reference'), ('dfars_reference', 'DFARS Reference')], max_length=20)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('is_negotiable', models.BooleanField(default=True)),
                ('risk_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['clause_number'],
            },
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contract_number', models.CharField(blank=True, max_length=100, unique=True)),
                ('title', models.CharField(max_length=500)),
                ('contract_type', models.CharField(choices=[('FFP', 'Firm Fixed Price'), ('T&M', 'Time & Materials'), ('CPFF', 'Cost Plus Fixed Fee'), ('CPAF', 'Cost Plus Award Fee'), ('CPIF', 'Cost Plus Incentive Fee'), ('IDIQ', 'Indefinite Delivery/Indefinite Quantity'), ('BPA', 'Blanket Purchase Agreement')], max_length=10)),
                ('status', models.CharField(choices=[('drafting', 'Drafting'), ('review', 'Review'), ('negotiation', 'Negotiation'), ('pending_execution', 'Pending Execution'), ('executed', 'Executed'), ('active', 'Active'), ('modification', 'Modification'), ('closeout', 'Closeout'), ('terminated', 'Terminated'), ('expired', 'Expired')], default='drafting', max_length=20)),
                ('total_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('period_of_performance_start', models.DateField(blank=True, null=True)),
                ('period_of_performance_end', models.DateField(blank=True, null=True)),
                ('option_years', models.IntegerField(default=0)),
                ('contracting_officer', models.CharField(blank=True, max_length=255)),
                ('contracting_officer_email', models.EmailField(blank=True, max_length=254)),
                ('cor_name', models.CharField(blank=True, max_length=255)),
                ('awarded_date', models.DateField(blank=True, null=True)),
                ('executed_date', models.DateField(blank=True, null=True)),
                ('document_file', models.FileField(blank=True, upload_to='contracts/')),
                ('notes', models.TextField(blank=True)),
                ('clauses', models.ManyToManyField(blank=True, to='contracts.contractclause')),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='deals.deal')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contracts.contracttemplate')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContractVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('version_number', models.IntegerField()),
                ('change_type', models.CharField(choices=[('initial', 'Initial'), ('modification', 'Modification'), ('amendment', 'Amendment'), ('option_exercise', 'Option Exercise'), ('administrative', 'Administrative')], default='initial', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('changes', models.JSONField(default=dict)),
                ('document_file', models.FileField(blank=True, upload_to='contract_versions/')),
                ('effective_date', models.DateField(blank=True, null=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='contracts.contract')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-version_number'],
                'unique_together': {('contract', 'version_number')},
            },
        ),
        migrations.CreateModel(
            name='ContractModification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('modification_number', models.CharField(max_length=50)),
                ('modification_type', models.CharField(choices=[('bilateral', 'Bilateral'), ('unilateral', 'Unilateral'), ('administrative', 'Administrative'), ('funding', 'Funding'), ('scope', 'Scope'), ('period_extension', 'Period Extension')], max_length=20)),
                ('description', models.TextField()),
                ('impact_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('new_total_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('effective_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('proposed', 'Proposed'), ('reviewing', 'Reviewing'), ('approved', 'Approved'), ('executed', 'Executed'), ('rejected', 'Rejected')], default='proposed', max_length=20)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_modifications', to=settings.AUTH_USER_MODEL)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modifications', to='contracts.contract')),
                ('requested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requested_modifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContractMilestone',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=500)),
                ('milestone_type', models.CharField(choices=[('deliverable', 'Deliverable'), ('payment', 'Payment'), ('review', 'Review'), ('option', 'Option'), ('transition', 'Transition'), ('closeout', 'Closeout')], max_length=20)),
                ('due_date', models.DateField()),
                ('status', models.CharField(choices=[('upcoming', 'Upcoming'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('overdue', 'Overdue'), ('waived', 'Waived')], default='upcoming', max_length=20)),
                ('completed_date', models.DateField(blank=True, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('deliverable_description', models.TextField(blank=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contract_milestones', to=settings.AUTH_USER_MODEL)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milestones', to='contracts.contract')),
            ],
            options={
                'ordering': ['due_date'],
            },
        ),
    ]
