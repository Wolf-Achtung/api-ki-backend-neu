
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

=============================================================================
Sprint N3-01: RESEARCH RELIABILITY LAYER
=============================================================================
- 2-stage retry mechanism for Perplexity timeouts
- Fallback to Tavily-only mode after max retries
- Research mode tagging (hybrid, tavily_only, partial_perplexity)
- Short Query Mode for finance/beratung branches with EN language

=============================================================================
Sprint N4.3: RESEARCH INTEGRATION MAPPING
=============================================================================

RESEARCH → REPORT INTEGRATION MAP:

  ┌─────────────────────────┬─────────────────────────┬──────────────────────┐
  │ Research Output         │ Section Alias           │ Template Variable    │
  ├─────────────────────────┼─────────────────────────┼──────────────────────┤
  │ TOOLS_TABLE_HTML        │ → TOOLS_HTML            │ {{ TOOLS_HTML }}     │
  ├─────────────────────────┼─────────────────────────┼──────────────────────┤
  │ FUNDING_TABLE_HTML      │ → FOERDERPROGRAMME_HTML │ {{ FOERDER... }}     │
  ├─────────────────────────┼─────────────────────────┼──────────────────────┤
  │ MARKET_INSIGHTS_HTML    │ (direct)                │ {{ MARKET_... }}     │
  ├─────────────────────────┼─────────────────────────┼──────────────────────┤
  │ NEWS_BOX_HTML           │ (direct)                │ {{ NEWS_BOX_HTML }}  │
  ├─────────────────────────┼─────────────────────────┼──────────────────────┤
  │ last_updated            │ → research_last_updated │ {{ LAST_UPDATED }}   │
  ├─────────────────────────┼─────────────────────────┼──────────────────────┤
  │ research_status (new)   │ (internal tracking)     │ N/A                  │
  └─────────────────────────┴─────────────────────────┴──────────────────────┘

STATUS TRACKING (Sprint N4.1):
  research_status = {
    "tools": success | partial | fallback | error,
    "funding": success | partial | fallback | error,
    "market": success | partial | fallback | error,
    "news": success | partial | fallback | error,
  }

FALLBACK CHAIN (Sprint N4.1):
  1. Tavily/Perplexity API call
  2. Web scraping fallback (if API empty)
  3. Static fallback HTML (if scraping empty)
  4. Fallback generators: _tools_fallback_html(), _funding_fallback_html(), etc.

INTEGRATION POINT: gpt_analyze.py (line ~4520)
  research_blocks = run_research(answers)
  sections.update(research_blocks)

