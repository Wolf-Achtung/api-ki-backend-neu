# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Analyse-Orchestrator (DE) – mit Auto-PDF & optionalem E-Mail-Versand.

Ablauf in run_async(briefing_id, email?):
  1) Analyse erzeugen (Analysis-Record + HTML)
  2) PDF-Service aufrufen -> Report-Record anlegen
  3) Falls E-Mail möglich: Mail an Empfänger (Anhang oder Link)

Robustheit:
  - Fallbacks: fehlender OPENAI_API_KEY -> Entwicklungs-HTML
  - PDF-Service-Fehler -> Report mit error-Info, Analyse bleibt erhalten
  - E-Mail optional: nur wenn SMTP konfiguriert & Empfänger vorhanden
"""

import logging, json, os
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from core.db import SessionLocal
from models import Briefing, Analysis, Report, User
from settings import settings
from services.prompt_engine import render_file, dumps
from services.pdf_client import render_pdf_from_html
from services.email import send_mail

log = logging.getLogger(__name__)

# ---- Templates ----
TEMPLATES_DE = {
    "executive_summary": "prompts/de/executive_summary_de.md",
    "business":          "prompts/de/business_de.md",
    "quick_wins":        "prompts/de/quick_wins_de.md",
    "roadmap":           "prompts/de/roadmap_de.md",
    "recommendations":   "prompts/de/recommendations_de.md",
    "risks":             "prompts/de/risks_de.md",
    "compliance":        "prompts/de/compliance_de.md",
}

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
    "bw":"Baden‑Württemberg","by":"Bayern","be":"Berlin","bb":"Brandenburg","hb":"Bremen","hh":"Hamburg","he":"Hessen",
    "mv":"Mecklenburg‑Vorpommern","ni":"Niedersachsen","nw":"Nordrhein‑Westfalen","rp":"Rheinland‑Pfalz","sl":"Saarland",
    "sn":"Sachsen","st":"Sachsen‑Anhalt","sh":"Schleswig‑Holstein","th":"Thüringen",
}

# ---- Kontext Builder ----
def _score(answers: Dict[str, Any]) -> Dict[str, Any]:
    s = {}
    try:
        s["digitalisierungsgrad"] = int(answers.get("digitalisierungsgrad") or 0)
    except Exception:
        s["digitalisierungsgrad"] = 0
    try:
        s["risikofreude"] = int(answers.get("risikofreude") or 0)
    except Exception:
        s["risikofreude"] = 0
    s["automation"] = (answers.get("automatisierungsgrad") or "unbekannt")
    s["ki_knowhow"] = (answers.get("ki_knowhow") or "unbekannt")
    return s

def _free_text(answers: Dict[str, Any]) -> str:
    keys = ["hauptleistung", "ki_projekte", "ki_potenzial", "ki_geschaeftsmodell_vision", "moonshot"]
    parts = []
    for k in keys:
        v = answers.get(k)
        if v:
            parts.append(f"{k}: {v}")
    return " | ".join(parts) if parts else "—"

def _tools_for(branch: str) -> List[Dict[str, Any]]:
    generic = [
        {"name":"RAG Wissensbasis", "zweck":"Interne Dokumente fragbar machen", "notizen":"Open‑source / Managed Optionen"},
        {"name":"Dokument‑Automation", "zweck":"Texte/Angebote/Protokolle", "notizen":"Vorlagen + KI‑Korrektur"},
        {"name":"Daten‑Pipelines", "zweck":"ETL/ELT für KI", "notizen":"SaaS/Cloud‑Services"},
    ]
    extra = {
        "marketing":[{"name":"KI‑Ad‑Ops", "zweck":"Kampagnenvorschläge, Varianten", "notizen":"Guardrails & Freigaben"}],
        "handel":[{"name":"Produkt‑Kategorisierung", "zweck":"Autom. Tags/Beschreibungen", "notizen":"Qualitätskontrollen"}],
        "industrie":[{"name":"Prozess‑Monitoring", "zweck":"Anomalien & Wartung", "notizen":"Sensor/SCADA‑Anbindung"}],
        "gesundheit":[{"name":"Termin & Doku Assist", "zweck":"Routine entlasten", "notizen":"Datenschutz streng beachten"}],
    }
    return generic + extra.get(branch, [])

def _funding_for(state: str) -> List[Dict[str, Any]]:
    return [
        {"programm":"Digital Jetzt (BMWK)", "hinweis":"Investitionen & Qualifizierung – Prüfen Sie Antragsfenster."},
        {"programm":"go‑digital (BMWK)", "hinweis":"Beratung & Umsetzung für KMU."},
        {"programm":f"Landesprogramme ({STATE_LABELS.get(state,state).title()})", "hinweis":"Regionale Fördertöpfe je nach Thema."},
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
    ctx = {
        "BRANCHE": branche,
        "BRANCHE_LABEL": BRANCH_LABELS.get(branche, branche.title()),
        "UNTERNEHMENSGROESSE": size,
        "UNTERNEHMENSGROESSE_LABEL": SIZE_LABELS.get(size, size),
        "HAUPTLEISTUNG": a.get("hauptleistung") or "—",
        "BUNDESLAND": state,
        "BUNDESLAND_LABEL": STATE_LABELS.get(state, state),
        "BRIEFING_JSON": dumps({k:a[k] for k in a.keys() if k in ("branche","unternehmensgroesse","bundesland","hauptleistung")}),
        "ALL_ANSWERS_JSON": dumps(a),
        "FREE_TEXT_NOTES": _free_text(a),
        "SCORING_JSON": dumps(_score(a)),
        "BENCHMARKS_JSON": dumps(_benchmarks_stub()),
        "TOOLS_JSON": dumps(_tools_for(branche)),
        "FUNDING_JSON": dumps(_funding_for(state)),
        "BUSINESS_JSON": dumps(_business_stub(a)),
    }
    return ctx

# ---- LLM Call ----
def _call_openai(prompt: str) -> str:
    if not settings.OPENAI_API_KEY:
        return f"""<p><em>Entwicklungsmodus – kein OPENAI_API_KEY gesetzt.</em></p>
