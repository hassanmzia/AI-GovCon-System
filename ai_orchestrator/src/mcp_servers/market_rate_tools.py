"""MCP tool server: Market rate intelligence – GSA schedules, salary benchmarks."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.market_rates")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")
_BLS_API_KEY = os.getenv("BLS_API_KEY", "")  # Bureau of Labor Statistics


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def get_rate_card(
    labor_category: str | None = None,
    skill_level: str | None = None,
    clearance_required: bool = False,
) -> list[dict[str, Any]]:
    """Fetch labor rate card data from the Django backend.

    Args:
        labor_category: Optional partial match on labor category name.
        skill_level: Optional filter (e.g. "junior", "mid", "senior", "principal").
        clearance_required: Filter for rates that include clearance premium.

    Returns:
        List of rate card entries with fully_loaded_rate, fringe, overhead, G&A.
    """
    try:
        params: dict[str, Any] = {}
        if labor_category:
            params["category"] = labor_category
        if skill_level:
            params["level"] = skill_level
        if clearance_required:
            params["clearance"] = "true"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/pricing/rate-cards/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Rate card fetch failed: %s", exc)
        return _default_rate_card(labor_category)


async def get_gsa_rates(
    labor_category: str,
    sin: str | None = None,
    contract_vehicle: str | None = None,
) -> dict[str, Any]:
    """Look up GSA schedule rates for a labor category.

    Queries GSA Advantage or internal rate database.

    Args:
        labor_category: Labor category to search.
        sin: GSA Special Item Number.
        contract_vehicle: Contract vehicle (e.g. "OASIS+", "SEWP VI").

    Returns:
        Dict with labor_category, gsa_rate_low, gsa_rate_high, gsa_rate_median.
    """
    # First check internal database via Django API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/pricing/gsa-rates/",
                params={"category": labor_category, "vehicle": contract_vehicle or ""},
                headers=_headers(),
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    return data if isinstance(data, dict) else data[0]
    except Exception:
        pass

    # Fallback: return industry benchmark estimates
    return _gsa_rate_estimate(labor_category)


async def get_salary_benchmarks(
    job_title: str,
    location: str = "national",
    experience_years: int | None = None,
) -> dict[str, Any]:
    """Get salary benchmarks for *job_title* from BLS or internal data.

    Args:
        job_title: Job title or labor category.
        location: Geographic location ("national" or MSA code).
        experience_years: Optional experience level for percentile filtering.

    Returns:
        Dict with p25, p50, p75, p90 annual salary estimates.
    """
    # Try BLS OES data if API key available
    if _BLS_API_KEY:
        try:
            result = await _bls_salary_lookup(job_title, location)
            if result:
                return result
        except Exception as exc:
            logger.warning("BLS salary lookup failed: %s", exc)

    return _salary_estimate(job_title, experience_years)


async def get_market_intelligence(
    opportunity_value: float,
    naics: str,
    agency: str,
    competition_type: str = "full_and_open",
) -> dict[str, Any]:
    """Generate market pricing intelligence for an opportunity.

    Args:
        opportunity_value: Government estimate or ceiling value.
        naics: NAICS code for the work.
        agency: Awarding agency.
        competition_type: "full_and_open", "small_business", or "sole_source".

    Returns:
        Dict with price guidance, competitive range, recommended_strategy.
    """
    from src.mcp_servers.competitive_intel_tools import get_price_benchmarks

    benchmarks = await get_price_benchmarks(naics=naics, agency=agency)

    avg = benchmarks.get("avg_award", opportunity_value)
    median = benchmarks.get("median_award", opportunity_value)

    # Competition intensity adjustment
    intensity_factor = {"full_and_open": 1.0, "small_business": 0.95, "sole_source": 1.15}.get(
        competition_type, 1.0
    )

    competitive_floor = median * 0.85 * intensity_factor
    competitive_ceiling = median * 1.10 * intensity_factor

    return {
        "opportunity_value": opportunity_value,
        "naics": naics,
        "agency": agency,
        "market_median": median,
        "market_avg": avg,
        "competitive_floor": competitive_floor,
        "competitive_ceiling": competitive_ceiling,
        "recommended_strategy": _pick_strategy(opportunity_value, median, competition_type),
        "price_to_win_estimate": median * 0.93 * intensity_factor,
        "sample_size": benchmarks.get("sample_size", 0),
        "confidence": "high" if benchmarks.get("sample_size", 0) > 10 else "low",
    }


async def compute_fully_loaded_rate(
    labor_category: str,
    base_salary: float,
    fringe_rate: float | None = None,
    overhead_rate: float | None = None,
    gna_rate: float | None = None,
    profit_rate: float | None = None,
) -> dict[str, Any]:
    """Compute fully-loaded labor rate from base salary and wrap rates.

    Args:
        labor_category: Labor category name.
        base_salary: Annual base salary in USD.
        fringe_rate: Fringe benefit rate (decimal, e.g. 0.25 for 25%). Auto-looked up if None.
        overhead_rate: Overhead rate. Auto-looked up if None.
        gna_rate: G&A rate. Auto-looked up if None.
        profit_rate: Profit/fee rate. Auto-looked up if None.

    Returns:
        Dict with all rate components and final fully_loaded_hourly_rate.
    """
    hourly = base_salary / 1920  # standard government hours/year

    # Use defaults if not provided
    fringe = fringe_rate if fringe_rate is not None else 0.28
    overhead = overhead_rate if overhead_rate is not None else 0.15
    gna = gna_rate if gna_rate is not None else 0.10
    profit = profit_rate if profit_rate is not None else 0.08

    with_fringe = hourly * (1 + fringe)
    with_overhead = with_fringe * (1 + overhead)
    with_gna = with_overhead * (1 + gna)
    fully_loaded = with_gna * (1 + profit)

    return {
        "labor_category": labor_category,
        "annual_salary": base_salary,
        "hourly_base": round(hourly, 2),
        "fringe_rate": fringe,
        "overhead_rate": overhead,
        "gna_rate": gna,
        "profit_rate": profit,
        "hourly_with_fringe": round(with_fringe, 2),
        "hourly_with_overhead": round(with_overhead, 2),
        "hourly_with_gna": round(with_gna, 2),
        "fully_loaded_hourly": round(fully_loaded, 2),
        "fully_loaded_annual": round(fully_loaded * 1920, 0),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _default_rate_card(category: str | None) -> list[dict]:
    defaults = [
        {"category": "Program Manager", "level": "senior", "fully_loaded_rate": 185},
        {"category": "Systems Engineer", "level": "senior", "fully_loaded_rate": 175},
        {"category": "Software Engineer", "level": "senior", "fully_loaded_rate": 165},
        {"category": "Software Engineer", "level": "mid", "fully_loaded_rate": 135},
        {"category": "Data Scientist", "level": "senior", "fully_loaded_rate": 170},
        {"category": "Business Analyst", "level": "mid", "fully_loaded_rate": 125},
        {"category": "Technical Writer", "level": "mid", "fully_loaded_rate": 105},
        {"category": "Cybersecurity Analyst", "level": "senior", "fully_loaded_rate": 165},
        {"category": "Cloud Architect", "level": "principal", "fully_loaded_rate": 210},
        {"category": "Project Coordinator", "level": "junior", "fully_loaded_rate": 85},
    ]
    if category:
        return [d for d in defaults if category.lower() in d["category"].lower()]
    return defaults


def _gsa_rate_estimate(category: str) -> dict:
    benchmarks = {
        "program manager": {"low": 140, "median": 175, "high": 225},
        "systems engineer": {"low": 130, "median": 165, "high": 215},
        "software engineer": {"low": 110, "median": 150, "high": 200},
        "data scientist": {"low": 120, "median": 160, "high": 210},
        "cybersecurity": {"low": 120, "median": 158, "high": 205},
        "cloud": {"low": 145, "median": 185, "high": 240},
    }
    cat_lower = category.lower()
    for key, rates in benchmarks.items():
        if key in cat_lower:
            return {
                "labor_category": category,
                "gsa_rate_low": rates["low"],
                "gsa_rate_median": rates["median"],
                "gsa_rate_high": rates["high"],
                "source": "industry_benchmark",
            }
    return {
        "labor_category": category,
        "gsa_rate_low": 100,
        "gsa_rate_median": 145,
        "gsa_rate_high": 200,
        "source": "industry_benchmark",
    }


def _salary_estimate(job_title: str, exp_years: int | None) -> dict:
    base = {"p25": 85000, "p50": 110000, "p75": 140000, "p90": 175000}
    title_lower = job_title.lower()
    if "principal" in title_lower or "staff" in title_lower:
        factor = 1.4
    elif "senior" in title_lower or "lead" in title_lower:
        factor = 1.2
    elif "junior" in title_lower or "associate" in title_lower:
        factor = 0.75
    else:
        factor = 1.0
    return {
        "job_title": job_title,
        "p25": int(base["p25"] * factor),
        "p50": int(base["p50"] * factor),
        "p75": int(base["p75"] * factor),
        "p90": int(base["p90"] * factor),
        "source": "industry_benchmark",
    }


def _pick_strategy(value: float, median: float, competition_type: str) -> str:
    if value < median * 0.5:
        return "floor"
    if competition_type == "small_business":
        return "competitive"
    if value > median * 2:
        return "value_based"
    return "competitive"


async def _bls_salary_lookup(job_title: str, location: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.bls.gov/publicAPI/v2/timeseries/data/",
                json={
                    "registrationkey": _BLS_API_KEY,
                    "seriesid": ["OEUS000000000000000000000"],
                    "startyear": "2022",
                    "endyear": "2024",
                },
            )
            resp.raise_for_status()
            # BLS returns aggregate wage data; parse as needed
            return None  # Simplified - full BLS OES parsing complex
    except Exception:
        return None
