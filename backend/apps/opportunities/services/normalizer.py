import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OpportunityNormalizer:
    """Normalize raw SAM.gov API response to Opportunity model fields."""

    def normalize_samgov(self, raw: dict) -> dict:
        """Normalize a single SAM.gov opportunity record."""
        pop = raw.get("placeOfPerformance") or {}
        return {
            "notice_id": raw.get("noticeId") or "",
            "title": raw.get("title") or "",
            "description": (raw.get("description") or "")[:50000],
            "agency": (raw.get("fullParentPathName") or "").split(".")[-1].strip() or raw.get("department") or "",
            "sub_agency": raw.get("subtierAgency") or "",
            "office": raw.get("office") or "",
            "notice_type": raw.get("type") or "",
            "sol_number": raw.get("solicitationNumber") or "",
            "naics_code": raw.get("naicsCode") or "",
            "naics_description": raw.get("naicsSolicitationDescription") or "",
            "psc_code": raw.get("classificationCode") or "",
            "set_aside": raw.get("typeOfSetAside") or "",
            "classification_code": raw.get("classificationCode") or "",
            "posted_date": self._parse_date(raw.get("postedDate")),
            "response_deadline": self._parse_date(raw.get("responseDeadLine")),
            "archive_date": self._parse_date(raw.get("archiveDate")),
            "estimated_value": raw.get("award", {}).get("amount") or None,
            "award_type": raw.get("typeOfSetAsideDescription") or "",
            "place_of_performance": pop.get("streetAddress") or "",
            "place_city": (pop.get("city") or {}).get("name") or "",
            "place_state": (pop.get("state") or {}).get("name") or "",
            "contacts": self._extract_contacts(raw.get("pointOfContact", [])),
            "attachments": self._extract_attachments(raw.get("resourceLinks", [])),
            "source_url": raw.get("uiLink") or (
                f"https://sam.gov/opp/{raw['noticeId']}/view" if raw.get("noticeId") else ""
            ),
            "raw_data": raw,
        }

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        for fmt in ("%m/%d/%Y %I:%M %p", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except (ValueError, AttributeError):
                continue
        # Fallback: ISO 8601 with timezone offset (e.g. 2026-03-31T17:00:00+02:00)
        try:
            return datetime.fromisoformat(date_str.strip())
        except (ValueError, AttributeError):
            pass
        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _extract_contacts(self, contacts: list) -> list[dict]:
        result = []
        for c in contacts or []:
            result.append({
                "name": c.get("fullName", ""),
                "email": c.get("email", ""),
                "phone": c.get("phone", ""),
                "type": c.get("type", "primary"),
            })
        return result

    def _extract_attachments(self, links: list) -> list[dict]:
        result = []
        for link in links or []:
            if isinstance(link, str):
                result.append({"url": link, "name": link.split("/")[-1], "size": None})
            elif isinstance(link, dict):
                result.append({
                    "url": link.get("url", ""),
                    "name": link.get("name", ""),
                    "size": link.get("size"),
                })
        return result
