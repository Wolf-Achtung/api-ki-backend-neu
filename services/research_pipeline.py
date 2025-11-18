
# -*- coding: utf-8 -*-
"""
services.research_pipeline
--------------------------
Öffentliche Entry-Funktion: run_research(answers: dict) -> dict

Gibt HTML-Strings zurück, die gpt_analyze.py direkt übernimmt:
- "TOOLS_TABLE_HTML"
- "FUNDING_TABLE_HTML"
- optional "NEWS_BOX_HTML"
- "last_updated"
"""
from __future__ import annotations

import os
import html
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .research_clients import parse_rss, harvest_links

log = logging.getLogger(__name__)

# --- Quellen (RSS/Listen) ---

DEFAULT_NEWS_RSS = [
    # Medien (DE)
    "https://www.heise.de/rss/heise-atom.xml",
    "https://www.golem.de/rss.php?tp=ki",     # KI-Themenkanal
    "https://t3n.de/news/feed/",
    # EU / Offiziell
    "https://ec.europa.eu/newsroom/dae/document.cfm?doc_id=12461",  # falls kein RSS, wird ignoriert
]

# KNOWN RSS for EU AI Act (reliable sources often do not offer direct AI-Act feeds; keep general tech/policy feeds)
AI_ACT_NEWS_RSS = [
    "https://digital-strategy.ec.europa.eu/en/newsroom/rss.xml",
    "https://commission.europa.eu/news/press-releases_en?f%5B0%5D=topic%3A1120",  # Pressreleases (policy)
]

TOOLS_PAGES = [
    # Produktplattformen (teilweise ohne RSS; wir harvesten Links)
    "https://www.producthunt.com/topics/artificial-intelligence",
    "https://huggingface.co/models",
]

FUNDING_HINT_PAGES = [
    # Kuratierte, zuverlässige Einstiege – Nutzer kann per ENV ergänzen
    "https://www.foerderdatenbank.de/",
    "https://www.bmwk.de/Navigation/DE/Home/home.html",
    "https://digital-strategy.ec.europa.eu/en/activities/digital-programme",
    "https://www.ibb.de/de/foerderprogramme/",
    "https://www.berlin.de/sen/wirtschaft/wirtschaft/foerderprogramme/",
]

def _kw(answers: Dict[str, Any]) -> List[str]:
    """Bestimme einfache Schlagwörter aus Fragebogen (Branche/Use-Cases)."""
    branche = (answers.get("BRANCHE_LABEL") or answers.get("branche") or "").lower()
    uses = answers.get("anwendungsfaelle", []) or []
    kws: set[str] = set()
    if branche:
        kws.update(word.strip() for word in branche.replace("/", " ").split())
    for u in uses:
        for w in str(u).split("_"):
            if w:
                kws.add(w)
    # Basis + EU-Bezug für KMU
    kws.update({"ai","ki","kmu","sme","eu","förderung","förder","digitalisierung"})
    return [k for k in kws if k]

def _match_any(text: str, keywords: List[str]) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in keywords)

