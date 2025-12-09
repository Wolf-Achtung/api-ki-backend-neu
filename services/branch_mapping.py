# -*- coding: utf-8 -*-
"""
Sprint G19.1-MAP: Frontend-Branch to Engine Mapping

Maps the 12 frontend dropdown branch values to the 11 branch profiles
in branch_profile_engine.py (G19+G19.1).

The mapping chain:
  Frontend-Value → BRANCH_MAPPING → Branch-Engine-Key

Version: 1.0.0 (Sprint G19.1-MAP)
"""
from __future__ import annotations

import logging
from typing import Dict

log = logging.getLogger(__name__)

# =============================================================================
# FRONTEND → ENGINE MAPPING
# =============================================================================

# Frontend dropdown "value" attributes → internal Branch-Keys from branch_profile_engine.py
BRANCH_MAPPING: Dict[str, str] = {
    "marketing_werbung": "marketing",
    "beratung_dienstleistungen": "beratung",
    "it_software": "it",
    "finanzen_versicherungen": "finanzen",
    "handel_ecommerce": "handel",
    "bildung": "bildung",
    "verwaltung": "verwaltung",
    "gesundheit_pflege": "gesundheit",
    "bauwesen_architektur": "bauwesen_architektur",
    # Medien & Kreativwirtschaft maps to marketing profile
    "medien_kreativwirtschaft": "marketing",
    "industrie_produktion": "industrie",
    "transport_logistik": "transport_logistik",
}

# =============================================================================
# SYNONYMS FOR LEGACY DATA / ALTERNATE FORMATS
# =============================================================================

# Text synonyms (labels, alt-data) → frontend value keys
BRANCH_SYNONYMS: Dict[str, str] = {
    # German labels with & and spaces
    "marketing & werbung": "marketing_werbung",
    "marketing und werbung": "marketing_werbung",
    "beratung & dienstleistungen": "beratung_dienstleistungen",
    "beratung und dienstleistungen": "beratung_dienstleistungen",
    "it & software": "it_software",
    "it und software": "it_software",
    "finanzen & versicherungen": "finanzen_versicherungen",
    "finanzen und versicherungen": "finanzen_versicherungen",
    "handel & e-commerce": "handel_ecommerce",
    "handel und e-commerce": "handel_ecommerce",
    "handel & ecommerce": "handel_ecommerce",
    "gesundheit & pflege": "gesundheit_pflege",
    "gesundheit und pflege": "gesundheit_pflege",
    "medien & kreativwirtschaft": "medien_kreativwirtschaft",
    "medien und kreativwirtschaft": "medien_kreativwirtschaft",
    "industrie & produktion": "industrie_produktion",
    "industrie und produktion": "industrie_produktion",
    "transport & logistik": "transport_logistik",
    "transport und logistik": "transport_logistik",
    "bauwesen & architektur": "bauwesen_architektur",
    "bauwesen und architektur": "bauwesen_architektur",
    # Short forms and English variants
    "bau": "bauwesen_architektur",
    "construction": "bauwesen_architektur",
    "architecture": "bauwesen_architektur",
    "architektur": "bauwesen_architektur",
    "public_sector": "verwaltung",
    "public sector": "verwaltung",
    "public": "verwaltung",
    "government": "verwaltung",
    "behoerde": "verwaltung",
    "behörde": "verwaltung",
    "logistik": "transport_logistik",
    "transport": "transport_logistik",
    "logistics": "transport_logistik",
    "spedition": "transport_logistik",
    "media": "medien_kreativwirtschaft",
    "creative": "medien_kreativwirtschaft",
    "kreativ": "medien_kreativwirtschaft",
    # Direct engine keys (passthrough)
    "marketing": "marketing_werbung",
    "beratung": "beratung_dienstleistungen",
    "it": "it_software",
    "finanzen": "finanzen_versicherungen",
    "handel": "handel_ecommerce",
    "gesundheit": "gesundheit_pflege",
    "industrie": "industrie_produktion",
    # Legacy/alternate formats
    "consulting": "beratung_dienstleistungen",
    "dienstleistung": "beratung_dienstleistungen",
    "dienstleistungen": "beratung_dienstleistungen",
    "software": "it_software",
    "tech": "it_software",
    "technologie": "it_software",
    "finance": "finanzen_versicherungen",
    "banking": "finanzen_versicherungen",
    "versicherung": "finanzen_versicherungen",
    "retail": "handel_ecommerce",
    "ecommerce": "handel_ecommerce",
    "e-commerce": "handel_ecommerce",
    "einzelhandel": "handel_ecommerce",
    "health": "gesundheit_pflege",
    "healthcare": "gesundheit_pflege",
    "medizin": "gesundheit_pflege",
    "pharma": "gesundheit_pflege",
    "pflege": "gesundheit_pflege",
    "education": "bildung",
    "training": "bildung",
    "schule": "bildung",
    "hochschule": "bildung",
    "manufacturing": "industrie_produktion",
    "produktion": "industrie_produktion",
    "fertigung": "industrie_produktion",
    "werbung": "marketing_werbung",
    "agentur": "marketing_werbung",
    "medien": "medien_kreativwirtschaft",
    "immobilien": "bauwesen_architektur",
    "real_estate": "bauwesen_architektur",
    "real estate": "bauwesen_architektur",
    "baugewerbe": "bauwesen_architektur",
    "warehousing": "transport_logistik",
    "lager": "transport_logistik",
    "supply_chain": "transport_logistik",
    "supply chain": "transport_logistik",
    "kommune": "verwaltung",
    "oeffentlich": "verwaltung",
    "öffentlich": "verwaltung",
    "oeffentlicher_dienst": "verwaltung",
    "öffentlicher dienst": "verwaltung",
    "administration": "verwaltung",
}


