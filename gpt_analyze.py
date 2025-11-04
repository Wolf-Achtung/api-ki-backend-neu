# -*- coding: utf-8 -*-
from __future__ import annotations
"""
gpt_analyze.py – v4.10.4-gs (Gold‑Standard+)
- Bewahrt Funktionsumfang eurer neuesten Pipeline (Scores, One‑liner, AI‑Act, Research, E‑Mails).
- Stärkt Prompts (Branche, Unternehmensgröße, Hauptleistung/ -produkt, Bundesland).
- Fügt Next‑Actions‑Box & One‑liner‑Leads für alle Kapitel hinzu.
- Liefert Wasserzeichen‑Text/WARTERMARK_TEXT, Report‑ID, Firmenname ins Template.
- Robuste Quick‑Wins‑Summierung + ENV‑Fallbacks.
- OpenAI: unterstützt OPENAI_API_BASE (Azure), Timeouts, sauberes Error‑Logging.
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

log = logging.getLogger(__name__)

# ----- LLM / API -----
OPENAI_API_KEY = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = getattr(settings, "OPENAI_MODEL", None) or os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_BASE = getattr(settings, "OPENAI_API_BASE", None) or os.getenv("OPENAI_API_BASE")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "120"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "3000"))

# ----- Feature Flags -----
ENABLE_NSFW_FILTER = (os.getenv("ENABLE_NSFW_FILTER", "1") == "1")
ENABLE_QUALITY_GATES = (os.getenv("ENABLE_QUALITY_GATES", "1") == "1")
ENABLE_REALISTIC_SCORES = (os.getenv("ENABLE_REALISTIC_SCORES", "1") == "1")
ENABLE_LLM_CONTENT = (os.getenv("ENABLE_LLM_CONTENT", "1") == "1")
ENABLE_REPAIR_HTML = (os.getenv("ENABLE_REPAIR_HTML", "1") == "1")
USE_INTERNAL_RESEARCH = (os.getenv("USE_INTERNAL_RESEARCH", "1") == "1")

# AI‑Act: Kapitel/CTA
ENABLE_AI_ACT_SECTION = (os.getenv("ENABLE_AI_ACT_SECTION", "1") == "1")
AI_ACT_INFO_PATH = os.getenv("AI_ACT_INFO_PATH", "EU-AI-ACT-Infos-wichtig.txt")
AI_ACT_PHASE_LABEL = os.getenv("AI_ACT_PHASE_LABEL", "2025–2027")

DBG_PDF = (os.getenv("DEBUG_LOG_PDF_INFO", "1") == "1")
DBG_MASK_EMAILS = (os.getenv("DEBUG_MASK_EMAILS", "1") == "1")

# -------------------- Helpers: NSFW‑Filter für Research ----------------------
NSFW_KEYWORDS = {
    'porn','xxx','sex','nude','naked','adult','nsfw','erotic','webcam','escort','dating','hookup','milf','teen','amateur',
    'porno','nackt','fick','muschi','schwanz','titten','chudai','chut','lund','gaand','bhabhi','desi',
    'onlyfans','patreon','leaked','torrent','pirate','crack'
}
NSFW_DOMAINS = {'xvideos.com','pornhub.com','xnxx.com','redtube.com','youporn.com','onlyfans.com','fansly.com','manyvids.com'}

def _is_nsfw_content(url: str, title: str, description: str) -> bool:
    if not ENABLE_NSFW_FILTER:
        return False
    url_lower = (url or "").lower()
    if any(domain in url_lower for domain in NSFW_DOMAINS):
        return True
    text = f\"{title} {description}\".lower()
    return any(k in text for k in NSFW_KEYWORDS)

def _filter_nsfw_from_research(research_data: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_NSFW_FILTER:
        return research_data
    filtered: Dict[str, Any] = {'tools': [], 'funding': []}
    for tool in research_data.get('tools', []):
        if not _is_nsfw_content(tool.get('url',''), tool.get('title',''), tool.get('description','')):
            filtered['tools'].append(tool)
    for fund in research_data.get('funding', []):
        if not _is_nsfw_content(fund.get('url',''), fund.get('title',''), fund.get('description','')):
            filtered['funding'].append(fund)
    return filtered


# ------------------------------- Scoring ------------------------------------
def _map_german_to_english_keys(answers: Dict[str, Any]) -> Dict[str, Any]:
    mapped: Dict[str, Any] = {}
    # Governance
    if answers.get('roadmap_vorhanden') == 'ja':
        mapped['ai_strategy'] = 'yes'
    elif answers.get('roadmap_vorhanden') == 'teilweise' or answers.get('vision_3_jahre') or answers.get('ki_ziele'):
        mapped['ai_strategy'] = 'in_progress'
    else:
        mapped['ai_strategy'] = 'no'
    if answers.get('governance_richtlinien') in ['ja','alle']:
        mapped['ai_responsible'] = 'yes'
    elif answers.get('governance_richtlinien') == 'teilweise':
        mapped['ai_responsible'] = 'shared'
    else:
        mapped['ai_responsible'] = 'no'
    budget_map = {'unter_2000': 'under_10k', '2000_10000':'under_10k', '10000_50000':'10k-50k', '50000_100000':'50k-100k', 'ueber_100000':'over_100k'}
    mapped['budget'] = budget_map.get(answers.get('investitionsbudget',''), 'none')
    ki_ziele = answers.get('ki_ziele', [])
    mapped['goals'] = ', '.join(ki_ziele) if ki_ziele else answers.get('strategische_ziele','')
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
    u = mapped['use_cases']
    if u and len(u) > 50: val_points = 8
    elif u: val_points = 4
    else: val_points = 0
    mapped['_value_points_from_uses'] = val_points
    roi = answers.get('vision_prioritaet','')
    mapped['roi_expected'] = 'high' if roi in ['marktfuehrerschaft','wachstum'] else ('medium' if roi else 'low')
    mapped['measurable_goals'] = 'yes' if (answers.get('strategische_ziele') or answers.get('ki_ziele')) else 'no'
    mapped['pilot_planned'] = 'yes' if answers.get('pilot_bereich') else ('in_progress' if answers.get('ki_projekte') else 'no')
    # Enablement
    kompetenz_map = {'hoch':'advanced','mittel':'intermediate','niedrig':'basic','keine':'none'}
    mapped['ai_skills'] = kompetenz_map.get(answers.get('ki_kompetenz',''), 'none')
    mapped['training_budget'] = 'yes' if answers.get('zeitbudget') in ['ueber_10','5_10'] else ('planned' if answers.get('zeitbudget') else 'no')
    change = answers.get('change_management','')
    mapped['change_management'] = 'yes' if change == 'hoch' else ('planned' if change in ['mittel','niedrig'] else 'no')
    innovationsprozess = answers.get('innovationsprozess','')
    mapped['innovation_culture'] = 'strong' if innovationsprozess in ['mitarbeitende','alle'] else ('moderate' if innovationsprozess else 'weak')
    return mapped

def _calculate_realistic_score(answers: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_REALISTIC_SCORES:
        return {'scores': {'governance':0,'security':0,'value':0,'enablement':0,'overall':0}, 'details':{}, 'total':0}
    m = _map_german_to_english_keys(answers)
    gov = sec = val = ena = 0
    details = {'governance': [], 'security': [], 'value': [], 'enablement': []}
    # Governance
    if m.get('ai_strategy') in ['yes','in_progress']: gov += 8; details['governance'].append("✅ KI-Strategie (+8)")
    else: details['governance'].append("❌ Keine KI-Strategie (-8)")
    if m.get('ai_responsible') in ['yes','shared']: gov += 7; details['governance'].append("✅ KI-Verantwortlicher (+7)")
    else: details['governance'].append("❌ Kein KI-Verantwortlicher (-7)")
    budget = m.get('budget','')
    if budget in ['10k-50k','50k-100k','over_100k']: gov += 6; details['governance'].append(f"✅ Budget: {budget} (+6)")
    elif budget == 'under_10k': gov += 3; details['governance'].append("⚠️ Budget: unter 10k (+3)")
    else: details['governance'].append("❌ Kein Budget (-6)")
    if m.get('goals') or m.get('use_cases'): gov += 4; details['governance'].append("✅ KI-Ziele definiert (+4)")
    else: details['governance'].append("❌ Keine KI-Ziele (-4)")
    # Security
    if m.get('gdpr_aware') == 'yes': sec += 8; details['security'].append("✅ DSGVO-Awareness (+8)")
    else: details['security'].append("❌ Keine DSGVO-Awareness (-8)")
    if m.get('data_protection') in ['comprehensive','basic']: sec += 7; details['security'].append("✅ Datenschutz-Maßnahmen (+7)")
    else: details['security'].append("❌ Keine Datenschutz-Maßnahmen (-7)")
    if m.get('risk_assessment') == 'yes': sec += 6; details['security'].append("✅ Risiko-Assessment (+6)")
    else: details['security'].append("❌ Kein Risiko-Assessment (-6)")
    if m.get('security_training') in ['regular','occasional']: sec += 4; details['security'].append("✅ Sicherheits-Training (+4)")
    else: details['security'].append("❌ Kein Training (-4)")
    # Value
    val += m.get('_value_points_from_uses',0)
    roi = m.get('roi_expected','')
    if roi in ['high','medium']: val += 7; details['value'].append(f"✅ ROI-Erwartung: {roi} (+7)")
    elif roi == 'low': val += 3; details['value'].append("⚠️ ROI niedrig (+3)")
    else: details['value'].append("❌ Keine ROI-Erwartung (-7)")
    if m.get('measurable_goals') == 'yes': val += 6; details['value'].append("✅ Messbare Ziele (+6)")
    else: details['value'].append("❌ Keine messbaren Ziele (-6)")
    if m.get('pilot_planned') in ['yes','in_progress']: val += 4; details['value'].append("✅ Pilot geplant (+4)")
    else: details['value'].append("❌ Kein Pilot (-4)")
    # Enablement
    skills = m.get('ai_skills','')
    if skills in ['advanced','intermediate']: ena += 8; details['enablement'].append(f"✅ Skills: {skills} (+8)")
    elif skills == 'basic': ena += 4; details['enablement'].append("⚠️ Basis-Skills (+4)")
    else: details['enablement'].append("❌ Keine Skills (-8)")
    if m.get('training_budget') in ['yes','planned']: ena += 7; details['enablement'].append("✅ Training-Budget (+7)")
    else: details['enablement'].append("❌ Kein Training (-7)")
    if m.get('change_management') == 'yes': ena += 6; details['enablement'].append("✅ Change-Management (+6)")
    else: details['enablement'].append("❌ Kein Change-Management (-6)")
    culture = m.get('innovation_culture','')
    if culture in ['strong','moderate']: ena += 4; details['enablement'].append(f"✅ Kultur: {culture} (+4)")
    else: details['enablement'].append("❌ Schwache Kultur (-4)")
    scores = {
        'governance': min(gov, 25) * 4,
        'security': min(sec, 25) * 4,
        'value': min(val, 25) * 4,
        'enablement': min(ena, 25) * 4,
        'overall': round((min(gov,25)+min(sec,25)+min(val,25)+min(ena,25))*4/4)
    }
    log.info("📊 REALISTIC SCORES v4.10.4: Gov=%s Sec=%s Val=%s Ena=%s Overall=%s",
             scores['governance'], scores['security'], scores['value'], scores['enablement'], scores['overall'])
    return {'scores': scores, 'details': details, 'total': scores['overall']}


# ------------------------------ OpenAI --------------------------------------
def _call_openai(prompt: str, system_prompt: str = "Du bist ein KI-Berater.",
                 temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Optional[str]:
    """Chat Completions; unterstützt OPENAI_API_BASE (Azure: header 'api-key')."""
    if not OPENAI_API_KEY:
        log.error("❌ OPENAI_API_KEY not set")
        return None
    if temperature is None: temperature = OPENAI_TEMPERATURE
    if max_tokens is None: max_tokens = OPENAI_MAX_TOKENS
    api_base = (OPENAI_API_BASE or "https://api.openai.com").rstrip("/")
    url = f"{api_base}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    # Azure: 'api-key' statt Authorization
    if "openai.azure.com" in api_base:
        headers["api-key"] = OPENAI_API_KEY
    else:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    try:
        r = requests.post(
            url, headers=headers,
            json={
                "model": OPENAI_MODEL,
                "messages": [{"role": "system", "content": system_prompt},
                             {"role": "user", "content": prompt}],
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
            },
            timeout=OPENAI_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        log.error("❌ OpenAI error: %s", exc)
        return None


# ------------------------------ HTML Repair ---------------------------------
def _clean_html(s: str) -> str:
    if not s: return s
    return s.replace("```html", "").replace("```", "").strip()

def _needs_repair(s: str) -> bool:
    if not s: return True
    sl = s.lower()
    return ("<" not in sl) or not any(t in sl for t in ("<p","<ul","<table","<div","<h4"))

def _repair_html(section: str, s: str) -> str:
    if not ENABLE_REPAIR_HTML:
        return _clean_html(s)
    fixed = _call_openai(
        f"""Konvertiere folgenden Text in **valides HTML** ohne Markdown‑Fences.
