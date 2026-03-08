import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contracts", "0001_initial"),
        ("deals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Employee",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=300)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("title", models.CharField(blank=True, max_length=300)),
                ("department", models.CharField(blank=True, max_length=200)),
                ("clearance_type", models.CharField(choices=[("none", "None"), ("confidential", "Confidential"), ("secret", "Secret"), ("top_secret", "Top Secret"), ("ts_sci", "TS/SCI")], default="none", max_length=20)),
                ("clearance_status", models.CharField(choices=[("active", "Active"), ("pending", "Pending"), ("expired", "Expired"), ("not_required", "Not Required")], default="not_required", max_length=20)),
                ("clearance_expiry", models.DateField(blank=True, null=True)),
                ("hire_date", models.DateField()),
                ("skills", models.JSONField(default=list)),
                ("certifications", models.JSONField(default=list)),
                ("labor_category", models.CharField(blank=True, max_length=255)),
                ("hourly_rate", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("utilization_target", models.FloatField(default=0.85)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="SkillMatrix",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("skill_name", models.CharField(max_length=200)),
                ("proficiency_level", models.IntegerField(choices=[(1, "Beginner"), (2, "Intermediate"), (3, "Proficient"), (4, "Advanced"), (5, "Expert")], default=1)),
                ("years_experience", models.FloatField(default=0.0)),
                ("last_assessed_date", models.DateField(blank=True, null=True)),
                ("verified_by", models.CharField(blank=True, max_length=300)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skill_matrix", to="workforce.employee")),
            ],
            options={
                "ordering": ["employee", "skill_name"],
                "unique_together": {("employee", "skill_name")},
            },
        ),
        migrations.CreateModel(
            name="ClearanceRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("clearance_type", models.CharField(choices=[("none", "None"), ("confidential", "Confidential"), ("secret", "Secret"), ("top_secret", "Top Secret"), ("ts_sci", "TS/SCI")], max_length=20)),
                ("status", models.CharField(choices=[("active", "Active"), ("pending", "Pending"), ("expired", "Expired"), ("denied", "Denied"), ("revoked", "Revoked")], default="pending", max_length=20)),
                ("investigation_type", models.CharField(blank=True, max_length=100)),
                ("submitted_date", models.DateField(blank=True, null=True)),
                ("granted_date", models.DateField(blank=True, null=True)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("sponsoring_agency", models.CharField(blank=True, max_length=300)),
                ("notes", models.TextField(blank=True)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="clearance_records", to="workforce.employee")),
            ],
            options={
                "ordering": ["-granted_date"],
            },
        ),
        migrations.CreateModel(
            name="Assignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(max_length=200)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("allocation_percentage", models.FloatField(default=100.0, help_text="Percentage of employee time allocated (0-100).")),
                ("is_active", models.BooleanField(default=True)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="workforce.employee")),
                ("contract", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="workforce_assignments", to="contracts.contract")),
                ("deal", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="workforce_assignments", to="deals.deal")),
            ],
            options={
                "ordering": ["-start_date"],
            },
        ),
        migrations.CreateModel(
            name="HiringRequisition",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=500)),
                ("department", models.CharField(blank=True, max_length=200)),
                ("labor_category", models.CharField(blank=True, max_length=255)),
                ("clearance_required", models.CharField(blank=True, max_length=20)),
                ("skills_required", models.JSONField(default=list)),
                ("min_experience_years", models.IntegerField(default=0)),
                ("status", models.CharField(choices=[("open", "Open"), ("sourcing", "Sourcing"), ("interviewing", "Interviewing"), ("offer", "Offer Extended"), ("filled", "Filled"), ("cancelled", "Cancelled")], default="open", max_length=20)),
                ("priority", models.IntegerField(choices=[(1, "Critical"), (2, "High"), (3, "Medium"), (4, "Low")], default=3)),
                ("justification", models.TextField(blank=True)),
                ("target_start_date", models.DateField(blank=True, null=True)),
                ("linked_deal", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="hiring_requisitions", to="deals.deal")),
                ("filled_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="filled_requisitions", to="workforce.employee")),
            ],
            options={
                "ordering": ["priority", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="employee",
            index=models.Index(fields=["department"], name="idx_employee_department"),
        ),
        migrations.AddIndex(
            model_name="employee",
            index=models.Index(fields=["clearance_type"], name="idx_employee_clearance"),
        ),
        migrations.AddIndex(
            model_name="employee",
            index=models.Index(fields=["labor_category"], name="idx_employee_labor_cat"),
        ),
        migrations.AddIndex(
            model_name="employee",
            index=models.Index(fields=["is_active"], name="idx_employee_active"),
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(fields=["employee", "is_active"], name="idx_assign_emp_active"),
        ),
    ]
