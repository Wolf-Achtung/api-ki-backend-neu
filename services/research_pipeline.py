# -*- coding: utf-8 -*-
from __future__ import annotations
import os, logging, html
from typing import Dict, Any, List
from .research_clients import hybrid

log = logging.getLogger(__name__)

def _table(rows: List[List[str]], head: List[str]) -> str:
    def esc(x): return html.escape(x or "")
    tr_head = "<thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead>"
    body = ""
    for r in rows:
        tds = "".join(f"<td>{esc(x)}</td>" for x in r)
        body += f"<tr>{tds}</tr>"
    return f"<table class='table'>{tr_head}<tbody>{body}</tbody></table>"

def run_research(answers: Dict[str,Any]) -> Dict[str,Any]:
    # queries
    branche = answers.get("BRANCHE_LABEL") or answers.get("branche","")
    bundesland = answers.get("BUNDESLAND_LABEL") or answers.get("bundesland","")
    days = int(os.getenv("RESEARCH_DAYS","14"))
    log.info("🔍 Research starting (hybrid) for %s/%s, days=%s", branche, bundesland, days)

    out: Dict[str,Any] = {"last_updated": os.getenv("RESEARCH_LAST_UPDATED","heute")}

    # Tools
    q_tools = f"Best AI tools for {branche or 'SMEs'} 2025 GDPR compliant site:eu OR site:com"
    tools = hybrid(q_tools, k=10, days=days)
    rows = []
    for t in tools:
        rows.append([t.get("title","Quelle"), "—", "—", "—", t.get("url","")])
    out["TOOLS_TABLE_HTML"] = _table(rows, ["Tool/Produkt","Kategorie","Preis","DSGVO/Host","Links"])

    # Funding
    region_hint = "Germany"
    if bundesland:
        region_hint = f"{bundesland} Germany"
    q_fund = f"Latest funding grants for AI and digitalization for SMEs {region_hint} 2025"
    funds = hybrid(q_fund, k=10, days=days)
    rows = []
    for f in funds:
        rows.append([f.get("title","Quelle"), region_hint, "—", "—", f.get("url","")])
    out["FUNDING_TABLE_HTML"] = _table(rows, ["Programm","Region","Förderquote","Frist","Link"])

    # AI Act
    q_ai = "EU AI Act timeline 2025 key dates obligations SMEs"
    ai_sources = hybrid(q_ai, k=8, days=days)
    # Just add as bullet list under SOURCES if needed
    if ai_sources:
        links = "".join(f"<li><a href='{html.escape(x.get('url',''))}'>{html.escape(x.get('title','Quelle'))}</a></li>" for x in ai_sources)
        out["AI_SOURCES_HTML"] = "<ul>"+links+"</ul>"

    return out
