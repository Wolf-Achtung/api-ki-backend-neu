# -*- coding: utf-8 -*-
"""
services.i18n
-------------
Multilingual v1 Step 3: Internationalization label loader and getter.

Provides:
- Cached loading of i18n/ui_labels.json
- get_label(key, lang) for retrieving translated labels
- ui(lang) Jinja2-compatible wrapper for templates
- get_label_for_segment(key, lang, segment) for segment-aware labels (SOLO Final Polish)
- ui_for_segment(lang, segment) for segment-aware Jinja2 wrapper

Version: 1.1.0 (Multilingual v1 + SOLO Final Polish)
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from services.lang_utils import normalize_lang

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Path to the UI labels JSON file (relative to project root)
_LABELS_FILE = Path(__file__).parent.parent / "i18n" / "ui_labels.json"

# Required languages that must be present in the labels file
_REQUIRED_LANGS = {"de", "en"}

# =============================================================================
# CACHE
# =============================================================================

_LABELS_CACHE: Optional[Dict[str, Dict[str, str]]] = None


def _load_labels_from_file() -> Dict[str, Dict[str, str]]:
    """
    Load labels from JSON file.

    Returns:
        Dict mapping label keys to lang->text dicts, or empty dict on error
    """
    if not _LABELS_FILE.exists():
        log.warning("[i18n] Labels file not found: %s", _LABELS_FILE)
        return {}

    try:
        with open(_LABELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            log.warning("[i18n] Labels file is not a dict")
            return {}

        # Filter out meta keys (starting with _)
        labels = {k: v for k, v in data.items() if not k.startswith("_")}

        # Validate structure: each value should be a dict with lang keys
        valid_labels: Dict[str, Dict[str, str]] = {}
        for key, translations in labels.items():
            if not isinstance(translations, dict):
                log.warning("[i18n] Label '%s' is not a dict, skipping", key)
                continue

            # Check required languages
            missing_langs = _REQUIRED_LANGS - set(translations.keys())
            if missing_langs:
                log.warning("[i18n] Label '%s' missing required langs: %s", key, missing_langs)
                # Still include it, will fallback

            valid_labels[key] = translations

        log.info("[i18n] Loaded %d UI labels from %s", len(valid_labels), _LABELS_FILE.name)
        return valid_labels

    except json.JSONDecodeError as e:
        log.warning("[i18n] JSON parse error in labels file: %s", e)
        return {}
    except Exception as e:
        log.warning("[i18n] Failed to load labels: %s", e)
        return {}


def load_labels() -> Dict[str, Dict[str, str]]:
    """
    Load and cache UI labels from i18n/ui_labels.json.

    Labels are cached per process (loaded once, then reused).

    Returns:
        Dict mapping label keys to {lang: text} dicts
    """
    global _LABELS_CACHE

    if _LABELS_CACHE is not None:
        return _LABELS_CACHE

    _LABELS_CACHE = _load_labels_from_file()
    return _LABELS_CACHE


def reload_labels() -> Dict[str, Dict[str, str]]:
    """
    Force reload labels from file (useful for development/testing).

    Returns:
        Freshly loaded labels dict
    """
    global _LABELS_CACHE
    _LABELS_CACHE = None
    return load_labels()


# =============================================================================
# LABEL GETTER
# =============================================================================

def get_label(
    key: str,
    lang: str,
    fallback: str = "de",
    default: Optional[str] = None
) -> str:
    """
    Get a translated UI label.

    Fallback cascade:
    1. key + normalized lang
    2. key + fallback lang (default: "de")
    3. key + "en" (if fallback != "en")
    4. default (if provided)
    5. key itself (deterministic fallback)

    Args:
        key: Label key (e.g., "company", "recommendations")
        lang: Language code (will be normalized)
        fallback: Fallback language if requested lang not available (default: "de")
        default: Optional default value if key not found (if None, returns key)

    Returns:
        Translated label string

    Examples:
        >>> get_label("company", "en")
        'Company'
        >>> get_label("company", "de")
        'Unternehmen'
        >>> get_label("nonexistent", "en")
        'nonexistent'
        >>> get_label("nonexistent", "en", default="N/A")
        'N/A'
    """
    labels = load_labels()

    # Normalize language
    lang_norm = normalize_lang(lang, default=fallback)

    # Key not found
    if key not in labels:
        if default is not None:
            return default
        return key

    translations = labels[key]

    # Try requested language
    if lang_norm in translations:
        return translations[lang_norm]

    # Try fallback language
    if fallback in translations:
        return translations[fallback]

    # Try English as last resort (if not already tried)
    if fallback != "en" and "en" in translations:
        return translations["en"]

    # Try German as absolute last resort
    if "de" in translations:
        return translations["de"]

    # Return default or key
    if default is not None:
        return default
    return key


def has_label(key: str) -> bool:
    """
    Check if a label key exists.

    Args:
        key: Label key to check

    Returns:
        True if the key exists in labels
    """
    labels = load_labels()
    return key in labels


def get_available_langs(key: str) -> list:
    """
    Get list of available languages for a label.

    Args:
        key: Label key

    Returns:
        List of language codes, or empty list if key not found
    """
    labels = load_labels()
    if key not in labels:
        return []
    return list(labels[key].keys())


# =============================================================================
# JINJA2 WRAPPER
# =============================================================================

def ui(lang: str) -> Callable[..., str]:
    """
    Create a Jinja2-compatible label getter for a specific language.

    Usage in report_renderer.py:
        ctx["ui"] = ui(lang)

    Usage in templates:
        {{ ui("company") }}
        {{ ui("unknown_key", "Default Value") }}

    Args:
        lang: Language code for this template context

    Returns:
        Callable that takes (key, default=None) and returns translated label
    """
    lang_norm = normalize_lang(lang, default="de")

    def _get(key: str, default: Optional[str] = None) -> str:
        return get_label(key, lang=lang_norm, default=default)

    return _get


def ui_label(key: str, lang: str, default: str = "") -> str:
    """
    Direct label getter (alternative to ui() wrapper).

    Useful when you need to get a single label without creating a closure.

    Args:
        key: Label key
        lang: Language code
        default: Default value if key not found (default: "")

    Returns:
        Translated label string
    """
    return get_label(key, lang=lang, default=default if default else None)


# =============================================================================
# SEGMENT-AWARE LABEL GETTER (SOLO Final Polish Briefing)
# =============================================================================

# Canonical segment values
_VALID_SEGMENTS = {"SOLO", "TEAM", "KMU"}


def get_label_for_segment(
    key: str,
    lang: str,
    segment: Optional[str] = None,
    fallback: str = "de",
    default: Optional[str] = None
) -> str:
    """
    Get a translated UI label with segment-aware fallback.

    For SOLO segment, tries segment-specific key first (e.g., key_solo),
    then falls back to the standard key.

    This allows templates to use simplified SOLO terminology:
    - toc_item_summary_solo → "Kurzfassung & Bewertung" (instead of "Executive Summary & Kurzurteil")
    - governance_label_solo → "Spielregeln" (instead of "Governance")

    Lookup cascade:
    1. key + "_" + segment.lower() (e.g., "toc_item_summary_solo")
    2. key (standard fallback)
    3. fallback language
    4. default or key

    Args:
        key: Base label key (e.g., "toc_item_summary", "governance_label")
        lang: Language code (will be normalized)
        segment: Segment identifier (SOLO, TEAM, KMU). None = no segment override.
        fallback: Fallback language if requested lang not available (default: "de")
        default: Optional default value if key not found

    Returns:
        Translated label string, potentially segment-specific

    Examples:
        >>> get_label_for_segment("toc_item_summary", "de", segment="SOLO")
        'Kurzfassung & Bewertung'
        >>> get_label_for_segment("toc_item_summary", "de", segment="TEAM")
        'Executive Summary & Kurzurteil'
        >>> get_label_for_segment("governance_label", "de", segment="SOLO")
        'Spielregeln'
    """
    # Normalize segment
    segment_norm = None
    if segment:
        segment_upper = segment.strip().upper()
        if segment_upper in _VALID_SEGMENTS:
            segment_norm = segment_upper
        else:
            log.debug("[i18n] Unknown segment '%s', using standard label", segment)

    # For SOLO segment, try segment-specific key first
    if segment_norm == "SOLO":
        solo_key = f"{key}_solo"
        labels = load_labels()

        if solo_key in labels:
            result = get_label(solo_key, lang=lang, fallback=fallback, default=None)
            if result and result != solo_key:
                log.debug("[i18n] Using SOLO-specific label: %s → %s", key, result)
                return result

    # Fall back to standard key
    return get_label(key, lang=lang, fallback=fallback, default=default)


def ui_for_segment(lang: str, segment: Optional[str] = None) -> Callable[..., str]:
    """
    Create a Jinja2-compatible segment-aware label getter.

    Usage in report_renderer.py:
        ctx["ui"] = ui_for_segment(lang, segment)

    Usage in templates:
        {{ ui("toc_item_summary") }}  # Returns SOLO-specific if segment is SOLO
        {{ ui("governance_label") }}   # Returns "Spielregeln" for SOLO

    Args:
        lang: Language code for this template context
        segment: Optional segment identifier (SOLO, TEAM, KMU)

    Returns:
        Callable that takes (key, default=None) and returns segment-appropriate label
    """
    lang_norm = normalize_lang(lang, default="de")

    # Normalize segment once
    segment_norm = None
    if segment:
        segment_upper = segment.strip().upper()
        if segment_upper in _VALID_SEGMENTS:
            segment_norm = segment_upper

    def _get(key: str, default: Optional[str] = None) -> str:
        return get_label_for_segment(
            key,
            lang=lang_norm,
            segment=segment_norm,
            default=default
        )

    return _get


# =============================================================================
# Fix-Batch J2: GERMAN NUMBER FORMATTING
# =============================================================================
# Problem: German reports show English decimal points (3.5) instead of commas (3,5)
# and EUR values lack thousand separators (1600€ instead of 1.600 €)
# Solution: Centralized formatting functions for all numeric output
# =============================================================================

def format_decimal_de(value: float, decimals: int = 1) -> str:
    """
    Format a decimal number for German locale.

    Uses comma as decimal separator (German standard).

    Args:
        value: The numeric value to format
        decimals: Number of decimal places (default: 1)

    Returns:
        German-formatted decimal string (e.g., "3,5" instead of "3.5")

    Examples:
        >>> format_decimal_de(3.5)
        '3,5'
        >>> format_decimal_de(12.75, 2)
        '12,75'
        >>> format_decimal_de(100.0, 0)
        '100'
    """
    if decimals == 0:
        return f"{value:.0f}"
    formatted = f"{value:.{decimals}f}"
    return formatted.replace(".", ",")


def format_eur_de(value: float, decimals: int = 0) -> str:
    """
    Format a EUR currency value for German locale.

    Uses:
    - Dot as thousand separator (German standard)
    - Comma as decimal separator
    - Space before € symbol

    Args:
        value: The EUR amount to format
        decimals: Number of decimal places (default: 0)

    Returns:
        German-formatted EUR string (e.g., "1.600 €" instead of "1600€")

    Examples:
        >>> format_eur_de(1600)
        '1.600 €'
        >>> format_eur_de(1234567.89, 2)
        '1.234.567,89 €'
        >>> format_eur_de(50)
        '50 €'
    """
    # Format with decimals
    if decimals > 0:
        formatted = f"{value:,.{decimals}f}"
    else:
        formatted = f"{value:,.0f}"

    # Convert English format to German:
    # 1,234.56 → 1.234,56
    # Step 1: Replace comma with temporary placeholder
    formatted = formatted.replace(",", "_TEMP_")
    # Step 2: Replace period with comma (decimal)
    formatted = formatted.replace(".", ",")
    # Step 3: Replace placeholder with period (thousand)
    formatted = formatted.replace("_TEMP_", ".")

    return f"{formatted} €"


def format_eur_range_de(min_val: float, max_val: float) -> str:
    """
    Format a EUR range for German locale.

    Args:
        min_val: Minimum EUR value
        max_val: Maximum EUR value

    Returns:
        German-formatted range string (e.g., "1.200–1.600 €")

    Examples:
        >>> format_eur_range_de(1200, 1600)
        '1.200–1.600 €'
    """
    min_fmt = format_eur_de(min_val).replace(" €", "")
    max_fmt = format_eur_de(max_val)
    return f"{min_fmt}–{max_fmt}"


# =============================================================================
# SELF-CHECK (for development/debugging)
# =============================================================================

def _self_check() -> None:
    """
    Quick self-check to verify i18n module is working.
    Run with: python -c "from services.i18n import _self_check; _self_check()"
    """
    print("=" * 60)
    print("i18n Self-Check")
    print("=" * 60)

    labels = load_labels()
    print(f"Loaded {len(labels)} labels")

    # Test get_label
    test_cases = [
        ("company", "de"),
        ("company", "en"),
        ("company", "fr"),
        ("recommendations", "en"),
        ("unknown_key", "en"),
    ]

    print("\nget_label() tests:")
    for key, lang in test_cases:
        result = get_label(key, lang)
        print(f"  get_label('{key}', '{lang}') = '{result}'")

    # Test ui() wrapper
    print("\nui() wrapper tests:")
    ui_en = ui("en")
    ui_de = ui("de")
    print(f"  ui('en')('company') = '{ui_en('company')}'")
    print(f"  ui('de')('company') = '{ui_de('company')}'")
    print(f"  ui('en')('missing', 'DEFAULT') = '{ui_en('missing', 'DEFAULT')}'")

    print("\n" + "=" * 60)
    print("Self-check complete!")


if __name__ == "__main__":
    # Run self-check when executed directly
    _self_check()