Erlaube nur: <p>, <ul>, <ol>, <li>, <table>, <thead>, <tbody>, <tr>, <th>, <td>, <div>, <h4>, <em>, <strong>, <br>.
Abschnitt: {section}. Antworte ausschließlich mit HTML.
---
{s}
""",
        system_prompt="Du bist ein strenger HTML‑Sanitizer. Gib nur validen HTML‑Code aus.",
        temperature=0.0, max_tokens=1200
    )
    return _clean_html(fixed or s)


# -------------------------- Quick‑Wins Parser --------------------------------
_QW_COMPILED = re.compile(
    r"(?:Ersparnis\\s*[:=]\\s*)?"          # optionales Label
    r"(\\d+(?:[.,]\\d{1,2})?)\\s*"          # Zahl (ggf. Dezimal)
    r"(?:h|std\\.?|stunden?)\\s*"          # Einheit
    r"(?:[/\\s]*(?:pro|/)?\\s*Monat)",     # Monatsmarker
    flags=re.IGNORECASE
)

def _sum_hours_from_quick_wins(html: str) -> int:
    """Summiert alle h/Monat‑Angaben robust (Dezimal, Duplikate filtern)."""
    if not html:
        return 0
    text = re.sub(r"<[^>]+>", " ", html)
    total = 0.0
    seen = set()
    for m in _QW_COMPILED.finditer(text):
        span = m.span()
        if span in seen:
            continue
        seen.add(span)
        try:
            val = float(m.group(1).replace(",", "."))
            if 0 < val <= 200:
                total += val
        except ValueError:
            continue
    return int(round(total))


# ----------------------- LLM‑Content Generator ------------------------------
def _generate_content_section(section_name: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    if not ENABLE_LLM_CONTENT:
        return f"<p><em>[{section_name} – LLM disabled]</em></p>"
    branche = briefing.get('branche', 'Unternehmen')
    hauptleistung = briefing.get('hauptleistung', '')
    unternehmensgroesse = briefing.get('UNTERNEHMENSGROESSE_LABEL') or briefing.get('unternehmensgroesse') or ''
    bundesland = briefing.get('BUNDESLAND_LABEL') or briefing.get('bundesland') or ''
    ki_ziele = briefing.get('ki_ziele', [])
    ki_projekte = briefing.get('ki_projekte', '')
    vision = briefing.get('vision_3_jahre', '')

    overall = scores.get('overall', 0); governance = scores.get('governance', 0)
    security = scores.get('security', 0); value = scores.get('value', 0); enablement = scores.get('enablement', 0)

    context = f"Branche: {branche}; Größe: {unternehmensgroesse}; Bundesland: {bundesland}; Hauptleistung/-produkt: {hauptleistung}."
    tone = "Sprache: neutral, dritte Person; keine Wir/Ich‑Formulierungen."
    only_html = "Antworte ausschließlich mit validem HTML (ohne Markdown‑Fences)."

    prompts = {
        'executive_summary': f"""Erstelle eine prägnante Executive Summary. {context}
