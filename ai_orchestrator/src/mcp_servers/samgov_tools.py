"""MCP tool server: SAM.gov search, opportunity detail, amendments, Q&A."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.samgov")

SAM_BASE = "https://api.sam.gov/opportunities/v2"
_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")


def _api_key() -> str:
    return os.getenv("SAMGOV_API_KEY", "")


async def search_opportunities(
    keywords: list[str] | None = None,
    naics: list[str] | None = None,
    posted_from: str | None = None,
    posted_to: str | None = None,
    set_aside: str | None = None,
    notice_type: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """Search SAM.gov for opportunities matching the given criteria.

    Args:
        keywords: Free-text search keywords.
        naics: NAICS codes to filter by.
        posted_from: Date filter – format MM/DD/YYYY.
        posted_to: Date filter – format MM/DD/YYYY.
        set_aside: Set-aside type code (e.g. "SBA", "HZC", "WOSB").
        notice_type: Notice type (e.g. "o" = solicitation, "p" = presolicitation).
        limit: Number of results to return (max 100).
        offset: Pagination offset.

    Returns:
        Dict with keys: totalRecords, opportunitiesData (list of notice dicts).
    """
    from datetime import datetime, timedelta

    params: dict[str, Any] = {
        "api_key": _api_key(),
        "limit": limit,
        "offset": offset,
        "postedFrom": posted_from or (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y"),
        "postedTo": posted_to or datetime.now().strftime("%m/%d/%Y"),
    }
    if keywords:
        params["q"] = " ".join(keywords)
    if naics:
        params["ncode"] = ",".join(naics)
    if set_aside:
        params["typeOfSetAside"] = set_aside
    if notice_type:
        params["ptype"] = notice_type

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{SAM_BASE}/search", params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("SAM.gov search failed: %s", exc)
        return {"totalRecords": 0, "opportunitiesData": [], "error": str(exc)}


async def get_opportunity_detail(notice_id: str) -> dict[str, Any]:
    """Fetch full detail for a single SAM.gov notice by noticeId.

    Returns:
        Full opportunity dict including description, attachments, and contact info.
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{SAM_BASE}/{notice_id}",
                params={"api_key": _api_key()},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("SAM.gov detail fetch failed for %s: %s", notice_id, exc)
        return {"noticeId": notice_id, "error": str(exc)}


async def get_amendments(notice_id: str) -> dict[str, Any]:
    """Return a list of amendments (related notices) for *notice_id*.

    SAM.gov amendments are related notices. This queries the API for all
    notices with the same base solicitation number.

    Returns:
        Dict with keys: parentNoticeId, amendments (list of notice dicts).
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{SAM_BASE}/{notice_id}/history",
                params={"api_key": _api_key()},
            )
            resp.raise_for_status()
            return {"parentNoticeId": notice_id, "amendments": resp.json()}
    except Exception as exc:
        logger.warning("SAM.gov amendments failed for %s: %s", notice_id, exc)
        return {"parentNoticeId": notice_id, "amendments": [], "error": str(exc)}


async def get_questions_and_answers(notice_id: str) -> dict[str, Any]:
    """Return vendor Q&A for *notice_id* as published on SAM.gov.

    Returns:
        Dict with keys: noticeId, questions (list of {question, answer, date}).
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{SAM_BASE}/{notice_id}/resources",
                params={"api_key": _api_key(), "resourceType": "qanda"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"noticeId": notice_id, "questions": data.get("resources", [])}
    except Exception as exc:
        logger.warning("SAM.gov Q&A fetch failed for %s: %s", notice_id, exc)
        return {"noticeId": notice_id, "questions": [], "error": str(exc)}


async def ingest_opportunity(notice_id: str) -> dict[str, Any]:
    """Fetch a SAM.gov notice and persist it via the Django API.

    Convenience wrapper combining detail fetch + Django ingest endpoint.
    Returns the created/updated Django Opportunity object.
    """
    detail = await get_opportunity_detail(notice_id)
    if "error" in detail and not detail.get("noticeId"):
        return detail
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/opportunities/ingest/",
                json={"notice": detail},
                headers={"X-Service-Token": os.getenv("DJANGO_SERVICE_TOKEN", "")},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Django ingest failed for %s: %s", notice_id, exc)
        return {"noticeId": notice_id, "error": str(exc)}