=============================================================================
"""
from __future__ import annotations

import os
import html
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from .research_clients import parse_rss, harvest_links
from . import provider_tavily
from . import provider_perplexity

log = logging.getLogger(__name__)

# =============================================================================
# Sprint N3-01: Research Reliability Configuration
# =============================================================================
RETRY_DELAYS = [1.5, 3.0]  # Exponential backoff delays in seconds
MAX_RETRIES = 2

# Branches that benefit from short query mode
SHORT_QUERY_BRANCHES = ["finance", "finanzen", "beratung", "consulting", "banking"]

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

# Max sichtbare Items pro Kategorie (Rest in <details> collapse)
MAX_VISIBLE_ITEMS = 6


def _build_rows_with_collapse(
    items: List[Dict[str, str]],
    row_builder,
    max_visible: int = MAX_VISIBLE_ITEMS
) -> Tuple[str, str]:
    """
    Teilt Items in sichtbare Rows und versteckte Rows.

    Returns:
        Tuple of (visible_rows_html, hidden_rows_html)
    """
    visible = items[:max_visible]
    hidden = items[max_visible:]

    visible_rows = "".join(row_builder(it) for it in visible)
    hidden_rows = "".join(row_builder(it) for it in hidden) if hidden else ""

    return visible_rows, hidden_rows


def _tools_table(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""

    def build_row(it):
        title = html.escape(it.get("title") or it.get("name") or it.get("source") or "Tool")
        url = html.escape(it.get("url", ""))
        src = html.escape(it.get("source", ""))
        return f"<tr><td>{title}</td><td><a href='{url}'>{src or url}</a></td></tr>"

    visible_rows, hidden_rows = _build_rows_with_collapse(items, build_row)

    table_html = "<table class='table table-modern'><thead><tr><th>Tool</th><th>Quelle</th></tr></thead><tbody>"
    table_html += visible_rows
    table_html += "</tbody></table>"

    if hidden_rows:
        hidden_count = len(items) - MAX_VISIBLE_ITEMS
        table_html += f"<details class='research-overflow'><summary class='small'>Weitere Tools ({hidden_count})</summary>"
        table_html += "<table class='table table-modern'><tbody>" + hidden_rows + "</tbody></table></details>"

    return table_html


def _funding_table(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""

    def build_row(it):
        title = html.escape(it.get("title") or it.get("name") or "Programm")
        url = html.escape(it.get("url", ""))
        src = html.escape(it.get("source", ""))
        return f"<tr><td>{title}</td><td><a href='{url}'>{src or url}</a></td></tr>"

    visible_rows, hidden_rows = _build_rows_with_collapse(items, build_row)

    table_html = "<table class='table table-modern'><thead><tr><th>Programm</th><th>Quelle</th></tr></thead><tbody>"
    table_html += visible_rows
    table_html += "</tbody></table>"

    if hidden_rows:
        hidden_count = len(items) - MAX_VISIBLE_ITEMS
        table_html += f"<details class='research-overflow'><summary class='small'>Weitere Programme ({hidden_count})</summary>"
        table_html += "<table class='table table-modern'><tbody>" + hidden_rows + "</tbody></table></details>"

    return table_html


def _news_box(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""

    visible = items[:MAX_VISIBLE_ITEMS]
    hidden = items[MAX_VISIBLE_ITEMS:]

    lis = []
    for it in visible:
        title = html.escape(it.get("title", ""))
        url = html.escape(it.get("url", ""))
        src = html.escape(it.get("source", ""))
        lis.append(f"<li><a href='{url}'>{title}</a> <span class='small muted'>({src})</span></li>")

    html_out = "<div class='fb-section'><div class='fb-head'><span class='fb-step'>News</span><h3 class='fb-title'>Aktuelle Meldungen (kuratiert)</h3></div><ul>" + "".join(lis) + "</ul>"

    if hidden:
        hidden_lis = []
        for it in hidden:
            title = html.escape(it.get("title", ""))
            url = html.escape(it.get("url", ""))
            hidden_lis.append(f"<li><a href='{url}'>{title}</a></li>")
        html_out += f"<details class='research-overflow'><summary class='small'>Weitere News ({len(hidden)})</summary><ul>" + "".join(hidden_lis) + "</ul></details>"

    html_out += "</div>"
    return html_out


def _market_insights_box(items: List[Dict[str, str]]) -> str:
    """Format Perplexity market insights as HTML with collapse for overflow."""
    if not items:
        return ""

    visible = items[:MAX_VISIBLE_ITEMS]
    hidden = items[MAX_VISIBLE_ITEMS:]

    lis = []
    for it in visible:
        title = html.escape(it.get("title", ""))
        url = html.escape(it.get("url", ""))
        content = html.escape(it.get("content", "")[:200] + "..." if len(it.get("content", "")) > 200 else it.get("content", ""))
        if url:
            lis.append(f"<li><strong><a href='{url}'>{title}</a></strong><br/><span class='small'>{content}</span></li>")
        else:
            lis.append(f"<li><strong>{title}</strong><br/><span class='small'>{content}</span></li>")

    html_out = "<div class='fb-section'><div class='fb-head'><span class='fb-step'>📊</span><h3 class='fb-title'>Markt & Wettbewerb (KI-Recherche)</h3></div><ul>" + "".join(lis) + "</ul>"

    if hidden:
        hidden_lis = []
        for it in hidden:
            title = html.escape(it.get("title", ""))
            url = html.escape(it.get("url", ""))
            if url:
                hidden_lis.append(f"<li><a href='{url}'>{title}</a></li>")
            else:
                hidden_lis.append(f"<li>{title}</li>")
        html_out += f"<details class='research-overflow'><summary class='small'>Weitere Insights ({len(hidden)})</summary><ul>" + "".join(hidden_lis) + "</ul></details>"

    html_out += "</div>"
    return html_out

# --- TAVILY INTEGRATION ---

def _policy_domains(kind: str) -> Tuple[List[str], List[str]]:
    """KIS-1266: (include, exclude) aus research_policy — die ENV-Listen
    RESEARCH_INCLUDE_FUNDING/TOOLS und RESEARCH_EXCLUDE waren gepflegt, aber
    nirgends angeschlossen. Fail-open: ohne Policy keine Filter."""
    try:
        from services.research_policy import load_policy_from_env
        policy = load_policy_from_env()
        include = policy.include_funding if kind == "funding" else policy.include_tools
        return list(include or []), list(policy.exclude or [])
    except Exception as exc:
        log.debug("research_policy nicht verfügbar (%s) — ohne Domänenfilter", exc)
        return [], []


def _tavily_funding_search(bundesland: str, branche: str, days: int = 90, report_year: int = None) -> List[Dict[str, str]]:
    """Live-Suche nach Förderprogrammen via Tavily API.

    FIX-506: report_year parameter replaces hardcoded 2025.
    """
    if not os.getenv("TAVILY_API_KEY"):
        return []

    # FIX-506: Use report_year or current year instead of hardcoded 2025
    from datetime import datetime
    year = report_year or datetime.now().year

    # Build targeted query
    query_parts = ["Förderprogramme", "KI", "Digitalisierung", "KMU"]
    if bundesland:
        query_parts.append(bundesland)
    if branche:
        query_parts.append(branche)
    query_parts.append(str(year))

    query = " ".join(query_parts)
    log.info("🔍 Tavily funding search: %s", query)

    try:
        include, exclude = _policy_domains("funding")
        results = provider_tavily.search(query, max_results=8, days=days,
                                         include_domains=include, exclude_domains=exclude)
        log.info("✅ Tavily returned %d funding results (domains: %d include / %d exclude)",
                 len(results), len(include), len(exclude))
        return results
    except Exception as exc:
        log.warning("⚠️ Tavily funding search failed: %s", exc)
        return []

def _tavily_tools_search(branche: str, use_cases: List[str], days: int = 60, report_year: int = None) -> List[Dict[str, str]]:
    """Live-Suche nach KI-Tools via Tavily API.

    FIX-506: report_year parameter replaces hardcoded 2025.
    """
    if not os.getenv("TAVILY_API_KEY"):
        return []

    # FIX-506: Use report_year or current year instead of hardcoded 2025
    from datetime import datetime
    year = report_year or datetime.now().year

    # Build targeted query
    query_parts = ["KI Tools", "AI Software"]
    if branche:
        query_parts.append(branche)
    if use_cases:
        query_parts.extend(use_cases[:2])  # Max 2 use cases
    query_parts.append(str(year))

    query = " ".join(query_parts)
    log.info("🔍 Tavily tools search: %s", query)

    try:
        include, exclude = _policy_domains("tools")
        results = provider_tavily.search(query, max_results=8, days=days,
                                         include_domains=include, exclude_domains=exclude)
        log.info("✅ Tavily returned %d tools results (domains: %d include / %d exclude)",
                 len(results), len(include), len(exclude))
        return results
    except Exception as exc:
        log.warning("⚠️ Tavily tools search failed: %s", exc)
        return []

# --- PERPLEXITY INTEGRATION ---

# =============================================================================
# Sprint N3-01: Short Query Mode & Retry Mechanism
# =============================================================================

def shorten_query(query: str) -> str:
    """
    N3-01: Short Query Mode for finance/beratung branches.
    Removes German/English context suffixes for cleaner API queries.
    """
    # Split on common context separators
    for sep in [" für ", " for ", " in der ", " in the "]:
        if sep in query.lower():
            parts = query.split(sep[0] + sep[1:])  # case-sensitive split
            if parts:
                return parts[0].strip()
    return query


def _perplexity_with_retry(
    search_func,
    *args,
    retry_delays: List[float] = None,
    **kwargs
) -> Tuple[List[Dict[str, str]], bool]:
    """
    N3-01: Execute Perplexity search with 2-stage retry mechanism.

    Args:
        search_func: The search function to call
        *args: Arguments to pass to search_func
        retry_delays: List of delay times between retries
        **kwargs: Keyword arguments to pass to search_func

    Returns:
        Tuple of (results, success_flag)
        - results: List of search results (may be empty)
        - success_flag: True if succeeded without fallback
    """
    if retry_delays is None:
        retry_delays = RETRY_DELAYS

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            results = search_func(*args, **kwargs)
            if results:
                return results, True
            # Empty result but no error - might be valid
            if attempt == 0:
                log.info("[RESEARCH-WARN] Perplexity returned empty, retrying...")
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                delay = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
                log.warning(
                    "[RESEARCH-WARN] Perplexity timeout (attempt %d/%d) – retrying in %.1fs...",
                    attempt + 1, MAX_RETRIES + 1, delay
                )
                time.sleep(delay)
            else:
                log.warning(
                    "[RESEARCH-WARN] Perplexity failed after %d attempts: %s",
                    MAX_RETRIES + 1, exc
                )

    return [], False


def _perplexity_market_insights(
    branche: str,
    hauptleistung: str,
    days: int = 30,
    lang: str = "de"
) -> Tuple[List[Dict[str, str]], bool]:
    """
    Markt- und Wettbewerbs-Insights via Perplexity API.

    N3-01 Enhanced:
    - Short Query Mode for finance/beratung + EN
    - 2-stage retry mechanism
    - Returns (results, success_flag)
    """
    if not os.getenv("PERPLEXITY_API_KEY"):
        return [], False

    # Build research topic
    topic_parts = ["KI Einsatz und Trends"]
    if branche:
        topic_parts.append(f"in der Branche {branche}")
    if hauptleistung:
        topic_parts.append(f"für {hauptleistung}")
    topic_parts.append("Deutschland")

    topic = " ".join(topic_parts)

    # N3-01: Short Query Mode for finance/beratung with EN language
    branche_lower = branche.lower() if branche else ""
    if lang == "en" and any(b in branche_lower for b in SHORT_QUERY_BRANCHES):
        topic = shorten_query(topic)
        log.info("[N3-01] Short Query Mode activated for %s (EN)", branche)

    log.info("🔍 Perplexity market insights: %s", topic)

    def _do_search():
        return provider_perplexity.search(topic, days=days, max_items=6)

    results, success = _perplexity_with_retry(_do_search)
    if results:
        log.info("✅ Perplexity returned %d market insights", len(results))
    return results, success


def _perplexity_competitor_analysis(
    branche: str,
    days: int = 30,
    lang: str = "de"
) -> Tuple[List[Dict[str, str]], bool]:
    """
    Wettbewerber-Analyse via Perplexity API.

    N3-01 Enhanced:
    - Short Query Mode for finance/beratung + EN
    - 2-stage retry mechanism
    - Returns (results, success_flag)

    FIX-511 CHANGE 3:
    - Dynamic year instead of hardcoded 2025
    - Clear endpoint/model logging
    """
    if not os.getenv("PERPLEXITY_API_KEY"):
        return [], False

    # FIX-511 CHANGE 3: Use dynamic year instead of hardcoded 2025
    current_year = datetime.now(timezone.utc).year
    topic = f"Wettbewerber und Marktführer KI-Lösungen {branche} Deutschland {current_year}"

    # N3-01: Short Query Mode for finance/beratung with EN language
    branche_lower = branche.lower() if branche else ""
    if lang == "en" and any(b in branche_lower for b in SHORT_QUERY_BRANCHES):
        topic = shorten_query(topic)
        log.info("[N3-01] Short Query Mode activated for competitor analysis (EN)")

    # FIX-511 CHANGE 3: Clear endpoint/model logging for transparency
    pplx_endpoint = os.getenv("PPLX_ENDPOINT", "https://api.perplexity.ai/chat/completions")
    pplx_model = os.getenv("PERPLEXITY_MODEL") or os.getenv("PPLX_MODEL", "sonar-pro")
    query_preview = topic[:120] + "..." if len(topic) > 120 else topic
    log.info(
        "[PERPLEXITY] endpoint=%s model=%s year=%d query=\"%s\"",
        pplx_endpoint, pplx_model, current_year, query_preview
    )

    log.info("🔍 Perplexity competitor analysis: %s", topic)

    def _do_search():
        return provider_perplexity.search(topic, days=days, max_items=5)

    results, success = _perplexity_with_retry(_do_search)
    if results:
        log.info("✅ Perplexity returned %d competitor insights", len(results))
    return results, success

def run_research(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    HYBRID APPROACH: Combines RSS, Tavily, and Perplexity for optimal results.

    Sprint N4.1: Enhanced with status tracking and robust error handling.
    Each research component has status: success | partial | error | fallback

    Sprint N3-01: Research Reliability Layer
    - 2-stage retry for Perplexity
    - Fallback to tavily_only mode
    - Research mode tagging (hybrid, tavily_only, partial_perplexity)

    Returns:
      {
        "TOOLS_TABLE_HTML": "...",
        "FUNDING_TABLE_HTML": "...",
        "MARKET_INSIGHTS_HTML": "...",
        "NEWS_BOX_HTML": "...",
        "last_updated": "YYYY-MM-DD",
        "research_status": {...},
        "research_sources": {"mode": "hybrid" | "tavily_only" | "partial_perplexity"}
      }
    """
    provider = os.getenv("RESEARCH_PROVIDER", "hybrid").strip().lower()
    # offline-only short-circuit
    offline_only = provider == "offline"

    # Sprint N4.1: Status tracking per component
    research_status = {
        "tools": "pending",
        "funding": "pending",
        "market": "pending",
        "news": "pending",
    }

    # Sprint N3-01: Research mode tracking
    research_sources = {
        "mode": "hybrid",  # Will be updated based on success/failure
        "perplexity_success": False,
        "tavily_success": False,
    }

    # Extract context from answers
    branche = answers.get("BRANCHE_LABEL") or answers.get("branche") or ""
    bundesland = answers.get("BUNDESLAND_LABEL") or answers.get("bundesland") or ""
    hauptleistung = answers.get("hauptleistung") or ""
    use_cases = answers.get("anwendungsfaelle", []) or []
    lang = answers.get("LANG") or answers.get("lang") or "de"

    # FIX-506: Extract report_year from report_date or use current year
    from datetime import datetime
    report_date = answers.get("report_date") or ""
    try:
        # Try to parse year from report_date (formats: "Januar 2026", "2026-01-15", etc.)
        import re
        year_match = re.search(r'20\d{2}', str(report_date))
        report_year = int(year_match.group()) if year_match else datetime.now().year
    except (ValueError, AttributeError):
        report_year = datetime.now().year

    kws = _kw(answers)
    tools: List[Dict[str, str]] = []
    funding: List[Dict[str, str]] = []
    news: List[Dict[str, str]] = []
    market_insights: List[Dict[str, str]] = []

    # N3-01: Track Perplexity success separately
    pplx_market_success = False
    pplx_competitor_success = False

    if not offline_only:
        log.info("🔬 Running HYBRID research (Tavily + Perplexity + RSS)...")

        # --- PARALLEL API CALLS for better performance ---
        with ThreadPoolExecutor(max_workers=5) as executor:
            # N3: Use Any type to accommodate different return types (List and Tuple)
            futures: Dict[str, Future[Any]] = {}

            # 1. Tavily for Tools (FIX-506: pass report_year)
            if os.getenv("TAVILY_API_KEY"):
                futures["tavily_tools"] = executor.submit(
                    _tavily_tools_search, branche, use_cases, 60, report_year
                )

            # 2. Tavily for Funding (FIX-506: pass report_year)
            if os.getenv("TAVILY_API_KEY"):
                futures["tavily_funding"] = executor.submit(
                    _tavily_funding_search, bundesland, branche, 90, report_year
                )

            # 3. Perplexity for Market Insights (N3-01: with retry + lang)
            if os.getenv("PERPLEXITY_API_KEY"):
                futures["pplx_market"] = executor.submit(
                    _perplexity_market_insights, branche, hauptleistung, 30, lang
                )

            # 4. Perplexity for Competitor Analysis (N3-01: with retry + lang)
            if os.getenv("PERPLEXITY_API_KEY"):
                futures["pplx_competitor"] = executor.submit(
                    _perplexity_competitor_analysis, branche, 30, lang
                )

            # Collect results
            for key, future in futures.items():
                try:
                    result = future.result(timeout=45)  # Extended timeout for retries
                    if key == "tavily_tools":
                        # Tavily returns List[Dict]
                        tavily_result: List[Dict[str, str]] = result
                        tools.extend(tavily_result)
                        if tavily_result:
                            research_sources["tavily_success"] = True
                    elif key == "tavily_funding":
                        # Tavily returns List[Dict]
                        tavily_result = result
                        funding.extend(tavily_result)
                        if tavily_result:
                            research_sources["tavily_success"] = True
                    elif key == "pplx_market":
                        # N3-01: Perplexity returns Tuple[List[Dict], bool]
                        pplx_tuple: Tuple[List[Dict[str, str]], bool] = result
                        pplx_results, pplx_market_success = pplx_tuple
                        market_insights.extend(pplx_results)
                    elif key == "pplx_competitor":
                        # N3-01: Perplexity returns Tuple[List[Dict], bool]
                        pplx_tuple = result
                        pplx_results, pplx_competitor_success = pplx_tuple
                        market_insights.extend(pplx_results)
                except Exception as exc:
                    log.warning("⚠️ %s failed: %s", key, exc)

        # N3-01: Determine research mode based on success
        research_sources["perplexity_success"] = pplx_market_success or pplx_competitor_success

        if research_sources["perplexity_success"] and research_sources["tavily_success"]:
            research_sources["mode"] = "hybrid"
        elif research_sources["tavily_success"] and not research_sources["perplexity_success"]:
            research_sources["mode"] = "tavily_only"
            log.warning("[N3-01] Perplexity unavailable, switched to tavily_only mode")
            # Mark market insights as fallback mode
            if not market_insights:
                research_status["market"] = "fallback_mode"
        elif research_sources["perplexity_success"] and not research_sources["tavily_success"]:
            research_sources["mode"] = "partial_perplexity"
        else:
            research_sources["mode"] = "fallback"

        log.info("[N3-01] Research mode: %s", research_sources["mode"])

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

    # Sprint N4.1: Update status based on results
    research_status["tools"] = "success" if len(tools) >= 3 else ("partial" if tools else "fallback")
    research_status["funding"] = "success" if len(funding) >= 3 else ("partial" if funding else "fallback")
    research_status["market"] = "success" if len(market_insights) >= 2 else ("partial" if market_insights else "fallback")
    research_status["news"] = "success" if len(news) >= 2 else ("partial" if news else "fallback")

    # Sprint N4.1: Compact status log
    log.info("[RESEARCH] tools=%s, funding=%s, market=%s, news=%s",
             research_status["tools"], research_status["funding"],
             research_status["market"], research_status["news"])
    log.info("📊 Research complete: %d tools, %d funding, %d news, %d market insights",
             len(tools), len(funding), len(news), len(market_insights))

    # Sprint N4.1: Generate fallback texts for empty results
    tools_html = _tools_table(tools) if tools else _tools_fallback_html(branche)
    funding_html = _funding_table(funding) if funding else _funding_fallback_html(bundesland)
    market_html = _market_insights_box(market_insights) if market_insights else _market_fallback_html()
    news_html = _news_box(news) if news else _news_fallback_html()

    data: Dict[str, Any] = {
        "TOOLS_TABLE_HTML": tools_html,
        "FUNDING_TABLE_HTML": funding_html,
        "MARKET_INSIGHTS_HTML": market_html,
        "NEWS_BOX_HTML": news_html,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "research_status": research_status,  # Sprint N4.1: status per component
        "research_sources": research_sources,  # Sprint N3-01: mode tracking
    }
    return data


