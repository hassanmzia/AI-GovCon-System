"""Endpoint that returns Mermaid diagrams of the LangGraph agent workflows."""

import logging
import re
from fastapi import APIRouter

logger = logging.getLogger("ai_orchestrator.routers.visualize")

router = APIRouter()


def _sanitize_langgraph_mermaid(code: str) -> str:
    """Clean up LangGraph's draw_mermaid() output for client-side rendering.

    LangGraph emits YAML frontmatter, HTML tags in labels, :::class suffixes,
    and classDef directives that break mermaid.js in the browser.
    """
    # Strip YAML frontmatter (---\nconfig:\n...\n---)
    code = re.sub(r"^---[\s\S]*?---\s*", "", code, count=1)

    lines = []
    for line in code.split("\n"):
        stripped = line.strip()

        # Skip classDef lines
        if stripped.startswith("classDef "):
            continue

        # Remove :::className suffixes
        line = re.sub(r":::[\w]+", "", line)

        # Replace <p>...</p> with plain text in node labels
        line = re.sub(r"<p>(.*?)</p>", r"\1", line)

        # Clean up __start__ / __end__ to readable names
        line = line.replace("__start__", "Start")
        line = line.replace("__end__", "End")

        # Convert ([...]) round-rect nodes to normal [...] for Start/End
        line = re.sub(r"Start\(\[([^\]]*)\]\)", r"Start((\1))", line)
        line = re.sub(r"End\(\[([^\]]*)\]\)", r"End((\1))", line)

        # Make node IDs into readable labels: load_company_profile -> Load Company Profile
        def _humanize_node(match: re.Match) -> str:
            node_id = match.group(1)
            label = node_id.replace("_", " ").title()
            return f"{node_id}[{label}]"

        # Match bare node declarations like "    node_name(node_name)" and convert
        line = re.sub(
            r"(\w+)\(\1\)",
            _humanize_node,
            line,
        )

        lines.append(line)

    result = "\n".join(lines).strip()

    # Ensure it starts with graph directive
    if not re.match(r"^(graph|flowchart)\s+(TD|TB|LR|RL|BT)", result):
        result = "graph TD\n" + result

    return result


def _get_proposal_graph_mermaid() -> str:
    """Generate Mermaid from the compiled proposal LangGraph."""
    try:
        from src.graphs.proposal_graph import proposal_graph
        raw = proposal_graph.get_graph().draw_mermaid()
        return _sanitize_langgraph_mermaid(raw)
    except Exception as exc:
        logger.warning("Could not generate proposal graph mermaid: %s", exc)
        return """graph TD
    load_deal_context[Load Deal Context] --> load_proposal_inputs[Load Proposal Inputs]
    load_proposal_inputs --> match_past_performance[Match Past Performance]
    match_past_performance --> plan_sections[Plan Sections]
    plan_sections --> generate_sections[Generate Sections]
    generate_sections --> run_ai_review[AI Review - Pink Team]
    run_ai_review --> human_review_gate{Human Review Gate}
    human_review_gate -->|Approved| generate_docx_output[Generate DOCX Output]
    human_review_gate -->|Needs Revision| await_approval[Await Approval]
    generate_docx_output --> done((End))
    await_approval --> done"""


def _get_daily_scan_graph_mermaid() -> str:
    """Generate Mermaid from the compiled daily scan LangGraph."""
    try:
        from src.graphs.daily_scan_graph import build_daily_scan_graph
        graph = build_daily_scan_graph()
        raw = graph.get_graph().draw_mermaid()
        return _sanitize_langgraph_mermaid(raw)
    except Exception as exc:
        logger.warning("Could not generate daily scan graph mermaid: %s", exc)
        return """graph TD
    load_company_profile[Load Company Profile] --> scan_sam_gov[Scan SAM.gov]
    scan_sam_gov --> score_opportunities[Score Opportunities]
    score_opportunities --> select_top_30[Select Top 30]
    select_top_30 --> apply_bandit_selection[Thompson Sampling Top 10]
    apply_bandit_selection --> persist_scores[Persist Scores]
    persist_scores --> send_daily_digest[Send Daily Digest]
    send_daily_digest --> done((End))"""


