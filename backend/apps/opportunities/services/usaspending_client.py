"""
USASpending.gov Client.

Queries USASpending API for federal spending data, incumbent identification,
and spending trend analysis for opportunity scoring.
"""

import logging
import os
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

USASPENDING_BASE_URL = "https://api.usaspending.gov/api/v2"


class USASpendingClient:
    """Client for querying USASpending.gov API."""

    def __init__(self):
        self.base_url = USASPENDING_BASE_URL
        self.timeout = 30.0

    async def search_spending(
        self,
        naics_codes: list[str] = None,
        agency: str = "",
        fiscal_year: str = "",
        limit: int = 50,
    ) -> list[dict]:
        """
        Search USASpending for contract spending data.

        Returns normalized spending records.
        """
        if not fiscal_year or fiscal_year == "current":
            fiscal_year = str(datetime.now().year)

        filters = {"time_period": [{"start_date": f"{fiscal_year}-01-01", "end_date": f"{fiscal_year}-12-31"}]}
        if naics_codes:
            filters["naics_codes"] = [{"naics": code} for code in naics_codes]
        if agency:
            filters["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency}]

        payload = {
            "filters": filters,
            "fields": [
                "Award ID", "Recipient Name", "Award Amount",
                "Description", "Start Date", "End Date",
                "Awarding Agency", "NAICS Code",
            ],
            "limit": min(limit, 100),
            "page": 1,
            "sort": "Award Amount",
            "order": "desc",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/search/spending_by_award/",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return self._normalize_results(data.get("results", []))
        except Exception as exc:
            logger.error("USASpending search failed: %s", exc)
            return []

    async def get_agency_spending_by_naics(
        self,
        agency: str,
        naics_code: str,
        fiscal_year: str = "",
    ) -> dict:
        """
        Get spending breakdown for an agency by NAICS code.

        Returns total spending, top vendors, and trend data.
        """
        if not fiscal_year:
            fiscal_year = str(datetime.now().year)

        results = await self.search_spending(
            naics_codes=[naics_code],
            agency=agency,
            fiscal_year=fiscal_year,
            limit=100,
        )

        # Aggregate by vendor
        vendor_spending = {}
        total_spending = 0.0

        for record in results:
            vendor = record.get("recipient_name", "Unknown")
            amount = record.get("award_amount", 0.0)
            total_spending += amount

            if vendor not in vendor_spending:
                vendor_spending[vendor] = {
                    "vendor_name": vendor,
                    "total_spending": 0.0,
                    "award_count": 0,
                }
            vendor_spending[vendor]["total_spending"] += amount
            vendor_spending[vendor]["award_count"] += 1

        top_vendors = sorted(
            vendor_spending.values(),
            key=lambda v: v["total_spending"],
            reverse=True,
        )[:10]

        return {
            "agency": agency,
            "naics_code": naics_code,
            "fiscal_year": fiscal_year,
            "total_spending": total_spending,
            "award_count": len(results),
            "top_vendors": top_vendors,
        }

    async def get_spending_trend(
        self,
        agency: str = "",
        naics_code: str = "",
        years: int = 5,
    ) -> list[dict]:
        """
        Get spending trend over multiple fiscal years.

        Returns annual spending totals for trend analysis.
        """
        current_year = datetime.now().year
        trend = []

        for year_offset in range(years):
            fy = str(current_year - year_offset)
            try:
                result = await self.get_agency_spending_by_naics(
                    agency=agency,
                    naics_code=naics_code,
                    fiscal_year=fy,
                )
                trend.append({
                    "fiscal_year": fy,
                    "total_spending": result["total_spending"],
                    "award_count": result["award_count"],
                })
            except Exception:
                trend.append({
                    "fiscal_year": fy,
                    "total_spending": 0.0,
                    "award_count": 0,
                })

        return sorted(trend, key=lambda t: t["fiscal_year"])

    async def get_recipient_profile(self, vendor_name: str) -> dict:
        """
        Get a vendor/recipient spending profile.

        Returns the vendor's total awards, agencies, and NAICS breakdown.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/recipient/duns/",
                    json={"keyword": vendor_name, "limit": 5},
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if results:
                    return {
                        "vendor_name": results[0].get("recipient_name", vendor_name),
                        "recipient_id": results[0].get("recipient_id", ""),
                        "total_amount": results[0].get("amount", 0.0),
                    }
        except Exception as exc:
            logger.warning("USASpending recipient lookup failed: %s", exc)

        return {"vendor_name": vendor_name, "recipient_id": "", "total_amount": 0.0}

    def _normalize_results(self, results: list) -> list[dict]:
        """Normalize USASpending API results to a common format."""
        normalized = []
        for r in results:
            normalized.append({
                "award_id": r.get("Award ID", ""),
                "recipient_name": r.get("Recipient Name", ""),
                "award_amount": float(r.get("Award Amount", 0) or 0),
                "description": r.get("Description", ""),
                "start_date": r.get("Start Date", ""),
                "end_date": r.get("End Date", ""),
                "awarding_agency": r.get("Awarding Agency", ""),
                "naics_code": r.get("NAICS Code", ""),
            })
        return normalized
