# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Analyse → Report (HTML/PDF) → E-Mail (User + Admin) mit korreliertem Debug‑Logging.
Gold‑Standard‑Variante: PEP8‑konform, robustes Error‑Handling, optionale Artefakt‑Ablage.

FIXES 2025-10-27 V2.3 (KB-LOADER DEAKTIVIERT):
- 🔧 FIX: KB-Loader komplett deaktiviert (KB-Konzepte sind direkt in Prompts)
- ✅ Projekt läuft wieder ohne KB-Dateinamen-Mismatch
- ✅ Alle 12 optimierten Prompts funktionieren standalone

FIXES 2025-10-27 V2.2 (COMPLETE FIX):
- 🔧 FIX 1: UTF-8-Encoding-Korrektur für Briefing-Daten (ä, ö, ü, ß, etc.)
- 🔧 FIX 2: UPPERCASE-Template-Variablen hinzugefügt (HAUPTLEISTUNG, BRANCHE_LABEL, etc.)
- 🔧 FIX 3: render_file() mit ctx-Parameter aufrufen (aus V2.1)
- ✅ Reihenfolge korrigiert: ctx_upper VOR render_file() erstellen
- ✅ Kontext-Keys erweitert: Alle Jinja2-Template-Variablen verfügbar
"""

FIXES 2025-10-27 V2.1:
- 🔧 CRITICAL FIX: render_file() mit ctx-Parameter aufrufen (Zeile 259)
- ✅ Reihenfolge korrigiert: ctx_upper VOR render_file() erstellen
- ✅ Template-Rendering korrigiert: render_template() statt dumps()
- ✅ Kontext-Keys in UPPERCASE konvertiert für Template-Matching
- ✅ Vereinfachte Template-Loading-Logik

UPDATES 2025-10-27 (V2.0 - KB-Integration):
- ❌ KB-Loader deaktiviert (V2.3): KB-Konzepte sind direkt in Prompts, kein Loader benötigt
- ✅ Alle 12 optimierten Prompts unterstützt (7 Core + 5 Extra)
- ✅ KB-Konzepte in Prompt-Text integriert (4 Säulen, 10-20-70, Legal Pitfalls, etc.)
- ✅ Zusätzliche Business-Daten für neue Sections
- ✅ 5 neue Extra-Sections: data_readiness, org_change, pilot_plan, gamechanger, costs_overview
"""
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from core.db import SessionLocal
from models import Analysis, Briefing, Report, User
from services.prompt_engine import render_template, render_file
from services.report_renderer import render as render_report_html
from services.pdf_client import render_pdf_from_html
from services.email import send_mail
from services.email_templates import render_report_ready_email
from services.research import search_funding_and_tools
from services.knowledge import get_knowledge_blocks
# from services.kb_loader import get_kb_loader, get_all_kb  # ❌ DEAKTIVIERT V2.3 - KB-Konzepte sind direkt in Prompts
from settings import settings

log = logging.getLogger(__name__)

# ---------- Konfiguration über ENV / settings ----------
OPENAI_MODEL = getattr(settings, "OPENAI_MODEL", None) or os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))

DBG_PROMPTS = (os.getenv("DEBUG_LOG_PROMPTS", "0") == "1")
DBG_HTML = (os.getenv("DEBUG_LOG_HTML_SNAPSHOT", "0") == "1")
DBG_PDF = (os.getenv("DEBUG_LOG_PDF_INFO", "1") == "1")
DBG_MASK_EMAILS = (os.getenv("DEBUG_MASK_EMAILS", "1") == "1")
DBG_SAVE_ARTIFACTS = (os.getenv("DEBUG_SAVE_ARTIFACTS", "0") == "1")

ARTIFACTS_ROOT = Path("/tmp/ki-artifacts")

def _mask_email(addr: Optional[str]) -> str:
    if not addr:
        return ""
    if not DBG_MASK_EMAILS:
        return addr
    try:
        name, domain = addr.split("@", 1)
        if len(name) <= 3:
            return f"{name}***@{domain}"
        return f"{name[:3]}***@{domain}"
    except Exception:
        return "***"

def _admin_recipients() -> List[str]:
    """Admin-Empfängerliste aus ADMIN_EMAILS (Komma-getrennt) + optional REPORT_ADMIN_EMAIL als Fallback."""
    emails: List[str] = []
    raw1 = getattr(settings, "ADMIN_EMAILS", None) or os.getenv("ADMIN_EMAILS", "")
    raw2 = getattr(settings, "REPORT_ADMIN_EMAIL", None) or os.getenv("REPORT_ADMIN_EMAIL", "")
    if raw1:
        emails.extend([e.strip() for e in raw1.split(",") if e.strip()])
    if raw2:
        emails.append(raw2.strip())
    seen: Dict[str, None] = {}
    out: List[str] = []
    for e in emails:
        if e not in seen:
            seen[e] = None
            out.append(e)
    return out

