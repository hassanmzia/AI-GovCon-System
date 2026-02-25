import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_control_mapping(self, deal_id: str, framework_id: str = None):
    """
    Map RFP/deal compliance requirements to security controls for a deal.
    If framework_id is provided, maps to that framework only; otherwise maps
    to all active frameworks.
    """
    from apps.deals.models import Deal
    from apps.security_compliance.models import (
        ComplianceRequirement,
        SecurityControl,
        SecurityControlMapping,
        SecurityFramework,
    )
    from apps.security_compliance.services.control_mapper import ControlMapper

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("run_control_mapping: deal %s not found", deal_id)
        return

    if framework_id:
        frameworks = SecurityFramework.objects.filter(pk=framework_id, is_active=True)
    else:
        frameworks = SecurityFramework.objects.filter(is_active=True)

    requirements = ComplianceRequirement.objects.filter(deal=deal)

    mapper = ControlMapper()
    total_mappings = 0

    for framework in frameworks:
        controls = SecurityControl.objects.filter(framework=framework)
        for req in requirements:
            mapped_controls = mapper.map_requirement_to_controls(
                requirement_text=req.requirement_text,
                framework=framework.name,
            )
            for control_id in mapped_controls:
                try:
                    control = controls.get(control_id=control_id)
                    SecurityControlMapping.objects.get_or_create(
                        deal=deal,
                        control=control,
                        defaults={"implementation_status": "planned"},
                    )
                    total_mappings += 1
                except SecurityControl.DoesNotExist:
                    pass

    logger.info(
        "Control mapping for deal %s: %d mappings created across %d frameworks",
        deal_id,
        total_mappings,
        frameworks.count(),
    )
    return {"deal_id": deal_id, "mappings_created": total_mappings}


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_compliance_report(self, deal_id: str, framework_id: str, report_type: str = "gap_analysis"):
    """
    Generate a SecurityComplianceReport for a deal against a framework.
    report_type: gap_analysis | readiness_assessment | poam | ssp_section
    """
    from apps.deals.models import Deal
    from apps.security_compliance.models import (
        SecurityControlMapping,
        SecurityComplianceReport,
        SecurityFramework,
    )
    from apps.security_compliance.services.gap_analyzer import analyze_compliance_gaps

    try:
        deal = Deal.objects.get(pk=deal_id)
        framework = SecurityFramework.objects.get(pk=framework_id)
    except (Deal.DoesNotExist, SecurityFramework.DoesNotExist) as exc:
        logger.error("generate_compliance_report: %s", exc)
        return

    mappings = SecurityControlMapping.objects.filter(
        deal=deal, control__framework=framework
    ).select_related("control")

    total = mappings.count()
    implemented = mappings.filter(implementation_status="implemented").count()
    partial = mappings.filter(implementation_status="partial").count()
    planned = mappings.filter(implementation_status="planned").count()
    na = mappings.filter(implementation_status="not_applicable").count()

    gaps = [
        {
            "control_id": m.control.control_id,
            "title": m.control.title,
            "gap": m.gap_description,
            "remediation": m.remediation_plan,
        }
        for m in mappings.filter(implementation_status__in=["planned", "partial"])
        if m.gap_description
    ]

    pct = round((implemented / total) * 100, 1) if total else 0.0

    report, created = SecurityComplianceReport.objects.update_or_create(
        deal=deal,
        framework=framework,
        report_type=report_type,
        defaults={
            "status": "draft",
            "overall_compliance_pct": pct,
            "controls_implemented": implemented,
            "controls_partial": partial,
            "controls_planned": planned,
            "controls_na": na,
            "gaps": gaps,
            "generated_by": "AI Compliance Agent",
        },
    )

    logger.info(
        "Compliance report (%s) for deal %s / %s: %.1f%% compliant",
        report_type,
        deal_id,
        framework.name,
        pct,
    )
    return {
        "report_id": str(report.id),
        "compliance_pct": pct,
        "gaps": len(gaps),
        "created": created,
    }


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def validate_evidence_references(self, deal_id: str):
    """
    Review all evidence_references fields across SecurityControlMappings for
    a deal and flag any that are broken/empty for controls claiming to be
    'implemented'.
    """
    from apps.security_compliance.models import SecurityControlMapping

    mappings = SecurityControlMapping.objects.filter(
        deal_id=deal_id, implementation_status="implemented"
    )

    flagged = []
    for mapping in mappings:
        if not mapping.evidence_references:
            flagged.append({
                "control_id": mapping.control.control_id,
                "mapping_id": str(mapping.id),
                "issue": "Claimed 'implemented' but has no evidence references",
            })

    logger.info(
        "Evidence validation for deal %s: %d controls flagged", deal_id, len(flagged)
    )
    return {"deal_id": deal_id, "flagged": flagged}


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_poam(self, deal_id: str, framework_id: str):
    """
    Generate a Plan of Action & Milestones (POA&M) for a deal by identifying
    all gaps and building a remediation timeline.
    """
    from apps.security_compliance.models import (
        SecurityControlMapping,
        SecurityComplianceReport,
        SecurityFramework,
    )

    try:
        framework = SecurityFramework.objects.get(pk=framework_id)
    except SecurityFramework.DoesNotExist:
        logger.error("generate_poam: framework %s not found", framework_id)
        return

    gap_mappings = SecurityControlMapping.objects.filter(
        deal_id=deal_id,
        control__framework=framework,
        implementation_status__in=["planned", "partial"],
    ).select_related("control")

    poam_items = []
    for i, mapping in enumerate(gap_mappings, 1):
        poam_items.append({
            "item_id": f"POA&M-{i:03d}",
            "control_id": mapping.control.control_id,
            "weakness": mapping.gap_description or "Gap identified",
            "remediation": mapping.remediation_plan or "Remediation plan required",
            "responsible_party": mapping.responsible_party or "TBD",
            "target_completion": (
                mapping.target_completion.isoformat()
                if mapping.target_completion
                else "TBD"
            ),
            "status": mapping.implementation_status,
        })

    # Persist as a compliance report of type poam
    SecurityComplianceReport.objects.update_or_create(
        deal_id=deal_id,
        framework=framework,
        report_type="poam",
        defaults={
            "status": "draft",
            "poam_items": poam_items,
            "generated_by": "AI Compliance Agent",
        },
    )

    logger.info(
        "POA&M generated for deal %s / %s: %d items", deal_id, framework.name, len(poam_items)
    )
    return {"deal_id": deal_id, "poam_items": len(poam_items)}