<div class="debug">{prompt[:300]}</div>"""
    base = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
    url = f"{base}/chat/completions"
    hdr = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {"model": getattr(settings, "OPENAI_MODEL", "gpt-4o"), "messages": [{"role":"user","content": prompt}], "temperature": 0.2}
    r = requests.post(url, headers=hdr, json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"OpenAI error {r.status_code}: {r.text[:200]}")
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()

def _render_section(name: str, template_path: str, ctx: Dict[str, Any]) -> str:
    prompt = render_file(template_path, ctx)
    html = _call_openai(prompt)
    return f'<section id="{name}">{html}</section>'

def build_full_report_html(br: Briefing) -> Dict[str, Any]:
    ctx = _ctx_for(br)
    sections = []
    for key, path in TEMPLATES_DE.items():
        try:
            sections.append(_render_section(key, path, ctx))
        except Exception as exc:
            log.exception("Section %s failed: %s", key, exc)
            sections.append(f'<section id="{key}"><p><em>Abschnitt "{key}" konnte nicht generiert werden.</em></p></section>')
    toc = "".join([f'<li><a href="#{k}">{k.replace("_"," ").title()}</a></li>' for k in TEMPLATES_DE.keys()])
    html = ('<article class="ki-report">'
            '<h2>KI‑Status‑Report</h2>'
            f'<nav><ul class="toc">{toc}</ul></nav>'
            + "".join(sections) +
            '</article>')
    meta = {"sections": list(TEMPLATES_DE.keys()), "lang": br.lang, "generated_at": datetime.now(timezone.utc).isoformat()}
    return {"html": html, "meta": meta}

# ---- Public API ----
def analyze_briefing(db: Session, briefing_id: int) -> Tuple[int, str, Dict[str, Any]]:
    br = db.get(Briefing, briefing_id)
    if not br:
        raise ValueError("Briefing not found")
    result = build_full_report_html(br)
    an = Analysis(user_id=br.user_id, briefing_id=briefing_id,
                  html=result["html"], meta=result["meta"],
                  created_at=datetime.now(timezone.utc))
    db.add(an); db.commit(); db.refresh(an)
    return an.id, result["html"], result["meta"]

def _determine_recipient(db: Session, briefing: Briefing, email_override: Optional[str]) -> Optional[str]:
    if email_override:
        return email_override
    if briefing.user_id:
        u = db.get(User, briefing.user_id)
        if u and getattr(u, "email", None):
            return u.email
    return None

def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    """Background‑freundlicher Wrapper: erstellt Analyse, PDF & versendet optional E‑Mail."""
    db = SessionLocal()
    try:
        # 1) Analyse
        an_id, html, meta = analyze_briefing(db, briefing_id)
        an = db.get(Analysis, an_id)
        br = db.get(Briefing, briefing_id)
        log.info("analysis created: id=%s", an_id)

        # 2) PDF (optional, robust)
        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id})
        pdf_url = pdf_info.get("pdf_url")
        pdf_bytes = pdf_info.get("pdf_bytes")
        pdf_error = pdf_info.get("error")

        rep = Report(
            user_id=br.user_id if br else None,
            briefing_id=briefing_id,
            analysis_id=an_id,
            pdf_url=pdf_url,
            pdf_bytes_len=(len(pdf_bytes) if pdf_bytes else None),
            created_at=datetime.now(timezone.utc),
        )
        db.add(rep); db.commit(); db.refresh(rep)
        log.info("report created: id=%s url=%s bytes=%s", rep.id, rep.pdf_url, rep.pdf_bytes_len)

        # 3) E-Mail (optional)
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
                attachments.append({"filename": f"KI-Status-Report-{an_id}.pdf", "content": pdf_bytes, "mimetype": "application/pdf"})
            mail_ok, mail_err = send_mail(recipient, subject, body_html, text=None, attachments=attachments)
            if mail_ok:
                log.info("report e-mail sent to %s", recipient)
            else:
                log.warning("report e-mail not sent: %s", mail_err)

    except Exception as exc:
        log.exception("run_async failed for briefing_id=%s: %s", briefing_id, exc)
    finally:
        db.close()
