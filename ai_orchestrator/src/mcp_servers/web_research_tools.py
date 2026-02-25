"""MCP tool server: Web search, news, and academic research."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.web_research")

_BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "")
_SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
_PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
_TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


async def web_search(
    query: str,
    num_results: int = 10,
    search_type: str = "web",
    date_range: str | None = None,
) -> dict[str, Any]:
    """Search the web for *query* and return ranked results.

    Tries providers in order: Tavily → Brave → Serper → fallback stub.

    Args:
        query: Search query string.
        num_results: Number of results to return.
        search_type: "web", "news", or "academic".
        date_range: Optional date filter (e.g. "past_week", "past_month", "past_year").

    Returns:
        Dict with keys: query, results (list of {title, url, snippet, date}).
    """
    if _TAVILY_API_KEY:
        return await _tavily_search(query, num_results, search_type)
    if _BRAVE_API_KEY:
        return await _brave_search(query, num_results, search_type)
    if _SERPER_API_KEY:
        return await _serper_search(query, num_results, search_type)

    logger.warning("No web search API key configured; returning empty results")
    return {"query": query, "results": [], "provider": "none"}


async def fetch_webpage(url: str, extract_text: bool = True) -> dict[str, Any]:
    """Fetch and optionally extract text from a webpage.

    Args:
        url: The URL to fetch.
        extract_text: If True, extract clean text from HTML.

    Returns:
        Dict with keys: url, title, text, status_code.
    """
    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; DealManagerBot/1.0)"},
        ) as client:
            resp = await client.get(url)
            html = resp.text

        title = ""
        text = html

        if extract_text:
            try:
                from bs4 import BeautifulSoup  # type: ignore

                soup = BeautifulSoup(html, "html.parser")
                title_tag = soup.find("title")
                title = title_tag.text.strip() if title_tag else ""
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
            except ImportError:
                pass

        return {
            "url": url,
            "title": title,
            "text": text[:50000],  # cap at 50k chars
            "char_count": len(text),
            "status_code": resp.status_code,
        }
    except Exception as exc:
        logger.error("Webpage fetch failed for %s: %s", url, exc)
        return {"url": url, "text": "", "error": str(exc)}


async def search_news(
    query: str,
    num_results: int = 10,
    days_back: int = 30,
) -> dict[str, Any]:
    """Search recent news articles about *query*.

    Args:
        query: News search query.
        num_results: Number of articles.
        days_back: How many days back to search.

    Returns:
        Dict with results list (title, url, snippet, published_date, source).
    """
    return await web_search(query, num_results=num_results, search_type="news")


async def search_academic(query: str, num_results: int = 5) -> dict[str, Any]:
    """Search academic sources (Semantic Scholar, arXiv) for *query*.

    Args:
        query: Academic search query.
        num_results: Number of results.

    Returns:
        Dict with results list (title, url, abstract, authors, year).
    """
    try:
        # Try Semantic Scholar API (no API key required for basic use)
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": query,
                    "limit": num_results,
                    "fields": "title,abstract,authors,year,url,externalIds",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for paper in data.get("data", []):
                results.append(
                    {
                        "title": paper.get("title", ""),
                        "abstract": paper.get("abstract", ""),
                        "authors": [a["name"] for a in paper.get("authors", [])],
                        "year": paper.get("year"),
                        "url": paper.get("url", ""),
                    }
                )
            return {"query": query, "results": results, "provider": "semantic_scholar"}
    except Exception as exc:
        logger.warning("Semantic Scholar search failed: %s", exc)

    return await web_search(f"site:arxiv.org OR site:scholar.google.com {query}", num_results)


async def deep_research(
    topic: str,
    research_questions: list[str] | None = None,
    num_sources: int = 15,
) -> dict[str, Any]:
    """Conduct multi-step deep research on *topic*, synthesizing multiple sources.

    Args:
        topic: Main research topic.
        research_questions: Specific questions to answer.
        num_sources: Number of sources to gather.

    Returns:
        Dict with topic, key_findings (list), sources (list), synthesis (str).
    """
    if _PERPLEXITY_API_KEY:
        return await _perplexity_research(topic, research_questions)

    # Manual multi-step research
    questions = research_questions or [
        f"What is {topic}?",
        f"Key players and competitors in {topic}",
        f"Latest developments in {topic}",
        f"Market size and trends for {topic}",
    ]

    all_results = []
    for q in questions[:4]:
        res = await web_search(q, num_results=5)
        all_results.extend(res.get("results", []))

    sources = list({r["url"]: r for r in all_results if r.get("url")}.values())

    return {
        "topic": topic,
        "research_questions": questions,
        "sources": sources[:num_sources],
        "key_findings": [r.get("snippet", "") for r in sources[:5]],
        "synthesis": f"Research gathered from {len(sources)} sources on: {topic}",
    }


# ── Provider implementations ──────────────────────────────────────────────────

async def _tavily_search(query: str, num_results: int, search_type: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": _TAVILY_API_KEY,
                    "query": query,
                    "max_results": num_results,
                    "search_depth": "advanced",
                    "topic": "news" if search_type == "news" else "general",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "score": r.get("score", 0),
                }
                for r in data.get("results", [])
            ]
            return {"query": query, "results": results, "provider": "tavily"}
    except Exception as exc:
        logger.warning("Tavily search failed: %s", exc)
        return {"query": query, "results": [], "provider": "tavily", "error": str(exc)}


async def _brave_search(query: str, num_results: int, search_type: str) -> dict:
    try:
        endpoint = "https://api.search.brave.com/res/v1/"
        endpoint += "news/search" if search_type == "news" else "web/search"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                endpoint,
                params={"q": query, "count": num_results},
                headers={"Accept": "application/json", "X-Subscription-Token": _BRAVE_API_KEY},
            )
            resp.raise_for_status()
            data = resp.json()
            web_results = data.get("web", {}).get("results", [])
            results = [
                {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("description", "")}
                for r in web_results
            ]
            return {"query": query, "results": results, "provider": "brave"}
    except Exception as exc:
        logger.warning("Brave search failed: %s", exc)
        return {"query": query, "results": [], "provider": "brave", "error": str(exc)}


async def _serper_search(query: str, num_results: int, search_type: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": num_results},
                headers={"X-API-KEY": _SERPER_API_KEY, "Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            results = [
                {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
                for r in data.get("organic", [])
            ]
            return {"query": query, "results": results, "provider": "serper"}
    except Exception as exc:
        logger.warning("Serper search failed: %s", exc)
        return {"query": query, "results": [], "provider": "serper", "error": str(exc)}


async def _perplexity_research(topic: str, questions: list[str] | None) -> dict:
    prompt = f"Research topic: {topic}"
    if questions:
        prompt += "\n\nKey questions to answer:\n" + "\n".join(f"- {q}" for q in questions)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                json={
                    "model": "llama-3.1-sonar-large-128k-online",
                    "messages": [{"role": "user", "content": prompt}],
                    "return_citations": True,
                },
                headers={"Authorization": f"Bearer {_PERPLEXITY_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])
            return {
                "topic": topic,
                "synthesis": content,
                "sources": [{"url": c} for c in citations],
                "provider": "perplexity",
            }
    except Exception as exc:
        logger.error("Perplexity research failed: %s", exc)
        return {"topic": topic, "synthesis": "", "sources": [], "error": str(exc)}
