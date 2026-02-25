# Generated migration for proposals app
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
            name='ProposalTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('volumes', models.JSONField(default=list)),
                ('is_default', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Proposal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=500)),
                ('version', models.IntegerField(default=1)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pink_team', 'Pink Team Review'), ('red_team', 'Red Team Review'), ('gold_team', 'Gold Team Review'), ('final', 'Final'), ('submitted', 'Submitted')], default='draft', max_length=30)),
                ('win_themes', models.JSONField(default=list)),
                ('discriminators', models.JSONField(default=list)),
                ('executive_summary', models.TextField(blank=True)),
                ('total_requirements', models.IntegerField(default=0)),
                ('compliant_count', models.IntegerField(default=0)),
                ('compliance_percentage', models.FloatField(default=0.0)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposals', to='deals.deal')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='proposals.proposaltemplate')),
            ],
            options={
                'ordering': ['-version'],
            },
        ),
        migrations.CreateModel(
            name='ProposalSection',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('volume', models.CharField(max_length=100)),
                ('section_number', models.CharField(max_length=50)),
                ('title', models.CharField(max_length=300)),
                ('order', models.IntegerField(default=0)),
                ('ai_draft', models.TextField(blank=True)),
                ('human_content', models.TextField(blank=True)),
                ('final_content', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('not_started', 'Not Started'), ('ai_drafted', 'AI Drafted'), ('in_review', 'In Review'), ('revised', 'Revised'), ('approved', 'Approved')], default='not_started', max_length=20)),
                ('word_count', models.IntegerField(default=0)),
                ('page_limit', models.IntegerField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('proposal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='proposals.proposal')),
            ],
            options={
                'ordering': ['volume', 'order'],
            },
        ),
        migrations.CreateModel(
            name='ReviewCycle',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('review_type', models.CharField(choices=[('pink', 'Pink Team'), ('red', 'Red Team'), ('gold', 'Gold Team')], max_length=20)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='scheduled', max_length=20)),
                ('scheduled_date', models.DateTimeField(blank=True, null=True)),
                ('completed_date', models.DateTimeField(blank=True, null=True)),
                ('overall_score', models.FloatField(blank=True, null=True)),
                ('summary', models.TextField(blank=True)),
                ('proposal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='proposals.proposal')),
                ('reviewers', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReviewComment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('comment_type', models.CharField(choices=[('strength', 'Strength'), ('weakness', 'Weakness'), ('suggestion', 'Suggestion'), ('must_fix', 'Must Fix')], max_length=20)),
                ('content', models.TextField()),
                ('is_resolved', models.BooleanField(default=False)),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='proposals.reviewcycle')),
                ('reviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_comments', to='proposals.proposalsection')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
