from django.db.models import Count
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Proposal,
    ProposalSection,
    ProposalTemplate,
    ReviewComment,
    ReviewCycle,
)
from .serializers import (
    ProposalDetailSerializer,
    ProposalListSerializer,
    ProposalSectionDetailSerializer,
    ProposalSectionListSerializer,
    ProposalTemplateSerializer,
    ReviewCommentSerializer,
    ReviewCycleDetailSerializer,
    ReviewCycleListSerializer,
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
        if self.action == "list":
            return ProposalSectionListSerializer
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
