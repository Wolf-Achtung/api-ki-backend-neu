# -*- coding: utf-8 -*-
from __future__ import annotations
"""Erweiterter Renderer: füllt fehlende Abschnitte automatisch (Tools, Förderungen, Security, Wettbewerber, ROI)."""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.tools_recommender import recommend_tools, to_html as tools_html
from services.funding_parser import suggest_programs, to_html as funding_html
from services.security_roadmap import build_security_roadmap, to_html as security_html
from services.competitor_insights import build_insights, to_html as competitors_html
from services.roi_calculator import calc_roi, to_html as roi_html

def _is_abs(u: str) -> bool:
    try:
        p = urlparse(u or "")
        return bool(p.scheme and p.netloc) or (u or "").startswith("/")
    except Exception:
        return False

def _to_data_uri(path: str) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        p2 = Path("templates") / path
        if p2.exists(): p = p2
        else: return ""
    mime = "image/png"
    if p.suffix.lower() in (".jpg",".jpeg"): mime = "image/jpeg"
    elif p.suffix.lower() == ".svg":
        try: return "data:image/svg+xml;utf8," + p.read_text(encoding="utf-8")
        except: return ""
    elif p.suffix.lower() == ".webp": mime = "image/webp"
    try:
        b = p.read_bytes()
        import base64
        return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")
    except Exception:
        return ""

def _alias(sections: Dict[str,Any]) -> Dict[str,Any]:
    ctx = dict(sections)
    # Header
    ctx.setdefault("COMPANY_NAME", sections.get("COMPANY_NAME") or sections.get("customer_name") or "")
    ctx.setdefault("BRANCHE_LABEL", sections.get("BRANCHE_LABEL") or sections.get("branche_label") or "")
    ctx.setdefault("UNTERNEHMENSGROESSE_LABEL", sections.get("UNTERNEHMENSGROESSE_LABEL") or sections.get("groesse_label") or "")
    ctx.setdefault("BUNDESLAND_LABEL", sections.get("BUNDESLAND_LABEL") or sections.get("bundesland_label") or "")

    ctx["customer_name"]    = ctx.get("COMPANY_NAME","")
    ctx["branche_label"]    = ctx.get("BRANCHE_LABEL","")
    ctx["groesse_label"]    = ctx.get("UNTERNEHMENSGROESSE_LABEL","")
    ctx["bundesland_label"] = ctx.get("BUNDESLAND_LABEL","")

    # Blöcke
    ctx["executive_summary_html"] = sections.get("EXECUTIVE_SUMMARY_HTML") or ""
    quick = sections.get("QUICK_WINS_HTML") or (sections.get("QUICK_WINS_HTML_LEFT","") + sections.get("QUICK_WINS_HTML_RIGHT",""))
    ctx["recommendations_html"] = quick

    # Scores
    def num(x): 
        try: return int(round(float(x)))
        except: return 0
    ctx["scores"] = [
        {"label":"Governance","value":num(sections.get("score_governance"))},
        {"label":"Sicherheit","value":num(sections.get("score_sicherheit"))},
        {"label":"Nutzen","value":num(sections.get("score_nutzen"))},
        {"label":"Befähigung","value":num(sections.get("score_befaehigung"))},
        {"label":"Gesamt","value":num(sections.get("score_gesamt") or 0)},
    ]

    # Logos als Data-URIs
    for k in ("LOGO_PRIMARY_SRC","COVER_BADGE_SRC","FOOTER_LEFT_LOGO_SRC","FOOTER_MID_LOGO_SRC","FOOTER_RIGHT_LOGO_SRC"):
        v = str(sections.get(k) or "").strip()
        if v and not _is_abs(v):
            data_uri = _to_data_uri(v)
            if data_uri: ctx[k] = data_uri

    # Build
    ctx.setdefault("BUILD_STAMP", f"Stand: {sections.get('report_date','')} · Report-ID: {sections.get('REPORT_PUBLIC_ID','')}")

    return ctx

def render(briefing: Any, run_id: Optional[str]=None, generated_sections: Optional[Dict[str,Any]]=None,
           use_fetchers: Optional[Dict[str,Any]]=None, scores: Optional[Dict[str,Any]]=None,
           meta: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
    sections = generated_sections or {}
    ctx = _alias(sections)

    # Auto-Füller
    if not sections.get("TOOLS_HTML"):
        rec = recommend_tools(briefing or {})
        ctx["TOOLS_HTML"] = tools_html(rec)
    if not sections.get("FOERDERPROGRAMME_HTML"):
        progs = suggest_programs(briefing or {})
        ctx["FOERDERPROGRAMME_HTML"] = funding_html(progs)
    if not sections.get("SECURITY_ROADMAP_HTML"):
        rd = build_security_roadmap(briefing or {}, scores or {})
        ctx["SECURITY_ROADMAP_HTML"] = security_html(rd)
    if not sections.get("COMPETITORS_HTML"):
        ins = build_insights(briefing or {})
        ctx["COMPETITORS_HTML"] = competitors_html(ins)
    if not sections.get("ROI_HTML"):
        # Quick Wins in strukturierter Form optional aus sections holen (falls vorhanden)
        ctx["ROI_HTML"] = roi_html(calc_roi(briefing or {}, []))

    # Template
    tpl_path = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")
    env = Environment(loader=FileSystemLoader(Path(tpl_path).parent or "templates"),
                      autoescape=select_autoescape(["html","xml"]), trim_blocks=True, lstrip_blocks=True)
    tpl = env.get_template(Path(tpl_path).name)
    html = tpl.render(**ctx)
    out_meta = dict(meta or {})
    out_meta.setdefault("scores", ctx.get("scores"))
    return {"html": html, "meta": out_meta}
