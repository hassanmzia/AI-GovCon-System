"""
Contract clause scanner.

Analyses contract text to identify applicable FAR/DFARS clauses,
flags risk areas, and provides negotiation guidance.

TODO: Implement clause scanning logic
- Parse contract text to extract referenced clause numbers
- Match against ContractClause library
- Flag missing mandatory clauses
- Score risk based on clause risk_level and presence/absence
- Generate negotiation recommendations for high-risk clauses
"""


def scan_contract(contract_id):
    """
    Scan a contract for clause compliance and risk.

    Extracts FAR/DFARS clause numbers referenced in the contract text,
    matches them against the ContractClause library, flags missing
    mandatory clauses, and produces a risk score with recommendations.

    Args:
        contract_id: UUID of the Contract to scan.

    Returns:
        dict: {
            "clauses_found": [{"clause_number", "title", "risk_level"}],
            "missing_mandatory": [{"clause_number", "title"}],
            "risk_score": float (0.0–1.0),
            "recommendations": [str],
        }
    """
    import re
    from apps.contracts.models import Contract, ContractClause

    try:
        contract = Contract.objects.prefetch_related("clauses", "template").get(
            pk=contract_id
        )
    except Contract.DoesNotExist:
        raise ValueError(f"Contract {contract_id} not found.")

    # Source text: contract notes/body + attached clause texts
    source_text = contract.notes or ""
    for clause in contract.clauses.all():
        source_text += f"\n{clause.clause_number} {clause.clause_text}"

    # ── Detect FAR / DFARS clause numbers (e.g. 52.204-21, 252.204-7012) ─────
    clause_number_re = re.compile(
        r'\b(52\.\d{3}-\d+|252\.\d{3}-\d+|DFARS\s+\d+\.\d+|FAR\s+\d+\.\d+)\b',
        re.IGNORECASE,
    )
    found_numbers = {m.group(1).upper() for m in clause_number_re.finditer(source_text)}

    # Match found numbers against our library
    library_map = {
        c.clause_number.upper(): c
        for c in ContractClause.objects.filter(
            clause_number__in=list(found_numbers)
        )
    }

    clauses_found = []
    high_risk_count = 0
    for num in found_numbers:
        if num in library_map:
            c = library_map[num]
            clauses_found.append({
                "clause_number": c.clause_number,
                "title": c.title,
                "risk_level": c.risk_level,
            })
            if c.risk_level == "high":
                high_risk_count += 1
        else:
            # Not in library — treat as unknown/medium risk
            clauses_found.append({
                "clause_number": num,
                "title": "Unknown clause",
                "risk_level": "medium",
            })

    # ── Check for missing mandatory clauses from the template ─────────────────
    missing_mandatory = []
    if contract.template and contract.template.required_clauses:
        required = contract.template.required_clauses  # list of clause numbers
        library_required = {
            c.clause_number.upper(): c
            for c in ContractClause.objects.filter(clause_number__in=required)
        }
        for req_num in required:
            if req_num.upper() not in found_numbers:
                if req_num.upper() in library_required:
                    c = library_required[req_num.upper()]
                    missing_mandatory.append({"clause_number": c.clause_number, "title": c.title})
                else:
                    missing_mandatory.append({"clause_number": req_num, "title": "Required clause"})

    # ── Risk score: weighted by high-risk clauses and missing mandatory ────────
    total_clauses = max(len(clauses_found), 1)
    risk_score = min(
        1.0,
        (high_risk_count * 0.15 + len(missing_mandatory) * 0.20) / total_clauses,
    )

    # ── Recommendations ───────────────────────────────────────────────────────
    recommendations = []
    if missing_mandatory:
        recommendations.append(
            f"Add {len(missing_mandatory)} missing mandatory clause(s): "
            + ", ".join(m["clause_number"] for m in missing_mandatory[:5])
        )
    if high_risk_count > 0:
        recommendations.append(
            f"Review {high_risk_count} high-risk clause(s) with legal counsel "
            "before execution."
        )
    # Flag common risk clauses
    risky_patterns = {
        "52.232": "Payment terms — verify invoicing and payment timelines.",
        "52.249": "Termination clause — review convenience and default provisions.",
        "52.215": "Cost or pricing data — ensure TINA compliance if applicable.",
        "252.204-7012": "DFARS cybersecurity — verify CMMC/NIST 800-171 compliance.",
    }
    for prefix, note in risky_patterns.items():
        if any(num.startswith(prefix) for num in found_numbers):
            recommendations.append(note)

    if not recommendations:
        recommendations.append("No critical issues found. Standard review recommended.")

    logger.info(
        "scan_contract: contract=%s found=%d missing=%d risk=%.2f",
        contract_id,
        len(clauses_found),
        len(missing_mandatory),
        risk_score,
    )

    return {
        "clauses_found": clauses_found,
        "missing_mandatory": missing_mandatory,
        "risk_score": round(risk_score, 3),
        "recommendations": recommendations,
    }


