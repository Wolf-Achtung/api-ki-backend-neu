# -*- coding: utf-8 -*-
"""
services.html_sanitizer
-----------------------
Kleiner, abhängigkeitsfreier Sanitizer für Abschnitts‑HTML.
Ziele:
- Entfernt komplette Dokument‑Wrapper (<html>, <head>, <body>, <!DOCTYPE>)
- Entfernt <script>, <iframe>, <object>, <embed>, <link>, <meta>
- Entfernt Inline‑Eventhandler (onClick, onload, …)
- Optional: komprimiert Whitespace
- Erhält valide Teil‑HTML (Listen, Tabellen, Divs, etc.) unverändert

Hinweis: bewusst konservativ, um Layout nicht zu zerstören.
"""
from __future__ import annotations
import re
from typing import Optional

_TRUTHY = {"1","true","TRUE","yes","YES","on","y"}

RE_DOCTYPES = re.compile(r"(?is)<!DOCTYPE.*?>")
RE_HTML_TAGS = re.compile(r"(?is)</?\s*html\b.*?>")
RE_HEAD_BLOCK = re.compile(r"(?is)<\s*head\b.*?>.*?</\s*head\s*>")
RE_BODY_TAGS = re.compile(r"(?is)</?\s*body\b.*?>")

# Tags, die komplett entfernt werden (inkl. Inhalt bei head)
RE_SCRIPT_BLOCK = re.compile(r"(?is)<\s*script\b.*?>.*?</\s*script\s*>")
RE_IFRAME_BLOCK = re.compile(r"(?is)<\s*iframe\b.*?>.*?</\s*iframe\s*>")
RE_OBJECT_BLOCK = re.compile(r"(?is)<\s*object\b.*?>.*?</\s*object\s*>")
RE_EMBED_BLOCK  = re.compile(r"(?is)<\s*embed\b.*?>.*?</\s*embed\s*>")
RE_LINK_TAG     = re.compile(r"(?is)<\s*link\b.*?/?>")
RE_META_TAG     = re.compile(r"(?is)<\s*meta\b.*?/?>")

# Inline‑Eventhandler (onload=, onclick=, …)
RE_ON_EVENT_ATTR = re.compile(r"(?i)\s+on[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*')")

# Daten‑/Sicherheitsfilter: Entferne javascript: URIs in href/src
RE_JS_PROTOCOL = re.compile(r"(?is)(\s(?:href|src)\s*=\s*['\"])\s*javascript:[^'\"]*(['\"])")

def sanitize_section_html(html: Optional[str], compress_ws: bool = True) -> str:
    if not html:
        return ""
    s = html

    # Entferne Dokument‑Wrapper & kritische Blöcke
    s = RE_DOCTYPES.sub("", s)
    s = RE_HEAD_BLOCK.sub("", s)
    s = RE_HTML_TAGS.sub("", s)
    s = RE_BODY_TAGS.sub("", s)

    # Entferne gefährliche Tags
    s = RE_SCRIPT_BLOCK.sub("", s)
    s = RE_IFRAME_BLOCK.sub("", s)
    s = RE_OBJECT_BLOCK.sub("", s)
    s = RE_EMBED_BLOCK.sub("", s)
    s = RE_LINK_TAG.sub("", s)
    s = RE_META_TAG.sub("", s)

    # Entferne Inline‑Events & javascript: URLs
    s = RE_ON_EVENT_ATTR.sub("", s)
    s = RE_JS_PROTOCOL.sub(r"\1#\2", s)

    if compress_ws:
        # Normiere Whitespace etwas, ohne HTML zu zerstören
        s = re.sub(r"[ \t]+\n", "\n", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        s = re.sub(r"[ \t]{2,}", " ", s)

    return s

def sanitize_sections_dict(sections: dict, truthy_env: Optional[bool] = True) -> dict:
    """Sanitisiert alle string‑Werte in einem Sections‑Dict."""
    if not isinstance(sections, dict):
        return sections  # type: ignore[unreachable]
    out = {}
    for k, v in sections.items():
        if isinstance(v, str):
            out[k] = sanitize_section_html(v, compress_ws=True)
        else:
            out[k] = v
    return out
