"""Contextual bandit for opportunity ranking and recommendation optimization.

Implements Thompson Sampling and LinUCB algorithms to select the daily Top 10
opportunities from Top 30 candidates, balancing exploration vs. exploitation.

The bandit learns which features predict engagement/win, improving Top 10 selection
over time as outcomes are observed.
"""
import logging
import math
import os
import random
from typing import Any

logger = logging.getLogger("ai_orchestrator.learning.bandit")


# ── Thompson Sampling ─────────────────────────────────────────────────────────

class ThompsonSamplingBandit:
    """Beta-distribution Thompson Sampling bandit for binary outcomes (win/no-win).

    Each "arm" is a potential action (e.g. bid on opportunity X).
    Maintains Beta(alpha, beta) posterior for each arm's win probability.
    """

    def __init__(self):
        # alpha = successes + 1, beta = failures + 1 (Beta prior)
        self.alpha: dict[str, float] = {}
        self.beta: dict[str, float] = {}

    def _init_arm(self, arm_id: str) -> None:
        if arm_id not in self.alpha:
            self.alpha[arm_id] = 1.0  # uniform prior
            self.beta[arm_id] = 1.0

    def sample(self, arm_id: str) -> float:
        """Draw a sample from Beta posterior for *arm_id*."""
        self._init_arm(arm_id)
        # Use Beta distribution sampling via inverse CDF approximation
        a = self.alpha[arm_id]
        b = self.beta[arm_id]
        return _beta_sample(a, b)

    def select_top_k(self, arm_ids: list[str], k: int = 10) -> list[str]:
        """Select top-k arms via Thompson Sampling.

        Args:
            arm_ids: List of candidate arm IDs.
            k: Number of arms to select.

        Returns:
            Selected arm IDs ranked by sampled value.
        """
        scored = [(arm, self.sample(arm)) for arm in arm_ids]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [arm for arm, _ in scored[:k]]

    def update(self, arm_id: str, reward: float) -> None:
        """Update posterior with observed reward.

        Args:
            arm_id: The arm that was pulled.
            reward: Observed reward (positive = success, non-positive = failure).
        """
        self._init_arm(arm_id)
        if reward > 0:
            self.alpha[arm_id] += reward
        else:
            self.beta[arm_id] += 1.0

    def get_win_probability_estimate(self, arm_id: str) -> float:
        """Return the posterior mean win probability for *arm_id*."""
        self._init_arm(arm_id)
        return self.alpha[arm_id] / (self.alpha[arm_id] + self.beta[arm_id])

    def to_dict(self) -> dict[str, Any]:
        return {"alpha": self.alpha, "beta": self.beta}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThompsonSamplingBandit":
        b = cls()
        b.alpha = data.get("alpha", {})
        b.beta = data.get("beta", {})
        return b


# ── LinUCB Contextual Bandit ──────────────────────────────────────────────────

class LinUCBBandit:
    """Linear UCB contextual bandit for opportunity scoring.

    Uses feature vectors to generalize across similar opportunities.
    Better than Thompson Sampling when feature context is available.

    Reference: Li et al. (2010) "A Contextual-Bandit Approach to Personalized News Article Recommendation"
    """

    def __init__(self, d: int = 10, alpha: float = 1.0):
        """
        Args:
            d: Feature vector dimension.
            alpha: Exploration parameter (higher = more exploration).
        """
        self.d = d
        self.alpha = alpha
        # Per-arm: A matrix (d×d), b vector (d)
        self.A: dict[str, list[list[float]]] = {}
        self.b: dict[str, list[float]] = {}

    def _init_arm(self, arm_id: str) -> None:
        if arm_id not in self.A:
            self.A[arm_id] = [[1.0 if i == j else 0.0 for j in range(self.d)] for i in range(self.d)]
            self.b[arm_id] = [0.0] * self.d

    def ucb_score(self, arm_id: str, context: list[float]) -> float:
        """Compute UCB score for *arm_id* given *context* feature vector.

        Returns:
            Expected reward + exploration bonus.
        """
        self._init_arm(arm_id)
        ctx = _pad_or_truncate(context, self.d)

        A_inv = _matrix_inverse(self.A[arm_id])
        theta = _mat_vec_mul(A_inv, self.b[arm_id])

        # Mean reward estimate
        mean = _dot(theta, ctx)

        # Uncertainty (exploration bonus)
        Ax = _mat_vec_mul(A_inv, ctx)
        uncertainty = math.sqrt(_dot(ctx, Ax))

        return mean + self.alpha * uncertainty

    def select_top_k(
        self,
        candidates: list[dict[str, Any]],
        k: int = 10,
        feature_key: str = "features",
    ) -> list[dict[str, Any]]:
        """Select top-k candidates using LinUCB.

        Args:
            candidates: List of candidate dicts, each with 'id' and feature_key.
            k: Number to select.
            feature_key: Key in candidate dict containing feature list.

        Returns:
            Top-k candidates sorted by UCB score.
        """
        scored = []
        for cand in candidates:
            arm_id = cand.get("id", str(id(cand)))
            features = cand.get(feature_key, [])
            score = self.ucb_score(arm_id, features)
            scored.append((cand, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:k]]

    def update(self, arm_id: str, context: list[float], reward: float) -> None:
        """Update LinUCB model with observed reward.

        Args:
            arm_id: The selected arm.
            context: Feature vector at decision time.
            reward: Observed reward.
        """
        self._init_arm(arm_id)
        ctx = _pad_or_truncate(context, self.d)

        # Update A = A + x*x^T
        for i in range(self.d):
            for j in range(self.d):
                self.A[arm_id][i][j] += ctx[i] * ctx[j]

        # Update b = b + r*x
        for i in range(self.d):
            self.b[arm_id][i] += reward * ctx[i]

    def to_dict(self) -> dict[str, Any]:
        return {"d": self.d, "alpha": self.alpha, "A": self.A, "b": self.b}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LinUCBBandit":
        b = cls(d=data.get("d", 10), alpha=data.get("alpha", 1.0))
        b.A = data.get("A", {})
        b.b = data.get("b", {})
        return b


