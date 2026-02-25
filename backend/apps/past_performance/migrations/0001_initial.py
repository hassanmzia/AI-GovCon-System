# Generated migration for past_performance app
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
            name='PastPerformance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project_name', models.CharField(max_length=500)),
                ('contract_number', models.CharField(blank=True, max_length=100)),
                ('client_agency', models.CharField(max_length=500)),
                ('client_name', models.CharField(blank=True, max_length=300)),
                ('client_email', models.EmailField(blank=True, max_length=254)),
                ('client_phone', models.CharField(blank=True, max_length=50)),
                ('description', models.TextField()),
                ('relevance_keywords', models.JSONField(default=list)),
                ('naics_codes', models.JSONField(default=list)),
                ('technologies', models.JSONField(default=list)),
                ('domains', models.JSONField(default=list)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('contract_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('contract_type', models.CharField(blank=True, max_length=50)),
                ('performance_rating', models.CharField(blank=True, max_length=50)),
                ('cpars_rating', models.CharField(blank=True, max_length=50)),
                ('on_time_delivery', models.BooleanField(default=True)),
                ('within_budget', models.BooleanField(default=True)),
                ('key_achievements', models.JSONField(default=list)),
                ('metrics', models.JSONField(default=dict)),
                ('narrative', models.TextField(blank=True)),
                ('lessons_learned', models.TextField(blank=True)),
                ('description_embedding', pgvector.django.VectorField(dimensions=1536, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_verified', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Past Performance Records',
                'ordering': ['-end_date'],
            },
        ),
        migrations.CreateModel(
            name='PastPerformanceMatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('relevance_score', models.FloatField()),
                ('match_rationale', models.TextField(blank=True)),
                ('matched_keywords', models.JSONField(default=list)),
                ('opportunity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='past_perf_matches', to='opportunities.opportunity')),
                ('past_performance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='past_performance.pastperformance')),
            ],
            options={
                'ordering': ['-relevance_score'],
                'unique_together': {('opportunity', 'past_performance')},
            },
        ),
    ]
