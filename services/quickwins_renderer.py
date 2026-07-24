# -*- coding: utf-8 -*-
"""
P0.7: Quick Wins Renderer - Canonical Value Calculation

This module provides utilities for rendering Quick Wins with correctly
calculated € values based on the canonical hourly rate.

Key features:
- € values calculated from hours * canonical_rate
- Removal of "Icon:" text artifacts
- German number formatting
"""

import os
import re
import logging
from typing import Tuple, Optional

log = logging.getLogger(__name__)

# TASK 1 (P0 FINAL): Import debug pipeline
try:
    from services.quickwins_debug import (
        dump_raw_json,
        dump_renderer_output,
        is_debug_enabled,
    )
except ImportError:
    # Fallback if debug module not available - signatures must match originals for mypy
    from typing import Any as _Any, Optional as _Opt
    def dump_raw_json(raw_data: _Any, context: str = "unknown") -> _Opt[str]: return None
    def dump_renderer_output(html: str, renderer_name: str = "unknown") -> _Opt[str]: return None
    def is_debug_enabled() -> bool: return False


# =============================================================================
# P0.7: Quick Wins € Calculation Helper
# =============================================================================

def calculate_quickwin_savings_display(raw_zeitersparnis: str, canonical_rate: int) -> str:
    """
    P0.7: Calculate Quick Win savings display from hours using canonical rate.

    Parses hours from zeitersparnis text and calculates € values:
    - eur_low = hours_low * canonical_rate
    - eur_high = hours_high * canonical_rate

    Args:
        raw_zeitersparnis: Raw zeitersparnis text (e.g., "10-15 h/Monat = 800-1.200 €")
        canonical_rate: Canonical hourly rate in EUR

    Returns:
        Formatted string like "10-15 h/Monat = 800–1.200 €"
    """
    import html as html_module

    if not raw_zeitersparnis:
        return "Zeitersparnis: auf Anfrage"

    # Try to extract hours range from the text
    # Pattern: "10-15 h" or "10 bis 15 h" or "10–15h" etc.
    hours_pattern = re.compile(
        r'(\d+(?:[.,]\d+)?)\s*[-–bis]+\s*(\d+(?:[.,]\d+)?)\s*(?:h|std|stunden?)',
        re.IGNORECASE
    )
    single_hours_pattern = re.compile(
        r'(\d+(?:[.,]\d+)?)\s*(?:h|std|stunden?)\s*(?:/\s*(?:monat|mon|m))?',
        re.IGNORECASE
    )

    hours_low = None
    hours_high = None

    # Try range pattern first
    match = hours_pattern.search(raw_zeitersparnis)
    if match:
        hours_low = float(match.group(1).replace(',', '.'))
        hours_high = float(match.group(2).replace(',', '.'))
    else:
        # Try single value pattern
        single_match = single_hours_pattern.search(raw_zeitersparnis)
        if single_match:
            hours_val = float(single_match.group(1).replace(',', '.'))
            # Create a range around single value
            hours_low = hours_val * 0.8
            hours_high = hours_val * 1.2

    # Calculate € values
    if hours_low is not None and hours_high is not None:
        eur_low = int(hours_low * canonical_rate)
        eur_high = int(hours_high * canonical_rate)

        # Format with German number formatting
        eur_low_fmt = f"{eur_low:,}".replace(",", ".")
        eur_high_fmt = f"{eur_high:,}".replace(",", ".")

        return f"{int(hours_low)}–{int(hours_high)} h/Monat = {eur_low_fmt}–{eur_high_fmt} €"

    # Fallback: clean and return original, removing any conflicting € values
    # P0.7: Strip existing € values from LLM text to avoid inconsistency
    cleaned = re.sub(r'=?\s*[\d.,]+\s*[-–]\s*[\d.,]+\s*€', '', raw_zeitersparnis)
    cleaned = re.sub(r'=?\s*[\d.,]+\s*€', '', cleaned)
    cleaned = cleaned.strip().rstrip('=').strip()

    return html_module.escape(cleaned) if cleaned else "Zeitersparnis: auf Anfrage"


def clean_icon_artifact(raw_icon: str) -> str:
    """
    P0.7: Remove 'Icon:' text artifact from icon field.

    Args:
        raw_icon: Raw icon string (e.g., "Icon: 🚀")

    Returns:
        Cleaned icon (e.g., "🚀")
    """
    if not raw_icon:
        return "◎"

    # Remove "Icon:" prefix (case insensitive)
    cleaned = re.sub(r'^Icon:\s*', '', str(raw_icon), flags=re.IGNORECASE).strip()
    return cleaned or "◎"


def parse_hours_from_zeitersparnis(raw_text: str) -> Tuple[Optional[float], Optional[float]]:
    """
    P0.7: Parse hours range from zeitersparnis text.

    Args:
        raw_text: Raw zeitersparnis text

    Returns:
        Tuple of (hours_low, hours_high) or (None, None) if not found
    """
    if not raw_text:
        return None, None

    # Try range pattern first
    hours_pattern = re.compile(
        r'(\d+(?:[.,]\d+)?)\s*[-–bis]+\s*(\d+(?:[.,]\d+)?)\s*(?:h|std|stunden?)',
        re.IGNORECASE
    )

    match = hours_pattern.search(raw_text)
    if match:
        hours_low = float(match.group(1).replace(',', '.'))
        hours_high = float(match.group(2).replace(',', '.'))
        return hours_low, hours_high

    # Try single value pattern
    single_hours_pattern = re.compile(
        r'(\d+(?:[.,]\d+)?)\s*(?:h|std|stunden?)\s*(?:/\s*(?:monat|mon|m))?',
        re.IGNORECASE
    )

    single_match = single_hours_pattern.search(raw_text)
    if single_match:
        hours_val = float(single_match.group(1).replace(',', '.'))
        return hours_val * 0.8, hours_val * 1.2

    return None, None


def format_eur_range(eur_low: float, eur_high: float) -> str:
    """
    P0.7: Format EUR range with German number formatting.

    Args:
        eur_low: Lower bound in EUR
        eur_high: Upper bound in EUR

    Returns:
        Formatted string like "800–1.200 €"
    """
    eur_low_fmt = f"{int(eur_low):,}".replace(",", ".")
    eur_high_fmt = f"{int(eur_high):,}".replace(",", ".")
    return f"{eur_low_fmt}–{eur_high_fmt} €"


# =============================================================================
# FIX-504 TASK 4: QuickWins LEFT_ONLY Full-Width Layout Enhancement
# =============================================================================
# When template_mode=LEFT_ONLY, enhance the layout to use full page width
# with a 2-column card grid for better visual presentation.

QUICKWINS_FULLWIDTH_CSS = """
<style>
/* FIX-517C: QuickWins full-width premium layout (WeasyPrint-safe, no CSS Grid) */
.quickwins-fullwidth-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 16px;
    table-layout: fixed;
}
.quickwins-fullwidth-table td {
    vertical-align: top;
    width: 50%;
    padding: 0;
}
.quickwins-fullwidth-table .quick-win-card,
.quickwins-fullwidth-table .quick-win-card-new {
    break-inside: avoid;
    page-break-inside: avoid;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
</style>
"""


