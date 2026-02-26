import hashlib
import logging
import re
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Strip repeated whitespace and common HTML entities
_ENTITY_RE = re.compile(r"&(?:amp|lt|gt|nbsp|quot|#39|#x27);")
_ENTITY_MAP = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&nbsp;": " ", "&quot;": '"', "&#39;": "'", "&#x27;": "'"}
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Keywords indicating a table column is solicitation-number-like
_SOL_HEADERS = ["solicitation number", "number", "rfp#", "rfq#", "bid#", "ref", "reference", "sol #", "sol#"]
_TITLE_HEADERS = ["title", "description", "solicitation title", "rfp title", "subject", "rfp/rfq", "name"]
_DEADLINE_HEADERS = ["due date", "deadline", "response date", "close date", "closing date", "due", "closing"]
_POSTED_HEADERS = ["posted", "issue date", "release date", "date posted", "date issued", "open date"]

# Date formats tried in order during parsing
_DATE_FORMATS = [
    "%m/%d/%Y %I:%M %p", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y",
    "%Y-%m-%d", "%m-%d-%Y", "%d %B %Y", "%d %b %Y", "%d-%b-%Y",
]

# Lab source definitions
LAB_CONFIGS: list[dict[str, str]] = [
    {
        "name": "Oak Ridge National Laboratory",
        "source_type": "web_scrape",
        "base_url": "https://procurement.ornl.gov",
        "solicitations_url": "https://procurement.ornl.gov/",
        "lab_agency": "Oak Ridge National Laboratory",
        "place_state": "TN",
    },
    {
        "name": "Brookhaven National Laboratory",
        "source_type": "web_scrape",
        "base_url": "https://www.bnl.gov",
        "solicitations_url": "https://www.bnl.gov/ops/procurement/solicitations.php",
        "lab_agency": "Brookhaven National Laboratory",
        "place_state": "NY",
    },
    {
        "name": "Sandia National Laboratories",
        "source_type": "web_scrape",
        "base_url": "https://www.sandia.gov",
        "solicitations_url": "https://www.sandia.gov/partners/working-with-sandia/procurement/current-solicitations/",
        "lab_agency": "Sandia National Laboratories",
        "place_state": "NM",
    },
    {
        "name": "Kansas City National Security Campus",
        "source_type": "web_scrape",
        "base_url": "https://www.nsc.honeywell.com",
        "solicitations_url": "https://www.nsc.honeywell.com/en/doing-business-with-us/subcontracting-opportunities",
        "lab_agency": "Kansas City National Security Campus",
        "place_state": "MO",
    },
]

# Regex to identify solicitation-like links / list items
_SOL_KEYWORD_RE = re.compile(
    r"solicit|rfp|rfq|bid|procurement|contract|proposal|sources.sought|opportunity|subcontract",
    re.IGNORECASE,
)


