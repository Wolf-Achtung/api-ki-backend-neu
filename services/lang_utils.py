# -*- coding: utf-8 -*-
"""
services.lang_utils
-------------------
Multilingual v1 Step 1: Unified language normalization utilities.

Provides consistent language code normalization across the backend:
- Supports: de, en, fr, es, it
- Normalizes variants like EN, en-US, en_GB, DE-de, fr-FR, etc.
- Single source of truth for language handling

Version: 1.0.0 (Multilingual v1)
"""
from __future__ import annotations

from typing import Any

# Supported language codes (ISO 639-1)
SUPPORTED_LANGS = ("de", "en", "fr", "es", "it")


def normalize_lang(raw: Any, default: str = "de") -> str:
    """
    Normalize a language code to a supported base language.

    Handles various input formats:
    - None, empty strings, non-string types
    - Uppercase: "EN" -> "en"
    - Locale variants: "en-US", "en_GB", "de-DE", "fr_FR" -> base code
    - Whitespace: "  en  " -> "en"

    Args:
        raw: Raw language value (any type, will be converted to str)
        default: Fallback language if normalization fails (default: "de")

    Returns:
        Normalized language code from SUPPORTED_LANGS, or default

    Examples:
        >>> normalize_lang("en-US")
        'en'
        >>> normalize_lang("EN")
        'en'
        >>> normalize_lang("fr_FR")
        'fr'
        >>> normalize_lang("pt")  # unsupported
        'de'
        >>> normalize_lang(None)
        'de'
        >>> normalize_lang("")
        'de'
    """
    # Handle None, empty, or non-string input
    if raw is None:
        return default

    # Convert to string and normalize
    lang_str = str(raw).strip().lower()

    if not lang_str:
        return default

    # Extract base language (before any separator)
    # Handles: en-US, en_GB, de-DE, fr_FR, es-ES, it-IT, etc.
    if "-" in lang_str:
        lang_str = lang_str.split("-")[0]
    elif "_" in lang_str:
        lang_str = lang_str.split("_")[0]

    # Check if the base language is supported
    if lang_str in SUPPORTED_LANGS:
        return lang_str

    # Check prefix match for edge cases (e.g., "english" -> "en")
    # This is a safety net, not expected in normal usage
    for supported in SUPPORTED_LANGS:
        if lang_str.startswith(supported):
            return supported

    # Fallback to default
    return default


def is_lang_supported(lang: str) -> bool:
    """
    Check if a language code is supported.

    Args:
        lang: Language code to check (should be normalized first)

    Returns:
        True if the language is in SUPPORTED_LANGS

    Examples:
        >>> is_lang_supported("en")
        True
        >>> is_lang_supported("pt")
        False
    """
    return lang in SUPPORTED_LANGS


def get_supported_langs() -> tuple:
    """
    Get the tuple of supported language codes.

    Returns:
        Tuple of supported language codes: ("de", "en", "fr", "es", "it")
    """
    return SUPPORTED_LANGS
