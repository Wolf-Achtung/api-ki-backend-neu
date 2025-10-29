# -*- coding: utf-8 -*-
"""
High-level pipeline to assemble the report HTML with:
- UTF-8 fixes
- HTML snippet normalization (no code fences)
- dynamic metrics derivation (default heuristics)
- single template selection
"""
from __future__ import annotations
import json
import logging
import os
from datetime import date
from typing import Dict, Any, Optional

from .metrics import derive_metrics
from .template_engine import render_template
from ..utils.sanitize import ensure_utf8, normalize_model_html, safe_text

LOGGER = logging.getLogger(__name__)

TEMPLATE_FILE = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")

def _read_file_utf8(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _normalize_snippet(snippet: Optional[str]) -> str:
    return normalize_model_html(snippet or "")

def build_context(briefing: Dict[str, Any], model_snippets: Dict[str, str]) -> Dict[str, Any]:
    metrics = derive_metrics(briefing or {})
    # Profile
    ctx: Dict[str, Any] = {
        "report_date": date.today().strftime("%d.%m.%Y"),
        "report_year": date.today().strftime("%Y"),
        "unternehmen_name": safe_text(briefing.get("unternehmen_name") or briefing.get("hauptleistung") or "—"),
        "branche": safe_text(briefing.get("branche") or "—"),
        "bundesland": safe_text(briefing.get("bundesland") or "—"),
        "jahresumsatz": safe_text(briefing.get("jahresumsatz") or "—"),
        "unternehmensgroesse": safe_text(briefing.get("unternehmensgroesse") or "—"),
        "ki_knowhow": safe_text(briefing.get("ki_knowhow") or "—"),
        # Scores (fallbacks to 0 to avoid empty charts)
        "score_governance": briefing.get("score_governance", 0),
        "score_sicherheit": briefing.get("score_sicherheit", 0),
        "score_nutzen": briefing.get("score_nutzen", 0),
        "score_befaehigung": briefing.get("score_befaehigung", 0),
        "score_gesamt": briefing.get("score_gesamt", 0),
        # Benchmarks (optional)
        "benchmark_avg": briefing.get("benchmark_avg", "—"),
        "benchmark_top": briefing.get("benchmark_top", "—"),
        # EU AI Act
        "eu_ai_act_risk": "gering (assistierend, menschliche Kontrolle)",
        # Logos (relative names expected to exist beside the template)
        "logo_primary": briefing.get("logo_primary", "logo-ki-sicherheit.png"),
        "logo_tuv": briefing.get("logo_tuv", "logo-tuv.svg"),
        "logo_dsgvo": briefing.get("logo_dsgvo", "logo-dsgvo.svg"),
        "logo_shield": briefing.get("logo_shield", "logo-shield.svg"),
        # Metrics (for template footnotes)
        **metrics,
    }
    # Snippets (HTML; normalized)
    html_keys = [
        "EXECUTIVE_SUMMARY_HTML",
        "QUICK_WINS_HTML_LEFT",
        "QUICK_WINS_HTML_RIGHT",
        "PILOT_PLAN_HTML",
        "ROI_HTML",
        "COSTS_OVERVIEW_HTML",
        "RISKS_HTML",
        "GAMECHANGER_HTML",
        "FOERDERPROGRAMME_HTML",
        "QUELLEN_HTML",
    ]
    for k in html_keys:
        ctx[k] = _normalize_snippet(model_snippets.get(k, ""))

    # Derived note for consistency
    ctx["monatsersparnis_stunden"] = metrics["monatsersparnis_stunden"]
    ctx["monatsersparnis_eur"] = metrics["monatsersparnis_eur"]
    ctx["jahresersparnis_stunden"] = metrics["jahresersparnis_stunden"]
    ctx["jahresersparnis_eur"] = metrics["jahresersparnis_eur"]
    return ctx

def render_report_html(briefing: Dict[str, Any], model_snippets: Dict[str, str]) -> str:
    template = _read_file_utf8(TEMPLATE_FILE)
    ctx = build_context(briefing, model_snippets)
    html = render_template(template, ctx, default="")
    return ensure_utf8(html)
