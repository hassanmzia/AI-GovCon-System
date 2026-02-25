"""Framework cross-walker: maps controls between NIST, CMMC, FedRAMP, ISO 27001."""
import logging
from typing import Any

logger = logging.getLogger("ai_deal_manager.security.crosswalker")

# ── Cross-walk mappings ────────────────────────────────────────────────────────

# NIST 800-53 → CMMC L2 → ISO 27001:2022 → CIS Controls v8
CROSSWALK: dict[str, dict[str, list[str]]] = {
    "AC-1":  {"cmmc_l2": [],           "iso_27001": ["5.1", "5.2"],          "cis_v8": ["5.1"]},
    "AC-2":  {"cmmc_l2": ["AC.L2-3.1.1"],  "iso_27001": ["5.15", "5.18"],  "cis_v8": ["5.3", "5.4", "5.6"]},
    "AC-3":  {"cmmc_l2": ["AC.L2-3.1.2"],  "iso_27001": ["5.15"],          "cis_v8": ["3.3", "6.7"]},
    "AC-17": {"cmmc_l2": ["AC.L2-3.1.3"],  "iso_27001": ["8.20", "8.21"],  "cis_v8": ["12.6"]},
    "AU-2":  {"cmmc_l2": ["AU.L2-3.3.1"],  "iso_27001": ["8.15"],          "cis_v8": ["8.2", "8.5"]},
    "AU-12": {"cmmc_l2": ["AU.L2-3.3.2"],  "iso_27001": ["8.15"],          "cis_v8": ["8.5"]},
    "CM-2":  {"cmmc_l2": ["CM.L2-3.4.1"],  "iso_27001": ["8.8", "8.9"],    "cis_v8": ["4.1", "4.2"]},
    "CM-6":  {"cmmc_l2": ["CM.L2-3.4.2"],  "iso_27001": ["8.9"],           "cis_v8": ["4.1"]},
    "CM-7":  {"cmmc_l2": ["CM.L2-3.4.6"],  "iso_27001": ["8.19"],          "cis_v8": ["4.8"]},
    "IA-2":  {"cmmc_l2": ["IA.L2-3.5.3"],  "iso_27001": ["5.17", "8.5"],   "cis_v8": ["6.3", "6.5"]},
    "IA-5":  {"cmmc_l2": ["IA.L2-3.5.4"],  "iso_27001": ["5.17"],          "cis_v8": ["5.2"]},
    "IR-4":  {"cmmc_l2": ["IR.L2-3.6.1"],  "iso_27001": ["5.26"],          "cis_v8": ["17.4", "17.6"]},
    "IR-6":  {"cmmc_l2": ["IR.L2-3.6.2"],  "iso_27001": ["5.26"],          "cis_v8": ["17.4"]},
    "MA-2":  {"cmmc_l2": ["MA.L2-3.7.1"],  "iso_27001": ["5.37"],          "cis_v8": ["4.4"]},
    "RA-3":  {"cmmc_l2": ["RA.L2-3.11.1"], "iso_27001": ["5.19", "8.8"],   "cis_v8": ["18.1"]},
    "SA-9":  {"cmmc_l2": ["SR.L2-3.17.1"], "iso_27001": ["5.19", "5.20"],  "cis_v8": ["15.1"]},
    "SC-7":  {"cmmc_l2": ["SC.L2-3.13.1"], "iso_27001": ["8.20", "8.22"],  "cis_v8": ["12.2", "13.1"]},
    "SC-8":  {"cmmc_l2": ["SC.L2-3.13.8"], "iso_27001": ["8.24"],          "cis_v8": ["3.10"]},
    "SC-28": {"cmmc_l2": ["SC.L2-3.13.16"],"iso_27001": ["8.24"],          "cis_v8": ["3.11"]},
    "SI-2":  {"cmmc_l2": ["SI.L2-3.14.1"], "iso_27001": ["8.8"],           "cis_v8": ["7.4"]},
    "SI-3":  {"cmmc_l2": ["SI.L2-3.14.2"], "iso_27001": ["8.7"],           "cis_v8": ["10.1"]},
}

# FedRAMP Moderate baseline controls
FEDRAMP_MODERATE_CONTROLS = list(CROSSWALK.keys())  # simplified – all listed controls