KI‑Ziele: {', '.join(ki_ziele) if ki_ziele else 'nicht definiert'} • Vision: {vision}
KI‑Reifegrad: Gesamt {overall}/100 • Governance {governance}/100 • Sicherheit {security}/100 • Nutzen {value}/100 • Befähigung {enablement}/100
{tone} {only_html} Verwende nur <p>-Absätze.""",
        'quick_wins': f"""Liste 4–6 **konkrete Quick Wins** (0–90 Tage) für {context}
Jeder Quick Win: Titel, 1–2 Sätze Nutzen, realistische **Ersparnis: … h/Monat**.
Bezug: Hauptleistung {hauptleistung}; Projekte: {ki_projekte or 'keine'}.
{tone} {only_html} Liefere exakt eine <ul>-Liste mit <li>-Einträgen im Format:
<li><strong>Titel:</strong> Beschreibung. <em>Ersparnis: 5 h/Monat</em></li>""",
        'roadmap': f"""Erstelle eine **90‑Tage‑Roadmap** (0–30 Test; 31–60 Pilot; 61–90 Rollout) mit Bezug auf {context}
{tone} {only_html} Pro Phase 3–5 Meilensteine. Format: <h4>Phase …</h4> + <ul>…</ul>.""",
        'business_roi': f"""Erstelle eine **ROI & Payback**‑Tabelle (Jahr 1) für {context}. {tone} {only_html}
