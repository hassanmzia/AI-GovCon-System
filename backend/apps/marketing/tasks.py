import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_campaign_analysis(self, campaign_id: str):
    """
    Run AI-powered analysis on a marketing campaign: compute ROI projection,
    audience fit score, and suggested optimisations.
    """
    from apps.marketing.models import MarketingCampaign

    try:
        campaign = MarketingCampaign.objects.get(pk=campaign_id)
    except MarketingCampaign.DoesNotExist:
        logger.error("run_campaign_analysis: campaign %s not found", campaign_id)
        return

    logger.info("Analysing campaign %s: %s", campaign_id, campaign.name)

    try:
        import asyncio
        from ai_orchestrator.src.agents.marketing_agent import MarketingAgent

        agent = MarketingAgent()
        result = asyncio.run(
            agent.run({
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "channel": campaign.channel,
                "budget": str(campaign.budget) if campaign.budget else None,
                "goals": campaign.goals,
                "target_audience": campaign.target_audience,
            })
        )

        # Persist the computed metrics back onto the campaign
        updated_metrics = campaign.metrics or {}
        updated_metrics.update({
            "roi_projection": result.get("roi_projection"),
            "audience_fit_score": result.get("audience_fit_score"),
            "suggested_optimisations": result.get("optimisations", []),
            "competitive_landscape": result.get("competitive_landscape", {}),
            "analysis_timestamp": result.get("timestamp"),
        })
        campaign.metrics = updated_metrics
        campaign.save(update_fields=["metrics", "updated_at"])

        logger.info("Campaign %s analysis complete: ROI=%s", campaign_id, result.get("roi_projection"))
        return result

    except Exception as exc:
        logger.error("run_campaign_analysis failed for %s: %s", campaign_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_campaign_digest(self):
    """
    Daily digest: summarise active campaign performance and send notifications
    to campaign owners.
    """
    from apps.core.models import Notification
    from apps.marketing.models import MarketingCampaign

    active_campaigns = MarketingCampaign.objects.filter(status="active").select_related("owner")
    digest_count = 0

    for campaign in active_campaigns:
        if not campaign.owner:
            continue

        roi = (campaign.metrics or {}).get("roi_projection")
        roi_text = f"Projected ROI: {roi}" if roi else "No ROI data yet"

        Notification.objects.get_or_create(
            user=campaign.owner,
            entity_type="marketing_campaign",
            entity_id=str(campaign.id),
            notification_type="info",
            defaults={
                "title": f"Campaign Digest: {campaign.name[:80]}",
                "message": (
                    f"Campaign '{campaign.name}' ({campaign.get_channel_display()}) is active. "
                    f"{roi_text}."
                ),
            },
        )
        digest_count += 1

    logger.info("Campaign digest sent for %d active campaigns", digest_count)
    return {"digest_sent": digest_count}


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def link_campaigns_to_opportunities(self):
    """
    Periodic task: auto-link active campaigns to opportunities that share
    target agencies or NAICS codes.
    """
    from apps.marketing.models import MarketingCampaign
    from apps.opportunities.models import Opportunity

    campaigns = MarketingCampaign.objects.filter(status="active")
    linked = 0

    for campaign in campaigns:
        # Only link to deals if audience contains agency names
        audience = campaign.target_audience.lower()
        if not audience:
            continue

        matching_opps = Opportunity.objects.filter(
            is_active=True,
            agency__icontains=audience[:50],
        )[:10]

        related_deal_ids = list(
            matching_opps.values_list("deal__id", flat=True).distinct()
        )
        if related_deal_ids:
            from apps.deals.models import Deal
            matching_deals = Deal.objects.filter(id__in=related_deal_ids)
            campaign.related_deals.add(*matching_deals)
            linked += matching_deals.count()

    logger.info("link_campaigns_to_opportunities: %d deal links created", linked)
    return {"links_created": linked}