def detect_quickwins_template_mode(sections: dict) -> str:
    """
    FIX-504: Detect QuickWins template mode based on section content.

    Returns:
        "LEFT_RIGHT" if both columns have content
        "LEFT_ONLY" if only left column has content
        "FULL" if only QUICK_WINS_HTML has content
        "NONE" if no QuickWins content
    """
    right_len = len(str(sections.get("QUICK_WINS_HTML_RIGHT", "") or ""))
    left_len = len(str(sections.get("QUICK_WINS_HTML_LEFT", "") or ""))
    full_len = len(str(sections.get("QUICK_WINS_HTML", "") or ""))

    if right_len > 0:
        return "LEFT_RIGHT"
    elif left_len > 0:
        return "LEFT_ONLY"
    elif full_len > 0:
        return "FULL"
    else:
        return "NONE"


def count_quickwin_cards(html: str) -> int:
    """
    FIX-504: Count the number of QuickWin cards in HTML.

    Counts elements with class="quick-win-card" or similar.

    Args:
        html: QuickWins HTML content

    Returns:
        Number of QuickWin cards found
    """
    if not html:
        return 0

    # Count by card class patterns
    card_patterns = [
        r'class="quick-win-card"',
        r'class="quick-win-card-new"',
        r'class="[^"]*quick-win[^"]*"',
        r'<div[^>]*data-quickwin',
    ]

    total = 0
    for pattern in card_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            total = max(total, len(matches))

    # Fallback: count by heading patterns if no cards found
    if total == 0:
        h3_matches = re.findall(r'<h3[^>]*>.*?</h3>', html, re.DOTALL | re.IGNORECASE)
        total = len(h3_matches)

    return total


def enhance_quickwins_for_fullwidth(html: str, min_cards: int = 4) -> str:
    """
    FIX-504 TASK 4: Enhance QuickWins HTML for full-width premium layout.

    When in LEFT_ONLY mode (right column empty), this wraps the QuickWins
    content in a 2-column grid layout for better visual presentation.

    Args:
        html: Original QuickWins HTML
        min_cards: Minimum expected cards (logs warning if fewer)

    Returns:
        Enhanced HTML with full-width premium layout
    """
    if not html or not html.strip():
        return html

    card_count = count_quickwin_cards(html)
    log.info(f"[QUICKWINS-FULLWIDTH] Found {card_count} QuickWin cards")

    if card_count < min_cards:
        log.warning(
            f"[QUICKWINS-FULLWIDTH] Only {card_count} QuickWins found, "
            f"expected at least {min_cards} for premium layout"
        )

    # FIX-517C: Check if already wrapped in a table container
    if 'quickwins-fullwidth-table' in html:
        log.debug("[QUICKWINS-FULLWIDTH] Already enhanced, skipping")
        return html

    # FIX-517C: Use table layout for WeasyPrint compatibility
    enhanced = QUICKWINS_FULLWIDTH_CSS

    # Extract individual card elements for 2-column distribution
    # Split by card opening tags, then reconstruct each card block
    card_split_pattern = re.compile(
        r'(?=<div[^>]*class="[^"]*quick-win(?:-card|-card-new)\b)',
        re.IGNORECASE
    )
    cards = [c for c in card_split_pattern.split(html) if c.strip() and 'quick-win' in c.lower()]

    if len(cards) >= 2:
        mid = (len(cards) + 1) // 2
        left_col = "\n".join(cards[:mid])
        right_col = "\n".join(cards[mid:])
        enhanced += f'''<table class="quickwins-fullwidth-table" style="width:100%;border-collapse:separate;border-spacing:16px;table-layout:fixed;">
<tr>
<td style="vertical-align:top;width:50%;">{left_col}</td>
<td style="vertical-align:top;width:50%;">{right_col}</td>
</tr>
</table>'''
    else:
        # Not enough cards for 2-column, use single column
        enhanced += html

    log.info("[QUICKWINS-FULLWIDTH] Enhanced QuickWins for full-width table layout")
    return enhanced


# =============================================================================
# FIX-506 TASK 3: QuickWins Premium Enrichment
# =============================================================================
# Enrich Quick Wins with deterministic sublines (Nutzen + Start/Aufwand)
# derived from title/icon to meet minimum word count requirements.

# Deterministic sublines by Quick Win category (based on icon/title keywords)
QUICKWIN_ENRICHMENT_MAP = {
    # Automation & Efficiency
    "automatisierung": {
        "nutzen": "Reduziert manuelle Arbeit und minimiert Fehlerquellen",
        "aufwand": "Startaufwand gering, erste Ergebnisse in 1-2 Wochen",
    },
    "effizienz": {
        "nutzen": "Steigert Durchsatz bei gleichbleibenden Ressourcen",
        "aufwand": "Umsetzung in bestehende Prozesse integrierbar",
    },
    "prozess": {
        "nutzen": "Verbessert Durchlaufzeiten und Prozessqualität",
        "aufwand": "Schrittweise Einführung empfohlen",
    },
    # Communication & Content
    "kommunikation": {
        "nutzen": "Erhöht Konsistenz und Qualität der Kommunikation",
        "aufwand": "Templates und Vorlagen in 1 Woche einsatzbereit",
    },
    "content": {
        "nutzen": "Beschleunigt Content-Erstellung bei gleichbleibender Qualität",
        "aufwand": "KI-Unterstützung ab Tag 1 nutzbar",
    },
    "text": {
        "nutzen": "Professionelle Texte in kürzerer Zeit",
        "aufwand": "Minimale Einarbeitung erforderlich",
    },
    # Data & Analysis
    "daten": {
        "nutzen": "Bessere Entscheidungsgrundlagen durch schnellere Auswertung",
        "aufwand": "Anbindung an bestehende Datenquellen notwendig",
    },
    "analyse": {
        "nutzen": "Tiefere Insights bei geringerem Zeitaufwand",
        "aufwand": "Erste Analysen in wenigen Stunden möglich",
    },
    "report": {
        "nutzen": "Automatisierte Berichtserstellung spart wöchentlich Zeit",
        "aufwand": "Template-basiert, einmalige Einrichtung",
    },
    # Customer & Service
    "kund": {
        "nutzen": "Schnellere Reaktionszeiten und höhere Kundenzufriedenheit",
        "aufwand": "Integration in CRM oder Helpdesk empfohlen",
    },
    "service": {
        "nutzen": "Verbessert First-Response-Zeit und Servicequalität",
        "aufwand": "Pilotierung mit häufigen Anfragen starten",
    },
    "support": {
        "nutzen": "Entlastet Support-Team bei Standardanfragen",
        "aufwand": "FAQ-basierte Konfiguration in 2-3 Tagen",
    },
    # Default for unmatched
    "default": {
        "nutzen": "Messbare Zeitersparnis und Qualitätsverbesserung",
        "aufwand": "Schnelle Umsetzung mit geringem Initialaufwand möglich",
    },
}


def get_quickwin_enrichment(title: str, icon: str = "") -> dict:
    """
    FIX-506: Get deterministic enrichment sublines for a Quick Win.

    Args:
        title: Quick Win title
        icon: Quick Win icon (optional)

    Returns:
        Dict with 'nutzen' and 'aufwand' sublines
    """
    combined = f"{title} {icon}".lower()

    for keyword, enrichment in QUICKWIN_ENRICHMENT_MAP.items():
        if keyword != "default" and keyword in combined:
            return enrichment

    return QUICKWIN_ENRICHMENT_MAP["default"]


# =============================================================================
# TASK 1 (P0 FINAL): Robust Quick Win Field Mapping
# =============================================================================
# Maps various field name variants to canonical names: problem, wirkung, umsetzung
# This ensures we capture data regardless of how the LLM named the fields.

