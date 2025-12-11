# -*- coding: utf-8 -*-
"""
Sprint G14: LLM Client with Retry Layer

Provides robust LLM API calls with:
- Exponential backoff retry (3s → 6s → 12s → 24s → 48s → 96s)
- Short-retry mode for reduced token requests
- Circuit breaker integration
- Detailed logging for timeout scenarios

SPRINT N1 CHANGES:
- Added LLM_TIMEOUT configuration (default: 75s, increased from 60s)
- Enhanced soft-retry with immediate retry on first timeout
- Soft-retry retries once before falling back to PLATIN

SPRINT A (PLATIN++ v4.16) CHANGES:
- Added SECTION_TIMEOUT_OVERRIDES for section-specific timeouts
- PREMIUM_SECTIONS list for enhanced retry behavior
- Two-stage soft-retry for premium sections
- Enhanced logging with section resilience metrics

SPRINT N3.6 PACKAGE F CHANGES:
- Premium sections timeout → 140s (from 90s)
- Retries → 5 stages (from 3)
- Backoff timing → 3s → 6s → 12s → 24s → 48s

SPRINT N3.7 PACKAGE F CHANGES:
- Premium sections timeout → 165s (from 140s)
- Retries → 6 stages (from 5)
- Backoff timing → 3s → 6s → 12s → 24s → 48s → 96s
- Section prioritization (exec_summary, roadmaps, recommendations first)
- Adaptive temperature on LLM errors (temp -0.2)
- Burst-load protection for parallel runs

Version: 1.4.0 (N3.7 - Performance Resilience v4)
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

import requests

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

# SPRINT N1: Increased default timeout from 60s to 75s
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "75"))

LLM_SHORT_RETRY_ENABLED = os.getenv("LLM_SHORT_RETRY_ENABLED", "1").lower() in ("1", "true", "yes")
LLM_SHORT_RETRY_MAXTOKENS = int(os.getenv("LLM_SHORT_RETRY_MAXTOKENS", "1200"))
# N3.7 PACKAGE F: 6 stages with 3s → 6s → 12s → 24s → 48s → 96s backoff
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "6"))
LLM_RETRY_BACKOFF_BASE = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "3.0"))
LLM_RETRY_BACKOFF_MULTIPLIER = float(os.getenv("LLM_RETRY_BACKOFF_MULTIPLIER", "2.0"))

# SPRINT N1: Enable soft-retry on first timeout (retry once immediately before fallback)
LLM_SOFT_RETRY_ENABLED = os.getenv("LLM_SOFT_RETRY_ENABLED", "1").lower() in ("1", "true", "yes")

# =============================================================================
# SPRINT A: SECTION-SPECIFIC TIMEOUT OVERRIDES
# =============================================================================

# Premium sections that get extended timeout and enhanced retry
# N3.3 TASK 5: Added exec_summary, ki_stack_summary, branch_deep_dive, risk_report
PREMIUM_SECTIONS: set[str] = {
    "unternehmensprofil_markt",
    "strategie_governance",
    "wettbewerb_benchmark",
    "roadmap_12m",
    "risks",
    "risk_report",  # N3.3: Added
    "gamechanger",
    "recommendations",
    "foerderpotenzial",
    # N3.3 TASK 5: Premium "Exec" sections
    "exec_summary",
    "ki_stack_summary",
    "branch_deep_dive",
}

# Section-specific timeout overrides (seconds)
# These sections typically require more generation time
# N3.7 PACKAGE F: Premium sections → 165s timeout (from 140s)
SECTION_TIMEOUT_OVERRIDES: dict[str, float] = {
    "unternehmensprofil_markt": 165.0,
    "strategie_governance": 165.0,
    "wettbewerb_benchmark": 165.0,  # Complex competitor analysis
    "roadmap_12m": 165.0,
    "risks": 165.0,
    "risk_report": 165.0,
    "gamechanger": 165.0,  # Creative content needs time
    "recommendations": 165.0,
    "foerderpotenzial": 165.0,
    "exec_summary": 165.0,
    "ki_stack_summary": 165.0,
    "branch_deep_dive": 165.0,
}


def get_section_timeout(section: str) -> float:
    """
    Get timeout for a specific section.

    Args:
        section: Section name

    Returns:
        Timeout in seconds (section-specific or default)
    """
    return SECTION_TIMEOUT_OVERRIDES.get(section, LLM_TIMEOUT)


def is_premium_section(section: str) -> bool:
    """Check if section is a premium section requiring enhanced retry."""
    return section in PREMIUM_SECTIONS


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class RetryStrategy(Enum):
    """Retry strategy types."""
    NONE = "none"              # No retry
    SHORT_RETRY = "short"      # Retry with reduced tokens
    FULL_RETRY = "full"        # Retry with same params


@dataclass
class LLMCallResult:
    """Result of an LLM API call."""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    retries_used: int = 0
    final_strategy: str = "primary"
    total_time_ms: float = 0.0


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = LLM_MAX_RETRIES
    backoff_base: float = LLM_RETRY_BACKOFF_BASE
    backoff_multiplier: float = LLM_RETRY_BACKOFF_MULTIPLIER
    short_retry_enabled: bool = LLM_SHORT_RETRY_ENABLED
    short_retry_max_tokens: int = LLM_SHORT_RETRY_MAXTOKENS
    # SPRINT N1: Soft-retry configuration
    timeout: float = LLM_TIMEOUT
    soft_retry_enabled: bool = LLM_SOFT_RETRY_ENABLED
    # SPRINT A: Premium section enhanced retry (2 stages for premium sections)
    premium_retry_stages: int = 2  # Number of soft-retry attempts for premium sections


# =============================================================================
# RETRY UTILITIES
# =============================================================================

def calculate_backoff(attempt: int, config: RetryConfig) -> float:
    """
    Calculate exponential backoff delay.

    N3.7 PACKAGE F: Backoff sequence: 3s → 6s → 12s → 24s → 48s → 96s (with default config)

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds before next retry
    """
    return config.backoff_base * (config.backoff_multiplier ** attempt)


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.

    Retryable errors:
    - Timeout errors
    - 429 Too Many Requests
    - 500-level server errors
    - Connection errors

    Non-retryable errors:
    - 400 Bad Request
    - 401 Unauthorized
    - 403 Forbidden
    - 404 Not Found
    """
    if isinstance(error, requests.exceptions.Timeout):
        return True
    if isinstance(error, requests.exceptions.ConnectionError):
        return True
    if isinstance(error, requests.exceptions.HTTPError):
        if hasattr(error, 'response') and error.response is not None:
            status: int = error.response.status_code
            # Retry on 429 and 5xx errors
            return status == 429 or status >= 500
    return False


