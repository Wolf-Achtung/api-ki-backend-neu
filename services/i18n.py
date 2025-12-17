# -*- coding: utf-8 -*-
"""
services.i18n
-------------
Multilingual v1 Step 3: Internationalization label loader and getter.

Provides:
- Cached loading of i18n/ui_labels.json
- get_label(key, lang) for retrieving translated labels
- ui(lang) Jinja2-compatible wrapper for templates

Version: 1.0.0 (Multilingual v1)
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

def ui(lang: str) -> Callable[[str, Optional[str]], str]:
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
