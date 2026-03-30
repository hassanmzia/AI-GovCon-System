from django.db.models import Count
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    ArchitectureDiagram,
    Proposal,
    ProposalSection,
    ProposalTemplate,
    ReviewComment,
    ReviewCycle,
    SolutionValidationReport,
    SourcesSoughtResponse,
    SubmissionEmail,
    TechnicalSolution,
)
from .serializers import (
    ArchitectureDiagramSerializer,
    ProposalDetailSerializer,
    ProposalListSerializer,
    ProposalSectionDetailSerializer,
    ProposalSectionListSerializer,
    ProposalTemplateSerializer,
    ReviewCommentSerializer,
    ReviewCycleDetailSerializer,
    ReviewCycleListSerializer,
    SolutionValidationReportSerializer,
    SourcesSoughtResponseSerializer,
    SubmissionEmailSerializer,
    TechnicalSolutionDetailSerializer,
    TechnicalSolutionListSerializer,
)


class ProposalTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for proposal templates.
    """
    queryset = ProposalTemplate.objects.all()
    serializer_class = ProposalTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]


class ProposalViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for proposals.

    Supports filtering by deal, status, and version. Searchable by title
    and executive_summary.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "status": ["exact"],
        "version": ["exact", "gte", "lte"],
        "template": ["exact"],
        "compliance_percentage": ["gte", "lte"],
    }
    search_fields = ["title", "executive_summary"]
    ordering_fields = [
        "version",
        "status",
        "compliance_percentage",
        "created_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Proposal.objects
            .select_related("deal", "template")
            .prefetch_related("sections", "reviews")
            .annotate(section_count=Count("sections"))
            .all()
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ProposalListSerializer
        return ProposalDetailSerializer


class ProposalSectionViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for proposal sections.

    Supports filtering by proposal, volume, status, and assigned_to.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "proposal": ["exact"],
        "volume": ["exact"],
        "status": ["exact"],
        "assigned_to": ["exact"],
    }
    search_fields = ["title", "section_number"]
    ordering_fields = ["volume", "order", "status", "created_at"]
    ordering = ["volume", "order"]

    def get_queryset(self):
        return ProposalSection.objects.select_related(
            "proposal", "assigned_to"
        ).all()

    def get_serializer_class(self):
        # Always return full detail serializer so section content
        # (ai_draft, human_content, final_content) is included in list views.
        return ProposalSectionDetailSerializer


class ReviewCycleViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for review cycles.

    Supports filtering by proposal, review_type, and status.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "proposal": ["exact"],
        "review_type": ["exact"],
        "status": ["exact"],
    }
    ordering_fields = ["scheduled_date", "completed_date", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            ReviewCycle.objects
            .select_related("proposal")
            .prefetch_related("reviewers", "comments")
            .annotate(comment_count=Count("comments"))
            .all()
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ReviewCycleListSerializer
        return ReviewCycleDetailSerializer


class ReviewCommentViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for review comments.

    Supports filtering by review, section, reviewer, comment_type,
    and is_resolved.
    """
    serializer_class = ReviewCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "review": ["exact"],
        "section": ["exact"],
        "reviewer": ["exact"],
        "comment_type": ["exact"],
        "is_resolved": ["exact"],
    }
    ordering_fields = ["comment_type", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return ReviewComment.objects.select_related(
            "review", "section", "reviewer"
        ).all()


class SourcesSoughtResponseViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for Sources Sought / RFI responses."""
    serializer_class = SourcesSoughtResponseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "status": ["exact"],
        "interest_level": ["exact"],
    }
    search_fields = ["title", "solicitation_number"]
    ordering_fields = ["created_at", "submitted_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return SourcesSoughtResponse.objects.filter(
            owner=self.request.user
        ).select_related("deal", "opportunity")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SubmissionEmailViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for submission email templates."""
    serializer_class = SubmissionEmailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "proposal": ["exact"],
        "sources_sought": ["exact"],
        "email_type": ["exact"],
        "is_sent": ["exact"],
    }

    def get_queryset(self):
        return SubmissionEmail.objects.select_related("proposal", "sources_sought").all()


# ── Solution Architecture ─────────────────────────────────────────────────────

class TechnicalSolutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for technical solutions.

    Supports filtering by deal. Returns a summary serializer on list
    and the full detail serializer on retrieve.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
    }
    ordering_fields = ["iteration_count", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return TechnicalSolution.objects.select_related("deal").prefetch_related("diagrams").all()

    def get_serializer_class(self):
        # Always return the full detail serializer so the frontend gets
        # the nested ArchitectureResult shape (requirement_analysis,
        # technical_solution, technical_volume).
        return TechnicalSolutionDetailSerializer


class ArchitectureDiagramViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for architecture diagrams.

    Supports filtering by technical_solution.
    """
    serializer_class = ArchitectureDiagramSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "technical_solution": ["exact"],
        "diagram_type": ["exact"],
    }
    ordering_fields = ["diagram_type", "created_at"]
    ordering = ["diagram_type"]

    def get_queryset(self):
        return ArchitectureDiagram.objects.select_related("technical_solution").all()


class SolutionValidationReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for solution validation reports.

    Supports filtering by technical_solution.
    """
    serializer_class = SolutionValidationReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "technical_solution": ["exact"],
        "passed": ["exact"],
        "overall_quality": ["exact"],
    }
    ordering_fields = ["score", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return SolutionValidationReport.objects.select_related("technical_solution").all()
