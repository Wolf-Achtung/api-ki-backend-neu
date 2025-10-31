# -*- coding: utf-8 -*-
from __future__ import annotations
"""
GOLD STANDARD v4.2 – Robust Content Mapping & PDF Rendering
===========================================================

Änderungen ggü. v4.1:
- 🔁 Einheitliches Mapping der LLM-Outputs auf Template-Keys (kein leerer Content mehr)
- ✅ Executive Summary → EXECUTIVE_SUMMARY_HTML (statt EXEC_SUMMARY_HTML)
- ✅ Quick Wins: automatische 2‑Spalten‑Aufteilung (LEFT/RIGHT)
- ✅ Roadmap: ROADMAP_HTML → PILOT_PLAN_HTML
- ✅ Business Case: BUSINESS_CASE_HTML → (ROI_HTML, COSTS_OVERVIEW_HTML)
- ✅ Gamechanger-Use Case: neu generiert (GAMECHANGER_HTML)
- ✅ Risiko-Matrix (falls Fetcher nichts liefern): LLM‑Fallback (RISKS_HTML)
- ✅ Scores werden als score_* Felder in den Template‑Kontext übernommen
- ✅ Transparenztext standardisiert (transparency_text)
- 🧼 UTF‑8, PEP8, Logging, Fehlerbehandlung verbessert

Hinweis: Der eigentliche PDF-HTML-Body kommt aus dem Template (pdf_template.html).
Diese Datei sorgt lediglich dafür, dass alle Platzhalter-Keys korrekt gefüllt werden.
"""
import json
import logging
import os
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
from services.content_normalizer import normalize_and_enrich_sections  # NEW
from settings import settings

log = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# NSFW Filter
# -----------------------------------------------------------------------------
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
    filtered_data = {'tools': [], 'funding': []}
    stats = {
        'tools_total': len(research_data.get('tools', [])),
        'tools_filtered': 0,
        'funding_total': len(research_data.get('funding', [])),
        'funding_filtered': 0,
    }
    for tool in research_data.get('tools', []):
        url = tool.get('url', '')
        title = tool.get('title', '')
        description = tool.get('description', '')
        if not _is_nsfw_content(url, title, description):
            filtered_data['tools'].append(tool)
        else:
            stats['tools_filtered'] += 1
            log.warning("🚨 Filtered NSFW tool: %s...", title[:50])
    for fund in research_data.get('funding', []):
        url = fund.get('url', '')
        title = fund.get('title', '')
        description = fund.get('description', '')
        if not _is_nsfw_content(url, title, description):
            filtered_data['funding'].append(fund)
        else:
            stats['funding_filtered'] += 1
            log.warning("🚨 Filtered NSFW funding: %s...", title[:50])
    if stats['tools_filtered'] > 0 or stats['funding_filtered'] > 0:
        log.warning(
            "🚨 NSFW FILTER: Tools: %s/%s, Funding: %s/%s filtered",
            stats['tools_filtered'], stats['tools_total'],
            stats['funding_filtered'], stats['funding_total']
        )
    else:
        log.info("✅ NSFW filter passed: %s tools, %s funding clean",
                 stats['tools_total'], stats['funding_total'])
    return filtered_data

# -----------------------------------------------------------------------------
# SCORE CALCULATION (v4.1 already fixed, reused in v4.2)
# -----------------------------------------------------------------------------