def identify_flow_down_clauses(contract_id):
    """
    Identify clauses that must flow down to subcontractors.

    Args:
        contract_id: UUID of the prime Contract.

    Returns:
        list[dict]: Clauses requiring flow-down with subcontractor guidance.
    """
    from apps.contracts.models import Contract

    try:
        contract = Contract.objects.prefetch_related("clauses").get(pk=contract_id)
    except Contract.DoesNotExist:
        raise ValueError(f"Contract {contract_id} not found.")

    # Well-known mandatory flow-down clauses (FAR/DFARS)
    mandatory_flow_down = {
        "52.202-1":    "Definitions",
        "52.203-13":   "Contractor Code of Business Ethics and Conduct",
        "52.203-15":   "Whistleblower Protections",
        "52.204-21":   "Basic Safeguarding of Covered Contractor Information Systems",
        "52.219-8":    "Utilization of Small Business Concerns",
        "52.222-26":   "Equal Opportunity",
        "52.222-35":   "Equal Opportunity for Veterans",
        "52.222-36":   "Equal Opportunity for Workers with Disabilities",
        "52.222-40":   "Notification of Employee Rights Under the NLRA",
        "52.222-50":   "Combating Trafficking in Persons",
        "52.223-18":   "Encouraging Contractor Policies to Ban Text Messaging",
        "52.225-13":   "Restrictions on Certain Foreign Purchases",
        "52.232-40":   "Providing Accelerated Payments to Small Business Subcontractors",
        "52.244-6":    "Subcontracts for Commercial Products and Services",
        "252.204-7012": "Safeguarding Covered Defense Information",
        "252.225-7001": "Buy American Act — Balance of Payments Program",
        "252.244-7000": "Subcontracts for Commercial Items",
    }

    flow_down_items = []

    # Check which mandatory flow-downs are referenced in the contract
    attached_clause_numbers = {
        c.clause_number.upper()
        for c in contract.clauses.all()
    }

    for clause_number, title in mandatory_flow_down.items():
        in_contract = clause_number.upper() in attached_clause_numbers
        flow_down_items.append({
            "clause_number": clause_number,
            "title": title,
            "in_prime_contract": in_contract,
            "must_flow_down": True,
            "guidance": (
                f"Include {clause_number} ({title}) in all subcontracts "
                f"at any tier where applicable."
            ),
        })

    # Also flag any high-risk clauses from attached library that require flow-down
    for clause in contract.clauses.filter(risk_level="high"):
        if clause.clause_number.upper() not in mandatory_flow_down:
            flow_down_items.append({
                "clause_number": clause.clause_number,
                "title": clause.title,
                "in_prime_contract": True,
                "must_flow_down": False,
                "guidance": (
                    f"Review {clause.clause_number} with legal counsel to "
                    "determine if flow-down is required for this subcontract."
                ),
            })

    logger.info(
        "identify_flow_down_clauses: contract=%s found %d flow-down clauses",
        contract_id,
        len(flow_down_items),
    )
    return flow_down_items
