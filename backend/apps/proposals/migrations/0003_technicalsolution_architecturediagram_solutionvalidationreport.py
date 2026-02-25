import django.db.models.deletion
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("deals", "0001_initial"),
        ("proposals", "0002_alter_proposaltemplate_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="TechnicalSolution",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deal", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="technical_solutions",
                    to="deals.deal",
                )),
                ("iteration_count", models.IntegerField(default=1)),
                ("selected_frameworks", models.JSONField(default=list)),
                ("requirement_analysis", models.JSONField(blank=True, default=dict)),
                ("executive_summary", models.TextField(blank=True)),
                ("architecture_pattern", models.CharField(blank=True, max_length=200)),
                ("core_components", models.JSONField(blank=True, default=list)),
                ("technology_stack", models.JSONField(blank=True, default=dict)),
                ("integration_points", models.JSONField(blank=True, default=list)),
                ("scalability_approach", models.TextField(blank=True)),
                ("security_architecture", models.TextField(blank=True)),
                ("deployment_model", models.CharField(blank=True, max_length=100)),
                ("technical_volume", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ArchitectureDiagram",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("technical_solution", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="diagrams",
                    to="proposals.technicalsolution",
                )),
                ("title", models.CharField(max_length=300)),
                ("diagram_type", models.CharField(
                    choices=[
                        ("system_context", "System Context"),
                        ("container", "Container"),
                        ("component", "Component"),
                        ("sequence", "Sequence"),
                        ("data_flow", "Data Flow"),
                        ("deployment", "Deployment"),
                        ("entity_relationship", "Entity Relationship"),
                    ],
                    max_length=30,
                )),
                ("mermaid_code", models.TextField(blank=True)),
                ("d2_code", models.TextField(blank=True)),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["diagram_type"],
            },
        ),
        migrations.CreateModel(
            name="SolutionValidationReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("technical_solution", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="validation_report",
                    to="proposals.technicalsolution",
                )),
                ("overall_quality", models.CharField(
                    choices=[
                        ("excellent", "Excellent"),
                        ("good", "Good"),
                        ("fair", "Fair"),
                        ("poor", "Poor"),
                    ],
                    max_length=20,
                )),
                ("score", models.FloatField(blank=True, null=True)),
                ("passed", models.BooleanField(default=False)),
                ("issues", models.JSONField(blank=True, default=list)),
                ("suggestions", models.JSONField(blank=True, default=list)),
                ("compliance_gaps", models.JSONField(blank=True, default=list)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
