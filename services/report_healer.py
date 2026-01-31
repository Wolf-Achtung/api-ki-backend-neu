# -*- coding: utf-8 -*-
"""
Report Healer - Fixes A-G + Redundancy Auto-Shortening
======================================================

Central pipeline for healing report HTML before PDF rendering.

Fixes implemented:
- Fix A: TEMPLATE_PHRASE - Remove prompt artifacts and placeholder texts
- Fix B: SIZE_MISMATCH - Enforce persona language for SOLO (simplified terms)
- Fix C: REDUNDANCY_DETECTED - Auto-shorten redundant content
- Fix D: ROI_PROHIBITED - ROI percentages only in Business Case
- Fix E: INCOMPLETE_SENTENCE - Trim sentence fragments
- Fix F: Payback consistency & duplicate removal
- Fix G: Segment budget logic for report shortening

Version: 1.1.0 (FIX-A-G + Type-Safe Recursive Healing)
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Tuple, TypeVar, Union

log = logging.getLogger(__name__)

__all__ = [
    "heal_report_html",
    "heal_final_html",
    "sanitize_template_phrases",
    "enforce_persona_language",
    "reduce_redundancy",
    "enforce_roi_rules",
    "trim_incomplete_sentences",
    "enforce_payback_consistency",
    "sanitize_payback_progress_labels",
    "apply_segment_budget",
    "parse_payback_months",
    "format_payback_de",
    "localize_business_case_labels_de",
    "run_quality_gate",
    "canonicalize_segment",
    "normalize_section_keys",
    "QualityGateResult",
    "ReportQualityError",
    "HealingResult",
    "BOILERPLATE_PATTERNS",
    "PAYBACK_PATTERNS_DE",
    "SOLO_BLACKLIST_TERMS",
    "BUSINESS_CASE_LABEL_LOCALIZATION_DE",
    "BoilerplatePattern",
    "PaybackPattern",
]


# =============================================================================
# HELPER: Type-Safe Recursive Healing (NO str() conversion for list/dict)
# =============================================================================

T = TypeVar("T")


def _walk(obj: Any, fn_string: Callable[[str], str]) -> Any:
    """
    Recursively traverse data structure and apply fn_string only to string leaves.

    Preserves types: list stays list, dict stays dict, numbers stay numbers.
    Only string values are transformed via fn_string.

    Args:
        obj: Any value (str, list, dict, int, float, None, etc.)
        fn_string: Function to apply to string values

    Returns:
        Transformed structure with same types, only strings modified
    """
    if isinstance(obj, str):
        return fn_string(obj)
    elif isinstance(obj, list):
        return [_walk(item, fn_string) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_walk(item, fn_string) for item in obj)
    elif isinstance(obj, dict):
        return {k: _walk(v, fn_string) for k, v in obj.items()}
    else:
        # int, float, bool, None, etc. - return unchanged
        return obj


# =============================================================================
# TASK 1: Segment Canonicalization
# =============================================================================

# Segment synonyms mapping to canonical values
_SEGMENT_SYNONYMS: Dict[str, str] = {
    # SOLO variants
    "solo": "SOLO",
    "SOLO": "SOLO",
    "einzel": "SOLO",
    "einzelunternehmer": "SOLO",
    "freiberuf": "SOLO",
    "freiberufler": "SOLO",
    "selbstständig": "SOLO",
    "selbständig": "SOLO",
    "solopreneur": "SOLO",
    "freelancer": "SOLO",
    # TEAM variants
    "team": "TEAM",
    "TEAM": "TEAM",
    "klein": "TEAM",
    "kleinunternehmen": "TEAM",
    "startup": "TEAM",
    "small": "TEAM",
    # KMU variants
    "kmu": "KMU",
    "KMU": "KMU",
    "sme": "KMU",
    "SME": "KMU",
    "mittelstand": "KMU",
    "mittelständisch": "KMU",
    "medium": "KMU",
}


def canonicalize_segment(segment: str) -> Literal["SOLO", "TEAM", "KMU"]:
    """
    TASK 1: Canonicalize segment identifier to uppercase standard form.

    Accepts various segment synonyms and returns canonical form:
    - "solo", "SOLO", "einzel", "freiberuf" → "SOLO"
    - "team", "TEAM", "klein", "startup" → "TEAM"
    - "kmu", "KMU", "sme", "mittelstand" → "KMU"

    Default: "TEAM" if unrecognized.

    Args:
        segment: Raw segment identifier (any case/synonym)

    Returns:
        Canonical segment: "SOLO", "TEAM", or "KMU"
    """
    if not segment:
        log.warning("[SEGMENT] Empty segment provided, defaulting to TEAM")
        return "TEAM"

    # Clean and normalize input
    cleaned = segment.strip().lower()

    # Look up in synonyms map
    canonical = _SEGMENT_SYNONYMS.get(cleaned)
    if canonical:
        if cleaned != canonical.lower():
            log.debug("[SEGMENT] Canonicalized '%s' → '%s'", segment, canonical)
        return canonical  # type: ignore

    # Try partial match for compound terms
    for synonym, canon in _SEGMENT_SYNONYMS.items():
        if synonym in cleaned or cleaned in synonym:
            log.debug("[SEGMENT] Partial match '%s' → '%s'", segment, canon)
            return canon  # type: ignore

    # Default to TEAM
    log.warning("[SEGMENT] Unknown segment '%s', defaulting to TEAM", segment)
    return "TEAM"


def _is_html_section_key(key: str) -> bool:
    """
    Check if a key represents an HTML section (vs metadata/numeric field).

    HTML sections are healed; metadata/numbers are preserved as-is.
    """
    # Internal metadata keys start with _
    if key.startswith("_"):
        return False
    # Known HTML section patterns
    html_patterns = ("_HTML", "_html", "HTML_")
    if any(p in key for p in html_patterns):
        return True
    # Known non-HTML keys (numbers, metadata)
    non_html_keys = {
        "PAYBACK_MONTHS", "ROI_12M", "CAPEX_REALISTISCH_EUR", "OPEX_REALISTISCH_EUR",
        "EINSPARUNG_MONAT_EUR", "score_governance", "score_sicherheit", "score_nutzen",
        "score_wertschoepfung", "score_befaehigung", "score_gesamt", "LANG",
        "report_date", "report_year", "BUILD_ID", "COMPACT_REPORT_MODE", "COMPANY_SIZE",
    }
    if key in non_html_keys:
        return False
    # Default: treat as potentially containing text that needs healing
    return True


def _extract_string_sections(sections: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract only the top-level string sections for redundancy/budget processing.

    Used by Fix C and Fix G which operate on flat Dict[str, str].
    Preserves structure but only returns actual string values.
    """
    result: Dict[str, str] = {}
    for key, value in sections.items():
        if isinstance(value, str) and _is_html_section_key(key):
            result[key] = value
    return result


def _merge_healed_sections(
    original: Dict[str, Any],
    healed_strings: Dict[str, str]
) -> Dict[str, Any]:
    """
    Merge healed string sections back into original structure.
    """
    result = dict(original)
    for key, value in healed_strings.items():
        result[key] = value
    return result


# =============================================================================
# TASK 5: Section Key Normalization & Redundant Key Dropping
# =============================================================================

# Keys that are redundant when more specific versions exist
_REDUNDANT_KEY_RULES: List[Tuple[str, str, List[str]]] = [
    # (key_to_drop, required_key_for_drop, segments_to_apply)
    # Drop pilot_plan_html if roadmap_90d_html exists (for SOLO and TEAM)
    ("pilot_plan_html", "roadmap_90d_html", ["SOLO", "TEAM"]),
    ("PILOT_PLAN_HTML", "ROADMAP_90D_HTML", ["SOLO", "TEAM"]),
    # Drop roadmap_html if roadmap_90d_html exists (all segments)
    ("roadmap_html", "roadmap_90d_html", ["SOLO", "TEAM", "KMU"]),
    ("ROADMAP_HTML", "ROADMAP_90D_HTML", ["SOLO", "TEAM", "KMU"]),
]


def normalize_section_keys(
    sections: Dict[str, Any],
    segment: Literal["SOLO", "TEAM", "KMU"]
) -> Tuple[Dict[str, Any], List[str]]:
    """
    TASK 5: Normalize section keys and drop redundant ones.

    - Normalizes keys to case-insensitive comparison
    - Drops redundant keys based on segment rules:
      - pilot_plan_html dropped if roadmap_90d_html exists (SOLO, TEAM)
      - roadmap_html dropped if roadmap_90d_html exists (all segments)

    Args:
        sections: Original sections dict
        segment: Canonical segment (SOLO, TEAM, KMU)

    Returns:
        Tuple of (normalized_sections, dropped_keys)
    """
    result = dict(sections)
    dropped_keys: List[str] = []

    # Build case-insensitive lookup
    lower_key_map: Dict[str, str] = {k.lower(): k for k in sections.keys()}

    for key_to_drop, required_key, applicable_segments in _REDUNDANT_KEY_RULES:
        # Check if this rule applies to current segment
        if segment not in applicable_segments:
            continue

        # Check if both keys exist (case-insensitive)
        drop_key_lower = key_to_drop.lower()
        required_key_lower = required_key.lower()

        if drop_key_lower in lower_key_map and required_key_lower in lower_key_map:
            actual_drop_key = lower_key_map[drop_key_lower]
            actual_required_key = lower_key_map[required_key_lower]

            # Only drop if required key has non-empty content
            required_content = result.get(actual_required_key)
            if required_content and (isinstance(required_content, str) and len(required_content) > 50):
                if actual_drop_key in result:
                    del result[actual_drop_key]
                    dropped_keys.append(actual_drop_key)
                    log.info(
                        "[TASK5] Dropped redundant key '%s' (segment=%s, '%s' exists)",
                        actual_drop_key, segment, actual_required_key
                    )

    return result, dropped_keys


# =============================================================================
# PAYBACK: Parsing and German Formatting
# =============================================================================

# Regex to extract payback number from various formats
_PAYBACK_EXTRACT_RE = re.compile(
    r"(\d+)[.,](\d+)|\b(\d+)\b",
    re.IGNORECASE
)


def parse_payback_months(value: Any) -> Optional[Decimal]:
    """
    Parse payback months from various formats to Decimal.

    Accepts:
    - float/int: 3.5, 4
    - strings: "3.5", "3,5", "3,5 Monate", "innerhalb von 3.5 Monaten"

    Returns:
        Decimal value or None if parsing fails
    """
    if value is None:
        return None

    # Handle numeric types directly
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    if isinstance(value, Decimal):
        return value

    if not isinstance(value, str):
        return None

    # Clean string: replace comma with dot for parsing
    cleaned = value.strip().replace(",", ".")

    # Try direct conversion first
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        pass

    # Extract number from text like "3.5 Monaten" or "innerhalb von 3,5 Monaten"
    match = _PAYBACK_EXTRACT_RE.search(cleaned)
    if match:
        if match.group(1) and match.group(2):
            # Decimal number: "3.5" or "3,5" (already converted to "3.5")
            try:
                return Decimal(f"{match.group(1)}.{match.group(2)}")
            except InvalidOperation:
                pass
        elif match.group(3):
            # Integer: "3"
            try:
                return Decimal(match.group(3))
            except InvalidOperation:
                pass

    return None


def format_payback_de(value: Union[Decimal, float, int, None], decimals: int = 1) -> str:
    """
    Format payback value to German format (comma as decimal separator).

    Args:
        value: Numeric value to format
        decimals: Number of decimal places (default 1)

    Returns:
        German formatted string like "3,5" or empty string if value is None
    """
    if value is None:
        return ""

    try:
        # Convert to Decimal for precise formatting
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return ""
            dec_value = Decimal(str(value))
        elif isinstance(value, int):
            dec_value = Decimal(value)
        elif isinstance(value, Decimal):
            dec_value = value
        else:
            return ""

        # Format with specified decimals and replace dot with comma
        formatted = f"{float(dec_value):.{decimals}f}"
        return formatted.replace(".", ",")
    except (InvalidOperation, ValueError):
        return ""

# =============================================================================
# FIX A: TEMPLATE_PHRASE PATTERNS (Boilerplate Registry)
# =============================================================================

@dataclass
class BoilerplatePattern:
    """Definition for a boilerplate pattern to remove or replace."""
    pattern: str  # Regex pattern
    action: Literal["drop", "replace"]
    replacement: str = ""
    description: str = ""


# =============================================================================
# BOILERPLATE_PATTERNS_DE - Comprehensive German Pattern Registry
# =============================================================================

