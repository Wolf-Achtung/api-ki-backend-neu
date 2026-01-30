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

Version: 1.0.0 (FIX-A-G)
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Pattern, Set, Tuple, Union

log = logging.getLogger(__name__)

__all__ = [
    "heal_report_html",
    "sanitize_template_phrases",
    "enforce_persona_language",
    "reduce_redundancy",
    "enforce_roi_rules",
    "trim_incomplete_sentences",
    "enforce_payback_consistency",
    "apply_segment_budget",
    "HealingResult",
    "BOILERPLATE_PATTERNS",
    "PAYBACK_PATTERNS_DE",
    "BoilerplatePattern",
    "PaybackPattern",
]


# =============================================================================
# HELPER: Safe String Coercion
# =============================================================================

def _to_text(value: Any) -> str:
    """
    Safely convert any value to string for regex operations.

    Args:
        value: Any value (str, int, float, None, list, dict, etc.)

    Returns:
        String representation, never raises
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        # Handle NaN and Inf safely
        if math.isnan(value) or math.isinf(value):
            return ""
        return str(value)
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, (list, tuple)):
        # Join list items, recursively converting each
        return " ".join(_to_text(item) for item in value if item is not None)
    if isinstance(value, dict):
        # For dicts, return empty - they shouldn't be in HTML content
        return ""
    # Fallback: try str(), but catch any errors
    try:
        return str(value)
    except Exception:
        return ""


def _coerce_sections_to_str(sections: Dict[str, Any]) -> Dict[str, str]:
    """
    Coerce all section values to strings for safe regex processing.

    Skips internal metadata keys (starting with _) that aren't HTML content.
    Logs warnings for non-string values.

    Args:
        sections: Dict with potentially mixed value types

    Returns:
        Dict with all values as strings
    """
    result: Dict[str, str] = {}

    for key, value in sections.items():
        # Skip internal metadata keys - preserve as-is converted to string
        if key.startswith("_"):
            if isinstance(value, str):
                result[key] = value
            elif isinstance(value, dict):
                # Metadata dicts - convert to JSON-like string for preservation
                import json
                try:
                    result[key] = json.dumps(value, ensure_ascii=False)
                except Exception:
                    result[key] = str(value)
            else:
                result[key] = _to_text(value)
            continue

        # For HTML content keys, coerce to string
        if isinstance(value, str):
            result[key] = value
        elif value is None:
            result[key] = ""
        else:
            # Log warning for unexpected types in HTML sections
            log.warning(
                "[HEALER] Non-string value in section '%s': type=%s, converting to str",
                key, type(value).__name__
            )
            result[key] = _to_text(value)

    return result

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
    # A) Prompt-/Chat-Blöcke
    # -------------------------------------------------------------------------
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
    "Governance": "Leitplanken",
    "Compliance": "Regelkonformität",
    "Policy": "Richtlinie",
    "Rollout": "Einführung",
    "Deployment": "Bereitstellung",
    # KPI/Dashboard terms
    "KPI-Dashboard": "Kennzahlen-Übersicht",
    "Dashboard": "Übersicht",
    "Metriken": "Kennzahlen",
    "Analytics": "Auswertungen",
    # Process terms
    "Workflow-Automation": "Automatisierung",
    "Orchestrierung": "Koordination",
    "Skalierung": "Wachstum",
    "skalierbar": "erweiterbar",
    "Enterprise": "Unternehmens",
    "enterprise-grade": "professionell",
    # Team/Org terms
    "Team-Meeting": "Besprechung",
    "Briefing": "Einweisung",
    "Onboarding": "Einarbeitung",
    "Change Management": "Veränderungsprozess",
}

# Patterns to remove entirely for SOLO (too complex)
SOLO_REMOVE_PATTERNS: List[str] = [
    r"(?:unternehmensweite|organisationsweite)\s+(?:Governance|Compliance|Audit)",
    r"(?:Enterprise|Multi-Team)\s+(?:Architektur|Rollout|Deployment)",
    r"(?:Skalierung|Scaling)\s+(?:auf|für)\s+(?:mehrere|viele)\s+(?:Teams|Abteilungen)",
]


def enforce_persona_language(
    html: str,
    segment: Literal["solo", "team", "kmu"]
) -> Tuple[str, int]:
    """
    Fix B: Enforce persona-appropriate language.

    For SOLO: Replace enterprise terms with simpler alternatives.
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

    # Apply term replacements (case-insensitive, preserve case of first letter)
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

    # Remove overly complex patterns for SOLO
    for remove_pattern in SOLO_REMOVE_PATTERNS:
        try:
            pattern = re.compile(remove_pattern, re.IGNORECASE)
            before_len = len(result)
            result = pattern.sub("", result)
            if len(result) < before_len:
                replacement_count += 1
        except re.error:
            pass

    if replacement_count > 0:
        log.info("[FIX-B] SOLO persona: %d term replacements applied", replacement_count)

    return result, replacement_count


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
    sections: Dict[str, str]
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


