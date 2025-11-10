
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

def _merge(a: Dict[str, Any], b: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = dict(a or {})
    for k, v in (b or {}).items():
        # Allow falsy values like 0; only skip None
        if v is None:
            continue
        out[k] = v
    return out

def _briefing_basics(br) -> Dict[str, Any]:
    # br can be ORM model or dict-like
    answers = getattr(br, "answers", None) or {}
    ctx = {
        "BRANCHE_LABEL": answers.get("BRANCHE_LABEL") or answers.get("branche", ""),
        "UNTERNEHMENSGROESSE_LABEL": answers.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse", ""),
        "BUNDESLAND_LABEL": answers.get("BUNDESLAND_LABEL") or answers.get("bundesland", ""),
        "HAUPTLEISTUNG": answers.get("hauptleistung", ""),
    }
    return ctx

def render(br,
           run_id: str,
           generated_sections: Dict[str, Any],
           use_fetchers: bool = False,
           scores: Optional[Dict[str, Any]] = None,
           meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Minimalistische, robuste Renderer-Funktion:
    - Fügt die generierten HTML-Blöcke 1:1 in das Jinja-Template ein
    - Keine harten Placeholder mehr (Fehlerursache im Log)
    - Unterstützt Logos/Branding über ENV-Variablen
    """
    # Basis-Kontext
    ctx: Dict[str, Any] = {}
    ctx.update(_briefing_basics(br))
    ctx.update({
        "report_date": generated_sections.get("report_date"),
        "report_id": generated_sections.get("report_id"),
        "report_year": generated_sections.get("report_year"),
        "OWNER_NAME": os.getenv("OWNER_NAME", "KI‑Sicherheit.jetzt"),
        "LOGO_PRIMARY_SRC": os.getenv("LOGO_PRIMARY_SRC", ""),
        "FOOTER_LEFT_LOGO_SRC": os.getenv("FOOTER_LEFT_LOGO_SRC", ""),
        "FOOTER_MID_LOGO_SRC": os.getenv("FOOTER_MID_LOGO_SRC", ""),
        "FOOTER_RIGHT_LOGO_SRC": os.getenv("FOOTER_RIGHT_LOGO_SRC", ""),
        "FOOTER_BRANDS_HTML": os.getenv("FOOTER_BRANDS_HTML", ""),
    })
    # Alle generierten Abschnitte in den Kontext mergen
    ctx = _merge(ctx, generated_sections)

    # Template laden
    tpl_path = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")
    tpl_dir = Path(tpl_path).parent or Path("templates")
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template(Path(tpl_path).name)
    html = tpl.render(**ctx)

    out_meta = dict(meta or {})
    if scores:
        out_meta.setdefault("scores", scores)
    out_meta.setdefault("research_last_updated", ctx.get("research_last_updated", ""))
    return {"html": html, "meta": out_meta}
