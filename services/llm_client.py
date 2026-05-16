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

STABILITY PATCH v1 (GPT-5.2):
- OpenAI read timeout → 120s (OPENAI_TIMEOUT_READ)
- Max retries → 3 (OPENAI_MAX_RETRIES) with backoff 1s → 3s → 7s
- Retry on ReadTimeout, 502, 503, ConnectionReset
- OpenAI concurrency semaphore (OPENAI_MAX_PARALLEL_REQUESTS=3)
- Log format: [LLM-RETRY] section=… attempt=N/3 reason=…

Version: 1.6.0 (Stability Patch v1 - GPT-5.2)
"""
from __future__ import annotations

import logging
import os
import threading
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
# STABILITY PATCH v1: OpenAI-specific Timeout/Retry/Concurrency
# =============================================================================
# Problem: Real ReadTimeout (45s) on long GPT-5.2 calls → fallbacks, truncation
# Solution: Dedicated OpenAI retry with longer timeout and concurrency control
#
# ENV Configuration:
#   OPENAI_TIMEOUT_READ=120        # Read timeout for OpenAI calls (seconds)
#   OPENAI_MAX_RETRIES=3           # Max retry attempts for OpenAI
#   OPENAI_RETRY_BACKOFF=exponential  # Backoff strategy
#   OPENAI_MAX_PARALLEL_REQUESTS=3 # Max concurrent OpenAI requests
# =============================================================================

OPENAI_TIMEOUT_READ = float(os.getenv("OPENAI_TIMEOUT_READ", "120"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
OPENAI_MAX_PARALLEL_REQUESTS = int(os.getenv("OPENAI_MAX_PARALLEL_REQUESTS", "3"))

# Stability Patch: Custom backoff sequence (1s → 3s → 7s)
OPENAI_RETRY_BACKOFF_STAGES = [1.0, 3.0, 7.0]

# Retryable HTTP status codes for OpenAI
OPENAI_RETRYABLE_STATUS_CODES = {502, 503, 429, 500}

# Global semaphore for OpenAI concurrency control
_openai_semaphore: Optional[threading.Semaphore] = None
_openai_semaphore_lock = threading.Lock()

# Timeout tracking for adaptive throttling
_timeout_counter = {"count": 0, "last_reset": time.time()}
_timeout_counter_lock = threading.Lock()


def get_openai_semaphore() -> threading.Semaphore:
    """Get or create OpenAI concurrency semaphore."""
    global _openai_semaphore
    with _openai_semaphore_lock:
        if _openai_semaphore is None:
            _openai_semaphore = threading.Semaphore(OPENAI_MAX_PARALLEL_REQUESTS)
            log.info(
                "[Stability-v1] OpenAI semaphore initialized: max_parallel=%d",
                OPENAI_MAX_PARALLEL_REQUESTS
            )
        return _openai_semaphore


def record_openai_timeout() -> int:
    """Record a timeout and return current count in window."""
    global _timeout_counter
    with _timeout_counter_lock:
        now = time.time()
        # Reset counter every 5 minutes
        if now - _timeout_counter["last_reset"] > 300:
            _timeout_counter["count"] = 0
            _timeout_counter["last_reset"] = now
        _timeout_counter["count"] += 1
        return int(_timeout_counter["count"])  # Cast to satisfy mypy


def is_openai_retryable_error(error: Exception) -> tuple[bool, str]:
    """
    Check if an error is retryable for OpenAI calls.

    Returns:
        Tuple of (is_retryable, reason_string)
    """
    # ReadTimeout
    if isinstance(error, requests.exceptions.ReadTimeout):
        return True, "timeout"

    # ConnectTimeout
    if isinstance(error, requests.exceptions.ConnectTimeout):
        return True, "connect_timeout"

    # ConnectionError (includes ConnectionReset)
    if isinstance(error, requests.exceptions.ConnectionError):
        error_str = str(error).lower()
        if "reset" in error_str or "connection" in error_str:
            return True, "connection_reset"
        return True, "connection_error"

    # HTTP errors with retryable status codes (502, 503, 429)
    if isinstance(error, requests.exceptions.HTTPError):
        if hasattr(error, 'response') and error.response is not None:
            status = error.response.status_code
            if status in OPENAI_RETRYABLE_STATUS_CODES:
                return True, f"http_{status}"

    return False, "non_retryable"


# =============================================================================
# GPT-5.2 MIGRATION: MODEL ROUTING SCAFFOLDING
# =============================================================================
# Task-based routing infrastructure to optimize model usage:
# - FAST: Quick tasks, HTML snippets, format generation (lower latency)
# - REASONING: Complex tasks requiring deep analysis (higher quality)
# - DEFAULT: Falls back to primary model (OPENAI_MODEL)
#
# PHASE 0/1 - SCAFFOLDING (Zero-Change):
#   No ENV changes needed. If OPENAI_MODEL_FAST/REASONING are not set,
#   the system uses OPENAI_MODEL (existing behavior preserved).
#
# PHASE 2 - ENABLE GPT-5.2 (Railway ENV Overrides):
#   OPENAI_MODEL_FAST=gpt-5.2-chat-latest      # Quick tasks
#   OPENAI_MODEL_REASONING=gpt-5.2             # Complex analysis
#   OPENAI_MODEL_FALLBACK=gpt-4.1-mini         # Stable fallback (not 5.2)
#   OPENAI_REASONING_EFFORT=high               # low|medium|high (xhigh selectively)
#
# VERIFICATION (Railway Logs):
#   Search for "[GPT5.2] Model Routing enabled" in Railway log viewer.
# =============================================================================

class ModelTier(Enum):
    """Model tier for task-based routing."""
    FAST = "fast"           # Quick tasks, HTML snippets
    REASONING = "reasoning"  # Complex analysis (Consistency, Governance)
    DEFAULT = "default"      # Primary model


# Sections that require REASONING model (complex analysis)
REASONING_SECTIONS: set[str] = {
    # Cross-Section Consistency / Auto-Heal (G22)
    "consistency_check",
    "auto_heal",
    "cross_section_validation",
    # Governance / Compliance
    "governance_narrative",
    "compliance_analysis",
    "ai_act_assessment",
    # Long-form reasoning tasks
    "executive_summary",
    "risk_analysis",
    "strategic_recommendations",
}

# Sections that use FAST model (quick generation)
FAST_SECTIONS: set[str] = {
    # Format/Snippet generators
    "html_snippet",
    "badge_generation",
    "kpi_format",
    "table_render",
    # Short content
    "label_generation",
    "status_badge",
}


def get_model_tier(section: str) -> ModelTier:
    """
    Determine which model tier to use for a section.

    GPT-5.2 Migration: Routes tasks to appropriate model based on complexity.

    Args:
        section: Section/task name

    Returns:
        ModelTier enum value
    """
    section_lower = section.lower()

    # Check for reasoning keywords
    for reasoning_key in REASONING_SECTIONS:
        if reasoning_key in section_lower:
            return ModelTier.REASONING

    # Check for fast keywords
    for fast_key in FAST_SECTIONS:
        if fast_key in section_lower:
            return ModelTier.FAST

    # Default: use primary model
    return ModelTier.DEFAULT


def get_model_for_section(section: str) -> str:
    """
    Get the appropriate model name for a section.

    Reads from settings to support ENV-based configuration.

    Args:
        section: Section/task name

    Returns:
        Model name string (e.g., "gpt-5.2" or "gpt-4o")
    """
    try:
        from settings import get_settings
        s = get_settings()
        openai_config = s.openai
    except Exception:
        # Fallback if settings not available
        return os.getenv("OPENAI_MODEL", "gpt-4o")

    tier = get_model_tier(section)

    if tier == ModelTier.REASONING:
        model = openai_config.model_reasoning
        log.debug("[GPT5.2] Section=%s → REASONING model=%s", section, model)
        return model
    elif tier == ModelTier.FAST:
        model = openai_config.model_fast
        log.debug("[GPT5.2] Section=%s → FAST model=%s", section, model)
        return model
    else:
        # DEFAULT: use primary model
        return openai_config.model


def get_reasoning_effort() -> str:
    """Get reasoning effort level from settings."""
    try:
        from settings import get_settings
        return get_settings().openai.reasoning_effort
    except Exception:
        return os.getenv("OPENAI_REASONING_EFFORT", "high")


_OPENAI_REASONING_MODEL_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def is_openai_reasoning_model(model: str) -> bool:
    """gpt-5.x and o-series models only accept the default temperature (1)
    and reject any explicit temperature value with 400."""
    m = (model or "").lower()
    return any(m.startswith(p) for p in _OPENAI_REASONING_MODEL_PREFIXES)


def maybe_openai_temperature(model: str, value: float) -> dict:
    """Return ``{"temperature": value}`` only when the model accepts it.
    Reasoning models (gpt-5.x, o1/o3/o4) reject the parameter outright."""
    if is_openai_reasoning_model(model):
        return {}
    return {"temperature": float(value)}


# =============================================================================
# STABILITY PATCH v1: OpenAI Call Wrapper with Retry & Semaphore
# =============================================================================

def call_openai_with_stability(
    call_fn: Callable[..., Optional[str]],
    section: str,
    max_tokens: int,
    **kwargs: Any
) -> Optional[str]:
    """
    Stability Patch v1: Call OpenAI with concurrency control and retry.

    Features:
    - Semaphore-limited concurrency (default: 3 parallel)
    - Retry on timeout/502/503/ConnectionReset
    - Exponential backoff: 1s → 3s → 7s
    - Adaptive throttling on high timeout count

    Args:
        call_fn: The actual OpenAI API call function
        section: Section name for logging
        max_tokens: Maximum tokens for the call
        **kwargs: Additional arguments passed to call_fn

    Returns:
        Response content or None on failure
    """
    semaphore = get_openai_semaphore()
    last_error: Optional[Exception] = None

    for attempt in range(1, OPENAI_MAX_RETRIES + 1):
        # Acquire semaphore for concurrency control
        acquired = semaphore.acquire(timeout=OPENAI_TIMEOUT_READ + 30)
        if not acquired:
            log.warning(
                "[LLM-RETRY] section=%s attempt=%d/%d reason=semaphore_timeout",
                section, attempt, OPENAI_MAX_RETRIES
            )
            continue

        try:
            # Execute the actual call
            result = call_fn(max_tokens=max_tokens, section=section, **kwargs)
            return result

        except Exception as e:
            last_error = e
            is_retryable, reason = is_openai_retryable_error(e)

            log.warning(
                "[LLM-RETRY] section=%s attempt=%d/%d reason=%s",
                section, attempt, OPENAI_MAX_RETRIES, reason
            )

            if not is_retryable:
                log.error(
                    "[LLM-RETRY] section=%s non-retryable error: %s",
                    section, str(e)[:100]
                )
                break

            # Record timeout for adaptive throttling
            if reason == "timeout":
                timeout_count = record_openai_timeout()
                if timeout_count >= 2:
                    log.warning(
                        "[LLM-RETRY] High timeout count (%d) in window, consider reducing parallelism",
                        timeout_count
                    )

            # Apply backoff before retry
            if attempt < OPENAI_MAX_RETRIES:
                backoff_idx = min(attempt - 1, len(OPENAI_RETRY_BACKOFF_STAGES) - 1)
                backoff = OPENAI_RETRY_BACKOFF_STAGES[backoff_idx]
                log.info(
                    "[LLM-RETRY] section=%s backoff=%.1fs before attempt %d",
                    section, backoff, attempt + 1
                )
                time.sleep(backoff)

        finally:
            semaphore.release()

    # All retries exhausted
    if last_error:
        log.error(
            "[LLM-RETRY] section=%s exhausted all %d retries, last_error=%s",
            section, OPENAI_MAX_RETRIES, str(last_error)[:100]
        )

    return None


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
    "[Stability-v1] LLM Client v1.6.0 loaded - default_timeout=%.0fs retry_enabled=%s "
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

# Stability Patch v1: Log OpenAI-specific configuration
log.info(
    "[Stability-v1] OpenAI config: timeout_read=%.0fs max_retries=%d max_parallel=%d "
    "backoff=%s",
    OPENAI_TIMEOUT_READ,
    OPENAI_MAX_RETRIES,
    OPENAI_MAX_PARALLEL_REQUESTS,
    "→".join(f"{s}s" for s in OPENAI_RETRY_BACKOFF_STAGES),
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

# GPT-5.2 Migration: Log model routing configuration
try:
    from settings import get_settings
    _s = get_settings()
    log.info(
        "[GPT5.2] Model Routing enabled - fast=%s reasoning=%s fallback=%s effort=%s",
        _s.openai.model_fast,
        _s.openai.model_reasoning,
        _s.openai.model_fallback,
        _s.openai.reasoning_effort,
    )
    log.info(
        "[GPT5.2] REASONING sections (%d): %s",
        len(REASONING_SECTIONS),
        ", ".join(sorted(REASONING_SECTIONS))
    )
    log.info(
        "[GPT5.2] FAST sections (%d): %s",
        len(FAST_SECTIONS),
        ", ".join(sorted(FAST_SECTIONS))
    )
except Exception as _e:
    log.warning("[GPT5.2] Could not load settings for model routing: %s", _e)
