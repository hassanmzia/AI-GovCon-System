from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    CompanyProfile,
    DailyDigest,
    NAICSCode,
    Opportunity,
    OpportunitySource,
    SAMRegistration,
    SBACertification,
)
from .serializers import (
    CompanyProfileSerializer,
    DailyDigestDetailSerializer,
    DailyDigestListSerializer,
    NAICSCodeSerializer,
    OpportunityDetailSerializer,
    OpportunityListSerializer,
    SAMRegistrationSerializer,
    SBACertificationSerializer,
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
        # Sources come from the OpportunitySource registry so that all configured
        # sources (e.g. SAM.gov) are always visible even before any opportunities
        # have been ingested from them.
        all_sources = list(
            OpportunitySource.objects.filter(is_active=True)
            .values_list("name", flat=True)
            .order_by("name")
        )
        # Agencies should reflect the contracting agency, not the scrape-source
        # name.  Exclude any agency value that is identical to a source name so
        # the two dropdowns stay distinct (national-lab opportunities are re-mapped
        # to their DOE parent agency via the scraper).
        source_names = set(all_sources)

        # Always include company profile NAICS codes so the dropdown is populated
        # even before opportunities with those codes have been ingested.
        profile = CompanyProfile.objects.filter(is_primary=True).first()
        profile_naics = list(profile.naics_codes) if profile and profile.naics_codes else []
        db_naics = list(
            qs.exclude(naics_code="")
              .exclude(naics_code__isnull=True)
              .values_list("naics_code", flat=True)
              .distinct()
        )
        all_naics = sorted(set(profile_naics + db_naics))

        return Response({
            "agencies": list(
                qs.exclude(agency="")
                  .exclude(agency__in=source_names)
                  .values_list("agency", flat=True)
                  .distinct()
                  .order_by("agency")
            ),
            "sources": all_sources,
            "statuses": list(
                qs.exclude(status="")
                  .values_list("status", flat=True)
                  .distinct()
                  .order_by("status")
            ),
            "naics_codes": all_naics,
            "states": list(
                qs.exclude(place_state="")
                  .values_list("place_state", flat=True)
                  .distinct()
                  .order_by("place_state")
            ),
        })

    @action(detail=False, methods=["post"])
    def trigger_scan(self, request):
        """Trigger async scans for SAM.gov, FPDS.gov, and national lab sources.

        Pass ``{"force": true}`` in the request body to clear stale rate-limit
        locks before queuing (useful when retries are exhausted but the lock
        TTL hasn't expired yet).

        Pass ``{"sources": ["samgov", "fpds"]}`` to scan specific sources only.
        Defaults to all sources if omitted.
        """
        from django.core.cache import cache
        from .tasks import (
            scan_samgov_opportunities,
            scan_fpds_opportunities,
            scan_national_labs,
            _SAMGOV_LOCK_KEY,
            _FPDS_LOCK_KEY,
            _NATIONAL_LABS_LOCK_KEY,
        )

        force = bool(request.data.get("force", False))
        requested_sources = request.data.get("sources")  # None = all

        if force:
            cache.delete(_SAMGOV_LOCK_KEY)
            cache.delete(_FPDS_LOCK_KEY)
            cache.delete(_NATIONAL_LABS_LOCK_KEY)

        queued = []
        if not requested_sources or "samgov" in requested_sources:
            scan_samgov_opportunities.delay()
            queued.append("SAM.gov")
        if not requested_sources or "fpds" in requested_sources:
            scan_fpds_opportunities.delay()
            queued.append("FPDS.gov")
        if not requested_sources or "national_labs" in requested_sources:
            scan_national_labs.delay()
            queued.append("National Labs")

        return Response(
            {
                "message": f"Scan queued for {', '.join(queued)}. Results will appear shortly.",
                "sources": queued,
                "locks_cleared": force,
            },
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


class SAMRegistrationViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for SAM.gov registration tracking."""
    serializer_class = SAMRegistrationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {
        "registration_status": ["exact"],
        "company_profile": ["exact"],
    }
    search_fields = ["legal_business_name", "tracking_number"]

    def get_queryset(self):
        return SAMRegistration.objects.select_related("company_profile").all()


class NAICSCodeViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for NAICS code reference data."""
    serializer_class = NAICSCodeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "code": ["exact", "startswith"],
        "sector": ["exact"],
        "size_standard_type": ["exact"],
    }
    search_fields = ["code", "title", "description"]
    ordering_fields = ["code", "title"]
    ordering = ["code"]

    def get_queryset(self):
        return NAICSCode.objects.all()


class SBACertificationViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for SBA certification tracking."""
    serializer_class = SBACertificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "company_profile": ["exact"],
        "certification_type": ["exact"],
        "status": ["exact"],
    }

    def get_queryset(self):
        return SBACertification.objects.select_related("company_profile").all()
