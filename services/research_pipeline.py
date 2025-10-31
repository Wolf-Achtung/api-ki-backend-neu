# -*- coding: utf-8 -*-
"""
services/research_pipeline.py
-----------------------------
Orchestriert Recherche über Tavily & Perplexity gemäß Research-Policy und
liefert strukturierte HTML-Blöcke für das PDF-Template.

Public:
    run_research(briefing: dict, policy: ResearchPolicy = DEFAULT_POLICY) -> dict

Return keys (merge-ready for template):
    - "TOOLS_HTML"
    - "FOERDERPROGRAMME_HTML"
    - "QUELLEN_HTML"
    - "last_updated": "YYYY-MM-DD"
"""
from __future__ import annotations
import logging
import datetime as dt
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .research_policy import ResearchPolicy, DEFAULT_POLICY, queries_for_briefing
from .research_clients import TavilyClient, PerplexityClient

log = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def _domain_score(host: str, policy: ResearchPolicy) -> float:
    # einfache Qualitätsgewichtung
    if any(h in host for h in policy.include_funding):
        return 1.0
    if any(h in host for h in policy.include_tools_hint):
        return 0.7
    return 0.5

def _dedup(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for it in items:
        key = it.get("url", "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

def _filter_domains(items: Iterable[Dict[str, Any]], policy: ResearchPolicy) -> List[Dict[str, Any]]:
    out = []
    for it in items:
        h = _host(it.get("url", ""))
        if not h:
            continue
        if any(bad in h for bad in policy.exclude_global):
            continue
        out.append(it)
    return out

def _filter_recency(items: Iterable[Dict[str, Any]], min_days: int, max_days: int) -> List[Dict[str, Any]]:
    today = dt.date.today()
    out = []
    for it in items:
        dstr = (it.get("published_at") or "").strip()
        if not dstr:
            # kein Datum -> zulassen, aber später niedriger score
            out.append(it)
            continue
        try:
            d = dt.date.fromisoformat(dstr[:10])
            delta = (today - d).days
            if min_days <= delta <= max_days:
                out.append(it)
        except Exception:
            out.append(it)
    return out

def _rank(items: Iterable[Dict[str, Any]], policy: ResearchPolicy) -> List[Dict[str, Any]]:
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

def _html_table(rows: List[List[str]], header: List[str]) -> str:
    head = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr></thead>"
    body = "<tbody>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</tbody>"
    return f'<table class="table">{head}{body}</table>'

def _a(label: str, href: str) -> str:
    return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{label}</a>'

# -----------------------------------------------------------------------------
# Builders
# -----------------------------------------------------------------------------

def _build_tools_html(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "<p><em>Keine verlässlichen Tool‑Quellen im Zeitraum gefunden.</em></p>"
    # Kompakte Tabelle: Tool/Anbieter (Host), Link
    rows = []
    for it in items[:10]:
        host = _host(it["url"])
        rows.append([it["title"], host, _a("Quelle", it["url"])])
    return _html_table(rows, ["Tool/Produkt", "Host", "Link"])

def _build_funding_html(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "<p><em>Keine geeigneten Förderprogramme im Zeitraum gefunden.</em></p>"
    # Tabelle: Programm, Träger/Region, Deadline, Link
    rows = []
    for it in items[:12]:
        host = _host(it["url"])
        rows.append([it["title"], host, (it.get("published_at") or "—"), _a("Details", it["url"])])
    return _html_table(rows, ["Programm", "Träger/Region", "Deadline/Datum", "Link"])

def _build_sources_html(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "<p><em>Keine Quellen verfügbar.</em></p>"
    rows = []
    for it in items[:12]:
        host = _host(it["url"])
        rows.append([it["title"], host, (it.get("published_at") or "—"), _a("Link", it["url"])])
    return _html_table(rows, ["Titel", "Host", "Datum", "Link"])

# -----------------------------------------------------------------------------
# Public
# -----------------------------------------------------------------------------

def run_research(briefing: Dict[str, Any], policy: ResearchPolicy = DEFAULT_POLICY) -> Dict[str, Any]:
    """
    Führt die Recherche aus und liefert HTML-Blöcke + last_updated.
    """
    tavily = TavilyClient()
    pplx = PerplexityClient()

    q = queries_for_briefing(briefing)
    all_tools: List[Dict[str, Any]] = []
    all_funding: List[Dict[str, Any]] = []
    all_sources: List[Dict[str, Any]] = []

    # --- Tools ---
    for query in q["tools"]:
        all_tools += tavily.search(
            query,
            include_domains=policy.include_tools_hint,
            exclude_domains=policy.exclude_global,
            days=policy.max_days,
            max_results=policy.max_results_tools,
        )
    if len(all_tools) < 4 and pplx.available():
        all_tools += pplx.ask_json("Gib 6 aktuelle (7–60 Tage) KI‑Tools/Produkt-Updates für KMU in DE/EU mit Link und Datum – nur Primärquellen (Hersteller/Docs/Trust Center) – JSON array.")

    # --- Funding ---
    for query in q["funding"]:
        all_funding += tavily.search(
            query,
            include_domains=policy.include_funding,
            exclude_domains=policy.exclude_global,
            days=policy.max_days,
            max_results=policy.max_results_funding,
        )
    if len(all_funding) < 4 and pplx.available():
        all_funding += pplx.ask_json("Gib 6 aktuelle (7–60 Tage) Förderaufrufe/Programme (DE/EU) für KMU mit Deadlines – NUR Primärquellen (BMWK, EU, Landesbanken) – JSON array.")

    # --- AI Act / Quellen ---
    for query in q["ai_act"]:
        all_sources += tavily.search(
            query,
            exclude_domains=policy.exclude_global,
            days=policy.max_days,
            max_results=policy.max_results_sources,
        )
    if len(all_sources) < 4 and pplx.available():
        all_sources += pplx.ask_json("Liste 6 aktuelle (7–60 Tage) Primärquellen (DE/EU) zum EU AI Act / Leitfäden für Unternehmen – JSON array.")

    # Filter/Dedup/Rank
    tools = _rank(_dedup(_filter_domains(all_tools, policy)), policy)
    funding = _rank(_dedup(_filter_domains(all_funding, policy)), policy)
    sources = _rank(_dedup(_filter_domains(all_sources, policy)), policy)

    # HTML bauen
    tools_html = _build_tools_html(tools)
    funding_html = _build_funding_html(funding)
    sources_html = _build_sources_html(sources)

    today = dt.date.today().isoformat()
    return {
        "TOOLS_HTML": tools_html,
        "FOERDERPROGRAMME_HTML": funding_html,
        "QUELLEN_HTML": sources_html,
        "last_updated": today,
    }
