# -*- coding: utf-8 -*-
"""
services.prompt_engine – v2.1 (Gold‑Standard+)
Einheitliche, sichere Prompt‑Templating‑Funktionen.

Merkmale
--------
- Unterstützt sowohl ``{{UPPER_CASE}}`` als auch ``{{ lower_case }}`` Platzhalter.
- Optionales HTML‑Escaping für Werte (default: ausgeschaltet – Loader übernimmt Escaping).
- JSON‑Serialisierung für dict/list (kompakt, UTF‑8).
- Unbekannte Platzhalter bleiben unangetastet → templates zukunftssicher.
- Reine Standardbibliothek; PEP8‑konform; Typannotationen.

Öffentliche API
---------------
- ``render_template(template_text, ctx, escape=False) -> str``
- ``render_file(path, ctx, escape=False) -> str``
"""
from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import json, re, html

# {{UPPER_CASE}}  ODER  {{ lower_case }}
_RE_UPPER = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")
_RE_LOWER = re.compile(r"\{\{\s*([a-z0-9_]+)\s*\}\}")

def _dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

def _value(val: Any, escape: bool) -> str:
    if isinstance(val, (dict, list)):
        s = _dumps(val)
    else:
        s = "" if val is None else str(val)
    return html.escape(s) if escape else s

def render_template(template_text: str, ctx: Dict[str, Any], escape: bool = False) -> str:
    """Render ``template_text`` mit Werten aus ``ctx``.
    - Upper‑Case Keys ("FOO_BAR") und lower‑case Keys ("foo_bar") werden unterstützt.
    - Unbekannte Platzhalter bleiben erhalten.
    """
    def sub_upper(m):
        key = m.group(1)
        val = ctx.get(key, m.group(0))
        return _value(val, escape)
    def sub_lower(m):
        key = m.group(1)
        # lower‑case kann aus ctx direkt, oder aus Upper‑Case als Fallback kommen
        v = ctx.get(key, ctx.get(key.upper(), m.group(0)))
        return _value(v, escape)
    out = _RE_UPPER.sub(sub_upper, template_text)
    out = _RE_LOWER.sub(sub_lower, out)
    return out

def render_file(path: str | Path, ctx: Dict[str, Any], escape: bool = False) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return render_template(text, ctx, escape=escape)
