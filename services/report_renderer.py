
# -*- coding: utf-8 -*-
from __future__ import annotations

"""services.report_renderer – Jinja2-basiertes Rendering (Gold-Standard+)

Exportiert:
    render(briefing, run_id=None, generated_sections=None, use_fetchers=None, scores=None, meta=None) -> dict
        Liefert {'html': <str>, 'meta': <dict>}.
        - Nutzt Jinja2 für templates/ (REPORT_TEMPLATE_PATH, Default: templates/pdf_template.html)
        - Setzt sinnvolle Aliase (UPPERCASE -> lower_snake_case), z. B. COMPANY_NAME -> customer_name
        - Wandelt Logo-Pfade in Data-URIs, wenn es keine absoluten URLs sind (stabile Assets in PaaS-Umgebungen)
        - Baut ein 'scores' Array (label/value/hint) für die Mini-Balken im Template

Voraussetzungen: jinja2 (pip install Jinja2)
"""

import os
import base64
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _is_absolute_url(s: str) -> bool:
    if not s or not isinstance(s, str): 
        return False
    try:
        u = urlparse(s)
        return bool(u.scheme and u.netloc) or s.startswith("/")
    except Exception:
        return False


def _to_data_uri(path: str) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        # Try relative to templates/
        tp = Path("templates") / path
        if tp.exists():
            p = tp
        else:
            return ""
    mime = "image/png"
    suf = p.suffix.lower()
    if suf in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    elif suf == ".svg":
        try:
            data = p.read_text(encoding="utf-8")
            return f"data:image/svg+xml;utf8,{data}"
        except Exception:
            return ""
    elif suf == ".webp":
        mime = "image/webp"
    elif suf == ".gif":
        mime = "image/gif"
    try:
        b = p.read_bytes()
        import base64 as _b64
        b64 = _b64.b64encode(b).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""


def _alias_context(sections: Dict[str, Any], scores: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Mappt UPPERCASE-Keys auf die im Template verwendeten lower_snake_case-Keys und baut helpers."""
    ctx = dict(sections)

    # Build stamp / version
    version_full = str(sections.get("version") or sections.get("VERSION") or os.getenv("VERSION") or "1.0.0")
    version_mm = ".".join(version_full.split(".")[:2]) if version_full else "1.0"
    ctx.setdefault("report_version", version_mm)

    # Primary aliases for header
    ctx.setdefault("COMPANY_NAME", sections.get("COMPANY_NAME") or sections.get("customer_name") or "")
    ctx.setdefault("BRANCHE_LABEL", sections.get("BRANCHE_LABEL") or sections.get("branche_label") or "")
    ctx.setdefault("UNTERNEHMENSGROESSE_LABEL", sections.get("UNTERNEHMENSGROESSE_LABEL") or sections.get("groesse_label") or "")
    ctx.setdefault("BUNDESLAND_LABEL", sections.get("BUNDESLAND_LABEL") or sections.get("bundesland_label") or "")

    # Lowercase aliases used by some templates
    ctx["customer_name"]    = ctx.get("COMPANY_NAME", "")
    ctx["branche_label"]    = ctx.get("BRANCHE_LABEL", "")
    ctx["groesse_label"]    = ctx.get("UNTERNEHMENSGROESSE_LABEL", "")
    ctx["bundesland_label"] = ctx.get("BUNDESLAND_LABEL", "")

    # Content blocks (keep both cases)
    ctx["executive_summary_html"] = sections.get("EXECUTIVE_SUMMARY_HTML") or sections.get("executive_summary_html") or ""
    # recommendations_html: bevorzugt vorbereitete Quick-Wins (Links + Rechts konsolidiert)
    rec = sections.get("QUICK_WINS_HTML") or ""
    if not rec:
        left = sections.get("QUICK_WINS_HTML_LEFT") or ""
        right = sections.get("QUICK_WINS_HTML_RIGHT") or ""
        rec = (left or "") + (right or "")
    ctx["recommendations_html"] = rec

    ctx["kreativ_tools_html"]   = sections.get("KREATIV_TOOLS_HTML") or ""
    ctx["sources_html"]         = sections.get("QUELLEN_HTML") or sections.get("SOURCES_BOX_HTML") or ""
    ctx["last_updated"]         = sections.get("research_last_updated") or sections.get("report_date") or ""

    # Scores: build array for mini-bars + keep individual values (0..100)
    score_list = []
    def _to_num(x): 
        try: return int(round(float(x)))
        except Exception: return 0
    sg = _to_num(sections.get("score_governance", 0))
    ss = _to_num(sections.get("score_sicherheit", 0))
    sv = _to_num(sections.get("score_nutzen", 0))
    se = _to_num(sections.get("score_befaehigung", 0))
    so = _to_num(sections.get("score_gesamt", max(0, min(100, (sg+ss+sv+se)//4))))
    score_list.extend([
        {"label": "Governance", "value": sg, "hint": ""},
        {"label": "Sicherheit", "value": ss, "hint": ""},
        {"label": "Nutzen", "value": sv, "hint": ""},
        {"label": "Befähigung", "value": se, "hint": ""},
        {"label": "Gesamt", "value": so, "hint": ""},
    ])
    ctx["scores"] = score_list

    # Logos: if not absolute URL, build data-URI (stable in PaaS)
    def _abs(s: str) -> bool:
        try:
            from urllib.parse import urlparse
            u = urlparse(s or "")
            return bool(u.scheme and u.netloc) or (s or "").startswith("/")
        except Exception:
            return False
    for key in ("LOGO_PRIMARY_SRC", "COVER_BADGE_SRC", "FOOTER_LEFT_LOGO_SRC", "FOOTER_MID_LOGO_SRC", "FOOTER_RIGHT_LOGO_SRC"):
        src = str(sections.get(key) or "").strip()
        if src and not _abs(src):
            data_uri = _to_data_uri(src)
            if data_uri:
                ctx[key] = data_uri  # overwrite with data-URI for stability

    # Build stamp
    if "BUILD_STAMP" not in ctx:
        report_date = ctx.get("report_date") or ctx.get("last_updated") or ""
        report_id   = ctx.get("report_id") or ctx.get("REPORT_PUBLIC_ID") or ""
        ctx["BUILD_STAMP"] = f"Stand: {report_date} · Report-ID: {report_id} · v{ctx.get('report_version','')}"

    return ctx


def render(briefing: Any, run_id: Optional[str] = None, generated_sections: Optional[Dict[str, Any]] = None,
           use_fetchers: Optional[Dict[str, Any]] = None, scores: Optional[Dict[str, Any]] = None,
           meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Rendert das PDF-HTML via Jinja2 und liefert {'html':..., 'meta':...}."""
    sections = generated_sections or {}
    tpl_path = os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")
    tpl_dir  = str(Path(tpl_path).parent)
    tpl_name = Path(tpl_path).name

    env = Environment(
        loader=FileSystemLoader(tpl_dir or "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template(tpl_name)

    ctx = _alias_context(sections, scores)
    # zusätzliche Standardwerte
    ctx.setdefault("FEEDBACK_URL", os.getenv("FEEDBACK_URL", os.getenv("FEEDBACK_REDIRECT_BASE", "")))
    ctx.setdefault("rendered_at", sections.get("report_date", ""))

    html = tpl.render(**ctx)

    out_meta = dict(meta or {})
    out_meta.setdefault("scores", ctx.get("scores", []))
    out_meta.setdefault("research_last_updated", ctx.get("last_updated", ""))
    return {"html": html, "meta": out_meta}
