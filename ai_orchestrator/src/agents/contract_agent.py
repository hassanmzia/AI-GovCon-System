"""Contract Drafting AI Agent using LangGraph.

Drafts contract sections, reviews FAR/DFARS compliance, identifies
risky clauses, recommends negotiations positions, and generates
redlined revisions.

Events: CONTRACT_DRAFTED, CONTRACT_REVIEWED, CONTRACT_RISKS_IDENTIFIED.
"""
import logging
import os
from typing import Annotated, Any
import operator

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.contract")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# High-risk FAR clauses that require careful review
_HIGH_RISK_CLAUSES = [
    "52.215-2",   # Audit and Records—Negotiation
    "52.222-54",  # Employment Eligibility Verification
    "52.227-14",  # Rights in Data—General
    "52.230-2",   # Cost Accounting Standards
    "52.232-7",   # Payments under Time-and-Materials and Labor-Hour Contracts
    "52.249-8",   # Default (Fixed-Price Supply and Service)
    "252.215-7013",  # Supplies and Services provided by Nontraditional Defense Contractors
    "252.227-7013",  # Rights in Technical Data
    "252.239-7010",  # Cloud Computing Services
]


# ── State ─────────────────────────────────────────────────────────────────────

class ContractState(TypedDict):
    deal_id: str
    contract_id: str                 # Existing contract to review/draft
    deal: dict
    contract_text: str               # Full contract text to analyze
    contract_type: str               # FFP, T&M, CPFF, IDIQ, etc.
    drafted_sections: dict           # {section: drafted_text}
    identified_clauses: list[dict]   # FAR/DFARS clauses found
    risk_clauses: list[dict]         # High-risk clauses requiring review
    negotiation_positions: list[dict] # {clause, current_text, recommended_position, rationale}
    redline_suggestions: list[dict]  # {clause, original, suggested, reason}
    legal_review_summary: str        # Overall legal assessment
    messages: Annotated[list, operator.add]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{DJANGO_API_URL}{path}", headers=_auth_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


