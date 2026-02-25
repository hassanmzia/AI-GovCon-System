from django.contrib import admin

from .models import Amendment, ComplianceMatrixItem, RFPDocument, RFPRequirement


@admin.register(RFPDocument)
class RFPDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "deal",
        "document_type",
        "extraction_status",
        "file_name",
        "file_size",
        "page_count",
        "version",
        "created_at",
    )
    list_filter = ("document_type", "extraction_status", "created_at")
    search_fields = ("title", "file_name", "deal__title")
    readonly_fields = (
        "id",
        "extracted_text",
        "page_count",
        "extracted_dates",
        "extracted_page_limits",
        "submission_instructions",
        "evaluation_criteria",
        "required_forms",
        "required_certifications",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("deal", "parent_document")


@admin.register(RFPRequirement)
class RFPRequirementAdmin(admin.ModelAdmin):
    list_display = (
        "requirement_id",
        "rfp_document",
        "requirement_type",
        "category",
        "section_reference",
        "created_at",
    )
    list_filter = ("requirement_type", "category")
    search_fields = ("requirement_id", "requirement_text", "section_reference")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("requirement_id",)
    raw_id_fields = ("rfp_document",)


@admin.register(ComplianceMatrixItem)
class ComplianceMatrixItemAdmin(admin.ModelAdmin):
    list_display = (
        "requirement",
        "rfp_document",
        "compliance_status",
        "response_status",
        "response_owner",
        "proposal_section",
        "created_at",
    )
    list_filter = ("compliance_status", "response_status")
    search_fields = (
        "requirement__requirement_id",
        "requirement__requirement_text",
        "proposal_section",
        "compliance_notes",
    )
    readonly_fields = ("id", "ai_draft_response", "created_at", "updated_at")
    ordering = ("requirement__requirement_id",)
    raw_id_fields = ("rfp_document", "requirement", "response_owner")


@admin.register(Amendment)
class AmendmentAdmin(admin.ModelAdmin):
    list_display = (
        "amendment_number",
        "rfp_document",
        "title",
        "is_material",
        "requires_compliance_update",
        "reviewed",
        "detected_at",
    )
    list_filter = ("is_material", "requires_compliance_update", "reviewed")
    search_fields = ("title", "summary")
    readonly_fields = (
        "id",
        "changes",
        "is_material",
        "requires_compliance_update",
        "detected_at",
        "created_at",
        "updated_at",
    )
    ordering = ("amendment_number",)
    raw_id_fields = ("rfp_document",)
