import logging
import os
from datetime import datetime, timedelta, timezone as dt_timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _parse_retry_after(header_value: str, default: int = 60) -> int:
    """Parse a Retry-After header that may be either an integer number of
    seconds or an HTTP-date string (e.g. 'Thu, 05 Mar 2026 00:00:00 GMT').
    Returns the number of seconds to wait, clamped to at least 1."""
    try:
        return max(1, int(header_value))
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(header_value)
        now = datetime.now(tz=dt_timezone.utc)
        delta = int((retry_at - now).total_seconds())
        return max(1, delta)
    except Exception:
        pass
    return default


class RateLimitError(Exception):
    """Raised when SAM.gov returns 429 Too Many Requests."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class SAMGovClient:
    """Official SAM.gov Opportunities API v2 client."""

    BASE_URL = "https://api.sam.gov/opportunities/v2"

    def __init__(self):
        self.api_key = os.environ.get("SAMGOV_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_opportunities(
        self,
        naics: list[str] | None = None,
        keywords: list[str] | None = None,
        posted_from: str | None = None,
        posted_to: str | None = None,
        set_aside: str | None = None,
        notice_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search SAM.gov for matching opportunities."""
        date_from = posted_from or (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")
        date_to = posted_to or datetime.now().strftime("%m/%d/%Y")

        # Build params as a list of tuples so multiple ncode values are sent as
        # separate query parameters (ncode=X&ncode=Y) rather than a single
        # comma-joined string, which SAM.gov v2 does not support.
        params: list[tuple[str, Any]] = [
            ("api_key", self.api_key),
            ("limit", limit),
            ("offset", offset),
            ("postedFrom", date_from),
            ("postedTo", date_to),
        ]
        if naics:
            for code in naics:
                params.append(("ncode", code))
        if keywords:
            params.append(("q", " ".join(keywords)))
        if set_aside:
            params.append(("typeOfSetAside", set_aside))
        if notice_type:
            params.append(("ptype", notice_type))

        logger.info(
            "SAM.gov search | q=%r | naics=%s | from=%s to=%s | offset=%d limit=%d",
            " ".join(keywords) if keywords else None,
            naics or "all",
            date_from,
            date_to,
            offset,
            limit,
        )

        try:
            response = await self.client.get(f"{self.BASE_URL}/search", params=params)
            if response.status_code == 429:
                retry_after = _parse_retry_after(response.headers.get("Retry-After", "60"))
                logger.warning(
                    "SAM.gov rate limited (429). Retry-After: %ds", retry_after
                )
                raise RateLimitError(
                    f"SAM.gov rate limit hit; retry after {retry_after}s",
                    retry_after=retry_after,
                )
            response.raise_for_status()
            data = response.json()
            logger.info(
                "SAM.gov search returned %d total records (this page: %d)",
                data.get("totalRecords", 0),
                len(data.get("opportunitiesData", [])),
            )
            return data
        except RateLimitError:
            raise
        except httpx.HTTPError as e:
            logger.error(f"SAM.gov API error: {e}")
            raise

    async def get_opportunity_detail(self, notice_id: str) -> dict[str, Any]:
        """Get full details for a specific opportunity."""
        params = {"api_key": self.api_key}
        try:
            response = await self.client.get(f"{self.BASE_URL}/{notice_id}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SAM.gov detail error for {notice_id}: {e}")
            raise

    async def check_amendments(self, notice_id: str) -> list[dict]:
        """Check for amendments on an opportunity."""
        detail = await self.get_opportunity_detail(notice_id)
        return detail.get("relatedNotices", [])

    async def close(self):
        await self.client.aclose()
