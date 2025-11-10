# -*- coding: utf-8 -*-
from __future__ import annotations

import os, json, html, re, time
from typing import Any, Dict, List, Tuple
import requests
from urllib.parse import urlparse

def _clean(s: str) -> str:
    return (s or "").replace("\n", " ").strip()

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def _unique(items: List[Dict[str, Any]], key="url") -> List[Dict[str, Any]]:
    seen = set(); out = []
    for it in items:
        v = (it or {}).get(key, "")
        if v and v not in seen:
            seen.add(v); out.append(it)
    return out

def _tavily_search(q: str, max_results: int = 8) -> List[Dict[str, Any]]:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key: 
        return []
    url = "https://api.tavily.com/search"
    try:
        r = requests.post(url, json={
            "api_key": api_key,
            "query": q,
            "max_results": max_results,
            "search_depth": "basic",
            "include_domains": [],
            "exclude_domains": [],
            "include_answer": False,
            "include_raw_content": False
        }, timeout=30)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        out = []
        for it in results:
            out.append({
                "title": _clean(it.get("title")),
                "url": it.get("url"),
                "snippet": _clean(it.get("content") or it.get("snippet") or ""),
                "source": "tavily"
            })
        return out
    except Exception:
        return []

def _perplexity_json(query: str, system: str = "Gib eine JSON-Liste von 5-8 Objekten mit title, url, description zurück.", model: str = None) -> List[Dict[str, Any]]:
    api_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    if not api_key:
        return []
    # Default model name may change; using "sonar" alias keeps it stable on their side
    model = model or os.getenv("PERPLEXITY_MODEL", "sonar")
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": query}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        # Try to extract JSON
        m = re.search(r"\[\s*\{.*\}\s*\]", content, flags=re.DOTALL)
        if m:
            return json.loads(m.group(0))
        # If not JSON, return empty
        return []
    except Exception:
        return []

def _render_tools_table(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "<p>Keine seriösen Tool-Quellen im gewünschten Zeitraum gefunden.</p>"
    rows = []
    for it in items[:10]:
        title = html.escape(it.get("title") or it.get("name") or "Quelle")
        url = it.get("url") or ""
        cat = html.escape(it.get("category", "—"))
        price = html.escape(it.get("price", "—"))
        host = html.escape(it.get("host", "—"))
        link = f"<a href='{html.escape(url)}' target='_blank' rel='noopener'>{title}</a>" if url else title
        rows.append(f"<tr><td>{link}</td><td>{cat}</td><td>{price}</td><td>{host}</td><td>{html.escape(_domain(url))}</td></tr>")
    table = ("<table class='table'><thead><tr>"
             "<th>Tool/Produkt</th><th>Kategorie</th><th>Preis</th><th>DSGVO/Host</th><th>Quelle</th>"
             "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>")
    return table

def _render_funding_table(items: List[Dict[str, Any]], bundesland_label: str) -> str:
    if not items:
        return f"<div class='callout'>Aktuell keine belastbaren Programme für {html.escape(bundesland_label or 'Ihr Bundesland')} gefunden (Zeitraum/Filter). Bitte später erneut prüfen.</div>"
    rows = []
    for it in items[:10]:
        name = html.escape(it.get("title") or "Programm")
        url = it.get("url") or ""
        quote = html.escape(it.get("rate", it.get("grant", "—")))
        target = html.escape(it.get("target", "KMU/Solo"))
        deadline = html.escape(it.get("deadline", "laufend / n. n."))
        elig = html.escape(it.get("eligibility", "Kurzprüfung nötig"))
        link = f"<a href='{html.escape(url)}' target='_blank' rel='noopener'>Offizielle Infos</a>" if url else "—"
        rows.append(f"<tr><td><strong>{name}</strong></td><td>{quote}</td><td>{target}</td><td>{deadline}</td><td>{elig}</td><td>{link}</td></tr>")
    table = ("<table class='table'><thead><tr>"
             "<th>Programm</th><th>Förderquote/Budget</th><th>Zielgruppe</th><th>Deadline</th><th>Eligibility</th><th>Quelle</th>"
             "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>")
    return table

def run_research(answers: Dict[str, Any]) -> Dict[str, str]:
    """
    Hybrid research: combine Tavily and Perplexity.
    Returns HTML blocks: TOOLS_TABLE_HTML, FUNDING_TABLE_HTML, optional AI_ACT_NEWS_HTML, last_updated
    """
    provider = os.getenv("RESEARCH_PROVIDER", "hybrid").lower().strip()
    days = int(os.getenv("RESEARCH_DAYS", "14"))
    branche = answers.get("BRANCHE_LABEL") or answers.get("branche", "")
    bundesland_label = answers.get("BUNDESLAND_LABEL") or answers.get("bundesland", "")
    size = answers.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse", "")
    now = time.strftime("%Y-%m-%d")

    tools_items: List[Dict[str, Any]] = []
    funding_items: List[Dict[str, Any]] = []

    # Queries
    q_tools = f"KI-Tools {branche} DSGVO EU Hosting Preise 2025 seriöse Quellen"
    q_funding = f"Förderprogramme Digitalisierung KI {bundesland_label} 2025 offizielle Richtlinien Fristen"
    q_ai_act = "EU AI Act timeline dates 2025 2026 2027 official commission.europa.eu changes"

    if provider in ("hybrid", "tavily"):
        tools_items += _tavily_search(q_tools, max_results=10)
        funding_items += _tavily_search(q_funding, max_results=10)

    if provider in ("hybrid", "perplexity"):
        tools_items += _perplexity_json(q_tools, system="Gib eine JSON-Liste von Tools (title, url, category, price, host). Präferiere EU/DSGVO-Angaben.")
        funding_items += _perplexity_json(q_funding, system="Gib eine JSON-Liste von Förderprogrammen (title, url, rate, target, deadline, eligibility). Nur offizielle/universitäre Quellen.")

    # Deduplicate by URL
    tools_items = _unique(tools_items, key="url")
    funding_items = _unique(funding_items, key="url")

    # Render HTML
    tools_html = _render_tools_table(tools_items)
    funding_html = _render_funding_table(funding_items, bundesland_label)

    # (Optional) AI Act news box via Perplexity (best-effort)
    ai_news_html = ""
    if provider in ("hybrid", "perplexity"):
        news_items = _perplexity_json(q_ai_act, system="Gib eine JSON-Liste von 3-6 Meldungen (title, url, summary). Nur EU/Behörden/seriöse Medien.")
        if news_items:
            lis = []
            for n in news_items[:6]:
                title = html.escape(n.get("title") or "Meldung")
                url = n.get("url") or ""
                summary = html.escape(n.get("summary",""))
                link = f"<a href='{html.escape(url)}' target='_blank' rel='noopener'>{title}</a>" if url else title
                lis.append(f"<li>{link} – {summary}</li>")
            ai_news_html = "<div class='callout'><ul>" + "".join(lis) + "</ul></div>"

    return {
        "TOOLS_TABLE_HTML": tools_html,
        "FUNDING_TABLE_HTML": funding_html,
        "AI_ACT_NEWS_HTML": ai_news_html,
        "last_updated": now
    }
