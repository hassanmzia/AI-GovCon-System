"""Tests for the governance subsystem: AutonomyController, RiskEngine, PolicyLoader."""
import math
from unittest.mock import AsyncMock, patch

import pytest

from src.governance.risk_engine import (
    RiskScore,
    assess,
    compute_compliance_risk,
    compute_composite,
    compute_deadline_risk,
    compute_financial_risk,
    compute_legal_risk,
    compute_reputation_risk,
    compute_security_risk,
)
from src.governance.autonomy_controller import AutonomyController
from src.governance import policy_loader


# ── RiskEngine: compute_deadline_risk ────────────────────────────────────────


class TestDeadlineRisk:
    def test_deadline_passed_returns_max_risk(self):
        assert compute_deadline_risk(days_remaining=0) == 1.0
        assert compute_deadline_risk(days_remaining=-5) == 1.0

    def test_ample_time_returns_low_risk(self):
        # 60 days remaining with 14 needed => ratio ~0.23, sigmoid well below 0.5
        risk = compute_deadline_risk(days_remaining=60, days_needed_estimate=14)
        assert risk < 0.05

    def test_tight_deadline_returns_high_risk(self):
        # 7 days remaining with 14 needed => ratio 2.0, sigmoid near 1.0
        risk = compute_deadline_risk(days_remaining=7, days_needed_estimate=14)
        assert risk > 0.9

    def test_equal_days_remaining_and_needed(self):
        # ratio = 1.0 => sigmoid at midpoint => ~0.5
        risk = compute_deadline_risk(days_remaining=14, days_needed_estimate=14)
        assert 0.45 <= risk <= 0.55

    def test_zero_days_needed_returns_zero_risk(self):
        assert compute_deadline_risk(days_remaining=10, days_needed_estimate=0) == 0.0

    def test_result_is_bounded_zero_to_one(self):
        for remaining in [0.5, 1, 5, 10, 100]:
            for needed in [1, 7, 14, 30]:
                risk = compute_deadline_risk(remaining, needed)
                assert 0.0 <= risk <= 1.0


# ── RiskEngine: compute_compliance_risk ──────────────────────────────────────


class TestComplianceRisk:
    def test_full_coverage_no_missing_forms(self):
        assert compute_compliance_risk(coverage_pct=1.0, missing_forms=0) == 0.0

    def test_zero_coverage(self):
        risk = compute_compliance_risk(coverage_pct=0.0, missing_forms=0)
        assert risk == 1.0

    def test_missing_forms_add_penalty(self):
        base = compute_compliance_risk(coverage_pct=0.8, missing_forms=0)
        with_forms = compute_compliance_risk(coverage_pct=0.8, missing_forms=2)
        assert with_forms == pytest.approx(base + 0.20, abs=0.001)

    def test_missing_forms_penalty_caps_at_040(self):
        risk_4 = compute_compliance_risk(coverage_pct=0.8, missing_forms=4)
        risk_10 = compute_compliance_risk(coverage_pct=0.8, missing_forms=10)
        assert risk_4 == risk_10  # both capped at 0.40 penalty

    def test_coverage_clipped_above_one(self):
        assert compute_compliance_risk(coverage_pct=1.5) == 0.0

    def test_coverage_clipped_below_zero(self):
        assert compute_compliance_risk(coverage_pct=-0.5) == 1.0

    def test_total_risk_caps_at_one(self):
        risk = compute_compliance_risk(coverage_pct=0.0, missing_forms=10)
        assert risk == 1.0


# ── RiskEngine: compute_legal_risk ───────────────────────────────────────────


class TestLegalRisk:
    def test_no_clauses_returns_zero(self):
        assert compute_legal_risk(prohibited_clauses=0, review_clauses=0) == 0.0

    def test_prohibited_clauses_scale(self):
        assert compute_legal_risk(prohibited_clauses=1) == pytest.approx(0.30)
        assert compute_legal_risk(prohibited_clauses=2) == pytest.approx(0.60)

    def test_prohibited_caps_at_090(self):
        assert compute_legal_risk(prohibited_clauses=5) == pytest.approx(0.90)

    def test_review_clauses_scale(self):
        assert compute_legal_risk(review_clauses=5) == pytest.approx(0.40)

    def test_combined_caps_at_one(self):
        risk = compute_legal_risk(prohibited_clauses=4, review_clauses=10)
        assert risk == 1.0


