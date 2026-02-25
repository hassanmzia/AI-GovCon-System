# Generated migration for opportunities app

from django.db import migrations, models
import django.db.models.deletion
import pgvector.django
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpportunitySource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('source_type', models.CharField(choices=[('samgov', 'SAM.gov API'), ('web_scrape', 'Web Scrape'), ('fpds', 'FPDS'), ('usaspending', 'USASpending'), ('manual', 'Manual Entry')], max_length=50)),
                ('base_url', models.URLField(blank=True)),
                ('api_key_env_var', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('scan_frequency_hours', models.IntegerField(default=4)),
                ('last_scan_at', models.DateTimeField(blank=True, null=True)),
                ('last_scan_status', models.CharField(default='pending', max_length=20)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Opportunity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notice_id', models.CharField(max_length=255, unique=True)),
                ('source_url', models.URLField(blank=True)),
                ('raw_data', models.JSONField(default=dict)),
                ('title', models.CharField(max_length=1000)),
                ('description', models.TextField(blank=True)),
                ('agency', models.CharField(blank=True, max_length=500)),
                ('sub_agency', models.CharField(blank=True, max_length=500)),
                ('office', models.CharField(blank=True, max_length=500)),
                ('notice_type', models.CharField(blank=True, max_length=100)),
                ('sol_number', models.CharField(blank=True, max_length=255)),
                ('naics_code', models.CharField(blank=True, max_length=10)),
                ('naics_description', models.CharField(blank=True, max_length=500)),
                ('psc_code', models.CharField(blank=True, max_length=10)),
                ('set_aside', models.CharField(blank=True, max_length=200)),
                ('classification_code', models.CharField(blank=True, max_length=50)),
                ('posted_date', models.DateTimeField(blank=True, null=True)),
                ('response_deadline', models.DateTimeField(blank=True, null=True)),
                ('archive_date', models.DateTimeField(blank=True, null=True)),
                ('estimated_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('award_type', models.CharField(blank=True, max_length=100)),
                ('place_of_performance', models.CharField(blank=True, max_length=500)),
                ('place_city', models.CharField(blank=True, max_length=200)),
                ('place_state', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[('active', 'Active'), ('closed', 'Closed'), ('cancelled', 'Cancelled'), ('awarded', 'Awarded'), ('archived', 'Archived')], default='active', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('incumbent', models.CharField(blank=True, max_length=500)),
                ('keywords', models.JSONField(default=list)),
                ('attachments', models.JSONField(default=list)),
                ('contacts', models.JSONField(default=list)),
                ('description_embedding', pgvector.django.VectorField(dimensions=1536, null=True)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opportunities', to='opportunities.opportunitysource')),
            ],
            options={
                'ordering': ['-posted_date'],
            },
        ),
        migrations.CreateModel(
            name='OpportunityScore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('total_score', models.FloatField(default=0.0)),
                ('recommendation', models.CharField(choices=[('strong_bid', 'Strong Bid'), ('bid', 'Bid'), ('consider', 'Consider'), ('no_bid', 'No Bid')], default='consider', max_length=20)),
                ('naics_match', models.FloatField(default=0.0)),
                ('psc_match', models.FloatField(default=0.0)),
                ('keyword_overlap', models.FloatField(default=0.0)),
                ('capability_similarity', models.FloatField(default=0.0)),
                ('past_performance_relevance', models.FloatField(default=0.0)),
                ('value_fit', models.FloatField(default=0.0)),
                ('deadline_feasibility', models.FloatField(default=0.0)),
                ('set_aside_match', models.FloatField(default=0.0)),
                ('competition_intensity', models.FloatField(default=0.0)),
                ('risk_factors', models.FloatField(default=0.0)),
                ('score_explanation', models.JSONField(default=dict)),
                ('ai_rationale', models.TextField(blank=True)),
                ('scored_at', models.DateTimeField(auto_now=True)),
                ('opportunity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='score', to='opportunities.opportunity')),
            ],
            options={
                'ordering': ['-total_score'],
            },
        ),
        migrations.CreateModel(
            name='CompanyProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('uei_number', models.CharField(blank=True, max_length=20)),
                ('cage_code', models.CharField(blank=True, max_length=10)),
                ('naics_codes', models.JSONField(default=list)),
                ('psc_codes', models.JSONField(default=list)),
                ('set_aside_categories', models.JSONField(default=list)),
                ('capability_statement', models.TextField(blank=True)),
                ('capability_embedding', pgvector.django.VectorField(dimensions=1536, null=True)),
                ('core_competencies', models.JSONField(default=list)),
                ('past_performance_summary', models.TextField(blank=True)),
                ('key_personnel', models.JSONField(default=list)),
                ('certifications', models.JSONField(default=list)),
                ('clearance_levels', models.JSONField(default=list)),
                ('contract_vehicles', models.JSONField(default=list)),
                ('target_agencies', models.JSONField(default=list)),
                ('target_value_min', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('target_value_max', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('is_primary', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DailyDigest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField(unique=True)),
                ('total_scanned', models.IntegerField(default=0)),
                ('total_new', models.IntegerField(default=0)),
                ('total_scored', models.IntegerField(default=0)),
                ('summary', models.TextField(blank=True)),
                ('is_sent', models.BooleanField(default=False)),
                ('opportunities', models.ManyToManyField(related_name='digests', to='opportunities.opportunity')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['notice_id'], name='opportunities_o_notice__idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['agency'], name='opportunities_o_agency_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['naics_code'], name='opportunities_o_naics_c_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['status'], name='opportunities_o_status_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['response_deadline'], name='opportunities_o_respons_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['posted_date'], name='opportunities_o_posted__idx'),
        ),
    ]
