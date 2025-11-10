# -*- coding: utf-8 -*-
from __future__ import annotations
import os, time, logging
from typing import List, Dict, Any
import requests

log = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
PPLX_API_KEY   = os.getenv("PPLX_API_KEY", "") or os.getenv("PERPLEXITY_API_KEY","")

def tavily_search(q: str, k: int = 10, days: int = 7) -> List[Dict[str,Any]]:
    if not TAVILY_API_KEY:
        return []
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": q, "search_depth": "advanced", "max_results": k, "include_answer": False, "days": days},
            timeout=25
        )
        r.raise_for_status()
        data = r.json() or {}
        out = []
        for it in data.get("results", []):
            out.append({"title": it.get("title",""), "url": it.get("url",""), "snippet": it.get("content","")})
        return out
    except Exception as exc:
        log.warning("Tavily error: %s", exc)
        return []

def perplexity_search(q: str, k: int = 8) -> List[Dict[str,Any]]:
    if not PPLX_API_KEY:
        return []
    try:
        r = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PPLX_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": os.getenv("PPLX_MODEL","sonar-small-online"),
                "messages": [{"role":"system","content":"You are a search/research assistant. Return concise list of sources with URLs."},
                             {"role":"user","content": f"Find up-to-date sources (URLs) for: {q}. Output only as bullet list with title – url"}],
                "temperature": 0.0,
                "top_p": 1.0
            },
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        content = (data.get("choices",[{}])[0].get("message",{}) or {}).get("content","")
        out = []
        for line in content.splitlines():
            line = line.strip("-• ").strip()
            if "http" in line:
                # naive split
                parts = line.split("http",1)
                title = parts[0].strip(" –-:") or "Quelle"
                url   = "http" + parts[1].strip()
                out.append({"title": title, "url": url, "snippet": ""})
        return out[:k]
    except Exception as exc:
        log.warning("Perplexity error: %s", exc)
        return []

def hybrid(q: str, k: int = 10, days: int = 7) -> List[Dict[str,Any]]:
    a = tavily_search(q, k=k, days=days)
    b = perplexity_search(q, k=max(3, k//2))
    # Merge by URL
    seen = set()
    res = []
    for L in (a+b):
        u = L.get("url","")
        if u and u not in seen:
            seen.add(u)
            res.append(L)
    return res[:k]
