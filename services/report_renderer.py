# -*- coding: utf-8 -*-
from __future__ import annotations
"""Render the final report HTML from a template and section fragments."""
from pathlib import Path
from typing import Dict
import re

PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

def render(template_path: str | Path, mapping: Dict[str, str]) -> str:
    html = Path(template_path).read_text(encoding="utf-8")
    def _sub(match: re.Match) -> str:
        key = match.group(1)
        return str(mapping.get(key, ""))
    return PLACEHOLDER.sub(_sub, html)
