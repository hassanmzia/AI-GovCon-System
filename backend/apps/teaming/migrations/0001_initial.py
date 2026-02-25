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
            name='TeamingPartnership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('partner_company', models.CharField(max_length=500)),
                ('partner_contact_name', models.CharField(blank=True, max_length=255)),
                ('partner_contact_email', models.EmailField(blank=True, max_length=254)),
                ('partner_contact_phone', models.CharField(blank=True, max_length=20)),
                ('relationship_type', models.CharField(choices=[('prime_contractor', 'Prime Contractor'), ('subcontractor', 'Subcontractor'), ('joint_venture', 'Joint Venture'), ('mentor', 'Mentor'), ('protege', 'Protege'), ('strategic_partner', 'Strategic Partner')], max_length=50)),
                ('status', models.CharField(choices=[('prospect', 'Prospect'), ('negotiating', 'Negotiating'), ('active', 'Active'), ('completed', 'Completed'), ('terminated', 'Terminated')], default='prospect', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('responsibilities', models.JSONField(blank=True, default=list)),
                ('revenue_share_percentage', models.FloatField(blank=True, null=True)),
                ('signed_agreement', models.BooleanField(default=False)),
                ('agreement_date', models.DateField(blank=True, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('terms_and_conditions', models.TextField(blank=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teaming_partnerships', to='deals.deal')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_partnerships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Teaming Partnership',
                'verbose_name_plural': 'Teaming Partnerships',
                'ordering': ['-created_at'],
            },
        ),
    ]
