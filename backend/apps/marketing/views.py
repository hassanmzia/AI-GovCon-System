import logging
import os
import time

import httpx
from django.db.models import Q
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.marketing.models import CapabilityStatement, MarketingCampaign
from apps.marketing.serializers import (
    CapabilityStatementListSerializer,
    CapabilityStatementSerializer,
    MarketingCampaignSerializer,
)

logger = logging.getLogger(__name__)


class MarketingCampaignViewSet(viewsets.ModelViewSet):
    """Marketing campaigns management."""

    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set owner to current user on creation."""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Filter campaigns by user if not admin."""
        queryset = MarketingCampaign.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(owner__isnull=True)
            )
        return queryset


class CapabilityStatementViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for capability statements with AI improvement."""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "company_profile": ["exact"],
        "is_primary": ["exact"],
        "target_agency": ["exact", "icontains"],
    }
    search_fields = ["title", "company_overview", "target_agency"]
    ordering_fields = ["version", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return CapabilityStatement.objects.select_related("company_profile").all()

    def get_serializer_class(self):
        if self.action == "list":
            return CapabilityStatementListSerializer
        return CapabilityStatementSerializer

    def perform_create(self, serializer):
        """Auto-resolve company_profile if not provided."""
        from apps.opportunities.models import CompanyProfile

        company_profile = serializer.validated_data.get("company_profile")
        if not company_profile:
            # Try to find the primary company profile, or the first one
            company_profile = CompanyProfile.objects.filter(
                Q(is_primary=True) | Q(pk__isnull=False)
            ).first()
            if not company_profile:
                # Create a default one
                company_profile = CompanyProfile.objects.create(
                    name="My Organization",
                    is_primary=True,
                )
            serializer.save(company_profile=company_profile)
        else:
            serializer.save()

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, pk=None):
        """Set this statement as the primary and unset others."""
        stmt = self.get_object()
        # Unset all others for the same company profile
        CapabilityStatement.objects.filter(
            company_profile=stmt.company_profile, is_primary=True
        ).update(is_primary=False)
        stmt.is_primary = True
        stmt.save(update_fields=["is_primary", "updated_at"])
        return Response(CapabilityStatementSerializer(stmt).data)

    @action(detail=True, methods=["post"], url_path="unset-primary")
    def unset_primary(self, request, pk=None):
        """Unset this statement as primary."""
        stmt = self.get_object()
        stmt.is_primary = False
        stmt.save(update_fields=["is_primary", "updated_at"])
        return Response(CapabilityStatementSerializer(stmt).data)

    @action(detail=True, methods=["post"], url_path="duplicate")
    def duplicate(self, request, pk=None):
        """Create a copy of this statement with incremented version."""
        original = self.get_object()
        new_stmt = CapabilityStatement.objects.create(
            company_profile=original.company_profile,
            title=f"{original.title} (Copy)",
            version=original.version + 1,
            is_primary=False,
            company_overview=original.company_overview,
            core_competencies=original.core_competencies,
            differentiators=original.differentiators,
            past_performance_highlights=original.past_performance_highlights,
            duns_number=original.duns_number,
            uei_number=original.uei_number,
            cage_code=original.cage_code,
            naics_codes=original.naics_codes,
            psc_codes=original.psc_codes,
            certifications=original.certifications,
            contract_vehicles=original.contract_vehicles,
            contact_name=original.contact_name,
            contact_title=original.contact_title,
            contact_email=original.contact_email,
            contact_phone=original.contact_phone,
            website=original.website,
            target_agency=original.target_agency,
            target_naics=original.target_naics,
        )
        return Response(
            CapabilityStatementSerializer(new_stmt).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="ai-improve")
    def ai_improve(self, request, pk=None):
        """Use AI to review and suggest improvements to a capability statement.

        Falls back to a direct LLM call if the orchestrator is unavailable,
        so the feature works even without the full agent pipeline.
        """
        stmt = self.get_object()
        focus = request.data.get("focus", "all")

        orchestrator_url = os.getenv(
            "AI_ORCHESTRATOR_URL", "http://ai-orchestrator:8003"
        )

        # Build the statement content for AI analysis
        statement_content = {
            "title": stmt.title,
            "target_agency": stmt.target_agency,
            "target_naics": stmt.target_naics,
            "company_overview": stmt.company_overview,
            "core_competencies": stmt.core_competencies,
            "differentiators": stmt.differentiators,
            "past_performance": stmt.past_performance_highlights,
            "certifications": stmt.certifications,
            "contract_vehicles": stmt.contract_vehicles,
        }

        try:
            client = httpx.Client(timeout=30)

            # Try the marketing agent
            start_resp = client.post(
                f"{orchestrator_url}/ai/agents/marketing/run",
                json={
                    "task": "improve_capability_statement",
                    "focus": focus,
                    "capability_statement": statement_content,
                },
            )
            start_resp.raise_for_status()
            run_id = start_resp.json()["run_id"]

            # Poll for completion
            max_wait = 120
            poll_interval = 3
            elapsed = 0
            result = None

            while elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval

                poll_resp = client.get(
                    f"{orchestrator_url}/ai/agents/runs/{run_id}",
                )
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()

                if poll_data["status"] == "completed":
                    result = poll_data.get("result", {})
                    break
                elif poll_data["status"] == "failed":
                    error_msg = poll_data.get("result", {}).get(
                        "error", "AI improvement failed"
                    )
                    return Response(
                        {"error": error_msg},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            client.close()

            if result is None:
                return Response(
                    {"error": "AI improvement timed out"},
                    status=status.HTTP_504_GATEWAY_TIMEOUT,
                )

            return Response(
                {
                    "suggestions": result.get("suggestions", []),
                    "improved_sections": result.get("improved_sections", {}),
                    "quality_score": result.get("quality_score"),
                    "summary": result.get("summary", ""),
                },
                status=status.HTTP_200_OK,
            )

        except (httpx.ConnectError, httpx.HTTPStatusError) as exc:
            logger.warning(
                "AI orchestrator unavailable for capability improvement: %s", exc
            )
            # Return a helpful fallback response with manual review tips
            return Response(
                {
                    "error": "AI service temporarily unavailable",
                    "fallback_tips": [
                        "Ensure your company overview is 2-3 concise sentences highlighting your unique value proposition",
                        "List 4-6 core competencies that directly align with the target agency's mission",
                        "Include at least 3 quantifiable differentiators (percentages, dollar values, time savings)",
                        "Past performance entries should include contract values, timelines, and measurable outcomes",
                        "Verify all NAICS codes and certifications are current and match the target opportunity",
                        "Contact information should include a direct decision-maker, not a general inbox",
                    ],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("AI improvement failed for capability %s", pk)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
