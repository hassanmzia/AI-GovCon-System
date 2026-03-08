"""
Tests for contract services: generator and clause_scanner.

Covers:
  - render_template() variable substitution
  - render_template() missing variable handling
  - scan_contract() FAR clause detection
  - scan_contract() missing mandatory clause detection
  - scan_contract() risk scoring
  - identify_flow_down_clauses()
"""

import pytest
from decimal import Decimal

from django.test import TestCase

from apps.contracts.services.generator import render_template
from apps.contracts.services.clause_scanner import (
    identify_flow_down_clauses,
    scan_contract,
)


class TestRenderTemplate(TestCase):
    """render_template() variable substitution and missing-variable markers."""

    def test_simple_substitution(self):
        template = "Contract for {{deal_title}} with agency {{agency}}."
        variables = {"deal_title": "Cyber Defense", "agency": "DoD"}
        result = render_template(template, variables)
        self.assertEqual(result, "Contract for Cyber Defense with agency DoD.")

    def test_multiple_occurrences(self):
        template = "{{name}} agrees. Signed by {{name}}."
        result = render_template(template, {"name": "Acme Corp"})
        self.assertEqual(result, "Acme Corp agrees. Signed by Acme Corp.")

    def test_whitespace_in_placeholder(self):
        """Placeholders may have spaces around the key: {{ key }}."""
        template = "Value: {{ total_value }}."
        result = render_template(template, {"total_value": "$1,000,000"})
        self.assertEqual(result, "Value: $1,000,000.")

    def test_missing_variable_gets_marker(self):
        template = "Agency: {{agency_name}}. Period: {{pop}}."
        variables = {"agency_name": "NASA"}
        result = render_template(template, variables)
        self.assertIn("NASA", result)
        self.assertIn("[MISSING: pop]", result)

    def test_all_missing(self):
        template = "{{a}} and {{b}}"
        result = render_template(template, {})
        self.assertEqual(result, "[MISSING: a] and [MISSING: b]")

    def test_none_value_treated_as_missing(self):
        """If the variable value is None, it should produce a MISSING marker."""
        template = "Officer: {{co_name}}"
        result = render_template(template, {"co_name": None})
        self.assertEqual(result, "Officer: [MISSING: co_name]")

    def test_numeric_values_converted(self):
        template = "Value: {{amount}}, Score: {{score}}"
        result = render_template(template, {"amount": 500000, "score": 85.3})
        self.assertEqual(result, "Value: 500000, Score: 85.3")

    def test_no_placeholders(self):
        """Plain text with no placeholders passes through unchanged."""
        template = "This is a plain contract."
        result = render_template(template, {"foo": "bar"})
        self.assertEqual(result, "This is a plain contract.")

    def test_empty_template(self):
        result = render_template("", {"key": "val"})
        self.assertEqual(result, "")

    def test_extra_variables_ignored(self):
        """Variables not referenced in the template are silently ignored."""
        template = "Title: {{title}}"
        result = render_template(template, {"title": "My Contract", "extra": "unused"})
        self.assertEqual(result, "Title: My Contract")

    def test_special_characters_in_value(self):
        """Values with special regex characters should not break."""
        template = "Note: {{note}}"
        result = render_template(template, {"note": "Cost is $1,000.00 (est.)"})
        self.assertEqual(result, "Note: Cost is $1,000.00 (est.)")


