import logging
import re

logger = logging.getLogger(__name__)


class OpportunityEnricher:
    """Enrich opportunities with extracted keywords and metadata."""

    # Common IT/AI keywords for an AI consulting company
    DOMAIN_KEYWORDS = [
        "artificial intelligence", "machine learning", "deep learning", "nlp",
        "natural language processing", "computer vision", "data science",
        "data analytics", "cloud", "aws", "azure", "gcp", "devops", "devsecops",
        "cybersecurity", "zero trust", "fedramp", "cmmc", "nist",
        "agile", "scrum", "microservices", "api", "kubernetes", "docker",
        "rpa", "automation", "digital transformation", "modernization",
        "data engineering", "data lake", "data warehouse", "etl",
        "blockchain", "iot", "edge computing", "5g",
    ]

    def enrich(self, opportunity_data: dict) -> dict:
        """Add enrichment fields to normalized opportunity data."""
        description = opportunity_data.get("description", "").lower()
        title = opportunity_data.get("title", "").lower()
        combined = f"{title} {description}"

        # Extract matching keywords
        keywords = []
        for kw in self.DOMAIN_KEYWORDS:
            if kw in combined:
                keywords.append(kw)

        opportunity_data["keywords"] = keywords
        return opportunity_data
