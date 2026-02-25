import logging

logger = logging.getLogger(__name__)


class PastPerformanceMatcher:
    """Match past performance records to opportunities using RAG."""

    def match(self, opportunity, top_k: int = 5) -> list[dict]:
        """Find most relevant past performance records."""
        # Phase 1: keyword-based matching
        from apps.past_performance.models import PastPerformance

        all_records = PastPerformance.objects.filter(is_active=True)
        scored = []

        opp_keywords = set(k.lower() for k in (opportunity.keywords or []))
        opp_naics = opportunity.naics_code or ""
        opp_agency = (opportunity.agency or "").lower()

        for record in all_records:
            score = 0.0
            matched = []

            # NAICS match
            if opp_naics and opp_naics in (record.naics_codes or []):
                score += 30
                matched.append(f"NAICS {opp_naics}")

            # Agency match
            if opp_agency and opp_agency in (record.client_agency or "").lower():
                score += 25
                matched.append(f"Agency: {record.client_agency}")

            # Keyword overlap
            record_kw = set(k.lower() for k in (record.relevance_keywords or []))
            overlap = opp_keywords & record_kw
            if overlap:
                kw_score = min(30, len(overlap) * 10)
                score += kw_score
                matched.extend(list(overlap)[:5])

            # Domain overlap
            record_domains = set(d.lower() for d in (record.domains or []))
            domain_overlap = opp_keywords & record_domains
            if domain_overlap:
                score += min(15, len(domain_overlap) * 5)

            if score > 0:
                scored.append({
                    "past_performance_id": str(record.id),
                    "relevance_score": min(100, score),
                    "match_rationale": f"Matched on: {', '.join(matched)}",
                    "matched_keywords": matched,
                })

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:top_k]