QUICKWIN_FIELD_ALIASES = {
    "problem": [
        "problem", "Problem", "PROBLEM",
        "pain", "Pain", "pain_point", "painpoint", "pain-point",
        "problemstellung", "Problemstellung",
        "ausgangslage", "Ausgangslage",
        "herausforderung", "Herausforderung",
        "issue", "Issue",
        "challenge", "Challenge",
        "current_state", "ist_zustand", "ist-zustand",
        # KIS-1250: Der Prompt-JSON-Vertrag (DE wie EN) heißt das Feld
        # "description" — ohne diesen Alias griff IMMER der Fallback-Text
        # (Lauf 1131: deutsche Fallbacks im EN-Report).
        "description", "Description", "beschreibung", "Beschreibung",
    ],
    "wirkung": [
        "wirkung", "Wirkung", "WIRKUNG",
        "benefit", "Benefit", "benefits",
        "impact", "Impact",
        "nutzen", "Nutzen",
        "effekt", "Effekt",
        "ergebnis", "Ergebnis",
        "outcome", "Outcome",
        "value", "Value", "mehrwert", "Mehrwert",
        "effect", "Effect",
        # KIS-1250: Prompt-JSON-Vertrag nennt das Feld "mit_ki"
        "mit_ki", "mit_KI", "Mit_KI", "with_ai", "with_AI", "solution", "Solution",
    ],
    "umsetzung": [
        "umsetzung", "Umsetzung", "UMSETZUNG",
        "how", "How",
        "implementation", "Implementation",
        "vorgehen", "Vorgehen",
        "next_steps", "next-steps", "nextSteps",
        "action", "Action", "actions", "Actions",
        "steps", "Steps", "schritte", "Schritte",
        "todo", "Todo", "TODO",
        "approach", "Approach",
        "howto", "how_to", "how-to",
    ],
}

# Values that count as "empty" (should trigger fallback)
EMPTY_VALUE_PATTERNS = ["", "—", "–", "-", "...", "…", "n/a", "N/A", "none", "None", "TBD", "tbd"]


def get_quickwin_field(qw: dict, canonical_field: str) -> str:
    """
    TASK 1 (P0 FINAL): Get Quick Win field value with robust alias mapping.

    Searches for the field using multiple possible key names and returns
    the first non-empty value found. Treats whitespace-only, dashes, and
    placeholder strings as empty.

    Args:
        qw: Quick Win dict with potentially varied field names
        canonical_field: Target field name (problem, wirkung, umsetzung)

    Returns:
        Field value (stripped) or empty string if not found/empty
    """
    if canonical_field not in QUICKWIN_FIELD_ALIASES:
        return str(qw.get(canonical_field, "")).strip()

    aliases = QUICKWIN_FIELD_ALIASES[canonical_field]

    for alias in aliases:
        value = qw.get(alias)
        if value is not None:
            value_str = str(value).strip()
            # Check if value is "empty" by our definition
            if value_str and value_str not in EMPTY_VALUE_PATTERNS:
                return value_str

    return ""


def normalize_quickwin_fields(qw: dict) -> dict:
    """
    TASK 1 (P0 FINAL): Normalize Quick Win field names to canonical names.

    Takes a Quick Win dict with potentially varied field names and returns
    a new dict with canonical field names (problem, wirkung, umsetzung).

    Args:
        qw: Quick Win dict with varied field names

    Returns:
        New dict with canonical field names and original values preserved
    """
    normalized = dict(qw)  # Copy original

    # Map aliases to canonical names
    for canonical_field in ["problem", "wirkung", "umsetzung"]:
        value = get_quickwin_field(qw, canonical_field)
        normalized[canonical_field] = value

    return normalized


def debug_quickwin_fields(qw: dict, index: int) -> None:
    """
    TASK 1 (P0 FINAL): Debug logging for Quick Win field mapping.

    Logs which fields exist in the Quick Win and their values.
    Helps diagnose why fields might be empty.
    """
    log.info("[QW-DEBUG] Quick Win #%d fields:", index + 1)
    log.info("[QW-DEBUG]   title=%r", qw.get("title", ""))

    for canonical_field in ["problem", "wirkung", "umsetzung"]:
        # Log all matching aliases found
        aliases_found = []
        for alias in QUICKWIN_FIELD_ALIASES.get(canonical_field, []):
            if alias in qw:
                aliases_found.append(f"{alias}={qw[alias]!r:.50}")

        resolved = get_quickwin_field(qw, canonical_field)
        log.info(
            "[QW-DEBUG]   %s: resolved=%r, aliases_found=%s",
            canonical_field, resolved[:50] if resolved else "(empty)", aliases_found or "(none)"
        )


# =============================================================================
# TASK B (P0): Quick Wins Completeness Gate
# =============================================================================
# Ensures all Quick Wins have non-empty problem/wirkung/umsetzung fields.
# Uses deterministic heuristics to fill missing fields from available context.

# Default fallback texts for empty fields based on title keywords
QUICKWIN_FIELD_FALLBACKS = {
    "problem": {
        "automatisierung": "Manuelle Prozesse binden Zeit und erhöhen Fehlerquoten.",
        "effizienz": "Ineffiziente Abläufe verursachen vermeidbare Kosten.",
        "kommunikation": "Inkonsistente Kommunikation mindert Professionalität.",
        "content": "Content-Erstellung ist zeitintensiv und ressourcenbindend.",
        "daten": "Datensilos verhindern fundierte Entscheidungen.",
        "kund": "Langsame Reaktionszeiten beeinträchtigen Kundenzufriedenheit.",
        "service": "Support-Anfragen überlasten das Team.",
        "default": "Aktueller Prozess ist zeitintensiv und fehleranfällig.",
    },
    "wirkung": {
        "automatisierung": "Automatisierte Abläufe reduzieren Zeitaufwand um 50-70%.",
        "effizienz": "Effizientere Prozesse steigern Durchsatz messbar.",
        "kommunikation": "Konsistente, professionelle Kommunikation stärkt Markenwahrnehmung.",
        "content": "Schnellere Content-Erstellung bei gleichbleibender Qualität.",
        "daten": "Bessere Datenverfügbarkeit ermöglicht schnellere Entscheidungen.",
        "kund": "Kürzere Reaktionszeiten erhöhen Kundenbindung.",
        "service": "Entlastung des Support-Teams bei Routineanfragen.",
        "default": "Spürbare Zeit- und Kostenersparnis bei höherer Qualität.",
    },
    "umsetzung": {
        "automatisierung": "Schrittweise Automatisierung der häufigsten Abläufe starten.",
        "effizienz": "Pilotprojekt mit höchstem Optimierungspotenzial beginnen.",
        "kommunikation": "Templates und Vorlagen für häufige Kommunikationsfälle erstellen.",
        "content": "KI-Unterstützung für Content-Workflows einrichten.",
        "daten": "Datenquellen verknüpfen und Dashboard aufsetzen.",
        "kund": "Chatbot oder Selbstservice-Portal für Standardanfragen implementieren.",
        "service": "FAQ-basierte Automatisierung für häufige Fragen einführen.",
        "default": "Pilotprojekt mit kleinem Scope starten, dann skalieren.",
    },
}

