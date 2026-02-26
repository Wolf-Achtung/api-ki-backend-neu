# -*- coding: utf-8 -*-
"""
Sprint G8.2 & G8.3: Centralized Validation Configuration
Sprint G15-A: Release validation functions

This module provides a single source of truth for:
- Section minimum word lengths (by size and section)
- Validation flags and thresholds
- AI Act validation parameters
- Release configuration validation (G15)

All values are configurable via ENV variables with sensible defaults.

Version: 1.1.0 (Sprint G15)
"""
from __future__ import annotations

import os
import logging
from typing import Dict, Tuple, Any, List

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
    REDUNDANCY_WORD_THRESHOLD: int = get_int_env("VALIDATION_REDUNDANCY_THRESHOLD", 25)  # FIX-B23-P4: was 20, raised to reduce false positives

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

    # SPRINT G13-D: Fallback optimization settings
    FALLBACK_TIMEOUT_SEC: int = get_int_env("FALLBACK_TIMEOUT_SEC", 60)  # aggressive timeout
    FALLBACK_TOKEN_BUDGET: int = get_int_env("FALLBACK_TOKEN_BUDGET", 2500)  # max tokens
    FALLBACK_MIN_WORD_RATIO: float = get_float_env("FALLBACK_MIN_WORD_RATIO", 0.85)  # 85% of min

    @classmethod
    def reload(cls) -> None:
        """Reload all config values from ENV (useful for testing)."""
        cls.HARD_STOP_ON_SIZE_MISMATCH = get_bool_env("HARD_STOP_ON_SIZE_MISMATCH", True)
        cls.MAX_REDUNDANCY_WARNINGS = get_int_env("VALIDATION_MAX_REDUNDANCY_WARNINGS", 5)
        cls.REDUNDANCY_WORD_THRESHOLD = get_int_env("VALIDATION_REDUNDANCY_THRESHOLD", 25)  # FIX-B23-P4
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
        # SPRINT G13-D: Fallback optimization
        cls.FALLBACK_TIMEOUT_SEC = get_int_env("FALLBACK_TIMEOUT_SEC", 60)
        cls.FALLBACK_TOKEN_BUDGET = get_int_env("FALLBACK_TOKEN_BUDGET", 2500)
        cls.FALLBACK_MIN_WORD_RATIO = get_float_env("FALLBACK_MIN_WORD_RATIO", 0.85)
        log.info("[CONFIG] ValidationConfig reloaded from ENV")


# =============================================================================
# G8.3: CENTRALIZED SECTION MIN-LENGTHS
# =============================================================================

# Single source of truth for section minimum word counts
# Format: (size, section_key) -> min_words
# Used by both prompt_enhancer.py and report_validator.py

