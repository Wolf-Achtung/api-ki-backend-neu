# -*- coding: utf-8 -*-
"""
Sprint G14: LLM Client with Retry Layer

Provides robust LLM API calls with:
- Exponential backoff retry (1.0s → 2.0s → 4.0s)
- Short-retry mode for reduced token requests
- Circuit breaker integration
- Detailed logging for timeout scenarios

Version: 1.0.0 (Sprint G14)
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

LLM_SHORT_RETRY_ENABLED = os.getenv("LLM_SHORT_RETRY_ENABLED", "1").lower() in ("1", "true", "yes")
LLM_SHORT_RETRY_MAXTOKENS = int(os.getenv("LLM_SHORT_RETRY_MAXTOKENS", "1200"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
LLM_RETRY_BACKOFF_BASE = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "1.0"))
LLM_RETRY_BACKOFF_MULTIPLIER = float(os.getenv("LLM_RETRY_BACKOFF_MULTIPLIER", "2.0"))


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


# =============================================================================
# RETRY UTILITIES
# =============================================================================

def calculate_backoff(attempt: int, config: RetryConfig) -> float:
    """
    Calculate exponential backoff delay.

    Backoff sequence: 1.0s → 2.0s → 4.0s (with default config)

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
            status = error.response.status_code
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

        result = LLMCallResult(success=False)
        last_error: Optional[Exception] = None

        # Phase 1: Primary call with full retries
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = calculate_backoff(attempt - 1, self.config)
                    log.info(
                        "[G14-Retry] section=%s attempt=%d/%d backoff=%.1fs",
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

                log.warning(
                    "[G14-Retry] Retryable error section=%s attempt=%d error=%s: %s",
                    section, attempt + 1, error_type, str(e)[:100]
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
                    return result

            except Exception as e:
                log.warning(
                    "[G14-Retry] Short-retry FAILED section=%s error=%s",
                    section, str(e)[:100]
                )

        # Phase 3: All retries exhausted → signal fallback needed
        log.warning(
            "[G14-Retry] Timeout (secondary) → PLATIN fallback section=%s",
            section
        )
        self._call_stats["fallbacks"] += 1

        result.error = str(last_error)[:200] if last_error else "Unknown error"
        result.retries_used = self.config.max_retries + (
            1 if self.config.short_retry_enabled else 0
        )
        result.final_strategy = "fallback"
        result.total_time_ms = (time.perf_counter() - start_time) * 1000

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get call statistics."""
        total = self._call_stats["total_calls"]
        if total == 0:
            return self._call_stats

        return {
            **self._call_stats,
            "retry_rate": self._call_stats["retries"] / total * 100,
            "short_retry_rate": self._call_stats["short_retries"] / total * 100,
            "fallback_rate": self._call_stats["fallbacks"] / total * 100,
        }

    def reset_stats(self) -> None:
        """Reset call statistics."""
        self._call_stats = {
            "total_calls": 0,
            "retries": 0,
            "short_retries": 0,
            "fallbacks": 0,
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
    "[G14] LLM Client loaded - retry_enabled=%s short_retry=%s max_retries=%d "
    "short_retry_tokens=%d backoff=%.1f×%.1f",
    True,  # Retry always enabled
    LLM_SHORT_RETRY_ENABLED,
    LLM_MAX_RETRIES,
    LLM_SHORT_RETRY_MAXTOKENS,
    LLM_RETRY_BACKOFF_BASE,
    LLM_RETRY_BACKOFF_MULTIPLIER,
)
