"""Precision tracker for the recommendation learning loop.

Measures how well the daily opportunity recommendations translate into actual
pursuit decisions and wins. Tracks Precision@K and Precision@Win metrics to
feed back into the bandit / scoring model.

Metrics:
  - Precision@K (default K=10): Of the top-K recommended opportunities in a
    digest, what fraction were actually pursued (i.e. converted to a Deal)?
  - Precision@Win: Of pursued opportunities, what fraction resulted in a win?
  - Daily metrics are recorded to the RecommendationMetric model via Django API.
"""
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.learning.precision_tracker")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


# ── API helpers ──────────────────────────────────────────────────────────────

async def _api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET request to the Django API."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}{path}",
                params=params or {},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return None


async def _api_post(path: str, data: dict[str, Any]) -> Any:
    """POST request to the Django API."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}{path}",
                json=data,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API POST %s failed: %s", path, exc)
        return None


# ── Data fetching ────────────────────────────────────────────────────────────

async def _fetch_digest_opportunities(
    target_date: date | None = None,
    k: int = 10,
) -> list[dict[str, Any]]:
    """Fetch the top-K recommended opportunities from a DailyDigest.

    Args:
        target_date: Date of the digest to query. Defaults to yesterday.
        k: Number of top opportunities to consider.

    Returns:
        List of opportunity dicts from the digest, limited to top K.
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    date_str = target_date.isoformat()
    data = await _api_get(
        "/api/opportunities/digests/",
        params={"date": date_str, "limit": 1},
    )

    if not data:
        logger.info("No digest found for %s", date_str)
        return []

    # Handle paginated and non-paginated responses
    digests = data if isinstance(data, list) else data.get("results", [])
    if not digests:
        logger.info("No digest found for %s", date_str)
        return []

    digest = digests[0]
    opportunity_ids = digest.get("opportunities", [])

    # If the digest returns full objects, use them directly
    if opportunity_ids and isinstance(opportunity_ids[0], dict):
        return opportunity_ids[:k]

    # Otherwise fetch each opportunity by ID
    opportunities: list[dict[str, Any]] = []
    for opp_id in opportunity_ids[:k]:
        opp = await _api_get(f"/api/opportunities/{opp_id}/")
        if opp:
            opportunities.append(opp)

    return opportunities


async def _fetch_deals_for_opportunities(
    opportunity_ids: list[str],
) -> dict[str, dict[str, Any]]:
    """Fetch deals that were created from the given opportunity IDs.

    Returns:
        Mapping of opportunity_id -> deal dict (only for opportunities that
        were pursued, i.e. have at least one Deal).
    """
    if not opportunity_ids:
        return {}

    deals_by_opp: dict[str, dict[str, Any]] = {}

    for opp_id in opportunity_ids:
        data = await _api_get(
            "/api/deals/",
            params={"opportunity": opp_id, "limit": 1},
        )
        if not data:
            continue

        deals = data if isinstance(data, list) else data.get("results", [])
        if deals:
            deals_by_opp[opp_id] = deals[0]

    return deals_by_opp


# ── Precision computations ───────────────────────────────────────────────────

