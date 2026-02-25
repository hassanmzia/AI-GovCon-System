import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='KnowledgeDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(choices=[('template', 'Template'), ('guide', 'Guide'), ('best_practice', 'Best Practice'), ('case_study', 'Case Study'), ('regulatory_reference', 'Regulatory Reference'), ('tool', 'Tool'), ('lesson_learned', 'Lesson Learned'), ('other', 'Other')], max_length=50)),
                ('content', models.TextField()),
                ('file_url', models.URLField(blank=True)),
                ('file_name', models.CharField(blank=True, max_length=500)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('review', 'In Review'), ('approved', 'Approved'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('keywords', models.JSONField(blank=True, default=list)),
                ('version', models.CharField(default='1.0', max_length=50)),
                ('is_public', models.BooleanField(default=False)),
                ('downloads', models.IntegerField(default=0)),
                ('views', models.IntegerField(default=0)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='knowledge_documents_authored', to=settings.AUTH_USER_MODEL)),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='knowledge_documents_reviewed', to=settings.AUTH_USER_MODEL)),
                ('related_documents', models.ManyToManyField(blank=True, related_name='related_to', to='knowledge_vault.knowledgedocument')),
            ],
            options={
                'verbose_name': 'Knowledge Document',
                'verbose_name_plural': 'Knowledge Documents',
                'ordering': ['-created_at'],
            },
        ),
    ]