Format: <table> mit 2 Spalten (Kennzahl, Wert).""",
        'business_costs': f"""Erstelle eine **Kostenübersicht Jahr 1** für {context}. {tone} {only_html}
Format: <table> mit 2 Spalten (Position, Betrag).""",
        'recommendations': f"""Formuliere 5–7 **Handlungsempfehlungen** mit Priorität [H/M/N] und Zeitrahmen (30/60/90). Kontext: {context}
{tone} {only_html} Format: <ol><li><strong>[H]</strong> Maßnahme — <em>60 Tage</em></li></ol>.""",
        'risks': f"""Erstelle eine **Risikomatrix** (5–7 Risiken) für {context} + EU‑AI‑Act Pflichtenliste.
{tone} {only_html} Format: <table> mit <thead>/<tbody>.""",
        'gamechanger': f"""Skizziere einen **Gamechanger‑Use Case** für {context}. (Idee: 3–4 Sätze; 3 Vorteile; 3 Schritte)
{tone} {only_html} Verwende <h4>, <p>, <ul>.""",
        'roadmap_12m': f"""Erstelle eine **12‑Monats‑Roadmap** in 3 Phasen (0–3/3–6/6–12) für {context}.
{tone} {only_html} Format: <div class="roadmap"><div class="roadmap-phase">…</div></div>.""",
        'data_readiness': f"""Erstelle eine kompakte **Dateninventar & ‑Qualität**‑Übersicht für {context}.
{tone} {only_html} Format: <div class="data-readiness"><h4>…</h4><ul>…</ul></div>.""",
        'org_change': f"""Beschreibe **Organisation & Change** (Governance‑Rollen, Skill‑Programm, Kommunikation) für {context}.
{tone} {only_html} Format: <div class="org-change">…</div>.""",
        'business_case': f"""Erstelle einen kompakten **Business Case (detailliert)** für {context} – Annahmen, Nutzen (J1), Kosten (CapEx/OpEx), Payback, ROI, Sensitivität.
{tone} {only_html} Format: <div class="business-case"> mit Listen & <p>.""",
        'reifegrad_sowhat': f"""Erkläre kurz: **Was heißt der Reifegrad konkret?** Kontext: {context}
Gesamt {overall}/100 • Governance {governance}/100 • Sicherheit {security}/100 • Nutzen {value}/100 • Befähigung {enablement}/100.
{tone} {only_html} Gib 4–6 Bullet‑Points (<ul>) aus."""
    }
    out = _call_openai(
        prompt=prompts[section_name],
        system_prompt="Du bist ein Senior‑KI‑Berater. Antworte nur mit validem HTML.",
        temperature=0.2, max_tokens=OPENAI_MAX_TOKENS
    ) or ""
    out = _clean_html(out)
    if _needs_repair(out):
        out = _repair_html(section_name, out)
    return out or f"<p><em>[{section_name} – generation failed]</em></p>"


def _one_liner(title: str, section_html: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    """Erzeugt One‑liner gemäß Vorlage (Erkenntnis; Wirkung → nächster Schritt)."""
    base = f"""Erzeuge einen prägnanten One‑liner unter der H2‑Überschrift "{title}".
