"""Government database searcher: USASpending, FPDS, SAM.gov entity search."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_deal_manager.research.gov_db")

_USASPENDING_BASE = "https://api.usaspending.gov/api/v2"
_SAM_BASE = "https://api.sam.gov"
_FPDS_BASE = "https://www.fpds.gov/ezsearch/FEEDS/ATOM"


async def search_gov_databases(
    query: str,
    research_type: str = "general",
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Search multiple government databases for *query*.

    Routes to appropriate databases based on research_type:
    - "competitor": USASpending contract awards
    - "agency": USASpending agency spending
    - "general": SAM.gov entity search + USASpending keyword
    """
    results: list[dict[str, Any]] = []

    if research_type in ("competitor", "general"):
        awards = await search_usaspending_awards(query, limit=limit)
        results.extend(awards)

    if research_type in ("agency", "general"):
        agency = await search_agency_spending(query)
        if agency:
            results.append(agency)

    if research_type in ("general", "regulatory"):
        sam_results = await search_sam_entities(query, limit=min(limit, 5))
        results.extend(sam_results)

    return results[:limit]


async def search_usaspending_awards(
    keyword: str,
    limit: int = 10,
    award_type: str | None = None,
) -> list[dict[str, Any]]:
    """Search USASpending.gov for contract awards matching *keyword*.

    Returns list of award summary dicts.
    """
    try:
        payload: dict[str, Any] = {
            "filters": {
                "keywords": [keyword],
                "time_period": [{"start_date": "2020-01-01", "end_date": "2025-12-31"}],
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Award Amount",
                "Awarding Agency",
                "Award Type",
                "Description",
                "Period of Performance Start Date",
                "Period of Performance Current End Date",
            ],
            "page": 1,
            "limit": limit,
            "sort": "Award Amount",
            "order": "desc",
        }
        if award_type:
            payload["filters"]["award_type_codes"] = [award_type]

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_USASPENDING_BASE}/search/spending_by_award/",
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                awards = data.get("results", [])
                return [
                    {
                        "source": "usaspending",
                        "type": "contract_award",
                        "title": a.get("Description", "Contract Award"),
                        "recipient": a.get("Recipient Name", ""),
                        "amount": a.get("Award Amount", 0),
                        "agency": a.get("Awarding Agency", ""),
                        "award_id": a.get("Award ID", ""),
                        "start_date": a.get("Period of Performance Start Date", ""),
                        "end_date": a.get("Period of Performance Current End Date", ""),
                        "url": f"https://www.usaspending.gov/award/{a.get('Award ID', '')}",
                    }
                    for a in awards
                ]
    except Exception as exc:
        logger.warning("USASpending awards search failed: %s", exc)
    return []


async def search_agency_spending(agency_name: str) -> dict[str, Any] | None:
    """Get spending summary for an agency by name from USASpending."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Search for agency
            resp = await client.get(
                f"{_USASPENDING_BASE}/references/toptier_agencies/",
            )
            if resp.status_code == 200:
                agencies = resp.json().get("results", [])
                name_lower = agency_name.lower()
                matched = next(
                    (a for a in agencies if name_lower in a.get("agency_name", "").lower()),
                    None,
                )
                if matched:
                    return {
                        "source": "usaspending",
                        "type": "agency_profile",
                        "title": matched.get("agency_name", agency_name),
                        "toptier_code": matched.get("toptier_code", ""),
                        "abbreviation": matched.get("abbreviation", ""),
                        "budget": matched.get("budget_authority_amount", 0),
                        "obligated": matched.get("obligated_amount", 0),
                        "url": f"https://www.usaspending.gov/agency/{matched.get('abbreviation', '').lower()}",
                    }
    except Exception as exc:
        logger.warning("Agency spending search failed: %s", exc)
    return None


async def search_sam_entities(
    keyword: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search SAM.gov entity registrations for *keyword*."""
    api_key = os.getenv("SAMGOV_API_KEY", "")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{_SAM_BASE}/entity-information/v3/entities",
                params={
                    "api_key": api_key,
                    "legalBusinessName": keyword,
                    "registrationStatus": "A",
                    "pageSize": limit,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                entities = data.get("entityData", [])
                return [
                    {
                        "source": "sam_gov",
                        "type": "entity",
                        "title": e.get("entityRegistration", {}).get("legalBusinessName", ""),
                        "uei": e.get("entityRegistration", {}).get("ueiSAM", ""),
                        "cage": e.get("entityRegistration", {}).get("cageCode", ""),
                        "status": e.get("entityRegistration", {}).get("registrationStatus", ""),
                        "url": f"https://sam.gov/entity/{e.get('entityRegistration', {}).get('ueiSAM', '')}",
                    }
                    for e in entities
                ]
    except Exception as exc:
        logger.warning("SAM entity search failed: %s", exc)
    return []


async def get_award_details(award_id: str) -> dict[str, Any]:
    """Fetch full details for a specific USASpending award."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{_USASPENDING_BASE}/awards/{award_id}/")
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("Award detail fetch failed for %s: %s", award_id, exc)
    return {}
