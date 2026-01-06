# -*- coding: utf-8 -*-
"""
Phase 5C: Centralized Validation Helpers & Constants.

Centralizes all validation logic and constants for questionnaire data
to ensure consistency across different services.

This module provides:
- All 13 Branchen from questionnaire
- Company size values (Frontend V2 + Legacy)
- Bundesland codes
- Validation functions with clear error messages
- Type-safe normalization functions

Version: 1.0.0 (Phase 5C - 2026-01-06)
Author: Claude + Wolf
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# COMPANY SIZE CONSTANTS
# =============================================================================

# Internal size values (used throughout backend)
SIZE_SOLO = "solo"      # 1 person (Solo-Selbstständig/Freiberuflich)
SIZE_SMALL = "small"    # 2-10 persons (Kleines Team)
SIZE_MEDIUM = "medium"  # 11-100 persons (KMU)

# Frontend V2 size values (from questionnaire, since 2026-01-06)
FRONTEND_SIZE_SOLO = "1"
FRONTEND_SIZE_SMALL = "2–10"           # En-Dash (U+2013)
FRONTEND_SIZE_SMALL_ALT = "2-10"       # Hyphen-Minus (U+002D) - alternative
FRONTEND_SIZE_MEDIUM = "11–100"        # En-Dash (U+2013)
FRONTEND_SIZE_MEDIUM_ALT = "11-100"    # Hyphen-Minus (U+002D) - alternative

# Legacy size values (for backward compatibility with pre-2026-01-06 data)
LEGACY_SIZE_SOLO = "solo"
LEGACY_SIZE_SMALL = "team"
LEGACY_SIZE_MEDIUM = "kmu"

# All valid size values (for validation)
VALID_SIZE_VALUES: Set[str] = {
    # Frontend V2
    FRONTEND_SIZE_SOLO,
    FRONTEND_SIZE_SMALL, FRONTEND_SIZE_SMALL_ALT,
    FRONTEND_SIZE_MEDIUM, FRONTEND_SIZE_MEDIUM_ALT,
    # Legacy
    LEGACY_SIZE_SOLO, LEGACY_SIZE_SMALL, LEGACY_SIZE_MEDIUM,
    # Internal (also accepted)
    SIZE_SOLO, SIZE_SMALL, SIZE_MEDIUM,
}

# Size multipliers for calculations (used in business case, benchmark, etc.)
SIZE_MULTIPLIERS: Dict[str, float] = {
    SIZE_SOLO: 0.6,    # Lower complexity for solo entrepreneurs
    SIZE_SMALL: 1.0,   # Base multiplier
    SIZE_MEDIUM: 1.4,  # Higher complexity for established SMEs
}


# =============================================================================
# BRANCHEN CONSTANTS (13 from questionnaire)
# =============================================================================

# Branche values (lowercase keys, German labels)
BRANCHE_MARKETING = "marketing"
BRANCHE_BERATUNG = "beratung"
BRANCHE_IT = "it"
BRANCHE_FINANZEN = "finanzen"
BRANCHE_HANDEL = "handel"
BRANCHE_BILDUNG = "bildung"
BRANCHE_VERWALTUNG = "verwaltung"
BRANCHE_GESUNDHEIT = "gesundheit"
BRANCHE_BAU = "bau"
BRANCHE_MEDIEN = "medien"
BRANCHE_INDUSTRIE = "industrie"
BRANCHE_LOGISTIK = "logistik"
BRANCHE_GASTRONOMIE = "gastronomie"

# All supported Branchen (for validation)
ALL_BRANCHEN: List[str] = [
    BRANCHE_MARKETING,       # 1. Marketing & Werbung
    BRANCHE_BERATUNG,        # 2. Beratung & Dienstleistungen
    BRANCHE_IT,              # 3. IT & Software
    BRANCHE_FINANZEN,        # 4. Finanzen & Versicherungen
    BRANCHE_HANDEL,          # 5. Handel & E-Commerce
    BRANCHE_BILDUNG,         # 6. Bildung
    BRANCHE_VERWALTUNG,      # 7. Verwaltung
    BRANCHE_GESUNDHEIT,      # 8. Gesundheit & Pflege
    BRANCHE_BAU,             # 9. Bauwesen & Architektur
    BRANCHE_MEDIEN,          # 10. Medien & Kreativwirtschaft
    BRANCHE_INDUSTRIE,       # 11. Industrie & Produktion
    BRANCHE_LOGISTIK,        # 12. Transport & Logistik
    BRANCHE_GASTRONOMIE,     # 13. Gastronomie & Tourismus
]

# Set for O(1) lookup
ALL_BRANCHEN_SET: Set[str] = set(ALL_BRANCHEN)

# Branchen with display labels (for UI/reports)
BRANCHEN_LABELS: Dict[str, str] = {
    BRANCHE_MARKETING: "Marketing & Werbung",
    BRANCHE_BERATUNG: "Beratung & Dienstleistungen",
    BRANCHE_IT: "IT & Software",
    BRANCHE_FINANZEN: "Finanzen & Versicherungen",
    BRANCHE_HANDEL: "Handel & E-Commerce",
    BRANCHE_BILDUNG: "Bildung",
    BRANCHE_VERWALTUNG: "Verwaltung",
    BRANCHE_GESUNDHEIT: "Gesundheit & Pflege",
    BRANCHE_BAU: "Bauwesen & Architektur",
    BRANCHE_MEDIEN: "Medien & Kreativwirtschaft",
    BRANCHE_INDUSTRIE: "Industrie & Produktion",
    BRANCHE_LOGISTIK: "Transport & Logistik",
    BRANCHE_GASTRONOMIE: "Gastronomie & Tourismus",
}

# Branche aliases for normalization
BRANCHE_ALIASES: Dict[str, str] = {
    # Marketing & Werbung
    "marketing": BRANCHE_MARKETING,
    "werbung": BRANCHE_MARKETING,
    "marketing & werbung": BRANCHE_MARKETING,
    # Beratung & Dienstleistungen
    "beratung": BRANCHE_BERATUNG,
    "dienstleistungen": BRANCHE_BERATUNG,
    "beratung & dienstleistungen": BRANCHE_BERATUNG,
    "consulting": BRANCHE_BERATUNG,
    # IT & Software
    "it": BRANCHE_IT,
    "software": BRANCHE_IT,
    "it & software": BRANCHE_IT,
    "technologie": BRANCHE_IT,
    "tech": BRANCHE_IT,
    # Finanzen & Versicherungen
    "finanzen": BRANCHE_FINANZEN,
    "versicherungen": BRANCHE_FINANZEN,
    "finanzen & versicherungen": BRANCHE_FINANZEN,
    "banking": BRANCHE_FINANZEN,
    "finance": BRANCHE_FINANZEN,
    # Handel & E-Commerce
    "handel": BRANCHE_HANDEL,
    "e-commerce": BRANCHE_HANDEL,
    "handel & e-commerce": BRANCHE_HANDEL,
    "ecommerce": BRANCHE_HANDEL,
    "retail": BRANCHE_HANDEL,
    # Bildung
    "bildung": BRANCHE_BILDUNG,
    "education": BRANCHE_BILDUNG,
    "schulung": BRANCHE_BILDUNG,
    # Verwaltung
    "verwaltung": BRANCHE_VERWALTUNG,
    "administration": BRANCHE_VERWALTUNG,
    "public": BRANCHE_VERWALTUNG,
    # Gesundheit & Pflege
    "gesundheit": BRANCHE_GESUNDHEIT,
    "pflege": BRANCHE_GESUNDHEIT,
    "gesundheit & pflege": BRANCHE_GESUNDHEIT,
    "healthcare": BRANCHE_GESUNDHEIT,
    "health": BRANCHE_GESUNDHEIT,
    # Bauwesen & Architektur
    "bau": BRANCHE_BAU,
    "architektur": BRANCHE_BAU,
    "bauwesen": BRANCHE_BAU,
    "bauwesen & architektur": BRANCHE_BAU,
    "construction": BRANCHE_BAU,
    "handwerk": BRANCHE_BAU,
    # Medien & Kreativwirtschaft
    "medien": BRANCHE_MEDIEN,
    "kreativwirtschaft": BRANCHE_MEDIEN,
    "medien & kreativwirtschaft": BRANCHE_MEDIEN,
    "creative": BRANCHE_MEDIEN,
    "media": BRANCHE_MEDIEN,
    "kreativ": BRANCHE_MEDIEN,
    # Industrie & Produktion
    "industrie": BRANCHE_INDUSTRIE,
    "produktion": BRANCHE_INDUSTRIE,
    "industrie & produktion": BRANCHE_INDUSTRIE,
    "manufacturing": BRANCHE_INDUSTRIE,
    # Transport & Logistik
    "logistik": BRANCHE_LOGISTIK,
    "transport": BRANCHE_LOGISTIK,
    "transport & logistik": BRANCHE_LOGISTIK,
    "logistics": BRANCHE_LOGISTIK,
    # Gastronomie & Tourismus
    "gastronomie": BRANCHE_GASTRONOMIE,
    "tourismus": BRANCHE_GASTRONOMIE,
    "gastronomie & tourismus": BRANCHE_GASTRONOMIE,
    "hospitality": BRANCHE_GASTRONOMIE,
    "tourism": BRANCHE_GASTRONOMIE,
    "restaurant": BRANCHE_GASTRONOMIE,
    "hotel": BRANCHE_GASTRONOMIE,
}


# =============================================================================
# BUNDESLAND CONSTANTS
# =============================================================================

# German Bundesland codes (lowercase)
BUNDESLAND_CODES: Dict[str, str] = {
    "bw": "Baden-Württemberg",
    "by": "Bayern",
    "be": "Berlin",
    "bb": "Brandenburg",
    "hb": "Bremen",
    "hh": "Hamburg",
    "he": "Hessen",
    "mv": "Mecklenburg-Vorpommern",
    "ni": "Niedersachsen",
    "nw": "Nordrhein-Westfalen",
    "rp": "Rheinland-Pfalz",
    "sl": "Saarland",
    "sn": "Sachsen",
    "st": "Sachsen-Anhalt",
    "sh": "Schleswig-Holstein",
    "th": "Thüringen",
}

# All valid Bundesland codes (for validation)
ALL_BUNDESLAND_CODES: Set[str] = set(BUNDESLAND_CODES.keys())


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_branche(branche: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate branche value from questionnaire.

    Supports all 13 Branchen from questionnaire (updated 2026-01-06):
    1. Marketing & Werbung
    2. Beratung & Dienstleistungen
    3. IT & Software
    4. Finanzen & Versicherungen
    5. Handel & E-Commerce
    6. Bildung
    7. Verwaltung
    8. Gesundheit & Pflege
    9. Bauwesen & Architektur
    10. Medien & Kreativwirtschaft
    11. Industrie & Produktion
    12. Transport & Logistik
    13. Gastronomie & Tourismus

    Args:
        branche: Branche value to validate

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_branche("marketing")
        (True, None)
        >>> validate_branche("invalid")
        (False, "Unknown branche: invalid. Valid values: marketing, beratung, ...")
    """
    if not branche:
        return False, "Branche is required"

    branche_str = str(branche).strip().lower()

    # Check direct match
    if branche_str in ALL_BRANCHEN_SET:
        return True, None

    # Check aliases
    if branche_str in BRANCHE_ALIASES:
        return True, None

    valid_list = ", ".join(ALL_BRANCHEN[:5]) + "..."
    return False, f"Unknown branche: {branche}. Valid values: {valid_list}"