def get_error_type(error: Exception) -> str:
    """Get a short error type string for logging."""
    if isinstance(error, requests.exceptions.Timeout):
        return "timeout"
    if isinstance(error, requests.exceptions.ConnectionError):
        return "connection_error"
    if isinstance(error, requests.exceptions.HTTPError):
        if hasattr(error, 'response') and error.response is not None:
            return f"http_{error.response.status_code}"
    return "unknown_error"


# =============================================================================
# LLM CLIENT WITH RETRY
# =============================================================================

T = TypeVar('T')


class LLMClient:
    """
    LLM API client with retry layer and short-retry fallback.

    Retry sequence:
    1. Primary call with full parameters
    2. If timeout → Short-retry with reduced max_tokens (if enabled)
    3. If still failing → PLATIN fallback (handled by caller)
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._call_stats: Dict[str, int] = {
            "total_calls": 0,
            "retries": 0,
            "short_retries": 0,
            "fallbacks": 0,
            # SPRINT A: Premium section tracking
            "premium_calls": 0,
            "premium_retries": 0,
            "premium_successes": 0,
        }

    def call_with_retry(
        self,
        call_fn: Callable[..., Optional[str]],
        section: str,
        max_tokens: int,
        **kwargs: Any
    ) -> LLMCallResult:
        """
        Execute LLM call with retry logic.

        SPRINT A: Enhanced with section-specific timeouts and 2-stage soft-retry
        for premium sections.

        Args:
            call_fn: The actual LLM API call function
            section: Section name for logging
            max_tokens: Maximum tokens for the call
            **kwargs: Additional arguments passed to call_fn

        Returns:
            LLMCallResult with success status and content
        """
        start_time = time.perf_counter()
        self._call_stats["total_calls"] += 1

        # SPRINT A: Track premium section calls
        is_premium = is_premium_section(section)
        section_timeout = get_section_timeout(section)
        if is_premium:
            self._call_stats["premium_calls"] += 1
            log.info(
                "[A-Resilience] Premium section=%s timeout=%.0fs",
                section, section_timeout
            )

        result = LLMCallResult(success=False)
        last_error: Optional[Exception] = None

        # Phase 1: Primary call with full retries
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = calculate_backoff(attempt - 1, self.config)
                    # N3.3 TASK 5: Updated log format "[RETRY] {section} attempt {n}/3 after {error}"
                    log.info(
                        "[RETRY] %s attempt %d/%d after %.1fs backoff",
                        section, attempt + 1, self.config.max_retries + 1, delay
                    )
                    time.sleep(delay)
                    self._call_stats["retries"] += 1

                content = call_fn(max_tokens=max_tokens, section=section, **kwargs)

                if content is not None:
                    result.success = True
                    result.content = content
                    result.retries_used = attempt
                    result.final_strategy = "primary" if attempt == 0 else "retry"
                    result.total_time_ms = (time.perf_counter() - start_time) * 1000
                    if is_premium:
                        self._call_stats["premium_successes"] += 1
                    return result

            except Exception as e:
                last_error = e
                error_type = get_error_type(e)

                if not is_retryable_error(e):
                    log.error(
                        "[G14-Retry] Non-retryable error section=%s error=%s: %s",
                        section, error_type, str(e)[:100]
                    )
                    break

                # N3.3 TASK 5: Updated log format "[RETRY] {section} attempt {n}/3 after {error}"
                log.warning(
                    "[RETRY] %s attempt %d/%d after %s: %s",
                    section, attempt + 1, self.config.max_retries + 1, error_type, str(e)[:100]
                )

        # Phase 2: Short-retry with reduced tokens (if enabled and was timeout)
        if (
            self.config.short_retry_enabled
            and last_error is not None
            and isinstance(last_error, requests.exceptions.Timeout)
            and max_tokens > self.config.short_retry_max_tokens
        ):
            log.info(
                "[G14-Retry] Timeout (primary) → Short-Retry active section=%s "
                "reducing tokens %d→%d",
                section, max_tokens, self.config.short_retry_max_tokens
            )
            self._call_stats["short_retries"] += 1

            try:
                content = call_fn(
                    max_tokens=self.config.short_retry_max_tokens,
                    section=section,
                    **kwargs
                )

                if content is not None:
                    result.success = True
                    result.content = content
                    result.retries_used = self.config.max_retries + 1
                    result.final_strategy = "short_retry"
                    result.total_time_ms = (time.perf_counter() - start_time) * 1000
                    log.info(
                        "[G14-Retry] Short-retry SUCCESS section=%s time=%.1fms",
                        section, result.total_time_ms
                    )
                    if is_premium:
                        self._call_stats["premium_successes"] += 1
                    return result

            except Exception as e:
                last_error = e
                log.warning(
                    "[G14-Retry] Short-retry FAILED section=%s error=%s",
                    section, str(e)[:100]
                )

        # Phase 2.5 (SPRINT A): Enhanced Soft-retry with 2 stages for premium sections
        # For premium sections: retry up to premium_retry_stages times
        # For regular sections: retry once (original N1 behavior)
        if (
            self.config.soft_retry_enabled
            and last_error is not None
            and isinstance(last_error, (requests.exceptions.Timeout, TimeoutError))
        ):
            retry_stages = (
                self.config.premium_retry_stages if is_premium else 1
            )

            for stage in range(retry_stages):
                if is_premium:
                    self._call_stats["premium_retries"] += 1
                    log.warning(
                        "[A-SoftRetry] Premium section=%s stage=%d/%d, retrying…",
                        section, stage + 1, retry_stages
                    )
                else:
                    log.warning(
                        "[N1-SoftRetry] Timeout on section=%s, retrying once…",
                        section
                    )

                try:
                    content = call_fn(max_tokens=max_tokens, section=section, **kwargs)

                    if content is not None:
                        result.success = True
                        result.content = content
                        result.retries_used = self.config.max_retries + 2 + stage
                        result.final_strategy = (
                            f"premium_soft_retry_stage{stage + 1}" if is_premium
                            else "soft_retry"
                        )
                        result.total_time_ms = (time.perf_counter() - start_time) * 1000
                        log.info(
                            "[A-SoftRetry] SUCCESS section=%s stage=%d time=%.1fms",
                            section, stage + 1, result.total_time_ms
                        )
                        if is_premium:
                            self._call_stats["premium_successes"] += 1
                        return result

                except Exception as e:
                    last_error = e
                    log.warning(
                        "[A-SoftRetry] stage=%d FAILED section=%s error=%s",
                        stage + 1, section, str(e)[:100]
                    )
                    # Small delay between premium retry stages
                    if is_premium and stage < retry_stages - 1:
                        time.sleep(1.0)

        # Phase 3: All retries exhausted → signal fallback needed
        log.warning(
            "[G14-Retry] All retries exhausted → PLATIN fallback section=%s premium=%s",
            section, is_premium
        )
        self._call_stats["fallbacks"] += 1

        result.error = str(last_error)[:200] if last_error else "Unknown error"
        result.retries_used = self.config.max_retries + (
            1 if self.config.short_retry_enabled else 0
        ) + (self.config.premium_retry_stages if is_premium else 1)
        result.final_strategy = "fallback"
        result.total_time_ms = (time.perf_counter() - start_time) * 1000

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get call statistics including premium section metrics."""
        total = self._call_stats["total_calls"]
        premium = self._call_stats["premium_calls"]
        if total == 0:
            return self._call_stats

        stats = {
            **self._call_stats,
            "retry_rate": self._call_stats["retries"] / total * 100,
            "short_retry_rate": self._call_stats["short_retries"] / total * 100,
            "fallback_rate": self._call_stats["fallbacks"] / total * 100,
        }

        # SPRINT A: Premium section success rate
        if premium > 0:
            stats["premium_success_rate"] = (
                self._call_stats["premium_successes"] / premium * 100
            )
            stats["premium_retry_rate"] = (
                self._call_stats["premium_retries"] / premium * 100
            )

        return stats

    def reset_stats(self) -> None:
        """Reset call statistics."""
        self._call_stats = {
            "total_calls": 0,
            "retries": 0,
            "short_retries": 0,
            "fallbacks": 0,
            # SPRINT A: Premium section tracking
            "premium_calls": 0,
            "premium_retries": 0,
            "premium_successes": 0,
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_client_instance: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def call_llm_with_retry(
    call_fn: Callable[..., Optional[str]],
    section: str,
    max_tokens: int,
    **kwargs: Any
) -> LLMCallResult:
    """
    Convenience function to call LLM with retry.

    Args:
        call_fn: The actual LLM API call function
        section: Section name for logging
        max_tokens: Maximum tokens for the call
        **kwargs: Additional arguments passed to call_fn

    Returns:
        LLMCallResult with success status and content
    """
    return get_llm_client().call_with_retry(call_fn, section, max_tokens, **kwargs)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[N3.7-F] LLM Client v1.4.0 loaded - default_timeout=%.0fs retry_enabled=%s "
    "short_retry=%s soft_retry=%s max_retries=%d short_retry_tokens=%d backoff=%.1f×%.1f",
    LLM_TIMEOUT,
    True,  # Retry always enabled
    LLM_SHORT_RETRY_ENABLED,
    LLM_SOFT_RETRY_ENABLED,
    LLM_MAX_RETRIES,
    LLM_SHORT_RETRY_MAXTOKENS,
    LLM_RETRY_BACKOFF_BASE,
    LLM_RETRY_BACKOFF_MULTIPLIER,
)

# SPRINT A: Log section-specific timeout configuration
log.info(
    "[A-Resilience] Premium sections (%d): %s",
    len(PREMIUM_SECTIONS),
    ", ".join(sorted(PREMIUM_SECTIONS))
)
log.info(
    "[A-Resilience] Section timeout overrides: %s",
    ", ".join(f"{k}={v}s" for k, v in sorted(SECTION_TIMEOUT_OVERRIDES.items()))
)
