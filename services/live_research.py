# -*- coding: utf-8 -*-
"""
Live-Recherche-Modul für den KI-Strategiebericht (Report 3).

Führt parallele Queries gegen Perplexity und Tavily APIs aus.
Verwendet die bestehenden Provider-Clients aus services/provider_perplexity.py
und services/provider_tavily.py.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List

from services import provider_perplexity
from services import provider_tavily

logger = logging.getLogger(__name__)

# Total timeout for all research queries combined
RESEARCH_TOTAL_TIMEOUT = 60  # seconds
# Per-query timeout
RESEARCH_QUERY_TIMEOUT = 30  # seconds


# =============================================================================
# QUERY TEMPLATES
# (from PROMPT-SPECS-Report3-v1.md, "RECHERCHE-PHASE")
# =============================================================================

RESEARCH_QUERIES = {
    "markt_trends": {
        "engine": "perplexity",
        "template": "{branche} KI Einsatz Deutschland Trends 2026",
        "fallback": "KI Mittelstand Deutschland Trends 2026",
        "feeds_into": "S2",
    },
    "wettbewerb_benchmark": {
        "engine": "perplexity",
        "template": "{branche} KI Automatisierung Mittelstand Benchmark Studie",
        "fallback": "KI Adoption Rate Mittelstand Deutschland Studie",
        "feeds_into": "S2",
    },
    "branche_stats_en": {
        "engine": "tavily",
        "template": "{branche_en} AI adoption rate SME Europe statistics 2025 2026",
        "fallback": "SME AI adoption Europe statistics 2025",
        "feeds_into": "S2",
    },
    "tool_vergleich_1": {
        "engine": "tavily",
        "template": "{handlungsfeld_1} KI Tool Vergleich DSGVO {branche} KMU",
        "fallback": "{handlungsfeld_1} KI Tool DSGVO konform Deutschland",
        "feeds_into": "S4",
    },
    "tool_vergleich_2": {
        "engine": "tavily",
        "template": "{handlungsfeld_2} AI SaaS pricing Europe SME GDPR",
        "fallback": "{handlungsfeld_2} AI tool comparison business",
        "feeds_into": "S4",
    },
    "tool_integration": {
        "engine": "tavily",
        "template": "{bestehende_software} KI Integration Plugin Erweiterung",
        "fallback": "Microsoft 365 KI Integration Mittelstand",
        "feeds_into": "S4",
    },
    "foerdermittel": {
        "engine": "perplexity",
        "template": "KI Förderung Mittelstand {bundesland} Landesförderung regionale Förderprogramme {branche} 2026 aktuell",
        "fallback": "KI Förderung KMU Deutschland regionale Landesförderung 2026 Übersicht",
        "feeds_into": "S7",
    },
    "foerdermittel_eu": {
        "engine": "tavily",
        "template": "EU digital funding SME AI 2026 Germany",
        "fallback": "Digital Europe Programme SME AI funding",
        "feeds_into": "S7",
    },
}


# =============================================================================
# BRANCHE MAPPING (German → English)
# =============================================================================

BRANCHE_MAP = {
    "Handwerk": "Skilled trades",
    "Einzelhandel": "Retail",
    "Produktion/Fertigung": "Manufacturing",
    "IT/Software": "IT Software",
    "Beratung/Dienstleistung": "Consulting services",
    "Gesundheitswesen": "Healthcare",
    "Finanzen/Versicherung": "Financial services insurance",
    "Gastronomie/Hotellerie": "Hospitality",
    "Bildung/Forschung": "Education research",
    "Immobilien": "Real estate",
    "Logistik/Transport": "Logistics transportation",
    "Marketing/Medien": "Marketing media",
}


# =============================================================================
# MAIN RESEARCH FUNCTION
# =============================================================================

async def execute_research(
    briefing_data: Dict[str, Any],
    strategy_questions: Dict[str, Any],
    handlungsfelder: List[str],
) -> Dict[str, Any]:
    """
    Führt alle Recherche-Queries parallel aus.

    Args:
        briefing_data: Briefing answers dict
        strategy_questions: Strategy questions dict (S1-S10)
        handlungsfelder: List of action fields derived from Report 1+2

    Returns:
        Dict with query keys and their results.
        Each entry: {"key": str, "query": str, "results": str, "source": str, "success": bool}
    """
    start_time = time.time()

    # 1. Build template variables
    branche = briefing_data.get("branche", "")
    variables = {
        "branche": branche,
        "branche_en": BRANCHE_MAP.get(branche, "SME"),
        "bundesland": briefing_data.get("bundesland", "Deutschland"),
        "handlungsfeld_1": handlungsfelder[0] if len(handlungsfelder) > 0 else "KI Automatisierung",
        "handlungsfeld_2": handlungsfelder[1] if len(handlungsfelder) > 1 else "Digitalisierung",
        "bestehende_software": strategy_questions.get("s5_software") or "Microsoft 365",
    }

    # 2. Build queries from templates
    queries = {}
    for key, config in RESEARCH_QUERIES.items():
        try:
            query_text = config["template"].format(**variables)
        except KeyError:
            query_text = config["fallback"].format(**variables)
        try:
            fallback_text = config.get("fallback", "").format(**variables)
        except KeyError:
            fallback_text = config.get("fallback", "")
        queries[key] = {
            "text": query_text,
            "engine": config["engine"],
            "fallback": fallback_text,
        }

    # 3. Execute all queries in parallel
    tasks = []
    for key, query in queries.items():
        if query["engine"] == "perplexity":
            tasks.append(_search_perplexity(key, query["text"], query["fallback"]))
        elif query["engine"] == "tavily":
            tasks.append(_search_tavily(key, query["text"], query["fallback"]))

    try:
        results_list = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=RESEARCH_TOTAL_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("[Strategy-Research] Total timeout (%ds) reached", RESEARCH_TOTAL_TIMEOUT)
        results_list = []

    # 4. Merge results
    research_context: Dict[str, Any] = {}
    for result in results_list:
        if isinstance(result, Exception):
            logger.error("[Strategy-Research] Query failed: %s", result)
            continue
        if isinstance(result, dict) and "key" in result:
            research_context[result["key"]] = result

    duration = time.time() - start_time
    logger.info(
        "[Strategy-Research] Complete: %d/%d queries successful in %.1fs",
        len(research_context),
        len(RESEARCH_QUERIES),
        duration,
    )

    return research_context


# =============================================================================
# PROVIDER WRAPPERS (async → sync bridge)
# =============================================================================

async def _search_perplexity(key: str, query: str, fallback: str) -> Dict[str, Any]:
    """
    Perplexity API call using the existing provider_perplexity.search().
    Falls back to fallback query on failure.
    """
    start = time.time()
    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(provider_perplexity.search, query, 30, 6),
            timeout=RESEARCH_QUERY_TIMEOUT,
        )
        if results:
            content = _format_results(results)
            logger.info("[Strategy-Research] perplexity/%s: %d results in %.1fs", key, len(results), time.time() - start)
            return {"key": key, "query": query, "results": content, "source": "perplexity", "success": True}
    except Exception as exc:
        logger.warning("[Strategy-Research] perplexity/%s primary failed: %s", key, exc)

    # Fallback query
    if fallback:
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(provider_perplexity.search, fallback, 30, 6),
                timeout=RESEARCH_QUERY_TIMEOUT,
            )
            if results:
                content = _format_results(results)
                logger.info("[Strategy-Research] perplexity/%s fallback: %d results in %.1fs", key, len(results), time.time() - start)
                return {"key": key, "query": fallback, "results": content, "source": "perplexity", "success": True}
        except Exception as exc2:
            logger.warning("[Strategy-Research] perplexity/%s fallback failed: %s", key, exc2)

    logger.warning("[Strategy-Research] perplexity/%s: no results", key)
    return {"key": key, "query": query, "results": "", "source": "perplexity", "success": False}


async def _search_tavily(key: str, query: str, fallback: str) -> Dict[str, Any]:
    """
    Tavily API call using the existing provider_tavily.search().
    Falls back to fallback query on failure.
    """
    start = time.time()
    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(provider_tavily.search, query, 6, 30),
            timeout=RESEARCH_QUERY_TIMEOUT,
        )
        if results:
            content = _format_results(results)
            logger.info("[Strategy-Research] tavily/%s: %d results in %.1fs", key, len(results), time.time() - start)
            return {"key": key, "query": query, "results": content, "source": "tavily", "success": True}
    except Exception as exc:
        logger.warning("[Strategy-Research] tavily/%s primary failed: %s", key, exc)

    # Fallback query
    if fallback:
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(provider_tavily.search, fallback, 6, 30),
                timeout=RESEARCH_QUERY_TIMEOUT,
            )
            if results:
                content = _format_results(results)
                logger.info("[Strategy-Research] tavily/%s fallback: %d results in %.1fs", key, len(results), time.time() - start)
                return {"key": key, "query": fallback, "results": content, "source": "tavily", "success": True}
        except Exception as exc2:
            logger.warning("[Strategy-Research] tavily/%s fallback failed: %s", key, exc2)

    logger.warning("[Strategy-Research] tavily/%s: no results", key)
    return {"key": key, "query": query, "results": "", "source": "tavily", "success": False}


def _format_results(results: List[Dict]) -> str:
    """Format search results into a text block for LLM consumption."""
    parts = []
    for r in results[:6]:
        title = r.get("title", "")
        content = r.get("content", "") or r.get("summary", "")
        url = r.get("url", "")
        if title or content:
            parts.append(f"- {title}: {content[:300]}" + (f" [Quelle: {url}]" if url else ""))
    return "\n".join(parts) if parts else ""