# FedRAMP High adds additional controls
FEDRAMP_HIGH_ADDITIONAL = ["AC-2(1)", "AC-2(2)", "SC-8(1)", "SC-28(1)"]


def crosswalk_controls(
    source_framework: str,
    source_controls: list[str],
    target_framework: str,
) -> dict[str, Any]:
    """Map controls from one framework to another.

    Args:
        source_framework: "NIST_800_53", "CMMC_L2", "ISO_27001", "CIS_V8".
        source_controls: List of control IDs in the source framework.
        target_framework: Target framework to map to.

    Returns:
        Dict with: mappings (source → target), unmapped, coverage_pct.
    """
    mappings: dict[str, list[str]] = {}
    unmapped: list[str] = []

    target_key = _framework_to_key(target_framework)
    source_key = _framework_to_key(source_framework)

    for ctrl in source_controls:
        ctrl_upper = ctrl.upper()

        if source_framework in ("NIST_800_53", "NIST"):
            # Mapping from NIST to other
            entry = CROSSWALK.get(ctrl_upper, {})
            targets = entry.get(target_key, [])
            if targets:
                mappings[ctrl] = targets
            else:
                unmapped.append(ctrl)

        elif source_framework in ("CMMC_L2", "CMMC"):
            # Reverse lookup: CMMC → NIST
            nist_ctrl = _cmmc_to_nist(ctrl_upper)
            if nist_ctrl:
                if target_framework in ("NIST_800_53", "NIST"):
                    mappings[ctrl] = [nist_ctrl]
                else:
                    # CMMC → NIST → target
                    entry = CROSSWALK.get(nist_ctrl, {})
                    targets = entry.get(target_key, [])
                    if targets:
                        mappings[ctrl] = targets
                    else:
                        unmapped.append(ctrl)
            else:
                unmapped.append(ctrl)

        else:
            # Generic: try to find in CROSSWALK values
            found = _reverse_lookup(ctrl_upper, source_key, target_key)
            if found:
                mappings[ctrl] = found
            else:
                unmapped.append(ctrl)

    total = len(source_controls)
    mapped_count = len(mappings)
    return {
        "source_framework": source_framework,
        "target_framework": target_framework,
        "mappings": mappings,
        "unmapped": unmapped,
        "mapped_count": mapped_count,
        "total_count": total,
        "coverage_pct": round(mapped_count / total * 100, 1) if total else 0.0,
    }


def get_fedramp_baseline(level: str = "moderate") -> list[str]:
    """Get FedRAMP control baseline for a given impact level."""
    if level.lower() == "high":
        return FEDRAMP_MODERATE_CONTROLS + FEDRAMP_HIGH_ADDITIONAL
    if level.lower() == "low":
        return [c for c in FEDRAMP_MODERATE_CONTROLS if c in ("AC-1", "AU-2", "CM-2", "IA-2", "SC-7", "SI-2", "SI-3")]
    return FEDRAMP_MODERATE_CONTROLS


def find_equivalent_controls(control_id: str) -> dict[str, list[str]]:
    """Find all equivalent controls across frameworks for a given NIST control."""
    entry = CROSSWALK.get(control_id.upper(), {})
    return {
        "nist_800_53": [control_id],
        "cmmc_l2": entry.get("cmmc_l2", []),
        "iso_27001": entry.get("iso_27001", []),
        "cis_v8": entry.get("cis_v8", []),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _framework_to_key(framework: str) -> str:
    mapping = {
        "CMMC_L2": "cmmc_l2",
        "CMMC": "cmmc_l2",
        "ISO_27001": "iso_27001",
        "ISO27001": "iso_27001",
        "CIS_V8": "cis_v8",
        "CIS": "cis_v8",
    }
    return mapping.get(framework.upper(), "cmmc_l2")


def _cmmc_to_nist(cmmc_id: str) -> str | None:
    from backend.apps.security_compliance.services.control_mapper import CMMC_L2_PRACTICES
    return CMMC_L2_PRACTICES.get(cmmc_id)


def _reverse_lookup(ctrl_id: str, source_key: str, target_key: str) -> list[str]:
    """Find controls by reverse mapping."""
    results = []
    for nist_id, mappings in CROSSWALK.items():
        if ctrl_id in mappings.get(source_key, []):
            targets = mappings.get(target_key, [])
            results.extend(targets)
            if target_key in ("nist_800_53", "nist"):
                results.append(nist_id)
    return list(set(results))
