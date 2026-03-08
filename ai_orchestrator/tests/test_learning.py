"""Tests for the learning subsystem: Thompson Sampling, LinUCB, DailyOpportunitySelector."""
import random

import pytest

from src.learning.bandit import (
    DailyOpportunitySelector,
    LinUCBBandit,
    ThompsonSamplingBandit,
    _beta_sample,
    _dot,
    _mat_vec_mul,
    _pad_or_truncate,
    opportunity_to_features,
)


# ── ThompsonSamplingBandit ───────────────────────────────────────────────────


class TestThompsonSamplingBandit:
    def test_new_arm_initialized_with_uniform_prior(self):
        bandit = ThompsonSamplingBandit()
        bandit._init_arm("arm_a")
        assert bandit.alpha["arm_a"] == 1.0
        assert bandit.beta["arm_a"] == 1.0

    def test_init_arm_idempotent(self):
        bandit = ThompsonSamplingBandit()
        bandit.alpha["arm_a"] = 5.0
        bandit.beta["arm_a"] = 3.0
        bandit._init_arm("arm_a")  # should NOT reset
        assert bandit.alpha["arm_a"] == 5.0

    def test_sample_returns_value_in_zero_one(self):
        bandit = ThompsonSamplingBandit()
        random.seed(42)
        for _ in range(100):
            s = bandit.sample("test_arm")
            assert 0.0 <= s <= 1.0

    def test_update_positive_reward_increments_alpha(self):
        bandit = ThompsonSamplingBandit()
        bandit._init_arm("arm_x")
        initial_alpha = bandit.alpha["arm_x"]
        bandit.update("arm_x", reward=1.0)
        assert bandit.alpha["arm_x"] == initial_alpha + 1.0
        assert bandit.beta["arm_x"] == 1.0  # unchanged

    def test_update_zero_reward_increments_beta(self):
        bandit = ThompsonSamplingBandit()
        bandit._init_arm("arm_x")
        initial_beta = bandit.beta["arm_x"]
        bandit.update("arm_x", reward=0)
        assert bandit.beta["arm_x"] == initial_beta + 1.0
        assert bandit.alpha["arm_x"] == 1.0  # unchanged

    def test_update_negative_reward_increments_beta(self):
        bandit = ThompsonSamplingBandit()
        bandit._init_arm("arm_x")
        bandit.update("arm_x", reward=-0.5)
        assert bandit.beta["arm_x"] == 2.0

    def test_select_top_k_returns_k_items(self):
        bandit = ThompsonSamplingBandit()
        arms = [f"arm_{i}" for i in range(20)]
        selected = bandit.select_top_k(arms, k=5)
        assert len(selected) == 5
        assert all(arm in arms for arm in selected)

    def test_select_top_k_returns_all_when_k_exceeds_arms(self):
        bandit = ThompsonSamplingBandit()
        arms = ["a", "b", "c"]
        selected = bandit.select_top_k(arms, k=10)
        assert len(selected) == 3

    def test_select_top_k_favors_high_alpha_arms(self):
        """Arms with many successes should be selected more often than fresh arms."""
        bandit = ThompsonSamplingBandit()
        # Give "winner" a strong track record
        bandit.alpha["winner"] = 100.0
        bandit.beta["winner"] = 2.0
        # Other arms are fresh (uniform prior)
        arms = ["winner"] + [f"arm_{i}" for i in range(9)]

        wins = sum(1 for _ in range(50) if "winner" in bandit.select_top_k(arms, k=3))
        # With alpha=100, beta=2, "winner" should be selected nearly every time
        assert wins > 40

    def test_get_win_probability_estimate(self):
        bandit = ThompsonSamplingBandit()
        bandit.alpha["arm_a"] = 8.0
        bandit.beta["arm_a"] = 2.0
        prob = bandit.get_win_probability_estimate("arm_a")
        assert prob == pytest.approx(0.8)

    def test_get_win_probability_new_arm(self):
        bandit = ThompsonSamplingBandit()
        prob = bandit.get_win_probability_estimate("new_arm")
        assert prob == pytest.approx(0.5)  # uniform prior => 1/(1+1)

    def test_serialization_roundtrip(self):
        bandit = ThompsonSamplingBandit()
        bandit.update("arm_1", 1.0)
        bandit.update("arm_1", 1.0)
        bandit.update("arm_2", 0.0)
        data = bandit.to_dict()

        restored = ThompsonSamplingBandit.from_dict(data)
        assert restored.alpha == bandit.alpha
        assert restored.beta == bandit.beta


