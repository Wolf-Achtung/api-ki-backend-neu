# -*- coding: utf-8 -*-
from __future__ import annotations
import html
import re
from typing import Dict, Any

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

def render_template(template: str, context: Dict[str, Any], default: str = "", escape_html: bool = True) -> str:
    """
    Render a template with variable substitution.

    Args:
        template: Template string with {{VARIABLE}} placeholders
        context: Dictionary of variable values
        default: Default value for missing variables
        escape_html: If True, HTML-escape all values (recommended for security)

    Returns:
        Rendered template string

    Security Note:
        HTML-escaping is enabled by default to prevent XSS attacks.
        Only disable if you are certain all values are safe.
    """
    def repl(m: re.Match) -> str:
        key = m.group(1)
        val = context.get(key, default)
        if val is None:
            return ""
        val_str = str(val)
        # SECURITY: HTML-escape by default to prevent XSS
        if escape_html:
            return html.escape(val_str)
        return val_str
    return PLACEHOLDER_RE.sub(repl, template)
