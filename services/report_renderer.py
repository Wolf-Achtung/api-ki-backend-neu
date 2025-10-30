# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import os
from typing import Dict, Any, Optional

from .report_pipeline import render_report_html
from . import research_fetcher, research_html, benchmarks
from .sanitize import ensure_utf8

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
    """
    Erstellt vollständiges Report-HTML aus Briefing und generierten Sections.
    
    Args:
        briefing: Briefing-Dict mit Antworten
        generated_sections: Dict mit HTML-Sections (z.B. {"EXEC_SUMMARY_HTML": "..."})
        use_fetchers: Ob externe Datenquellen (Tavily etc.) verwendet werden sollen
    
    Returns:
        String mit vollständigem HTML
    """
    snippets = dict(generated_sections or {})
    snippets = _enrich_snippets_with_fetchers(briefing, snippets, use_fetchers=use_fetchers)
    snippets = _enrich_with_benchmarks(briefing, snippets)
    html = render_report_html(briefing, snippets)
    return ensure_utf8(html)


def render(briefing: Any, run_id: str = None, **kwargs) -> Dict[str, Any]:
    """
    High-Level Render-Funktion für gpt_analyze.py
    
    Diese Funktion wird von gpt_analyze.py aufgerufen und gibt ein Dict zurück.
    
    Args:
        briefing: Briefing-Objekt oder Dict
        run_id: Optional Run-ID für Logging
        **kwargs: Zusätzliche Parameter (generated_sections, use_fetchers, etc.)
    
    Returns:
        Dict mit keys:
        - "html": Vollständiges Report-HTML
        - "meta": Metadata-Dict
    """
    # Konvertiere Briefing-Objekt zu Dict falls nötig
    if hasattr(briefing, '__dict__'):
        briefing_dict = {
            "id": getattr(briefing, "id", None),
            "user_id": getattr(briefing, "user_id", None),
            "lang": getattr(briefing, "lang", "de"),
            "answers": getattr(briefing, "answers", {}),
            "created_at": getattr(briefing, "created_at", None),
        }
        # Merge answers in top-level für einfacheren Zugriff
        briefing_dict.update(briefing_dict.get("answers", {}))
    else:
        briefing_dict = briefing
    
    # Generiere HTML
    generated_sections = kwargs.get("generated_sections")
    use_fetchers = kwargs.get("use_fetchers", True)
    
    html = build_full_report_html(
        briefing_dict,
        generated_sections=generated_sections,
        use_fetchers=use_fetchers
    )
    
    # Erstelle Metadata
    meta = {
        "briefing_id": briefing_dict.get("id"),
        "run_id": run_id,
        "sections_count": len(generated_sections or {}),
        "html_length": len(html),
        "fetchers_used": use_fetchers,
    }
    
    return {
        "html": html,
        "meta": meta,
    }