Formel: "Kernaussage; Konsequenz → konkreter nächster Schritt".
Gib nur **eine** Zeile ohne HTML‑Tags zurück."""
    text = _call_openai(base + "\\n---\\n" + re.sub(r"<[^>]+>", " ", section_html)[:1800],
                        system_prompt="Du formulierst prägnante One‑liner auf Deutsch.",
                        temperature=0.1, max_tokens=80)
    return (text or "").strip()


def _split_li_list_to_columns(html_list: str) -> Tuple[str, str]:
    if not html_list: return "<ul></ul>", "<ul></ul>"
    items = re.findall(r"<li[\\s>].*?</li>", html_list, flags=re.DOTALL | re.IGNORECASE)
    if not items:
        lines = [ln.strip() for ln in re.split(r"<br\\s*/?>|\\n", html_list) if ln.strip()]
        items = [f"<li>{ln}</li>" for ln in lines]
    mid = (len(items) + 1) // 2
    return "<ul>" + "".join(items[:mid]) + "</ul>", "<ul>" + "".join(items[mid:]) + "</ul>"


# ----------------------- AI-Act: Datei → HTML‑Blöcke ------------------------
def _try_read(path: str) -> Optional[str]:
    # Datei kann je nach Deployment unter /app oder /mnt/data liegen.
    if os.path.exists(path):
        try:
            return open(path, "r", encoding="utf-8").read()
        except Exception:
            return None
    alt = os.path.join("/mnt/data", os.path.basename(path))
    if os.path.exists(alt):
        try:
            return open(alt, "r", encoding="utf-8").read()
        except Exception:
            return None
    return None

def _md_to_simple_html(md: str) -> str:
    """Sehr schlanker Markdown→HTML Konverter (H3/H4, Listen, Absätze)."""
    if not md:
        return ""
    out: List[str] = []
    in_ul = False
    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            if in_ul:
                out.append("</ul>"); in_ul = False
            continue
        if line.startswith("!["):  # Bilder im PDF weglassen
            continue
        if re.match(r"^\\[\\d+\\]:\\s*https?://", line):  # Fußnoten-Links unterdrücken
            continue
        if line.startswith("#### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h4>{line[5:].strip()}</h4>")
            continue
        if line.startswith("### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h3>{line[4:].strip()}</h3>")
            continue
        if line.startswith(("* ", "- ")):
            if not in_ul:
                in_ul = True; out.append("<ul>")
            out.append(f"<li>{line[2:].strip()}</li>")
            continue
        # Absatz
        if in_ul:
            out.append("</ul>"); in_ul = False
        out.append(f"<p>{line}</p>")
    if in_ul:
        out.append("</ul>")
    return "\\n".join(out)

def _build_ai_act_blocks() -> Dict[str, str]:
    """Liest die AI-Act-Datei, erstellt Summary + CTA + Add-on-Pakete."""
    if not ENABLE_AI_ACT_SECTION:
        return {}
    text = _try_read(AI_ACT_INFO_PATH) or ""
    html = _md_to_simple_html(text) if text else ""
    if not html:
        html = (
            "<h3>Wesentliche Eckdaten</h3>"
            "<ul><li>Gestaffelte Anwendung ab 2025; Kernpflichten 2025–2027.</li>"
            "<li>Frühzeitige Vorbereitung: Risiko- & Governance-Prozesse, Dokumentation, Monitoring.</li></ul>"
        )
    cta = (
        '<div class="callout">'
        "<strong>Auf Wunsch:</strong> eine <em>tabellarische Übersicht</em> mit allen zentralen Terminen, "
        "Übergangsfristen und Praxis‑Checkpoints <strong>speziell für Ihre Zielgruppe</strong> – Fokus "
        f"auf die Phase <strong>{AI_ACT_PHASE_LABEL}</strong>. "
        "Inklusive Verantwortlichkeiten, Nachweisen und Starter‑Checkliste."
        "</div>"
    )
    packages = (
        '<table class="table">'
        "<thead><tr><th>Paket</th><th>Umfang</th><th>Ergebnisse</th></tr></thead><tbody>"
        "<tr><td><strong>Lite: Tabellen‑Kit</strong></td>"
        "<td>Individuelle Termin‑ & Fristen‑Tabelle (2025–2027), 10–15 Praxis‑Checkpoints, Verantwortliche & Nachweise.</td>"
        "<td>PDF/CSV + kurze Einordnung pro Zeile.</td></tr>"
        "<tr><td><strong>Pro: Compliance‑Kit</strong></td>"
        "<td>Alles aus Lite + Vorlagen (Risikomanagement, Logging, Post‑Market‑Monitoring), Kurz‑Guideline zu Pflichten.</td>"
        "<td>Dokupaket (editierbar) + 60‑Tage‑Aktionsplan.</td></tr>"
        "<tr><td><strong>Max: Audit‑Ready</strong></td>"
        "<td>Alles aus Pro + Abgleich mit bestehenden Prozessen, Nachweis‑Mapping, Brown‑Bag‑Session.</td>"
        "<td>Audit‑Map + Meilensteinplan, Q&A‑Session.</td></tr>"
        "</tbody></table>"
    )
    return {
        "AI_ACT_SUMMARY_HTML": html,
        "AI_ACT_TABLE_OFFER_HTML": cta,
        "AI_ACT_ADDON_PACKAGES_HTML": packages,
        "ai_act_phase_label": AI_ACT_PHASE_LABEL,
    }


# ----------------------- Section Composer (+Meta) ----------------------------
def _derive_kundencode(answers: Dict[str, Any], user_email: str) -> str:
    raw = (answers.get("unternehmen") or answers.get("firma") or answers.get("company") or "")[:32]
    if not raw and user_email and "@" in user_email:
        raw = user_email.split("@", 1)[-1].split(".")[0]
    code = re.sub(r"[^A-Za-z0-9]", "", raw.upper())
    return (code[:3] or "KND")

def _version_major_minor(v: str) -> str:
    m = re.match(r"^\\s*(\\d+)\\.(\\d+)", v or "")
    return f"{m.group(1)}.{m.group(2)}" if m else "1.0"

def _build_watermark_text(report_id: str, version_mm: str) -> str:
    return f"Trusted KI‑Check · Report‑ID: {report_id} · v{version_mm}"

def _company_name(answers: Dict[str, Any]) -> str:
    return (answers.get("unternehmen") or answers.get("firma") or answers.get("company") or "—").strip()

def _build_sensitivity_table() -> str:
    return (
        '<table class="table">'
        '<thead><tr><th>Adoption</th><th>Kommentar</th></tr></thead>'
        '<tbody>'
        '<tr><td>100 %</td><td>Planmäßige Wirkung der Maßnahmen.</td></tr>'
        '<tr><td>80 %</td><td>Leichte Abweichungen – Payback +2–3 Monate.</td></tr>'
        '<tr><td>60 %</td><td> konservativ – nur Kernmaßnahmen; Payback länger.</td></tr>'
        '</tbody></table>'
    )

def _generate_content_sections(briefing: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, str]:
    sections: Dict[str, str] = {}

    # Hauptblöcke
    sections['EXECUTIVE_SUMMARY_HTML'] = _generate_content_section('executive_summary', briefing, scores)

    qw_html = _generate_content_section('quick_wins', briefing, scores)
    if _needs_repair(qw_html): qw_html = _repair_html("quick_wins", qw_html)
    left, right = _split_li_list_to_columns(qw_html)
    sections['QUICK_WINS_HTML_LEFT'] = left
    sections['QUICK_WINS_HTML_RIGHT'] = right

    # Summen/€ + Reality‑Note
    total_h = 0
    try: total_h = _sum_hours_from_quick_wins(qw_html)
    except Exception: total_h = 0
    if total_h <= 0:
        try: fb = int(os.getenv("FALLBACK_QW_MONTHLY_H", "0"))
        except Exception: fb = 0
        if fb <= 0:
            try: fb = int(os.getenv("DEFAULT_QW1_H", "0")) + int(os.getenv("DEFAULT_QW2_H", "0"))
            except Exception: fb = 0
        total_h = max(0, fb)
    rate = int(briefing.get("stundensatz_eur") or os.getenv("DEFAULT_STUNDENSATZ_EUR", "60") or 60)
    if total_h > 0:
        sections['monatsersparnis_stunden'] = total_h
        sections['monatsersparnis_eur'] = total_h * rate
        sections['jahresersparnis_stunden'] = total_h * 12
        sections['jahresersparnis_eur'] = total_h * rate * 12
        sections['stundensatz_eur'] = rate
        lo = max(1, int(round(total_h * 0.7))); hi = int(round(total_h * 1.2))
        sections['REALITY_NOTE_QW'] = f"Praxis‑Hinweis: Diese Quick‑Wins sparen ~{lo}–{hi} h/Monat (konservativ geschätzt)."

    # Weitere Abschnitte
    sections['PILOT_PLAN_HTML']     = _generate_content_section('roadmap', briefing, scores)
    sections['ROADMAP_12M_HTML']    = _generate_content_section('roadmap_12m', briefing, scores)
    sections['ROI_HTML']            = _generate_content_section('business_roi', briefing, scores)
    sections['COSTS_OVERVIEW_HTML'] = _generate_content_section('business_costs', briefing, scores)
    sections['BUSINESS_CASE_HTML']  = _generate_content_section('business_case', briefing, scores)
    sections['BUSINESS_SENSITIVITY_HTML'] = _build_sensitivity_table()
    sections['DATA_READINESS_HTML'] = _generate_content_section('data_readiness', briefing, scores)
    sections['ORG_CHANGE_HTML']     = _generate_content_section('org_change', briefing, scores)
    sections['RISKS_HTML']          = _generate_content_section('risks', briefing, scores)
    sections['GAMECHANGER_HTML']    = _generate_content_section('gamechanger', briefing, scores)
    sections['RECOMMENDATIONS_HTML']= _generate_content_section('recommendations', briefing, scores)
    sections['REIFEGRAD_SOWHAT_HTML'] = _generate_content_section('reifegrad_sowhat', briefing, scores)

    # Next Actions (30 Tage)
    nxt = _call_openai(
        """Erstelle 3–7 **Next Actions (30 Tage)** in <ol>.