# ── RiskEngine: compute_financial_risk ───────────────────────────────────────


class TestFinancialRisk:
    def test_margin_above_floor_no_deficit(self):
        risk = compute_financial_risk(
            margin_pct=25.0, margin_floor=18.0, price_uncertainty=0.0, assumption_weakness=0.0
        )
        assert risk == 0.0

    def test_margin_below_floor_adds_risk(self):
        # 4 points below floor => 4 * 0.05 = 0.20 margin risk
        risk = compute_financial_risk(
            margin_pct=14.0, margin_floor=18.0, price_uncertainty=0.0, assumption_weakness=0.0
        )
        assert risk == pytest.approx(0.20)

    def test_uncertainty_and_assumption_compound(self):
        risk = compute_financial_risk(
            margin_pct=25.0, margin_floor=18.0, price_uncertainty=0.8, assumption_weakness=0.8
        )
        # uncertainty: min(0.8*0.25, 0.25)=0.20, assumption: min(0.8*0.15,0.15)=0.12
        assert risk == pytest.approx(0.32)


# ── RiskEngine: compute_security_risk ────────────────────────────────────────


class TestSecurityRisk:
    def test_no_flags(self):
        assert compute_security_risk(has_cui=False, has_itar=False) == 0.0

    def test_cui_only(self):
        assert compute_security_risk(has_cui=True, has_itar=False) == pytest.approx(0.35)

    def test_itar_only(self):
        assert compute_security_risk(has_cui=False, has_itar=True) == pytest.approx(0.50)

    def test_both_flags(self):
        assert compute_security_risk(has_cui=True, has_itar=True) == pytest.approx(0.85)


# ── RiskEngine: compute_composite ────────────────────────────────────────────


class TestComposite:
    def test_all_zeros(self):
        assert compute_composite(0, 0, 0, 0, 0, 0) == 0.0

    def test_all_ones(self):
        assert compute_composite(1, 1, 1, 1, 1, 1) == 1.0

    def test_weights_sum_to_one(self):
        # Verify correct weighting: legal 25%, compliance 25%, deadline 15%, financial 15%, security 10%, reputation 10%
        result = compute_composite(
            legal=1.0, compliance=0.0, deadline=0.0, financial=0.0, security=0.0, reputation=0.0
        )
        assert result == pytest.approx(0.25)

    def test_weighted_average(self):
        result = compute_composite(
            legal=0.5, compliance=0.5, deadline=0.5, financial=0.5, security=0.5, reputation=0.5
        )
        assert result == pytest.approx(0.5)


# ── RiskEngine: RiskScore dataclass ──────────────────────────────────────────


class TestRiskScore:
    def test_composite_auto_computed(self):
        score = RiskScore(legal=0.4, compliance=0.2, deadline=0.1)
        expected = compute_composite(0.4, 0.2, 0.1, 0.0, 0.0, 0.0)
        assert score.composite == pytest.approx(expected)

    def test_exceeds_threshold_true(self):
        score = RiskScore(legal=1.0, compliance=1.0)
        assert score.exceeds_threshold(0.3)

    def test_exceeds_threshold_false(self):
        score = RiskScore()  # all zeros
        assert not score.exceeds_threshold(0.01)

    def test_to_dict_has_all_keys(self):
        d = RiskScore().to_dict()
        expected_keys = {"legal", "compliance", "deadline", "financial", "security", "reputation", "composite"}
        assert set(d.keys()) == expected_keys

    def test_default_risk_score_is_zero(self):
        score = RiskScore()
        assert score.composite == 0.0


# ── RiskEngine: assess() integration ─────────────────────────────────────────


