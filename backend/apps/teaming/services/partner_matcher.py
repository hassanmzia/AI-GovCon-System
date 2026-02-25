"""Partner matching service – RAG-based partner search and ranking."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def search_partners(
    capability_query: str,
    naics: list[str] | None = None,
    clearance_level: str | None = None,
    sb_status: list[str] | None = None,
    exclude_names: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search partner database using semantic similarity + hard filters.

    Args:
        capability_query: Description of capabilities needed.
        naics: Required NAICS codes.
        clearance_level: Minimum clearance ("Secret", "TS", "TS/SCI").
        sb_status: Required SB certifications.
        exclude_names: Company names to exclude.
        limit: Max results.

    Returns:
        Ranked list of matching partners.
    """
    try:
        from apps.teaming.models import TeamingPartner  # type: ignore
        from django.db.models import Q  # type: ignore

        qs = TeamingPartner.objects.filter(is_active=True)

        if naics:
            qs = qs.filter(naics_codes__overlap=naics)
        if clearance_level:
            clearance_order = {"None": 0, "Public Trust": 1, "Secret": 2, "TS": 3, "TS/SCI": 4}
            min_level = clearance_order.get(clearance_level, 0)
            qs = qs.filter(max_clearance_level__in=[
                k for k, v in clearance_order.items() if v >= min_level
            ])
        if sb_status:
            for cert in sb_status:
                qs = qs.filter(sb_certifications__contains=[cert])
        if exclude_names:
            for name in exclude_names:
                qs = qs.exclude(company_name__icontains=name)

        partners = list(qs.values())

        # Rank by capability similarity and reliability score
        if capability_query:
            partners = await _rank_by_capability(partners, capability_query)

        return partners[:limit]

    except Exception as exc:
        logger.error("Partner search failed: %s", exc)
        return []


async def rank_partners_for_opportunity(
    partners: list[dict[str, Any]],
    opportunity: dict[str, Any],
    required_capabilities: list[str],
) -> list[dict[str, Any]]:
    """Rank a list of partners for a specific opportunity.

    Scoring factors:
    - Capability match to required capabilities
    - Reliability score
    - Past performance with agency
    - SB certification alignment
    - Contract vehicle availability

    Args:
        partners: List of partner dicts.
        opportunity: Opportunity dict.
        required_capabilities: List of required capability areas.

    Returns:
        Partners ranked by composite score.
    """
    agency = opportunity.get("agency_name", "")
    scored = []
    for partner in partners:
        score = _compute_partner_score(partner, required_capabilities, agency)
        scored.append({**partner, "ranking_score": score})

    scored.sort(key=lambda p: p["ranking_score"], reverse=True)
    return scored


async def get_partner_history(partner_id: str, agency: str | None = None) -> dict[str, Any]:
    """Get teaming history with a partner.

    Returns:
        Dict with past_teaming_count, win_rate, last_teaming_date, notes.
    """
    try:
        from apps.teaming.models import TeamingAgreement  # type: ignore

        agreements = TeamingAgreement.objects.filter(partner_id=partner_id)
        if agency:
            agreements = agreements.filter(opportunity__agency_name__icontains=agency)

        wins = agreements.filter(outcome="won").count()
        total = agreements.count()

        return {
            "partner_id": partner_id,
            "past_teaming_count": total,
            "wins": wins,
            "win_rate": wins / max(1, total),
            "last_teaming": agreements.order_by("-created_at").values("created_at").first(),
        }
    except Exception as exc:
        logger.warning("Partner history fetch failed: %s", exc)
        return {"partner_id": partner_id, "past_teaming_count": 0, "wins": 0, "win_rate": 0}


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _rank_by_capability(partners: list[dict], query: str) -> list[dict]:
    """Rank partners by capability similarity to query."""
    try:
        import os
        import openai  # type: ignore

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return sorted(partners, key=lambda p: p.get("reliability_score", 0), reverse=True)

        client = openai.AsyncOpenAI(api_key=api_key)
        query_resp = await client.embeddings.create(
            input=query, model="text-embedding-3-small"
        )
        query_vec = query_resp.data[0].embedding

        scored = []
        for p in partners:
            cap_text = " ".join(p.get("capabilities", []) or [])
            if cap_text:
                cap_resp = await client.embeddings.create(
                    input=cap_text, model="text-embedding-3-small"
                )
                cap_vec = cap_resp.data[0].embedding
                similarity = _cosine_sim(query_vec, cap_vec)
            else:
                similarity = 0.0
            scored.append({**p, "_cap_similarity": similarity})

        return sorted(scored, key=lambda x: x["_cap_similarity"], reverse=True)

    except Exception as exc:
        logger.warning("Capability ranking failed, using reliability score: %s", exc)
        return sorted(partners, key=lambda p: p.get("reliability_score", 0), reverse=True)


def _compute_partner_score(
    partner: dict,
    required_capabilities: list[str],
    agency: str,
) -> float:
    score = 0.0

    # Reliability score (0-10 scaled to 0-40)
    reliability = float(partner.get("reliability_score", 5) or 5)
    score += reliability * 4

    # Capability match
    partner_caps = set(c.lower() for c in (partner.get("capabilities") or []))
    required_lower = set(c.lower() for c in required_capabilities)
    if required_lower:
        cap_overlap = len(partner_caps & required_lower) / len(required_lower)
        score += cap_overlap * 30

    # Agency relationship
    past_agencies = [a.lower() for a in (partner.get("past_agencies") or [])]
    if agency.lower() in " ".join(past_agencies):
        score += 15

    # SB bonus
    if partner.get("sb_certifications"):
        score += 5

    # Contract vehicle bonus
    if partner.get("contract_vehicles"):
        score += 5

    # Risk penalty
    risk = partner.get("risk_level", "low")
    penalties = {"low": 0, "medium": -5, "high": -15, "critical": -30}
    score += penalties.get(risk, 0)

    return max(0.0, score)


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
