"""
Autonomy Controller — enforces policy-defined autonomy levels (L0–L3).

Checks whether an AI action is permitted under the active policy.
Returns an ActionDecision with allowed/blocked status and reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUTONOMY_LEVELS: dict[int, str] = {
    0: "L0_assist",
    1: "L1_guided",
    2: "L2_conditional",
    3: "L3_strategic",
}

# Actions that ALWAYS require human review regardless of autonomy level or risk score.
MANDATORY_HITL_ACTIONS: frozenset[str] = frozenset(
    {
        "bid_no_bid",
        "final_price",
        "final_submission",
        "contract_terms",
        "contract_sign",
        "send_external_email",
    }
)


# ---------------------------------------------------------------------------
# ActionDecision dataclass
# ---------------------------------------------------------------------------

@dataclass
class ActionDecision:
    """Result of evaluating whether an AI action is permitted."""

    allowed: bool
    autonomy_level: str
    reason: str
    requires_hitl: bool
    risk_assessment: dict | None = field(default=None)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def get_active_level(policy: dict) -> int:
    """
    Return the integer autonomy level from the policy.

    Reads policy.get("current_autonomy_level", 1) and clamps to 0–3.
    """
    raw = policy.get("current_autonomy_level", 1)
    try:
        level = int(raw)
    except (TypeError, ValueError):
        level = 1
    return max(0, min(3, level))


def is_kill_switch_active(policy: dict) -> bool:
    """
    Return True if the kill switch has been activated in the policy.

    When the kill switch is active, every AI action requires human-in-the-loop
    review and no autonomous action is permitted.
    """
    return bool(policy.get("kill_switch_active", False))


def _get_allowed_actions_for_level(policy: dict, level: int) -> list[str]:
    """
    Extract the list of actions permitted at *level* from the policy document.

    The policy is expected to contain an "autonomy_levels" mapping like::

        {
            "autonomy_levels": {
                "0": {"allowed_actions": ["read_deal", "suggest_text"]},
                "1": {"allowed_actions": ["draft_section", "score_opportunity"]},
                "2": {"allowed_actions": ["submit_draft", "negotiate_terms"]},
                "3": {"allowed_actions": ["*"]},
            }
        }

    Level 3 with the wildcard ``"*"`` means any action is allowed at that level
    (subject to mandatory HITL and kill-switch overrides).

    All levels below *level* are considered included (cumulative permissions).
    """
    autonomy_levels_cfg = policy.get("autonomy_levels", {})
    accumulated: list[str] = []
    for lvl in range(0, level + 1):
        lvl_cfg = autonomy_levels_cfg.get(str(lvl), autonomy_levels_cfg.get(lvl, {}))
        actions = lvl_cfg.get("allowed_actions", [])
        accumulated.extend(actions)
    return accumulated


def _risk_exceeds_policy_threshold(policy: dict, risk_assessment: dict | None) -> bool:
    """
    Return True if the provided risk assessment composite score exceeds the
    policy's configured risk threshold.
    """
    if risk_assessment is None:
        return False
    threshold = float(policy.get("auto_approve_risk_ceiling", 0.6))
    composite = float(risk_assessment.get("composite", 0.0))
    return composite > threshold


# ---------------------------------------------------------------------------
# Primary public function
# ---------------------------------------------------------------------------

def check_action(
    action_name: str,
    policy: dict,
    risk_assessment: dict | None = None,
) -> ActionDecision:
    """
    Determine whether *action_name* is permitted under *policy*.

    Evaluation order (first matching rule wins):
    1. Kill switch active → blocked, requires_hitl=True.
    2. Action is in MANDATORY_HITL_ACTIONS → allowed=False, requires_hitl=True.
    3. Risk score exceeds policy threshold → blocked, requires_hitl=True.
    4. Action not in the accumulated allowed-actions for the current level → blocked.
    5. Otherwise → allowed.

    Parameters
    ----------
    action_name:
        Identifier for the AI action being requested (e.g. "draft_section").
    policy:
        Active policy document as a plain dict.  Key fields used:
          - current_autonomy_level (int, default 1)
          - kill_switch_active (bool, default False)
          - autonomy_levels (dict mapping str(int) → {"allowed_actions": [...]})
          - auto_approve_risk_ceiling (float, default 0.6)
          - hitl_risk_threshold (float, default 0.6)
    risk_assessment:
        Optional dict from risk_engine.RiskAssessment.to_dict().

    Returns
    -------
    ActionDecision
    """
    active_level = get_active_level(policy)
    level_label = AUTONOMY_LEVELS.get(active_level, f"L{active_level}_unknown")

    # --- Rule 1: Kill switch ---
    if is_kill_switch_active(policy):
        return ActionDecision(
            allowed=False,
            autonomy_level=level_label,
            reason=(
                "Kill switch is active. All AI actions require human review "
                "until the kill switch is deactivated."
            ),
            requires_hitl=True,
            risk_assessment=risk_assessment,
        )

    # --- Rule 2: Mandatory HITL actions ---
    if action_name in MANDATORY_HITL_ACTIONS:
        return ActionDecision(
            allowed=False,
            autonomy_level=level_label,
            reason=(
                f"Action '{action_name}' is classified as mandatory-HITL and can never "
                "be executed autonomously — human sign-off is required."
            ),
            requires_hitl=True,
            risk_assessment=risk_assessment,
        )

    # --- Rule 3: Risk threshold ---
    if _risk_exceeds_policy_threshold(policy, risk_assessment):
        composite = risk_assessment.get("composite", 0.0) if risk_assessment else 0.0
        threshold = policy.get("auto_approve_risk_ceiling", 0.6)
        return ActionDecision(
            allowed=False,
            autonomy_level=level_label,
            reason=(
                f"Risk score {composite:.3f} exceeds the policy ceiling of {threshold}. "
                "Human review is required before this action can proceed."
            ),
            requires_hitl=True,
            risk_assessment=risk_assessment,
        )

    # --- Rule 4: Allowed-actions check ---
    allowed_actions = _get_allowed_actions_for_level(policy, active_level)

    # Wildcard — any action is permitted at this level (after above checks)
    if "*" in allowed_actions:
        return ActionDecision(
            allowed=True,
            autonomy_level=level_label,
            reason=(
                f"Action '{action_name}' is permitted under autonomy level "
                f"{level_label} (wildcard grant)."
            ),
            requires_hitl=False,
            risk_assessment=risk_assessment,
        )

    if action_name not in allowed_actions:
        return ActionDecision(
            allowed=False,
            autonomy_level=level_label,
            reason=(
                f"Action '{action_name}' is not in the list of actions permitted "
                f"at autonomy level {level_label}. Escalate to a higher autonomy "
                "level or obtain explicit human approval."
            ),
            requires_hitl=False,
            risk_assessment=risk_assessment,
        )

    # --- Rule 5: Permitted ---
    return ActionDecision(
        allowed=True,
        autonomy_level=level_label,
        reason=(
            f"Action '{action_name}' is permitted under autonomy level {level_label}."
        ),
        requires_hitl=False,
        risk_assessment=risk_assessment,
    )
