# -*- coding: utf-8 -*-
"""
Sprint G19.1-MAP: Frontend-Branch to Engine Mapping

Maps the 13 frontend dropdown branch values (canonical per formbuilder_de_SINGLE_FULL.js)
to the 11 branch profiles in branch_profile_engine.py (G19+G19.1).

The mapping chain:
  Frontend-Value → BRANCH_MAPPING → Branch-Engine-Key

13 Canonical branches:
  marketing, beratung, it, finanzen, handel, bildung, verwaltung,
  gesundheit, bau, medien, industrie, logistik, gastronomie

Version: 1.2.0 (FIX-BRANCH-UNMAPPED)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

log = logging.getLogger(__name__)


# =============================================================================
# BRANCH MAPPING RESULT (FIX-BRANCH-UNMAPPED)
# =============================================================================

@dataclass
class BranchMappingResult:
    """
    Result of branch mapping with metadata about the mapping process.

    FIX-BRANCH-UNMAPPED: Includes flag to indicate unmapped/unknown input.
    """
    canonical: str          # The canonical engine branch key
    original: str           # The original input value
    match_type: str         # How it was matched: 'direct', 'synonym', 'alias', 'fallback'
    unmapped: bool = False  # True if original was not found, fallback was used

    @property
    def branch(self) -> str:
        """Alias for canonical (backwards compatibility)."""
        return self.canonical

# =============================================================================
# FRONTEND → ENGINE MAPPING
# =============================================================================

# Frontend dropdown "value" attributes → internal Branch-Keys from branch_profile_engine.py
# FIX-BRANCH-13: 13 canonical values from formbuilder_de_SINGLE_FULL.js
BRANCH_MAPPING: Dict[str, str] = {
    # =========================================================================
    # CANONICAL 13 FORM VALUES (formbuilder_de_SINGLE_FULL.js)
    # =========================================================================
    "marketing": "marketing",
    "beratung": "beratung",
    "it": "it",
    "finanzen": "finanzen",
    "handel": "handel",
    "bildung": "bildung",
    "verwaltung": "verwaltung",
    "gesundheit": "gesundheit",
    "bau": "bauwesen_architektur",
    "medien": "medien",
    "industrie": "industrie",
    "logistik": "transport_logistik",
    "gastronomie": "handel",  # FIX-BRANCH-13: Gastronomie → handel (B2C/Operations-similar)
    # =========================================================================
    # LEGACY VALUES (backwards compatibility with existing data)
    # =========================================================================
    "marketing_werbung": "marketing",
    "beratung_dienstleistungen": "beratung",
    "it_software": "it",
    "finanzen_versicherungen": "finanzen",
    "handel_ecommerce": "handel",
    "gesundheit_pflege": "gesundheit",
    "bauwesen_architektur": "bauwesen_architektur",
    "medien_kreativwirtschaft": "medien",
    "industrie_produktion": "industrie",
    "transport_logistik": "transport_logistik",
}

# =============================================================================
# SYNONYMS FOR LEGACY DATA / ALTERNATE FORMATS
# =============================================================================

# Text synonyms (labels, alt-data) → frontend value keys (canonical or legacy)
# FIX-BRANCH-13: All synonyms now map to canonical 13 form values where possible
BRANCH_SYNONYMS: Dict[str, str] = {
    # =========================================================================
    # GASTRONOMIE & TOURISMUS (FIX-BRANCH-13: new canonical branch)
    # =========================================================================
    "gastronomie": "gastronomie",
    "gastronomie & tourismus": "gastronomie",
    "gastronomie und tourismus": "gastronomie",
    "tourismus": "gastronomie",
    "hotel": "gastronomie",
    "hotellerie": "gastronomie",
    "restaurant": "gastronomie",
    "gastgewerbe": "gastronomie",
    "gastro": "gastronomie",
    "hospitality": "gastronomie",
    "tourism": "gastronomie",
    "catering": "gastronomie",
    "eventgastronomie": "gastronomie",
    "reise": "gastronomie",
    "reisen": "gastronomie",
    "travel": "gastronomie",
    # =========================================================================
    # German labels with & and spaces
    # =========================================================================
    "marketing & werbung": "marketing",
    "marketing und werbung": "marketing",
    "beratung & dienstleistungen": "beratung",
    "beratung und dienstleistungen": "beratung",
    "it & software": "it",
    "it und software": "it",
    "finanzen & versicherungen": "finanzen",
    "finanzen und versicherungen": "finanzen",
    "handel & e-commerce": "handel",
    "handel und e-commerce": "handel",
    "handel & ecommerce": "handel",
    "gesundheit & pflege": "gesundheit",
    "gesundheit und pflege": "gesundheit",
    "medien & kreativwirtschaft": "medien",
    "medien und kreativwirtschaft": "medien",
    "industrie & produktion": "industrie",
    "industrie und produktion": "industrie",
    "transport & logistik": "logistik",
    "transport und logistik": "logistik",
    "bauwesen & architektur": "bau",
    "bauwesen und architektur": "bau",
    # =========================================================================
    # Legacy underscore format mappings (for backwards compatibility)
    # =========================================================================
    "marketing_werbung": "marketing",
    "beratung_dienstleistungen": "beratung",
    "it_software": "it",
    "finanzen_versicherungen": "finanzen",
    "handel_ecommerce": "handel",
    "gesundheit_pflege": "gesundheit",
    "medien_kreativwirtschaft": "medien",
    "industrie_produktion": "industrie",
    "transport_logistik": "logistik",
    "bauwesen_architektur": "bau",
    # =========================================================================
    # Short forms and English variants (map to canonical 13 values)
    # =========================================================================
    "construction": "bau",
    "architecture": "bau",
    "architektur": "bau",
    "public_sector": "verwaltung",
    "public sector": "verwaltung",
    "public": "verwaltung",
    "government": "verwaltung",
    "behoerde": "verwaltung",
    "behörde": "verwaltung",
    "transport": "logistik",
    "logistics": "logistik",
    "spedition": "logistik",
    "media": "medien",
    "creative": "medien",
    "kreativ": "medien",
    "kreativwirtschaft": "medien",
    "film": "medien",
    "film & tv": "medien",
    "film und tv": "medien",
    "tv": "medien",
    "fernsehen": "medien",
    "entertainment": "medien",
    "unterhaltung": "medien",
    "musik": "medien",
    "music": "medien",
    "games": "medien",
    "gaming": "medien",
    "verlag": "medien",
    "publishing": "medien",
    "postproduktion": "medien",
    "vfx": "medien",
    # =========================================================================
    # Legacy/alternate formats (map to canonical 13 values)
    # =========================================================================
    "consulting": "beratung",
    "dienstleistung": "beratung",
    "dienstleistungen": "beratung",
    "software": "it",
    "tech": "it",
    "technologie": "it",
    "finance": "finanzen",
    "banking": "finanzen",
    "versicherung": "finanzen",
    "retail": "handel",
    "ecommerce": "handel",
    "e-commerce": "handel",
    "einzelhandel": "handel",
    "health": "gesundheit",
    "healthcare": "gesundheit",
    "medizin": "gesundheit",
    "pharma": "gesundheit",
    "pflege": "gesundheit",
    "education": "bildung",
    "training": "bildung",
    "schule": "bildung",
    "hochschule": "bildung",
    "manufacturing": "industrie",
    "produktion": "industrie",
    "fertigung": "industrie",
    "werbung": "marketing",
    "agentur": "marketing",
    "immobilien": "bau",
    "real_estate": "bau",
    "real estate": "bau",
    "baugewerbe": "bau",
    "warehousing": "logistik",
    "lager": "logistik",
    "supply_chain": "logistik",
    "supply chain": "logistik",
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


def map_frontend_branch_with_status(raw_value: str) -> BranchMappingResult:
    """
    Map a frontend branch value with full metadata about the mapping.

    FIX-BRANCH-UNMAPPED: Returns a BranchMappingResult that includes:
    - canonical: The mapped engine branch key
    - original: The input value
    - match_type: How it was matched ('direct', 'synonym', 'normalized', 'key', 'engine', 'alias', 'fallback')
    - unmapped: True if the input was unknown and fallback was used

    Args:
        raw_value: Raw branch value from frontend

    Returns:
        BranchMappingResult with full metadata

    Example:
        >>> result = map_frontend_branch_with_status("unknown_branch")
        >>> result.canonical
        "beratung"
        >>> result.unmapped
        True
    """
    if not raw_value:
        log.debug("[G19.1-MAP-STATUS] Empty branch value, defaulting to 'beratung'")
        return BranchMappingResult(
            canonical="beratung",
            original=raw_value or "",
            match_type="fallback",
            unmapped=True
        )

    # 1) Direct match on frontend value key
    key = raw_value.strip().lower()
    if key in BRANCH_MAPPING:
        result = BRANCH_MAPPING[key]
        log.debug("[G19.1-MAP-STATUS] Direct match: '%s' → '%s'", raw_value, result)
        return BranchMappingResult(
            canonical=result,
            original=raw_value,
            match_type="direct",
            unmapped=False
        )

    # 2) Match via synonym
    norm = raw_value.strip().lower()
    if norm in BRANCH_SYNONYMS:
        mapped_frontend_key = BRANCH_SYNONYMS[norm]
        result = BRANCH_MAPPING.get(mapped_frontend_key, "beratung")
        log.debug("[G19.1-MAP-STATUS] Synonym match: '%s' → '%s'", raw_value, result)
        return BranchMappingResult(
            canonical=result,
            original=raw_value,
            match_type="synonym",
            unmapped=False
        )

    # 3) Match via normalized form
    norm2 = _normalize(raw_value)
    if norm2 in BRANCH_SYNONYMS:
        mapped_frontend_key = BRANCH_SYNONYMS[norm2]
        result = BRANCH_MAPPING.get(mapped_frontend_key, "beratung")
        log.debug("[G19.1-MAP-STATUS] Normalized match: '%s' → '%s'", raw_value, result)
        return BranchMappingResult(
            canonical=result,
            original=raw_value,
            match_type="normalized",
            unmapped=False
        )

    # 4) Try underscore-normalized key format
    norm_key = _normalize_to_key(raw_value)
    if norm_key in BRANCH_MAPPING:
        result = BRANCH_MAPPING[norm_key]
        log.debug("[G19.1-MAP-STATUS] Key-normalized match: '%s' → '%s'", raw_value, result)
        return BranchMappingResult(
            canonical=result,
            original=raw_value,
            match_type="key",
            unmapped=False
        )

    # 5) Check if raw value is already an engine key
    from services.branch_profile_engine import BRANCH_MATURITY_DATA, BRANCH_ALIASES
    if key in BRANCH_MATURITY_DATA:
        log.debug("[G19.1-MAP-STATUS] Already engine key: '%s'", raw_value)
        return BranchMappingResult(
            canonical=key,
            original=raw_value,
            match_type="engine",
            unmapped=False
        )

    # 6) Try branch_profile_engine's own alias resolution
    if key in BRANCH_ALIASES:
        result = BRANCH_ALIASES[key]
        log.debug("[G19.1-MAP-STATUS] Engine alias match: '%s' → '%s'", raw_value, result)
        return BranchMappingResult(
            canonical=result,
            original=raw_value,
            match_type="alias",
            unmapped=False
        )

    # 7) Fallback - FIX-BRANCH-UNMAPPED: Set unmapped=True
    log.warning("[G19.1-MAP-STATUS] Unknown branch '%s', defaulting to 'beratung' (unmapped=True)", raw_value)
    return BranchMappingResult(
        canonical="beratung",
        original=raw_value,
        match_type="fallback",
        unmapped=True
    )


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

    FIX-BRANCH-13: Returns the 13 canonical form values from formbuilder_de_SINGLE_FULL.js.
    These are the exact values used in the questionnaire form.

    Returns:
        List of (value, label) tuples for HTML select options
    """
    return [
        ("marketing", "Marketing & Werbung"),
        ("beratung", "Beratung & Dienstleistungen"),
        ("it", "IT & Software"),
        ("finanzen", "Finanzen & Versicherungen"),
        ("handel", "Handel & E-Commerce"),
        ("bildung", "Bildung"),
        ("verwaltung", "Verwaltung"),
        ("gesundheit", "Gesundheit & Pflege"),
        ("bau", "Bauwesen & Architektur"),
        ("medien", "Medien & Kreativwirtschaft"),
        ("industrie", "Industrie & Produktion"),
        ("logistik", "Transport & Logistik"),
        ("gastronomie", "Gastronomie & Tourismus"),
    ]


def is_branch_known(raw_value: str) -> bool:
    """
    Check if a branch value is known/recognized.

    FIX-BRANCH-UNMAPPED: Quick check without full mapping.

    Args:
        raw_value: Branch value to check

    Returns:
        True if branch is recognized, False if it would use fallback
    """
    result = map_frontend_branch_with_status(raw_value)
    return not result.unmapped


def get_canonical_branches() -> list[str]:
    """
    Return list of the 13 canonical branch keys.

    These are the official values from formbuilder_de_SINGLE_FULL.js.
    """
    return [
        "marketing", "beratung", "it", "finanzen", "handel",
        "bildung", "verwaltung", "gesundheit", "bau", "medien",
        "industrie", "logistik", "gastronomie"
    ]


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G19.1-MAP] Branch Mapping loaded - %d frontend values, %d synonyms, %d canonicals",
    len(BRANCH_MAPPING),
    len(BRANCH_SYNONYMS),
    len(get_canonical_branches()),
)
