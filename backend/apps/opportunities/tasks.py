import asyncio
import logging
from contextlib import contextmanager
from datetime import date

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

_SAMGOV_LOCK_KEY = "lock:scan_samgov_opportunities"
_SAMGOV_LOCK_TIMEOUT = 1800  # 30 min — maximum expected run time


@contextmanager
def _samgov_task_lock():
    """Redis-backed lock that prevents concurrent SAM.gov scan executions.

    Uses Django's cache (backed by Redis in this project) with ``add`` semantics
    so that only the first caller acquires the lock; subsequent callers raise
    ``RuntimeError`` without blocking.
    """
    acquired = cache.add(_SAMGOV_LOCK_KEY, "1", timeout=_SAMGOV_LOCK_TIMEOUT)
    if not acquired:
        raise RuntimeError("scan_samgov_opportunities is already running — skipping duplicate")
    try:
        yield
    finally:
        cache.delete(_SAMGOV_LOCK_KEY)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scan_samgov_opportunities(self):
    """
    Scan SAM.gov for new opportunities, normalize, enrich, and save them.
    """
    from .models import Opportunity, OpportunitySource
    from .services.samgov_client import SAMGovClient, RateLimitError
    from .services.normalizer import OpportunityNormalizer
    from .services.enricher import OpportunityEnricher

    import os
    if not os.environ.get("SAMGOV_API_KEY"):
        logger.warning("SAMGOV_API_KEY not set — skipping SAM.gov scan")
        return {"new": 0, "updated": 0, "total": 0, "skipped": "no api key"}

    # Prevent multiple concurrent instances from hammering the SAM.gov API.
    try:
        lock_ctx = _samgov_task_lock()
        lock_ctx.__enter__()
    except RuntimeError as lock_err:
        logger.warning(str(lock_err))
        return {"skipped": "already_running"}

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
            # naics=[] (empty list) means no primary profile had codes; treat as None
            if not naics:
                naics = None
            logger.info(
                "SAM.gov scan starting | profile=%s | naics=%s",
                profile.name if profile else "none",
                naics or "unfiltered (all)",
            )

            # ---- helper: paginate a single search query ----
            def _fetch_all(**search_kwargs) -> list[dict]:
                results = []
                _offset = 0
                while True:
                    page = loop.run_until_complete(
                        client.search_opportunities(**search_kwargs, limit=100, offset=_offset)
                    )
                    batch = page.get("opportunitiesData", [])
                    results.extend(batch)
                    total = page.get("totalRecords", 0)
                    _offset += len(batch)
                    if not batch or _offset >= total:
                        break
                    logger.info("SAM.gov paginating: fetched %d/%d", _offset, total)
                return results

            # Pass 1: search by NAICS codes
            opportunities_data = _fetch_all(naics=naics) if naics else []
            seen_ids = {r.get("noticeId") for r in opportunities_data}
            logger.info("NAICS search returned %d records", len(opportunities_data))

            # Pass 2: keyword searches to catch PSC-relevant opportunities
            # that may not share our NAICS codes (SAM.gov has no PSC filter).
            KEYWORD_QUERIES = [
                ["software development", "IT services"],
                ["cybersecurity", "information security"],
                ["cloud computing", "hosting", "platform"],
                ["research and development", "R&D"],
                ["training", "education services"],
                ["artificial intelligence", "machine learning"],
            ]
            for kw_group in KEYWORD_QUERIES:
                kw_results = _fetch_all(keywords=kw_group)
                for r in kw_results:
                    if r.get("noticeId") not in seen_ids:
                        opportunities_data.append(r)
                        seen_ids.add(r.get("noticeId"))
            logger.info(
                "Total unique opportunities after keyword passes: %d",
                len(opportunities_data),
            )
        finally:
            loop.run_until_complete(client.close())
            loop.close()

        created_count = 0
        updated_count = 0
        error_count = 0

        for raw in opportunities_data:
            try:
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
            except Exception as record_exc:
                error_count += 1
                if error_count <= 5:
                    logger.warning(
                        "Skipping opportunity %s [%s]: %s",
                        raw.get("noticeId", "?"),
                        type(record_exc).__name__,
                        record_exc,
                    )
                elif error_count == 6:
                    logger.warning("Further per-record errors suppressed (showing first 5 only)")

        source.last_scan_status = "success"
        source.save(update_fields=["last_scan_status"])

        logger.info(
            f"SAM.gov scan complete: {created_count} new, "
            f"{updated_count} updated, {error_count} skipped "
            f"out of {len(opportunities_data)} records"
        )
        lock_ctx.__exit__(None, None, None)
        return {
            "new": created_count,
            "updated": updated_count,
            "skipped": error_count,
            "total": len(opportunities_data),
        }

    except RateLimitError as exc:
        lock_ctx.__exit__(type(exc), exc, exc.__traceback__)
        logger.warning(
            "SAM.gov rate limited — scheduling retry in %ds (attempt %d/%d)",
            exc.retry_after,
            self.request.retries + 1,
            self.max_retries,
        )
        try:
            source.last_scan_status = "failed"
            source.save(update_fields=["last_scan_status"])
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=exc.retry_after)

    except Exception as exc:
        lock_ctx.__exit__(type(exc), exc, exc.__traceback__)
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scan_national_labs(self):
    """
    Scrape all configured national lab procurement pages and persist opportunities.
    """
    from .models import Opportunity, OpportunitySource
    from .services.national_labs_scraper import NationalLabsScraper, LAB_CONFIGS
    from .services.enricher import OpportunityEnricher

    logger.info("Starting national labs procurement scan...")

    enricher = OpportunityEnricher()
    scraper = NationalLabsScraper()

    try:
        all_results = scraper.scrape_all()
    except Exception as exc:
        logger.error(f"National labs scrape failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        scraper.close()

    total_created = 0
    total_updated = 0

    for config in LAB_CONFIGS:
        lab_name = config["name"]
        opps = all_results.get(lab_name, [])

        source, _ = OpportunitySource.objects.get_or_create(
            name=lab_name,
            defaults={
                "source_type": "web_scrape",
                "base_url": config["base_url"],
                "is_active": True,
                "scan_frequency_hours": 24,
            },
        )
        source.last_scan_at = timezone.now()
        source.last_scan_status = "running"
        source.save(update_fields=["last_scan_at", "last_scan_status"])

        created = 0
        updated = 0
        for normalized in opps:
            try:
                enriched = enricher.enrich(normalized)
                notice_id = enriched.pop("notice_id")
                raw_data_field = enriched.pop("raw_data")
                _, was_created = Opportunity.objects.update_or_create(
                    notice_id=notice_id,
                    defaults={"source": source, "raw_data": raw_data_field, **enriched},
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as exc:
                logger.error(f"Error saving opportunity from {lab_name}: {exc}")

        source.last_scan_status = "success"
        source.save(update_fields=["last_scan_status"])
        total_created += created
        total_updated += updated
        logger.info(f"{lab_name}: {created} new, {updated} updated")

    logger.info(
        f"National labs scan complete: {total_created} new, {total_updated} updated"
    )
    return {"new": total_created, "updated": total_updated}


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