# ---------- Prompt/Template-Zuordnung ----------
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

def _fix_utf8_encoding(text: str) -> str:
    """
    ✅ FIX 1 (2025-10-27 V2.1): Korrigiert doppelt-encodete UTF-8-Strings.
    Beispiel: "MarktfÃ¼hrer" → "Marktführer"
    """
    if not text or not isinstance(text, str):
        return text
    try:
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            return text.encode('cp1252').decode('utf-8')
        except:
            return text

def _fix_utf8_encoding_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ✅ FIX 1 (2025-10-27 V2.1): Korrigiert UTF-8-Encoding rekursiv in einem Dictionary.
    """
    if not isinstance(data, dict):
        return data
    
    fixed = {}
    for key, value in data.items():
        if isinstance(value, str):
            fixed[key] = _fix_utf8_encoding(value)
        elif isinstance(value, dict):
            fixed[key] = _fix_utf8_encoding_dict(value)
        elif isinstance(value, list):
            fixed[key] = [
                _fix_utf8_encoding(item) if isinstance(item, str)
                else _fix_utf8_encoding_dict(item) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            fixed[key] = value
    
    return fixed

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
        {"programm": f"Landes‑Förderprogramme ({STATE_LABELS.get(state, state)})", "hinweis": "Länder‑spezifische Digitalisierungsinitiativen."},
    ]

def _save_artifact(run_id: str, filename: str, content: str) -> None:
    if not DBG_SAVE_ARTIFACTS:
        return
    try:
        run_dir = ARTIFACTS_ROOT / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / filename).write_text(content, encoding="utf-8")
    except Exception as exc:
        log.warning("[%s] artifact_save_failed file=%s: %s", run_id, filename, exc)

@dataclass
class ModelReq:
    system: str
    user: str
    max_tokens: int = 4000
    temperature: float = OPENAI_TEMPERATURE

def _call_openai(req: ModelReq, run_id: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '')}",
    }
    payload = {
        "model": OPENAI_MODEL,
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
        "messages": [
            {"role": "system", "content": req.system},
            {"role": "user", "content": req.user},
        ],
    }
    
    if DBG_PROMPTS:
        sys_head = (req.system[:100] + "…") if len(req.system) > 100 else req.system
        usr_head = (req.user[:200] + "…") if len(req.user) > 200 else req.user
        log.debug("[%s] LLM_CALL model=%s temp=%.2f sys=\"%s\" usr=\"%s\"",
                  run_id, OPENAI_MODEL, req.temperature,
                  sys_head.replace("\n", "\\n"),
                  usr_head.replace("\n", "\\n"))
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=OPENAI_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        
        if DBG_PROMPTS:
            resp_head = (text[:200] + "…") if len(text) > 200 else text
            log.debug("[%s] LLM_RESPONSE len=%s resp=\"%s\"",
                      run_id, len(text), resp_head.replace("\n", "\\n"))
        
        return text
        
    except Exception as exc:
        log.exception("[%s] LLM_CALL_FAILED: %s", run_id, exc)
        raise

def _render_section(key: str, template_path: str, answers: Dict[str, Any], 
                    context: Dict[str, Any], run_id: str) -> str:
    """
    ✅ NEUE LOGIK (2025-10-27 V2 - FIXED):
    1. Context mit UPPERCASE Keys erstellen
    2. Template-Datei laden MIT Kontext (Markdown → Jinja2-Rendering)
    3. render_template() aufrufen → ergibt finalen Prompt-String
    4. Prompt an LLM senden
    5. HTML zurückgeben
    
    🔧 FIX 2025-10-27: render_file() benötigt ctx als 2. Parameter
    """
    try:
        # 1. Context mit UPPERCASE Keys erstellen (MUSS VOR render_file sein!)
        ctx_upper = {k.upper(): v for k, v in context.items()}
        ctx_upper["ANSWERS"] = json.dumps(answers, ensure_ascii=False, indent=2)
        
        # 2. Template laden MIT Kontext (✅ FIX: ctx_upper als 2. Parameter übergeben)
        prompt_md = render_file(template_path, ctx_upper)
        _save_artifact(run_id, f"{key}_template.md", prompt_md)
        
        # 3. Template rendern → finaler Prompt
        full = render_template(prompt_md, ctx_upper)
        _save_artifact(run_id, f"{key}_prompt.txt", full)
        
        # 4. LLM-Call
        req = ModelReq(
            system="Du bist KI‑Berater für KMU. Dein Output ist HTML‑Snippet (deutschsprachig, sachlich, klar).",
            user=full
        )
        html = _call_openai(req, run_id=run_id)
        _save_artifact(run_id, f"{key}_response.html", html)
        
        return html
        
    except Exception as exc:
        log.exception("[%s] section_render_failed key=%s: %s", run_id, key, exc)
        return f"<p><em>Fehler bei der Generierung von {key}</em></p>"

def build_full_report_html(br: Briefing, run_id: str) -> Dict[str, Any]:
    answers = getattr(br, "answers", None) or {}
    
    # ✅ FIX 1: UTF-8-Encoding korrigieren (2025-10-27 V2.1)
    answers = _fix_utf8_encoding_dict(answers)
    
    branch = answers.get("branche", "")
    state = answers.get("bundesland", "")
    size = answers.get("unternehmensgroesse", "")
    
    # ✅ FIX 2 (2025-10-27 V2.1): Erweiterte Context-Variablen für Templates
    kw = {
        # Lowercase Keys (für interne Nutzung)
        "branche_name": BRANCH_LABELS.get(branch, branch),
        "bundesland_name": STATE_LABELS.get(state, state),
        "unternehmensgroesse_name": SIZE_LABELS.get(size, size),
        "scores": _score(answers),
        "freitext": _free_text(answers),
        "tools": _tools_for(branch),
        "funding": _funding_for(state),
        "research_data": search_funding_and_tools(branch, state),
        "knowledge_blocks": get_knowledge_blocks(br.lang if hasattr(br, 'lang') else "de"),
        "created_at": getattr(br, "created_at", None),
        "company_name": answers.get("company_name", "Unbekannt"),
        
        # ✅ UPPERCASE Keys für Jinja2-Templates (FIX 2)
        "BRANCHE_LABEL": BRANCH_LABELS.get(branch, branch or "Unbekannt"),
        "BUNDESLAND_LABEL": STATE_LABELS.get(state, state or "Unbekannt"),
        "UNTERNEHMENSGROESSE_LABEL": SIZE_LABELS.get(size, size or "Unbekannt"),
        "HAUPTLEISTUNG": answers.get("hauptleistung", "Ihre Hauptleistung"),
        "MOONSHOT": answers.get("moonshot", "") or answers.get("ki_geschaeftsmodell_vision", "Ihre Vision"),
        "KI_PROJEKTE": answers.get("ki_projekte", ""),
        "KI_POTENZIAL": answers.get("ki_potenzial", ""),
        "JAHRESUMSATZ": answers.get("jahresumsatz", ""),
        "INVESTITIONSBUDGET": answers.get("investitionsbudget", ""),
        "ZEITBUDGET": answers.get("zeitbudget", ""),
        "DIGITALISIERUNGSGRAD": answers.get("digitalisierungsgrad", 0),
        "RISIKOFREUDE": answers.get("risikofreude", 0),
        
        # ✅ NEU V2.0: KB-Integration (DEAKTIVIERT - KB-Konzepte sind direkt in Prompts)
        # **get_all_kb(),  # ❌ DEAKTIVIERT V2.3 - Dateinamen-Mismatch, KB nicht benötigt
        
        # ✅ NEU V2.0: Business-Daten
        "business_json": json.dumps({
            "investitionsbudget": answers.get("investitionsbudget", "keine_angabe"),
            "zeitbudget": answers.get("zeitbudget", "unbekannt"),
            "roi_erwartung": answers.get("roi_erwartung", "keine_angabe"),
        }, ensure_ascii=False),
        
        # ✅ NEU V2.0: Benchmarks
        "benchmarks_json": json.dumps({
            "branche_durchschnitt": 0,
            "groesse_durchschnitt": 0,
            "note": "Benchmark-Daten werden schrittweise ergänzt"
        }, ensure_ascii=False),
    }
    
    order: List[str] = []
    rendered: Dict[str, str] = {}
    
    # Core Sections
    for key, tpl, env_key in CORE_SECTIONS:
        order.append(key)
        rendered[env_key] = _render_section(key, tpl, answers, kw, run_id=run_id)
    
    # Extra Patterns
    for key, tpl, label in EXTRA_PATTERNS:
        if _should_include_pattern(key, answers):
            order.append(key)
            rendered[f"{key.upper()}_HTML"] = _render_section(key, tpl, answers, kw, run_id=run_id)

    final_html = render_report_html("templates/pdf_template.html", rendered)
    
    if DBG_HTML:
        head = final_html[:400].replace("\n", "\\n")
        log.debug("[%s] HTML_SNAPSHOT len=%s head=\"%s\"", run_id, len(final_html), head)
        _save_artifact(run_id, "report.html", final_html)
    
    meta = {
        "sections": order,
        "lang": br.lang if hasattr(br, 'lang') else "de",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    return {"html": final_html, "meta": meta}

def _should_include_pattern(key: str, answers: Dict[str, Any]) -> bool:
    if key == "data_readiness":
        return answers.get("datenquellen") not in [None, [], ["keine"]]
    if key == "org_change":
        return answers.get("unternehmensgroesse") != "solo"
    if key == "gamechanger":
        usecases = answers.get("ki_usecases") or []
        return "produktinnovation" in usecases or "markterschliessung" in answers.get("projektziel", [])
    if key == "pilot_plan":
        return answers.get("zeitbudget") in ["2-5", "5-10", "ueber_10"]
    if key == "costs_overview":
        return answers.get("investitionsbudget") not in [None, "keine_angabe"]
    return False

def _determine_user_email(db: Session, briefing: Briefing, email_override: Optional[str]) -> Optional[str]:
    if email_override:
        return email_override
    
    user_id = getattr(briefing, "user_id", None)
    if user_id:
        u = db.get(User, user_id)
        if u and getattr(u, "email", None):
            return u.email
    
    answers = getattr(briefing, "answers", None) or {}
    return answers.get("email") or answers.get("kontakt_email")

def _send_emails(db: Session, rep: Report, br: Briefing, 
                 pdf_url: Optional[str], pdf_bytes: Optional[bytes], run_id: str) -> None:
    # 1) User
    user_email = _determine_user_email(db, br, getattr(rep, "user_email", None))
    if user_email:
        try:
            subject = "Ihr persönlicher KI‑Status‑Report ist fertig"
            body_html = render_report_ready_email(recipient="user", pdf_url=pdf_url)
            attachments = []
            if pdf_bytes and not pdf_url:
                attachments.append({
                    "filename": f"KI-Status-Report-{getattr(rep,'id', None) or 'report'}.pdf",
                    "content": pdf_bytes,
                    "mimetype": "application/pdf"
                })
            log.debug("[%s] MAIL_USER to=%s attach_pdf=%s link=%s",
                      run_id, _mask_email(user_email), bool(pdf_bytes and not pdf_url), bool(pdf_url))
            ok, err = send_mail(user_email, subject, body_html, text=None, attachments=attachments)
            if ok and hasattr(rep, "email_sent_user"):
                rep.email_sent_user = True
            if not ok and hasattr(rep, "email_error_user"):
                rep.email_error_user = err or "send_mail returned False"
        except Exception as exc:
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = str(exc)
            log.warning("[%s] MAIL_USER failed: %s", run_id, exc)

    # 2) Admin(s)
    admins = _admin_recipients()
    if admins:
        try:
            subject = "Kopie: KI‑Status‑Report (inkl. Briefing)"
            body_html = render_report_ready_email(recipient="admin", pdf_url=pdf_url)
            attachments = []
            
            # Briefing-JSON
            try:
                bjson = json.dumps(getattr(br, "answers", {}) or {}, ensure_ascii=False, indent=2).encode("utf-8")
                attachments.append({
                    "filename": f"briefing-{br.id}.json",
                    "content": bjson,
                    "mimetype": "application/json"
                })
            except Exception:
                pass
            
            # PDF
            if pdf_bytes and not pdf_url:
                attachments.append({
                    "filename": f"KI-Status-Report-{getattr(rep,'id', None) or 'report'}.pdf",
                    "content": pdf_bytes,
                    "mimetype": "application/pdf"
                })
            
            any_ok = False
            for addr in admins:
                log.debug("[%s] MAIL_ADMIN to=%s attach_pdf=%s link=%s",
                          run_id, _mask_email(addr), bool(pdf_bytes and not pdf_url), bool(pdf_url))
                ok, err = send_mail(addr, subject, body_html, text=None, attachments=attachments)
                any_ok = any_ok or ok
                if not ok and hasattr(rep, "email_error_admin"):
                    prev = getattr(rep, "email_error_admin", None) or ""
                    rep.email_error_admin = (prev + f"; {addr}: {err}").strip("; ")
            
            if any_ok and hasattr(rep, "email_sent_admin"):
                rep.email_sent_admin = True
                
        except Exception as exc:
            if hasattr(rep, "email_error_admin"):
                rep.email_error_admin = str(exc)
            log.warning("[%s] MAIL_ADMIN failed: %s", run_id, exc)

def analyze_briefing(db: Session, briefing_id: int, run_id: str) -> Tuple[int, str, Dict[str, Any]]:
    br = db.get(Briefing, briefing_id)
    if not br:
        raise ValueError("Briefing not found")
    
    result = build_full_report_html(br, run_id=run_id)
    
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

def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    """Erzeugt Analyse → Report (pending→done/failed) → E‑Mails (User + Admin)."""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    rep: Optional[Report] = None
    
    try:
        # 1. Analyse erstellen
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
        br = db.get(Briefing, briefing_id)
        log.info("[%s] analysis_created id=%s briefing_id=%s user_id=%s",
                 run_id, an_id, briefing_id, getattr(br, "user_id", None))

        # 2. Report anlegen (pending)
        rep = Report(
            user_id=br.user_id if br else None,
            briefing_id=briefing_id,
            analysis_id=an_id,
            created_at=datetime.now(timezone.utc),
        )
        
        if hasattr(rep, "user_email"):
            user_email = _determine_user_email(db, br, email)
            rep.user_email = user_email or ""
        if hasattr(rep, "task_id"):
            rep.task_id = f"local-{uuid.uuid4()}"
        if hasattr(rep, "status"):
            rep.status = "pending"
        
        db.add(rep)
        db.commit()
        db.refresh(rep)
        log.info("[%s] report_pending id=%s", run_id, getattr(rep, "id", None))

        # 3. PDF rendern
        if DBG_PDF:
            log.debug("[%s] pdf_render start", run_id)
        
        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id})
        pdf_url = pdf_info.get("pdf_url")
        pdf_bytes = pdf_info.get("pdf_bytes")
        pdf_error = pdf_info.get("error")
        
        if DBG_PDF:
            log.debug("[%s] pdf_render done url=%s bytes_len=%s error=%s",
                     run_id, bool(pdf_url), len(pdf_bytes or b""), pdf_error)

        # ✅ Prüfe ob PDF erfolgreich
        if not pdf_url and not pdf_bytes:
            error_msg = f"PDF generation failed: {pdf_error or 'no output returned'}"
            log.error("[%s] %s", run_id, error_msg)
            
            if hasattr(rep, "status"):
                rep.status = "failed"
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = error_msg
            if hasattr(rep, "updated_at"):
                rep.updated_at = datetime.now(timezone.utc)
            
            db.add(rep)
            db.commit()
            db.refresh(rep)
            
            log.info("[%s] report_failed id=%s reason=pdf_generation_failed",
                     run_id, getattr(rep, "id", None))
            raise ValueError(error_msg)

        # 4. Report aktualisieren (nur bei Erfolg!)
        if hasattr(rep, "pdf_url"):
            rep.pdf_url = pdf_url
        if hasattr(rep, "pdf_bytes_len") and pdf_bytes:
            rep.pdf_bytes_len = len(pdf_bytes)
        if hasattr(rep, "status"):
            rep.status = "done"
        if hasattr(rep, "updated_at"):
            rep.updated_at = datetime.now(timezone.utc)
        
        db.add(rep)
        db.commit()
        db.refresh(rep)
        
        log.info("[%s] report_done id=%s url=%s bytes=%s",
                 run_id, getattr(rep, "id", None), bool(pdf_url), len(pdf_bytes or b""))

        # 5. E-Mails versenden
        try:
            _send_emails(db, rep, br, pdf_url, pdf_bytes, run_id=run_id)
            if hasattr(rep, "updated_at"):
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep)
            db.commit()
        except Exception as exc:
            log.warning("[%s] email_dispatch_failed: %s", run_id, exc)

    except Exception as exc:
        log.exception("[%s] run_async_failed briefing_id=%s err=%s", run_id, briefing_id, exc)
        
        # Report als failed markieren
        try:
            if rep is None:
                r = db.query(Report).filter(Report.briefing_id == briefing_id).order_by(Report.id.desc()).first()
            else:
                r = rep
            
            if r:
                if hasattr(r, "status"):
                    r.status = "failed"
                if hasattr(r, "updated_at"):
                    r.updated_at = datetime.now(timezone.utc)
                db.add(r)
                db.commit()
                log.info("[%s] report_marked_failed id=%s", run_id, getattr(r, "id", None))
                
        except Exception as inner:
            log.warning("[%s] mark_failed_exception: %s", run_id, inner)
            
    finally:
        db.close()
