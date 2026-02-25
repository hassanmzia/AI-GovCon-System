from rest_framework import serializers

from .models import Amendment, ComplianceMatrixItem, RFPDocument, RFPRequirement


# ── RFP Requirement ─────────────────────────────────────────


class RFPRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFPRequirement
        fields = [
            "id",
            "rfp_document",
            "requirement_id",
            "requirement_text",
            "section_reference",
            "requirement_type",
            "category",
            "evaluation_weight",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ── RFP Document ────────────────────────────────────────────


class RFPDocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    requirement_count = serializers.IntegerField(read_only=True)
    compliance_item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = RFPDocument
        fields = [
            "id",
            "deal",
            "title",
            "document_type",
            "file_name",
            "file_size",
            "file_type",
            "extraction_status",
            "page_count",
            "version",
            "parent_document",
            "requirement_count",
            "compliance_item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RFPDocumentDetailSerializer(serializers.ModelSerializer):
    """Full serializer with extracted metadata and nested relationships."""
    requirements = RFPRequirementSerializer(many=True, read_only=True)
    requirement_count = serializers.IntegerField(read_only=True)
    compliance_item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = RFPDocument
        fields = [
            "id",
            "deal",
            "title",
            "document_type",
            "file",
            "file_name",
            "file_size",
            "file_type",
            "extraction_status",
            "extracted_text",
            "page_count",
            "extracted_dates",
            "extracted_page_limits",
            "submission_instructions",
            "evaluation_criteria",
            "required_forms",
            "required_certifications",
            "version",
            "parent_document",
            "requirements",
            "requirement_count",
            "compliance_item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "extraction_status",
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
        ]


class RFPDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer used for the file upload action."""

    class Meta:
        model = RFPDocument
        fields = [
            "id",
            "deal",
            "title",
            "document_type",
            "file",
            "version",
            "parent_document",
        ]
        read_only_fields = ["id"]

    def validate_file(self, value):
        max_size = 100 * 1024 * 1024  # 100 MB
        if value.size > max_size:
            raise serializers.ValidationError(
                "File size exceeds maximum of 100 MB."
            )
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/msword",
            "text/plain",
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Unsupported file type: {value.content_type}. "
                "Allowed types: PDF, DOCX, XLSX, DOC, TXT."
            )
        return value


# ── Compliance Matrix ───────────────────────────────────────


class ComplianceMatrixItemSerializer(serializers.ModelSerializer):
    """Compliance matrix item with nested requirement for context."""
    requirement = RFPRequirementSerializer(read_only=True)
    requirement_id = serializers.PrimaryKeyRelatedField(
        queryset=RFPRequirement.objects.all(),
        source="requirement",
        write_only=True,
    )
    response_owner_email = serializers.EmailField(
        source="response_owner.email", read_only=True
    )

    class Meta:
        model = ComplianceMatrixItem
        fields = [
            "id",
            "rfp_document",
            "requirement",
            "requirement_id",
            "proposal_section",
            "proposal_page",
            "response_owner",
            "response_owner_email",
            "response_status",
            "ai_draft_response",
            "human_final_response",
            "compliance_status",
            "compliance_notes",
            "evidence_references",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "ai_draft_response", "created_at", "updated_at"]


# ── Amendment ───────────────────────────────────────────────


class AmendmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Amendment
        fields = [
            "id",
            "rfp_document",
            "amendment_number",
            "title",
            "file",
            "summary",
            "changes",
            "is_material",
            "requires_compliance_update",
            "detected_at",
            "reviewed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "changes",
            "is_material",
            "requires_compliance_update",
            "detected_at",
            "created_at",
            "updated_at",
        ]
