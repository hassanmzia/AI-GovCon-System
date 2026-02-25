from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from apps.core.models import BaseModel


class KnowledgeDocument(BaseModel):
    """Knowledge vault document for storing templates, guides, and reference materials."""

    CATEGORY_CHOICES = [
        ("template", "Template"),
        ("guide", "Guide"),
        ("best_practice", "Best Practice"),
        ("case_study", "Case Study"),
        ("regulatory_reference", "Regulatory Reference"),
        ("tool", "Tool"),
        ("lesson_learned", "Lesson Learned"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "In Review"),
        ("approved", "Approved"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    content = models.TextField()
    file_url = models.URLField(blank=True)
    file_name = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    tags = models.JSONField(default=list, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="knowledge_documents_authored",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="knowledge_documents_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    version = models.CharField(max_length=50, default="1.0")
    related_documents = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="related_to"
    )
    is_public = models.BooleanField(default=False)
    downloads = models.IntegerField(default=0)
    views = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Knowledge Document"
        verbose_name_plural = "Knowledge Documents"

    def __str__(self):
        return f"{self.title} [{self.get_category_display()}]"


class KnowledgeVault(BaseModel):
    """
    Primary container for multimodal RAG knowledge items ingested via the
    ingestion pipeline (PDF, DOCX, images, URLs, code).
    Distinct from KnowledgeDocument which is used for human-curated library items.
    """

    CONTENT_TYPE_CHOICES = [
        ("text", "Text"),
        ("markdown", "Markdown"),
        ("code", "Code"),
        ("image", "Image"),
        ("table", "Table"),
        ("pdf", "PDF"),
        ("url", "URL"),
    ]

    CATEGORY_CHOICES = [
        ("architecture", "Architecture"),
        ("legal", "Legal"),
        ("pricing", "Pricing"),
        ("security", "Security"),
        ("proposal", "Proposal"),
        ("research", "Research"),
        ("technical", "Technical"),
        ("general", "General"),
    ]

    title = models.CharField(max_length=500)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default="text")
    content = models.TextField(blank=True, help_text="Text preview (first 10 000 chars)")
    tags = models.JSONField(default=list, blank=True)
    source_url = models.URLField(blank=True)
    file_path = models.CharField(max_length=500, blank=True, help_text="MinIO object key")
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Knowledge Vault Item"
        verbose_name_plural = "Knowledge Vault Items"

    def __str__(self):
        return f"{self.title} [{self.content_type}]"


class KnowledgeChunk(BaseModel):
    """
    A chunk extracted from a KnowledgeVault item or KnowledgeDocument,
    stored with its vector embedding for RAG retrieval.
    Can also be linked to a SolutioningFramework section.
    """

    CHUNK_TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image"),
        ("table", "Table"),
        ("code", "Code"),
    ]

    # At least one of these FKs is populated
    vault_item = models.ForeignKey(
        KnowledgeVault,
        on_delete=models.CASCADE,
        related_name="chunks",
        null=True,
        blank=True,
    )
    document = models.ForeignKey(
        KnowledgeDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
        null=True,
        blank=True,
    )
    solutioning_framework = models.ForeignKey(
        "SolutioningFramework",
        on_delete=models.CASCADE,
        related_name="chunks",
        null=True,
        blank=True,
    )

    chunk_index = models.IntegerField(default=0)
    content_type = models.CharField(max_length=20, choices=CHUNK_TYPE_CHOICES, default="text")

    # Text content
    text = models.TextField(blank=True)
    token_count = models.IntegerField(default=0)

    # Image-specific
    image_url = models.URLField(blank=True)
    image_type = models.CharField(max_length=50, blank=True)  # diagram, chart, screenshot

    # Embeddings
    text_embedding = VectorField(dimensions=1536, null=True)
    image_embedding = VectorField(dimensions=512, null=True)  # CLIP dimensions

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["chunk_index"]
        indexes = [
            models.Index(fields=["vault_item", "chunk_index"]),
            models.Index(fields=["document", "chunk_index"]),
        ]

    def __str__(self):
        source = (
            self.vault_item.title if self.vault_item
            else self.document.title if self.document
            else str(self.solutioning_framework)
        )
        return f"Chunk {self.chunk_index} of {source}"


class SolutioningFramework(BaseModel):
    """
    Architecture and solutioning frameworks (TOGAF, C4, arc42, agentic patterns, etc.)
    stored for RAG retrieval by the Solution Architect agent.
    """

    CATEGORY_CHOICES = [
        ("enterprise_architecture", "Enterprise Architecture"),
        ("software_architecture", "Software Architecture"),
        ("agentic", "Agentic / AI Patterns"),
        ("security", "Security Architecture"),
        ("cloud", "Cloud Architecture"),
        ("data", "Data Architecture"),
        ("integration", "Integration Patterns"),
    ]

    name = models.CharField(max_length=200, unique=True)
    version = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    # Structured sections: {section_name: section_content_text}
    sections = models.JSONField(default=dict, blank=True)

    # Use cases this framework applies to
    use_cases = models.JSONField(default=list, blank=True)

    # Key patterns / principles
    patterns = models.JSONField(default=list, blank=True)

    # External reference
    reference_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name = "Solutioning Framework"
        verbose_name_plural = "Solutioning Frameworks"

    def __str__(self):
        return f"{self.name} {self.version}".strip()
