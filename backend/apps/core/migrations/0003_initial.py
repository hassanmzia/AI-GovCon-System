# Generated migration for core models - AITraceLog

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_initial'),
        ('deals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AITraceLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent_name', models.CharField(max_length=100)),
                ('action', models.CharField(max_length=255)),
                ('prompt', models.TextField()),
                ('tool_calls', models.JSONField(default=list)),
                ('retrieved_sources', models.JSONField(default=list)),
                ('output', models.TextField()),
                ('approval_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('auto', 'Auto-approved')], default='pending', max_length=20)),
                ('cost_usd', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('latency_ms', models.IntegerField(blank=True, null=True)),
                ('model_name', models.CharField(blank=True, default='', max_length=100)),
                ('trace_id', models.CharField(blank=True, default='', max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('deal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_traces', to='deals.deal')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