# =============================================================================
# Sprint N4.1: Fallback HTML generators for empty research results
# =============================================================================

def _tools_fallback_html(branche: str) -> str:
    """Generates fallback HTML when no tools research is available."""
    branche_text = f" für {branche}" if branche else ""
    return f'''
<div class="research-fallback tools-fallback">
  <p><strong>Empfohlene KI-Werkzeuge{branche_text}:</strong></p>
  <ul>
    <li><a href="https://openai.com/" target="_blank">OpenAI GPT-4o</a> – Leistungsfähiges Sprachmodell für Textgenerierung</li>
    <li><a href="https://claude.ai/" target="_blank">Anthropic Claude</a> – Zuverlässiger KI-Assistent für komplexe Aufgaben</li>
    <li><a href="https://huggingface.co/models" target="_blank">Hugging Face</a> – Open-Source-Modelle und ML-Plattform</li>
  </ul>
  <p class="small muted">Tipp: Prüfen Sie aktuelle Anbietervergleiche für branchenspezifische Tools.</p>
</div>
'''.strip()


def _funding_fallback_html(bundesland: str) -> str:
    """Generates fallback HTML when no funding research is available."""
    region_text = f" in {bundesland}" if bundesland else ""
    return f'''
<div class="research-fallback funding-fallback">
  <p><strong>Förderprogramme für KI und Digitalisierung{region_text}:</strong></p>
  <p>Aktuell wurden keine spezifischen Förderprogramme für Ihr Profil gefunden.
     Prüfen Sie regelmäßig folgende Quellen:</p>
  <ul>
    <li><a href="https://www.foerderdatenbank.de/" target="_blank">Förderdatenbank des Bundes</a></li>
    <li><a href="https://www.bmwk.de/" target="_blank">Bundesministerium für Wirtschaft</a></li>
    <li><a href="https://digital-strategy.ec.europa.eu/en/activities/digital-programme" target="_blank">EU Digital Programme</a></li>
  </ul>
  <p class="small muted">Hinweis: Förderlandschaft ändert sich regelmäßig – quartalsweise prüfen empfohlen.</p>
</div>
'''.strip()


