"""Tests for analytics app: KPI snapshots and win/loss analysis."""
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.analytics.models import KPISnapshot, WinLossAnalysis, AgentPerformanceMetric
from apps.opportunities.models import Opportunity, OpportunitySource
from apps.deals.models import Deal

User = get_user_model()


def make_deal(title="Test Deal"):
    src, _ = OpportunitySource.objects.get_or_create(
        name="SAM.gov", defaults={"source_type": "samgov"}
    )
    opp, _ = Opportunity.objects.get_or_create(
        notice_id=f"OPP-{title[:20]}",
        defaults={"source": src, "title": title},
    )
    return Deal.objects.create(title=title, opportunity=opp, stage="closed_won")


class KPISnapshotTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst", email="a@example.com", password="Pass1!",
            role=User.Role.CAPTURE_MANAGER,
        )
        resp = self.client.post(
            "/api/auth/token/", {"username": "analyst", "password": "Pass1!"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    def test_create_kpi_snapshot(self):
        KPISnapshot.objects.create(
            date=date.today(),
            active_deals=10,
            pipeline_value=5000000,
            win_rate=0.65,
        )
        snap = KPISnapshot.objects.get(date=date.today())
        self.assertEqual(snap.active_deals, 10)
        self.assertAlmostEqual(snap.win_rate, 0.65)

    def test_kpi_snapshot_str(self):
        snap = KPISnapshot.objects.create(
            date=date(2025, 1, 15), pipeline_value=1234567
        )
        self.assertIn("2025-01-15", str(snap))

    def test_list_kpi_snapshots_api(self):
        KPISnapshot.objects.create(date=date.today(), active_deals=5, pipeline_value=1000000)
        resp = self.client.get("/api/analytics/kpi-snapshots/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unique_date_constraint(self):
        KPISnapshot.objects.create(date=date(2025, 6, 1))
        with self.assertRaises(Exception):
            KPISnapshot.objects.create(date=date(2025, 6, 1))


class WinLossAnalysisTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="wl_analyst", email="wl@example.com", password="Pass1!",
        )
        resp = self.client.post(
            "/api/auth/token/", {"username": "wl_analyst", "password": "Pass1!"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        self.deal = make_deal("Closed Deal")

    def test_create_win_loss(self):
        wl = WinLossAnalysis.objects.create(
            deal=self.deal,
            outcome="won",
            close_date=date.today(),
            primary_loss_reason="",
            lessons_learned="Great team collaboration",
        )
        self.assertEqual(wl.outcome, "won")
        self.assertIn("Closed Deal", str(wl))

    def test_list_win_loss_api(self):
        WinLossAnalysis.objects.create(
            deal=self.deal, outcome="lost", close_date=date.today(),
            primary_loss_reason="Price", competitor_name="Competitor Inc",
        )
        resp = self.client.get("/api/analytics/win-loss/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class AgentPerformanceTests(TestCase):
    def test_agent_metric_creation(self):
        metric = AgentPerformanceMetric.objects.create(
            agent_name="DealScoringAgent",
            date=date.today(),
            total_runs=100,
            successful_runs=95,
            failed_runs=5,
            avg_duration_seconds=2.5,
        )
        self.assertEqual(metric.agent_name, "DealScoringAgent")
        self.assertEqual(metric.successful_runs, 95)
        self.assertIn("DealScoringAgent", str(metric))

    def test_unique_agent_date_constraint(self):
        AgentPerformanceMetric.objects.create(
            agent_name="TestAgent", date=date(2025, 1, 1)
        )
        with self.assertRaises(Exception):
            AgentPerformanceMetric.objects.create(
                agent_name="TestAgent", date=date(2025, 1, 1)
            )
