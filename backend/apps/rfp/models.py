import uuid
from django.conf import settings
from django.db import models
from pgvector.django import VectorField
from apps.core.models import BaseModel


class RFPDocument(BaseModel):
    """Uploaded RFP document with extracted metadata."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE, related_name='rfp_documents')
    title = models.CharField(max_length=500)
    document_type = models.CharField(max_length=50, choices=[
        ('rfp', 'RFP'),
        ('rfi', 'RFI'),
        ('rfq', 'RFQ'),
        ('sources_sought', 'Sources Sought'),
        ('amendment', 'Amendment'),
        ('qa_response', 'Q&A Response'),
        ('attachment', 'Attachment'),
        ('other', 'Other'),
    ])
    file = models.FileField(upload_to='rfp_documents/')
    file_name = models.CharField(max_length=500)
    file_size = models.IntegerField(default=0)
    file_type = models.CharField(max_length=50, blank=True)  # pdf, docx, xlsx

    # Extraction status
    extraction_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')

    # Extracted metadata
    extracted_text = models.TextField(blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    extracted_dates = models.JSONField(default=dict)  # {qa_deadline, proposal_due, award_estimate}
    extracted_page_limits = models.JSONField(default=dict)  # {volume_i: 50, volume_ii: 30, ...}
    submission_instructions = models.TextField(blank=True)
    evaluation_criteria = models.JSONField(default=list)  # [{criterion, weight, description}]
    required_forms = models.JSONField(default=list)  # [{form_name, form_number, required: bool}]
    required_certifications = models.JSONField(default=list)

    # Version tracking
    version = models.IntegerField(default=1)
    parent_document = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (v{self.version})"


class RFPRequirement(BaseModel):
    """Individual requirement extracted from RFP."""
    rfp_document = models.ForeignKey(RFPDocument, on_delete=models.CASCADE, related_name='requirements')
    requirement_id = models.CharField(max_length=50)  # L.3.2.1
    requirement_text = models.TextField()
    section_reference = models.CharField(max_length=200, blank=True)
    requirement_type = models.CharField(max_length=30, choices=[
        ('mandatory', 'Mandatory'),
        ('desirable', 'Desirable'),
        ('informational', 'Informational'),
    ], default='mandatory')
    category = models.CharField(max_length=100, blank=True)  # technical, management, security, etc.
    evaluation_weight = models.FloatField(null=True, blank=True)

    # Embedding for matching
    requirement_embedding = VectorField(dimensions=1536, null=True)

    class Meta:
        ordering = ['requirement_id']

    def __str__(self):
        return f"{self.requirement_id}: {self.requirement_text[:60]}"


class ComplianceMatrixItem(BaseModel):
    """Maps RFP requirement to proposal response."""
    rfp_document = models.ForeignKey(RFPDocument, on_delete=models.CASCADE, related_name='compliance_items')
    requirement = models.ForeignKey(RFPRequirement, on_delete=models.CASCADE, related_name='compliance_items')

    # Response mapping
    proposal_section = models.CharField(max_length=200, blank=True)
    proposal_page = models.CharField(max_length=50, blank=True)
    response_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    response_status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('drafted', 'Drafted'),
        ('reviewed', 'Reviewed'),
        ('final', 'Final'),
    ], default='not_started')

    # Content
    ai_draft_response = models.TextField(blank=True)
    human_final_response = models.TextField(blank=True)

    # Compliance assessment
    compliance_status = models.CharField(max_length=20, choices=[
        ('compliant', 'Compliant'),
        ('partial', 'Partially Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('not_assessed', 'Not Assessed'),
    ], default='not_assessed')
    compliance_notes = models.TextField(blank=True)
    evidence_references = models.JSONField(default=list)

    class Meta:
        ordering = ['requirement__requirement_id']

    def __str__(self):
        return f"[{self.compliance_status}] {self.requirement.requirement_id}"


class Amendment(BaseModel):
    """Tracks amendments/modifications to an RFP."""
    rfp_document = models.ForeignKey(RFPDocument, on_delete=models.CASCADE, related_name='amendments')
    amendment_number = models.IntegerField()
    title = models.CharField(max_length=500, blank=True)
    file = models.FileField(upload_to='rfp_amendments/', blank=True)
    summary = models.TextField(blank=True)
    changes = models.JSONField(default=list)  # [{section, old_text, new_text, impact}]
    is_material = models.BooleanField(default=False)  # Material change requiring re-review
    requires_compliance_update = models.BooleanField(default=False)
    detected_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ['amendment_number']

    def __str__(self):
        return f"Amendment {self.amendment_number} for {self.rfp_document}"
