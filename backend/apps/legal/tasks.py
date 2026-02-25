import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_compliance_assessment(self, deal_id: str, user_id: str = None):
    """Run a full FAR/DFARS compliance assessment for a deal.

    Creates a ComplianceAssessment record, invokes the FARAnalyzer service
    to check compliance, and updates the assessment with findings.

    Args:
        deal_id: UUID of the Deal to assess.
        user_id: Optional UUID of the User performing the assessment.
    """
    from apps.deals.models import Deal
    from apps.legal.models import ComplianceAssessment
    from apps.legal.services.far_analyzer import FARAnalyzer

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("run_compliance_assessment: Deal %s not found.", deal_id)
        return

    assessed_by = None
    if user_id:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            assessed_by = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.warning(
                "run_compliance_assessment: User %s not found. Proceeding without assessor.",
                user_id,
            )

    assessment = ComplianceAssessment.objects.create(
        deal=deal,
        assessed_by=assessed_by,
        status="in_progress",
    )

    try:
        analyzer = FARAnalyzer()
        result = analyzer.check_compliance(deal_id)

        assessment.far_compliance_score = result.get("far_compliance_score", 0.0)
        assessment.dfars_compliance_score = result.get("dfars_compliance_score", 0.0)
        assessment.overall_risk_level = result.get("overall_risk_level", "low")
        assessment.findings = result.get("findings", [])
        assessment.recommendations = result.get("recommendations", [])
        assessment.non_compliant_items = result.get("non_compliant_items", [])
        assessment.status = "completed"
        assessment.save()

        logger.info(
            "run_compliance_assessment: Completed assessment %s for deal %s. "
            "FAR score: %.1f, DFARS score: %.1f, risk level: %s",
            assessment.id,
            deal_id,
            assessment.far_compliance_score,
            assessment.dfars_compliance_score,
            assessment.overall_risk_level,
        )

    except Exception as exc:
        logger.exception(
            "run_compliance_assessment: Failed for deal %s: %s", deal_id, exc
        )
        assessment.status = "pending"
        assessment.findings = [{"error": str(exc)}]
        assessment.save()
        raise self.retry(exc=exc)
