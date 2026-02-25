"""Competitive intelligence service: aggregates competitor and market data."""
import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_deal_manager.strategy.competitive_intel")

_USASPENDING_BASE = "https://api.usaspending.gov/api/v2"


async def build_competitive_landscape(
    opportunity_id: str | None = None,
    naics_codes: list[str] | None = None,
    agency_name: str | None = None,
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Build a competitive landscape for an opportunity or market segment.

    Returns:
        Dict with: top_competitors, market_concentration, incumbent_info,
                   pricing_benchmarks, win_rate_indicators.
    """
    tasks: list = []

    if naics_codes:
        for naics in naics_codes[:3]:
            tasks.append(_get_top_contractors_by_naics(naics))

    if agency_name:
        tasks.append(_get_agency_top_vendors(agency_name))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge competitor lists
    all_competitors: dict[str, dict] = {}
    for result in results:
        if isinstance(result, list):
            for c in result:
                name = c.get("name", "")
                if name:
                    if name in all_competitors:
                        all_competitors[name]["total_awards"] = (
                            all_competitors[name].get("total_awards", 0)
                            + c.get("total_awards", 0)
                        )
                    else:
                        all_competitors[name] = c

    competitors = sorted(
        all_competitors.values(),
        key=lambda x: x.get("total_value", 0),
        reverse=True,
    )[:10]

    hhi = _compute_hhi(competitors)

    return {
        "opportunity_id": opportunity_id,
        "top_competitors": competitors,
        "competitor_count": len(competitors),
        "market_concentration": _classify_hhi(hhi),
        "hhi_score": hhi,
        "pricing_benchmarks": _extract_pricing_benchmarks(competitors),
        "win_rate_indicators": _estimate_win_rate_indicators(competitors),
        "analysis_notes": _generate_analysis_notes(competitors, hhi),
    }


async def analyze_competitor(
    company_name: str,
    naics_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Build a detailed competitor profile from USASpending data."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{_USASPENDING_BASE}/search/spending_by_award/",
                json={
                    "filters": {
                        "recipient_search_text": [company_name],
                        "time_period": [{"start_date": "2019-01-01", "end_date": "2025-12-31"}],
                        "award_type_codes": ["A", "B", "C", "D"],
                    },
                    "fields": [
                        "Award ID", "Award Amount", "Awarding Agency",
                        "Description", "Award Type", "NAICS Code",
                        "Period of Performance Start Date",
                        "Period of Performance Current End Date",
                    ],
                    "page": 1,
                    "limit": 25,
                    "sort": "Award Amount",
                    "order": "desc",
                },
            )
            if resp.status_code == 200:
                awards = resp.json().get("results", [])
            else:
                awards = []
    except Exception as exc:
        logger.warning("Competitor analysis failed for %s: %s", company_name, exc)
        awards = []

    total_value = sum(float(a.get("Award Amount", 0) or 0) for a in awards)
    agencies = list({a.get("Awarding Agency", "") for a in awards if a.get("Awarding Agency")})
    naics_used = list({a.get("NAICS Code", "") for a in awards if a.get("NAICS Code")})

    return {
        "company_name": company_name,
        "total_contract_value": total_value,
        "contract_count": len(awards),
        "primary_agencies": agencies[:5],
        "naics_codes": naics_used[:10],
        "recent_awards": awards[:5],
        "average_award_size": total_value / len(awards) if awards else 0,
        "market_presence": _classify_market_presence(total_value, len(awards)),
    }


async def find_incumbents(
    agency: str,
    naics_code: str | None = None,
    keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Find likely incumbent contractors for a given agency/NAICS combination."""
    try:
        filters: dict = {
            "agencies": [{"type": "awarding", "tier": "toptier", "name": agency}],
            "time_period": [{"start_date": "2022-01-01", "end_date": "2025-12-31"}],
            "award_type_codes": ["A", "B", "C", "D"],
        }
        if naics_code:
            filters["naics_codes"] = [naics_code]
        if keywords:
            filters["keywords"] = keywords

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{_USASPENDING_BASE}/search/spending_by_award/",
                json={
                    "filters": filters,
                    "fields": [
                        "Award ID", "Recipient Name", "Award Amount",
                        "Description", "Period of Performance Current End Date",
                    ],
                    "page": 1,
                    "limit": 10,
                    "sort": "Award Amount",
                    "order": "desc",
                },
            )
            if resp.status_code == 200:
                awards = resp.json().get("results", [])
                return [
                    {
                        "company": a.get("Recipient Name", ""),
                        "award_amount": a.get("Award Amount", 0),
                        "award_id": a.get("Award ID", ""),
                        "description": a.get("Description", "")[:200],
                        "end_date": a.get("Period of Performance Current End Date", ""),
                        "incumbent_likelihood": "high" if float(a.get("Award Amount", 0) or 0) > 1_000_000 else "medium",
                    }
                    for a in awards
                ]
    except Exception as exc:
        logger.warning("Incumbent search failed: %s", exc)
    return []


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _get_top_contractors_by_naics(naics_code: str) -> list[dict]:
    """Get top contractors for a NAICS code from USASpending."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_USASPENDING_BASE}/search/spending_by_recipient/",
                json={
                    "filters": {
                        "naics_codes": [naics_code],
                        "time_period": [{"start_date": "2022-01-01", "end_date": "2025-12-31"}],
                    },
                    "fields": ["recipient_id", "recipient_name", "total_obligated_amount"],
                    "page": 1,
                    "limit": 10,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {
                        "name": r.get("recipient_name", ""),
                        "total_value": float(r.get("total_obligated_amount", 0) or 0),
                        "total_awards": 1,
                        "naics_code": naics_code,
                    }
                    for r in data.get("results", [])
                ]
    except Exception as exc:
        logger.warning("NAICS contractor search failed for %s: %s", naics_code, exc)
    return []


async def _get_agency_top_vendors(agency_name: str) -> list[dict]:
    """Get top vendors for an agency."""
    # Similar pattern to _get_top_contractors_by_naics but filtered by agency
    return []  # Placeholder - real implementation would use USASpending agency filter


def _compute_hhi(competitors: list[dict]) -> float:
    """Compute Herfindahl-Hirschman Index for market concentration."""
    total = sum(c.get("total_value", 0) for c in competitors)
    if not total:
        return 0.0
    shares = [c.get("total_value", 0) / total * 100 for c in competitors]
    return sum(s**2 for s in shares)


def _classify_hhi(hhi: float) -> str:
    """Classify market concentration from HHI score."""
    if hhi < 1500:
        return "competitive"
    if hhi < 2500:
        return "moderately_concentrated"
    return "highly_concentrated"


def _classify_market_presence(total_value: float, count: int) -> str:
    if total_value > 500_000_000:
        return "dominant"
    if total_value > 100_000_000:
        return "major"
    if total_value > 10_000_000:
        return "established"
    return "emerging"


def _extract_pricing_benchmarks(competitors: list[dict]) -> dict:
    values = [c.get("total_value", 0) for c in competitors if c.get("total_value")]
    if not values:
        return {}
    values.sort()
    n = len(values)
    return {
        "min": values[0],
        "max": values[-1],
        "median": values[n // 2],
        "avg": sum(values) / n,
    }


def _estimate_win_rate_indicators(competitors: list[dict]) -> dict:
    top3_share = sum(c.get("total_value", 0) for c in competitors[:3])
    total = sum(c.get("total_value", 0) for c in competitors) or 1
    return {
        "top3_market_share_pct": round(top3_share / total * 100, 1),
        "competition_level": "high" if len(competitors) > 7 else "medium" if len(competitors) > 3 else "low",
    }


def _generate_analysis_notes(competitors: list[dict], hhi: float) -> list[str]:
    notes = []
    if hhi > 2500:
        notes.append("Market is highly concentrated – a few dominant players control this space.")
    elif hhi > 1500:
        notes.append("Market is moderately concentrated with clear leaders and room for challengers.")
    else:
        notes.append("Competitive market – multiple players with no single dominant contractor.")
    if competitors:
        top = competitors[0].get("name", "Unknown")
        notes.append(f"Market leader appears to be {top} by contract value.")
    return notes
