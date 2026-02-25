"""Teaming agreement generation service – delegates to the legal contract drafter."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def generate_agreement(
    prime_name: str,
    partner_name: str,
    agreement_type: str = "teaming",
    opportunity: dict[str, Any] | None = None,
    work_scope: str = "",
    work_share_percent: float | None = None,
    additional_terms: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a teaming-related agreement document.

    Dispatches to the appropriate draft function based on agreement_type.

    Args:
        prime_name: Prime contractor name.
        partner_name: Partner/subcontractor name.
        agreement_type: "nda", "loi", "teaming", "subcontract".
        opportunity: Opportunity context dict.
        work_scope: Partner's scope of work.
        work_share_percent: Planned work share percentage.
        additional_terms: Additional terms to include.

    Returns:
        Generated agreement dict with document_text and key_terms.
    """
    from apps.legal.services.contract_drafter import (
        draft_nda,
        draft_teaming_agreement,
        draft_subcontract_agreement,
    )

    opp = opportunity or {}
    opp_title = opp.get("title", "[Opportunity Title]")
    sol_number = opp.get("solicitation_number", "[Solicitation Number]")

    if agreement_type == "nda":
        return await draft_nda(
            party_a=prime_name,
            party_b=partner_name,
            purpose=f"evaluation of potential teaming for {opp_title}",
        )

    if agreement_type == "teaming":
        return await draft_teaming_agreement(
            prime_name=prime_name,
            partner_name=partner_name,
            opportunity_title=opp_title,
            solicitation_number=sol_number,
            work_scope=work_scope,
            work_share_percent=work_share_percent,
        )

    if agreement_type == "subcontract":
        contract_value = float(opp.get("estimated_value", 500_000) or 500_000)
        return await draft_subcontract_agreement(
            prime_name=prime_name,
            sub_name=partner_name,
            prime_contract_number=sol_number,
            work_scope=work_scope,
            period_of_performance=opp.get("period_of_performance", "[TBD]"),
            total_value=contract_value * ((work_share_percent or 20) / 100),
        )

    if agreement_type == "loi":
        return _draft_loi(prime_name, partner_name, opp_title, sol_number, work_scope)

    return {
        "error": f"Unknown agreement type: {agreement_type}",
        "supported_types": ["nda", "loi", "teaming", "subcontract"],
    }


async def generate_engagement_plan(
    partner: dict[str, Any],
    opportunity: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate a partner engagement plan with milestones and actions.

    Returns:
        Ordered list of engagement steps with timeline and owner.
    """
    opp_title = opportunity.get("title", "opportunity")
    partner_name = partner.get("company_name", "Partner")

    return [
        {
            "step": 1,
            "action": f"Reach out to {partner_name} leadership",
            "description": "Initial phone/email to gauge interest and availability",
            "timeline": "T-120 days before proposal due",
            "owner": "Capture Manager",
            "template": "intro_email",
        },
        {
            "step": 2,
            "action": "Execute NDA",
            "description": "Sign mutual NDA before sharing sensitive proposal information",
            "timeline": "T-110 days",
            "owner": "Contracts",
            "deliverable": "Signed NDA",
        },
        {
            "step": 3,
            "action": "Capability briefing exchange",
            "description": f"Share capabilities relevant to {opp_title}; receive partner capabilities",
            "timeline": "T-100 days",
            "owner": "Technical Lead",
        },
        {
            "step": 4,
            "action": "Agree on work scope and work share",
            "description": "Define responsibilities, work share percentage, and pricing approach",
            "timeline": "T-75 days",
            "owner": "Capture Manager + Pricing",
        },
        {
            "step": 5,
            "action": "Execute Letter of Intent (LOI)",
            "description": "Formalize commitment to pursue opportunity together",
            "timeline": "T-60 days",
            "owner": "Contracts",
            "deliverable": "Signed LOI",
        },
        {
            "step": 6,
            "action": "Execute Teaming Agreement",
            "description": "Full teaming agreement with exclusivity and IP provisions",
            "timeline": "T-45 days",
            "owner": "Contracts + Legal",
            "deliverable": "Signed Teaming Agreement",
        },
        {
            "step": 7,
            "action": "Proposal preparation collaboration",
            "description": "Partner submits resume, past performance, and technical contributions",
            "timeline": "T-30 to T-5 days",
            "owner": "Proposal Manager",
        },
        {
            "step": 8,
            "action": "Post-award subcontract execution",
            "description": "Execute subcontract agreement within 30 days of prime award",
            "timeline": "Post-award + 30 days",
            "owner": "Contracts",
            "conditional": "upon_award",
        },
    ]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _draft_loi(
    prime_name: str,
    partner_name: str,
    opp_title: str,
    sol_number: str,
    work_scope: str,
) -> dict[str, Any]:
    """Draft a simple Letter of Intent."""
    from datetime import date

    today = date.today().strftime("%B %d, %Y")

    doc = f"""LETTER OF INTENT

{today}

{partner_name}
Attn: [Partner Contact Name]
[Partner Address]

Re: Letter of Intent – Teaming for {opp_title} ({sol_number})

Dear [Partner Contact]:

This letter confirms the intent of {prime_name} ("Prime") and {partner_name} ("Partner")
to collaborate in pursuit of the above-referenced opportunity.

Prime and Partner agree in principle to the following:
• Prime will serve as the prime contractor
• Partner will serve as a subcontractor performing: {work_scope or "[scope to be defined]"}
• The Parties will negotiate and execute a formal Teaming Agreement

This Letter of Intent is non-binding and does not create any legal obligation.
The Parties will negotiate in good faith toward a formal Teaming Agreement.

This LOI expires 60 days from the date above.

{prime_name}

By: ____________________________
Name: __________________________
Title: _________________________
Date: {today}

ACCEPTED:
{partner_name}

By: ____________________________
Name: __________________________
Date: __________________________
"""
    return {
        "document_text": doc,
        "agreement_type": "loi",
        "parties": [prime_name, partner_name],
        "binding": False,
        "expiry_days": 60,
        "word_count": len(doc.split()),
    }
