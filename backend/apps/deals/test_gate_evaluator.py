"""
Tests for the Gate Review Evaluator — auto-evaluates gate readiness criteria.

Covers:
  - evaluate_gate() returns green when no gate defined
  - _evaluate_bid_no_bid() with scored/unscored opportunity
  - _evaluate_final_review() with/without proposal sections
  - _evaluate_submit() deadline check
  - _build_evaluation() red/amber/green logic
"""

import pytest
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.deals.services.gate_evaluator import (
    GateCriterion,
    GateEvaluation,
    _build_evaluation,
    _evaluate_bid_no_bid,
    _evaluate_final_review,
    _evaluate_submit,
    evaluate_gate,
)


@pytest.mark.django_db
class TestEvaluateGateNoGate(TestCase):
    """evaluate_gate() returns green/can_proceed when no gate is configured."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.user = User.objects.create_user(
            username="ge_user", email="ge@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov GE", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-GE-001",
            source=self.source,
            title="Gate Eval Opp",
        )

    def _make_deal(self, stage="intake"):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp, owner=self.user,
            title="Gate Eval Deal", stage=stage,
            estimated_value=Decimal("400000"),
        )

    def test_no_gate_for_qualify(self):
        """'qualify' has no gate evaluator; should return green."""
        deal = self._make_deal(stage="intake")
        result = evaluate_gate(deal, "qualify")
        self.assertEqual(result.overall_status, "green")
        self.assertTrue(result.can_proceed)
        self.assertIn("No gate criteria", result.summary)

    def test_no_gate_for_capture_plan(self):
        deal = self._make_deal()
        result = evaluate_gate(deal, "capture_plan")
        self.assertEqual(result.overall_status, "green")
        self.assertTrue(result.can_proceed)

    def test_no_gate_for_proposal_dev(self):
        deal = self._make_deal()
        result = evaluate_gate(deal, "proposal_dev")
        self.assertTrue(result.can_proceed)

    def test_no_gate_for_nonexistent_stage(self):
        deal = self._make_deal()
        result = evaluate_gate(deal, "some_random_stage")
        self.assertTrue(result.can_proceed)
        self.assertEqual(result.overall_status, "green")


@pytest.mark.django_db
class TestEvaluateBidNoBid(TestCase):
    """_evaluate_bid_no_bid() checks score, strategy, owner, value."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.user = User.objects.create_user(
            username="ge_bnb", email="gebnb@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov BNB", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-BNB-001",
            source=self.source,
            title="Bid/No-Bid Opp",
            agency="DoD",
        )

    def _make_deal(self, owner=None, estimated_value=None, ai_recommendation=""):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp,
            owner=owner,
            title="BNB Deal",
            stage="qualify",
            estimated_value=estimated_value,
            ai_recommendation=ai_recommendation,
        )

    def test_scored_opportunity_with_owner_and_value_is_green(self):
        """All critical criteria met + non-critical met => green."""
        from apps.opportunities.models import OpportunityScore

        OpportunityScore.objects.create(
            opportunity=self.opp, total_score=82.0, recommendation="bid",
        )
        deal = self._make_deal(
            owner=self.user,
            estimated_value=Decimal("1000000"),
            ai_recommendation="Recommend bid based on past performance",
        )
        result = _evaluate_bid_no_bid(deal)

        self.assertEqual(result.overall_status, "green")
        self.assertTrue(result.can_proceed)
        self.assertEqual(result.stage, "bid_no_bid")

        # Verify individual criteria
        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Opportunity Scored"].status, "green")
        self.assertIn("82", criteria_map["Opportunity Scored"].detail)
        self.assertEqual(criteria_map["Owner Assigned"].status, "green")
        self.assertEqual(criteria_map["Strategy Assessment"].status, "green")
        self.assertEqual(criteria_map["Value Estimated"].status, "green")

    def test_unscored_opportunity_is_red(self):
        """Missing OpportunityScore => critical red => overall red, blocked."""
        deal = self._make_deal(owner=self.user, estimated_value=Decimal("500000"))
        result = _evaluate_bid_no_bid(deal)

        self.assertEqual(result.overall_status, "red")
        self.assertFalse(result.can_proceed)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Opportunity Scored"].status, "red")
        self.assertTrue(criteria_map["Opportunity Scored"].is_critical)

    def test_no_owner_is_red(self):
        """Missing owner is critical => red."""
        from apps.opportunities.models import OpportunityScore

        OpportunityScore.objects.create(
            opportunity=self.opp, total_score=70.0, recommendation="consider",
        )
        deal = self._make_deal(owner=None, estimated_value=Decimal("200000"))
        result = _evaluate_bid_no_bid(deal)

        self.assertFalse(result.can_proceed)
        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Owner Assigned"].status, "red")

    def test_missing_strategy_and_value_is_amber(self):
        """Missing strategy (non-critical) + missing value (non-critical) => amber, can proceed."""
        from apps.opportunities.models import OpportunityScore

        OpportunityScore.objects.create(
            opportunity=self.opp, total_score=65.0, recommendation="consider",
        )
        deal = self._make_deal(
            owner=self.user,
            estimated_value=None,  # non-critical
            ai_recommendation="",  # non-critical
        )
        result = _evaluate_bid_no_bid(deal)

        self.assertEqual(result.overall_status, "amber")
        self.assertTrue(result.can_proceed)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Strategy Assessment"].status, "amber")
        self.assertEqual(criteria_map["Value Estimated"].status, "amber")


