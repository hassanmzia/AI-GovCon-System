import logging

logger = logging.getLogger(__name__)


class RFPParser:
    """AI-powered RFP document parser."""

    async def extract_requirements(self, document_text: str) -> list[dict]:
        """Extract shall/must statements as requirements."""
        # Phase 1: Regex-based extraction for shall/must/will statements
        import re
        requirements = []
        patterns = [
            r'(?:shall|must|will|is required to)\s+(.{20,500})',
        ]
        req_id = 1
        for pattern in patterns:
            matches = re.findall(pattern, document_text, re.IGNORECASE)
            for match in matches:
                requirements.append({
                    "requirement_id": f"REQ-{req_id:03d}",
                    "requirement_text": match.strip().rstrip('.'),
                    "requirement_type": "mandatory",
                })
                req_id += 1
        logger.info(f"Extracted {len(requirements)} requirements")
        return requirements

    async def extract_evaluation_criteria(self, document_text: str) -> list[dict]:
        """Extract evaluation criteria and weights from Section M."""
        import re

        criteria = []

        # Focus on Section M when present
        section_m = re.compile(
            r'section\s+m[\s\-\u2013:]+.*?(?=section\s+[a-ln-z]|\Z)',
            re.IGNORECASE | re.DOTALL,
        )
        m = section_m.search(document_text)
        search_text = m.group(0) if m else document_text

        weight_re = re.compile(r'(\d{1,3})\s*(?:%|percent|points?)', re.IGNORECASE)

        factor_patterns = [
            r'(?:factor|criterion|criteria|element|area)[:\s]+([A-Za-z][^\n]{5,80})',
            r'([A-Za-z][^\n]{5,60})\s*[\-\u2013]\s*\d{1,3}\s*(?:%|percent|points?)',
            r'(technical\s+approach|management\s+approach|past\s+performance|price[/\s]cost|small\s+business)[^\n]{0,60}',
        ]

        seen: set[str] = set()
        for pattern in factor_patterns:
            for match in re.finditer(pattern, search_text, re.IGNORECASE):
                text = match.group(0).strip()
                if len(text) < 8 or text.lower() in seen:
                    continue
                seen.add(text.lower())
                wm = weight_re.search(text)
                criteria.append({
                    "criterion": text[:200],
                    "weight": int(wm.group(1)) if wm else None,
                    "section": "M",
                })

        if not criteria:
            for standard in ["Technical Approach", "Management Approach",
                              "Past Performance", "Price/Cost"]:
                if re.search(standard, search_text, re.IGNORECASE):
                    criteria.append({"criterion": standard, "weight": None, "section": "M"})

        logger.info("Extracted %d evaluation criteria", len(criteria))
        return criteria

    async def extract_dates(self, document_text: str) -> dict:
        """Extract key dates from the RFP."""
        import re

        dates: dict[str, str] = {}

        date_patterns = {
            "questions_due":         r'(?:questions?|inquiries?|rfis?)\s+(?:are\s+)?due[:\s]+([A-Za-z0-9,\s/\-]+\d{4})',
            "proposal_due":          r'(?:proposal|offer|response|submission)\s+(?:is\s+)?due[:\s]+([A-Za-z0-9,\s/\-]+\d{4})',
            "response_deadline":     r'(?:response\s+deadline|closing\s+date)[:\s]+([A-Za-z0-9,\s/\-]+\d{4})',
            "site_visit":            r'(?:site\s+visit|pre-?proposal\s+conference)[:\s]+([A-Za-z0-9,\s/\-]+\d{4})',
            "award_date":            r'(?:anticipated\s+)?award\s+date[:\s]+([A-Za-z0-9,\s/\-]+\d{4})',
            "period_of_performance": r'period\s+of\s+performance[:\s]+([A-Za-z0-9,\s/\-\u2013]+\d{4})',
            "solicitation_issued":   r'(?:issued|posted|released)[:\s]+([A-Za-z0-9,\s/\-]+\d{4})',
        }

        for key, pattern in date_patterns.items():
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                dates[key] = match.group(1).strip().rstrip('.,;')[:60]

        # Fallback: pick up ISO/US dates on labelled lines
        generic = re.compile(
            r'(?:date|deadline|due)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            re.IGNORECASE,
        )
        for gm in generic.finditer(document_text):
            raw = gm.group(1)
            if raw not in dates.values():
                dates.setdefault("other_date", raw)

        logger.info("Extracted %d dates from RFP", len(dates))
        return dates

    async def extract_page_limits(self, document_text: str) -> dict:
        """Extract page/format limits from Section L."""
        import re

        limits: dict[str, str] = {}

        # Focus on Section L when present
        section_l = re.compile(
            r'section\s+l[\s\-\u2013:]+.*?(?=section\s+[a-km-z]|\Z)',
            re.IGNORECASE | re.DOTALL,
        )
        m = section_l.search(document_text)
        search_text = m.group(0) if m else document_text

        page_patterns = {
            "total_pages":            r'(?:total|overall)\s+(?:page\s+)?limit\s*(?:is|of|:)?\s*(\d+)\s*pages?',
            "technical_pages":        r'technical\s+(?:volume|approach|proposal)[^.]{0,50}?(\d+)\s*pages?',
            "management_pages":       r'management\s+(?:volume|approach|plan)[^.]{0,50}?(\d+)\s*pages?',
            "past_performance_pages": r'past\s+performance[^.]{0,50}?(\d+)\s*pages?',
            "price_pages":            r'(?:price|cost)\s+(?:volume|proposal)[^.]{0,50}?(\d+)\s*pages?',
            "font_size":              r'(?:font\s+size|type\s+size)[:\s]+(\d{2}(?:\.\d)?\s*(?:pt|point))',
            "font_type":              r'(?:font\s+type|typeface)[:\s]+([A-Za-z\s]{3,30})',
            "line_spacing":           r'(?:line\s+spacing|line\s+space)[:\s]+([^\n]{3,40})',
            "margin":                 r'\bmargins?\b[:\s]+([^\n]{3,40})',
            "file_format":            r'(?:file\s+format|acceptable\s+format)[:\s]+(PDF|Word|DOCX|MS\s+Word[^\n]{0,30})',
        }

        for key, pattern in page_patterns.items():
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                limits[key] = match.group(1).strip()[:80]

        # Generic "N-page limit" catch-all
        generic = re.compile(r'(\d+)\s*(?:-|\s)page\s+limit', re.IGNORECASE)
        for gm in generic.finditer(search_text):
            limits.setdefault("page_limit_generic", gm.group(1))

        logger.info("Extracted %d page/format limits from RFP", len(limits))
        return limits
