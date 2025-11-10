# -*- coding: utf-8 -*-
"""
services.research_clients
Hybrid-Research-Clients für Tavily und Perplexity.

ENV:
- RESEARCH_PROVIDER=hybrid|tavily|perplexity|disabled
- TAVILY_API_KEY=xxx
- PERPLEXITY_API_KEY=xxx
- RESEARCH_DAYS=7 (Recency)
- RESEARCH_TIMEOUT=20 (Sekunden)
"""
from __future__ import annotations
import os, time, json, logging
from typing import Dict, List, Optional
import requests

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = int(os.getenv("RESEARCH_TIMEOUT", "20"))
RECENCY_DAYS = int(os.getenv("RESEARCH_DAYS", "7"))

def _time_depth_from_days(days: int) -> str:
    # Tavily option: "day", "week", "month", "year"
    if days <= 1: return "day"
    if days <= 7: return "week"
    if days <= 31: return "month"
    return "year"

def normalize_item(url: str, title: str = "", description: str = "") -> Dict[str, str]:
    return {
        "url": (url or "").strip(),
        "title": (title or "").strip() or (url or "").strip(),
        "description": (description or "").strip()
    }

def dedup_by_url(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen, out = set(), []
    for it in items:
        u = (it.get("url") or "").strip()
        if u and u not in seen:
            seen.add(u); out.append(it)
    return out

# ---------------- Tavily ----------------
def tavily_search(query: str, max_results: int = 10, days: Optional[int] = None) -> List[Dict[str, str]]:
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        log.warning("Tavily disabled (no API key)")
        return []
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": key,
        "query": query,
        "max_results": int(max_results),
        "include_answer": False,
        "search_depth": "advanced",
        "topic": "general",
        "time_depth": _time_depth_from_days(days or RECENCY_DAYS)
    }
    try:
        r = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        data = r.json() or {}
        results = []
        for ritem in data.get("results", []):
            results.append(normalize_item(ritem.get("url",""), ritem.get("title",""), ritem.get("content","")))
        return dedup_by_url(results)
    except Exception as exc:
        log.warning("Tavily error: %s", exc)
        return []

# ---------------- Perplexity ----------------
def perplexity_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    key = os.getenv("PERPLEXITY_API_KEY", "").strip() or os.getenv("PPLX_API_KEY", "").strip()
    if not key:
        log.warning("Perplexity disabled (no API key)")
        return []
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {
        "model": os.getenv("PERPLEXITY_MODEL","sonar-small-online"),
        "temperature": 0.0,
        "top_p": 1.0,
        "return_citations": True,
        "messages": [
            {"role": "system", "content": "Be concise. Return factual citations relevant to the user's query."},
            {"role": "user", "content": f"{query}\n\nPlease provide authoritative sources."}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        data = r.json() or {}
        items: List[Dict[str,str]] = []
        # Try new-style citations on the message
        try:
            msg = (data.get("choices") or [{}])[0].get("message", {})
            cits = msg.get("citations") or []
            for u in cits:
                items.append(normalize_item(str(u)))
        except Exception:
            pass
        # Fallback: parse "citations" on the top-level or URLs from text
        if not items:
            for u in (data.get("citations") or []):
                items.append(normalize_item(str(u)))
        # Best effort: scrape URLs from the content
        if not items:
            import re
            content = (data.get("choices") or [{}])[0].get("message",{}).get("content","")
            for u in re.findall(r"https?://[^\s)>\]]+", content or ""):
                items.append(normalize_item(u))
        return dedup_by_url(items)[:max_results]
    except Exception as exc:
        log.warning("Perplexity error: %s", exc)
        return []

def hybrid_search(queries: List[str], max_results:int = 10, days:int = RECENCY_DAYS) -> List[Dict[str,str]]:
    out: List[Dict[str,str]] = []
    for q in queries:
        # Tavily
        out.extend(tavily_search(q, max_results=max_results, days=days))
        # Perplexity
        out.extend(perplexity_search(q, max_results=max_results))
    return dedup_by_url(out)[:max_results*len(queries)]
