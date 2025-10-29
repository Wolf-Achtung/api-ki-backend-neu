# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import date
from typing import Dict, Any, Optional
import os

from services.metrics import derive_metrics
from services.template_engine import render_template
from services.sanitize import ensure_utf8, normalize_model_html, safe_text

TEMPLATE_FILE = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")

def _read_file_utf8(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _normalize_snippet(snippet: Optional[str]) -> str:
    return normalize_model_html(snippet or "")

def build_context(briefing: Dict[str, Any], model_snippets: Dict[str, str]) -> Dict[str, Any]:
    metrics = derive_metrics(briefing or {})
    ctx: Dict[str, Any] = {
        "report_date": date.today().strftime("%d.%m.%Y"),
        "report_year": date.today().strftime("%Y"),
        "unternehmen_name": safe_text(briefing.get("unternehmen_name") or briefing.get("hauptleistung") or "—"),
        "branche": safe_text(briefing.get("branche") or "—"),
        "bundesland": safe_text(briefing.get("bundesland") or "—"),
        "jahresumsatz": safe_text(briefing.get("jahresumsatz") or "—"),
        "unternehmensgroesse": safe_text(briefing.get("unternehmensgroesse") or "—"),
        "ki_knowhow": safe_text(briefing.get("ki_knowhow") or "—"),
        "score_governance": briefing.get("score_governance", 0),
        "score_sicherheit": briefing.get("score_sicherheit", 0),
        "score_nutzen": briefing.get("score_nutzen", 0),
        "score_befaehigung": briefing.get("score_befaehigung", 0),
        "score_gesamt": briefing.get("score_gesamt", 0),
        "benchmark_avg": briefing.get("benchmark_avg", "—"),
        "benchmark_top": briefing.get("benchmark_top", "—"),
        "eu_ai_act_risk": "gering (assistierend, menschliche Kontrolle)",
        # Logo defaults for root/templates/
        "logo_primary": briefing.get("logo_primary", "ki-sicherheit-logo.webp"),
        "logo_tuv": briefing.get("logo_tuv", "tuev-logo-transparent.webp"),
        "logo_dsgvo": briefing.get("logo_dsgvo", "dsgvo.svg"),
        "logo_eu_ai": briefing.get("logo_eu_ai", "eu-ai.svg"),
        "logo_ready": briefing.get("logo_ready", "ki-ready-2025.webp"),
        **metrics,
    }
    html_keys = [
        "EXECUTIVE_SUMMARY_HTML","QUICK_WINS_HTML_LEFT","QUICK_WINS_HTML_RIGHT",
        "PILOT_PLAN_HTML","ROI_HTML","COSTS_OVERVIEW_HTML","RISKS_HTML",
        "GAMECHANGER_HTML","FOERDERPROGRAMME_HTML","QUELLEN_HTML","TOOLS_HTML",
    ]
    for k in html_keys:
        ctx[k] = _normalize_snippet(model_snippets.get(k, ""))
    return ctx

def render_report_html(briefing: Dict[str, Any], model_snippets: Dict[str, str]) -> str:
    template = _read_file_utf8(TEMPLATE_FILE)
    ctx = build_context(briefing, model_snippets)
    html = render_template(template, ctx, default="")
    return ensure_utf8(html)
