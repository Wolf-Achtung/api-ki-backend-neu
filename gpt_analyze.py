# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Analyse-Orchestrator (DE) – rendert alle Kernsektionen + optionale Zusatzsektionen,
baut den finalen Report-HTML via templates/pdf_template.html und kümmert sich in
run_async() zusätzlich um PDF-Erzeugung und optionalen E-Mail-Versand.

Voraussetzungen:
- services/prompt_engine.py    -> render_file(), dumps()
- services/report_renderer.py  -> render()
- services/pdf_client.py       -> render_pdf_from_html()
- services/email.py            -> send_mail()

Modelle:
- Briefing (answers JSON, lang, user_id ...)
- Analysis(html, meta, briefing_id, user_id, created_at)
- Report(pdf_url | pdf_bytes_len, analysis_id, briefing_id, user_id, created_at)
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from core.db import SessionLocal
from models import Analysis, Briefing, Report, User
from services.prompt_engine import dumps, render_file
from services.report_renderer import render as render_report_html
from services.pdf_client import render_pdf_from_html
from services.email import send_mail
from settings import settings

log = logging.getLogger(__name__)

# -------------------------- Prompt-Mapping --------------------------
CORE_SECTIONS = [
    ("executive_summary", "prompts/de/executive_summary_de.md", "EXEC_SUMMARY_HTML"),
    ("quick_wins",        "prompts/de/quick_wins_de.md",        "QUICK_WINS_HTML"),
    ("roadmap",           "prompts/de/roadmap_de.md",           "ROADMAP_HTML"),
    ("risks",             "prompts/de/risks_de.md",             "RISKS_HTML"),
    ("compliance",        "prompts/de/compliance_de.md",        "COMPLIANCE_HTML"),
    ("business",          "prompts/de/business_de.md",          "BUSINESS_CASE_HTML"),
    ("recommendations",   "prompts/de/recommendations_de.md",   "RECOMMENDATIONS_HTML"),
]

EXTRA_PATTERNS = [
    ("data_readiness", "prompts/de/data_readiness_de.md", "Dateninventar & -qualität"),
    ("org_change",     "prompts/de/org_change_de.md",     "Organisation & Change"),
    ("gamechanger",    "prompts/de/gamechanger_de.md",    "Gamechanger-Use Case"),
    ("pilot_plan",     "prompts/de/pilot_plan_de.md",     "90-Tage Pilotplan"),
    ("costs_overview", "prompts/de/costs_overview_de.md", "Kosten/Nutzen-Übersicht"),
]

BRANCH_LABELS = {
    "marketing": "Marketing & Werbung",
    "beratung": "Beratung & Dienstleistungen",
    "it": "IT & Software",
    "finanzen": "Finanzen & Versicherungen",
    "handel": "Handel & E‑Commerce",
    "bildung": "Bildung",
    "verwaltung": "Verwaltung",
    "gesundheit": "Gesundheit & Pflege",
    "bau": "Bauwesen & Architektur",
    "medien": "Medien & Kreativwirtschaft",
    "industrie": "Industrie & Produktion",
    "logistik": "Transport & Logistik",
}
SIZE_LABELS = {
    "solo": "1 (Solo‑Selbstständig/Freiberuflich)",
    "team": "2–10 (Kleines Team)",
    "kmu": "11–100 (KMU)",
}
STATE_LABELS = {
    "bw": "Baden‑Württemberg",
    "by": "Bayern",
    "be": "Berlin",
    "bb": "Brandenburg",
    "hb": "Bremen",
    "hh": "Hamburg",
    "he": "Hessen",
    "mv": "Mecklenburg‑Vorpommern",
    "ni": "Niedersachsen",
    "nw": "Nordrhein‑Westfalen",
    "rp": "Rheinland‑Pfalz",
    "sl": "Saarland",
    "sn": "Sachsen",
    "st": "Sachsen‑Anhalt",
    "sh": "Schleswig‑Holstein",
    "th": "Thüringen",
}

# -------------------------- Kontextaufbereitung --------------------------
def _score(answers: Dict[str, Any]) -> Dict[str, Any]:
    s: Dict[str, Any] = {}
    try:
        s["digitalisierungsgrad"] = int(answers.get("digitalisierungsgrad") or 0)
    except Exception:
        s["digitalisierungsgrad"] = 0
    try:
        s["risikofreude"] = int(answers.get("risikofreude") or 0)
    except Exception:
        s["risikofreude"] = 0
    s["automation"] = answers.get("automatisierungsgrad") or "unbekannt"
    s["ki_knowhow"] = answers.get("ki_knowhow") or "unbekannt"
    return s

def _free_text(answers: Dict[str, Any]) -> str:
    keys = ["hauptleistung", "ki_projekte", "ki_potenzial", "ki_geschaeftsmodell_vision", "moonshot"]
    parts: List[str] = []
    for k in keys:
        v = answers.get(k)
        if v:
            parts.append(f"{k}: {v}")
    return " | ".join(parts) if parts else "—"

