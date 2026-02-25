import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


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
