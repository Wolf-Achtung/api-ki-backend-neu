# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Load curated knowledge blocks (HTML partials) to enrich the report with
serious, well-structured foundations.
"""
from pathlib import Path
from typing import Dict

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def get_knowledge_blocks(lang: str = "de") -> Dict[str, str]:
    base = Path("knowledge") / lang
    return {
        "KB_FOUR_PILLARS_HTML": _read(base / "four_pillars.html"),
        "KB_102070_HTML": _read(base / "ten_20_70.html"),
        "KB_LEGAL_PITFALLS_HTML": _read(base / "legal_pitfalls.html"),
        "KB_KMU_KEYPOINTS_HTML": _read(base / "kmu_keypoints.html"),
    }
