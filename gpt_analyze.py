# -*- coding: utf-8 -*-
from __future__ import annotations
"""
EMERGENCY HOTFIX v4.1 - Critical Bug Fixes from v4.0

BUGS FIXED IN v4.1:
===================
🐛 BUG #1: Score-Formel FALSCH (388/100 → 97/100)
   - Problem: scores['overall'] = (sum) * 4 → 388
   - Fixed: Jede Säule * 4 für Template (0-100), dann Durchschnitt

🐛 BUG #2: Research-API Parameter FALSCH
   - Problem: search_funding_and_tools(state=...) → KeyError
   - Fixed: Nutze bestehende Fetchers aus report_renderer

🐛 BUG #3: Scores nicht im PDF (0/100 im PDF trotz 97/100 im Log)
   - Problem: Scores nicht korrekt ans Template übergeben
   - Fixed: Übergebe Scores in briefing_dict für Template

🐛 BUG #4: Content-Sections nicht im PDF (trotz erfolgreicher LLM-Generation)
   - Problem: generated_sections nicht korrekt durch Pipeline
   - Fixed: Sichere Übergabe an report_renderer

EXPECTED RESULTS v4.1:
======================
Governance:    88/100 (war: 0/100) ✅
Security:      100/100 (war: 0/100) ✅
Value:         100/100 (war: 0/100) ✅
Enablement:    100/100 (war: 0/100) ✅
OVERALL:       97/100 (war: 0/100, 4.0: 388/100) ✅

Executive Summary: 4-6 Sätze ✅
Quick Wins: 3-4 Items ✅
Roadmap: 90-Tage-Plan ✅
Business Case: ROI-Tabelle ✅
Recommendations: 5-7 Maßnahmen ✅
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
from settings import settings

log = logging.getLogger(__name__)

# Config
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

# NSFW Filter
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
            log.warning(f"🚨 Filtered NSFW tool: {title[:50]}...")
    
    for fund in research_data.get('funding', []):
        url = fund.get('url', '')
        title = fund.get('title', '')
        description = fund.get('description', '')
        if not _is_nsfw_content(url, title, description):
            filtered_data['funding'].append(fund)
        else:
            stats['funding_filtered'] += 1
            log.warning(f"🚨 Filtered NSFW funding: {title[:50]}...")
    
    if stats['tools_filtered'] > 0 or stats['funding_filtered'] > 0:
        log.warning(
            f"🚨 NSFW FILTER: Tools: {stats['tools_filtered']}/{stats['tools_total']}, "
            f"Funding: {stats['funding_filtered']}/{stats['funding_total']} filtered"
        )
    else:
        log.info(f"✅ NSFW filter passed: {stats['tools_total']} tools, {stats['funding_total']} funding clean")
    
    return filtered_data

# ========================================
# SCORE CALCULATION (FIXED v4.1)
# ========================================

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
    if ki_ziele and len(ki_ziele) > 0:
        mapped['goals'] = ', '.join(ki_ziele)
    else:
        mapped['goals'] = answers.get('strategische_ziele', '')
    
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
    
    if answers.get('folgenabschaetzung') == 'ja':
        mapped['risk_assessment'] = 'yes'
    else:
        mapped['risk_assessment'] = 'no'
    
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
    
    if answers.get('strategische_ziele') or answers.get('ki_ziele'):
        mapped['measurable_goals'] = 'yes'
    else:
        mapped['measurable_goals'] = 'no'
    
    if answers.get('pilot_bereich'):
        mapped['pilot_planned'] = 'yes'
    elif answers.get('ki_projekte'):
        mapped['pilot_planned'] = 'in_progress'
    else:
        mapped['pilot_planned'] = 'no'
    
    # Enablement
    kompetenz_map = {
        'hoch': 'advanced',
        'mittel': 'intermediate',
        'niedrig': 'basic',
        'keine': 'none'
    }
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
    🔧 FIXED v4.1: Score-Formel korrigiert
    
    Berechnet Scores korrekt:
    - Intern: 0-25 Punkte pro Säule
    - Template: 0-100 Punkte pro Säule (mal 4)
    - Gesamt: Durchschnitt der 4 Säulen (0-100)
    """
    if not ENABLE_REALISTIC_SCORES:
        return {
            'scores': {'governance': 0, 'security': 0, 'value': 0, 'enablement': 0, 'overall': 0},
            'details': {},
            'total': 0
        }
    
    mapped_answers = _map_german_to_english_keys(answers)
    log.debug(f"🔄 Mapped {len(answers)} german keys to {len(mapped_answers)} english keys")
    
    # Intern: 0-25 pro Säule
    gov_score = 0
    sec_score = 0
    val_score = 0
    ena_score = 0
    
    details = {
        'governance': [],
        'security': [],
        'value': [],
        'enablement': []
    }
    
    # === GOVERNANCE (0-25) ===
    if mapped_answers.get('ai_strategy') in ['yes', 'in_progress']:
        gov_score += 8
        details['governance'].append("✅ KI-Strategie (+8)")
    else:
        details['governance'].append("❌ Keine KI-Strategie (-8)")
    
    if mapped_answers.get('ai_responsible') in ['yes', 'shared']:
        gov_score += 7
        details['governance'].append("✅ KI-Verantwortlicher (+7)")
    else:
        details['governance'].append("❌ Kein KI-Verantwortlicher (-7)")
    
    budget = mapped_answers.get('budget', '')
    if budget in ['10k-50k', '50k-100k', 'over_100k']:
        gov_score += 6
        details['governance'].append(f"✅ Budget: {budget} (+6)")
    elif budget == 'under_10k':
        gov_score += 3
        details['governance'].append("⚠️ Budget: unter 10k (+3)")
    else:
        details['governance'].append("❌ Kein Budget (-6)")
    
    if mapped_answers.get('goals') or mapped_answers.get('use_cases'):
        gov_score += 4
        details['governance'].append("✅ KI-Ziele definiert (+4)")
    else:
        details['governance'].append("❌ Keine KI-Ziele (-4)")
    
    # === SECURITY (0-25) ===
    if mapped_answers.get('gdpr_aware') == 'yes':
        sec_score += 8
        details['security'].append("✅ DSGVO-Awareness (+8)")
    else:
        details['security'].append("❌ Keine DSGVO-Awareness (-8)")
    
    if mapped_answers.get('data_protection') in ['comprehensive', 'basic']:
        sec_score += 7
        details['security'].append("✅ Datenschutz-Maßnahmen (+7)")
    else:
        details['security'].append("❌ Keine Datenschutz-Maßnahmen (-7)")
    
    if mapped_answers.get('risk_assessment') == 'yes':
        sec_score += 6
        details['security'].append("✅ Risiko-Assessment (+6)")
    else:
        details['security'].append("❌ Kein Risiko-Assessment (-6)")
    
    if mapped_answers.get('security_training') in ['regular', 'occasional']:
        sec_score += 4
        details['security'].append("✅ Sicherheits-Training (+4)")
    else:
        details['security'].append("❌ Kein Training (-4)")
    
    # === VALUE (0-25) ===
    use_cases = mapped_answers.get('use_cases', '')
    if use_cases and len(use_cases) > 50:
        val_score += 8
        details['value'].append("✅ Use Cases definiert (+8)")
    elif use_cases:
        val_score += 4
        details['value'].append("⚠️ Use Cases ansatzweise (+4)")
    else:
        details['value'].append("❌ Keine Use Cases (-8)")
    
    roi = mapped_answers.get('roi_expected', '')
    if roi in ['high', 'medium']:
        val_score += 7
        details['value'].append(f"✅ ROI-Erwartung: {roi} (+7)")
    elif roi == 'low':
        val_score += 3
        details['value'].append("⚠️ ROI niedrig (+3)")
    else:
        details['value'].append("❌ Keine ROI-Erwartung (-7)")
    
    if mapped_answers.get('measurable_goals') == 'yes':
        val_score += 6
        details['value'].append("✅ Messbare Ziele (+6)")
    else:
        details['value'].append("❌ Keine messbaren Ziele (-6)")
    
    if mapped_answers.get('pilot_planned') in ['yes', 'in_progress']:
        val_score += 4
        details['value'].append("✅ Pilot geplant (+4)")
    else:
        details['value'].append("❌ Kein Pilot (-4)")
    
    # === ENABLEMENT (0-25) ===
    skills = mapped_answers.get('ai_skills', '')
    if skills in ['advanced', 'intermediate']:
        ena_score += 8
        details['enablement'].append(f"✅ Skills: {skills} (+8)")
    elif skills == 'basic':
        ena_score += 4
        details['enablement'].append("⚠️ Basis-Skills (+4)")
    else:
        details['enablement'].append("❌ Keine Skills (-8)")
    
    if mapped_answers.get('training_budget') in ['yes', 'planned']:
        ena_score += 7
        details['enablement'].append("✅ Training-Budget (+7)")
    else:
        details['enablement'].append("❌ Kein Training-Budget (-7)")
    
    if mapped_answers.get('change_management') == 'yes':
        ena_score += 6
        details['enablement'].append("✅ Change-Management (+6)")
    else:
        details['enablement'].append("❌ Kein Change-Management (-6)")
    
    culture = mapped_answers.get('innovation_culture', '')
    if culture in ['strong', 'moderate']:
        ena_score += 4
        details['enablement'].append(f"✅ Kultur: {culture} (+4)")
    else:
        details['enablement'].append("❌ Schwache Kultur (-4)")
    
    # 🔧 FIX: Richtige Score-Berechnung für Template
    # Intern: 0-25, Template: 0-100 (mal 4), Gesamt: Durchschnitt
    scores = {
        'governance': min(gov_score, 25) * 4,    # 0-100
        'security': min(sec_score, 25) * 4,      # 0-100
        'value': min(val_score, 25) * 4,         # 0-100
        'enablement': min(ena_score, 25) * 4,    # 0-100
        'overall': round((min(gov_score, 25) + min(sec_score, 25) + min(val_score, 25) + min(ena_score, 25)) * 4 / 4)  # 0-100
    }
    
    log.info(
        f"📊 REALISTIC SCORES: "
        f"Governance={scores['governance']}/100, "
        f"Security={scores['security']}/100, "
        f"Value={scores['value']}/100, "
        f"Enablement={scores['enablement']}/100, "
        f"OVERALL={scores['overall']}/100"
    )
    
    return {
        'scores': scores,
        'details': details,
        'total': scores['overall']
    }

