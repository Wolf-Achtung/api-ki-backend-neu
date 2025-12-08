# -*- coding: utf-8 -*-
"""
Sprint G15-A: Release R1 Configuration Profile

Centralized release configuration defining:
- Production defaults for all G1-G14 features
- Required ENV variables for production
- Validation rules for release readiness

Version: 1.0.0 (Release R1)
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

log = logging.getLogger(__name__)


# =============================================================================
# RELEASE R1 CONFIGURATION PROFILE
# =============================================================================

@dataclass
class ReleaseConfig:
    """
    Release R1 configuration profile.

    Defines all ENV variables, their production defaults, and whether
    they are required for production deployment.
    """

    # -------------------------------------------------------------------------
    # Core / Environment
    # -------------------------------------------------------------------------
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "info"

    # -------------------------------------------------------------------------
    # AI Act & Compliance (G7, G12)
    # -------------------------------------------------------------------------
    AI_ACT_ENABLED: bool = True
    AI_ACT_STRICT_VALIDATION: bool = True
    AI_ACT_FAIL_ON_INCONSISTENCY: bool = False  # Soft mode for R1
    AI_ACT_APPLY_BC_MODIFIERS: bool = True
    AI_ACT_REQUIRE_FUNDING_IMPACT: bool = True

    # -------------------------------------------------------------------------
    # Business Case (G4, G12)
    # -------------------------------------------------------------------------
    BC_RECONCILE_ENABLED: bool = True
    BC_FAIL_ON_INCONSISTENCY: bool = False  # Soft mode for R1
    BC_ROUNDING_DECIMALS: int = 1

    # -------------------------------------------------------------------------
    # Product Mode (G11)
    # -------------------------------------------------------------------------
    REPORT_VERSIONING_ENABLED: bool = True
    ENABLE_DASHBOARD_API: bool = True
    ENABLE_DELTA_ENGINE: bool = True
    ENABLE_BC_VISUALS: bool = True
    ENABLE_PREMIUM_FUNDING: bool = False  # Premium feature, off by default

    # -------------------------------------------------------------------------
    # LLM Stability (G14)
    # -------------------------------------------------------------------------
    LLM_SHORT_RETRY_ENABLED: bool = True
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_BACKOFF_BASE: float = 1.0
    LLM_RETRY_BACKOFF_MULTIPLIER: float = 2.0

    # -------------------------------------------------------------------------
    # Research Pipeline (G14)
    # -------------------------------------------------------------------------
    PPLX_FAILURE_THRESHOLD: int = 2
    PPLX_CIRCUIT_RESET_SEC: int = 120
    TAVILY_TIMEOUT: int = 8

    # -------------------------------------------------------------------------
    # Rate Limiting (G12)
    # -------------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    REPORT_RATE_LIMIT_PER_MINUTE: int = 5
    REPORT_RATE_LIMIT_GLOBAL: int = 20

    # -------------------------------------------------------------------------
    # Circuit Breaker (G12)
    # -------------------------------------------------------------------------
    LLM_CIRCUIT_BREAKER_ENABLED: bool = True
    LLM_CIRCUIT_FAILURE_THRESHOLD: int = 5
    LLM_CIRCUIT_RESET_SECONDS: int = 60

    # -------------------------------------------------------------------------
    # Degradation Monitor (G12)
    # -------------------------------------------------------------------------
    DEGRADATION_MONITORING_ENABLED: bool = True
    DEGRADATION_HARD_STOP_THRESHOLD: int = 30
    DEGRADATION_WARN_THRESHOLD: int = 60

    # -------------------------------------------------------------------------
    # PDF (G12)
    # -------------------------------------------------------------------------
    PDF_GUARD_ENABLED: bool = True
    PDF_MAX_RETRIES: int = 3
    PDF_FAIL_ON_OVERSIZE: bool = False

    # -------------------------------------------------------------------------
    # Fallback (G13)
    # -------------------------------------------------------------------------
    FALLBACK_TIMEOUT_SEC: int = 60
    FALLBACK_TOKEN_BUDGET: int = 2500
    FALLBACK_MIN_WORD_RATIO: float = 0.85


# =============================================================================
# REQUIRED ENV VARIABLES FOR PRODUCTION
# =============================================================================

# Variables that MUST be set (not empty) in production
REQUIRED_ENV_VARS: List[str] = [
    # Core
    "DATABASE_URL",
    "JWT_SECRET",

    # LLM API Keys
    "OPENAI_API_KEY",

    # SMTP (for notifications)
    "SMTP_HOST",
    "SMTP_USER",
    "SMTP_PASS",

    # PDF Service
    "PDF_SERVICE_URL",
]

# Variables that SHOULD be set for full functionality
RECOMMENDED_ENV_VARS: List[str] = [
    "ANTHROPIC_API_KEY",      # For exec summary
    "PERPLEXITY_API_KEY",     # For research
    "TAVILY_API_KEY",         # For research fallback
    "ADMIN_NOTIFY_EMAIL",     # For alerts
]

# Variables with specific validation rules
VALIDATED_ENV_VARS: Dict[str, Dict[str, Any]] = {
    "OPENAI_MODEL_DEFAULT": {
        "type": "string",
        "allowed": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default": "gpt-4o",
    },
    "LOG_LEVEL": {
        "type": "string",
        "allowed": ["debug", "info", "warning", "error"],
        "default": "info",
    },
    "ENVIRONMENT": {
        "type": "string",
        "allowed": ["production", "staging", "development", "test"],
        "default": "production",
    },
    "REPORT_RATE_LIMIT_PER_MINUTE": {
        "type": "int",
        "min": 1,
        "max": 100,
        "default": 5,
    },
    "LLM_MAX_RETRIES": {
        "type": "int",
        "min": 0,
        "max": 5,
        "default": 2,
    },
    "PPLX_FAILURE_THRESHOLD": {
        "type": "int",
        "min": 1,
        "max": 10,
        "default": 2,
    },
}


# =============================================================================
# FEATURE FLAGS SUMMARY
# =============================================================================

FEATURE_FLAGS: Dict[str, Dict[str, Any]] = {
    # Sprint G7: AI Act
    "AI_ACT_ENABLED": {
        "sprint": "G7",
        "description": "Enable AI Act risk classification",
        "production_default": True,
    },
    # Sprint G11: Product Mode
    "REPORT_VERSIONING_ENABLED": {
        "sprint": "G11",
        "description": "Enable report versioning",
        "production_default": True,
    },
    "ENABLE_DASHBOARD_API": {
        "sprint": "G11",
        "description": "Enable dashboard API endpoints",
        "production_default": True,
    },
    "ENABLE_DELTA_ENGINE": {
        "sprint": "G11",
        "description": "Enable delta comparison between versions",
        "production_default": True,
    },
    # Sprint G12: Resilience
    "RATE_LIMIT_ENABLED": {
        "sprint": "G12",
        "description": "Enable rate limiting",
        "production_default": True,
    },
    "LLM_CIRCUIT_BREAKER_ENABLED": {
        "sprint": "G12",
        "description": "Enable LLM circuit breaker",
        "production_default": True,
    },
    "DEGRADATION_MONITORING_ENABLED": {
        "sprint": "G12",
        "description": "Enable degradation monitoring",
        "production_default": True,
    },
    # Sprint G14: Stability
    "LLM_SHORT_RETRY_ENABLED": {
        "sprint": "G14",
        "description": "Enable LLM short retry with reduced tokens",
        "production_default": True,
    },
    # Premium Features (off by default)
    "ENABLE_PREMIUM_FUNDING": {
        "sprint": "G11",
        "description": "Enable premium smart funding recommender",
        "production_default": False,
    },
}


# =============================================================================
# RELEASE HEALTH THRESHOLDS
# =============================================================================

RELEASE_HEALTH_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "fallback_rate_pct": {
        "warn": 10.0,
        "critical": 25.0,
        "description": "Percentage of sections using fallback",
    },
    "pdf_error_rate_pct": {
        "warn": 5.0,
        "critical": 15.0,
        "description": "Percentage of PDF generation failures",
    },
    "ai_act_high_risk_share_pct": {
        "warn": 50.0,
        "critical": 80.0,
        "description": "Percentage of reports with high-risk classification",
    },
    "avg_generation_time_sec": {
        "warn": 120.0,
        "critical": 180.0,
        "description": "Average report generation time",
    },
    "circuit_breaker_open_count": {
        "warn": 1,
        "critical": 3,
        "description": "Number of open circuit breakers",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_release_config() -> ReleaseConfig:
    """Get release configuration instance."""
    return ReleaseConfig()


def get_current_feature_status() -> Dict[str, bool]:
    """Get current status of all feature flags."""
    status = {}
    for flag, info in FEATURE_FLAGS.items():
        env_value = os.getenv(flag)
        if env_value is None:
            status[flag] = info["production_default"]
        else:
            status[flag] = env_value.lower() in ("1", "true", "yes")
    return status


def get_env_validation_summary() -> Dict[str, List[str]]:
    """
    Get summary of ENV variable validation.

    Returns dict with:
    - missing_required: Required vars that are not set
    - missing_recommended: Recommended vars that are not set
    - invalid_values: Vars with invalid values
    """
    missing_required = []
    missing_recommended = []
    invalid_values = []

    # Check required
    for var in REQUIRED_ENV_VARS:
        val = os.getenv(var)
        if not val or val.strip() == "":
            missing_required.append(var)

    # Check recommended
    for var in RECOMMENDED_ENV_VARS:
        val = os.getenv(var)
        if not val or val.strip() == "":
            missing_recommended.append(var)

    # Check validated
    for var, rules in VALIDATED_ENV_VARS.items():
        val = os.getenv(var)
        if val:
            if rules.get("allowed") and val.lower() not in [v.lower() for v in rules["allowed"]]:
                invalid_values.append(f"{var}={val} (allowed: {rules['allowed']})")
            if rules.get("type") == "int":
                try:
                    int_val = int(val)
                    if rules.get("min") and int_val < rules["min"]:
                        invalid_values.append(f"{var}={val} (min: {rules['min']})")
                    if rules.get("max") and int_val > rules["max"]:
                        invalid_values.append(f"{var}={val} (max: {rules['max']})")
                except ValueError:
                    invalid_values.append(f"{var}={val} (expected int)")

    return {
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "invalid_values": invalid_values,
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G15-A] Release configuration module loaded (Release R1)")