async def compute_precision_at_k(
    k: int = 10,
    target_date: date | None = None,
) -> dict[str, Any]:
    """Compute Precision@K: of the top-K recommended opportunities, how many were pursued.

    A "pursued" opportunity is one that has a Deal record created for it,
    meaning the BD team moved it past intake.

    Args:
        k: Number of top recommendations to evaluate.
        target_date: Date of the digest to evaluate. Defaults to yesterday.

    Returns:
        Dict with:
            - k: the K value
            - date: digest date
            - recommended_count: number of opportunities in digest (up to K)
            - pursued_count: number that were pursued (have deals)
            - precision: pursued_count / recommended_count
            - recommended_ids: list of opportunity IDs
            - pursued_ids: list of pursued opportunity IDs
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    opportunities = await _fetch_digest_opportunities(target_date, k)
    if not opportunities:
        return {
            "k": k,
            "date": target_date.isoformat(),
            "recommended_count": 0,
            "pursued_count": 0,
            "precision": 0.0,
            "recommended_ids": [],
            "pursued_ids": [],
        }

    opp_ids = [
        str(opp.get("id", opp.get("notice_id", "")))
        for opp in opportunities
    ]
    opp_ids = [oid for oid in opp_ids if oid]

    deals_map = await _fetch_deals_for_opportunities(opp_ids)
    pursued_ids = list(deals_map.keys())

    recommended_count = len(opp_ids)
    pursued_count = len(pursued_ids)
    precision = pursued_count / recommended_count if recommended_count > 0 else 0.0

    logger.info(
        "Precision@%d for %s: %d/%d = %.2f",
        k, target_date, pursued_count, recommended_count, precision,
    )

    return {
        "k": k,
        "date": target_date.isoformat(),
        "recommended_count": recommended_count,
        "pursued_count": pursued_count,
        "precision": precision,
        "recommended_ids": opp_ids,
        "pursued_ids": pursued_ids,
    }


async def compute_precision_at_win(
    target_date: date | None = None,
    lookback_days: int = 180,
) -> dict[str, Any]:
    """Compute Precision@Win: of pursued opportunities, how many were won.

    Looks back over `lookback_days` from `target_date` to find deals that
    originated from daily digest recommendations and checks their outcomes.

    Args:
        target_date: Reference date. Defaults to today.
        lookback_days: How far back to look for completed deals.

    Returns:
        Dict with:
            - date: reference date
            - lookback_days: window size
            - pursued_count: total deals from recommendations in the window
            - won_count: deals with outcome='won'
            - lost_count: deals with outcome='lost'
            - pending_count: deals still in pipeline
            - precision_win: won_count / pursued_count
    """
    if target_date is None:
        target_date = date.today()

    start_date = target_date - timedelta(days=lookback_days)

    # Fetch all digests in the lookback window
    all_opp_ids: list[str] = []
    current = start_date
    while current <= target_date:
        opps = await _fetch_digest_opportunities(current, k=10)
        for opp in opps:
            opp_id = str(opp.get("id", opp.get("notice_id", "")))
            if opp_id and opp_id not in all_opp_ids:
                all_opp_ids.append(opp_id)
        current += timedelta(days=1)

    if not all_opp_ids:
        return {
            "date": target_date.isoformat(),
            "lookback_days": lookback_days,
            "pursued_count": 0,
            "won_count": 0,
            "lost_count": 0,
            "pending_count": 0,
            "precision_win": 0.0,
        }

    deals_map = await _fetch_deals_for_opportunities(all_opp_ids)

    won = 0
    lost = 0
    pending = 0
    for deal in deals_map.values():
        outcome = deal.get("outcome", "")
        if outcome == "won":
            won += 1
        elif outcome == "lost":
            lost += 1
        else:
            pending += 1

    pursued = len(deals_map)
    precision_win = won / pursued if pursued > 0 else 0.0

    logger.info(
        "Precision@Win for %s (lookback=%dd): %d won / %d pursued = %.2f",
        target_date, lookback_days, won, pursued, precision_win,
    )

    return {
        "date": target_date.isoformat(),
        "lookback_days": lookback_days,
        "pursued_count": pursued,
        "won_count": won,
        "lost_count": lost,
        "pending_count": pending,
        "precision_win": precision_win,
    }


# ── Daily metrics recording ─────────────────────────────────────────────────

async def record_daily_metrics(
    target_date: date | None = None,
    k: int = 10,
) -> dict[str, Any]:
    """Compute and record daily precision metrics to the RecommendationMetric model.

    Computes both Precision@K and Precision@Win, then saves the results
    via the Django API.

    Args:
        target_date: Date to compute metrics for. Defaults to yesterday.
        k: K value for Precision@K.

    Returns:
        Dict with both metric results and the saved record ID (if successful).
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    # Compute both precision metrics
    precision_k = await compute_precision_at_k(k=k, target_date=target_date)
    precision_win = await compute_precision_at_win(target_date=target_date)

    metrics_payload = {
        "date": target_date.isoformat(),
        "metric_type": "daily_precision",
        "precision_at_k": precision_k["precision"],
        "k_value": k,
        "recommended_count": precision_k["recommended_count"],
        "pursued_count": precision_k["pursued_count"],
        "precision_at_win": precision_win["precision_win"],
        "won_count": precision_win["won_count"],
        "lost_count": precision_win["lost_count"],
        "pending_count": precision_win["pending_count"],
        "details": {
            "precision_at_k_full": precision_k,
            "precision_at_win_full": precision_win,
        },
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save to Django via API
    result = await _api_post(
        "/api/learning/recommendation-metrics/",
        metrics_payload,
    )

    if result:
        metrics_payload["id"] = result.get("id")
        logger.info(
            "Recorded daily metrics for %s: P@%d=%.2f, P@Win=%.2f",
            target_date, k, precision_k["precision"], precision_win["precision_win"],
        )
    else:
        logger.warning("Failed to save daily metrics for %s to Django", target_date)

    return metrics_payload


async def get_precision_trend(
    days: int = 30,
    k: int = 10,
) -> list[dict[str, Any]]:
    """Fetch the precision trend over the last N days.

    Args:
        days: Number of days to look back.
        k: K value filter.

    Returns:
        List of daily metric records, ordered by date ascending.
    """
    data = await _api_get(
        "/api/learning/recommendation-metrics/",
        params={"days": days, "k_value": k, "ordering": "date"},
    )

    if not data:
        return []

    metrics = data if isinstance(data, list) else data.get("results", [])
    return metrics