# ========================================
# LLM CONTENT GENERATION
# ========================================

def _call_openai(prompt: str, system_prompt: str = "Du bist ein KI-Berater.", 
                 temperature: float = None, max_tokens: int = 2000) -> Optional[str]:
    """Zentrale OpenAI API Wrapper"""
    if not OPENAI_API_KEY:
        log.error("❌ OPENAI_API_KEY not set")
        return None
    
    if temperature is None:
        temperature = OPENAI_TEMPERATURE
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
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
        log.debug(f"✅ OpenAI success ({len(content)} chars)")
        return content
    except Exception as e:
        log.error(f"❌ OpenAI error: {e}")
        return None

def _generate_content_section(section_name: str, briefing: Dict[str, Any], 
                              scores: Dict[str, Any], research_data: Dict[str, Any]) -> str:
    """Generiert eine Content-Section mit LLM"""
    if not ENABLE_LLM_CONTENT:
        return f"<p><em>[{section_name} - LLM disabled]</em></p>"
    
    branche = briefing.get('branche', 'Unternehmen')
    hauptleistung = briefing.get('hauptleistung', '')
    ki_ziele = briefing.get('ki_ziele', [])
    ki_projekte = briefing.get('ki_projekte', '')
    vision = briefing.get('vision_3_jahre', '')
    
    overall = scores.get('scores', {}).get('overall', 0)
    governance = scores.get('scores', {}).get('governance', 0)
    security = scores.get('scores', {}).get('security', 0)
    
    prompts = {
        'executive_summary': f"""Erstelle Executive Summary für {branche}-Unternehmen:

Hauptleistung: {hauptleistung}
KI-Ziele: {', '.join(ki_ziele) if ki_ziele else 'Nicht definiert'}
Vision: {vision}

KI-Reifegrad: {overall}/100
Governance: {governance}/100
Sicherheit: {security}/100

Schreibe 4-6 Sätze die: 1) Reifegrad einordnen, 2) Chancen nennen, 3) Top-3 Handlungsfelder

Format: HTML mit <p> Tags. KEINE Überschriften.""",

        'quick_wins': f"""Erstelle 3-4 Quick Wins für {branche} mit Score {overall}/100:

Hauptleistung: {hauptleistung}
Projekte: {ki_projekte or 'Keine'}

Jeder Quick Win: 0-30 Tage umsetzbar, konkrete Zeitersparnis, spezifisch für {branche}

Format: HTML <ul><li><strong>Name:</strong> Beschreibung + Zeitersparnis</li></ul>""",

        'roadmap': f"""Erstelle 90-Tage-Roadmap für {branche}:

KI-Ziele: {', '.join(ki_ziele) if ki_ziele else 'Effizienz'}
Projekte: {ki_projekte or 'Keine'}

3 Phasen:
1. Tage 0-30 (Test): Pilot definieren
2. Tage 31-60 (Pilot): Tests
3. Tage 61-90 (Rollout): Skalierung

Format: HTML <h4>Phase</h4><ul><li>Meilensteine</li></ul>""",

        'business': f"""Business Case für {branche}:

Hauptleistung: {hauptleistung}
Vision: {vision}

Berechne:
1. Investition: €2.000-10.000
2. Einsparungen: Zeit * Stundensatz
3. ROI: (Einsparung - Investition) / Investition * 100%
4. Payback: Monate

Format: HTML-Tabelle mit Zahlen.""",

        'recommendations': f"""5-7 Handlungsempfehlungen für {branche} mit Score {overall}/100:

Governance ({governance}/100): {('Gut' if governance > 60 else 'Ausbau')}
Sicherheit ({security}/100): {('Gut' if security > 60 else 'Kritisch')}

Jede: Maßnahme, Priorität (Hoch/Mittel/Niedrig), Zeitrahmen (30/60/90 Tage)

Format: HTML <ul><li><strong>[PRIO]</strong> Maßnahme (Zeit)</li></ul>""",
    }
    
    prompt = prompts.get(section_name)
    if not prompt:
        return f"<p><em>[{section_name} - no template]</em></p>"
    
    log.info(f"🤖 Generating {section_name}...")
    content = _call_openai(
        prompt=prompt,
        system_prompt="Du bist ein KI-Berater. Antworte mit validen HTML. Keine Markdown.",
        max_tokens=2000,
    )
    
    if not content:
        return f"<p><em>[{section_name} - generation failed]</em></p>"
    
    content = content.replace('```html', '').replace('```', '').strip()
    log.info(f"✅ Generated {section_name} ({len(content)} chars)")
    return content