def _map_german_to_english_keys(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Map deutsche Briefing-Keys zu englischen Keys für Score-Berechnung"""
    mapped = {}
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
    if anwendungsfaelle:
        mapped['use_cases'] = ', '.join(anwendungsfaelle) + '. ' + ki_projekte
    else:
        mapped['use_cases'] = ki_projekte
    # Security
    if answers.get('datenschutz') is True or answers.get('datenschutzbeauftragter') == 'ja':
        mapped['gdpr_aware'] = 'yes'
    else:
        mapped['gdpr_aware'] = 'no'
    if answers.get('technische_massnahmen') == 'alle':
        mapped['data_protection'] = 'comprehensive'
    elif answers.get('technische_massnahmen'):
        mapped['data_protection'] = 'basic'
    else:
        mapped['data_protection'] = 'none'
    mapped['risk_assessment'] = 'yes' if answers.get('folgenabschaetzung') == 'ja' else 'no'
    trainings = answers.get('trainings_interessen', [])
    if trainings and len(trainings) > 2:
        mapped['security_training'] = 'regular'
    elif trainings:
        mapped['security_training'] = 'occasional'
    else:
        mapped['security_training'] = 'no'
    # Value
    if answers.get('vision_prioritaet') in ['marktfuehrerschaft', 'wachstum']:
        mapped['roi_expected'] = 'high'
    elif answers.get('vision_prioritaet'):
        mapped['roi_expected'] = 'medium'
    else:
        mapped['roi_expected'] = 'low'
    mapped['measurable_goals'] = 'yes' if (answers.get('strategische_ziele') or answers.get('ki_ziele')) else 'no'
    if answers.get('pilot_bereich'):
        mapped['pilot_planned'] = 'yes'
    elif answers.get('ki_projekte'):
        mapped['pilot_planned'] = 'in_progress'
    else:
        mapped['pilot_planned'] = 'no'
    # Enablement
    kompetenz_map = {'hoch': 'advanced', 'mittel': 'intermediate', 'niedrig': 'basic', 'keine': 'none'}
    mapped['ai_skills'] = kompetenz_map.get(answers.get('ki_kompetenz', ''), 'none')
    if answers.get('zeitbudget') in ['ueber_10', '5_10']:
        mapped['training_budget'] = 'yes'
    elif answers.get('zeitbudget'):
        mapped['training_budget'] = 'planned'
    else:
        mapped['training_budget'] = 'no'
    change = answers.get('change_management', '')
    if change == 'hoch':
        mapped['change_management'] = 'yes'
    elif change in ['mittel', 'niedrig']:
        mapped['change_management'] = 'planned'
    else:
        mapped['change_management'] = 'no'
    innovationsprozess = answers.get('innovationsprozess', '')
    if innovationsprozess in ['mitarbeitende', 'alle']:
        mapped['innovation_culture'] = 'strong'
    elif innovationsprozess:
        mapped['innovation_culture'] = 'moderate'
    else:
        mapped['innovation_culture'] = 'weak'
    return mapped

def _calculate_realistic_score(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score-Formel (intern 0–25, Template 0–100), Gesamt = Durchschnitt.
    """
    if not ENABLE_REALISTIC_SCORES:
        return {'scores': {'governance': 0, 'security': 0, 'value': 0, 'enablement': 0, 'overall': 0},
                'details': {}, 'total': 0}
    mapped = _map_german_to_english_keys(answers)
    log.debug("🔄 Keys mapped for scoring: %d → %d", len(answers), len(mapped))

    gov = sec = val = ena = 0
    details = {'governance': [], 'security': [], 'value': [], 'enablement': []}

    # GOVERNANCE
    if mapped.get('ai_strategy') in ['yes', 'in_progress']:
        gov += 8; details['governance'].append("✅ KI-Strategie (+8)")
    else:
        details['governance'].append("❌ Keine KI-Strategie (-8)")
    if mapped.get('ai_responsible') in ['yes', 'shared']:
        gov += 7; details['governance'].append("✅ KI-Verantwortlicher (+7)")
    else:
        details['governance'].append("❌ Kein KI-Verantwortlicher (-7)")
    budget = mapped.get('budget', '')
    if budget in ['10k-50k', '50k-100k', 'over_100k']:
        gov += 6; details['governance'].append(f"✅ Budget: {budget} (+6)")
    elif budget == 'under_10k':
        gov += 3; details['governance'].append("⚠️ Budget: unter 10k (+3)")
    else:
        details['governance'].append("❌ Kein Budget (-6)")
    if mapped.get('goals') or mapped.get('use_cases'):
        gov += 4; details['governance'].append("✅ KI-Ziele definiert (+4)")
    else:
        details['governance'].append("❌ Keine KI-Ziele (-4)")

    # SECURITY
    if mapped.get('gdpr_aware') == 'yes':
        sec += 8; details['security'].append("✅ DSGVO-Awareness (+8)")
    else:
        details['security'].append("❌ Keine DSGVO-Awareness (-8)")
    if mapped.get('data_protection') in ['comprehensive', 'basic']:
        sec += 7; details['security'].append("✅ Datenschutz-Maßnahmen (+7)")
    else:
        details['security'].append("❌ Keine Datenschutz-Maßnahmen (-7)")
    if mapped.get('risk_assessment') == 'yes':
        sec += 6; details['security'].append("✅ Risiko-Assessment (+6)")
    else:
        details['security'].append("❌ Kein Risiko-Assessment (-6)")
    if mapped.get('security_training') in ['regular', 'occasional']:
        sec += 4; details['security'].append("✅ Sicherheits-Training (+4)")
    else:
        details['security'].append("❌ Kein Training (-4)")

    # VALUE
    u = mapped.get('use_cases', '')
    if u and len(u) > 50:
        val += 8; details['value'].append("✅ Use Cases definiert (+8)")
    elif u:
        val += 4; details['value'].append("⚠️ Use Cases ansatzweise (+4)")
    else:
        details['value'].append("❌ Keine Use Cases (-8)")
    roi = mapped.get('roi_expected', '')
    if roi in ['high', 'medium']:
        val += 7; details['value'].append(f"✅ ROI-Erwartung: {roi} (+7)")
    elif roi == 'low':
        val += 3; details['value'].append("⚠️ ROI niedrig (+3)")
    else:
        details['value'].append("❌ Keine ROI-Erwartung (-7)")
    if mapped.get('measurable_goals') == 'yes':
        val += 6; details['value'].append("✅ Messbare Ziele (+6)")
    else:
        details['value'].append("❌ Keine messbaren Ziele (-6)")
    if mapped.get('pilot_planned') in ['yes', 'in_progress']:
        val += 4; details['value'].append("✅ Pilot geplant (+4)")
    else:
        details['value'].append("❌ Kein Pilot (-4)")

    # ENABLEMENT
    skills = mapped.get('ai_skills', '')
    if skills in ['advanced', 'intermediate']:
        ena += 8; details['enablement'].append(f"✅ Skills: {skills} (+8)")
    elif skills == 'basic':
        ena += 4; details['enablement'].append("⚠️ Basis-Skills (+4)")
    else:
        details['enablement'].append("❌ Keine Skills (-8)")
    if mapped.get('training_budget') in ['yes', 'planned']:
        ena += 7; details['enablement'].append("✅ Training-Budget (+7)")
    else:
        details['enablement'].append("❌ Kein Training-Budget (-7)")
    if mapped.get('change_management') == 'yes':
        ena += 6; details['enablement'].append("✅ Change-Management (+6)")
    else:
        details['enablement'].append("❌ Kein Change-Management (-6)")
    culture = mapped.get('innovation_culture', '')
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
    log.info("📊 REALISTIC SCORES: Governance=%s/100, Security=%s/100, Value=%s/100, "
             "Enablement=%s/100, OVERALL=%s/100",
             scores['governance'], scores['security'], scores['value'],
             scores['enablement'], scores['overall'])
    return {'scores': scores, 'details': details, 'total': scores['overall']}

# -----------------------------------------------------------------------------
# LLM CONTENT GENERATION
# -----------------------------------------------------------------------------

def _call_openai(prompt: str, system_prompt: str = "Du bist ein KI-Berater.",
                 temperature: float | None = None, max_tokens: int = 2000) -> Optional[str]:
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

def _generate_content_section(section_name: str, briefing: Dict[str, Any],
                              scores: Dict[str, Any], research_data: Dict[str, Any]) -> str:
    """Generiert eine Content-Section per LLM und liefert validen HTML-String."""
    if not ENABLE_LLM_CONTENT:
        return f"<p><em>[{section_name} – LLM disabled]</em></p>"

    branche = briefing.get('branche', 'Unternehmen')
    hauptleistung = briefing.get('hauptleistung', '')
    ki_ziele = briefing.get('ki_ziele', [])
    ki_projekte = briefing.get('ki_projekte', '')
    vision = briefing.get('vision_3_jahre', '')
    overall = scores.get('scores', {}).get('overall', 0)
    governance = scores.get('scores', {}).get('governance', 0)
    security = scores.get('scores', {}).get('security', 0)

    prompts = {
        'executive_summary': f"""Erstelle eine prägnante Executive Summary für ein {branche}-Unternehmen.

Hauptleistung: {hauptleistung}
KI-Ziele: {', '.join(ki_ziele) if ki_ziele else 'nicht definiert'}
Vision: {vision}

KI-Reifegrad gesamt: {overall}/100
Governance: {governance}/100
Sicherheit: {security}/100

Schreibe 4–6 Sätze, die: (1) Reifegrad einordnen, (2) Chancen benennen, (3) 3 priorisierte Handlungsfelder empfehlen.
Format: **VALIDE HTML** mit <p>-Tags. **Keine Überschriften, keine Markdown**.""",

        'quick_wins': f"""Liste 3–5 **konkrete Quick Wins** für die nächsten 0–90 Tage (Branche: {branche}). 
Jeder Quick Win enthält: Titel, 1–2 Sätze Nutzen, **realistische Zeitersparnis/Monat** in Stunden.

Bezugspunkte:
- Hauptleistung: {hauptleistung}
- Laufende/Geplante Projekte: {ki_projekte or 'keine Angabe'}

Format: VALIDE HTML, genau eine Liste:
<ul>
  <li><strong>Titel:</strong> Beschreibung. <em>Ersparnis: 5 h/Monat</em></li>
</ul>""",

        'roadmap': f"""Erstelle eine **90‑Tage‑Roadmap** mit 3 Phasen:
1) 0–30 Tage (Test), 2) 31–60 Tage (Pilot), 3) 61–90 Tage (Rollout).
Für jede Phase 3–5 Meilensteine (konkret, überprüfbar).

Kontext:
- KI‑Ziele: {', '.join(ki_ziele) if ki_ziele else 'Effizienz'}
- Projekte: {ki_projekte or 'keine Angabe'}

Format: VALIDE HTML, z.B.:
<h4>Phase 0–30 Tage (Test)</h4>
<ul><li>Meilenstein ...</li></ul>""",

        'business': f"""Erstelle einen **Business Case (Jahr 1)** mit grober ROI‑Betrachtung für ein {branche}-Unternehmen.

Annahmen:
- Investition initial: 2.000–10.000 € (einmalig)
- Zeitersparnis: Summe der Quick Wins * Stundensatz
- Stundensatz: 50–80 €/h (nutze 60 €/h als Standard, falls unklar)
- ROI = (Ersparnis – Investition) / Investition * 100 %
- Payback in Monaten

Format: **ZWEI HTML‑TABELLEN**, ohne Überschriften:
(1) ROI & Payback (Kennzahl, Wert)
(2) Kosten (Jahr 1) (Position, Betrag)""",

        'recommendations': f"""Formuliere 5–7 **Handlungsempfehlungen** (Priorität Hoch/Mittel/Niedrig; Zeitrahmen 30/60/90 Tage). 
Passe auf {branche} an (Score gesamt {overall}/100, Governance {governance}/100).

Format: VALIDE HTML-Liste:
<ul><li><strong>[PRIO]</strong> Maßnahme (Zeitrahmen)</li></ul>""",

        'risks': f"""Erstelle eine kurze **Risikomatrix** (5–7 Risiken) für ein {branche}-Unternehmen, das KI assistierend einsetzt.
Typische Risiken: Datenschutz/DSGVO, Falschauskünfte/Haftung, Bias, Tool‑Abhängigkeit, Kostenüberschreitung, Verfügbarkeit.

Format: VALIDE HTML‑Tabelle:
<table>
  <thead><tr><th>Risiko</th><th>Eintritt</th><th>Auswirkung</th><th>Mitigation</th></tr></thead>
  <tbody>
    <tr><td>…</td><td>niedrig/mittel/hoch</td><td>…</td><td>…</td></tr>
  </tbody>
</table>""",

        'gamechanger': f"""Skizziere einen **Gamechanger‑Use Case** für {branche} basierend auf:
- Hauptleistung: {hauptleistung}
- Vision (3 Jahre): {vision or 'Marktführerschaft durch automatisierte, KI‑gestützte Beratung'}

Beschreibe: (1) Idee in 3–4 Sätzen, (2) 3 Schlüsselvorteile, (3) erste 3 Umsetzungsschritte.
Format: VALIDE HTML mit <h4>, <p>, <ul>.""",
    }

    prompt = prompts.get(section_name)
    if not prompt:
        return f"<p><em>[{section_name} – no template]</em></p>"

    log.info("🤖 Generating %s...", section_name)
    content = _call_openai(
        prompt=prompt,
        system_prompt="Du bist ein Senior‑KI‑Berater. Antworte mit **valide HTML**, niemals Markdown.",
        max_tokens=2000,
    )
    if not content:
        return f"<p><em>[{section_name} – generation failed]</em></p>"
    # Entferne evtl. Code-Fences
    content = content.replace('```html', '').replace('```', '').strip()
    log.info("✅ Generated %s (%d chars)", section_name, len(content))
    return content

def _generate_content_sections(briefing: Dict[str, Any], scores: Dict[str, Any],
                               research_data: Dict[str, Any]) -> Dict[str, str]:
    """Generiert alle Content‑Sections und liefert ein Dict von Template‑Keys → HTML."""
    sections: Dict[str, str] = {}

    # Reihenfolge & Coverage
    section_names = [
        'executive_summary',
        'quick_wins',
        'roadmap',
        'business',
        'risks',        # Fallback, falls Fetcher nichts liefert
        'gamechanger',  # neu
        'recommendations',  # aktuell nicht im PDF-Template verbaut, aber für Web nützlich
    ]

    for name in section_names:
        html_key = f"{name.upper()}_HTML"
        if name == 'executive_summary':
            html_key = 'EXECUTIVE_SUMMARY_HTML'  # ✅ Key auf Template-Norm
        elif name == 'business':
            html_key = 'BUSINESS_CASE_HTML'      # später splitten in ROI/Kosten
        elif name == 'roadmap':
            html_key = 'ROADMAP_HTML'            # später auf PILOT_PLAN_HTML mappen
        elif name == 'recommendations':
            html_key = 'RECOMMENDATIONS_HTML'
        elif name == 'risks':
            html_key = 'RISKS_HTML'
        elif name == 'gamechanger':
            html_key = 'GAMECHANGER_HTML'

        sections[html_key] = _generate_content_section(name, briefing, scores, research_data)

    return sections

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

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
    # unique order‑preserving
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
                attachments.append({
                    "filename": f"KI-Status-Report-{getattr(rep, 'id', None)}.pdf",
                    "content": pdf_bytes,
                    "mimetype": "application/pdf"
                })
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
                attachments.append({
                    "filename": f"KI-Status-Report-{getattr(rep, 'id', None)}.pdf",
                    "content": pdf_bytes,
                    "mimetype": "application/pdf"
                })
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

# -----------------------------------------------------------------------------
# MAIN ANALYSIS PIPELINE
# -----------------------------------------------------------------------------

def analyze_briefing(db: Session, briefing_id: int, run_id: str) -> Tuple[int, str, Dict[str, Any]]:
    """
    Führt die vollständige Analyse aus:
    1) Scores berechnen
    2) Content mit LLM erzeugen
    3) Content normalisieren (Keys, Splits, Fallbacks, Scores)
    4) HTML rendern
    5) Analysis-Objekt speichern
    """
    br = db.get(Briefing, briefing_id)
    if not br:
        raise ValueError("Briefing not found")

    answers: Dict[str, Any] = getattr(br, "answers", {}) or {}

    # 1) Scores
    log.info("[%s] Calculating realistic scores...", run_id)
    scores = _calculate_realistic_score(answers)

    # 2) LLM Content
    log.info("[%s] Generating content sections with LLM...", run_id)
    raw_sections = _generate_content_sections(
        briefing=answers,
        scores=scores,
        research_data={},  # Research via report_renderer Fetchers
    )

    # 3) Normalize / Enrich
    normalized_sections = normalize_and_enrich_sections(
        sections=raw_sections,
        answers=answers,
        scores=scores.get("scores", {}),
    )

    # 4) Render HTML (über Fetcher kommen u. a. TOOLS, FÖRDERPROGRAMME, BENCHMARK, QUELLEN)
    log.info("[%s] Rendering final HTML...", run_id)
    result = render(
        br,
        run_id=run_id,
        generated_sections=normalized_sections,
        use_fetchers=True,
    )

    # 5) Meta anreichern & quality gate
    result['meta'] = result.get('meta', {})
    result['meta']['scores'] = scores['scores']
    result['meta']['score_details'] = scores['details']
    result['meta'].update(normalized_sections)

    if ENABLE_QUALITY_GATES:
        issues: List[str] = []
        if not normalized_sections.get('EXECUTIVE_SUMMARY_HTML'):
            issues.append("Missing EXECUTIVE_SUMMARY_HTML")
        if scores['scores']['overall'] == 0:
            issues.append("Score overall is zero")
        if issues:
            log.warning("[%s] Quality warnings: %s", run_id, issues)
            result['meta']['quality_warnings'] = issues

    # Persist Analysis
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
    log.info("[%s] ✅ Analysis created (v4.2): id=%s", run_id, an.id)

    return an.id, result["html"], result["meta"]

def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    """Asynchroner Runner für die Analyse und PDF-Erstellung inkl. E‑Mail-Versand."""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    rep: Optional[Report] = None
    try:
        log.info("[%s] 🚀 Starting analysis for briefing_id=%s", run_id, briefing_id)

        # Analyse/Fabrication
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
        br = db.get(Briefing, briefing_id)
        log.info("[%s] analysis_created id=%s briefing_id=%s user_id=%s",
                 run_id, an_id, briefing_id, getattr(br, 'user_id', None))

        # Report entity
        rep = Report(
            user_id=br.user_id if br else None,
            briefing_id=briefing_id,
            analysis_id=an_id,
            created_at=datetime.now(timezone.utc),
        )
        if hasattr(rep, "user_email"):
            rep.user_email = _determine_user_email(db, br, email) or ""
        if hasattr(rep, "task_id"):
            rep.task_id = f"local-{uuid.uuid4()}"
        if hasattr(rep, "status"):
            rep.status = "pending"
        db.add(rep)
        db.commit()
        db.refresh(rep)
        log.info("[%s] report_pending id=%s", run_id, getattr(rep, 'id', None))

        # PDF render
        if DBG_PDF:
            log.debug("[%s] pdf_render start", run_id)
        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id})
        pdf_url = pdf_info.get("pdf_url")
        pdf_bytes = pdf_info.get("pdf_bytes")
        pdf_error = pdf_info.get("error")
        if DBG_PDF:
            log.debug("[%s] pdf_render done url=%s bytes=%s error=%s",
                      run_id, bool(pdf_url), len(pdf_bytes or b''), pdf_error)

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

        # Update report
        if hasattr(rep, "pdf_url"):
            rep.pdf_url = pdf_url
        if hasattr(rep, "pdf_bytes_len") and pdf_bytes:
            rep.pdf_bytes_len = len(pdf_bytes)
        if hasattr(rep, "status"):
            rep.status = "done"
        if hasattr(rep, "updated_at"):
            rep.updated_at = datetime.now(timezone.utc)
        db.add(rep); db.commit(); db.refresh(rep)
        log.info("[%s] ✅ report_done id=%s url=%s bytes=%s",
                 run_id, getattr(rep, 'id', None), bool(pdf_url), len(pdf_bytes or b''))

        # Emails
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