# =============================================================================
# NORMALIZATION HELPERS
# =============================================================================

def _normalize(value: str) -> str:
    """
    Normalize a branch value for matching.

    Handles:
    - Lowercase conversion
    - Umlaut replacement (ä→ae, ö→oe, ü→ue, ß→ss)
    - Special character normalization (&, -, /)
    - Whitespace normalization
    """
    if not value:
        return ""

    v = value.strip().lower()

    # Umlaut replacement
    v = v.replace("ä", "ae")
    v = v.replace("ö", "oe")
    v = v.replace("ü", "ue")
    v = v.replace("ß", "ss")

    # Special characters to spaces
    for ch in ["&", "-", "/"]:
        v = v.replace(ch, " ")

    # Normalize whitespace
    v = " ".join(v.split())

    return v


def _normalize_to_key(value: str) -> str:
    """
    Normalize value to underscore-separated key format.

    E.g., "Beratung & Dienstleistungen" → "beratung_dienstleistungen"
    """
    normalized = _normalize(value)
    return normalized.replace(" ", "_")


# =============================================================================
# MAIN MAPPING FUNCTION
# =============================================================================

def map_frontend_branch_to_engine(raw_value: str) -> str:
    """
    Map a frontend branch value to the internal engine key.

    Takes the branch value from the questionnaire (dropdown value or label)
    and returns the internal branch key expected by:
    - branch_profile_engine.py
    - tools_analytics.py
    - funding_recommender.py

    Args:
        raw_value: Raw branch value from frontend (value or label)

    Returns:
        Internal branch key for the engine (e.g., "beratung", "it", "verwaltung")

    Example:
        >>> map_frontend_branch_to_engine("beratung_dienstleistungen")
        "beratung"
        >>> map_frontend_branch_to_engine("Beratung & Dienstleistungen")
        "beratung"
        >>> map_frontend_branch_to_engine("construction")
        "bauwesen_architektur"
    """
    if not raw_value:
        log.debug("[G19.1-MAP] Empty branch value, defaulting to 'beratung'")
        return "beratung"

    # 1) Direct match on frontend value key (e.g., "beratung_dienstleistungen")
    key = raw_value.strip().lower()
    if key in BRANCH_MAPPING:
        result = BRANCH_MAPPING[key]
        log.debug("[G19.1-MAP] Direct match: '%s' → '%s'", raw_value, result)
        return result

    # 2) Match via synonym (e.g., "Beratung & Dienstleistungen")
    norm = raw_value.strip().lower()
    if norm in BRANCH_SYNONYMS:
        mapped_frontend_key = BRANCH_SYNONYMS[norm]
        result = BRANCH_MAPPING.get(mapped_frontend_key, "beratung")
        log.debug("[G19.1-MAP] Synonym match: '%s' → '%s' → '%s'", raw_value, mapped_frontend_key, result)
        return result

    # 3) Match via normalized form (handles umlauts, special chars)
    norm2 = _normalize(raw_value)
    if norm2 in BRANCH_SYNONYMS:
        mapped_frontend_key = BRANCH_SYNONYMS[norm2]
        result = BRANCH_MAPPING.get(mapped_frontend_key, "beratung")
        log.debug("[G19.1-MAP] Normalized synonym match: '%s' → '%s' → '%s'", raw_value, mapped_frontend_key, result)
        return result

    # 4) Try underscore-normalized key format
    norm_key = _normalize_to_key(raw_value)
    if norm_key in BRANCH_MAPPING:
        result = BRANCH_MAPPING[norm_key]
        log.debug("[G19.1-MAP] Key-normalized match: '%s' → '%s'", raw_value, result)
        return result

    # 5) Check if raw value is already an engine key
    from services.branch_profile_engine import BRANCH_MATURITY_DATA, BRANCH_ALIASES
    if key in BRANCH_MATURITY_DATA:
        log.debug("[G19.1-MAP] Already engine key: '%s'", raw_value)
        return key

    # 6) Try branch_profile_engine's own alias resolution
    if key in BRANCH_ALIASES:
        result = BRANCH_ALIASES[key]
        log.debug("[G19.1-MAP] Engine alias match: '%s' → '%s'", raw_value, result)
        return result

    # 7) Fallback to default
    log.warning("[G19.1-MAP] Unknown branch '%s', defaulting to 'beratung'", raw_value)
    return "beratung"


def get_all_supported_branches() -> list[str]:
    """
    Return list of all supported internal branch keys.

    Returns:
        List of unique branch engine keys
    """
    return list(set(BRANCH_MAPPING.values()))


def get_frontend_branch_options() -> list[tuple[str, str]]:
    """
    Return list of (value, label) tuples for frontend dropdown.

    Returns:
        List of (value, label) tuples for HTML select options
    """
    return [
        ("marketing_werbung", "Marketing & Werbung"),
        ("beratung_dienstleistungen", "Beratung & Dienstleistungen"),
        ("it_software", "IT & Software"),
        ("finanzen_versicherungen", "Finanzen & Versicherungen"),
        ("handel_ecommerce", "Handel & E-Commerce"),
        ("bildung", "Bildung"),
        ("verwaltung", "Verwaltung"),
        ("gesundheit_pflege", "Gesundheit & Pflege"),
        ("bauwesen_architektur", "Bauwesen & Architektur"),
        ("medien_kreativwirtschaft", "Medien & Kreativwirtschaft"),
        ("industrie_produktion", "Industrie & Produktion"),
        ("transport_logistik", "Transport & Logistik"),
    ]


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G19.1-MAP] Branch Mapping loaded - %d frontend values, %d synonyms",
    len(BRANCH_MAPPING),
    len(BRANCH_SYNONYMS),
)
