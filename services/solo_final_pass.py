# -*- coding: utf-8 -*-
"""
FIX-554: Solo Final Pass – Last-Mile Cleanup for Solo Reports
=============================================================

This module provides the FINAL cleanup passes that run after ALL HTML blocks
have been assembled, ensuring zero enterprise terminology and consistent
Sie-Ansprache in solo reports.

Three passes:
1. Enterprise Term Elimination (robust, tag-aware)
2. Duz→Sie Conversion (German du/dir/dein → Sie/Ihnen/Ihr)
3. KPI → Kennzahlen normalization

Version: 1.0.0 (FIX-554)
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION: Forbidden Enterprise Terms
# =============================================================================

# Terms that must NEVER appear in solo report output.
# Each entry: (regex_pattern, replacement, description)
# Patterns are designed to match even through HTML tag splits, soft hyphens, etc.
ENTERPRISE_TERM_REPLACEMENTS: List[Tuple[str, str, str]] = [
    # --- Governance (highest priority – the main offender in Report 554) ---
    # Adjective inflection-aware: r→n (Dativ/Genitiv), s→r (Neutrum), n→n (Akk)
    (r"starker\s+Governance", "klaren Spielregeln", "starker Governance → klaren Spielregeln"),
    (r"starken\s+Governance", "klaren Spielregeln", "starken Governance → klaren Spielregeln"),
    (r"starkes\s+Governance", "klares Regelwerk", "starkes Governance → klares Regelwerk"),
    (r"starke\s+Governance", "klare Spielregeln", "starke Governance → klare Spielregeln"),
    (r"klarer\s+Governance", "klaren Spielregeln", "klarer Governance → klaren Spielregeln"),
    (r"klaren\s+Governance", "klaren Spielregeln", "klaren Governance → klaren Spielregeln"),
    (r"klare\s+Governance", "klare Spielregeln", "klare Governance → klare Spielregeln"),
    (r"guter\s+Governance", "guten Spielregeln", "guter Governance → guten Spielregeln"),
    (r"guten\s+Governance", "guten Spielregeln", "guten Governance → guten Spielregeln"),
    (r"gute\s+Governance", "gute Spielregeln", "gute Governance → gute Spielregeln"),
    (r"Governance[-\s]?Framework", "Grundregeln", "Governance-Framework → Grundregeln"),
    (r"Governance[-\s]?Prozess(?:e|en)?", "Abstimmungsregeln", "Governance-Prozess → Abstimmungsregeln"),
    (r"Governance[-\s]?Struktur(?:en)?", "Regelwerk", "Governance-Struktur → Regelwerk"),
    (r"Governance[-\s]?Board", "Ihre Steuerung", "Governance Board → Ihre Steuerung"),
    (r"Governance[-\s]?Modell", "Regelwerk", "Governance-Modell → Regelwerk"),

    # --- Audit-Trail ---
    (r"Audit[-\u2011\u2010\s]?Trail", "nachvollziehbare Protokollierung", "Audit-Trail → Protokollierung"),

    # --- Stakeholder ---
    # FIX-S14C: Compound patterns first (longer match before shorter)
    (r"Stakeholder-Analyse", "Beteiligten-Analyse", "Stakeholder-Analyse → Beteiligten-Analyse"),
    (r"Stakeholder-Alignment", "Abstimmung der Beteiligten", "Stakeholder-Alignment → Abstimmung"),
    (r"Stakeholder-Feedback", "Rückmeldung der Beteiligten", "Stakeholder-Feedback → Rückmeldung"),
    (r"Stakeholder-Management", "Beteiligten-Management", "Stakeholder-Management → Beteiligten-Mgmt"),
    (r"Stakeholder-Kommunikation", "Kommunikation mit Beteiligten", "Stakeholder-Kommunikation → Komm."),
    (r"Stakeholder-[A-Za-zäöüÄÖÜß]+", "Beteiligten-Abstimmung", "Stakeholder-Compound → Fallback"),
    (r"Stakeholdern", "wichtigen Personen", "Stakeholdern → wichtigen Personen"),
    (r"Stakeholders", "wichtiger Personen", "Stakeholders → wichtiger Personen"),
    (r"Stakeholder", "wichtige Personen", "Stakeholder → wichtige Personen"),

    # --- Stack ---
    (r"Tech[-\s]?Stack", "Werkzeugkasten", "Tech-Stack → Werkzeugkasten"),
    (r"KI[-\s]?Stack", "KI-Werkzeuge", "KI-Stack → KI-Werkzeuge"),
    # Catch "Stack" standalone (not inside other words, not after "KI-" handled above)
    (r"(?<![-\w])Stack(?:s)?(?![-\w])", "Werkzeugkasten", "Stack → Werkzeugkasten"),

    # --- Layer ---
    (r"\bLayers\b", "Ebenen", "Layers → Ebenen"),
    (r"\bLayer\b", "Ebene", "Layer → Ebene"),

    # --- Architektur ---
    (r"Systemarchitektur", "Systemaufbau", "Systemarchitektur → Systemaufbau"),
    (r"IT[-\s]?Architektur", "IT-Aufbau", "IT-Architektur → IT-Aufbau"),
    (r"\bArchitekturen\b", "Strukturen", "Architekturen → Strukturen"),
    (r"\bArchitektur\b", "Aufbau", "Architektur → Aufbau"),

    # --- Rollout ---
    (r"\bRoll[-\s]?out(?:s)?\b", "Einführung", "Rollout → Einführung"),
    (r"\bRollout(?:s)?\b", "Einführung", "Rollout → Einführung"),

    # --- Prozesslandschaft ---
    (r"\bProzesslandschaft(?:en)?\b", "Arbeitsabläufe", "Prozesslandschaft → Arbeitsabläufe"),

    # --- Enterprise (FIX-RS2-7) ---
    (r"\bEnterprise[-\s]?Software\b", "Unternehmenssoftware", "Enterprise-Software → Unternehmenssoftware"),
    (r"\bEnterprise[-\s]?Lösung(?:en)?\b", "Unternehmenslösung", "Enterprise-Lösung → Unternehmenslösung"),
    (r"\bEnterprise[-\s]?Plattform\b", "Unternehmensplattform", "Enterprise-Plattform → Unternehmensplattform"),
    (r"(?<![-\w])Enterprise(?:s)?(?![-\w])", "Unternehmen", "Enterprise → Unternehmen"),

    # --- Audit standalone (FIX-RS2-7: not just Audit-Trail) ---
    (r"\bAudit[-\s]?Prozess(?:e|en)?\b", "Prüfprozess", "Audit-Prozess → Prüfprozess"),
    (r"\bAudit[-\s]?Bericht(?:e|en)?\b", "Prüfbericht", "Audit-Bericht → Prüfbericht"),
    (r"(?<![-\w])Audits(?![-\w])", "Prüfungen", "Audits → Prüfungen"),
    (r"(?<![-\w])Audit(?![-\w\u2011\u2010]Trail)", "Prüfung", "Audit → Prüfung"),

    # --- Baukasten (in the sense of enterprise toolkit jargon) ---
    # Note: "Baukasten" in the replacement whitelist context (Solo-friendly) is fine.
    # This targets enterprise "Baukasten-Prinzip/System" language.
    (r"\bBaukasten[-\s]?Prinzip\b", "modulares Vorgehen", "Baukasten-Prinzip → modulares Vorgehen"),
    (r"\bBaukasten[-\s]?System\b", "modulares System", "Baukasten-System → modulares System"),
]

# Catch-all regex for Governance: matches even through HTML tag splits and soft hyphens
# This handles cases like Gover</span><span>nance, Gover­nance, etc.
# IMPORTANT: Only applies to text content, not inside HTML tag attributes.
_GOVERNANCE_CHARS = r'[\s\u00AD\u200B]*(?:<[^>]*>[\s\u00AD\u200B]*)*'
_GOVERNANCE_CATCHALL = re.compile(
    r'G' + _GOVERNANCE_CHARS + r'o' + _GOVERNANCE_CHARS + r'v' + _GOVERNANCE_CHARS +
    r'e' + _GOVERNANCE_CHARS + r'r' + _GOVERNANCE_CHARS + r'n' + _GOVERNANCE_CHARS +
    r'a' + _GOVERNANCE_CHARS + r'n' + _GOVERNANCE_CHARS + r'c' + _GOVERNANCE_CHARS + r'e',
    re.IGNORECASE
)

# Catch-all for Audit-Trail through HTML/hyphen splits
_AUDIT_TRAIL_CATCHALL = re.compile(
    r'A' + _GOVERNANCE_CHARS + r'u' + _GOVERNANCE_CHARS + r'd' + _GOVERNANCE_CHARS +
    r'i' + _GOVERNANCE_CHARS + r't'
    r'[\s\-\u00AD\u2011\u2010]*(?:<[^>]*>[\s\u00AD]*)*'
    r'T' + _GOVERNANCE_CHARS + r'r' + _GOVERNANCE_CHARS + r'a' + _GOVERNANCE_CHARS +
    r'i' + _GOVERNANCE_CHARS + r'l',
    re.IGNORECASE
)


# =============================================================================
# CONFIGURATION: Duz→Sie Conversion
# =============================================================================

# German informal → formal pronoun/verb replacements
# Order matters: longer patterns first to avoid partial matches
DUZ_TO_SIE_REPLACEMENTS: List[Tuple[str, str, str]] = [
    # --- Possessivpronomen (longer patterns first) ---
    (r"\bdeinen\b", "Ihren", "deinen → Ihren"),
    (r"\bdeiner\b", "Ihrer", "deiner → Ihrer"),
    (r"\bdeinem\b", "Ihrem", "deinem → Ihrem"),
    (r"\bdeines\b", "Ihres", "deines → Ihres"),
    (r"\bdeine\b", "Ihre", "deine → Ihre"),
    (r"\bdein\b", "Ihr", "dein → Ihr"),
    (r"\bDeinen\b", "Ihren", "Deinen → Ihren"),
    (r"\bDeiner\b", "Ihrer", "Deiner → Ihrer"),
    (r"\bDeinem\b", "Ihrem", "Deinem → Ihrem"),
    (r"\bDeines\b", "Ihres", "Deines → Ihres"),
    (r"\bDeine\b", "Ihre", "Deine → Ihre"),
    (r"\bDein\b", "Ihr", "Dein → Ihr"),

    # --- euch/euer ---
    (r"\beuren\b", "Ihren", "euren → Ihren"),
    (r"\beurer\b", "Ihrer", "eurer → Ihrer"),
    (r"\beurem\b", "Ihrem", "eurem → Ihrem"),
    (r"\beures\b", "Ihres", "eures → Ihres"),
    (r"\beure\b", "Ihre", "eure → Ihre"),
    (r"\beuer\b", "Ihr", "euer → Ihr"),
    (r"\bEuren\b", "Ihren", "Euren → Ihren"),
    (r"\bEurer\b", "Ihrer", "Eurer → Ihrer"),
    (r"\bEurem\b", "Ihrem", "Eurem → Ihrem"),
    (r"\bEures\b", "Ihres", "Eures → Ihres"),
    (r"\bEure\b", "Ihre", "Eure → Ihre"),
    (r"\bEuer\b", "Ihr", "Euer → Ihr"),
    (r"\beuch\b", "Ihnen", "euch → Ihnen"),
    (r"\bEuch\b", "Ihnen", "Euch → Ihnen"),

    # --- Personalpronomen ---
    (r"\bdich\b", "Sie", "dich → Sie"),
    (r"\bDich\b", "Sie", "Dich → Sie"),
    (r"\bdir\b", "Ihnen", "dir → Ihnen"),
    (r"\bDir\b", "Ihnen", "Dir → Ihnen"),
    # "du" last (shortest, most common)
    (r"\bdu\b", "Sie", "du → Sie"),
    (r"\bDu\b", "Sie", "Du → Sie"),
]

# Verification pattern: any remaining Duz-forms after conversion
_DUZ_CHECK_PATTERN = re.compile(
    r"\b(du|dir|dein|deine|deinem|deinen|deiner|deines|dich|euch|euer|eure|eurem|euren|eurer|eures)\b",
    re.IGNORECASE
)


# =============================================================================
# CONFIGURATION: KPI → Kennzahlen
# =============================================================================

KPI_REPLACEMENTS: List[Tuple[str, str, str]] = [
    (r"\bKPI[-\s]?Forecasts?\b", "Kennzahlen-Prognosen", "KPI-Forecasts → Kennzahlen-Prognosen"),
    (r"\bKPI[-\s]?Dashboard\b", "Kennzahlen-Übersicht", "KPI-Dashboard → Kennzahlen-Übersicht"),
    (r"\bKPIs\b", "Kennzahlen", "KPIs → Kennzahlen"),
    (r"\bKPI\b", "Kennzahl", "KPI → Kennzahl"),
]


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def _apply_catchall_safe(
    html: str,
    pattern: re.Pattern[str],
    replacement: str,
    label: str,
) -> Tuple[str, int]:
    """
    Apply a catch-all regex to HTML, replacing only matches that span text content
    (not matches entirely within HTML tag attributes).

    This is needed for tag-split cases like Gover</span><span>nance.
    The regex is applied to the full HTML, but each match is checked:
    if the match is entirely within an HTML tag (between < and >), it's skipped.
    """
    if not html:
        return html, 0

    # Find tag ranges to know what's inside tags
    tag_ranges = []
    for m in re.finditer(r'<[^>]+>', html):
        tag_ranges.append((m.start(), m.end()))

    def is_entirely_in_tag(match_start: int, match_end: int) -> bool:
        """Check if the match is entirely within a single HTML tag."""
        for tag_start, tag_end in tag_ranges:
            if match_start >= tag_start and match_end <= tag_end:
                return True
        return False

    # Apply replacements, skipping matches inside tags
    total_count = 0
    result = html
    offset = 0

    for match in pattern.finditer(html):
        if is_entirely_in_tag(match.start(), match.end()):
            continue
        # This match touches text content - replace it
        total_count += 1

    # If we have matches to replace, do a full sub
    # (the regex inherently won't match inside single tags because tag-split patterns
    #  only occur across text+tag boundaries)
    if total_count > 0:
        # Use a callback to skip tag-only matches
        def replace_if_not_in_tag(m: re.Match[str]) -> str:
            if is_entirely_in_tag(m.start(), m.end()):
                return m.group(0)  # Keep original
            return replacement

        result = pattern.sub(replace_if_not_in_tag, html)
        log.info("[FIX-554][ENTERPRISE] %s catch-all: %d matches replaced", label, total_count)

    return result, total_count


def _apply_replacements_to_text(
    text: str,
    replacements: List[Tuple[str, str, str]],
    pass_name: str = "replacement",
) -> Tuple[str, int]:
    """
    Apply regex replacements to plain text content.

    Only replaces in text portions (not inside HTML tags).
    Returns (modified_text, replacement_count).
    """
    if not text:
        return text, 0

    total_count = 0
    result = text

    for pattern, replacement, description in replacements:
        try:
            regex = re.compile(pattern, re.UNICODE)
            new_result, count = regex.subn(replacement, result)
            if count > 0:
                total_count += count
                result = new_result
                log.debug("[FIX-554][%s] %s (%dx)", pass_name, description, count)
        except re.error as e:
            log.warning("[FIX-554][%s] Invalid regex '%s': %s", pass_name, pattern, e)

    return result, total_count


def _apply_replacements_to_html(
    html: str,
    replacements: List[Tuple[str, str, str]],
    pass_name: str = "replacement",
) -> Tuple[str, int]:
    """
    Apply replacements only to text content within HTML (not inside tags).

    Splits HTML by tags, applies replacements only to text nodes.
    """
    if not html:
        return html, 0

    parts = re.split(r'(<[^>]+>)', html)
    total_count = 0
    result_parts = []

    for part in parts:
        if part.startswith('<') and part.endswith('>'):
            result_parts.append(part)
        else:
            modified, count = _apply_replacements_to_text(part, replacements, pass_name)
            result_parts.append(modified)
            total_count += count

    return ''.join(result_parts), total_count


def eliminate_enterprise_terms(html: str, run_id: str = "") -> Tuple[str, int]:
    """
    FIX-554 Pass 1: Eliminate ALL enterprise terms from solo report HTML.

    Applies:
    1. Phrase-level replacements (context-aware)
    2. Catch-all regex for Governance (handles tag splits, soft hyphens)
    3. Catch-all regex for Audit-Trail (handles tag splits, hyphens)

    Args:
        html: Final assembled HTML
        run_id: For logging

    Returns:
        Tuple of (cleaned_html, total_replacements)
    """
    if not html:
        return html, 0

    total = 0
    result = html

    # Step 1: Apply phrase-level replacements (text nodes only)
    result, count = _apply_replacements_to_html(result, ENTERPRISE_TERM_REPLACEMENTS, "ENTERPRISE")
    total += count

    # Step 2: Catch-all for Governance through tag splits (text nodes only)
    # We need to be careful not to replace inside HTML attributes (class, id, etc.)
    result, catchall_count = _apply_catchall_safe(result, _GOVERNANCE_CATCHALL, "Spielregeln", "Governance")
    total += catchall_count

    # Step 3: Catch-all for Audit-Trail through tag/hyphen splits (text nodes only)
    result, catchall_count = _apply_catchall_safe(result, _AUDIT_TRAIL_CATCHALL, "Protokollierung", "Audit-Trail")
    total += catchall_count

    if total > 0:
        log.info("[FIX-554][ENTERPRISE] Total enterprise term replacements: %d (run=%s)", total, run_id)

    return result, total


def convert_duz_to_sie(html: str, run_id: str = "") -> Tuple[str, int]:
    """
    FIX-554 Pass 2: Convert all Duz-forms to Sie-Ansprache in solo report HTML.

    Only modifies text content (not HTML tags/attributes).

    Args:
        html: HTML content
        run_id: For logging

    Returns:
        Tuple of (converted_html, replacement_count)
    """
    if not html:
        return html, 0

    result, count = _apply_replacements_to_html(html, DUZ_TO_SIE_REPLACEMENTS, "DUZ-SIE")

    if count > 0:
        log.info("[FIX-554][DUZ-SIE] Converted %d Duz-forms to Sie (run=%s)", count, run_id)

    # Verification: check for remaining Duz-forms in visible text
    text_only = re.sub(r'<[^>]+>', ' ', result)
    remaining = _DUZ_CHECK_PATTERN.findall(text_only)
    if remaining:
        log.warning(
            "[FIX-554][DUZ-SIE] %d Duz-forms still remaining after conversion: %s (run=%s)",
            len(remaining), remaining[:5], run_id
        )

    return result, count


def replace_kpi_terms(html: str, run_id: str = "") -> Tuple[str, int]:
    """
    FIX-554 Pass 3: Replace KPI with Kennzahlen for solo-friendly language.

    Args:
        html: HTML content
        run_id: For logging

    Returns:
        Tuple of (modified_html, replacement_count)
    """
    if not html:
        return html, 0

    result, count = _apply_replacements_to_html(html, KPI_REPLACEMENTS, "KPI")

    if count > 0:
        log.info("[FIX-554][KPI] Replaced %d KPI terms with Kennzahlen (run=%s)", count, run_id)

    return result, count


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def apply_solo_final_pass(
    html: str,
    run_id: str = "",
    enable_enterprise_elimination: bool = True,
    enable_duz_conversion: bool = True,
    enable_kpi_replacement: bool = True,
) -> Tuple[str, Dict[str, int]]:
    """
    FIX-554: Apply all final solo cleanup passes to assembled HTML.

    This function should be called AFTER the report HTML is fully assembled
    (post-render, post-minification) as the LAST processing step before PDF.

    Args:
        html: Final assembled HTML
        run_id: Run identifier for logging
        enable_enterprise_elimination: Enable enterprise term removal
        enable_duz_conversion: Enable du→Sie conversion
        enable_kpi_replacement: Enable KPI→Kennzahlen replacement

    Returns:
        Tuple of (cleaned_html, stats_dict)
    """
    if not html:
        return html, {"enterprise": 0, "duz_sie": 0, "kpi": 0, "total": 0}

    result = html
    stats: Dict[str, int] = {"enterprise": 0, "duz_sie": 0, "kpi": 0, "total": 0}

    try:
        # Pass 1: Enterprise term elimination
        if enable_enterprise_elimination:
            result, count = eliminate_enterprise_terms(result, run_id)
            stats["enterprise"] = count
            stats["total"] += count

        # Pass 2: Duz→Sie conversion
        if enable_duz_conversion:
            result, count = convert_duz_to_sie(result, run_id)
            stats["duz_sie"] = count
            stats["total"] += count

        # Pass 3: KPI → Kennzahlen
        if enable_kpi_replacement:
            result, count = replace_kpi_terms(result, run_id)
            stats["kpi"] = count
            stats["total"] += count

        if stats["total"] > 0:
            log.info(
                "[FIX-554] Solo final pass complete: %d total replacements "
                "(enterprise=%d, duz_sie=%d, kpi=%d) run=%s",
                stats["total"], stats["enterprise"], stats["duz_sie"], stats["kpi"], run_id
            )
        else:
            log.debug("[FIX-554] Solo final pass: no replacements needed (run=%s)", run_id)

    except Exception as e:
        log.error("[FIX-554] Solo final pass failed: %s (run=%s) – returning original HTML", e, run_id)
        return html, stats

    return result, stats


def apply_solo_final_pass_to_sections(
    sections: Dict[str, Any],
    run_id: str = "",
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Apply solo final pass to all string sections (pre-render).

    This is useful for cleaning sections BEFORE they go into template rendering.

    Args:
        sections: Dict of section_key → content
        run_id: For logging

    Returns:
        Tuple of (processed_sections, aggregated_stats)
    """
    processed = dict(sections)
    total_stats: Dict[str, int] = {"enterprise": 0, "duz_sie": 0, "kpi": 0, "total": 0}

    for key, content in sections.items():
        if not isinstance(content, str):
            continue
        if len(content) < 30:
            continue
        # Skip internal/metadata keys
        if key.startswith("_"):
            continue

        result, stats = apply_solo_final_pass(content, run_id=f"{run_id}/{key}")
        if stats["total"] > 0:
            processed[key] = result
            for stat_key in total_stats:
                total_stats[stat_key] += stats[stat_key]

    if total_stats["total"] > 0:
        log.info(
            "[FIX-554] Solo final pass on sections: %d total replacements (run=%s)",
            total_stats["total"], run_id
        )

    return processed, total_stats


