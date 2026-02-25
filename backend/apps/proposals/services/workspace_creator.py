"""Proposal workspace creation service.

Creates a full proposal workspace from a deal — sets up the Proposal record,
pulls RFP requirements, creates ProposalSection records matching the RFP volume
structure, and links past performance matches.
"""
import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.deals.models import Deal
from apps.past_performance.models import PastPerformance, PastPerformanceMatch
from apps.proposals.models import Proposal, ProposalSection, ProposalTemplate
from apps.rfp.models import RFPDocument, RFPRequirement

logger = logging.getLogger(__name__)

# Default volume/section structure when no RFP-specific structure exists
_DEFAULT_VOLUMES = [
    {
        "volume_name": "Volume I - Technical Approach",
        "sections": [
            {"name": "Executive Summary", "description": "Overall executive summary", "page_limit": 5},
            {"name": "Understanding of Requirements", "description": "Demonstrate understanding of agency needs", "page_limit": 10},
            {"name": "Technical Solution", "description": "Detailed technical approach", "page_limit": 30},
            {"name": "Quality Assurance", "description": "QA/QC approach", "page_limit": 5},
            {"name": "Risk Management", "description": "Risk identification and mitigation", "page_limit": 5},
        ],
    },
    {
        "volume_name": "Volume II - Management Approach",
        "sections": [
            {"name": "Management Plan", "description": "Project management methodology", "page_limit": 10},
            {"name": "Staffing Plan", "description": "Key personnel and staffing approach", "page_limit": 10},
            {"name": "Transition Plan", "description": "Transition-in approach", "page_limit": 5},
        ],
    },
    {
        "volume_name": "Volume III - Past Performance",
        "sections": [
            {"name": "Past Performance Overview", "description": "Summary of relevant past performance", "page_limit": 2},
            {"name": "Past Performance References", "description": "Detailed project references", "page_limit": 15},
        ],
    },
    {
        "volume_name": "Volume IV - Price/Cost",
        "sections": [
            {"name": "Pricing Narrative", "description": "Pricing approach and assumptions", "page_limit": 5},
            {"name": "Cost Detail", "description": "Detailed cost breakdown", "page_limit": None},
        ],
    },
]


def create_proposal_workspace(deal: Deal) -> Proposal:
    """Create a complete proposal workspace for the given deal.

    This function:
    1. Creates a Proposal record linked to the deal.
    2. Pulls RFP requirements from the rfp app and determines volume structure.
    3. Creates ProposalSection records from templates matching the RFP volume
       structure (or defaults if no RFP structure is available).
    4. Links past performance matches from the opportunity.
    5. Updates the proposal with initial compliance tracking counts.

    Args:
        deal: The Deal instance to create a proposal workspace for.

    Returns:
        The created Proposal instance with all sections and metadata populated.

    Raises:
        ValueError: If the deal is not in a proposal-eligible stage.
    """
    eligible_stages = (
        "capture_plan", "proposal_dev", "red_team", "final_review", "submit",
    )
    if deal.stage not in eligible_stages:
        raise ValueError(
            f"Deal is in stage '{deal.stage}'; must be one of {eligible_stages} "
            f"to create a proposal workspace."
        )

    with transaction.atomic():
        # ── 1. Determine template and volume structure ───────────────────
        template = _resolve_template(deal)
        volumes = _resolve_volume_structure(deal, template)

        # ── 2. Create Proposal ───────────────────────────────────────────
        existing_count = Proposal.objects.filter(deal=deal).count()
        proposal = Proposal.objects.create(
            deal=deal,
            template=template,
            title=f"Proposal: {deal.title}",
            version=existing_count + 1,
            status="draft",
            win_themes=_extract_win_themes(deal),
            discriminators=[],
        )
        logger.info(
            "Created Proposal %s (v%d) for deal %s",
            proposal.id, proposal.version, deal.id,
        )

        # ── 3. Create ProposalSection records ────────────────────────────
        section_order = 0
        for volume in volumes:
            volume_name = volume.get("volume_name", "Untitled Volume")
            for idx, sec in enumerate(volume.get("sections", []), start=1):
                section_order += 1
                ProposalSection.objects.create(
                    proposal=proposal,
                    volume=volume_name,
                    section_number=f"{volume_name.split(' ')[0]}.{volume_name.split(' ')[1] if len(volume_name.split(' ')) > 1 else ''}.{idx}".replace('..', '.'),
                    title=sec.get("name", f"Section {idx}"),
                    order=section_order,
                    status="not_started",
                    page_limit=sec.get("page_limit"),
                )

        logger.info(
            "Created %d sections across %d volumes for proposal %s",
            section_order, len(volumes), proposal.id,
        )

        # ── 4. Pull RFP requirements and update compliance counts ────────
        requirements = _pull_rfp_requirements(deal)
        proposal.total_requirements = len(requirements)
        proposal.compliant_count = 0
        proposal.compliance_percentage = 0.0
        proposal.save(update_fields=[
            "total_requirements", "compliant_count", "compliance_percentage",
        ])

        # ── 5. Link past performance matches ─────────────────────────────
        _link_past_performance(deal, proposal)

    return proposal


# ── Internal helpers ──────────────────────────────────────────────────────────


def _resolve_template(deal: Deal) -> ProposalTemplate | None:
    """Find the best matching ProposalTemplate for this deal.

    Looks for a template linked to the deal's RFP document type or falls back
    to the default template.
    """
    # Check for a default template first
    template = ProposalTemplate.objects.filter(is_default=True).first()
    if template:
        return template
    # Fallback: return the most recently created template if any exist
    return ProposalTemplate.objects.order_by("-created_at").first()


