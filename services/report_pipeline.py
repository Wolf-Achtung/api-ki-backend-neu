# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import datetime as dt
import re
from typing import Dict, Any

from ..utils.sanitize import ensure_utf8

# ---- Defaults (safe heuristics for Solo/KMU) ----
DEFAULTS = {
    "stundensatz_eur": int(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60")),
    "qw1_monat_stunden": int(os.getenv("DEFAULT_QW1_H", "10")),
    "qw2_monat_stunden": int(os.getenv("DEFAULT_QW2_H", "8")),
}

CODE_FENCE_RE = re.compile(r"```+[a-zA-Z]*\s*|\u200b", flags=re.MULTILINE)

def _strip_code_fences(html: str) -> str:
    return CODE_FENCE_RE.sub("", html or "").strip()

def _dash(value: Any) -> str:
    return "—" if value in (None, "", [], {}) else str(value)

def derive_metrics(briefing: Dict[str, Any]) -> Dict[str, Any]:
    """Derive consistent metrics from minimal inputs; fall back to sensible defaults."""
    stunden = DEFAULTS["qw1_monat_stunden"] + DEFAULTS["qw2_monat_stunden"]
    stundensatz = DEFAULTS["stundensatz_eur"]

    # Heuristics by size
    size = (briefing.get("unternehmensgroesse") or "").lower()
    if size in {"solo", "einzel", "freiberufler"}:
        stundensatz = int(os.getenv("DEFAULT_STUNDENSATZ_SOLO", stundensatz))
    elif size in {"kmu", "mittel"}:
        stundensatz = int(os.getenv("DEFAULT_STUNDENSATZ_KMU", stundensatz))

    monats_eur = stunden * stundensatz
    jahres_stunden = stunden * 12
    jahres_eur = monats_eur * 12

    return {
        "stundensatz_eur": stundensatz,
        "monatsersparnis_stunden": stunden,
        "monatsersparnis_eur": monats_eur,
        "jahresersparnis_stunden": jahres_stunden,
        "jahresersparnis_eur": jahres_eur,
    }

def build_context(briefing: Dict[str, Any], snippets: Dict[str, str]) -> Dict[str, Any]:
    metrics = derive_metrics(briefing or {})
    today = dt.date.today()
    context = {
        "unternehmen_name": _dash(briefing.get("unternehmen_name")),
        "branche": _dash(briefing.get("branche")),
        "bundesland": _dash(briefing.get("bundesland")),
        "jahresumsatz": _dash(briefing.get("jahresumsatz")),
        "unternehmensgroesse": _dash(briefing.get("unternehmensgroesse")),
        "ki_knowhow": _dash(briefing.get("ki_knowhow")),
        "score_governance": briefing.get("score_governance", 0),
        "score_sicherheit": briefing.get("score_sicherheit", 0),
        "score_nutzen": briefing.get("score_nutzen", 0),
        "score_befaehigung": briefing.get("score_befaehigung", 0),
        "score_gesamt": briefing.get("score_gesamt", 0),
        "benchmark_avg": briefing.get("benchmark_avg", "—"),
        "benchmark_top": briefing.get("benchmark_top", "—"),
        "report_date": today.strftime("%d.%m.%Y"),
        "report_year": today.year,
        # Logos resolved relative to templates/
        "logo_primary": "templates/ki-sicherheit-logo.webp",
        "logo_tuv": "templates/tuev-logo-transparent.webp",
        "logo_dsgvo": "templates/dsgvo.svg",
        "logo_eu_ai": "templates/eu-ai.svg",
        "logo_ready": "templates/ki-ready-2025.webp",
    }
    # Merge metrics
    context.update(metrics)

    # Attach normalized HTML snippets
    for key in (
        "EXECUTIVE_SUMMARY_HTML","QUICK_WINS_HTML_LEFT","QUICK_WINS_HTML_RIGHT",
        "PILOT_PLAN_HTML","ROI_HTML","COSTS_OVERVIEW_HTML","RISKS_HTML","GAMECHANGER_HTML",
        "FOERDERPROGRAMME_HTML","QUELLEN_HTML","TOOLS_HTML"
    ):
        context[key] = _strip_code_fences(snippets.get(key, ""))

    return context

def render_report_html(briefing: Dict[str, Any], snippets: Dict[str, str]) -> str:
    """Render final HTML from the pdf_template.html with context placeholders."""
    context = build_context(briefing, snippets)
    # Load template
    template_path = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    html = template
    for k, v in context.items():
        html = html.replace("{{" + k + "}}", ensure_utf8(str(v)))

    return ensure_utf8(html)
