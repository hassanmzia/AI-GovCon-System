"""
Agency Forecast Portal Client.

Scrapes and ingests pre-RFP pipeline data from agency forecast portals
(e.g., DHS, DOD, DOE, NASA procurement forecasts).
"""

import logging
import os
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


# Known forecast data sources
FORECAST_SOURCES = {
    "dhs": {
        "name": "DHS Procurement Forecast",
        "url": "https://www.dhs.gov/procurement-forecast",
        "type": "web_scrape",
    },
    "gsa": {
        "name": "GSA Forecast of Contracting Opportunities",
        "url": "https://hallways.cap.gsa.gov/app/#/gateway/FBO/forecast",
        "type": "web_scrape",
    },
    "doe": {
        "name": "DOE Acquisition Forecast",
        "url": "https://www.energy.gov/management/acquisition-forecast",
        "type": "web_scrape",
    },
}


class ForecastClient:
    """Client for ingesting agency forecast portal data."""

    def __init__(self):
        self.timeout = 30.0

    async def get_forecasts(
        self,
        agency: str = "",
        naics_codes: list[str] = None,
        fiscal_year: str = "",
    ) -> list[dict]:
        """
        Get forecast opportunities from agency portals.

        Since forecast portals vary widely, this provides a normalized
        interface. In production, each agency portal gets a dedicated
        scraper/parser.
        """
        if not fiscal_year:
            fiscal_year = str(datetime.now().year)

        forecasts = []

        # For now, use SAM.gov's forecast data as primary source
        try:
            sam_forecasts = await self._fetch_sam_forecasts(
                agency=agency,
                naics_codes=naics_codes,
                fiscal_year=fiscal_year,
            )
            forecasts.extend(sam_forecasts)
        except Exception as exc:
            logger.warning("SAM.gov forecast fetch failed: %s", exc)

        return forecasts

    async def _fetch_sam_forecasts(
        self,
        agency: str = "",
        naics_codes: list[str] = None,
        fiscal_year: str = "",
    ) -> list[dict]:
        """
        Fetch pre-solicitation and sources sought notices from SAM.gov
        as a proxy for forecast data.
        """
        api_key = os.getenv("SAM_GOV_API_KEY", "")
        if not api_key:
            logger.warning("SAM_GOV_API_KEY not set, skipping forecast fetch")
            return []

        params = {
            "api_key": api_key,
            "ntype": "p,r",  # Presolicitation + Sources Sought
            "limit": 50,
            "postedFrom": f"01/01/{fiscal_year}",
        }
        if agency:
            params["deptname"] = agency
        if naics_codes:
            params["naics"] = naics_codes[0]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    "https://api.sam.gov/opportunities/v2/search",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
                return self._normalize_sam_forecasts(
                    data.get("opportunitiesData", [])
                )
        except Exception as exc:
            logger.error("SAM.gov forecast API call failed: %s", exc)
            return []

    def _normalize_sam_forecasts(self, opps: list) -> list[dict]:
        """Normalize SAM.gov pre-solicitation data."""
        normalized = []
        for opp in opps:
            normalized.append({
                "notice_id": opp.get("noticeId", ""),
                "title": opp.get("title", ""),
                "agency": opp.get("department", ""),
                "sub_agency": opp.get("subtier", ""),
                "description": opp.get("description", "")[:2000],
                "naics_code": opp.get("naicsCode", ""),
                "set_aside": opp.get("typeOfSetAside", ""),
                "posted_date": opp.get("postedDate", ""),
                "response_deadline": opp.get("responseDeadLine", ""),
                "notice_type": opp.get("type", ""),
                "source": "forecast",
                "is_forecast": True,
                "estimated_release_date": opp.get("archiveDate", ""),
            })
        return normalized