# KIS-1250: EN counterparts — a German fallback sentence must never appear
# in an English report (run 1131 leaked "Aktueller Prozess ist zeitintensiv…").
QUICKWIN_FIELD_FALLBACKS_EN = {
    "problem": {
        "automat": "Manual processes tie up time and increase error rates.",
        "efficien": "Inefficient workflows cause avoidable costs.",
        "communicat": "Inconsistent communication undermines professionalism.",
        "content": "Content creation is time-consuming and resource-intensive.",
        "data": "Data silos prevent well-founded decisions.",
        "client": "Slow response times hurt client satisfaction.",
        "customer": "Slow response times hurt customer satisfaction.",
        "service": "Support requests overload the team.",
        "default": "The current process is time-consuming and error-prone.",
    },
    "wirkung": {
        "automat": "Automated workflows reduce time spent by 50-70%.",
        "efficien": "More efficient processes measurably increase throughput.",
        "communicat": "Consistent, professional communication strengthens brand perception.",
        "content": "Faster content creation at consistent quality.",
        "data": "Better data availability enables faster decisions.",
        "client": "Shorter response times increase client retention.",
        "customer": "Shorter response times increase customer retention.",
        "service": "Relieves the support team of routine requests.",
        "default": "Tangible time and cost savings at higher quality.",
    },
    "umsetzung": {
        "automat": "Start automating the most frequent workflows step by step.",
        "efficien": "Begin with the pilot project offering the highest optimisation potential.",
        "communicat": "Create templates for frequent communication cases.",
        "content": "Set up AI support for content workflows.",
        "data": "Connect data sources and set up a dashboard.",
        "client": "Implement a chatbot or self-service portal for standard requests.",
        "customer": "Implement a chatbot or self-service portal for standard requests.",
        "service": "Introduce FAQ-based automation for frequent questions.",
        "default": "Start a pilot project with a small scope, then scale.",
    },
}


def _get_field_fallback(field: str, title: str, hinweis: str = "", lang: str = "de") -> str:
    """
    Get deterministic fallback text for a missing Quick Win field.

    Args:
        field: Field name (problem, wirkung, umsetzung)
        title: Quick Win title for keyword matching
        hinweis: Optional hint text that might contain useful info

    Returns:
        Fallback text for the field
    """
    _table = (
        QUICKWIN_FIELD_FALLBACKS_EN
        if str(lang or "de").lower().startswith("en")
        else QUICKWIN_FIELD_FALLBACKS
    )
    if field not in _table:
        return ""

    field_fallbacks = _table[field]
    combined = f"{title} {hinweis}".lower()

    # Try to match a keyword
    for keyword, text in field_fallbacks.items():
        if keyword != "default" and keyword in combined:
            return text

    return field_fallbacks.get("default", "")


def enforce_quickwins_complete(quickwins: list, lang: str = "de") -> list:
    """
    TASK B (P0) + TASK 1 (P0 FINAL): Ensure all Quick Wins have complete fields.

    For each Quick Win:
    1. TASK 1: Use robust field mapping to find values under various key names
    2. Normalize fields to canonical names (problem, wirkung, umsetzung)
    3. If still empty, use deterministic heuristics to fill from title/hinweis
    4. Log completeness actions for debugging

    Args:
        quickwins: List of Quick Win dicts with potentially varied field names

    Returns:
        List of Quick Wins with all fields completed (non-empty)

    Example:
        >>> qw = [{"title": "Automatisierung", "pain": "Test", "wirkung": "", "umsetzung": ""}]
        >>> result = enforce_quickwins_complete(qw)
        >>> result[0]["problem"]  # "pain" mapped to "problem"
        'Test'
        >>> all(result[0][f] for f in ["problem", "wirkung", "umsetzung"])
        True
    """
    if not quickwins or not isinstance(quickwins, list):
        return quickwins

    completed = []
    completions_made = 0
    mappings_made = 0

    for i, qw in enumerate(quickwins):
        if not isinstance(qw, dict):
            completed.append(qw)
            continue

        # TASK 1: Debug log the raw fields
        debug_quickwin_fields(qw, i)

        # TASK 1: First normalize field names using robust mapping
        qw_copy = normalize_quickwin_fields(qw)

        title = str(qw_copy.get("title", "")).strip()
        hinweis = str(qw_copy.get("hinweis", "")).strip()

        # Check and fill each required field
        for field in ["problem", "wirkung", "umsetzung"]:
            # TASK 1: Use robust getter that checks multiple aliases
            current_value = get_quickwin_field(qw_copy, field)

            if current_value:
                # Value found via alias mapping
                if qw_copy.get(field) != current_value:
                    mappings_made += 1
                    log.debug(
                        "[QUICKWINS-COMPLETE] QW#%d '%s': mapped alias to %s=%r",
                        i + 1, title[:30], field, current_value[:50]
                    )
                qw_copy[field] = current_value
            else:
                # Field is truly empty - fill with deterministic fallback
                fallback = _get_field_fallback(field, title, hinweis, lang=lang)
                qw_copy[field] = fallback
                completions_made += 1
                log.info(
                    "[QUICKWINS-COMPLETE] QW#%d '%s': filled empty %s with fallback: %r",
                    i + 1, title[:30], field, fallback[:50] if fallback else "(no fallback)"
                )

        completed.append(qw_copy)

    log.info(
        "[QUICKWINS-COMPLETE] Processed %d Quick Wins: %d fields mapped, %d filled with fallbacks",
        len(quickwins), mappings_made, completions_made
    )

    return completed


def enrich_quickwin_card(html: str) -> str:
    """
    FIX-506: Enrich a single Quick Win card with Nutzen and Aufwand sublines.

    Adds deterministic sublines after the title for premium presentation.

    Args:
        html: Single Quick Win card HTML

    Returns:
        Enriched card HTML
    """
    if not html:
        return html

    # Check if already enriched
    if 'data-qw-enriched="true"' in html or 'qw-nutzen' in html:
        return html

    # Extract title from card
    title_match = re.search(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL | re.IGNORECASE)
    if not title_match:
        # Try other heading patterns
        title_match = re.search(r'class="quick-win-title[^"]*"[^>]*>(.*?)</(?:div|span|h\d)', html, re.DOTALL | re.IGNORECASE)

    title = title_match.group(1).strip() if title_match else ""
    title = re.sub(r'<[^>]+>', '', title)  # Strip HTML tags

    # Get enrichment
    enrichment = get_quickwin_enrichment(title)

    # Create enrichment HTML
    enrichment_html = f'''
<div class="qw-enrichment" data-qw-enriched="true" style="margin-top:8px;padding:8px 0;border-top:1px solid #e5e7eb;">
  <div class="qw-nutzen" style="font-size:11px;color:#059669;margin-bottom:4px;">
    <strong>Nutzen:</strong> {enrichment['nutzen']}
  </div>
  <div class="qw-aufwand" style="font-size:11px;color:#6b7280;">
    <strong>Start:</strong> {enrichment['aufwand']}
  </div>
</div>'''

    # Insert before closing card tag
    # Try to find card body ending
    body_close_patterns = [
        (r'(</div>\s*</div>\s*</div>)\s*$', rf'{enrichment_html}\1'),
        (r'(<div class="quick-win-body[^"]*"[^>]*>.*?)(</div>)', rf'\1{enrichment_html}\2'),
        (r'(</div>)\s*$', rf'{enrichment_html}\1'),
    ]

    for pattern, replacement in body_close_patterns:
        if re.search(pattern, html, re.DOTALL | re.IGNORECASE):
            html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL | re.IGNORECASE)
            break

    return html


