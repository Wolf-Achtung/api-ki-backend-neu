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
- NEU: Markdown → HTML Konvertierung (render_markdown_safe)
- NEU: Broken HTML Recovery (recover_text_from_broken_html)

Hinweis: bewusst konservativ, um Layout nicht zu zerstören.
"""
from __future__ import annotations
import re
import html
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Versuche markdown-it-py oder mistune zu importieren
try:
    import mistune
    MISTUNE_AVAILABLE = True
except ImportError:
    MISTUNE_AVAILABLE = False
    log.debug("[HTML-SANITIZER] mistune not available, markdown rendering disabled")

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


# --- Markdown → HTML Konvertierung ---

def render_markdown_safe(md_text: str) -> str:
    """
    Konvertiert Markdown sicher zu HTML.

    - Erlaubte Tags: p, h2-h4, ul, ol, li, strong, em, br
    - Keine Raw-HTML Injection
    - Auto-Closing erzwungen
    - Deterministisches Output

    Args:
        md_text: Markdown-Text

    Returns:
        Sicheres HTML
    """
    if not md_text:
        return ""

    if MISTUNE_AVAILABLE:
        try:
            # Mistune 3.x mit sicheren Einstellungen
            renderer = mistune.create_markdown(
                escape=True,  # HTML escapen
                plugins=['strikethrough', 'table']
            )
            html_output = renderer(md_text)
            # Nachbearbeitung: Nur erlaubte Tags behalten
            return _filter_allowed_tags(html_output)
        except Exception as e:
            log.warning("[MD-RENDER] mistune failed: %s, using fallback", e)

    # Fallback: Einfache Regex-basierte Konvertierung
    return _markdown_fallback(md_text)


def _filter_allowed_tags(html_text: str) -> str:
    """Filtert HTML auf erlaubte Tags."""
    ALLOWED_TAGS = {
        'p', 'h2', 'h3', 'h4', 'ul', 'ol', 'li',
        'strong', 'em', 'b', 'i', 'br', 'section'
    }

    def tag_replacer(match):
        tag = match.group(1).lower().split()[0]  # Erstes Wort ist Tag-Name
        if tag.lstrip('/') in ALLOWED_TAGS:
            return match.group(0)
        return ''  # Tag entfernen

    # Entferne nicht-erlaubte Tags
    result = re.sub(r'<(/?\w+)[^>]*>', tag_replacer, html_text)
    return result


def _markdown_fallback(md_text: str) -> str:
    """
    Einfache Markdown → HTML Konvertierung ohne externe Abhängigkeiten.
    """
    lines = md_text.strip().split('\n')
    html_parts = []
    in_list = False
    list_type = None

    for line in lines:
        stripped = line.strip()

        # Überschriften
        if stripped.startswith('## '):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            html_parts.append(f'<h2>{html.escape(stripped[3:])}</h2>')
        elif stripped.startswith('### '):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            html_parts.append(f'<h3>{html.escape(stripped[4:])}</h3>')
        elif stripped.startswith('#### '):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            html_parts.append(f'<h4>{html.escape(stripped[5:])}</h4>')

        # Listen
        elif stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
                list_type = 'ul'
            content = _convert_inline_markdown(stripped[2:])
            html_parts.append(f'<li>{content}</li>')

        elif re.match(r'^\d+\.\s', stripped):
            if not in_list:
                html_parts.append('<ol>')
                in_list = True
                list_type = 'ol'
            content = _convert_inline_markdown(re.sub(r'^\d+\.\s', '', stripped))
            html_parts.append(f'<li>{content}</li>')

        # Leerzeile
        elif not stripped:
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False

        # Normaler Text
        else:
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            content = _convert_inline_markdown(stripped)
            html_parts.append(f'<p>{content}</p>')

    # Liste am Ende schließen
    if in_list:
        html_parts.append(f'</{list_type}>')

    return '\n'.join(html_parts)


def _convert_inline_markdown(text: str) -> str:
    """Konvertiert Inline-Markdown (bold, italic)."""
    # Escape HTML zuerst
    text = html.escape(text)
    # **bold** → <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # *italic* → <em>
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text


# --- HTML Recovery für kaputtes HTML ---

def recover_text_from_broken_html(html_text: str, min_words: int = 50) -> str:
    """
    Extrahiert Text aus potenziell kaputtem HTML.

    Priorität:
    1. Versuche HTML normal zu parsen
    2. Wenn Fehler → strip_tags()
    3. Mindest-Text behalten

    Args:
        html_text: Potenziell kaputtes HTML
        min_words: Mindestanzahl Wörter für Recovery

    Returns:
        Bereinigter Text oder ursprünglicher Inhalt als Fallback
    """
    if not html_text:
        return ""

    original_text = html_text.strip()

    # Schritt 1: Versuche normale Tag-Entfernung
    try:
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        clean_text = clean_text.strip()

        if clean_text:
            words = clean_text.split()
            if len(words) >= min_words:
                log.debug("[HTML-RECOVERY] Normal extraction: %d words", len(words))
                return clean_text
    except Exception as e:
        log.warning("[HTML-RECOVERY] Normal extraction failed: %s", e)

    # Schritt 2: Aggressivere Tag-Entfernung (auch kaputte Tags)
    try:
        # Entferne alles was wie ein Tag aussieht, auch unvollständige
        aggressive_clean = re.sub(r'<[^>]*>?', '', html_text)
        aggressive_clean = re.sub(r'<[^>]*$', '', aggressive_clean)  # Unvollständige Tags am Ende
        aggressive_clean = aggressive_clean.strip()

        if aggressive_clean:
            words = aggressive_clean.split()
            if len(words) >= min_words:
                log.debug("[HTML-RECOVERY] Aggressive extraction: %d words", len(words))
                return aggressive_clean
    except Exception as e:
        log.warning("[HTML-RECOVERY] Aggressive extraction failed: %s", e)

    # Schritt 3: Nur alphanumerische Zeichen behalten
    try:
        text_only = re.sub(r'[<>]', ' ', html_text)
        text_only = re.sub(r'\s+', ' ', text_only).strip()

        if text_only:
            words = text_only.split()
            if len(words) >= 10:  # Mindestens 10 Wörter
                log.debug("[HTML-RECOVERY] Text-only extraction: %d words", len(words))
                return text_only
    except Exception as e:
        log.warning("[HTML-RECOVERY] Text-only extraction failed: %s", e)

    # Letzter Fallback: Original zurückgeben
    log.warning("[HTML-RECOVERY] All extractions failed, returning original")
    return original_text


def sanitize_or_recover(html_content: str, min_words: int = 50) -> str:
    """
    Kombiniert Sanitization mit Recovery für kaputtes HTML.

    Args:
        html_content: HTML-String
        min_words: Mindestanzahl Wörter für erfolgreiche Verarbeitung

    Returns:
        Sanitisiertes HTML oder recovered Text
    """
    if not html_content:
        return ""

    # Zuerst normale Sanitization versuchen
    sanitized = sanitize_section_html(html_content)

    # Prüfe ob genug Text übrig ist
    text_only = re.sub(r'<[^>]+>', '', sanitized).strip()
    words = text_only.split()

    if len(words) >= min_words:
        return sanitized

    # Falls zu wenig: Recovery versuchen
    log.warning("[SANITIZE-RECOVER] Only %d words after sanitization, trying recovery", len(words))
    recovered = recover_text_from_broken_html(html_content, min_words)

    # Recovered Text als Paragraphen wrappen
    if recovered and not recovered.startswith('<'):
        # Teile in Absätze
        paragraphs = recovered.split('\n\n')
        if len(paragraphs) > 1:
            return '\n'.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
        return f'<p>{recovered}</p>'

    return recovered or sanitized


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
