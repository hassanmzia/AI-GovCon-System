import logging
from typing import Any

logger = logging.getLogger(__name__)


class ComplianceMapper:
    """Maps deal requirements to security framework controls and performs
    gap analysis and POAM generation."""

    def map_requirements(
        self, deal_id: str, framework_id: str
    ) -> dict[str, Any]:
        """Auto-map deal compliance requirements to security controls.

        Analyses the deal's characteristics and associated requirements,
        then creates SecurityControlMapping records for every applicable
        control in the specified framework.

        Args:
            deal_id: UUID of the deal to map.
            framework_id: UUID of the SecurityFramework to map against.

        Returns:
            A dict summarising the mapping results including counts of
            controls mapped, gaps identified, and a list of mapping ids.
        """
        # TODO: Implement full mapping logic:
        #   1. Load the deal and its compliance requirements.
        #   2. Load all controls for the given framework.
        #   3. Use NLP / keyword matching to associate requirements
        #      with the most relevant controls.
        #   4. Create SecurityControlMapping records for each match.
        #   5. Return summary statistics.

        from apps.deals.models import Deal
        from apps.security_compliance.models import (
            SecurityControlMapping,
            SecurityFramework,
        )

        try:
            deal = Deal.objects.get(pk=deal_id)
            framework = SecurityFramework.objects.get(pk=framework_id)
        except (Deal.DoesNotExist, SecurityFramework.DoesNotExist) as exc:
            logger.error("map_requirements: %s", exc)
            return {"error": str(exc)}

        controls = framework.controls.all()
        mappings_created = []

        for control in controls:
            mapping, created = SecurityControlMapping.objects.get_or_create(
                deal=deal,
                control=control,
                defaults={
                    "implementation_status": "planned",
                },
            )
            if created:
                mappings_created.append(str(mapping.id))

        logger.info(
            "map_requirements: Created %d mappings for deal %s against %s",
            len(mappings_created),
            deal_id,
            framework.name,
        )

        return {
            "deal_id": str(deal_id),
            "framework_id": str(framework_id),
            "framework_name": framework.name,
            "total_controls": controls.count(),
            "mappings_created": len(mappings_created),
            "mapping_ids": mappings_created,
        }

    def assess_gaps(self, deal_id: str) -> dict[str, Any]:
        """Produce a gap analysis for all mapped controls on a deal.

        Examines every SecurityControlMapping for the deal and categorises
        each as implemented, partial, planned, or not-applicable.  Controls
        that are not yet implemented are flagged as gaps.

        Args:
            deal_id: UUID of the deal.

        Returns:
            A dict containing gap counts, gap details, and overall
            compliance percentage.
        """
        # TODO: Implement AI-powered gap analysis:
        #   1. Load all SecurityControlMapping records for the deal.
        #   2. Evaluate each mapping's implementation status and evidence.
        #   3. Use LLM to compare implementation descriptions against
        #      control requirements.
        #   4. Generate gap descriptions where controls are not fully met.
        #   5. Calculate overall compliance percentage.

        from apps.security_compliance.models import SecurityControlMapping

        mappings = SecurityControlMapping.objects.filter(
            deal_id=deal_id
        ).select_related("control", "control__framework")

        total = mappings.count()
        if total == 0:
            return {
                "deal_id": str(deal_id),
                "total_controls": 0,
                "compliance_pct": 0.0,
                "gaps": [],
            }

        implemented = mappings.filter(
            implementation_status="implemented"
        ).count()
        partial = mappings.filter(implementation_status="partial").count()
        planned = mappings.filter(implementation_status="planned").count()
        na = mappings.filter(implementation_status="not_applicable").count()

        applicable = total - na
        compliance_pct = (
            ((implemented + partial * 0.5) / applicable * 100)
            if applicable > 0
            else 0.0
        )

        gaps = []
        gap_mappings = mappings.exclude(
            implementation_status__in=["implemented", "not_applicable"]
        )
        for mapping in gap_mappings:
            gaps.append(
                {
                    "control_id": mapping.control.control_id,
                    "control_title": mapping.control.title,
                    "framework": mapping.control.framework.name,
                    "status": mapping.implementation_status,
                    "gap_description": mapping.gap_description,
                    "remediation_plan": mapping.remediation_plan,
                    "target_completion": (
                        mapping.target_completion.isoformat()
                        if mapping.target_completion
                        else None
                    ),
                }
            )

        logger.info(
            "assess_gaps: Deal %s - %.1f%% compliant, %d gaps found",
            deal_id,
            compliance_pct,
            len(gaps),
        )

        return {
            "deal_id": str(deal_id),
            "total_controls": total,
            "implemented": implemented,
            "partial": partial,
            "planned": planned,
            "not_applicable": na,
            "compliance_pct": round(compliance_pct, 2),
            "gaps": gaps,
        }

    def generate_poam(self, deal_id: str) -> dict[str, Any]:
        """Create a Plan of Action and Milestones (POA&M) for a deal.

        Gathers all non-implemented controls and builds a prioritised
        action plan with milestones and target dates.

        Args:
            deal_id: UUID of the deal.

        Returns:
            A dict with the POA&M items list and summary metadata.
        """
        # TODO: Implement full POA&M generation:
        #   1. Load all gap mappings (planned / partial).
        #   2. Prioritise by control priority (P1 > P2 > P3) and
        #      baseline impact level.
        #   3. Generate remediation milestones with estimated effort.
        #   4. Use LLM to draft remediation action descriptions.
        #   5. Store POA&M in a SecurityComplianceReport record.

        from apps.security_compliance.models import SecurityControlMapping

        gap_mappings = (
            SecurityControlMapping.objects.filter(deal_id=deal_id)
            .exclude(
                implementation_status__in=["implemented", "not_applicable"]
            )
            .select_related("control", "control__framework")
            .order_by("control__priority", "control__baseline_impact")
        )

        poam_items = []
        for idx, mapping in enumerate(gap_mappings, start=1):
            poam_items.append(
                {
                    "item_number": idx,
                    "control_id": mapping.control.control_id,
                    "control_title": mapping.control.title,
                    "framework": mapping.control.framework.name,
                    "weakness_description": (
                        mapping.gap_description
                        or f"Control {mapping.control.control_id} is not "
                        f"fully implemented."
                    ),
                    "priority": mapping.control.priority,
                    "remediation_plan": (
                        mapping.remediation_plan
                        or "Remediation plan to be determined."
                    ),
                    "target_completion": (
                        mapping.target_completion.isoformat()
                        if mapping.target_completion
                        else None
                    ),
                    "responsible_party": mapping.responsible_party or "TBD",
                    "current_status": mapping.implementation_status,
                }
            )

        logger.info(
            "generate_poam: Generated %d POA&M items for deal %s",
            len(poam_items),
            deal_id,
        )

        return {
            "deal_id": str(deal_id),
            "total_items": len(poam_items),
            "poam_items": poam_items,
        }
