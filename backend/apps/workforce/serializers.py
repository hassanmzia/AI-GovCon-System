from rest_framework import serializers

from apps.workforce.models import (
    Assignment,
    ClearanceRecord,
    Employee,
    HiringRequisition,
    SkillMatrix,
)


# ── Employee ─────────────────────────────────────────────


class EmployeeSerializer(serializers.ModelSerializer):
    clearance_type_display = serializers.CharField(
        source="get_clearance_type_display", read_only=True
    )
    clearance_status_display = serializers.CharField(
        source="get_clearance_status_display", read_only=True
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "email",
            "title",
            "department",
            "clearance_type",
            "clearance_type_display",
            "clearance_status",
            "clearance_status_display",
            "clearance_expiry",
            "hire_date",
            "skills",
            "certifications",
            "labor_category",
            "hourly_rate",
            "utilization_target",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── SkillMatrix ──────────────────────────────────────────


class SkillMatrixSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.name", read_only=True
    )
    proficiency_level_display = serializers.CharField(
        source="get_proficiency_level_display", read_only=True
    )

    class Meta:
        model = SkillMatrix
        fields = [
            "id",
            "employee",
            "employee_name",
            "skill_name",
            "proficiency_level",
            "proficiency_level_display",
            "years_experience",
            "last_assessed_date",
            "verified_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── ClearanceRecord ──────────────────────────────────────


class ClearanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.name", read_only=True
    )
    clearance_type_display = serializers.CharField(
        source="get_clearance_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = ClearanceRecord
        fields = [
            "id",
            "employee",
            "employee_name",
            "clearance_type",
            "clearance_type_display",
            "status",
            "status_display",
            "investigation_type",
            "submitted_date",
            "granted_date",
            "expiry_date",
            "sponsoring_agency",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── Assignment ───────────────────────────────────────────


class AssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.name", read_only=True
    )

    class Meta:
        model = Assignment
        fields = [
            "id",
            "employee",
            "employee_name",
            "contract",
            "deal",
            "role",
            "start_date",
            "end_date",
            "allocation_percentage",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── HiringRequisition ───────────────────────────────────


class HiringRequisitionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    filled_by_name = serializers.CharField(
        source="filled_by.name", read_only=True, default=None
    )

    class Meta:
        model = HiringRequisition
        fields = [
            "id",
            "title",
            "department",
            "labor_category",
            "clearance_required",
            "skills_required",
            "min_experience_years",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "linked_deal",
            "justification",
            "target_start_date",
            "filled_by",
            "filled_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
