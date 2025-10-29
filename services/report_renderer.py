# -*- coding: utf-8 -*-
"""
Report Renderer – orchestrates snippet enrichment (funding/tools) and renders the
single-column HTML using the new pipeline and template.

Usage:
    html = build_full_report_html(briefing, generated_sections)
    # send `html` to your PDF client
"""
from __future__ import annotations
import logging
import os
from typing import Dict, Any, Optional

from .report_pipeline import render_report_html
from . import research_fetcher, research_html
from ..utils.sanitize import ensure_utf8

LOGGER = logging.getLogger(__name__)

DEFAULT_FUNDING_DAYS = int(os.getenv("FUNDING_DAYS", "30"))
DEFAULT_TOOLS_DAYS = int(os.getenv("TOOLS_DAYS", "30"))

def _enrich_snippets_with_fetchers(
    briefing: Dict[str, Any],
    snippets: Dict[str, str],
    use_fetchers: bool = True
) -> Dict[str, str]:
    """Fill FOERDERPROGRAMME_HTML and TOOLS_HTML if missing/empty using web fetchers."""
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

def build_full_report_html(
    briefing: Dict[str, Any],
    generated_sections: Optional[Dict[str, str]] = None,
    use_fetchers: bool = True
) -> str:
    """
    Render the final HTML. `generated_sections` may contain model-generated HTML snippets.
    Missing snippets for funding/tools are auto-filled by the web fetchers (cache + recency).

    Required keys in `generated_sections` (may be empty strings):
        EXECUTIVE_SUMMARY_HTML, QUICK_WINS_HTML_LEFT, QUICK_WINS_HTML_RIGHT,
        PILOT_PLAN_HTML, ROI_HTML, COSTS_OVERVIEW_HTML, RISKS_HTML, GAMECHANGER_HTML,
        FOERDERPROGRAMME_HTML (optional), QUELLEN_HTML (optional), TOOLS_HTML (optional)
    """
    snippets = dict(generated_sections or {})
    snippets = _enrich_snippets_with_fetchers(briefing, snippets, use_fetchers=use_fetchers)
    html = render_report_html(briefing, snippets)
    return ensure_utf8(html)
