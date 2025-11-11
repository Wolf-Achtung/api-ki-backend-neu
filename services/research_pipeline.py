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
    """
    Extrahiert Zeitfenster aus Briefing-Antworten oder ENV.
    UI-Feld „research_days": erlaubt 7, 30, 60
    """
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
    """
    Hauptfunktion: Recherchiert Tools, Förderprogramme und AI-Act-Quellen.
    
    Args:
        briefing: Briefing-Antworten Dict
        policy: ResearchPolicy mit Domain-Whitelists/Blacklists
        
    Returns:
        Dict mit HTML-Tabellen für Template:
        - TOOLS_HTML
        - FOERDERPROGRAMME_HTML  
        - QUELLEN_HTML
        - last_updated
    """
    # ✅ Clients mit Error-Handling initialisieren
    try:
        tavily = TavilyClient()
    except Exception as exc:
        log.error("❌ TavilyClient init failed: %s", exc)
        tavily = None
    
    try:
        pplx = PerplexityClient()
    except Exception as exc:
        log.warning("⚠️ PerplexityClient init failed (optional): %s", exc)
        pplx = None

    q = queries_for_briefing(briefing)
    days = _days_from_answers(briefing or {}, policy.default_days)
    
    log.info("🔍 Research starting: days=%d, queries=%s", days, {k: len(v) for k, v in q.items()})

    all_tools: List[Dict[str, Any]] = []
    all_funding: List[Dict[str, Any]] = []
    all_sources: List[Dict[str, Any]] = []

    # ========== TOOLS ==========
    if tavily:
        for query in q["tools"]:
            try:
                results = tavily.search(
                    query,
                    include_domains=policy.include_tools_hint,
                    exclude_domains=policy.exclude_global,
                    days=days,
                    max_results=policy.max_results_tools,
                )
                all_tools += results
                log.debug("📦 Tavily tools: query='%s' -> %d results", query, len(results))
            except Exception as exc:
                log.warning("⚠️ Tavily tools search failed for '%s': %s", query, exc)
    
    # Perplexity Fallback für Tools
    if len(all_tools) < 4 and pplx and pplx.available():
        try:
            fallback = pplx.ask_json(
                "Gib 6 aktuelle (7–60 Tage) KI-Tools/Produkt-Updates für KMU in DE/EU "
                "mit Link und Datum – nur Primärquellen (Hersteller/Docs/Trust Center) – JSON array."
            )
            all_tools += fallback
            log.info("🔄 Perplexity tools fallback: +%d results", len(fallback))
        except Exception as exc:
            log.warning("⚠️ Perplexity tools fallback failed: %s", exc)

    # ========== FUNDING ==========
    if tavily:
        for query in q["funding"]:
            try:
                results = tavily.search(
                    query,
                    include_domains=policy.include_funding,
                    exclude_domains=policy.exclude_global,
                    days=days,
                    max_results=policy.max_results_funding,
                )
                all_funding += results
                log.debug("💰 Tavily funding: query='%s' -> %d results", query, len(results))
            except Exception as exc:
                log.warning("⚠️ Tavily funding search failed for '%s': %s", query, exc)
    
    # Perplexity Fallback für Funding
    if len(all_funding) < 4 and pplx and pplx.available():
        try:
            fallback = pplx.ask_json(
                "Gib 6 aktuelle (7–60 Tage) Förderaufrufe/Programme (DE/EU) für KMU "
                "mit Deadlines – NUR Primärquellen (BMWK, EU, Landesbanken) – JSON array."
            )
            all_funding += fallback
            log.info("🔄 Perplexity funding fallback: +%d results", len(fallback))
        except Exception as exc:
            log.warning("⚠️ Perplexity funding fallback failed: %s", exc)

    # ========== AI ACT / SOURCES ==========
    if tavily:
        for query in q["ai_act"]:
            try:
                results = tavily.search(
                    query,
                    exclude_domains=policy.exclude_global,
                    days=days,
                    max_results=policy.max_results_sources,
                )
                all_sources += results
                log.debug("📚 Tavily sources: query='%s' -> %d results", query, len(results))
            except Exception as exc:
                log.warning("⚠️ Tavily sources search failed for '%s': %s", query, exc)
    
    # Perplexity Fallback für Sources
    if len(all_sources) < 4 and pplx and pplx.available():
        try:
            fallback = pplx.ask_json(
                "Liste 6 aktuelle (7–60 Tage) Primärquellen (DE/EU) zum EU AI Act / "
                "Leitfäden für Unternehmen – JSON array."
            )
            all_sources += fallback
            log.info("🔄 Perplexity sources fallback: +%d results", len(fallback))
        except Exception as exc:
            log.warning("⚠️ Perplexity sources fallback failed: %s", exc)

    # ========== FILTER/DEDUP/RANK PIPELINE ==========
    def pipeline(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter -> Dedup -> Rank"""
        # 1. Filter: Nur Items mit URL
        out = [x for x in items if x.get("url")]
        
        # 2. Filter: Global exclude domains
        out = [x for x in out if not any(bad in urlparse(x["url"]).netloc.lower() for bad in policy.exclude_global)]
        
        # 3. Dedup by URL
        deduped = []
        seen = set()
        for x in out:
            u = x["url"]
            if u in seen:
                continue
            seen.add(u)
            deduped.append(x)
        
        # 4. Rank by domain quality
        ranked = []
        for it in deduped:
            h = urlparse(it["url"]).netloc.lower()
            score = 1.0 if any(hint in h for hint in policy.include_funding) else \
                    0.7 if any(hint in h for hint in policy.include_tools_hint) else 0.5
            if not it.get("published_at"):
                score -= 0.1
            it["score"] = max(0.0, score)
            ranked.append(it)
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked

    tools = pipeline(all_tools)
    funding = pipeline(all_funding)
    sources = pipeline(all_sources)
    
    log.info("✅ Research complete: tools=%d, funding=%d, sources=%d", len(tools), len(funding), len(sources))

    # ========== HTML GENERATION ==========
    tools_html = _html_table(
        _tools_rows(tools), 
        ["Tool/Produkt", "Anbieter (Host)", "Preis-Hinweis", "DSGVO/Trust Center", "Link"]
    )
    funding_html = _html_table(
        _funding_rows(funding), 
        ["Programm", "Träger/Region", "Deadline/Datum", "Link"]
    )
    sources_html = _html_table(
        _sources_rows(sources), 
        ["Titel", "Host", "Datum", "Link"]
    )

    today = dt.date.today().isoformat()
    
    return {
        "TOOLS_HTML": tools_html,
        "FOERDERPROGRAMME_HTML": funding_html,
        "QUELLEN_HTML": sources_html,
        "last_updated": today,
    }
