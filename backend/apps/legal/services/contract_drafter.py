"""Contract drafting service – prime contracts, teaming agreements, NDAs, subcontracts."""
import logging
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


async def draft_teaming_agreement(
    prime_name: str,
    partner_name: str,
    opportunity_title: str = "",
    solicitation_number: str = "",
    work_scope: str = "",
    work_share_percent: float | None = None,
    exclusivity_period_months: int = 18,
) -> dict[str, Any]:
    """Draft a teaming agreement between prime and subcontractor.

    Returns:
        Dict with document_text, key_terms, recommended_provisions.
    """
    today = date.today().strftime("%B %d, %Y")

    doc = f"""TEAMING AGREEMENT

This Teaming Agreement ("Agreement") is entered into as of {today}, between:

{prime_name} ("Prime Contractor"), and
{partner_name} ("Subcontractor")

(collectively, the "Parties").

RECITALS

WHEREAS, the Parties desire to pursue and perform, if awarded, the following contract opportunity:
  Solicitation: {solicitation_number or "[Solicitation Number]"}
  Opportunity: {opportunity_title or "[Opportunity Title]"}
  Issuing Agency: [Agency Name]

AGREEMENT

1. PURPOSE
   The Parties agree to cooperate in the pursuit and, if awarded, performance of the Opportunity.
   Prime Contractor shall serve as the prime contractor; Subcontractor shall serve as a subcontractor.

2. ROLES AND RESPONSIBILITIES
   2.1 Prime Contractor shall:
       (a) Lead proposal preparation and submission;
       (b) Serve as the single point of contact with the Government;
       (c) Manage overall contract performance.
   2.2 Subcontractor shall:
       (a) Provide technical resources, expertise, and personnel as agreed;
       (b) Support proposal preparation as directed by Prime;
       (c) Perform the following work scope: {work_scope or "[Work scope to be defined]"}.
{"   2.3 Work Share: Subcontractor's anticipated work share is approximately " + str(work_share_percent) + "% of total contract value." if work_share_percent else "   2.3 Work share percentages shall be defined in the executed subcontract."}

3. EXCLUSIVITY
   3.1 This Agreement is exclusive to the above Opportunity.
   3.2 Term: This Agreement expires {exclusivity_period_months} months from execution, or upon
       contract award, whichever is later.
   3.3 Neither Party may pursue the Opportunity as prime or sub with a competing team without
       prior written consent.

4. INTELLECTUAL PROPERTY
   4.1 Each Party retains ownership of its pre-existing intellectual property.
   4.2 Jointly developed IP shall be jointly owned unless otherwise agreed.
   4.3 Each Party grants the other a license to use its IP solely for proposal preparation.

5. CONFIDENTIALITY
   5.1 Each Party shall protect Confidential Information of the other party.
   5.2 This obligation survives termination for three (3) years.

6. NON-SOLICITATION
   6.1 During the term and for one (1) year thereafter, neither Party shall solicit
       the other's employees who worked on this Opportunity.

7. LIMITATION OF LIABILITY
   Neither Party shall be liable for consequential, indirect, or punitive damages.
   Total liability shall not exceed amounts paid under the executed subcontract.

8. GENERAL PROVISIONS
   8.1 Governing Law: This Agreement is governed by the laws of the United States.
   8.2 Entire Agreement: This Agreement constitutes the entire agreement on this subject.
   8.3 Amendments: Must be in writing and signed by authorized representatives.
   8.4 Non-Assignment: Neither Party may assign without prior written consent.

IN WITNESS WHEREOF, the Parties have executed this Agreement:

{prime_name}                          {partner_name}

By: ____________________________    By: ____________________________
Name: __________________________    Name: __________________________
Title: _________________________    Title: _________________________
Date: __________________________    Date: __________________________
"""

    return {
        "document_text": doc,
        "agreement_type": "teaming",
        "parties": [prime_name, partner_name],
        "opportunity": opportunity_title,
        "key_terms": {
            "exclusivity_months": exclusivity_period_months,
            "work_share": work_share_percent,
            "work_scope": work_scope,
            "governing_law": "United States Federal Law",
        },
        "recommended_provisions": [
            "Add specific SOW/PWS section once RFP is released",
            "Define payment milestones and invoicing terms",
            "Include key personnel list",
            "Consider adding non-compete for this specific agency/opportunity",
            "Review with legal counsel before signing",
        ],
        "word_count": len(doc.split()),
    }


