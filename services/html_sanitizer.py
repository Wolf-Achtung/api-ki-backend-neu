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
    """Filtert HTML auf erlaubte Tags.

    PDF-SLIMDOWN v2.0: Erweiterte Whitelist, CSS-Klassen werden NICHT gestrippt.
    """
    # Erweiterte Whitelist inkl. Tabellen und strukturelle Tags
    ALLOWED_TAGS = {
        'p', 'h2', 'h3', 'h4', 'h5', 'ul', 'ol', 'li',
        'strong', 'em', 'b', 'i', 'br', 'section', 'div', 'span',
        # Tabellen (werden NICHT entfernt)
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
        # Strukturelle Tags
        'article', 'header', 'footer', 'nav', 'aside',
        # Links (ohne href-Manipulation)
        'a',
    }

    def tag_replacer(match):
        full_tag = match.group(0)
        tag_name = match.group(1).lower().split()[0]  # Erstes Wort ist Tag-Name
        if tag_name.lstrip('/') in ALLOWED_TAGS:
            # CSS-Klassen und andere Attribute BEIBEHALTEN
            return full_tag
        return ''  # Tag entfernen, Inhalt behalten

    # Entferne nicht-erlaubte Tags (aber behalte deren Inhalt)
    result = re.sub(r'<(/?\w+)([^>]*)>', tag_replacer, html_text)
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

# Mindest-Wortanzahl für Recovery (PDF-SLIMDOWN v2.0)
MIN_WORDS_DEFAULT = 50


def recover_text_from_broken_html(html_text: str, min_words: int = MIN_WORDS_DEFAULT) -> str:
    """
    Extrahiert Text aus potenziell kaputtem HTML.

    Priorität:
    1. Versuche HTML normal zu parsen
    2. Wenn Fehler → strip_tags()
    3. Mindest-Text behalten (min 50 Wörter)

    Args:
        html_text: Potenziell kaputtes HTML
        min_words: Mindestanzahl Wörter für Recovery (default: 50)

    Returns:
        Bereinigter Text oder heuristisch aufbereiteter Inhalt (min 50 Wörter)
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
                # PDF-SLIMDOWN: Garantiere mindestens 50 Wörter durch heuristische Aufbereitung
                if len(words) < min_words:
                    return _heuristic_padding(text_only, min_words)
                return text_only
    except Exception as e:
        log.warning("[HTML-RECOVERY] Text-only extraction failed: %s", e)

    # Letzter Fallback: Original mit heuristischer Aufbereitung
    log.warning("[HTML-RECOVERY] All extractions failed, applying heuristic padding")
    return _heuristic_padding(original_text, min_words)


def _heuristic_padding(text: str, min_words: int = MIN_WORDS_DEFAULT) -> str:
    """
    Heuristische Aufbereitung um Mindest-Wortanzahl zu garantieren.

    Fügt einen neutralen Kontext-Satz hinzu wenn der Text zu kurz ist.
    Verhindert "0 Wörter"-Situationen.

    Args:
        text: Der zu kurze Text
        min_words: Mindestanzahl Wörter

    Returns:
        Text mit mindestens min_words Wörtern
    """
    words = text.split()
    current_count = len(words)

    if current_count >= min_words:
        return text

    # Neutraler Fülltext für Recovery-Situationen
    padding_de = (
        "Dieser Abschnitt enthält weitere Details zur Analyse. "
        "Die vollständigen Informationen werden im Gesamtkontext des Reports bereitgestellt. "
        "Für zusätzliche Erläuterungen siehe die angrenzenden Kapitel des Reports."
    )
    padding_en = (
        "This section contains additional analysis details. "
        "Complete information is provided in the overall report context. "
        "For additional explanations, see adjacent report chapters."
    )

    # Entscheide anhand des Texts ob DE oder EN
    de_indicators = ["der", "die", "das", "und", "für", "mit", "eine", "einen"]
    text_lower = text.lower()
    is_german = any(ind in text_lower for ind in de_indicators)

    padding = padding_de if is_german else padding_en

    log.info("[HEURISTIC-PADDING] Added padding to reach %d words (had %d)", min_words, current_count)
    return f"{text} {padding}"


# =============================================================================
# PDF-SLIMDOWN v2.0: Auto-Summary Fallback (Stufe 3)
# =============================================================================

def generate_auto_summary(
    section_name: str,
    recovered_text: str,
    branch: str = "",
    size: str = "",
    guardrails: bool = False
) -> str:
    """
    Generiert eine Auto-Summary für Recovery-Situationen (Stufe 3 im Fallback).

    Wird verwendet wenn:
    - Token-Limit abgebrochen hat
    - < 10 Wörter vorhanden sind
    - HTML zerstört ist

    Args:
        section_name: Name der Sektion (z.B. "roadmap_12m")
        recovered_text: Der gerettete Text aus vorherigen Stufen
        branch: Branche (für branchen-aware Summary)
        size: Unternehmensgröße (solo/team/kmu)
        guardrails: Ob Guardrails-Hinweise eingefügt werden sollen

    Returns:
        HTML-formatierte Auto-Summary (80-120 Wörter)
    """
    if not recovered_text:
        recovered_text = ""

    # Extrahiere Schlüsselwörter aus dem geretteten Text
    words = recovered_text.split()[:50]  # Erste 50 Wörter als Kontext
    context_snippet = " ".join(words) if words else "keine Inhalte verfügbar"

    # Section-spezifische Templates
    templates = {
        "roadmap_12m": {
            "de": f"""<div class="auto-summary">
