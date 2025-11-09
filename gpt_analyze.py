# -*- coding: utf-8 -*-
from __future__ import annotations
"""
gpt_analyze.py – v4.14.0-GOLD-PLUS
---------------------------------------------------------------------
🎯 GOLD STANDARD+ OPTIMIERUNGEN (Phase 2):
- ✅ Nutzt prompt_loader.py System (statt hardcoded prompts)
- ✅ Dynamische Dates in Next Actions ({{TODAY}} Variablen)
- ✅ Bessere Fallbacks wenn GPT wenig liefert
- ✅ Quick Wins mit strukturierten Prompts aus /prompts/de/
- ✅ Roadmap mit Variablen-Interpolation
- ✅ ROI Calculator Integration vorbereitet

Version History:
- 4.13.5-gs: Original mit Research-Integration
- 4.14.0-GOLD-PLUS: Prompt-System aktiviert, dynamische Daten
---------------------------------------------------------------------
"""
import json
import logging
import os
import re
import uuid
import html
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from sqlalchemy.orm import Session

try:
    import resend  # type: ignore
except ImportError:
    resend = None  # type: ignore

try:
    from core.db import SessionLocal  # type: ignore
except Exception:  # pragma: no cover
    SessionLocal = None  # type: ignore

from models import Analysis, Briefing, Report, User  # type: ignore
from services.report_renderer import render  # type: ignore
from services.pdf_client import render_pdf_from_html  # type: ignore
from services.email_templates import render_report_ready_email  # type: ignore
from settings import settings  # type: ignore
from services.coverage_guard import analyze_coverage, build_html_report  # type: ignore
from services.prompt_loader import load_prompt  # type: ignore

log = logging.getLogger(__name__)

OPENAI_API_KEY = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = getattr(settings, "OPENAI_MODEL", None) or os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_BASE = getattr(settings, "OPENAI_API_BASE", None) or os.getenv("OPENAI_API_BASE")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "120"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "3000"))

ENABLE_NSFW_FILTER = (os.getenv("ENABLE_NSFW_FILTER", "1") in ("1", "true", "TRUE", "yes", "YES"))
ENABLE_REALISTIC_SCORES = (os.getenv("ENABLE_REALISTIC_SCORES", "1") in ("1", "true", "TRUE", "yes", "YES"))
ENABLE_LLM_CONTENT = (os.getenv("ENABLE_LLM_CONTENT", "1") in ("1", "true", "TRUE", "yes", "YES"))
ENABLE_REPAIR_HTML = (os.getenv("ENABLE_REPAIR_HTML", "1") in ("1", "true", "TRUE", "yes", "YES"))
USE_INTERNAL_RESEARCH = (os.getenv("RESEARCH_PROVIDER", "hybrid") != "disabled")
ENABLE_AI_ACT_SECTION = (os.getenv("ENABLE_AI_ACT_SECTION", "1") in ("1", "true", "TRUE", "yes", "YES"))
USE_PROMPT_SYSTEM = (os.getenv("USE_PROMPT_SYSTEM", "1") in ("1", "true", "TRUE", "yes", "YES"))

AI_ACT_INFO_PATH = os.getenv("AI_ACT_INFO_PATH", "EU-AI-ACT-Infos-wichtig.txt")
AI_ACT_PHASE_LABEL = os.getenv("AI_ACT_PHASE_LABEL", "2025–2027")
GLOSSAR_PATH = os.getenv("GLOSSAR_PATH", "content/glossar-de.md")
INCLUDE_COVERAGE_BOX = os.getenv("INCLUDE_COVERAGE_BOX", "0") in ("1","true","TRUE","yes","YES")

DBG_PDF = (os.getenv("DEBUG_LOG_PDF_INFO", "1") in ("1", "true", "TRUE", "yes", "YES"))
DBG_MASK_EMAILS = (os.getenv("MASK_EMAILS", "1") in ("1", "true", "TRUE", "yes", "YES"))

# Resend Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SMTP_FROM = os.getenv("SMTP_FROM", "bewertung@send.ki-sicherheit.jetzt")

def _send_email_via_resend(to_email: str, subject: str, html_body: str, attachments: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, Optional[str]]:
    """Send email via Resend API with optional attachments"""
    if not resend or not RESEND_API_KEY:
        return False, "Resend not configured"
    
    try:
        resend.api_key = RESEND_API_KEY
        
        # Prepare attachments for Resend
        resend_attachments = []
        if attachments:
            import base64
            for att in attachments:
                if "content" in att and "filename" in att:
                    content_bytes = att["content"] if isinstance(att["content"], bytes) else att["content"].encode("utf-8")
                    resend_attachments.append({
                        "filename": att["filename"],
                        "content": list(content_bytes)  # Resend expects list of bytes
                    })
        
        params = {
            "from": SMTP_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }
        
        if resend_attachments:
            params["attachments"] = resend_attachments
        
        response = resend.Emails.send(params)
        return True, None
        
    except Exception as exc:
        return False, str(exc)


# -------------------- helpers --------------------
def _ellipsize(s: str, max_len: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max(0, max_len - 1)].rstrip() + "…"

_LABEL_MAX = int(os.getenv("LABEL_MAX_LEN", "80"))

# -------------------- NSFW filter ----------------
NSFW_KEYWORDS = {"porn","xxx","sex","nude","naked","adult","nsfw","erotic","escort","dating","porno","nackt","fick","titten","onlyfans","torrent","crack"}
NSFW_DOMAINS = {"xvideos.com","pornhub.com","xnxx.com","redtube.com","youporn.com","onlyfans.com"}

def _is_nsfw_content(url: str, title: str, description: str) -> bool:
    if not ENABLE_NSFW_FILTER:
        return False
    url_lower = (url or "").lower()
    if any(domain in url_lower for domain in NSFW_DOMAINS):
        return True
    text = f"{title} {description}".lower()
    return any(k in text for k in NSFW_KEYWORDS)