# Registry of known boilerplate/prompt artifacts (BOILERPLATE_PATTERNS_DE)
BOILERPLATE_PATTERNS: List[BoilerplatePattern] = [
    # -------------------------------------------------------------------------
    # A) Prompt-/Chat-Blöcke (TASK 1: Robust prompt artifact removal)
    # -------------------------------------------------------------------------
    # A1) "Wobei soll/kann ich dich unterstützen?" + <ol>/<ul> block (with <strong>)
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*<strong>\s*Wobei\s+(?:kann|soll)\s+ich\s+(?:dir|dich|Sie|Ihnen)[^<]*(?:unterstützen|helfen)[^<]*</strong>\s*</p>\s*<(?:ol|ul)[^>]*>.*?</(?:ol|ul)>',
        action="drop",
        description="PROMPT_WOBEI_STRONG_BLOCK: 'Wobei soll ich dich unterstützen?' with <strong> + list"
    ),
    # A2) Same but without <strong> tags
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*Wobei\s+(?:kann|soll)\s+ich\s+(?:dir|dich|Sie|Ihnen)[^<]*(?:unterstützen|helfen)[^<]*\??\s*</p>\s*<(?:ol|ul)[^>]*>.*?</(?:ol|ul)>',
        action="drop",
        description="PROMPT_WOBEI_PLAIN_BLOCK: 'Wobei soll ich...' without <strong> + list"
    ),
    # A3) Fallback: Just the question text + following list (no <p> wrapper)
    BoilerplatePattern(
        pattern=r'(?is)Wobei\s+(?:kann|soll)\s+ich\s+(?:dir|dich|Sie|Ihnen)\s+.*?(?:unterstützen|helfen)\s*\??\s*(?:</(?:p|strong)>)?\s*<(?:ol|ul)[^>]*>.*?</(?:ol|ul)>',
        action="drop",
        description="PROMPT_WOBEI_FALLBACK_BLOCK: 'Wobei soll/kann ich...' fallback with list"
    ),
    # A4) Question text alone (no list) - catch any remaining instances
    BoilerplatePattern(
        pattern=r'(?i)<p[^>]*>\s*(?:<strong>)?\s*Wobei\s+(?:kann|soll)\s+ich\s+(?:dir|dich|Sie|Ihnen)\s+[^<]*(?:unterstützen|helfen)[^<]*\??\s*(?:</strong>)?\s*</p>',
        action="drop",
        description="PROMPT_WOBEI_QUESTION_ONLY: Standalone question paragraph"
    ),
    # A5) Original patterns for "Wie/Wobei kann ich helfen"
    BoilerplatePattern(
        pattern=r'(?is)<div[^>]*class="heading[^"]*heading-h1"[^>]*>.*?(?:Wie|Wobei)\s+kann\s+ich.*?</div>',
        action="drop",
        description="PROMPT_HELP_H1_BLOCK: Chat-UI heading block"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<p>\s*(?:Wie|Wobei)\s+kann\s+ich\s+(?:Ihnen|dir)\s+(?:heute\s+)?helfen\?[^<]*</p>(?:\s*<ul>.*?</ul>)?',
        action="drop",
        description="PROMPT_HELP_P_PLUS_LIST: Prompt question with optional list"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*Bitte\s+beschreibe?\s+kurz[:\s]*[^<]*</p>(?:\s*<(?:ul|ol)>.*?</(?:ul|ol)>)?',
        action="drop",
        description="PROMPT_DESCRIBE_BLOCK: 'Bitte beschreibe kurz' with list"
    ),
    # -----------------------------------------------------------------
    # TASK 3: "Wobei kann ich helfen? Bitte beschreibe kurz:" Block
    # -----------------------------------------------------------------
    # A6) Block pattern: <p>Wobei kann ich (dir) helfen? Bitte beschreibe kurz:</p><ul/ol>...</ul/ol>
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*Wobei\s+kann\s+ich\s+(?:dir\s+)?helfen\?\s*(?:Bitte\s+beschreib(?:e|en)\s+kurz:?)?\s*</p>\s*(?:<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>)?',
        action="drop",
        description="PROMPT_WOBEI_HELFEN_BLOCK: 'Wobei kann ich helfen? Bitte beschreibe kurz:' + list"
    ),
    # A7) Text-only fallback without HTML wrapper
    BoilerplatePattern(
        pattern=r'(?i)\bWobei\s+kann\s+ich\s+(?:dir\s+)?helfen\?\s*(?:Bitte\s+beschreib(?:e|en)\s+kurz:?)?\b',
        action="drop",
        description="PROMPT_WOBEI_HELFEN_TEXT: 'Wobei kann ich helfen?' text-only fallback"
    ),
    # A8) Extended patterns for various prompt formats
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*(?:Wie|Wobei)\s+kann\s+ich\s+(?:dir|Ihnen|euch)?\s*(?:dabei\s+)?(?:helfen|unterstützen|assistieren)\?[^<]*</p>\s*(?:<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>)?',
        action="drop",
        description="PROMPT_KANN_ICH_EXTENDED: Extended 'Wie/Wobei kann ich helfen' patterns"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<div[^>]*class="[^"]*(?:chat-input|prompt-box|input-area)[^"]*"[^>]*>.*?</div>',
        action="drop",
        description="CHAT_INPUT_DIV: Chat input container"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<textarea[^>]*>.*?</textarea>',
        action="drop",
        description="TEXTAREA_BLOCK: Any textarea element"
    ),

    # -----------------------------------------------------------------
    # TASK 3 (FINAL FIX): Additional Prompt Leak Patterns
    # -----------------------------------------------------------------
    # A9) "Strategische Empfehlungen ? Bitte beschreibe kurz:" + list (complete block)
    BoilerplatePattern(
        pattern=r'(?is)<h[1-6][^>]*>\s*Strategische\s+Empfehlungen\s*\??\s*</h[1-6]>\s*(?:<p>)?\s*Bitte\s+beschreibe?\s+kurz\s*:?\s*(?:</p>)?\s*(?:<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>)?',
        action="drop",
        description="PROMPT_STRATEGISCHE_EMPFEHLUNGEN_BLOCK: 'Strategische Empfehlungen? Bitte beschreibe kurz:' + list"
    ),
    # A9b) "Strategische Empfehlungen?" heading alone (with ?)
    BoilerplatePattern(
        pattern=r'(?is)<h[1-6][^>]*>\s*Strategische\s+Empfehlungen\s*\?\s*</h[1-6]>',
        action="drop",
        description="PROMPT_STRATEGISCHE_EMPFEHLUNGEN_HEADING_Q: 'Strategische Empfehlungen?' heading with question mark"
    ),
    # A10) Generic "Bitte beschreibe kurz:" standalone (with optional ? before)
    BoilerplatePattern(
        pattern=r'(?im)^\s*\??\s*Bitte\s+beschreibe?\s+kurz\s*:?\s*$',
        action="drop",
        description="PROMPT_BITTE_BESCHREIBE_STANDALONE: Standalone 'Bitte beschreibe kurz:'"
    ),
    # A10b) <p>Bitte beschreibe kurz:</p> paragraph block
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*Bitte\s+beschreibe?\s+kurz\s*:?\s*</p>',
        action="drop",
        description="PROMPT_BITTE_BESCHREIBE_P: 'Bitte beschreibe kurz:' paragraph"
    ),
    # A11) "Wenn du magst" chatty sentences (outside code blocks)
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*Wenn\s+du\s+magst[^<]*</p>',
        action="drop",
        description="CHATTY_WENN_DU_MAGST_P: 'Wenn du magst...' paragraph"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<li[^>]*>\s*Wenn\s+du\s+magst[^<]*</li>',
        action="drop",
        description="CHATTY_WENN_DU_MAGST_LI: 'Wenn du magst...' list item"
    ),
    BoilerplatePattern(
        pattern=r'(?im)^\s*Wenn\s+du\s+magst\s*,.*$',
        action="drop",
        description="CHATTY_WENN_DU_MAGST_LINE: 'Wenn du magst,' line"
    ),
    # A12) "Falls du möchtest" / "Wenn du möchtest" variants
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*(?:Falls|Wenn)\s+du\s+m[öo]chtest[^<]*</p>',
        action="drop",
        description="CHATTY_FALLS_DU_MOECHTEST_P: 'Falls/Wenn du möchtest...' paragraph"
    ),
    # A13) Prompt leak with "?" before description
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*\?\s*Bitte\s+beschreibe?\s+kurz[^<]*</p>',
        action="drop",
        description="PROMPT_QUESTION_BITTE_BESCHREIBE: '? Bitte beschreibe kurz' paragraph"
    ),

    # -----------------------------------------------------------------
    # TASK 3 (SOLO Final Polish): "Bitte nenne kurz" Leak Patterns
    # -----------------------------------------------------------------
    # A14) "Bitte nenne kurz" + list block
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*Bitte\s+nenne?\s+kurz[:\s]*[^<]*</p>(?:\s*<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>)?',
        action="drop",
        description="PROMPT_BITTE_NENNE_BLOCK: 'Bitte nenne kurz' with list"
    ),
    # A14b) Standalone "Bitte nenne kurz:" without HTML
    BoilerplatePattern(
        pattern=r'(?im)^\s*Bitte\s+nenne?\s+kurz\s*:?\s*$',
        action="drop",
        description="PROMPT_BITTE_NENNE_STANDALONE: Standalone 'Bitte nenne kurz:'"
    ),
    # A14c) "Bitte nennen Sie kurz" (formal variant)
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*Bitte\s+nennen\s+Sie\s+kurz[:\s]*[^<]*</p>(?:\s*<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>)?',
        action="drop",
        description="PROMPT_BITTE_NENNEN_SIE_BLOCK: 'Bitte nennen Sie kurz' with list"
    ),
    # A15) Combined "Wobei kann ich helfen? Bitte nenne kurz:" pattern
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*(?:Wobei|Wie)\s+kann\s+ich\s+(?:dir\s+)?helfen\?\s*Bitte\s+nenne?\s+kurz\s*:?\s*</p>\s*(?:<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>)?',
        action="drop",
        description="PROMPT_WOBEI_BITTE_NENNE_BLOCK: 'Wobei kann ich helfen? Bitte nenne kurz:' + list"
    ),
    # A15b) Text-only fallback for "Bitte nenne kurz"
    BoilerplatePattern(
        pattern=r'(?i)\bBitte\s+nenne?\s+kurz\s*:?\s*(?:\n|$)',
        action="drop",
        description="PROMPT_BITTE_NENNE_TEXT: 'Bitte nenne kurz:' text-only"
    ),
    # A15c) "? Bitte nenne kurz" with leading question mark
    BoilerplatePattern(
        pattern=r'(?is)<p[^>]*>\s*\?\s*Bitte\s+nenne?\s+kurz[^<]*</p>',
        action="drop",
        description="PROMPT_QUESTION_BITTE_NENNE: '? Bitte nenne kurz' paragraph"
    ),

    # -------------------------------------------------------------------------
    # B) Platzhalter in eckigen Klammern
    # -------------------------------------------------------------------------
    BoilerplatePattern(
        pattern=r'(?is)\[(?:\s*(?:platzhalter|hier\s+einf\u00fcgen|your\s+text|insert|placeholder|name|firma|datum|kundenname|firmenname)[^\]]*)\]',
        action="drop",
        description="BRACKET_PLACEHOLDER_GENERIC: Generic bracket placeholders"
    ),
    BoilerplatePattern(
        pattern=r'(?i)<p>\s*\[[^\]]{0,60}\]\s*</p>',
        action="drop",
        description="BRACKET_PLACEHOLDER_P: Paragraph with only bracket placeholder"
    ),
    BoilerplatePattern(
        pattern=r'(?i)\[___+\]',
        action="drop",
        description="BRACKET_UNDERLINE: [___] fill-in placeholder"
    ),
    BoilerplatePattern(
        pattern=r'(?i)\[\.\.\.\]',
        action="drop",
        description="BRACKET_ELLIPSIS: [...] placeholder"
    ),
    BoilerplatePattern(
        pattern=r'(?i)_{3,}',
        action="drop",
        description="BARE_UNDERLINE: ___ fill-in blank"
    ),

    # -------------------------------------------------------------------------
    # C) Unreplaced Template-Tokens
    # -------------------------------------------------------------------------
    BoilerplatePattern(
        pattern=r'(?s)\{\{\s*[^}]+\s*\}\}',
        action="drop",
        description="JINJA_MUSTACHE_TOKEN: {{variable}} tokens"
    ),
    BoilerplatePattern(
        pattern=r'(?s)\{%\s*[^%]+\s*%\}',
        action="drop",
        description="JINJA_BLOCK_TOKEN: {% block %} tokens"
    ),
    BoilerplatePattern(
        pattern=r'(?i)\$\{[^}]+\}',
        action="drop",
        description="DOLLAR_BRACE_TOKEN: ${variable} tokens"
    ),
    BoilerplatePattern(
        pattern=r'(?i)<%[^%]+%>',
        action="drop",
        description="ERB_TOKEN: <% erb %> tokens"
    ),

    # -------------------------------------------------------------------------
    # D) LLM Instruction/Meta Leaks
    # -------------------------------------------------------------------------
    BoilerplatePattern(
        pattern=r'(?is)<p>\s*(?:Hinweis|Note|Anmerkung):\s*(?:Dies|Das|This)\s+ist\s+(?:ein|a|nur\s+ein)\s+(?:Beispiel|Example|Muster|Template)[^<]*</p>',
        action="drop",
        description="EXAMPLE_NOTE_LEAK: 'This is an example' notes"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<p>\s*\[(?:TODO|FIXME|XXX|TBD|DRAFT|WIP)[^\]]*\]\s*</p>',
        action="drop",
        description="TODO_MARKER: [TODO] placeholders"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<!--\s*(?:TODO|FIXME|XXX|NOTE|DRAFT)[^>]*-->',
        action="drop",
        description="HTML_COMMENT_TODO: HTML comment TODOs"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<p>\s*\*\*(?:INTERNAL|DRAFT|DO\s+NOT\s+PUBLISH)[^*]*\*\*\s*</p>',
        action="drop",
        description="INTERNAL_MARKER: **INTERNAL** markers"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<p>\s*(?:SYSTEM|ASSISTANT|USER):\s*[^<]*</p>',
        action="drop",
        description="ROLE_PREFIX_LEAK: SYSTEM:/ASSISTANT:/USER: prefixes"
    ),

    # -------------------------------------------------------------------------
    # E) Navigation/UI Artifacts
    # -------------------------------------------------------------------------
    BoilerplatePattern(
        pattern=r'(?is)<nav[^>]*>.*?</nav>',
        action="drop",
        description="NAV_BLOCK: Navigation blocks"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<(?:button|input)[^>]*(?:type="(?:submit|button)")?[^>]*>.*?</(?:button|input)>',
        action="drop",
        description="BUTTON_INPUT: Button/input elements"
    ),
    BoilerplatePattern(
        pattern=r'(?is)<a[^>]*(?:href="#"|onclick)[^>]*>(?:Zur\u00fcck|Back|Weiter|Next|Abbrechen|Cancel)</a>',
        action="drop",
        description="NAV_LINK: Navigation links"
    ),

    # -------------------------------------------------------------------------
    # F) Empty/Whitespace Containers
    # -------------------------------------------------------------------------
    BoilerplatePattern(
        pattern=r'(?s)<p>\s*</p>',
        action="drop",
        description="EMPTY_P: Empty paragraphs"
    ),
    BoilerplatePattern(
        pattern=r'(?s)<div[^>]*>\s*</div>',
        action="drop",
        description="EMPTY_DIV: Empty divs"
    ),
    BoilerplatePattern(
        pattern=r'(?s)<span[^>]*>\s*</span>',
        action="drop",
        description="EMPTY_SPAN: Empty spans"
    ),
    BoilerplatePattern(
        pattern=r'(?s)<li>\s*</li>',
        action="drop",
        description="EMPTY_LI: Empty list items"
    ),
    BoilerplatePattern(
        pattern=r'(?s)<ul>\s*</ul>',
        action="drop",
        description="EMPTY_UL: Empty unordered lists"
    ),
    BoilerplatePattern(
        pattern=r'(?s)<ol>\s*</ol>',
        action="drop",
        description="EMPTY_OL: Empty ordered lists"
    ),

    # -------------------------------------------------------------------------
    # G) Duplicate/Repeated Boilerplate
    # -------------------------------------------------------------------------
    BoilerplatePattern(
        pattern=r'(?is)(<p>[^<]{50,}</p>)\s*\1',
        action="replace",
        replacement=r'\1',
        description="CONSECUTIVE_DUP_P: Consecutive duplicate paragraphs"
    ),
    BoilerplatePattern(
        pattern=r'(?is)(<li>[^<]{30,}</li>)\s*\1',
        action="replace",
        replacement=r'\1',
        description="CONSECUTIVE_DUP_LI: Consecutive duplicate list items"
    ),
]


