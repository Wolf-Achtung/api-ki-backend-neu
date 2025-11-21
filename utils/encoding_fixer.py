# -*- coding: utf-8 -*-
"""
UTF-8 Encoding fixer for German umlauts.
Fixes double-encoded UTF-8 characters (Mojibake).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


def fix_utf8_encoding(text: str) -> str:
    """
    Fix double-encoded UTF-8 German umlauts.

    Examples:
        "FragebÃ¶gen" -> "Fragebögen"
        "MarktfÃ¼hrer" -> "Marktführer"

    Args:
        text: Input string that may contain Mojibake

    Returns:
        Fixed string with correct German umlauts
    """
    if not isinstance(text, str):
        return text

    # Quick check if there's anything to fix
    if 'Ã' not in text and 'â' not in text:
        return text

    # Direct replacements for common Mojibake patterns
    replacements = {
        'Ã¤': 'ä', 'Ã¶': 'ö', 'Ã¼': 'ü',
        'Ã„': 'Ä', 'Ã–': 'Ö', 'Ãœ': 'Ü',
        'ÃŸ': 'ß', 'Ã©': 'é', 'Ã¨': 'è',
        'Ã ': 'à', 'Ã¡': 'á', 'Ãª': 'ê',
        'Ã®': 'î', 'Ã¯': 'ï', 'Ã´': 'ô',
        'Ã¹': 'ù', 'Ãº': 'ú', 'Ã±': 'ñ',
        'â€™': "'", 'â€œ': '"', 'â€': '"',
        'â€"': '–', 'â€"': '—', 'â€¢': '•',
    }

    original = text
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    # Fallback: encode/decode trick for remaining issues
    if 'Ã' in text:
        try:
            text = text.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass

    if original != text:
        logger.debug(f"[ENCODING-FIX] Fixed: '{original[:50]}...' -> '{text[:50]}...'")

    return text


def clean_briefing_data(data: Union[Dict, List, str, Any]) -> Union[Dict, List, str, Any]:
    """
    Recursively clean all strings in data structure.

    Args:
        data: Dictionary, list, string, or other data type

    Returns:
        Cleaned data with all strings fixed for UTF-8 encoding
    """
    if isinstance(data, dict):
        return {key: clean_briefing_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_briefing_data(item) for item in data]
    elif isinstance(data, str):
        return fix_utf8_encoding(data)
    else:
        return data
