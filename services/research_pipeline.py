# -*- coding: utf-8 -*-
"""
services.research_pipeline
Bündelt Recherche über Tavily + Perplexity (Hybrid).
Erzeugt HTML-Tabellen, die gpt_analyze konsumiert:
- TOOLS_TABLE_HTML
- FUNDING_TABLE_HTML
- last_updated
"""
from __future__ import annotations
import os, logging, html
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from .research_clients import hybrid_search, tavily_search, perplexity_search

log = logging.getLogger(__name__)

PROVIDER = os.getenv("RESEARCH_PROVIDER", "hybrid").strip().lower()
RECENCY_DAYS = int(os.getenv("RESEARCH_DAYS", "7"))
MAX_RESULTS = int(os.getenv("RESEARCH_MAX_RESULTS", "12"))

_OFFICIAL = {"bmwk.de","bund.de","bmbf.de","bmi.bund.de","europa.eu","ec.europa.eu","commission.europa.eu",
             "berlin.de","service.berlin.de","foerderdatenbank.de","bsi.bund.de","bafin.de"}

def _provider_search(queries: List[str]) -> List[Dict[str,str]]:
    if PROVIDER == "disabled":
        return []
    if PROVIDER == "tavily":
        out = []
        for q in queries:
            out.extend(tavily_search(q, max_results=MAX_RESULTS, days=RECENCY_DAYS))
        return out
    if PROVIDER == "perplexity":
        out = []
        for q in queries:
            out.extend(perplexity_search(q, max_results=MAX_RESULTS))
        return out
    # default hybrid
    return hybrid_search(queries, max_results=MAX_RESULTS, days=RECENCY_DAYS)

def _table(head: List[str], rows: List[List[str]]) -> str:
    thead = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead>"
    body = "<tbody>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</tbody>"
    return f"<table class='table'>{thead}{body}</table>"

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def _sort_links(urls: List[Tuple[str,str]]) -> List[Tuple[str,str]]:
    def key(x):
        dom = _domain(x[0])
        cat = 0 if any(dom==d or dom.endswith("."+d) for d in _OFFICIAL) else 1
        return (cat, dom, x[1].lower())
    return sorted(urls, key=key)

def _size_hint(size_label: str) -> str:
    s = (size_label or "").lower()
    if "solo" in s: return "Solo/Selbstständig"
    if "2" in s or "team" in s: return "Kleines Team"
    if "kmu" in s or "11" in s or "100" in s: return "KMU"
    return "KMU"

def run_research(answers: Dict[str, str]) -> Dict[str, str]:
    branche = answers.get("BRANCHE_LABEL") or answers.get("branche") or ""
    bundesland = answers.get("BUNDESLAND_LABEL") or answers.get("bundesland") or ""
    groesse = answers.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse") or ""
    size_hint = _size_hint(groesse)

    # --------- Queries ---------
    tool_queries = [
        f"beste KI Tools {branche} 2025 DSGVO EU hosting pricing",
        f"{branche} generative AI tools Germany GDPR 2025 review",
        f"{branche} workflow automation tools 2025 EU",
        "Azure OpenAI EU alternatives Mistral Aleph Alpha German market"
    ]
    funding_queries = [
        f"{bundesland} Förderprogramm Digitalisierung KI 2025 KMU Zuschuss",
        f"{bundesland} Innovationsförderung 2025 Pro FIT ZIM go-digital",
        "Deutschland Förderprogramme KI Mittelstand 2025 Liste",
        "EU-Programme KI KMU 2025 Ausschreibungen"
    ]

    # --------- Search ---------
    tools_items = _provider_search(tool_queries)
    fund_items = _provider_search(funding_queries)

    # --------- Build TOOLS table ---------
    tool_rows: List[List[str]] = []
    for it in tools_items[:MAX_RESULTS]:
        href = it.get("url","").strip()
        if not href: 
            continue
        title = html.escape((it.get("title") or href).strip())
        link = f"<a href='{href}' target='_blank' rel='noopener'>{title}</a>"
        # Kategorie/Preis/DSGVO: Platzhalter – werden später von _rewrite_table_links_with_labels überschrieben/ergänzt
        tool_rows.append([title, "—", "—", "—", link])
    tools_html = _table(["Tool/Produkt","Kategorie","Preis","DSGVO/Host","Links"], tool_rows) if tool_rows else ""

    # --------- Build FUNDING table ---------
    fund_rows: List[List[str]] = []
    for it in fund_items[:MAX_RESULTS]:
        href = it.get("url","").strip()
        if not href:
            continue
        title = html.escape((it.get("title") or href).strip())
        link = f"<a href='{href}' target='_blank' rel='noopener'>Förderrichtlinie</a>"
        ziel = "Solo" if "solo" in size_hint.lower() else "KMU"
        fund_rows.append([title, "—", ziel, "—", f"{ziel}-Passung kurz", link])
    funding_html = _table(["Programm","Förderung","Zielgruppe","Deadline","Eligibility","Quelle"], fund_rows) if fund_rows else ""

    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "TOOLS_TABLE_HTML": tools_html,
        "FUNDING_TABLE_HTML": funding_html,
        "last_updated": last_updated
    }
