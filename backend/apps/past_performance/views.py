from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import PastPerformance, PastPerformanceMatch
from .serializers import (
    PastPerformanceDetailSerializer,
    PastPerformanceListSerializer,
    PastPerformanceMatchSerializer,
)


class PastPerformanceViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for past performance records.

    Supports filtering by client_agency, naics_codes, contract_type,
    performance_rating, and is_active. Searchable by project_name,
    client_agency, description, and contract_number.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "client_agency": ["exact", "icontains"],
        "contract_type": ["exact"],
        "performance_rating": ["exact"],
        "cpars_rating": ["exact"],
        "is_active": ["exact"],
        "on_time_delivery": ["exact"],
        "within_budget": ["exact"],
        "start_date": ["gte", "lte"],
        "end_date": ["gte", "lte"],
        "contract_value": ["gte", "lte"],
    }
    search_fields = [
        "project_name",
        "client_agency",
        "description",
        "contract_number",
        "client_name",
    ]
    ordering_fields = [
        "end_date",
        "start_date",
        "contract_value",
        "performance_rating",
        "created_at",
    ]
    ordering = ["-end_date"]

    def get_queryset(self):
        return PastPerformance.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return PastPerformanceListSerializer
        return PastPerformanceDetailSerializer


class PastPerformanceMatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for past performance matches.

    Supports filtering by opportunity and relevance_score.
    """
    serializer_class = PastPerformanceMatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "opportunity": ["exact"],
        "relevance_score": ["gte", "lte"],
    }
    ordering_fields = ["relevance_score", "created_at"]
    ordering = ["-relevance_score"]

    def get_queryset(self):
        return PastPerformanceMatch.objects.select_related(
            "opportunity", "past_performance"
        ).all()

    @action(detail=False, methods=["post"], url_path="trigger")
    def trigger(self, request):
        """Trigger AI matching for a given opportunity.

        Body: { "opportunity_id": "<uuid>" }
        Enqueues a Celery task and returns the task_id.
        """
        opportunity_id = request.data.get("opportunity_id")
        if not opportunity_id:
            return Response(
                {"error": "opportunity_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.opportunities.models import Opportunity
            Opportunity.objects.get(pk=opportunity_id)
        except Exception:
            return Response(
                {"error": "Opportunity not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            from apps.past_performance.tasks import match_past_performance_task
            task = match_past_performance_task.delay(str(opportunity_id))
            return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)
        except Exception:
            # Celery not available — run synchronously as fallback
            from apps.past_performance.services.matcher import match_past_performance
            import asyncio
            try:
                asyncio.run(match_past_performance(opportunity_id))
            except Exception:
                pass
            return Response({"task_id": None}, status=status.HTTP_202_ACCEPTED)
