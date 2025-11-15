# -*- coding: utf-8 -*-
from __future__ import annotations

import html
import os
import datetime as dt
import re
from typing import Dict, Any

def ensure_utf8(x: str) -> str:
    return (x or "").encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

CODE_FENCE_RE = re.compile(r"```+[a-zA-Z]*\s*|\u200b", flags=re.MULTILINE)

def _strip_code_fences(html: str) -> str:
    return CODE_FENCE_RE.sub("", html or "").strip()

def _dash(value: Any) -> str:
    return "—" if value in (None, "", [], {}) else str(value)

def _strip_and_set(context: Dict[str, Any], snippets: Dict[str, Any], key: str) -> None:
    context[key] = ensure_utf8(_strip_code_fences(snippets.get(key, "")))

def build_context(briefing: Dict[str, Any], snippets: Dict[str, str]) -> Dict[str, Any]:
    today = dt.date.today()
    user_email = briefing.get("user_email") or briefing.get("email") or ""

    context = {
        "unternehmen_name": _dash(briefing.get("unternehmen_name")),
        "branche": _dash(briefing.get("branche")),
        "bundesland": _dash(briefing.get("bundesland")),
        "jahresumsatz": _dash(briefing.get("jahresumsatz")),
        "unternehmensgroesse": _dash(briefing.get("unternehmensgroesse")),
        "ki_knowhow": _dash(briefing.get("ki_knowhow")),
        "user_email": _dash(user_email),
        "report_date": today.strftime("%d.%m.%Y"),
        "report_year": today.year,
        "CHANGELOG_SHORT": os.getenv("CHANGELOG_SHORT", "—"),
        "AUDITOR_INITIALS": os.getenv("AUDITOR_INITIALS", "KSJ"),
        "WATERMARK_TEXT": os.getenv("WATERMARK_TEXT", "Trusted KI‑Check"),
        "OWNER_NAME": os.getenv("OWNER_NAME", "Wolf Hohl"),
        "CONTACT_EMAIL": os.getenv("CONTACT_EMAIL", "kontakt@ki-sicherheit.jetzt"),
        "SITE_URL": os.getenv("SITE_URL", "https://ki-sicherheit.jetzt"),
    }

    for key in (
        "EXECUTIVE_SUMMARY_HTML","QUICK_WINS_HTML_LEFT","QUICK_WINS_HTML_RIGHT","PILOT_PLAN_HTML",
        "ROI_HTML","COSTS_OVERVIEW_HTML","RISKS_HTML","GAMECHANGER_HTML","FOERDERPROGRAMME_HTML",
        "QUELLEN_HTML","TOOLS_HTML","BENCHMARK_HTML","KPI_HTML","KPI_BRANCHE_HTML",
        "BUSINESS_SENSITIVITY_HTML","BUSINESS_CASE_HTML","ROADMAP_12M_HTML","DATA_READINESS_HTML",
        "ORG_CHANGE_HTML","KREATIV_SPECIAL_HTML","LEISTUNG_NACHWEIS_HTML","GLOSSAR_HTML",
        "FEEDBACK_BOX_HTML","AI_ACT_SUMMARY_HTML","AI_ACT_TABLE_OFFER_HTML","AI_ACT_ADDON_PACKAGES_HTML",
        "NEXT_ACTIONS_HTML","ai_act_phase_label","LEAD_EXEC","LEAD_KPI","LEAD_QW","LEAD_ROADMAP_90",
        "LEAD_ROADMAP_12","LEAD_BUSINESS","LEAD_BUSINESS_DETAIL","LEAD_TOOLS","LEAD_DATA","LEAD_ORG",
        "LEAD_RISKS","LEAD_GC","LEAD_FUNDING","LEAD_NEXT_ACTIONS","LEAD_AI_ACT","LEAD_AI_ACT_ADDON",
        "BRANCHE_LABEL","BUNDESLAND_LABEL","UNTERNEHMENSGROESSE_LABEL","JAHRESUMSATZ_LABEL",
        "score_governance","score_sicherheit","score_nutzen","score_befaehigung","score_gesamt",
        "report_version","report_id","research_last_updated","WATERMARK_TEXT",
        "LEAD_ZIM_ALERT","ZIM_ALERT_HTML",
        "LEAD_ZIM_WORKFLOW","ZIM_WORKFLOW_HTML"
    ):
        if key in snippets:
            _strip_and_set(context, snippets, key)

    return context

def render_report_html(briefing: Dict[str, Any], snippets: Dict[str, str]) -> str:
    """
    DEPRECATED: This function uses unsafe string replacement.
    Use services/report_renderer.py (Jinja2 with auto-escaping) instead.

    This function is kept for backward compatibility only.
    """
    template_path = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    context = build_context(briefing, snippets)

    html_content = template
    for k, v in context.items():
        # SECURITY: Escape HTML to prevent XSS
        # Skip escaping for keys that contain pre-sanitized HTML snippets
        if k.endswith('_HTML'):
            # These are already sanitized by html_sanitizer.py
            html_content = html_content.replace("{{" + k + "}}", ensure_utf8(str(v)))
        else:
            # User input must be HTML-escaped
            html_content = html_content.replace("{{" + k + "}}", html.escape(ensure_utf8(str(v))))

    html_content = re.sub(r"{{\s*[A-Z0-9_]+\s*}}", "—", html_content)
    return ensure_utf8(html_content)