# The stage trigger pipeline is not a LangGraph StateGraph but a sequential
# orchestrator. This diagram shows the full deal lifecycle agent chains.
STAGE_PIPELINE_MERMAID = """graph TD
    subgraph intake[Stage: Intake]
        scout[Scout Agent<br/>Assess Opportunity]
    end

    subgraph qualify[Stage: Qualify]
        fit[Fit Agent<br/>Score PWin]
        strategy_q[Strategy Agent<br/>Bid/No-Bid Assessment]
        fit --> strategy_q
    end

    subgraph bid_no_bid[Stage: Bid/No-Bid]
        strategy_b[Strategy Agent<br/>Strategic Alignment]
        research_b[Research Agent<br/>Agency Due Diligence]
        marketing_b[Marketing Agent<br/>Develop Win Themes]
        strategy_b --> research_b --> marketing_b
        hitl_bnb{HITL Gate<br/>Bid/No-Bid Approval}
        marketing_b --> hitl_bnb
    end

    subgraph capture_plan[Stage: Capture Plan]
        capture[Capture Agent<br/>Generate Plan]
        research_c[Research Agent<br/>Competitor Intel]
        comp_sim[Competitor Sim Agent<br/>Simulate Competitors]
        teaming[Teaming Agent<br/>Identify Partners]
        capture --> research_c --> comp_sim --> teaming
    end

    subgraph proposal_dev[Stage: Proposal Development]
        rfp[RFP Analyst<br/>Parse Requirements]
        past_perf[Past Performance<br/>Match Records]
        sol_arch[Solution Architect<br/>Design Solution]
        prop_writer[Proposal Writer<br/>Draft Sections]
        pricing[Pricing Agent<br/>Build Scenarios]
        sec_comp_p[Security Compliance<br/>Map Controls]
        rfp --> past_perf --> sol_arch --> prop_writer --> pricing --> sec_comp_p
    end

    subgraph red_team[Stage: Red Team]
        red[Red Team Agent<br/>Evaluate Proposal]
        compliance[Compliance Agent<br/>Verify FAR/DFARS]
        qa[QA Agent<br/>Quality Check]
        synth_eval[Synthetic Evaluator<br/>Simulate Evaluation]
        red --> compliance --> qa --> synth_eval
    end

    subgraph final_review[Stage: Final Review]
        marketing_f[Marketing Agent<br/>Finalize Win Themes]
        legal[Legal Agent<br/>Final Compliance]
        marketing_f --> legal
        hitl_fr{HITL Gate<br/>Final Review Approval}
        legal --> hitl_fr
    end

    subgraph submit[Stage: Submit]
        hitl_sub{HITL Gate<br/>Submission Approval}
        submission[Submission Agent<br/>Package & Submit]
        hitl_sub --> submission
    end

    subgraph contract_setup[Stage: Contract Setup]
        contract[Contract Agent<br/>Generate Contract]
    end

    subgraph post_award[Stage: Post Award]
        learning_w[Learning Agent<br/>Record Win]
        learning_l[Learning Agent<br/>Record Loss]
    end

    intake --> qualify --> bid_no_bid --> capture_plan --> proposal_dev
    proposal_dev --> red_team --> final_review --> submit
    submit --> contract_setup
    submit --> post_award

    style intake fill:#e3f2fd,stroke:#1565c0
    style qualify fill:#e8f5e9,stroke:#2e7d32
    style bid_no_bid fill:#fff3e0,stroke:#ef6c00
    style capture_plan fill:#f3e5f5,stroke:#7b1fa2
    style proposal_dev fill:#e8eaf6,stroke:#283593
    style red_team fill:#fce4ec,stroke:#c62828
    style final_review fill:#e0f7fa,stroke:#00838f
    style submit fill:#f1f8e9,stroke:#558b2f
    style contract_setup fill:#fff8e1,stroke:#f9a825
    style post_award fill:#efebe9,stroke:#4e342e"""


