# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import os
from typing import Dict, Any, Optional

from .report_pipeline import render_report_html
from . import research_fetcher, research_html, benchmarks
from ..utils.sanitize import ensure_utf8

LOGGER = logging.getLogger(__name__)

DEFAULT_FUNDING_DAYS = int(os.getenv("FUNDING_DAYS", "30"))
DEFAULT_TOOLS_DAYS = int(os.getenv("TOOLS_DAYS", "30"))
TRANSPARENCY_TEXT = os.getenv(
    "TRANSPARENCY_TEXT",
    "Dieser Report wurde teilweise mit KI‑Unterstützung aus Europa unter strikter Einhaltung von Eu AI Acts sowie DSGVO erstellt."
)

def _enrich_snippets_with_fetchers(
    briefing: Dict[str, Any],
    snippets: Dict[str, str],
    use_fetchers: bool = True
) -> Dict[str, str]:
    if not use_fetchers:
        return snippets

    # Funding (Bundesland)
    if not snippets.get("FOERDERPROGRAMME_HTML"):
        state = str(briefing.get("bundesland") or "Deutschland")
        try:
            items = research_fetcher.fetch_funding(state=state, days=DEFAULT_FUNDING_DAYS)
            snippets["FOERDERPROGRAMME_HTML"] = research_html.items_to_html(items, title=f"Förderprogramme – {state}")
        except Exception as exc:
            LOGGER.warning("Funding fetch failed: %s", exc)

    # Tools (Branche + Unternehmensgröße)
    if not snippets.get("TOOLS_HTML"):
        branch = str(briefing.get("branche") or "KMU")
        size = str(briefing.get("unternehmensgroesse") or "klein")
        try:
            items = research_fetcher.fetch_tools(branch=branch, company_size=size, days=DEFAULT_TOOLS_DAYS, include_open_source=True)
            snippets["TOOLS_HTML"] = research_html.items_to_html(items, title=f"Empfohlene Tools – {branch}/{size}")
        except Exception as exc:
            LOGGER.warning("Tools fetch failed: %s", exc)

    return snippets

def _enrich_with_benchmarks(briefing: Dict[str, Any], snippets: Dict[str, str]) -> Dict[str, str]:
    branch = str(briefing.get("branche") or "")
    b = benchmarks.lookup(branch)
    snippets.setdefault("BENCHMARK_HTML", benchmarks.build_html(branch))
    # Push numeric values for template (used in small headline line if present)
    snippets.setdefault("benchmark_avg", b.get("avg", ""))
    snippets.setdefault("benchmark_top", b.get("top25", ""))
    # Transparency text propagated
    snippets.setdefault("transparency_text", TRANSPARENCY_TEXT)
    return snippets

def build_full_report_html(
    briefing: Dict[str, Any],
    generated_sections: Optional[Dict[str, str]] = None,
    use_fetchers: bool = True
) -> str:
    snippets = dict(generated_sections or {})
    snippets = _enrich_snippets_with_fetchers(briefing, snippets, use_fetchers=use_fetchers)
    snippets = _enrich_with_benchmarks(briefing, snippets)
    html = render_report_html(briefing, snippets)
    return ensure_utf8(html)