class TestAssess:
    def test_assess_with_empty_context_uses_safe_defaults(self):
        policy = policy_loader.DEFAULT_POLICY
        score = assess({}, policy)
        # Empty context => days_remaining=30, days_needed=14, coverage=1.0, margin=20 (>18 floor)
        assert score.compliance == 0.0
        assert score.legal == 0.0
        assert score.security == 0.0

    def test_assess_high_risk_deal(self):
        policy = policy_loader.DEFAULT_POLICY
        context = {
            "days_remaining": 2,
            "days_needed_estimate": 14,
            "compliance_coverage_pct": 0.3,
            "missing_forms": 5,
            "prohibited_clauses": 3,
            "has_cui": True,
            "has_itar": True,
            "margin_pct": 10.0,
        }
        score = assess(context, policy)
        assert score.composite > 0.5
        assert score.deadline > 0.9
        assert score.legal > 0.8
        assert score.security == pytest.approx(0.85)

    def test_assess_uses_policy_margin_floor(self):
        # Custom policy with high margin floor
        policy = {**policy_loader.DEFAULT_POLICY, "pricing_guardrails": {"min_margin_percent": 30}}
        context = {"margin_pct": 25.0}  # below 30 floor
        score = assess(context, policy)
        assert score.financial > 0.0

        # Same context with low margin floor => no margin deficit
        policy2 = {**policy_loader.DEFAULT_POLICY, "pricing_guardrails": {"min_margin_percent": 10}}
        score2 = assess(context, policy2)
        assert score2.financial < score.financial


# ── PolicyLoader: DEFAULT_POLICY structure ───────────────────────────────────


class TestPolicyLoaderDefaults:
    def test_default_policy_has_required_keys(self):
        p = policy_loader.DEFAULT_POLICY
        assert "current_autonomy_level" in p
        assert "kill_switch_active" in p
        assert "autonomy_levels" in p
        assert "risk_thresholds" in p
        assert "pricing_guardrails" in p

    def test_default_policy_level_is_one(self):
        assert policy_loader.DEFAULT_POLICY["current_autonomy_level"] == 1

    def test_default_kill_switch_is_off(self):
        assert policy_loader.DEFAULT_POLICY["kill_switch_active"] is False

    def test_default_policy_has_three_levels(self):
        levels = policy_loader.DEFAULT_POLICY["autonomy_levels"]
        assert "L0" in levels
        assert "L1" in levels
        assert "L2" in levels

    def test_l1_allows_research_actions(self):
        l1 = policy_loader.DEFAULT_POLICY["autonomy_levels"]["L1"]
        assert "opportunity_search" in l1["allowed_actions"]
        assert "rfp_analysis" in l1["allowed_actions"]
        assert "market_research" in l1["allowed_actions"]

    def test_l1_requires_hitl_for_consequential_actions(self):
        l1 = policy_loader.DEFAULT_POLICY["autonomy_levels"]["L1"]
        assert "final_price" in l1["requires_hitl"]
        assert "final_submission" in l1["requires_hitl"]
        assert "contract_terms" in l1["requires_hitl"]

    def test_cache_invalidation_clears_state(self):
        policy_loader._cache["policy"] = {"fake": True}
        policy_loader._cache["loaded_at"] = 999999999.0
        policy_loader.invalidate_cache()
        assert policy_loader._cache["policy"] is None
        assert policy_loader._cache["loaded_at"] == 0.0


# ── AutonomyController.can_act() ─────────────────────────────────────────────