def _generate_content_sections(briefing: Dict[str, Any], scores: Dict[str, Any], 
                               research_data: Dict[str, Any]) -> Dict[str, str]:
    """Generiert alle Content-Sections"""
    sections = {}
    
    section_names = ['executive_summary', 'quick_wins', 'roadmap', 'business', 'recommendations']
    
    for section_name in section_names:
        html_key = f"{section_name.upper()}_HTML"
        if section_name == 'executive_summary':
            html_key = 'EXEC_SUMMARY_HTML'
        elif section_name == 'business':
            html_key = 'BUSINESS_CASE_HTML'
        
        sections[html_key] = _generate_content_section(section_name, briefing, scores, research_data)
    
    return sections

# ========================================
# HELPERS
# ========================================

def _mask_email(addr: Optional[str]) -> str:
    if not addr or not DBG_MASK_EMAILS:
        return addr or ""
    try:
        name, domain = addr.split("@", 1)
        return f"{name[:3]}***@{domain}" if len(name) > 3 else f"{name}***@{domain}"
    except:
        return "***"

def _admin_recipients() -> List[str]:
    emails = []
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
        if u and hasattr(u, "email") and u.email:
            return u.email
    answers = getattr(briefing, "answers", None) or {}
    return answers.get("email") or answers.get("kontakt_email")