def enrich_quickwins_premium(html: str) -> str:
    """
    FIX-506 TASK 3: Enrich all Quick Win cards with premium sublines.

    Adds Nutzen and Aufwand sublines to each Quick Win card to:
    1. Meet minimum word count requirements
    2. Provide premium visual presentation
    3. Give actionable context without LLM calls

    Args:
        html: Full Quick Wins HTML

    Returns:
        Enriched HTML with all cards having sublines
    """
    if not html:
        return html

    # Check if already enriched
    if 'data-qw-enriched="true"' in html:
        log.debug("[QUICKWINS-PREMIUM] Already enriched, skipping")
        return html

    # Find and enrich each card
    card_pattern = re.compile(
        r'(<div[^>]*class="[^"]*quick-win-card[^"]*"[^>]*>.*?</div>\s*</div>\s*</div>)',
        re.DOTALL | re.IGNORECASE
    )

    def enrich_match(match):
        return enrich_quickwin_card(match.group(0))

    enriched = card_pattern.sub(enrich_match, html)

    # Count enrichments
    enrichment_count = enriched.count('data-qw-enriched="true"')
    log.info(f"[QUICKWINS-PREMIUM] Enriched {enrichment_count} Quick Win cards")

    return enriched


# =============================================================================
# KIS-1272-R4-T2: Helpers für Premium-Karten — Labels, Listenwerte, Hinweis
# =============================================================================

# KIS-1272-R4-T2a: EN-Label-Map für die Feldboxen der Premium-Karten
# (Run 4 zeigte "WIRKUNG:" im EN-Report). DE bleibt byte-identisch.
QUICKWIN_CARD_LABELS = {
    "de": {"problem": "Problem:", "wirkung": "Wirkung:", "umsetzung": "Umsetzung:"},
    "en": {"problem": "Problem:", "wirkung": "Impact:", "umsetzung": "Implementation:"},
}

# KIS-1272-R4-T2b: String, der wie ein Python-Listen-Literal aussieht
# (beginnt mit [' oder ["). Solche Werte dürfen nie roh gerendert werden.
_QW_PY_LIST_LITERAL_RE = re.compile(r"^\[\s*['\"]")


def _qw_items_to_ul_html(items) -> str:
    """KIS-1272-R4-T2b: Listeneinträge als escaptes <ul><li> rendern."""
    import html as html_module
    lis = "".join(
        f"<li>{html_module.escape(str(it).strip())}</li>"
        for it in items
        if str(it or "").strip()
    )
    if not lis:
        return ""
    return f'<ul style="margin:4px 0 0 0;padding-left:18px;">{lis}</ul>'


def qw_field_value_to_html(value) -> str:
    """KIS-1272-R4-T2b: Quick-Win-Feldwert sicher als HTML rendern.

    - Liste/Tupel → <ul><li>…</li></ul>
    - String, der wie ein Python-Listen-Literal aussieht (['…', '…']) →
      defensiv per ast.literal_eval parsen und als <ul> joinen; bei
      Parse-Fehler Original (escaped) behalten.
    - Sonst: escapter String.

    Sprachneutral — ein rohes Listen-Literal darf auch in DE nie erscheinen.
    """
    import html as html_module
    if isinstance(value, (list, tuple)):
        html_list = _qw_items_to_ul_html(value)
        return html_list if html_list else ""
    text = str(value or "").strip()
    if _QW_PY_LIST_LITERAL_RE.match(text):
        import ast
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError, MemoryError, RecursionError):
            parsed = None
        if isinstance(parsed, (list, tuple)):
            html_list = _qw_items_to_ul_html(parsed)
            if html_list:
                return html_list
    return html_module.escape(text)


# =============================================================================
# FIX-510 CHANGE 2: QuickWins Premium Renderer
# =============================================================================
# Renders FIX-506 JSON format (title, icon, problem, wirkung, umsetzung, hinweis)
# to rich HTML cards that meet >=30 word requirements.

