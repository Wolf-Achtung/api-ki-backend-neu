# -*- coding: utf-8 -*-
"""
services/research_pipeline.py
-----------------------------
Orchestriert Recherche über Tavily & Perplexity gemäß Research-Policy.
Dynamische Zeitfenster (7/30/60) werden aus den Antworten oder ENV gelesen.

Public:
    run_research(briefing: dict, policy: ResearchPolicy = DEFAULT_POLICY) -> dict

Return keys (merge-ready for template):
    - "TOOLS_HTML"
    - "FOERDERPROGRAMME_HTML"
    - "QUELLEN_HTML"
    - "last_updated": "YYYY-MM-DD"
"""
from __future__ import annotations
import os
import logging
import datetime as dt
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

from .research_policy import ResearchPolicy, DEFAULT_POLICY, queries_for_briefing
from .research_clients import TavilyClient, PerplexityClient

log = logging.getLogger(__name__)


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def _domain_score(host: str, policy: ResearchPolicy) -> float:
    if any(h in host for h in policy.include_funding):
        return 1.0
    if any(h in host for h in policy.include_tools_hint):
        return 0.7
    return 0.5

def _dedup(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for it in items:
        key = it.get("url", "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

def _filter_domains(items: List[Dict[str, Any]], policy: ResearchPolicy) -> List[Dict[str, Any]]:
    out = []
    for it in items:
        h = _host(it.get("url", ""))
        if not h:
            continue
        if any(bad in h for bad in policy.exclude_global):
            continue
        out.append(it)
    return out

def _rank(items: List[Dict[str, Any]], policy: ResearchPolicy) -> List[Dict[str, Any]]:
    ranked = []
    for it in items:
        h = _host(it.get("url", ""))
        score = _domain_score(h, policy)
        if not it.get("published_at"):
            score -= 0.1
        it["score"] = max(0.0, score)
        ranked.append(it)
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked

def _a(label: str, href: str) -> str:
    return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{label}</a>'

def _html_table(rows: List[List[str]], header: List[str]) -> str:
    head = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr></thead>"
    body = "<tbody>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</tbody>"
    return f'<table class="table">{head}{body}</table>'

def _days_from_answers(answers: Dict[str, Any], fallback: int) -> int:
    # UI-Feld „research_days“: erlaubt 7, 30, 60
    v = (answers or {}).get("research_days") or (answers or {}).get("tools_days") or (answers or {}).get("funding_days")
    if v:
        try:
            v = int(v)
            if v in (7, 30, 60):
                return v
        except Exception:
            pass
    # ENV Fallbacks
    for name in ("TOOLS_DAYS", "FUNDING_DAYS", "RESEARCH_DAYS_DEFAULT"):
        val = os.getenv(name)
        if val:
            try:
                x = int(val)
                if x in (7, 30, 60):
                    return x
            except Exception:
                pass
    return fallback

def _tools_rows(items: List[Dict[str, Any]]) -> List[List[str]]:
    rows = []
    for it in items[:10]:
        host = _host(it["url"])
        rows.append([it["title"], host, it.get("price_hint", "—"), it.get("tc", "—"), _a("Quelle", it["url"])])
    return rows

def _funding_rows(items: List[Dict[str, Any]]) -> List[List[str]]:
    rows = []
    for it in items[:12]:
        host = _host(it["url"])
        rows.append([it["title"], host, (it.get("published_at") or "—"), _a("Details", it["url"])])
    return rows

def _sources_rows(items: List[Dict[str, Any]]) -> List[List[str]]:
    rows = []
    for it in items[:12]:
        host = _host(it["url"])
        rows.append([it["title"], host, (it.get("published_at") or "—"), _a("Link", it["url"])])
    return rows

def run_research(briefing: Dict[str, Any], policy: ResearchPolicy = DEFAULT_POLICY) -> Dict[str, Any]:
    tavily = TavilyClient()
    pplx = PerplexityClient()
    q = queries_for_briefing(briefing)

    days = _days_from_answers(briefing or {}, policy.default_days)

    all_tools: List[Dict[str, Any]] = []
    all_funding: List[Dict[str, Any]] = []
    all_sources: List[Dict[str, Any]] = []

    # Tools
    for query in q["tools"]:
        all_tools += tavily.search(
            query,
            include_domains=policy.include_tools_hint,
            exclude_domains=policy.exclude_global,
            days=days,
            max_results=policy.max_results_tools,
        )
    if len(all_tools) < 4 and pplx.available():
        all_tools += pplx.ask_json("Gib 6 aktuelle (7–60 Tage) KI‑Tools/Produkt-Updates für KMU in DE/EU mit Link und Datum – nur Primärquellen (Hersteller/Docs/Trust Center) – JSON array.")

    # Funding
    for query in q["funding"]:
        all_funding += tavily.search(
            query,
            include_domains=policy.include_funding,
            exclude_domains=policy.exclude_global,
            days=days,
            max_results=policy.max_results_funding,
        )
    if len(all_funding) < 4 and pplx.available():
        all_funding += pplx.ask_json("Gib 6 aktuelle (7–60 Tage) Förderaufrufe/Programme (DE/EU) für KMU mit Deadlines – NUR Primärquellen (BMWK, EU, Landesbanken) – JSON array.")

    # AI Act / Sources
    for query in q["ai_act"]:
        all_sources += tavily.search(
            query,
            exclude_domains=policy.exclude_global,
            days=days,
            max_results=policy.max_results_sources,
        )
    if len(all_sources) < 4 and pplx.available():
        all_sources += pplx.ask_json("Liste 6 aktuelle (7–60 Tage) Primärquellen (DE/EU) zum EU AI Act / Leitfäden für Unternehmen – JSON array.")

    # Filter/Dedup/Rank
    def pipeline(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = [x for x in items if x.get("url")]
        # Filter global domains
        out = [x for x in out if not any(bad in (urlparse(x["url"]).netloc.lower()) for bad in policy.exclude_global)]
        # Dedup by URL
        deduped = []
        seen = set()
        for x in out:
            u = x["url"]
            if u in seen:
                continue
            seen.add(u)
            deduped.append(x)
        # Rank
        ranked = []
        for it in deduped:
            h = urlparse(it["url"]).netloc.lower()
            score = 1.0 if any(hint in h for hint in policy.include_funding) else 0.7 if any(hint in h for hint in policy.include_tools_hint) else 0.5
            if not it.get("published_at"):
                score -= 0.1
            it["score"] = max(0.0, score)
            ranked.append(it)
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked

    tools = pipeline(all_tools)
    funding = pipeline(all_funding)
    sources = pipeline(all_sources)

    tools_html = _html_table(_tools_rows(tools), ["Tool/Produkt", "Anbieter (Host)", "Preis‑Hinweis", "DSGVO/Trust Center", "Link"])
    funding_html = _html_table(_funding_rows(funding), ["Programm", "Träger/Region", "Deadline/Datum", "Link"])
    sources_html = _html_table(_sources_rows(sources), ["Titel", "Host", "Datum", "Link"])

    today = dt.date.today().isoformat()
    return {
        "TOOLS_HTML": tools_html,
        "FOERDERPROGRAMME_HTML": funding_html,
        "QUELLEN_HTML": sources_html,
        "last_updated": today,
    }