def _tools_table(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    rows = []
    for it in items:
        # Support both "title" and "name" fields for robustness
        title = html.escape(it.get("title") or it.get("name") or it.get("source") or "Tool")
        url = html.escape(it.get("url",""))
        src = html.escape(it.get("source",""))
        rows.append(f"<tr><td>{title}</td><td><a href='{url}'>{src or url}</a></td></tr>")
    return "<table class='table'><thead><tr><th>Tool</th><th>Quelle</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"

def _funding_table(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    rows = []
    for it in items:
        # Support both "title" and "name" fields for robustness
        title = html.escape(it.get("title") or it.get("name") or "Programm")
        url = html.escape(it.get("url",""))
        src = html.escape(it.get("source",""))
        rows.append(f"<tr><td>{title}</td><td><a href='{url}'>{src or url}</a></td></tr>")
    return "<table class='table'><thead><tr><th>Programm</th><th>Quelle</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"

def _news_box(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    lis = []
    for it in items[:10]:
        title = html.escape(it.get("title",""))
        url = html.escape(it.get("url",""))
        src = html.escape(it.get("source",""))
        lis.append(f"<li><a href='{url}'>{title}</a> <span class='small muted'>({src})</span></li>")
    return "<div class='fb-section'><div class='fb-head'><span class='fb-step'>News</span><h3 class='fb-title'>Aktuelle Meldungen (kuratiert)</h3></div><ul>" + "".join(lis) + "</ul></div>"

def run_research(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
      {
        "TOOLS_TABLE_HTML": "...",
        "FUNDING_TABLE_HTML": "...",
        "NEWS_BOX_HTML": "...",
        "last_updated": "YYYY-MM-DD"
      }
    """
    provider = os.getenv("RESEARCH_PROVIDER", "hybrid").strip().lower()
    # offline-only short-circuit
    offline_only = provider == "offline"

    kws = _kw(answers)
    tools: List[Dict[str, str]] = []
    funding: List[Dict[str, str]] = []
    news: List[Dict[str, str]] = []

    # --- TOOLS ---
    if not offline_only:
        try:
            # harvest links from curated pages
            for url in TOOLS_PAGES:
                items = harvest_links(url, allow_domains=None, limit=30)
                # simple filter: keep items that look like model/tool pages
                sel = [i for i in items if _match_any((i.get("title","") + " " + i.get("url","")), kws)]
                tools.extend(sel[:10])
        except Exception as exc:
            log.warning("TOOLS harvest failed: %s", exc)

    if not tools:
        # fallback: simple curated baseline (could be extended via repo data)
        tools = [
            {"title": "OpenAI GPT‑4o", "url": "https://openai.com/", "source": "openai.com"},
            {"title": "Azure OpenAI Service", "url": "https://azure.microsoft.com/services/cognitive-services/openai-service/", "source": "azure.microsoft.com"},
            {"title": "Hugging Face Models", "url": "https://huggingface.co/models", "source": "huggingface.co"},
        ]

    # --- FUNDING ---
    # Allow user to specify custom RSS/pages via ENV (comma-separated)
    extra_funding_pages = [u.strip() for u in os.getenv("FUNDING_PAGES", "").split(",") if u.strip()]
    pages = FUNDING_HINT_PAGES + extra_funding_pages

    if not offline_only:
        try:
            for url in pages:
                items = harvest_links(url, allow_domains=None, limit=40)
                sel = [i for i in items if _match_any((i.get("title","") + " " + i.get("url","")), ["förder", "grant", "fund", "digital", "ai", "ki", "kmu", "sme"])]
                funding.extend(sel[:10])
        except Exception as exc:
            log.warning("FUNDING harvest failed: %s", exc)

    # fallback to static json
    if not funding:
        try:
            import json  # os already imported at top
            path = os.getenv("FUNDING_FALLBACK_PATH", "data/funding_programs.json")
            if os.path.exists(path):
                raw = json.load(open(path, "r", encoding="utf-8"))
                for it in raw[:12]:
                    # Fix: Support both "title" and "name" fields (JSON uses "name")
                    title = it.get("title") or it.get("name") or "Programm"
                    funding.append({
                        "title": title,
                        "url": it.get("url",""),
                        "source": it.get("url","")
                    })
        except Exception as exc:
            log.warning("FUNDING fallback failed: %s", exc)

    # --- NEWS (AI / EU‑AI‑Act relevant) ---
    if not offline_only:
        try:
            for url in (AI_ACT_NEWS_RSS + DEFAULT_NEWS_RSS):
                items = parse_rss(url, limit=8)
                sel = [i for i in items if _match_any((i.get("title","") + " " + i.get("summary","")), ["ai act","eu ai act","künstliche intelligenz","ki","sme","kmu","förderung","compliance","policy","gesetz"])]
                news.extend(sel[:6])
        except Exception as exc:
            log.warning("NEWS parse failed: %s", exc)

    # Deduplicate by URL
    def _uniq(lst: List[Dict[str, str]]) -> List[Dict[str, str]]:
        seen, out = set(), []
        for it in lst:
            u = it.get("url","")
            if not u or u in seen:
                continue
            seen.add(u)
            out.append(it)
        return out

    tools = _uniq(tools)[:12]
    funding = _uniq(funding)[:12]
    news = _uniq(news)[:12]

    data: Dict[str, Any] = {
        "TOOLS_TABLE_HTML": _tools_table(tools),
        "FUNDING_TABLE_HTML": _funding_table(funding),
        "NEWS_BOX_HTML": _news_box(news),
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    return data