def render_quickwins_premium_json(raw_json: str, template_mode: str = "FULL", run_id: str = "", lang: str = "de") -> Optional[str]:
    """
    FIX-510 CHANGE 2: Premium renderer for FIX-506 QuickWins JSON format.

    Converts JSON with fields (title, icon, problem, wirkung, umsetzung, hinweis)
    to rich HTML cards with sufficient word count (>=30 words).

    Args:
        raw_json: JSON string with QuickWins array
        template_mode: "LEFT_ONLY", "FULL", etc.
        run_id: Optional briefing/run identifier for diagnostic logs.

    Returns:
        Rich HTML string or None if parsing fails
    """
    import json
    import html as html_module

    # [QW-JSON-DEBUG] Strukturierter Marker für Diagnose des Premium-Pfades.
    # Loggt ausschließlich Metriken (keine Roh-JSON-Inhalte), damit nach Merge
    # in Production sichtbar wird, warum der Premium-Renderer für ein konkretes
    # Briefing nach None fällt und der Legacy-Pfad greift.
    raw_chars = len(raw_json or "")

    if not raw_json or not raw_json.strip():
        log.info(
            "[QW-JSON-DEBUG] run_id=%s renderer=premium status=fail "
            "reason=empty_input json_raw_chars=%d", run_id, raw_chars,
        )
        return None

    try:
        # Parse JSON
        cleaned = raw_json.strip()

        # Remove markdown code fences
        if cleaned.startswith("```"):
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
            if match:
                cleaned = match.group(1).strip()
            else:
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)

        # Extract array
        match = re.search(r'(\[[\s\S]*\])', cleaned)
        if match:
            cleaned = match.group(1)

        # KIS-1236: literale Steuerzeichen (Newlines) in JSON-Strings mit
        # strict=False heilen statt in den Legacy-/STRICT-Pfad zu fallen.
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as _strict_err:
            if "control character" not in str(_strict_err).lower():
                raise
            data = json.loads(cleaned, strict=False)
            log.info(
                "[QW-JSON-DEBUG] run_id=%s renderer=premium strict_false_heal "
                "pos=%d", run_id, _strict_err.pos or 0,
            )

        if not isinstance(data, list) or len(data) == 0:
            log.info(
                "[QW-JSON-DEBUG] run_id=%s renderer=premium status=fail "
                "reason=%s json_raw_chars=%d item_count=%d",
                run_id,
                "not_a_list" if not isinstance(data, list) else "empty_array",
                raw_chars,
                len(data) if isinstance(data, list) else 0,
            )
            return None

        # TASK 1 (P0 FINAL): DUMP POINT 1 - Raw JSON after parsing
        dump_raw_json(data, context="render_quickwins_premium_json")

        # [QW-JSON-DEBUG] Pro Quick-Win: welche der vom Prompt geforderten
        # Felder (title/icon/problem/wirkung/umsetzung/hinweis) fehlen oder
        # sind leer? Aufschluss darüber, ob das LLM den Output-Vertrag
        # einhält oder bestimmte Felder systematisch leer lässt. Ausgeführt
        # VOR enforce_quickwins_complete, damit die Roh-Daten gemessen werden.
        _required = ("title", "icon", "problem", "wirkung", "umsetzung", "hinweis")
        _missing_per_qw = [
            [f for f in _required if not (isinstance(qw, dict) and str(qw.get(f, "")).strip())]
            for qw in data
        ]
        log.info(
            "[QW-JSON-DEBUG] run_id=%s renderer=premium status=parsed "
            "json_raw_chars=%d item_count=%d fields_missing_per_qw=%s",
            run_id, raw_chars, len(data), _missing_per_qw,
        )

        # TASK B (P0): Apply completeness gate - fill empty fields with deterministic fallbacks
        data = enforce_quickwins_complete(data, lang=lang)

        # KIS-1232: Überschrift/TOC versprechen "Quick Wins: Top 3" — der
        # KMU-Lauf lieferte 4 Karten. Auf die Top-N kappen (ENV-Override).
        try:
            _qw_max = int(os.getenv("QUICK_WINS_MAX_CARDS", "3"))
        except ValueError:
            _qw_max = 3
        if _qw_max > 0 and len(data) > _qw_max:
            log.info(
                "[KIS-1232-QW] Kappe Quick Wins von %d auf %d Karten (QUICK_WINS_MAX_CARDS)",
                len(data), _qw_max,
            )
            data = data[:_qw_max]

        # Build premium cards
        cards_html = []
        total_words = 0

        # KIS-1272-R4-T2a: Label-Map sprachabhängig wählen (EN: Impact/Implementation).
        _lang_en = str(lang or "de").lower().startswith("en")
        _labels = QUICKWIN_CARD_LABELS["en" if _lang_en else "de"]

        for i, qw in enumerate(data):
            if not isinstance(qw, dict):
                continue

            title = html_module.escape(str(qw.get("title", f"Quick Win {i+1}")).strip())
            icon = str(qw.get("icon", "🎯")).strip()
            # KIS-1272-R4-T2b: Listen/Listen-Literale sicher als <ul> rendern
            # (sprachneutral — auch DE darf nie ein rohes ['…'] zeigen).
            problem = qw_field_value_to_html(qw.get("problem", ""))
            wirkung = qw_field_value_to_html(qw.get("wirkung", ""))
            umsetzung = qw_field_value_to_html(qw.get("umsetzung", ""))
            # KIS-1272-R4-T2c: Hinweis-Default und "siehe Business Case" im EN-Pfad
            # englisch ("see business case"); DE bleibt byte-identisch.
            _hinweis_default = "see business case" if _lang_en else "siehe Business Case"
            _hinweis_raw = str(qw.get("hinweis", _hinweis_default) or _hinweis_default).strip()
            if _lang_en and _hinweis_raw.lower() == "siehe business case":
                _hinweis_raw = "see business case"
            hinweis = html_module.escape(_hinweis_raw)

            # Count words for this card
            card_text = f"{title} {problem} {wirkung} {umsetzung} {hinweis}"
            card_words = len(card_text.split())
            total_words += card_words

            # TASK B: Build field blocks only if they have content (skip empty)
            problem_block = ""
            if problem:
                problem_block = f'''
        <div class="quick-win-problem" style="margin-bottom:10px;padding:10px;background:#fef2f2;border-radius:8px;border-left:3px solid #ef4444;">
            <strong style="color:#dc2626;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">{_labels["problem"]}</strong>
            <p style="margin:4px 0 0 0;">{problem}</p>
        </div>'''

            wirkung_block = ""
            if wirkung:
                wirkung_block = f'''
        <div class="quick-win-wirkung" style="margin-bottom:10px;padding:10px;background:#f0fdf4;border-radius:8px;border-left:3px solid #22c55e;">
            <strong style="color:#16a34a;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">{_labels["wirkung"]}</strong>
            <p style="margin:4px 0 0 0;">{wirkung}</p>
        </div>'''

            umsetzung_block = ""
            if umsetzung:
                umsetzung_block = f'''
        <div class="quick-win-umsetzung" style="margin-bottom:10px;padding:10px;background:#eff6ff;border-radius:8px;border-left:3px solid #3b82f6;">
            <strong style="color:#2563eb;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">{_labels["umsetzung"]}</strong>
            <p style="margin:4px 0 0 0;">{umsetzung}</p>
        </div>'''

            # TASK B: Build card HTML with conditional blocks (skip empty ones)
            card_html = f'''
<div class="quick-win quick-win-card-premium" data-qw-json-rendered="true" data-qw-premium="true" style="background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:16px;break-inside:avoid;page-break-inside:avoid;">
    <div class="quick-win-header" style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
        <span class="quick-win-icon" style="font-size:24px;flex-shrink:0;">{icon}</span>
        <h4 class="quick-win-title" style="margin:0;font-size:14px;font-weight:600;color:#1e293b;line-height:1.3;">{title}</h4>
    </div>
    <div class="quick-win-body" style="font-size:12px;line-height:1.5;color:#475569;">{problem_block}{wirkung_block}{umsetzung_block}
        <div class="quick-win-hinweis" style="font-size:11px;color:#6b7280;font-style:italic;padding-top:8px;border-top:1px solid #e5e7eb;">
            💡 {hinweis}
        </div>
    </div>
</div>'''
            cards_html.append(card_html)

        if not cards_html:
            log.info(
                "[QW-JSON-DEBUG] run_id=%s renderer=premium status=fail "
                "reason=no_valid_cards json_raw_chars=%d item_count=%d",
                run_id, raw_chars, len(data),
            )
            return None

        # FIX-517C: WeasyPrint-safe layout (table instead of CSS Grid)
        if template_mode == "LEFT_ONLY" and len(cards_html) >= 2:
            # 2-column table layout for full-width mode
            mid = (len(cards_html) + 1) // 2
            left_col = "".join(cards_html[:mid])
            right_col = "".join(cards_html[mid:])
            html_out = f'''<div class="quickwins-premium-container quick-wins" data-qw-json-rendered="true" data-qw-premium="true" style="width:100%;">
<table class="quickwins-fullwidth-table" style="width:100%;border-collapse:separate;border-spacing:16px;table-layout:fixed;">
<tr>
<td style="vertical-align:top;width:50%;">{left_col}</td>
<td style="vertical-align:top;width:50%;">{right_col}</td>
</tr>
</table>
</div>'''
        else:
            wrapper_class = "quickwins-premium-container quick-wins"
            wrapper_style = "width:100%;"
            html_out = f'''<div class="{wrapper_class}" data-qw-json-rendered="true" data-qw-premium="true" style="{wrapper_style}">
{"".join(cards_html)}
</div>'''

        # Log for debugging (FIX-510 requirement)
        has_marker = 'data-qw-json-rendered="true"' in html_out
        has_class = 'class="quick-win' in html_out
        log.info(
            "[FIX-510-QW] premium_render items=%d words=%d mode=%s has_marker=%d has_class=%d",
            len(cards_html), total_words, template_mode, has_marker, has_class
        )

        # TASK 1 (P0 FINAL): DUMP POINT 2 - Renderer output HTML
        dump_renderer_output(html_out, renderer_name="render_quickwins_premium_json")

        log.info(
            "[QW-JSON-DEBUG] run_id=%s renderer=premium status=ok "
            "json_raw_chars=%d item_count=%d total_words=%d mode=%s",
            run_id, raw_chars, len(cards_html), total_words, template_mode,
        )

        return html_out

    except json.JSONDecodeError as e:
        log.debug("[FIX-510-QW] JSON parse failed: %s", e)
        log.info(
            "[QW-JSON-DEBUG] run_id=%s renderer=premium status=fail "
            "reason=json_decode_error json_raw_chars=%d err=%.80s",
            run_id, raw_chars, str(e),
        )
        return None
    except Exception as e:
        log.warning("[FIX-510-QW] Premium render failed: %s", e)
        log.info(
            "[QW-JSON-DEBUG] run_id=%s renderer=premium status=fail "
            "reason=exception json_raw_chars=%d err_type=%s err=%.80s",
            run_id, raw_chars, type(e).__name__, str(e),
        )
        return None