def validate_company_size(size: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate company size value from questionnaire.

    Accepts both Frontend V2 ("1", "2–10", "11–100") and legacy formats.

    **Frontend V2 (current, since 2026-01-06):**
    - "1" → Solo-Selbstständig
    - "2–10" → Kleines Team
    - "11–100" → KMU

    **Legacy Format (pre-2026-01-06):**
    - "solo", "team", "kmu"

    Args:
        size: Company size value to validate

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_company_size("1")
        (True, None)
        >>> validate_company_size("2–10")
        (True, None)
        >>> validate_company_size("team")  # Legacy
        (True, None)
    """
    if not size:
        return False, "Company size is required"

    size_str = str(size).strip().lower()

    # Check all valid values (case-insensitive)
    if size_str in {v.lower() for v in VALID_SIZE_VALUES}:
        return True, None

    return False, f"Invalid company size: {size}. Valid values: 1, 2–10, 11–100 (or legacy: solo, team, kmu)"


def validate_bundesland(bundesland: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate Bundesland code.

    Accepts 2-letter codes (case-insensitive):
    bw, by, be, bb, hb, hh, he, mv, ni, nw, rp, sl, sn, st, sh, th

    Args:
        bundesland: Bundesland code to validate

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_bundesland("nw")
        (True, None)
        >>> validate_bundesland("NW")  # Case-insensitive
        (True, None)
        >>> validate_bundesland(None)
        (True, None)  # Optional field
    """
    if not bundesland:
        return True, None  # Optional field

    bundesland_str = str(bundesland).strip().lower()

    if bundesland_str in ALL_BUNDESLAND_CODES:
        return True, None

    valid_codes = ", ".join(sorted(ALL_BUNDESLAND_CODES))
    return False, f"Invalid Bundesland code: {bundesland}. Valid codes: {valid_codes}"


# =============================================================================
# NORMALIZATION FUNCTIONS
# =============================================================================

def normalize_company_size(size: Any) -> str:
    """
    Normalize company size to internal standard values.

    This function supports both current frontend (V2, since 2026-01-06)
    and legacy data formats for backward compatibility.

    **Frontend V2 (current):**
    - Input: "1", "2–10", "11–100"
    - Direct string matching (fast path)

    **Legacy Format (pre-2026-01-06):**
    - Input: "solo", "team", "kmu"
    - Keyword-based fallback (for old data)

    **Internal Values (output):**
    - "solo": 1 person (Solo-Selbstständig)
    - "small": 2-10 persons (Kleines Team)
    - "medium": 11-100 persons (KMU)

    Args:
        size: Company size from questionnaire or legacy data.
              Can be str, int, or None.

    Returns:
        str: Normalized size ("solo", "small", or "medium")

    Examples:
        >>> normalize_company_size("1")
        'solo'
        >>> normalize_company_size("2–10")
        'small'
        >>> normalize_company_size("11–100")
        'medium'
        >>> normalize_company_size("team")  # Legacy
        'small'

    Notes:
        - Supports both dash types: "–" (En-Dash) and "-" (Hyphen)
        - Default fallback: "small" (most common use case)
        - Legacy support maintained for data migration period
    """
    # Edge case: None, empty string, or whitespace-only
    if not size or not str(size).strip():
        log.debug("Empty size received, defaulting to 'small'")
        return SIZE_SMALL

    size_str = str(size).strip().lower()

    # --- Frontend V2 (fast path) ---
    # Support both En-Dash (–) and Hyphen (-) from different keyboards
    if size_str == FRONTEND_SIZE_SOLO:
        return SIZE_SOLO
    if size_str in (FRONTEND_SIZE_SMALL.lower(), FRONTEND_SIZE_SMALL_ALT):
        return SIZE_SMALL
    if size_str in (FRONTEND_SIZE_MEDIUM.lower(), FRONTEND_SIZE_MEDIUM_ALT):
        return SIZE_MEDIUM

    # --- Legacy keyword matching (fallback) ---
    # Medium keywords (11-100 Personen)
    if any(kw in size_str for kw in ["medium", "mittel", "kmu"]):
        return SIZE_MEDIUM

    # Small keywords (2-10 Personen)
    if any(kw in size_str for kw in ["small", "klein", "team", "startup"]):
        return SIZE_SMALL

    # Solo keywords (1 Person)
    if any(kw in size_str for kw in ["solo", "einzelunternehmer", "freelancer", "selbststaendig", "freiberuf"]):
        return SIZE_SOLO

    # Edge case: numeric input
    if isinstance(size, (int, float)):
        if size == 1:
            return SIZE_SOLO
        elif 2 <= size <= 10:
            return SIZE_SMALL
        elif 11 <= size <= 100:
            return SIZE_MEDIUM
        else:
            log.warning(f"Company size {size} out of expected range (1-100), defaulting to 'small'")
            return SIZE_SMALL

    # Unknown value - log for monitoring and default
    log.info(
        "Unknown size format detected",
        extra={
            "input_size": str(size),
            "normalized": SIZE_SMALL,
            "needs_review": True
        }
    )
    return SIZE_SMALL


def normalize_branche(branche: Any) -> str:
    """
    Normalize branche input to standard lowercase key.

    Supports all 13 Branchen from questionnaire (updated 2026-01-06):
    marketing, beratung, it, finanzen, handel, bildung, verwaltung,
    gesundheit, bau, medien, industrie, logistik, gastronomie

    Args:
        branche: Branche value from questionnaire or legacy data.
                 Can be str or None.

    Returns:
        str: Normalized branche key (e.g., 'marketing', 'gastronomie')
             Returns 'beratung' as default for unknown values.

    Examples:
        >>> normalize_branche("Marketing & Werbung")
        'marketing'
        >>> normalize_branche("IT & Software")
        'it'
        >>> normalize_branche("Gastronomie & Tourismus")
        'gastronomie'
    """
    # Edge case: None, empty string, or whitespace-only
    if not branche or not str(branche).strip():
        log.debug("Empty branche received, defaulting to 'beratung'")
        return BRANCHE_BERATUNG

    branche_str = str(branche).strip().lower()

    # Handle Umlaute for robust matching
    branche_normalized = (branche_str
        .replace('ä', 'ae')
        .replace('ö', 'oe')
        .replace('ü', 'ue')
        .replace('ß', 'ss'))

    # Check direct match first
    if branche_str in ALL_BRANCHEN_SET:
        return branche_str

    # Check aliases
    if branche_str in BRANCHE_ALIASES:
        return BRANCHE_ALIASES[branche_str]

    # Check normalized version in aliases
    if branche_normalized in BRANCHE_ALIASES:
        return BRANCHE_ALIASES[branche_normalized]

    # Partial match (for compound names like "Marketing & Werbung")
    for alias, normalized in BRANCHE_ALIASES.items():
        if alias in branche_str or branche_str in alias:
            return normalized

    # Unknown branche - log for monitoring
    log.warning(
        f"Unknown branche '{branche}' -> defaulting to 'beratung'",
        extra={
            "input_branche": str(branche),
            "normalized": BRANCHE_BERATUNG,
            "needs_review": True
        }
    )
    return BRANCHE_BERATUNG


def normalize_bundesland(bundesland: Any) -> Optional[str]:
    """
    Normalize Bundesland code to lowercase.

    Args:
        bundesland: Bundesland code (e.g., "NW", "nw", "Nordrhein-Westfalen")

    Returns:
        str: Lowercase 2-letter code (e.g., "nw") or None if invalid/empty

    Examples:
        >>> normalize_bundesland("NW")
        'nw'
        >>> normalize_bundesland("Bayern")
        'by'
    """
    if not bundesland:
        return None

    bundesland_str = str(bundesland).strip().lower()

    # Direct match
    if bundesland_str in ALL_BUNDESLAND_CODES:
        return bundesland_str

    # Full name match
    for code, name in BUNDESLAND_CODES.items():
        if bundesland_str == name.lower():
            return code

    return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_branchen_list() -> List[Dict[str, str]]:
    """
    Get list of all supported Branchen with labels.

    Returns:
        List of dicts with 'value' and 'label' keys.

    Example:
        >>> get_branchen_list()[0]
        {'value': 'marketing', 'label': 'Marketing & Werbung'}
    """
    return [
        {"value": key, "label": label}
        for key, label in BRANCHEN_LABELS.items()
    ]


def get_size_multiplier(size: str) -> float:
    """
    Get size multiplier for calculations.

    Args:
        size: Normalized size ("solo", "small", or "medium")

    Returns:
        float: Multiplier (0.6 for solo, 1.0 for small, 1.4 for medium)
    """
    return SIZE_MULTIPLIERS.get(size, SIZE_MULTIPLIERS[SIZE_SMALL])


def get_branche_label(branche: str) -> str:
    """
    Get display label for branche.

    Args:
        branche: Normalized branche key

    Returns:
        str: German display label
    """
    return BRANCHEN_LABELS.get(branche, branche.title())


def get_bundesland_name(code: str) -> str:
    """
    Get full Bundesland name from code.

    Args:
        code: 2-letter Bundesland code

    Returns:
        str: Full German name
    """
    return BUNDESLAND_CODES.get(code.lower(), code)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[Phase5C-Validators] Loaded with %d Branchen, %d Bundesländer",
    len(ALL_BRANCHEN),
    len(ALL_BUNDESLAND_CODES)
)
