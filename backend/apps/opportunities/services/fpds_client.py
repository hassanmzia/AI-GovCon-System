"""
FPDS (Federal Procurement Data System) Client.

Queries FPDS for contract award history, incumbent identification,
and competitive landscape analysis.
"""

import logging
import os
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

FPDS_BASE_URL = "https://www.fpds.gov/ezsearch/LATEST"
FPDS_ATOM_URL = "https://www.fpds.gov/ezsearch/fpdsportal"


class FPDSClient:
    """Client for querying FPDS contract award data."""

    def __init__(self):
        self.base_url = FPDS_ATOM_URL
        self.timeout = 30.0

    async def search_awards(
        self,
        naics_code: str = "",
        agency: str = "",
        vendor_name: str = "",
        date_from: str = "",
        date_to: str = "",
        limit: int = 50,
    ) -> list[dict]:
        """
        Search FPDS for contract awards.

        Returns normalized award records with vendor, value, and contract details.
        """
        query_parts = []
        if naics_code:
            query_parts.append(f"PRINCIPAL_NAICS_CODE:\"{naics_code}\"")
        if agency:
            query_parts.append(f"CONTRACTING_AGENCY_NAME:\"{agency}\"")
        if vendor_name:
            query_parts.append(f"VENDOR_FULL_NAME:\"{vendor_name}\"")
        if date_from:
            query_parts.append(f"SIGNED_DATE:[{date_from},]")
        elif not date_to:
            # Default to last 2 years
            two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y/%m/%d")
            query_parts.append(f"SIGNED_DATE:[{two_years_ago},]")

        query = " ".join(query_parts) if query_parts else "CONTRACTING_AGENCY_NAME:*"

        params = {
            "q": query,
            "s": "0",
            "num_records": str(min(limit, 100)),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}",
                    params=params,
                )
                resp.raise_for_status()
                return self._parse_atom_response(resp.text)
        except Exception as exc:
            logger.error("FPDS search failed: %s", exc)
            return []

    async def get_incumbent(self, agency: str, naics_code: str) -> list[dict]:
        """
        Identify incumbent contractors for a given agency and NAICS.

        Returns list of vendors sorted by total award value.
        """
        awards = await self.search_awards(
            agency=agency,
            naics_code=naics_code,
            limit=100,
        )

        # Aggregate by vendor
        vendor_totals = {}
        for award in awards:
            vendor = award.get("vendor_name", "Unknown")
            if vendor not in vendor_totals:
                vendor_totals[vendor] = {
                    "vendor_name": vendor,
                    "total_value": 0.0,
                    "contract_count": 0,
                    "contracts": [],
                }
            vendor_totals[vendor]["total_value"] += award.get("total_value", 0.0)
            vendor_totals[vendor]["contract_count"] += 1
            vendor_totals[vendor]["contracts"].append({
                "contract_id": award.get("contract_id", ""),
                "description": award.get("description", "")[:200],
                "value": award.get("total_value", 0.0),
                "date": award.get("signed_date", ""),
            })

        # Sort by total value descending
        sorted_vendors = sorted(
            vendor_totals.values(),
            key=lambda v: v["total_value"],
            reverse=True,
        )

        return sorted_vendors[:10]

    async def get_competition_level(self, naics_code: str, agency: str = "") -> dict:
        """
        Estimate competition level for a NAICS code / agency combination.

        Returns average number of bidders and set-aside distribution.
        """
        awards = await self.search_awards(
            naics_code=naics_code,
            agency=agency,
            limit=100,
        )

        if not awards:
            return {"avg_bidders": 0, "total_awards": 0, "competition_level": "unknown"}

        bidder_counts = [a.get("number_of_offers", 1) for a in awards]
        avg_bidders = sum(bidder_counts) / len(bidder_counts) if bidder_counts else 0

        set_aside_dist = {}
        for a in awards:
            sa = a.get("set_aside", "Full and Open")
            set_aside_dist[sa] = set_aside_dist.get(sa, 0) + 1

        level = "low"
        if avg_bidders > 5:
            level = "high"
        elif avg_bidders > 3:
            level = "medium"

        return {
            "avg_bidders": round(avg_bidders, 1),
            "total_awards": len(awards),
            "competition_level": level,
            "set_aside_distribution": set_aside_dist,
        }

    def _parse_atom_response(self, xml_text: str) -> list[dict]:
        """Parse FPDS Atom/XML response into normalized dicts."""
        awards = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_text)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "ns1": "https://www.fpds.gov/FPDS",
            }

            for entry in root.findall(".//atom:entry", ns):
                content = entry.find("atom:content", ns)
                if content is None:
                    continue

                award = content.find(".//ns1:award", ns)
                if award is None:
                    continue

                awards.append(self._extract_award(award, ns))

        except Exception as exc:
            logger.warning("FPDS XML parse failed: %s", exc)

        return awards

    def _extract_award(self, award_elem, ns: dict) -> dict:
        """Extract fields from an FPDS award XML element."""

        def _text(parent, tag):
            el = parent.find(f".//ns1:{tag}", ns)
            return el.text.strip() if el is not None and el.text else ""

        def _attr(parent, tag, attr):
            el = parent.find(f".//ns1:{tag}", ns)
            return el.get(attr, "") if el is not None else ""

        return {
            "contract_id": _text(award_elem, "PIID"),
            "agency": _attr(award_elem, "contractingOfficeAgencyID", "name"),
            "vendor_name": _text(award_elem, "vendorName"),
            "description": _text(award_elem, "descriptionOfContractRequirement"),
            "naics_code": _text(award_elem, "principalNAICSCode"),
            "total_value": float(_text(award_elem, "totalBaseAndAllOptionsValue") or 0),
            "signed_date": _text(award_elem, "signedDate"),
            "number_of_offers": int(_text(award_elem, "numberOfOffersReceived") or 1),
            "set_aside": _attr(award_elem, "typeOfSetAside", "description"),
            "contract_type": _attr(award_elem, "typeOfContractPricing", "description"),
        }
