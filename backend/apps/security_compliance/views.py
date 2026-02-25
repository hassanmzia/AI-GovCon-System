from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.security_compliance.models import (
    ComplianceRequirement,
    SecurityComplianceReport,
    SecurityControl,
    SecurityControlMapping,
    SecurityFramework,
)
from apps.security_compliance.serializers import (
    ComplianceRequirementSerializer,
    SecurityComplianceReportSerializer,
    SecurityControlMappingSerializer,
    SecurityControlSerializer,
    SecurityFrameworkSerializer,
)


class SecurityFrameworkViewSet(viewsets.ModelViewSet):
    """CRUD for security frameworks."""

    queryset = SecurityFramework.objects.all()
    serializer_class = SecurityFrameworkSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"is_active": ["exact"]}
    search_fields = ["name", "version", "description"]
    ordering_fields = ["name", "version", "created_at"]
    ordering = ["name"]


class SecurityControlViewSet(viewsets.ModelViewSet):
    """CRUD for security controls."""

    queryset = SecurityControl.objects.all()
    serializer_class = SecurityControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"framework": ["exact"], "priority": ["exact"], "family": ["exact"]}
    search_fields = ["control_id", "title", "description"]
    ordering_fields = ["control_id", "priority", "created_at"]
    ordering = ["framework", "control_id"]


class SecurityControlMappingViewSet(viewsets.ModelViewSet):
    """CRUD for security control mappings."""

    queryset = SecurityControlMapping.objects.select_related("deal", "control", "assessed_by")
    serializer_class = SecurityControlMappingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "control": ["exact"],
        "implementation_status": ["exact"],
    }
    search_fields = ["responsible_party", "gap_description"]
    ordering_fields = ["implementation_status", "assessment_date", "created_at"]
    ordering = ["-created_at"]


class SecurityComplianceReportViewSet(viewsets.ModelViewSet):
    """CRUD for security compliance reports."""

    queryset = SecurityComplianceReport.objects.select_related("deal", "framework", "approved_by")
    serializer_class = SecurityComplianceReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"deal": ["exact"], "framework": ["exact"], "report_type": ["exact"], "status": ["exact"]}
    search_fields = ["generated_by"]
    ordering_fields = ["report_type", "status", "overall_compliance_pct", "created_at"]
    ordering = ["-created_at"]


class ComplianceRequirementViewSet(viewsets.ModelViewSet):
    """CRUD for compliance requirements."""

    queryset = ComplianceRequirement.objects.select_related("deal")
    serializer_class = ComplianceRequirementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "category": ["exact"],
        "priority": ["exact"],
        "current_status": ["exact"],
    }
    search_fields = ["source_document", "requirement_text", "gap_description"]
    ordering_fields = ["priority", "current_status", "created_at"]
    ordering = ["-created_at"]