def apply_quickwins_fullwidth_enhancement(sections: dict) -> dict:
    """
    FIX-504 TASK 4: Apply QuickWins full-width enhancement when LEFT_ONLY mode.

    Automatically detects template mode and applies premium layout enhancement
    when the right column is empty (LEFT_ONLY mode).

    FIX-506 TASK 3: Also applies premium enrichment with sublines.

    Args:
        sections: Dict with all report sections

    Returns:
        Sections with enhanced QuickWins layout
    """
    template_mode = detect_quickwins_template_mode(sections)
    log.info(f"[QUICKWINS-FULLWIDTH] Detected template_mode={template_mode}")

    # Only enhance for LEFT_ONLY or FULL mode (no split columns)
    if template_mode not in ("LEFT_ONLY", "FULL"):
        log.debug("[QUICKWINS-FULLWIDTH] Skipping - not in full-width mode")
        return sections

    # Get the QuickWins HTML to enhance
    qw_key = "QUICK_WINS_HTML"
    qw_html = sections.get(qw_key, "")

    if not qw_html or not isinstance(qw_html, str):
        # Try LEFT key
        qw_key = "QUICK_WINS_HTML_LEFT"
        qw_html = sections.get(qw_key, "")

    if not qw_html or not isinstance(qw_html, str):
        log.debug("[QUICKWINS-FULLWIDTH] No QuickWins HTML found")
        return sections

    # FIX-506 TASK 3: Apply premium enrichment first (adds sublines for word count)
    enriched = enrich_quickwins_premium(qw_html)

    # FIX-504 TASK 4: Apply fullwidth layout enhancement
    enhanced = enhance_quickwins_for_fullwidth(enriched)
    sections[qw_key] = enhanced

    # Also update the main key if we enhanced LEFT
    if qw_key == "QUICK_WINS_HTML_LEFT":
        sections["QUICK_WINS_HTML"] = enhanced

    return sections


# =============================================================================
# FIX-512: QuickWins Deterministic Normalization (Text/Bullets → HTML)
# =============================================================================
# Kill-switch for STRICT blocker: instead of aborting on missing HTML structure,
# deterministically normalize plain-text/bullets/bare-HTML to valid QW HTML.

_BULLET_PATTERN = re.compile(r'^\s*(?:[-•*]|\d+[.)]\s)', re.MULTILINE)


def _extract_items_from_text(raw: str) -> list:
    """
    FIX-512: Extract meaningful items from plain-text/bullet content.

    Returns list of stripped item strings.
    """
    lines = raw.strip().splitlines()
    items = []
    for line in lines:
        # Strip bullet/number prefix
        cleaned = re.sub(r'^\s*(?:[-•*]|\d+[.)]\s*)\s*', '', line).strip()
        # Skip empty or too-short lines
        if cleaned and len(cleaned) >= 10:
            items.append(cleaned)
    # If no bullet items found, try splitting by sentence-like chunks
    if not items:
        for line in lines:
            stripped = line.strip()
            if stripped and len(stripped) >= 10:
                items.append(stripped)
    return items


def _render_items_as_html(items: list) -> str:
    """
    FIX-512: Render extracted items as Quick Wins HTML list.
    """
    import html as html_module

    li_items = []
    for item in items[:6]:
        escaped = html_module.escape(item)
        li_items.append(
            f'  <li class="quick-win" data-qw-json-rendered="true">{escaped}</li>'
        )

    inner = "\n".join(li_items)
    return (
        f'<div class="quick-wins-container" data-qw-json-rendered="true">\n'
        f'<ul class="quick-wins-list">\n{inner}\n</ul>\n'
        f'</div>'
    )


def _inject_markers_into_html(html_content: str) -> str:
    """
    FIX-512: Inject class="quick-win" and data-qw-json-rendered markers into
    existing HTML that lacks them.
    """
    modified = html_content

    # Inject container wrapper if no quick-wins-container
    if 'quick-wins-container' not in modified:
        modified = (
            f'<div class="quick-wins-container" data-qw-json-rendered="true">\n'
            f'{modified}\n</div>'
        )
    elif 'data-qw-json-rendered' not in modified:
        # Add marker to existing container
        modified = modified.replace(
            'class="quick-wins-container"',
            'class="quick-wins-container" data-qw-json-rendered="true"',
            1
        )

    # Inject class="quick-win" on <li> or card divs if missing
    if 'class="quick-win' not in modified:
        # Try to add to <li> elements
        modified = re.sub(
            r'<li(?![^>]*class=)([^>]*)>',
            r'<li class="quick-win"\1>',
            modified,
            count=6
        )
        # If still no quick-win class (no <li>s), try <div> items
        if 'class="quick-win' not in modified:
            modified = re.sub(
                r'<div(?![^>]*class=)([^>]*)>',
                r'<div class="quick-win"\1>',
                modified,
                count=1
            )

    return modified


