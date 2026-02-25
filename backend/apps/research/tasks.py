import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def run_research_project(self, project_id: str):
    """
    Execute a research project asynchronously.

    Gathers data from web sources, analyzes findings, and updates the
    ResearchProject with results. Called when a user starts a research
    project via the API.

    Args:
        project_id: UUID string of the ResearchProject to execute.
    """
    from apps.research.models import ResearchProject

    try:
        project = ResearchProject.objects.select_related("deal").get(
            pk=project_id
        )
    except ResearchProject.DoesNotExist:
        logger.error(
            "run_research_project: Project %s not found", project_id
        )
        return

    logger.info(
        "run_research_project: Starting research for project '%s' (type=%s)",
        project.title,
        project.research_type,
    )

    try:
        import asyncio
        from apps.research.services.web_researcher import WebResearcher

        project.status = "in_progress"
        project.save(update_fields=["status", "updated_at"])

        researcher = WebResearcher()
        params = project.parameters or {}
        deal = project.deal

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if project.research_type == "agency_analysis":
                agency_name = (
                    params.get("agency_name")
                    or (deal.opportunity.agency if deal.opportunity else "")
                    or deal.title
                )
                result = loop.run_until_complete(
                    researcher.analyze_agency(agency_name)
                )
            elif project.research_type == "competitive_intel":
                competitor = params.get("competitor_name", "")
                if competitor:
                    result = loop.run_until_complete(
                        researcher.analyze_competitor(competitor)
                    )
                else:
                    result = loop.run_until_complete(
                        researcher.search_web(
                            f"competitors government contracting {deal.title}"
                        )
                    )
            elif project.research_type in ("market_analysis", "technology_trends"):
                naics = params.get("naics_codes") or (
                    [deal.opportunity.naics_code]
                    if deal.opportunity and deal.opportunity.naics_code
                    else []
                )
                agencies = params.get("agencies") or (
                    [deal.opportunity.agency]
                    if deal.opportunity and deal.opportunity.agency
                    else []
                )
                result = loop.run_until_complete(
                    researcher.research_market_trends(naics, agencies)
                )
            elif project.research_type == "incumbent_analysis":
                query = params.get("query") or f"incumbent contractor {deal.title}"
                result = loop.run_until_complete(researcher.search_web(query))
            else:
                query = params.get("query") or project.title
                result = loop.run_until_complete(researcher.search_web(query))
        finally:
            loop.close()

        project.findings = {
            "status": "completed",
            "research_type": project.research_type,
            **result,
        }
        project.executive_summary = (
            result.get("executive_summary")
            or (result.get("overview") or {}).get("mission", "")
            or result.get("analysis", "")
            or f"Research completed for '{project.title}'."
        )
        project.sources = result.get("sources", [])
        project.status = "completed"
        project.save(
            update_fields=[
                "findings",
                "executive_summary",
                "sources",
                "status",
                "updated_at",
            ]
        )

        logger.info(
            "run_research_project: Project %s completed successfully",
            project_id,
        )

    except Exception as exc:
        logger.exception(
            "run_research_project: Project %s failed with error: %s",
            project_id,
            exc,
        )
        project.status = "failed"
        project.findings = {
            "status": "failed",
            "error": str(exc),
        }
        project.save(update_fields=["status", "findings", "updated_at"])

        # Retry on transient failures
        raise self.retry(exc=exc)
