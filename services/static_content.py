# -*- coding: utf-8 -*-
"""
services/static_content.py – Loader für statische Report-Blöcke
- Lädt optionale HTML-Partials aus templates/partials
- Liefert sie als Dict mit APPENDIX_*_HTML-Keys zurück
- Fehlertolerant: Bei Fehlern werden leere Strings geliefert
"""
from __future__ import annotations
from typing import Dict
import os
from pathlib import Path
from datetime import datetime

PARTIALS = {
    "APPENDIX_INTRO_HTML": "intro.html",  # optional
    "APPENDIX_DSGVO_AI_HTML": "grundlagen_dsgvo_ai_act.html",
    "APPENDIX_TOOL_OVERVIEW_HTML": "tools_overview.html",
    "APPENDIX_CREATIVE_TOOLS_HTML": "guide_kreativtools_2025.html",
    "APPENDIX_USE_CASES_HTML": "use_cases_kmu_generic.html",
}

def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8").strip()
    except Exception:
        return ""

def load_static_annex(base_dir: str | None = None) -> Dict[str, str]:
    if os.getenv("APPENDIX_ENABLE", "1") != "1":
        return {}
    base = Path(base_dir or ".") / "templates" / "partials"
    out: Dict[str, str] = {}
    for key, filename in PARTIALS.items():
        out[key] = _read(base / filename)
    out["APPENDIX_LAST_UPDATED"] = datetime.now().strftime("%d.%m.%Y")
    return out