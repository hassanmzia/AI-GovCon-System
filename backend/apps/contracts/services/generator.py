"""
Contract document generator.

Produces contract documents from templates by substituting variables,
attaching applicable clauses, and rendering the final document.

TODO: Implement contract generation logic
- Load ContractTemplate and resolve variables from deal data
- Attach mandatory FAR/DFARS clauses based on contract type and agency
- Render the final document content
- Create a ContractVersion snapshot
"""


def render_template(template_content: str, variables: dict) -> str:
    """
    Render template content by substituting {{variable}} placeholders.

    Args:
        template_content: Raw template string with {{variable}} placeholders.
        variables: Dict mapping variable names to values.

    Returns:
        str: Rendered content with all known placeholders substituted.
             Unknown placeholders are left with a [MISSING: key] marker.
    """
    import re

    def replacer(match: re.Match) -> str:
        key = match.group(1).strip()
        if key in variables and variables[key] is not None:
            return str(variables[key])
        return f"[MISSING: {key}]"

    return re.sub(r'\{\{([^}]+)\}\}', replacer, template_content)


def generate_contract(deal_id, template_id, variable_overrides=None):
    """
    Generate a contract document from a template for a deal.

    Steps:
      1. Load the Deal and ContractTemplate.
      2. Build a variable context from deal data.
      3. Apply variable_overrides on top.
      4. Render the template content.
      5. Attach required clauses from the template.
      6. Create a Contract record and an initial ContractVersion snapshot.

    Args:
        deal_id: UUID of the Deal.
        template_id: UUID of the ContractTemplate.
        variable_overrides: Optional dict of variable name -> value overrides.

    Returns:
        Contract: The created Contract instance.
    """
    import uuid
    from datetime import date
    from apps.contracts.models import Contract, ContractClause, ContractTemplate, ContractVersion
    from apps.deals.models import Deal

    try:
        deal = Deal.objects.select_related("opportunity").get(pk=deal_id)
    except Deal.DoesNotExist:
        raise ValueError(f"Deal {deal_id} not found.")

    try:
        template = ContractTemplate.objects.get(pk=template_id)
    except ContractTemplate.DoesNotExist:
        raise ValueError(f"ContractTemplate {template_id} not found.")

    opp = deal.opportunity
    variables: dict = {
        "deal_title":            deal.title,
        "contract_number":       f"DRAFT-{uuid.uuid4().hex[:8].upper()}",
        "contract_type":         template.get_contract_type_display(),
        "contracting_agency":    opp.agency if opp else "",
        "solicitation_number":   getattr(opp, "sol_number", "") if opp else "",
        "naics_code":            opp.naics_code if opp else "",
        "effective_date":        date.today().isoformat(),
        "period_of_performance": "12 months",
        "total_value":           str(deal.value) if getattr(deal, "value", None) else "TBD",
        "description":           (
            (deal.notes or "")
            or (opp.description[:500] if opp and opp.description else "")
        ),
    }
    if variable_overrides:
        variables.update(variable_overrides)

    rendered_content = render_template(template.template_content, variables)

    contract = Contract.objects.create(
        deal=deal,
        template=template,
        contract_number=variables["contract_number"],
        title=f"{deal.title} — {template.get_contract_type_display()}",
        contract_type=template.contract_type,
        status="drafting",
        notes=rendered_content,
    )

    if template.required_clauses:
        clauses = ContractClause.objects.filter(
            clause_number__in=template.required_clauses
        )
        contract.clauses.set(clauses)

    ContractVersion.objects.create(
        contract=contract,
        version_number=1,
        change_type="initial",
        description="Initial draft generated from template.",
        changes={
            "template_id": str(template_id),
            "variables_used": list(variables.keys()),
        },
    )

    logger.info(
        "generate_contract: contract=%s deal=%s template=%s",
        contract.id,
        deal_id,
        template_id,
    )
    return contract
