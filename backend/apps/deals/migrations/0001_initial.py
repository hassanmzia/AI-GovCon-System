# Generated migration for deals app
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('opportunities', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Deal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=500)),
                ('stage', models.CharField(choices=[('intake', 'Intake'), ('qualify', 'Qualify'), ('bid_no_bid', 'Bid/No-Bid Decision'), ('capture_plan', 'Capture Planning'), ('proposal_dev', 'Proposal Development'), ('red_team', 'Red Team Review'), ('final_review', 'Final Review'), ('submit', 'Submission'), ('post_submit', 'Post-Submission'), ('award_pending', 'Award Pending'), ('contract_setup', 'Contract Setup'), ('delivery', 'Delivery/Execution'), ('closed_won', 'Closed - Won'), ('closed_lost', 'Closed - Lost'), ('no_bid', 'No-Bid')], default='intake', max_length=30)),
                ('priority', models.IntegerField(choices=[(1, 'Critical'), (2, 'High'), (3, 'Medium'), (4, 'Low')], default=3)),
                ('estimated_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('win_probability', models.FloatField(default=0.0)),
                ('fit_score', models.FloatField(default=0.0)),
                ('strategic_score', models.FloatField(default=0.0)),
                ('composite_score', models.FloatField(default=0.0)),
                ('ai_recommendation', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('stage_entered_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('bid_decision_date', models.DateTimeField(blank=True, null=True)),
                ('submission_date', models.DateTimeField(blank=True, null=True)),
                ('award_date', models.DateTimeField(blank=True, null=True)),
                ('outcome', models.CharField(blank=True, choices=[('won', 'Won'), ('lost', 'Lost'), ('no_bid', 'No Bid'), ('cancelled', 'Cancelled')], max_length=20)),
                ('outcome_notes', models.TextField(blank=True)),
                ('opportunity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals', to='opportunities.opportunity')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_deals', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('stage', models.CharField(max_length=30)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True)),
                ('default_priority', models.IntegerField(default=3)),
                ('days_until_due', models.IntegerField(default=7)),
                ('is_required', models.BooleanField(default=True)),
                ('is_auto_completable', models.BooleanField(default=False)),
                ('order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['stage', 'order'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('blocked', 'Blocked'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('priority', models.IntegerField(default=3)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('stage', models.CharField(blank=True, max_length=30)),
                ('is_ai_generated', models.BooleanField(default=False)),
                ('is_auto_completable', models.BooleanField(default=False)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tasks', to=settings.AUTH_USER_MODEL)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='deals.deal')),
            ],
            options={
                'ordering': ['priority', 'due_date'],
            },
        ),
        migrations.CreateModel(
            name='DealStageHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('from_stage', models.CharField(blank=True, max_length=30)),
                ('to_stage', models.CharField(max_length=30)),
                ('reason', models.TextField(blank=True)),
                ('duration_in_previous_stage', models.DurationField(blank=True, null=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stage_history', to='deals.deal')),
                ('transitioned_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content', models.TextField()),
                ('is_ai_generated', models.BooleanField(default=False)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='deals.deal')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Approval',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approval_type', models.CharField(choices=[('bid_no_bid', 'Bid/No-Bid Decision'), ('pricing', 'Pricing Approval'), ('proposal_final', 'Final Proposal Approval'), ('submission', 'Submission Authorization'), ('contract_terms', 'Contract Terms Approval')], max_length=30)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('ai_recommendation', models.TextField(blank=True)),
                ('ai_confidence', models.FloatField(blank=True, null=True)),
                ('decision_rationale', models.TextField(blank=True)),
                ('decided_at', models.DateTimeField(blank=True, null=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approvals', to='deals.deal')),
                ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approvals_requested', to=settings.AUTH_USER_MODEL)),
                ('requested_from', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approvals_pending', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('metadata', models.JSONField(default=dict)),
                ('is_ai_action', models.BooleanField(default=False)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='deals.deal')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='deal',
            name='team',
            field=models.ManyToManyField(blank=True, related_name='deal_team', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['stage'], name='deals_deal_stage_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['owner'], name='deals_deal_owner_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['priority'], name='deals_deal_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='deal',
            index=models.Index(fields=['due_date'], name='deals_deal_due_date_idx'),
        ),
    ]
