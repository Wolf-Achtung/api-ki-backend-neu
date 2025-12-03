# -*- coding: utf-8 -*-
"""
services.html_sanitizer
-----------------------
Kleiner, abhängigkeitsfreier Sanitizer für Abschnitts‑HTML.
Ziele:
- Entfernt komplette Dokument‑Wrapper (<html>, <head>, <body>, <!DOCTYPE>)
- Entfernt <script>, <iframe>, <object>, <embed>, <link>, <meta>
- Entfernt Inline‑Eventhandler (onClick, onload, …)
- Behebt UTF-8 Mojibake (Ã¶ → ö)
- Optional: komprimiert Whitespace
- Erhält valide Teil‑HTML (Listen, Tabellen, Divs, etc.) unverändert

Hinweis: bewusst konservativ, um Layout nicht zu zerstören.
"""
from __future__ import annotations
import re
import html
from typing import Optional

_TRUTHY = {"1","true","TRUE","yes","YES","on","y"}

def _fix_utf8_mojibake(text: str) -> str:
    """Behebt falsch encodierte UTF-8 Zeichen (Mojibake).

    Beispiele:
    - "FragebÃ¶gen" → "Fragebögen"
    - "MarktfÃ¼hrer" → "Marktführer"
    """
    if not text or not isinstance(text, str):
        return text
    if 'Ã' not in text and 'â' not in text:
        return text
    try:
        # Versuche als Latin-1 zu decodieren und als UTF-8 zu encoden
        return text.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
    except Exception:
        try:
            return html.unescape(text)
        except Exception:
            return text

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

# --- HTML Minification Patterns ---
# Empty tags that can be safely removed
RE_EMPTY_P = re.compile(r"<p[^>]*>\s*</p>", re.IGNORECASE)
RE_EMPTY_SPAN = re.compile(r"<span[^>]*>\s*</span>", re.IGNORECASE)
RE_EMPTY_DIV = re.compile(r"<div[^>]*>\s*</div>", re.IGNORECASE)
RE_EMPTY_LI = re.compile(r"<li[^>]*>\s*</li>", re.IGNORECASE)
RE_LONE_BR = re.compile(r"(?:<br\s*/?>){2,}", re.IGNORECASE)  # Multiple consecutive <br>

# Empty class attributes
RE_EMPTY_CLASS = re.compile(r'\s+class\s*=\s*["\'][\s]*["\']', re.IGNORECASE)

# Redundant whitespace in style attributes
RE_STYLE_WHITESPACE = re.compile(r'style\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)

def _cleanup_template_phrases(text: str) -> str:
    """Entfernt versehentlich eingebettete Template-Phrasen aus dem Output.

    Diese können von GPT trotz Anweisungen übernommen werden.
    """
    replacements = [
        ("Freitextfeld", "Textabschnitt"),
        ("Freitext-Feld", "Textabschnitt"),
        ("Freitext-Felder", "Textabschnitte"),
        ("freitextfeld", "Textabschnitt"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _minify_inline_style(match: re.Match) -> str:
    """Minifiziert ein style-Attribut (Whitespace entfernen)."""
    style_content = match.group(1)
    # Entferne überflüssige Whitespace
    style_content = re.sub(r"\s*:\s*", ":", style_content)
    style_content = re.sub(r"\s*;\s*", ";", style_content)
    style_content = style_content.strip().rstrip(";")
    if not style_content:
        return ""  # Leeres style-Attribut ganz entfernen
    return f'style="{style_content}"'


def minify_html(html_content: str) -> str:
    """
    Minifiziert HTML durch Entfernen leerer Tags und überflüssiger Attribute.

    - Entfernt leere <p>, <span>, <div>, <li> Tags
    - Reduziert mehrfache <br> auf einzelne
    - Entfernt leere class="" Attribute
    - Komprimiert Whitespace in style-Attributen
    - Entfernt Leerzeilen zwischen Tags

    Args:
        html_content: HTML-String

    Returns:
        Minifiziertes HTML
    """
    if not html_content:
        return ""

    s = html_content

    # Entferne leere Tags (mehrfach, da verschachtelt sein können)
    for _ in range(3):
        s = RE_EMPTY_P.sub("", s)
        s = RE_EMPTY_SPAN.sub("", s)
        s = RE_EMPTY_DIV.sub("", s)
        s = RE_EMPTY_LI.sub("", s)

    # Reduziere mehrfache <br> auf einzelne
    s = RE_LONE_BR.sub("<br>", s)

    # Entferne leere class-Attribute
    s = RE_EMPTY_CLASS.sub("", s)

    # Minifiziere style-Attribute
    s = RE_STYLE_WHITESPACE.sub(_minify_inline_style, s)

    # Entferne leere style-Attribute die übrig geblieben sind
    s = re.sub(r'\s+style\s*=\s*["\'][\s]*["\']', "", s, flags=re.IGNORECASE)

    # Entferne Leerzeilen zwischen Tags (aber behalte single newlines)
    s = re.sub(r">\s*\n\s*\n+\s*<", ">\n<", s)

    return s


def sanitize_section_html(
    html_content: Optional[str],
    compress_ws: bool = True,
    minify: bool = True
) -> str:
    """
    Sanitisiert und minifiziert HTML für Report-Sektionen.

    Args:
        html_content: HTML-String
        compress_ws: Whitespace normalisieren
        minify: HTML minifizieren (leere Tags, Attribute entfernen)

    Returns:
        Bereinigtes HTML
    """
    if not html_content:
        return ""
    s = html_content

    # ZUERST: Behebe UTF-8 Mojibake (Ã¶ → ö)
    s = _fix_utf8_mojibake(s)

    # Post-Processing: Entferne versehentliche Template-Phrasen
    s = _cleanup_template_phrases(s)

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

    # HTML minifizieren (leere Tags, Attribute entfernen)
    if minify:
        s = minify_html(s)

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