# Master system architecture showing all 19 agents and how they connect
SYSTEM_ARCHITECTURE_MERMAID = """graph LR
    subgraph discovery[Discovery & Qualification]
        scout_agent[Scout<br/>Opportunity Discovery]
        fit_agent[Fit<br/>PWin Scoring]
        competitor_sim_agent[Competitor Sim<br/>Competitive Intel]
    end

    subgraph capture[Capture & Strategy]
        teaming_agent[Teaming<br/>Partner Identification]
        rfp_analyst_agent[RFP Analyst<br/>Requirements Parsing]
        compliance_agent[Compliance<br/>FAR/DFARS Verification]
    end

    subgraph solution[Solution Design]
        solution_architect_agent[Solution Architect<br/>Technical Design]
        pricing_agent[Pricing<br/>Cost Model & PTW]
        security_compliance_agent[Security<br/>NIST/508 Compliance]
    end

    subgraph authoring[Proposal Authoring]
        proposal_writer_agent[Proposal Writer<br/>Section Drafting]
        past_performance_agent[Past Performance<br/>Record Matching]
        management_approach_agent[Management<br/>Approach Drafting]
        marketing_agent[Marketing<br/>Win Themes]
    end

    subgraph review[Review & QA]
        red_team_agent[Red Team<br/>Adversarial Review]
        synthetic_evaluator_agent[Synthetic Evaluator<br/>AI Scoring]
        cui_handler_agent[CUI Handler<br/>CUI Scanning]
    end

    subgraph delivery[Submission & Learning]
        submission_agent[Submission<br/>Package & Deliver]
        learning_agent[Learning<br/>Win/Loss Analysis]
        deal_pipeline_agent[Deal Pipeline<br/>Forecasting]
    end

    discovery --> capture --> solution --> authoring --> review --> delivery

    style discovery fill:#e3f2fd,stroke:#1565c0
    style capture fill:#e8f5e9,stroke:#2e7d32
    style solution fill:#e8eaf6,stroke:#283593
    style authoring fill:#f3e5f5,stroke:#7b1fa2
    style review fill:#fce4ec,stroke:#c62828
    style delivery fill:#f1f8e9,stroke:#558b2f"""


@router.get("/ai/graphs", tags=["visualization"])
async def list_graphs():
    """Return metadata about available LangGraph workflow visualizations."""
    return {
        "graphs": [
            {
                "id": "system_architecture",
                "title": "Agent System Architecture",
                "description": "All 19 GovCon agents organized by functional area",
                "type": "architecture",
            },
            {
                "id": "stage_pipeline",
                "title": "Deal Stage Pipeline",
                "description": "Agent chains triggered at each deal stage transition",
                "type": "pipeline",
            },
            {
                "id": "proposal_graph",
                "title": "Proposal Generation Graph",
                "description": "LangGraph workflow: RFP analysis → drafting → review → DOCX output",
                "type": "langgraph",
            },
            {
                "id": "daily_scan_graph",
                "title": "Daily Opportunity Scan",
                "description": "LangGraph workflow: SAM.gov scan → scoring → Thompson sampling → digest",
                "type": "langgraph",
            },
        ]
    }


@router.get("/ai/graphs/{graph_id}/mermaid", tags=["visualization"])
async def get_graph_mermaid(graph_id: str):
    """Return the Mermaid diagram code for a specific graph."""
    graphs = {
        "system_architecture": {
            "title": "Agent System Architecture",
            "mermaid": SYSTEM_ARCHITECTURE_MERMAID,
        },
        "stage_pipeline": {
            "title": "Deal Stage Pipeline",
            "mermaid": STAGE_PIPELINE_MERMAID,
        },
        "proposal_graph": {
            "title": "Proposal Generation Graph",
            "mermaid": _get_proposal_graph_mermaid(),
        },
        "daily_scan_graph": {
            "title": "Daily Opportunity Scan",
            "mermaid": _get_daily_scan_graph_mermaid(),
        },
    }

    if graph_id not in graphs:
        return {"error": f"Graph '{graph_id}' not found", "available": list(graphs.keys())}

    return graphs[graph_id]