# =============================================================================
# SIZE-AWARE FINAL PASS (Team/KMU support)
# =============================================================================

# Team gets softer enterprise term filtering (only the most jarring terms)
TEAM_ENTERPRISE_TERM_REPLACEMENTS: List[Tuple[str, str, str]] = [
    # Team still avoids the worst enterprise jargon
    (r"\bMatrixorganisation\b", "Teamstruktur", "Matrixorganisation → Teamstruktur"),
    (r"\bWertschöpfungskette\b", "Leistungskette", "Wertschöpfungskette → Leistungskette"),
    (r"\bEnterprise[-\s]?Software\b", "Business-Software", "Enterprise-Software → Business-Software"),
    (r"\bUnternehmensarchitektur\b", "Unternehmensstruktur", "Unternehmensarchitektur → Unternehmensstruktur"),
    (r"\bCompliance[-\s]?Framework\b", "Regelwerk", "Compliance-Framework → Regelwerk"),
]

# KMU gets minimal filtering (only truly inappropriate terms)
KMU_ENTERPRISE_TERM_REPLACEMENTS: List[Tuple[str, str, str]] = [
    (r"\bMatrixorganisation\b", "Organisationsstruktur", "Matrixorganisation → Organisationsstruktur"),
]


def apply_size_final_pass(
    html: str,
    segment: str = "solo",
    run_id: str = "",
) -> Tuple[str, Dict[str, int]]:
    """
    Size-aware final pass: applies appropriate cleanup rules per segment.

    - solo: Full enterprise elimination + Duz→Sie + KPI→Kennzahlen
    - team: Soft enterprise filtering + Duz→Sie (no KPI replacement)
    - kmu:  Minimal filtering + Duz→Sie (no KPI replacement)

    Args:
        html: Final assembled HTML
        segment: "solo" | "team" | "kmu"
        run_id: For logging

    Returns:
        Tuple of (cleaned_html, stats_dict)
    """
    seg = segment.lower().strip()

    if seg == "solo":
        return apply_solo_final_pass(
            html, run_id=run_id,
            enable_enterprise_elimination=True,
            enable_duz_conversion=True,
            enable_kpi_replacement=True,
        )

    if not html:
        return html, {"enterprise": 0, "duz_sie": 0, "kpi": 0, "total": 0}

    result = html
    stats: Dict[str, int] = {"enterprise": 0, "duz_sie": 0, "kpi": 0, "total": 0}

    try:
        # Enterprise term filtering (softer for team, minimal for kmu)
        if seg == "team":
            result, count = _apply_replacements_to_html(
                result, TEAM_ENTERPRISE_TERM_REPLACEMENTS, "TEAM-ENTERPRISE"
            )
            stats["enterprise"] = count
            stats["total"] += count
        elif seg == "kmu":
            result, count = _apply_replacements_to_html(
                result, KMU_ENTERPRISE_TERM_REPLACEMENTS, "KMU-ENTERPRISE"
            )
            stats["enterprise"] = count
            stats["total"] += count

        # Duz→Sie conversion (all sizes get this)
        result, count = convert_duz_to_sie(result, run_id)
        stats["duz_sie"] = count
        stats["total"] += count

        if stats["total"] > 0:
            log.info(
                "[SIZE-PASS] %s final pass: %d replacements (enterprise=%d, duz_sie=%d) run=%s",
                seg.upper(), stats["total"], stats["enterprise"], stats["duz_sie"], run_id
            )

    except Exception as e:
        log.error("[SIZE-PASS] %s final pass failed: %s (run=%s)", seg.upper(), e, run_id)
        return html, stats

    return result, stats


