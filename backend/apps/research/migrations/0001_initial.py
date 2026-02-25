# Generated migration for research app
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
            name='ResearchProject',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('research_type', models.CharField(choices=[('market_analysis', 'Market Analysis'), ('competitive_intel', 'Competitive Intelligence'), ('agency_analysis', 'Agency Analysis'), ('technology_trends', 'Technology Trends'), ('incumbent_analysis', 'Incumbent Analysis'), ('regulatory_landscape', 'Regulatory Landscape')], max_length=30)),
                ('parameters', models.JSONField(blank=True, default=dict)),
                ('findings', models.JSONField(blank=True, default=dict)),
                ('executive_summary', models.TextField(blank=True)),
                ('sources', models.JSONField(blank=True, default=list)),
                ('ai_agent_trace_id', models.UUIDField(blank=True, null=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='research_projects', to='deals.deal')),
                ('requested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='research_projects', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ResearchSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('url', models.URLField(max_length=2000)),
                ('title', models.CharField(max_length=500)),
                ('source_type', models.CharField(choices=[('web', 'Web'), ('government_db', 'Government Database'), ('news', 'News'), ('academic', 'Academic'), ('industry_report', 'Industry Report')], max_length=20)),
                ('content', models.TextField(blank=True)),
                ('relevance_score', models.FloatField(default=0.0)),
                ('extracted_data', models.JSONField(blank=True, default=dict)),
                ('fetched_at', models.DateTimeField(blank=True, null=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='research_sources', to='research.researchproject')),
            ],
            options={
                'ordering': ['-relevance_score'],
            },
        ),
        migrations.CreateModel(
            name='CompetitorProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('cage_code', models.CharField(blank=True, max_length=20)),
                ('duns_number', models.CharField(blank=True, max_length=20)),
                ('website', models.URLField(blank=True, max_length=500)),
                ('naics_codes', models.JSONField(blank=True, default=list)),
                ('contract_vehicles', models.JSONField(blank=True, default=list)),
                ('key_personnel', models.JSONField(blank=True, default=list)),
                ('revenue_range', models.CharField(blank=True, max_length=100)),
                ('employee_count', models.IntegerField(blank=True, null=True)),
                ('past_performance_summary', models.TextField(blank=True)),
                ('strengths', models.JSONField(blank=True, default=list)),
                ('weaknesses', models.JSONField(blank=True, default=list)),
                ('win_rate', models.FloatField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MarketIntelligence',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.CharField(choices=[('budget_trends', 'Budget Trends'), ('policy_changes', 'Policy Changes'), ('technology_shifts', 'Technology Shifts'), ('procurement_patterns', 'Procurement Patterns'), ('workforce_trends', 'Workforce Trends')], max_length=30)),
                ('title', models.CharField(max_length=500)),
                ('summary', models.TextField()),
                ('detail', models.JSONField(blank=True, default=dict)),
                ('impact_assessment', models.TextField(blank=True)),
                ('affected_naics', models.JSONField(blank=True, default=list)),
                ('affected_agencies', models.JSONField(blank=True, default=list)),
                ('source_url', models.URLField(blank=True, max_length=2000)),
                ('published_date', models.DateField(blank=True, null=True)),
                ('relevance_window_days', models.IntegerField(default=90)),
            ],
            options={
                'verbose_name_plural': 'Market intelligence',
                'ordering': ['-published_date'],
            },
        ),
        migrations.AddIndex(
            model_name='researchproject',
            index=models.Index(fields=['deal', 'research_type'], name='research_researchproject_deal_research_type_idx'),
        ),
        migrations.AddIndex(
            model_name='researchproject',
            index=models.Index(fields=['status'], name='research_researchproject_status_idx'),
        ),
        migrations.AddIndex(
            model_name='competitorprofile',
            index=models.Index(fields=['cage_code'], name='research_competitorprofile_cage_code_idx'),
        ),
        migrations.AddIndex(
            model_name='competitorprofile',
            index=models.Index(fields=['is_active'], name='research_competitorprofile_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='marketintelligence',
            index=models.Index(fields=['category'], name='research_marketintelligence_category_idx'),
        ),
        migrations.AddIndex(
            model_name='marketintelligence',
            index=models.Index(fields=['published_date'], name='research_marketintelligence_published_date_idx'),
        ),
    ]
