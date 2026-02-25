from django.contrib import admin

from apps.security_compliance.models import (
    ComplianceRequirement,
    SecurityComplianceReport,
    SecurityControl,
    SecurityControlMapping,
    SecurityFramework,
)


class SecurityControlInline(admin.TabularInline):
    model = SecurityControl
    extra = 0
    fields = [
        "control_id",
        "title",
        "family",
        "priority",
        "baseline_impact",
    ]
    ordering = ["control_id"]


@admin.register(SecurityFramework)
class SecurityFrameworkAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "version",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "name"]
    search_fields = ["name", "version", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [SecurityControlInline]


@admin.register(SecurityControl)
class SecurityControlAdmin(admin.ModelAdmin):
    list_display = [
        "control_id",
        "title",
        "framework",
        "family",
        "priority",
        "baseline_impact",
    ]
    list_filter = ["framework", "family", "priority", "baseline_impact"]
    search_fields = [
        "control_id",
        "title",
        "description",
        "framework__name",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["framework"]


@admin.register(SecurityControlMapping)
class SecurityControlMappingAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "control",
        "implementation_status",
        "responsible_party",
        "assessed_by",
        "assessment_date",
        "target_completion",
    ]
    list_filter = [
        "implementation_status",
        "control__framework",
        "assessment_date",
    ]
    search_fields = [
        "deal__title",
        "control__control_id",
        "control__title",
        "responsible_party",
        "implementation_description",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "control", "assessed_by"]
    date_hierarchy = "created_at"


@admin.register(SecurityComplianceReport)
class SecurityComplianceReportAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "framework",
        "report_type",
        "status",
        "overall_compliance_pct",
        "controls_implemented",
        "controls_partial",
        "controls_planned",
        "controls_na",
        "generated_by",
        "approved_by",
        "created_at",
    ]
    list_filter = ["report_type", "status", "framework"]
    search_fields = [
        "deal__title",
        "framework__name",
        "generated_by",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "framework", "approved_by"]
    date_hierarchy = "created_at"


@admin.register(ComplianceRequirement)
class ComplianceRequirementAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "category",
        "priority",
        "current_status",
        "source_document",
        "remediation_cost_estimate",
        "created_at",
    ]
    list_filter = ["category", "priority", "current_status"]
    search_fields = [
        "deal__title",
        "requirement_text",
        "source_document",
        "gap_description",
        "notes",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal"]
    date_hierarchy = "created_at"