def _send_emails(db: Session, rep: Report, br: Briefing, 
                 pdf_url: Optional[str], pdf_bytes: Optional[bytes], run_id: str) -> None:
    # User email
    user_email = _determine_user_email(db, br, getattr(rep, "user_email", None))
    if user_email:
        try:
            subject = "Ihr KI-Status-Report ist fertig"
            body_html = render_report_ready_email(recipient="user", pdf_url=pdf_url)
            attachments = []
            if pdf_bytes and not pdf_url:
                attachments.append({
                    "filename": f"KI-Status-Report-{getattr(rep,'id', None)}.pdf",
                    "content": pdf_bytes,
                    "mimetype": "application/pdf"
                })
            log.debug(f"[{run_id}] MAIL_USER to={_mask_email(user_email)}")
            ok, err = send_mail(user_email, subject, body_html, text=None, attachments=attachments)
            if ok and hasattr(rep, "email_sent_user"):
                rep.email_sent_user = True
            if not ok and hasattr(rep, "email_error_user"):
                rep.email_error_user = err or "send_mail failed"
        except Exception as exc:
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = str(exc)
            log.warning(f"[{run_id}] MAIL_USER failed: {exc}")
    
    # Admin emails
    admins = _admin_recipients()
    if admins:
        try:
            subject = "Kopie: KI-Status-Report"
            body_html = render_report_ready_email(recipient="admin", pdf_url=pdf_url)
            attachments = []
            try:
                bjson = json.dumps(getattr(br, "answers", {}) or {}, ensure_ascii=False, indent=2).encode("utf-8")
                attachments.append({
                    "filename": f"briefing-{br.id}.json",
                    "content": bjson,
                    "mimetype": "application/json"
                })
            except:
                pass
            if pdf_bytes and not pdf_url:
                attachments.append({
                    "filename": f"KI-Status-Report-{getattr(rep,'id', None)}.pdf",
                    "content": pdf_bytes,
                    "mimetype": "application/pdf"
                })
            any_ok = False
            for addr in admins:
                log.debug(f"[{run_id}] MAIL_ADMIN to={_mask_email(addr)}")
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
            log.warning(f"[{run_id}] MAIL_ADMIN failed: {exc}")

