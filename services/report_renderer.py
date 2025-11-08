# -*- coding: utf-8 -*-
from __future__ import annotations
import os, base64
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ._normalize import _briefing_to_dict
from .tools_recommender import recommend_tools, to_html as tools_html
from .funding_parser import suggest_programs, to_html as funding_html
from .security_roadmap import build_security_roadmap, to_html as security_html
from .competitor_insights import build_insights, to_html as competitors_html
from .roi_calculator import calc_roi, to_html as roi_html

STRICT_DATASET = os.getenv("RENDER_STRICT_DATASET", "1") == "1"

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
        if p2.exists():
            p = p2
        else:
            return ""
    mime = "image/png"
    s = p.suffix.lower()
    if s in (".jpg",".jpeg"):
        mime = "image/jpeg"
    elif s == ".svg":
        try:
            return "data:image/svg+xml;utf8," + p.read_text(encoding="utf-8")
        except Exception:
            return ""
    elif s == ".webp":
        mime = "image/webp"
    try:
        b = p.read_bytes()
        return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")
    except Exception:
        return ""

def _alias(sections: Dict[str,Any], meta: Optional[Dict[str,Any]] = None) -> Dict[str,Any]:
    ctx = dict(sections or {})
    # Aliases
    ctx.setdefault("COMPANY_NAME", ctx.get("COMPANY_NAME") or ctx.get("customer_name") or "")
    ctx.setdefault("BRANCHE_LABEL", ctx.get("BRANCHE_LABEL") or ctx.get("branche_label") or "")
    ctx.setdefault("UNTERNEHMENSGROESSE_LABEL", ctx.get("UNTERNEHMENSGROESSE_LABEL") or ctx.get("groesse_label") or "")
    ctx.setdefault("BUNDESLAND_LABEL", ctx.get("BUNDESLAND_LABEL") or ctx.get("bundesland_label") or "")

    ctx["customer_name"]    = ctx.get("COMPANY_NAME","")
    ctx["branche_label"]    = ctx.get("BRANCHE_LABEL","")
    ctx["groesse_label"]    = ctx.get("UNTERNEHMENSGROESSE_LABEL","")
    ctx["bundesland_label"] = ctx.get("BUNDESLAND_LABEL","")

    # Scores
    def num(x):
        try:
            return int(round(float(x)))
        except Exception:
            return 0
    ctx["scores"] = [
        {"label":"Governance","value":num(ctx.get("score_governance"))},
        {"label":"Sicherheit","value":num(ctx.get("score_sicherheit"))},
        {"label":"Nutzen","value":num(ctx.get("score_nutzen"))},
        {"label":"Befähigung","value":num(ctx.get("score_befaehigung"))},
        {"label":"Gesamt","value":num(ctx.get("score_gesamt") or 0)},
    ]

    # Logos: erst aus ctx, dann ENV
    for k in ("LOGO_PRIMARY_SRC","COVER_BADGE_SRC","FOOTER_LEFT_LOGO_SRC","FOOTER_MID_LOGO_SRC","FOOTER_RIGHT_LOGO_SRC"):
        v = str(ctx.get(k) or "").strip()
        if not v:
            v = os.getenv(k,"").strip()
            if v:
                ctx[k] = v
        if v and not _is_abs(v):
            data_uri = _to_data_uri(v)
            if data_uri:
                ctx[k] = data_uri

    # Feedback-URL aus ENV, falls leer
    if not ctx.get("FEEDBACK_URL"):
        env_fb = os.getenv("FEEDBACK_URL")
        if env_fb:
            ctx["FEEDBACK_URL"] = env_fb

    # Research-Stand
    ctx["RESEARCH_LAST_UPDATED"] = ctx.get("RESEARCH_LAST_UPDATED") or (meta or {}).get("research_last_updated") or os.getenv("REPORT_DATE") or ""

    # Build-Stempel
    ctx.setdefault("BUILD_STAMP", f"Stand: {ctx.get('report_date','')} · Report-ID: {ctx.get('REPORT_PUBLIC_ID','')}")
    return ctx

def render(briefing: Any, run_id: Optional[str]=None, generated_sections: Optional[Dict[str,Any]]=None,
           use_fetchers: Optional[Dict[str,Any]]=None, scores: Optional[Dict[str,Any]]=None,
           meta: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
    sections = generated_sections or {}
    ctx = _alias(sections, meta=meta)
    b = _briefing_to_dict(briefing)

    # Daten aus kuratierten Modulen — strikt (überschreibt ggf. LLM-Ausgaben)
    if STRICT_DATASET or not sections.get("TOOLS_HTML"):
        rec = recommend_tools(b)
        ctx["TOOLS_HTML"] = tools_html(rec)

    if STRICT_DATASET or not sections.get("FOERDERPROGRAMME_HTML"):
        progs = suggest_programs(b)
        ctx["FOERDERPROGRAMME_HTML"] = funding_html(progs, research_stand=ctx.get("RESEARCH_LAST_UPDATED",""))

    if STRICT_DATASET or not sections.get("SECURITY_ROADMAP_HTML"):
        rd = build_security_roadmap(b, scores or {})
        ctx["SECURITY_ROADMAP_HTML"] = security_html(rd)

    if STRICT_DATASET or not sections.get("COMPETITORS_HTML"):
        ins = build_insights(b)
        ctx["COMPETITORS_HTML"] = competitors_html(ins)

    if STRICT_DATASET or not sections.get("ROI_HTML"):
        ctx["ROI_HTML"] = roi_html(calc_roi(b, []))

    # Template
    tpl_path = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")
    tpl_dir = Path(tpl_path).parent or Path("templates")
    env = Environment(loader=FileSystemLoader(tpl_dir),
                      autoescape=select_autoescape(["html","xml"]), trim_blocks=True, lstrip_blocks=True)
    tpl = env.get_template(Path(tpl_path).name)
    html = tpl.render(**ctx)

    out_meta = dict(meta or {})
    out_meta.setdefault("scores", ctx.get("scores"))
    out_meta.setdefault("research_last_updated", ctx.get("RESEARCH_LAST_UPDATED",""))
    return {"html": html, "meta": out_meta}
