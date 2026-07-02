# -*- coding: utf-8 -*-
"""
FIX-505: Centralized OpenAI Retry Module

This module provides a single source of truth for all OpenAI HTTP calls,
ensuring consistent timeout handling, retry logic, and logging.

Key Features:
- Centralized request function with exact timeout logging
- Exponential backoff retry with jitter
- Respect for Retry-After header on 429 responses
- Per-section timeout configuration
- STRICT_MODE fail-closed behavior
- Debug attachments for Admin emails on failure

Usage:
    from services.openai_retry import openai_request, OpenAIRequestError

    result = openai_request(
        section="recommendations_expand",
        payload={...},
        connect_timeout_s=10,
        read_timeout_s=300,
    )

Version: 1.0.0 (FIX-505)
"""
from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import requests

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# STRICT_MODE: Fail hard on exhausted retries
RELEASE_STRICT_MODE = os.getenv("RELEASE_STRICT_MODE", "0") in ("1", "true", "True")

# Default timeouts (seconds)
# FIX-514: Accept both OPENAI_TIMEOUT_CONNECT and OPENAI_CONNECT_TIMEOUT env vars
DEFAULT_CONNECT_TIMEOUT = float(
    os.getenv("OPENAI_TIMEOUT_CONNECT", os.getenv("OPENAI_CONNECT_TIMEOUT", "10"))
)
# FIX-514: Accept both OPENAI_TIMEOUT_READ and OPENAI_READ_TIMEOUT, default 180
DEFAULT_READ_TIMEOUT = float(
    os.getenv("OPENAI_TIMEOUT_READ", os.getenv("OPENAI_READ_TIMEOUT", "180"))
)
EXPAND_READ_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_READ_EXPAND", "300"))
REPAIR_READ_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_READ_REPAIR", "300"))

# Retry configuration
DEFAULT_MAX_ATTEMPTS = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
BACKOFF_BASE = float(os.getenv("OPENAI_BACKOFF_BASE", "1.0"))
BACKOFF_FACTOR = float(os.getenv("OPENAI_BACKOFF_FACTOR", "2.0"))
BACKOFF_MAX = float(os.getenv("OPENAI_BACKOFF_MAX", "30.0"))
JITTER_RANGE = float(os.getenv("OPENAI_JITTER_RANGE", "0.5"))

# Retryable HTTP status codes
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

# Per-section timeout overrides
SECTION_TIMEOUTS: Dict[str, Tuple[float, float]] = {
    # (connect_timeout, read_timeout)
    # Expand sections (N4.6 2-pass)
    "recommendations_expand": (DEFAULT_CONNECT_TIMEOUT, EXPAND_READ_TIMEOUT),
    "gamechanger_expand": (DEFAULT_CONNECT_TIMEOUT, EXPAND_READ_TIMEOUT),
    "roadmap_expand": (DEFAULT_CONNECT_TIMEOUT, EXPAND_READ_TIMEOUT),
    "risks_expand": (DEFAULT_CONNECT_TIMEOUT, EXPAND_READ_TIMEOUT),
    # Repair sections
    "html_repair": (DEFAULT_CONNECT_TIMEOUT, REPAIR_READ_TIMEOUT),
    "quickwins_repair": (DEFAULT_CONNECT_TIMEOUT, REPAIR_READ_TIMEOUT),
    # Heavy sections
    "unternehmensprofil_markt": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "strategie_governance": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "wettbewerb_benchmark": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "roadmap_12m": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "risks": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "risk_report": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "gamechanger": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "recommendations": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "foerderpotenzial": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "exec_summary": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "ki_stack_summary": (DEFAULT_CONNECT_TIMEOUT, 165.0),
    "branch_deep_dive": (DEFAULT_CONNECT_TIMEOUT, 165.0),
}


# =============================================================================
# EXCEPTIONS
# =============================================================================