def sanitize_template_phrases(html: str) -> Tuple[str, int]:
    """
    Fix A: Remove prompt artifacts and placeholder texts.

    Args:
        html: HTML content to sanitize

    Returns:
        Tuple of (sanitized_html, removed_count)
    """
    if not html:
        return html, 0

    result = html
    removed_count = 0

    for bp in BOILERPLATE_PATTERNS:
        try:
            pattern = re.compile(bp.pattern, re.IGNORECASE | re.DOTALL)
            matches = pattern.findall(result)
            if matches:
                removed_count += len(matches)
                if bp.action == "drop":
                    result = pattern.sub("", result)
                else:  # replace
                    result = pattern.sub(bp.replacement, result)
                log.debug(
                    "[FIX-A] Removed %d instances: %s",
                    len(matches), bp.description
                )
        except re.error as e:
            log.warning("[FIX-A] Regex error for pattern '%s': %s", bp.pattern[:50], e)

    # Clean up empty paragraphs left behind
    result = re.sub(r"<p>\s*</p>", "", result)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result, removed_count


# =============================================================================
# FIX B: SIZE_MISMATCH - Persona Language Enforcement
# =============================================================================

# Enterprise → Simple term mappings for SOLO
SOLO_TERM_REPLACEMENTS: Dict[str, str] = {
    # Architecture/Technical terms
    "Architektur": "Aufbau",
    "KI-Architektur": "KI-Aufbau",
    "Stack": "Tool-Set",
    "KI-Stack": "KI-Werkzeugkasten",
    "Tech-Stack": "Werkzeugkasten",
    "Engine": "Modul",
    "Pipeline": "Ablauf",
    "Framework": "Rahmenwerk",
    "Infrastruktur": "Grundausstattung",
    # Governance/Compliance terms
    "Stakeholder": "Beteiligte",
    "Audit-Trail": "Protokoll",
    "Audit Trail": "Protokoll",
    "Audit": "Prüfung",
    "Audits": "Prüfungen",
    "Governance": "Spielregeln",
    "Compliance": "Regelkonformität",
    "Policy": "Richtlinie",
    "Rollout": "Einführung",
    "Deployment": "Bereitstellung",
    # TASK 2: Additional terms from validator warnings
    "Executive": "Kurzfassung",
    "Executive Summary": "Kurzfassung",
    "executive": "kurzfassung",
    "Layer": "Ebene",
    "Layers": "Ebenen",
    "layer": "ebene",
    "Plattform": "Lösung",
    "Plattformen": "Lösungen",
    "plattform": "lösung",
    "Baukasten": "Werkzeugkasten",
    "baukasten": "werkzeugkasten",
    # KPI/Dashboard terms
    "KPI-Dashboard": "Kennzahlen-Übersicht",
    "kpi-dashboard": "kennzahlen-übersicht",
    "Dashboard": "Übersicht",
    "Metriken": "Kennzahlen",
    "Analytics": "Auswertungen",
    # Process terms
    "Workflow-Automation": "Automatisierung",
    "Orchestrierung": "Koordination",
    "Skalierung": "Wachstum",
    "skalierbar": "erweiterbar",
    "Enterprise": "größere Firma",
    "enterprise": "größere firma",
    "enterprise-grade": "professionell",
    # Team/Org terms
    "Team-Meeting": "Besprechung",
    "Briefing": "Einweisung",
    "Onboarding": "Einarbeitung",
    "Change Management": "Veränderungsprozess",
}

# Extended SOLO term replacements (TASK 2: Comprehensive mapping)
SOLO_TERM_REPLACEMENTS_EXTENDED: Dict[str, str] = {
    # TASK 2 (FINAL FIX): Phrase-level mappings (must come first for priority)
    "Executive Summary & Kurzurteil": "Kurzfassung & Bewertung",
    "Executive Summary und Kurzurteil": "Kurzfassung und Bewertung",
    "EXECUTIVE SUMMARY": "KURZFASSUNG",
    "Executive Summary": "Kurzfassung",
    "executive summary": "kurzfassung",
    # Additional mappings from TASK 2 specification
    "Governance": "Spielregeln",
    "governance": "spielregeln",
    "GOVERNANCE": "SPIELREGELN",
    "Executive": "Kurzfassung",
    "executive": "kurzfassung",
    "EXECUTIVE": "KURZFASSUNG",
    "Audit": "Prüfung",
    "audit": "prüfung",
    "Audits": "Prüfungen",
    "Audit-Trail": "Protokoll",
    "audit-trail": "protokoll",
    "Rollout": "Einführung",
    "rollout": "einführung",
    "Layer": "Ebene",
    "layer": "ebene",
    "Layers": "Ebenen",
    "Enterprise": "größere Firma",
    "enterprise": "größere firma",
    "Blueprint": "Vorlage",
    "blueprint": "vorlage",
    "Blueprints": "Vorlagen",
    "Framework": "Vorgehensrahmen",
    "framework": "vorgehensrahmen",
    "Frameworks": "Vorgehensrahmen",
    "KPI-Dashboard": "Kennzahlen-Übersicht",
    "kpi-dashboard": "kennzahlen-übersicht",
    "Operating Model": "Arbeitsmodell",
    "operating model": "arbeitsmodell",
    "Compliance": "Regelkonformität",
    "compliance": "regelkonformität",
    # TASK 2: Additional terms from validator warnings
    "Architektur": "Aufbau",
    "architektur": "aufbau",
    "Stakeholder": "Beteiligte",
    "stakeholder": "beteiligte",
    "Plattform": "Lösung",
    "plattform": "lösung",
    "Skalierung": "Wachstum",
    "skalierung": "wachstum",
    "Engine": "Modul",
    "engine": "modul",
    "Baukasten": "Werkzeugkasten",
    "baukasten": "werkzeugkasten",
    # Additional enterprise terms
    "Konzern": "größere Firma",
    "konzern": "größere firma",
    "Konzerne": "größere Firmen",
}

# SOLO Blacklist Terms (TASK 2: Hard blacklist for SOLO segment)
SOLO_BLACKLIST_TERMS: List[str] = [
    "Governance",
    "Executive",
    "Audit",
    "Rollout",
    "Layer",
    "Enterprise",
    "Blueprint",
    "KPI-Dashboard",
    "Operating Model",
    "Compliance",
    "Stakeholder",
    "Architektur",
    "Framework",
    "Pipeline",
    "Deployment",
    "Konzern",
]

# Fallback replacements for blacklist terms that slip through
SOLO_BLACKLIST_FALLBACKS: Dict[str, str] = {
    "Governance": "Spielregeln",
    "Executive": "Kurzfassung",
    "Audit": "Prüfung",
    "Rollout": "Einführung",
    "Layer": "Ebene",
    "Enterprise": "größere Firma",
    "Blueprint": "Vorlage",
    "KPI-Dashboard": "Kennzahlen-Übersicht",
    "Operating Model": "Arbeitsmodell",
    "Compliance": "Regelkonformität",
    "Stakeholder": "Beteiligte",
    "Architektur": "Aufbau",
    "Framework": "Vorgehensrahmen",
    "Pipeline": "Ablauf",
    "Deployment": "Bereitstellung",
    "Konzern": "größere Firma",
    # TASK 2: Additional fallbacks
    "Plattform": "Lösung",
    "Skalierung": "Wachstum",
    "Engine": "Modul",
    "Baukasten": "Werkzeugkasten",
    "Audit-Trail": "Protokoll",
}

# Patterns to remove entirely for SOLO (too complex)
SOLO_REMOVE_PATTERNS: List[str] = [
    r"(?:unternehmensweite|organisationsweite)\s+(?:Governance|Compliance|Audit)",
    r"(?:Enterprise|Multi-Team)\s+(?:Architektur|Rollout|Deployment)",
    r"(?:Skalierung|Scaling)\s+(?:auf|für)\s+(?:mehrere|viele)\s+(?:Teams|Abteilungen)",
]

# =============================================================================
# TASK 3: Business-Case Label Localization (English → German)
# =============================================================================

