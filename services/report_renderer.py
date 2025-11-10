
# -*- coding: utf-8 -*-
"""
services.report_renderer
Rendert das PDF auf Basis des HTML-Templates und harmonisiert Variablennamen zwischen
Template und Generierungslogik (Backward-Compat mit älteren Prompts).
"""
from __future__ import annotations
import os, re, datetime
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

DEFAULT_TEMPLATE = os.getenv("PDF_TEMPLATE_PATH", "templates/pdf_template.html")

def _score_bars_html(scores: Dict[str, Any]) -> str:
    def row(label: str, key: str) -> str:
        try:
            v = max(0, min(100, int(float(scores.get(key, 0)))))
        except Exception:
            v = 0
        return (
            f"<tr><td style='padding:6px 8px;width:160px'>{label}</td>"
            f"<td style='padding:6px 8px;width:100%'>"
            f"<div style='height:8px;border-radius:6px;background:#eef2ff;overflow:hidden'><i style='display:block;height:8px;width:{v}%;background:linear-gradient(90deg,#3b82f6,#2563eb)'></i></div>"
            f"<div style='font-size:10px;color:#475569'>{v}/100</div>"
            f"</td></tr>"
        )
    rows = "".join([
        row("Governance", "governance"),
        row("Sicherheit", "security"),
        row("Wertschöpfung", "value"),
        row("Befähigung", "enablement"),
        row("Gesamt", "overall"),
    ])
    return f"<table style='width:100%;border-collapse:collapse'>{rows}</table>"


def _merge_sections(generated: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    s = dict(generated or {})
    # Synonyme/Back-Compat
    # Quick Wins: Wenn zwei Spalten vorhanden, zusammenführen
    if s.get("QUICK_WINS_HTML_LEFT") or s.get("QUICK_WINS_HTML_RIGHT"):
        left = s.get("QUICK_WINS_HTML_LEFT","")
        right = s.get("QUICK_WINS_HTML_RIGHT","")
        s["QUICK_WINS_HTML"] = f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:16px'>{left}{right}</div>"
    s.setdefault("QUICK_WINS_HTML", s.get("QUICK_WINS", ""))

    # Roadmaps
    s.setdefault("ROADMAP_90_HTML", s.get("PILOT_PLAN_HTML", ""))
    s.setdefault("ROADMAP_12_HTML", s.get("ROADMAP_12M_HTML", ""))

    # Funding
    s.setdefault("FUNDING_HTML", s.get("FOERDERPROGRAMME_HTML", s.get("FUNDING_TABLE_HTML","")))

    # Next Steps
    s.setdefault("NEXT_STEPS_HTML", s.get("NEXT_ACTIONS_HTML", ""))

    # KPI / Scores
    s.setdefault("KPI_SCORES_HTML", _score_bars_html(scores or {}))

    # Transparenz
    if not s.get("TRANSPARENCY_HTML"):
        s["TRANSPARENCY_HTML"] = s.get("SOURCES_BOX_HTML","")

    return s


def render(briefing, run_id: str, generated_sections: Dict[str, Any], use_fetchers: bool, scores: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    # Template laden
    tpl_path = DEFAULT_TEMPLATE
    # Fallback: wenn im aktuellen Arbeitsverzeichnis eine pdf_template.html liegt
    if not os.path.exists(tpl_path):
        alt = Path("pdf_template.html")
        if alt.exists():
            tpl_path = str(alt)

    env = Environment(
        loader=FileSystemLoader(Path(tpl_path).parent),
        autoescape=select_autoescape(enabled_extensions=("html","xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    tpl = env.get_template(Path(tpl_path).name)

    # Kontext zusammenbauen
    answers = getattr(briefing, "answers", None) or {}
    ctx: Dict[str, Any] = {}

    # Basics
    today = datetime.date.today().strftime("%d.%m.%Y")
    ctx["report_date"] = generated_sections.get("report_date") or today
    ctx["report_id"] = generated_sections.get("report_id") or meta.get("analysis_id") or ""
    ctx["LANG"] = "de"

    # Headline-Daten
    ctx["BRANCHE_LABEL"] = generated_sections.get("BRANCHE_LABEL") or answers.get("BRANCHE_LABEL") or answers.get("branche","")
    ctx["UNTERNEHMENSGROESSE_LABEL"] = generated_sections.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse","")
    ctx["BUNDESLAND_LABEL"] = generated_sections.get("BUNDESLAND_LABEL") or answers.get("BUNDESLAND_LABEL") or answers.get("bundesland","")
    ctx["HAUPTLEISTUNG"] = generated_sections.get("HAUPTLEISTUNG") or answers.get("hauptleistung","")

    # Besitzer/Branding
    ctx["OWNER_NAME"] = generated_sections.get("OWNER_NAME") or os.getenv("OWNER_NAME", "KI‑Sicherheit.jetzt")

    # Scores für Platzhalter
    ctx["score_governance"] = scores.get("governance", 0)
    ctx["score_sicherheit"] = scores.get("security", 0)
    ctx["score_wertschoepfung"] = scores.get("value", 0)
    ctx["score_befaehigung"] = scores.get("enablement", 0)
    ctx["score_gesamt"] = scores.get("overall", 0)

    # Abschnitte harmonisieren
    sections = _merge_sections(generated_sections, scores)
    ctx.update(sections)

    # Zusätzliche Legacy-Variablen (für ältere Prompts)
    ctx.setdefault("heute_iso", today)
    ctx.setdefault("build_id", generated_sections.get("BUILD_ID",""))

    html_out = tpl.render(**ctx)
    return {"html": html_out, "meta": {"scores": scores, **(meta or {})}}
