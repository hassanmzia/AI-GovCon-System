import logging
from typing import Any

logger = logging.getLogger(__name__)


class FrameworkAnalyzer:
    """Analyses deal characteristics to determine applicable frameworks
    and provides cross-framework control mapping."""

    def get_applicable_frameworks(
        self, deal_id: str
    ) -> list[dict[str, Any]]:
        """Determine which security frameworks apply to a deal based on
        its characteristics (agency, contract type, data sensitivity, etc.).

        Args:
            deal_id: UUID of the deal.

        Returns:
            A list of dicts, each describing an applicable framework with
            its id, name, version, and rationale for applicability.
        """
        # TODO: Implement intelligent framework selection:
        #   1. Load the deal and its opportunity metadata.
        #   2. Analyse agency (DoD -> CMMC/NIST, HHS -> HIPAA, etc.).
        #   3. Check for CUI/classified data handling needs.
        #   4. Evaluate cloud hosting requirements for FedRAMP.
        #   5. Consider contract clauses (DFARS 252.204-7012, etc.).
        #   6. Use LLM for ambiguous cases.

        from apps.deals.models import Deal
        from apps.security_compliance.models import SecurityFramework

        try:
            deal = Deal.objects.select_related("opportunity").get(pk=deal_id)
        except Deal.DoesNotExist:
            logger.error(
                "get_applicable_frameworks: Deal %s not found", deal_id
            )
            return []

        # Agency/keyword rules for framework applicability
        agency = (
            (deal.opportunity.agency if deal.opportunity else "") or ""
        ).upper()
        title_upper = deal.title.upper()

        likely_keywords: list[str] = []

        dod_tokens = {"DOD", "DEPARTMENT OF DEFENSE", "ARMY", "NAVY", "AIR FORCE",
                      "MARINES", "SOCOM", "DARPA", "DIA", "NSA", "DISA"}
        if any(tok in agency for tok in dod_tokens):
            likely_keywords.extend(["CMMC", "800-171", "800-53", "DISA"])

        civilian_tokens = {"GSA", "DHS", "DOJ", "STATE", "TREASURY", "HUD",
                           "DOT", "DOE", "DOL", "DOC", "USDA", "DOI", "EPA",
                           "SBA", "SSA", "VA", "OPM"}
        if any(tok in agency for tok in civilian_tokens):
            likely_keywords.extend(["800-53", "FISMA"])

        if any(tok in agency for tok in {"HHS", "NIH", "CDC", "FDA", "CMS", "HEALTH"}):
            likely_keywords.extend(["HIPAA", "800-53"])

        cloud_tokens = {"CLOUD", "SAAS", "IAAS", "PAAS", "AWS", "AZURE", "GCP"}
        if any(k in title_upper for k in cloud_tokens) or any(k in agency for k in cloud_tokens):
            likely_keywords.append("FEDRAMP")

        if any(k in title_upper for k in {"ITAR", "EAR", "EXPORT", "MUNITIONS"}):
            likely_keywords.extend(["800-53", "CMMC"])

        # Always baseline-include NIST 800-53 / FISMA for any federal contract
        if not likely_keywords:
            likely_keywords.extend(["800-53", "FISMA"])

        likely_upper = [k.upper() for k in likely_keywords]

        frameworks = SecurityFramework.objects.filter(is_active=True)
        results = []
        for fw in frameworks:
            fw_upper = fw.name.upper()
            if not any(kw in fw_upper for kw in likely_upper):
                continue

            rationale_parts: list[str] = []
            if any(k in fw_upper for k in ("CMMC", "800-171")):
                rationale_parts.append(
                    "Required for DoD contracts handling CUI per DFARS 252.204-7012."
                )
            if "800-53" in fw_upper or "FISMA" in fw_upper:
                rationale_parts.append(
                    f"Required under FISMA for federal information systems "
                    f"(agency: {deal.opportunity.agency if deal.opportunity else 'federal'})."
                )
            if "FEDRAMP" in fw_upper:
                rationale_parts.append(
                    "Required for cloud service offerings in federal environments."
                )
            if "HIPAA" in fw_upper:
                rationale_parts.append(
                    "Required for contracts handling Protected Health Information (PHI)."
                )
            if not rationale_parts:
                rationale_parts.append(f"Applicable based on deal context: '{deal.title}'.")

            results.append(
                {
                    "id": str(fw.id),
                    "name": fw.name,
                    "version": fw.version,
                    "rationale": " ".join(rationale_parts),
                }
            )

        logger.info(
            "get_applicable_frameworks: Found %d candidate frameworks "
            "for deal %s",
            len(results),
            deal_id,
        )
        return results

    def cross_map_controls(
        self,
        source_framework_id: str,
        target_framework_id: str,
    ) -> dict[str, Any]:
        """Map controls between two different security frameworks.

        Useful for organisations that need to demonstrate compliance across
        multiple frameworks (e.g. NIST 800-53 to FedRAMP, or CMMC to
        NIST 800-171).

        Args:
            source_framework_id: UUID of the source framework.
            target_framework_id: UUID of the target framework.

        Returns:
            A dict containing the mapping results: lists of matched
            controls, unmatched source controls, and unmatched target
            controls.
        """
        # TODO: Implement cross-framework mapping:
        #   1. Load controls from both frameworks.
        #   2. Use related_controls JSON field for known cross-references.
        #   3. Apply keyword / semantic similarity for fuzzy matching.
        #   4. Allow LLM refinement for ambiguous matches.
        #   5. Return matched pairs plus unmapped controls on each side.

        from apps.security_compliance.models import SecurityFramework

        try:
            source = SecurityFramework.objects.get(pk=source_framework_id)
            target = SecurityFramework.objects.get(pk=target_framework_id)
        except SecurityFramework.DoesNotExist as exc:
            logger.error("cross_map_controls: %s", exc)
            return {"error": str(exc)}

        source_controls = list(
            source.controls.values("id", "control_id", "title", "related_controls")
        )
        target_controls = list(
            target.controls.values("id", "control_id", "title", "related_controls")
        )

        # Placeholder: build a naive mapping based on related_controls refs.
        target_lookup = {tc["control_id"]: tc for tc in target_controls}
        matched = []
        unmatched_source = []

        for sc in source_controls:
            related = sc.get("related_controls") or []
            match_found = False
            for ref in related:
                if ref in target_lookup:
                    matched.append(
                        {
                            "source_control_id": sc["control_id"],
                            "source_title": sc["title"],
                            "target_control_id": ref,
                            "target_title": target_lookup[ref]["title"],
                            "confidence": "high",
                        }
                    )
                    match_found = True
            if not match_found:
                unmatched_source.append(
                    {
                        "control_id": sc["control_id"],
                        "title": sc["title"],
                    }
                )

        matched_target_ids = {m["target_control_id"] for m in matched}
        unmatched_target = [
            {"control_id": tc["control_id"], "title": tc["title"]}
            for tc in target_controls
            if tc["control_id"] not in matched_target_ids
        ]

        logger.info(
            "cross_map_controls: %s -> %s: %d matched, %d unmatched source, "
            "%d unmatched target",
            source.name,
            target.name,
            len(matched),
            len(unmatched_source),
            len(unmatched_target),
        )

        return {
            "source_framework": source.name,
            "target_framework": target.name,
            "matched_controls": matched,
            "unmatched_source_controls": unmatched_source,
            "unmatched_target_controls": unmatched_target,
            "total_matched": len(matched),
        }
