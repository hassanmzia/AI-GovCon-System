"""
MCP tool server: USASpending.gov API integration.

Provides async tool functions for querying USASpending.gov for:
  - Federal spending by agency, NAICS, and fiscal year
  - Award recipient research (competitor profiling)
  - Contract vehicle usage patterns
  - Budget/obligation trend analysis

USASpending.gov API: https://api.usaspending.gov/api/v2/

These functions are called by scout_agent, competitor_sim_agent, and
the pricing_agent for market intelligence.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.usaspending")

USA_SPENDING_BASE = "https://api.usaspending.gov/api/v2"
_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Request timeout — USASpending can be slow
_TIMEOUT = 30.0


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def _usa_get(path: str, params: dict | None = None) -> Any:
    """GET request to USASpending.gov API."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{USA_SPENDING_BASE}{path}", params=params or {})
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("USASpending GET %s failed: %s", path, exc)
        return None


async def _usa_post(path: str, body: dict) -> Any:
    """POST request to USASpending.gov API (used for filtered searches)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{USA_SPENDING_BASE}{path}",
                json=body,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("USASpending POST %s failed: %s", path, exc)
        return None


async def _django_get(path: str, params: dict | None = None) -> Any:
    """Proxy through Django backend (has caching and normalization)."""
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}{path}",
                params=params or {},
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Django USASpending proxy %s failed: %s", path, exc)
        return None


def _current_fiscal_year() -> int:
    """Return the current US federal fiscal year (starts Oct 1)."""
    from datetime import date
    today = date.today()
    return today.year if today.month < 10 else today.year + 1


# ── Public tool functions ──────────────────────────────────────────────────────


async def search_spending(
    naics_codes: list[str] | None = None,
    agency_codes: list[str] | None = None,
    fiscal_year: str | int = "current",
    award_type: str = "contracts",
    limit: int = 50,
) -> list[dict]:
    """
    Search USASpending.gov for federal spending matching given criteria.

    Args:
        naics_codes:   List of NAICS codes to filter by (up to 3).
        agency_codes:  List of agency toptier codes (e.g. "097" for DOD).
        fiscal_year:   Fiscal year as int, or "current" / "last" string.
        award_type:    "contracts" | "grants" | "all".
        limit:         Maximum results to return.

    Returns:
        List of normalized spending record dicts.

    Usage by agents:
        from src.mcp_servers.usaspending_tools import search_spending
        spending = await search_spending(naics_codes=["541512"], fiscal_year="current")
    """
    fy = _current_fiscal_year() if fiscal_year == "current" else (
        _current_fiscal_year() - 1 if fiscal_year == "last" else int(fiscal_year)
    )

    # Try Django proxy first (has caching)
    proxy = await _django_get("/api/opportunities/usaspending/search/", {
        "naics": ",".join((naics_codes or [])[:3]),
        "agencies": ",".join((agency_codes or [])[:3]),
        "fiscal_year": fy,
        "limit": limit,
    })
    if isinstance(proxy, list) and proxy:
        return proxy[:limit]
    if isinstance(proxy, dict) and proxy.get("results"):
        return proxy["results"][:limit]

    # Fall back to direct USASpending API
    filters: dict[str, Any] = {
        "time_period": [{"start_date": f"{fy - 1}-10-01", "end_date": f"{fy}-09-30"}],
        "award_type_codes": ["A", "B", "C", "D"] if award_type == "contracts" else [],
    }
    if naics_codes:
        filters["naics_codes"] = {"require": naics_codes[:5]}
    if agency_codes:
        filters["agencies"] = [{"type": "awarding", "tier": "toptier", "toptier_code": c} for c in agency_codes[:3]]

    body = {
        "filters": filters,
        "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency",
                   "Award Date", "NAICS Code", "NAICS Description", "Contract Award Type"],
        "page": 1,
        "limit": min(limit, 100),
        "sort": "Award Amount",
        "order": "desc",
    }

    data = await _usa_post("/search/spending_by_award/", body)
    if not data:
        return []

    results = data.get("results", [])
    return [_normalize_spending_record(r) for r in results]


def _normalize_spending_record(raw: dict) -> dict:
    """Normalize a USASpending API result to a common schema."""
    return {
        "award_id": raw.get("Award ID", ""),
        "recipient_name": raw.get("Recipient Name", ""),
        "amount": raw.get("Award Amount"),
        "agency": raw.get("Awarding Agency", ""),
        "award_date": raw.get("Award Date", ""),
        "naics_code": raw.get("NAICS Code", ""),
        "naics_description": raw.get("NAICS Description", ""),
        "contract_type": raw.get("Contract Award Type", ""),
        "source": "usaspending",
    }


async def get_agency_spending_profile(
    agency_toptier_code: str,
    fiscal_year: int | None = None,
) -> dict:
    """
    Retrieve a spending profile for a specific federal agency.

    Useful for understanding agency budget size, top contractors,
    and dominant NAICS categories before pursuing a new agency.

    Args:
        agency_toptier_code: FPDS agency code (e.g. "097" for DOD, "047" for GSA).
        fiscal_year:         Fiscal year (defaults to current FY).

    Returns:
        Dict with keys: agency_name, total_obligations, top_contractors (list),
                        top_naics (list), fiscal_year.
    """
    fy = fiscal_year or _current_fiscal_year()

    data = await _usa_get(
        f"/agency/{agency_toptier_code}/",
        params={"fiscal_year": fy},
    )
    if not data:
        return {"agency_toptier_code": agency_toptier_code, "fiscal_year": fy, "error": "Agency data unavailable"}

    return {
        "agency_toptier_code": agency_toptier_code,
        "agency_name": data.get("agency_name", ""),
        "total_obligations": data.get("total_obligations"),
        "transaction_count": data.get("transaction_count"),
        "fiscal_year": fy,
        "source": "usaspending",
    }


async def get_recipient_profile(recipient_name: str, limit: int = 20) -> dict:
    """
    Retrieve award history and spending profile for a recipient (competitor).

    Args:
        recipient_name: Company/vendor name to look up.
        limit:          Max number of recent awards to return.

    Returns:
        Dict with keys: recipient_name, total_awards, total_amount,
                        recent_awards (list), top_agencies (list), top_naics (list).
    """
    fy = _current_fiscal_year()

    # Search for awards to this recipient
    body = {
        "filters": {
            "time_period": [{"start_date": f"{fy - 2}-10-01", "end_date": f"{fy}-09-30"}],
            "award_type_codes": ["A", "B", "C", "D"],
            "recipient_search_text": [recipient_name],
        },
        "fields": ["Award ID", "Award Amount", "Awarding Agency", "Award Date",
                   "NAICS Code", "NAICS Description"],
        "page": 1,
        "limit": min(limit, 100),
        "sort": "Award Amount",
        "order": "desc",
    }

    data = await _usa_post("/search/spending_by_award/", body)
    if not data:
        return {"recipient_name": recipient_name, "error": "Data unavailable"}

    results = data.get("results", [])
    awards = [_normalize_spending_record(r) for r in results]

    total_amount = sum(a["amount"] or 0 for a in awards)
    agency_counts: dict[str, float] = {}
    naics_counts: dict[str, float] = {}

    for award in awards:
        ag = award.get("agency", "Unknown")
        naics = award.get("naics_code", "Unknown")
        amt = award.get("amount") or 0
        agency_counts[ag] = agency_counts.get(ag, 0) + amt
        naics_counts[naics] = naics_counts.get(naics, 0) + amt

    top_agencies = sorted(agency_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_naics = sorted(naics_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "recipient_name": recipient_name,
        "total_awards": len(awards),
        "total_amount": total_amount,
        "recent_awards": awards[:10],
        "top_agencies": [{"agency": ag, "amount": amt} for ag, amt in top_agencies],
        "top_naics": [{"naics_code": n, "amount": amt} for n, amt in top_naics],
        "fiscal_year_range": f"{fy - 2}–{fy}",
        "source": "usaspending",
    }


async def get_naics_market_size(
    naics_code: str,
    fiscal_year: int | None = None,
) -> dict:
    """
    Compute total federal market size for a NAICS code in a given fiscal year.

    Used by the pricing agent and market intelligence module to size
    the addressable federal market for a given service area.

    Args:
        naics_code:  6-digit NAICS code.
        fiscal_year: Fiscal year (defaults to current FY).

    Returns:
        Dict with keys: naics_code, total_obligations, award_count,
                        top_agencies (list), fiscal_year.
    """
    fy = fiscal_year or _current_fiscal_year()

    body = {
        "filters": {
            "time_period": [{"start_date": f"{fy - 1}-10-01", "end_date": f"{fy}-09-30"}],
            "award_type_codes": ["A", "B", "C", "D"],
            "naics_codes": {"require": [naics_code]},
        },
        "category": "awarding_agency",
        "limit": 10,
        "page": 1,
    }

    data = await _usa_post("/search/spending_by_category/", body)
    if not data:
        return {"naics_code": naics_code, "fiscal_year": fy, "error": "Market size data unavailable"}

    categories = data.get("results", [])
    total = data.get("total_obligated_amount", 0)

    return {
        "naics_code": naics_code,
        "fiscal_year": fy,
        "total_obligations": total,
        "award_count": data.get("count", 0),
        "top_agencies": [
            {
                "agency": c.get("name", ""),
                "amount": c.get("amount"),
                "id": c.get("id", ""),
            }
            for c in categories[:5]
        ],
        "source": "usaspending",
    }
