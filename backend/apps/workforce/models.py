from django.db import models

from apps.core.models import BaseModel


class Employee(BaseModel):
    """Employee record for workforce planning and clearance tracking."""

    CLEARANCE_TYPE_CHOICES = [
        ("none", "None"),
        ("confidential", "Confidential"),
        ("secret", "Secret"),
        ("top_secret", "Top Secret"),
        ("ts_sci", "TS/SCI"),
    ]

    CLEARANCE_STATUS_CHOICES = [
        ("active", "Active"),
        ("pending", "Pending"),
        ("expired", "Expired"),
        ("not_required", "Not Required"),
    ]

    name = models.CharField(max_length=300)
    email = models.EmailField(unique=True)
    title = models.CharField(max_length=300, blank=True)
    department = models.CharField(max_length=200, blank=True)
    clearance_type = models.CharField(
        max_length=20,
        choices=CLEARANCE_TYPE_CHOICES,
        default="none",
    )
    clearance_status = models.CharField(
        max_length=20,
        choices=CLEARANCE_STATUS_CHOICES,
        default="not_required",
    )
    clearance_expiry = models.DateField(null=True, blank=True)
    hire_date = models.DateField()
    skills = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    labor_category = models.CharField(max_length=255, blank=True)
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    utilization_target = models.FloatField(default=0.85)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["department"], name="idx_employee_department"),
            models.Index(fields=["clearance_type"], name="idx_employee_clearance"),
            models.Index(fields=["labor_category"], name="idx_employee_labor_cat"),
            models.Index(fields=["is_active"], name="idx_employee_active"),
        ]

    def __str__(self):
        return f"{self.name} ({self.title})"


class SkillMatrix(BaseModel):
    """Detailed skill proficiency record for an employee."""

    PROFICIENCY_CHOICES = [
        (1, "Beginner"),
        (2, "Intermediate"),
        (3, "Proficient"),
        (4, "Advanced"),
        (5, "Expert"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="skill_matrix"
    )
    skill_name = models.CharField(max_length=200)
    proficiency_level = models.IntegerField(choices=PROFICIENCY_CHOICES, default=1)
    years_experience = models.FloatField(default=0.0)
    last_assessed_date = models.DateField(null=True, blank=True)
    verified_by = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["employee", "skill_name"]
        unique_together = [["employee", "skill_name"]]

    def __str__(self):
        return f"{self.employee.name} — {self.skill_name} (L{self.proficiency_level})"


class ClearanceRecord(BaseModel):
    """Historical clearance investigation and status tracking."""

    CLEARANCE_TYPE_CHOICES = [
        ("none", "None"),
        ("confidential", "Confidential"),
        ("secret", "Secret"),
        ("top_secret", "Top Secret"),
        ("ts_sci", "TS/SCI"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("pending", "Pending"),
        ("expired", "Expired"),
        ("denied", "Denied"),
        ("revoked", "Revoked"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="clearance_records"
    )
    clearance_type = models.CharField(max_length=20, choices=CLEARANCE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    investigation_type = models.CharField(max_length=100, blank=True)
    submitted_date = models.DateField(null=True, blank=True)
    granted_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    sponsoring_agency = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-granted_date"]

    def __str__(self):
        return (
            f"{self.employee.name} — "
            f"{self.get_clearance_type_display()} ({self.get_status_display()})"
        )


class Assignment(BaseModel):
    """Employee assignment to a contract or deal."""

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="assignments"
    )
    contract = models.ForeignKey(
        "contracts.Contract",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workforce_assignments",
    )
    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workforce_assignments",
    )
    role = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    allocation_percentage = models.FloatField(
        default=100.0,
        help_text="Percentage of employee time allocated (0-100).",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["employee", "is_active"], name="idx_assign_emp_active"),
        ]

    def __str__(self):
        target = self.contract or self.deal or "Unassigned"
        return f"{self.employee.name} → {target} ({self.role})"


class HiringRequisition(BaseModel):
    """Hiring requisition linked to pipeline demand."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("sourcing", "Sourcing"),
        ("interviewing", "Interviewing"),
        ("offer", "Offer Extended"),
        ("filled", "Filled"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        (1, "Critical"),
        (2, "High"),
        (3, "Medium"),
        (4, "Low"),
    ]

    title = models.CharField(max_length=500)
    department = models.CharField(max_length=200, blank=True)
    labor_category = models.CharField(max_length=255, blank=True)
    clearance_required = models.CharField(max_length=20, blank=True)
    skills_required = models.JSONField(default=list)
    min_experience_years = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open"
    )
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3)
    linked_deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hiring_requisitions",
    )
    justification = models.TextField(blank=True)
    target_start_date = models.DateField(null=True, blank=True)
    filled_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="filled_requisitions",
    )

    class Meta:
        ordering = ["priority", "-created_at"]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"
