"""
Tests for the WorkflowEngine — deal pipeline stage transitions.

Covers:
  - can_transition() valid and invalid transitions
  - Gate evaluation blocking (critical criteria block, amber allows)
  - HITL approval requirements
  - transition() happy path
  - transition() side-effects: stage_orchestrator, signals, velocity recording
  - transition() creates DealStageHistory and Activity records
"""

import pytest
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from apps.deals.workflow import WorkflowEngine, VALID_TRANSITIONS, HITL_GATES
from apps.deals.services.gate_evaluator import GateEvaluation, GateCriterion


@pytest.mark.django_db
class TestCanTransitionValid(TestCase):
    """WorkflowEngine.can_transition() with valid stage pairs."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.engine = WorkflowEngine()
        self.user = User.objects.create_user(
            username="wf_user", email="wf@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-WF-001",
            source=self.source,
            title="Test Opportunity",
            agency="DoD",
            naics_code="541512",
        )

    def _make_deal(self, stage="intake", **kwargs):
        from apps.deals.models import Deal

        defaults = dict(
            opportunity=self.opp,
            owner=self.user,
            title="Test Deal",
            stage=stage,
            estimated_value=Decimal("500000"),
            ai_recommendation="Recommend bid",
        )
        defaults.update(kwargs)
        return Deal.objects.create(**defaults)

    # ── Valid transitions without HITL gates ─────────────────────────────

    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_intake_to_qualify_is_valid(self, mock_gate):
        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green", can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        ok, msg = self.engine.can_transition(deal, "qualify")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_intake_to_no_bid_is_valid(self, mock_gate):
        mock_gate.return_value = GateEvaluation(
            stage="no_bid", overall_status="green", can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        ok, msg = self.engine.can_transition(deal, "no_bid")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_capture_plan_to_proposal_dev_is_valid(self, mock_gate):
        mock_gate.return_value = GateEvaluation(
            stage="proposal_dev", overall_status="green", can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="capture_plan")
        ok, msg = self.engine.can_transition(deal, "proposal_dev")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_red_team_can_loop_back_to_proposal_dev(self, mock_gate):
        """Red team review can loop back to proposal_dev."""
        mock_gate.return_value = GateEvaluation(
            stage="proposal_dev", overall_status="green", can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="red_team")
        ok, msg = self.engine.can_transition(deal, "proposal_dev")
        self.assertTrue(ok)

    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_post_submit_to_award_pending(self, mock_gate):
        mock_gate.return_value = GateEvaluation(
            stage="award_pending", overall_status="green", can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="post_submit")
        ok, msg = self.engine.can_transition(deal, "award_pending")
        self.assertTrue(ok)


@pytest.mark.django_db
class TestCanTransitionInvalid(TestCase):
    """WorkflowEngine.can_transition() with invalid stage pairs."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.engine = WorkflowEngine()
        self.user = User.objects.create_user(
            username="wf_inv", email="wfinv@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov Inv", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-WF-INV-001",
            source=self.source,
            title="Invalid Transition Opp",
        )

    def _make_deal(self, stage="intake"):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp,
            owner=self.user,
            title="Invalid Deal",
            stage=stage,
            estimated_value=Decimal("100000"),
        )

    def test_intake_cannot_jump_to_proposal_dev(self):
        deal = self._make_deal(stage="intake")
        ok, msg = self.engine.can_transition(deal, "proposal_dev")
        self.assertFalse(ok)
        self.assertIn("Cannot transition", msg)
        self.assertIn("proposal_dev", msg)

    def test_submit_cannot_go_to_intake(self):
        deal = self._make_deal(stage="submit")
        ok, msg = self.engine.can_transition(deal, "intake")
        self.assertFalse(ok)
        self.assertIn("Cannot transition", msg)

    def test_delivery_cannot_go_to_proposal_dev(self):
        deal = self._make_deal(stage="delivery")
        ok, msg = self.engine.can_transition(deal, "proposal_dev")
        self.assertFalse(ok)

    def test_closed_won_is_terminal(self):
        """closed_won has no valid outgoing transitions."""
        deal = self._make_deal(stage="closed_won")
        ok, msg = self.engine.can_transition(deal, "delivery")
        self.assertFalse(ok)

    def test_nonexistent_stage(self):
        deal = self._make_deal(stage="intake")
        ok, msg = self.engine.can_transition(deal, "fantasy_stage")
        self.assertFalse(ok)
        self.assertIn("Cannot transition", msg)


