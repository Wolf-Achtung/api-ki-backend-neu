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

import re
import logging
from typing import Tuple, Optional

log = logging.getLogger(__name__)


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
