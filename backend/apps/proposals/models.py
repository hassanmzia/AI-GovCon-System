import uuid
from django.conf import settings
from django.db import models
from apps.core.models import BaseModel


class ProposalTemplate(BaseModel):
    """Template defining volume/section structure."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    volumes = models.JSONField(default=list)  # [{volume_name, sections: [{name, description, page_limit}]}]
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Proposal(BaseModel):
    """Proposal linked to a deal."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE, related_name='proposals')
    template = models.ForeignKey(ProposalTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=500)
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=30, choices=[
        ('draft', 'Draft'),
        ('pink_team', 'Pink Team Review'),
        ('red_team', 'Red Team Review'),
        ('gold_team', 'Gold Team Review'),
        ('final', 'Final'),
        ('submitted', 'Submitted'),
    ], default='draft')

    # Metadata
    win_themes = models.JSONField(default=list)
    discriminators = models.JSONField(default=list)
    executive_summary = models.TextField(blank=True)

    # Compliance tracking
    total_requirements = models.IntegerField(default=0)
    compliant_count = models.IntegerField(default=0)
    compliance_percentage = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-version']

    def __str__(self):
        return f"{self.title} v{self.version}"


class ProposalSection(BaseModel):
    """Individual section of a proposal."""
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='sections')
    volume = models.CharField(max_length=100)  # Volume I, II, III, etc.
    section_number = models.CharField(max_length=50)
    title = models.CharField(max_length=300)
    order = models.IntegerField(default=0)

    # Content
    ai_draft = models.TextField(blank=True)
    human_content = models.TextField(blank=True)
    final_content = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('ai_drafted', 'AI Drafted'),
        ('in_review', 'In Review'),
        ('revised', 'Revised'),
        ('approved', 'Approved'),
    ], default='not_started')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    word_count = models.IntegerField(default=0)
    page_limit = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['volume', 'order']

    def __str__(self):
        return f"[{self.volume}] {self.section_number} {self.title}"


class ReviewCycle(BaseModel):
    """Review cycle (Pink/Red/Gold team)."""
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='reviews')
    review_type = models.CharField(max_length=20, choices=[
        ('pink', 'Pink Team'),
        ('red', 'Red Team'),
        ('gold', 'Gold Team'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], default='scheduled')
    scheduled_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)
    summary = models.TextField(blank=True)
    reviewers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    class Meta:
        ordering = ['-created_at']


# ── Solution Architecture models ──────────────────────────────────────────────

class TechnicalSolution(BaseModel):
    """
    Stores the output of the Solution Architect Agent for a deal:
    selected frameworks, synthesized solution design, LOE signals, etc.
    One record per agent run; latest is canonical.
    """
    deal = models.ForeignKey(
        'deals.Deal', on_delete=models.CASCADE, related_name='technical_solutions'
    )

    # Agent metadata
    iteration_count = models.IntegerField(default=1)
    selected_frameworks = models.JSONField(default=list)

    # Requirement analysis (full dict from agent)
    requirement_analysis = models.JSONField(default=dict, blank=True)

    # Solution design
    executive_summary = models.TextField(blank=True)
    architecture_pattern = models.CharField(max_length=200, blank=True)
    core_components = models.JSONField(default=list, blank=True)
    technology_stack = models.JSONField(default=dict, blank=True)
    integration_points = models.JSONField(default=list, blank=True)
    scalability_approach = models.TextField(blank=True)
    security_architecture = models.TextField(blank=True)
    deployment_model = models.CharField(max_length=100, blank=True)

    # Technical volume sections {section_title: content}
    technical_volume = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Technical Solution for {self.deal} (iter {self.iteration_count})"


class ArchitectureDiagram(BaseModel):
    """
    An architecture diagram (Mermaid, D2, PlantUML) associated with a TechnicalSolution.
    """

    DIAGRAM_TYPE_CHOICES = [
        ('system_context', 'System Context'),
        ('container', 'Container'),
        ('component', 'Component'),
        ('sequence', 'Sequence'),
        ('data_flow', 'Data Flow'),
        ('deployment', 'Deployment'),
        ('entity_relationship', 'Entity Relationship'),
    ]

    technical_solution = models.ForeignKey(
        TechnicalSolution, on_delete=models.CASCADE, related_name='diagrams'
    )
    title = models.CharField(max_length=300)
    diagram_type = models.CharField(max_length=30, choices=DIAGRAM_TYPE_CHOICES)
    mermaid_code = models.TextField(blank=True)
    d2_code = models.TextField(blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['diagram_type']

    def __str__(self):
        return f"{self.title} ({self.diagram_type})"


class SolutionValidationReport(BaseModel):
    """
    Self-critique / validation report produced by the Solution Architect Agent
    after generating a TechnicalSolution.
    """

    QUALITY_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    technical_solution = models.OneToOneField(
        TechnicalSolution, on_delete=models.CASCADE, related_name='validation_report'
    )
    overall_quality = models.CharField(max_length=20, choices=QUALITY_CHOICES)
    score = models.FloatField(null=True, blank=True)  # 0.0–1.0
    passed = models.BooleanField(default=False)
    issues = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    compliance_gaps = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Validation: {self.overall_quality} (pass={self.passed})"
    def __str__(self):
        return f"{self.review_type} Team - {self.proposal}"


class ReviewComment(BaseModel):
    """Comment on a specific proposal section during review."""
    review = models.ForeignKey(ReviewCycle, on_delete=models.CASCADE, related_name='comments')
    section = models.ForeignKey(ProposalSection, on_delete=models.CASCADE, related_name='review_comments')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment_type = models.CharField(max_length=20, choices=[
        ('strength', 'Strength'),
        ('weakness', 'Weakness'),
        ('suggestion', 'Suggestion'),
        ('must_fix', 'Must Fix'),
    ])
    content = models.TextField()
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
