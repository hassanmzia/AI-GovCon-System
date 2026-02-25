import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.research.models import (
    CompetitorProfile,
    MarketIntelligence,
    ResearchProject,
    ResearchSource,
)
from apps.research.serializers import (
    CompetitorProfileSerializer,
    MarketIntelligenceSerializer,
    ResearchProjectDetailSerializer,
    ResearchProjectListSerializer,
    ResearchSourceSerializer,
)

logger = logging.getLogger(__name__)


class ResearchProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for research projects plus custom action to start research.

    Supports filtering by deal, status, research_type, and requested_by.
    """

    queryset = ResearchProject.objects.select_related(
        "deal", "requested_by"
    ).prefetch_related("research_sources")
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "deal": ["exact"],
        "status": ["exact", "in"],
        "research_type": ["exact", "in"],
        "requested_by": ["exact"],
    }
    search_fields = ["title", "description", "executive_summary"]
    ordering_fields = ["created_at", "updated_at", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ResearchProjectListSerializer
        return ResearchProjectDetailSerializer

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="start-research")
    def start_research(self, request, pk=None):
        """
        Kick off the research process for a project.

        Transitions the project to 'in_progress' and queues the
        Celery task for async research execution.
        """
        project = self.get_object()

        if project.status not in ("pending", "failed"):
            return Response(
                {
                    "detail": (
                        f"Cannot start research: project is currently "
                        f"'{project.get_status_display()}'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        project.status = "in_progress"
        project.save(update_fields=["status", "updated_at"])

        # Queue the async research task
        from apps.research.tasks import run_research_project

        run_research_project.delay(str(project.id))

        logger.info(
            "Research project %s started by user %s",
            project.id,
            request.user,
        )

        return Response(
            ResearchProjectDetailSerializer(project).data,
            status=status.HTTP_200_OK,
        )


class ResearchSourceViewSet(viewsets.ModelViewSet):
    """CRUD for research sources linked to projects."""

    queryset = ResearchSource.objects.select_related("project")
    serializer_class = ResearchSourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "project": ["exact"],
        "source_type": ["exact", "in"],
        "relevance_score": ["gte", "lte"],
    }
    search_fields = ["title", "url", "content"]
    ordering_fields = ["relevance_score", "fetched_at", "created_at"]
    ordering = ["-relevance_score"]


class CompetitorProfileViewSet(viewsets.ModelViewSet):
    """
    CRUD for competitor profiles.

    Supports filtering by active status, CAGE code, and name search.
    """

    queryset = CompetitorProfile.objects.all()
    serializer_class = CompetitorProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "is_active": ["exact"],
        "cage_code": ["exact"],
    }
    search_fields = ["name", "cage_code", "duns_number"]
    ordering_fields = ["name", "win_rate", "created_at"]
    ordering = ["name"]


class MarketIntelligenceViewSet(viewsets.ModelViewSet):
    """
    CRUD for market intelligence entries.

    Supports filtering by category and published date range.
    """

    queryset = MarketIntelligence.objects.all()
    serializer_class = MarketIntelligenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "category": ["exact", "in"],
        "published_date": ["gte", "lte"],
    }
    search_fields = ["title", "summary", "impact_assessment"]
    ordering_fields = ["published_date", "created_at", "category"]
    ordering = ["-published_date"]