async def draft_nda(
    party_a: str,
    party_b: str,
    purpose: str = "evaluation of potential teaming or business relationship",
    term_years: int = 3,
    mutual: bool = True,
) -> dict[str, Any]:
    """Draft a Non-Disclosure Agreement.

    Returns:
        Dict with document_text, key_terms.
    """
    today = date.today().strftime("%B %d, %Y")
    direction = "Mutual" if mutual else "One-Way"

    doc = f"""{direction.upper()} NON-DISCLOSURE AGREEMENT

This {direction} Non-Disclosure Agreement ("Agreement") is entered into as of {today}, between:

{party_a} ("{'Party A' if mutual else 'Disclosing Party'}"), and
{party_b} ("{'Party B' if mutual else 'Receiving Party'}")

1. PURPOSE
   The Parties wish to exchange confidential information for the purpose of: {purpose}.

2. DEFINITION OF CONFIDENTIAL INFORMATION
   "Confidential Information" means any non-public information disclosed by {"either" if mutual else "the Disclosing"} Party
   that is designated as confidential or that reasonably should be understood to be confidential.

   Excluded: information (a) publicly known, (b) independently developed, (c) lawfully received
   from a third party, or (d) required to be disclosed by law or court order.

3. OBLIGATIONS
   The Receiving Party shall:
   (a) Hold Confidential Information in strict confidence;
   (b) Not disclose to third parties without prior written consent;
   (c) Use only for the stated purpose;
   (d) Limit internal access to those with a need to know;
   (e) Protect with at least the same care as its own confidential information (at minimum reasonable care).

4. TERM
   This Agreement is effective for {term_years} years from the date of execution.
   Obligations survive termination for an additional {term_years} years.

5. RETURN OF INFORMATION
   Upon request, the Receiving Party shall promptly return or destroy all Confidential Information.

6. REMEDIES
   The Parties acknowledge that breach may cause irreparable harm and agree that
   injunctive relief is an appropriate remedy without posting bond.

7. GOVERNING LAW
   This Agreement is governed by the laws of the Commonwealth of Virginia / United States Federal Law.

8. ENTIRE AGREEMENT
   This Agreement constitutes the entire agreement regarding confidentiality between the Parties.

{party_a}                             {party_b}

By: ____________________________    By: ____________________________
Name: __________________________    Name: __________________________
Title: _________________________    Title: _________________________
Date: __________________________    Date: __________________________
"""

    return {
        "document_text": doc,
        "agreement_type": "nda",
        "mutual": mutual,
        "parties": [party_a, party_b],
        "key_terms": {
            "term_years": term_years,
            "purpose": purpose,
            "mutual": mutual,
        },
        "word_count": len(doc.split()),
    }


async def draft_subcontract_agreement(
    prime_name: str,
    sub_name: str,
    prime_contract_number: str,
    work_scope: str,
    period_of_performance: str,
    total_value: float,
    contract_type: str = "FFP",
) -> dict[str, Any]:
    """Draft a subcontract agreement.

    Returns:
        Dict with document_text, key_terms, far_flow_downs.
    """
    today = date.today().strftime("%B %d, %Y")

    doc = f"""SUBCONTRACT AGREEMENT

Subcontract No.: [SUB-{datetime.now().year}-001]
Prime Contract No.: {prime_contract_number}

This Subcontract Agreement is entered into as of {today}, between:
{prime_name} ("Prime") and {partner_name} ("Subcontractor") – corrected below

{prime_name} ("Prime Contractor"), and
{sub_name} ("Subcontractor")

1. STATEMENT OF WORK
   Subcontractor shall perform the following work:
   {work_scope}

2. PERIOD OF PERFORMANCE
   {period_of_performance}

3. CONTRACT TYPE AND PRICE
   Contract Type: {contract_type}
   Total Value: ${total_value:,.2f}
   (Subject to increase by written modification only)

4. INVOICING AND PAYMENT
   4.1 Subcontractor shall invoice monthly by the 15th of each month.
   4.2 Prime shall pay within 30 days of receiving government payment.
   4.3 Prompt payment clause applies per FAR 52.232-27.

5. CHANGES
   Prime may direct changes within the general scope. Equitable adjustments shall
   be provided consistent with FAR 43.

6. KEY PERSONNEL
   [Key personnel to be identified per RFP requirements]

7. FAR/DFARS FLOW-DOWN CLAUSES
   Applicable FAR/DFARS clauses flow down as required by the prime contract.
   [Flow-down list to be attached as Exhibit A]

8. TERMINATION
   8.1 For Convenience: Prime may terminate with 30 days written notice.
   8.2 For Default: Immediate termination for material breach.

9. DISPUTE RESOLUTION
   Disputes shall be resolved per the Contract Disputes Act of 1978.

10. LIMITATION OF LIABILITY
    Neither party is liable for consequential or indirect damages.

{prime_name}                          {sub_name}

By: ____________________________    By: ____________________________
"""

    # Identify required flow-down clauses
    far_flow_downs = [
        {"clause": "52.203-13", "title": "Contractor Code of Business Ethics", "required": True},
        {"clause": "52.219-8", "title": "Utilization of Small Business", "required": True},
        {"clause": "52.222-26", "title": "Equal Opportunity", "required": True},
        {"clause": "52.227-14", "title": "Rights in Data – General", "required": True},
        {"clause": "52.232-27", "title": "Prompt Payment for Construction Contracts", "required": False},
    ]

    return {
        "document_text": doc,
        "agreement_type": "subcontract",
        "parties": [prime_name, sub_name],
        "prime_contract_number": prime_contract_number,
        "key_terms": {
            "contract_type": contract_type,
            "total_value": total_value,
            "period_of_performance": period_of_performance,
        },
        "far_flow_downs": far_flow_downs,
        "recommended_exhibits": [
            "Exhibit A: Statement of Work",
            "Exhibit B: FAR/DFARS Flow-Down Clauses",
            "Exhibit C: Deliverables List",
            "Exhibit D: Key Personnel List",
        ],
        "word_count": len(doc.split()),
    }