def apply_size_final_pass_to_sections(
    sections: Dict[str, Any],
    segment: str = "solo",
    run_id: str = "",
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Size-aware final pass applied to all string sections (pre-render).

    Args:
        sections: Dict of section_key → content
        segment: "solo" | "team" | "kmu"
        run_id: For logging

    Returns:
        Tuple of (processed_sections, aggregated_stats)
    """
    processed = dict(sections)
    total_stats: Dict[str, int] = {"enterprise": 0, "duz_sie": 0, "kpi": 0, "total": 0}

    for key, content in sections.items():
        if not isinstance(content, str):
            continue
        if len(content) < 30:
            continue
        if key.startswith("_"):
            continue

        result, stats = apply_size_final_pass(content, segment=segment, run_id=f"{run_id}/{key}")
        if stats["total"] > 0:
            processed[key] = result
            for stat_key in total_stats:
                total_stats[stat_key] += stats[stat_key]

    if total_stats["total"] > 0:
        log.info(
            "[SIZE-PASS] %s section pass: %d total replacements (run=%s)",
            segment.upper(), total_stats["total"], run_id
        )

    return processed, total_stats


# =============================================================================
# VERIFICATION FUNCTION (for CI/testing)
# =============================================================================

# All forbidden tokens for solo reports (case-insensitive matching)
FORBIDDEN_SOLO_TOKENS = [
    "Governance",
    "Audit-Trail",
    "Audit Trail",
    "Stakeholder",
    "Stack",
    "Layer",
    "Architektur",
    "Rollout",
    "Roll-out",
    "Prozesslandschaft",
    "Baukasten-Prinzip",
    "Baukasten-System",
]

FORBIDDEN_DUZ_TOKENS_PATTERN = re.compile(
    r"\b(du|dir|dein|deine|deinem|deinen|deiner|deines|dich|euch|euer|eure|eurem|euren|eurer|eures)\b",
    re.IGNORECASE,
)


def verify_solo_report_clean(
    html: str,
    check_enterprise: bool = True,
    check_duz: bool = True,
    check_kpi: bool = False,
) -> Dict[str, Any]:
    """
    Verify that a solo report is clean of forbidden tokens.

    Args:
        html: Report HTML to verify
        check_enterprise: Check for enterprise terms
        check_duz: Check for Duz-forms
        check_kpi: Check for KPI terms (optional)

    Returns:
        Dict with verification results:
        {
            "passed": bool,
            "enterprise_violations": [...],
            "duz_violations": [...],
            "kpi_violations": [...],
            "total_violations": int,
        }
    """
    # Strip HTML tags for text-only scanning
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)

    result: Dict[str, Any] = {
        "passed": True,
        "enterprise_violations": [],
        "duz_violations": [],
        "kpi_violations": [],
        "total_violations": 0,
    }

    if check_enterprise:
        for token in FORBIDDEN_SOLO_TOKENS:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                for m in matches:
                    # Get context
                    idx = text.lower().find(m.lower())
                    start = max(0, idx - 30)
                    end = min(len(text), idx + len(m) + 30)
                    context = text[start:end]
                    result["enterprise_violations"].append({
                        "token": token,
                        "matched": m,
                        "context": f"...{context}...",
                    })
                result["total_violations"] += len(matches)

    if check_duz:
        for m in FORBIDDEN_DUZ_TOKENS_PATTERN.finditer(text):
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            context = text[start:end]
            result["duz_violations"].append({
                "token": m.group(0),
                "context": f"...{context}...",
            })
            result["total_violations"] += 1

    if check_kpi:
        kpi_pattern = re.compile(r"\bKPI\b", re.IGNORECASE)
        for m in kpi_pattern.finditer(text):
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            context = text[start:end]
            result["kpi_violations"].append({
                "token": "KPI",
                "context": f"...{context}...",
            })
            result["total_violations"] += 1

    result["passed"] = result["total_violations"] == 0
    return result


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[FIX-554] solo_final_pass initialized: %d enterprise rules, %d duz rules, %d kpi rules",
    len(ENTERPRISE_TERM_REPLACEMENTS),
    len(DUZ_TO_SIE_REPLACEMENTS),
    len(KPI_REPLACEMENTS),
)
