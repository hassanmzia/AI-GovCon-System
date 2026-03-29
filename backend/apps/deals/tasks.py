import logging
import os
import time
from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Pipeline automation tasks ────────────────────────────────────────────────
# These tasks are auto-triggered by stage_orchestrator.py when a deal
# transitions to the corresponding stage.  They form the "Central Nervous
# System" that connects the deal pipeline to every tool.


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def auto_score_opportunity(self, deal_id: str):
    """Auto-score the opportunity when a deal enters the 'qualify' stage.

    Uses the rule-based OpportunityScorer to generate an OpportunityScore
    record linked to the deal's opportunity.
    """
    from apps.deals.models import Activity, Deal
    from apps.opportunities.models import Opportunity, OpportunityScore

    try:
        deal = Deal.objects.select_related("opportunity").get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("auto_score_opportunity: Deal %s not found", deal_id)
        return

    opportunity = deal.opportunity

    # Skip if already scored
    if hasattr(opportunity, "score"):
        logger.info("Opportunity %s already scored, skipping", opportunity.id)
        return {"status": "already_scored", "score": opportunity.score.total_score}

    try:
        from apps.opportunities.services.scorer import OpportunityScorer
        from apps.opportunities.models import CompanyProfile

        profile = CompanyProfile.objects.first()
        scorer = OpportunityScorer(company_profile=profile)
        result = scorer.score(opportunity)

        score_obj, _ = OpportunityScore.objects.update_or_create(
            opportunity=opportunity,
            defaults={
                "total_score": result["total_score"],
                "recommendation": result["recommendation"],
                "naics_match": result.get("naics_match", 0),
                "psc_match": result.get("psc_match", 0),
                "keyword_overlap": result.get("keyword_overlap", 0),
                "capability_similarity": result.get("capability_similarity", 0),
                "past_performance_relevance": result.get("past_performance_relevance", 0),
                "value_fit": result.get("value_fit", 0),
                "deadline_feasibility": result.get("deadline_feasibility", 0),
                "set_aside_match": result.get("set_aside_match", 0),
                "competition_intensity": result.get("competition_intensity", 0),
                "risk_factors": result.get("risk_factors", 0),
                "score_explanation": result.get("score_explanation", {}),
            },
        )

        # Update deal's fit_score for quick reference
        deal.fit_score = result["total_score"]
        deal.save(update_fields=["fit_score", "updated_at"])

        Activity.objects.create(
            deal=deal,
            actor=None,
            action="opportunity_scored",
            description=(
                f"Opportunity auto-scored: {result['total_score']}/100 "
                f"({result['recommendation']})"
            ),
            metadata={
                "total_score": result["total_score"],
                "recommendation": result["recommendation"],
            },
            is_ai_action=True,
        )

        logger.info(
            "auto_score_opportunity: deal=%s score=%.1f rec=%s",
            deal_id, result["total_score"], result["recommendation"],
        )
        return result

    except Exception as exc:
        logger.error("auto_score_opportunity failed for deal %s: %s", deal_id, exc, exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def auto_run_solution_architect(self, deal_id: str):
    """Auto-trigger the Solution Architect Agent when deal enters proposal_dev.

    Calls the AI Orchestrator, polls for completion, persists results to
    TechnicalSolution + ArchitectureDiagram models, and chains to pricing.
    """
    import httpx
    from apps.deals.models import Activity, Deal

    try:
        deal = Deal.objects.select_related("opportunity").get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("auto_run_solution_architect: Deal %s not found", deal_id)
        return

    # Skip if a solution already exists for this deal
    from apps.proposals.models import TechnicalSolution
    if TechnicalSolution.objects.filter(deal=deal).exists():
        logger.info("TechnicalSolution already exists for deal %s, skipping", deal_id)
        # Still chain to pricing in case it wasn't generated yet
        auto_build_pricing.delay(deal_id)
        return {"status": "already_exists"}

    orchestrator_url = os.getenv("AI_ORCHESTRATOR_URL", "http://ai-orchestrator:8003")

    try:
        client = httpx.Client(timeout=30)

        # Start the agent run
        start_resp = client.post(
            f"{orchestrator_url}/ai/agents/solution-architect/run",
            json={
                "deal_id": str(deal.id),
                "opportunity_id": str(deal.opportunity_id),
            },
        )
        start_resp.raise_for_status()
        run_id = start_resp.json()["run_id"]

        # Poll for completion (max 180s)
        max_wait, poll_interval, elapsed = 180, 3, 0
        result = None

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            poll_resp = client.get(f"{orchestrator_url}/ai/agents/runs/{run_id}")
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()

            if poll_data["status"] == "completed":
                result = poll_data.get("result", {})
                break
            elif poll_data["status"] == "failed":
                error_msg = poll_data.get("result", {}).get("error", "Agent failed")
                logger.error("Solution Architect failed for deal %s: %s", deal_id, error_msg)
                Activity.objects.create(
                    deal=deal, actor=None, action="solution_architect_failed",
                    description=f"Solution Architect Agent failed: {error_msg[:200]}",
                    is_ai_action=True,
                )
                return {"status": "failed", "error": error_msg}

        client.close()

        if result is None:
            logger.warning("Solution Architect timed out for deal %s", deal_id)
            return {"status": "timeout"}

        # Persist the solution
        _persist_solution_result(deal, result)

        Activity.objects.create(
            deal=deal, actor=None, action="solution_architect_completed",
            description="Solution Architect Agent completed — technical solution generated",
            metadata={"iteration_count": result.get("iteration_count", 1)},
            is_ai_action=True,
        )

        logger.info("auto_run_solution_architect: completed for deal %s", deal_id)

        # Chain: auto-build pricing after solution is ready
        auto_build_pricing.delay(deal_id)

        return {"status": "completed"}

    except Exception as exc:
        logger.error("auto_run_solution_architect failed for deal %s: %s", deal_id, exc, exc_info=True)
        raise self.retry(exc=exc)


def _persist_solution_result(deal, result):
    """Persist Solution Architect result to Django models."""
    from apps.proposals.models import (
        ArchitectureDiagram,
        Proposal,
        ProposalSection,
        SolutionValidationReport,
        TechnicalSolution,
    )

    ts_data = result.get("technical_solution", {})
    ts, _ = TechnicalSolution.objects.update_or_create(
        deal=deal,
        defaults={
            "iteration_count": result.get("iteration_count", 1),
            "selected_frameworks": result.get("selected_frameworks", []),
            "requirement_analysis": result.get("requirement_analysis", {}),
            "executive_summary": ts_data.get("executive_summary", ""),
            "architecture_pattern": ts_data.get("architecture_pattern", ""),
            "core_components": ts_data.get("core_components", []),
            "technology_stack": ts_data.get("technology_stack", {}),
            "integration_points": ts_data.get("integration_points", []),
            "scalability_approach": ts_data.get("scalability_approach", ""),
            "security_architecture": ts_data.get("security_architecture", ""),
            "deployment_model": ts_data.get("deployment_model", ""),
            "technical_volume": result.get("technical_volume", {}).get("sections", {}),
        },
    )

    # Persist diagrams
    ArchitectureDiagram.objects.filter(technical_solution=ts).delete()
    for diag in result.get("diagrams", []):
        ArchitectureDiagram.objects.create(
            technical_solution=ts,
            title=diag.get("title", "Diagram"),
            diagram_type=diag.get("type", "system_context"),
            mermaid_code=diag.get("mermaid", ""),
            description=diag.get("description", ""),
        )

    # Persist validation report
    vr = result.get("validation_report", {})
    if vr:
        SolutionValidationReport.objects.update_or_create(
            technical_solution=ts,
            defaults={
                "overall_quality": vr.get("overall_quality", "fair"),
                "score": vr.get("score"),
                "passed": vr.get("pass", False),
                "issues": vr.get("issues", []),
                "suggestions": vr.get("suggestions", []),
                "compliance_gaps": vr.get("compliance_gaps", []),
            },
        )

    # Populate proposal sections from technical volume
    proposal = Proposal.objects.filter(deal=deal).first()
    if proposal and ts.technical_volume:
        for i, (title, content) in enumerate(ts.technical_volume.items()):
            ProposalSection.objects.update_or_create(
                proposal=proposal,
                volume="Volume I - Technical",
                title=title,
                defaults={
                    "section_number": f"1.{i + 1}",
                    "order": i,
                    "ai_draft": content,
                    "status": "ai_drafted",
                },
            )


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def auto_build_pricing(self, deal_id: str):
    """Auto-generate LOE estimate, cost model, and pricing scenarios for a deal.

    This is chained after the Solution Architect completes, using the
    TechnicalSolution's technology_stack and core_components to derive
    a labor estimate, then building a cost model and generating all 7
    pricing scenarios.
    """
    from apps.deals.models import Activity, Deal
    from apps.pricing.models import CostModel, LOEEstimate, RateCard
    from apps.proposals.models import TechnicalSolution

    try:
        deal = Deal.objects.select_related("opportunity").get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("auto_build_pricing: Deal %s not found", deal_id)
        return

    # Skip if pricing scenarios already exist
    if deal.pricing_scenarios.exists():
        logger.info("Pricing scenarios already exist for deal %s, skipping", deal_id)
        # Still chain to proposal population
        auto_populate_proposal.delay(deal_id)
        return {"status": "already_exists"}

    try:
        solution = TechnicalSolution.objects.filter(deal=deal).first()

        # ── Build LOE estimate from solution components ─────────────────
        wbs_elements = []
        total_hours = 0

        if solution and solution.core_components:
            components = solution.core_components
            if isinstance(components, list):
                for i, comp in enumerate(components):
                    comp_name = comp if isinstance(comp, str) else comp.get("name", f"Component {i+1}")
                    hours = 320  # ~2 months per component (default)
                    wbs_elements.append({
                        "wbs_id": f"1.{i+1}",
                        "name": comp_name,
                        "labor_category": "Software Engineer",
                        "hours_optimistic": int(hours * 0.7),
                        "hours_likely": hours,
                        "hours_pessimistic": int(hours * 1.5),
                        "hours_estimated": hours,
                    })
                    total_hours += hours

        # Add standard GovCon overhead tasks
        standard_tasks = [
            ("Project Management", "Program Manager", 240),
            ("Quality Assurance", "QA Analyst", 160),
            ("Security & Compliance", "Security Engineer", 120),
            ("Documentation & Training", "Technical Writer", 80),
        ]
        for name, category, hours in standard_tasks:
            wbs_elements.append({
                "wbs_id": f"2.{len(wbs_elements)+1}",
                "name": name,
                "labor_category": category,
                "hours_optimistic": int(hours * 0.7),
                "hours_likely": hours,
                "hours_pessimistic": int(hours * 1.5),
                "hours_estimated": hours,
            })
            total_hours += hours

        # If no solution components, create a minimal estimate
        if not wbs_elements:
            wbs_elements = [
                {"wbs_id": "1.1", "name": "Technical Implementation", "labor_category": "Software Engineer",
                 "hours_estimated": 1000},
                {"wbs_id": "1.2", "name": "Project Management", "labor_category": "Program Manager",
                 "hours_estimated": 240},
            ]
            total_hours = 1240

        loe = LOEEstimate.objects.create(
            deal=deal,
            wbs_elements=wbs_elements,
            total_hours=total_hours,
            total_ftes=round(total_hours / 2080, 1),  # 2080 hours/year
            duration_months=12,
            estimation_method="wbs_bottom_up" if solution else "analogous",
            confidence_level=0.7 if solution else 0.5,
        )

        # ── Build cost model from LOE + rate cards ──────────────────────
        labor_detail = []
        direct_labor = Decimal("0")

        for elem in wbs_elements:
            category = elem.get("labor_category", "Software Engineer")
            hours = elem.get("hours_estimated", 0)

            # Look up rate card; fall back to reasonable default
            rate_card = RateCard.objects.filter(
                labor_category__icontains=category, is_active=True
            ).first()
            rate = rate_card.internal_rate if rate_card else Decimal("125.00")

            line_total = rate * hours
            direct_labor += line_total
            labor_detail.append({
                "category": category,
                "hours": hours,
                "rate": str(rate),
                "total": str(line_total),
            })

        fringe_rate, overhead_rate, ga_rate = 0.30, 0.40, 0.10
        fringe = direct_labor * Decimal(str(fringe_rate))
        overhead = (direct_labor + fringe) * Decimal(str(overhead_rate))
        subtotal = direct_labor + fringe + overhead
        ga = subtotal * Decimal(str(ga_rate))
        total_cost = subtotal + ga

        cost_model = CostModel.objects.create(
            deal=deal,
            loe=loe,
            direct_labor=direct_labor,
            fringe_benefits=fringe,
            overhead=overhead,
            ga_expense=ga,
            total_cost=total_cost,
            fringe_rate=fringe_rate,
            overhead_rate=overhead_rate,
            ga_rate=ga_rate,
            labor_detail=labor_detail,
        )

        # ── Generate pricing scenarios ──────────────────────────────────
        from apps.pricing.services.scenario_engine import generate_scenarios
        scenarios = generate_scenarios(str(cost_model.id))

        Activity.objects.create(
            deal=deal, actor=None, action="pricing_auto_generated",
            description=(
                f"Pricing auto-generated: LOE {total_hours}h, "
                f"cost ${total_cost:,.0f}, {len(scenarios)} scenarios"
            ),
            metadata={
                "loe_id": str(loe.id),
                "cost_model_id": str(cost_model.id),
                "total_hours": total_hours,
                "total_cost": str(total_cost),
                "scenarios_count": len(scenarios),
            },
            is_ai_action=True,
        )

        logger.info(
            "auto_build_pricing: deal=%s hours=%d cost=$%s scenarios=%d",
            deal_id, total_hours, total_cost, len(scenarios),
        )

        # Chain: populate proposal with pricing volume
        auto_populate_proposal.delay(deal_id)

        return {
            "status": "completed",
            "total_hours": total_hours,
            "total_cost": str(total_cost),
            "scenarios": len(scenarios),
        }

    except Exception as exc:
        logger.error("auto_build_pricing failed for deal %s: %s", deal_id, exc, exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def auto_populate_proposal(self, deal_id: str):
    """Auto-populate Proposal sections and PricingVolume from solution + pricing.

    Creates Volume I (Technical) sections from TechnicalSolution,
    Volume III (Pricing) sections from the recommended PricingScenario,
    and links everything via PricingVolume.
    """
    from apps.deals.models import Activity, Deal
    from apps.pricing.models import CostModel, PricingScenario, PricingVolume
    from apps.proposals.models import Proposal, ProposalSection, TechnicalSolution

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        return

    proposal = Proposal.objects.filter(deal=deal).first()
    if not proposal:
        logger.info("No proposal for deal %s, skipping populate", deal_id)
        return

    sections_created = 0

    # ── Volume I: Technical (from TechnicalSolution) ────────────────────
    solution = TechnicalSolution.objects.filter(deal=deal).first()
    if solution and solution.technical_volume:
        for i, (title, content) in enumerate(solution.technical_volume.items()):
            _, created = ProposalSection.objects.update_or_create(
                proposal=proposal,
                volume="Volume I - Technical",
                title=title,
                defaults={
                    "section_number": f"1.{i + 1}",
                    "order": i,
                    "ai_draft": content,
                    "status": "ai_drafted",
                },
            )
            if created:
                sections_created += 1

    # ── Volume III: Pricing (from recommended scenario) ─────────────────
    recommended = PricingScenario.objects.filter(
        deal=deal, is_recommended=True
    ).first()
    cost_model = CostModel.objects.filter(deal=deal).order_by("-version").first()

    if recommended and cost_model:
        pricing_sections = [
            ("Pricing Overview", (
                f"Strategy: {recommended.name}\n"
                f"Total Price: ${recommended.total_price:,.2f}\n"
                f"Profit Margin: {recommended.margin_pct:.1%}\n"
                f"Win Probability: {recommended.probability_of_win:.1%}\n"
                f"Expected Value: ${recommended.expected_value:,.2f}\n\n"
                f"{recommended.rationale}"
            )),
            ("Cost Breakdown", (
                f"Direct Labor: ${cost_model.direct_labor:,.2f}\n"
                f"Fringe Benefits ({cost_model.fringe_rate:.0%}): ${cost_model.fringe_benefits:,.2f}\n"
                f"Overhead ({cost_model.overhead_rate:.0%}): ${cost_model.overhead:,.2f}\n"
                f"G&A ({cost_model.ga_rate:.0%}): ${cost_model.ga_expense:,.2f}\n"
                f"Other Direct Costs: ${cost_model.odcs:,.2f}\n"
                f"Subcontractors: ${cost_model.subcontractor_costs:,.2f}\n"
                f"Travel: ${cost_model.travel:,.2f}\n"
                f"Materials: ${cost_model.materials:,.2f}\n"
                f"───────────────\n"
                f"Total Cost: ${cost_model.total_cost:,.2f}\n"
                f"Profit: ${recommended.profit:,.2f}\n"
                f"Total Price: ${recommended.total_price:,.2f}"
            )),
            ("Labor Rate Summary", _format_labor_detail(cost_model.labor_detail)),
        ]

        for i, (title, content) in enumerate(pricing_sections):
            _, created = ProposalSection.objects.update_or_create(
                proposal=proposal,
                volume="Volume III - Pricing",
                title=title,
                defaults={
                    "section_number": f"3.{i + 1}",
                    "order": 100 + i,  # After technical sections
                    "ai_draft": content,
                    "status": "ai_drafted",
                },
            )
            if created:
                sections_created += 1

        # ── Create PricingVolume link ───────────────────────────────────
        PricingVolume.objects.update_or_create(
            deal=deal,
            proposal=proposal,
            defaults={
                "selected_scenario": recommended,
                "total_price": recommended.total_price,
                "labor_cost": cost_model.direct_labor,
                "odc_cost": cost_model.odcs,
                "profit_margin": recommended.margin_pct,
                "status": "draft",
            },
        )

    if sections_created:
        Activity.objects.create(
            deal=deal, actor=None, action="proposal_sections_populated",
            description=f"{sections_created} proposal section(s) auto-populated from solution & pricing",
            metadata={"sections_created": sections_created},
            is_ai_action=True,
        )

    logger.info("auto_populate_proposal: deal=%s sections=%d", deal_id, sections_created)
    return {"sections_created": sections_created}


def _format_labor_detail(labor_detail):
    """Format labor_detail JSON into readable table."""
    if not labor_detail:
        return "No labor detail available."
    lines = ["Category | Hours | Rate | Total", "--- | --- | --- | ---"]
    for item in labor_detail:
        lines.append(
            f"{item.get('category', 'N/A')} | "
            f"{item.get('hours', 0)} | "
            f"${item.get('rate', '0')} | "
            f"${item.get('total', '0')}"
        )
    return "\n".join(lines)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def auto_generate_stage_tasks(self, deal_id: str, stage: str):
    """
    When a deal enters a new stage, create tasks from the matching
    TaskTemplate records.

    Called automatically by ``WorkflowEngine.transition()`` and can also
    be triggered manually via the Celery CLI or Django admin.
    """
    from apps.deals.models import Activity, Deal, Task, TaskTemplate

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("auto_generate_stage_tasks: Deal %s not found", deal_id)
        return

    templates = TaskTemplate.objects.filter(stage=stage).order_by("order")
    if not templates.exists():
        logger.info(
            "No task templates for stage '%s' (deal %s). Skipping.", stage, deal_id
        )
        return

    now = timezone.now()
    created_tasks = []

    for tmpl in templates:
        due = now + timedelta(days=tmpl.days_until_due) if tmpl.days_until_due else None
        task = Task.objects.create(
            deal=deal,
            title=tmpl.title,
            description=tmpl.description,
            priority=tmpl.default_priority,
            due_date=due,
            stage=stage,
            is_ai_generated=True,
            is_auto_completable=tmpl.is_auto_completable,
        )
        created_tasks.append(task)

    Activity.objects.create(
        deal=deal,
        actor=None,
        action="tasks_auto_generated",
        description=(
            f"{len(created_tasks)} task(s) auto-generated for stage '{stage}'"
        ),
        metadata={
            "stage": stage,
            "task_ids": [str(t.id) for t in created_tasks],
        },
        is_ai_action=True,
    )

    logger.info(
        "auto_generate_stage_tasks: Created %d tasks for deal %s in stage '%s'",
        len(created_tasks),
        deal_id,
        stage,
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def check_overdue_tasks(self):
    """
    Periodic task that flags overdue tasks and creates notifications
    for task assignees and deal owners.

    Should be scheduled via Celery Beat (e.g. every hour or once daily).
    """
    from apps.core.models import Notification
    from apps.deals.models import Activity, Task

    now = timezone.now()

    overdue_tasks = (
        Task.objects.filter(
            due_date__lt=now,
            status__in=["pending", "in_progress"],
        )
        .select_related("deal", "assigned_to", "deal__owner")
    )

    if not overdue_tasks.exists():
        logger.info("check_overdue_tasks: No overdue tasks found.")
        return

    flagged_count = 0

    for task in overdue_tasks:
        overdue_delta = now - task.due_date
        overdue_hours = overdue_delta.total_seconds() / 3600

        # Notify the assignee (if set)
        recipients = set()
        if task.assigned_to:
            recipients.add(task.assigned_to)
        if task.deal.owner:
            recipients.add(task.deal.owner)

        for user in recipients:
            Notification.objects.get_or_create(
                user=user,
                entity_type="task",
                entity_id=str(task.id),
                notification_type="warning",
                defaults={
                    "title": f"Overdue Task: {task.title[:100]}",
                    "message": (
                        f"Task '{task.title}' on deal '{task.deal.title}' "
                        f"is overdue by {overdue_hours:.0f} hours. "
                        f"Due date was {task.due_date.strftime('%Y-%m-%d %H:%M')}."
                    ),
                },
            )

        # Log the overdue activity on the deal (once per check cycle)
        Activity.objects.create(
            deal=task.deal,
            actor=None,
            action="task_overdue",
            description=(
                f"Task '{task.title}' is overdue by {overdue_hours:.0f} hours"
            ),
            metadata={
                "task_id": str(task.id),
                "due_date": task.due_date.isoformat(),
                "overdue_hours": round(overdue_hours, 1),
            },
            is_ai_action=True,
        )

        flagged_count += 1

    logger.info(
        "check_overdue_tasks: Flagged %d overdue task(s) and sent notifications.",
        flagged_count,
    )