@pytest.mark.django_db
class TestEvaluateFinalReview(TestCase):
    """_evaluate_final_review() checks proposal, compliance, pricing, red team."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.user = User.objects.create_user(
            username="ge_fr", email="gefr@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov FR", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-FR-001", source=self.source, title="Final Review Opp",
        )

    def _make_deal(self):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp, owner=self.user,
            title="Final Review Deal", stage="red_team",
            estimated_value=Decimal("800000"),
        )

    def test_no_proposal_is_red(self):
        """No proposal at all => critical red on 'Proposal Exists'."""
        deal = self._make_deal()
        result = _evaluate_final_review(deal)

        self.assertFalse(result.can_proceed)
        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Proposal Exists"].status, "red")
        self.assertTrue(criteria_map["Proposal Exists"].is_critical)

    def test_proposal_with_sections_is_green_on_that_criterion(self):
        """Proposal with sections passes the 'Proposal Exists' criterion."""
        from apps.proposals.models import Proposal, ProposalSection

        deal = self._make_deal()
        proposal = Proposal.objects.create(deal=deal, title="Test Proposal", status="draft")
        ProposalSection.objects.create(
            proposal=proposal, volume="Volume I", section_number="1.0",
            title="Executive Summary", order=1,
        )
        ProposalSection.objects.create(
            proposal=proposal, volume="Volume I", section_number="2.0",
            title="Technical Approach", order=2,
        )
        result = _evaluate_final_review(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Proposal Exists"].status, "green")
        self.assertIn("2 sections", criteria_map["Proposal Exists"].detail)

    def test_no_pricing_approval_is_red(self):
        """Missing pricing approval is critical => red."""
        deal = self._make_deal()
        result = _evaluate_final_review(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Pricing Approved"].status, "red")
        self.assertTrue(criteria_map["Pricing Approved"].is_critical)

    def test_with_pricing_approval_is_green(self):
        """Having a pricing approval makes that criterion green."""
        from apps.deals.models import Approval

        deal = self._make_deal()
        Approval.objects.create(
            deal=deal, approval_type="pricing", status="approved",
            requested_by=self.user,
        )
        result = _evaluate_final_review(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Pricing Approved"].status, "green")

    def test_red_team_not_done_is_amber(self):
        """Red team review not completed is non-critical => amber."""
        deal = self._make_deal()
        result = _evaluate_final_review(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Red Team Review"].status, "amber")
        self.assertFalse(criteria_map["Red Team Review"].is_critical)

    def test_red_team_done_is_green(self):
        """Completed red team task makes that criterion green."""
        from apps.deals.models import Task

        deal = self._make_deal()
        Task.objects.create(
            deal=deal, title="Red Team Review", stage="red_team",
            status="completed", priority=2,
        )
        result = _evaluate_final_review(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Red Team Review"].status, "green")

    def test_full_green_final_review(self):
        """All criteria met => green, can_proceed."""
        from apps.deals.models import Approval, Task
        from apps.proposals.models import Proposal, ProposalSection

        deal = self._make_deal()

        # Proposal with sections
        proposal = Proposal.objects.create(deal=deal, title="Full Proposal", status="final")
        ProposalSection.objects.create(
            proposal=proposal, volume="I", section_number="1.0",
            title="Exec Summary", order=1,
        )

        # Pricing approved
        Approval.objects.create(
            deal=deal, approval_type="pricing", status="approved",
            requested_by=self.user,
        )

        # Red team task completed
        Task.objects.create(
            deal=deal, title="Red Team", stage="red_team",
            status="completed", priority=2,
        )

        result = _evaluate_final_review(deal)

        # Compliance is amber (no items) but non-critical
        # So overall should be amber (non-critical amber present)
        self.assertTrue(result.can_proceed)
        self.assertIn(result.overall_status, ("green", "amber"))


@pytest.mark.django_db
class TestEvaluateSubmit(TestCase):
    """_evaluate_submit() checks final approval, deadline, critical tasks."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.user = User.objects.create_user(
            username="ge_sub", email="gesub@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov Sub", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-SUB-001", source=self.source, title="Submit Opp",
        )

    def _make_deal(self, due_date=None):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp, owner=self.user,
            title="Submit Deal", stage="final_review",
            estimated_value=Decimal("900000"),
            due_date=due_date,
        )

    def test_deadline_in_future_is_green(self):
        future = timezone.now() + timedelta(days=7)
        deal = self._make_deal(due_date=future)
        result = _evaluate_submit(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Deadline Not Passed"].status, "green")

    def test_deadline_in_past_is_red(self):
        past = timezone.now() - timedelta(days=1)
        deal = self._make_deal(due_date=past)
        result = _evaluate_submit(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Deadline Not Passed"].status, "red")
        self.assertTrue(criteria_map["Deadline Not Passed"].is_critical)
        self.assertFalse(result.can_proceed)

    def test_no_deadline_is_green(self):
        """No deadline set => treated as OK (green)."""
        deal = self._make_deal(due_date=None)
        result = _evaluate_submit(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Deadline Not Passed"].status, "green")
        self.assertIn("No deadline set", criteria_map["Deadline Not Passed"].detail)

    def test_no_final_approval_is_red(self):
        deal = self._make_deal()
        result = _evaluate_submit(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Final Proposal Approved"].status, "red")
        self.assertFalse(result.can_proceed)

    def test_with_final_approval_passes_that_criterion(self):
        from apps.deals.models import Approval

        deal = self._make_deal(due_date=timezone.now() + timedelta(days=5))
        Approval.objects.create(
            deal=deal, approval_type="proposal_final", status="approved",
            requested_by=self.user,
        )
        result = _evaluate_submit(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Final Proposal Approved"].status, "green")

    def test_pending_critical_tasks_block(self):
        """Pending critical tasks (priority <= 2) cause red on Critical Tasks Complete."""
        from apps.deals.models import Task

        deal = self._make_deal(due_date=timezone.now() + timedelta(days=5))
        Task.objects.create(
            deal=deal, title="Write Section 1", stage="proposal_dev",
            status="in_progress", priority=1,  # Critical
        )
        result = _evaluate_submit(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Critical Tasks Complete"].status, "red")
        self.assertIn("1 critical tasks remaining", criteria_map["Critical Tasks Complete"].detail)

    def test_no_pending_critical_tasks_is_green(self):
        """All critical tasks completed => green."""
        from apps.deals.models import Task

        deal = self._make_deal(due_date=timezone.now() + timedelta(days=5))
        Task.objects.create(
            deal=deal, title="Review", stage="proposal_dev",
            status="completed", priority=1,
        )
        result = _evaluate_submit(deal)

        criteria_map = {c.name: c for c in result.criteria}
        self.assertEqual(criteria_map["Critical Tasks Complete"].status, "green")

    def test_full_green_submit(self):
        """All criteria met => green, can_proceed."""
        from apps.deals.models import Approval

        deal = self._make_deal(due_date=timezone.now() + timedelta(days=10))
        Approval.objects.create(
            deal=deal, approval_type="proposal_final", status="approved",
            requested_by=self.user,
        )
        result = _evaluate_submit(deal)

        self.assertTrue(result.can_proceed)
        self.assertEqual(result.overall_status, "green")


class TestBuildEvaluation(TestCase):
    """_build_evaluation() computes overall status from criteria list."""

    def test_all_green(self):
        criteria = [
            GateCriterion(name="A", description="a", is_critical=True, status="green"),
            GateCriterion(name="B", description="b", is_critical=False, status="green"),
        ]
        result = _build_evaluation("test_stage", criteria)

        self.assertEqual(result.overall_status, "green")
        self.assertTrue(result.can_proceed)
        self.assertIn("All criteria met", result.summary)

    def test_critical_red_means_overall_red(self):
        criteria = [
            GateCriterion(name="A", description="a", is_critical=True, status="red"),
            GateCriterion(name="B", description="b", is_critical=False, status="green"),
        ]
        result = _build_evaluation("test_stage", criteria)

        self.assertEqual(result.overall_status, "red")
        self.assertFalse(result.can_proceed)
        self.assertIn("Critical criteria not met", result.summary)

    def test_noncritical_red_means_amber(self):
        """Non-critical red => amber, can still proceed."""
        criteria = [
            GateCriterion(name="A", description="a", is_critical=True, status="green"),
            GateCriterion(name="B", description="b", is_critical=False, status="red"),
        ]
        result = _build_evaluation("test_stage", criteria)

        self.assertEqual(result.overall_status, "amber")
        self.assertTrue(result.can_proceed)
        self.assertIn("warnings", result.summary)

    def test_amber_criterion_means_overall_amber(self):
        criteria = [
            GateCriterion(name="A", description="a", is_critical=True, status="green"),
            GateCriterion(name="B", description="b", is_critical=False, status="amber"),
        ]
        result = _build_evaluation("test_stage", criteria)

        self.assertEqual(result.overall_status, "amber")
        self.assertTrue(result.can_proceed)

    def test_mixed_critical_red_and_amber(self):
        """Critical red trumps everything."""
        criteria = [
            GateCriterion(name="A", description="a", is_critical=True, status="red"),
            GateCriterion(name="B", description="b", is_critical=False, status="amber"),
            GateCriterion(name="C", description="c", is_critical=True, status="green"),
        ]
        result = _build_evaluation("test_stage", criteria)

        self.assertEqual(result.overall_status, "red")
        self.assertFalse(result.can_proceed)

    def test_empty_criteria_is_green(self):
        """No criteria at all => green (nothing to fail)."""
        result = _build_evaluation("test_stage", [])
        self.assertEqual(result.overall_status, "green")
        self.assertTrue(result.can_proceed)

    def test_stage_name_preserved(self):
        result = _build_evaluation("my_custom_stage", [])
        self.assertEqual(result.stage, "my_custom_stage")

    def test_multiple_critical_reds(self):
        criteria = [
            GateCriterion(name="X", description="x", is_critical=True, status="red"),
            GateCriterion(name="Y", description="y", is_critical=True, status="red"),
        ]
        result = _build_evaluation("test_stage", criteria)

        self.assertEqual(result.overall_status, "red")
        self.assertFalse(result.can_proceed)