class OpenAIRequestError(Exception):
    """FIX-505: Raised when an OpenAI request fails after all retries."""

    def __init__(
        self,
        message: str,
        section: str,
        attempts: int,
        last_error: Optional[Exception] = None,
        debug_info: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.section = section
        self.attempts = attempts
        self.last_error = last_error
        self.debug_info = debug_info or {}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RetryAttempt:
    """Record of a single retry attempt."""
    attempt: int
    success: bool
    error: Optional[str] = None
    status_code: Optional[int] = None
    sleep_duration: float = 0.0
    timeout_used: Tuple[float, float] = (0.0, 0.0)


@dataclass
class OpenAIResponse:
    """Result of an OpenAI request."""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    section: str = ""
    model: str = ""
    attempts: int = 0
    total_time_ms: float = 0.0
    timeout_used: Tuple[float, float] = (0.0, 0.0)
    attempts_log: List[RetryAttempt] = field(default_factory=list)
    finish_reason: Optional[str] = None
    completion_tokens: int = 0

    def to_debug_dict(self) -> Dict[str, Any]:
        """Convert to dict for debug attachments."""
        return {
            "success": self.success,
            "section": self.section,
            "model": self.model,
            "attempts": self.attempts,
            "total_time_ms": self.total_time_ms,
            "timeout_used": list(self.timeout_used),
            "finish_reason": self.finish_reason,
            "completion_tokens": self.completion_tokens,
            "error": self.error,
            "attempts_log": [
                {
                    "attempt": a.attempt,
                    "success": a.success,
                    "error": a.error,
                    "status_code": a.status_code,
                    "sleep_duration": a.sleep_duration,
                    "timeout_used": list(a.timeout_used),
                }
                for a in self.attempts_log
            ],
        }


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def get_section_timeout(section: str) -> Tuple[float, float]:
    """
    Get timeout tuple for a section.

    Args:
        section: Section name

    Returns:
        Tuple of (connect_timeout, read_timeout)
    """
    # Check for explicit override
    if section in SECTION_TIMEOUTS:
        return SECTION_TIMEOUTS[section]

    # Check for _expand or _repair suffix
    if section.endswith("_expand"):
        return (DEFAULT_CONNECT_TIMEOUT, EXPAND_READ_TIMEOUT)
    if section.endswith("_repair"):
        return (DEFAULT_CONNECT_TIMEOUT, REPAIR_READ_TIMEOUT)

    # Default timeouts
    return (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)


def calculate_backoff(attempt: int, retry_after: Optional[float] = None) -> float:
    """
    Calculate backoff duration with jitter.

    Args:
        attempt: Current attempt number (1-indexed)
        retry_after: Optional Retry-After header value

    Returns:
        Sleep duration in seconds
    """
    if retry_after is not None and retry_after > 0:
        # Respect Retry-After header
        return min(retry_after, BACKOFF_MAX)

    # Exponential backoff: base * factor^(attempt-1)
    backoff = BACKOFF_BASE * (BACKOFF_FACTOR ** (attempt - 1))

    # Add jitter: ±JITTER_RANGE
    jitter = random.uniform(-JITTER_RANGE, JITTER_RANGE) * backoff
    backoff += jitter

    # Cap at max
    return min(backoff, BACKOFF_MAX)


def is_retryable_error(error: Exception) -> Tuple[bool, str]:
    """
    Check if an error is retryable.

    Args:
        error: The exception

    Returns:
        Tuple of (is_retryable, reason)
    """
    # Timeout errors
    if isinstance(error, requests.exceptions.ReadTimeout):
        return True, "ReadTimeout"
    if isinstance(error, requests.exceptions.ConnectTimeout):
        return True, "ConnectTimeout"
    if isinstance(error, requests.exceptions.ConnectionError):
        return True, "ConnectionError"

    # HTTP errors
    if isinstance(error, requests.exceptions.HTTPError):
        if hasattr(error, "response") and error.response is not None:
            status = error.response.status_code
            if status in RETRYABLE_STATUS_CODES:
                return True, f"HTTP_{status}"

    return False, "non_retryable"


def parse_retry_after(response: requests.Response) -> Optional[float]:
    """
    Parse Retry-After header from response.

    Args:
        response: HTTP response

    Returns:
        Retry duration in seconds, or None
    """
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None

    try:
        # Try parsing as integer seconds
        return float(retry_after)
    except ValueError:
        pass

    # Could also parse HTTP date format, but typically OpenAI uses seconds
    return None


def openai_request(
    section: str,
    payload: Dict[str, Any],
    api_key: str,
    api_base: str = "https://api.openai.com",
    connect_timeout_s: Optional[float] = None,
    read_timeout_s: Optional[float] = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    strict_mode: Optional[bool] = None,
) -> OpenAIResponse:
    """
    FIX-505: Central function for all OpenAI HTTP calls.

    This is the Single Source of Truth for OpenAI requests. It ensures:
    - Exact timeout logging (what you see = what you get)
    - Proper retry with exponential backoff + jitter
    - Respect for Retry-After headers
    - STRICT_MODE fail-closed behavior

    Args:
        section: Section name for logging/timeout selection
        payload: Request payload (model, messages, etc.)
        api_key: OpenAI API key
        api_base: API base URL
        connect_timeout_s: Optional connect timeout override
        read_timeout_s: Optional read timeout override
        max_attempts: Maximum retry attempts (default: 3)
        strict_mode: Override for RELEASE_STRICT_MODE

    Returns:
        OpenAIResponse with result or error

    Raises:
        OpenAIRequestError: In STRICT_MODE when all retries exhausted
    """
    start_time = time.perf_counter()
    is_strict = strict_mode if strict_mode is not None else RELEASE_STRICT_MODE

    # Determine timeouts
    default_connect, default_read = get_section_timeout(section)
    connect_timeout = connect_timeout_s if connect_timeout_s is not None else default_connect
    read_timeout = read_timeout_s if read_timeout_s is not None else default_read
    timeout_tuple = (connect_timeout, read_timeout)

    # FIX-514: Definitive timeout log (single source of truth)
    source_env = "OPENAI_TIMEOUT_READ_EXPAND" if read_timeout == EXPAND_READ_TIMEOUT else "OPENAI_TIMEOUT_READ"
    model = payload.get("model", "unknown")
    log.info(
        "[FIX-514][OPENAI] section=%s model=%s timeout=(connect=%d,read=%d) source_env=%s",
        section, model, int(connect_timeout), int(read_timeout), source_env
    )

    # Build URL and headers
    url = f"{api_base.rstrip('/')}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    if "openai.azure.com" in api_base:
        headers["api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    response = OpenAIResponse(
        success=False,
        section=section,
        model=model,
        timeout_used=timeout_tuple,
    )

    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        attempt_record = RetryAttempt(
            attempt=attempt,
            success=False,
            timeout_used=timeout_tuple,
        )

        # Log the attempt with EXACT timeout tuple
        log.info(
            "[FIX-505][OPENAI] attempt=%d/%d section=%s timeout=(%d,%d) model=%s",
            attempt, max_attempts, section,
            int(connect_timeout), int(read_timeout), model
        )

        try:
            r = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout_tuple,
            )

            # Check for retryable status codes
            if r.status_code in RETRYABLE_STATUS_CODES:
                retry_after = parse_retry_after(r)
                sleep_duration = calculate_backoff(attempt, retry_after)

                log.warning(
                    "[FIX-505][OPENAI][RETRY] section=%s in=%.1fs reason=HTTP_%d",
                    section, sleep_duration, r.status_code
                )

                attempt_record.error = f"HTTP_{r.status_code}"
                attempt_record.status_code = r.status_code
                attempt_record.sleep_duration = sleep_duration
                response.attempts_log.append(attempt_record)

                if attempt < max_attempts:
                    time.sleep(sleep_duration)
                continue

            r.raise_for_status()

            # Parse successful response
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            finish_reason = data["choices"][0].get("finish_reason", "unknown")
            completion_tokens = data.get("usage", {}).get("completion_tokens", 0)

            response.success = True
            response.content = str(content)
            response.finish_reason = finish_reason
            response.completion_tokens = completion_tokens
            response.attempts = attempt
            response.total_time_ms = (time.perf_counter() - start_time) * 1000

            attempt_record.success = True
            response.attempts_log.append(attempt_record)

            log.info(
                "[FIX-505][OPENAI] success section=%s attempt=%d/%d "
                "finish_reason=%s tokens=%d time=%.0fms",
                section, attempt, max_attempts,
                finish_reason, completion_tokens, response.total_time_ms
            )

            return response

        except requests.exceptions.RequestException as e:
            last_error = e
            is_retryable, reason = is_retryable_error(e)

            log.warning(
                "[FIX-505][OPENAI][RETRY] section=%s attempt=%d/%d reason=%s error=%s",
                section, attempt, max_attempts, reason, str(e)[:100]
            )

            attempt_record.error = reason
            attempt_record.sleep_duration = 0.0

            if is_retryable and attempt < max_attempts:
                sleep_duration = calculate_backoff(attempt)
                attempt_record.sleep_duration = sleep_duration
                response.attempts_log.append(attempt_record)

                log.info(
                    "[FIX-505][OPENAI][RETRY] section=%s in=%.1fs reason=%s",
                    section, sleep_duration, reason
                )
                time.sleep(sleep_duration)
            else:
                response.attempts_log.append(attempt_record)
                break

        except (KeyError, IndexError, TypeError) as e:
            # Response parsing error - not retryable
            last_error = e
            attempt_record.error = f"parse_error: {str(e)[:50]}"
            response.attempts_log.append(attempt_record)
            log.error(
                "[FIX-505][OPENAI] parse error section=%s error=%s",
                section, str(e)[:100]
            )
            break

    # All retries exhausted
    response.attempts = max_attempts
    response.total_time_ms = (time.perf_counter() - start_time) * 1000
    response.error = str(last_error)[:200] if last_error else "Unknown error"

    log.error(
        "[FIX-505][OPENAI][EXHAUSTED] section=%s attempts=%d timeout=(%d,%d) "
        "last_error=%s strict=%d",
        section, max_attempts, int(connect_timeout), int(read_timeout),
        response.error, int(is_strict)
    )

    if is_strict:
        raise OpenAIRequestError(
            f"[FIX-505][OPENAI] STRICT_MODE: All {max_attempts} attempts exhausted for section={section}",
            section=section,
            attempts=max_attempts,
            last_error=last_error,
            debug_info=response.to_debug_dict(),
        )
    else:
        log.warning(
            "[FIX-505][OPENAI][FALLBACK] section=%s attempts_exhausted=%d",
            section, max_attempts
        )

    return response


