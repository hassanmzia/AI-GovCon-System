# Generated migration for strategy app
from django.db import migrations, models
import django.db.models.deletion
import pgvector.django
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('opportunities', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyStrategy',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('version', models.IntegerField(default=1)),
                ('effective_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('mission_statement', models.TextField(blank=True)),
                ('vision_3_year', models.TextField(blank=True)),
                ('target_revenue', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('target_win_rate', models.FloatField(default=0.4)),
                ('target_margin', models.FloatField(default=0.12)),
                ('target_agencies', models.JSONField(default=list)),
                ('target_domains', models.JSONField(default=list)),
                ('target_naics_codes', models.JSONField(default=list)),
                ('growth_markets', models.JSONField(default=list)),
                ('mature_markets', models.JSONField(default=list)),
                ('exit_markets', models.JSONField(default=list)),
                ('differentiators', models.JSONField(default=list)),
                ('win_themes', models.JSONField(default=list)),
                ('pricing_philosophy', models.TextField(blank=True)),
                ('teaming_strategy', models.TextField(blank=True)),
                ('max_concurrent_proposals', models.IntegerField(default=5)),
                ('available_key_personnel', models.JSONField(default=list)),
                ('clearance_capacity', models.JSONField(default=dict)),
                ('strategy_embedding', pgvector.django.VectorField(dimensions=1536, null=True)),
            ],
            options={
                'verbose_name_plural': 'Company Strategies',
                'ordering': ['-version'],
            },
        ),
        migrations.CreateModel(
            name='StrategicGoal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(choices=[('revenue', 'Revenue Growth'), ('market_entry', 'New Market Entry'), ('market_share', 'Market Share Defense'), ('capability', 'Capability Building'), ('relationship', 'Client Relationship'), ('portfolio', 'Portfolio Balance'), ('profitability', 'Profitability')], max_length=50)),
                ('metric', models.CharField(max_length=100)),
                ('current_value', models.FloatField(default=0.0)),
                ('target_value', models.FloatField()),
                ('deadline', models.DateField()),
                ('weight', models.FloatField(default=1.0)),
                ('status', models.CharField(choices=[('on_track', 'On Track'), ('at_risk', 'At Risk'), ('behind', 'Behind'), ('achieved', 'Achieved')], default='on_track', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goals', to='strategy.companystrategy')),
            ],
            options={
                'ordering': ['-weight', 'deadline'],
            },
        ),
        migrations.CreateModel(
            name='StrategicScore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('strategic_score', models.FloatField(default=0.0)),
                ('composite_score', models.FloatField(default=0.0)),
                ('agency_alignment', models.FloatField(default=0.0)),
                ('domain_alignment', models.FloatField(default=0.0)),
                ('growth_market_bonus', models.FloatField(default=0.0)),
                ('portfolio_balance', models.FloatField(default=0.0)),
                ('revenue_contribution', models.FloatField(default=0.0)),
                ('capacity_fit', models.FloatField(default=0.0)),
                ('relationship_value', models.FloatField(default=0.0)),
                ('competitive_positioning', models.FloatField(default=0.0)),
                ('bid_recommendation', models.CharField(choices=[('bid', 'BID'), ('no_bid', 'NO BID'), ('conditional_bid', 'CONDITIONAL BID')], default='conditional_bid', max_length=20)),
                ('strategic_rationale', models.TextField(blank=True)),
                ('opportunity_cost', models.TextField(blank=True)),
                ('portfolio_impact', models.TextField(blank=True)),
                ('resource_impact', models.TextField(blank=True)),
                ('scored_at', models.DateTimeField(auto_now=True)),
                ('opportunity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='strategic_score', to='opportunities.opportunity')),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='strategy.companystrategy')),
            ],
            options={
                'ordering': ['-strategic_score'],
            },
        ),
        migrations.CreateModel(
            name='PortfolioSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('snapshot_date', models.DateField()),
                ('active_deals', models.IntegerField(default=0)),
                ('total_pipeline_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('weighted_pipeline', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('deals_by_agency', models.JSONField(default=dict)),
                ('deals_by_domain', models.JSONField(default=dict)),
                ('deals_by_stage', models.JSONField(default=dict)),
                ('deals_by_size', models.JSONField(default=dict)),
                ('capacity_utilization', models.FloatField(default=0.0)),
                ('concentration_risk', models.JSONField(default=dict)),
                ('strategic_alignment_score', models.FloatField(default=0.0)),
                ('ai_recommendations', models.JSONField(default=list)),
                ('strategy', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='strategy.companystrategy')),
            ],
            options={
                'ordering': ['-snapshot_date'],
            },
        ),
    ]