BUSINESS_CASE_LABEL_LOCALIZATION_DE: Dict[str, str] = {
    # Primary labels
    "Payback Progress": "Amortisations-Fortschritt",
    "payback progress": "Amortisations-Fortschritt",
    "Payback progress": "Amortisations-Fortschritt",
    "Time Savings Hours": "Zeitersparnis (Std.)",
    "Time Savings (Hours)": "Zeitersparnis (Stunden)",
    "time savings hours": "Zeitersparnis (Std.)",
    "Time Savings/Month": "Zeitersparnis/Monat",
    "Time Savings (hrs)": "Zeitersparnis (Std.)",
    "Monthly Savings": "Monatliche Einsparung",
    "monthly savings": "monatliche Einsparung",
    "Monthly Savings (€)": "Monatliche Ersparnis (€)",
    "Annual Savings": "Jährliche Einsparung",
    "annual savings": "jährliche Einsparung",
    # Secondary labels
    "Payback Period": "Amortisationszeitraum",
    "payback period": "Amortisationszeitraum",
    "ROI Details": "ROI-Details",
    "ROI Comparison": "ROI-Vergleich",
    "Expected Trend": "Erwarteter Verlauf",
    "12-Month Trend": "12-Monats-Trend",
    # Contextual savings
    "Cost Savings": "Kosteneinsparung",
    "cost savings": "Kosteneinsparung",
    "Savings": "Einsparung",
}


# =============================================================================
# TASK D (P1 optional): ROI as Ranges/Qualitative for SOLO
# =============================================================================
# For SOLO segment, convert exact ROI % values to qualitative ranges
# to avoid overly precise numbers that may seem unrealistic.

# ROI value ranges and their qualitative descriptions (German)
ROI_QUALITATIVE_RANGES_DE = [
    (300, "sehr hoch (über 300%)"),
    (200, "hoch (200-300%)"),
    (150, "gut (150-200%)"),
    (100, "solide (100-150%)"),
    (50, "moderat (50-100%)"),
    (0, "gering (unter 50%)"),
]


def format_roi_span(roi_value: float, lang: str = "de") -> str:
    """
    TASK D: Convert exact ROI % to qualitative range/span.

    For SOLO segment, replaces exact ROI numbers with ranges
    to make the numbers more approachable and realistic.

    Args:
        roi_value: ROI as percentage (e.g., 200.0 for 200%)
        lang: Language code (currently only 'de' supported)

    Returns:
        Qualitative ROI description like "hoch (200-300%)"

    Examples:
        >>> format_roi_span(250.0)
        'hoch (200-300%)'
        >>> format_roi_span(75.0)
        'moderat (50-100%)'
    """
    if lang != "de":
        # For non-German, return the numeric value for now
        return f"{roi_value:.0f}%"

    for threshold, description in ROI_QUALITATIVE_RANGES_DE:
        if roi_value >= threshold:
            return description

    return "gering (unter 50%)"


def sanitize_roi_for_solo(html: str) -> Tuple[str, int]:
    """
    TASK D: Convert exact ROI % values to qualitative ranges in SOLO HTML.

    Finds patterns like "ROI: 250%" or "ROI von 200%" and replaces
    with qualitative descriptions for SOLO.

    Args:
        html: HTML content to process

    Returns:
        Tuple of (processed_html, replacements_count)

    Example patterns matched:
        - "ROI: 200%"
        - "ROI von 150%"
        - "200% ROI"
        - "ROI 12M: 180%"
    """
    if not html:
        return html, 0

    result = html
    replacement_count = 0

    # Pattern for ROI followed by percentage
    roi_patterns = [
        # "ROI: 200%" or "ROI von 200%" or "ROI 200%"
        (r'ROI[\s:]*(?:von\s+)?(\d+(?:[.,]\d+)?)\s*%', r'ROI: {qual}'),
        # "200% ROI" - percentage before ROI
        (r'(\d+(?:[.,]\d+)?)\s*%\s*ROI', r'{qual} ROI'),
        # "ROI 12M: 200%" - with 12M suffix
        (r'ROI\s*(?:12M|12\s*M)[\s:]*(\d+(?:[.,]\d+)?)\s*%', r'ROI 12M: {qual}'),
    ]

    for pattern, replacement_template in roi_patterns:
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        for match in reversed(matches):  # Process in reverse to maintain positions
            try:
                roi_str = match.group(1).replace(',', '.')
                roi_val = float(roi_str)
                qual = format_roi_span(roi_val)
                replacement = replacement_template.format(qual=qual)
                result = result[:match.start()] + replacement + result[match.end():]
                replacement_count += 1
            except (ValueError, IndexError):
                continue

    if replacement_count > 0:
        log.info("[TASK-D] SOLO ROI: Converted %d exact ROI values to qualitative ranges", replacement_count)

    return result, replacement_count


def enforce_persona_language(
    html: str,
    segment: Literal["solo", "team", "kmu"]
) -> Tuple[str, int]:
    """
    Fix B: Enforce persona-appropriate language.

    For SOLO: Replace enterprise terms with simpler alternatives,
              then enforce blacklist with fallback replacements.
    For TEAM/KMU: Keep B2B standard tone.

    Args:
        html: HTML content to process
        segment: Target segment (solo, team, kmu)

    Returns:
        Tuple of (processed_html, replacement_count)
    """
    if not html:
        return html, 0

    if segment != "solo":
        return html, 0  # No changes for team/kmu

    result = html
    replacement_count = 0

    # Step 1: Apply primary term replacements (case-insensitive, preserve case)
    for enterprise_term, simple_term in SOLO_TERM_REPLACEMENTS.items():
        pattern = re.compile(re.escape(enterprise_term), re.IGNORECASE)
        matches = pattern.findall(result)
        if matches:
            replacement_count += len(matches)

            def replace_preserve_case(m: re.Match) -> str:
                original = m.group(0)
                if original[0].isupper():
                    return simple_term[0].upper() + simple_term[1:]
                return simple_term.lower()

            result = pattern.sub(replace_preserve_case, result)

    # Step 2: Apply extended term replacements (TASK 2)
    for enterprise_term, simple_term in SOLO_TERM_REPLACEMENTS_EXTENDED.items():
        pattern = re.compile(re.escape(enterprise_term), re.IGNORECASE)
        matches = pattern.findall(result)
        if matches:
            replacement_count += len(matches)

            def replace_preserve_case_ext(m: re.Match) -> str:
                original = m.group(0)
                if not simple_term:  # Empty replacement means remove
                    return ""
                if original[0].isupper():
                    return simple_term[0].upper() + simple_term[1:]
                return simple_term.lower()

            result = pattern.sub(replace_preserve_case_ext, result)

    # Step 3: Remove overly complex patterns for SOLO
    for remove_pattern in SOLO_REMOVE_PATTERNS:
        try:
            pattern = re.compile(remove_pattern, re.IGNORECASE)
            before_len = len(result)
            result = pattern.sub("", result)
            if len(result) < before_len:
                replacement_count += 1
        except re.error:
            pass

    # Step 4: SOLO Blacklist Guard (TASK 2) - catch any remaining blacklist terms
    result, blacklist_fixes = _enforce_solo_blacklist(result)
    replacement_count += blacklist_fixes

    if replacement_count > 0:
        log.info("[FIX-B] SOLO persona: %d term replacements applied", replacement_count)

    return result, replacement_count


def _enforce_solo_blacklist(html: str) -> Tuple[str, int]:
    """
    TASK 2: Enforce SOLO blacklist - replace any remaining blacklist terms.

    Runs AFTER the primary replacements as a safety net.
    TASK 4 (FINAL FIX): Properly handles ALL-CAPS (EXECUTIVE → KURZFASSUNG).

    Args:
        html: HTML content to check

    Returns:
        Tuple of (cleaned_html, fixes_applied)
    """
    if not html:
        return html, 0

    result = html
    fixes_applied = 0
    replacement_log: list[str] = []  # TASK 5: Track replacements for detailed logging

    for term in SOLO_BLACKLIST_TERMS:
        # Case-insensitive search for the term
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)

        def replace_with_case(m: re.Match[str]) -> str:
            """Replace match preserving case: ALL-CAPS, Title Case, or lowercase."""
            nonlocal fixes_applied
            matched = m.group(0)
            fallback = SOLO_BLACKLIST_FALLBACKS.get(term, "")

            if not fallback:
                fixes_applied += 1
                replacement_log.append(f"REMOVED: '{matched}'")
                return ""

            # Determine case pattern of the matched term
            if matched.isupper():
                # ALL-CAPS: EXECUTIVE → KURZFASSUNG
                replacement = fallback.upper()
            elif matched.islower():
                # all lowercase: executive → kurzfassung
                replacement = fallback.lower()
            elif matched[0].isupper():
                # Title Case: Executive → Kurzfassung
                replacement = fallback[0].upper() + fallback[1:].lower() if len(fallback) > 1 else fallback.upper()
            else:
                replacement = fallback

            fixes_applied += 1
            replacement_log.append(f"'{matched}' → '{replacement}'")
            log.debug(
                "[FIX-B-BLACKLIST] Replaced SOLO blacklist term '%s' with '%s'",
                matched, replacement
            )
            return replacement

        result = pattern.sub(replace_with_case, result)

    # Clean up any double spaces or empty patterns left behind
    result = re.sub(r'\s{2,}', ' ', result)
    result = re.sub(r'<p>\s*</p>', '', result)

    if fixes_applied > 0:
        # TASK 5: Enhanced logging with detailed replacement summary
        log.info(
            "[FIX-B-BLACKLIST] Applied %d SOLO blacklist fixes: %s",
            fixes_applied,
            "; ".join(replacement_log[:5]) + ("..." if len(replacement_log) > 5 else "")
        )

    return result, fixes_applied


def localize_business_case_labels_de(html: str) -> Tuple[str, int]:
    """
    TASK 3: Localize business-case labels from English to German.

    Replaces English labels like "Payback Progress", "Time Savings Hours",
    "Monthly Savings" with German equivalents.

    Args:
        html: HTML content to process

    Returns:
        Tuple of (localized_html, replacements_made)
    """
    if not html:
        return html, 0

    result = html
    replacements_made = 0

    # Apply label localizations (exact match, case-sensitive for proper labels)
    for en_label, de_label in BUSINESS_CASE_LABEL_LOCALIZATION_DE.items():
        if en_label in result:
            count = result.count(en_label)
            result = result.replace(en_label, de_label)
            replacements_made += count
            log.debug(
                "[LOCALIZE-BC] Replaced '%s' → '%s' (%d times)",
                en_label, de_label, count
            )

    if replacements_made > 0:
        log.info("[LOCALIZE-BC] Localized %d business-case labels to German", replacements_made)

    return result, replacements_made


# =============================================================================
# FIX C: REDUNDANCY_DETECTED - Deduplication
# =============================================================================

@dataclass
class RedundancyStats:
    """Statistics from redundancy reduction."""
    blocks_removed: int = 0
    chars_reduced: int = 0
    sections_affected: List[str] = field(default_factory=list)


def _normalize_for_fingerprint(text: str) -> str:
    """
    Normalize text for fingerprint comparison.

    - Lowercase
    - Collapse whitespace
    - Remove punctuation
    - Normalize numbers to #
    """
    if not text:
        return ""

    result = text.lower()
    result = re.sub(r"\s+", " ", result)
    # Remove punctuation including German quotes
    result = re.sub(r'[.,;:!?\"\'\u201e\u201c\u201a\u2018\u00bb\u00ab\-\u2013\u2014]', "", result)
    result = re.sub(r"\d+(?:[.,]\d+)?", "#", result)
    return result.strip()


def _extract_blocks(html: str) -> List[Tuple[str, str, int, int]]:
    """
    Extract text blocks from HTML.

    Returns list of (tag, content, start, end) tuples.
    """
    blocks: List[Tuple[str, str, int, int]] = []

    # Match paragraphs, list items, and divs with text
    patterns = [
        (r"<p[^>]*>(.*?)</p>", "p"),
        (r"<li[^>]*>(.*?)</li>", "li"),
        (r"<div[^>]*class=\"[^\"]*(?:callout|box|card)[^\"]*\"[^>]*>(.*?)</div>", "div"),
    ]

    for pattern, tag in patterns:
        for m in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
            content = re.sub(r"<[^>]+>", "", m.group(1))  # Strip inner HTML
            content = content.strip()
            if len(content) >= 20:  # Minimum content length
                blocks.append((tag, content, m.start(), m.end()))

    return blocks


