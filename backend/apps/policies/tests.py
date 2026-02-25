"""Tests for policies app: BusinessPolicy CRUD and evaluation logic."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.policies.models import BusinessPolicy, PolicyRule, PolicyEvaluation, PolicyException
from apps.opportunities.models import Opportunity, OpportunitySource
from apps.deals.models import Deal

User = get_user_model()


def make_deal(title="Policy Test Deal"):
    src, _ = OpportunitySource.objects.get_or_create(
        name="SAM.gov", defaults={"source_type": "samgov"}
    )
    opp, _ = Opportunity.objects.get_or_create(
        notice_id=f"OPP-POL-{title[:15]}",
        defaults={"source": src, "title": title},
    )
    return Deal.objects.create(title=title, opportunity=opp)


class BusinessPolicyModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="policymaker", email="pm@example.com", password="pass"
        )

    def test_create_policy(self):
        policy = BusinessPolicy.objects.create(
            name="Min Bid Threshold",
            policy_type="bid_threshold",
            scope="global",
            conditions={"min_value": 100000},
            actions={"block_submission": True},
            created_by=self.user,
        )
        self.assertEqual(policy.name, "Min Bid Threshold")
        self.assertTrue(policy.is_active)
        self.assertEqual(policy.version, 1)

    def test_policy_str(self):
        policy = BusinessPolicy.objects.create(
            name="Test Policy", policy_type="approval_gate",
        )
        self.assertIn("Test Policy", str(policy))
        self.assertIn("v1", str(policy))

    def test_is_effective_no_dates(self):
        policy = BusinessPolicy.objects.create(
            name="Always On", policy_type="risk_limit",
        )
        self.assertTrue(policy.is_effective())

    def test_inactive_policy(self):
        policy = BusinessPolicy.objects.create(
            name="Disabled", policy_type="risk_limit", is_active=False,
        )
        self.assertFalse(policy.is_active)

    def test_policy_ordering_by_priority(self):
        BusinessPolicy.objects.create(name="High P", policy_type="risk_limit", priority=10)
        BusinessPolicy.objects.create(name="Low P", policy_type="risk_limit", priority=200)
        policies = list(BusinessPolicy.objects.all())
        self.assertLessEqual(policies[0].priority, policies[-1].priority)


class PolicyRuleTests(TestCase):
    def setUp(self):
        self.policy = BusinessPolicy.objects.create(
            name="Value Gate", policy_type="bid_threshold",
        )

    def test_create_blocking_rule(self):
        rule = PolicyRule.objects.create(
            policy=self.policy,
            rule_name="Contract value >= 100k",
            field_path="estimated_value",
            operator="gte",
            threshold_value="100000",
            is_blocking=True,
            error_message="Contract value must be at least $100,000.",
        )
        self.assertTrue(rule.is_blocking)
        self.assertIn("Value Gate", str(rule))

    def test_create_warning_rule(self):
        rule = PolicyRule.objects.create(
            policy=self.policy,
            rule_name="Win prob check",
            field_path="win_probability",
            operator="gt",
            threshold_value="0.2",
            is_blocking=False,
            warning_message="Low win probability.",
        )
        self.assertFalse(rule.is_blocking)


class PolicyEvaluationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resolver", email="r@example.com", password="pass"
        )
        self.policy = BusinessPolicy.objects.create(
            name="Gate Policy", policy_type="approval_gate",
        )
        self.deal = make_deal()

    def test_create_pass_evaluation(self):
        evaluation = PolicyEvaluation.objects.create(
            policy=self.policy,
            deal=self.deal,
            outcome="pass",
            triggered_rules=[],
        )
        self.assertEqual(evaluation.outcome, "pass")
        self.assertIn("pass", str(evaluation))

    def test_create_fail_evaluation_with_rules(self):
        evaluation = PolicyEvaluation.objects.create(
            policy=self.policy,
            deal=self.deal,
            outcome="fail",
            triggered_rules=[
                {"rule_name": "Value check", "passed": False, "message": "Too low"}
            ],
        )
        self.assertEqual(len(evaluation.triggered_rules), 1)


class PolicyExceptionTests(TestCase):
    def setUp(self):
        self.approver = User.objects.create_user(
            username="approver", email="ap@example.com", password="pass",
            role=User.Role.ADMIN,
        )
        self.requester = User.objects.create_user(
            username="requester", email="req@example.com", password="pass"
        )
        self.policy = BusinessPolicy.objects.create(
            name="Strict Gate", policy_type="approval_gate",
        )
        self.deal = make_deal("Exception Deal")

    def test_create_exception_request(self):
        exc = PolicyException.objects.create(
            policy=self.policy,
            deal=self.deal,
            reason="Strategic partnership requires override",
            requested_by=self.requester,
        )
        self.assertEqual(exc.status, "pending")
        self.assertFalse(exc.is_valid())

    def test_approved_exception_is_valid(self):
        from django.utils import timezone
        exc = PolicyException.objects.create(
            policy=self.policy,
            deal=self.deal,
            reason="Executive approval obtained",
            requested_by=self.requester,
            approved_by=self.approver,
            approved_at=timezone.now(),
            status="approved",
        )
        self.assertTrue(exc.is_valid())


class PoliciesAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin_api", email="admin@example.com", password="AdminPass1!",
            role=User.Role.ADMIN,
        )
        resp = self.client.post(
            "/api/auth/token/", {"username": "admin_api", "password": "AdminPass1!"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    def test_list_policies(self):
        BusinessPolicy.objects.create(name="P1", policy_type="bid_threshold")
        resp = self.client.get("/api/policies/policies/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_policy_via_api(self):
        resp = self.client.post("/api/policies/policies/", {
            "name": "API Policy",
            "policy_type": "risk_limit",
            "scope": "global",
            "conditions": {"max_risk": 0.8},
            "actions": {"notify": ["manager"]},
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "API Policy")

    def test_unauthenticated_blocked(self):
        client = APIClient()
        resp = client.get("/api/policies/policies/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