# ── LinUCBBandit ─────────────────────────────────────────────────────────────


class TestLinUCBBandit:
    def test_init_arm_creates_identity_matrix(self):
        bandit = LinUCBBandit(d=3, alpha=1.0)
        bandit._init_arm("arm_a")
        A = bandit.A["arm_a"]
        # Should be 3x3 identity
        for i in range(3):
            for j in range(3):
                expected = 1.0 if i == j else 0.0
                assert A[i][j] == expected

    def test_init_arm_creates_zero_b_vector(self):
        bandit = LinUCBBandit(d=4, alpha=1.0)
        bandit._init_arm("arm_b")
        assert bandit.b["arm_b"] == [0.0] * 4

    def test_ucb_score_new_arm_with_zero_context(self):
        bandit = LinUCBBandit(d=3, alpha=1.0)
        score = bandit.ucb_score("new_arm", [0.0, 0.0, 0.0])
        # theta = A_inv @ b = I @ [0,0,0] = [0,0,0]; mean = 0
        # uncertainty = sqrt(ctx^T A_inv ctx) = 0 for zero ctx
        assert score == pytest.approx(0.0)

    def test_ucb_score_exploration_bonus(self):
        bandit = LinUCBBandit(d=3, alpha=2.0)
        # With identity A and zero b, score = 0 + alpha * sqrt(ctx^T ctx)
        ctx = [1.0, 0.0, 0.0]
        score = bandit.ucb_score("arm_a", ctx)
        # mean = 0, uncertainty = sqrt(1) = 1, so score = 2.0 * 1.0 = 2.0
        assert score == pytest.approx(2.0)

    def test_update_modifies_A_and_b(self):
        bandit = LinUCBBandit(d=2, alpha=1.0)
        bandit._init_arm("arm_a")
        bandit.update("arm_a", context=[1.0, 0.5], reward=1.0)
        # A should be I + x*x^T
        assert bandit.A["arm_a"][0][0] == pytest.approx(2.0)  # 1 + 1*1
        assert bandit.A["arm_a"][0][1] == pytest.approx(0.5)  # 0 + 1*0.5
        assert bandit.A["arm_a"][1][1] == pytest.approx(1.25)  # 1 + 0.5*0.5
        # b should be r*x
        assert bandit.b["arm_a"][0] == pytest.approx(1.0)
        assert bandit.b["arm_a"][1] == pytest.approx(0.5)

    def test_select_top_k_candidates(self):
        bandit = LinUCBBandit(d=3, alpha=1.0)
        candidates = [
            {"id": f"opp_{i}", "features": [float(i), 0.0, 0.0]}
            for i in range(15)
        ]
        selected = bandit.select_top_k(candidates, k=5)
        assert len(selected) == 5
        # All selected should be from the original candidates
        selected_ids = {c["id"] for c in selected}
        assert selected_ids.issubset({c["id"] for c in candidates})

    def test_learned_arm_scores_higher(self):
        """An arm that has been rewarded with positive context should score higher."""
        bandit = LinUCBBandit(d=3, alpha=0.5)
        ctx = [1.0, 1.0, 1.0]
        # Train arm_good with positive rewards
        for _ in range(10):
            bandit.update("arm_good", context=ctx, reward=1.0)

        score_good = bandit.ucb_score("arm_good", ctx)
        score_new = bandit.ucb_score("arm_new", ctx)
        assert score_good > score_new

    def test_serialization_roundtrip(self):
        bandit = LinUCBBandit(d=3, alpha=1.5)
        bandit.update("arm_1", [1.0, 0.0, 0.0], 1.0)
        data = bandit.to_dict()

        restored = LinUCBBandit.from_dict(data)
        assert restored.d == 3
        assert restored.alpha == 1.5
        assert restored.A == bandit.A
        assert restored.b == bandit.b

    def test_context_padding(self):
        """Short context vectors should be padded; long ones truncated."""
        bandit = LinUCBBandit(d=5, alpha=1.0)
        # Should not raise even with wrong-length context
        score = bandit.ucb_score("arm_a", [1.0, 2.0])  # too short
        assert isinstance(score, float)

        score2 = bandit.ucb_score("arm_b", [1.0] * 20)  # too long
        assert isinstance(score2, float)


# ── Math helpers ─────────────────────────────────────────────────────────────


