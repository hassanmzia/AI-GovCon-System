# Generated migration for pricing app
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
            name='RateCard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('labor_category', models.CharField(max_length=255)),
                ('gsa_equivalent', models.CharField(blank=True, max_length=255)),
                ('gsa_sin', models.CharField(blank=True, max_length=50)),
                ('internal_rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('gsa_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('proposed_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('market_low', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('market_median', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('market_high', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('education_requirement', models.CharField(blank=True, max_length=100)),
                ('experience_years', models.IntegerField(blank=True, null=True)),
                ('clearance_required', models.CharField(blank=True, max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('effective_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'ordering': ['labor_category'],
            },
        ),
        migrations.CreateModel(
            name='ConsultantProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=300)),
                ('hourly_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('skills', models.JSONField(default=list)),
                ('certifications', models.JSONField(default=list)),
                ('clearance_level', models.CharField(blank=True, max_length=50)),
                ('years_experience', models.IntegerField(default=0)),
                ('availability_date', models.DateField(blank=True, null=True)),
                ('utilization_pct', models.FloatField(default=0.0)),
                ('is_key_personnel', models.BooleanField(default=False)),
                ('is_available', models.BooleanField(default=True)),
                ('resume_file', models.FileField(blank=True, upload_to='resumes/')),
                ('bio', models.TextField(blank=True)),
                ('labor_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pricing.ratecard')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PricingScenario',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('strategy_type', models.CharField(choices=[('max_profit', 'Maximum Profit'), ('value_based', 'Value-Based'), ('competitive', 'Competitive'), ('aggressive', 'Aggressive'), ('incumbent_match', 'Incumbent Match'), ('budget_fit', 'Budget Fit'), ('floor', 'Floor')], max_length=50)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=15)),
                ('profit', models.DecimalField(decimal_places=2, max_digits=15)),
                ('margin_pct', models.FloatField()),
                ('probability_of_win', models.FloatField(default=0.0)),
                ('expected_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('competitive_position', models.CharField(blank=True, max_length=50)),
                ('sensitivity_data', models.JSONField(default=dict)),
                ('is_recommended', models.BooleanField(default=False)),
                ('rationale', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-expected_value'],
            },
        ),
        migrations.CreateModel(
            name='PricingIntelligence',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source', models.CharField(max_length=100)),
                ('labor_category', models.CharField(blank=True, max_length=255)),
                ('agency', models.CharField(blank=True, max_length=255)),
                ('rate_low', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('rate_median', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('rate_high', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('data_date', models.DateField(blank=True, null=True)),
                ('raw_data', models.JSONField(default=dict)),
            ],
            options={
                'ordering': ['-data_date'],
            },
        ),
        migrations.CreateModel(
            name='PricingApproval',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('decided_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pricing_approvals', to=settings.AUTH_USER_MODEL)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_approvals', to='deals.deal')),
                ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pricing_requests', to=settings.AUTH_USER_MODEL)),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingscenario')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LOEEstimate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('version', models.IntegerField(default=1)),
                ('wbs_elements', models.JSONField(default=list)),
                ('total_hours', models.IntegerField(default=0)),
                ('total_ftes', models.FloatField(default=0.0)),
                ('duration_months', models.IntegerField(default=12)),
                ('staffing_plan', models.JSONField(default=dict)),
                ('key_personnel', models.JSONField(default=list)),
                ('estimation_method', models.CharField(choices=[('analogous', 'Analogous'), ('parametric', 'Parametric'), ('three_point', 'Three-Point'), ('wbs_bottom_up', 'WBS Bottom-Up')], default='three_point', max_length=50)),
                ('confidence_level', models.FloatField(default=0.7)),
                ('assumptions', models.JSONField(default=list)),
                ('risks', models.JSONField(default=list)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loe_estimates', to='deals.deal')),
            ],
            options={
                'ordering': ['-version'],
            },
        ),
        migrations.CreateModel(
            name='CostModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('version', models.IntegerField(default=1)),
                ('direct_labor', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('fringe_benefits', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('overhead', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('odcs', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('subcontractor_costs', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('travel', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('materials', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('ga_expense', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('fringe_rate', models.FloatField(default=0.3)),
                ('overhead_rate', models.FloatField(default=0.4)),
                ('ga_rate', models.FloatField(default=0.1)),
                ('labor_detail', models.JSONField(default=list)),
                ('odc_detail', models.JSONField(default=list)),
                ('travel_detail', models.JSONField(default=list)),
                ('sub_detail', models.JSONField(default=list)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cost_models', to='deals.deal')),
                ('loe', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pricing.loeestimate')),
            ],
            options={
                'ordering': ['-version'],
            },
        ),
        migrations.AddField(
            model_name='pricingscenario',
            name='cost_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.costmodel'),
        ),
        migrations.AddField(
            model_name='pricingscenario',
            name='deal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_scenarios', to='deals.deal'),
        ),
    ]
