# -*- coding: utf-8 -*-
from __future__ import annotations
"""
gpt_analyze.py – v4.5 (Gold-Standard+ with Ensemble Evaluators)
==============================================================
Drop-in Replacement auf Basis v4.4 mit folgenden Erweiterungen:

- ✅ **Ensemble‑Evaluatoren** (Compliance, Innovation, Effizienz) als optionale Module.
- ✅ Liefert zusätzliche HTML-Blöcke:
     • ENSEMBLE_SUMMARY_HTML – Scores & Gewichte als Tabelle
     • ENSEMBLE_ACTIONS_HTML – priorisierte Maßnahmenliste
     • ENSEMBLE_CONFLICTS_HTML – erkannte Zielkonflikte
- ✅ Scores & Content bleiben rückwärtskompatibel (alle bisherigen Keys vorhanden).
- ✅ Fehlerrobust: Falls Evaluator-Module fehlen, läuft alles wie in v4.4 weiter.

Hinweis: Dieses File importiert optionale Module aus `services.evaluators.*`. Sind diese
nicht vorhanden, wird der Ensemble-Teil still übersprungen.
"""
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from core.db import SessionLocal
from models import Analysis, Briefing, Report, User
from services.report_renderer import render
from services.pdf_client import render_pdf_from_html
from services.email import send_mail
from services.email_templates import render_report_ready_email
from settings import settings

# ---------------- optional: bestehende Services (failsafe) -------------------
def _pass_through(x):  # noqa: D401
    """No-op Normalizer."""
    return x

try:
    from services.answers_normalizer import normalize_answers  # type: ignore
except Exception:  # pragma: no cover - optional
    normalize_answers = _pass_through  # type: ignore

try:
    from services.research_pipeline import run_research  # type: ignore
except Exception:  # pragma: no cover - optional
    run_research = None  # type: ignore

try:
    from services.kpi_builder import build_kpis  # type: ignore
except Exception:  # pragma: no cover - optional
    build_kpis = None  # type: ignore

try:
    from services.playbooks import build_playbooks  # type: ignore
except Exception:  # pragma: no cover - optional
    build_playbooks = None  # type: ignore

# ------------------- NEW: Ensemble Evaluators (optional) ---------------------
try:
    from services.evaluators.ensemble import run_ensemble  # type: ignore
except Exception:  # pragma: no cover - optional
    run_ensemble = None  # type: ignore

# ----------------------------------------------------------------------------
# Konfiguration
# ----------------------------------------------------------------------------
log = logging.getLogger(__name__)

OPENAI_API_KEY = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = getattr(settings, "OPENAI_MODEL", None) or os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))

DBG_PDF = (os.getenv("DEBUG_LOG_PDF_INFO", "1") == "1")
DBG_MASK_EMAILS = (os.getenv("DEBUG_MASK_EMAILS", "1") == "1")

# Feature Flags
ENABLE_NSFW_FILTER = (os.getenv("ENABLE_NSFW_FILTER", "1") == "1")
ENABLE_QUALITY_GATES = (os.getenv("ENABLE_QUALITY_GATES", "1") == "1")
ENABLE_REALISTIC_SCORES = (os.getenv("ENABLE_REALISTIC_SCORES", "1") == "1")
ENABLE_LLM_CONTENT = (os.getenv("ENABLE_LLM_CONTENT", "1") == "1")

# Research-Fallback: falls interne Research-Module verfügbar sind, nutzen wir sie
USE_INTERNAL_RESEARCH = (os.getenv("USE_INTERNAL_RESEARCH", "1") == "1")

# ----------------------------------------------------------------------------
# NSFW Filter
# ----------------------------------------------------------------------------
NSFW_KEYWORDS = {
    'porn', 'xxx', 'sex', 'nude', 'naked', 'adult', 'nsfw', 'erotic',
    'webcam', 'escort', 'dating', 'hookup', 'milf', 'teen', 'amateur',
    'porno', 'nackt', 'fick', 'muschi', 'schwanz', 'titten',
    'chudai', 'chut', 'lund', 'gaand', 'bhabhi', 'desi',
    'onlyfans', 'patreon', 'leaked', 'torrent', 'pirate', 'crack'
}
NSFW_DOMAINS = {
    'xvideos.com', 'pornhub.com', 'xnxx.com', 'redtube.com', 'youporn.com',
    'onlyfans.com', 'fansly.com', 'manyvids.com'
}