def _strip_tags(html: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = _TAG_RE.sub(" ", html)
    for entity, replacement in _ENTITY_MAP.items():
        text = text.replace(entity, replacement)
    return _WS_RE.sub(" ", text).strip()


def _find_col(headers: list[str], candidates: list[str]) -> int | None:
    """Return the first column index whose header matches any candidate."""
    for cand in candidates:
        for i, h in enumerate(headers):
            if cand in h or h in cand:
                return i
    return None


def _resolve_url(href: str, base_url: str) -> str:
    """Turn a relative href into an absolute URL."""
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return base_url.rstrip("/") + "/" + href


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    clean = _WS_RE.sub(" ", date_str.strip())
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    logger.debug("Could not parse date: %r", date_str)
    return None


def _make_notice_id(lab_name: str, sol_number: str, title: str) -> str:
    """Generate a stable, unique notice_id for a scraped opportunity."""
    prefix = re.sub(r"[^A-Z]", "", lab_name.upper())[:4]
    if sol_number:
        slug = re.sub(r"[^A-Z0-9\-]", "", sol_number.upper())[:24]
        return f"{prefix}-{slug}" if slug else f"{prefix}-{hashlib.md5(sol_number.encode()).hexdigest()[:12]}"
    return f"{prefix}-{hashlib.md5(title.encode()).hexdigest()[:12]}"


class NationalLabsScraper:
    """
    Scrapes procurement opportunity listings from national laboratory websites.

    Each lab uses a different HTML layout, so the extractor applies a series
    of heuristic strategies (table → list → anchor fallback) and returns a
    uniform list of raw dicts that are then normalized to the Opportunity schema.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; GovConBot/1.0; procurement research)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def __init__(self):
        self.client = httpx.Client(timeout=30.0, follow_redirects=True, headers=self.HEADERS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape_all(self) -> dict[str, list[dict]]:
        """Scrape all national labs. Returns {lab_name: [normalized_opportunity, ...]}."""
        results: dict[str, list[dict]] = {}
        for config in LAB_CONFIGS:
            try:
                opps = self._scrape_lab(config)
                results[config["name"]] = opps
                logger.info("Scraped %d opportunities from %s", len(opps), config["name"])
            except Exception as exc:
                logger.error("Failed to scrape %s: %s", config["name"], exc)
                results[config["name"]] = []
        return results

    def scrape_single(self, lab_name: str) -> list[dict]:
        """Scrape a single lab by its configured name."""
        for config in LAB_CONFIGS:
            if config["name"] == lab_name:
                return self._scrape_lab(config)
        raise ValueError(f"Unknown lab: {lab_name!r}")

    def close(self):
        self.client.close()

    # ------------------------------------------------------------------
    # Internal scraping helpers
    # ------------------------------------------------------------------

    def _scrape_lab(self, config: dict) -> list[dict]:
        url = config["solicitations_url"]
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching %s: %s", url, exc)
            return []

        html = resp.text
        raw_items = self._extract_opportunities(html, config)
        return [self._normalize(item, config) for item in raw_items]

    def _extract_opportunities(self, html: str, config: dict) -> list[dict]:
        """Apply extraction strategies in order, stopping at first non-empty result."""
        items = self._extract_from_table(html, config)
        if items:
            return items
        items = self._extract_from_list(html, config)
        if items:
            return items
        return self._extract_from_links(html, config)

    # --- Strategy 1: HTML tables ---

    def _extract_from_table(self, html: str, config: dict) -> list[dict]:
        items: list[dict] = []
        tables = re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL | re.IGNORECASE)
        for table in tables:
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL | re.IGNORECASE)
            if len(rows) < 2:
                continue

            # Parse header cells (th or first td row)
            header_cells = re.findall(
                r"<t[hd][^>]*>(.*?)</t[hd]>", rows[0], re.DOTALL | re.IGNORECASE
            )
            headers = [_strip_tags(c).lower() for c in header_cells]

            # Skip tables with no procurement-related headers
            if not any(kw in " ".join(headers) for kw in ("title", "solicitation", "rfp", "rfq", "bid", "number", "description")):
                continue

            title_idx = _find_col(headers, _TITLE_HEADERS)
            sol_idx = _find_col(headers, _SOL_HEADERS)
            deadline_idx = _find_col(headers, _DEADLINE_HEADERS)
            posted_idx = _find_col(headers, _POSTED_HEADERS)

            for row in rows[1:]:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
                if not cells:
                    continue

                def cell_text(idx: int | None) -> str:
                    return _strip_tags(cells[idx]).strip() if idx is not None and idx < len(cells) else ""

                def cell_link(idx: int | None) -> str:
                    # Try the specified column first, then fall back to scanning all cells
                    search_cells = ([cells[idx]] if idx is not None and idx < len(cells) else []) + cells
                    for c in search_cells:
                        hrefs = re.findall(r'href=["\']([^"\']+)["\']', c, re.IGNORECASE)
                        if hrefs:
                            return hrefs[0]
                    return ""

                title = cell_text(title_idx)
                if not title:
                    # Fall back to the first cell with enough text
                    for c in cells:
                        t = _strip_tags(c).strip()
                        if len(t) > 10:
                            title = t
                            break
                if not title:
                    continue

                items.append({
                    "title": title,
                    "sol_number": cell_text(sol_idx),
                    "deadline": cell_text(deadline_idx),
                    "posted": cell_text(posted_idx),
                    "url": _resolve_url(cell_link(None), config["base_url"]),
                })

        return items

    # --- Strategy 2: List items ---

    def _extract_from_list(self, html: str, config: dict) -> list[dict]:
        items: list[dict] = []
        lists = re.findall(r"<[uo]l[^>]*>(.*?)</[uo]l>", html, re.DOTALL | re.IGNORECASE)
        for lst in lists:
            lis = re.findall(r"<li[^>]*>(.*?)</li>", lst, re.DOTALL | re.IGNORECASE)
            for li in lis:
                text = _strip_tags(li).strip()
                if len(text) < 10:
                    continue
                hrefs = re.findall(r'href=["\']([^"\']+)["\']', li, re.IGNORECASE)
                link = _resolve_url(hrefs[0], config["base_url"]) if hrefs else ""
                # Skip obvious nav links
                if text.lower() in {"home", "about", "contact", "search", "menu", "news"}:
                    continue
                if not link and not _SOL_KEYWORD_RE.search(text):
                    continue
                items.append({"title": text, "sol_number": "", "deadline": "", "posted": "", "url": link})
        return items

    # --- Strategy 3: Anchor tag fallback ---

    def _extract_from_links(self, html: str, config: dict) -> list[dict]:
        items: list[dict] = []
        seen: set[str] = set()
        anchors = re.findall(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            html, re.DOTALL | re.IGNORECASE
        )
        for href, inner in anchors:
            text = _strip_tags(inner).strip()
            if not text or len(text) < 6:
                continue
            if not (_SOL_KEYWORD_RE.search(href) or _SOL_KEYWORD_RE.search(text)):
                continue
            url = _resolve_url(href, config["base_url"])
            if url in seen:
                continue
            seen.add(url)
            items.append({"title": text, "sol_number": "", "deadline": "", "posted": "", "url": url})
        return items

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def _normalize(self, item: dict, config: dict) -> dict:
        """Convert a raw scraped dict to the Opportunity field schema."""
        title = item.get("title", "").strip()
        sol_number = item.get("sol_number", "").strip()
        url = item.get("url", "").strip()
        notice_id = _make_notice_id(config["name"], sol_number, title)

        return {
            "notice_id": notice_id,
            "title": title[:1000],
            "description": "",
            "agency": config["lab_agency"],
            "sub_agency": "",
            "office": "",
            "notice_type": "Solicitation",
            "sol_number": sol_number,
            "naics_code": "",
            "naics_description": "",
            "psc_code": "",
            "set_aside": "",
            "classification_code": "",
            "posted_date": _parse_date(item.get("posted", "")),
            "response_deadline": _parse_date(item.get("deadline", "")),
            "archive_date": None,
            "estimated_value": None,
            "award_type": "",
            "place_of_performance": "",
            "place_city": "",
            "place_state": config.get("place_state", ""),
            "contacts": [],
            "attachments": [{"url": url, "name": "Solicitation Page", "size": None}] if url else [],
            "source_url": url,
            "raw_data": item,
            "keywords": [],
        }
