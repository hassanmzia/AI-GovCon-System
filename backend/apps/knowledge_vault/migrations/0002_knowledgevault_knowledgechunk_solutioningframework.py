import django.db.models.deletion
import pgvector.django
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_vault", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeVault",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=500)),
                ("category", models.CharField(
                    choices=[
                        ("architecture", "Architecture"),
                        ("legal", "Legal"),
                        ("pricing", "Pricing"),
                        ("security", "Security"),
                        ("proposal", "Proposal"),
                        ("research", "Research"),
                        ("technical", "Technical"),
                        ("general", "General"),
                    ],
                    max_length=50,
                )),
                ("content_type", models.CharField(
                    choices=[
                        ("text", "Text"),
                        ("markdown", "Markdown"),
                        ("code", "Code"),
                        ("image", "Image"),
                        ("table", "Table"),
                        ("pdf", "PDF"),
                        ("url", "URL"),
                    ],
                    default="text",
                    max_length=20,
                )),
                ("content", models.TextField(blank=True, help_text="Text preview (first 10 000 chars)")),
                ("tags", models.JSONField(blank=True, default=list)),
                ("source_url", models.URLField(blank=True)),
                ("file_path", models.CharField(blank=True, help_text="MinIO object key", max_length=500)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Knowledge Vault Item",
                "verbose_name_plural": "Knowledge Vault Items",
            },
        ),
        migrations.CreateModel(
            name="SolutioningFramework",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200, unique=True)),
                ("version", models.CharField(blank=True, max_length=50)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(
                    choices=[
                        ("enterprise_architecture", "Enterprise Architecture"),
                        ("software_architecture", "Software Architecture"),
                        ("agentic", "Agentic / AI Patterns"),
                        ("security", "Security Architecture"),
                        ("cloud", "Cloud Architecture"),
                        ("data", "Data Architecture"),
                        ("integration", "Integration Patterns"),
                    ],
                    max_length=50,
                )),
                ("sections", models.JSONField(blank=True, default=dict)),
                ("use_cases", models.JSONField(blank=True, default=list)),
                ("patterns", models.JSONField(blank=True, default=list)),
                ("reference_url", models.URLField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["category", "name"],
                "verbose_name": "Solutioning Framework",
                "verbose_name_plural": "Solutioning Frameworks",
            },
        ),
        migrations.CreateModel(
            name="KnowledgeChunk",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("vault_item", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="chunks",
                    to="knowledge_vault.knowledgevault",
                )),
                ("document", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="chunks",
                    to="knowledge_vault.knowledgedocument",
                )),
                ("solutioning_framework", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="chunks",
                    to="knowledge_vault.solutioningframework",
                )),
                ("chunk_index", models.IntegerField(default=0)),
                ("content_type", models.CharField(
                    choices=[
                        ("text", "Text"),
                        ("image", "Image"),
                        ("table", "Table"),
                        ("code", "Code"),
                    ],
                    default="text",
                    max_length=20,
                )),
                ("text", models.TextField(blank=True)),
                ("token_count", models.IntegerField(default=0)),
                ("image_url", models.URLField(blank=True)),
                ("image_type", models.CharField(blank=True, max_length=50)),
                ("text_embedding", pgvector.django.VectorField(dimensions=1536, null=True)),
                ("image_embedding", pgvector.django.VectorField(dimensions=512, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "ordering": ["chunk_index"],
            },
        ),
        migrations.AddIndex(
            model_name="knowledgechunk",
            index=models.Index(fields=["vault_item", "chunk_index"], name="kv_chunk_vault_idx"),
        ),
        migrations.AddIndex(
            model_name="knowledgechunk",
            index=models.Index(fields=["document", "chunk_index"], name="kv_chunk_doc_idx"),
        ),
    ]