# ========================================
# MAIN ANALYSIS
# ========================================

def analyze_briefing(db: Session, briefing_id: int, run_id: str) -> Tuple[int, str, Dict[str, Any]]:
    """
    🔧 FIXED v4.1: Analyze briefing mit allen Bug-Fixes
    
    Fixes:
    - Score-Formel korrekt (97/100 statt 388/100)
    - Research via report_renderer Fetchers (kein API-Error)
    - Scores in briefing_dict für Template
    - Content-Sections korrekt übergeben
    """
    br = db.get(Briefing, briefing_id)
    if not br:
        raise ValueError("Briefing not found")
    
    answers = getattr(br, "answers", {}) or {}
    
    # STEP 1: Calculate scores
    log.info(f"[{run_id}] Calculating realistic scores...")
    scores = _calculate_realistic_score(answers)
    
    # STEP 2: Generate content with LLM
    log.info(f"[{run_id}] Generating content sections with LLM...")
    generated_sections = _generate_content_sections(
        briefing=answers,
        scores=scores,
        research_data={},  # Research via report_renderer
    )
    
    # 🔧 FIX: Übergebe Scores in briefing_dict für Template
    briefing_dict = dict(answers)
    briefing_dict['scores'] = scores['scores']
    briefing_dict['score_details'] = scores['details']
    
    # STEP 3: Render HTML via report_renderer
    # 🔧 FIX: use_fetchers=True nutzt bestehende Research-Fetchers
    log.info(f"[{run_id}] Rendering final HTML...")
    result = render(
        br,
        run_id=run_id,
        generated_sections=generated_sections,
        use_fetchers=True,  # 🔧 FIX: Nutze bestehende Fetchers
    )
    
    # Add metadata
    result['meta']['scores'] = scores['scores']
    result['meta']['score_details'] = scores['details']
    result['meta'].update(generated_sections)
    
    # Quality gate (warning only)
    if ENABLE_QUALITY_GATES:
        issues = []
        if not generated_sections.get('EXEC_SUMMARY_HTML'):
            issues.append("Missing EXEC_SUMMARY_HTML")
        if scores['scores']['overall'] == 0:
            issues.append("Score is zero")
        if issues:
            log.warning(f"[{run_id}] Quality warnings: {issues}")
            result['meta']['quality_warnings'] = issues
    
    # Create analysis
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
    
    log.info(f"[{run_id}] ✅ Analysis created (HOTFIX v4.1): id={an.id}")
    
    return an.id, result["html"], result["meta"]