class TestMathHelpers:
    def test_beta_sample_returns_bounded_value(self):
        random.seed(42)
        for _ in range(100):
            s = _beta_sample(2.0, 3.0)
            assert 0.0 <= s <= 1.0

    def test_beta_sample_fallback_on_bad_params(self):
        # Very small params should still work (clamped to 0.01 minimum)
        s = _beta_sample(0.0, 0.0)
        assert isinstance(s, float)
        assert 0.0 <= s <= 1.0

    def test_dot_product(self):
        assert _dot([1, 2, 3], [4, 5, 6]) == 32

    def test_mat_vec_mul(self):
        M = [[1, 0], [0, 1]]
        v = [3, 7]
        result = _mat_vec_mul(M, v)
        assert result == [3, 7]

    def test_pad_or_truncate_short(self):
        result = _pad_or_truncate([1.0, 2.0], 5)
        assert result == [1.0, 2.0, 0.0, 0.0, 0.0]

    def test_pad_or_truncate_long(self):
        result = _pad_or_truncate([1.0, 2.0, 3.0, 4.0], 2)
        assert result == [1.0, 2.0]

    def test_pad_or_truncate_exact(self):
        result = _pad_or_truncate([1.0, 2.0], 2)
        assert result == [1.0, 2.0]


# ── DailyOpportunitySelector ────────────────────────────────────────────────


class TestDailyOpportunitySelector:
    def test_returns_all_when_fewer_than_10(self):
        selector = DailyOpportunitySelector()
        candidates = [{"id": f"opp_{i}", "fit_score": 0.8, "features": []} for i in range(5)]
        result = selector.select_top_10(candidates)
        assert len(result) == 5

    def test_returns_10_from_30_candidates(self):
        selector = DailyOpportunitySelector()
        candidates = [
            {"id": f"opp_{i}", "fit_score": i / 30, "features": [float(i)] * 10}
            for i in range(30)
        ]
        result = selector.select_top_10(candidates, use_linucb=True)
        assert len(result) == 10

    def test_ts_fallback_when_no_features(self):
        selector = DailyOpportunitySelector()
        candidates = [
            {"id": f"opp_{i}", "fit_score": i / 30}
            for i in range(20)
        ]
        result = selector.select_top_10(candidates, use_linucb=True)
        # Should fall back to Thompson Sampling since no features
        assert len(result) == 10

    def test_record_outcome_updates_both_bandits(self):
        selector = DailyOpportunitySelector()
        features = [0.5] * 10
        selector.record_outcome("opp_1", features, reward=1.0)
        # TS bandit should have updated alpha
        assert selector.ts_bandit.alpha["opp_1"] == 2.0  # 1 (init) + 1 (reward)
        # LinUCB bandit should have updated A and b
        assert "opp_1" in selector.linucb_bandit.A

    def test_serialization_roundtrip(self):
        selector = DailyOpportunitySelector()
        selector.record_outcome("opp_1", [1.0] * 10, reward=1.0)
        selector.record_outcome("opp_2", [0.5] * 10, reward=0.0)
        data = selector.to_dict()

        restored = DailyOpportunitySelector.from_dict(data)
        assert restored.ts_bandit.alpha == selector.ts_bandit.alpha
        assert restored.linucb_bandit.d == selector.linucb_bandit.d


# ── opportunity_to_features ──────────────────────────────────────────────────


class TestOpportunityToFeatures:
    def test_returns_10_element_vector(self):
        opp = {"fit_score": 0.8, "strategic_score": 0.7, "estimated_value": 5_000_000}
        features = opportunity_to_features(opp)
        assert len(features) == 10

    def test_empty_opportunity_uses_defaults(self):
        features = opportunity_to_features({})
        assert len(features) == 10
        assert features[0] == 0.0  # fit_score default
        assert features[4] == 0.5  # competition_intensity default

    def test_estimated_value_normalized_to_millions(self):
        opp = {"estimated_value": 2_000_000}
        features = opportunity_to_features(opp)
        assert features[2] == pytest.approx(2.0)

    def test_set_aside_flag(self):
        opp_with = {"set_aside": "8(a)"}
        opp_without = {"set_aside": None}
        assert opportunity_to_features(opp_with)[3] == 1.0
        assert opportunity_to_features(opp_without)[3] == 0.0

    def test_days_to_deadline_normalized(self):
        opp = {"days_to_deadline": 15}
        features = opportunity_to_features(opp)
        assert features[7] == pytest.approx(0.5)  # 15/30
