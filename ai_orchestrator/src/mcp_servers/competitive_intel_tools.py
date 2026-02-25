"""MCP tool server: Competitive intelligence via FPDS, USASpending, and research."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.competitive_intel")

_USASPENDING_URL = "https://api.usaspending.gov/api/v2"
_FPDS_URL = "https://www.fpds.gov/ezsearch/MAIN_PAGE.do"
_SAM_URL = "https://api.sam.gov/entity-information/v3"
_SAM_API_KEY = os.getenv("SAMGOV_API_KEY", "")


async def search_competitor_contracts(
    company_name: str,
    naics: list[str] | None = None,
    agency: str | None = None,
    min_award_year: int = 2019,
    limit: int = 20,
) -> dict[str, Any]:
    """Search USASpending for contracts awarded to a competitor.

    Args:
        company_name: Competitor company name (partial match supported).
        naics: Filter by NAICS codes.
        agency: Filter by awarding agency name.
        min_award_year: Earliest award year.
        limit: Max contracts to return.

    Returns:
        Dict with company_name, contracts (list), total_value, win_count.
    """
    try:
        filters: dict[str, Any] = {
            "recipient_search_text": [company_name],
            "time_period": [{"start_date": f"{min_award_year}-01-01", "end_date": "2099-12-31"}],
            "award_type_codes": ["A", "B", "C", "D"],  # contracts only
        }
        if naics:
            filters["naics_codes"] = naics
        if agency:
            filters["agencies"] = [{"type": "awarding", "tier": "subtier", "name": agency}]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_USASPENDING_URL}/search/spending_by_award/",
                json={
                    "filters": filters,
                    "fields": [
                        "Award ID", "Recipient Name", "Award Amount", "Start Date",
                        "End Date", "Awarding Agency", "Awarding Sub Agency",
                        "Contract Award Type", "NAICS Code", "NAICS Description",
                        "Description",
                    ],
                    "limit": limit,
                    "sort": "Award Amount",
                    "order": "desc",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        contracts = data.get("results", [])
        total_value = sum(c.get("Award Amount", 0) or 0 for c in contracts)

        return {
            "company_name": company_name,
            "contracts": contracts,
            "total_value": total_value,
            "win_count": len(contracts),
            "source": "usaspending",
        }
    except Exception as exc:
        logger.error("USASpending competitor search failed for %s: %s", company_name, exc)
        return {"company_name": company_name, "contracts": [], "error": str(exc)}


async def get_agency_spending(
    agency_name: str,
    naics: list[str] | None = None,
    fiscal_year: int | None = None,
) -> dict[str, Any]:
    """Get spending patterns for an agency by NAICS code.

    Args:
        agency_name: Awarding agency name (partial match).
        naics: NAICS codes to filter.
        fiscal_year: Fiscal year (defaults to last 3 years).

    Returns:
        Dict with agency, total_spending, top_vendors, award_count, avg_award_size.
    """
    from datetime import datetime
    fy = fiscal_year or datetime.now().year - 1

    try:
        filters: dict[str, Any] = {
            "agencies": [{"type": "awarding", "tier": "toptier", "name": agency_name}],
            "time_period": [{"start_date": f"{fy - 2}-10-01", "end_date": f"{fy}-09-30"}],
            "award_type_codes": ["A", "B", "C", "D"],
        }
        if naics:
            filters["naics_codes"] = naics

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_USASPENDING_URL}/search/spending_by_award/",
                json={
                    "filters": filters,
                    "fields": [
                        "Recipient Name", "Award Amount", "Awarding Sub Agency",
                        "NAICS Code", "NAICS Description", "Award ID", "Start Date",
                    ],
                    "limit": 50,
                    "sort": "Award Amount",
                    "order": "desc",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        contracts = data.get("results", [])
        total = sum(c.get("Award Amount", 0) or 0 for c in contracts)

        # Aggregate by vendor
        vendors: dict[str, float] = {}
        for c in contracts:
            name = c.get("Recipient Name", "Unknown")
            vendors[name] = vendors.get(name, 0) + (c.get("Award Amount", 0) or 0)

        top_vendors = sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "agency": agency_name,
            "fiscal_years": list(range(fy - 2, fy + 1)),
            "total_spending": total,
            "award_count": len(contracts),
            "avg_award_size": total / max(1, len(contracts)),
            "top_vendors": [{"name": n, "total": v} for n, v in top_vendors],
            "source": "usaspending",
        }
    except Exception as exc:
        logger.error("Agency spending lookup failed for %s: %s", agency_name, exc)
        return {"agency": agency_name, "error": str(exc)}


async def find_incumbent(
    solicitation_number: str | None = None,
    agency: str | None = None,
    contract_description: str | None = None,
) -> dict[str, Any]:
    """Identify the incumbent contractor for a recompete opportunity.

    Args:
        solicitation_number: The solicitation/contract number to search.
        agency: Awarding agency.
        contract_description: Description keywords if number unknown.

    Returns:
        Dict with incumbent_name, contract_value, period_of_performance, confidence.
    """
    filters: dict[str, Any] = {
        "award_type_codes": ["A", "B", "C", "D"],
    }
    query_terms = []
    if solicitation_number:
        query_terms.append(solicitation_number)
    if agency:
        filters["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency}]
    if contract_description:
        query_terms.append(contract_description)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_USASPENDING_URL}/search/spending_by_award/",
                json={
                    "filters": filters,
                    "keywords": query_terms,
                    "fields": [
                        "Award ID", "Recipient Name", "Award Amount",
                        "Start Date", "End Date", "Description",
                    ],
                    "limit": 5,
                    "sort": "End Date",
                    "order": "desc",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        contracts = data.get("results", [])
        if contracts:
            top = contracts[0]
            return {
                "incumbent_name": top.get("Recipient Name", "Unknown"),
                "contract_id": top.get("Award ID", ""),
                "contract_value": top.get("Award Amount", 0),
                "start_date": top.get("Start Date", ""),
                "end_date": top.get("End Date", ""),
                "description": top.get("Description", ""),
                "confidence": "high" if solicitation_number else "medium",
                "all_matches": contracts,
            }
        return {"incumbent_name": "Unknown", "confidence": "low", "matches": []}
    except Exception as exc:
        logger.error("Incumbent search failed: %s", exc)
        return {"incumbent_name": "Unknown", "error": str(exc)}


async def get_price_benchmarks(
    naics: str,
    agency: str | None = None,
    contract_type: str | None = None,
    min_year: int = 2020,
) -> dict[str, Any]:
    """Pull historical contract award prices for NAICS-based price benchmarking.

    Args:
        naics: NAICS code.
        agency: Optional agency filter.
        contract_type: Optional type filter (e.g. "FFP", "T&M", "CPFF").
        min_year: Earliest award year.

    Returns:
        Dict with naics, avg_award, median_award, min_award, max_award, sample_size.
    """
    filters: dict[str, Any] = {
        "naics_codes": [naics],
        "time_period": [{"start_date": f"{min_year}-01-01", "end_date": "2099-12-31"}],
        "award_type_codes": ["A", "B", "C", "D"],
    }
    if agency:
        filters["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency}]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_USASPENDING_URL}/search/spending_by_award/",
                json={
                    "filters": filters,
                    "fields": ["Award Amount", "NAICS Code", "Awarding Agency", "Recipient Name"],
                    "limit": 100,
                    "sort": "Award Amount",
                    "order": "desc",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        amounts = [
            float(c.get("Award Amount") or 0)
            for c in data.get("results", [])
            if c.get("Award Amount")
        ]

        if amounts:
            amounts_sorted = sorted(amounts)
            mid = len(amounts_sorted) // 2
            median = (
                amounts_sorted[mid]
                if len(amounts_sorted) % 2 != 0
                else (amounts_sorted[mid - 1] + amounts_sorted[mid]) / 2
            )
            return {
                "naics": naics,
                "avg_award": sum(amounts) / len(amounts),
                "median_award": median,
                "min_award": min(amounts),
                "max_award": max(amounts),
                "sample_size": len(amounts),
                "source": "usaspending",
            }

        return {"naics": naics, "sample_size": 0, "avg_award": 0}
    except Exception as exc:
        logger.error("Price benchmark fetch failed for NAICS %s: %s", naics, exc)
        return {"naics": naics, "error": str(exc)}


async def search_company_entity(uei_or_name: str) -> dict[str, Any]:
    """Look up a company entity in SAM.gov.

    Args:
        uei_or_name: UEI code or company name.

    Returns:
        Dict with company details: UEI, CAGE, NAICS, SB certifications, etc.
    """
    params: dict[str, Any] = {"api_key": _SAM_API_KEY}
    if len(uei_or_name) == 12 and uei_or_name.isalnum():
        params["ueiSAM"] = uei_or_name
    else:
        params["legalBusinessName"] = uei_or_name

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{_SAM_URL}/entities", params=params)
            resp.raise_for_status()
            data = resp.json()
            entities = data.get("entityData", [])
            return {
                "query": uei_or_name,
                "entities": entities[:5],
                "count": len(entities),
            }
    except Exception as exc:
        logger.error("SAM.gov entity lookup failed for %s: %s", uei_or_name, exc)
        return {"query": uei_or_name, "entities": [], "error": str(exc)}
