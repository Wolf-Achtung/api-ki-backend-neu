# -*- coding: utf-8 -*-
from __future__ import annotations
import os, logging
from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

log = logging.getLogger(__name__)

def _env() -> Environment:
    tpl_dir = Path(os.getenv("REPORT_TEMPLATE_DIR", "templates"))
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html","xml"]),
        undefined=None,  # allow missing vars
        trim_blocks=True, lstrip_blocks=True,
    )
    # Backwards-compat filter for old templates using {{LANG|de}}
    env.filters["de"] = lambda v=None: (v or "de")
    return env

def _self_check(env: Environment, template_name: str) -> None:
    """Validate template at startup to avoid runtime surprises."""
    try:
        src = env.loader.get_source(env, template_name)[0]
        if "{{LANG|de}}" in src or "{{ LANG|de }}" in src:
            log.warning("⚠️ Template uses deprecated '|de' filter. Please switch to '|default(\"de\")'.")
        # Try compile (will raise if invalid)
        env.get_template(template_name)
        log.info("✓ Template validated: %s", template_name)
    except Exception as exc:
        log.error("❌ Template validation failed: %s", exc)
        raise

def render(briefing_obj: Any,
           run_id: str,
           generated_sections: Dict[str, Any],
           use_fetchers: bool = False,
           scores: Optional[Dict[str, Any]] = None,
           meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    tpl_path = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")
    tpl_dir = Path(tpl_path).parent
    tpl_name = Path(tpl_path).name

    env = _env()
    _self_check(env, tpl_name)

    # Context
    sections = dict(generated_sections or {})
    # Alias FUNDING if necessary
    if not sections.get("FUNDING_HTML") and sections.get("FOERDERPROGRAMME_HTML"):
        sections["FUNDING_HTML"] = sections["FOERDERPROGRAMME_HTML"]

    # Safe defaults
    ctx = {
        "LANG": sections.get("LANG", "de"),
        "OWNER_NAME": sections.get("OWNER_NAME", os.getenv("OWNER_NAME","KI‑Sicherheit.jetzt")),
        "report_date": sections.get("report_date", ""),
        "report_id": sections.get("report_id", ""),
        "report_year": sections.get("report_year", ""),
        "BRANCHE_LABEL": sections.get("BRANCHE_LABEL",""),
        "UNTERNEHMENSGROESSE_LABEL": sections.get("UNTERNEHMENSGROESSE_LABEL",""),
        "BUNDESLAND_LABEL": sections.get("BUNDESLAND_LABEL",""),
        "HAUPTLEISTUNG": sections.get("HAUPTLEISTUNG",""),
        # dynamic sections
        **sections,
    }

    html = env.get_template(tpl_name).render(**ctx)
    return {"html": html, "meta": meta or {}}
