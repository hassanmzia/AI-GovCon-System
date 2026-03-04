import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _str(value, max_len=None) -> str:
    """Safely coerce a value to string, truncating if needed."""
    if value is None:
        return ""
    if isinstance(value, dict):
        # SAM.gov sometimes returns objects where a string is expected
        value = value.get("name") or value.get("code") or ""
    result = str(value)
    return result[:max_len] if max_len else result


def _nested_name(obj) -> str:
    """Extract .name from a SAM.gov nested object (dict or plain string)."""
    if not obj:
        return ""
    if isinstance(obj, dict):
        return str(obj.get("name") or obj.get("code") or "")
    return str(obj)


class OpportunityNormalizer:
    """Normalize raw SAM.gov API response to Opportunity model fields."""

    def normalize_samgov(self, raw: dict) -> dict:
        """Normalize a single SAM.gov opportunity record."""
        pop = raw.get("placeOfPerformance")
        if not isinstance(pop, dict):
            pop = {}

        return {
            "notice_id": _str(raw.get("noticeId"))[:255],
            "title": _str(raw.get("title"))[:1000],
            "description": (raw.get("description") or "")[:50000],
            "agency": _str(
                (raw.get("fullParentPathName") or "").split(".")[-1].strip()
                or raw.get("department")
            )[:500],
            "sub_agency": _str(raw.get("subtierAgency"))[:500],
            "office": _str(raw.get("office"))[:500],
            "notice_type": _str(raw.get("type"))[:100],
            "sol_number": _str(raw.get("solicitationNumber"))[:255],
            "naics_code": _str(raw.get("naicsCode"))[:10],
            "naics_description": _str(raw.get("naicsSolicitationDescription"))[:500],
            "psc_code": _str(raw.get("classificationCode"))[:10],
            "set_aside": _str(raw.get("typeOfSetAside"))[:200],
            "classification_code": _str(raw.get("classificationCode"))[:50],
            "posted_date": self._parse_date(raw.get("postedDate")),
            "response_deadline": self._parse_date(raw.get("responseDeadLine")),
            "archive_date": self._parse_date(raw.get("archiveDate")),
            "estimated_value": (raw.get("award") or {}).get("amount") or None,
            "award_type": _str(raw.get("typeOfSetAsideDescription"))[:100],
            "place_of_performance": _str(pop.get("streetAddress"))[:500],
            "place_city": _nested_name(pop.get("city"))[:200],
            "place_state": _nested_name(pop.get("state"))[:100],
            "contacts": self._extract_contacts(raw.get("pointOfContact")),
            "attachments": self._extract_attachments(raw.get("resourceLinks")),
            "source_url": _str(
                raw.get("uiLink")
                or (f"https://sam.gov/opp/{raw['noticeId']}/view" if raw.get("noticeId") else "")
            )[:2000],
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

    def _extract_contacts(self, contacts) -> list[dict]:
        result = []
        for c in contacts or []:
            if not isinstance(c, dict):
                continue
            result.append({
                "name": _str(c.get("fullName")),
                "email": _str(c.get("email")),
                "phone": _str(c.get("phone")),
                "type": _str(c.get("type")) or "primary",
            })
        return result

    def _extract_attachments(self, links) -> list[dict]:
        result = []
        for link in links or []:
            if isinstance(link, str):
                result.append({"url": link, "name": link.split("/")[-1], "size": None})
            elif isinstance(link, dict):
                result.append({
                    "url": _str(link.get("url")),
                    "name": _str(link.get("name")),
                    "size": link.get("size"),
                })
        return result
