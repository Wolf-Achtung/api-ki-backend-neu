# -*- coding: utf-8 -*-
"""
Lightweight prompt templating engine for {{UPPER_CASE}} placeholders.
- Only replaces placeholders that exist in the context (upper-case keys).
- Supports JSON helpers for rich objects.
- Keeps unknown placeholders untouched (so templates stay future proof).
"""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Dict, Any

PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

def render_template(template_text: str, ctx: Dict[str, Any]) -> str:
    def _sub(m):
        key = m.group(1)
        val = ctx.get(key, m.group(0))
        if isinstance(val, (dict, list)):
            return dumps(val)
        return str(val)
    return PLACEHOLDER.sub(_sub, template_text)

def render_file(path: str | Path, ctx: Dict[str, Any]) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return render_template(text, ctx)
