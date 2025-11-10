
# -*- coding: utf-8 -*-
"""
services.research_clients
Hybrid-Research-Clients: Tavily + Perplexity
- Keine harten Abhängigkeiten: Wenn API-Key fehlt, wird die Quelle automatisch übersprungen.
- Einheitliches Normalisierungsformat für Treffer.
"""
from __future__ import annotations
import os, time, json, re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

import requests

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro").strip()

USER_AGENT = os.getenv("RESEARCH_UA", "ki-sicherheit-research/1.0 (+https://ki-sicherheit.jetzt)")


def _norm_url(u: str) -> str:
    try:
        p = urlparse((u or "").strip())
        scheme = p.scheme or "https"
        netloc = p.netloc.lower()
        path = re.sub(r"/+$", "", p.path or "")
        return f"{scheme}://{netloc}{path}"
    except Exception:
        return (u or "").strip()


def _norm_item(title: str, url: str, description: str, source: str) -> Dict[str, str]:
    return {
        "title": (title or "").strip()[:200],
        "url": _norm_url(url),
        "description": (description or "").strip()[:500],
        "source": source,
    }


# ---------------- Tavily ----------------
def search_tavily(query: str, max_results: int = 8, days: Optional[int] = None) -> List[Dict[str, str]]:
    if not TAVILY_API_KEY:
        return []
    try:
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
            "include_images": False,
            "include_domains": [],
        }
        if days is not None:
            payload["days"] = int(days)
        r = requests.post("https://api.tavily.com/search", json=payload, timeout=20)
        r.raise_for_status()
        data = r.json() or {}
        out: List[Dict[str, str]] = []
        for item in (data.get("results") or []):
            out.append(_norm_item(item.get("title",""), item.get("url",""), item.get("content",""), "tavily"))
        return out
    except Exception:
        return []


# ---------------- Perplexity ----------------
def search_perplexity(query: str, max_results: int = 8, days: Optional[int] = None, model: Optional[str] = None) -> List[Dict[str, str]]:
    if not PERPLEXITY_API_KEY:
        return []
    model = (model or PERPLEXITY_MODEL or "sonar-pro").strip()
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        system = "You are a web researcher. Return concise, trustworthy sources (official and vendor pages preferred)."
        query_aug = query
        if days:
            query_aug = f"{query} updated within last {int(days)} days"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Provide 8 high-quality links with titles and one-sentence summaries for: {query_aug}. Output JSON array with objects: title,url,description."}
            ],
            "temperature": 0.0,
        }
        r = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Try parsing JSON payload if model complied
        items: List[Dict[str, Any]] = []
        try:
            # Find first JSON array in content
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1 and end > start:
                items = json.loads(content[start:end+1])
        except Exception:
            items = []
        out: List[Dict[str, str]] = []
        for it in items or []:
            out.append(_norm_item(it.get("title",""), it.get("url",""), it.get("description",""), "perplexity"))
        # Fallback: use citations if present
        if not out:
            citations = (data.get("citations") or []) if isinstance(data.get("citations"), list) else []
            for c in citations[:max_results]:
                out.append(_norm_item(c, c, "", "perplexity"))
        return out[:max_results]
    except Exception:
        return []


# --------------- Dedup & Filter ---------------
NSFW_DOMAINS = {"xvideos.com","pornhub.com","xnxx.com","redtube.com","youporn.com","onlyfans.com"}
NSFW_WORDS = {"porn","xxx","sex","nude","naked","adult","nsfw","erotic","escort","dating","porno","nackt","fick","titten","onlyfans","torrent","crack"}

def _is_nsfw(item: Dict[str,str]) -> bool:
    u = (item.get("url") or "").lower()
    if any(d in u for d in NSFW_DOMAINS):
        return True
    txt = f"{item.get('title','')} {item.get('description','')}".lower()
    return any(w in txt for w in NSFW_WORDS)

def dedup_and_filter(items: List[Dict[str,str]]) -> List[Dict[str,str]]:
    seen = set()
    out: List[Dict[str,str]] = []
    for it in items:
        if _is_nsfw(it): 
            continue
        u = it.get("url","")
        if u and u not in seen:
            seen.add(u)
            out.append(it)
    return out


def search_hybrid(queries: List[str], max_results_per_query: int = 8, days: Optional[int] = None) -> List[Dict[str, str]]:
    """Run Tavily + Perplexity and merge results."""
    all_items: List[Dict[str,str]] = []
    for q in queries:
        tav = search_tavily(q, max_results=max_results_per_query, days=days)
        ppl = search_perplexity(q, max_results=max_results_per_query, days=days)
        all_items.extend(tav)
        all_items.extend(ppl)
    return dedup_and_filter(all_items)
