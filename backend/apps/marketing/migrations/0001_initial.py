import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('deals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketingCampaign',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True)),
                ('channel', models.CharField(choices=[('email', 'Email'), ('social_media', 'Social Media'), ('webinar', 'Webinar'), ('trade_show', 'Trade Show'), ('direct_outreach', 'Direct Outreach'), ('advertising', 'Advertising'), ('partnership', 'Partnership'), ('other', 'Other')], max_length=50)),
                ('status', models.CharField(choices=[('planning', 'Planning'), ('active', 'Active'), ('paused', 'Paused'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='planning', max_length=20)),
                ('target_audience', models.CharField(blank=True, max_length=500)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('budget', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('goals', models.JSONField(blank=True, default=list)),
                ('metrics', models.JSONField(blank=True, default=dict)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='marketing_campaigns', to=settings.AUTH_USER_MODEL)),
                ('related_deals', models.ManyToManyField(blank=True, related_name='marketing_campaigns', to='deals.deal')),
            ],
            options={
                'verbose_name': 'Marketing Campaign',
                'verbose_name_plural': 'Marketing Campaigns',
                'ordering': ['-created_at'],
            },
        ),
    ]
