from django.contrib import admin

from apps.legal.models import (
    ComplianceAssessment,
    ContractReviewNote,
    FARClause,
    LegalRisk,
    RegulatoryRequirement,
)


@admin.register(FARClause)
class FARClauseAdmin(admin.ModelAdmin):
    list_display = [
        "clause_number",
        "title",
        "category",
        "is_mandatory",
        "applicability_threshold",
        "last_updated",
    ]
    list_filter = ["category", "is_mandatory"]
    search_fields = ["clause_number", "title", "full_text", "plain_language_summary"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["clause_number"]


@admin.register(RegulatoryRequirement)
class RegulatoryRequirementAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "title",
        "regulation_source",
        "effective_date",
        "expiration_date",
    ]
    list_filter = ["regulation_source"]
    search_fields = ["reference_number", "title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["regulation_source", "reference_number"]


@admin.register(ComplianceAssessment)
class ComplianceAssessmentAdmin(admin.ModelAdmin):
    list_display = [
        "deal",
        "assessed_by",
        "status",
        "far_compliance_score",
        "dfars_compliance_score",
        "overall_risk_level",
        "created_at",
    ]
    list_filter = ["status", "overall_risk_level"]
    search_fields = ["deal__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "assessed_by"]
    filter_horizontal = ["clauses_reviewed"]
    date_hierarchy = "created_at"


@admin.register(LegalRisk)
class LegalRiskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "deal",
        "risk_type",
        "severity",
        "probability",
        "status",
        "identified_by",
        "created_at",
    ]
    list_filter = ["risk_type", "severity", "probability", "status"]
    search_fields = ["title", "description", "deal__title", "mitigation_strategy"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "identified_by"]
    date_hierarchy = "created_at"


@admin.register(ContractReviewNote)
class ContractReviewNoteAdmin(admin.ModelAdmin):
    list_display = [
        "section",
        "deal",
        "reviewer",
        "note_type",
        "priority",
        "status",
        "created_at",
    ]
    list_filter = ["note_type", "priority", "status"]
    search_fields = ["section", "note_text", "deal__title", "response"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "reviewer"]
    date_hierarchy = "created_at"
