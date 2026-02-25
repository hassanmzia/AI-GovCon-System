from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    CompanyProfile,
    DailyDigest,
    Opportunity,
)
from .serializers import (
    CompanyProfileSerializer,
    DailyDigestDetailSerializer,
    DailyDigestListSerializer,
    OpportunityDetailSerializer,
    OpportunityListSerializer,
)


class OpportunityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving opportunities.

    Supports filtering by agency, naics_code, status, set_aside, and
    recommendation (via score__recommendation).
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "agency": ["exact", "icontains"],
        "naics_code": ["exact"],
        "status": ["exact"],
        "set_aside": ["exact", "icontains"],
        "notice_type": ["exact"],
        "is_active": ["exact"],
        "score__recommendation": ["exact"],
        "posted_date": ["gte", "lte"],
        "response_deadline": ["gte", "lte"],
        "estimated_value": ["gte", "lte"],
        "place_state": ["exact", "icontains"],
    }
    search_fields = ["title", "description", "agency", "notice_id", "sol_number"]
    ordering_fields = [
        "posted_date",
        "response_deadline",
        "estimated_value",
        "score__total_score",
        "created_at",
    ]
    ordering = ["-posted_date"]

    def get_queryset(self):
        return (
            Opportunity.objects
            .select_related("source", "score")
            .all()
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OpportunityDetailSerializer
        return OpportunityListSerializer

    @action(detail=False, methods=["post"])
    def trigger_scan(self, request):
        """Trigger an async SAM.gov scan."""
        from .tasks import scan_samgov_opportunities
        scan_samgov_opportunities.delay()
        return Response(
            {"message": "SAM.gov scan queued. Results will appear shortly."},
            status=status.HTTP_202_ACCEPTED,
        )


class CompanyProfileViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for company profiles used in opportunity scoring.
    """
    queryset = CompanyProfile.objects.all()
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "uei_number", "cage_code"]


class DailyDigestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving daily opportunity digests.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "date": ["exact", "gte", "lte"],
        "is_sent": ["exact"],
    }
    ordering_fields = ["date"]
    ordering = ["-date"]

    def get_queryset(self):
        return DailyDigest.objects.prefetch_related("opportunities").all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DailyDigestDetailSerializer
        return DailyDigestListSerializer
