# -*- coding: utf-8 -*-
"""
provider_tavily.py
------------------
Tavily API client for web search.

SPRINT G14-B: Reduced timeout from 20s to 8s for faster fallback.
"""
from __future__ import annotations
import os, json, logging, re, requests
from typing import List, Dict, Any

LOGGER = logging.getLogger(__name__)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_ENDPOINT = os.getenv("TAVILY_ENDPOINT", "https://api.tavily.com/search")

# SPRINT G14-B: Aggressive timeout for faster fallback (was 20s)
TAVILY_TIMEOUT = int(os.getenv("TAVILY_TIMEOUT", "8"))


def _post_json(url: str, payload: dict, timeout: int = TAVILY_TIMEOUT) -> dict[Any, Any]:
    headers = {"Content-Type":"application/json","Accept":"application/json"}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, dict) else {}

def _sanitize_query(query: str, max_len: int = 400) -> str:
    """Sanitize query: strip control chars, limit length, replace problematic chars."""
    import unicodedata
    # Normalize unicode (e.g. decompose umlauts then recompose)
    q = unicodedata.normalize("NFC", query)
    # Remove control characters
    q = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', q)
    # Collapse whitespace
    q = re.sub(r'\s+', ' ', q).strip()
    # Truncate to max_len
    if len(q) > max_len:
        q = q[:max_len].rsplit(' ', 1)[0]
    return q


def search(query: str, max_results: int = 6, days: int = 30) -> List[Dict]:
    if not TAVILY_API_KEY:
        LOGGER.warning("TAVILY_API_KEY not set")
        return []

    query = _sanitize_query(query)
    if not query:
        LOGGER.warning("Tavily query empty after sanitization")
        return []

    # Map days to valid Tavily time_range values
    if days <= 1:
        time_range = "day"
    elif days <= 7:
        time_range = "week"
    elif days <= 30:
        time_range = "month"
    else:
        time_range = "year"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max(1, min(max_results, 10)),
        "search_depth": "advanced",
        "include_answer": False,
        "include_raw_content": False,
    }

    # Only add time_range if not searching all time
    if days < 365:
        payload["days"] = days  # Tavily uses 'days' parameter directly
    try:
        data = _post_json(TAVILY_ENDPOINT, payload)
        out = []
        for r in data.get("results") or []:
            out.append({"title": r.get("title") or "", "url": r.get("url") or "", "content": r.get("content") or "", "source":"tavily"})
        return out
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            # Retry with shortened query
            short_q = _sanitize_query(query, max_len=200)
            if short_q and short_q != query:
                LOGGER.warning("Tavily 400 error, retrying with shortened query (%d chars)", len(short_q))
                payload["query"] = short_q
                try:
                    data = _post_json(TAVILY_ENDPOINT, payload)
                    return [{"title": r.get("title") or "", "url": r.get("url") or "", "content": r.get("content") or "", "source": "tavily"} for r in data.get("results") or []]
                except Exception:
                    pass
            LOGGER.error("Tavily search failed (400): query=%r", query[:100])
        else:
            LOGGER.error("Tavily search failed: %s", exc)
        return []
    except Exception as exc:
        LOGGER.error("Tavily search failed: %s", exc)
        return []
