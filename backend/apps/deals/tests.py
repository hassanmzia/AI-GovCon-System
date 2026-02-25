"""Tests for deals app: CRUD operations and stage transitions."""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.deals.models import Deal
from apps.opportunities.models import Opportunity, OpportunitySource

User = get_user_model()


def make_opportunity(title="Test Opp"):
    src, _ = OpportunitySource.objects.get_or_create(
        name="SAM.gov",
        defaults={"source_type": "samgov"},
    )
    opp, _ = Opportunity.objects.get_or_create(
        notice_id=f"NOTICE-{title[:20]}",
        defaults={
            "source": src,
            "title": title,
            "is_active": True,
        },
    )
    return opp


class DealCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="cm", email="cm@example.com", password="Pass1234!",
            role=User.Role.CAPTURE_MANAGER,
        )
        resp = self.client.post(
            "/api/auth/token/", {"username": "cm", "password": "Pass1234!"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        self.opp = make_opportunity()

    def _create_deal(self, title="Test Deal", stage="intake"):
        return self.client.post("/api/deals/", {
            "title": title,
            "opportunity": str(self.opp.id),
            "stage": stage,
            "priority": 3,
        })

    def test_create_deal(self):
        resp = self._create_deal()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["title"], "Test Deal")
        self.assertEqual(resp.data["stage"], "intake")

    def test_list_deals(self):
        self._create_deal("Deal A")
        self._create_deal("Deal B")
        resp = self.client.get("/api/deals/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data.get("results", resp.data)), 2)

    def test_retrieve_deal(self):
        create_resp = self._create_deal("Single Deal")
        deal_id = create_resp.data["id"]
        resp = self.client.get(f"/api/deals/{deal_id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "Single Deal")

    def test_update_deal_stage(self):
        create_resp = self._create_deal()
        deal_id = create_resp.data["id"]
        resp = self.client.patch(f"/api/deals/{deal_id}/", {"stage": "qualify"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["stage"], "qualify")

    def test_update_deal_value(self):
        create_resp = self._create_deal()
        deal_id = create_resp.data["id"]
        resp = self.client.patch(f"/api/deals/{deal_id}/", {"estimated_value": "1500000.00"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data["estimated_value"]), Decimal("1500000.00"))

    def test_delete_deal(self):
        create_resp = self._create_deal()
        deal_id = create_resp.data["id"]
        del_resp = self.client.delete(f"/api/deals/{deal_id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        get_resp = self.client.get(f"/api/deals/{deal_id}/")
        self.assertEqual(get_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_list(self):
        client = APIClient()
        resp = client.get("/api/deals/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class DealModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner", email="owner@example.com", password="p"
        )
        self.opp = make_opportunity("Model Test Opp")

    def test_deal_str(self):
        deal = Deal.objects.create(
            title="My Deal",
            opportunity=self.opp,
            owner=self.user,
            stage="intake",
        )
        self.assertIn("My Deal", str(deal))

    def test_deal_default_stage(self):
        deal = Deal.objects.create(title="D", opportunity=self.opp)
        self.assertEqual(deal.stage, "intake")

    def test_deal_default_scores(self):
        deal = Deal.objects.create(title="D", opportunity=self.opp)
        self.assertEqual(deal.win_probability, 0.0)
        self.assertEqual(deal.fit_score, 0.0)
        self.assertEqual(deal.composite_score, 0.0)