def reduce_redundancy(
    sections: Dict[str, str],
    *,
    min_chars: int = 160,
    similarity_threshold: float = 0.92
) -> Tuple[Dict[str, str], RedundancyStats]:
    """
    Fix C: Reduce redundant content across sections.

    Args:
        sections: Dict of section_name -> HTML content
        min_chars: Minimum block length to consider for deduplication
        similarity_threshold: Similarity threshold for near-duplicates (0-1)

    Returns:
        Tuple of (processed_sections, stats)
    """
    stats = RedundancyStats()
    result: Dict[str, str] = {}
    seen_fingerprints: Dict[str, str] = {}  # fingerprint -> first section

    # Process sections in order (earlier sections have priority)
    for section_name, html in sections.items():
        if not html:
            result[section_name] = html
            continue

        processed = html
        section_removed = 0
        original_len = len(html)

        # Extract blocks from this section
        blocks = _extract_blocks(processed)

        # Track blocks to remove (by position, reverse order for safe removal)
        removals: List[Tuple[int, int, str]] = []  # (start, end, reason)

        for tag, content, start, end in blocks:
            if len(content) < min_chars:
                continue

            fingerprint = _normalize_for_fingerprint(content)
            fp_hash = hashlib.md5(fingerprint.encode()).hexdigest()[:16]

            if fp_hash in seen_fingerprints:
                first_section = seen_fingerprints[fp_hash]
                if first_section != section_name:
                    # Cross-section duplicate
                    removals.append((start, end, f"duplicate from {first_section}"))
                    log.debug(
                        "[FIX-C] Cross-section duplicate: %s (first in %s)",
                        content[:50], first_section
                    )
            else:
                seen_fingerprints[fp_hash] = section_name

        # Also check for intra-section duplicates
        section_fps: Dict[str, int] = {}
        for tag, content, start, end in blocks:
            if len(content) < min_chars:
                continue

            fingerprint = _normalize_for_fingerprint(content)
            fp_hash = hashlib.md5(fingerprint.encode()).hexdigest()[:16]

            if fp_hash in section_fps:
                # Intra-section duplicate
                if (start, end, f"duplicate from {section_name}") not in removals:
                    removals.append((start, end, "intra-section duplicate"))
            else:
                section_fps[fp_hash] = start

        # Remove duplicates (reverse order to preserve positions)
        removals.sort(key=lambda x: x[0], reverse=True)
        for start, end, reason in removals:
            processed = processed[:start] + processed[end:]
            section_removed += 1

        # Clean up empty elements
        processed = re.sub(r"<p>\s*</p>", "", processed)
        processed = re.sub(r"<li>\s*</li>", "", processed)
        processed = re.sub(r"<ul>\s*</ul>", "", processed)
        processed = re.sub(r"<ol>\s*</ol>", "", processed)

        result[section_name] = processed

        if section_removed > 0:
            stats.blocks_removed += section_removed
            stats.chars_reduced += original_len - len(processed)
            stats.sections_affected.append(section_name)
            log.info(
                "[FIX-C] Section '%s': removed %d blocks, -%d chars",
                section_name, section_removed, original_len - len(processed)
            )

    return result, stats


# =============================================================================
# FIX D: ROI_PROHIBITED - ROI Rules Enforcement
# =============================================================================

# Sections where ROI percentages are prohibited
ROI_PROHIBITED_SECTIONS: Set[str] = {
    "RECOMMENDATIONS_HTML",
    "recommendations",
    "strategische_empfehlungen",
    "empfehlungen",
    "QUICK_WINS_HTML",
    "quick_wins",
}

# Pattern to match ROI percentages
ROI_PERCENT_PATTERN = re.compile(
    r"\b(?:ROI|Rendite|Return)[:\s]+(?:ca\.?\s*)?\d+(?:[.,]\d+)?\s*%",
    re.IGNORECASE
)

# Alternative pattern for standalone percentages with ROI context
ROI_CONTEXT_PATTERN = re.compile(
    r"(?:erreichen|erzielen|erwarten|versprechen)\s+(?:ca\.?\s*)?\d+(?:[.,]\d+)?\s*%\s*(?:ROI|Rendite)",
    re.IGNORECASE
)


def enforce_roi_rules(sections: Dict[str, str]) -> Tuple[Dict[str, str], int]:
    """
    Fix D: Enforce ROI rules - no ROI percentages in recommendations.

    Args:
        sections: Dict of section_name -> HTML content

    Returns:
        Tuple of (processed_sections, violations_fixed)
    """
    result: Dict[str, str] = {}
    violations_fixed = 0

    for section_name, html in sections.items():
        if not html:
            result[section_name] = html
            continue

        # Only process prohibited sections
        section_lower = section_name.lower()
        is_prohibited = any(
            prohibited.lower() in section_lower
            for prohibited in ROI_PROHIBITED_SECTIONS
        )

        if not is_prohibited:
            result[section_name] = html
            continue

        processed = html

        # Remove ROI percentages
        for pattern in [ROI_PERCENT_PATTERN, ROI_CONTEXT_PATTERN]:
            matches = pattern.findall(processed)
            if matches:
                violations_fixed += len(matches)
                processed = pattern.sub(
                    "hohe Wirtschaftlichkeit (siehe Business Case)",
                    processed
                )
                log.info(
                    "[FIX-D] Removed %d ROI percentages from '%s'",
                    len(matches), section_name
                )

        result[section_name] = processed

    return result, violations_fixed


# =============================================================================
# FIX E: INCOMPLETE_SENTENCE - Trim Fragments
# =============================================================================

# Connectors that indicate incomplete sentence when at end
INCOMPLETE_CONNECTORS: Set[str] = {
    "und", "oder", "sowie", "inkl.", "inkl", "bzw.", "bzw",
    "mit", "für", "bei", "von", "zu", "zur", "zum",
    "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einen", "einem", "einer",
}

# Minimum tail length to keep (chars after last sentence end)
MIN_TAIL_CHARS = 30


def trim_incomplete_sentences(html: str) -> Tuple[str, int]:
    """
    Fix E: Trim incomplete sentence fragments from end of blocks.

    Args:
        html: HTML content to process

    Returns:
        Tuple of (processed_html, fragments_trimmed)
    """
    if not html:
        return html, 0

    fragments_trimmed = 0

    def trim_block_content(content: str) -> str:
        nonlocal fragments_trimmed

        if not content or len(content) < 20:
            return content

        # Find last sentence ending
        sentence_endings = [
            (content.rfind("."), "."),
            (content.rfind("!"), "!"),
            (content.rfind("?"), "?"),
            (content.rfind("…"), "…"),
        ]
        last_end = max((pos for pos, _ in sentence_endings), default=-1)

        if last_end == -1:
            return content  # No sentence ending found

        tail = content[last_end + 1:].strip()

        if len(tail) == 0:
            return content  # No tail

        if len(tail) < MIN_TAIL_CHARS:
            # Short tail - check if it ends with connector
            tail_words = tail.split()
            if tail_words:
                last_word = tail_words[-1].lower().rstrip(".,;:")
                if last_word in INCOMPLETE_CONNECTORS:
                    fragments_trimmed += 1
                    return content[:last_end + 1]

        # Check if tail ends with connector
        tail_words = tail.split()
        if tail_words:
            last_word = tail_words[-1].lower().rstrip(".,;:")
            if last_word in INCOMPLETE_CONNECTORS:
                fragments_trimmed += 1
                return content[:last_end + 1]

        return content

    # Process paragraphs
    def process_p(m: re.Match[str]) -> str:
        full_tag: str = m.group(0)
        content: str = m.group(1)
        trimmed = trim_block_content(content)
        return full_tag.replace(content, trimmed)

    result = re.sub(r"(<p[^>]*>)(.*?)(</p>)",
                    lambda m: str(m.group(1)) + trim_block_content(str(m.group(2))) + str(m.group(3)),
                    html, flags=re.DOTALL)

    if fragments_trimmed > 0:
        log.info("[FIX-E] Trimmed %d incomplete sentence fragments", fragments_trimmed)

    return result, fragments_trimmed


# =============================================================================
# FIX F: PAYBACK CONSISTENCY (PAYBACK_PATTERNS_DE)
# =============================================================================

@dataclass
class PaybackPattern:
    """Definition for a payback normalization pattern."""
    id: str
    pattern: str
    action: Literal["normalize", "remove", "flag"]
    replacement: str = ""
    description: str = ""


# PAYBACK_PATTERNS_DE - Comprehensive German Payback Pattern Registry
PAYBACK_PATTERNS_DE: List[PaybackPattern] = [
    # -------------------------------------------------------------------------
    # Decimal Normalization (3.5 → 3,5)
    # -------------------------------------------------------------------------
    PaybackPattern(
        id="PAYBACK_DECIMAL_DOT_TO_COMMA_MONTHS",
        pattern=r'(?i)(\d+)\.(\d+)\s*(Monat(?:e|en)?)',
        action="normalize",
        replacement=r'\1,\2 \3',
        description="Convert 3.5 Monate/Monaten → 3,5 Monate/Monaten"
    ),
    PaybackPattern(
        id="PAYBACK_DECIMAL_DOT_TO_COMMA_WEEKS",
        pattern=r'(?i)(\d+)\.(\d+)\s*(Woche(?:n)?)',
        action="normalize",
        replacement=r'\1,\2 \3',
        description="Convert 2.5 Wochen → 2,5 Wochen"
    ),

    # -------------------------------------------------------------------------
    # Progress Label Detection
    # -------------------------------------------------------------------------
    PaybackPattern(
        id="PAYBACK_PROGRESS_LABEL_SPAN",
        pattern=r'(?is)<span[^>]*>\s*Payback\s+Progress[:\s]*(\d+(?:[.,]\d+)?)\s*%?\s*</span>',
        action="flag",
        description="Payback Progress span (track for duplicate removal)"
    ),
    PaybackPattern(
        id="PAYBACK_PROGRESS_INLINE",
        pattern=r'(?i)Payback\s+Progress[:\s]+(\d+(?:[.,]\d+)?)\s*%',
        action="flag",
        description="Payback Progress inline (track for duplicate removal)"
    ),
    PaybackPattern(
        id="PROGRESS_100_STANDALONE",
        pattern=r'(?i)Progress[:\s]+100\s*%',
        action="flag",
        description="Progress: 100% standalone (track for duplicate removal)"
    ),

    # -------------------------------------------------------------------------
    # Payback Value Extraction
    # -------------------------------------------------------------------------
    PaybackPattern(
        id="PAYBACK_COLON_VALUE",
        pattern=r'(?i)Payback[:\s]+(\d+(?:[.,]\d+)?)\s*(?:Monat(?:e|en)?|Woche(?:n)?|months?|weeks?)',
        action="flag",
        description="Payback: X Monate/Monaten format"
    ),
    PaybackPattern(
        id="AMORTISATION_VALUE",
        pattern=r'(?i)Amortisation(?:szeit)?[:\s]+(\d+(?:[.,]\d+)?)\s*(?:Monat(?:e|en)?|Woche(?:n)?)',
        action="flag",
        description="Amortisation(szeit): X Monate/Monaten format"
    ),
    PaybackPattern(
        id="PAYBACK_PERIOD_VALUE",
        pattern=r'(?i)(\d+(?:[.,]\d+)?)\s*(?:Monat(?:e|en)?|Woche(?:n)?)\s+(?:Payback|Amortisation)',
        action="flag",
        description="X Monate/Monaten Payback format"
    ),
]

# Compiled patterns for payback extraction
PAYBACK_PATTERNS = [
    re.compile(r"Payback[:\s]+(\d+(?:[.,]\d+)?)\s*(?:Monat(?:e|en)?|months?)", re.IGNORECASE),
    re.compile(r"Amortisation(?:szeit)?[:\s]+(\d+(?:[.,]\d+)?)\s*(?:Monat(?:e|en)?|months?)", re.IGNORECASE),
    re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:Monat(?:e|en)?|months?)\s+(?:Payback|Amortisation)", re.IGNORECASE),
]

# Pattern for "Payback Progress 100%" duplicates
PAYBACK_PROGRESS_PATTERN = re.compile(
    r"(?:Payback\s+)?Progress[:\s]+100\s*%",
    re.IGNORECASE
)

# Pattern for decimal dot to comma normalization (handles Monat, Monate, Monaten, Woche, Wochen)
PAYBACK_DECIMAL_PATTERN = re.compile(
    r"(\d+)\.(\d+)\s*(Monat(?:e|en)?|Woche(?:n)?)",
    re.IGNORECASE
)


