"""Deep Research Agent using LangGraph."""
import logging
import os
from typing import Annotated, Any
import operator

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.research")


# ── State ─────────────────────────────────────────────────────────────────────

class ResearchState(TypedDict):
    query: str
    research_type: str  # "agency_due_diligence" | "competitor_intelligence" | "market_analysis" | "opportunity_specific"
    search_results: list[dict]
    analysis: str
    findings_summary: str
    sources: list[dict]
    report: str
    key_insights: list[str]
    messages: Annotated[list, operator.add]


# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4096,
    )


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def plan_research(state: ResearchState) -> dict:
    """Claude breaks the query into sub-topics to research."""
    logger.info("Planning research for query: %s", state["query"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a senior research director at a government contracting consulting firm. "
            "Your job is to decompose a research query into specific, actionable sub-topics "
            "that will yield comprehensive intelligence. Be precise and methodical."
        )
    )
    human = HumanMessage(
        content=(
            f"Research Query: {state['query']}\n"
            f"Research Type: {state['research_type']}\n\n"
            "Break this into 4-6 specific sub-topics to investigate. "
            "For each sub-topic, provide:\n"
            "1. Sub-topic title\n"
            "2. Key questions to answer\n"
            "3. Why this is important for the overall research\n\n"
            "Format as a numbered list."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        plan_content = response.content
    except Exception as exc:
        logger.error("LLM call failed in plan_research: %s", exc)
        plan_content = f"1. Overview of {state['query']}\n2. Key findings\n3. Recommendations"

    return {
        "messages": [
            HumanMessage(content=f"Research plan created for: {state['query']}\n\n{plan_content}")
        ],
    }


async def gather_sources(state: ResearchState) -> dict:
    """
    Simulated web search: Claude generates realistic-looking search result summaries
    based on the query since no live web search is available in this implementation.
    """
    logger.info("Gathering sources for: %s", state["query"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a research assistant generating simulated search result summaries. "
            "Based on the research query, generate 5-7 realistic-looking search results "
            "that would be found when researching this topic. Include plausible sources "
            "from government websites, industry publications, and news outlets."
        )
    )
    human = HumanMessage(
        content=(
            f"Research Query: {state['query']}\n"
            f"Research Type: {state['research_type']}\n\n"
            "Generate 5-7 simulated search results. For each result provide:\n"
            "- title: Article/document title\n"
            "- url: Plausible URL (e.g., agency.gov, industry-publication.com)\n"
            "- snippet: 2-3 sentence summary of the content\n"
            "- source_type: government | industry | news | academic\n\n"
            "Return as a structured list."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in gather_sources: %s", exc)
        content = "Source gathering unavailable."

    # Parse response into structured source dicts
    sources = []
    current_source: dict[str, str] = {}
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            if current_source:
                sources.append(current_source)
                current_source = {}
            continue
        for field in ("title", "url", "snippet", "source_type"):
            if line.lower().startswith(f"{field}:"):
                current_source[field] = line.split(":", 1)[-1].strip()
                break
    if current_source:
        sources.append(current_source)

    # Fallback: create a single source entry with raw content
    if not sources:
        sources = [{"title": "Research Results", "url": "", "snippet": content, "source_type": "generated"}]

    search_results = [{"query": state["query"], "results": sources}]

    return {
        "search_results": search_results,
        "sources": sources,
        "messages": [HumanMessage(content=f"Gathered {len(sources)} sources.")],
    }


async def analyze_findings(state: ResearchState) -> dict:
    """Claude synthesizes information into coherent analysis."""
    logger.info("Analyzing findings")
    llm = _get_llm()

    sources_text = "\n\n".join(
        f"Source: {s.get('title', 'Unknown')}\nURL: {s.get('url', '')}\n{s.get('snippet', '')}"
        for s in state["sources"]
    )

    system = SystemMessage(
        content=(
            "You are a senior intelligence analyst at a government contracting firm. "
            "Synthesize research findings into a coherent, insightful analysis. "
            "Identify patterns, draw conclusions, and highlight strategic implications."
        )
    )
    human = HumanMessage(
        content=(
            f"Research Query: {state['query']}\n"
            f"Research Type: {state['research_type']}\n\n"
            f"Source Material:\n{sources_text}\n\n"
            "Provide a comprehensive analysis that:\n"
            "1. Synthesizes the key information\n"
            "2. Identifies patterns and trends\n"
            "3. Draws actionable conclusions\n"
            "4. Highlights strategic implications for a government contractor\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        analysis = response.content
    except Exception as exc:
        logger.error("LLM call failed in analyze_findings: %s", exc)
        analysis = "Analysis unavailable due to API error."

    # Create a concise findings summary (first 500 chars of analysis)
    findings_summary = analysis[:500].rsplit(" ", 1)[0] + "..." if len(analysis) > 500 else analysis

    return {
        "analysis": analysis,
        "findings_summary": findings_summary,
        "messages": [HumanMessage(content="Findings analysis complete.")],
    }


async def write_report(state: ResearchState) -> dict:
    """Claude writes a consulting-quality report with sections, findings, and recommendations."""
    logger.info("Writing research report")
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a partner at a top government contracting consulting firm. "
            "Write professional, consulting-quality research reports. "
            "Reports should be structured, evidence-based, and actionable."
        )
    )
    human = HumanMessage(
        content=(
            f"Research Query: {state['query']}\n"
            f"Research Type: {state['research_type']}\n\n"
            f"Analysis:\n{state['analysis']}\n\n"
            "Write a structured consulting report with these sections:\n"
            "1. Executive Summary\n"
            "2. Background & Context\n"
            "3. Key Findings\n"
            "4. Analysis & Implications\n"
            "5. Recommendations\n"
            "6. Appendix: Sources\n\n"
            "The report should be professional, concise, and actionable."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        report = response.content
    except Exception as exc:
        logger.error("LLM call failed in write_report: %s", exc)
        report = f"# Research Report\n\n**Query:** {state['query']}\n\nReport generation failed: {exc}"

    return {
        "report": report,
        "messages": [HumanMessage(content="Research report written.")],
    }


async def extract_key_insights(state: ResearchState) -> dict:
    """Extract actionable insights as bullet points."""
    logger.info("Extracting key insights")
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a strategic advisor extracting the most important, actionable insights "
            "from research for busy executives. Be crisp, specific, and action-oriented."
        )
    )
    human = HumanMessage(
        content=(
            f"Based on this research report, extract 5-8 key actionable insights:\n\n"
            f"{state['report']}\n\n"
            "Format as a numbered list. Each insight should be one concise, actionable sentence."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in extract_key_insights: %s", exc)
        content = "1. Key insight extraction unavailable due to API error."

    # Parse numbered list
    insights = []
    for line in content.split("\n"):
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            insight = line.split(".", 1)[-1].strip()
            if insight:
                insights.append(insight)

    if not insights:
        insights = [content.strip()]

    return {
        "key_insights": insights,
        "messages": [HumanMessage(content=f"Extracted {len(insights)} key insights.")],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_research_graph() -> StateGraph:
    """Construct and compile the research LangGraph workflow."""
    workflow = StateGraph(ResearchState)

    workflow.add_node("plan_research", plan_research)
    workflow.add_node("gather_sources", gather_sources)
    workflow.add_node("analyze_findings", analyze_findings)
    workflow.add_node("write_report", write_report)
    workflow.add_node("extract_key_insights", extract_key_insights)

    workflow.set_entry_point("plan_research")
    workflow.add_edge("plan_research", "gather_sources")
    workflow.add_edge("gather_sources", "analyze_findings")
    workflow.add_edge("analyze_findings", "write_report")
    workflow.add_edge("write_report", "extract_key_insights")
    workflow.add_edge("extract_key_insights", END)

    return workflow.compile()


# Compiled graph instance (exported for src/graphs/research_graph.py)
research_graph = build_research_graph()


# ── Agent class ───────────────────────────────────────────────────────────────

class ResearchAgent(BaseAgent):
    """LangGraph-based Deep Research Agent."""

    agent_name = "research_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run deep research on a topic.

        Args:
            input_data: Must contain 'query'. Optional: 'research_type'.

        Returns:
            dict with keys: query, research_type, report, key_insights, sources, findings_summary.
        """
        query = input_data.get("query", "")
        if not query:
            return {"error": "query is required"}

        research_type = input_data.get("research_type", "market_analysis")

        initial_state: ResearchState = {
            "query": query,
            "research_type": research_type,
            "search_results": [],
            "analysis": "",
            "findings_summary": "",
            "sources": [],
            "report": "",
            "key_insights": [],
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Starting deep research: {query}"},
                execution_id=query[:50],
            )
            final_state = await research_graph.ainvoke(initial_state)
            await self.emit_event(
                "output",
                {"insights_count": len(final_state["key_insights"])},
                execution_id=query[:50],
            )
            return {
                "query": final_state["query"],
                "research_type": final_state["research_type"],
                "report": final_state["report"],
                "key_insights": final_state["key_insights"],
                "sources": final_state["sources"],
                "findings_summary": final_state["findings_summary"],
            }
        except Exception as exc:
            logger.exception("ResearchAgent.run failed for query: %s", query)
            await self.emit_event("error", {"error": str(exc)}, execution_id=query[:50])
            return {"error": str(exc), "query": query}
