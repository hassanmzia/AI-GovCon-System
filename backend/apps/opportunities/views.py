from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
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


class OpportunityPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500


class OpportunityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving opportunities.

    Supports filtering by agency, naics_code, status, set_aside, and
    recommendation (via score__recommendation).
    """
    permission_classes = [IsAuthenticated]
    pagination_class = OpportunityPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "agency": ["exact", "icontains"],
        "naics_code": ["exact", "icontains", "startswith"],
        "status": ["exact"],
        "set_aside": ["exact", "icontains"],
        "notice_type": ["exact"],
        "is_active": ["exact"],
        "score__recommendation": ["exact"],
        "posted_date": ["gte", "lte"],
        "response_deadline": ["gte", "lte"],
        "estimated_value": ["gte", "lte"],
        "place_state": ["exact", "icontains"],
        "source__name": ["exact", "icontains"],
    }
    search_fields = ["title", "description", "agency", "notice_id", "sol_number"]
    ordering_fields = [
        "posted_date",
        "response_deadline",
        "estimated_value",
        "score__total_score",
        "created_at",
    ]
    # created_at is always populated; posted_date is NULL for many scraped records
    # so use created_at as primary to guarantee stable ordering across all sources.
    ordering = ["-created_at"]

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

    @action(detail=False, methods=["get"])
    def filters(self, request):
        """Return distinct values used to populate filter dropdowns."""
        qs = self.get_queryset()
        return Response({
            "agencies": list(
                qs.exclude(agency="")
                  .values_list("agency", flat=True)
                  .distinct()
                  .order_by("agency")
            ),
            "sources": list(
                qs.exclude(source__name="")
                  .values_list("source__name", flat=True)
                  .distinct()
                  .order_by("source__name")
            ),
            "statuses": list(
                qs.exclude(status="")
                  .values_list("status", flat=True)
                  .distinct()
                  .order_by("status")
            ),
            "naics_codes": list(
                qs.exclude(naics_code="")
                  .values_list("naics_code", flat=True)
                  .distinct()
                  .order_by("naics_code")
            ),
            "states": list(
                qs.exclude(place_state="")
                  .values_list("place_state", flat=True)
                  .distinct()
                  .order_by("place_state")
            ),
        })

    @action(detail=False, methods=["post"])
    def trigger_scan(self, request):
        """Trigger async scans for SAM.gov and all national lab sources."""
        from .tasks import scan_samgov_opportunities, scan_national_labs
        scan_samgov_opportunities.delay()
        scan_national_labs.delay()
        return Response(
            {"message": "Scan queued for SAM.gov and national labs. Results will appear shortly."},
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