def enforce_payback_consistency(
    sections: Dict[str, str],
    canonical_payback_months: Optional[float] = None
) -> Tuple[Dict[str, str], int]:
    """
    Fix F: Enforce payback consistency and remove duplicates.

    Applies:
    1. Decimal normalization: 3.5 Monate → 3,5 Monate (German format)
    2. Duplicate "Payback Progress 100%" removal (keep first occurrence)
    3. Canonical payback value normalization if provided

    Args:
        sections: Dict of section_name -> HTML content
        canonical_payback_months: Canonical payback value if known

    Returns:
        Tuple of (processed_sections, fixes_applied)
    """
    result: Dict[str, str] = {}
    fixes_applied = 0

    # Track "Payback Progress 100%" occurrences
    progress_seen = False

    for section_name, html in sections.items():
        if not html:
            result[section_name] = html
            continue

        processed = html

        # Step 1: Normalize decimal format (3.5 → 3,5)
        decimal_matches = list(PAYBACK_DECIMAL_PATTERN.finditer(processed))
        if decimal_matches:
            # Replace from end to preserve positions
            for m in reversed(decimal_matches):
                old_val = m.group(0)
                new_val = PAYBACK_DECIMAL_PATTERN.sub(r'\1,\2 \3', old_val)
                if old_val != new_val:
                    processed = processed[:m.start()] + new_val + processed[m.end():]
                    fixes_applied += 1
                    log.debug("[FIX-F] Normalized decimal: %s → %s", old_val, new_val)

        # Step 2: Remove duplicate "Payback Progress 100%" (keep first)
        if "Progress" in processed and "100" in processed:
            matches = list(PAYBACK_PROGRESS_PATTERN.finditer(processed))
            if len(matches) > 1 or (matches and progress_seen):
                # Remove all but first (or all if already seen)
                for m in reversed(matches[1:] if not progress_seen else matches):
                    processed = processed[:m.start()] + processed[m.end():]
                    fixes_applied += 1
                    log.debug("[FIX-F] Removed duplicate Payback Progress 100%%")
            if matches and not progress_seen:
                progress_seen = True

        # Step 3: Normalize payback format if canonical value provided
        if canonical_payback_months is not None:
            canonical_str = f"{canonical_payback_months:.1f}".replace(".", ",") + " Monate"
            for pattern in PAYBACK_PATTERNS:
                if pattern.search(processed):
                    processed = pattern.sub(f"Payback: {canonical_str}", processed)
                    fixes_applied += 1

        result[section_name] = processed

    if fixes_applied > 0:
        log.info("[FIX-F] Applied %d payback consistency fixes", fixes_applied)

    return result, fixes_applied


# =============================================================================
# TASK 4: Payback Progress Label Sanitization (% removal + deduplication)
# =============================================================================

# Pattern to match "Payback Progress 100%" in various forms
_PAYBACK_PROGRESS_100_PATTERN = re.compile(
    r'Payback\s+Progress\s*:?\s*100\s*%',
    re.IGNORECASE
)

# Pattern to match any "Payback Progress X%" label
_PAYBACK_PROGRESS_PERCENT_PATTERN = re.compile(
    r'Payback\s+Progress\s*:?\s*\d+(?:[.,]\d+)?\s*%',
    re.IGNORECASE
)

# Pattern to find payback progress spans/divs for deduplication
_PAYBACK_PROGRESS_SPAN_PATTERN = re.compile(
    r'<span[^>]*>\s*Payback\s+Progress\s*:?\s*(\d+(?:[.,]\d+)?)\s*%\s*</span>',
    re.IGNORECASE | re.DOTALL
)

# TASK 1 (FINAL FIX): Pattern for split-span Payback Progress
# Matches: <span>Payback Progress</span><span>100%</span> and variants
_PAYBACK_PROGRESS_SPLIT_SPAN_PATTERN = re.compile(
    r'Payback\s*Progress\s*'                      # Label
    r'(?:</[^>]+>\s*<[^>]+>\s*)*'                  # Zero or more closing/opening tags
    r'(\d{1,3})\s*%',                             # Value with %
    re.IGNORECASE | re.DOTALL
)

# Pattern for split-span with full HTML wrapper (more precise)
_PAYBACK_PROGRESS_SPLIT_SPAN_FULL_PATTERN = re.compile(
    r'<span[^>]*>\s*Payback\s*Progress\s*</span>\s*'  # Label in span
    r'<span[^>]*>\s*(\d{1,3})\s*%?\s*</span>',        # Value in separate span
    re.IGNORECASE | re.DOTALL
)


def sanitize_payback_progress_labels(html: str) -> Tuple[str, int]:
    """
    TASK 4: Sanitize Payback Progress labels.

    1. Replace "Payback Progress 100%" → "Payback: erreicht"
    2. Replace "Payback Progress X%" → "Payback-Fortschritt: X" (no %)
    3. Remove duplicate payback progress labels (keep first occurrence)

    Args:
        html: HTML content to sanitize

    Returns:
        Tuple of (sanitized_html, fixes_applied)
    """
    if not html:
        return html, 0

    result = html
    fixes_applied = 0

    # TASK 1 (FINAL FIX): Step 0: Handle split-span Payback Progress first
    # Pattern: <span>Payback Progress</span><span>100%</span>
    def replace_split_span(m: re.Match[str]) -> str:
        nonlocal fixes_applied
        value = m.group(1)
        fixes_applied += 1
        if value == "100":
            log.debug("[TASK1-FINAL] Replaced split-span 'Payback Progress 100%%' → 'Payback: erreicht'")
            return "Payback: erreicht"
        log.debug("[TASK1-FINAL] Replaced split-span 'Payback Progress %s%%' → 'Payback-Fortschritt: %s'", value, value)
        return f"Payback-Fortschritt: {value}"

    # First try full span pattern (more precise)
    if _PAYBACK_PROGRESS_SPLIT_SPAN_FULL_PATTERN.search(result):
        result = _PAYBACK_PROGRESS_SPLIT_SPAN_FULL_PATTERN.sub(replace_split_span, result)

    # Then try generic split pattern
    if _PAYBACK_PROGRESS_SPLIT_SPAN_PATTERN.search(result):
        result = _PAYBACK_PROGRESS_SPLIT_SPAN_PATTERN.sub(replace_split_span, result)

    # Step 1: Replace "Payback Progress 100%" with "Payback: erreicht"
    if _PAYBACK_PROGRESS_100_PATTERN.search(result):
        count_100 = len(_PAYBACK_PROGRESS_100_PATTERN.findall(result))
        result = _PAYBACK_PROGRESS_100_PATTERN.sub("Payback: erreicht", result)
        fixes_applied += count_100
        log.debug("[TASK4] Replaced %d 'Payback Progress 100%%' → 'Payback: erreicht'", count_100)

    # Step 2: Replace remaining "Payback Progress X%" → "Payback-Fortschritt: X"
    def replace_progress_percent(m: re.Match[str]) -> str:
        nonlocal fixes_applied
        text: str = m.group(0)
        # Extract the number
        num_match = re.search(r'(\d+(?:[.,]\d+)?)', text)
        if num_match:
            value = num_match.group(1)
            fixes_applied += 1
            # Convert 100 to "erreicht"
            if value == "100":
                return "Payback: erreicht"
            return f"Payback-Fortschritt: {value}"
        return text

    result = _PAYBACK_PROGRESS_PERCENT_PATTERN.sub(replace_progress_percent, result)

    # Step 3: Remove duplicate payback progress labels (keep first)
    # Find all span-wrapped payback labels
    spans = list(_PAYBACK_PROGRESS_SPAN_PATTERN.finditer(result))
    if len(spans) > 1:
        # Keep first, remove rest (process in reverse to maintain positions)
        for span in reversed(spans[1:]):
            result = result[:span.start()] + result[span.end():]
            fixes_applied += 1
            log.debug("[TASK4] Removed duplicate payback progress span")

    # Also deduplicate "Payback: erreicht" if it appears multiple times
    erreicht_pattern = re.compile(r'Payback:\s*erreicht', re.IGNORECASE)
    erreicht_matches = list(erreicht_pattern.finditer(result))
    if len(erreicht_matches) > 1:
        # Keep first, remove rest
        for m in reversed(erreicht_matches[1:]):
            result = result[:m.start()] + result[m.end():]
            fixes_applied += 1
            log.debug("[TASK4] Removed duplicate 'Payback: erreicht'")

    # TASK 1 (FINAL FIX): Step 4: Replace any remaining standalone "Payback Progress" labels
    # This catches edge cases where the label exists without a value
    remaining_pp = re.compile(r'Payback\s+Progress(?!\s*-?\s*Fortschritt)', re.IGNORECASE)
    if remaining_pp.search(result):
        count_remaining = len(remaining_pp.findall(result))
        result = remaining_pp.sub("Payback-Status", result)
        fixes_applied += count_remaining
        log.debug("[TASK1-FINAL] Replaced %d remaining 'Payback Progress' → 'Payback-Status'", count_remaining)

    if fixes_applied > 0:
        log.info("[TASK4] Applied %d payback progress label fixes", fixes_applied)

    return result, fixes_applied


# =============================================================================
# FIX G: SEGMENT BUDGET LOGIC
# =============================================================================

# Section budgets by segment (max chars or max blocks)
SEGMENT_BUDGETS: Dict[str, Dict[str, int]] = {
    "solo": {
        "EXECUTIVE_SUMMARY_HTML": 2000,
        "QUICK_WINS_HTML": 1500,
        "ROADMAP_90D_HTML": 1200,
        "RECOMMENDATIONS_HTML": 1500,
        "RISKS_HTML": 1200,
        "BUSINESS_CASE_HTML": 2500,
        "_default": 1000,
    },
    "team": {
        "EXECUTIVE_SUMMARY_HTML": 3000,
        "QUICK_WINS_HTML": 2000,
        "ROADMAP_90D_HTML": 1800,
        "RECOMMENDATIONS_HTML": 2500,
        "RISKS_HTML": 1800,
        "BUSINESS_CASE_HTML": 4000,
        "_default": 1500,
    },
    "kmu": {
        "EXECUTIVE_SUMMARY_HTML": 4000,
        "QUICK_WINS_HTML": 2500,
        "ROADMAP_90D_HTML": 2500,
        "RECOMMENDATIONS_HTML": 3500,
        "RISKS_HTML": 2500,
        "BUSINESS_CASE_HTML": 5000,
        "_default": 2000,
    },
}


def apply_segment_budget(
    sections: Dict[str, str],
    segment: Literal["solo", "team", "kmu"]
) -> Tuple[Dict[str, str], int]:
    """
    Fix G: Apply segment-based budget limits.

    Shortens sections that exceed budget by:
    1. Removing redundant content first
    2. Trimming examples
    3. Keeping core statements

    Args:
        sections: Dict of section_name -> HTML content
        segment: Target segment

    Returns:
        Tuple of (processed_sections, sections_trimmed)
    """
    budgets = SEGMENT_BUDGETS.get(segment, SEGMENT_BUDGETS["team"])
    default_budget = budgets.get("_default", 1500)

    result: Dict[str, str] = {}
    sections_trimmed = 0

    for section_name, html in sections.items():
        if not html:
            result[section_name] = html
            continue

        budget = budgets.get(section_name, default_budget)
        current_len = len(html)

        if current_len <= budget:
            result[section_name] = html
            continue

        # Over budget - need to trim
        log.info(
            "[FIX-G] Section '%s' over budget: %d > %d chars",
            section_name, current_len, budget
        )

        processed = html

        # Strategy 1: Remove "nice-to-have" phrases
        nice_to_have_patterns = [
            r"<p>\s*(?:Beispiel(?:sweise)?|Zum Beispiel|Z\.B\.)[^<]*</p>",
            r"<p>\s*(?:Optional|Ergänzend)[^<]*</p>",
            r"<li>\s*(?:Optional|Ergänzend|ggf\.)[^<]*</li>",
        ]
        for pattern in nice_to_have_patterns:
            if len(processed) > budget:
                processed = re.sub(pattern, "", processed, flags=re.IGNORECASE)

        # Strategy 2: Shorten bullet lists (keep first 3-5 items)
        if len(processed) > budget:
            # Find all <li> items and keep only first N
            li_pattern = re.compile(r"<li[^>]*>.*?</li>", re.DOTALL)
            lists_found = list(li_pattern.finditer(processed))
            if len(lists_found) > 5:
                # Remove excess list items
                for li in reversed(lists_found[5:]):
                    processed = processed[:li.start()] + processed[li.end():]

        # Strategy 3: Truncate long paragraphs
        if len(processed) > budget:
            def truncate_long_p(m: re.Match[str]) -> str:
                content: str = str(m.group(2))
                if len(content) > 500:
                    # Find sentence boundary around 400 chars
                    end_pos = content.rfind(".", 300, 450)
                    if end_pos > 0:
                        return str(m.group(1)) + content[:end_pos + 1] + str(m.group(3))
                return str(m.group(0))

            processed = re.sub(
                r"(<p[^>]*>)(.*?)(</p>)",
                truncate_long_p,
                processed,
                flags=re.DOTALL
            )

        # Clean up
        processed = re.sub(r"<p>\s*</p>", "", processed)
        processed = re.sub(r"\n{3,}", "\n\n", processed)

        if len(processed) < current_len:
            sections_trimmed += 1
            log.info(
                "[FIX-G] Section '%s' trimmed: %d -> %d chars",
                section_name, current_len, len(processed)
            )

        result[section_name] = processed

    return result, sections_trimmed


