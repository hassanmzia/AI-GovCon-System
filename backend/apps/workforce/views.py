import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.workforce.models import (
    Assignment,
    ClearanceRecord,
    Employee,
    HiringRequisition,
    SkillMatrix,
)
from apps.workforce.serializers import (
    AssignmentSerializer,
    ClearanceRecordSerializer,
    EmployeeSerializer,
    HiringRequisitionSerializer,
    SkillMatrixSerializer,
)

logger = logging.getLogger(__name__)


# ── Employee ViewSet ─────────────────────────────────────


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    CRUD for employees.

    Supports filtering by department, clearance_type, clearance_status,
    labor_category, and is_active.  Search across name, email, and title.
    """

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "department": ["exact"],
        "clearance_type": ["exact", "in"],
        "clearance_status": ["exact", "in"],
        "labor_category": ["exact"],
        "is_active": ["exact"],
    }
    search_fields = ["name", "email", "title", "labor_category"]
    ordering_fields = ["name", "hire_date", "created_at", "hourly_rate"]
    ordering = ["name"]


# ── SkillMatrix ViewSet ──────────────────────────────────


class SkillMatrixViewSet(viewsets.ModelViewSet):
    """
    CRUD for employee skill matrix entries.

    Supports filtering by employee, skill_name, and proficiency_level.
    """

    queryset = SkillMatrix.objects.select_related("employee")
    serializer_class = SkillMatrixSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "employee": ["exact"],
        "skill_name": ["exact"],
        "proficiency_level": ["exact", "gte", "lte"],
    }
    search_fields = ["skill_name", "employee__name"]
    ordering_fields = ["proficiency_level", "years_experience", "skill_name"]
    ordering = ["skill_name"]


# ── ClearanceRecord ViewSet ──────────────────────────────


class ClearanceRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD for clearance investigation records.

    Supports filtering by employee, clearance_type, and status.
    """

    queryset = ClearanceRecord.objects.select_related("employee")
    serializer_class = ClearanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "employee": ["exact"],
        "clearance_type": ["exact", "in"],
        "status": ["exact", "in"],
        "sponsoring_agency": ["exact"],
    }
    ordering_fields = ["granted_date", "expiry_date", "created_at"]
    ordering = ["-granted_date"]


# ── Assignment ViewSet ───────────────────────────────────


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    CRUD for employee assignments to contracts/deals.

    Supports filtering by employee, contract, deal, and is_active.
    """

    queryset = Assignment.objects.select_related("employee", "contract", "deal")
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "employee": ["exact"],
        "contract": ["exact"],
        "deal": ["exact"],
        "is_active": ["exact"],
    }
    search_fields = ["role", "employee__name"]
    ordering_fields = ["start_date", "end_date", "allocation_percentage", "created_at"]
    ordering = ["-start_date"]


# ── HiringRequisition ViewSet ────────────────────────────


class HiringRequisitionViewSet(viewsets.ModelViewSet):
    """
    CRUD for hiring requisitions.

    Supports filtering by status, priority, department, labor_category,
    and linked_deal.
    """

    queryset = HiringRequisition.objects.select_related("linked_deal", "filled_by")
    serializer_class = HiringRequisitionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "status": ["exact", "in"],
        "priority": ["exact", "lte", "gte"],
        "department": ["exact"],
        "labor_category": ["exact"],
        "linked_deal": ["exact"],
        "clearance_required": ["exact"],
    }
    search_fields = ["title", "labor_category", "justification"]
    ordering_fields = ["priority", "target_start_date", "created_at", "status"]
    ordering = ["priority", "-created_at"]


# ── Analytics ViewSet ────────────────────────────────────


class AnalyticsViewSet(viewsets.ViewSet):
    """
    Workforce analytics and demand forecasting.

    Provides computed endpoints that aggregate data across
    employees, assignments, and the deal pipeline.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="demand-forecast")
    def demand_forecast(self, request):
        """
        Compute a hiring demand forecast from the active deal pipeline.

        Queries deals in proposal+ stages, extracts labor category needs from
        pricing scenarios, weights by win probability, and returns a
        {labor_category: demand_count} forecast along with gap analysis
        comparing forecast to current workforce capacity.
        """
        try:
            from apps.workforce.services.demand_forecaster import DemandForecaster

            forecaster = DemandForecaster()
            result = forecaster.compute_forecast()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Demand forecast computation failed")
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