async def _llm(system: str, human: str, max_tokens: int = 3000) -> str:
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
        )
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_contract_context(state: ContractState) -> dict:
    logger.info("ContractAgent: loading context for deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})

    # Load contract if contract_id provided
    contract_text = state.get("contract_text", "")
    contract_type = state.get("contract_type", "")
    if state.get("contract_id") and not contract_text:
        contract_data = await _get(f"/api/contracts/{state['contract_id']}/", default={})
        contract_text = contract_data.get("content", "")
        contract_type = contract_data.get("contract_type", contract_type)

    return {
        "deal": deal,
        "contract_text": contract_text,
        "contract_type": contract_type or "FFP",
        "messages": [HumanMessage(content=f"Reviewing contract for: {deal.get('title', state['deal_id'])}")],
    }


async def identify_and_classify_clauses(state: ContractState) -> dict:
    """Extract and classify all FAR/DFARS clauses from the contract."""
    logger.info("ContractAgent: identifying clauses for deal %s", state["deal_id"])

    import re
    contract_text = state.get("contract_text", "")

    if not contract_text:
        return {
            "identified_clauses": [],
            "risk_clauses": [],
            "messages": [HumanMessage(content="No contract text — clause identification skipped.")],
        }

    # Extract FAR/DFARS clause numbers
    far_pattern = re.compile(r'(?:FAR\s+)?52\.\d{3}-\d{1,4}', re.IGNORECASE)
    dfars_pattern = re.compile(r'(?:DFARS\s+)?252\.\d{3}-\d{4}', re.IGNORECASE)

    far_clauses = set(far_pattern.findall(contract_text))
    dfars_clauses = set(dfars_pattern.findall(contract_text))
    all_clauses = list(far_clauses | dfars_clauses)

    identified = [
        {
            "clause_number": clause,
            "type": "DFARS" if clause.startswith("252") else "FAR",
            "is_high_risk": any(clause.startswith(hr) for hr in _HIGH_RISK_CLAUSES),
        }
        for clause in all_clauses
    ]

    risk_clauses = [c for c in identified if c["is_high_risk"]]

    return {
        "identified_clauses": identified,
        "risk_clauses": risk_clauses,
        "messages": [HumanMessage(content=f"Found {len(identified)} clause(s), {len(risk_clauses)} high-risk.")],
    }


async def analyze_contract_risks(state: ContractState) -> dict:
    """Claude analyzes risk clauses and generates negotiation positions."""
    logger.info("ContractAgent: analyzing risks for deal %s", state["deal_id"])

    risk_clauses = state.get("risk_clauses") or []
    contract_text = state.get("contract_text", "")
    contract_type = state.get("contract_type", "FFP")

    if not risk_clauses and not contract_text[:500]:
        return {
            "negotiation_positions": [],
            "messages": [HumanMessage(content="No risk clauses to analyze.")],
        }

    clause_list = "\n".join(f"- {c['clause_number']} ({c['type']})" for c in risk_clauses[:10])
    contract_excerpt = contract_text[:3000] if contract_text else "No contract text provided."

    content = await _llm(
        system=(
            "You are a government contracts attorney specializing in FAR/DFARS. "
            "Analyze contract clauses for risk and provide practical negotiation positions. "
            "Focus on protecting the contractor's interests while maintaining compliance."
        ),
        human=(
            f"Contract Type: {contract_type}\n"
            f"Deal: {state['deal'].get('title', '')}\n\n"
            f"High-Risk Clauses Found:\n{clause_list}\n\n"
            f"Contract Excerpt (first 3000 chars):\n{contract_excerpt}\n\n"
            "For each high-risk clause provide:\n"
            "CLAUSE: [number] | RISK: brief risk description | "
            "POSITION: recommended negotiation position | PRIORITY: HIGH/MEDIUM/LOW\n\n"
            "Also identify any non-standard terms that deviate from FAR templates."
        ),
        max_tokens=2500,
    )

    positions = []
    for line in content.split("\n"):
        if "CLAUSE:" in line and "RISK:" in line:
            parts = line.split("|")
            if len(parts) >= 3:
                positions.append({
                    "clause": parts[0].replace("CLAUSE:", "").strip(),
                    "risk": parts[1].replace("RISK:", "").strip(),
                    "position": parts[2].replace("POSITION:", "").strip(),
                    "priority": parts[3].replace("PRIORITY:", "").strip() if len(parts) > 3 else "MEDIUM",
                })

    return {
        "negotiation_positions": positions,
        "messages": [HumanMessage(content=f"Risk analysis complete: {len(positions)} negotiation position(s).")],
    }


async def draft_redline_suggestions(state: ContractState) -> dict:
    """Generate specific redline (markup) suggestions for problematic clauses."""
    logger.info("ContractAgent: drafting redlines for deal %s", state["deal_id"])

    positions = state.get("negotiation_positions") or []
    contract_text = state.get("contract_text", "")

    if not positions:
        return {
            "redline_suggestions": [],
            "messages": [HumanMessage(content="No negotiation positions — no redlines needed.")],
        }

    high_priority = [p for p in positions if p.get("priority") == "HIGH"][:5]
    if not high_priority:
        high_priority = positions[:3]

    content = await _llm(
        system=(
            "You are a contracts attorney drafting redline revisions. "
            "For each clause, provide specific language changes that protect contractor interests "
            "while remaining compliant with FAR/DFARS requirements."
        ),
        human=(
            f"Contract Type: {state.get('contract_type', 'FFP')}\n\n"
            "For each of the following high-priority negotiation positions, "
            "draft specific redline language:\n\n"
            + "\n".join(
                f"Clause {p['clause']}: {p['risk']}\nRecommended position: {p['position']}"
                for p in high_priority
            )
            + "\n\nFor each clause provide:\n"
            "CLAUSE: [number]\n"
            "ORIGINAL: [original language or standard FAR text]\n"
            "SUGGESTED: [revised language]\n"
            "REASON: [brief justification]\n"
            "---"
        ),
        max_tokens=2500,
    )

    suggestions = []
    blocks = content.split("---")
    for block in blocks:
        if "CLAUSE:" in block:
            lines = {
                line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip()
                for line in block.strip().split("\n")
                if ":" in line
            }
            if "CLAUSE" in lines:
                suggestions.append({
                    "clause": lines.get("CLAUSE", ""),
                    "original": lines.get("ORIGINAL", ""),
                    "suggested": lines.get("SUGGESTED", ""),
                    "reason": lines.get("REASON", ""),
                })

    return {
        "redline_suggestions": suggestions,
        "messages": [HumanMessage(content=f"Generated {len(suggestions)} redline suggestion(s).")],
    }


async def generate_legal_review_summary(state: ContractState) -> dict:
    """Generate final legal review summary and overall risk rating."""
    logger.info("ContractAgent: generating legal summary for deal %s", state["deal_id"])

    identified = state.get("identified_clauses") or []
    risk_clauses = state.get("risk_clauses") or []
    positions = state.get("negotiation_positions") or []
    redlines = state.get("redline_suggestions") or []

    content = await _llm(
        system="You are a senior contracts attorney writing a legal review memo.",
        human=(
            f"Contract Review Summary for: {state['deal'].get('title', state['deal_id'])}\n"
            f"Contract Type: {state.get('contract_type', 'Unknown')}\n\n"
            f"Clauses Found: {len(identified)} total, {len(risk_clauses)} high-risk\n"
            f"Negotiation Positions: {len(positions)}\n"
            f"Redline Suggestions: {len(redlines)}\n\n"
            "Provide a legal review memo covering:\n"
            "1. Overall risk rating: LOW / MEDIUM / HIGH / CRITICAL\n"
            "2. Top 3 legal concerns requiring immediate attention\n"
            "3. Contract terms favorable to the government that should be negotiated\n"
            "4. Recommended escalation path (in-house counsel, outside counsel, etc.)\n"
            "5. Estimated negotiation timeline and strategy"
        ),
        max_tokens=1500,
    )

    return {
        "legal_review_summary": content,
        "messages": [HumanMessage(content="Legal review summary complete.")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_contract_graph() -> StateGraph:
    wf = StateGraph(ContractState)
    wf.add_node("load_contract_context", load_contract_context)
    wf.add_node("identify_and_classify_clauses", identify_and_classify_clauses)
    wf.add_node("analyze_contract_risks", analyze_contract_risks)
    wf.add_node("draft_redline_suggestions", draft_redline_suggestions)
    wf.add_node("generate_legal_review_summary", generate_legal_review_summary)
    wf.set_entry_point("load_contract_context")
    wf.add_edge("load_contract_context", "identify_and_classify_clauses")
    wf.add_edge("identify_and_classify_clauses", "analyze_contract_risks")
    wf.add_edge("analyze_contract_risks", "draft_redline_suggestions")
    wf.add_edge("draft_redline_suggestions", "generate_legal_review_summary")
    wf.add_edge("generate_legal_review_summary", END)
    return wf.compile()


contract_graph = build_contract_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class ContractAgent(BaseAgent):
    """AI agent that reviews contracts, identifies risks, and drafts redlines."""

    agent_name = "contract_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: ContractState = {
            "deal_id": deal_id,
            "contract_id": input_data.get("contract_id", ""),
            "deal": {},
            "contract_text": input_data.get("contract_text", ""),
            "contract_type": input_data.get("contract_type", "FFP"),
            "drafted_sections": {},
            "identified_clauses": [],
            "risk_clauses": [],
            "negotiation_positions": [],
            "redline_suggestions": [],
            "legal_review_summary": "",
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Reviewing contract for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await contract_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "clauses_found": len(fs["identified_clauses"]),
                    "risk_clauses": len(fs["risk_clauses"]),
                    "redlines": len(fs["redline_suggestions"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "identified_clauses": fs["identified_clauses"],
                "risk_clauses": fs["risk_clauses"],
                "negotiation_positions": fs["negotiation_positions"],
                "redline_suggestions": fs["redline_suggestions"],
                "legal_review_summary": fs["legal_review_summary"],
            }
        except Exception as exc:
            logger.exception("ContractAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
