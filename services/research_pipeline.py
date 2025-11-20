
# -*- coding: utf-8 -*-
"""
services.research_pipeline
--------------------------
Öffentliche Entry-Funktion: run_research(answers: dict) -> dict

Gibt HTML-Strings zurück, die gpt_analyze.py direkt übernimmt:
- "TOOLS_TABLE_HTML"
- "FUNDING_TABLE_HTML"
- "MARKET_INSIGHTS_HTML"  # NEW: Perplexity-basierte Markt-Insights
- optional "NEWS_BOX_HTML"
- "last_updated"

HYBRID APPROACH (2025-11-20):
- RSS für News (kostenlos, schnell)
- Tavily für Förder-/Tool-Recherche (aktuelle Web-Ergebnisse)
- Perplexity für Markt-/Wettbewerbs-Insights (strukturierte Analyse)
"""
from __future__ import annotations

import os
import html
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .research_clients import parse_rss, harvest_links
from . import provider_tavily
from . import provider_perplexity

log = logging.getLogger(__name__)

# --- Quellen (RSS/Listen) ---

DEFAULT_NEWS_RSS = [
    # Medien (DE)
    "https://www.heise.de/rss/heise-atom.xml",
    "https://www.golem.de/rss.php?tp=ki",     # KI-Themenkanal
    "https://t3n.de/news/feed/",
    # EU / Offiziell
    "https://ec.europa.eu/newsroom/dae/document.cfm?doc_id=12461",  # falls kein RSS, wird ignoriert
]

# KNOWN RSS for EU AI Act (reliable sources often do not offer direct AI-Act feeds; keep general tech/policy feeds)
AI_ACT_NEWS_RSS = [
    "https://digital-strategy.ec.europa.eu/en/newsroom/rss.xml",
    "https://commission.europa.eu/news/press-releases_en?f%5B0%5D=topic%3A1120",  # Pressreleases (policy)
]

TOOLS_PAGES = [
    # Produktplattformen (teilweise ohne RSS; wir harvesten Links)
    # "https://www.producthunt.com/topics/artificial-intelligence",  # DISABLED: ProductHunt blockiert Scraping - benötigt API-Key
    "https://huggingface.co/models",
]

FUNDING_HINT_PAGES = [
    # Kuratierte, zuverlässige Einstiege – Nutzer kann per ENV ergänzen
    "https://www.foerderdatenbank.de/",
    "https://www.bmwk.de/Navigation/DE/Home/home.html",
    "https://digital-strategy.ec.europa.eu/en/activities/digital-programme",
    "https://www.ibb.de/de/foerderprogramme.html",  # Korrigiert: vorher /foerderprogramme/ (ohne .html)
    # "https://www.berlin.de/sen/wirtschaft/wirtschaft/foerderprogramme/",  # DISABLED: 404 Error - ersetzt durch IBB URL oben
]

def _kw(answers: Dict[str, Any]) -> List[str]:
    """Bestimme einfache Schlagwörter aus Fragebogen (Branche/Use-Cases)."""
    branche = (answers.get("BRANCHE_LABEL") or answers.get("branche") or "").lower()
    uses = answers.get("anwendungsfaelle", []) or []
    kws: set[str] = set()
    if branche:
        kws.update(word.strip() for word in branche.replace("/", " ").split())
    for u in uses:
        for w in str(u).split("_"):
            if w:
                kws.add(w)
    # Basis + EU-Bezug für KMU
    kws.update({"ai","ki","kmu","sme","eu","förderung","förder","digitalisierung"})
    return [k for k in kws if k]

def _match_any(text: str, keywords: List[str]) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in keywords)

