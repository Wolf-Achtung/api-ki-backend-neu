# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Report pipeline (Gold‑Standard+) – robust context building & HTML rendering.
- Behebt Score‑0/100‑Bug (mehrere Quellen für Scores + Heuristik)
- Füllt KPI‑Platzhalter & Business Case via Content‑Normalizer
- UTF‑8‑sicheres Templating
"""

import os
import datetime as dt
import re
from typing import Dict, Any

from .sanitize import ensure_utf8

DEFAULTS = {
    "stundensatz_eur": int(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60")),
    "qw1_monat_stunden": int(os.getenv("DEFAULT_QW1_H", "10")),
    "qw2_monat_stunden": int(os.getenv("DEFAULT_QW2_H", "8")),
}
TRANSPARENCY_TEXT = os.getenv(
    "TRANSPARENCY_TEXT",
    "Dieser Report wurde teilweise mit KI‑Unterstützung in Europa unter Einhaltung von EU AI Act und DSGVO erstellt."
)

CODE_FENCE_RE = re.compile(r"```+[a-zA-Z]*\s*|\u200b", flags=re.MULTILINE)

def _strip_code_fences(html: str) -> str:
    return CODE_FENCE_RE.sub("", html or "").strip()

def _dash(value: Any) -> str:
    return "—" if value in (None, "", [], {}) else str(value)

def derive_metrics(briefing: Dict[str, Any]) -> Dict[str, Any]:
    stunden = DEFAULTS["qw1_monat_stunden"] + DEFAULTS["qw2_monat_stunden"]
    stundensatz = DEFAULTS["stundensatz_eur"]
    size = (briefing.get("unternehmensgroesse") or "").lower()
    if size in {"kmu", "mittel", "11–100", "11-100"}:
        stundensatz = max(stundensatz, 70)
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

def _score_from_sources(briefing: Dict[str, Any], snippets: Dict[str, Any], key: str, aliases=None) -> int:
    aliases = aliases or []
    # 1) briefing
    if isinstance(briefing.get(key), (int, float)):
        return int(briefing.get(key))
    # 2) snippets (flat keys or nested dict in 'scores')
    if isinstance(snippets.get(key), (int, float)):
        return int(snippets.get(key))
    scores_obj = snippets.get("scores") or snippets.get("SCORES") or {}
    if isinstance(scores_obj, dict):
        if isinstance(scores_obj.get(key), (int, float)):
            return int(scores_obj.get(key))
        for a in aliases:
            if isinstance(scores_obj.get(a), (int, float)):
                return int(scores_obj.get(a))
    # 3) fallback
    return -1  # -1 signalisiert: nicht vorhanden

def derive_scores(briefing: Dict[str, Any], snippets: Dict[str, Any]) -> Dict[str, int]:
    # Versuche möglichst vorhandene Zahlen zu übernehmen
    gov = _score_from_sources(briefing, snippets, "score_governance", ["governance", "gov"]) 
    sec = _score_from_sources(briefing, snippets, "score_sicherheit", ["security", "sec"]) 
    val = _score_from_sources(briefing, snippets, "score_nutzen", ["value", "val"]) 
    ena = _score_from_sources(briefing, snippets, "score_befaehigung", ["enablement", "ena"]) 
    overall = _score_from_sources(briefing, snippets, "score_gesamt", ["overall", "total"]) 

    # Heuristik, falls nicht vorhanden
    if min(gov, sec, val, ena, overall) == -1:
        # simple heuristics basierend auf briefing-antworten
        gov = 85 if briefing.get("governance_richtlinien") == "ja" else 70
        if (briefing.get("loeschregeln") or "").startswith("teil"): 
            gov -= 5
        if (briefing.get("meldewege") or "").startswith("teil"):
            gov -= 2

        sec = 78 if briefing.get("technische_massnahmen") == "alle" else 65
        if (briefing.get("loeschregeln") or "").startswith("teil"):
            sec -= 2

        val = 95
        if briefing.get("automatisierungsgrad") == "sehr_hoch" and briefing.get("prozesse_papierlos", "0").startswith("81"):
            val = 100

        ena = 80 if briefing.get("change_management") in {"hoch", "sehr_hoch"} else 65
        if briefing.get("roadmap_vorhanden") == "teilweise": 
            ena -= 4

        overall = round((gov + sec + val + ena) / 4)

    return {
        "score_governance": max(0, min(100, int(gov))),
        "score_sicherheit": max(0, min(100, int(sec))),
        "score_nutzen": max(0, min(100, int(val))),
        "score_befaehigung": max(0, min(100, int(ena))),
        "score_gesamt": max(0, min(100, int(overall))),
    }

def _strip_and_set(context: Dict[str, Any], snippets: Dict[str, Any], key: str) -> None:
    context[key] = ensure_utf8(_strip_code_fences(snippets.get(key, "")))

def build_context(briefing: Dict[str, Any], snippets: Dict[str, str]) -> Dict[str, Any]:
    metrics = derive_metrics(briefing or {})
    scores = derive_scores(briefing or {}, snippets or {})
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
        **scores,
        "report_date": today.strftime("%d.%m.%Y"),
        "report_year": today.year,
        "logo_primary": "templates/ki-sicherheit-logo.webp",
        "logo_tuv": "templates/tuev-logo-transparent.webp",
        "logo_dsgvo": "templates/dsgvo.svg",
        "logo_eu_ai": "templates/eu-ai.svg",
        "logo_ready": "templates/ki-ready-2025.webp",
        "transparency_text": snippets.get("transparency_text", TRANSPARENCY_TEXT),
    }
    context.update(metrics)

    # Textuelle Sektionen — inkl. KPI-HTML
    for key in (
        "EXECUTIVE_SUMMARY_HTML","QUICK_WINS_HTML_LEFT","QUICK_WINS_HTML_RIGHT",
        "PILOT_PLAN_HTML","ROI_HTML","COSTS_OVERVIEW_HTML","RISKS_HTML","GAMECHANGER_HTML",
        "FOERDERPROGRAMME_HTML","QUELLEN_HTML","TOOLS_HTML","BENCHMARK_HTML",
        "KPI_HTML","KPI_BRANCHE_HTML",
    ):
        _strip_and_set(context, snippets, key)

    # Globale Kontextvariablen ergänzen
    domain = (user_email.split("@")[1] if "@" in user_email else "")
    kundencode = (domain.split(".")[0][:3] if domain else "XXX").upper()
    report_id = f"R-{today.strftime('%Y%m%d')}-{kundencode}"
    version_full = os.getenv("VERSION", "1.0.0")
    version_mm = ".".join(version_full.split(".")[:2])
    context["report_id"] = report_id
    context["report_version"] = version_mm
    context["WATERMARK_TEXT"] = f"Trusted KI-Check · Report-ID: {report_id} · v{version_mm}"
    context["CHANGELOG_SHORT"] = os.getenv("CHANGELOG_SHORT", "—")
    context["AUDITOR_INITIALS"] = os.getenv("AUDITOR_INITIALS", "KSJ")
    context["research_last_updated"] = briefing.get("research_last_updated") or context.get("report_date", "")

    return context

def render_report_html(briefing: Dict[str, Any], snippets: Dict[str, str]) -> str:
    # Vorab anreichern (KPI/ROI/Tools/Förderungen) – failsafe optional import
    metrics = derive_metrics(briefing or {})
    try:
        from .content_normalizer import normalize_and_enrich_sections
        snippets = normalize_and_enrich_sections(briefing, snippets, metrics)
    except Exception:
        # Harmlos weiter – Template zeigt ggf. Defaults/Striche
        pass

    context = build_context(briefing, snippets)

    template_path = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    html = template
    for k, v in context.items():
        html = html.replace("{{" + k + "}}", ensure_utf8(str(v)))

    # Platzhalter, die übrig bleiben, neutralisieren (sauberes PDF)
    html = re.sub(r"{{\s*[A-Z0-9_]+\s*}}", "—", html)
    return ensure_utf8(html)
