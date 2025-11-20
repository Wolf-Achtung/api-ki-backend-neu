# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, logging, requests
from typing import List, Dict, Any

LOGGER = logging.getLogger(__name__)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_ENDPOINT = os.getenv("TAVILY_ENDPOINT", "https://api.tavily.com/search")

def _post_json(url: str, payload: dict, timeout: int = 20) -> dict[Any, Any]:
    headers = {"Content-Type":"application/json","Accept":"application/json"}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, dict) else {}

def search(query: str, max_results: int = 6, days: int = 30) -> List[Dict]:
    if not TAVILY_API_KEY:
        LOGGER.warning("TAVILY_API_KEY not set")
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
    except Exception as exc:
        LOGGER.error("Tavily search failed: %s", exc)
        return []