@pytest.mark.django_db
class TestHITLApprovalGating(TestCase):
    """HITL approval requirements block transitions to gated stages."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource, OpportunityScore

        self.engine = WorkflowEngine()
        self.user = User.objects.create_user(
            username="wf_hitl", email="hitl@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov HITL", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-HITL-001",
            source=self.source,
            title="HITL Opp",
            agency="DoD",
        )
        # Create score so the bid_no_bid gate evaluator finds one
        OpportunityScore.objects.create(
            opportunity=self.opp,
            total_score=75.0,
            recommendation="bid",
        )

    def _make_deal(self, stage="qualify"):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp,
            owner=self.user,
            title="HITL Deal",
            stage=stage,
            estimated_value=Decimal("1000000"),
            ai_recommendation="Recommend bid",
        )

    def test_bid_no_bid_blocked_without_approval(self):
        """bid_no_bid is in HITL_GATES; no approval record => blocked."""
        deal = self._make_deal(stage="qualify")
        ok, msg = self.engine.can_transition(deal, "bid_no_bid")
        self.assertFalse(ok)
        self.assertIn("HITL approval", msg)

    def test_bid_no_bid_allowed_with_pending_approval(self):
        """A pending approval record is enough to pass the HITL check (gate eval decides)."""
        from apps.deals.models import Approval

        deal = self._make_deal(stage="qualify")
        Approval.objects.create(
            deal=deal,
            approval_type="bid_no_bid",
            status="pending",
            requested_by=self.user,
        )
        # Gate evaluator still needs to pass; mock it green
        with patch("apps.deals.services.gate_evaluator.evaluate_gate") as mock_gate:
            mock_gate.return_value = GateEvaluation(
                stage="bid_no_bid", overall_status="green",
                can_proceed=True, summary="OK"
            )
            ok, msg = self.engine.can_transition(deal, "bid_no_bid")
            self.assertTrue(ok)

    def test_bid_no_bid_allowed_with_approved_approval(self):
        from apps.deals.models import Approval

        deal = self._make_deal(stage="qualify")
        Approval.objects.create(
            deal=deal,
            approval_type="bid_no_bid",
            status="approved",
            requested_by=self.user,
        )
        with patch("apps.deals.services.gate_evaluator.evaluate_gate") as mock_gate:
            mock_gate.return_value = GateEvaluation(
                stage="bid_no_bid", overall_status="green",
                can_proceed=True, summary="OK"
            )
            ok, msg = self.engine.can_transition(deal, "bid_no_bid")
            self.assertTrue(ok)

    def test_final_review_blocked_without_approval(self):
        """final_review is gated; no approval => blocked."""
        deal = self._make_deal(stage="red_team")
        ok, msg = self.engine.can_transition(deal, "final_review")
        self.assertFalse(ok)
        self.assertIn("HITL approval", msg)

    def test_non_hitl_stage_does_not_require_approval(self):
        """capture_plan is NOT a HITL gate — no approval needed."""
        self.assertNotIn("capture_plan", HITL_GATES)
        deal = self._make_deal(stage="qualify")
        # capture_plan is not a valid target from qualify anyway;
        # test from bid_no_bid which can go to capture_plan
        deal.stage = "bid_no_bid"
        deal.save(update_fields=["stage"])

        # Need to pass HITL for bid_no_bid first, but we're going TO capture_plan
        with patch("apps.deals.services.gate_evaluator.evaluate_gate") as mock_gate:
            mock_gate.return_value = GateEvaluation(
                stage="capture_plan", overall_status="green",
                can_proceed=True, summary="OK"
            )
            ok, msg = self.engine.can_transition(deal, "capture_plan")
            self.assertTrue(ok)


@pytest.mark.django_db
class TestGateEvaluationBlocking(TestCase):
    """Gate evaluation with critical red criteria blocks the transition."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.engine = WorkflowEngine()
        self.user = User.objects.create_user(
            username="wf_gate", email="gate@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov Gate", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-GATE-001",
            source=self.source,
            title="Gate Opp",
        )

    def _make_deal(self, stage="qualify"):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp,
            owner=self.user,
            title="Gate Deal",
            stage=stage,
            estimated_value=Decimal("250000"),
        )

    def test_critical_red_criterion_blocks_transition(self):
        """A critical criterion with status=red blocks can_transition."""
        deal = self._make_deal(stage="qualify")
        # Provide HITL approval so we get past that check
        from apps.deals.models import Approval
        Approval.objects.create(
            deal=deal, approval_type="bid_no_bid", status="approved",
            requested_by=self.user,
        )

        red_eval = GateEvaluation(
            stage="bid_no_bid",
            overall_status="red",
            can_proceed=False,
            summary="Critical criteria not met. Cannot proceed.",
            criteria=[
                GateCriterion(
                    name="Opportunity Scored",
                    description="Must be scored",
                    is_critical=True,
                    status="red",
                    detail="Not scored yet",
                ),
            ],
        )
        with patch("apps.deals.services.gate_evaluator.evaluate_gate", return_value=red_eval):
            ok, msg = self.engine.can_transition(deal, "bid_no_bid")
            self.assertFalse(ok)
            self.assertIn("Gate criteria not met", msg)
            self.assertIn("Opportunity Scored", msg)

    def test_amber_allows_transition(self):
        """Amber (non-critical warnings) allow the transition to proceed."""
        deal = self._make_deal(stage="qualify")
        from apps.deals.models import Approval
        Approval.objects.create(
            deal=deal, approval_type="bid_no_bid", status="approved",
            requested_by=self.user,
        )

        amber_eval = GateEvaluation(
            stage="bid_no_bid",
            overall_status="amber",
            can_proceed=True,
            summary="Some criteria have warnings.",
            criteria=[
                GateCriterion(
                    name="Opportunity Scored", description="Scored",
                    is_critical=True, status="green", detail="Score: 82",
                ),
                GateCriterion(
                    name="Strategy Assessment", description="AI rec",
                    is_critical=False, status="amber",
                    detail="No AI recommendation yet",
                ),
            ],
        )
        with patch("apps.deals.services.gate_evaluator.evaluate_gate", return_value=amber_eval):
            ok, msg = self.engine.can_transition(deal, "bid_no_bid")
            self.assertTrue(ok)
            self.assertEqual(msg, "")