@pytest.mark.django_db
class TestScanContract(TestCase):
    """scan_contract() clause detection and risk scoring."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.user = User.objects.create_user(
            username="cs_user", email="cs@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov CS", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-CS-001", source=self.source, title="Clause Scan Opp",
            agency="DoD", naics_code="541512",
        )

    def _make_deal(self):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp, owner=self.user,
            title="Clause Scan Deal", stage="contract_setup",
            estimated_value=Decimal("2000000"),
        )

    def _make_template(self, required_clauses=None):
        from apps.contracts.models import ContractTemplate

        return ContractTemplate.objects.create(
            name="FFP Standard",
            contract_type="FFP",
            template_content="Standard FFP template content.",
            required_clauses=required_clauses or [],
        )

    def _make_clause(self, clause_number, title, risk_level="medium"):
        from apps.contracts.models import ContractClause

        return ContractClause.objects.create(
            clause_number=clause_number,
            title=title,
            clause_text=f"Full text of {clause_number}",
            clause_type="far_reference",
            risk_level=risk_level,
        )

    def _make_contract(self, deal, template=None, notes=""):
        from apps.contracts.models import Contract
        import uuid

        return Contract.objects.create(
            deal=deal,
            template=template,
            contract_number=f"TEST-{uuid.uuid4().hex[:8].upper()}",
            title="Test Contract",
            contract_type="FFP",
            status="drafting",
            notes=notes,
        )

    def test_detects_far_clause_in_notes(self):
        """FAR clause numbers (52.xxx-xx) in contract notes are detected."""
        deal = self._make_deal()
        clause = self._make_clause("52.204-21", "Basic Safeguarding", risk_level="high")
        contract = self._make_contract(
            deal,
            notes="This contract incorporates 52.204-21 for cybersecurity.",
        )

        result = scan_contract(contract.id)

        found_numbers = [c["clause_number"] for c in result["clauses_found"]]
        self.assertIn("52.204-21", found_numbers)

    def test_detects_dfars_clause(self):
        """DFARS clause numbers (252.xxx-xxxx) are detected."""
        deal = self._make_deal()
        clause = self._make_clause("252.204-7012", "Safeguarding CDI", risk_level="high")
        contract = self._make_contract(
            deal,
            notes="Per DFARS, 252.204-7012 applies to all CUI handling.",
        )

        result = scan_contract(contract.id)

        found_numbers = [c["clause_number"] for c in result["clauses_found"]]
        self.assertIn("252.204-7012", found_numbers)

    def test_unknown_clause_treated_as_medium_risk(self):
        """Clause numbers found in text but not in library are 'Unknown clause'."""
        deal = self._make_deal()
        contract = self._make_contract(
            deal,
            notes="This references 52.999-99 which does not exist in our library.",
        )

        result = scan_contract(contract.id)

        found = [c for c in result["clauses_found"] if c["clause_number"] == "52.999-99"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["title"], "Unknown clause")
        self.assertEqual(found[0]["risk_level"], "medium")

    def test_missing_mandatory_clauses_detected(self):
        """Clauses required by template but not in contract text are flagged."""
        deal = self._make_deal()
        required = self._make_clause("52.222-26", "Equal Opportunity", risk_level="low")
        template = self._make_template(required_clauses=["52.222-26"])
        contract = self._make_contract(
            deal, template=template,
            notes="This contract has no clause references at all.",
        )

        result = scan_contract(contract.id)

        missing_numbers = [m["clause_number"] for m in result["missing_mandatory"]]
        self.assertIn("52.222-26", missing_numbers)

    def test_missing_mandatory_increases_risk_score(self):
        """Missing mandatory clauses contribute to a higher risk score."""
        deal = self._make_deal()
        self._make_clause("52.222-26", "Equal Opportunity")
        self._make_clause("52.222-35", "EO for Veterans")
        template = self._make_template(required_clauses=["52.222-26", "52.222-35"])
        contract = self._make_contract(
            deal, template=template,
            notes="Plain contract with no clause references.",
        )

        result = scan_contract(contract.id)
        self.assertGreater(result["risk_score"], 0.0)
        self.assertLessEqual(result["risk_score"], 1.0)

    def test_no_clauses_found_has_standard_recommendation(self):
        """Contract with no clause references gets a standard recommendation."""
        deal = self._make_deal()
        contract = self._make_contract(deal, notes="A very simple contract.")

        result = scan_contract(contract.id)

        self.assertEqual(len(result["clauses_found"]), 0)
        self.assertTrue(len(result["recommendations"]) > 0)

    def test_high_risk_clause_flagged_in_recommendations(self):
        """High-risk clauses produce a recommendation to review with counsel."""
        deal = self._make_deal()
        self._make_clause("52.249-1", "Termination for Convenience", risk_level="high")
        contract = self._make_contract(
            deal,
            notes="Termination: per 52.249-1 the Government may terminate.",
        )

        result = scan_contract(contract.id)
        has_review_rec = any("high-risk" in r.lower() for r in result["recommendations"])
        self.assertTrue(has_review_rec)

    def test_risky_pattern_produces_specific_recommendation(self):
        """52.232-xx triggers a specific payment terms recommendation."""
        deal = self._make_deal()
        contract = self._make_contract(
            deal,
            notes="Payment shall be in accordance with 52.232-25.",
        )

        result = scan_contract(contract.id)
        has_payment_rec = any("payment" in r.lower() for r in result["recommendations"])
        self.assertTrue(has_payment_rec)

    def test_dfars_cybersecurity_pattern_flagged(self):
        """252.204-7012 triggers CMMC/NIST compliance recommendation."""
        deal = self._make_deal()
        self._make_clause("252.204-7012", "Safeguarding CDI", risk_level="high")
        contract = self._make_contract(
            deal,
            notes="DFARS 252.204-7012 applies. Contractor must comply.",
        )

        result = scan_contract(contract.id)
        has_cyber_rec = any("CMMC" in r or "NIST" in r for r in result["recommendations"])
        self.assertTrue(has_cyber_rec)

    def test_contract_not_found_raises(self):
        import uuid
        with self.assertRaises(ValueError) as ctx:
            scan_contract(uuid.uuid4())
        self.assertIn("not found", str(ctx.exception))

    def test_required_clause_present_not_flagged_as_missing(self):
        """If a required clause is in the contract text, it should NOT be missing."""
        deal = self._make_deal()
        self._make_clause("52.222-26", "Equal Opportunity")
        template = self._make_template(required_clauses=["52.222-26"])
        contract = self._make_contract(
            deal, template=template,
            notes="This contract includes 52.222-26 Equal Opportunity provisions.",
        )

        result = scan_contract(contract.id)
        missing_numbers = [m["clause_number"] for m in result["missing_mandatory"]]
        self.assertNotIn("52.222-26", missing_numbers)


@pytest.mark.django_db
class TestIdentifyFlowDownClauses(TestCase):
    """identify_flow_down_clauses() finds mandatory flow-down and high-risk clauses."""

    def setUp(self):
        from apps.accounts.models import User
        from apps.opportunities.models import Opportunity, OpportunitySource

        self.user = User.objects.create_user(
            username="fd_user", email="fd@test.com", password="Pass1234!", role="admin"
        )
        self.source = OpportunitySource.objects.create(
            name="SAM.gov FD", source_type="samgov"
        )
        self.opp = Opportunity.objects.create(
            notice_id="OPP-FD-001", source=self.source, title="Flow Down Opp",
        )

    def _make_deal(self):
        from apps.deals.models import Deal

        return Deal.objects.create(
            opportunity=self.opp, owner=self.user,
            title="Flow Down Deal", stage="contract_setup",
        )

    def _make_contract(self, deal):
        from apps.contracts.models import Contract
        import uuid

        return Contract.objects.create(
            deal=deal,
            contract_number=f"FD-{uuid.uuid4().hex[:8].upper()}",
            title="Flow Down Contract",
            contract_type="FFP",
            status="active",
        )

    def _make_clause(self, clause_number, title, risk_level="medium"):
        from apps.contracts.models import ContractClause

        return ContractClause.objects.create(
            clause_number=clause_number,
            title=title,
            clause_text=f"Text for {clause_number}",
            clause_type="far_reference",
            risk_level=risk_level,
        )

    def test_mandatory_flow_down_list_populated(self):
        """Result always contains the mandatory flow-down clause list (16 entries)."""
        deal = self._make_deal()
        contract = self._make_contract(deal)

        result = identify_flow_down_clauses(contract.id)

        # The function defines 16 mandatory flow-down clauses
        mandatory_numbers = [item["clause_number"] for item in result if item["must_flow_down"]]
        self.assertGreaterEqual(len(mandatory_numbers), 16)
        self.assertIn("52.222-26", mandatory_numbers)
        self.assertIn("252.204-7012", mandatory_numbers)

    def test_attached_clause_marked_in_prime_contract(self):
        """If a mandatory flow-down clause is attached, in_prime_contract=True."""
        deal = self._make_deal()
        contract = self._make_contract(deal)
        clause = self._make_clause("52.222-26", "Equal Opportunity")
        contract.clauses.add(clause)

        result = identify_flow_down_clauses(contract.id)

        eo_items = [i for i in result if i["clause_number"] == "52.222-26"]
        self.assertEqual(len(eo_items), 1)
        self.assertTrue(eo_items[0]["in_prime_contract"])

    def test_missing_mandatory_marked_not_in_prime(self):
        """If a mandatory flow-down clause is NOT attached, in_prime_contract=False."""
        deal = self._make_deal()
        contract = self._make_contract(deal)

        result = identify_flow_down_clauses(contract.id)

        eo_items = [i for i in result if i["clause_number"] == "52.222-26"]
        self.assertEqual(len(eo_items), 1)
        self.assertFalse(eo_items[0]["in_prime_contract"])

    def test_high_risk_non_mandatory_clause_included(self):
        """High-risk clauses attached to the contract but NOT in the mandatory
        list are included with must_flow_down=False."""
        deal = self._make_deal()
        contract = self._make_contract(deal)
        custom_clause = self._make_clause(
            "52.999-1", "Custom High-Risk Clause", risk_level="high"
        )
        contract.clauses.add(custom_clause)

        result = identify_flow_down_clauses(contract.id)

        custom_items = [i for i in result if i["clause_number"] == "52.999-1"]
        self.assertEqual(len(custom_items), 1)
        self.assertFalse(custom_items[0]["must_flow_down"])
        self.assertTrue(custom_items[0]["in_prime_contract"])
        self.assertIn("legal counsel", custom_items[0]["guidance"])

    def test_low_risk_non_mandatory_clause_excluded(self):
        """Low/medium risk non-mandatory clauses should NOT appear in the extra list."""
        deal = self._make_deal()
        contract = self._make_contract(deal)
        low_clause = self._make_clause("52.888-1", "Low Risk Clause", risk_level="low")
        contract.clauses.add(low_clause)

        result = identify_flow_down_clauses(contract.id)

        custom_items = [i for i in result if i["clause_number"] == "52.888-1"]
        self.assertEqual(len(custom_items), 0)

    def test_guidance_text_present(self):
        """Every flow-down item has a non-empty guidance string."""
        deal = self._make_deal()
        contract = self._make_contract(deal)

        result = identify_flow_down_clauses(contract.id)
        for item in result:
            self.assertTrue(
                len(item["guidance"]) > 0,
                f"Missing guidance for {item['clause_number']}"
            )

    def test_contract_not_found_raises(self):
        import uuid
        with self.assertRaises(ValueError) as ctx:
            identify_flow_down_clauses(uuid.uuid4())
        self.assertIn("not found", str(ctx.exception))
