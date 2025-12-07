# -*- coding: utf-8 -*-
"""
Sprint G8.2 & G8.3: Centralized Validation Configuration

This module provides a single source of truth for:
- Section minimum word lengths (by size and section)
- Validation flags and thresholds
- AI Act validation parameters

All values are configurable via ENV variables with sensible defaults.

Version: 1.0.0 (Sprint G8)
"""
from __future__ import annotations

import os
import logging
from typing import Dict, Tuple, Any

log = logging.getLogger(__name__)


# =============================================================================
# G8.2: ENV HELPER FUNCTIONS
# =============================================================================

def get_bool_env(name: str, default: bool = False) -> bool:
    """Get boolean value from ENV variable."""
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "y", "on")


def get_int_env(name: str, default: int) -> int:
    """Get integer value from ENV variable."""
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        log.warning("Invalid int ENV value for %s, using default %d", name, default)
        return default


def get_float_env(name: str, default: float) -> float:
    """Get float value from ENV variable."""
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        log.warning("Invalid float ENV value for %s, using default %.2f", name, default)
        return default


# =============================================================================
# G8.2: EXTERNALIZED VALIDATION FLAGS
# =============================================================================

class ValidationConfig:
    """
    Centralized validation configuration with ENV externalization.

    All values can be overridden via ENV variables.
    """

    # Size mismatch handling
    HARD_STOP_ON_SIZE_MISMATCH: bool = get_bool_env("HARD_STOP_ON_SIZE_MISMATCH", True)

    # Redundancy settings
    MAX_REDUNDANCY_WARNINGS: int = get_int_env("VALIDATION_MAX_REDUNDANCY_WARNINGS", 5)
    REDUNDANCY_WORD_THRESHOLD: int = get_int_env("VALIDATION_REDUNDANCY_THRESHOLD", 20)

    # AI Act validation
    AI_ACT_MIN_REASONING_WORDS: int = get_int_env("AI_ACT_MIN_REASONING_WORDS", 60)
    AI_ACT_MIN_DUTY_MATRIX_ROWS: int = get_int_env("AI_ACT_MIN_DUTY_MATRIX_ROWS", 3)
    AI_ACT_MIN_ALERTS: int = get_int_env("AI_ACT_MIN_ALERTS", 2)
    AI_ACT_MAX_ALERTS: int = get_int_env("AI_ACT_MAX_ALERTS", 10)
    AI_ACT_MIN_GAPS: int = get_int_env("AI_ACT_MIN_GAPS", 2)
    AI_ACT_MAX_GAPS: int = get_int_env("AI_ACT_MAX_GAPS", 8)

    # AI Act feature flags
    AI_ACT_ENABLED: bool = get_bool_env("AI_ACT_ENABLED", True)
    AI_ACT_VERBOSE: bool = get_bool_env("AI_ACT_SECTION_VERBOSE", False)
    AI_ACT_APPLY_BC_MODIFIERS: bool = get_bool_env("AI_ACT_APPLY_BC_MODIFIERS", True)

    # Fallback limits
    MAX_FALLBACKS_PER_REPORT: int = get_int_env("HARD_STOP_MAX_FALLBACKS", 5)

    @classmethod
    def reload(cls) -> None:
        """Reload all config values from ENV (useful for testing)."""
        cls.HARD_STOP_ON_SIZE_MISMATCH = get_bool_env("HARD_STOP_ON_SIZE_MISMATCH", True)
        cls.MAX_REDUNDANCY_WARNINGS = get_int_env("VALIDATION_MAX_REDUNDANCY_WARNINGS", 5)
        cls.REDUNDANCY_WORD_THRESHOLD = get_int_env("VALIDATION_REDUNDANCY_THRESHOLD", 20)
        cls.AI_ACT_MIN_REASONING_WORDS = get_int_env("AI_ACT_MIN_REASONING_WORDS", 60)
        cls.AI_ACT_MIN_DUTY_MATRIX_ROWS = get_int_env("AI_ACT_MIN_DUTY_MATRIX_ROWS", 3)
        cls.AI_ACT_MIN_ALERTS = get_int_env("AI_ACT_MIN_ALERTS", 2)
        cls.AI_ACT_MAX_ALERTS = get_int_env("AI_ACT_MAX_ALERTS", 10)
        cls.AI_ACT_MIN_GAPS = get_int_env("AI_ACT_MIN_GAPS", 2)
        cls.AI_ACT_MAX_GAPS = get_int_env("AI_ACT_MAX_GAPS", 8)
        cls.AI_ACT_ENABLED = get_bool_env("AI_ACT_ENABLED", True)
        cls.AI_ACT_VERBOSE = get_bool_env("AI_ACT_SECTION_VERBOSE", False)
        cls.AI_ACT_APPLY_BC_MODIFIERS = get_bool_env("AI_ACT_APPLY_BC_MODIFIERS", True)
        cls.MAX_FALLBACKS_PER_REPORT = get_int_env("HARD_STOP_MAX_FALLBACKS", 5)
        log.info("[CONFIG] ValidationConfig reloaded from ENV")


# =============================================================================
# G8.3: CENTRALIZED SECTION MIN-LENGTHS
# =============================================================================

# Single source of truth for section minimum word counts
# Format: (size, section_key) -> min_words
# Used by both prompt_enhancer.py and report_validator.py