def normalize_quickwins_to_html(raw: str, strict: bool = False, company_size: str = "solo", lang: str = "de") -> tuple[str, dict]:
    """
    FIX-512: Deterministic QuickWins normalization (Text/Bullets → HTML).

    Converts any raw Quick Wins content (JSON, bare HTML, plain text/bullets)
    into valid HTML with class="quick-win" and data-qw-json-rendered="true".

    Args:
        raw: Raw Quick Wins content (JSON, HTML, or plain text)
        strict: If True and normalization fails, raise RuntimeError
        company_size: Company size for size-aware fallback (solo/team/kmu)

    Returns:
        Tuple of (normalized_html, meta_dict) where meta_dict contains:
        - path: "JSON" | "HTML" | "TEXT_BULLETS"
        - items: number of items found
        - has_marker: bool
        - has_class: bool
        - len: output length
    """
    if not raw or not raw.strip():
        if strict:
            # FIX-PIPELINE: Empty input in STRICT mode → return fallback (no raise)
            log.warning("[QW-NORMALIZE] ⚠️ empty input in STRICT mode - generating fallback")
            fallback_html = _generate_minimal_quickwins_fallback(company_size)
            fallback_meta = {
                "path": "FALLBACK_STRICT",
                "items": 3,
                "has_marker": True,
                "has_class": True,
                "len": len(fallback_html),
                "reason": "empty_input",
            }
            return fallback_html, fallback_meta
        return "", {"path": "EMPTY", "items": 0, "has_marker": False, "has_class": False, "len": 0}

    stripped = raw.strip()
    path = "UNKNOWN"
    result_html = ""

    # --- Path 1: JSON (starts with [ or {) ---
    if stripped.startswith(('[', '{')):
        path = "JSON"
        # KIS-1272-R4-T2: lang durchreichen, damit EN-Karten EN-Labels bekommen.
        rendered = render_quickwins_premium_json(stripped, lang=lang)
        if rendered:
            result_html = rendered
        else:
            # Try simpler JSON extraction
            import json
            try:
                cleaned = stripped
                if cleaned.startswith("```"):
                    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                    cleaned = re.sub(r'\s*```$', '', cleaned)
                data = json.loads(cleaned)
                if isinstance(data, list) and len(data) > 0:
                    items_text = []
                    for item in data:
                        if isinstance(item, dict):
                            title = item.get("title") or item.get("titel") or item.get("name", "")
                            if title:
                                items_text.append(str(title))
                    if items_text:
                        result_html = _render_items_as_html(items_text)
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    # --- Path 2: HTML (contains tags) ---
    elif '<' in stripped and '>' in stripped and re.search(r'<\w+[\s>]', stripped):
        path = "HTML"
        result_html = _inject_markers_into_html(stripped)

    # --- Path 3: Plain text / bullets ---
    if not result_html:
        if path == "UNKNOWN":
            path = "TEXT_BULLETS"
        items = _extract_items_from_text(stripped)
        if items:
            result_html = _render_items_as_html(items)

    # --- Validate result ---
    has_marker = 'data-qw-json-rendered="true"' in result_html
    has_class = 'class="quick-win' in result_html

    # Count items
    item_count = result_html.count('class="quick-win')

    meta = {
        "path": path,
        "items": item_count,
        "has_marker": has_marker,
        "has_class": has_class,
        "len": len(result_html),
    }

    # STRICT validation - FIX: Never raise, always fallback (Pipeline-Stabilität)
    # FIX-E3+H1: Bevor Fallback, alternative Item-Zählung via mehrere Marker
    if strict and (item_count < 3 or len(result_html) < 250):
        h4_count = len(re.findall(r'<h4[^>]*>', result_html, re.IGNORECASE))
        # FIX-H1: Auch nummerierte <strong>-Patterns als Items zählen
        # LLM strukturiert oft als "<strong>1. Titel</strong>" oder "<p><strong>Nutzen:"
        strong_numbered = len(re.findall(r'<strong>\s*\d+[\.\):]', result_html))
        # Oder <li> mit substantiellem Content als Items
        li_items = len(re.findall(r'<li[^>]*>[^<]{20,}', result_html))
        # Beste Schätzung: Maximum aller Marker
        best_count = max(h4_count, strong_numbered, li_items // 2)
        log.info(
            "[FIX-H1] QW item detection: h4=%d, strong_num=%d, li=%d, best=%d, len=%d",
            h4_count, strong_numbered, li_items, best_count, len(result_html)
        )
        if best_count >= 3 and len(result_html) > 1000:
            log.info(
                "[FIX-H1] QW-NORMALIZE: best_count=%d overrides item_count=%d, len=%d - skipping fallback",
                best_count, item_count, len(result_html)
            )
            item_count = best_count
            has_class = True  # Trust the content
        else:
            log.warning(
                "[QW-NORMALIZE] ⚠️ insufficient content in STRICT mode "
                "(items=%d best=%d h4=%d strong=%d li=%d len=%d) - generating fallback",
                item_count, best_count, h4_count, strong_numbered, li_items, len(result_html)
            )
        # Generate minimal fallback HTML instead of raising
        fallback_html = _generate_minimal_quickwins_fallback(company_size)
        fallback_meta = {
            "path": "FALLBACK_STRICT",
            "items": 3,
            "has_marker": True,
            "has_class": True,
            "len": len(fallback_html),
            "original_items": item_count,
            "original_len": len(result_html),
            "reason": "insufficient_content",
        }
        return fallback_html, fallback_meta

    log.info(
        "[FIX-512-QW] normalize path=%s items=%d has_marker=%s has_class=%s len=%d",
        path, item_count, has_marker, has_class, len(result_html)
    )

    return result_html, meta


def _generate_minimal_quickwins_fallback(company_size: str = "solo") -> str:
    """
    Generate minimal Quick Wins fallback HTML when normalization fails.

    FIX-PIPELINE: This ensures Quick Wins NEVER crashes the pipeline.
    FIX-620: Size-aware - generates 3 items for solo, 4 for team, 5 for KMU.
    Returns a valid HTML structure with generic but useful items.
    """
    items = [
        '''  <div class="quick-win" data-fallback="true">
    <h4>1. KI-Assistenten für Alltagsaufgaben einsetzen</h4>
    <p><strong>Nutzen:</strong> Zeitersparnis bei wiederkehrenden Texten, E-Mails und Recherchen.</p>
    <p><strong>Aufwand:</strong> S (wenige Stunden Einarbeitung)</p>
    <p><strong>Nächste Schritte:</strong></p>
    <ol>
      <li>Passenden KI-Assistenten auswählen (ChatGPT, Claude, etc.)</li>
      <li>Erste Anwendungsfälle identifizieren</li>
      <li>Prompt-Templates für häufige Aufgaben erstellen</li>
    </ol>
  </div>''',
        '''  <div class="quick-win" data-fallback="true">
    <h4>2. Dokumentation und Wissensbasis aufbauen</h4>
    <p><strong>Nutzen:</strong> Schnellerer Zugriff auf wichtige Informationen, weniger Suchzeit.</p>
    <p><strong>Aufwand:</strong> M (1-2 Wochen schrittweise)</p>
    <p><strong>Nächste Schritte:</strong></p>
    <ol>
      <li>Zentrale Ablage für Dokumente einrichten</li>
      <li>Wichtigste Prozesse dokumentieren</li>
      <li>Suchfunktion optimieren oder KI-Suche integrieren</li>
    </ol>
  </div>''',
        '''  <div class="quick-win" data-fallback="true">
    <h4>3. Erste Automatisierung einrichten</h4>
    <p><strong>Nutzen:</strong> Manuelle Routineaufgaben eliminieren, Fehler reduzieren.</p>
    <p><strong>Aufwand:</strong> M (wenige Tage Setup)</p>
    <p><strong>Nächste Schritte:</strong></p>
    <ol>
      <li>Zeitfresser-Prozess identifizieren</li>
      <li>Automatisierungstool auswählen (Make, Zapier, n8n)</li>
      <li>Ersten Workflow aufsetzen und testen</li>
    </ol>
  </div>''',
        '''  <div class="quick-win" data-fallback="true">
    <h4>4. KI-gestützte Qualitätssicherung etablieren</h4>
    <p><strong>Nutzen:</strong> Konsistentere Ergebnisse, weniger manuelle Nacharbeit bei Dokumenten und Prozessen.</p>
    <p><strong>Aufwand:</strong> S (wenige Stunden Setup)</p>
    <p><strong>Nächste Schritte:</strong></p>
    <ol>
      <li>Prüfchecklisten für KI-Outputs definieren</li>
      <li>Korrektur-Workflows mit KI-Unterstützung aufsetzen</li>
      <li>Feedback-Schleife für kontinuierliche Verbesserung einrichten</li>
    </ol>
  </div>''',
        '''  <div class="quick-win" data-fallback="true">
    <h4>5. Datenbasierte Entscheidungsgrundlagen schaffen</h4>
    <p><strong>Nutzen:</strong> Bessere Entscheidungen durch KI-Analyse vorhandener Geschäftsdaten und Marktinformationen.</p>
    <p><strong>Aufwand:</strong> M (1-2 Wochen schrittweise)</p>
    <p><strong>Nächste Schritte:</strong></p>
    <ol>
      <li>Relevante Datenquellen identifizieren und konsolidieren</li>
      <li>KI-Analysetool für Ihr Datenformat auswählen</li>
      <li>Erste Dashboard-Vorlage mit KI-Unterstützung erstellen</li>
    </ol>
  </div>''',
    ]

    # FIX-620: Size-aware item count
    size_lower = (company_size or "").lower()
    if any(x in size_lower for x in ("kmu", "mittel", "11-100", "100")):
        item_count = 5
    elif any(x in size_lower for x in ("team", "klein", "2-10")):
        item_count = 4
    else:
        item_count = 3

    selected = items[:item_count]
    inner = "\n".join(selected)
    return f'''<!-- RENDERED:quick_wins -->
<div class="quick-wins-container" data-qw-json-rendered="true">
{inner}
</div>'''
