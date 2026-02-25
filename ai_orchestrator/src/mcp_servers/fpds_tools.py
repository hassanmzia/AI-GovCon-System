"""
MCP tool server: FPDS (Federal Procurement Data System) search and award lookup.

Provides async tool functions for querying FPDS contract award data to support:
  - Competitive landscape analysis (who wins in a given agency/NAICS)
  - Incumbent identification for a specific contract/agency
  - Price benchmarking from historical award data
  - Scout agent multi-source ingestion

These functions wrap the Django-side FPDSClient service and expose the data
to AI agents as structured dicts ready for LangGraph nodes.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.fpds")

FPDS_ATOM_URL = "https://www.fpds.gov/ezsearch/fpdsportal"
_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def _django_get(path: str, params: dict | None = None) -> Any:
    """Proxy through the Django backend (which caches/normalizes FPDS responses)."""
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
        logger.warning("Django FPDS proxy %s failed: %s", path, exc)
        return None


async def _fpds_atom_search(query: str, start: int = 0, size: int = 50) -> list[dict]:
    """
    Query the FPDS Atom feed directly.

    Returns a list of normalized award dicts. Falls back to empty list on error.
    """
    params = {
        "q": query,
        "s": str(start),
        "num_records": str(min(size, 100)),
        "rss": "1",
        "version": "1.5",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(FPDS_ATOM_URL, params=params)
            resp.raise_for_status()
            return _parse_fpds_atom(resp.text)
    except Exception as exc:
        logger.error("FPDS Atom search failed (query=%s): %s", query[:80], exc)
        return []


def _parse_fpds_atom(xml_text: str) -> list[dict]:
    """
    Parse FPDS Atom XML feed into normalized award dicts.

    Each dict contains: contract_number, vendor_name, agency, value, award_date, naics_code.
    """
    import xml.etree.ElementTree as ET  # stdlib, safe

    awards = []
    try:
        root = ET.fromstring(xml_text)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "ns1": "https://www.fpds.gov/FPDS",
        }
        for entry in root.findall("atom:entry", ns):
            content = entry.find("atom:content", ns)
            if content is None:
                continue

            def _text(tag: str) -> str:
                el = content.find(f"ns1:{tag}", ns)
                return el.text.strip() if el is not None and el.text else ""

            awards.append({
                "contract_number": _text("contractNumber") or _text("PIID"),
                "vendor_name": _text("vendorName"),
                "agency": _text("contractingAgencyName") or _text("fundingAgencyName"),
                "subagency": _text("contractingSubAgencyName"),
                "value": _safe_float(_text("obligatedAmount") or _text("baseAndAllOptionsValue")),
                "award_date": _text("signedDate") or _text("awardDate"),
                "naics_code": _text("principalNAICSCode"),
                "description": _text("productOrServiceDescription"),
                "place_of_performance": _text("placeOfPerformanceStateName"),
                "contract_type": _text("typeOfContractDescription"),
                "set_aside": _text("typeOfSetAsideDescription"),
            })
    except ET.ParseError as exc:
        logger.warning("FPDS Atom XML parse error: %s", exc)

    return awards


def _safe_float(s: str) -> float | None:
    try:
        return float(s.replace(",", "").replace("$", "")) if s else None
    except (ValueError, TypeError):
        return None


# ── Public tool functions ──────────────────────────────────────────────────────


async def search_recent_awards(
    naics_codes: list[str] | None = None,
    agency: str | None = None,
    vendor_name: str | None = None,
    days_back: int = 365,
    limit: int = 50,
) -> list[dict]:
    """
    Search FPDS for recent contract awards.

    Args:
        naics_codes: List of NAICS codes to filter by (uses first 3).
        agency:      Contracting agency name (partial match).
        vendor_name: Vendor name to search for (partial match).
        days_back:   How many days back to search (default: 365).
        limit:       Maximum results to return.

    Returns:
        List of normalized award dicts with vendor, value, agency, NAICS, dates.

    Usage by agents:
        from src.mcp_servers.fpds_tools import search_recent_awards
        awards = await search_recent_awards(naics_codes=["541512"], agency="DOD")
    """
    # First try Django proxy (has caching)
    proxy_result = await _django_get("/api/opportunities/fpds/awards/", {
        "naics_codes": ",".join((naics_codes or [])[:3]),
        "agency": agency or "",
        "vendor": vendor_name or "",
        "days_back": days_back,
        "limit": limit,
    })
    if isinstance(proxy_result, list) and proxy_result:
        return proxy_result[:limit]
    if isinstance(proxy_result, dict) and proxy_result.get("results"):
        return proxy_result["results"][:limit]

    # Fall back to direct FPDS Atom search
    query_parts = []
    if naics_codes:
        naics_filter = " OR ".join(f'PRINCIPAL_NAICS_CODE:"{n}"' for n in naics_codes[:3])
        query_parts.append(f"({naics_filter})")
    if agency:
        query_parts.append(f'CONTRACTING_AGENCY_NAME:"{agency}"')
    if vendor_name:
        query_parts.append(f'VENDOR_FULL_NAME:"{vendor_name}"')

    date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    query_parts.append(f"SIGNED_DATE:[{date_from},]")

    query = " ".join(query_parts) if query_parts else "CONTRACTING_AGENCY_NAME:*"
    return await _fpds_atom_search(query, size=limit)


async def get_incumbent(agency: str, naics_code: str, limit: int = 10) -> list[dict]:
    """
    Identify incumbent contractors for an agency + NAICS combination.

    Returns the most recent awardees, ranked by award date, useful for
    determining who the incumbent is on a recompete.

    Args:
        agency:     The contracting agency name.
        naics_code: The primary NAICS code for the contract.
        limit:      Number of recent awards to return.

    Returns:
        List of award dicts sorted by award_date descending.
    """
    awards = await search_recent_awards(
        naics_codes=[naics_code],
        agency=agency,
        days_back=1095,  # 3 years
        limit=limit,
    )
    # Sort by award date descending
    def _sort_key(a: dict) -> str:
        return a.get("award_date", "") or ""

    return sorted(awards, key=_sort_key, reverse=True)


async def get_price_benchmarks(
    naics_code: str,
    agency: str | None = None,
    days_back: int = 730,
) -> dict:
    """
    Compute price benchmarks from FPDS historical award data.

    Args:
        naics_code: NAICS code to benchmark.
        agency:     Optional agency filter.
        days_back:  Look-back window in days (default: 2 years).

    Returns:
        Dict with keys: count, min_value, max_value, avg_value, median_value,
                        awards (list of raw award dicts).
    """
    awards = await search_recent_awards(
        naics_codes=[naics_code],
        agency=agency,
        days_back=days_back,
        limit=100,
    )

    values = [a["value"] for a in awards if a.get("value") and a["value"] > 0]
    if not values:
        return {"count": 0, "min_value": None, "max_value": None, "avg_value": None, "median_value": None, "awards": awards}

    values.sort()
    n = len(values)
    avg = sum(values) / n
    median = values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2

    return {
        "count": n,
        "min_value": values[0],
        "max_value": values[-1],
        "avg_value": round(avg, 2),
        "median_value": round(median, 2),
        "naics_code": naics_code,
        "agency": agency,
        "awards": awards[:20],  # Return sample
    }


async def get_vendor_history(vendor_name: str, limit: int = 25) -> list[dict]:
    """
    Retrieve award history for a specific vendor (competitor profiling).

    Args:
        vendor_name: Full or partial vendor/company name.
        limit:       Maximum results to return.

    Returns:
        List of award dicts sorted by award_date descending.
    """
    awards = await search_recent_awards(
        vendor_name=vendor_name,
        days_back=1095,
        limit=limit,
    )
    return sorted(awards, key=lambda a: a.get("award_date", "") or "", reverse=True)