# =============================================================================
# MAIN HEALING PIPELINE
# =============================================================================

def heal_report_html(
    sections: Dict[str, Any],
    segment: Literal["solo", "team", "kmu"],
    *,
    canonical_payback_months: Optional[float] = None,
    skip_fixes: Optional[Set[str]] = None
) -> HealingResult:
    """
    Main healing pipeline for report HTML.

    Runs all fixes A-G in sequence:
    1. sanitize_template_phrases (Fix A)
    2. enforce_persona_language (Fix B)
    3. reduce_redundancy (Fix C)
    4. trim_incomplete_sentences (Fix E)
    5. enforce_roi_rules (Fix D)
    6. enforce_payback_consistency (Fix F)
    7. apply_segment_budget (Fix G)

    Args:
        sections: Dict of section_name -> HTML content (non-strings are coerced)
        segment: Target segment (solo, team, kmu)
        canonical_payback_months: Optional canonical payback value
        skip_fixes: Set of fix letters to skip (e.g., {"A", "C"})

    Returns:
        HealingResult with processed sections and statistics
    """
    skip = skip_fixes or set()

    # ROBUSTNESS: Coerce all section values to strings before processing
    # This prevents crashes from float/int/None/list values in sections
    coerced_sections = _coerce_sections_to_str(sections)
    result = HealingResult(sections=coerced_sections)

    log.info(
        "[HEALER] Starting heal_report_html: segment=%s, sections=%d, skip=%s",
        segment, len(sections), skip
    )

    # Fix A: Template phrases
    if "A" not in skip:
        for section_name, html in list(result.sections.items()):
            if html and isinstance(html, str):
                try:
                    processed, count = sanitize_template_phrases(html)
                    result.sections[section_name] = processed
                    result.template_phrases_removed += count
                except Exception as e:
                    log.warning("[FIX-A] Error in section '%s': %s - skipping", section_name, e)

    # Fix B: Persona language
    if "B" not in skip:
        for section_name, html in list(result.sections.items()):
            if html and isinstance(html, str):
                try:
                    processed, count = enforce_persona_language(html, segment)
                    result.sections[section_name] = processed
                    result.persona_replacements += count
                except Exception as e:
                    log.warning("[FIX-B] Error in section '%s': %s - skipping", section_name, e)

    # Fix C: Redundancy reduction
    if "C" not in skip:
        try:
            result.sections, result.redundancy_stats = reduce_redundancy(result.sections)
        except Exception as e:
            log.warning("[FIX-C] Error in redundancy reduction: %s - skipping", e)

    # Fix E: Incomplete sentences (before D to clean up content)
    if "E" not in skip:
        for section_name, html in list(result.sections.items()):
            if html and isinstance(html, str):
                try:
                    processed, count = trim_incomplete_sentences(html)
                    result.sections[section_name] = processed
                    result.fragments_trimmed += count
                except Exception as e:
                    log.warning("[FIX-E] Error in section '%s': %s - skipping", section_name, e)

    # Fix D: ROI rules
    if "D" not in skip:
        try:
            result.sections, result.roi_violations_fixed = enforce_roi_rules(result.sections)
        except Exception as e:
            log.warning("[FIX-D] Error in ROI rules: %s - skipping", e)

    # Fix F: Payback consistency
    if "F" not in skip:
        try:
            result.sections, result.payback_fixes = enforce_payback_consistency(
                result.sections,
                canonical_payback_months
            )
        except Exception as e:
            log.warning("[FIX-F] Error in payback consistency: %s - skipping", e)

    # Fix G: Segment budget
    if "G" not in skip:
        try:
            result.sections, result.sections_budget_trimmed = apply_segment_budget(
                result.sections,
                segment
            )
        except Exception as e:
            log.warning("[FIX-G] Error in segment budget: %s - skipping", e)

    # Add healing flag to sections meta
    result.sections["_redundancy_healed"] = "true"
    result.sections["_healer_version"] = "1.0.0"
    result.sections["_healer_segment"] = segment

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
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[HEALER] Report Healer loaded - %d boilerplate patterns, %d payback patterns, %d SOLO term replacements",
    len(BOILERPLATE_PATTERNS),
    len(PAYBACK_PATTERNS_DE),
    len(SOLO_TERM_REPLACEMENTS)
)