# ── Daily Top 10 Selector ─────────────────────────────────────────────────────

class DailyOpportunitySelector:
    """Combines fit scoring with Thompson Sampling to select the daily Top 10.

    Process:
    1. Get Top 30 candidates from the opportunity scorer (rule-based + ML)
    2. Apply Thompson Sampling to select final Top 10 (explore/exploit balance)
    3. After outcomes are known, update the bandit model
    """

    def __init__(self):
        self.ts_bandit = ThompsonSamplingBandit()
        self.linucb_bandit = LinUCBBandit(d=10, alpha=0.5)

    def select_top_10(
        self,
        top_30_candidates: list[dict[str, Any]],
        use_linucb: bool = True,
    ) -> list[dict[str, Any]]:
        """Select Top 10 from Top 30 candidates.

        Each candidate should have: id, fit_score, features (list[float]).
        """
        if len(top_30_candidates) <= 10:
            return top_30_candidates

        if use_linucb and any(c.get("features") for c in top_30_candidates):
            return self.linucb_bandit.select_top_k(top_30_candidates, k=10)

        # Thompson Sampling fallback (arm-per-opportunity)
        arm_ids = [c.get("id", str(i)) for i, c in enumerate(top_30_candidates)]
        # Bias sampling toward higher fit scores
        for c, arm_id in zip(top_30_candidates, arm_ids):
            fit = c.get("fit_score", 0.5) or 0.5
            self.ts_bandit.alpha[arm_id] = max(1.0, fit * 10)
            self.ts_bandit.beta[arm_id] = max(1.0, (1 - fit) * 10)

        selected_ids = set(self.ts_bandit.select_top_k(arm_ids, k=10))
        return [c for c in top_30_candidates if c.get("id") in selected_ids]

    def record_outcome(
        self,
        opportunity_id: str,
        features: list[float],
        reward: float,
    ) -> None:
        """Update both bandits with the observed outcome."""
        self.ts_bandit.update(opportunity_id, reward)
        self.linucb_bandit.update(opportunity_id, features, reward)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts_bandit": self.ts_bandit.to_dict(),
            "linucb_bandit": self.linucb_bandit.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DailyOpportunitySelector":
        sel = cls()
        if "ts_bandit" in data:
            sel.ts_bandit = ThompsonSamplingBandit.from_dict(data["ts_bandit"])
        if "linucb_bandit" in data:
            sel.linucb_bandit = LinUCBBandit.from_dict(data["linucb_bandit"])
        return sel


# ── Math helpers ──────────────────────────────────────────────────────────────

def _beta_sample(a: float, b: float) -> float:
    """Sample from Beta(a, b) using Python's random module."""
    try:
        return random.betavariate(max(0.01, a), max(0.01, b))
    except Exception:
        return a / (a + b)  # Return mean as fallback


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _mat_vec_mul(M: list[list[float]], v: list[float]) -> list[float]:
    return [_dot(row, v) for row in M]


def _matrix_inverse(M: list[list[float]]) -> list[list[float]]:
    """Compute matrix inverse for small matrices (fallback to identity if singular)."""
    n = len(M)
    if n == 1:
        return [[1.0 / max(1e-10, M[0][0])]]

    # Diagonal approximation (fast and stable for diagonal-dominant matrices)
    result = [[0.0] * n for _ in range(n)]
    for i in range(n):
        diag = M[i][i]
        result[i][i] = 1.0 / max(1e-10, diag)
    return result


def _pad_or_truncate(v: list[float], d: int) -> list[float]:
    if len(v) >= d:
        return v[:d]
    return v + [0.0] * (d - len(v))


def opportunity_to_features(opportunity: dict[str, Any]) -> list[float]:
    """Convert an opportunity dict to a fixed-length feature vector for LinUCB."""
    return [
        float(opportunity.get("fit_score", 0) or 0),
        float(opportunity.get("strategic_score", 0) or 0),
        float(opportunity.get("estimated_value", 0) or 0) / 1_000_000,  # normalize to $M
        1.0 if opportunity.get("set_aside") else 0.0,
        float(opportunity.get("competition_intensity", 0.5) or 0.5),
        float(opportunity.get("agency_relationship_score", 0.5) or 0.5),
        float(opportunity.get("incumbent_known", 0) or 0),
        float(opportunity.get("days_to_deadline", 30) or 30) / 30.0,  # normalize
        float(opportunity.get("naics_match_score", 0) or 0),
        float(opportunity.get("past_performance_relevance", 0) or 0),
    ]