def _is_nsfw_content(url: str, title: str, description: str) -> bool:
    if not ENABLE_NSFW_FILTER:
        return False
    url_lower = url.lower()
    for domain in NSFW_DOMAINS:
        if domain in url_lower:
            return True
    combined_text = f"{title} {description}".lower()
    for keyword in NSFW_KEYWORDS:
        if keyword in combined_text:
            return True
    return False


def _filter_nsfw_from_research(research_data: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_NSFW_FILTER:
        return research_data
    filtered_data: Dict[str, Any] = {'tools': [], 'funding': []}
    for tool in research_data.get('tools', []):
        url = tool.get('url', '')
        title = tool.get('title', '')
        description = tool.get('description', '')
        if not _is_nsfw_content(url, title, description):
            filtered_data['tools'].append(tool)
    for fund in research_data.get('funding', []):
        url = fund.get('url', '')
        title = fund.get('title', '')
        description = fund.get('description', '')
        if not _is_nsfw_content(url, title, description):
            filtered_data['funding'].append(fund)
    return filtered_data

# ----------------------------------------------------------------------------
# SCORE CALCULATION (wie v4.4)
# ----------------------------------------------------------------------------
def _map_german_to_english_keys(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Map deutsche Briefing-Keys zu englischen Keys für Score-Berechnung."""
    mapped: Dict[str, Any] = {}
    # Governance
    if answers.get('roadmap_vorhanden') == 'ja':
        mapped['ai_strategy'] = 'yes'
    elif answers.get('roadmap_vorhanden') == 'teilweise':
        mapped['ai_strategy'] = 'in_progress'
    elif answers.get('vision_3_jahre') or answers.get('ki_ziele'):
        mapped['ai_strategy'] = 'in_progress'
    else:
        mapped['ai_strategy'] = 'no'
    if answers.get('governance_richtlinien') in ['ja', 'alle']:
        mapped['ai_responsible'] = 'yes'
    elif answers.get('governance_richtlinien') == 'teilweise':
        mapped['ai_responsible'] = 'shared'
    else:
        mapped['ai_responsible'] = 'no'
    budget_map = {
        'unter_2000': 'under_10k',
        '2000_10000': 'under_10k',
        '10000_50000': '10k-50k',
        '50000_100000': '50k-100k',
        'ueber_100000': 'over_100k'
    }
    mapped['budget'] = budget_map.get(answers.get('investitionsbudget', ''), 'none')
    ki_ziele = answers.get('ki_ziele', [])
    mapped['goals'] = ', '.join(ki_ziele) if ki_ziele else answers.get('strategische_ziele', '')
    anwendungsfaelle = answers.get('anwendungsfaelle', [])
    ki_projekte = answers.get('ki_projekte', '')
    mapped['use_cases'] = (', '.join(anwendungsfaelle) + '. ' + ki_projekte) if anwendungsfaelle else ki_projekte
    # Security
    mapped['gdpr_aware'] = 'yes' if (answers.get('datenschutz') is True or answers.get('datenschutzbeauftragter') == 'ja') else 'no'
    if answers.get('technische_massnahmen') == 'alle':
        mapped['data_protection'] = 'comprehensive'
    elif answers.get('technische_massnahmen'):
        mapped['data_protection'] = 'basic'
    else:
        mapped['data_protection'] = 'none'
    mapped['risk_assessment'] = 'yes' if answers.get('folgenabschaetzung') == 'ja' else 'no'
    trainings = answers.get('trainings_interessen', [])
    mapped['security_training'] = 'regular' if trainings and len(trainings) > 2 else ('occasional' if trainings else 'no')
    # Value
    if answers.get('vision_prioritaet') in ['marktfuehrerschaft', 'wachstum']:
        mapped['roi_expected'] = 'high'
    elif answers.get('vision_prioritaet'):
        mapped['roi_expected'] = 'medium'
    else:
        mapped['roi_expected'] = 'low'
    mapped['measurable_goals'] = 'yes' if (answers.get('strategische_ziele') or answers.get('ki_ziele')) else 'no'
    mapped['pilot_planned'] = 'yes' if answers.get('pilot_bereich') else ('in_progress' if answers.get('ki_projekte') else 'no')
    # Enablement
    kompetenz_map = {'hoch': 'advanced', 'mittel': 'intermediate', 'niedrig': 'basic', 'keine': 'none'}
    mapped['ai_skills'] = kompetenz_map.get(answers.get('ki_kompetenz', ''), 'none')
    mapped['training_budget'] = 'yes' if answers.get('zeitbudget') in ['ueber_10', '5_10'] else ('planned' if answers.get('zeitbudget') else 'no')
    change = answers.get('change_management', '')
    mapped['change_management'] = 'yes' if change == 'hoch' else ('planned' if change in ['mittel', 'niedrig'] else 'no')
    innovationsprozess = answers.get('innovationsprozess', '')
    mapped['innovation_culture'] = 'strong' if innovationsprozess in ['mitarbeitende', 'alle'] else ('moderate' if innovationsprozess else 'weak')
    return mapped


def _calculate_realistic_score(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Berechnet realistische Scores (0–100); Gesamt = Durchschnitt der vier Säulen."""
    if not ENABLE_REALISTIC_SCORES:
        return {'scores': {'governance': 0, 'security': 0, 'value': 0, 'enablement': 0, 'overall': 0}, 'details': {}, 'total': 0}
    m = _map_german_to_english_keys(answers)
    gov = sec = val = ena = 0
    details = {'governance': [], 'security': [], 'value': [], 'enablement': []}
    # Governance
    if m.get('ai_strategy') in ['yes', 'in_progress']:
        gov += 8; details['governance'].append("✅ KI-Strategie (+8)")
    else:
        details['governance'].append("❌ Keine KI-Strategie (-8)")
    if m.get('ai_responsible') in ['yes', 'shared']:
        gov += 7; details['governance'].append("✅ KI-Verantwortlicher (+7)")
    else:
        details['governance'].append("❌ Kein KI-Verantwortlicher (-7)")
    budget = m.get('budget', '')
    if budget in ['10k-50k', '50k-100k', 'over_100k']:
        gov += 6; details['governance'].append(f"✅ Budget: {budget} (+6)")
    elif budget == 'under_10k':
        gov += 3; details['governance'].append("⚠️ Budget: unter 10k (+3)")
    else:
        details['governance'].append("❌ Kein Budget (-6)")
    if m.get('goals') or m.get('use_cases'):
        gov += 4; details['governance'].append("✅ KI-Ziele definiert (+4)")
    else:
        details['governance'].append("❌ Keine KI-Ziele (-4)")
    # Security
    if m.get('gdpr_aware') == 'yes':
        sec += 8; details['security'].append("✅ DSGVO-Awareness (+8)")
    else:
        details['security'].append("❌ Keine DSGVO-Awareness (-8)")
    if m.get('data_protection') in ['comprehensive', 'basic']:
        sec += 7; details['security'].append("✅ Datenschutz-Maßnahmen (+7)")
    else:
        details['security'].append("❌ Keine Datenschutz-Maßnahmen (-7)")
    if m.get('risk_assessment') == 'yes':
        sec += 6; details['security'].append("✅ Risiko-Assessment (+6)")
    else:
        details['security'].append("❌ Kein Risiko-Assessment (-6)")
    if m.get('security_training') in ['regular', 'occasional']:
        sec += 4; details['security'].append("✅ Sicherheits-Training (+4)")
    else:
        details['security'].append("❌ Kein Training (-4)")
    # Value
    u = m.get('use_cases', '')
    if u and len(u) > 50:
        val += 8; details['value'].append("✅ Use Cases definiert (+8)")
    elif u:
        val += 4; details['value'].append("⚠️ Use Cases ansatzweise (+4)")
    else:
        details['value'].append("❌ Keine Use Cases (-8)")
    roi = m.get('roi_expected', '')
    if roi in ['high', 'medium']:
        val += 7; details['value'].append(f"✅ ROI-Erwartung: {roi} (+7)")
    elif roi == 'low':
        val += 3; details['value'].append("⚠️ ROI niedrig (+3)")
    else:
        details['value'].append("❌ Keine ROI-Erwartung (-7)")
    if m.get('measurable_goals') == 'yes':
        val += 6; details['value'].append("✅ Messbare Ziele (+6)")
    else:
        details['value'].append("❌ Keine messbaren Ziele (-6)")
    if m.get('pilot_planned') in ['yes', 'in_progress']:
        val += 4; details['value'].append("✅ Pilot geplant (+4)")
    else:
        details['value'].append("❌ Kein Pilot (-4)")
    # Enablement
    skills = m.get('ai_skills', '')
    if skills in ['advanced', 'intermediate']:
        ena += 8; details['enablement'].append(f"✅ Skills: {skills} (+8)")
    elif skills == 'basic':
        ena += 4; details['enablement'].append("⚠️ Basis-Skills (+4)")
    else:
        details['enablement'].append("❌ Keine Skills (-8)")
    if m.get('training_budget') in ['yes', 'planned']:
        ena += 7; details['enablement'].append("✅ Training-Budget (+7)")
    else:
        details['enablement'].append("❌ Kein Training-Budget (-7)")
    if m.get('change_management') == 'yes':
        ena += 6; details['enablement'].append("✅ Change-Management (+6)")
    else:
        details['enablement'].append("❌ Kein Change-Management (-6)")
    culture = m.get('innovation_culture', '')
    if culture in ['strong', 'moderate']:
        ena += 4; details['enablement'].append(f"✅ Kultur: {culture} (+4)")
    else:
        details['enablement'].append("❌ Schwache Kultur (-4)")
    scores = {
        'governance': min(gov, 25) * 4,
        'security': min(sec, 25) * 4,
        'value': min(val, 25) * 4,
        'enablement': min(ena, 25) * 4,
        'overall': round((min(gov, 25) + min(sec, 25) + min(val, 25) + min(ena, 25)) * 4 / 4)
    }
    log.info("📊 REALISTIC SCORES v4.5: Gov=%s Sec=%s Val=%s Ena=%s Overall=%s",
             scores['governance'], scores['security'], scores['value'], scores['enablement'], scores['overall'])
    return {'scores': scores, 'details': details, 'total': scores['overall']}

# ----------------------------------------------------------------------------
# LLM Content Generation (wie v4.4)
# ----------------------------------------------------------------------------
def _call_openai(prompt: str, system_prompt: str = "Du bist ein KI-Berater.",
                 temperature: Optional[float] = None, max_tokens: int = 2000) -> Optional[str]:
    """Zentrale OpenAI Chat Completions API (synchron)."""
    if not OPENAI_API_KEY:
        log.error("❌ OPENAI_API_KEY not set")
        return None
    if temperature is None:
        temperature = OPENAI_TEMPERATURE
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=OPENAI_TIMEOUT,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        log.debug("✅ OpenAI success (%d chars)", len(content))
        return content
    except Exception as exc:
        log.error("❌ OpenAI error: %s", exc)
        return None


def _clean_html(s: str) -> str:
    if not s:
        return s
    s = s.replace("```html", "").replace("```", "").strip()
    return s


def _split_li_list_to_columns(html_list: str) -> Tuple[str, str]:
    """Splittet eine <ul>…</ul> Liste in zwei Spalten mit gleicher Itemzahl (±1)."""
    if not html_list:
        return "<ul></ul>", "<ul></ul>"
    items = re.findall(r"<li[\s>].*?</li>", html_list, flags=re.DOTALL | re.IGNORECASE)
    if not items:
        lines = [ln.strip() for ln in re.split(r"<br\s*/?>|\n", html_list) if ln.strip()]
        items = [f"<li>{ln}</li>" for ln in lines]
    mid = (len(items) + 1) // 2
    left = "<ul>" + "".join(items[:mid]) + "</ul>"
    right = "<ul>" + "".join(items[mid:]) + "</ul>"
    return left, right


def _generate_content_section(section_name: str, briefing: Dict[str, Any],
                              scores: Dict[str, Any]) -> str:
    """Generiert eine Content-Section per LLM und liefert validen HTML-String."""
    if not ENABLE_LLM_CONTENT:
        return f"<p><em>[{section_name} – LLM disabled]</em></p>"
    branche = briefing.get('branche', 'Unternehmen')
    hauptleistung = briefing.get('hauptleistung', '')
    ki_ziele = briefing.get('ki_ziele', [])
    ki_projekte = briefing.get('ki_projekte', '')
    vision = briefing.get('vision_3_jahre', '')
    
    # ✅ FIX: Alle 4 Score-Dimensionen für bessere Prompt-Qualität
    overall = scores.get('overall', 0)
    governance = scores.get('governance', 0)
    security = scores.get('security', 0)
    value = scores.get('value', 0)
    enablement = scores.get('enablement', 0)
    
    prompts = {
        'executive_summary': f"""Erstelle eine prägnante Executive Summary für ein {branche}-Unternehmen.
Hauptleistung: {hauptleistung}
KI-Ziele: {', '.join(ki_ziele) if ki_ziele else 'nicht definiert'}
Vision: {vision}
KI-Reifegrad: Gesamt {overall}/100 • Governance {governance}/100 • Sicherheit {security}/100 • Nutzen {value}/100 • Befähigung {enablement}/100
Schreibe 4–6 Sätze.
Format: **VALIDE HTML** nur mit <p>-Tags. **Keine Überschriften/Markdown**.""",
        'quick_wins': f"""Liste 4–6 **konkrete Quick Wins** (0–90 Tage) für {branche}.
Jeder Quick Win: Titel, 1–2 Sätze Nutzen, realistische **Ersparnis/Monat (h)**.
Bezug: Hauptleistung: {hauptleistung}; Projekte: {ki_projekte or 'keine'}.
Format: VALIDE HTML, **genau eine** ungeordnete Liste:
<ul>
  <li><strong>Titel:</strong> Beschreibung. <em>Ersparnis: 5 h/Monat</em></li>
</ul>""",
        'roadmap': f"""Erstelle eine **90‑Tage‑Roadmap** (0–30 Test; 31–60 Pilot; 61–90 Rollout).
Für jede Phase 3–5 Meilensteine (konkret, überprüfbar).
Kontext: Ziele={', '.join(ki_ziele) if ki_ziele else 'Effizienz'}, Vision={vision or '—'}.
Format: **VALIDE HTML** mit <h4>Phase …</h4> und <ul>…</ul>.""",
        'business_roi': f"""Erstelle eine **ROI & Payback**-Tabelle (Jahr 1) für {branche}.
Annahmen: Stundensatz 60 €/h (falls unklar), Investition 2.000–10.000 € (einmalig),
Ersparnis = Summe Quick Wins * 12 * Stundensatz (falls nicht vorhanden: 18 h/Monat Beispiel).
Format: **VALIDE HTML-TABELLE** (2 Spalten: Kennzahl, Wert).""",
        'business_costs': f"""Erstelle eine **Kostenübersicht Jahr 1**.
Positionen: Initiale Investition, Lizenzen/Hosting, Schulung/Change, Betrieb (Schätzung).
Format: **VALIDE HTML-TABELLE** (2 Spalten: Position, Betrag).""",
        'recommendations': f"""Formuliere 5–7 **Handlungsempfehlungen** mit Priorität [H/M/N] und Zeitrahmen (30/60/90 Tage).
Kontext: Branche {branche}, Score Gesamt {overall}/100 (Governance {governance}/100, Sicherheit {security}/100, Nutzen {value}/100, Befähigung {enablement}/100).
Format: VALIDE HTML-Liste: <ul><li><strong>[H]</strong> Maßnahme – <em>60 Tage</em></li></ul>""",
        'risks': f"""Erstelle eine **Risikomatrix** (5–7 Risiken) für {branche}.
Spalten: Risiko | Eintritt (niedrig/mittel/hoch) | Auswirkung | Mitigation.
Format: VALIDE HTML-TABELLE (<table> mit <thead>/<tbody>).""",
        'gamechanger': f"""Skizziere einen **Gamechanger‑Use Case** für {branche}.
Teile: (1) 3–4 Sätze Idee, (2) 3 Vorteile (Liste), (3) 3 erste Schritte (Liste).
Kontext: Hauptleistung {hauptleistung}, Vision {vision or '—'}.
Format: VALIDE HTML mit <h4>, <p>, <ul>."""
    }
    prompt = prompts.get(section_name)
    if not prompt:
        return f"<p><em>[{section_name} – no template]</em></p>"
    log.info("🤖 Generating %s...", section_name)
    content = _call_openai(
        prompt=prompt,
        system_prompt="Du bist ein Senior‑KI‑Berater. Antworte ausschließlich mit validem HTML (kein Markdown).",
        max_tokens=2000,
    )
    if not content:
        return f"<p><em>[{section_name} – generation failed]</em></p>"
    return _clean_html(content)


def _generate_content_sections(briefing: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, str]:
    """Generiert alle Content‑Sections und liefert Dict von Template-Key → HTML."""
    sections: Dict[str, str] = {}
    sections['EXECUTIVE_SUMMARY_HTML'] = _generate_content_section('executive_summary', briefing, scores)
    qw_html = _generate_content_section('quick_wins', briefing, scores)
    left, right = _split_li_list_to_columns(qw_html)
    sections['QUICK_WINS_HTML_LEFT'] = left
    sections['QUICK_WINS_HTML_RIGHT'] = right
    sections['PILOT_PLAN_HTML'] = _generate_content_section('roadmap', briefing, scores)
    sections['ROI_HTML'] = _generate_content_section('business_roi', briefing, scores)
    sections['COSTS_OVERVIEW_HTML'] = _generate_content_section('business_costs', briefing, scores)
    sections['RISKS_HTML'] = _generate_content_section('risks', briefing, scores)
    sections['GAMECHANGER_HTML'] = _generate_content_section('gamechanger', briefing, scores)
    sections['RECOMMENDATIONS_HTML'] = _generate_content_section('recommendations', briefing, scores)
    return sections

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _mask_email(addr: Optional[str]) -> str:
    if not addr or not DBG_MASK_EMAILS:
        return addr or ""
    try:
        name, domain = addr.split("@", 1)
        return f"{name[:3]}***@{domain}" if len(name) > 3 else f"{name}***@{domain}"
    except Exception:
        return "***"


def _admin_recipients() -> List[str]:
    emails: List[str] = []
    raw1 = getattr(settings, "ADMIN_EMAILS", None) or os.getenv("ADMIN_EMAILS", "")
    raw2 = getattr(settings, "REPORT_ADMIN_EMAIL", None) or os.getenv("REPORT_ADMIN_EMAIL", "")
    if raw1:
        emails.extend([e.strip() for e in raw1.split(",") if e.strip()])
    if raw2:
        emails.append(raw2.strip())
    return list(dict.fromkeys(emails))


def _determine_user_email(db: Session, briefing: Briefing, override: Optional[str]) -> Optional[str]:
    if override:
        return override
    user_id = getattr(briefing, "user_id", None)
    if user_id:
        u = db.get(User, user_id)
        if u and getattr(u, "email", ""):
            return u.email
    answers = getattr(briefing, "answers", None) or {}
    return answers.get("email") or answers.get("kontakt_email")


def _send_emails(db: Session, rep: Report, br: Briefing,
                 pdf_url: Optional[str], pdf_bytes: Optional[bytes], run_id: str) -> None:
    # User mail
    user_email = _determine_user_email(db, br, getattr(rep, "user_email", None))
    if user_email:
        try:
            subject = "Ihr KI‑Status‑Report ist fertig"
            body_html = render_report_ready_email(recipient="user", pdf_url=pdf_url)
            attachments = []
            if pdf_bytes and not pdf_url:
                attachments.append({"filename": f"KI-Status-Report-{getattr(rep,'id', None)}.pdf",
                                    "content": pdf_bytes, "mimetype": "application/pdf"})
            log.debug("[%s] MAIL_USER to=%s", run_id, _mask_email(user_email))
            ok, err = send_mail(user_email, subject, body_html, text=None, attachments=attachments)
            if ok and hasattr(rep, "email_sent_user"):
                rep.email_sent_user = True
            if not ok and hasattr(rep, "email_error_user"):
                rep.email_error_user = err or "send_mail failed"
        except Exception as exc:
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = str(exc)
            log.warning("[%s] MAIL_USER failed: %s", run_id, exc)
    # Admin copies
    admins = _admin_recipients()
    if admins:
        try:
            subject = "Kopie: KI‑Status‑Report"
            body_html = render_report_ready_email(recipient="admin", pdf_url=pdf_url)
            attachments = []
            try:
                bjson = json.dumps(getattr(br, "answers", {}) or {}, ensure_ascii=False, indent=2).encode("utf-8")
                attachments.append({"filename": f"briefing-{br.id}.json", "content": bjson, "mimetype": "application/json"})
            except Exception:
                pass
            if pdf_bytes and not pdf_url:
                attachments.append({"filename": f"KI-Status-Report-{getattr(rep,'id', None)}.pdf",
                                    "content": pdf_bytes, "mimetype": "application/pdf"})
            any_ok = False
            for addr in admins:
                log.debug("[%s] MAIL_ADMIN to=%s", run_id, _mask_email(addr))
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

# ----------------------------------------------------------------------------
# MAIN ANALYSIS
# ----------------------------------------------------------------------------
def analyze_briefing(db: Session, briefing_id: int, run_id: str) -> tuple[int, str, Dict[str, Any]]:
    """
    1) Antworten normalisieren
    2) Scores berechnen
    3) LLM‑Content generieren (kapitelweise; Template‑kompatibel)
    4) Optional Ensemble, Research, KPI, Playbooks mergen
    5) HTML rendern & Analysis persistieren
    """
    br = db.get(Briefing, briefing_id)
    if not br:
        raise ValueError("Briefing not found")

    raw_answers: Dict[str, Any] = getattr(br, "answers", {}) or {}
    answers = normalize_answers(raw_answers)

    # Scores
    log.info("[%s] Calculating realistic scores (v4.5)...", run_id)
    score_wrap = _calculate_realistic_score(answers)
    scores = score_wrap['scores']

    # LLM‑Content
    log.info("[%s] Generating content sections with LLM...", run_id)
    generated_sections = _generate_content_sections(briefing=answers, scores=scores)

    # Scores in Template-Variablen (einzeln UND als realistic_scores Dictionary)
    generated_sections['score_governance'] = scores.get('governance', 0)
    generated_sections['score_sicherheit'] = scores.get('security', 0)
    generated_sections['score_nutzen'] = scores.get('value', 0)
    generated_sections['score_befaehigung'] = scores.get('enablement', 0)
    generated_sections['score_gesamt'] = scores.get('overall', 0)
    
    # ✅ FIX: realistic_scores Format für Template hinzufügen
    generated_sections['realistic_scores'] = {
        'governance': scores.get('governance', 0),
        'security': scores.get('security', 0),
        'value': scores.get('value', 0),
        'enablement': scores.get('enablement', 0),
        'overall': scores.get('overall', 0)
    }

    # NEW: Ensemble Evaluators (optional)
    if run_ensemble:
        try:
            log.info("[%s] Running ensemble evaluators...", run_id)
            ens = run_ensemble(answers)
            if isinstance(ens, dict):
                generated_sections.update({
                    'ENSEMBLE_SUMMARY_HTML': ens.get('summary_html', ''),
                    'ENSEMBLE_ACTIONS_HTML': ens.get('actions_html', ''),
                    'ENSEMBLE_CONFLICTS_HTML': ens.get('conflicts_html', ''),
                })
        except Exception as exc:  # pragma: no cover - optional
            log.warning("[%s] Ensemble evaluators failed: %s", run_id, exc)

    # Optionale Zusatzblöcke (failsafe)
    if build_kpis:
        try:
            generated_sections['KPIS_HTML'] = build_kpis(answers)
        except Exception as exc:
            log.warning("[%s] KPI build failed: %s", run_id, exc)
    if build_playbooks:
        try:
            generated_sections['PLAYBOOKS_HTML'] = build_playbooks(answers)
        except Exception as exc:
            log.warning("[%s] Playbooks build failed: %s", run_id, exc)

    # Research (optional intern) oder via Fetchers
    use_fetchers = True
    if USE_INTERNAL_RESEARCH and run_research:
        try:
            log.info("[%s] Running internal research...", run_id)
            research_blocks = run_research(answers)  # liefert TOOLS_HTML, FOERDERPROGRAMME_HTML, QUELLEN_HTML, last_updated
            generated_sections.update(research_blocks or {})
            use_fetchers = False
        except Exception as exc:
            log.warning("[%s] Internal research failed, falling back to fetchers: %s", run_id, exc)
            use_fetchers = True

    # ✅ FIX: Meta VOR render() vorbereiten
    meta = {
        'scores': scores,
        'score_details': score_wrap.get('details', {}),
        'realistic_scores': generated_sections['realistic_scores']
    }

    # Render MIT scores/meta
    log.info("[%s] Rendering final HTML...", run_id)
    result = render(
        br,
        run_id=run_id,
        generated_sections=generated_sections,
        use_fetchers=use_fetchers,
        scores=scores,  # ✅ FIX: scores explizit übergeben
        meta=meta  # ✅ FIX: meta explizit übergeben
    )

    # Meta anreichern (für Rückgabewert)
    result['meta'] = result.get('meta', {})
    result['meta'].update(meta)
    result['meta'].update(generated_sections)

    # Quality gate
    if ENABLE_QUALITY_GATES:
        issues: List[str] = []
        if not generated_sections.get('EXECUTIVE_SUMMARY_HTML'):
            issues.append("Missing EXECUTIVE_SUMMARY_HTML")
        if scores.get('overall', 0) == 0:
            issues.append("Score overall is zero")
        if issues:
            log.warning("[%s] Quality warnings: %s", run_id, issues)
            result['meta']['quality_warnings'] = issues

    # Persist
    an = Analysis(
        user_id=br.user_id,
        briefing_id=briefing_id,
        html=result["html"],
        meta=result["meta"],
        created_at=datetime.now(timezone.utc),
    )
    db.add(an); db.commit(); db.refresh(an)
    log.info("[%s] ✅ Analysis created (v4.5): id=%s", run_id, an.id)
    return an.id, result["html"], result["meta"]


def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    """Asynchroner Runner für Analyse und PDF-Erstellung inkl. E‑Mail‑Versand."""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    rep: Optional[Report] = None
    try:
        log.info("[%s] 🚀 Starting analysis v4.5 for briefing_id=%s", run_id, briefing_id)
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
        br = db.get(Briefing, briefing_id)
        log.info("[%s] analysis_created id=%s briefing_id=%s user_id=%s", run_id, an_id, briefing_id, getattr(br, 'user_id', None))
        rep = Report(user_id=br.user_id if br else None, briefing_id=briefing_id, analysis_id=an_id, created_at=datetime.now(timezone.utc))
        if hasattr(rep, "user_email"):
            rep.user_email = _determine_user_email(db, br, email) or ""
        if hasattr(rep, "task_id"):
            rep.task_id = f"local-{uuid.uuid4()}"
        if hasattr(rep, "status"):
            rep.status = "pending"
        db.add(rep); db.commit(); db.refresh(rep)
        log.info("[%s] report_pending id=%s", run_id, getattr(rep, 'id', None))

        # PDF
        if DBG_PDF:
            log.debug("[%s] pdf_render start", run_id)
        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id})
        pdf_url = pdf_info.get("pdf_url"); pdf_bytes = pdf_info.get("pdf_bytes"); pdf_error = pdf_info.get("error")
        if DBG_PDF:
            log.debug("[%s] pdf_render done url=%s bytes=%s error=%s", run_id, bool(pdf_url), len(pdf_bytes or b''), pdf_error)

        if not pdf_url and not pdf_bytes:
            error_msg = f"PDF failed: {pdf_error or 'no output'}"
            log.error("[%s] %s", run_id, error_msg)
            if hasattr(rep, "status"):
                rep.status = "failed"
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = error_msg
            if hasattr(rep, "updated_at"):
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep); db.commit()
            raise ValueError(error_msg)

        if hasattr(rep, "pdf_url"):
            rep.pdf_url = pdf_url
        if hasattr(rep, "pdf_bytes_len") and pdf_bytes:
            rep.pdf_bytes_len = len(pdf_bytes)
        if hasattr(rep, "status"):
            rep.status = "done"
        if hasattr(rep, "updated_at"):
            rep.updated_at = datetime.now(timezone.utc)
        db.add(rep); db.commit(); db.refresh(rep)
        log.info("[%s] ✅ report_done id=%s url=%s bytes=%s (v4.5)", run_id, getattr(rep, 'id', None), bool(pdf_url), len(pdf_bytes or b''))

        try:
            _send_emails(db, rep, br, pdf_url, pdf_bytes, run_id=run_id)
            db.add(rep); db.commit()
        except Exception as exc:
            log.warning("[%s] email error: %s", run_id, exc)

    except Exception as exc:
        log.error("[%s] ❌ Analysis failed: %s", run_id, exc, exc_info=True)
        if rep and hasattr(rep, "status"):
            rep.status = "failed"
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = str(exc)
            if hasattr(rep, "updated_at"):
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep); db.commit()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python gpt_analyze.py <briefing_id>")
        sys.exit(1)
    run_async(int(sys.argv[1]))
