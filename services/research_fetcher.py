# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, hashlib
from typing import List, Dict, Any
from services.research_cache import cache_get, cache_set
from services import provider_tavily, provider_perplexity

PROVIDER = os.getenv("RESEARCH_PROVIDER", "tavily").strip().lower()
MAX_RESULTS = int(os.getenv("RESEARCH_MAX_RESULTS", "6"))

def _make_key(prefix: str, params: Dict[str, Any]) -> str:
    raw = json.dumps({"prefix": prefix, "params": params}, sort_keys=True, ensure_ascii=False)
    import hashlib
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"

def _provider_search(query: str, days: int):
    if PROVIDER == "perplexity":
        return provider_perplexity.search(topic=query, days=days, max_items=MAX_RESULTS)
    return provider_tavily.search(query=query, max_results=MAX_RESULTS, days=days)

def fetch_funding(state: str, days: int = 30) -> List[Dict[str, Any]]:
    q = f"Förderprogramm Digitalisierung {state} Antragsfristen Änderungen"
    key = _make_key("funding", {"state": state, "days": days})
    cached = cache_get(key, max_age_days=days)
    if cached is not None:
        return cached
    items = []
    for r in _provider_search(q, days):
        if not r.get("url"): 
            continue
        items.append({"title": r.get("title") or "Förderprogramm", "url": r.get("url"), "summary": (r.get("content") or "")[:400], "tags": ["förderung", state], "source": r.get("source","web")})
    cache_set(key, items)
    return items

def fetch_tools(branch: str, company_size: str, days: int = 30, include_open_source: bool = True) -> List[Dict[str, Any]]:
    queries = [f"Beste KI Tools EU Hosting DSGVO {branch} {company_size} Preise 2025"]
    if include_open_source:
        queries.append(f"Open Source KI Tools {branch} {company_size} EU self-hosted 2025")
    key = _make_key("tools", {"branch": branch, "size": company_size, "days": days, "oss": include_open_source})
    cached = cache_get(key, max_age_days=days)
    if cached is not None:
        return cached
    items = []
    for q in queries:
        for r in _provider_search(q, days):
            if not r.get("url"): 
                continue
            items.append({"title": r.get("title") or "Tool", "url": r.get("url"), "summary": (r.get("content") or "")[:400], "tags": ["tool", branch, company_size], "source": r.get("source","web")})
    # dedupe
    uniq, seen = [], set()
    for it in items:
        if it["url"] in seen: 
            continue
        seen.add(it["url"])
        uniq.append(it)
    cache_set(key, uniq[: MAX_RESULTS * 2])
    return uniq[: MAX_RESULTS * 2]