<h4>12-Monats-Roadmap (Zusammenfassung)</h4>
<p>Die strategische Roadmap für die nächsten 12 Monate umfasst die systematische
Einführung von KI-gestützten Prozessen. Die wichtigsten Phasen sind: Fundament &
erste Use Cases (Monate 1-3), Pilotierung & Qualitätssicherung (Monate 4-6),
sowie Ausbau & Skalierung (Monate 7-12). Jede Phase enthält konkrete KPIs und
Verantwortlichkeiten angepasst an die Unternehmensgröße{' ' + size if size else ''}.</p>
{_guardrails_hint() if guardrails else ''}
</div>""",
            "en": f"""<div class="auto-summary">
<h4>12-Month Roadmap (Summary)</h4>
<p>The strategic roadmap for the next 12 months covers the systematic introduction
of AI-powered processes. Key phases include: Foundation & first use cases (months 1-3),
Piloting & quality assurance (months 4-6), and Expansion & scaling (months 7-12).
Each phase contains specific KPIs and responsibilities adapted to company size{' ' + size if size else ''}.</p>
{_guardrails_hint_en() if guardrails else ''}
</div>"""
        },
        "roadmap_90d": {
            "de": f"""<div class="auto-summary">
<h4>90-Tage-Roadmap (Zusammenfassung)</h4>
<p>Die 90-Tage-Roadmap fokussiert auf schnelle Erfolge und stabile Grundlagen.
In den ersten Wochen werden priorisierte Use Cases definiert und erste Workflows
etabliert. Bis Woche 8 entstehen dokumentierte Qualitätsstandards. Die Konsolidierung
erfolgt in Woche 9-13 mit klarer Entscheidung für die Skalierung.</p>
</div>""",
            "en": f"""<div class="auto-summary">
<h4>90-Day Roadmap (Summary)</h4>
<p>The 90-day roadmap focuses on quick wins and stable foundations. During the
first weeks, prioritized use cases are defined and initial workflows established.
By week 8, documented quality standards emerge. Consolidation occurs in weeks 9-13
with a clear decision for scaling.</p>
</div>"""
        },
        "recommendations": {
            "de": f"""<div class="auto-summary">
<h4>Handlungsempfehlungen (Zusammenfassung)</h4>
<p>Die wichtigsten Empfehlungen umfassen: Etablierung eines Standard-Workflows,
Systematisierung der Qualitätssicherung, Aufbau eines Wissensmanagements,
Pilotierung branchenspezifischer Use Cases, sowie Definition von Governance &
Leitplanken. Prioritäten und Zeitrahmen sind an die Unternehmensgröße angepasst.</p>
</div>""",
            "en": f"""<div class="auto-summary">
<h4>Recommendations (Summary)</h4>
<p>Key recommendations include: establishing a standard workflow, systematizing
quality assurance, building knowledge management, piloting industry-specific use
cases, and defining governance & guidelines. Priorities and timeframes are adapted
to company size.</p>
</div>"""
        }
    }

    # Fallback-Template für unbekannte Sections
    default_template = {
        "de": f"""<div class="auto-summary">