class TestAutonomyControllerCanAct:
    @pytest.fixture
    def controller(self):
        return AutonomyController()

    @pytest.mark.asyncio
    async def test_allowed_action_at_l1(self, controller):
        """An L1-allowed action with low risk should be autonomous."""
        policy = {**policy_loader.DEFAULT_POLICY, "current_autonomy_level": 1}
        with patch("src.governance.policy_loader.get_policy", new_callable=AsyncMock, return_value=policy), \
             patch("src.governance.hitl_manager.check_gate", new_callable=AsyncMock) as mock_gate:
            mock_gate.return_value = {
                "allowed": True,
                "requires_hitl": False,
                "reason": "Permitted at L1.",
                "autonomy_level": 1,
            }
            result = await controller.can_act("rfp_analysis", "deal-123")
            assert result["can_act"] is True
            assert result["requires_hitl"] is False
            assert result["policy_level"] == 1

    @pytest.mark.asyncio
    async def test_mandatory_hitl_action_blocked(self, controller):
        """A mandatory HITL action like final_submission should require approval."""
        policy = {**policy_loader.DEFAULT_POLICY, "current_autonomy_level": 2}
        with patch("src.governance.policy_loader.get_policy", new_callable=AsyncMock, return_value=policy), \
             patch("src.governance.hitl_manager.check_gate", new_callable=AsyncMock) as mock_gate:
            mock_gate.return_value = {
                "allowed": False,
                "requires_hitl": True,
                "reason": "Mandatory HITL.",
                "autonomy_level": 2,
            }
            result = await controller.can_act("final_submission", "deal-456")
            assert result["can_act"] is False
            assert result["requires_hitl"] is True

    @pytest.mark.asyncio
    async def test_kill_switch_blocks_everything(self, controller):
        """When kill switch is active, all actions should be blocked."""
        policy = {**policy_loader.DEFAULT_POLICY, "kill_switch_active": True}
        with patch("src.governance.policy_loader.get_policy", new_callable=AsyncMock, return_value=policy), \
             patch("src.governance.hitl_manager.check_gate", new_callable=AsyncMock) as mock_gate:
            mock_gate.return_value = {
                "allowed": False,
                "requires_hitl": False,
                "reason": "Kill switch is active.",
                "autonomy_level": 1,
            }
            result = await controller.can_act("opportunity_search", "deal-789")
            assert result["can_act"] is False

    @pytest.mark.asyncio
    async def test_policy_load_failure_uses_default(self, controller):
        """When policy loading fails, controller should fall back to DEFAULT_POLICY."""
        with patch("src.governance.policy_loader.get_policy", new_callable=AsyncMock, side_effect=Exception("DB down")), \
             patch("src.governance.hitl_manager.check_gate", new_callable=AsyncMock) as mock_gate:
            mock_gate.return_value = {
                "allowed": True,
                "requires_hitl": False,
                "reason": "Fallback allowed.",
                "autonomy_level": 1,
            }
            result = await controller.can_act("rfp_analysis", "deal-001")
            # Should still work — using DEFAULT_POLICY
            assert "can_act" in result
            assert "risk_score" in result

    @pytest.mark.asyncio
    async def test_risk_assessment_failure_uses_zero_score(self, controller):
        """When risk engine fails, controller should use a zero RiskScore."""
        policy = policy_loader.DEFAULT_POLICY
        with patch("src.governance.policy_loader.get_policy", new_callable=AsyncMock, return_value=policy), \
             patch("src.governance.risk_engine.assess", side_effect=Exception("math error")), \
             patch("src.governance.hitl_manager.check_gate", new_callable=AsyncMock) as mock_gate:
            mock_gate.return_value = {
                "allowed": True,
                "requires_hitl": False,
                "reason": "OK",
                "autonomy_level": 1,
            }
            result = await controller.can_act("rfp_analysis", "deal-002")
            # Risk score should be all zeros (fallback)
            assert result["risk_score"]["composite"] == 0.0

    @pytest.mark.asyncio
    async def test_gate_failure_defaults_to_block(self, controller):
        """When check_gate itself fails, controller should block the action."""
        policy = policy_loader.DEFAULT_POLICY
        with patch("src.governance.policy_loader.get_policy", new_callable=AsyncMock, return_value=policy), \
             patch("src.governance.hitl_manager.check_gate", new_callable=AsyncMock, side_effect=Exception("gate crash")):
            result = await controller.can_act("rfp_analysis", "deal-003")
            assert result["can_act"] is False
            assert result["requires_hitl"] is True
            assert "failed unexpectedly" in result["reason"]

    @pytest.mark.asyncio
    async def test_result_contains_risk_score_dict(self, controller):
        """The can_act result should always include a risk_score dict."""
        policy = policy_loader.DEFAULT_POLICY
        with patch("src.governance.policy_loader.get_policy", new_callable=AsyncMock, return_value=policy), \
             patch("src.governance.hitl_manager.check_gate", new_callable=AsyncMock) as mock_gate:
            mock_gate.return_value = {
                "allowed": True,
                "requires_hitl": False,
                "reason": "OK",
                "autonomy_level": 1,
            }
            result = await controller.can_act("rfp_analysis", "deal-004", deal_context={"days_remaining": 20})
            rs = result["risk_score"]
            assert "composite" in rs
            assert "legal" in rs
            assert "deadline" in rs
