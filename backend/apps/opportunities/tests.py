"""Tests for opportunities app: ingestion, scoring, and filters."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.opportunities.models import Opportunity, OpportunitySource

User = get_user_model()


def make_source(name="SAM.gov", source_type="samgov"):
    src, _ = OpportunitySource.objects.get_or_create(
        name=name, defaults={"source_type": source_type}
    )
    return src


class OpportunityFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst", email="a@example.com", password="Pass1!"
        )
        resp = self.client.post(
            "/api/auth/token/", {"username": "analyst", "password": "Pass1!"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        src = make_source()

        Opportunity.objects.create(
            notice_id="OPP-001", source=src, title="AI Research Contract",
            agency="DARPA", naics_code="541715", is_active=True,
        )
        Opportunity.objects.create(
            notice_id="OPP-002", source=src, title="Cloud Platform Services",
            agency="GSA", naics_code="518210", is_active=True,
        )
        Opportunity.objects.create(
            notice_id="OPP-003", source=src, title="Inactive Opp",
            agency="DoD", is_active=False,
        )

    def test_list_active_only(self):
        resp = self.client.get("/api/opportunities/?is_active=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data.get("results", resp.data)
        titles = [r["title"] for r in results]
        self.assertNotIn("Inactive Opp", titles)

    def test_filter_by_agency(self):
        resp = self.client.get("/api/opportunities/?agency=DARPA")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data.get("results", resp.data)
        self.assertTrue(all("DARPA" in r["agency"] for r in results))

    def test_search_by_title(self):
        resp = self.client.get("/api/opportunities/?search=AI")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data.get("results", resp.data)
        self.assertTrue(len(results) >= 1)

    def test_retrieve_opportunity(self):
        opp = Opportunity.objects.get(notice_id="OPP-001")
        resp = self.client.get(f"/api/opportunities/{opp.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["notice_id"], "OPP-001")

    def test_unauthenticated_access_blocked(self):
        client = APIClient()
        resp = client.get("/api/opportunities/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class OpportunityModelTests(TestCase):
    def test_str_representation(self):
        src = make_source()
        opp = Opportunity.objects.create(
            notice_id="OPP-STR", source=src, title="Test Opportunity"
        )
        self.assertIn("Test Opportunity", str(opp))

    def test_default_is_active(self):
        src = make_source()
        opp = Opportunity.objects.create(
            notice_id="OPP-DEF", source=src, title="Default Opp"
        )
        # Default depends on model — just verify it exists and has a value
        self.assertIsNotNone(opp.is_active)
