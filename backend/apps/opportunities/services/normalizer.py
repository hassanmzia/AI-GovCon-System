import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OpportunityNormalizer:
    """Normalize raw SAM.gov API response to Opportunity model fields."""

    def normalize_samgov(self, raw: dict) -> dict:
        """Normalize a single SAM.gov opportunity record."""
        return {
            "notice_id": raw.get("noticeId", ""),
            "title": raw.get("title", ""),
            "description": raw.get("description", "")[:50000],
            "agency": raw.get("fullParentPathName", "").split(".")[-1].strip() if raw.get("fullParentPathName") else raw.get("department", ""),
            "sub_agency": raw.get("subtierAgency", ""),
            "office": raw.get("office", ""),
            "notice_type": raw.get("type", ""),
            "sol_number": raw.get("solicitationNumber", ""),
            "naics_code": raw.get("naicsCode", ""),
            "naics_description": raw.get("naicsSolicitationDescription", ""),
            "psc_code": raw.get("classificationCode", ""),
            "set_aside": raw.get("typeOfSetAside", ""),
            "classification_code": raw.get("classificationCode", ""),
            "posted_date": self._parse_date(raw.get("postedDate")),
            "response_deadline": self._parse_date(raw.get("responseDeadLine")),
            "archive_date": self._parse_date(raw.get("archiveDate")),
            "estimated_value": raw.get("award", {}).get("amount") if raw.get("award") else None,
            "award_type": raw.get("typeOfSetAsideDescription", ""),
            "place_of_performance": raw.get("placeOfPerformance", {}).get("streetAddress", "") if raw.get("placeOfPerformance") else "",
            "place_city": raw.get("placeOfPerformance", {}).get("city", {}).get("name", "") if raw.get("placeOfPerformance") else "",
            "place_state": raw.get("placeOfPerformance", {}).get("state", {}).get("name", "") if raw.get("placeOfPerformance") else "",
            "contacts": self._extract_contacts(raw.get("pointOfContact", [])),
            "attachments": self._extract_attachments(raw.get("resourceLinks", [])),
            "source_url": raw.get("uiLink", ""),
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
