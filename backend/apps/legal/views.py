import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.legal.models import (
    ComplianceAssessment,
    ContractReviewNote,
    FARClause,
    LegalRisk,
    RegulatoryRequirement,
)
from apps.legal.serializers import (
    ComplianceAssessmentSerializer,
    ContractReviewNoteSerializer,
    FARClauseSerializer,
    LegalRiskSerializer,
    RegulatoryRequirementSerializer,
)

logger = logging.getLogger(__name__)


# ── FAR Clause ViewSet ──────────────────────────────────


class FARClauseViewSet(viewsets.ModelViewSet):
    """CRUD for FAR clause references."""

    queryset = FARClause.objects.all()
    serializer_class = FARClauseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "category": ["exact"],
        "is_mandatory": ["exact"],
    }
    search_fields = ["clause_number", "title", "full_text", "plain_language_summary"]
    ordering_fields = ["clause_number", "title", "created_at"]
    ordering = ["clause_number"]


# ── Regulatory Requirement ViewSet ──────────────────────


class RegulatoryRequirementViewSet(viewsets.ModelViewSet):
    """CRUD for regulatory requirements."""

    queryset = RegulatoryRequirement.objects.all()
    serializer_class = RegulatoryRequirementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "regulation_source": ["exact"],
    }
    search_fields = ["reference_number", "title", "description"]
    ordering_fields = ["regulation_source", "reference_number", "created_at"]
    ordering = ["regulation_source", "reference_number"]


# ── Compliance Assessment ViewSet ───────────────────────


class ComplianceAssessmentViewSet(viewsets.ModelViewSet):
    """CRUD for compliance assessments with a custom compliance-check action."""

    queryset = ComplianceAssessment.objects.select_related(
        "deal", "assessed_by"
    ).prefetch_related("clauses_reviewed")
    serializer_class = ComplianceAssessmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "status": ["exact"],
        "overall_risk_level": ["exact"],
        "assessed_by": ["exact"],
    }
    search_fields = ["deal__title"]
    ordering_fields = ["created_at", "far_compliance_score", "dfars_compliance_score"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"], url_path="run-compliance-check")
    def run_compliance_check(self, request, pk=None):
        """Trigger a compliance check for this assessment's deal.

        Delegates to the FARAnalyzer service to evaluate FAR/DFARS compliance
        and updates the assessment with findings.
        """
        assessment = self.get_object()

        try:
            from apps.legal.services.far_analyzer import FARAnalyzer

            analyzer = FARAnalyzer()
            result = analyzer.check_compliance(str(assessment.deal_id))

            assessment.status = "completed"
            assessment.far_compliance_score = result.get("far_compliance_score", 0.0)
            assessment.dfars_compliance_score = result.get("dfars_compliance_score", 0.0)
            assessment.overall_risk_level = result.get("overall_risk_level", "low")
            assessment.findings = result.get("findings", [])
            assessment.recommendations = result.get("recommendations", [])
            assessment.non_compliant_items = result.get("non_compliant_items", [])
            assessment.save()

            return Response(ComplianceAssessmentSerializer(assessment).data)

        except Exception as exc:
            logger.exception("Compliance check failed for assessment %s: %s", pk, exc)
            return Response(
                {"detail": f"Compliance check failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ── Legal Risk ViewSet ──────────────────────────────────


class LegalRiskViewSet(viewsets.ModelViewSet):
    """CRUD for legal risks associated with deals."""

    queryset = LegalRisk.objects.select_related("deal", "identified_by")
    serializer_class = LegalRiskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "risk_type": ["exact"],
        "severity": ["exact"],
        "probability": ["exact"],
        "status": ["exact"],
    }
    search_fields = ["title", "description", "mitigation_strategy"]
    ordering_fields = ["severity", "probability", "created_at"]
    ordering = ["-created_at"]


# ── Contract Review Note ViewSet ────────────────────────


class ContractReviewNoteViewSet(viewsets.ModelViewSet):
    """CRUD for contract review notes."""

    queryset = ContractReviewNote.objects.select_related("deal", "reviewer")
    serializer_class = ContractReviewNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "deal": ["exact"],
        "reviewer": ["exact"],
        "note_type": ["exact"],
        "priority": ["exact"],
        "status": ["exact"],
    }
    search_fields = ["section", "note_text", "response"]
    ordering_fields = ["priority", "created_at"]
    ordering = ["-created_at"]
