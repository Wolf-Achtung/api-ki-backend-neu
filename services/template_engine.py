# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import Dict, Any

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

def render_template(template: str, context: Dict[str, Any], default: str = "") -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        val = context.get(key, default)
        return "" if val is None else str(val)
    return PLACEHOLDER_RE.sub(repl, template)