def openai_request_simple(
    section: str,
    prompt: str,
    system_prompt: str = "Du bist ein KI-Berater.",
    model: str = os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature: float = 0.2,
    max_tokens: int = 3000,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    strict_mode: Optional[bool] = None,
) -> Optional[str]:
    """
    Simplified interface for OpenAI requests.

    This wraps openai_request() with common defaults for easier use.

    Args:
        section: Section name
        prompt: User prompt
        system_prompt: System prompt
        model: Model name
        temperature: Temperature
        max_tokens: Max tokens
        api_key: API key (from env if not provided)
        api_base: API base URL
        strict_mode: STRICT_MODE override

    Returns:
        Response content or None on failure
    """
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        log.error("[FIX-505][OPENAI] No API key provided")
        return None

    base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com")

    # Reasoning models (gpt-5.x, o-series) reject temperature with 400.
    from services.llm_client import maybe_openai_temperature
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        **maybe_openai_temperature(model, temperature),
    }

    # Set token parameter based on model
    if model.startswith("gpt-5"):
        payload["max_completion_tokens"] = max_tokens
    else:
        payload["max_tokens"] = max_tokens

    try:
        response = openai_request(
            section=section,
            payload=payload,
            api_key=key,
            api_base=base,
            strict_mode=strict_mode,
        )
        return response.content if response.success else None
    except OpenAIRequestError as e:
        # In STRICT_MODE, let it propagate
        raise
    except Exception as e:
        log.error("[FIX-505][OPENAI] Unexpected error: %s", str(e)[:100])
        return None


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[FIX-505][OPENAI] Retry module loaded: "
    "default_timeout=(%d,%d) expand_timeout=%d repair_timeout=%d "
    "max_attempts=%d backoff=%.1fx%.1f strict=%d",
    int(DEFAULT_CONNECT_TIMEOUT), int(DEFAULT_READ_TIMEOUT),
    int(EXPAND_READ_TIMEOUT), int(REPAIR_READ_TIMEOUT),
    DEFAULT_MAX_ATTEMPTS, BACKOFF_BASE, BACKOFF_FACTOR,
    int(RELEASE_STRICT_MODE)
)
