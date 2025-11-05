# -*- coding: utf-8 -*-
from __future__ import annotations
"""
services.report_renderer – Gold‑Standard+
- Fester UTF‑8‑Pfad; robustes Laden des Templates.
- Fallbacks: render_template/content_normalizer optional – verhindert Import‑Hard‑fail.
- Public API:
    render(briefing, run_id, generated_sections, use_fetchers, scores, meta) -> {"html": str, "meta": dict}
"""
from typing import Any, Dict, Optional
from pathlib import Path
import os
import logging

from settings import settings

LOGGER = logging.getLogger(__name__)

# Fallback‑Implementierungen, falls optionale Module fehlen.
try:
    from .template_engine import render_template  # type: ignore
except Exception:  # why: App darf auch ohne Template‑Engine starten
    def render_template(template_str: str, context: Dict[str, Any], default: str = "") -> str:
        out = template_str or ""
        # sehr einfache {{key}}‑Ersetzung (nur für Fallback)
        for k, v in (context or {}).items():
            out = out.replace("{{" + k + "}}", str(v))
        return out or default

try:
    from .content_normalizer import normalize_and_enrich_sections  # type: ignore
except Exception:  # why: Notfalls ohne Enrichment
    def normalize_and_enrich_sections(briefing: Dict[str, Any], snippets: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        base = dict(briefing or {})
        base.update(snippets or {})
        # Vereinheitliche Platzhalter: Tools/Förderungen
        if base.get("TOOLS_TABLE_HTML"):
            base.setdefault("TOOLS_HTML", base["TOOLS_TABLE_HTML"])
        if base.get("FUNDING_TABLE_HTML"):
            base.setdefault("FOERDERPROGRAMME_HTML", base["FUNDING_TABLE_HTML"])
        # Forschungsdatum übernehmen
        research_date = base.get("research_last_updated") or base.get("report_date") or ""
        if research_date:
            base.setdefault("research_last_updated", research_date)
        return base

def _read_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception as exc:
        LOGGER.error("Template read failed: %s", exc)
        return ""

def build_full_report_html(
    briefing: Dict[str, Any],
    generated_sections: Optional[Dict[str, Any]] = None,
    use_fetchers: bool = True,
    scores: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """Mergen: Briefing + generierte Sections -> finaler Context -> Template."""
    snippets: Dict[str, Any] = dict(generated_sections or {})
    enriched = normalize_and_enrich_sections(
        briefing=briefing, snippets=snippets,
        metrics={"scores": scores or {}},
        scores=scores or {}, meta=meta or {}
    )
    # Logos optional (keine Pflicht)
    for key in ("logo_primary","logo_tuv","logo_dsgvo","logo_eu_ai","logo_ready"):
        enriched.setdefault(key, enriched.get(key, ""))

    # Template laden (ENV: REPORT_TEMPLATE_PATH, sonst Fallback)
    tpl_path = Path(getattr(settings, "REPORT_TEMPLATE_PATH", "") or os.getenv("REPORT_TEMPLATE_PATH", "") or "templates/pdf_template.html")
    if not tpl_path.exists():
        alt = Path("pdf_template.html")
        tpl_path = alt if alt.exists() else tpl_path
    tpl = _read_file(tpl_path)
    return render_template(tpl, enriched, default="")

def render(
    briefing: Any,
    run_id: Optional[str] = None,
    generated_sections: Optional[Dict[str, Any]] = None,
    use_fetchers: bool = True,
    scores: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Wrapper, wie von gpt_analyze.py verwendet."""
    # Briefing‑Objekt → Dict + Answers hochziehen (Kompatibilität zum Bestand)
    if hasattr(briefing, "__dict__"):
        bdict: Dict[str, Any] = {
            "id": getattr(briefing, "id", None),
            "user_id": getattr(briefing, "user_id", None),
            "lang": getattr(briefing, "lang", "de"),
            "answers": getattr(briefing, "answers", {}),
            "created_at": getattr(briefing, "created_at", None),
        }
        bdict.update(bdict.get("answers", {}))
    else:
        bdict = dict(briefing or {})

    html = build_full_report_html(
        briefing=bdict,
        generated_sections=generated_sections or {},
        use_fetchers=use_fetchers,
        scores=scores or {},
        meta=meta or {},
    )
    meta_out: Dict[str, Any] = {
        "briefing_id": bdict.get("id"),
        "run_id": run_id,
        "sections_count": len(generated_sections or {}),
        "html_length": len(html),
        "fetchers_used": use_fetchers,
    }
    return {"html": html, "meta": meta_out}
