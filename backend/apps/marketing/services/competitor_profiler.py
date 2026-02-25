"""Competitor profiling service – capabilities, contract history, strengths/weaknesses."""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_USASPENDING_URL = "https://api.usaspending.gov/api/v2"
_SAM_URL = "https://api.sam.gov/entity-information/v3"


async def build_competitor_profile(
    company_name: str,
    naics: list[str] | None = None,
) -> dict[str, Any]:
    """Build a comprehensive competitor intelligence profile.

    Gathers: contract history, capabilities, key personnel, win/loss record,
    strengths/weaknesses, pricing patterns.

    Args:
        company_name: Competitor company name.
        naics: NAICS codes to focus on.

    Returns:
        Comprehensive competitor profile dict.
    """
    import asyncio

    contract_task = asyncio.create_task(_get_competitor_contracts(company_name, naics))
    contract_data = await contract_task

    total_value = contract_data.get("total_value", 0)
    contracts = contract_data.get("contracts", [])

    # Derive insights
    agencies = {}
    naics_dist: dict[str, int] = {}
    for c in contracts:
        agency = c.get("Awarding Agency", "Unknown") or "Unknown"
        agencies[agency] = agencies.get(agency, 0) + 1
        n = c.get("NAICS Code", "Unknown") or "Unknown"
        naics_dist[n] = naics_dist.get(n, 0) + 1

    return {
        "company_name": company_name,
        "total_contract_value": total_value,
        "contract_count": len(contracts),
        "active_agencies": list(agencies.keys())[:10],
        "naics_specializations": list(naics_dist.keys())[:5],
        "recent_wins": contracts[:5],
        "capabilities": _infer_capabilities(contracts, naics_dist),
        "key_personnel": [],  # Populated via web research / LinkedIn
        "clearances": [],  # Populated via SAM.gov entity data
        "sb_certifications": [],
        "contract_vehicles": _infer_vehicles(contracts),
        "strengths": _derive_strengths(contract_data),
        "weaknesses": [],  # Requires qualitative research
        "win_rate_estimate": None,  # Would need lost bids data
        "typical_price_position": "unknown",  # Requires bid price data
        "profile_completeness": 0.5,
        "data_sources": ["usaspending"],
    }


async def get_competitor_win_history(
    company_name: str,
    agency: str | None = None,
    naics: str | None = None,
    years: int = 3,
) -> list[dict[str, Any]]:
    """Get a competitor's recent contract wins.

    Returns:
        List of contract award records.
    """
    data = await _get_competitor_contracts(
        company_name, [naics] if naics else None, agency, years
    )
    return data.get("contracts", [])


async def compare_competitors(
    our_company: str,
    competitors: list[str],
    opportunity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare our company vs. competitors for a specific opportunity context.

    Args:
        our_company: Our company name.
        competitors: List of competitor company names.
        opportunity: Optional opportunity context for targeted comparison.

    Returns:
        Dict with comparative analysis, likely winner, strengths/weaknesses.
    """
    import asyncio

    all_companies = [our_company] + competitors
    profiles = await asyncio.gather(
        *[build_competitor_profile(c) for c in all_companies]
    )

    comparison = {
        "opportunity_context": opportunity.get("title", "General") if opportunity else "General",
        "companies": {},
        "likely_winner": None,
        "competitive_landscape": "moderate",
    }

    max_value = 0
    likely_winner = our_company

    for company, profile in zip(all_companies, profiles):
        comparison["companies"][company] = {
            "total_contract_value": profile["total_contract_value"],
            "contract_count": profile["contract_count"],
            "active_agencies": profile["active_agencies"],
            "strengths": profile["strengths"],
        }
        if profile["total_contract_value"] > max_value and company != our_company:
            max_value = profile["total_contract_value"]
            likely_winner = company  # Richest competitor is likely strongest

    comparison["likely_winner"] = likely_winner

    return comparison


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _get_competitor_contracts(
    company_name: str,
    naics: list[str] | None = None,
    agency: str | None = None,
    years: int = 3,
) -> dict:
    from datetime import datetime

    current_year = datetime.now().year
    filters: dict = {
        "recipient_search_text": [company_name],
        "time_period": [
            {
                "start_date": f"{current_year - years}-01-01",
                "end_date": f"{current_year + 1}-12-31",
            }
        ],
        "award_type_codes": ["A", "B", "C", "D"],
    }
    if naics:
        filters["naics_codes"] = naics
    if agency:
        filters["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency}]

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                f"{_USASPENDING_URL}/search/spending_by_award/",
                json={
                    "filters": filters,
                    "fields": [
                        "Recipient Name", "Award Amount", "Awarding Agency",
                        "NAICS Code", "NAICS Description", "Start Date", "End Date",
                        "Description", "Award ID",
                    ],
                    "limit": 50,
                    "sort": "Award Amount",
                    "order": "desc",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("Competitor contracts fetch failed for %s: %s", company_name, exc)
        return {"contracts": [], "total_value": 0}

    contracts = data.get("results", [])
    total_value = sum(float(c.get("Award Amount") or 0) for c in contracts)

    return {"contracts": contracts, "total_value": total_value}


def _infer_capabilities(contracts: list[dict], naics_dist: dict) -> list[str]:
    """Infer capabilities from contract descriptions and NAICS."""
    capability_map = {
        "541511": "Custom Computer Programming",
        "541512": "Computer Systems Design",
        "541513": "Computer Facilities Management",
        "541519": "IT Services",
        "541330": "Engineering Services",
        "541611": "Management Consulting",
        "541690": "Scientific Research",
        "561210": "Facilities Support Services",
        "621111": "Healthcare Services",
    }
    caps = []
    for naics_code in list(naics_dist.keys())[:5]:
        if naics_code in capability_map:
            caps.append(capability_map[naics_code])
    if not caps and contracts:
        caps.append("Government Services")
    return caps


def _infer_vehicles(contracts: list[dict]) -> list[str]:
    """Attempt to infer contract vehicles from contract data."""
    # Can't easily determine vehicles from basic USASpending data
    # Would need FPDS advanced query
    return ["Unknown – requires FPDS research"]


def _derive_strengths(contract_data: dict) -> list[str]:
    strengths = []
    total = contract_data.get("total_value", 0)
    count = contract_data.get("contract_count", 0)

    if total > 100_000_000:
        strengths.append("Large contract portfolio – established federal contractor")
    if count > 20:
        strengths.append("High win rate – proven track record with federal agencies")

    return strengths or ["Requires qualitative research"]
