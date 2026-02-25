import asyncio
import logging
from datetime import date

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scan_samgov_opportunities(self):
    """
    Scan SAM.gov for new opportunities, normalize, enrich, and save them.
    """
    from .models import Opportunity, OpportunitySource
    from .services.samgov_client import SAMGovClient
    from .services.normalizer import OpportunityNormalizer
    from .services.enricher import OpportunityEnricher

    logger.info("Starting SAM.gov opportunity scan...")

    try:
        source, _ = OpportunitySource.objects.get_or_create(
            source_type="samgov",
            defaults={
                "name": "SAM.gov",
                "base_url": "https://api.sam.gov/opportunities/v2",
            },
        )
        source.last_scan_at = timezone.now()
        source.last_scan_status = "running"
        source.save(update_fields=["last_scan_at", "last_scan_status"])

        client = SAMGovClient()
        normalizer = OpportunityNormalizer()
        enricher = OpportunityEnricher()

        # Run the async client in a sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Fetch from SAM.gov using the company's NAICS codes
            from .models import CompanyProfile
            profile = CompanyProfile.objects.filter(is_primary=True).first()
            naics = profile.naics_codes if profile else None

            raw_data = loop.run_until_complete(
                client.search_opportunities(naics=naics)
            )
        finally:
            loop.run_until_complete(client.close())
            loop.close()

        opportunities_data = raw_data.get("opportunitiesData", [])
        created_count = 0
        updated_count = 0

        for raw in opportunities_data:
            normalized = normalizer.normalize_samgov(raw)
            enriched = enricher.enrich(normalized)

            notice_id = enriched.pop("notice_id")
            raw_data_field = enriched.pop("raw_data")

            opp, created = Opportunity.objects.update_or_create(
                notice_id=notice_id,
                defaults={
                    "source": source,
                    "raw_data": raw_data_field,
                    **enriched,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        source.last_scan_status = "success"
        source.save(update_fields=["last_scan_status"])

        logger.info(
            f"SAM.gov scan complete: {created_count} new, "
            f"{updated_count} updated out of {len(opportunities_data)} records"
        )
        return {
            "new": created_count,
            "updated": updated_count,
            "total": len(opportunities_data),
        }

    except Exception as exc:
        logger.error(f"SAM.gov scan failed: {exc}")
        try:
            source.last_scan_status = "failed"
            source.save(update_fields=["last_scan_status"])
        except Exception:
            pass
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def score_opportunities(self):
    """
    Score all active opportunities that do not yet have a score.
    """
    from .models import CompanyProfile, Opportunity, OpportunityScore
    from .services.scorer import OpportunityScorer

    logger.info("Starting opportunity scoring...")

    profile = CompanyProfile.objects.filter(is_primary=True).first()
    if not profile:
        logger.warning("No primary company profile found. Skipping scoring.")
        return {"scored": 0, "reason": "no_company_profile"}

    scorer = OpportunityScorer(company_profile=profile)

    unscored = Opportunity.objects.filter(
        is_active=True,
        status="active",
    ).exclude(
        score__isnull=False,
    )

    scored_count = 0
    for opp in unscored.iterator():
        try:
            result = scorer.score(opp)
            OpportunityScore.objects.update_or_create(
                opportunity=opp,
                defaults={
                    "total_score": result["total_score"],
                    "recommendation": result["recommendation"],
                    "naics_match": result["naics_match"],
                    "psc_match": result["psc_match"],
                    "keyword_overlap": result["keyword_overlap"],
                    "capability_similarity": result["capability_similarity"],
                    "past_performance_relevance": result["past_performance_relevance"],
                    "value_fit": result["value_fit"],
                    "deadline_feasibility": result["deadline_feasibility"],
                    "set_aside_match": result["set_aside_match"],
                    "competition_intensity": result["competition_intensity"],
                    "risk_factors": result["risk_factors"],
                    "score_explanation": result["score_explanation"],
                },
            )
            scored_count += 1
        except Exception as exc:
            logger.error(f"Error scoring opportunity {opp.notice_id}: {exc}")

    logger.info(f"Scoring complete: {scored_count} opportunities scored")
    return {"scored": scored_count}


@shared_task
def generate_daily_digest():
    """
    Generate a daily top-10 opportunity digest from the highest scored
    active opportunities.
    """
    from .models import DailyDigest, Opportunity

    logger.info("Generating daily digest...")

    today = date.today()

    # Avoid duplicate digests
    if DailyDigest.objects.filter(date=today).exists():
        logger.info(f"Digest for {today} already exists. Skipping.")
        return {"date": str(today), "status": "already_exists"}

    total_active = Opportunity.objects.filter(is_active=True, status="active").count()

    top_opportunities = (
        Opportunity.objects
        .filter(is_active=True, status="active", score__isnull=False)
        .order_by("-score__total_score")[:10]
    )

    digest = DailyDigest.objects.create(
        date=today,
        total_scanned=total_active,
        total_new=Opportunity.objects.filter(
            created_at__date=today,
        ).count(),
        total_scored=Opportunity.objects.filter(
            score__isnull=False,
            is_active=True,
        ).count(),
        summary=_build_digest_summary(top_opportunities),
    )
    digest.opportunities.set(top_opportunities)

    logger.info(f"Daily digest generated for {today} with {top_opportunities.count()} opportunities")
    return {"date": str(today), "opportunities": top_opportunities.count()}


def _build_digest_summary(opportunities) -> str:
    """Build a plain-text summary of the top opportunities."""
    if not opportunities:
        return "No scored opportunities available for today's digest."

    lines = [f"Top {len(opportunities)} Opportunities for Today", "=" * 40, ""]
    for i, opp in enumerate(opportunities, 1):
        score_val = getattr(opp, "score", None)
        score_display = f"{score_val.total_score:.1f}" if score_val else "N/A"
        rec = score_val.recommendation if score_val else "N/A"
        lines.append(
            f"{i}. [{score_display} - {rec}] {opp.title[:100]}"
        )
        lines.append(f"   Agency: {opp.agency} | NAICS: {opp.naics_code}")
        if opp.response_deadline:
            lines.append(f"   Deadline: {opp.response_deadline.strftime('%Y-%m-%d')}")
        lines.append("")

    return "\n".join(lines)