# =============================================================================
# HEALING RESULT
# =============================================================================

@dataclass
class HealingResult:
    """Result of the healing pipeline."""
    sections: Dict[str, Any]  # Preserves original types (list, dict, etc.)
    template_phrases_removed: int = 0
    persona_replacements: int = 0
    redundancy_stats: Optional[RedundancyStats] = None
    roi_violations_fixed: int = 0
    fragments_trimmed: int = 0
    payback_fixes: int = 0
    sections_budget_trimmed: int = 0

    @property
    def total_fixes(self) -> int:
        """Total number of fixes applied."""
        return (
            self.template_phrases_removed +
            self.persona_replacements +
            (self.redundancy_stats.blocks_removed if self.redundancy_stats else 0) +
            self.roi_violations_fixed +
            self.fragments_trimmed +
            self.payback_fixes +
            self.sections_budget_trimmed
        )

    @property
    def stats(self) -> Dict[str, int]:
        """Return stats as dict for logging/metadata."""
        return {
            "total_fixes": self.total_fixes,
            "template_phrases_removed": self.template_phrases_removed,
            "persona_replacements": self.persona_replacements,
            "redundancy_blocks_removed": self.redundancy_stats.blocks_removed if self.redundancy_stats else 0,
            "roi_violations_fixed": self.roi_violations_fixed,
            "fragments_trimmed": self.fragments_trimmed,
            "payback_fixes": self.payback_fixes,
            "sections_budget_trimmed": self.sections_budget_trimmed,
        }


# =============================================================================
# MAIN HEALING PIPELINE (PRE-RENDER)
# =============================================================================

def _apply_fix_a_recursive(value: Any) -> Tuple[Any, int]:
    """Apply Fix A (template phrases) recursively to string leaves."""
    count = 0

    def heal_string(s: str) -> str:
        nonlocal count
        if not s or not s.strip():
            return s
        try:
            result, c = sanitize_template_phrases(s)
            count += c
            return result
        except Exception as e:
            log.warning("[FIX-A] Error healing string: %s", e)
            return s

    healed = _walk(value, heal_string)
    return healed, count


def _apply_fix_b_recursive(value: Any, segment: Literal["solo", "team", "kmu"]) -> Tuple[Any, int]:
    """Apply Fix B (persona language) recursively to string leaves."""
    count = 0

    def heal_string(s: str) -> str:
        nonlocal count
        if not s or not s.strip():
            return s
        try:
            result, c = enforce_persona_language(s, segment)
            count += c
            return result
        except Exception as e:
            log.warning("[FIX-B] Error healing string: %s", e)
            return s

    healed = _walk(value, heal_string)
    return healed, count


def _apply_fix_e_recursive(value: Any) -> Tuple[Any, int]:
    """Apply Fix E (incomplete sentences) recursively to string leaves."""
    count = 0

    def heal_string(s: str) -> str:
        nonlocal count
        if not s or not s.strip():
            return s
        try:
            result, c = trim_incomplete_sentences(s)
            count += c
            return result
        except Exception as e:
            log.warning("[FIX-E] Error healing string: %s", e)
            return s

    healed = _walk(value, heal_string)
    return healed, count


def _apply_fix_f_recursive(value: Any, canonical_payback: Optional[Decimal]) -> Tuple[Any, int]:
    """Apply Fix F (payback consistency) recursively to string leaves."""
    count = 0
    canonical_float = float(canonical_payback) if canonical_payback else None

    def heal_string(s: str) -> str:
        nonlocal count
        if not s or not s.strip():
            return s
        try:
            # Apply decimal normalization
            processed = s
            decimal_matches = list(PAYBACK_DECIMAL_PATTERN.finditer(processed))
            if decimal_matches:
                for m in reversed(decimal_matches):
                    old_val = m.group(0)
                    new_val = PAYBACK_DECIMAL_PATTERN.sub(r'\1,\2 \3', old_val)
                    if old_val != new_val:
                        processed = processed[:m.start()] + new_val + processed[m.end():]
                        count += 1
            return processed
        except Exception as e:
            log.warning("[FIX-F] Error healing string: %s", e)
            return s

    healed = _walk(value, heal_string)
    return healed, count


def heal_report_html(
    sections: Dict[str, Any],
    segment: Literal["solo", "team", "kmu", "SOLO", "TEAM", "KMU"],
    *,
    canonical_payback_months: Optional[Union[float, Decimal, str]] = None,
    skip_fixes: Optional[Set[str]] = None
) -> HealingResult:
    """
    Main healing pipeline for report HTML (PRE-RENDER).

    TYPE-SAFE: Recursively heals string leaves while preserving list/dict structures.
    Does NOT convert list/dict to strings.

    Runs all fixes A-G in sequence (UPDATED ORDER - TASK 6):
    1. TASK 1: canonicalize_segment() - normalize segment to SOLO/TEAM/KMU
    2. TASK 5: normalize_section_keys() - drop redundant keys (pilot_plan, roadmap)
    3. sanitize_template_phrases (Fix A) - recursive on all string leaves
    4. enforce_persona_language (Fix B) - recursive on all string leaves
    5. reduce_redundancy (Fix C) - on top-level HTML string sections only
    6. enforce_roi_rules (Fix D) - on top-level HTML string sections only
    7. enforce_payback_consistency (Fix F) - recursive on all string leaves
    8. TASK 4: sanitize_payback_progress_labels() - remove % from payback labels
    9. apply_segment_budget (Fix G) - on top-level HTML string sections only
    10. trim_incomplete_sentences (Fix E) - AFTER budget to catch fragments (TASK 6)

    Args:
        sections: Dict of section_name -> content (preserves types: list, dict, etc.)
        segment: Target segment (solo, team, kmu) - any case/synonym accepted
        canonical_payback_months: Optional canonical payback value (float, Decimal, or str)
        skip_fixes: Set of fix letters to skip (e.g., {"A", "C"})

    Returns:
        HealingResult with processed sections (same structure, types preserved)
    """
    skip = skip_fixes or set()

    # TASK 1: Canonicalize segment at the very beginning
    canonical_segment = canonicalize_segment(segment)
    # For internal use, convert to lowercase for existing logic compatibility
    segment_lower: Literal["solo", "team", "kmu"] = canonical_segment.lower()  # type: ignore

    # Parse canonical payback to Decimal for consistent handling
    canonical_payback = parse_payback_months(canonical_payback_months)

    # Start with a copy of the original sections (preserves types!)
    healed_sections: Dict[str, Any] = dict(sections)
    result = HealingResult(sections=healed_sections)

    log.info(
        "[HEALER] Starting heal_report_html (type-safe): segment=%s (canonical=%s), sections=%d, skip=%s",
        segment, canonical_segment, len(sections), skip
    )

    # TASK 5: Normalize section keys and drop redundant ones BEFORE other processing
    if "KEYS" not in skip:
        try:
            healed_sections, dropped_keys = normalize_section_keys(healed_sections, canonical_segment)
            if dropped_keys:
                log.info("[TASK5] Dropped %d redundant keys: %s", len(dropped_keys), dropped_keys)
        except Exception as e:
            log.warning("[TASK5] Error in key normalization: %s - skipping", e)

    # Fix A: Template phrases - RECURSIVE on all string leaves
    if "A" not in skip:
        for key in list(healed_sections.keys()):
            if _is_html_section_key(key):
                try:
                    healed_sections[key], count = _apply_fix_a_recursive(healed_sections[key])
                    result.template_phrases_removed += count
                except Exception as e:
                    log.warning("[FIX-A] Error in section '%s': %s - skipping", key, e)

    # Fix B: Persona language - RECURSIVE on all string leaves
    if "B" not in skip:
        for key in list(healed_sections.keys()):
            if _is_html_section_key(key):
                try:
                    healed_sections[key], count = _apply_fix_b_recursive(healed_sections[key], segment_lower)
                    result.persona_replacements += count
                except Exception as e:
                    log.warning("[FIX-B] Error in section '%s': %s - skipping", key, e)

    # Fix C: Redundancy reduction - on FLAT string sections only
    if "C" not in skip:
        try:
            string_sections = _extract_string_sections(healed_sections)
            if string_sections:
                healed_strings, result.redundancy_stats = reduce_redundancy(string_sections)
                healed_sections = _merge_healed_sections(healed_sections, healed_strings)
        except Exception as e:
            log.warning("[FIX-C] Error in redundancy reduction: %s - skipping", e)

    # Fix D: ROI rules - on FLAT string sections only
    if "D" not in skip:
        try:
            string_sections = _extract_string_sections(healed_sections)
            if string_sections:
                healed_strings, result.roi_violations_fixed = enforce_roi_rules(string_sections)
                healed_sections = _merge_healed_sections(healed_sections, healed_strings)
        except Exception as e:
            log.warning("[FIX-D] Error in ROI rules: %s - skipping", e)

    # Fix F: Payback consistency - RECURSIVE decimal normalization + FLAT for dedup/canonical
    if "F" not in skip:
        # Step 1: Recursive decimal normalization on all string leaves (handles nested lists/dicts)
        for key in list(healed_sections.keys()):
            if _is_html_section_key(key):
                try:
                    healed_sections[key], count = _apply_fix_f_recursive(healed_sections[key], canonical_payback)
                    result.payback_fixes += count
                except Exception as e:
                    log.warning("[FIX-F] Error in section '%s': %s - skipping", key, e)

        # Step 2: Flat section processing for duplicate progress removal and canonical replacement
        try:
            string_sections = _extract_string_sections(healed_sections)
            if string_sections:
                canonical_float = float(canonical_payback) if canonical_payback else None
                healed_strings, flat_fixes = enforce_payback_consistency(string_sections, canonical_float)
                healed_sections = _merge_healed_sections(healed_sections, healed_strings)
                result.payback_fixes += flat_fixes
        except Exception as e:
            log.warning("[FIX-F] Error in payback consistency (flat): %s - skipping", e)

    # TASK 4: Sanitize payback progress labels (remove %, deduplicate)
    if "F" not in skip:  # Part of Fix F family
        for key in list(healed_sections.keys()):
            if _is_html_section_key(key) and isinstance(healed_sections[key], str):
                try:
                    healed_sections[key], count = sanitize_payback_progress_labels(healed_sections[key])
                    result.payback_fixes += count
                except Exception as e:
                    log.warning("[TASK4] Error in section '%s': %s - skipping", key, e)

    # Fix G: Segment budget - on FLAT string sections only
    if "G" not in skip:
        try:
            string_sections = _extract_string_sections(healed_sections)
            if string_sections:
                healed_strings, result.sections_budget_trimmed = apply_segment_budget(string_sections, segment_lower)
                healed_sections = _merge_healed_sections(healed_sections, healed_strings)
        except Exception as e:
            log.warning("[FIX-G] Error in segment budget: %s - skipping", e)

    # Fix E: Incomplete sentences - RECURSIVE on all string leaves
    # TASK 6: Moved AFTER Fix G (Segment Budget) to catch fragments from budget trimming
    if "E" not in skip:
        for key in list(healed_sections.keys()):
            if _is_html_section_key(key):
                try:
                    healed_sections[key], count = _apply_fix_e_recursive(healed_sections[key])
                    result.fragments_trimmed += count
                except Exception as e:
                    log.warning("[FIX-E] Error in section '%s': %s - skipping", key, e)

    # Add healing flag to sections meta
    healed_sections["_redundancy_healed"] = "true"
    healed_sections["_healer_version"] = "1.2.0"  # Bumped version for TASK 1-6 changes
    healed_sections["_healer_segment"] = canonical_segment  # Use canonical form

    result.sections = healed_sections

    log.info(
        "[HEALER] Completed: total_fixes=%d (A=%d, B=%d, C=%d, D=%d, E=%d, F=%d, G=%d)",
        result.total_fixes,
        result.template_phrases_removed,
        result.persona_replacements,
        result.redundancy_stats.blocks_removed if result.redundancy_stats else 0,
        result.roi_violations_fixed,
        result.fragments_trimmed,
        result.payback_fixes,
        result.sections_budget_trimmed
    )

    return result