def _tools_for(branch: str) -> List[Dict[str, Any]]:
    generic = [
        {"name": "RAG Wissensbasis", "zweck": "Interne Dokumente fragbar machen", "notizen": "Open‑source / Managed Optionen"},
        {"name": "Dokument‑Automation", "zweck": "Texte/Angebote/Protokolle", "notizen": "Vorlagen + KI‑Korrektur"},
        {"name": "Daten‑Pipelines", "zweck": "ETL/ELT für KI", "notizen": "SaaS/Cloud‑Services"},
    ]
    extra = {
        "marketing": [{"name": "KI‑Ad‑Ops", "zweck": "Kampagnenvorschläge, Varianten", "notizen": "Guardrails & Freigaben"}],
        "handel": [{"name": "Produkt‑Kategorisierung", "zweck": "Autom. Tags/Beschreibungen", "notizen": "Qualitätskontrollen"}],
        "industrie": [{"name": "Prozess‑Monitoring", "zweck": "Anomalien & Wartung", "notizen": "Sensor/SCADA‑Anbindung"}],
        "gesundheit": [{"name": "Termin & Doku Assist", "zweck": "Routine entlasten", "notizen": "Datenschutz streng beachten"}],
    }
    return generic + extra.get(branch, [])

def _funding_for(state: str) -> List[Dict[str, Any]]:
    return [
        {"programm": "Digital Jetzt (BMWK)", "hinweis": "Investitionen & Qualifizierung – Prüfen Sie Antragsfenster."},
        {"programm": "go‑digital (BMWK)", "hinweis": "Beratung & Umsetzung für KMU."},
        {"programm": f"Landesprogramme ({STATE_LABELS.get(state, state).title()})", "hinweis": "Regionale Fördertöpfe je nach Thema."},
    ]

def _benchmarks_stub() -> Dict[str, Any]:
    return {"source": "intern", "notes": "Pilotbetrieb – Platzhalter für künftige Vergleiche."}

def _business_stub(answers: Dict[str, Any]) -> Dict[str, Any]:
    return {"umsatz_range": answers.get("jahresumsatz") or "keine_angabe"}

def _ctx_for(br: Briefing) -> Dict[str, Any]:
    a = br.answers or {}
    branche = str(a.get("branche") or "unbekannt")
    size = str(a.get("unternehmensgroesse") or "unbekannt")
    state = str(a.get("bundesland") or "unbekannt")
    ctx: Dict[str, Any] = {
        "BRANCHE": branche,
        "BRANCHE_LABEL": BRANCH_LABELS.get(branche, branche.title()),
        "UNTERNEHMENSGROESSE": size,
        "UNTERNEHMENSGROESSE_LABEL": SIZE_LABELS.get(size, size),
        "HAUPTLEISTUNG": a.get("hauptleistung") or "—",
        "BUNDESLAND": state,
        "BUNDESLAND_LABEL": STATE_LABELS.get(state, state),
        "BRIEFING_JSON": dumps({k: a[k] for k in a.keys() if k in ("branche", "unternehmensgroesse", "bundesland", "hauptleistung")}),
        "ALL_ANSWERS_JSON": dumps(a),
        "FREE_TEXT_NOTES": _free_text(a),
        "SCORING_JSON": dumps(_score(a)),
        "BENCHMARKS_JSON": dumps(_benchmarks_stub()),
        "TOOLS_JSON": dumps(_tools_for(branche)),
        "FUNDING_JSON": dumps(_funding_for(state)),
        "BUSINESS_JSON": dumps(_business_stub(a)),
    }
    return ctx

# -------------------------- LLM-Aufruf --------------------------
def _call_openai(prompt: str) -> str:
    if not settings.OPENAI_API_KEY:
        return "<p><em>Entwicklungsmodus – kein OPENAI_API_KEY gesetzt.</em></p>"
    base = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o")
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    if resp.status_code >= 400:
        raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()

def _render_section(template_path: str, ctx: Dict[str, Any]) -> str:
    prompt = render_file(template_path, ctx)
    return _call_openai(prompt)

# -------------------------- Hilfs-HTML (ohne LLM) --------------------------
def _build_profile_html(ctx: Dict[str, Any]) -> str:
    def pill(label: str, val: str) -> str:
        return f'<span class="pill"><b>{label}</b>: {val}</span>'
    items = [
        pill("Branche", ctx.get("BRANCHE_LABEL", "–")),
        pill("Größe", ctx.get("UNTERNEHMENSGROESSE_LABEL", "–")),
        pill("Hauptleistung", ctx.get("HAUPTLEISTUNG", "–")),
        pill("Bundesland", ctx.get("BUNDESLAND_LABEL", "–")),
    ]
    return "<p>" + " ".join(items) + "</p>"