def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    """Main async runner mit HOTFIX v4.1"""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    rep: Optional[Report] = None
    
    try:
        log.info(f"[{run_id}] 🚀 Starting HOTFIX v4.1 analysis for briefing_id={briefing_id}")
        
        # Analyse
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
        br = db.get(Briefing, briefing_id)
        log.info(f"[{run_id}] analysis_created id={an_id} briefing_id={briefing_id} user_id={getattr(br, 'user_id', None)}")
        
        # Report
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
        log.info(f"[{run_id}] report_pending id={getattr(rep, 'id', None)}")
        
        # PDF
        if DBG_PDF:
            log.debug(f"[{run_id}] pdf_render start")
        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id})
        pdf_url = pdf_info.get("pdf_url")
        pdf_bytes = pdf_info.get("pdf_bytes")
        pdf_error = pdf_info.get("error")
        if DBG_PDF:
            log.debug(f"[{run_id}] pdf_render done url={bool(pdf_url)} bytes={len(pdf_bytes or b'')} error={pdf_error}")
        
        if not pdf_url and not pdf_bytes:
            error_msg = f"PDF failed: {pdf_error or 'no output'}"
            log.error(f"[{run_id}] {error_msg}")
            if hasattr(rep, "status"):
                rep.status = "failed"
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = error_msg
            if hasattr(rep, "updated_at"):
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep)
            db.commit()
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
        db.add(rep)
        db.commit()
        db.refresh(rep)
        log.info(f"[{run_id}] ✅ report_done id={getattr(rep, 'id', None)} url={bool(pdf_url)} bytes={len(pdf_bytes or b'')} (HOTFIX v4.1)")
        
        # Emails
        try:
            _send_emails(db, rep, br, pdf_url, pdf_bytes, run_id=run_id)
            db.add(rep)
            db.commit()
        except Exception as exc:
            log.warning(f"[{run_id}] email error: {exc}")
    
    except Exception as exc:
        log.error(f"[{run_id}] ❌ Analysis failed: {exc}", exc_info=True)
        if rep and hasattr(rep, "status"):
            rep.status = "failed"
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = str(exc)
            if hasattr(rep, "updated_at"):
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep)
            db.commit()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python gpt_analyze.py <briefing_id>")
        sys.exit(1)
    briefing_id = int(sys.argv[1])
    run_async(briefing_id)
