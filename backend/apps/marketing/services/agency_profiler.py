"""Agency profiling service – builds intelligence profiles from SAM.gov, USASpending, and web."""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_USASPENDING_URL = "https://api.usaspending.gov/api/v2"


async def build_agency_profile(agency_name: str) -> dict[str, Any]:
    """Build a comprehensive intelligence profile for a government agency.

    Gathers: mission, priorities, budget trends, procurement patterns,
    key contacts, relationship scores.

    Args:
        agency_name: Full or partial agency name.

    Returns:
        Comprehensive agency profile dict.
    """
    # Gather data from multiple sources in parallel
    import asyncio

    spending_task = asyncio.create_task(_get_agency_spending(agency_name))
    contractors_task = asyncio.create_task(_get_top_contractors(agency_name))

    spending = await spending_task
    top_contractors = await contractors_task

    return {
        "agency_name": agency_name,
        "mission": f"Mission and priorities for {agency_name} (requires web research)",
        "budget_trends": spending.get("budget_trends", []),
        "total_annual_spending": spending.get("total_annual_spending", 0),
        "procurement_patterns": spending.get("procurement_patterns", {}),
        "top_contractors": top_contractors,
        "naics_distribution": spending.get("naics_distribution", {}),
        "preferred_contract_types": spending.get("preferred_contract_types", []),
        "set_aside_usage": spending.get("set_aside_usage", {}),
        "small_business_utilization": spending.get("small_business_utilization", 0),
        "relationship_score": 5.0,  # Default – updated via CRM interactions
        "key_contacts": [],  # Populated via user input or LinkedIn research
        "profile_completeness": 0.6,
    }


async def get_procurement_patterns(agency_name: str) -> dict[str, Any]:
    """Extract procurement patterns – typical contract size, type, frequency, NAICS focus.

    Returns:
        Dict with avg_contract_size, preferred_types, award_frequency, naics_focus.
    """
    spending = await _get_agency_spending(agency_name)
    return {
        "agency": agency_name,
        "avg_contract_size": spending.get("avg_contract_size", 0),
        "preferred_contract_types": spending.get("preferred_contract_types", []),
        "award_frequency": spending.get("award_frequency", "unknown"),
        "naics_focus": spending.get("naics_distribution", {}),
        "set_aside_preference": spending.get("set_aside_usage", {}),
    }


async def get_budget_trends(agency_name: str, years: int = 3) -> list[dict[str, Any]]:
    """Get year-over-year budget and spending trends for an agency.

    Returns:
        List of annual spending records with year, total, change_pct.
    """
    trends = []
    try:
        from datetime import datetime

        current_fy = datetime.now().year
        for fy in range(current_fy - years, current_fy):
            # Query USASpending for that FY
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        f"{_USASPENDING_URL}/search/spending_by_award/",
                        json={
                            "filters": {
                                "agencies": [{"type": "awarding", "tier": "toptier", "name": agency_name}],
                                "time_period": [
                                    {"start_date": f"{fy}-10-01", "end_date": f"{fy + 1}-09-30"}
                                ],
                                "award_type_codes": ["A", "B", "C", "D"],
                            },
                            "fields": ["Award Amount"],
                            "limit": 1,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        total = data.get("total_count", 0) * 500_000  # Rough estimate
                        trends.append({"fiscal_year": fy + 1, "total_spending": total})
            except Exception:
                trends.append({"fiscal_year": fy + 1, "total_spending": None, "error": "fetch_failed"})
    except Exception as exc:
        logger.error("Budget trends failed for %s: %s", agency_name, exc)

    return trends


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _get_agency_spending(agency_name: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{_USASPENDING_URL}/search/spending_by_award/",
                json={
                    "filters": {
                        "agencies": [{"type": "awarding", "tier": "toptier", "name": agency_name}],
                        "award_type_codes": ["A", "B", "C", "D"],
                    },
                    "fields": [
                        "Award Amount", "NAICS Code", "Recipient Name",
                        "Contract Award Type", "Type of Set Aside",
                    ],
                    "limit": 100,
                    "sort": "Award Amount",
                    "order": "desc",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("USASpending agency spending failed for %s: %s", agency_name, exc)
        return {}

    results = data.get("results", [])
    if not results:
        return {}

    amounts = [float(r.get("Award Amount") or 0) for r in results]
    total = sum(amounts)
    avg = total / max(1, len(amounts))

    # NAICS distribution
    naics_dist: dict[str, int] = {}
    for r in results:
        n = r.get("NAICS Code", "Unknown") or "Unknown"
        naics_dist[n] = naics_dist.get(n, 0) + 1

    # Contract type distribution
    type_dist: dict[str, int] = {}
    for r in results:
        t = r.get("Contract Award Type", "Unknown") or "Unknown"
        type_dist[t] = type_dist.get(t, 0) + 1

    # Set-aside usage
    sa_dist: dict[str, int] = {}
    for r in results:
        sa = r.get("Type of Set Aside", "None") or "None"
        sa_dist[sa] = sa_dist.get(sa, 0) + 1

    return {
        "total_annual_spending": total,
        "avg_contract_size": avg,
        "award_count": len(results),
        "naics_distribution": dict(sorted(naics_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
        "preferred_contract_types": list(type_dist.keys())[:3],
        "set_aside_usage": dict(sorted(sa_dist.items(), key=lambda x: x[1], reverse=True)[:5]),
        "budget_trends": [],
    }


async def _get_top_contractors(agency_name: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{_USASPENDING_URL}/search/spending_by_award/",
                json={
                    "filters": {
                        "agencies": [{"type": "awarding", "tier": "toptier", "name": agency_name}],
                        "award_type_codes": ["A", "B", "C", "D"],
                    },
                    "fields": ["Recipient Name", "Award Amount"],
                    "limit": 100,
                    "sort": "Award Amount",
                    "order": "desc",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    # Aggregate by vendor
    vendors: dict[str, float] = {}
    for r in data.get("results", []):
        name = r.get("Recipient Name", "Unknown") or "Unknown"
        amount = float(r.get("Award Amount") or 0)
        vendors[name] = vendors.get(name, 0) + amount

    return [
        {"company": name, "total_awards": amount}
        for name, amount in sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
