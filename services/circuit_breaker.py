# -*- coding: utf-8 -*-
"""
Sprint G12: Circuit Breaker for LLM Providers

Implements circuit breaker pattern for OpenAI and Anthropic APIs to prevent
cascade failures and enable auto-recovery.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit tripped, requests fail fast (60s pause)
- HALF_OPEN: Testing recovery, allows 1 probe request

Version: 1.0.0 (Sprint G12)
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

LLM_CIRCUIT_BREAKER_ENABLED = os.getenv("LLM_CIRCUIT_BREAKER_ENABLED", "1").lower() in ("1", "true", "yes")
LLM_CIRCUIT_FAILURE_THRESHOLD = int(os.getenv("LLM_CIRCUIT_FAILURE_THRESHOLD", "5"))
LLM_CIRCUIT_RESET_SECONDS = int(os.getenv("LLM_CIRCUIT_RESET_SECONDS", "60"))
LLM_CIRCUIT_WINDOW_SECONDS = int(os.getenv("LLM_CIRCUIT_WINDOW_SECONDS", "90"))
LLM_CIRCUIT_STATE_FILE = os.getenv("LLM_CIRCUIT_STATE_FILE", "/tmp/circuit_breaker_state.json")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit tripped, fail fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ProviderState:
    """State tracking for a single provider."""
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    opened_at: float = 0.0
    failure_timestamps: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "opened_at": self.opened_at,
            "failure_timestamps": self.failure_timestamps,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderState":
        state = cls(name=data.get("name", "unknown"))
        state.state = CircuitState(data.get("state", "closed"))
        state.failure_count = data.get("failure_count", 0)
        state.success_count = data.get("success_count", 0)
        state.last_failure_time = data.get("last_failure_time", 0.0)
        state.last_success_time = data.get("last_success_time", 0.0)
        state.opened_at = data.get("opened_at", 0.0)
        state.failure_timestamps = data.get("failure_timestamps", [])
        return state


class CircuitBreakerError(Exception):
    """Raised when circuit is open and request cannot proceed."""
    def __init__(self, provider: str, retry_after: float):
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker OPEN for {provider}. Retry after {retry_after:.1f}s")


# =============================================================================
# CIRCUIT BREAKER IMPLEMENTATION
# =============================================================================

class CircuitBreaker:
    """
    Circuit breaker for LLM providers with sliding window failure tracking.

    Features:
    - Sliding window (90s default) for failure counting
    - Configurable failure threshold (5 default)
    - Auto-reset after timeout (60s default)
    - Half-open probing for recovery testing
    - Persistent state via file or Redis
    """

    def __init__(
        self,
        failure_threshold: int = LLM_CIRCUIT_FAILURE_THRESHOLD,
        reset_timeout: int = LLM_CIRCUIT_RESET_SECONDS,
        window_seconds: int = LLM_CIRCUIT_WINDOW_SECONDS,
        state_file: str = LLM_CIRCUIT_STATE_FILE,
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.window_seconds = window_seconds
        self.state_file = state_file
        self._providers: Dict[str, ProviderState] = {}
        self._lock = threading.RLock()
        self._load_state()

    def _get_provider(self, name: str) -> ProviderState:
        """Get or create provider state."""
        if name not in self._providers:
            self._providers[name] = ProviderState(name=name)
        return self._providers[name]

    def _clean_old_failures(self, provider: ProviderState) -> None:
        """Remove failures outside the sliding window."""
        now = time.time()
        cutoff = now - self.window_seconds
        provider.failure_timestamps = [
            ts for ts in provider.failure_timestamps if ts > cutoff
        ]
        provider.failure_count = len(provider.failure_timestamps)

    def check(self, provider_name: str) -> bool:
        """
        Check if request can proceed for given provider.

        Returns True if request can proceed, raises CircuitBreakerError if circuit is open.
        """
        if not LLM_CIRCUIT_BREAKER_ENABLED:
            return True

        with self._lock:
            provider = self._get_provider(provider_name)
            now = time.time()

            if provider.state == CircuitState.CLOSED:
                return True

            elif provider.state == CircuitState.OPEN:
                # Check if reset timeout has passed
                time_since_open = now - provider.opened_at
                if time_since_open >= self.reset_timeout:
                    # Transition to half-open for probing
                    provider.state = CircuitState.HALF_OPEN
                    log.info("[G12-CB] Circuit %s transitioning to HALF_OPEN for probe", provider_name)
                    self._save_state()
                    return True
                else:
                    retry_after = self.reset_timeout - time_since_open
                    raise CircuitBreakerError(provider_name, retry_after)

            elif provider.state == CircuitState.HALF_OPEN:
                # Allow single probe request
                return True

        return True

    def record_failure(self, provider_name: str, error: Optional[Exception] = None) -> None:
        """Record a failure for the provider."""
        if not LLM_CIRCUIT_BREAKER_ENABLED:
            return

        with self._lock:
            provider = self._get_provider(provider_name)
            now = time.time()

            # Add failure timestamp
            provider.failure_timestamps.append(now)
            provider.last_failure_time = now

            # Clean old failures and recount
            self._clean_old_failures(provider)

            error_msg = str(error)[:100] if error else "unknown"
            log.warning(
                "[G12-CB] Failure recorded for %s: count=%d threshold=%d error=%s",
                provider_name, provider.failure_count, self.failure_threshold, error_msg
            )

            if provider.state == CircuitState.HALF_OPEN:
                # Probe failed, reopen circuit
                provider.state = CircuitState.OPEN
                provider.opened_at = now
                log.error("[G12-CB] Circuit %s probe FAILED - reopening circuit", provider_name)

            elif provider.state == CircuitState.CLOSED:
                if provider.failure_count >= self.failure_threshold:
                    # Trip the circuit
                    provider.state = CircuitState.OPEN
                    provider.opened_at = now
                    log.error(
                        "[G12-CB] Circuit %s OPENED after %d failures in %ds window",
                        provider_name, provider.failure_count, self.window_seconds
                    )

            self._save_state()

    def record_success(self, provider_name: str) -> None:
        """Record a success for the provider."""
        if not LLM_CIRCUIT_BREAKER_ENABLED:
            return

        with self._lock:
            provider = self._get_provider(provider_name)
            now = time.time()

            provider.success_count += 1
            provider.last_success_time = now

            if provider.state == CircuitState.HALF_OPEN:
                # Probe succeeded, close circuit
                provider.state = CircuitState.CLOSED
                provider.failure_timestamps = []
                provider.failure_count = 0
                log.info("[G12-CB] Circuit %s CLOSED after successful probe", provider_name)

            self._save_state()

    def get_status(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current status of circuit breaker(s)."""
        with self._lock:
            if provider_name:
                provider = self._get_provider(provider_name)
                self._clean_old_failures(provider)
                return provider.to_dict()
            else:
                result = {}
                for name, provider in self._providers.items():
                    self._clean_old_failures(provider)
                    result[name] = provider.to_dict()
                return result

    def reset(self, provider_name: Optional[str] = None) -> None:
        """Reset circuit breaker state (for admin/testing)."""
        with self._lock:
            if provider_name:
                if provider_name in self._providers:
                    self._providers[provider_name] = ProviderState(name=provider_name)
                    log.info("[G12-CB] Circuit %s manually reset", provider_name)
            else:
                self._providers = {}
                log.info("[G12-CB] All circuits manually reset")
            self._save_state()

    def force_open(self, provider_name: str) -> None:
        """Force circuit open (for testing/maintenance)."""
        with self._lock:
            provider = self._get_provider(provider_name)
            provider.state = CircuitState.OPEN
            provider.opened_at = time.time()
            log.warning("[G12-CB] Circuit %s forced OPEN", provider_name)
            self._save_state()

    def _save_state(self) -> None:
        """Persist state to file."""
        try:
            state = {
                name: provider.to_dict()
                for name, provider in self._providers.items()
            }
            Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f)
        except Exception as e:
            log.warning("[G12-CB] Could not save state: %s", e)

    def _load_state(self) -> None:
        """Load state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                for name, data in state.items():
                    self._providers[name] = ProviderState.from_dict(data)
                log.info("[G12-CB] Loaded state for %d providers", len(self._providers))
        except Exception as e:
            log.warning("[G12-CB] Could not load state: %s", e)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_breaker_instance: Optional[CircuitBreaker] = None
_breaker_lock = threading.Lock()


def get_circuit_breaker() -> CircuitBreaker:
    """Get singleton circuit breaker instance."""
    global _breaker_instance
    if _breaker_instance is None:
        with _breaker_lock:
            if _breaker_instance is None:
                _breaker_instance = CircuitBreaker()
    return _breaker_instance


# =============================================================================
# DECORATOR FOR PROTECTED CALLS
# =============================================================================

T = TypeVar('T')


def circuit_protected(provider: str) -> Callable:
    """
    Decorator to protect a function with circuit breaker.

    Usage:
        @circuit_protected("openai")
        def call_openai_api(...):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            breaker = get_circuit_breaker()
            breaker.check(provider)  # May raise CircuitBreakerError
            try:
                result = func(*args, **kwargs)
                breaker.record_success(provider)
                return result
            except Exception as e:
                breaker.record_failure(provider, e)
                raise
        return wrapper
    return decorator


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G12] Circuit Breaker loaded - enabled=%s threshold=%d reset=%ds window=%ds",
    LLM_CIRCUIT_BREAKER_ENABLED,
    LLM_CIRCUIT_FAILURE_THRESHOLD,
    LLM_CIRCUIT_RESET_SECONDS,
    LLM_CIRCUIT_WINDOW_SECONDS,
)