def _tools_table(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    rows = []
    for it in items:
        # Support both "title" and "name" fields for robustness
        title = html.escape(it.get("title") or it.get("name") or it.get("source") or "Tool")
        url = html.escape(it.get("url",""))
        src = html.escape(it.get("source",""))
        rows.append(f"<tr><td>{title}</td><td><a href='{url}'>{src or url}</a></td></tr>")
    return "<table class='table'><thead><tr><th>Tool</th><th>Quelle</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"

def _funding_table(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    rows = []
    for it in items:
        # Support both "title" and "name" fields for robustness
        title = html.escape(it.get("title") or it.get("name") or "Programm")
        url = html.escape(it.get("url",""))
        src = html.escape(it.get("source",""))
        rows.append(f"<tr><td>{title}</td><td><a href='{url}'>{src or url}</a></td></tr>")
    return "<table class='table'><thead><tr><th>Programm</th><th>Quelle</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"

def _news_box(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    lis = []
    for it in items[:10]:
        title = html.escape(it.get("title",""))
        url = html.escape(it.get("url",""))
        src = html.escape(it.get("source",""))
        lis.append(f"<li><a href='{url}'>{title}</a> <span class='small muted'>({src})</span></li>")
    return "<div class='fb-section'><div class='fb-head'><span class='fb-step'>News</span><h3 class='fb-title'>Aktuelle Meldungen (kuratiert)</h3></div><ul>" + "".join(lis) + "</ul></div>"

def _market_insights_box(items: List[Dict[str, str]]) -> str:
    """Format Perplexity market insights as HTML."""
    if not items:
        return ""
    lis = []
    for it in items[:8]:
        title = html.escape(it.get("title",""))
        url = html.escape(it.get("url",""))
        content = html.escape(it.get("content","")[:200] + "..." if len(it.get("content","")) > 200 else it.get("content",""))
        if url:
            lis.append(f"<li><strong><a href='{url}'>{title}</a></strong><br/><span class='small'>{content}</span></li>")
        else:
            lis.append(f"<li><strong>{title}</strong><br/><span class='small'>{content}</span></li>")
    return "<div class='fb-section'><div class='fb-head'><span class='fb-step'>📊</span><h3 class='fb-title'>Markt & Wettbewerb (KI-Recherche)</h3></div><ul>" + "".join(lis) + "</ul></div>"

# --- TAVILY INTEGRATION ---

def _tavily_funding_search(bundesland: str, branche: str, days: int = 90) -> List[Dict[str, str]]:
    """Live-Suche nach Förderprogrammen via Tavily API."""
    if not os.getenv("TAVILY_API_KEY"):
        return []

    # Build targeted query
    query_parts = ["Förderprogramme", "KI", "Digitalisierung", "KMU"]
    if bundesland:
        query_parts.append(bundesland)
    if branche:
        query_parts.append(branche)
    query_parts.append("2025")

    query = " ".join(query_parts)
    log.info("🔍 Tavily funding search: %s", query)

    try:
        results = provider_tavily.search(query, max_results=8, days=days)
        log.info("✅ Tavily returned %d funding results", len(results))
        return results
    except Exception as exc:
        log.warning("⚠️ Tavily funding search failed: %s", exc)
        return []

def _tavily_tools_search(branche: str, use_cases: List[str], days: int = 60) -> List[Dict[str, str]]:
    """Live-Suche nach KI-Tools via Tavily API."""
    if not os.getenv("TAVILY_API_KEY"):
        return []

    # Build targeted query
    query_parts = ["KI Tools", "AI Software"]
    if branche:
        query_parts.append(branche)
    if use_cases:
        query_parts.extend(use_cases[:2])  # Max 2 use cases
    query_parts.append("2025")

    query = " ".join(query_parts)
    log.info("🔍 Tavily tools search: %s", query)

    try:
        results = provider_tavily.search(query, max_results=8, days=days)
        log.info("✅ Tavily returned %d tools results", len(results))
        return results
    except Exception as exc:
        log.warning("⚠️ Tavily tools search failed: %s", exc)
        return []

# --- PERPLEXITY INTEGRATION ---

def _perplexity_market_insights(branche: str, hauptleistung: str, days: int = 30) -> List[Dict[str, str]]:
    """Markt- und Wettbewerbs-Insights via Perplexity API."""
    if not os.getenv("PERPLEXITY_API_KEY"):
        return []

    # Build research topic
    topic_parts = ["KI Einsatz und Trends"]
    if branche:
        topic_parts.append(f"in der Branche {branche}")
    if hauptleistung:
        topic_parts.append(f"für {hauptleistung}")
    topic_parts.append("Deutschland")

    topic = " ".join(topic_parts)
    log.info("🔍 Perplexity market insights: %s", topic)

    try:
        results = provider_perplexity.search(topic, days=days, max_items=6)
        log.info("✅ Perplexity returned %d market insights", len(results))
        return results
    except Exception as exc:
        log.warning("⚠️ Perplexity market insights failed: %s", exc)
        return []

def _perplexity_competitor_analysis(branche: str, days: int = 30) -> List[Dict[str, str]]:
    """Wettbewerber-Analyse via Perplexity API."""
    if not os.getenv("PERPLEXITY_API_KEY"):
        return []

    topic = f"Wettbewerber und Marktführer KI-Lösungen {branche} Deutschland 2025"
    log.info("🔍 Perplexity competitor analysis: %s", topic)

    try:
        results = provider_perplexity.search(topic, days=days, max_items=5)
        log.info("✅ Perplexity returned %d competitor insights", len(results))
        return results
    except Exception as exc:
        log.warning("⚠️ Perplexity competitor analysis failed: %s", exc)
        return []

def run_research(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    HYBRID APPROACH: Combines RSS, Tavily, and Perplexity for optimal results.

    Returns:
      {
        "TOOLS_TABLE_HTML": "...",
        "FUNDING_TABLE_HTML": "...",
        "MARKET_INSIGHTS_HTML": "...",  # NEW
        "NEWS_BOX_HTML": "...",
        "last_updated": "YYYY-MM-DD"
      }
    """
    provider = os.getenv("RESEARCH_PROVIDER", "hybrid").strip().lower()
    # offline-only short-circuit
    offline_only = provider == "offline"

    # Extract context from answers
    branche = answers.get("BRANCHE_LABEL") or answers.get("branche") or ""
    bundesland = answers.get("BUNDESLAND_LABEL") or answers.get("bundesland") or ""
    hauptleistung = answers.get("hauptleistung") or ""
    use_cases = answers.get("anwendungsfaelle", []) or []

    kws = _kw(answers)
    tools: List[Dict[str, str]] = []
    funding: List[Dict[str, str]] = []
    news: List[Dict[str, str]] = []
    market_insights: List[Dict[str, str]] = []

    if not offline_only:
        log.info("🔬 Running HYBRID research (Tavily + Perplexity + RSS)...")

        # --- PARALLEL API CALLS for better performance ---
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}

            # 1. Tavily for Tools
            if os.getenv("TAVILY_API_KEY"):
                futures["tavily_tools"] = executor.submit(
                    _tavily_tools_search, branche, use_cases
                )

            # 2. Tavily for Funding
            if os.getenv("TAVILY_API_KEY"):
                futures["tavily_funding"] = executor.submit(
                    _tavily_funding_search, bundesland, branche
                )

            # 3. Perplexity for Market Insights
            if os.getenv("PERPLEXITY_API_KEY"):
                futures["pplx_market"] = executor.submit(
                    _perplexity_market_insights, branche, hauptleistung
                )

            # 4. Perplexity for Competitor Analysis
            if os.getenv("PERPLEXITY_API_KEY"):
                futures["pplx_competitor"] = executor.submit(
                    _perplexity_competitor_analysis, branche
                )

            # Collect results
            for key, future in futures.items():
                try:
                    result = future.result(timeout=30)
                    if key == "tavily_tools":
                        tools.extend(result)
                    elif key == "tavily_funding":
                        funding.extend(result)
                    elif key in ("pplx_market", "pplx_competitor"):
                        market_insights.extend(result)
                except Exception as exc:
                    log.warning("⚠️ %s failed: %s", key, exc)

    # --- FALLBACK: Traditional web scraping if Tavily returned nothing ---
    if not tools and not offline_only:
        log.info("📡 Tavily returned no tools, falling back to web scraping...")
        try:
            for url in TOOLS_PAGES:
                items = harvest_links(url, allow_domains=None, limit=30)
                sel = [i for i in items if _match_any((i.get("title","") + " " + i.get("url","")), kws)]
                tools.extend(sel[:10])
        except Exception as exc:
            log.warning("TOOLS harvest failed: %s", exc)

    if not tools:
        # Static fallback
        tools = [
            {"title": "OpenAI GPT‑4o", "url": "https://openai.com/", "source": "openai.com"},
            {"title": "Azure OpenAI Service", "url": "https://azure.microsoft.com/services/cognitive-services/openai-service/", "source": "azure.microsoft.com"},
            {"title": "Hugging Face Models", "url": "https://huggingface.co/models", "source": "huggingface.co"},
        ]

    # --- FUNDING FALLBACK ---
    if not funding and not offline_only:
        log.info("📡 Tavily returned no funding, falling back to web scraping...")
        extra_funding_pages = [u.strip() for u in os.getenv("FUNDING_PAGES", "").split(",") if u.strip()]
        pages = FUNDING_HINT_PAGES + extra_funding_pages

        try:
            for url in pages:
                items = harvest_links(url, allow_domains=None, limit=40)
                sel = [i for i in items if _match_any((i.get("title","") + " " + i.get("url","")), ["förder", "grant", "fund", "digital", "ai", "ki", "kmu", "sme"])]
                funding.extend(sel[:10])
        except Exception as exc:
            log.warning("FUNDING harvest failed: %s", exc)

    # Static JSON fallback
    if not funding:
        try:
            import json
            path = os.getenv("FUNDING_FALLBACK_PATH", "data/funding_programs.json")
            if os.path.exists(path):
                raw = json.load(open(path, "r", encoding="utf-8"))
                for it in raw[:12]:
                    title = it.get("title") or it.get("name") or "Programm"
                    funding.append({
                        "title": title,
                        "url": it.get("url",""),
                        "source": it.get("url","")
                    })
        except Exception as exc:
            log.warning("FUNDING fallback failed: %s", exc)

    # --- NEWS via RSS (always use RSS - it's fast and free) ---
    if not offline_only:
        try:
            for url in (AI_ACT_NEWS_RSS + DEFAULT_NEWS_RSS):
                items = parse_rss(url, limit=8)
                sel = [i for i in items if _match_any((i.get("title","") + " " + i.get("summary","")), ["ai act","eu ai act","künstliche intelligenz","ki","sme","kmu","förderung","compliance","policy","gesetz"])]
                news.extend(sel[:6])
        except Exception as exc:
            log.warning("NEWS parse failed: %s", exc)

    # Deduplicate by URL
    def _uniq(lst: List[Dict[str, str]]) -> List[Dict[str, str]]:
        seen, out = set(), []
        for it in lst:
            u = it.get("url","")
            if not u or u in seen:
                continue
            seen.add(u)
            out.append(it)
        return out

    tools = _uniq(tools)[:12]
    funding = _uniq(funding)[:12]
    news = _uniq(news)[:12]
    market_insights = _uniq(market_insights)[:10]

    # Log summary
    log.info("📊 Research complete: %d tools, %d funding, %d news, %d market insights",
             len(tools), len(funding), len(news), len(market_insights))

    data: Dict[str, Any] = {
        "TOOLS_TABLE_HTML": _tools_table(tools),
        "FUNDING_TABLE_HTML": _funding_table(funding),
        "MARKET_INSIGHTS_HTML": _market_insights_box(market_insights),  # NEW
        "NEWS_BOX_HTML": _news_box(news),
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    return data