SECTION_MIN_WORDS: Dict[Tuple[str, str], int] = {
    # ----- SOLO -----
    # SPRINT N1: Reduced min_words for Solo to avoid unnecessary fallbacks
    # SPRINT N2: Further reduced roadmap thresholds
    ("solo", "executive_summary"): 150,
    ("solo", "ki_stack_summary"): 150,  # G20: KI-Stack Summary Card
    ("solo", "quick_wins"): 60,
    ("solo", "roadmap_90d"): 130,       # SPRINT N2: 150→130 (reduced warnings)
    ("solo", "roadmap_12m"): 550,       # SPRINT N2: 600→550 (reduced warnings)
    ("solo", "strategie_governance"): 90,   # SPRINT N1: 130→90 (Solo-friendly)
    ("solo", "recommendations"): 500,
    ("solo", "risks"): 500,
    ("solo", "gamechanger"): 500,       # SPRINT N1: reasonable for Solo
    ("solo", "foerderpotenzial"): 600,
    ("solo", "technologie_prozesse"): 130,
    ("solo", "transparency_box"): 50,   # SPRINT N1: 130→50 (minimal overhead)
    ("solo", "tools_empfehlungen"): 100,
    ("solo", "org_change"): 300,
    ("solo", "unternehmensprofil_markt"): 200,  # FIX-B23-P3: was 350, card-based layout
    ("solo", "branch_deep_dive"): 250,  # G24: Branch Deep-Dive Addon

    # ----- TEAM -----
    # SPRINT N2: Reduced roadmap thresholds
    ("team", "executive_summary"): 180,
    ("team", "ki_stack_summary"): 180,  # G20: KI-Stack Summary Card
    ("team", "quick_wins"): 90,
    ("team", "roadmap_90d"): 170,       # SPRINT N2: 200→170 (reduced warnings)
    ("team", "roadmap_12m"): 550,       # SPRINT N2: 600→550 (reduced warnings)
    ("team", "strategie_governance"): 130,
    ("team", "recommendations"): 600,
    ("team", "risks"): 600,
    ("team", "gamechanger"): 600,
    ("team", "foerderpotenzial"): 700,
    ("team", "technologie_prozesse"): 160,
    ("team", "transparency_box"): 160,
    ("team", "tools_empfehlungen"): 130,
    ("team", "org_change"): 400,
    ("team", "unternehmensprofil_markt"): 230,  # FIX-B23-P3: was 400, card-based layout
    ("team", "branch_deep_dive"): 300,  # G24: Branch Deep-Dive Addon

    # ----- KMU -----
    # SPRINT N2: Reduced roadmap thresholds
    ("kmu", "executive_summary"): 200,
    ("kmu", "ki_stack_summary"): 200,  # G20: KI-Stack Summary Card
    ("kmu", "quick_wins"): 120,
    ("kmu", "roadmap_90d"): 190,        # SPRINT N2: 220→190 (reduced warnings)
    ("kmu", "roadmap_12m"): 650,        # SPRINT N2: 700→650 (reduced warnings)
    ("kmu", "strategie_governance"): 160,
    ("kmu", "recommendations"): 700,
    ("kmu", "risks"): 700,
    ("kmu", "gamechanger"): 700,
    ("kmu", "foerderpotenzial"): 800,
    ("kmu", "technologie_prozesse"): 180,
    ("kmu", "transparency_box"): 180,
    ("kmu", "tools_empfehlungen"): 160,
    ("kmu", "org_change"): 500,
    ("kmu", "unternehmensprofil_markt"): 230,  # FIX-B23-P3: was 500, card-based layout (242 observed)
    ("kmu", "branch_deep_dive"): 350,  # G24: Branch Deep-Dive Addon
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
    # Normalize size using canonical normalizer (handles en-dash, form values, etc.)
    from services.company_size_normalizer import get_segment
    size_key = get_segment(size) if size else "kmu"

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
    # Normalize size using canonical normalizer
    from services.company_size_normalizer import get_segment
    size_key = get_segment(size) if size else "kmu"

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
# SPRINT G25: TOOL PROFILE VALIDATION
# =============================================================================

class ToolProfileValidation:
    """
    Validation rules for G25 Tools Engine v4 ToolProfile fields.

    Score interpretation:
    - Levels (1-5): 1 = best/low, 5 = worst/high (varies by field)
    - Fit scores (0.0-1.0): 1.0 = perfect fit
    """

    # Level field bounds (1-5)
    COST_LEVEL_MIN: int = 1
    COST_LEVEL_MAX: int = 5
    COMPLEXITY_LEVEL_MIN: int = 1
    COMPLEXITY_LEVEL_MAX: int = 5
    MATURITY_LEVEL_MIN: int = 1
    MATURITY_LEVEL_MAX: int = 5
    COMPLIANCE_SCORE_MIN: int = 1
    COMPLIANCE_SCORE_MAX: int = 5
    VENDOR_RISK_MIN: int = 1
    VENDOR_RISK_MAX: int = 5

    # Fit score bounds (0.0-1.0)
    FIT_SCORE_MIN: float = 0.0
    FIT_SCORE_MAX: float = 1.0

    @classmethod
    def validate_level(cls, value: int, field_name: str) -> Tuple[bool, str]:
        """Validate a level field (1-5)."""
        if not isinstance(value, int):
            return False, f"{field_name} must be int, got {type(value).__name__}"
        if value < 1 or value > 5:
            return False, f"{field_name} must be 1-5, got {value}"
        return True, ""

    @classmethod
    def validate_fit_score(cls, value: float, field_name: str) -> Tuple[bool, str]:
        """Validate a fit score field (0.0-1.0)."""
        if not isinstance(value, (int, float)):
            return False, f"{field_name} must be numeric, got {type(value).__name__}"
        if value < 0.0 or value > 1.0:
            return False, f"{field_name} must be 0.0-1.0, got {value}"
        return True, ""

    @classmethod
    def validate_eu_hosting(cls, value: Any) -> Tuple[bool, str]:
        """Validate eu_hosting field (bool or None)."""
        if value is not None and not isinstance(value, bool):
            return False, f"eu_hosting must be bool or None, got {type(value).__name__}"
        return True, ""

    @classmethod
    def validate_tool_profile(cls, profile: Dict[str, Any]) -> List[str]:
        """
        Validate a complete tool profile dictionary.

        Returns list of error messages (empty if valid).
        """
        errors = []

        # Required fields
        if not profile.get("name"):
            errors.append("Tool profile missing 'name' field")
        if not profile.get("category"):
            errors.append("Tool profile missing 'category' field")

        # Level fields
        level_fields = [
            ("cost_level", "cost_level"),
            ("complexity_level", "complexity_level"),
            ("maturity_level", "maturity_level"),
            ("compliance_score", "compliance_score"),
            ("vendor_risk", "vendor_risk"),
        ]

        for field_key, field_name in level_fields:
            if field_key in profile:
                valid, msg = cls.validate_level(profile[field_key], field_name)
                if not valid:
                    errors.append(msg)

        # Fit score fields
        fit_fields = ["fit_solo", "fit_team", "fit_kmu"]
        for field in fit_fields:
            if field in profile:
                valid, msg = cls.validate_fit_score(profile[field], field)
                if not valid:
                    errors.append(msg)

        # EU hosting
        if "eu_hosting" in profile:
            valid, msg = cls.validate_eu_hosting(profile["eu_hosting"])
            if not valid:
                errors.append(msg)

        return errors

    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default values for tool profile fields."""
        return {
            "cost_level": 3,
            "complexity_level": 3,
            "maturity_level": 3,
            "compliance_score": 3,
            "vendor_risk": 3,
            "eu_hosting": None,
            "fit_solo": 0.5,
            "fit_team": 0.5,
            "fit_kmu": 0.5,
        }


def validate_tool_profile_v4(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a G25 tool profile.

    Args:
        profile: Tool profile dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = ToolProfileValidation.validate_tool_profile(profile)
    return len(errors) == 0, errors


# =============================================================================
# SPRINT G15-A: RELEASE CONFIGURATION VALIDATION
# =============================================================================

class ReleaseValidationResult:
    """Result of release configuration validation."""

    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_info(self, msg: str) -> None:
        self.info.append(msg)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


def validate_release_config() -> ReleaseValidationResult:
    """
    SPRINT G15-A: Validate release configuration for production readiness.

    Checks:
    - Required ENV variables are set
    - API keys are present
    - Feature flags are consistent
    - Value ranges are valid

    Returns:
        ReleaseValidationResult with is_valid, errors, warnings, info
    """
    result = ReleaseValidationResult()

    # Import release config
    try:
        from services.config_release import (
            REQUIRED_ENV_VARS,
            RECOMMENDED_ENV_VARS,
            VALIDATED_ENV_VARS,
            get_env_validation_summary,
        )
    except ImportError:
        result.add_error("Cannot import config_release module")
        return result

    # Get validation summary
    summary = get_env_validation_summary()

    # Check required variables
    for var in summary["missing_required"]:
        result.add_error(f"Required ENV variable not set: {var}")

    # Check recommended variables
    for var in summary["missing_recommended"]:
        result.add_warning(f"Recommended ENV variable not set: {var}")

    # Check invalid values
    for msg in summary["invalid_values"]:
        result.add_error(f"Invalid ENV value: {msg}")

    # Check critical production settings
    env = os.getenv("ENVIRONMENT", "").lower()
    if env == "production":
        # In production, certain features should be enabled
        if not get_bool_env("AI_ACT_ENABLED", True):
            result.add_warning("AI_ACT_ENABLED is off in production")

        if not get_bool_env("RATE_LIMIT_ENABLED", True):
            result.add_warning("RATE_LIMIT_ENABLED is off in production")

        if not get_bool_env("LLM_CIRCUIT_BREAKER_ENABLED", True):
            result.add_warning("LLM_CIRCUIT_BREAKER_ENABLED is off in production")

        # Check JWT_SECRET is not default
        jwt_secret = os.getenv("JWT_SECRET", "")
        if jwt_secret in ("", "change-me", "secret", "jwt-secret"):
            result.add_error("JWT_SECRET must be changed from default in production")

        result.add_info(f"Environment: {env}")

    # Check LLM configuration
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-"):
        result.add_warning("OPENAI_API_KEY doesn't look like a valid key")

    # Check timeout values are reasonable
    pdf_timeout = get_int_env("PDF_TIMEOUT_MS", 90000)
    if pdf_timeout > 300000:  # 5 minutes
        result.add_warning(f"PDF_TIMEOUT_MS={pdf_timeout}ms is very high")

    openai_timeout = get_int_env("OPENAI_TIMEOUT", 90)
    if openai_timeout > 300:
        result.add_warning(f"OPENAI_TIMEOUT={openai_timeout}s is very high")

    # Check rate limits are reasonable
    rate_limit = get_int_env("REPORT_RATE_LIMIT_PER_MINUTE", 5)
    if rate_limit > 60:
        result.add_warning(f"REPORT_RATE_LIMIT_PER_MINUTE={rate_limit} is very high")

    # Summary info
    if result.is_valid:
        result.add_info("Release configuration validation passed")
    else:
        result.add_info(f"Release configuration has {len(result.errors)} error(s)")

    return result


def print_release_validation() -> bool:
    """
    Print release validation results to console.

    Returns:
        True if validation passed, False otherwise
    """
    result = validate_release_config()

    print("")
    print("=" * 78)
    print("G15-A RELEASE CONFIGURATION VALIDATION")
    print("=" * 78)
    print("")

    if result.errors:
        print(f"ERRORS ({len(result.errors)}):")
        for err in result.errors:
            print(f"   {err}")
        print("")

    if result.warnings:
        print(f"WARNINGS ({len(result.warnings)}):")
        for warn in result.warnings:
            print(f"   {warn}")
        print("")

    if result.info:
        print("INFO:")
        for info in result.info:
            print(f"   {info}")
        print("")

    status = "PASS" if result.is_valid else "FAIL"
    print(f"STATUS: {status}")
    print("=" * 78)
    print("")

    return result.is_valid


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