def _resolve_volume_structure(
    deal: Deal,
    template: ProposalTemplate | None,
) -> list[dict[str, Any]]:
    """Determine the volume/section structure for this proposal.

    Priority:
    1. RFP document extracted_page_limits (maps volume names to page limits).
    2. ProposalTemplate.volumes JSON field.
    3. Default volume structure.
    """
    # Try RFP-derived structure
    rfp_doc = (
        RFPDocument.objects
        .filter(deal=deal, extraction_status="completed")
        .order_by("-version")
        .first()
    )
    if rfp_doc and rfp_doc.extracted_page_limits:
        volumes = _volumes_from_rfp(rfp_doc)
        if volumes:
            return volumes

    # Try template
    if template and template.volumes:
        return template.volumes

    # Default structure
    return _DEFAULT_VOLUMES


def _volumes_from_rfp(rfp_doc: RFPDocument) -> list[dict[str, Any]]:
    """Build volume structure from RFP extracted data.

    Uses extracted_page_limits and evaluation_criteria to infer sections.
    """
    page_limits = rfp_doc.extracted_page_limits or {}
    eval_criteria = rfp_doc.evaluation_criteria or []

    if not page_limits:
        return []

    volumes: list[dict[str, Any]] = []
    for volume_key, limit in page_limits.items():
        # Normalize volume key to a readable name
        volume_name = volume_key.replace("_", " ").title()
        if not volume_name.lower().startswith("volume"):
            volume_name = f"Volume - {volume_name}"

        # Build sections from evaluation criteria that mention this volume
        sections = []
        for criterion in eval_criteria:
            crit_name = criterion.get("criterion", "")
            crit_desc = criterion.get("description", "")
            if _criterion_matches_volume(crit_name, volume_name):
                sections.append({
                    "name": crit_name,
                    "description": crit_desc,
                    "page_limit": None,
                })

        # If no criteria matched, add a generic section
        if not sections:
            sections.append({
                "name": volume_name,
                "description": f"Content for {volume_name}",
                "page_limit": limit if isinstance(limit, int) else None,
            })

        volumes.append({"volume_name": volume_name, "sections": sections})

    return volumes


def _criterion_matches_volume(criterion_name: str, volume_name: str) -> bool:
    """Check if an evaluation criterion relates to a given volume."""
    criterion_lower = criterion_name.lower()
    volume_lower = volume_name.lower()
    # Match on key terms
    keyword_map = {
        "technical": ["technical", "approach", "solution"],
        "management": ["management", "staffing", "personnel"],
        "past performance": ["past performance", "experience", "reference"],
        "price": ["price", "cost", "pricing"],
    }
    for category, keywords in keyword_map.items():
        if any(kw in volume_lower for kw in keywords):
            if any(kw in criterion_lower for kw in keywords):
                return True
    return False


def _extract_win_themes(deal: Deal) -> list[str]:
    """Extract win themes from the deal's capture plan if available."""
    try:
        capture_plan = getattr(deal, "capture_plan", None)
        if capture_plan and capture_plan.key_differentiators:
            return list(capture_plan.key_differentiators)[:5]
    except Exception:
        pass
    return []


def _pull_rfp_requirements(deal: Deal) -> list[RFPRequirement]:
    """Pull all RFP requirements associated with the deal's RFP documents."""
    rfp_docs = RFPDocument.objects.filter(deal=deal, extraction_status="completed")
    if not rfp_docs.exists():
        logger.info("No completed RFP documents found for deal %s", deal.id)
        return []

    requirements = list(
        RFPRequirement.objects.filter(rfp_document__in=rfp_docs).order_by("requirement_id")
    )
    logger.info(
        "Pulled %d RFP requirements for deal %s",
        len(requirements), deal.id,
    )
    return requirements


def _link_past_performance(deal: Deal, proposal: Proposal) -> int:
    """Link past performance matches from the opportunity to the proposal.

    Retrieves PastPerformanceMatch records for the deal's opportunity and
    stores match info in the proposal's discriminators JSON field.

    Returns:
        Number of past performance records linked.
    """
    try:
        opportunity = deal.opportunity
    except Exception:
        logger.info("No opportunity linked to deal %s; skipping past performance", deal.id)
        return 0

    matches = (
        PastPerformanceMatch.objects
        .filter(opportunity=opportunity)
        .select_related("past_performance")
        .order_by("-relevance_score")
    )

    if not matches.exists():
        logger.info("No past performance matches for opportunity %s", opportunity.id)
        return 0

    pp_references = []
    for match in matches[:10]:  # Top 10 matches
        pp = match.past_performance
        pp_references.append({
            "past_performance_id": str(pp.id),
            "project_name": pp.project_name,
            "client_agency": pp.client_agency,
            "relevance_score": match.relevance_score,
            "match_rationale": match.match_rationale,
            "contract_value": str(pp.contract_value) if pp.contract_value else None,
            "performance_rating": pp.performance_rating,
        })

    # Store in the proposal's discriminators field alongside any existing data
    discriminators = proposal.discriminators or []
    discriminators.append({
        "type": "past_performance",
        "matches": pp_references,
        "count": len(pp_references),
    })
    proposal.discriminators = discriminators
    proposal.save(update_fields=["discriminators"])

    logger.info(
        "Linked %d past performance matches to proposal %s",
        len(pp_references), proposal.id,
    )
    return len(pp_references)