Jede Zeile: 👤 Owner, ⏱ Aufwand (z. B. ½ Tag), 🎯 Impact (hoch/mittel/niedrig), 📆 Termin (TT.MM.JJJJ) — kurze Maßnahme.
Antwort NUR als <ol>…</ol>.""",
        system_prompt="Du bist PMO‑Lead. Antworte nur mit HTML.",
        temperature=0.2, max_tokens=600
    ) or ""
    sections['NEXT_ACTIONS_HTML'] = _clean_html(nxt) if nxt else "<ol></ol>"

    # One‑liner Leads (unter H2)
    sections['LEAD_EXEC']             = _one_liner("Executive Summary", sections['EXECUTIVE_SUMMARY_HTML'], briefing, scores)
    sections['LEAD_KPI']              = _one_liner("KPI‑Dashboard & Monitoring", "", briefing, scores)
    sections['LEAD_QW']               = _one_liner("Quick Wins (0–90 Tage)", qw_html, briefing, scores)
    sections['LEAD_ROADMAP_90']       = _one_liner("Roadmap (90 Tage – Test → Pilot → Rollout)", sections['PILOT_PLAN_HTML'], briefing, scores)
    sections['LEAD_ROADMAP_12']       = _one_liner("Roadmap (12 Monate)", sections['ROADMAP_12M_HTML'], briefing, scores)
    sections['LEAD_BUSINESS']         = _one_liner("Business Case & Kostenübersicht", sections['ROI_HTML'], briefing, scores)
    sections['LEAD_BUSINESS_DETAIL']  = _one_liner("Business Case (detailliert)", sections['BUSINESS_CASE_HTML'], briefing, scores)
    sections['LEAD_TOOLS']            = _one_liner("Empfohlene Tools (Pro & Open‑Source)", "", briefing, scores)
    sections['LEAD_DATA']             = _one_liner("Dateninventar & ‑Qualität", sections['DATA_READINESS_HTML'], briefing, scores)
    sections['LEAD_ORG']              = _one_liner("Organisation & Change", sections['ORG_CHANGE_HTML'], briefing, scores)
    sections['LEAD_RISKS']            = _one_liner("Risiko‑Assessment & Compliance", sections['RISKS_HTML'], briefing, scores)
    sections['LEAD_GC']               = _one_liner("Gamechanger‑Use Case", sections['GAMECHANGER_HTML'], briefing, scores)
    sections['LEAD_FUNDING']          = _one_liner("Aktuelle Förderprogramme & Quellen", "", briefing, scores)
    sections['LEAD_NEXT_ACTIONS']     = _one_liner("Nächste Schritte (30 Tage)", sections['NEXT_ACTIONS_HTML'], briefing, scores)

    # ---- EU AI Act – Zusammenfassung + Angebot ----
    if ENABLE_AI_ACT_SECTION:
        ai_act = _build_ai_act_blocks()
        sections.update(ai_act)
        sections['LEAD_AI_ACT'] = _one_liner(f"EU AI Act – Überblick & Fristen ({ai_act.get('ai_act_phase_label', AI_ACT_PHASE_LABEL)})",
                                             ai_act.get("AI_ACT_SUMMARY_HTML", ""), briefing, scores)
        sections['LEAD_AI_ACT_ADDON'] = _one_liner("Optionale Vertiefung: EU‑AI‑Act‑Add‑on",
                                                   ai_act.get("AI_ACT_ADDON_PACKAGES_HTML", ""), briefing, scores)

    return sections


# ------------------------------ Mail/Meta ------------------------------------
def _mask_email(addr: Optional[str]) -> str:
    if not addr or not DBG_MASK_EMAILS: return addr or ""
    try:
        name, domain = addr.split("@", 1)
        return f"{name[:3]}***@{domain}" if len(name) > 3 else f"{name}***@{domain}"
    except Exception:
        return "***"

def _admin_recipients() -> List[str]:
    emails: List[str] = []
    for raw in (
        getattr(settings, "ADMIN_EMAILS", None) or os.getenv("ADMIN_EMAILS", ""),
        getattr(settings, "REPORT_ADMIN_EMAIL", None) or os.getenv("REPORT_ADMIN_EMAIL", ""),
        os.getenv("ADMIN_NOTIFY_EMAIL", ""),
    ):
        if raw:
            emails.extend([e.strip() for e in raw.split(",") if e.strip()])
    return list(dict.fromkeys(emails))

def _determine_user_email(db: Session, briefing: Briefing, override: Optional[str]) -> Optional[str]:
    if override: return override
    if getattr(briefing, "user_id", None):
        u = db.get(User, briefing.user_id)
        if u and getattr(u, "email", ""):
            return u.email
    answers = getattr(briefing, "answers", None) or {}
    return answers.get("email") or answers.get("kontakt_email")

def _fetch_pdf_if_needed(pdf_url: Optional[str], pdf_bytes: Optional[bytes]) -> Optional[bytes]:
    if pdf_bytes: return pdf_bytes
    if not pdf_url: return None
    try:
        r = requests.get(pdf_url, timeout=30)
        if r.ok: return r.content
    except Exception:
        return None
    return None

def _send_emails(db: Session, rep: Report, br: Briefing,
                 pdf_url: Optional[str], pdf_bytes: Optional[bytes], run_id: str) -> None:
    best_pdf = _fetch_pdf_if_needed(pdf_url, pdf_bytes)
    attachments_admin: List[Dict[str, Any]] = []
    if best_pdf:
        attachments_admin.append({"filename": f"KI-Status-Report-{getattr(rep,'id', None)}.pdf",
                                  "content": best_pdf, "mimetype": "application/pdf"})
    try:
        bjson = json.dumps(getattr(br, "answers", {}) or {}, ensure_ascii=False, indent=2).encode("utf-8")
        attachments_admin.append({"filename": f"briefing-{br.id}.json", "content": bjson, "mimetype": "application/json"})
    except Exception:
        pass

    # User
    try:
        user_email = _determine_user_email(db, br, getattr(rep, "user_email", None))
        if user_email:
            ok, err = send_mail(
                user_email, "Ihr KI‑Status‑Report ist fertig",
                render_report_ready_email(recipient="user", pdf_url=pdf_url),
                text=None, attachments=([] if pdf_url else attachments_admin[:1])
            )
            if ok: log.info("[%s] 📧 Mail sent to user %s", run_id, _mask_email(user_email))
            else: log.warning("[%s] MAIL_USER failed: %s", run_id, err)
    except Exception as exc:
        log.warning("[%s] MAIL_USER failed: %s", run_id, exc)

    # Admins
    try:
        if os.getenv("ENABLE_ADMIN_NOTIFY", "1") in ("1","true","TRUE","yes","YES"):
            for addr in _admin_recipients():
                ok, err = send_mail(
                    addr, f"Neuer KI‑Status‑Report – Analysis #{rep.analysis_id} / Briefing #{rep.briefing_id}",
                    render_report_ready_email(recipient="admin", pdf_url=pdf_url),
                    text=None, attachments=attachments_admin
                )
                if ok: log.info("[%s] 📧 Admin notify sent to %s", run_id, _mask_email(addr))
                else: log.warning("[%s] MAIL_ADMIN failed for %s: %s", run_id, _mask_email(addr), err)
    except Exception as exc:
        log.warning("[%s] MAIL_ADMIN block failed: %s", run_id, exc)


# ------------------------------ Pipeline -------------------------------------
def analyze_briefing(db: Session, briefing_id: int, run_id: str) -> tuple[int, str, Dict[str, Any]]:
    br = db.get(Briefing, briefing_id)
    if not br: raise ValueError("Briefing not found")

    raw_answers: Dict[str, Any] = getattr(br, "answers", {}) or {}
    answers = (_pass_through := lambda x: x)(raw_answers)
    try:
        from services.answers_normalizer import normalize_answers  # type: ignore
        answers = normalize_answers(raw_answers)
    except Exception:
        pass

    # Scores
    log.info("[%s] Calculating realistic scores (v4.10.4)...", run_id)
    score_wrap = _calculate_realistic_score(answers)
    scores = score_wrap['scores']

    # LLM‑Sections
    log.info("[%s] Generating content sections...", run_id)
    sections = _generate_content_sections(briefing=answers, scores=scores)

    # Labels & Meta
    sections['BRANCHE_LABEL'] = answers.get('BRANCHE_LABEL','')
    sections['BUNDESLAND_LABEL'] = answers.get('BUNDESLAND_LABEL','')
    sections['UNTERNEHMENSGROESSE_LABEL'] = answers.get('UNTERNEHMENSGROESSE_LABEL','')
    sections['JAHRESUMSATZ_LABEL'] = answers.get('JAHRESUMSATZ_LABEL', answers.get('jahresumsatz',''))
    sections['ki_kompetenz'] = answers.get('ki_kompetenz') or answers.get('ki_knowhow','')
    sections['report_date'] = datetime.now().strftime("%d.%m.%Y")
    sections['report_year'] = datetime.now().strftime("%Y")
    sections['transparency_text'] = getattr(settings, "TRANSPARENCY_TEXT", None) or os.getenv("TRANSPARENCY_TEXT", "") or ""
    sections['user_email'] = answers.get('email') or answers.get('kontakt_email') or ""
    sections['company_name'] = _company_name(answers)

    # Scores ins Template
    sections['score_governance'] = scores.get('governance', 0)
    sections['score_sicherheit'] = scores.get('security', 0)
    sections['score_nutzen'] = scores.get('value', 0)
    sections['score_befaehigung'] = scores.get('enablement', 0)
    sections['score_gesamt'] = scores.get('overall', 0)

    # Version/Watermark
    version_full = getattr(settings, "VERSION", "1.0.0")
    version_mm = _version_major_minor(version_full)
    kundencode = _derive_kundencode(answers, sections['user_email'])
    report_id = f"R-{datetime.now().strftime('%Y%m%d')}-{kundencode}"
    sections['kundencode'] = kundencode
    sections['report_id'] = report_id
    sections['report_version'] = version_mm
    sections['WATERMARK_TEXT'] = _build_watermark_text(report_id, version_mm)
    sections['CHANGELOG_SHORT'] = os.getenv("CHANGELOG_SHORT", "—")
    sections['AUDITOR_INITIALS'] = os.getenv("AUDITOR_INITIALS", "KSJ")

    # Optional Research (intern)
    use_fetchers = True
    research_last_updated = ""
    try:
        from services.research_pipeline import run_research  # type: ignore
    except Exception:
        run_research = None  # type: ignore
    if USE_INTERNAL_RESEARCH and run_research:
        try:
            log.info("[%s] Running internal research...", run_id)
            research_blocks = run_research(answers)
            if isinstance(research_blocks, dict):
                for k, v in research_blocks.items():
                    if isinstance(v, str):
                        sections[k] = v
                research_last_updated = str(research_blocks.get("last_updated") or "")
            use_fetchers = False
        except Exception as exc:
            log.warning("[%s] Internal research failed: %s", run_id, exc)
            use_fetchers = True
    sections['research_last_updated'] = research_last_updated or sections['report_date']

    # KPIs/Playbooks (optional)
    try:
        from services.kpi_builder import build_kpis  # type: ignore
        sections['KPI_HTML'] = sections.get('KPI_HTML') or build_kpis(answers)
        sections.setdefault('KPI_BRANCHE_HTML', sections.get('KPI_HTML', ''))
    except Exception:
        pass
    try:
        from services.playbooks import build_playbooks  # type: ignore
        sections['PLAYBOOKS_HTML'] = build_playbooks(answers)
    except Exception:
        pass

    # Render HTML
    log.info("[%s] Rendering final HTML...", run_id)
    result = render(
        br, run_id=run_id, generated_sections=sections,
        use_fetchers=use_fetchers, scores=scores,
        meta={'scores': scores, 'score_details': score_wrap.get('details', {}),
              'research_last_updated': sections['research_last_updated']}
    )

    # Persist
    an = Analysis(
        user_id=br.user_id, briefing_id=briefing_id,
        html=result["html"], meta=result.get("meta", {}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(an); db.commit(); db.refresh(an)
    log.info("[%s] ✅ Analysis created (v4.10.4-gs): id=%s", run_id, an.id)

    return an.id, result["html"], result.get("meta", {})


def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    rep: Optional[Report] = None
    try:
        log.info("[%s] 🚀 Starting analysis v4.10.4-gs for briefing_id=%s", run_id, briefing_id)
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
        br = db.get(Briefing, briefing_id)
        rep = Report(user_id=br.user_id if br else None, briefing_id=briefing_id, analysis_id=an_id, created_at=datetime.now(timezone.utc))
        if hasattr(rep, "user_email"): rep.user_email = _determine_user_email(db, br, email) or ""
        if hasattr(rep, "task_id"): rep.task_id = f"local-{uuid.uuid4()}"
        if hasattr(rep, "status"): rep.status = "pending"
        db.add(rep); db.commit(); db.refresh(rep)

        if DBG_PDF: log.debug("[%s] pdf_render start", run_id)
        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id, "run_id": run_id})
        pdf_url = pdf_info.get("pdf_url"); pdf_bytes = pdf_info.get("pdf_bytes"); pdf_error = pdf_info.get("error")
        if DBG_PDF: log.debug("[%s] pdf_render done url=%s bytes=%s error=%s", run_id, bool(pdf_url), len(pdf_bytes or b''), pdf_error)

        if not pdf_url and not pdf_bytes:
            error_msg = f"PDF failed: {pdf_error or 'no output'}"
            log.error("[%s] %s", run_id, error_msg)
            if hasattr(rep, "status"): rep.status = "failed"
            if hasattr(rep, "email_error_user"): rep.email_error_user = error_msg
            if hasattr(rep, "updated_at"): rep.updated_at = datetime.now(timezone.utc)
            db.add(rep); db.commit()
            raise ValueError(error_msg)

        if hasattr(rep, "pdf_url"): rep.pdf_url = pdf_url
        if hasattr(rep, "pdf_bytes_len") and pdf_bytes: rep.pdf_bytes_len = len(pdf_bytes)
        if hasattr(rep, "status"): rep.status = "done"
        if hasattr(rep, "updated_at"): rep.updated_at = datetime.now(timezone.utc)
        db.add(rep); db.commit(); db.refresh(rep)

        _send_emails(db, rep, br, pdf_url, pdf_bytes, run_id)

    except Exception as exc:
        log.error("[%s] ❌ Analysis failed: %s", run_id, exc, exc_info=True)
        if rep and hasattr(rep, "status"):
            rep.status = "failed"
            if hasattr(rep, "email_error_user"): rep.email_error_user = str(exc)
            if hasattr(rep, "updated_at"): rep.updated_at = datetime.now(timezone.utc)
            db.add(rep); db.commit()
        raise
    finally:
        db.close()
