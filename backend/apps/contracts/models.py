import uuid

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class ContractTemplate(BaseModel):
    """Reusable contract templates by contract type."""

    CONTRACT_TYPE_CHOICES = [
        ('FFP', 'Firm Fixed Price'),
        ('T&M', 'Time & Materials'),
        ('CPFF', 'Cost Plus Fixed Fee'),
        ('CPAF', 'Cost Plus Award Fee'),
        ('CPIF', 'Cost Plus Incentive Fee'),
        ('IDIQ', 'Indefinite Delivery/Indefinite Quantity'),
        ('BPA', 'Blanket Purchase Agreement'),
    ]

    name = models.CharField(max_length=300)
    contract_type = models.CharField(max_length=10, choices=CONTRACT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    template_content = models.TextField()
    required_clauses = models.JSONField(default=list)
    optional_clauses = models.JSONField(default=list)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_contract_type_display()})"


class ContractClause(BaseModel):
    """Library of contract clauses (FAR, DFARS, custom, etc.)."""

    CLAUSE_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('special', 'Special'),
        ('custom', 'Custom'),
        ('far_reference', 'FAR Reference'),
        ('dfars_reference', 'DFARS Reference'),
    ]

    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    clause_number = models.CharField(max_length=50)
    title = models.CharField(max_length=500)
    clause_text = models.TextField()
    clause_type = models.CharField(max_length=20, choices=CLAUSE_TYPE_CHOICES)
    category = models.CharField(max_length=100, blank=True)
    is_negotiable = models.BooleanField(default=True)
    risk_level = models.CharField(
        max_length=10, choices=RISK_LEVEL_CHOICES, default='medium'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['clause_number']

    def __str__(self):
        return f"{self.clause_number}: {self.title}"


class Contract(BaseModel):
    """Contract linked to a deal, tracking full lifecycle."""

    CONTRACT_TYPE_CHOICES = [
        ('FFP', 'Firm Fixed Price'),
        ('T&M', 'Time & Materials'),
        ('CPFF', 'Cost Plus Fixed Fee'),
        ('CPAF', 'Cost Plus Award Fee'),
        ('CPIF', 'Cost Plus Incentive Fee'),
        ('IDIQ', 'Indefinite Delivery/Indefinite Quantity'),
        ('BPA', 'Blanket Purchase Agreement'),
    ]

    STATUS_CHOICES = [
        ('drafting', 'Drafting'),
        ('review', 'Review'),
        ('negotiation', 'Negotiation'),
        ('pending_execution', 'Pending Execution'),
        ('executed', 'Executed'),
        ('active', 'Active'),
        ('modification', 'Modification'),
        ('closeout', 'Closeout'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired'),
    ]

    deal = models.ForeignKey(
        'deals.Deal', on_delete=models.CASCADE, related_name='contracts'
    )
    template = models.ForeignKey(
        ContractTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    contract_number = models.CharField(max_length=100, unique=True, blank=True)
    title = models.CharField(max_length=500)
    contract_type = models.CharField(max_length=10, choices=CONTRACT_TYPE_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='drafting'
    )
    total_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    period_of_performance_start = models.DateField(null=True, blank=True)
    period_of_performance_end = models.DateField(null=True, blank=True)
    option_years = models.IntegerField(default=0)
    clauses = models.ManyToManyField(ContractClause, blank=True)
    contracting_officer = models.CharField(max_length=255, blank=True)
    contracting_officer_email = models.EmailField(blank=True)
    cor_name = models.CharField(max_length=255, blank=True)
    awarded_date = models.DateField(null=True, blank=True)
    executed_date = models.DateField(null=True, blank=True)
    document_file = models.FileField(upload_to='contracts/', blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class ContractVersion(BaseModel):
    """Version history for contract changes."""

    CHANGE_TYPE_CHOICES = [
        ('initial', 'Initial'),
        ('modification', 'Modification'),
        ('amendment', 'Amendment'),
        ('option_exercise', 'Option Exercise'),
        ('administrative', 'Administrative'),
    ]

    contract = models.ForeignKey(
        Contract, on_delete=models.CASCADE, related_name='versions'
    )
    version_number = models.IntegerField()
    change_type = models.CharField(
        max_length=20, choices=CHANGE_TYPE_CHOICES, default='initial'
    )
    description = models.TextField(blank=True)
    changes = models.JSONField(default=dict)
    document_file = models.FileField(upload_to='contract_versions/', blank=True)
    effective_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        ordering = ['-version_number']
        unique_together = [['contract', 'version_number']]

    def __str__(self):
        return f"v{self.version_number} of {self.contract.title}"


class ContractMilestone(BaseModel):
    """Milestones and deliverables tracked within a contract."""

    MILESTONE_TYPE_CHOICES = [
        ('deliverable', 'Deliverable'),
        ('payment', 'Payment'),
        ('review', 'Review'),
        ('option', 'Option'),
        ('transition', 'Transition'),
        ('closeout', 'Closeout'),
    ]

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),
    ]

    contract = models.ForeignKey(
        Contract, on_delete=models.CASCADE, related_name='milestones'
    )
    title = models.CharField(max_length=500)
    milestone_type = models.CharField(max_length=20, choices=MILESTONE_TYPE_CHOICES)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='upcoming'
    )
    completed_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    deliverable_description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contract_milestones',
    )

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()}) - {self.due_date}"


class ContractModification(BaseModel):
    """Tracks modifications (bilateral, unilateral, etc.) to a contract."""

    MODIFICATION_TYPE_CHOICES = [
        ('bilateral', 'Bilateral'),
        ('unilateral', 'Unilateral'),
        ('administrative', 'Administrative'),
        ('funding', 'Funding'),
        ('scope', 'Scope'),
        ('period_extension', 'Period Extension'),
    ]

    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('reviewing', 'Reviewing'),
        ('approved', 'Approved'),
        ('executed', 'Executed'),
        ('rejected', 'Rejected'),
    ]

    contract = models.ForeignKey(
        Contract, on_delete=models.CASCADE, related_name='modifications'
    )
    modification_number = models.CharField(max_length=50)
    modification_type = models.CharField(
        max_length=20, choices=MODIFICATION_TYPE_CHOICES
    )
    description = models.TextField()
    impact_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text='Positive or negative dollar impact.',
    )
    new_total_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    effective_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='proposed'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_modifications',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_modifications',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Mod {self.modification_number} - {self.contract.title}"
