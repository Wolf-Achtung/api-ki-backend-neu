# -*- coding: utf-8 -*-
"""
Tiny template engine for {{placeholders}} with safe defaults.
"""
from __future__ import annotations
import logging
import re
from typing import Dict, Any

LOGGER = logging.getLogger(__name__)

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

def render_template(template: str, context: Dict[str, Any], default: str = "") -> str:
    def repl(match: re.Match) -> str:
        key = match.group(1)
        val = context.get(key, default)
        return "" if val is None else str(val)
    return PLACEHOLDER_RE.sub(repl, template)
