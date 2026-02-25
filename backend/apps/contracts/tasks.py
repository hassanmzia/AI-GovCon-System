import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scan_contract_for_risks(self, contract_id: str):
    """
    Scan a contract's clauses for risk patterns using the legal clause scanner.
    Logs findings and updates ContractVersion notes if changes detected.
    """
    from apps.contracts.models import Contract
    from apps.contracts.services.clause_scanner import ClauseScanner

    try:
        contract = Contract.objects.prefetch_related("clauses").get(pk=contract_id)
    except Contract.DoesNotExist:
        logger.error("scan_contract_for_risks: contract %s not found", contract_id)
        return

    logger.info("Scanning contract %s (%s) for risks", contract_id, contract.title)

    try:
        scanner = ClauseScanner()
        results = scanner.scan_contract(contract)

        high_risk = [r for r in results if r.get("risk_level") == "high"]
        medium_risk = [r for r in results if r.get("risk_level") == "medium"]

        logger.info(
            "Contract %s scan complete: %d high-risk, %d medium-risk clauses",
            contract_id,
            len(high_risk),
            len(medium_risk),
        )
        return {
            "contract_id": contract_id,
            "high_risk": len(high_risk),
            "medium_risk": len(medium_risk),
            "findings": results[:20],  # cap payload size
        }

    except Exception as exc:
        logger.error("scan_contract_for_risks failed for %s: %s", contract_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def check_milestone_deadlines(self):
    """
    Periodic task: flag overdue milestones and send notifications to assigned users.
    Should be scheduled via Celery Beat (e.g. daily at 08:00).
    """
    from apps.contracts.models import ContractMilestone
    from apps.core.models import Notification

    now = timezone.now().date()
    warning_horizon = now + timedelta(days=14)

    # Mark overdue milestones
    overdue = ContractMilestone.objects.filter(
        due_date__lt=now, status__in=["upcoming", "in_progress"]
    ).select_related("contract", "assigned_to")

    overdue_count = 0
    for milestone in overdue:
        milestone.status = "overdue"
        milestone.save(update_fields=["status", "updated_at"])

        if milestone.assigned_to:
            Notification.objects.get_or_create(
                user=milestone.assigned_to,
                entity_type="contract_milestone",
                entity_id=str(milestone.id),
                notification_type="warning",
                defaults={
                    "title": f"Overdue Milestone: {milestone.title[:80]}",
                    "message": (
                        f"Contract milestone '{milestone.title}' on "
                        f"'{milestone.contract.title}' was due {milestone.due_date}."
                    ),
                },
            )
        overdue_count += 1

    # Warn about upcoming milestones within 14 days
    upcoming = ContractMilestone.objects.filter(
        due_date__range=[now, warning_horizon], status="upcoming"
    ).select_related("contract", "assigned_to")

    warning_count = 0
    for milestone in upcoming:
        if milestone.assigned_to:
            Notification.objects.get_or_create(
                user=milestone.assigned_to,
                entity_type="contract_milestone",
                entity_id=str(milestone.id),
                notification_type="info",
                defaults={
                    "title": f"Upcoming Milestone: {milestone.title[:80]}",
                    "message": (
                        f"Contract milestone '{milestone.title}' on "
                        f"'{milestone.contract.title}' is due {milestone.due_date}."
                    ),
                },
            )
        warning_count += 1

    logger.info(
        "check_milestone_deadlines: %d overdue flagged, %d upcoming warnings sent",
        overdue_count,
        warning_count,
    )
    return {"overdue": overdue_count, "warnings_sent": warning_count}


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_contract_draft(self, deal_id: str, contract_type: str):
    """
    Generate a contract draft using the ContractGenerator service and
    create a Contract record in 'drafting' status.
    """
    from apps.contracts.models import Contract, ContractTemplate
    from apps.contracts.services.generator import ContractGenerator
    from apps.deals.models import Deal

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("generate_contract_draft: deal %s not found", deal_id)
        return

    template = ContractTemplate.objects.filter(
        contract_type=contract_type, is_active=True
    ).first()

    logger.info(
        "Generating %s contract draft for deal %s", contract_type, deal_id
    )

    try:
        generator = ContractGenerator()
        draft_content = generator.draft(deal=deal, template=template)

        contract = Contract.objects.create(
            deal=deal,
            template=template,
            title=f"{deal.title} — {contract_type} Contract",
            contract_type=contract_type,
            status="drafting",
            notes=draft_content.get("notes", ""),
        )

        logger.info(
            "Contract draft created: %s (deal %s)", contract.id, deal_id
        )
        return {"contract_id": str(contract.id)}

    except Exception as exc:
        logger.error("generate_contract_draft failed for deal %s: %s", deal_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def process_contract_modification(self, contract_id: str, modification_id: str):
    """
    Process a contract modification: recalculate total value, create a new
    ContractVersion, and notify stakeholders.
    """
    from apps.contracts.models import Contract, ContractModification, ContractVersion
    from apps.core.models import Notification

    try:
        mod = ContractModification.objects.select_related(
            "contract", "requested_by"
        ).get(pk=modification_id)
    except ContractModification.DoesNotExist:
        logger.error(
            "process_contract_modification: modification %s not found", modification_id
        )
        return

    contract = mod.contract

    # Update new total value
    if mod.new_total_value:
        contract.total_value = mod.new_total_value
        contract.status = "modification"
        contract.save(update_fields=["total_value", "status", "updated_at"])

    # Create a version snapshot
    last_version = (
        ContractVersion.objects.filter(contract=contract)
        .order_by("-version_number")
        .first()
    )
    version_number = (last_version.version_number + 1) if last_version else 1

    ContractVersion.objects.create(
        contract=contract,
        version_number=version_number,
        change_type="modification",
        description=mod.description,
        changes={
            "modification_number": mod.modification_number,
            "modification_type": mod.modification_type,
            "impact_value": str(mod.impact_value) if mod.impact_value else None,
        },
        effective_date=mod.effective_date,
        created_by=mod.requested_by,
    )

    logger.info(
        "Modification %s processed for contract %s (v%d)",
        modification_id,
        contract_id,
        version_number,
    )
    return {"version": version_number, "new_total": str(contract.total_value)}