def _market_fallback_html() -> str:
    """
    Generates fallback HTML when no market insights are available.

    SPRINT G14-B: Expanded to 3 substantive paragraphs for better content quality.
    FIX-511: Dynamic year instead of hardcoded 2025.
    """
    # FIX-511: Use dynamic year
    current_year = datetime.now(timezone.utc).year
    return f'''
<div class="research-fallback market-fallback">
  <p><strong>Markt-Insights:</strong></p>
  <p>Aktuell keine spezifischen Markt-Insights verfügbar. Der KI-Markt entwickelt sich
     dynamisch – relevante Trends und Wettbewerbsinformationen sollten regelmäßig
     über Branchenpublikationen und Fachmedien verfolgt werden.</p>
  <p><strong>Aktuelle Markttrends {current_year}:</strong> Generative KI wird zunehmend in
     Geschäftsprozessen eingesetzt. Besonders gefragt sind Lösungen für
     Dokumentenverarbeitung, Kundenkommunikation und Prozessautomatisierung.
     KMU profitieren von sinkenden Einstiegskosten und benutzerfreundlichen
     SaaS-Angeboten der führenden Anbieter.</p>
  <p><strong>Wettbewerbslandschaft:</strong> Neben den großen Anbietern (OpenAI,
     Microsoft, Google, Anthropic) etablieren sich spezialisierte europäische
     Lösungen mit Fokus auf DSGVO-Konformität und lokaler Datenhaltung.
     Branchenspezifische Anbieter gewinnen an Bedeutung, da sie maßgeschneiderte
     Lösungen für regulierte Branchen wie Gesundheit, Finanzen und Recht bieten.</p>
  <p class="small muted">Empfehlung: Newsletter von Heise, t3n oder Branchenpublikationen abonnieren.</p>
</div>
'''.strip()


def _news_fallback_html() -> str:
    """Generates fallback HTML when no news are available."""
    return '''
<div class="research-fallback news-fallback">
  <p><strong>Aktuelle KI-News:</strong></p>
  <p>Aktuell keine relevanten News-Artikel gefunden. Für aktuelle Entwicklungen
     empfehlen wir die regelmäßige Lektüre von:</p>
  <ul>
    <li>Heise Online – KI & Machine Learning</li>
    <li>t3n – Digitalisierung & Tech</li>
    <li>EU Digital Strategy News</li>
  </ul>
</div>
'''.strip()