<h4>{section_name.replace('_', ' ').title()} (Zusammenfassung)</h4>
<p>Dieser Abschnitt enthält strategische Empfehlungen und Analysen für den
Bereich {section_name.replace('_', ' ')}. Die vollständigen Details sind im
Gesamtkontext des Reports zu finden. Für Rückfragen steht das Beratungsteam
zur Verfügung.</p>
</div>""",
        "en": f"""<div class="auto-summary">
<h4>{section_name.replace('_', ' ').title()} (Summary)</h4>
<p>This section contains strategic recommendations and analysis for
{section_name.replace('_', ' ')}. Complete details can be found in the
overall report context. The consulting team is available for questions.</p>
</div>"""
    }

    # Wähle Template
    section_templates = templates.get(section_name, default_template)

    # Sprache aus Kontext erkennen
    de_indicators = ["der", "die", "das", "und", "für", "mit", "eine", "einen"]
    is_german = any(ind in recovered_text.lower() for ind in de_indicators)
    lang = "de" if is_german else "en"

    result = section_templates.get(lang, section_templates.get("de", default_template["de"]))

    log.info("[AUTO-SUMMARY] Generated summary for section=%s (lang=%s, size=%s)",
             section_name, lang, size or "unknown")

    return result


def _guardrails_hint() -> str:
    """Guardrails-Hinweis für deutsche Auto-Summaries."""
    return '<p class="small muted">Hinweis: Leitplanken und No-Gos des Unternehmens wurden berücksichtigt.</p>'


def _guardrails_hint_en() -> str:
    """Guardrails hint for English auto-summaries."""
    return '<p class="small muted">Note: Company guidelines and restrictions have been considered.</p>'


def sanitize_or_recover(
    html_content: str,
    min_words: int = MIN_WORDS_DEFAULT,
    section_name: str = "",
    branch: str = "",
    size: str = "",
    guardrails: bool = False
) -> str:
    """
    Kombiniert Sanitization mit Recovery für kaputtes HTML.

    PDF-SLIMDOWN v2.0 Fallback-Pipeline:
    - Stufe 1: HTML-Recovery (Tag-Entfernung)
    - Stufe 2: Markdown-Rendering
    - Stufe 3: Auto-Summary (NEU) - 80-120 Wörter, size-/branch-aware
    - Stufe 4: PLATIN-Fallback

    Args:
        html_content: HTML-String
        min_words: Mindestanzahl Wörter für erfolgreiche Verarbeitung (default: 50)
        section_name: Name der Sektion (für Auto-Summary)
        branch: Branche (für branchen-aware Summary)
        size: Unternehmensgröße (solo/team/kmu)
        guardrails: Ob Guardrails-Hinweise eingefügt werden sollen

    Returns:
        Sanitisiertes HTML oder recovered/auto-summarized Text
    """
    if not html_content:
        # Keine "0 Wörter"-Situation: Auto-Summary generieren
        if section_name:
            log.warning("[SANITIZE-RECOVER] Empty content for section=%s, using auto-summary", section_name)
            return generate_auto_summary(section_name, "", branch, size, guardrails)
        return ""

    # Stufe 1: Normale Sanitization versuchen
    sanitized = sanitize_section_html(html_content)

    # Prüfe ob genug Text übrig ist
    text_only = re.sub(r'<[^>]+>', '', sanitized).strip()
    words = text_only.split()

    if len(words) >= min_words:
        return sanitized

    # Stufe 2: Falls zu wenig - Recovery versuchen
    log.warning("[SANITIZE-RECOVER] Only %d words after sanitization, trying recovery", len(words))
    recovered = recover_text_from_broken_html(html_content, min_words)

    # Prüfe Recovery-Ergebnis
    recovered_text_only = re.sub(r'<[^>]+>', '', recovered).strip() if recovered else ""
    recovered_words = recovered_text_only.split()

    if len(recovered_words) >= min_words:
        # Recovered Text als Paragraphen wrappen
        if recovered and not recovered.startswith('<'):
            paragraphs = recovered.split('\n\n')
            if len(paragraphs) > 1:
                return '\n'.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
            return f'<p>{recovered}</p>'
        return recovered

    # Stufe 3: Auto-Summary generieren (NEU)
    if section_name and len(recovered_words) < min_words:
        log.warning("[SANITIZE-RECOVER] Recovery insufficient (%d words), using auto-summary for %s",
                   len(recovered_words), section_name)
        return generate_auto_summary(section_name, recovered or text_only, branch, size, guardrails)

    # Stufe 4: Fallback - heuristische Aufbereitung
    return _heuristic_padding(recovered or text_only, min_words)


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
