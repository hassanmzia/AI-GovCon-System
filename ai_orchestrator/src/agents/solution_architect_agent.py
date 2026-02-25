"""
Solution Architect AI Agent using LangGraph.

Fully autonomous AI Solutions Architect that analyzes RFP requirements,
synthesizes a complete technical solution across 17 architecture areas,
generates Mermaid.js architecture diagrams, and produces full technical
volume sections ready for proposal insertion.

LangGraph pipeline:
  analyze_requirements
    → select_frameworks
      → retrieve_knowledge
        → synthesize_solution
          → generate_diagrams
            → generate_volume
              → validate
                → refine (if issues found, max 2 iterations)
                  → back to generate_diagrams
                → human_review (HITL gate, then END)
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

logger = logging.getLogger("ai_orchestrator.agents.solution_architect")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Maximum self-critique / refine iterations before forcing acceptance
_MAX_REFINE_ITERATIONS = 2


# ── State ─────────────────────────────────────────────────────────────────────

class SolutionArchitectState(TypedDict):
    deal_id: str
    opportunity_id: str
    deal: dict
    opportunity: dict
    rfp_requirements: list[dict]
    compliance_matrix: list[dict]
    company_strategy: dict
    knowledge_bundle: dict          # Retrieved from KnowledgeVault
    requirement_analysis: dict      # Deep parsed requirement categories
    selected_frameworks: list[str]  # e.g. ["C4", "TOGAF", "arc42"]
    technical_solution: dict        # Full solution across 17 architecture areas
    diagrams: list[dict]            # Generated Mermaid.js diagrams
    technical_volume: dict          # Proposal-ready section texts
    validation_report: dict         # Self-critique findings
    iteration_count: int            # Tracks refine loops
    messages: Annotated[list, operator.add]


# ── Django API helpers ─────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    token = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {token}"} if token else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}{path}", headers=_auth_headers()
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm(max_tokens: int = 4096) -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=max_tokens,
    )


async def _llm(system: str, human: str, max_tokens: int = 4096) -> str:
    """Single LLM call helper."""
    try:
        llm = _get_llm(max_tokens)
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=human),
        ])
        return response.content
    except Exception as exc:
        logger.error("LLM call failed in SolutionArchitectAgent: %s", exc)
        return f"[LLM unavailable: {exc}]"


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_context(state: SolutionArchitectState) -> dict:
    """Fetch deal, opportunity, RFP requirements, strategy, and knowledge vault."""
    logger.info("SA: Loading context for deal %s", state["deal_id"])

    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    opp_id = deal.get("opportunity") or state.get("opportunity_id", "")
    opportunity = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}

    # RFP requirements (from rfp app)
    rfp_data = await _get(
        f"/api/rfp/requirements/?deal={state['deal_id']}&limit=100", default={}
    )
    rfp_requirements = rfp_data.get("results", []) if isinstance(rfp_data, dict) else []

    # Company strategy
    strategy = await _get("/api/strategy/current/", default={})

    # Knowledge vault — retrieve approved documents relevant to architecture
    kv_data = await _get(
        "/api/knowledge-vault/?status=approved&limit=20", default={}
    )
    knowledge_docs = kv_data.get("results", []) if isinstance(kv_data, dict) else []
    knowledge_bundle = {
        "documents": [
            {"title": d.get("title"), "category": d.get("category"),
             "tags": d.get("tags", []), "snippet": (d.get("content") or "")[:500]}
            for d in knowledge_docs
        ],
        "total_documents": len(knowledge_docs),
    }

    return {
        "deal": deal,
        "opportunity": opportunity,
        "rfp_requirements": rfp_requirements,
        "company_strategy": strategy,
        "knowledge_bundle": knowledge_bundle,
        "messages": [HumanMessage(content=f"SA Agent starting for: {deal.get('title', state['deal_id'])}")],
    }


async def analyze_requirements(state: SolutionArchitectState) -> dict:
    """Deep analysis of ALL RFP requirements into categorised structure."""
    logger.info("SA: Analyzing requirements for deal %s", state["deal_id"])

    content = await _llm(
        system=(
            "You are a senior Solutions Architect with 20 years of U.S. federal IT "
            "contracting experience. Perform a deep analysis of the RFP requirements, "
            "categorizing every requirement and identifying key design decisions. "
            "Be precise, technical, and thorough."
        ),
        human=(
            f"Deal: {state['deal']}\n\n"
            f"Opportunity: {state['opportunity']}\n\n"
            f"RFP Requirements ({len(state['rfp_requirements'])} total):\n"
            f"{state['rfp_requirements'][:30]}\n\n"
            "Perform a DEEP requirement analysis. Produce:\n\n"
            "## 1. Functional Requirements\n"
            "List core system capabilities the solution must provide.\n\n"
            "## 2. Non-Functional Requirements\n"
            "Performance, scalability, availability (SLA), latency targets.\n\n"
            "## 3. Security & Compliance Requirements\n"
            "Specific frameworks (NIST, CMMC, FedRAMP, FISMA), data classification, "
            "clearance levels, encryption mandates.\n\n"
            "## 4. Integration Requirements\n"
            "External systems, APIs, data sources, legacy systems to interface with.\n\n"
            "## 5. Data Requirements\n"
            "Data volumes, sensitivity, retention policies, analytics needs.\n\n"
            "## 6. AI/ML Requirements (if present)\n"
            "Model accuracy targets, explainability, bias mitigation, real-time vs. batch.\n\n"
            "## 7. Infrastructure & Deployment Constraints\n"
            "Cloud provider, on-prem, hybrid, containerization, CI/CD, ATO boundary.\n\n"
            "## 8. Key Design Decisions\n"
            "Top 5 architectural decisions that must be made, with options and trade-offs.\n\n"
            "## 9. Risk Flags\n"
            "Conflicting requirements, impossible constraints, ambiguities needing clarification.\n\n"
            "## 10. Complexity Assessment\n"
            "Overall complexity: Low / Medium / High / Very High with justification."
        ),
        max_tokens=4096,
    )

    requirement_analysis = {
        "analysis_text": content,
        "requirements_count": len(state["rfp_requirements"]),
        "opportunity_title": state["opportunity"].get("title", ""),
    }

    return {
        "requirement_analysis": requirement_analysis,
        "messages": [HumanMessage(content="Requirements analysis complete.")],
    }


async def select_frameworks(state: SolutionArchitectState) -> dict:
    """Select the appropriate solutioning frameworks for this opportunity."""
    logger.info("SA: Selecting frameworks for deal %s", state["deal_id"])

    content = await _llm(
        system=(
            "You are an enterprise architect expert in federal IT. Select the optimal "
            "combination of architecture frameworks and methodologies for this specific "
            "government IT opportunity. Justify each selection."
        ),
        human=(
            f"Opportunity: {state['opportunity']}\n\n"
            f"Requirement Analysis Summary:\n"
            f"{state['requirement_analysis'].get('analysis_text', '')[:1000]}\n\n"
            "Select the appropriate frameworks from:\n"
            "- **C4 Model** (Context/Container/Component/Code diagrams — best for microservices)\n"
            "- **TOGAF / ArchiMate** (Enterprise architecture — best for large transformation)\n"
            "- **arc42** (Pragmatic documentation — best for agile teams)\n"
            "- **DoDAF** (DoD Architecture Framework — required for DoD programs)\n"
            "- **FedRAMP System Architecture** (required for cloud/SaaS)\n"
            "- **NIST Cybersecurity Framework** (security architecture overlay)\n"
            "- **Microservices Architecture Pattern** (distributed systems)\n"
            "- **Event-Driven Architecture** (real-time processing)\n"
            "- **Data Mesh / Lake Architecture** (data-heavy solutions)\n\n"
            "For each selected framework provide:\n"
            "1. Why it was selected for this specific opportunity\n"
            "2. Which diagrams/views it will produce\n"
            "3. How it maps to evaluation criteria\n\n"
            "List the selected frameworks as a comma-separated line starting with "
            "'SELECTED_FRAMEWORKS:' for easy parsing."
        ),
        max_tokens=2048,
    )

    # Extract framework list
    selected = []
    for line in content.split("\n"):
        if line.startswith("SELECTED_FRAMEWORKS:"):
            raw = line.replace("SELECTED_FRAMEWORKS:", "").strip()
            selected = [f.strip() for f in raw.split(",") if f.strip()]
            break
    if not selected:
        selected = ["C4 Model", "NIST Cybersecurity Framework"]

    return {
        "selected_frameworks": selected,
        "messages": [HumanMessage(content=f"Frameworks selected: {', '.join(selected)}")],
    }


async def retrieve_knowledge(state: SolutionArchitectState) -> dict:
    """Retrieve and synthesize relevant knowledge from the Knowledge Vault."""
    logger.info("SA: Retrieving knowledge for deal %s", state["deal_id"])

    kb = state["knowledge_bundle"]
    docs = kb.get("documents", [])

    if docs:
        # Filter knowledge docs relevant to this solution's context
        opp_title = state["opportunity"].get("title", "")
        frameworks = " ".join(state["selected_frameworks"])

        content = await _llm(
            system=(
                "You are a knowledge curator for a government contracting firm. "
                "Identify which reference documents are most relevant to the current "
                "solution and extract key insights to inform the architecture."
            ),
            human=(
                f"Opportunity: {opp_title}\n"
                f"Selected Frameworks: {frameworks}\n\n"
                f"Available Knowledge Documents ({len(docs)}):\n"
                + "\n".join(
                    f"- [{d['category']}] {d['title']}: {d['snippet']}"
                    for d in docs[:15]
                )
                + "\n\nFor each relevant document provide:\n"
                "1. Document title\n"
                "2. Key insights applicable to this solution\n"
                "3. Specific architecture patterns or best practices to apply"
            ),
            max_tokens=2048,
        )
        kb["relevant_insights"] = content
    else:
        kb["relevant_insights"] = (
            "No knowledge vault documents available. "
            "Solution will be generated from first principles using AI expertise."
        )

    return {
        "knowledge_bundle": kb,
        "messages": [HumanMessage(content=f"Knowledge retrieved: {len(docs)} documents processed.")],
    }


async def synthesize_solution(state: SolutionArchitectState) -> dict:
    """Core solutioning engine — generates a complete technical solution."""
    logger.info("SA: Synthesizing technical solution for deal %s", state["deal_id"])

    content = await _llm(
        system=(
            "You are a Principal Solutions Architect with deep expertise in U.S. federal IT "
            "systems. Synthesize a COMPLETE, NOVEL, TAILORED technical solution for this "
            "specific opportunity. This is not a generic template — every element must be "
            "directly tied to the RFP requirements. Be specific about technologies, "
            "cloud services, integration patterns, and implementation approaches."
        ),
        human=(
            f"Opportunity: {state['opportunity']}\n\n"
            f"Requirement Analysis:\n{state['requirement_analysis'].get('analysis_text', '')[:2000]}\n\n"
            f"Selected Frameworks: {', '.join(state['selected_frameworks'])}\n\n"
            f"Knowledge Insights:\n{state['knowledge_bundle'].get('relevant_insights', '')[:500]}\n\n"
            f"Company Strategy: {state['company_strategy']}\n\n"
            "Generate a COMPLETE technical solution covering ALL areas:\n\n"
            "## 1. Solution Overview & Vision\n"
            "Executive-level solution description (3-4 paragraphs).\n\n"
            "## 2. Architecture Approach\n"
            "Which frameworks used, which patterns applied, and why.\n\n"
            "## 3. System Context (C4 Level 1)\n"
            "External actors, system boundaries, key interfaces.\n\n"
            "## 4. Container Architecture (C4 Level 2)\n"
            "Major services, databases, APIs, and their relationships.\n\n"
            "## 5. Technology Stack\n"
            "Every major technology choice with justification.\n\n"
            "## 6. Data Architecture\n"
            "Data flows, storage strategy, ETL/ELT, analytics, data governance.\n\n"
            "## 7. AI/ML Architecture\n"
            "Models, training pipeline, serving infrastructure, MLOps.\n\n"
            "## 8. Security Architecture\n"
            "Zero Trust design, IAM, encryption at rest/transit, compliance controls.\n\n"
            "## 9. Infrastructure & Cloud Design\n"
            "Cloud topology, containers/Kubernetes, IaC, environments.\n\n"
            "## 10. Integration Architecture\n"
            "APIs, event bus, legacy system interfaces, data exchange protocols.\n\n"
            "## 11. DevSecOps & CI/CD Pipeline\n"
            "Toolchain, SAST/DAST/SCA, deployment strategy, release cadence.\n\n"
            "## 12. Scalability & Performance Design\n"
            "Auto-scaling strategy, caching, CDN, performance targets.\n\n"
            "## 13. Disaster Recovery & Business Continuity\n"
            "RTO/RPO targets, backup strategy, failover design.\n\n"
            "## 14. Transition & Migration Plan\n"
            "Phased migration approach, cutover strategy, data migration.\n\n"
            "## 15. Innovation Differentiators\n"
            "3-5 novel elements that set this solution apart from competitors.\n\n"
            "## 16. Risk Register\n"
            "Top 8 technical risks with probability, impact, and mitigations.\n\n"
            "## 17. Staffing & Skill Requirements\n"
            "Key roles, certifications required, team structure."
        ),
        max_tokens=4096,
    )

    technical_solution = {
        "full_solution": content,
        "deal_id": state["deal_id"],
        "opportunity_title": state["opportunity"].get("title", ""),
        "frameworks_used": state["selected_frameworks"],
    }

    return {
        "technical_solution": technical_solution,
        "messages": [HumanMessage(content="Technical solution synthesis complete.")],
    }


async def generate_diagrams(state: SolutionArchitectState) -> dict:
    """Generate architecture diagrams as Mermaid.js code."""
    logger.info("SA: Generating architecture diagrams for deal %s", state["deal_id"])

    solution_text = state["technical_solution"].get("full_solution", "")[:3000]

    content = await _llm(
        system=(
            "You are an expert software architect and technical illustrator. "
            "Generate production-quality Mermaid.js diagrams for a federal IT solution. "
            "Each diagram must be syntactically correct Mermaid.js that can be rendered "
            "directly. Use clear labels, appropriate shapes, and meaningful relationships. "
            "Wrap each diagram in a fenced code block with 'mermaid' as the language."
        ),
        human=(
            f"Technical Solution Summary:\n{solution_text}\n\n"
            f"Selected Frameworks: {', '.join(state['selected_frameworks'])}\n\n"
            "Generate the following diagrams:\n\n"
            "### Diagram 1: System Context (C4 Level 1)\n"
            "Show the system's external actors and boundary using C4 notation.\n\n"
            "### Diagram 2: Container Architecture (C4 Level 2)\n"
            "Show major containers (services, databases, APIs) and their interactions.\n\n"
            "### Diagram 3: Data Flow\n"
            "Show how data flows through the system from ingestion to consumption.\n\n"
            "### Diagram 4: Security Architecture\n"
            "Show the Zero Trust security layers, IAM, and compliance boundaries.\n\n"
            "### Diagram 5: Deployment Architecture\n"
            "Show the cloud infrastructure, AZ layout, and network topology.\n\n"
            "For each diagram provide:\n"
            "1. Diagram title\n"
            "2. The complete Mermaid.js code in a ```mermaid ... ``` block\n"
            "3. A 2-sentence description for proposal insertion"
        ),
        max_tokens=4096,
    )

    # Parse diagram blocks from the response
    import re
    diagram_blocks = re.findall(
        r'###\s+Diagram\s+(\d+):?\s*([^\n]+)\n(.*?)```mermaid\n(.*?)```(.*?)(?=###\s+Diagram|\Z)',
        content,
        re.DOTALL,
    )

    diagrams = []
    if diagram_blocks:
        for num, title, _, mermaid_code, description in diagram_blocks:
            diagrams.append({
                "number": int(num),
                "title": title.strip(),
                "mermaid_code": mermaid_code.strip(),
                "description": description.strip()[:500],
            })
    else:
        # Fallback: extract all mermaid blocks
        all_mermaid = re.findall(r'```mermaid\n(.*?)```', content, re.DOTALL)
        for idx, code in enumerate(all_mermaid, 1):
            diagrams.append({
                "number": idx,
                "title": f"Architecture Diagram {idx}",
                "mermaid_code": code.strip(),
                "description": "",
            })

    if not diagrams:
        # Provide a default system context diagram if parsing failed
        diagrams = [{
            "number": 1,
            "title": "System Context",
            "mermaid_code": (
                "graph TB\n"
                f"    User[End User] --> System[{state['opportunity'].get('title', 'Solution')[:40]}]\n"
                "    System --> Agency[Government Agency Systems]\n"
                "    System --> Cloud[Cloud Infrastructure]\n"
                "    System --> Security[Security & IAM]\n"
                "    style System fill:#0066cc,color:#fff"
            ),
            "description": "High-level system context diagram.",
        }]

    logger.info("SA: Generated %d architecture diagrams", len(diagrams))

    return {
        "diagrams": diagrams,
        "messages": [HumanMessage(content=f"Generated {len(diagrams)} architecture diagram(s).")],
    }


async def generate_volume(state: SolutionArchitectState) -> dict:
    """Generate full technical volume sections ready for proposal insertion."""
    logger.info("SA: Generating technical volume for deal %s", state["deal_id"])

    solution = state["technical_solution"].get("full_solution", "")[:3000]
    diagram_titles = [d["title"] for d in state["diagrams"]]

    content = await _llm(
        system=(
            "You are a proposal writer and solutions architect. Write compelling, "
            "evaluation-criteria-aligned technical volume sections in U.S. federal "
            "proposal style. Be specific, technical, and directly responsive to requirements. "
            "Use active voice, quantify claims where possible, and highlight differentiators."
        ),
        human=(
            f"Opportunity: {state['opportunity']}\n\n"
            f"Technical Solution:\n{solution}\n\n"
            f"Architecture Diagrams Available: {', '.join(diagram_titles)}\n\n"
            "Write the following Technical Volume (Volume I) sections:\n\n"
            "## Section 1: Understanding of Requirements\n"
            "Demonstrate deep understanding of the agency's mission and technical needs. "
            "2-3 paragraphs, directly referencing key RFP requirements.\n\n"
            "## Section 2: Technical Approach\n"
            "Full technical approach narrative. Describe the proposed solution, "
            "key design decisions, and how it meets every major requirement. "
            "5-7 paragraphs. Reference the architecture diagrams where appropriate.\n\n"
            "## Section 3: Architecture Overview\n"
            "Describe the system architecture, key components, and integration points. "
            "3-4 paragraphs. Structured for proposal Volume I.\n\n"
            "## Section 4: Innovation & Differentiators\n"
            "Describe 3-5 innovative elements of the solution that differentiate it "
            "from competitors and provide measurable value to the agency.\n\n"
            "## Section 5: Risk Mitigation\n"
            "Technical risk register with mitigations. Present as a structured narrative "
            "demonstrating proactive risk management.\n\n"
            "## Section 6: Technical Compliance Matrix\n"
            "For each major technical requirement, state: Requirement | How Addressed | "
            "Evidence/Section Reference. Format as a pipe-delimited table."
        ),
        max_tokens=4096,
    )

    # Parse sections
    import re
    sections: dict[str, str] = {}
    section_pattern = re.compile(r'##\s+Section\s+\d+:\s+([^\n]+)\n(.*?)(?=##\s+Section|\Z)', re.DOTALL)
    for m in section_pattern.finditer(content):
        sections[m.group(1).strip()] = m.group(2).strip()

    technical_volume = {
        "full_text": content,
        "sections": sections,
        "diagram_count": len(state["diagrams"]),
        "word_count_estimate": len(content.split()),
    }

    return {
        "technical_volume": technical_volume,
        "messages": [HumanMessage(content=f"Technical volume generated ({len(sections)} sections, ~{len(content.split())} words).")],
    }


async def validate_solution(state: SolutionArchitectState) -> dict:
    """Self-critique: validate the solution for completeness, accuracy, and win-ability."""
    logger.info(
        "SA: Validating solution (iteration %d) for deal %s",
        state["iteration_count"],
        state["deal_id"],
    )

    solution_preview = state["technical_solution"].get("full_solution", "")[:2000]
    volume_preview = state["technical_volume"].get("full_text", "")[:1000]

    content = await _llm(
        system=(
            "You are a red team reviewer and chief architect for a government contracting firm. "
            "Your job is to critically evaluate a proposed technical solution and identify "
            "gaps, weaknesses, and risks BEFORE it goes to the customer. Be brutally honest."
        ),
        human=(
            f"Opportunity: {state['opportunity']}\n\n"
            f"Technical Solution (preview):\n{solution_preview}\n\n"
            f"Technical Volume (preview):\n{volume_preview}\n\n"
            f"Architecture Diagrams: {len(state['diagrams'])} generated\n\n"
            "Evaluate this solution on:\n\n"
            "## 1. Requirements Coverage\n"
            "Are ALL key requirements addressed? List any gaps.\n\n"
            "## 2. Technical Soundness\n"
            "Are the architectural choices technically sound? Any anti-patterns?\n\n"
            "## 3. Compliance Completeness\n"
            "Are all security/compliance requirements fully addressed?\n\n"
            "## 4. Win-ability\n"
            "Would this solution score well against evaluation criteria? What's weak?\n\n"
            "## 5. Risk Assessment\n"
            "What risks in this solution could cause evaluation score deductions?\n\n"
            "## 6. Verdict\n"
            "PASS (ready for human review) or REVISE (requires refinement). "
            "State on a line by itself starting with 'VERDICT:'"
        ),
        max_tokens=2048,
    )

    verdict = "PASS"
    for line in content.split("\n"):
        if line.strip().startswith("VERDICT:"):
            verdict_text = line.replace("VERDICT:", "").strip().upper()
            if "REVISE" in verdict_text:
                verdict = "REVISE"
            break

    validation_report = {
        "review_text": content,
        "verdict": verdict,
        "iteration": state["iteration_count"],
    }

    return {
        "validation_report": validation_report,
        "messages": [HumanMessage(content=f"Validation complete. Verdict: {verdict}")],
    }


async def refine_solution(state: SolutionArchitectState) -> dict:
    """Refine the solution based on validation critique."""
    logger.info(
        "SA: Refining solution (iteration %d) for deal %s",
        state["iteration_count"],
        state["deal_id"],
    )

    critique = state["validation_report"].get("review_text", "")
    solution = state["technical_solution"].get("full_solution", "")

    refined = await _llm(
        system=(
            "You are a Principal Solutions Architect refining a technical solution based on "
            "red team feedback. Address each issue identified, strengthen weak areas, and "
            "ensure all requirements are explicitly covered. Maintain the same structure."
        ),
        human=(
            f"Original Solution:\n{solution[:3000]}\n\n"
            f"Red Team Critique:\n{critique[:1500]}\n\n"
            "Revise the technical solution to address all issues raised. "
            "Keep all strong elements. Explicitly note what changed with [REVISED] markers."
        ),
        max_tokens=4096,
    )

    updated_solution = dict(state["technical_solution"])
    updated_solution["full_solution"] = refined
    updated_solution["revision_notes"] = critique[:500]

    return {
        "technical_solution": updated_solution,
        "iteration_count": state["iteration_count"] + 1,
        "messages": [HumanMessage(content=f"Solution refined (iteration {state['iteration_count'] + 1}).")],
    }


# ── Routing ────────────────────────────────────────────────────────────────────

def route_validation(state: SolutionArchitectState) -> str:
    """Route after validation: PASS → end; REVISE → refine (up to max iterations)."""
    verdict = state["validation_report"].get("verdict", "PASS")
    iterations = state["iteration_count"]

    if verdict == "REVISE" and iterations < _MAX_REFINE_ITERATIONS:
        logger.info("SA: Routing to refine (iteration %d/%d)", iterations, _MAX_REFINE_ITERATIONS)
        return "refine"

    logger.info("SA: Routing to END (verdict=%s, iterations=%d)", verdict, iterations)
    return "end"


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_solution_architect_graph() -> StateGraph:
    """Construct and compile the Solution Architect LangGraph workflow."""
    workflow = StateGraph(SolutionArchitectState)

    workflow.add_node("load_context", load_context)
    workflow.add_node("analyze_requirements", analyze_requirements)
    workflow.add_node("select_frameworks", select_frameworks)
    workflow.add_node("retrieve_knowledge", retrieve_knowledge)
    workflow.add_node("synthesize_solution", synthesize_solution)
    workflow.add_node("generate_diagrams", generate_diagrams)
    workflow.add_node("generate_volume", generate_volume)
    workflow.add_node("validate", validate_solution)
    workflow.add_node("refine", refine_solution)

    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "analyze_requirements")
    workflow.add_edge("analyze_requirements", "select_frameworks")
    workflow.add_edge("select_frameworks", "retrieve_knowledge")
    workflow.add_edge("retrieve_knowledge", "synthesize_solution")
    workflow.add_edge("synthesize_solution", "generate_diagrams")
    workflow.add_edge("generate_diagrams", "generate_volume")
    workflow.add_edge("generate_volume", "validate")

    # Conditional after validation: refine or end
    workflow.add_conditional_edges(
        "validate",
        route_validation,
        {"refine": "refine", "end": END},
    )
    # After refinement, re-generate diagrams and volume with the improved solution
    workflow.add_edge("refine", "generate_diagrams")

    return workflow.compile()


solution_architect_graph = build_solution_architect_graph()


# ── Agent class ───────────────────────────────────────────────────────────────

class SolutionArchitectAgent(BaseAgent):
    """
    Fully Autonomous AI Solutions Architect.

    Given a deal/opportunity, produces a COMPLETE technical solution including:
    - Deep requirement analysis across 10 categories
    - Framework selection (C4, TOGAF, arc42, DoDAF, FedRAMP, etc.)
    - Knowledge Vault retrieval and synthesis
    - Full solution across 17 architecture areas
    - 5 Mermaid.js architecture diagrams
    - Complete Technical Volume (Volume I) sections
    - Self-critique validation with up to 2 refinement iterations
    """

    agent_name = "solution_architect_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run solution architecture for a deal.

        Args:
            input_data: Must contain 'deal_id'. Optional: 'opportunity_id'.

        Returns:
            dict with keys: deal_id, requirement_analysis, selected_frameworks,
            technical_solution, diagrams, technical_volume, validation_report.
        """
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial_state: SolutionArchitectState = {
            "deal_id": deal_id,
            "opportunity_id": input_data.get("opportunity_id", ""),
            "deal": {},
            "opportunity": {},
            "rfp_requirements": [],
            "compliance_matrix": [],
            "company_strategy": {},
            "knowledge_bundle": {},
            "requirement_analysis": {},
            "selected_frameworks": [],
            "technical_solution": {},
            "diagrams": [],
            "technical_volume": {},
            "validation_report": {},
            "iteration_count": 0,
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Solution Architect starting for deal {deal_id}"},
                execution_id=deal_id,
            )

            final_state = await solution_architect_graph.ainvoke(initial_state)

            await self.emit_event(
                "output",
                {
                    "diagrams_generated": len(final_state["diagrams"]),
                    "frameworks_used": final_state["selected_frameworks"],
                    "validation_verdict": final_state["validation_report"].get("verdict"),
                },
                execution_id=deal_id,
            )

            return {
                "deal_id": final_state["deal_id"],
                "requirement_analysis": final_state["requirement_analysis"],
                "selected_frameworks": final_state["selected_frameworks"],
                "knowledge_bundle": {
                    "documents_count": final_state["knowledge_bundle"].get("total_documents", 0),
                    "insights_summary": (
                        final_state["knowledge_bundle"].get("relevant_insights", "")[:500]
                    ),
                },
                "technical_solution": final_state["technical_solution"],
                "diagrams": final_state["diagrams"],
                "technical_volume": final_state["technical_volume"],
                "validation_report": final_state["validation_report"],
                "iterations": final_state["iteration_count"],
            }

        except Exception as exc:
            logger.exception("SolutionArchitectAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
