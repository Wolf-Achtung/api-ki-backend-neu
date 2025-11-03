# file: app/services/report_renderer.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, Optional
from pathlib import Path
import os, logging

from settings import settings
from .template_engine import render_template
from .content_normalizer import normalize_and_enrich_sections  # hält KPIs/Defaults aktuell

LOGGER = logging.getLogger(__name__)

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
    # Normalize/Enrich (füllt KPI/Quellen/Tools + „So‑What“ Fallbacks u. a.)
    enriched = normalize_and_enrich_sections(
        briefing=briefing, snippets=snippets,
        metrics={"scores": scores or {}},
        scores=scores or {}, meta=meta or {}
    )
    # Logos optional (keine Pflicht)
    enriched.setdefault("logo_primary", enriched.get("logo_primary", ""))
    enriched.setdefault("logo_tuv", enriched.get("logo_tuv", ""))
    enriched.setdefault("logo_dsgvo", enriched.get("logo_dsgvo", ""))
    enriched.setdefault("logo_eu_ai", enriched.get("logo_eu_ai", ""))
    enriched.setdefault("logo_ready", enriched.get("logo_ready", ""))

    # Template laden (ENV: REPORT_TEMPLATE_PATH, sonst Fallback)
    tpl_path = Path(getattr(settings, "REPORT_TEMPLATE_PATH", "") or os.getenv("REPORT_TEMPLATE_PATH", "") or "templates/pdf_template.html")
    if not tpl_path.exists():
        # Fallback: lokale Datei im Arbeitsverzeichnis
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