def _build_kpi_bars_html(ctx: Dict[str, Any]) -> str:
    s = {}
    try:
        s = json.loads(ctx.get("SCORING_JSON", "{}"))
    except Exception:
        s = {}
    def bar(label: str, val: Any, median: int = 50) -> str:
        try:
            v = int(val)
        except Exception:
            v = 0
        # Interpret 0-10 Skalen als 0-100%
        v = v * 10 if v <= 10 else v
        v = max(0, min(100, v))
        return (
            '<div class="kpi bar">'
            f'<div class="label">{label}</div>'
            '<div class="bar__track">'
            f'<div class="bar__fill" style="width:{v}%"></div>'
            f'<div class="bar__median" style="left:{median}%"></div>'
            '</div>'
            f'<div class="bar__delta">{v}%</div>'
            '</div>'
        )
    items = [
        bar("Digitalisierungsgrad", s.get("digitalisierungsgrad", 0)),
        bar("Risikofreude", s.get("risikofreude", 0)),
    ]
    return "\n".join(items)

# -------------------------- Report-Bau --------------------------
def build_full_report_html(br: Briefing) -> Dict[str, Any]:
    ctx = _ctx_for(br)

    # Kernsektionen
    rendered: Dict[str, str] = {}
    order: List[str] = []
    for key, path, placeholder in CORE_SECTIONS:
        try:
            html = _render_section(path, ctx)
        except Exception as exc:
            log.exception("Section %s failed: %s", key, exc)
            html = f'<p><em>Abschnitt "{key}" konnte nicht generiert werden.</em></p>'
        rendered[placeholder] = html
        order.append(key)

    # Extras → Appendix
    extra_blocks: List[str] = []
    for key, path, title in EXTRA_PATTERNS:
        try:
            html = _render_section(path, ctx)
            extra_blocks.append(f'<div class="section"><h2>{title}</h2>{html}</div>')
            order.append(key)
        except Exception as exc:
            log.warning("Extra section %s skipped: %s", key, exc)

    # Nicht-LLM-Teile
    rendered["PROFILE_HTML"] = _build_profile_html(ctx)
    rendered["KPI_BARS_HTML"] = _build_kpi_bars_html(ctx)
    rendered["REPORT_DATE"] = datetime.now(timezone.utc).date().isoformat()
    rendered["EXTRA_SECTIONS_HTML"] = "\n".join(extra_blocks)

    final_html = render_report_html("templates/pdf_template.html", rendered)
    meta = {"sections": order, "lang": br.lang, "generated_at": datetime.now(timezone.utc).isoformat()}
    return {"html": final_html, "meta": meta}

def analyze_briefing(db: Session, briefing_id: int) -> Tuple[int, str, Dict[str, Any]]:
    br = db.get(Briefing, briefing_id)
    if not br:
        raise ValueError("Briefing not found")
    result = build_full_report_html(br)
    an = Analysis(
        user_id=br.user_id,
        briefing_id=briefing_id,
        html=result["html"],
        meta=result["meta"],
        created_at=datetime.now(timezone.utc),
    )
    db.add(an)
    db.commit()
    db.refresh(an)
    return an.id, result["html"], result["meta"]

# -------------------------- Auto-PDF & Mail --------------------------
def _determine_recipient(db: Session, briefing: Briefing, email_override: Optional[str]) -> Optional[str]:
    if email_override:
        return email_override
    if briefing.user_id:
        u = db.get(User, briefing.user_id)
        if u and getattr(u, "email", None):
            return u.email
    return None

def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    """Background-freundlicher Wrapper: erstellt Analyse, PDF & versendet optional E‑Mail."""
    db = SessionLocal()
    try:
        an_id, html, meta = analyze_briefing(db, briefing_id)
        br = db.get(Briefing, briefing_id)
        log.info("analysis created: id=%s", an_id)

        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id})
        pdf_url = pdf_info.get("pdf_url")
        pdf_bytes = pdf_info.get("pdf_bytes")

        rep = Report(
            user_id=br.user_id if br else None,
            briefing_id=briefing_id,
            analysis_id=an_id,
            pdf_url=pdf_url,
            pdf_bytes_len=(len(pdf_bytes) if pdf_bytes else None),
            created_at=datetime.now(timezone.utc),
        )
        db.add(rep)
        db.commit()
        db.refresh(rep)
        log.info("report created: id=%s url=%s bytes=%s", rep.id, rep.pdf_url, rep.pdf_bytes_len)

        recipient = _determine_recipient(db, br, email)
        if recipient:
            subject = "Ihr KI‑Status‑Report"
            body_html = (
                "<p>Guten Tag,</p>"
                "<p>anbei erhalten Sie den automatisch generierten KI‑Status‑Report.</p>"
                + (f'<p>Sie können den Report <a href="{pdf_url}">hier als PDF abrufen</a>.</p>' if pdf_url else "")
                + "<p>Viele Grüße</p>"
            )
            attachments = []
            if pdf_bytes and not pdf_url:
                attachments.append({
                    "filename": f"KI-Status-Report-{an_id}.pdf",
                    "content": pdf_bytes,
                    "mimetype": "application/pdf",
                })
            ok, err = send_mail(recipient, subject, body_html, text=None, attachments=attachments)
            if ok:
                log.info("report e-mail sent to %s", recipient)
            else:
                log.warning("report e-mail not sent: %s", err)

    except Exception as exc:
        log.exception("run_async failed for briefing_id=%s: %s", briefing_id, exc)
    finally:
        db.close()
