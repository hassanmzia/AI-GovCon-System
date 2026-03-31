from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.teaming.models import TeamingPartnership, TeamingPartner, TeamingAgreement
from apps.teaming.serializers import (
    TeamingPartnershipSerializer,
    TeamingPartnerListSerializer,
    TeamingPartnerDetailSerializer,
    TeamingAgreementSerializer,
)


class TeamingPartnershipViewSet(viewsets.ModelViewSet):
    """Teaming partnerships management."""

    queryset = TeamingPartnership.objects.all()
    serializer_class = TeamingPartnershipSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "relationship_type", "deal"]
    search_fields = ["partner_company", "description"]
    ordering_fields = ["created_at", "partner_company", "status"]

    def perform_create(self, serializer):
        """Set owner to current user on creation."""
        serializer.save(owner=self.request.user)


class TeamingPartnerViewSet(viewsets.ModelViewSet):
    """Partner directory — reusable partner company database."""

    queryset = TeamingPartner.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "clearance_level", "risk_level", "is_small_business", "is_channel_partner"]
    search_fields = ["name", "uei", "cage_code", "capabilities", "headquarters"]
    ordering_fields = ["name", "reliability_score", "past_revenue", "created_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return TeamingPartnerListSerializer
        return TeamingPartnerDetailSerializer

    @action(detail=False, methods=["post"])
    def search_by_capability(self, request):
        """AI-powered partner search by capability description."""
        import asyncio
        from apps.teaming.services.partner_matcher import search_partners

        query = request.data.get("query", "")
        naics = request.data.get("naics_codes", [])
        clearance = request.data.get("clearance_level")
        sb_status = request.data.get("sb_certifications", [])
        limit = int(request.data.get("limit", 20))

        try:
            results = asyncio.get_event_loop().run_until_complete(
                search_partners(query, naics=naics, clearance_level=clearance, sb_status=sb_status, limit=limit)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(
                search_partners(query, naics=naics, clearance_level=clearance, sb_status=sb_status, limit=limit)
            )
            loop.close()

        return Response({"results": results, "count": len(results)})

    @action(detail=True, methods=["get"])
    def risk_assessment(self, request, pk=None):
        """Get risk assessment for this partner."""
        import asyncio
        from apps.teaming.services.risk_assessor import assess_partner_risk

        partner = self.get_object()
        partner_dict = TeamingPartnerDetailSerializer(partner).data

        try:
            result = asyncio.get_event_loop().run_until_complete(
                assess_partner_risk(partner_dict)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(assess_partner_risk(partner_dict))
            loop.close()

        return Response(result)

    @action(detail=False, methods=["post"])
    def optimize_team(self, request):
        """Optimize team composition for an opportunity."""
        import asyncio
        from apps.teaming.services.team_optimizer import optimize_team

        opportunity = request.data.get("opportunity", {})
        partner_ids = request.data.get("partner_ids", [])
        required_capabilities = request.data.get("required_capabilities", [])
        max_partners = int(request.data.get("max_partners", 4))

        partners = TeamingPartner.objects.filter(id__in=partner_ids, is_active=True)
        partner_list = list(TeamingPartnerDetailSerializer(partners, many=True).data)

        try:
            result = asyncio.get_event_loop().run_until_complete(
                optimize_team(opportunity, partner_list, required_capabilities, max_partners=max_partners)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                optimize_team(opportunity, partner_list, required_capabilities, max_partners=max_partners)
            )
            loop.close()

        return Response(result)

    @action(detail=False, methods=["post"])
    def sb_compliance(self, request):
        """Check small business compliance for a team."""
        import asyncio
        from apps.teaming.services.sb_analyzer import analyze_sb_compliance

        team_members = request.data.get("team_members", [])
        opportunity = request.data.get("opportunity", {})
        goals = request.data.get("sb_goals")

        try:
            result = asyncio.get_event_loop().run_until_complete(
                analyze_sb_compliance(team_members, opportunity, goals)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                analyze_sb_compliance(team_members, opportunity, goals)
            )
            loop.close()

        return Response(result)


class TeamingAgreementViewSet(viewsets.ModelViewSet):
    """Teaming agreement lifecycle management."""

    queryset = TeamingAgreement.objects.select_related("partnership", "partnership__deal")
    serializer_class = TeamingAgreementSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["agreement_type", "status", "partnership"]
    search_fields = ["title", "work_scope"]
    ordering_fields = ["created_at", "agreement_type", "status"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def generate_document(self, request, pk=None):
        """Generate agreement document text using the legal drafter."""
        import asyncio
        from apps.teaming.services.agreement_generator import generate_agreement

        agreement = self.get_object()
        partnership = agreement.partnership
        prime_name = request.data.get("prime_name", "Our Company")

        opp_data = {}
        if partnership.deal:
            opp_data = {
                "title": partnership.deal.title,
                "solicitation_number": getattr(partnership.deal, "solicitation_number", ""),
            }

        try:
            result = asyncio.get_event_loop().run_until_complete(
                generate_agreement(
                    prime_name=prime_name,
                    partner_name=partnership.partner_company,
                    agreement_type=agreement.agreement_type,
                    opportunity=opp_data,
                    work_scope=agreement.work_scope,
                    work_share_percent=agreement.work_share_pct,
                )
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                generate_agreement(
                    prime_name=prime_name,
                    partner_name=partnership.partner_company,
                    agreement_type=agreement.agreement_type,
                    opportunity=opp_data,
                    work_scope=agreement.work_scope,
                    work_share_percent=agreement.work_share_pct,
                )
            )
            loop.close()

        # Save generated text
        if "document_text" in result:
            agreement.document_text = result["document_text"]
            agreement.save(update_fields=["document_text", "updated_at"])

        return Response(result)

    @action(detail=True, methods=["post"])
    def mark_signed(self, request, pk=None):
        """Mark agreement as signed."""
        from django.utils import timezone
        agreement = self.get_object()
        agreement.status = "signed"
        agreement.signed_date = request.data.get("signed_date", timezone.now().date())
        agreement.our_signatory = request.data.get("our_signatory", "")
        agreement.partner_signatory = request.data.get("partner_signatory", "")
        agreement.save(update_fields=["status", "signed_date", "our_signatory", "partner_signatory", "updated_at"])
        return Response(TeamingAgreementSerializer(agreement).data)
