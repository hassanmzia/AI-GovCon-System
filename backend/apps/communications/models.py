from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class CommunicationThread(BaseModel):
    """A communication thread linked optionally to a deal."""

    THREAD_TYPE_CHOICES = [
        ("internal", "Internal"),
        ("client", "Client"),
        ("agency", "Agency"),
        ("vendor", "Vendor"),
        ("teaming_partner", "Teaming Partner"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("archived", "Archived"),
        ("resolved", "Resolved"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="communication_threads",
    )
    subject = models.CharField(max_length=255)
    thread_type = models.CharField(max_length=20, choices=THREAD_TYPE_CHOICES)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ThreadParticipant",
        related_name="communication_threads",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="normal"
    )
    tags = models.JSONField(default=list)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"[{self.thread_type}] {self.subject}"


class ThreadParticipant(BaseModel):
    """Through model for thread participants with roles."""

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("member", "Member"),
        ("observer", "Observer"),
    ]

    thread = models.ForeignKey(
        CommunicationThread,
        on_delete=models.CASCADE,
        related_name="thread_participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="thread_participations",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [["thread", "user"]]

    def __str__(self):
        return f"{self.user} in {self.thread} ({self.role})"


class Message(BaseModel):
    """A message within a communication thread."""

    MESSAGE_TYPE_CHOICES = [
        ("text", "Text"),
        ("system", "System"),
        ("ai_generated", "AI Generated"),
        ("file_share", "File Share"),
    ]

    thread = models.ForeignKey(
        CommunicationThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20, choices=MESSAGE_TYPE_CHOICES, default="text"
    )
    attachments = models.JSONField(default=list)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message by {self.sender} in {self.thread}"


class ClarificationQuestion(BaseModel):
    """Q&A tracking for RFP clarification questions."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("answered", "Answered"),
        ("withdrawn", "Withdrawn"),
    ]

    SOURCE_CHOICES = [
        ("vendor_submitted", "Vendor Submitted"),
        ("government_issued", "Government Issued"),
        ("internal", "Internal"),
    ]

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="clarification_questions",
    )
    rfp_section = models.CharField(max_length=255, blank=True, default="")
    question_text = models.TextField()
    question_number = models.IntegerField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_questions",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_government_question = models.BooleanField(default=False)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="internal")

    class Meta:
        ordering = ["question_number", "created_at"]

    def __str__(self):
        prefix = f"Q{self.question_number}" if self.question_number else "Q"
        return f"{prefix}: {self.question_text[:60]}"


class ClarificationAnswer(BaseModel):
    """Answer to a clarification question."""

    question = models.ForeignKey(
        ClarificationQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    answer_text = models.TextField()
    answered_by = models.CharField(max_length=255, blank=True, default="")
    answered_at = models.DateTimeField(null=True, blank=True)
    impacts_proposal = models.BooleanField(default=False)
    amendment_reference = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-answered_at"]

    def __str__(self):
        return f"Answer to {self.question}"


class QAImpactMapping(BaseModel):
    """Maps Q&A answers to proposal sections they impact."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    answer = models.ForeignKey(
        ClarificationAnswer,
        on_delete=models.CASCADE,
        related_name="impact_mappings",
    )
    proposal_section = models.CharField(max_length=255)
    impact_description = models.TextField()
    action_required = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_impact_mappings",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Impact on {self.proposal_section} from {self.answer}"
