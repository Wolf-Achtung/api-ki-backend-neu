# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Report Renderer (patched for Gold‑Standard+)
==========================================

Dieses Modul übernimmt die Zusammenführung aller generierten Section‑Fragmente
und übernimmt die finale HTML‑Erstellung. In der Gold‑Standard+ Version
verwenden wir den Content‑Normalizer aus services.content_normalizer, um
fehlerhafte Scores zu korrigieren, die KPI‑Dashboards zu generieren und
weitere Kontextvariablen (z. B. monatsersparnis_…) zu berechnen. Die
Normalisierung wird durchgeführt, bevor externe Fetcher (Tools/Förderungen)
aufgerufen werden, sodass alle Template‑Variablen verfügbar sind.
"""

import logging
import os
from typing import Dict, Any, Optional

from .report_pipeline import render_report_html
from . import research_fetcher, research_html, benchmarks
from .sanitize import ensure_utf8
from .content_normalizer import normalize_and_enrich_sections

# Set up a module‑level logger
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
    """Reichert Snippets über externe Fetcher an.

    Wenn use_fetchers=True, werden fehlende Förderprogramme bzw. Tools
    mittels research_fetcher gesucht und als HTML eingebettet. Bereits
    vorhandene Snippets werden nicht überschrieben.
    """
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
    """Fügt Benchmark‑Informationen und Transparenztext zum Snippet‑Dict hinzu."""
    branch = str(briefing.get("branche") or "")
    b = benchmarks.lookup(branch)
    snippets.setdefault("BENCHMARK_HTML", benchmarks.build_html(branch))
    snippets.setdefault("benchmark_avg", b.get("avg", ""))
    snippets.setdefault("benchmark_top", b.get("top25", ""))
    snippets.setdefault("transparency_text", TRANSPARENCY_TEXT)
    return snippets

def build_full_report_html(
    briefing: Dict[str, Any],
    generated_sections: Optional[Dict[str, str]] = None,
    use_fetchers: bool = True,
    scores: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """Erstellt vollständiges Report‑HTML aus Briefing und generierten Sections.

    In der Gold‑Standard+ Version werden die generierten Sections via
    normalize_and_enrich_sections angereichert, sodass Scores, KPIs und
    Quick‑Win‑Berechnungen konsistent sind. Anschließend werden Fetcher
    (Tools/Förderprogramme) und Benchmarks ergänzt.

    Args:
        briefing: Briefing‑Dict mit Antworten
        generated_sections: Dict mit HTML‑Sections (z. B. {"EXECUTIVE_SUMMARY_HTML": "…"})
        use_fetchers: Ob externe Datenquellen (Tavily etc.) verwendet werden sollen
        scores: Score‑Dict (für normalize_and_enrich_sections)
        meta: Metadata‑Dict (für normalize_and_enrich_sections)
    Returns:
        Vollständiges HTML als String
    """
    # Starte mit einer Kopie der generierten Sections
    snippets: Dict[str, Any] = dict(generated_sections or {})
    # Wende den Content‑Normalizer an, um alle Template‑Variablen zu berechnen
    try:
        normalized = normalize_and_enrich_sections(sections=snippets, answers=briefing, scores=scores or {}, meta=meta or {})
        snippets.update(normalized)
    except Exception as exc:
        LOGGER.warning("Normalization failed: %s", exc)
    # Ergänze Fetcher‑Inhalte (Tools/Förderungen) nur, wenn die Sections leer sind
    snippets = _enrich_snippets_with_fetchers(briefing, snippets, use_fetchers=use_fetchers)
    # Ergänze Benchmarks und Transparenz
    snippets = _enrich_with_benchmarks(briefing, snippets)
    # Erstelle finalen HTML‑String per Template
    html = render_report_html(briefing, snippets)
    return ensure_utf8(html)

def render(briefing: Any, run_id: str = None, **kwargs) -> Dict[str, Any]:
    """High‑Level Render‑Funktion für gpt_analyze.py.

    Diese Funktion wird von gpt_analyze.py aufgerufen und gibt ein Dict mit
    fertigem HTML und Meta‑Informationen zurück. Sie übernimmt die
    Normalisierung der Sections sowie das Einbinden von Research, Benchmarks
    und KPI‑Dashboards.

    Args:
        briefing: Briefing‑Objekt oder Dict
        run_id: Optionale Run‑ID für Logging
        **kwargs: Zusätzliche Parameter (generated_sections, use_fetchers, scores, meta)
    Returns:
        Dict mit keys:
            - "html": Vollständiges Report‑HTML
            - "meta": Metadata‑Dict
    """
    # Konvertiere Briefing‑Objekt zu Dict, falls nötig
    if hasattr(briefing, '__dict__'):
        briefing_dict: Dict[str, Any] = {
            "id": getattr(briefing, "id", None),
            "user_id": getattr(briefing, "user_id", None),
            "lang": getattr(briefing, "lang", "de"),
            "answers": getattr(briefing, "answers", {}),
            "created_at": getattr(briefing, "created_at", None),
        }
        # Merge answers in top‑level für einfacheren Zugriff
        briefing_dict.update(briefing_dict.get("answers", {}))
    else:
        briefing_dict = briefing  # type: ignore
    # Parameter aus kwargs
    generated_sections: Optional[Dict[str, str]] = kwargs.get("generated_sections")
    use_fetchers: bool = kwargs.get("use_fetchers", True)
    scores: Optional[Dict[str, Any]] = kwargs.get("scores")
    meta: Optional[Dict[str, Any]] = kwargs.get("meta")
    # Erstelle HTML
    html = build_full_report_html(
        briefing_dict,
        generated_sections=generated_sections,
        use_fetchers=use_fetchers,
        scores=scores,
        meta=meta,
    )
    # Erstelle Metadata
    meta_out: Dict[str, Any] = {
        "briefing_id": briefing_dict.get("id"),
        "run_id": run_id,
        "sections_count": len(generated_sections or {}),
        "html_length": len(html),
        "fetchers_used": use_fetchers,
    }
    return {
        "html": html,
        "meta": meta_out,
    }