# -*- coding: utf-8 -*-
"""
Centralized Size Profiles Configuration
========================================

Single source of truth for all size-dependent behavior:
- Tonality & Ansprache
- Forbidden enterprise terms
- Section budgets (max chars)
- Minimum word counts per section
- Max report pages

Three profiles: solo (1), team (2-10), kmu (11-100)

Version: 1.0.0
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

log = logging.getLogger(__name__)


# =============================================================================
# SIZE PROFILES
# =============================================================================

SIZE_PROFILES: Dict[str, Dict[str, Any]] = {
    # -----------------------------------------------------------------
    # SOLO (1 Person)
    # -----------------------------------------------------------------
    "solo": {
        "display_name": "Solo / Freiberuflich",
        "employee_range": "1",
        "segment": "solo",

        "tonality": {
            "ansprache": "Sie",
            "formality": "formal_but_warm",
            "description": (
                "Sie-Ansprache, persönlich aber professionell. "
                "Keine Du-Formen. Kurze, praxisnahe Sätze."
            ),
            "enforce_duz_to_sie": True,
        },

        "forbidden_enterprise_terms": [
            "Governance", "Audit-Trail", "Audit Trail", "Stakeholder",
            "Stack", "Layer", "Architektur", "Rollout", "Roll-out",
            "Prozesslandschaft", "Baukasten-Prinzip", "Baukasten-System",
            "Pipeline", "Framework", "Deployment", "Engine",
            "Skalierung", "KPI-Dashboard", "Matrixorganisation",
            "Wertschöpfungskette", "Enterprise-Software",
            "Unternehmensarchitektur", "Compliance-Framework",
            "Strategische Roadmap", "Meilenstein-Planung",
            "Change Management", "Governance-Struktur",
        ],

        "forbidden_persona_terms": [
            "PMO-Team", "Team aufbauen", "Team-Struktur",
            "Mitarbeiter einstellen", "Abteilung", "Abteilungen",
            "HR-Abteilung", "IT-Abteilung", "Fachbereich",
            "bereichsübergreifend",
        ],

        "section_budgets": {
            "EXECUTIVE_SUMMARY_HTML": 2000,
            "QUICK_WINS_HTML": 1500,
            "ROADMAP_90D_HTML": 1200,
            "ROADMAP_12M_HTML": 8000,
            "RECOMMENDATIONS_HTML": 1500,
            "RISKS_HTML": 1200,
            "GAMECHANGER_HTML": 1500,
            "FOERDERPOTENZIAL_HTML": 1000,
            "ORG_CHANGE_HTML": 1200,
            "BUSINESS_CASE_HTML": 2500,
            "PILOT_PLAN_HTML": 1200,
            "DATA_READINESS_HTML": 1200,
            "STRATEGIE_GOVERNANCE_HTML": 1200,
            "UNTERNEHMENSPROFIL_MARKT_HTML": 1500,
            "MONETARISIERUNG_HTML": 1200,
            "KI_SKILLPLAN_HTML": 1200,
            "TOOLS_EMPFEHLUNGEN_HTML": 1200,
            "TECHNOLOGIE_PROZESSE_HTML": 2000,
            "_default": 1000,
        },

        "min_words": {
            "executive_summary": 100,
            "quick_wins": 30,
            "roadmap_90d": 150,
            "roadmap_12m": 600,
            "org_change": 80,
            "strategie_governance": 90,
            "tools_empfehlungen": 80,
            "foerderpotenzial": 40,
            "gamechanger": 100,
            "transparency_box": 50,
            "technologie_prozesse": 150,
        },

        "max_pages": 25,
        "enable_kpi_replacement": True,
        "enable_enterprise_elimination": True,
        "enable_duz_conversion": True,
    },

    # -----------------------------------------------------------------
    # TEAM (2-10 Personen)
    # -----------------------------------------------------------------
    "team": {
        "display_name": "2–10 (Kleines Team)",
        "employee_range": "2-10",
        "segment": "team",

        "tonality": {
            "ansprache": "Sie",
            "formality": "professional",
            "description": (
                "Sie-Ansprache, professionell. "
                "Team-orientierte Sprache, kollaborativer Ton."
            ),
            "enforce_duz_to_sie": True,
        },

        "forbidden_enterprise_terms": [
            # Team gets softer filtering - no enterprise jargon but allow
            # some structural terms like Architektur, Governance (in context)
            "Matrixorganisation", "Wertschöpfungskette",
            "Enterprise-Software", "Unternehmensarchitektur",
            "Strategische Roadmap", "Meilenstein-Planung",
            "Compliance-Framework",
        ],

        "forbidden_persona_terms": [
            "Governance-Board", "Enterprise-Architektur", "Konzernstruktur",
            "Solo-Selbstständige", "Solo-Selbstständigen", "Solo-Berater",
            "Einzelunternehmer", "Freiberufler", "freiberuflich",
            "Selbstständiger", "Selbstständige",
            "als Einzelperson", "persönliche Kapazität",
        ],

        "section_budgets": {
            "EXECUTIVE_SUMMARY_HTML": 3000,
            "QUICK_WINS_HTML": 2000,
            "ROADMAP_90D_HTML": 1800,
            "ROADMAP_12M_HTML": 12000,
            "RECOMMENDATIONS_HTML": 2500,
            "RISKS_HTML": 1800,
            "GAMECHANGER_HTML": 10000,
            "FOERDERPOTENZIAL_HTML": 2000,
            "ORG_CHANGE_HTML": 1800,
            "BUSINESS_CASE_HTML": 4000,
            "PILOT_PLAN_HTML": 1800,
            "DATA_READINESS_HTML": 1800,
            "STRATEGIE_GOVERNANCE_HTML": 3000,
            "UNTERNEHMENSPROFIL_MARKT_HTML": 2500,
            "MONETARISIERUNG_HTML": 1800,
            "KI_SKILLPLAN_HTML": 1800,
            "TOOLS_EMPFEHLUNGEN_HTML": 3000,
            "TECHNOLOGIE_PROZESSE_HTML": 3000,
            "_default": 1500,
        },

        "min_words": {
            "executive_summary": 140,   # FIX-TEAM-KMU: realistic for LLM output
            "quick_wins": 90,
            "roadmap_90d": 200,
            "roadmap_12m": 600,
            "org_change": 100,
            "tools_empfehlungen": 190,
            "strategie_governance": 200,
            "foerderpotenzial": 40,     # FIX-629: compact Förder-Überblick layout (~45 words valid)
            "gamechanger": 750,
            "transparency_box": 150,
            "technologie_prozesse": 200,
        },

        "max_pages": 35,
        "enable_kpi_replacement": False,
        "enable_enterprise_elimination": True,
        "enable_duz_conversion": True,
    },

    # -----------------------------------------------------------------
    # KMU (11-100 Personen)
    # -----------------------------------------------------------------
    "kmu": {
        "display_name": "11–100 (KMU)",
        "employee_range": "11-100",
        "segment": "kmu",

        "tonality": {
            "ansprache": "Sie",
            "formality": "formal_business",
            "description": (
                "Sie-Ansprache, geschäftlich-formal. "
                "Strukturierte Sprache, Governance/Compliance-Kontext erlaubt."
            ),
            "enforce_duz_to_sie": True,
        },

        "forbidden_enterprise_terms": [
            # KMU allows most enterprise terms - only ban truly inappropriate ones
            "Matrixorganisation",
        ],

        "forbidden_persona_terms": [
            "Solo-Selbstständige", "Solo-Selbstständigen", "Solo-Berater",
            "Einzelunternehmer", "Freiberufler", "freiberuflich",
            "Selbstständiger", "Selbstständige",
            "als Einzelperson", "persönliche Kapazität",
        ],

        "section_budgets": {
            "EXECUTIVE_SUMMARY_HTML": 4000,
            "QUICK_WINS_HTML": 2500,
            "ROADMAP_90D_HTML": 2500,
            "ROADMAP_12M_HTML": 14000,
            "RECOMMENDATIONS_HTML": 3500,
            "RISKS_HTML": 2500,
            "GAMECHANGER_HTML": 12000,
            "FOERDERPOTENZIAL_HTML": 10000,
            "ORG_CHANGE_HTML": 2000,
            "BUSINESS_CASE_HTML": 5000,
            "PILOT_PLAN_HTML": 2000,
            "DATA_READINESS_HTML": 2000,
            "STRATEGIE_GOVERNANCE_HTML": 3500,
            "UNTERNEHMENSPROFIL_MARKT_HTML": 3000,
            "MONETARISIERUNG_HTML": 2000,
            "KI_SKILLPLAN_HTML": 2000,
            "TOOLS_EMPFEHLUNGEN_HTML": 3500,
            "TECHNOLOGIE_PROZESSE_HTML": 3000,
            "_default": 2000,
        },

        "min_words": {
            "executive_summary": 140,   # FIX-TEAM-KMU: realistic for LLM output
            "quick_wins": 120,
            "roadmap_90d": 220,
            "roadmap_12m": 700,
            "org_change": 120,
            "tools_empfehlungen": 220,
            "strategie_governance": 220,
            "foerderpotenzial": 800,
            "gamechanger": 750,
            "transparency_box": 150,
            "technologie_prozesse": 200,
        },

        "max_pages": 45,
        "enable_kpi_replacement": False,
        "enable_enterprise_elimination": False,
        "enable_duz_conversion": True,
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Mapping from raw/normalized size values to profile keys
_SIZE_TO_PROFILE_KEY = {
    # Numeric raw values
    "1": "solo",
    "2-10": "team",
    "2\u201310": "team",  # En-dash
    "11-100": "kmu",
    "11\u2013100": "kmu",  # En-dash
    # Normalized bucket names
    "solo": "solo",
    "small_team": "team",
    "team": "team",
    "kmu": "kmu",
    # Legacy/alternative values
    "freiberufler": "solo",
    "freelancer": "solo",
    "einzelunternehmer": "solo",
    "selbstständig": "solo",
    "klein": "team",
    "kleines team": "team",
    "mittelstand": "kmu",
}


def get_size_profile(size_value: str) -> Dict[str, Any]:
    """
    Get the size profile for a given raw or normalized size value.

    Args:
        size_value: Raw unternehmensgroesse value or normalized bucket name.

    Returns:
        The matching SIZE_PROFILES entry. Defaults to 'solo' if unknown.
    """
    if not size_value:
        return SIZE_PROFILES["solo"]

    key = _SIZE_TO_PROFILE_KEY.get(size_value.strip().lower())
    if key:
        return SIZE_PROFILES[key]

    # Substring fallback
    lower = size_value.lower()
    if "solo" in lower or "einzel" in lower or "freiberuf" in lower:
        return SIZE_PROFILES["solo"]
    if "team" in lower or "klein" in lower:
        return SIZE_PROFILES["team"]
    if "kmu" in lower or "mittel" in lower:
        return SIZE_PROFILES["kmu"]

    log.warning("Unknown size value '%s', defaulting to solo profile", size_value)
    return SIZE_PROFILES["solo"]


def get_segment_for_size(size_value: str) -> str:
    """
    Get the segment key ('solo', 'team', 'kmu') for a size value.

    This is the canonical mapping used by healer, validator, and final pass.
    """
    profile = get_size_profile(size_value)
    return str(profile["segment"])


def get_section_budget(segment: str, html_key: str) -> int:
    """
    Get the character budget for a section in a given segment.

    Args:
        segment: 'solo', 'team', or 'kmu'
        html_key: Canonical HTML key (e.g., 'GAMECHANGER_HTML')

    Returns:
        Character budget for the section. Falls back to _default, then 2000.
    """
    profile = SIZE_PROFILES.get(segment, SIZE_PROFILES["solo"])
    budgets = profile.get("section_budgets", {})
    return int(budgets.get(html_key, budgets.get("_default", 2000)))


def get_min_words(segment: str, logical_name: str) -> int:
    """
    Get the minimum word count for a section in a given segment.

    Args:
        segment: 'solo', 'team', or 'kmu'
        logical_name: Logical section name (e.g., 'gamechanger')

    Returns:
        Minimum word count. Defaults to 50 if not specified.
    """
    profile = SIZE_PROFILES.get(segment, SIZE_PROFILES["solo"])
    min_words = profile.get("min_words", {})
    return int(min_words.get(logical_name, 50))


def sanity_check_profiles() -> list[str]:
    """
    Startup sanity check: verify that section_budgets can accommodate min_words.

    Rule: budget_chars >= min_words * 7 (average ~7 chars per German word incl. HTML)
    This is a conservative estimate; actual HTML overhead varies.

    Returns:
        List of warning messages. Empty list means all checks passed.
    """
    warnings: list[str] = []
    chars_per_word = 7  # Conservative estimate for German text with HTML markup

    # Import canonical mapping for name resolution
    try:
        from services.section_keys import CANONICAL_MAP
    except ImportError:
        log.warning("[SIZE-PROFILES] Cannot import section_keys for sanity check")
        return warnings

    for seg_name, profile in SIZE_PROFILES.items():
        min_words_map = profile.get("min_words", {})
        budgets = profile.get("section_budgets", {})
        default_budget = budgets.get("_default", 2000)

        for logical_name, min_w in min_words_map.items():
            html_key = CANONICAL_MAP.get(logical_name, logical_name.upper() + "_HTML")
            budget = budgets.get(html_key, default_budget)
            min_chars_needed = min_w * chars_per_word

            if budget < min_chars_needed:
                msg = (
                    f"[{seg_name}] {html_key}: budget={budget} chars < "
                    f"min_words({min_w}) * {chars_per_word} = {min_chars_needed} chars"
                )
                warnings.append(msg)
                log.warning("[SIZE-PROFILES][SANITY] %s", msg)

    return warnings


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[SIZE-PROFILES] Loaded %d profiles: %s",
    len(SIZE_PROFILES),
    list(SIZE_PROFILES.keys()),
)

# Run sanity check at import time
_sanity_warnings = sanity_check_profiles()
if _sanity_warnings:
    log.warning(
        "[SIZE-PROFILES] Sanity check found %d issues:\n  %s",
        len(_sanity_warnings),
        "\n  ".join(_sanity_warnings),
    )
else:
    log.info("[SIZE-PROFILES] Sanity check passed: all budgets accommodate min_words")