# =============================================================================
# POST-RENDER HEALING (Safety Net for Final HTML)
# =============================================================================

def heal_final_html(
    html: str,
    segment: Literal["solo", "team", "kmu", "SOLO", "TEAM", "KMU"] = "team",
    *,
    canonical_payback_months: Optional[Union[float, Decimal, str]] = None,
    localize_labels: bool = True,
    run_quality_check: bool = False,
) -> str:
    """
    POST-RENDER safety net: Heal the final rendered HTML string.

    This is a CONSERVATIVE healing pass that runs AFTER template rendering.
    It catches artifacts that were generated during rendering (e.g., from lists).

    Applies safe fixes that won't break HTML structure:
    - Fix A: Template/prompt artifacts removal (including Wobei soll/kann ich blocks)
    - Fix B: SOLO blacklist enforcement (for SOLO segment)
    - Fix F: Payback decimal normalization (3.5 → 3,5)
    - TASK 3: Business-case label localization (English → German)
    - TASK 4: Payback Progress label sanitization (remove %, deduplicate)
    - Consecutive duplicate removal (conservative)

    Args:
        html: Final rendered HTML string
        segment: Target segment (for segment-specific healing) - any case accepted
        canonical_payback_months: Optional canonical payback value
        localize_labels: If True, localize English BC labels to German
        run_quality_check: If True, log quality gate results (no exception)

    Returns:
        Healed HTML string
    """
    if not html or not isinstance(html, str):
        return html or ""

    # TASK 1: Canonicalize segment
    canonical_segment = canonicalize_segment(segment)
    segment_lower: Literal["solo", "team", "kmu"] = canonical_segment.lower()  # type: ignore

    canonical_payback = parse_payback_months(canonical_payback_months)
    result = html
    fixes_applied = 0

    log.info("[HEALER-POST] Starting heal_final_html: len=%d, segment=%s (canonical=%s)", len(html), segment, canonical_segment)

    # Fix A: Remove prompt/template artifacts (TASK 1 - robust patterns)
    try:
        for bp in BOILERPLATE_PATTERNS:
            try:
                pattern = re.compile(bp.pattern, re.IGNORECASE | re.DOTALL)
                matches = pattern.findall(result)
                if matches:
                    fixes_applied += len(matches)
                    if bp.action == "drop":
                        result = pattern.sub("", result)
                    else:  # replace
                        result = pattern.sub(bp.replacement, result)
                    log.debug("[HEALER-POST] Removed %d matches for: %s", len(matches), bp.description)
            except re.error:
                pass
    except Exception as e:
        log.warning("[HEALER-POST] Fix A error: %s", e)

    # Fix B: SOLO blacklist enforcement (TASK 2 + TASK 3 FINAL FIX)
    if segment_lower == "solo":
        try:
            # TASK 2 (FINAL FIX): First apply phrase-level replacements
            for phrase, replacement in SOLO_TERM_REPLACEMENTS_EXTENDED.items():
                if phrase in result:
                    result = result.replace(phrase, replacement)
                    fixes_applied += 1
                    log.debug("[HEALER-POST] Replaced phrase '%s' → '%s'", phrase, replacement)

            # Then apply term-level blacklist enforcement
            result, blacklist_fixes = _enforce_solo_blacklist(result)
            fixes_applied += blacklist_fixes
        except Exception as e:
            log.warning("[HEALER-POST] Fix B (SOLO blacklist) error: %s", e)

    # Fix F: Payback decimal normalization (3.5 Monat* → 3,5 Monat*)
    try:
        decimal_matches = list(PAYBACK_DECIMAL_PATTERN.finditer(result))
        if decimal_matches:
            for m in reversed(decimal_matches):
                old_val = m.group(0)
                new_val = PAYBACK_DECIMAL_PATTERN.sub(r'\1,\2 \3', old_val)
                if old_val != new_val:
                    result = result[:m.start()] + new_val + result[m.end():]
                    fixes_applied += 1
    except Exception as e:
        log.warning("[HEALER-POST] Fix F error: %s", e)

    # TASK 4: Sanitize payback progress labels (remove %, deduplicate)
    try:
        result, payback_label_fixes = sanitize_payback_progress_labels(result)
        fixes_applied += payback_label_fixes
    except Exception as e:
        log.warning("[HEALER-POST] TASK4 payback label error: %s", e)

    # TASK 3: Business-case label localization
    if localize_labels:
        try:
            result, label_fixes = localize_business_case_labels_de(result)
            fixes_applied += label_fixes
        except Exception as e:
            log.warning("[HEALER-POST] Label localization error: %s", e)

    # TASK D: ROI as qualitative ranges for SOLO (P1 optional)
    if segment_lower == "solo":
        try:
            result, roi_fixes = sanitize_roi_for_solo(result)
            fixes_applied += roi_fixes
        except Exception as e:
            log.warning("[HEALER-POST] TASK-D ROI sanitization error: %s", e)

    # Remove duplicate "Progress 100%" (keep first) - legacy pattern
    try:
        matches = list(PAYBACK_PROGRESS_PATTERN.finditer(result))
        if len(matches) > 1:
            for m in reversed(matches[1:]):
                result = result[:m.start()] + result[m.end():]
                fixes_applied += 1
    except Exception as e:
        log.warning("[HEALER-POST] Progress dedup error: %s", e)

    # Clean up empty paragraphs left behind
    result = re.sub(r"<p>\s*</p>", "", result)
    result = re.sub(r"\n{3,}", "\n\n", result)

    log.info("[HEALER-POST] Completed: fixes_applied=%d, len=%d→%d", fixes_applied, len(html), len(result))

    # TASK 4: Optional quality gate check (logs only, no exception)
    if run_quality_check:
        try:
            qg_result = run_quality_gate(result, segment_lower, strict=False)
            if not qg_result.passed:
                log.warning(
                    "[HEALER-POST] Quality gate violations remaining: %s",
                    qg_result.to_dict()
                )
        except Exception as e:
            log.warning("[HEALER-POST] Quality gate error: %s", e)

    return result


# =============================================================================
# TASK 4: Quality Gate - Final Smoke Checks
# =============================================================================

@dataclass
class QualityGateResult:
    """Result of quality gate checks."""
    passed: bool = True
    prompt_leaks: List[str] = field(default_factory=list)
    english_decimals: List[str] = field(default_factory=list)
    solo_blacklist_hits: List[str] = field(default_factory=list)
    business_case_english_labels: List[str] = field(default_factory=list)

    @property
    def total_violations(self) -> int:
        """Total number of quality violations."""
        return (
            len(self.prompt_leaks) +
            len(self.english_decimals) +
            len(self.solo_blacklist_hits) +
            len(self.business_case_english_labels)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging/serialization."""
        return {
            "passed": self.passed,
            "total_violations": self.total_violations,
            "prompt_leaks": self.prompt_leaks,
            "english_decimals": self.english_decimals,
            "solo_blacklist_hits": self.solo_blacklist_hits,
            "business_case_english_labels": self.business_case_english_labels,
        }


# Patterns for quality gate checks
_QG_PROMPT_LEAK_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("Wobei soll ich", re.compile(r'Wobei\s+soll\s+ich', re.IGNORECASE)),
    ("Wobei kann ich", re.compile(r'Wobei\s+kann\s+ich', re.IGNORECASE)),
    ("Wie kann ich dir helfen", re.compile(r'Wie\s+kann\s+ich\s+(?:dir|Ihnen)\s+helfen', re.IGNORECASE)),
    ("Bitte beschreibe kurz", re.compile(r'Bitte\s+beschreibe?\s+kurz', re.IGNORECASE)),
    # TASK 3 (FINAL FIX): Additional prompt leak patterns
    ("Wenn du magst", re.compile(r'Wenn\s+du\s+magst', re.IGNORECASE)),
    ("Falls du möchtest", re.compile(r'Falls\s+du\s+m[öo]chtest', re.IGNORECASE)),
    ("Wenn du möchtest", re.compile(r'Wenn\s+du\s+m[öo]chtest', re.IGNORECASE)),
    ("Strategische Empfehlungen ?", re.compile(r'Strategische\s+Empfehlungen\s*\?', re.IGNORECASE)),
]

_QG_ENGLISH_DECIMAL_PATTERN = re.compile(
    r'\d+\.\d+\s+Monat(?:e|en)?',
    re.IGNORECASE
)

_QG_ENGLISH_BC_LABELS: List[str] = [
    "Payback Progress",
    "Time Savings Hours",
    "Time Savings (Hours)",
    "Monthly Savings",
    "Annual Savings",
]


def run_quality_gate(
    html: str,
    segment: Literal["solo", "team", "kmu", "SOLO", "TEAM", "KMU"] = "team",
    *,
    strict: bool = False,
    check_bc_labels: bool = True,
) -> QualityGateResult:
    """
    TASK 4: Run quality gate checks on final HTML before PDF generation.

    Checks for:
    1. Prompt leaks (Wobei soll ich, Wobei kann ich, Wenn du magst, etc.)
    2. English decimal format before "Monat(e)" (should be German 3,5 not 3.5)
    3. SOLO blacklist term violations (only for segment="solo")
    4. English business-case labels (optional)

    Args:
        html: Final HTML to check
        segment: Target segment for segment-specific checks (any case accepted)
        strict: If True, raises ReportQualityError on violations
        check_bc_labels: If True, also check for English BC labels

    Returns:
        QualityGateResult with all violations found

    Raises:
        ReportQualityError: If strict=True and violations found
    """
    result = QualityGateResult()

    if not html:
        return result

    # Canonicalize segment for consistent checking
    canonical_segment = canonicalize_segment(segment)

    # Check 1: Prompt leaks
    for name, pattern in _QG_PROMPT_LEAK_PATTERNS:
        if pattern.search(html):
            result.prompt_leaks.append(name)
            result.passed = False
            log.error("[QUALITY-GATE] Prompt leak detected: '%s'", name)

    # Check 2: English decimal format (3.5 Monate should be 3,5 Monate)
    english_decimal_matches = _QG_ENGLISH_DECIMAL_PATTERN.findall(html)
    if english_decimal_matches:
        result.english_decimals = english_decimal_matches
        result.passed = False
        log.error(
            "[QUALITY-GATE] English decimal format detected: %s",
            english_decimal_matches
        )

    # Check 3: SOLO blacklist (only for SOLO segment)
    if canonical_segment == "SOLO":
        for term in SOLO_BLACKLIST_TERMS:
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            if pattern.search(html):
                result.solo_blacklist_hits.append(term)
                result.passed = False
                log.error("[QUALITY-GATE] SOLO blacklist term detected: '%s'", term)

    # Check 4: English business-case labels (optional)
    if check_bc_labels:
        for label in _QG_ENGLISH_BC_LABELS:
            if label in html:
                result.business_case_english_labels.append(label)
                result.passed = False
                log.error("[QUALITY-GATE] English BC label detected: '%s'", label)

    # Log summary
    if result.passed:
        log.info("[QUALITY-GATE] PASSED - No quality violations found")
    else:
        log.warning(
            "[QUALITY-GATE] FAILED - %d violations: prompts=%d, decimals=%d, solo_blacklist=%d, bc_labels=%d",
            result.total_violations,
            len(result.prompt_leaks),
            len(result.english_decimals),
            len(result.solo_blacklist_hits),
            len(result.business_case_english_labels)
        )

    # Strict mode: raise exception on failure
    if strict and not result.passed:
        raise ReportQualityError(
            f"Quality gate failed with {result.total_violations} violations: "
            f"prompts={result.prompt_leaks}, decimals={result.english_decimals}, "
            f"solo_blacklist={result.solo_blacklist_hits}, bc_labels={result.business_case_english_labels}"
        )

    return result


class ReportQualityError(Exception):
    """Raised when report quality gate fails in strict mode."""
    pass


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[HEALER] Report Healer loaded - %d boilerplate patterns, %d payback patterns, %d SOLO term replacements, %d blacklist terms",
    len(BOILERPLATE_PATTERNS),
    len(PAYBACK_PATTERNS_DE),
    len(SOLO_TERM_REPLACEMENTS),
    len(SOLO_BLACKLIST_TERMS)
)