def _filter_nsfw(research_data: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_NSFW_FILTER:
        return research_data
    out: Dict[str, Any] = {"tools": [], "funding": []}
    for t in research_data.get("tools", []):
        if not _is_nsfw_content(t.get("url", ""), t.get("title", ""), t.get("description", "")):
            out["tools"].append(t)
    for f in research_data.get("funding", []):
        if not _is_nsfw_content(f.get("url", ""), f.get("title", ""), f.get("description", "")):
            out["funding"].append(f)
    return out

# -------------------- scoring --------------------
def _map_german_to_english_keys(answers: Dict[str, Any]) -> Dict[str, Any]:
    m: Dict[str, Any] = {}
    m["ai_strategy"] = (
        "yes"
        if answers.get("roadmap_vorhanden") == "ja"
        else "in_progress"
        if answers.get("roadmap_vorhanden") == "teilweise"
        or answers.get("vision_3_jahre")
        or answers.get("ki_ziele")
        else "no"
    )
    m["ai_responsible"] = (
        "yes"
        if answers.get("governance_richtlinien") in ["ja", "alle"]
        else "shared"
        if answers.get("governance_richtlinien") == "teilweise"
        else "no"
    )
    budget_map = {
        "unter_2000": "under_10k",
        "2000_10000": "under_10k",
        "10000_50000": "10k-50k",
        "50000_100000": "50k-100k",
        "ueber_100000": "over_100k",
    }
    m["budget"] = budget_map.get(answers.get("investitionsbudget", ""), "none")
    m["goals"] = (", ".join(answers.get("ki_ziele", [])) if answers.get("ki_ziele") else answers.get("strategische_ziele", ""))
    anwendungen = answers.get("anwendungsfaelle", [])
    proj = answers.get("ki_projekte", "")
    m["use_cases"] = (", ".join(anwendungen) + (". " + proj if proj else "")) if anwendungen else proj
    m["gdpr_aware"] = "yes" if (answers.get("datenschutz") is True or answers.get("datenschutzbeauftragter") == "ja") else "no"
    if answers.get("technische_massnahmen") == "alle":
        m["data_protection"] = "comprehensive"
    elif answers.get("technische_massnahmen"):
        m["data_protection"] = "basic"
    else:
        m["data_protection"] = "none"
    m["risk_assessment"] = "yes" if answers.get("folgenabschaetzung") == "ja" else "no"
    trainings = answers.get("trainings_interessen", [])
    m["security_training"] = "regular" if trainings and len(trainings) > 2 else ("occasional" if trainings else "no")
    m["trainings_list"] = ", ".join(trainings) if trainings else ""
    u = m["use_cases"]
    val_points = 8 if u and len(u) > 50 else (4 if u else 0)
    m["_value_points_from_uses"] = val_points
    roi = answers.get("vision_prioritaet", "")
    m["roi_expected"] = "high" if roi in ["marktfuehrerschaft", "wachstum"] else ("medium" if roi else "low")
    m["measurable_goals"] = "yes" if (answers.get("strategische_ziele") or answers.get("ki_ziele")) else "no"
    m["pilot_planned"] = "yes" if answers.get("pilot_bereich") else ("in_progress" if answers.get("ki_projekte") else "no")
    kompetenz_map = {"hoch": "advanced", "mittel": "intermediate", "niedrig": "basic", "keine": "none"}
    m["ai_skills"] = kompetenz_map.get(answers.get("ki_kompetenz", ""), "none")
    m["training_budget"] = "yes" if answers.get("zeitbudget") in ["ueber_10", "5_10"] else ("planned" if answers.get("zeitbudget") else "no")
    change = answers.get("change_management", "")
    m["change_management"] = "yes" if change == "hoch" else ("planned" if change in ["mittel", "niedrig"] else "no")
    innovationsprozess = answers.get("innovationsprozess", "")
    m["innovation_culture"] = "strong" if innovationsprozess in ["mitarbeitende", "alle"] else ("moderate" if innovationsprozess else "weak")
    return m

def _calculate_realistic_score(answers: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_REALISTIC_SCORES:
        return {"scores": {"governance": 0, "security": 0, "value": 0, "enablement": 0, "overall": 0}, "details": {}, "total": 0}
    m = _map_german_to_english_keys(answers)
    gov = sec = val = ena = 0
    details = {"governance": [], "security": [], "value": [], "enablement": []}
    gov += 8 if m.get("ai_strategy") in ["yes", "in_progress"] else 0
    details["governance"].append("✅ KI-Strategie" if m.get("ai_strategy") in ["yes", "in_progress"] else "❌ Keine KI-Strategie")
    gov += 7 if m.get("ai_responsible") in ["yes", "shared"] else 0
    details["governance"].append("✅ KI-Verantwortlicher" if m.get("ai_responsible") in ["yes", "shared"] else "❌ Kein KI-Verantwortlicher")
    budget = m.get("budget", "")
    if budget in ["10k-50k", "50k-100k", "over_100k"]:
        gov += 6; details["governance"].append("✅ Ausreichendes Budget")
    elif budget == "under_10k":
        gov += 3; details["governance"].append("⚠️ Niedriges Budget")
    else:
        details["governance"].append("❌ Kein Budget")
    gov += 4 if (m.get("goals") or m.get("use_cases")) else 0
    sec += 8 if m.get("gdpr_aware") == "yes" else 0
    sec += 7 if m.get("data_protection") in ["comprehensive", "basic"] else 0
    sec += 6 if m.get("risk_assessment") == "yes" else 0
    sec += 4 if m.get("security_training") in ["regular", "occasional"] else 0
    val += m.get("_value_points_from_uses", 0)
    roi = m.get("roi_expected", "")
    val += 7 if roi in ["high", "medium"] else (3 if roi == "low" else 0)
    val += 6 if m.get("measurable_goals") == "yes" else 0
    val += 4 if m.get("pilot_planned") in ["yes", "in_progress"] else 0
    skills = m.get("ai_skills", "")
    ena += 8 if skills in ["advanced", "intermediate"] else (4 if skills == "basic" else 0)
    ena += 7 if m.get("training_budget") in ["yes", "planned"] else 0
    ena += 6 if m.get("change_management") == "yes" else 0
    culture = m.get("innovation_culture", "")
    ena += 4 if culture in ["strong", "moderate"] else 0
    scores = {
        "governance": min(gov, 25) * 4,
        "security": min(sec, 25) * 4,
        "value": min(val, 25) * 4,
        "enablement": min(ena, 25) * 4,
        "overall": round((min(gov, 25) + min(sec, 25) + min(val, 25) + min(ena, 25)) * 4 / 4),
    }
    log.info("📊 REALISTIC SCORES v4.14.0-GOLD-PLUS: Gov=%s Sec=%s Val=%s Ena=%s Overall=%s",
             scores["governance"], scores["security"], scores["value"], scores["enablement"], scores["overall"])
    return {"scores": scores, "details": details, "total": scores["overall"]}

# -------------------- OpenAI client ----------------
def _call_openai(prompt: str, system_prompt: str = "Du bist ein KI-Berater.",
                 temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Optional[str]:
    if not OPENAI_API_KEY:
        log.error("❌ OPENAI_API_KEY not set"); return None
    if temperature is None: temperature = OPENAI_TEMPERATURE
    if max_tokens is None: max_tokens = OPENAI_MAX_TOKENS
    api_base = (OPENAI_API_BASE or "https://api.openai.com").rstrip("/")
    url = f"{api_base}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if "openai.azure.com" in api_base: headers["api-key"] = OPENAI_API_KEY
    else: headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    try:
        r = requests.post(url, headers=headers, json={
            "model": OPENAI_MODEL,
            "messages": [{"role": "system","content": system_prompt},{"role": "user","content": prompt}],
            "temperature": float(temperature), "max_tokens": int(max_tokens),
        }, timeout=OPENAI_TIMEOUT)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        log.error("❌ OpenAI error: %s", exc); return None

# -------------------- HTML repair ----------------
def _clean_html(s: str) -> str:
    if not s: return s
    return s.replace("```html","").replace("```","").strip()

def _needs_repair(s: str) -> bool:
    if not s: return True
    sl = s.lower()
    return ("<" not in sl) or not any(t in sl for t in ("<p","<ul","<table","<div","<h4","<ol"))

def _repair_html(section: str, s: str) -> str:
    if not ENABLE_REPAIR_HTML: return _clean_html(s)
    fixed = _call_openai(
        f"""Konvertiere folgenden Text in **valides HTML** ohne Markdown‑Fences.
Erlaube nur: <p>, <ul>, <ol>, <li>, <table>, <thead>, <tbody>, <tr>, <th>, <td>, <div>, <h4>, <em>, <strong>, <br>.
Abschnitt: {section}. Antworte ausschließlich mit HTML.
---
{s}
""",
        system_prompt="Du bist ein strenger HTML‑Sanitizer. Gib nur validen HTML‑Code aus.",
        temperature=0.0, max_tokens=1200,
    )
    return _clean_html(fixed or s)

# -------------------- Quick‑Wins sum ----------------
_QW_RE = re.compile(r"(?:Ersparnis\s*[:=]\s*)(\d+(?:[.,]\d{1,2})?)\s*(?:h|std\.?|stunden?)\s*(?:[/\s]*(?:pro|/)?\s*Monat)", re.IGNORECASE)
def _sum_hours_from_quick_wins(html_text: str) -> int:
    if not html_text: return 0
    text = re.sub(r"<[^>]+>", " ", html_text)
    total = 0.0; seen = set()
    for m in _QW_RE.finditer(text):
        span = m.span()
        if span in seen: continue
        seen.add(span)
        try:
            val = float(m.group(1).replace(",", "."))
            if 0 < val <= 200: total += val
        except ValueError: continue
    return int(round(total))

# -------------------- Benchmarks ----------------
def _read_json_first(*paths: str) -> Optional[dict]:
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as fh:
                    return json.load(fh)
        except Exception:
            continue
    return None
def _load_branch_benchmarks() -> Dict[str, Any]:
    path1 = os.getenv("BENCHMARKS_PATH", "data/benchmarks.json")
    path2 = "data/benchmarks.json"
    data = _read_json_first(path1, path2)
    return data or {}

def _estimate_size_benchmark(size_label: str) -> Dict[str, int]:
    sl = (size_label or "").lower()
    if "solo" in sl or "freiberuf" in sl:
        return {"avg": 15, "top25": 30}
    if "kleinst" in sl or "2-9" in sl:
        return {"avg": 25, "top25": 45}
    if "klein" in sl or "10-49" in sl:
        return {"avg": 35, "top25": 55}
    if "mittel" in sl or "50-249" in sl:
        return {"avg": 45, "top25": 65}
    if "groß" in sl or "250" in sl:
        return {"avg": 55, "top25": 75}
    return {"avg": 30, "top25": 50}

def _build_benchmark_html(briefing: Dict[str, Any]) -> str:
    benchmarks = _load_branch_benchmarks()
    branche = briefing.get("BRANCHE_LABEL") or briefing.get("branche", "")
    size_label = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", "")
    row_html = []
    if branche:
        b = (branche or "").lower()
        bench = benchmarks.get(b, {})
        if bench and isinstance(bench, dict):
            avg = bench.get("avg", "—")
            top25 = bench.get("top25", "—")
            source = bench.get("source", "Branchenstudie 2024")
            row_html.append(f"<tr><td><strong>Branche</strong>: {html.escape(branche)}</td><td>Ø {avg}% · Top‑25% {top25}%</td><td>{html.escape(source)}</td></tr>")
        else:
            row_html.append(f"<tr><td><strong>Branche</strong>: {html.escape(branche or '—')}</td><td>—</td><td>—</td></tr>")
    if size_label:
        sb = _estimate_size_benchmark(size_label)
        row_html.append(
            f"<tr><td><strong>Unternehmensgröße</strong>: {html.escape(size_label)}</td>"
            f"<td>Ø {sb['avg']}% · Top‑25% {sb['top25']}%</td>"
            f"<td>Schätzung (konservativ)</td></tr>"
        )
    table = (
        "<table class='table'>"
        "<thead><tr><th>Vergleich</th><th>Wert</th><th>Quelle</th></tr></thead>"
        f"<tbody>{''.join(row_html)}</tbody>"
        "</table>"
        "<p class='small muted'>Hinweis: Größenwerte sind konservative Schätzungen (mangels belastbarer Daten). Branchenwerte stammen aus aktuellen Studien; siehe Quelle.</p>"
    )
    return table

# -------------------- Quellenkasten & Links ----------------
_LINK_RE = re.compile(r"""<a\s+[^>]*href=['"]([^'"]+)['"][^>]*>(.*?)</a>""", re.IGNORECASE | re.DOTALL)

def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "")

def _table_rows(html_block: str) -> List[str]:
    return re.findall(r"<tr[^>]*>(.*?)</tr>", html_block or "", flags=re.IGNORECASE | re.DOTALL)

def _tds(row_html: str) -> List[str]:
    return re.findall(r"<td[^>]*>(.*?)</td>", row_html or "", flags=re.IGNORECASE | re.DOTALL)

def _extract_links_from_tools_table(table_html: str) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for row in _table_rows(table_html):
        cells = _tds(row)
        if not cells: continue
        title = html.unescape(_strip_tags(cells[0])).strip()
        m = _LINK_RE.search(row)
        if m:
            href = m.group(1).strip()
            label = _ellipsize(title or urlparse(href).netloc, _LABEL_MAX)
            if href: items.append((href, label))
    return items

def _extract_links_from_generic_html(block: str) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for href, label in _LINK_RE.findall(block or ""):
        t = _strip_tags(label).strip()
        if not t or t.lower() in {"quelle","details","link","mehr","info"}:
            t = urlparse(href).netloc or href
        items.append((href.strip(), _ellipsize(html.unescape(t), _LABEL_MAX)))
    return items

def _unique_by_href(pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen = set(); out: List[Tuple[str, str]] = []
    for href, label in pairs:
        if href in seen: continue
        seen.add(href); out.append((href, label))
    return out

_OFFICIAL = {"bmwk.de","bund.de","bmi.bund.de","bmbf.de","bmwi.de","foerderdatenbank.de","europa.eu","ec.europa.eu","commission.europa.eu","berlin.de","service.berlin.de","bsi.bund.de","bafin.de"}
_MEDIA = {"heise.de","golem.de","computerwoche.de","handelsblatt.com","t3n.de","gruenderszene.de","welt.de","faz.net","zeit.de"}
_VENDOR = {"microsoft.com","azure.microsoft.com","openai.com","google.com","cloud.google.com","aws.amazon.com","meta.com","huggingface.co"}

def _domain_category(dom: str) -> int:
    d = dom.lower()
    if any(d == x or d.endswith("." + x) for x in _OFFICIAL): return 0
    if any(d == x or d.endswith("." + x) for x in _MEDIA): return 1
    if any(d == x or d.endswith("." + x) for x in _VENDOR): return 2
    return 1

def _sort_pairs(pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    def key(x: Tuple[str, str]):
        dom = urlparse(x[0]).netloc
        return (_domain_category(dom), x[1].lower())
    return sorted(pairs, key=key)

def _rewrite_table_links_with_labels(table_html: str) -> str:
    if not table_html: return table_html
    out_rows = []
    for row in _table_rows(table_html):
        cells = _tds(row)
        if not cells:
            out_rows.append(row); continue
        title = _ellipsize(html.unescape(_strip_tags(cells[0])).strip(), _LABEL_MAX)
        def repl(m):
            href = m.group(1)
            return f"<a href='{href}'>{html.escape(title)}</a>"
        row2 = re.sub(_LINK_RE, repl, row, count=0)
        out_rows.append(row2)
    body = "".join(f"<tr>{r}</tr>" for r in out_rows)
    if "<tbody" in table_html.lower():
        return re.sub(r"(<tbody[^>]*>).*(</tbody>)", r"\1"+body+r"\2", table_html, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"<table[^>]*>.*</table>", lambda _: "<table>"+body+"</table>", table_html, flags=re.IGNORECASE | re.DOTALL)

def _build_sources_box_html(sections: Dict[str, str], last_updated: str) -> str:
    pairs: List[Tuple[str, str]] = []
    if sections.get("TOOLS_HTML"):
        pairs += _extract_links_from_tools_table(sections["TOOLS_HTML"])
    if sections.get("FOERDERPROGRAMME_HTML"):
        pairs += _extract_links_from_tools_table(sections["FOERDERPROGRAMME_HTML"])
    for key in ("EXECUTIVE_SUMMARY_HTML","AI_ACT_SUMMARY_HTML","BUSINESS_CASE_HTML","ROI_HTML"):
        if sections.get(key):
            pairs += _extract_links_from_generic_html(sections[key])
    pairs = _unique_by_href(pairs)
    if not pairs:
        return f"<div class='callout'><strong>Aktualisierung:</strong> Stand der Quellen: {html.escape(last_updated)}.</div>"
    pairs = _sort_pairs(pairs)
    lis = []
    for href, label in pairs:
        dom = urlparse(href).netloc.lower()
        label_clean = html.escape(label)
        lis.append(f"<li><a href='{href}'>{label_clean}</a> <span class='small muted'>({dom})</span></li>")
    ul = "<ul>" + "".join(lis) + "</ul>"
    return ("<div class='fb-section'>"
            "<div class='fb-head'><span class='fb-step'>Quellen</span><h3 class='fb-title'>Quellen & Aktualisierung</h3></div>"
            f"<p class='small muted'>Stand der externen Quellen: {html.escape(last_updated)}.</p>{ul}"
            "</div>")

# -------------------- Kreativ-Tools ----------------
def _read_text(path: str) -> Optional[str]:
    if not path: return None
    if os.path.exists(path):
        try: return open(path, "r", encoding="utf-8").read()
        except Exception: return None
    alt = os.path.join("/mnt/data", os.path.basename(path))
    if os.path.exists(alt):
        try: return open(alt, "r", encoding="utf-8").read()
        except Exception: return None
    return None

def _parse_kreativ_tools(raw: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for line in (raw or "").splitlines():
        ln = line.strip()
        if not ln or ln.startswith("#"): continue
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 2 and parts[1].startswith(("http://","https://")):
            label = parts[0]; href = parts[1]
            if len(parts) >= 3 and parts[2]: label = f"{label} – {parts[2]}"
            out.append((label, href)); continue
        m = re.match(r"^(.*?)[\-\u2013\u2014]\s*(https?://\S+)$", ln)
        if m: out.append((m.group(1).strip(), m.group(2).strip())); continue
        m = re.match(r"^\[(.+?)\]\((https?://[^)]+)\)$", ln)
        if m: out.append((m.group(1).strip(), m.group(2).strip())); continue
        m = re.search(r"(https?://\S+)", ln)
        if m:
            href = m.group(1).strip(); label = urlparse(href).netloc
            out.append((label, href)); continue
        out.append((ln, ""))
    return out

def _build_kreativ_tools_html(path: str, report_date: str) -> str:
    raw = _read_text(path) or ""
    pairs = _parse_kreativ_tools(raw)
    if not pairs: return ""
    items = []
    for label, href in pairs:
        label_html = html.escape(_ellipsize(label, _LABEL_MAX))
        if href: items.append(f"<li><a href='{href}'>{label_html}</a></li>")
        else: items.append(f"<li>{label_html}</li>")
    ul = "<ul>" + "".join(items) + "</ul>"
    return ("<div class='fb-section'>"
            "<div class='fb-head'><span class='fb-step'>Kreativ</span><h3 class='fb-title'>Kreativ‑Tools (kuratierte Liste)</h3></div>"
            f"{ul}<p class='small muted'>Stand: {html.escape(report_date)} · Quelle: {html.escape(os.path.basename(path))}</p>"
            "</div>")

# -------------------- Werkbank ----------------
def _build_werkbank_html() -> str:
    def ul(items: List[str]) -> str:
        return "<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in items) + "</ul>"
    blocks = []
    blocks.append("<h3>RAG‑Stack (Open‑Source & lokal)</h3>" + ul([
        "LLM: Mistral 7B / Llama‑3.x (lokal oder gehostet)",
        "Embeddings: E5 / Instructor",
        "Vektordatenbank: FAISS / Chroma",
        "Orchestrierung: LangChain / LiteLLM",
        "Guardrails & Moderation: Pydantic‑Validatoren / Rebuff",
        "Beobachtbarkeit: OpenTelemetry Hooks (einfach)"
    ]))
    blocks.append("<h3>Azure‑only Stack (Enterprise/DSGVO)</h3>" + ul([
        "Azure OpenAI (Chat Completions / Assistants)",
        "Azure Cognitive Search (RAG)",
        "Functions + Blob Storage (Pipelines & Daten)",
        "Content Safety + Key Vault (Sicherheit)",
        "Azure Monitor/App Insights (Monitoring)"
    ]))
    blocks.append("<h3>Schneller Assistenz‑Stack (SaaS)</h3>" + ul([
        "LLM: OpenAI GPT‑4o",
        "Automatisierung: Make/Zapier",
        "Wissensablage: Notion/Confluence",
        "Kommunikation: Slack/MS Teams Bot",
        "Formulare: Tally/Typeform für Intake"
    ]))
    note = "<p class='small muted'>Hinweis: Stacks sind exemplarisch und anpassbar; Auswahl hängt von Datenschutz, Budget und IT‑Landschaft ab.</p>"
    return "<div class='fb-section'>" + "".join(blocks) + note + "</div>"

# -------------------- Score Bars (CSS-only) ----------------
def _build_score_bars_html(scores: Dict[str, Any]) -> str:
    def row(label: str, key: str) -> str:
        val = 0
        try:
            val = max(0, min(100, int(float(scores.get(key, 0)))))
        except Exception:
            val = 0
        return (
            f"<tr><td style='padding:6px 8px;width:160px'>{html.escape(label)}</td>"
            f"<td style='padding:6px 8px;width:100%'>"
            f"<div style='height:8px;border-radius:6px;background:#eef2ff;overflow:hidden'>"
            f"<i style='display:block;height:100%;width:{val}%;background:linear-gradient(90deg,#3b82f6,#2563eb)'></i>"
            f"</div>"
            f"<div style='font-size:10px;color:#475569'>{val}/100</div>"
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

# -------------------- Werkbank (dynamisch nach Branche/Größe) ----------------
def _build_werkbank_html_dynamic(answers: Dict[str, Any]) -> str:
    path = os.getenv("STARTER_STACKS_PATH", "").strip()
    branche = (answers.get("BRANCHE_LABEL") or answers.get("branche") or "").strip().lower()
    size = (answers.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse") or "").strip().lower()

    def _safe_ul(items):
        return "<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in (items or [])) + "</ul>"

    if path and os.path.exists(path):
        try:
            import json as _json
            data = _json.load(open(path, "r", encoding="utf-8"))
            common = (data.get("common") or {})
            bran = (data.get(branche) or {})
            blocks = []
            if size in (common or {}):
                blocks.append("<h3>Common</h3>" + _safe_ul(common[size]))
            if size in (bran or {}):
                title = (branche.capitalize() if branche else "Branche")
                blocks.append(f"<h3>{html.escape(title)}</h3>" + _safe_ul(bran[size]))
            if blocks:
                note = "<p class='small muted'>Stacks aus Starter‑Registry · anpassbar je Datenschutz/Budget/IT‑Landschaft.</p>"
                return "<div class='fb-section'>" + "".join(blocks) + note + "</div>"
        except Exception:
            pass
    return _build_werkbank_html()

# -------------------- Feedback-Box ----------------
def _build_feedback_box(feedback_url: str, report_date: str) -> str:
    if not feedback_url:
        return ""
    link = html.escape(feedback_url.strip())
    return (
        "<div class='fb-section'>"
        "<div class='fb-head'><span class='fb-step'>Feedback</span><h3 class='fb-title'>Ihre Meinung zählt</h3></div>"
        "<p>Was war hilfreich, was fehlt? Teilen Sie uns Ihr Feedback mit – es dauert weniger als 2 Minuten.</p>"
        f"<p><a href='{link}' target='_blank' rel='noopener'>Feedback geben</a> "
        f"<span class='small muted'>· Stand: {html.escape(report_date)}</span></p>"
        "</div>"
    )

# -------------------- 🎯 NEW: Estimate hourly rate from revenue ----------------
def _estimate_hourly_rate_from_revenue(briefing: Dict[str, Any]) -> int:
    """
    Estimate a realistic hourly rate based on company size and revenue.
    This is needed because the questionnaire doesn't have a 'stundensatz_eur' field,
    but we need it for ROI calculations.
    
    Returns: Estimated hourly rate in EUR
    """
    # First check if there's an explicit hourly rate in the briefing
    explicit_rate = briefing.get("stundensatz_eur")
    if explicit_rate:
        try:
            return int(explicit_rate)
        except (ValueError, TypeError):
            pass
    
    # Get company size and revenue
    size = briefing.get("unternehmensgroesse", "").lower()
    revenue_label = briefing.get("jahresumsatz", "").lower()
    
    # Solo/Freelancer baseline
    if "solo" in size or "freiberuf" in size or "einzelunt" in size:
        return 55
    
    # Estimate based on revenue bands
    # Small companies (under 100k)
    if "unter" in revenue_label and "100" in revenue_label:
        return 50
    
    # 100k-500k range
    if any(x in revenue_label for x in ["100", "250", "500"]) and "mio" not in revenue_label:
        return 65
    
    # 500k-1M range
    if "500" in revenue_label or ("1" in revenue_label and "mio" in revenue_label):
        return 75
    
    # 1M-5M range
    if any(x in revenue_label for x in ["2", "3", "4", "5"]) and "mio" in revenue_label:
        return 85
    
    # 5M+ range
    if any(x in revenue_label for x in ["10", "20", "50"]) and "mio" in revenue_label:
        return 95
    
    # Default fallback
    try:
        return int(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60"))
    except (ValueError, TypeError):
        return 60

# -------------------- 🎯 NEW: Build prompt variables ----------------
def _build_prompt_vars(briefing: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build complete variable dict for prompt interpolation.
    Extended to 60+ variables based on comprehensive analysis of:
    - Questionnaire fields (formbuilder_de_SINGLE_FULL_15_33_03.js)
    - Prompt templates (prompts/de/*.md)
    - PDF template (pdf_template.html)
    """
    now = datetime.now()
    today = now.strftime("%d.%m.%Y")
    date_30d = (now + timedelta(days=30)).strftime("%d.%m.%Y")
    report_year = now.strftime("%Y")
    
    # ===== BLOCK 1: Time & Date =====
    # Used in next_actions_de.md for dynamic deadlines
    base_vars = {
        "TODAY": today,
        "DATE_30D": date_30d,
        "report_date": today,
        "report_year": report_year,
    }
    
    # ===== BLOCK 2: Company Basics =====
    # Core company information needed across all prompts
    # Both uppercase and lowercase variants for compatibility
    base_vars.update({
        "BRANCHE": briefing.get("branche", ""),
        "branche": briefing.get("branche", ""),
        "BRANCHE_LABEL": briefing.get("BRANCHE_LABEL") or briefing.get("branche", ""),
        "UNTERNEHMENSGROESSE": briefing.get("unternehmensgroesse", ""),
        "unternehmensgroesse": briefing.get("unternehmensgroesse", ""),
        "UNTERNEHMENSGROESSE_LABEL": briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", ""),
        "BUNDESLAND_LABEL": briefing.get("BUNDESLAND_LABEL") or briefing.get("bundesland", ""),
        "bundesland": briefing.get("bundesland", ""),
        "HAUPTLEISTUNG": briefing.get("hauptleistung", ""),
        "JAHRESUMSATZ_LABEL": briefing.get("JAHRESUMSATZ_LABEL", briefing.get("jahresumsatz", "")),
    })
    
    # ===== BLOCK 3: Strategy & Vision =====
    # Strategic direction and goals
    hemmnisse_raw = briefing.get("ki_hemmnisse", [])  # Fixed: was "hemmnisse", should be "ki_hemmnisse"
    if not hemmnisse_raw:
        hemmnisse_raw = briefing.get("hemmnisse", [])  # Fallback for legacy data
    
    base_vars.update({
        "VISION_PRIORITAET": briefing.get("vision_3_jahre", ""),
        "PROJEKTZIEL": ", ".join(briefing.get("ki_ziele", [])) if briefing.get("ki_ziele") else briefing.get("strategische_ziele", ""),
        "KI_KNOWHOW": briefing.get("ki_kompetenz", ""),
        "KI_HEMMNISSE": ", ".join(hemmnisse_raw) if isinstance(hemmnisse_raw, list) else hemmnisse_raw,
    })
    
    # ===== BLOCK 4: Resources =====
    # Budget and time availability
    base_vars.update({
        "INVESTITIONSBUDGET": briefing.get("investitionsbudget", ""),
        "ZEITBUDGET": briefing.get("zeitbudget", ""),
    })
    
    # ===== BLOCK 5: Data & Quality (NEW!) =====
    # Critical for data_readiness_de.md prompt
    base_vars.update({
        "DATENQUELLEN": briefing.get("datenquellen", "Nicht spezifiziert"),
        "DATENQUALITAET": briefing.get("datenqualitaet", "Nicht bewertet"),
        "LOESCHREGELN": briefing.get("loeschregeln", "Nicht dokumentiert"),
        "PROZESSE_PAPIERLOS": briefing.get("prozesse_papierlos", "Nicht angegeben"),
    })
    
    # ===== BLOCK 6: Training & Culture (NEW!) =====
    # Critical for org_change_de.md prompt
    base_vars.update({
        "TRAININGS_INTERESSEN": briefing.get("trainings_interessen", "Nicht spezifiziert"),
        "INNOVATIONSKULTUR": briefing.get("innovationskultur", "Nicht bewertet"),
    })
    
    # ===== BLOCK 7: Quick Wins & ROI (EXTENDED!) =====
    # Calculate hourly rate using our smart estimation function
    stundensatz_eur = _estimate_hourly_rate_from_revenue(briefing)
    
    # Quick Win hours from environment or defaults
    qw1_h = int(os.getenv("DEFAULT_QW1_H", "20"))
    qw2_h = int(os.getenv("DEFAULT_QW2_H", "15"))
    
    # Calculate monthly and yearly savings
    monatsersparnis_stunden = qw1_h + qw2_h
    monatsersparnis_eur = monatsersparnis_stunden * stundensatz_eur
    jahresersparnis_stunden = monatsersparnis_stunden * 12
    jahresersparnis_eur = monatsersparnis_eur * 12
    
    base_vars.update({
        "qw1_monat_stunden": qw1_h,
        "qw2_monat_stunden": qw2_h,
        "stundensatz_eur": stundensatz_eur,
        "monatsersparnis_stunden": monatsersparnis_stunden,
        "monatsersparnis_eur": monatsersparnis_eur,
        "jahresersparnis_stunden": jahresersparnis_stunden,
        "jahresersparnis_eur": jahresersparnis_eur,
    })
    
    # ===== BLOCK 8: Business Case (NEW!) =====
    # Investment estimates for business_case_de.md
    # Conservative estimates based on company size
    try:
        umsatz_label = briefing.get("jahresumsatz", "").lower()
        if "mio" in umsatz_label:
            capex_realistisch = 15000
            opex_realistisch = 3000
        elif any(x in umsatz_label for x in ["500", "1"]):
            capex_realistisch = 8000
            opex_realistisch = 2000
        else:
            capex_realistisch = 5000
            opex_realistisch = 1500
    except Exception:
        capex_realistisch = 5000
        opex_realistisch = 1500
    
    base_vars.update({
        "capex_realistisch_eur": capex_realistisch,
        "capex_konservativ_eur": int(capex_realistisch * 1.3),
        "opex_realistisch_eur": opex_realistisch,
        "opex_konservativ_eur": int(opex_realistisch * 1.2),
    })
    
    # ===== BLOCK 9: Scores (CRITICAL FIX!) =====
    # Both English AND German variants needed!
    # English: Used in code (score_security, score_value)
    # German: Used in prompts (score_sicherheit, score_nutzen)
    base_vars.update({
        # English variants (code)
        "score_governance": scores.get("governance", 0),
        "score_security": scores.get("security", 0),
        "score_value": scores.get("value", 0),
        "score_enablement": scores.get("enablement", 0),
        "score_overall": scores.get("overall", 0),
        
        # German variants (prompts)
        "score_sicherheit": scores.get("security", 0),
        "score_nutzen": scores.get("value", 0),
        "score_befaehigung": scores.get("enablement", 0),
        "score_gesamt": scores.get("overall", 0),
        
        # Special alias for PDF template
        "score_wertschoepfung": scores.get("value", 0),  # Alias for score_value in template
    })
    
    # ===== BLOCK 10: JSON Dumps =====
    # Complex data structures for advanced prompts
    base_vars.update({
        "ALL_ANSWERS_JSON": json.dumps(briefing, ensure_ascii=False, indent=2)[:2000],
        "BRIEFING_JSON": json.dumps(briefing, ensure_ascii=False, indent=2)[:2000],
        "SCORING_JSON": json.dumps(scores, ensure_ascii=False, indent=2),
        "BUSINESS_JSON": json.dumps({
            "stundensatz": stundensatz_eur,
            "monatsersparnis_h": monatsersparnis_stunden,
            "jahresersparnis_eur": jahresersparnis_eur,
            "capex": capex_realistisch,
            "opex": opex_realistisch
        }, ensure_ascii=False, indent=2),
    })
    
    return base_vars
# -------------------- 🎯 NEW: Better fallbacks when GPT fails ----------------
def _get_fallback_content(section_key: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    """Provide meaningful fallback content if GPT fails or returns too little"""
    branche = briefing.get("BRANCHE_LABEL") or briefing.get("branche", "Ihr Unternehmen")
    size = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", "")
    
    fallbacks = {
        "quick_wins": f"""<ul>
<li><strong>E-Mail-Entwürfe automatisieren:</strong> Automatische Vorschläge für Standard-Antworten und Textbausteine. <em>Ersparnis: 20 h/Monat</em></li>
<li><strong>Meeting-Protokolle mit KI:</strong> Automatische Transkription und Zusammenfassung von Besprechungen. <em>Ersparnis: 15 h/Monat</em></li>
<li><strong>Dokumenten-Recherche beschleunigen:</strong> Semantische Suche in Ihrer Wissensdatenbank statt manuelles Durchsuchen. <em>Ersparnis: 12 h/Monat</em></li>
<li><strong>Social Media Posts generieren:</strong> KI-gestützte Content-Vorschläge für LinkedIn, Instagram und andere Kanäle. <em>Ersparnis: 8 h/Monat</em></li>
</ul>
<p class="small muted">Angepasst an {branche} · {size}</p>""",
        
        "roadmap": f"""<div class="roadmap">
<h4>Phase 1: Test & Schulung (0-30 Tage)</h4>
<ul>
<li>Stakeholder-Kick-off und Use-Case-Priorisierung durchführen</li>
<li>Tool-Evaluierung (3-5 Kandidaten) inklusive Datenschutz-Check</li>
<li>Team-Training durchführen: Prompt Engineering Basics (1-2 Tage Workshop)</li>
</ul>

<h4>Phase 2: Pilotierung (31-60 Tage)</h4>
<ul>
<li>Pilot-Projekt mit 3-5 Power-Anwendern starten</li>
<li>Wöchentliche Review-Meetings etablieren und Feedback-Loop aufbauen</li>
<li>Erste ROI-Messung durchführen und Lessons Learned dokumentieren</li>
</ul>

<h4>Phase 3: Rollout (61-90 Tage)</h4>
<ul>
<li>Schrittweise Erweiterung auf weitere Teams und Abteilungen</li>
<li>Governance-Framework und Nutzungsrichtlinien etablieren</li>
<li>90-Tage-Review durchführen und nächste Use Cases planen</li>
</ul>
</div>""",
        
        "roadmap_12m": f"""<div class="roadmap">
<div class="roadmap-phase">
<h3>Quartale 1-2 (Monate 0-6): Foundation Building</h3>
<ul>
<li><strong>Q1:</strong> KI-Strategie entwickeln, Tool-Auswahl treffen, erste Pilots starten</li>
<li><strong>Q2:</strong> Skalierung auf 2-3 Abteilungen, strukturiertes Training-Programm aufsetzen</li>
</ul>
</div>

<div class="roadmap-phase">
<h3>Quartale 3-4 (Monate 7-12): Scale & Optimize</h3>
<ul>
<li><strong>Q3:</strong> Organisations-weiter Rollout, Governance-Strukturen etablieren</li>
<li><strong>Q4:</strong> Advanced Use Cases implementieren, ROI-Optimierung, Roadmap 2.0 planen</li>
</ul>
</div>
</div>""",
        
        "next_actions": f"""<ol>
<li><strong>KI-Manager:in</strong> — Stakeholder-Kick-off organisieren und Top-3 Use Cases priorisieren<br>
⏱ 2 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=14)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3-5 priorisierte Use Cases dokumentiert und abgestimmt</li>

<li><strong>IT-Leitung</strong> — Tool-Evaluierung durchführen (inkl. DSGVO-Check und Security-Review)<br>
⏱ 3 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=21)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3 Tools evaluiert, 1 konkrete Empfehlung mit Begründung</li>

<li><strong>Datenschutzbeauftragte:r</strong> — Datenschutz-Konzept für KI-Einsatz erstellen<br>
⏱ 2 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=21)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> DSGVO-Checkliste vollständig abgearbeitet</li>

<li><strong>Team-Lead</strong> — Pilot-Team auswählen und Erwartungen klären<br>
⏱ 1 Tag · 🎯 mittel · 📆 {(datetime.now() + timedelta(days=28)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3-5 motivierte Pilot-User identifiziert</li>
</ol>""",
    }
    
    return fallbacks.get(section_key, f"<p><em>[{section_key} – Content wird erstellt]</em></p>")

# -------------------- 🎯 NEW: Use prompt system instead of hardcoded prompts ----------------
def _generate_content_section(section_name: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    """🎯 UPDATED: Now uses prompt_loader system with variable interpolation!"""
    if not ENABLE_LLM_CONTENT:
        return f"<p><em>[{section_name} – LLM disabled]</em></p>"
    
    # Map section names to prompt files (without _de suffix for load_prompt)
    prompt_map = {
        "executive_summary": "executive_summary",
        "quick_wins": "quick_wins",
        "roadmap": "pilot_plan",  # 90-day roadmap
        "roadmap_12m": "roadmap_12m",
        "business_roi": "costs_overview",
        "business_costs": "costs_overview",
        "business_case": "business_case",
        "data_readiness": "data_readiness",
        "org_change": "org_change",
        "risks": "risks",
        "gamechanger": "gamechanger",
        "recommendations": "recommendations",
        "reifegrad_sowhat": "executive_summary",  # fallback to exec summary prompt
    }
    
    prompt_key = prompt_map.get(section_name)
    
    # Try to use prompt system if enabled and prompt exists
    if USE_PROMPT_SYSTEM and prompt_key:
        try:
            # Build variables for interpolation
            vars_dict = _build_prompt_vars(briefing, scores)
            
            # Load prompt with variable interpolation
            prompt_text = load_prompt(prompt_key, lang="de", vars_dict=vars_dict)
            
            if not isinstance(prompt_text, str):
                log.warning("⚠️ Prompt %s returned non-string: %s, falling back", prompt_key, type(prompt_text))
                raise ValueError("Non-string prompt")
            
            # Call GPT with loaded prompt
            result = _call_openai(
                prompt=prompt_text,
                system_prompt="Du bist ein Senior‑KI‑Berater. Antworte nur mit validem HTML.",
                temperature=0.2,
                max_tokens=OPENAI_MAX_TOKENS
            ) or ""
            
            result = _clean_html(result)
            if _needs_repair(result):
                result = _repair_html(section_name, result)
            
            # Check if result is substantial enough
            if not result or len(result.strip()) < 50:
                log.warning("⚠️ GPT returned too little for %s (%d chars), using fallback", section_name, len(result))
                return _get_fallback_content(section_name, briefing, scores)
            
            return result
            
        except FileNotFoundError as e:
            log.warning("⚠️ Prompt file not found for %s: %s - using legacy", prompt_key, e)
        except Exception as e:
            log.error("❌ Error loading/using prompt for %s: %s - using legacy", section_name, e)
    
    # Fallback to legacy hardcoded prompts
    branche = briefing.get("branche", "Unternehmen")
    hauptleistung = briefing.get("hauptleistung", "")
    unternehmensgroesse = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse") or ""
    bundesland = briefing.get("BUNDESLAND_LABEL") or briefing.get("bundesland") or ""
    ki_ziele = briefing.get("ki_ziele", [])
    ki_projekte = briefing.get("ki_projekte", "")
    vision = briefing.get("vision_3_jahre", "")
    trainings_liste = briefing.get("trainings_interessen", [])
    overall = scores.get("overall", 0)
    governance = scores.get("governance", 0)
    security = scores.get("security", 0)
    value = scores.get("value", 0)
    enablement = scores.get("enablement", 0)
    context = f"Branche: {branche}; Größe: {unternehmensgroesse}; Bundesland: {bundesland}; Hauptleistung/-produkt: {hauptleistung}."
    tone = "Sprache: neutral, dritte Person; keine Wir/Ich‑Formulierungen."
    only_html = "Antworte ausschließlich mit validem HTML (ohne Markdown‑Fences)."
    prompts = {
        "executive_summary": f"""Erstelle eine prägnante Executive Summary. {context}
KI‑Ziele: {', '.join(ki_ziele) if ki_ziele else 'nicht definiert'} • Vision: {vision}
KI‑Reifegrad: Gesamt {overall}/100 • Governance {governance}/100 • Sicherheit {security}/100 • Nutzen {value}/100 • Befähigung {enablement}/100
{tone} {only_html} Verwende nur <p>-Absätze.""",
        "quick_wins": f"""Liste 4–6 **konkrete Quick Wins** (0–90 Tage) für {context}
Jeder Quick Win: Titel, 1–2 Sätze Nutzen, realistische **Ersparnis: … h/Monat**.
Bezug: Hauptleistung {hauptleistung}; Projekte: {ki_projekte or 'keine'}; Trainingsinteressen: {', '.join(trainings_liste) if trainings_liste else '—'}.
{tone} {only_html} Liefere exakt eine <ul>-Liste mit <li>-Einträgen im Format:
<li><strong>Titel:</strong> Beschreibung. <em>Ersparnis: 5 h/Monat</em></li>""",
        "roadmap": f"""Erstelle eine **90‑Tage‑Roadmap** (0–30 Test; 31–60 Pilot; 61–90 Rollout) mit Bezug auf {context}
{tone} {only_html} Pro Phase 3–5 Meilensteine. Format: <h4>Phase …</h4> + <ul>…</ul>.""",
        "roadmap_12m": f"""Erstelle eine **12‑Monats‑Roadmap** in 3 Phasen (0–3/3–6/6–12) für {context}.
{tone} {only_html} Format: <div class="roadmap"><div class="roadmap-phase">…</div></div>. """,
        "business_roi": f"""Erstelle eine **ROI & Payback**‑Tabelle (Jahr 1) für {context}. {tone} {only_html}
Format: <table> mit 2 Spalten (Kennzahl, Wert).""",
        "business_costs": f"""Erstelle eine **Kostenübersicht Jahr 1** für {context}. {tone} {only_html}
Format: <table> mit 2 Spalten (Position, Betrag).""",
        "recommendations": f"""Formuliere 5–7 **Handlungsempfehlungen** mit Priorität [H/M/N] und Zeitrahmen (30/60/90). Kontext: {context}
{tone} {only_html} Format: <ol><li><strong>[H]</strong> Maßnahme — <em>60 Tage</em></li></ol>.""",
        "risks": f"""Erstelle eine **Risikomatrix** (5–7 Risiken) für {context} + EU‑AI‑Act Pflichtenliste.
{tone} {only_html} Format: <table> mit <thead>/<tbody>. """,
        "gamechanger": f"""Skizziere einen **Gamechanger‑Use Case** für {context}. (Idee: 3–4 Sätze; 3 Vorteile; 3 Schritte)
{tone} {only_html} Verwende <h4>, <p>, <ul>. """,
        "data_readiness": f"""Erstelle eine kompakte **Dateninventar & ‑Qualität**‑Übersicht für {context}.
{tone} {only_html} Format: <div class="data-readiness"><h4>…</h4><ul>…</ul></div>. """,
        "org_change": f"""Beschreibe **Organisation & Change** (Governance‑Rollen, Skill‑Programm, Kommunikation) für {context}.
{tone} {only_html} Format: <div class="org-change">…</div>. """,
        "business_case": f"""Erstelle einen kompakten **Business Case (detailliert)** für {context} – Annahmen, Nutzen (J1), Kosten (CapEx/OpEx), Payback, ROI, Sensitivität.
{tone} {only_html} Format: <div class="business-case"> … </div>. """,
        "reifegrad_sowhat": f"""Erkläre kurz: **Was heißt der Reifegrad konkret?** Kontext: {context}
Gesamt {overall}/100 • Governance {governance}/100 • Sicherheit {security}/100 • Nutzen {value}/100 • Befähigung {enablement}/100.
{tone} {only_html} Gib 4–6 Bullet‑Points (<ul>) aus.""",
    }
    
    out = _call_openai(prompt=prompts.get(section_name, ""), system_prompt="Du bist ein Senior‑KI‑Berater. Antworte nur mit validem HTML.", temperature=0.2, max_tokens=OPENAI_MAX_TOKENS) or ""
    out = _clean_html(out)
    if _needs_repair(out): out = _repair_html(section_name, out)
    
    # If still empty or too short, use fallback
    if not out or len(out.strip()) < 50:
        return _get_fallback_content(section_name, briefing, scores)
    
    return out

def _one_liner(title: str, section_html: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    base = f'Erzeuge einen prägnanten One‑liner unter der H2‑Überschrift "{title}". Formel: "Kernaussage; Konsequenz → nächster Schritt". Nur 1 Zeile.'
    text = _call_openai(base + "\n---\n" + re.sub(r"<[^>]+>", " ", section_html)[:1800], system_prompt="Du formulierst prägnante One‑liner auf Deutsch.", temperature=0.1, max_tokens=80)
    return (text or "").strip()

def _split_li_list_to_columns(html_list: str) -> Tuple[str, str]:
    if not html_list: return "<ul></ul>", "<ul></ul>"
    items = re.findall(r"<li[\s>].*?</li>", html_list, flags=re.DOTALL | re.IGNORECASE)
    if not items:
        lines = [ln.strip() for ln in re.split(r"<br\s*/?>|\n", html_list) if ln.strip()]
        items = [f"<li>{ln}</li>" for ln in lines]
    mid = (len(items) + 1) // 2
    return "<ul>" + "".join(items[:mid]) + "</ul>", "<ul>" + "".join(items[mid:]) + "</ul>"

# -------------------- AI Act ----------------
def _try_read(path: str) -> Optional[str]:
    if os.path.exists(path):
        try: return open(path, "r", encoding="utf-8").read()
        except Exception: return None
    alt = os.path.join("/mnt/data", os.path.basename(path))
    if os.path.exists(alt):
        try: return open(alt, "r", encoding="utf-8").read()
        except Exception: return None
    return None

def _md_to_simple_html(md: str) -> str:
    if not md: return ""
    out: List[str] = []; in_ul = False
    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            if in_ul: out.append("</ul>"); in_ul = False
            continue
        if line.startswith("!["): continue
        if re.match(r"^\[\d+\]:\s*https?://", line): continue
        if line.startswith("#### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h4>{html.escape(line[5:].strip())}</h4>"); continue
        if line.startswith("### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h3>{html.escape(line[4:].strip())}</h3>"); continue
        if line.startswith(("* ", "- ")):
            if not in_ul: in_ul = True; out.append("<ul>")
            out.append(f"<li>{html.escape(line[2:].strip())}</li>"); continue
        if in_ul: out.append("</ul>"); in_ul = False
        out.append(f"<p>{html.escape(line)}</p>")
    if in_ul: out.append("</ul>")
    return "\n".join(out)

def _build_ai_act_blocks() -> Dict[str, str]:
    if not ENABLE_AI_ACT_SECTION: return {}
    text = _try_read(AI_ACT_INFO_PATH) or ""
    html_block = _md_to_simple_html(text) if text else ("<h3>Wesentliche Eckdaten</h3>"
        "<ul><li>Gestaffelte Anwendung ab 2025; Kernpflichten 2025–2027.</li>"
        "<li>Frühzeitige Vorbereitung: Risiko- & Governance-Prozesse, Dokumentation, Monitoring.</li></ul>")
    cta = ('<div class="callout">'
           "<strong>Auf Wunsch:</strong> Tabellarische Übersicht der Termine/Fristen – Phase "
           f"<strong>{html.escape(AI_ACT_PHASE_LABEL)}</strong> – inkl. Verantwortlichkeiten und Checkpoints."
           "</div>")
    packages = ('<table class="table">'
                "<thead><tr><th>Paket</th><th>Umfang</th><th>Ergebnisse</th></tr></thead><tbody>"
                "<tr><td><strong>Lite: Tabellen‑Kit</strong></td>"
                "<td>Termin-/Fristen‑Tabelle (2025–2027) + 10–15 Checkpoints.</td>"
                "<td>PDF/CSV, kurze Einordnung pro Zeile.</td></tr>"
                "<tr><td><strong>Pro: Compliance‑Kit</strong></td>"
                "<td>Lite + Vorlagen (Risikomanagement, Logging, Monitoring) + 60‑Tage‑Plan.</td>"
                "<td>Dokupaket, editierbar.</td></tr>"
                "<tr><td><strong>Max: Audit‑Ready</strong></td>"
                "<td>Pro + Abgleich mit Prozessen, Nachweis‑Mapping, Q&A.</td>"
                "<td>Audit‑Map + Meilensteine.</td></tr>"
                "</tbody></table>")
    return {"AI_ACT_SUMMARY_HTML": html_block, "AI_ACT_TABLE_OFFER_HTML": cta, "AI_ACT_ADDON_PACKAGES_HTML": packages, "ai_act_phase_label": AI_ACT_PHASE_LABEL}

# -------------------- Mail & helpers ----------------
def _mask_email(addr: Optional[str]) -> str:
    if not addr or not DBG_MASK_EMAILS: return addr or ""
    try:
        name, domain = addr.split("@", 1)
        return f"{name[:3]}***@{domain}" if len(name) > 3 else f"{name}***@{domain}"
    except Exception:
        return "***"

def _admin_recipients() -> List[str]:
    emails: List[str] = []
    for raw in (getattr(settings, "ADMIN_EMAILS", None) or os.getenv("ADMIN_EMAILS", ""),
                getattr(settings, "REPORT_ADMIN_EMAIL", None) or os.getenv("REPORT_ADMIN_EMAIL", ""),
                os.getenv("ADMIN_NOTIFY_EMAIL", "")):
        if raw: emails.extend([e.strip() for e in raw.split(",") if e.strip()])
    return list(dict.fromkeys(emails))

def _determine_user_email(db: Session, briefing: Briefing, override: Optional[str]) -> Optional[str]:
    if override: return override
    if getattr(briefing, "user_id", None):
        u = db.get(User, briefing.user_id)
        if u and getattr(u, "email", ""): return u.email
    answers = getattr(briefing, "answers", None) or {}
    return answers.get("email") or answers.get("kontakt_email")

def _version_major_minor(v: str) -> str:
    m = re.match(r"^\s*(\d+)\.(\d+)", v or ""); return f"{m.group(1)}.{m.group(2)}" if m else "1.0"

def _build_watermark_text(report_id: str, version_mm: str) -> str:
    return f"Trusted KI‑Check · Report‑ID: {report_id} · v{version_mm}"

def _derive_kundencode(answers: Dict[str, Any], user_email: str) -> str:
    raw = ""
    if user_email and "@" in user_email:
        raw = user_email.split("@", 1)[-1].split(".")[0]
    code = re.sub(r"[^A-Za-z0-9]", "", (raw or "KND").upper())
    return code[:3] or "KND"

def _theme_vars_for_branch(branch_label: str) -> str:
    b = (branch_label or "").lower()
    brand, weak, accent = "#2563eb", "#dbeafe", "#1e3a5f"
    if "it" in b or "software" in b:
        brand, weak, accent = "#1d4ed8", "#c7d2fe", "#16327a"
    elif "marketing" in b or "werbung" in b:
        brand, weak, accent = "#0ea5e9", "#bae6fd", "#0c4a6e"
    elif "industrie" in b or "produktion" in b:
        brand, weak, accent = "#1e40af", "#c7d2fe", "#112a63"
    elif "verwaltung" in b:
        brand, weak, accent = "#1e3a8a", "#c7d2fe", "#0f2c5a"
    return f"<style>:root{{--c-brand:{brand};--c-brand-weak:{weak};--c-accent:{accent};}}</style>"

def _build_freetext_snippets_html(ans: Dict[str, Any]) -> str:
    keys = [
        ("hauptleistung", "Hauptleistung/Produkt"),
        ("ki_projekte", "Laufende/geplante KI‑Projekte"),
        ("zeitersparnis_prioritaet", "Zeitersparnis‑Priorität"),
        ("geschaeftsmodell_evolution", "Geschäftsmodell‑Idee"),
        ("vision_3_jahre", "Vision 3 Jahre"),
        ("strategische_ziele", "Strategische Ziele"),
    ]
    items: list[str] = []
    for k, label in keys:
        val = (ans.get(k) or "").strip()
        if val:
            items.append(f"<li><strong>{html.escape(label)}:</strong> {html.escape(val)}</li>")
    if not items:
        return ""
    title = "Ihre Freitext‑Eingaben (Kurzüberblick)"
    return (
        "<section class='fb-section'>"
        "<div class='fb-head'><span class='fb-step'>F</span>"
        f"<h3 class='fb-title'>{html.escape(title)}</h3></div>"
        "<ul>" + "".join(items) + "</ul>"
        "</section>"
    )
# -------------------- 🎯 UPDATED: Main composer with prompt system ----------------
def _generate_content_sections(briefing: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, str]:
    """Generate all content sections - now using prompt system where available!"""
    sections: Dict[str, str] = {}
    
    # Executive Summary
    sections["EXECUTIVE_SUMMARY_HTML"] = _generate_content_section("executive_summary", briefing, scores)
    
    # Quick Wins - with improved fallbacks
    qw_html = _generate_content_section("quick_wins", briefing, scores)
    if _needs_repair(qw_html): 
        qw_html = _repair_html("quick_wins", qw_html)
    
    # Split into columns
    left, right = _split_li_list_to_columns(qw_html)
    sections["QUICK_WINS_HTML_LEFT"] = left
    sections["QUICK_WINS_HTML_RIGHT"] = right
    
    # Calculate hours saved from Quick Wins
    total_h = 0
    try: 
        total_h = _sum_hours_from_quick_wins(qw_html)
    except Exception: 
        total_h = 0
    
    # Fallback if no hours detected
    if total_h <= 0:
        try: 
            fb = int(os.getenv("FALLBACK_QW_MONTHLY_H", "0"))
        except Exception: 
            fb = 0
        if fb <= 0:
            try: 
                fb = int(os.getenv("DEFAULT_QW1_H", "20")) + int(os.getenv("DEFAULT_QW2_H", "15"))
            except Exception: 
                fb = 35  # conservative default
        total_h = max(0, fb)
    
    # Calculate ROI metrics
    rate = int(briefing.get("stundensatz_eur") or os.getenv("DEFAULT_STUNDENSATZ_EUR", "60") or 60)
    if total_h > 0:
        sections.update({
            "monatsersparnis_stunden": total_h,
            "monatsersparnis_eur": total_h * rate,
            "jahresersparnis_stunden": total_h * 12,
            "jahresersparnis_eur": total_h * rate * 12,
            "stundensatz_eur": rate,
            "REALITY_NOTE_QW": f"Praxis‑Hinweis: Diese Quick‑Wins sparen ~{max(1, int(round(total_h*0.7)))}–{int(round(total_h*1.2))} h/Monat (konservativ geschätzt)."
        })
    
    # Roadmaps - with improved prompts
    sections["PILOT_PLAN_HTML"] = _generate_content_section("roadmap", briefing, scores)
    sections["ROADMAP_12M_HTML"] = _generate_content_section("roadmap_12m", briefing, scores)
    
    # Business sections
    sections["ROI_HTML"] = _generate_content_section("business_roi", briefing, scores)
    sections["COSTS_OVERVIEW_HTML"] = _generate_content_section("business_costs", briefing, scores)
    sections["BUSINESS_CASE_HTML"] = _generate_content_section("business_case", briefing, scores)
    sections["BUSINESS_SENSITIVITY_HTML"] = (
        '<table class="table"><thead><tr><th>Adoption</th><th>Kommentar</th></tr></thead>'
        "<tbody><tr><td>100%</td><td>Planmäßige Wirkung der Maßnahmen.</td></tr>"
        "<tr><td>80%</td><td>Leichte Abweichungen – Payback +2–3 Monate.</td></tr>"
        "<tr><td>60%</td><td>Konservativ – nur Kernmaßnahmen; Payback länger.</td></tr></tbody></table>"
    )
    
    # Other detailed sections
    sections["DATA_READINESS_HTML"] = _generate_content_section("data_readiness", briefing, scores)
    sections["ORG_CHANGE_HTML"] = _generate_content_section("org_change", briefing, scores)
    sections["RISKS_HTML"] = _generate_content_section("risks", briefing, scores)
    sections["GAMECHANGER_HTML"] = _generate_content_section("gamechanger", briefing, scores)
    sections["RECOMMENDATIONS_HTML"] = _generate_content_section("recommendations", briefing, scores)
    sections["REIFEGRAD_SOWHAT_HTML"] = _generate_content_section("reifegrad_sowhat", briefing, scores)
    
    # 🎯 NEW: Next Actions with DYNAMIC DATES via prompt system
    if USE_PROMPT_SYSTEM:
        try:
            vars_dict = _build_prompt_vars(briefing, scores)
            prompt_text = load_prompt("next_actions", lang="de", vars_dict=vars_dict)
            nxt = _call_openai(
                prompt=prompt_text,
                system_prompt="Du bist PMO‑Lead. Antworte nur mit HTML.",
                temperature=0.2,
                max_tokens=600
            ) or ""
            sections["NEXT_ACTIONS_HTML"] = _clean_html(nxt) if nxt else _get_fallback_content("next_actions", briefing, scores)
        except Exception as e:
            log.warning("⚠️ Next actions prompt system failed: %s, using fallback", e)
            sections["NEXT_ACTIONS_HTML"] = _get_fallback_content("next_actions", briefing, scores)
    else:
        # Legacy fallback with dynamic dates
        now = datetime.now()
        nxt = _call_openai(
            f"""Erstelle 3–7 **Next Actions (30 Tage)** in <ol>. Jede Zeile: 👤 Rolle (kein Name), ⏱ Aufwand (z. B. ½ Tag), 
            🎯 Impact (hoch/mittel/niedrig), 📆 Deadline (zwischen {now.strftime('%d.%m.%Y')} und {(now + timedelta(days=30)).strftime('%d.%m.%Y')}) — Maßnahme. 
            Antwort NUR als <ol>…</ol>.""",
            system_prompt="Du bist PMO‑Lead. Antworte nur mit HTML.",
            temperature=0.2,
            max_tokens=600
        ) or ""
        sections["NEXT_ACTIONS_HTML"] = _clean_html(nxt) if nxt else _get_fallback_content("next_actions", briefing, scores)
    
    # Generate one-liners for all sections
    sections["LEAD_EXEC"] = _one_liner("Executive Summary", sections["EXECUTIVE_SUMMARY_HTML"], briefing, scores)
    sections["LEAD_KPI"] = _one_liner("KPI‑Dashboard & Monitoring", "", briefing, scores)
    sections["LEAD_QW"] = _one_liner("Quick Wins (0–90 Tage)", qw_html, briefing, scores)
    sections["LEAD_ROADMAP_90"] = _one_liner("Roadmap (90 Tage – Test → Pilot → Rollout)", sections["PILOT_PLAN_HTML"], briefing, scores)
    sections["LEAD_ROADMAP_12"] = _one_liner("Roadmap (12 Monate)", sections["ROADMAP_12M_HTML"], briefing, scores)
    sections["LEAD_BUSINESS"] = _one_liner("Business Case & Kostenübersicht", sections["ROI_HTML"], briefing, scores)
    sections["LEAD_BUSINESS_DETAIL"] = _one_liner("Business Case (detailliert)", sections["BUSINESS_CASE_HTML"], briefing, scores)
    sections["LEAD_TOOLS"] = _one_liner("Empfohlene Tools (Pro & Open‑Source)", sections.get("TOOLS_HTML",""), briefing, scores)
    sections["LEAD_DATA"] = _one_liner("Dateninventar & ‑Qualität", sections["DATA_READINESS_HTML"], briefing, scores)
    sections["LEAD_ORG"] = _one_liner("Organisation & Change", sections["ORG_CHANGE_HTML"], briefing, scores)
    sections["LEAD_RISKS"] = _one_liner("Risiko‑Assessment & Compliance", sections["RISKS_HTML"], briefing, scores)
    sections["LEAD_GC"] = _one_liner("Gamechanger‑Use Case", sections["GAMECHANGER_HTML"], briefing, scores)
    sections["LEAD_FUNDING"] = _one_liner("Aktuelle Förderprogramme & Quellen", sections.get("FOERDERPROGRAMME_HTML",""), briefing, scores)
    sections["LEAD_NEXT_ACTIONS"] = _one_liner("Nächste Schritte (30 Tage)", sections["NEXT_ACTIONS_HTML"], briefing, scores)
    
    # Benchmark table
    sections["BENCHMARK_HTML"] = _build_benchmark_html(briefing)
    
    # ===== NEW: Additional sections required by PDF template =====
    
    # KPI Context - Interpretation of scores with benchmark comparison
    score_overall = scores.get("overall", 0)
    benchmark_avg = briefing.get("benchmark_avg", 35)
    benchmark_top = briefing.get("benchmark_top", 55)
    
    # Determine interpretation based on score
    if score_overall >= 70:
        interpretation = "Sehr gut – überdurchschnittlich"
    elif score_overall >= 50:
        interpretation = "Solide – im guten Mittelfeld"
    else:
        interpretation = "Ausbaufähig – erhebliches Potenzial vorhanden"
    
    kpi_context = f"""<div class="kpi-context">
<p><strong>Interpretation:</strong> {interpretation}</p>
<p><strong>Benchmark:</strong> Durchschnitt {benchmark_avg}/100 · Top-Quartil {benchmark_top}/100</p>
</div>"""
    sections["KPI_CONTEXT_HTML"] = kpi_context
    
    # ZIM Förderung (optional, from environment)
    # These are funding program specific sections that can be configured via ENV
    sections["ZIM_ALERT_HTML"] = os.getenv("ZIM_ALERT_HTML", "")
    sections["ZIM_WORKFLOW_HTML"] = os.getenv("ZIM_WORKFLOW_HTML", "")
    
    # Kreativ Tools (will be set later from file if available)
    sections.setdefault("KREATIV_TOOLS_HTML", "")
    
    # LEADs for new sections
    sections["LEAD_ZIM_ALERT"] = "Wichtige Änderung ab 2025"
    sections["LEAD_ZIM_WORKFLOW"] = "Schritt-für-Schritt-Anleitung zur volldigitalen Antragstellung"
    sections["LEAD_CREATIV"] = "Kuratierte Tools für kreative Branchen"
    sections.setdefault("LEAD_ROADMAP", _one_liner("Roadmap", sections.get("PILOT_PLAN_HTML", ""), briefing, scores))
    
    return sections

# -------------------- pipeline (kept from original with minor logging updates) ----------------
def analyze_briefing(db: Session, briefing_id: int, run_id: str) -> tuple[int, str, Dict[str, Any]]:
    br = db.get(Briefing, briefing_id)
    if not br: raise ValueError("Briefing not found")
    raw_answers: Dict[str, Any] = getattr(br, "answers", {}) or {}
    answers = (lambda x: x)(raw_answers)
    try:
        from services.answers_normalizer import normalize_answers  # type: ignore
        answers = normalize_answers(raw_answers)
    except Exception:
        pass
    
    log.info("[%s] 📊 Calculating realistic scores (v4.14.0-GOLD-PLUS)...", run_id)
    score_wrap = _calculate_realistic_score(answers)
    scores = score_wrap["scores"]
    
    log.info("[%s] 🎨 Generating content sections with %s...", run_id, "PROMPT SYSTEM" if USE_PROMPT_SYSTEM else "legacy prompts")
    sections = _generate_content_sections(briefing=answers, scores=scores)
    
    now = datetime.now()
    sections["BRANCHE_LABEL"] = answers.get("BRANCHE_LABEL", "") or answers.get("branche", "")
    sections["BUNDESLAND_LABEL"] = answers.get("BUNDESLAND_LABEL", "") or answers.get("bundesland", "")
    sections["UNTERNEHMENSGROESSE_LABEL"] = answers.get("UNTERNEHMENSGROESSE_LABEL", "") or answers.get("unternehmensgroesse", "")
    sections["JAHRESUMSATZ_LABEL"] = answers.get("JAHRESUMSATZ_LABEL", answers.get("jahresumsatz", ""))
    sections["ki_kompetenz"] = answers.get("ki_kompetenz") or answers.get("ki_knowhow", "")
    sections["report_date"] = now.strftime("%d.%m.%Y")
    sections["report_year"] = now.strftime("%Y")
    sections["transparency_text"] = getattr(settings, "TRANSPARENCY_TEXT", None) or os.getenv("TRANSPARENCY_TEXT", "") or ""
    sections["user_email"] = answers.get("email") or answers.get("kontakt_email") or ""
    sections["score_governance"] = scores.get("governance", 0)
    sections["score_sicherheit"] = scores.get("security", 0)
    sections["score_nutzen"] = scores.get("value", 0)
    sections["score_befaehigung"] = scores.get("enablement", 0)
    sections["score_gesamt"] = scores.get("overall", 0)
    
    version_full = getattr(settings, "VERSION", "1.0.0")
    version_mm = re.match(r"^\s*(\d+)\.(\d+)", version_full or "")
    version_mm = f"{version_mm.group(1)}.{version_mm.group(2)}" if version_mm else "1.0"
    kundencode = _derive_kundencode(answers, sections["user_email"])
    report_id = f"R-{now.strftime('%Y%m%d')}-{kundencode}"
    sections["kundencode"] = kundencode
    sections["report_id"] = report_id
    sections["report_version"] = version_mm
    sections["WATERMARK_TEXT"] = _build_watermark_text(report_id, version_mm)
    
    # Build stamp & Feedback box
    sections["BUILD_STAMP"] = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · {report_id} · v{version_mm}"
    if sections.get("FEEDBACK_URL"):
        fb_html = _build_feedback_box(sections["FEEDBACK_URL"], sections["report_date"])
        if fb_html:
            sections["FEEDBACK_BOX_HTML"] = fb_html

    sections["CHANGELOG_SHORT"] = os.getenv("CHANGELOG_SHORT", "—")
    sections["AUDITOR_INITIALS"] = os.getenv("AUDITOR_INITIALS", "KSJ")
    sections.setdefault("KPI_HTML","")
    sections.setdefault("FEEDBACK_BOX_HTML","Feedback willkommen – was war hilfreich, was fehlt?")
    sections.setdefault("DATA_COVERAGE_HTML","")
    sections.setdefault("FREITEXT_SNIPPETS_HTML","")
    sections.setdefault("KREATIV_SPECIAL_HTML","")
    sections.setdefault("LEISTUNG_NACHWEIS_HTML","")
    sections.setdefault("GLOSSAR_HTML","")
    
    # Kreativ Tools
    kreat_path = os.getenv("KREATIV_TOOLS_PATH", "").strip()
    if kreat_path:
        kreat_html = _build_kreativ_tools_html(kreat_path, sections["report_date"])
        if kreat_html:
            sections["KREATIV_TOOLS_HTML"] = kreat_html
            sections["KREATIV_SPECIAL_HTML"] = kreat_html
    
    # Research integration
    research_last_updated = ""
    try:
        from services.research_pipeline import run_research  # type: ignore
        if USE_INTERNAL_RESEARCH and run_research:
            log.info("[%s] 🔬 Running internal research...", run_id)
            research_blocks = run_research(answers)
            if isinstance(research_blocks, dict):
                for k, v in research_blocks.items():
                    if isinstance(v, str): 
                        sections[k] = v
                research_last_updated = str(research_blocks.get("last_updated") or "")
    except Exception as exc:
        log.warning("[%s] ⚠️ Internal research failed: %s", run_id, exc)
    
    sections["research_last_updated"] = research_last_updated or sections["report_date"]
    
    # Map research results
    if "TOOLS_TABLE_HTML" in sections: 
        sections["TOOLS_HTML"] = sections.pop("TOOLS_TABLE_HTML", "")
    if "FUNDING_TABLE_HTML" in sections: 
        sections["FOERDERPROGRAMME_HTML"] = sections.pop("FUNDING_TABLE_HTML", "")
    
    # Rewrite table link labels
    if sections.get("TOOLS_HTML"): 
        sections["TOOLS_HTML"] = _rewrite_table_links_with_labels(sections["TOOLS_HTML"])
    if sections.get("FOERDERPROGRAMME_HTML"): 
        sections["FOERDERPROGRAMME_HTML"] = _rewrite_table_links_with_labels(sections["FOERDERPROGRAMME_HTML"])
    
    sections["SOURCES_BOX_HTML"] = _build_sources_box_html(sections, sections["research_last_updated"])

    # Freitext snippets
    sections['FREITEXT_SNIPPETS_HTML'] = _build_freetext_snippets_html(answers)
    
    # Glossar
    gloss_raw = _try_read(GLOSSAR_PATH) or ""
    if gloss_raw:
        if GLOSSAR_PATH.lower().endswith(".md"):
            sections["GLOSSAR_HTML"] = _md_to_simple_html(gloss_raw)
        else:
            sections["GLOSSAR_HTML"] = gloss_raw

    # Coverage guard
    try:
        cov = analyze_coverage(answers)
        log.info("[%s] 📈 Coverage: %s%% (present=%s, missing=%s)", run_id, cov.get("coverage_pct"), len(cov.get("present",[])), len(cov.get("missing",[])))
        if INCLUDE_COVERAGE_BOX:
            sections["LEISTUNG_NACHWEIS_HTML"] = (sections.get("LEISTUNG_NACHWEIS_HTML","") + build_html_report(cov))
    except Exception as _exc:
        log.warning("[%s] ⚠️ Coverage-guard warning: %s", run_id, _exc)

    # Logos & branding
    sections["LOGO_PRIMARY_SRC"] = os.getenv("LOGO_PRIMARY_SRC", "")
    sections["FOOTER_LEFT_LOGO_SRC"] = os.getenv("FOOTER_LEFT_LOGO_SRC", "")
    sections["FOOTER_MID_LOGO_SRC"] = os.getenv("FOOTER_MID_LOGO_SRC", "")
    sections["FOOTER_RIGHT_LOGO_SRC"] = os.getenv("FOOTER_RIGHT_LOGO_SRC", "")
    sections["FEEDBACK_URL"] = (os.getenv("FEEDBACK_URL") or os.getenv("FEEDBACK_REDIRECT_BASE") or "").strip()
    sections["FOOTER_BRANDS_HTML"] = os.getenv("FOOTER_BRANDS_HTML", "")
    sections["OWNER_NAME"] = getattr(settings, "OWNER_NAME", None) or os.getenv("OWNER_NAME", "KI‑Sicherheit.jetzt")
    sections["CONTACT_EMAIL"] = getattr(settings, "CONTACT_EMAIL", None) or os.getenv("CONTACT_EMAIL", "info@example.com")
    sections["THEME_CSS_VARS"] = _theme_vars_for_branch(sections.get("BRANCHE_LABEL") or sections.get("branche", ""))
    
    # BUILD_ID - timestamp for report generation tracking
    sections["BUILD_ID"] = f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}"
    
    # Werkbank
    sections["WERKBANK_HTML"] = _build_werkbank_html_dynamic(answers)
    
    # AI Act blocks
    ai_act_blocks = _build_ai_act_blocks()
    sections.update(ai_act_blocks)
    
    log.info("[%s] 🎨 Rendering final HTML...", run_id)
    result = render(
        br, 
        run_id=run_id, 
        generated_sections=sections, 
        use_fetchers=False, 
        scores=scores, 
        meta={
            "scores": scores, 
            "score_details": score_wrap.get("details", {}), 
            "research_last_updated": sections["research_last_updated"]
        }
    )
    
    an = Analysis(
        user_id=br.user_id, 
        briefing_id=briefing_id, 
        html=result["html"], 
        meta=result.get("meta", {}), 
        created_at=datetime.now(timezone.utc)
    )
    db.add(an)
    db.commit()
    db.refresh(an)
    
    log.info("[%s] ✅ Analysis created (v4.14.0-GOLD-PLUS): id=%s", run_id, an.id)
    return an.id, result["html"], result.get("meta", {})

# -------------------- runner (kept from original) ----------------
def _fetch_pdf_if_needed(pdf_url: Optional[str], pdf_bytes: Optional[bytes]) -> Optional[bytes]:
    if pdf_bytes: return pdf_bytes
    if not pdf_url: return None
    try:
        r = requests.get(pdf_url, timeout=30)
        if r.ok: return r.content
    except Exception:
        return None
    return None

def _send_emails(db: Session, rep: Report, br: Briefing, pdf_url: Optional[str], pdf_bytes: Optional[bytes], run_id: str) -> None:
    """Send emails via Resend API"""
    best_pdf = _fetch_pdf_if_needed(pdf_url, pdf_bytes)
    attachments_admin: List[Dict[str, Any]] = []
    if best_pdf:
        attachments_admin.append({
            "filename": f"KI-Status-Report-{getattr(rep, 'id', None)}.pdf", 
            "content": best_pdf, 
            "mimetype": "application/pdf"
        })
    try:
        bjson = json.dumps(getattr(br, "answers", {}) or {}, ensure_ascii=False, indent=2).encode("utf-8")
        attachments_admin.append({
            "filename": f"briefing-{br.id}.json", 
            "content": bjson, 
            "mimetype": "application/json"
        })
    except Exception:
        pass
    
    # Send to user
    try:
        user_email = None
        try: 
            user_email = _determine_user_email(db, br, getattr(rep, "user_email", None))
        except Exception: 
            user_email = None
        
        if user_email:
            user_attachments = [] if pdf_url else attachments_admin[:1]
            ok, err = _send_email_via_resend(
                user_email, 
                "Ihr KI‑Status‑Report ist fertig", 
                render_report_ready_email(recipient="user", pdf_url=pdf_url),
                attachments=user_attachments
            )
            if ok: 
                log.info("[%s] 📧 Mail sent to user %s via Resend", run_id, _mask_email(user_email))
            else: 
                log.warning("[%s] ⚠️ MAIL_USER failed: %s", run_id, err)
    except Exception as exc:
        log.warning("[%s] ⚠️ MAIL_USER failed: %s", run_id, exc)
    
    # Send to admins
    try:
        if os.getenv("ENABLE_ADMIN_NOTIFY", "1") in ("1","true","TRUE","yes","YES"):
            for addr in _admin_recipients():
                ok, err = _send_email_via_resend(
                    addr, 
                    f"Neuer KI‑Status‑Report – Analysis #{rep.analysis_id} / Briefing #{rep.briefing_id}", 
                    render_report_ready_email(recipient="admin", pdf_url=pdf_url),
                    attachments=attachments_admin
                )
                if ok: 
                    log.info("[%s] 📧 Admin notify sent to %s via Resend", run_id, _mask_email(addr))
                else: 
                    log.warning("[%s] ⚠️ MAIL_ADMIN failed for %s: %s", run_id, _mask_email(addr), err)
    except Exception as exc:
        log.warning("[%s] ⚠️ MAIL_ADMIN block failed: %s", run_id, exc)

def run_analysis_for_briefing(briefing_id: int, email: Optional[str] = None) -> None:
    """Public API: Start analysis for a briefing (called from routes/briefings.py)"""
    run_async(briefing_id, email)

def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    if SessionLocal is None: 
        raise RuntimeError("database_unavailable")
    db = SessionLocal()
    rep: Optional[Report] = None
    try:
        log.info("[%s] 🚀 Starting analysis v4.14.0-GOLD-PLUS for briefing_id=%s", run_id, briefing_id)
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
        br = db.get(Briefing, briefing_id)
        rep = Report(
            user_id=br.user_id if br else None, 
            briefing_id=briefing_id, 
            analysis_id=an_id, 
            created_at=datetime.now(timezone.utc)
        )
        if hasattr(rep, "user_email"): 
            rep.user_email = (email or "")
        if hasattr(rep, "task_id"): 
            rep.task_id = f"local-{uuid.uuid4()}"
        if hasattr(rep, "status"): 
            rep.status = "pending"
        db.add(rep)
        db.commit()
        db.refresh(rep)
        
        if DBG_PDF: 
            log.debug("[%s] 📄 pdf_render start", run_id)
        pdf_info = render_pdf_from_html(html, meta={"analysis_id": an_id, "briefing_id": briefing_id, "run_id": run_id})
        pdf_url = pdf_info.get("pdf_url")
        pdf_bytes = pdf_info.get("pdf_bytes")
        pdf_error = pdf_info.get("error")
        if DBG_PDF: 
            log.debug("[%s] 📄 pdf_render done url=%s bytes=%s error=%s", run_id, bool(pdf_url), len(pdf_bytes or b""), pdf_error)
        
        if not pdf_url and not pdf_bytes:
            error_msg = f"PDF failed: {pdf_error or 'no output'}"
            log.error("[%s] ❌ %s", run_id, error_msg)
            if hasattr(rep, "status"): 
                rep.status = "failed"
            if hasattr(rep, "email_error_user"): 
                rep.email_error_user = error_msg
            if hasattr(rep, "updated_at"): 
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep)
            db.commit()
            raise ValueError(error_msg)
        
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
        
        _send_emails(db, rep, br, pdf_url, pdf_bytes, run_id)
        
    except Exception as exc:
        log.error("[%s] ❌ Analysis failed: %s", run_id, exc, exc_info=True)
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