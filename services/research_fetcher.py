# -*- coding: utf-8 -*-
"""
High-level fetcher with on-disk JSON cache.
"""
from __future__ import annotations
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from .providers.perplexity import perplexity_search
from .providers.tavily import tavily_search

LOGGER = logging.getLogger(__name__)

CACHE_PATH = os.getenv("RESEARCH_CACHE_PATH", "data/research_cache.json")
DEFAULT_TTL_SECONDS = int(os.getenv("RESEARCH_CACHE_TTL", str(7 * 24 * 3600)))  # 7 Tage

def _load_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save_cache(cache: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def _cache_key(prefix: str, **kwargs: Any) -> str:
    parts = [prefix] + [f"{k}={kwargs[k]}" for k in sorted(kwargs)]
    return "|".join(parts)

def _get_cached(cache: Dict[str, Any], key: str, ttl: int) -> Optional[Any]:
    rec = cache.get(key)
    if not rec:
        return None
    if time.time() - rec.get("ts", 0) > ttl:
        return None
    return rec.get("data")

def _set_cached(cache: Dict[str, Any], key: str, data: Any) -> None:
    cache[key] = {"ts": time.time(), "data": data}

def _search_union(queries: List[str], max_items: int = 8) -> List[Dict[str, Any]]:
    """Try Tavily first (structured), fall back to Perplexity (LLM)."""
    items: List[Dict[str, Any]] = []
    try:
        items = tavily_search(queries, max_items=max_items)
    except Exception as exc:
        LOGGER.warning("Tavily failed: %s", exc)
    if not items:
        try:
            items = perplexity_search(queries, max_items=max_items)
        except Exception as exc:
            LOGGER.warning("Perplexity failed: %s", exc)
    return items[:max_items]

def fetch_funding(state: str, days: int = 30, max_items: int = 8) -> List[Dict[str, Any]]:
    """Fetch current funding programs for a German state or 'Deutschland'."""
    cache = _load_cache()
    key = _cache_key("funding", state=state, days=days)
    cached = _get_cached(cache, key, DEFAULT_TTL_SECONDS)
    if cached and isinstance(cached, list):
        return list(cached)

    queries = [
        f"Förderprogramm KI {state} {days} Tage site:.de",
        f"Digitalisierung Förderung {state} {days} Tage",
        f"KMU Förderung KI {state} Fristen",
    ]
    items = _search_union(queries, max_items=max_items)
    items_result: list[dict[str, Any]] = items if isinstance(items, list) else []
    _set_cached(cache, key, items_result)
    _save_cache(cache)
    return items

def fetch_tools(branch: str, company_size: str, days: int = 30, include_open_source: bool = True, max_items: int = 10) -> List[Dict[str, Any]]:
    """Fetch tools (SaaS + optional Open‑Source) relevant to branch/size."""
    cache = _load_cache()
    key = _cache_key("tools", branch=branch, size=company_size, days=days, oss=include_open_source)
    cached = _get_cached(cache, key, DEFAULT_TTL_SECONDS)
    if cached and isinstance(cached, list):
        return list(cached)

    base = [
        f"beste KI Tools {branch} Deutschland {days} Tage",
        f"{branch} generative AI pricing latency EU hosting",
    ]
    if include_open_source:
        base.append(f"open source {branch} AI tools EU {days} Tage")

    items = _search_union(base, max_items=max_items)
    _set_cached(cache, key, items)
    _save_cache(cache)
    return items
