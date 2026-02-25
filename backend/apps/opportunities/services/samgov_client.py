import logging
import os
from datetime import datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)


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
        params = {
            "api_key": self.api_key,
            "limit": limit,
            "offset": offset,
            "postedFrom": posted_from or (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y"),
            "postedTo": posted_to or datetime.now().strftime("%m/%d/%Y"),
        }
        if naics:
            params["ncode"] = ",".join(naics)
        if keywords:
            params["q"] = " ".join(keywords)
        if set_aside:
            params["typeOfSetAside"] = set_aside
        if notice_type:
            params["ptype"] = notice_type

        try:
            response = await self.client.get(f"{self.BASE_URL}/search", params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"SAM.gov search returned {data.get('totalRecords', 0)} results")
            return data
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
