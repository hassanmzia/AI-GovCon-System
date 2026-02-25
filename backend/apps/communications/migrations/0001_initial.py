# Generated migration for communications app
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
            name='CommunicationThread',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subject', models.CharField(max_length=255)),
                ('thread_type', models.CharField(choices=[('internal', 'Internal'), ('client', 'Client'), ('agency', 'Agency'), ('vendor', 'Vendor'), ('teaming_partner', 'Teaming Partner')], max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('archived', 'Archived'), ('resolved', 'Resolved')], default='active', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=10)),
                ('tags', models.JSONField(default=list)),
                ('deal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='communication_threads', to='deals.deal')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ThreadParticipant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(choices=[('owner', 'Owner'), ('member', 'Member'), ('observer', 'Observer')], max_length=10)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('last_read_at', models.DateTimeField(blank=True, null=True)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='thread_participants', to='communications.communicationthread')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='thread_participations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('thread', 'user')},
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content', models.TextField()),
                ('message_type', models.CharField(choices=[('text', 'Text'), ('system', 'System'), ('ai_generated', 'AI Generated'), ('file_share', 'File Share')], default='text', max_length=20)),
                ('attachments', models.JSONField(default=list)),
                ('is_edited', models.BooleanField(default=False)),
                ('edited_at', models.DateTimeField(blank=True, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='communications.message')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='communications.communicationthread')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='ClarificationQuestion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rfp_section', models.CharField(blank=True, default='', max_length=255)),
                ('question_text', models.TextField()),
                ('question_number', models.IntegerField(blank=True, null=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('answered', 'Answered'), ('withdrawn', 'Withdrawn')], default='draft', max_length=20)),
                ('is_government_question', models.BooleanField(default=False)),
                ('source', models.CharField(choices=[('vendor_submitted', 'Vendor Submitted'), ('government_issued', 'Government Issued'), ('internal', 'Internal')], default='internal', max_length=20)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clarification_questions', to='deals.deal')),
                ('submitted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_questions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['question_number', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='ClarificationAnswer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('answer_text', models.TextField()),
                ('answered_by', models.CharField(blank=True, default='', max_length=255)),
                ('answered_at', models.DateTimeField(blank=True, null=True)),
                ('impacts_proposal', models.BooleanField(default=False)),
                ('amendment_reference', models.CharField(blank=True, default='', max_length=255)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='communications.clarificationquestion')),
            ],
            options={
                'ordering': ['-answered_at'],
            },
        ),
        migrations.CreateModel(
            name='QAImpactMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('proposal_section', models.CharField(max_length=255)),
                ('impact_description', models.TextField()),
                ('action_required', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='impact_mappings', to='communications.clarificationanswer')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_impact_mappings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
