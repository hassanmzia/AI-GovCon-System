import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("deals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="KPISnapshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField(unique=True)),
                ("active_deals", models.IntegerField(default=0)),
                ("pipeline_value", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("open_proposals", models.IntegerField(default=0)),
                ("win_rate", models.FloatField(blank=True, null=True)),
                ("avg_fit_score", models.FloatField(blank=True, null=True)),
                ("closed_won", models.IntegerField(default=0)),
                ("closed_lost", models.IntegerField(default=0)),
                ("total_opportunities", models.IntegerField(default=0)),
                ("pending_approvals", models.IntegerField(default=0)),
                ("new_deals_this_week", models.IntegerField(default=0)),
                ("stage_distribution", models.JSONField(blank=True, default=dict)),
                ("proposal_distribution", models.JSONField(blank=True, default=dict)),
                ("revenue_by_type", models.JSONField(blank=True, default=dict)),
            ],
            options={"ordering": ["-date"], "verbose_name": "KPI Snapshot", "verbose_name_plural": "KPI Snapshots"},
        ),
        migrations.CreateModel(
            name="DealVelocityMetric",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="velocity_metrics", to="deals.deal")),
                ("stage", models.CharField(max_length=50)),
                ("entered_at", models.DateTimeField()),
                ("exited_at", models.DateTimeField(blank=True, null=True)),
                ("days_in_stage", models.FloatField(blank=True, null=True)),
            ],
            options={"ordering": ["entered_at"], "unique_together": {("deal", "stage")}},
        ),
        migrations.CreateModel(
            name="WinLossAnalysis",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deal", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="win_loss_analysis", to="deals.deal")),
                ("outcome", models.CharField(choices=[("won", "Won"), ("lost", "Lost"), ("no_bid", "No Bid")], max_length=20)),
                ("close_date", models.DateField()),
                ("final_value", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("primary_loss_reason", models.CharField(blank=True, max_length=100)),
                ("competitor_name", models.CharField(blank=True, max_length=300)),
                ("competitor_price", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("our_price", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("lessons_learned", models.TextField(blank=True)),
                ("win_themes", models.JSONField(blank=True, default=list)),
                ("loss_factors", models.JSONField(blank=True, default=list)),
                ("ai_analysis", models.TextField(blank=True)),
                ("recorded_by", models.CharField(blank=True, max_length=200)),
            ],
            options={"ordering": ["-close_date"]},
        ),
        migrations.CreateModel(
            name="AgentPerformanceMetric",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("agent_name", models.CharField(max_length=100)),
                ("date", models.DateField()),
                ("total_runs", models.IntegerField(default=0)),
                ("successful_runs", models.IntegerField(default=0)),
                ("failed_runs", models.IntegerField(default=0)),
                ("avg_duration_seconds", models.FloatField(blank=True, null=True)),
                ("avg_tokens_used", models.IntegerField(blank=True, null=True)),
                ("total_cost_usd", models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ("user_feedback_positive", models.IntegerField(default=0)),
                ("user_feedback_negative", models.IntegerField(default=0)),
            ],
            options={"ordering": ["-date"], "unique_together": {("agent_name", "date")}},
        ),
    ]