SECTION_MIN_WORDS: Dict[Tuple[str, str], int] = {
    # ----- SOLO -----
    ("solo", "executive_summary"): 150,
    ("solo", "quick_wins"): 60,
    ("solo", "roadmap_12m"): 500,
    ("solo", "strategie_governance"): 130,
    ("solo", "recommendations"): 500,
    ("solo", "risks"): 500,
    ("solo", "gamechanger"): 500,
    ("solo", "foerderpotenzial"): 600,
    ("solo", "technologie_prozesse"): 130,
    ("solo", "transparency_box"): 130,
    ("solo", "tools_empfehlungen"): 100,
    ("solo", "org_change"): 300,
    ("solo", "unternehmensprofil_markt"): 350,

    # ----- TEAM -----
    ("team", "executive_summary"): 180,
    ("team", "quick_wins"): 90,
    ("team", "roadmap_12m"): 600,
    ("team", "strategie_governance"): 130,
    ("team", "recommendations"): 600,
    ("team", "risks"): 600,
    ("team", "gamechanger"): 600,
    ("team", "foerderpotenzial"): 700,
    ("team", "technologie_prozesse"): 160,
    ("team", "transparency_box"): 160,
    ("team", "tools_empfehlungen"): 130,
    ("team", "org_change"): 400,
    ("team", "unternehmensprofil_markt"): 400,

    # ----- KMU -----
    ("kmu", "executive_summary"): 200,
    ("kmu", "quick_wins"): 120,
    ("kmu", "roadmap_12m"): 700,
    ("kmu", "strategie_governance"): 160,
    ("kmu", "recommendations"): 700,
    ("kmu", "risks"): 700,
    ("kmu", "gamechanger"): 700,
    ("kmu", "foerderpotenzial"): 800,
    ("kmu", "technologie_prozesse"): 180,
    ("kmu", "transparency_box"): 180,
    ("kmu", "tools_empfehlungen"): 160,
    ("kmu", "org_change"): 500,
    ("kmu", "unternehmensprofil_markt"): 500,
}

# Default min words for unknown sections
DEFAULT_MIN_WORDS = 100


def get_min_words(size: str, section_key: str) -> int:
    """
    Get minimum word count for a section based on size.

    Args:
        size: Company size (solo/team/kmu)
        section_key: Section identifier

    Returns:
        Minimum word count for the section
    """
    size_lower = size.lower()

    # Normalize size - check specific keywords first, solo is fallback for single-person
    if "kmu" in size_lower or "mittel" in size_lower or "50" in size_lower:
        size_key = "kmu"
    elif "team" in size_lower or "klein" in size_lower or "2-10" in size_lower:
        size_key = "team"
    elif "solo" in size_lower or "freiberuf" in size_lower or "(1 " in size_lower or "(1)" in size_lower:
        size_key = "solo"
    else:
        # Default to kmu for unknown sizes (safer than under-delivering)
        size_key = "kmu"

    # Normalize section key
    section_normalized = section_key.lower().replace("-", "_")

    # Look up in map
    key = (size_key, section_normalized)
    if key in SECTION_MIN_WORDS:
        return SECTION_MIN_WORDS[key]

    # Try without size for generic sections
    for (s, sec), val in SECTION_MIN_WORDS.items():
        if sec == section_normalized:
            return val

    return DEFAULT_MIN_WORDS


def get_all_min_words_for_size(size: str) -> Dict[str, int]:
    """
    Get all minimum word counts for a given size.

    Args:
        size: Company size (solo/team/kmu)

    Returns:
        Dict mapping section_key -> min_words
    """
    size_lower = size.lower()

    # Normalize size
    if "solo" in size_lower or "freiberuf" in size_lower:
        size_key = "solo"
    elif "team" in size_lower or "klein" in size_lower:
        size_key = "team"
    else:
        size_key = "kmu"

    result = {}
    for (s, section), min_words in SECTION_MIN_WORDS.items():
        if s == size_key:
            result[section] = min_words

    return result


# =============================================================================
# BUSINESS CASE VALIDATION
# =============================================================================

def validate_business_case_with_ai_act(
    business_case: Dict[str, Any],
    risk_level: str = "minimal"
) -> list:
    """
    Validate business case values after AI Act modifiers are applied.

    Returns list of warnings if any values are inconsistent.
    """
    warnings = []

    capex = business_case.get("CAPEX_REALISTISCH_EUR", 0)
    opex = business_case.get("OPEX_REALISTISCH_EUR", 0)
    payback = business_case.get("PAYBACK_MONTHS")
    roi = business_case.get("ROI_12M")

    # Check for negative values
    if capex < 0:
        warnings.append(f"[AI-ACT-BC] Negative CAPEX: {capex}")
    if opex < 0:
        warnings.append(f"[AI-ACT-BC] Negative OPEX: {opex}")
    if payback is not None and payback < 0:
        warnings.append(f"[AI-ACT-BC] Negative PAYBACK: {payback}")

    # Check for unrealistic ROI with high-risk
    if risk_level == "high-risk" and roi is not None and roi > 300:
        warnings.append(f"[AI-ACT-BC] High ROI ({roi:.0f}%) for high-risk classification may be unrealistic")

    # Check payback is reasonable for high-risk
    if risk_level == "high-risk" and payback is not None and payback < 3:
        warnings.append(f"[AI-ACT-BC] Very short payback ({payback:.1f} months) for high-risk classification")

    return warnings


# =============================================================================
# LOGGING
# =============================================================================

# Log configuration on module load
log.info(
    "[CONFIG] ValidationConfig loaded: HARD_STOP=%s, MAX_REDUNDANCY=%d, AI_ACT_MIN_REASONING=%d",
    ValidationConfig.HARD_STOP_ON_SIZE_MISMATCH,
    ValidationConfig.MAX_REDUNDANCY_WARNINGS,
    ValidationConfig.AI_ACT_MIN_REASONING_WORDS
)
