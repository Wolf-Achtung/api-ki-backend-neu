# file: gpt_analyze.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
v4.10.2 – Analyzer mit Micro‑Polish & EU‑AI‑Act
- One‑liner unter jeder H2 (Erkenntnis; Wirkung → nächster Schritt)
- Watermark & Report‑ID (Deckblatt + Schlussseite)
- EU‑AI‑Act: Zusammenfassung (aus Datei), Timeline‑Tabelle (HTML) + CSV‑Anhang (optional)
- Auto‑Injection: 2 AI‑Act‑Tasks in „Nächste Schritte (30 Tage)“
- Kompatibel zu Settings/ENV, keine DB‑Änderungen
"""
import json, logging, os, re, uuid, requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.db import SessionLocal
from models import Analysis, Briefing, Report, User
from services.report_renderer import render
from services.pdf_client import render_pdf_from_html
from services.email import send_mail
from services.email_templates import render_report_ready_email
from services.ai_act_table import build_timeline  # wichtig
from settings import settings

log = logging.getLogger(__name__)

# ------------------------------ ENV / Config ------------------------------
OPENAI_API_KEY = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = getattr(settings, "OPENAI_MODEL", None) or os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_BASE = getattr(settings, "OPENAI_API_BASE", None) or os.getenv("OPENAI_API_BASE")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "120"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "3000"))

ENABLE_NSFW_FILTER = (os.getenv("ENABLE_NSFW_FILTER", "1") == "1")
ENABLE_QUALITY_GATES = (os.getenv("ENABLE_QUALITY_GATES", "1") == "1")
ENABLE_REALISTIC_SCORES = (os.getenv("ENABLE_REALISTIC_SCORES", "1") == "1")
ENABLE_LLM_CONTENT = (os.getenv("ENABLE_LLM_CONTENT", "1") == "1")
ENABLE_REPAIR_HTML = (os.getenv("ENABLE_REPAIR_HTML", "1") == "1")
USE_INTERNAL_RESEARCH = (os.getenv("USE_INTERNAL_RESEARCH", "1") == "1")

# EU‑AI‑Act
ENABLE_AI_ACT_SECTION = (os.getenv("ENABLE_AI_ACT_SECTION", "1") == "1")
AI_ACT_INFO_PATH = os.getenv("AI_ACT_INFO_PATH", "EU-AI-ACT-Infos-wichtig.txt")
AI_ACT_PHASE_LABEL = os.getenv("AI_ACT_PHASE_LABEL", "2025–2027")
ENABLE_AI_ACT_TABLE = (os.getenv("ENABLE_AI_ACT_TABLE", "1") == "1")
ENABLE_AI_ACT_ATTACH_CSV = (os.getenv("ENABLE_AI_ACT_ATTACH_CSV", "1") == "1")

DBG_PDF = (os.getenv("DEBUG_LOG_PDF_INFO", "1") == "1")
DBG_MASK_EMAILS = (os.getenv("DEBUG_MASK_EMAILS", "1") == "1")

# ------------------------------ Low‑level utils ------------------------------
def _try_read(path: str) -> Optional[str]:
    if os.path.exists(path):
        try: return open(path, "r", encoding="utf-8").read()
        except Exception: return None
    alt = os.path.join("/mnt/data", os.path.basename(path))
    if os.path.exists(alt):
        try: return open(alt, "r", encoding="utf-8").read()
        except Exception: return None
    return None

def _mask_email(addr: Optional[str]) -> str:
    if not addr or not DBG_MASK_EMAILS: return addr or ""
    try:
        name, domain = addr.split("@", 1)
        return f"{name[:3]}***@{domain}" if len(name) > 3 else f"{name}***@{domain}"
    except Exception:
        return "***"

def _admin_recipients() -> List[str]:
    vals = []
    for raw in (
        getattr(settings, "ADMIN_EMAILS", None) or os.getenv("ADMIN_EMAILS", ""),
        getattr(settings, "REPORT_ADMIN_EMAIL", None) or os.getenv("REPORT_ADMIN_EMAIL", ""),
        os.getenv("ADMIN_NOTIFY_EMAIL", ""),
    ):
        if raw: vals.extend([p.strip() for p in raw.split(",") if p.strip()])
    seen=set(); out=[]
    for v in vals:
        if v not in seen: seen.add(v); out.append(v)
    return out

def _determine_user_email(db: Session, briefing: Briefing, override: Optional[str]) -> Optional[str]:
    if override: return override
    if getattr(briefing, "user_id", None):
        u = db.get(User, briefing.user_id)
        if u and getattr(u, "email", ""): return u.email
    answers = getattr(briefing, "answers", None) or {}
    return answers.get("email") or answers.get("kontakt_email")

# ------------------------------ LLM core ------------------------------
def _call_openai(prompt: str, system_prompt: str="Du bist ein KI-Berater.",
                 temperature: Optional[float]=None, max_tokens: Optional[int]=None) -> Optional[str]:
    if not OPENAI_API_KEY:
        log.error("❌ OPENAI_API_KEY not set"); return None
    if temperature is None: temperature = OPENAI_TEMPERATURE
    if max_tokens is None: max_tokens = OPENAI_MAX_TOKENS
    api_base = (OPENAI_API_BASE or "https://api.openai.com").rstrip("/")
    url = f"{api_base}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if "openai.azure.com" in api_base: headers["api-key"] = OPENAI_API_KEY  # warum: Azure
    else: headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    try:
        r = requests.post(url, headers=headers, json={
            "model": OPENAI_MODEL,
            "messages": [{"role":"system","content":system_prompt},{"role":"user","content":prompt}],
            "temperature": float(temperature), "max_tokens": int(max_tokens),
        }, timeout=OPENAI_TIMEOUT)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        log.error("❌ OpenAI error: %s", exc); return None

def _clean_html(s: str) -> str:
    return (s or "").replace("```html","").replace("```","").strip()

def _needs_repair(s: str) -> bool:
    if not s: return True
    sl = s.lower()
    return ("<" not in sl) or not any(t in sl for t in ("<p","<ul","<table","<div","<h4"))

def _repair_html(section: str, s: str) -> str:
    if not ENABLE_REPAIR_HTML: return _clean_html(s)
    fixed = _call_openai(
        f"Konvertiere in **valide HTML‑Struktur** (nur p,ul,ol,li,table,thead,tbody,tr,th,td,div,h4,em,strong,br). Abschnitt: {section}\n---\n{s}",
        system_prompt="Du bist ein strenger HTML‑Sanitizer. Gib nur validen HTML‑Code aus.",
        temperature=0.0, max_tokens=1200
    )
    return _clean_html(fixed or s)

# ------------------------------ Scores (kompakt) ------------------------------
def _map_german_to_english_keys(answers: Dict[str, Any]) -> Dict[str, Any]:
    m: Dict[str, Any] = {}
    m['ai_strategy']     = 'yes' if answers.get('roadmap_vorhanden')=='ja' else ('in_progress' if answers.get('roadmap_vorhanden')=='teilweise' or answers.get('vision_3_jahre') or answers.get('ki_ziele') else 'no')
    m['ai_responsible']  = 'yes' if answers.get('governance_richtlinien') in ['ja','alle'] else ('shared' if answers.get('governance_richtlinien')=='teilweise' else 'no')
    budget_map = {'unter_2000':'under_10k','2000_10000':'under_10k','10000_50000':'10k-50k','50000_100000':'50k-100k','ueber_100000':'over_100k'}
    m['budget']          = budget_map.get(answers.get('investitionsbudget',''), 'none')
    m['goals']           = ', '.join(answers.get('ki_ziele', []) or []) or answers.get('strategische_ziele','')
    anwendungen = answers.get('anwendungsfaelle', []); proj = answers.get('ki_projekte', '')
    m['use_cases']       = (', '.join(anwendungen) + '. ' + proj) if anwendungen else proj
    m['gdpr_aware']      = 'yes' if (answers.get('datenschutz') is True or answers.get('datenschutzbeauftragter')=='ja') else 'no'
    m['data_protection'] = 'comprehensive' if answers.get('technische_massnahmen')=='alle' else ('basic' if answers.get('technische_massnahmen') else 'none')
    m['risk_assessment'] = 'yes' if answers.get('folgenabschaetzung')=='ja' else 'no'
    trainings = answers.get('trainings_interessen', [])
    m['security_training']= 'regular' if trainings and len(trainings)>2 else ('occasional' if trainings else 'no')
    u = m['use_cases']; m['_value_points_from_uses'] = 8 if u and len(u)>50 else (4 if u else 0)
    roi = answers.get('vision_prioritaet','')
    m['roi_expected']    = 'high' if roi in ['marktfuehrerschaft','wachstum'] else ('medium' if roi else 'low')
    m['measurable_goals']= 'yes' if (answers.get('strategische_ziele') or answers.get('ki_ziele')) else 'no'
    m['pilot_planned']   = 'yes' if answers.get('pilot_bereich') else ('in_progress' if answers.get('ki_projekte') else 'no')
    kmap={'hoch':'advanced','mittel':'intermediate','niedrig':'basic','keine':'none'}
    m['ai_skills']       = kmap.get(answers.get('ki_kompetenz',''),'none')
    m['training_budget'] = 'yes' if answers.get('zeitbudget') in ['ueber_10','5_10'] else ('planned' if answers.get('zeitbudget') else 'no')
    ch=answers.get('change_management',''); m['change_management']='yes' if ch=='hoch' else ('planned' if ch in ['mittel','niedrig'] else 'no')
    inv=answers.get('innovationsprozess',''); m['innovation_culture']='strong' if inv in ['mitarbeitende','alle'] else ('moderate' if inv else 'weak')
    return m

def _calculate_realistic_score(ans: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_REALISTIC_SCORES:
        return {'scores': {'governance':0,'security':0,'value':0,'enablement':0,'overall':0}, 'details':{}, 'total':0}
    m=_map_german_to_english_keys(ans); gov=sec=val=ena=0
    if m['ai_strategy'] in ['yes','in_progress']: gov+=8
    if m['ai_responsible'] in ['yes','shared']:   gov+=7
    if m['budget'] in ['10k-50k','50k-100k','over_100k']: gov+=6
    elif m['budget']=='under_10k': gov+=3
    if m['goals'] or m['use_cases']: gov+=4
    if m['gdpr_aware']=='yes': sec+=8
    if m['data_protection'] in ['comprehensive','basic']: sec+=7
    if m['risk_assessment']=='yes': sec+=6
    if m['security_training'] in ['regular','occasional']: sec+=4
    val += m['_value_points_from_uses']
    if m['roi_expected'] in ['high','medium']: val+=7
    elif m['roi_expected']=='low': val+=3
    if m['measurable_goals']=='yes': val+=6
    if m['pilot_planned'] in ['yes','in_progress']: val+=4
    if m['ai_skills'] in ['advanced','intermediate']: ena+=8
    elif m['ai_skills']=='basic': ena+=4
    if m['training_budget'] in ['yes','planned']: ena+=7
    if m['change_management']=='yes': ena+=6
    if m['innovation_culture'] in ['strong','moderate']: ena+=4
    cap=lambda x: min(x,25)*4
    scores={'governance':cap(gov),'security':cap(sec),'value':cap(val),'enablement':cap(ena)}
    scores['overall']=round((scores['governance']+scores['security']+scores['value']+scores['enablement'])/4)
    log.info("📊 REALISTIC SCORES v4.10.2: %s", scores)
    return {'scores':scores,'details':{},'total':scores['overall']}

# ------------------------------ Sections & One‑liner ------------------------------
def _one_liner(title: str, section_html: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    prompt = (f'Erzeuge einen **One‑liner** zu "{title}" – "Kernaussage; Konsequenz → konkreter Schritt". Nur eine Zeile.')
    t = _call_openai(prompt + "\n---\n" + re.sub(r"<[^>]+>"," ",section_html)[:1800],
                     system_prompt="Du formulierst prägnante One‑liner auf Deutsch.",
                     temperature=0.1, max_tokens=80)
    return (t or "").strip()

def _generate_content_section(section_name: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    if not ENABLE_LLM_CONTENT: return f"<p><em>[{section_name} – LLM disabled]</em></p>"
    branche = briefing.get('branche','Unternehmen'); proj = briefing.get('ki_projekte','')
    overall=scores.get('overall',0); gov=scores.get('governance',0); sec=scores.get('security',0); val=scores.get('value',0); ena=scores.get('enablement',0)
    only_html="Antworte ausschließlich mit validem HTML (ohne Markdown‑Fences)."
    prompts={
        'executive_summary': f"""Erstelle eine prägnante Executive Summary. Score gesamt {overall}/100 (Gov {gov}, Sec {sec}, Val {val}, Ena {ena}). {only_html} Nur <p>-Absätze.""",
        'quick_wins': f"""Liste 4–6 Quick Wins (0–90 Tage) für {branche} ({proj or 'keine bestehenden Projekte'}). {only_html} Format: <ul><li><strong>Titel:</strong> Beschreibung. <em>Ersparnis: 5 h/Monat</em></li></ul>.""",
        'roadmap': f"""Erstelle eine 90‑Tage‑Roadmap (Test/Pilot/Rollout). {only_html} Mit <h4> und <ul>. """,
        'roadmap_12m': f"""Erstelle eine 12‑Monats‑Roadmap in 3 Phasen. {only_html} Mit <div> + <h4>/<ul>. """,
        'business_roi': f"""ROI & Payback (Jahr 1) als <table>(Kennzahl,Wert). {only_html}""",
        'business_costs': f"""Kostenübersicht (Jahr 1) als <table>(Position,Betrag). {only_html}""",
        'business_case': f"""Business Case (detailliert): Annahmen/Nutzen/Kosten/Payback/Sensitivität. {only_html}""",
        'data_readiness': f"""Dateninventar & -Qualität kompakt. {only_html}""",
        'org_change': f"""Organisation & Change (Rollen, Skills, Kommunikation). {only_html}""",
        'risks': f"""Risikomatrix + AI‑Act‑Pflichtenliste als <table>. {only_html}""",
        'recommendations': f"""5–7 Handlungsempfehlungen [H/M/N]. {only_html}""",
        'gamechanger': f"""Gamechanger‑Use Case: Idee (3–4 Sätze), 3 Vorteile, 3 Schritte. {only_html}""",
        'reifegrad_sowhat': f"""4–6 Bullet‑Points: Was heißt der Reifegrad konkret? {only_html} <ul>…</ul>"""
    }
    out = _call_openai(prompts[section_name], system_prompt="Senior‑KI‑Berater, nur valides HTML.", temperature=0.2, max_tokens=OPENAI_MAX_TOKENS) or ""
    out=_clean_html(out)
    return _repair_html(section_name, out) if _needs_repair(out) else out

def _split_li_list_to_columns(html_list: str) -> Tuple[str, str]:
    if not html_list: return "<ul></ul>", "<ul></ul>"
    items = re.findall(r"<li[\s>].*?</li>", html_list, flags=re.DOTALL|re.IGNORECASE)
    if not items:
        lines=[ln.strip() for ln in re.split(r"<br\s*/?>|\n", html_list) if ln.strip()]
        items=[f"<li>{ln}</li>" for ln in lines]
    mid=(len(items)+1)//2
    return "<ul>"+"".join(items[:mid])+"</ul>", "<ul>"+"".join(items[mid:])+"</ul>"

def _sum_hours_from_quick_wins(html: str) -> int:
    text=re.sub(r"<[^>]+>"," ", html or "")
    total=0.0; seen=set()
    for m in re.finditer(r"(?:Ersparnis\s*[:=]\s*)?(\d+(?:[.,]\d{1,2})?)\s*(?:h|std\.?|stunden?)\s*(?:[/\s]*(?:pro|/)?\s*Monat)", text, flags=re.I):
        span=m.span()
        if span in seen: continue
        seen.add(span)
        try: val=float(m.group(1).replace(",",".")); 
        except: continue
        if 0<val<=200: total+=val
    return int(round(total))

def _append_tasks_to_ol(ol_html: str, extra_li: List[str]) -> str:
    if not extra_li: return ol_html or "<ol></ol>"
    if not ol_html or "<ol" not in (ol_html.lower()):
        return "<ol>"+"".join(extra_li)+"</ol>"
    m = re.search(r"</ol\s*>", ol_html, flags=re.I)
    if m: return ol_html[:m.start()] + "".join(extra_li) + ol_html[m.start():]
    return "<ol>" + (re.sub(r"</?ol[^>]*>","",ol_html)) + "".join(extra_li) + "</ol>"

# ------------------------------ EU‑AI‑Act Blocks ------------------------------
def _build_ai_act_blocks_from_file() -> Dict[str, Any]:
    if not ENABLE_AI_ACT_SECTION:
        return {}
    text = _try_read(AI_ACT_INFO_PATH) or ""
    # Simple MD→HTML (Absätze + Bullets)
    summary = ""
    if text:
        lines = [ln.strip() for ln in text.splitlines()]
        buf: List[str]=[]; in_ul=False
        for ln in lines:
            if not ln:
                if in_ul: buf.append("</ul>"); in_ul=False
                continue
            if ln.startswith(("* ","- ")):
                if not in_ul: buf.append("<ul>"); in_ul=True
                buf.append(f"<li>{ln[2:].strip()}</li>"); continue
            if in_ul: buf.append("</ul>"); in_ul=False
            buf.append(f"<p>{ln}</p>")
        if in_ul: buf.append("</ul>")
        summary = "\n".join(buf)
    if not summary:
        summary = "<p>Gestaffelte Anwendung 2025–2027 mit Pflichten für Governance, GPAI und Hochrisiko‑Systeme.</p>"

    # CTA Add‑on
    cta = (
        '<div class="callout"><strong>Auf Wunsch:</strong> tabellarische Übersicht aller Termine, '
        f'Übergangsfristen & Praxis‑Checkpoints <strong>für Ihre Zielgruppe</strong> (Fokus {AI_ACT_PHASE_LABEL}).</div>'
    )

    # Pakete (Lite/Pro/Max) – für Upsell im Report
    packages = (
        '<table class="table"><thead><tr><th>Paket</th><th>Umfang</th><th>Ergebnisse</th></tr></thead><tbody>'
        '<tr><td><strong>Lite: Tabellen‑Kit</strong></td><td>Termin‑ & Fristen‑Tabelle (2025–2027), 10–15 Checkpoints, Verantwortliche/Nachweise.</td><td>PDF/CSV + Kurzbewertung je Zeile.</td></tr>'
        '<tr><td><strong>Pro: Compliance‑Kit</strong></td><td>+ Vorlagen (Risiko, Logging, POMM), Kurz‑Guideline.</td><td>Dokupaket (editierbar) + 60‑Tage‑Plan.</td></tr>'
        '<tr><td><strong>Max: Audit‑Ready</strong></td><td>+ Abgleich mit Prozessen, Nachweis‑Mapping, Brown‑Bag.</td><td>Audit‑Map + Meilensteinplan + Q&A.</td></tr>'
        '</tbody></table>'
    )

    # Timeline + CSV + 2 Tasks
    table_html=""; csv_bytes=b""; tasks=[]
    if ENABLE_AI_ACT_TABLE:
        res = build_timeline(text, phase_label=AI_ACT_PHASE_LABEL)
        table_html = res["table_html"]; csv_bytes = res["csv_bytes"]; tasks = res["tasks_li"]

    return {
        "AI_ACT_SUMMARY_HTML": summary,
        "AI_ACT_TABLE_OFFER_HTML": cta,
        "AI_ACT_ADDON_PACKAGES_HTML": packages,
        "AI_ACT_TABLE_HTML": table_html,
        "AI_ACT_CSV_BYTES": csv_bytes,
        "AI_ACT_TASKS_LI": tasks,
        "ai_act_phase_label": AI_ACT_PHASE_LABEL,
    }

# ------------------------------ Meta helpers ------------------------------
def _version_major_minor(v: str) -> str:
    m=re.match(r"^\s*(\d+)\.(\d+)", v or "")
    return f"{m.group(1)}.{m.group(2)}" if m else "1.0"

def _derive_kundencode(answers: Dict[str, Any], user_email: str) -> str:
    raw=(answers.get("unternehmen") or answers.get("firma") or answers.get("company") or "")[:32]
    if not raw and user_email and "@" in user_email: raw=user_email.split("@",1)[-1].split(".")[0]
    return (re.sub(r"[^A-Za-z0-9]","", (raw or "").upper())[:3] or "KND")

def _build_watermark_text(report_id: str, version_mm: str) -> str:
    return f"Trusted KI‑Check · Report‑ID: {report_id} · v{version_mm}"

# ------------------------------ Compose sections ------------------------------
def _compose_sections(briefing: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str,str]:
    sec: Dict[str,str]={}
    sec['EXECUTIVE_SUMMARY_HTML'] = _generate_content_section('executive_summary', briefing, scores)

    qw_html = _generate_content_section('quick_wins', briefing, scores)
    if _needs_repair(qw_html): qw_html=_repair_html("quick_wins", qw_html)
    left,right = _split_li_list_to_columns(qw_html)
    sec['QUICK_WINS_HTML_LEFT']=left; sec['QUICK_WINS_HTML_RIGHT']=right

    total_h = _sum_hours_from_quick_wins(qw_html) or max(0, int(os.getenv("FALLBACK_QW_MONTHLY_H","0")))
    if total_h<=0:
        try: total_h = int(os.getenv("DEFAULT_QW1_H","0")) + int(os.getenv("DEFAULT_QW2_H","0"))
        except Exception: total_h = 0
    rate = int(briefing.get("stundensatz_eur") or os.getenv("DEFAULT_STUNDENSATZ_EUR","60") or 60)
    if total_h>0:
        sec['monatsersparnis_stunden']=total_h
        sec['monatsersparnis_eur']=total_h*rate
        sec['jahresersparnis_stunden']=total_h*12
        sec['jahresersparnis_eur']=total_h*rate*12
        sec['stundensatz_eur']=rate
        lo=max(1, int(round(total_h*0.7))); hi=int(round(total_h*1.2))
        sec['REALITY_NOTE_QW']=f"Praxis‑Hinweis: Diese Quick‑Wins sparen ~{lo}–{hi} h/Monat (konservativ geschätzt)."

    # Weitere Blöcke
    sec['PILOT_PLAN_HTML']     = _generate_content_section('roadmap', briefing, scores)
    sec['ROADMAP_12M_HTML']    = _generate_content_section('roadmap_12m', briefing, scores)
    sec['ROI_HTML']            = _generate_content_section('business_roi', briefing, scores)
    sec['COSTS_OVERVIEW_HTML'] = _generate_content_section('business_costs', briefing, scores)
    sec['BUSINESS_CASE_HTML']  = _generate_content_section('business_case', briefing, scores)
    sec['DATA_READINESS_HTML'] = _generate_content_section('data_readiness', briefing, scores)
    sec['ORG_CHANGE_HTML']     = _generate_content_section('org_change', briefing, scores)
    sec['RISKS_HTML']          = _generate_content_section('risks', briefing, scores)
    sec['GAMECHANGER_HTML']    = _generate_content_section('gamechanger', briefing, scores)
    sec['RECOMMENDATIONS_HTML']= _generate_content_section('recommendations', briefing, scores)
    sec['REIFEGRAD_SOWHAT_HTML'] = _generate_content_section('reifegrad_sowhat', briefing, scores)

    # Next Actions (LLM‑Basis)
    nxt = _call_openai(
        "Erstelle 3–7 Next Actions (30 Tage) als <ol>. Format je Zeile: '👤 Owner, ⏱ Aufwand, 🎯 Impact, 📆 Termin — Maßnahme'. Nur HTML <ol>…</ol>.",
        system_prompt="Du bist PMO‑Lead. Nur valides HTML.", temperature=0.2, max_tokens=600
    ) or ""
    sec['NEXT_ACTIONS_HTML'] = _clean_html(nxt) if nxt else "<ol></ol>"

    # One‑liner Leads
    sec['LEAD_EXEC']             = _one_liner("Executive Summary", sec['EXECUTIVE_SUMMARY_HTML'], briefing, scores)
    sec['LEAD_KPI']              = _one_liner("KPI‑Dashboard & Monitoring", "", briefing, scores)
    sec['LEAD_QW']               = _one_liner("Quick Wins (0–90 Tage)", qw_html, briefing, scores)
    sec['LEAD_ROADMAP_90']       = _one_liner("Roadmap (90 Tage – Test → Pilot → Rollout)", sec['PILOT_PLAN_HTML'], briefing, scores)
    sec['LEAD_ROADMAP_12']       = _one_liner("Roadmap (12 Monate)", sec['ROADMAP_12M_HTML'], briefing, scores)
    sec['LEAD_BUSINESS']         = _one_liner("Business Case & Kostenübersicht", sec['ROI_HTML'], briefing, scores)
    sec['LEAD_BUSINESS_DETAIL']  = _one_liner("Business Case (detailliert)", sec['BUSINESS_CASE_HTML'], briefing, scores)
    sec['LEAD_TOOLS']            = _one_liner("Empfohlene Tools (Pro & Open‑Source)", "", briefing, scores)
    sec['LEAD_DATA']             = _one_liner("Dateninventar & ‑Qualität", sec['DATA_READINESS_HTML'], briefing, scores)
    sec['LEAD_ORG']              = _one_liner("Organisation & Change", sec['ORG_CHANGE_HTML'], briefing, scores)
    sec['LEAD_RISKS']            = _one_liner("Risiko‑Assessment & Compliance", sec['RISKS_HTML'], briefing, scores)
    sec['LEAD_GC']               = _one_liner("Gamechanger‑Use Case", sec['GAMECHANGER_HTML'], briefing, scores)
    sec['LEAD_FUNDING']          = _one_liner("Aktuelle Förderprogramme & Quellen", "", briefing, scores)
    sec['LEAD_NEXT_ACTIONS']     = _one_liner("Nächste Schritte (30 Tage)", sec['NEXT_ACTIONS_HTML'], briefing, scores)

    # EU‑AI‑Act: Summary + Timeline + CTA + Tasks
    if ENABLE_AI_ACT_SECTION:
        ai = _build_ai_act_blocks_from_file()
        sec.update(ai)
        sec['LEAD_AI_ACT'] = _one_liner(
            f"EU AI Act – Überblick & Fristen ({ai.get('ai_act_phase_label', AI_ACT_PHASE_LABEL)})",
            ai.get("AI_ACT_SUMMARY_HTML",""), briefing, scores
        )
        sec['LEAD_AI_ACT_ADDON'] = _one_liner(
            "Optionale Vertiefung: EU‑AI‑Act‑Add‑on",
            ai.get("AI_ACT_ADDON_PACKAGES_HTML",""), briefing, scores
        )
        if ai.get("AI_ACT_TASKS_LI"):
            sec['NEXT_ACTIONS_HTML'] = _append_tasks_to_ol(sec['NEXT_ACTIONS_HTML'], ai["AI_ACT_TASKS_LI"])
    return sec

# ------------------------------ Pipeline ------------------------------
def analyze_briefing(db: Session, briefing_id: int, run_id: str) -> tuple[int, str, Dict[str, Any]]:
    br = db.get(Briefing, briefing_id)
    if not br: raise ValueError("Briefing not found")

    raw = getattr(br, "answers", {}) or {}
    answers = raw
    try:
        from services.answers_normalizer import normalize_answers  # optional
        answers = normalize_answers(raw)
    except Exception:
        pass

    log.info("[%s] Calculating realistic scores (v4.10.2)...", run_id)
    score_wrap = _calculate_realistic_score(answers)
    scores = score_wrap['scores']

    log.info("[%s] Generating content sections...", run_id)
    sections = _compose_sections(briefing=answers, scores=scores)

    # Meta/Labels
    sections['BRANCHE_LABEL'] = answers.get('BRANCHE_LABEL',''); sections['BUNDESLAND_LABEL'] = answers.get('BUNDESLAND_LABEL','')
    sections['UNTERNEHMENSGROESSE_LABEL'] = answers.get('UNTERNEHMENSGROESSE_LABEL','')
    sections['JAHRESUMSATZ_LABEL'] = answers.get('JAHRESUMSATZ_LABEL', answers.get('jahresumsatz',''))
    sections['ki_kompetenz'] = answers.get('ki_kompetenz') or answers.get('ki_knowhow','')
    sections['report_date'] = datetime.now().strftime("%d.%m.%Y"); sections['report_year'] = datetime.now().strftime("%Y")
    sections['transparency_text'] = getattr(settings, "TRANSPARENCY_TEXT", None) or os.getenv("TRANSPARENCY_TEXT","") or ""
    sections['user_email'] = answers.get('email') or answers.get('kontakt_email') or ""

    sections['score_governance']=scores.get('governance',0); sections['score_sicherheit']=scores.get('security',0)
    sections['score_nutzen']=scores.get('value',0); sections['score_befaehigung']=scores.get('enablement',0); sections['score_gesamt']=scores.get('overall',0)

    version_full = getattr(settings, "VERSION", "1.0.0")
    version_mm = _version_major_minor(version_full)
    kundencode = _derive_kundencode(answers, sections['user_email'])
    report_id = f"R-{datetime.now().strftime('%Y%m%d')}-{kundencode}"
    sections['kundencode']=kundencode; sections['report_id']=report_id
    sections['report_version']=version_mm; sections['WATERMARK_TEXT']=_build_watermark_text(report_id, version_mm)
    sections['CHANGELOG_SHORT']=os.getenv("CHANGELOG_SHORT","—"); sections['AUDITOR_INITIALS']=os.getenv("AUDITOR_INITIALS","KSJ")

    # Render
    result = render(
        br, run_id=run_id, generated_sections=sections, use_fetchers=True, scores=scores,
        meta={"scores":scores, "score_details":score_wrap.get("details", {}), "ai_act_csv": bool(sections.get("AI_ACT_CSV_BYTES", b""))}
    )

    an = Analysis(user_id=br.user_id, briefing_id=briefing_id, html=result["html"], meta=result.get("meta", {}),
                  created_at=datetime.now(timezone.utc))
    db.add(an); db.commit(); db.refresh(an)
    log.info("[%s] ✅ Analysis created (v4.10.2): id=%s", run_id, an.id)
    return an.id, result["html"], {"ai_act_csv_bytes": sections.get("AI_ACT_CSV_BYTES", b"")}

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
                 pdf_url: Optional[str], pdf_bytes: Optional[bytes], run_id: str,
                 extra_attachments: Optional[List[Dict[str, Any]]] = None) -> None:
    """Warum: CSV & CTA mitversenden, Admins audit‑ready halten."""
    best_pdf = _fetch_pdf_if_needed(pdf_url, pdf_bytes)
    attachments_admin: List[Dict[str, Any]] = []
    if best_pdf:
        attachments_admin.append({"filename": f"KI-Status-Report-{getattr(rep,'id', None)}.pdf","content": best_pdf,"mimetype":"application/pdf"})
    try:
        bjson = json.dumps(getattr(br, "answers", {}) or {}, ensure_ascii=False, indent=2).encode("utf-8")
        attachments_admin.append({"filename": f"briefing-{br.id}.json","content": bjson,"mimetype":"application/json"})
    except Exception: pass
    if extra_attachments: attachments_admin.extend(extra_attachments)

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

def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    run_id = f"run-{uuid.uuid4().hex[:8]}"; db = SessionLocal()
    rep: Optional[Report] = None
    try:
        log.info("[%s] 🚀 Starting analysis v4.10.2 for briefing_id=%s", run_id, briefing_id)
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
        br = db.get(Briefing, briefing_id)
        rep = Report(user_id=br.user_id if br else None, briefing_id=briefing_id, analysis_id=an_id, created_at=datetime.now(timezone.utc))
        if hasattr(rep,"user_email"): rep.user_email = email or (br and (getattr(br,"answers",{}) or {}).get("email") or "")  # fallback
        if hasattr(rep,"task_id"): rep.task_id = f"local-{uuid.uuid4()}"
        if hasattr(rep,"status"): rep.status = "pending"
        db.add(rep); db.commit(); db.refresh(rep)

        if DBG_PDF: log.debug("[%s] pdf_render start", run_id)
        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id})
        pdf_url = pdf_info.get("pdf_url"); pdf_bytes = pdf_info.get("pdf_bytes"); pdf_error = pdf_info.get("error")
        if DBG_PDF: log.debug("[%s] pdf_render done url=%s bytes=%s error=%s", run_id, bool(pdf_url), len(pdf_bytes or b''), pdf_error)

        if not pdf_url and not pdf_bytes:
            err = f"PDF failed: {pdf_error or 'no output'}"; log.error("[%s] %s", run_id, err)
            if hasattr(rep,"status"): rep.status="failed"
            if hasattr(rep,"email_error_user"): rep.email_error_user = err
            if hasattr(rep,"updated_at"): rep.updated_at = datetime.now(timezone.utc)
            db.add(rep); db.commit(); raise ValueError(err)

        if hasattr(rep,"pdf_url"): rep.pdf_url = pdf_url
        if hasattr(rep,"pdf_bytes_len") and pdf_bytes: rep.pdf_bytes_len = len(pdf_bytes)
        if hasattr(rep,"status"): rep.status = "done"
        if hasattr(rep,"updated_at"): rep.updated_at = datetime.now(timezone.utc)
        db.add(rep); db.commit(); db.refresh(rep)

        extra_atts: List[Dict[str, Any]] = []
        ai_csv: bytes = meta.get("ai_act_csv_bytes") or b""
        if ENABLE_AI_ACT_ATTACH_CSV and ai_csv:
            extra_atts.append({"filename":"AI-Act-Timeline-2025-2027.csv","content": ai_csv,"mimetype":"text/csv"})
        _send_emails(db, rep, br, pdf_url, pdf_bytes, run_id, extra_attachments=extra_atts)

    except Exception as exc:
        log.error("[%s] ❌ Analysis failed: %s", run_id, exc, exc_info=True)
        if rep and hasattr(rep,"status"):
            rep.status="failed"
            if hasattr(rep,"email_error_user"): rep.email_error_user=str(exc)
            if hasattr(rep,"updated_at"): rep.updated_at=datetime.now(timezone.utc)
            db.add(rep); db.commit()
        raise
    finally:
        db.close()