@pytest.mark.django_db
class TestTransitionHappyPath(TestCase):
    """WorkflowEngine.transition() end-to-end happy path."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.engine = WorkflowEngine()
        self.user = User.objects.create_user(
            username="wf_trans", email="trans@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov Trans", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-TRANS-001",
            source=self.source,
            title="Transition Opp",
            agency="DoD",
        )

    def _make_deal(self, stage="intake"):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp,
            owner=self.user,
            title="Transition Deal",
            stage=stage,
            estimated_value=Decimal("750000"),
            ai_recommendation="Go",
        )

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_transition_intake_to_qualify(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        old_entered_at = deal.stage_entered_at

        result = self.engine.transition(deal, "qualify", user=self.user, reason="Looks good")

        self.assertTrue(result)

        # Deal stage updated
        deal.refresh_from_db()
        self.assertEqual(deal.stage, "qualify")
        self.assertGreaterEqual(deal.stage_entered_at, old_entered_at)

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_transition_creates_history_record(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        from apps.deals.models import DealStageHistory

        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        self.engine.transition(deal, "qualify", user=self.user, reason="Moving forward")

        history = DealStageHistory.objects.filter(deal=deal)
        self.assertEqual(history.count(), 1)
        entry = history.first()
        self.assertEqual(entry.from_stage, "intake")
        self.assertEqual(entry.to_stage, "qualify")
        self.assertEqual(entry.transitioned_by, self.user)
        self.assertEqual(entry.reason, "Moving forward")
        self.assertIsNotNone(entry.duration_in_previous_stage)

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_transition_creates_activity_record(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        from apps.deals.models import Activity

        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        self.engine.transition(deal, "qualify", user=self.user)

        activities = Activity.objects.filter(deal=deal, action="stage_changed")
        self.assertEqual(activities.count(), 1)
        activity = activities.first()
        self.assertIn("intake", activity.description)
        self.assertIn("qualify", activity.description)
        self.assertEqual(activity.metadata["from"], "intake")
        self.assertEqual(activity.metadata["to"], "qualify")
        self.assertEqual(activity.actor, self.user)

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_transition_raises_on_invalid(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        """transition() raises ValueError when can_transition() returns False."""
        deal = self._make_deal(stage="intake")
        with self.assertRaises(ValueError) as ctx:
            self.engine.transition(deal, "proposal_dev", user=self.user)
        self.assertIn("Cannot transition", str(ctx.exception))


@pytest.mark.django_db
class TestTransitionSideEffects(TestCase):
    """Verify transition() calls stage_orchestrator, signals, and velocity tasks."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.engine = WorkflowEngine()
        self.user = User.objects.create_user(
            username="wf_side", email="side@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov Side", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-SIDE-001",
            source=self.source,
            title="Side Effect Opp",
        )

    def _make_deal(self, stage="intake"):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp,
            owner=self.user,
            title="Side Effect Deal",
            stage=stage,
            estimated_value=Decimal("600000"),
        )

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_velocity_recorded_on_transition(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        self.engine.transition(deal, "qualify", user=self.user)

        # record_deal_velocity called twice: exit old stage, enter new stage
        self.assertEqual(mock_velocity.call_count, 2)
        exit_call = mock_velocity.call_args_list[0]
        enter_call = mock_velocity.call_args_list[1]
        self.assertEqual(exit_call[0], (str(deal.id), "intake", "exit"))
        self.assertEqual(enter_call[0], (str(deal.id), "qualify", "enter"))

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_auto_generate_tasks_called(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        self.engine.transition(deal, "qualify", user=self.user)

        mock_auto_tasks.assert_called_once_with(str(deal.id), "qualify")

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_stage_orchestrator_called(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        self.engine.transition(deal, "qualify", user=self.user)

        mock_orchestrator.assert_called_once_with(deal, "intake", "qualify", self.user)

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_stage_changed_signal_emitted(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        self.engine.transition(deal, "qualify", user=self.user)

        mock_signal.assert_called_once_with(
            deal_id=str(deal.id),
            from_stage="intake",
            to_stage="qualify",
            user_id=self.user.id,
        )

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_outcome_signal_emitted_for_terminal_stage(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        """Transitioning to closed_won emits on_deal_outcome with outcome='won'."""
        mock_gate.return_value = GateEvaluation(
            stage="closed_won", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="delivery")
        self.engine.transition(deal, "closed_won", user=self.user)

        mock_outcome.assert_called_once_with(
            deal_id=str(deal.id),
            outcome="won",
            user_id=self.user.id,
        )

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_outcome_signal_not_emitted_for_nonterminal_stage(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        """Non-terminal stages do not emit on_deal_outcome."""
        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        self.engine.transition(deal, "qualify", user=self.user)
        mock_outcome.assert_not_called()

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_no_bid_outcome_signal(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        """Transitioning to no_bid emits on_deal_outcome with outcome='no_bid'."""
        mock_gate.return_value = GateEvaluation(
            stage="no_bid", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        self.engine.transition(deal, "no_bid", user=self.user)

        mock_outcome.assert_called_once_with(
            deal_id=str(deal.id),
            outcome="no_bid",
            user_id=self.user.id,
        )

    @patch("apps.deals.signals.on_deal_stage_changed")
    @patch("apps.deals.signals.on_deal_outcome")
    @patch("apps.deals.services.stage_orchestrator.handle_stage_transition")
    @patch("apps.deals.tasks.auto_generate_stage_tasks.delay")
    @patch("apps.analytics.tasks.record_deal_velocity.delay")
    @patch("apps.deals.services.gate_evaluator.evaluate_gate")
    def test_transition_without_user(
        self, mock_gate, mock_velocity, mock_auto_tasks,
        mock_orchestrator, mock_outcome, mock_signal
    ):
        """transition() works with user=None (system-initiated)."""
        mock_gate.return_value = GateEvaluation(
            stage="qualify", overall_status="green",
            can_proceed=True, summary="OK"
        )
        deal = self._make_deal(stage="intake")
        result = self.engine.transition(deal, "qualify", user=None)
        self.assertTrue(result)

        deal.refresh_from_db()
        self.assertEqual(deal.stage, "qualify")

        mock_signal.assert_called_once_with(
            deal_id=str(deal.id),
            from_stage="intake",
            to_stage="qualify",
            user_id=None,
        )


@pytest.mark.django_db
class TestTransitionMap(TestCase):
    """Validate the VALID_TRANSITIONS map itself."""

    def test_all_stages_have_entries(self):
        """Every non-terminal stage should appear as a key in VALID_TRANSITIONS."""
        terminal = {"closed_won", "closed_lost", "no_bid"}
        from apps.deals.models import Deal
        all_stages = {code for code, _ in Deal.STAGES}
        for stage in all_stages - terminal:
            self.assertIn(
                stage, VALID_TRANSITIONS,
                f"Stage '{stage}' missing from VALID_TRANSITIONS"
            )

    def test_hitl_gates_are_subset_of_valid_targets(self):
        """Every HITL gate must appear as a target in at least one transition."""
        all_targets = set()
        for targets in VALID_TRANSITIONS.values():
            all_targets.update(targets)
        for gate in HITL_GATES:
            self.assertIn(
                gate, all_targets,
                f"HITL gate '{gate}' never appears as a transition target"
            )
