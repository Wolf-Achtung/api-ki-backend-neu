# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Lightweight research wrapper for Förderprogramme & Tools.
Providers: Tavily (preferred), Perplexity (optional). If no API keys are set,
returns a graceful placeholder.
"""
import os
import json
import logging
from typing import Dict, List, Any
import requests

log = logging.getLogger(__name__)

def _build_queries(branch_label: str, state_label: str, lang: str) -> Dict[str, str]:
    state_q = (state_label or "").strip()
    # Funding query focuses on official sources first (BMWK, KfW, Landesportale)
    q_funding = f"{'Förderprogramme Digitalisierung' if lang=='de' else 'funding programs digitalization'} {state_q} BMWK KfW site:.de"
    # Tools query focuses on practical AI tooling for the branch
    q_tools = f"KI Tools {branch_label} Praxis 2025 site:.de"
    return {"funding": q_funding, "tools": q_tools}

def _tavily(api_key: str, query: str, max_results: int = 6) -> List[Dict[str, str]]:
    try:
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": False,
        }
        r = requests.post("https://api.tavily.com/search", json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        out: List[Dict[str, str]] = []
        for it in data.get("results", [])[:max_results]:
            url = it.get("url") or ""
            title = it.get("title") or url
            out.append({"title": title, "url": url, "source": "tavily"})
        return out
    except Exception as exc:
        log.warning("Tavily search failed: %s", exc)
        return []

def _perplexity(api_key: str, query: str, max_items: int = 6) -> List[Dict[str, str]]:
    """
    Ask Perplexity to list top links (OpenAI-like chat completion). This keeps it simple.
    """
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {
            "model": "sonar-small-online",
            "messages": [
                {"role": "system", "content": "List 5-6 high-quality, trustworthy links only. Return a JSON array of {title,url}."},
                {"role": "user", "content": query},
            ],
            "temperature": 0.0,
        }
        r = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=body, timeout=45)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        arr = json.loads(content) if content.strip().startswith("[") else []
        out: List[Dict[str, str]] = []
        for it in arr[:max_items]:
            out.append({"title": it.get("title",""), "url": it.get("url",""), "source": "perplexity"})
        return out
    except Exception as exc:
        log.warning("Perplexity search failed: %s", exc)
        return []

def _render_links_block(title: str, items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    lis = "".join([f'<li><a href="{it["url"]}">{it["title"]}</a></li>' for it in items if it.get("url")])
    return f'<div class="card"><h3>{title}</h3><ul>{lis}</ul></div>'

def search_funding_and_tools(branch_label: str, state_label: str, lang: str = "de") -> Dict[str, Any]:
    provider = (os.getenv("RESEARCH_PROVIDER") or "tavily").lower()
    tavily_key = os.getenv("TAVILY_API_KEY") or ""
    perplexity_key = os.getenv("PERPLEXITY_API_KEY") or ""

    queries = _build_queries(branch_label, state_label, lang)

    funding_links: List[Dict[str, str]] = []
    tool_links: List[Dict[str, str]] = []

    if provider == "tavily" and tavily_key:
        funding_links = _tavily(tavily_key, queries["funding"])
        tool_links = _tavily(tavily_key, queries["tools"])
    elif provider == "perplexity" and perplexity_key:
        funding_links = _perplexity(perplexity_key, queries["funding"])
        tool_links = _perplexity(perplexity_key, queries["tools"])
    else:
        # Graceful placeholder (no external calls)
        msg = ("(Hinweis: Für aktuelle Links bitte TAVILY_API_KEY oder PERPLEXITY_API_KEY setzen.)")
        html = f'<div class="card"><h3>Aktuelle Programme & Tools</h3><p class="muted">{msg}</p></div>'
        return {"funding_links": [], "tool_links": [], "html": html}

    html = (
        _render_links_block("Förderprogramme (aktuelle Quellen)", funding_links) +
        _render_links_block("KI‑Tools & Praxis (aktuelle Quellen)", tool_links)
    )
    return {"funding_links": funding_links, "tool_links": tool_links, "html": html}
