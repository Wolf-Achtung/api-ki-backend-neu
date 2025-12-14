# utils/llm_overrides.py
"""
Helper to override model/temperature/max_tokens for specific sections.

STABILITY PATCH v1 (GPT-5.2):
Section-specific token budgets to prevent truncation on long-form sections.

ENV Variables (Railway):
  # High-Risk sections (must be high)
  TOKENS_ROADMAP=4500
  TOKENS_ROADMAP_12M=4500
  TOKENS_ORG_CHANGE=3000
  TOKENS_UNTERNEHMENSPROFIL_MARKT=2800
  TOKENS_BUSINESS_CASE=5000
  TOKENS_GAMECHANGER=5000

  # Medium sections
  TOKENS_RISKS=3500
  TOKENS_STRATEGIE_GOVERNANCE=3500
  TOKENS_WETTBEWERB_BENCHMARK=3500
  TOKENS_FOERDERPOTENZIAL=3500

  # Short-form (warnings OK)
  TOKENS_ONE_LINER=80
  TOKENS_KI_STACK_SUMMARY=1200
  TOKENS_EXECUTIVE_SUMMARY=1500

Fallback: If ENV not set, uses code default from SECTION_TOKEN_BUDGETS.
"""
from __future__ import annotations
import os
import logging
from typing import Dict, Any

log = logging.getLogger(__name__)


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


# =============================================================================
# STABILITY PATCH v1: Section-Specific Token Budgets
# =============================================================================
# Problem: Token limits hit same sections, causing truncation + fallbacks.
# Solution: Targeted token increases for high-risk sections only.
#
# Categories:
#   🔴 High-Risk (must be high): roadmap, business_case, gamechanger
#   🟡 Medium: risks, strategie_governance, benchmark
#   🟢 Short-form (warnings OK): one_liner, ki_stack_summary
# =============================================================================

SECTION_TOKEN_BUDGETS: Dict[str, int] = {
    # 🔴 High-Risk sections (must be high)
    "roadmap": 4500,
    "roadmap_90d": 4500,
    "roadmap_12m": 4500,
    "org_change": 3000,
    "unternehmensprofil_markt": 2800,
    "business_case": 5000,
    "business_case_simulation": 5000,
    "gamechanger": 5000,
    "gamechanger_expand": 5000,

    # 🟡 Medium sections
    "risks": 3500,
    "risk_report": 3500,
    "strategie_governance": 3500,
    "wettbewerb_benchmark": 3500,
    "foerderpotenzial": 3500,
    "recommendations": 3500,

    # 🟢 Short-form (warnings accepted)
    "one_liner": 80,
    "ki_stack_summary": 1200,
    "executive_summary": 1500,
    "exec_summary": 1500,
}

# ENV variable prefix for token overrides
TOKEN_ENV_PREFIX = "TOKENS_"


def get_section_token_budget(section: str) -> int:
    """
    Get token budget for a specific section.

    Checks ENV first (e.g., TOKENS_ROADMAP), falls back to SECTION_TOKEN_BUDGETS,
    then to global OPENAI_MAX_TOKENS default.

    Args:
        section: Section name (case-insensitive)

    Returns:
        Token budget (int)
    """
    section_lower = section.lower().strip()

    # Check ENV override first (TOKENS_<SECTION_NAME>)
    env_key = f"{TOKEN_ENV_PREFIX}{section_lower.upper()}"
    env_value = os.getenv(env_key)
    if env_value:
        try:
            tokens = int(env_value)
            log.debug("[TokenBudget] %s → %d (from ENV %s)", section, tokens, env_key)
            return tokens
        except ValueError:
            pass

    # Check predefined budget
    if section_lower in SECTION_TOKEN_BUDGETS:
        tokens = SECTION_TOKEN_BUDGETS[section_lower]
        log.debug("[TokenBudget] %s → %d (from defaults)", section, tokens)
        return tokens

    # Fallback to global default
    default_tokens = _get_int("OPENAI_MAX_TOKENS", 3000)
    log.debug("[TokenBudget] %s → %d (global default)", section, default_tokens)
    return default_tokens


def exec_summary_llm_config() -> Dict[str, Any]:
    """Return LLM params for the Executive Summary based on env overrides.
    Env:
      - OPENAI_MODEL_EXEC_SUMMARY
      - OPENAI_TEMP_EXEC_SUMMARY
      - OPENAI_MAX_TOKENS_EXEC_SUMMARY (optional)
      - TOKENS_EXECUTIVE_SUMMARY (Stability Patch v1)
    Fallback:
      - OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
    """
    model = os.getenv("OPENAI_MODEL_EXEC_SUMMARY") or os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = _get_float("OPENAI_TEMP_EXEC_SUMMARY", _get_float("OPENAI_TEMPERATURE", 0.2))

    # Stability Patch v1: Check section-specific budget first
    max_tokens = get_section_token_budget("executive_summary")

    # Legacy override still takes precedence if explicitly set
    legacy_override = os.getenv("OPENAI_MAX_TOKENS_EXEC_SUMMARY")
    if legacy_override:
        max_tokens = _get_int("OPENAI_MAX_TOKENS_EXEC_SUMMARY", max_tokens)

    # clamp
    temperature = min(max(temperature, 0.0), 2.0)
    max_tokens = max(256, max_tokens)
    return {"model": model, "temperature": temperature, "max_tokens": max_tokens}


def llm_config_for(section: str) -> Dict[str, Any]:
    """
    Get LLM configuration for a specific section.

    Stability Patch v1: Uses section-specific token budgets.

    Args:
        section: Section name

    Returns:
        Dict with model, temperature, max_tokens
    """
    section_lower = (section or "").lower()

    # Special handling for exec_summary (legacy compatibility)
    if section_lower in {"executive_summary", "exec_summary", "summary"}:
        return exec_summary_llm_config()

    # Standard config with section-specific token budget
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = _get_float("OPENAI_TEMPERATURE", 0.2)
    max_tokens = get_section_token_budget(section_lower)

    return {"model": model, "temperature": temperature, "max_tokens": max_tokens}


# Log loaded token budgets at module init
_high_risk = ["roadmap", "roadmap_12m", "business_case", "gamechanger"]
_budget_summary = ", ".join(
    f"{s}={SECTION_TOKEN_BUDGETS.get(s, 3000)}"
    for s in _high_risk
)
log.info("[Stability-v1] Token budgets loaded (high-risk): %s", _budget_summary)
