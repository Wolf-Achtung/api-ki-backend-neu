# -*- coding: utf-8 -*-
"""
Tests for Sprint G12: Circuit Breaker

Tests circuit breaker state transitions, failure tracking, and recovery.
"""
import os
import time
import pytest

# Set test environment
os.environ["LLM_CIRCUIT_BREAKER_ENABLED"] = "1"
os.environ["LLM_CIRCUIT_FAILURE_THRESHOLD"] = "3"
os.environ["LLM_CIRCUIT_RESET_SECONDS"] = "2"
os.environ["LLM_CIRCUIT_WINDOW_SECONDS"] = "10"
os.environ["LLM_CIRCUIT_STATE_FILE"] = "/tmp/test_circuit_breaker.json"


class TestCircuitBreaker:
    """Test suite for circuit breaker functionality."""

    def setup_method(self) -> None:
        """Reset circuit breaker before each test."""
        # Import here to pick up env vars
        from services.circuit_breaker import CircuitBreaker, CircuitState
        self.CircuitBreaker = CircuitBreaker
        self.CircuitState = CircuitState
        self.breaker = CircuitBreaker(
            failure_threshold=3,
            reset_timeout=2,
            window_seconds=10,
            state_file="/tmp/test_circuit_breaker.json",
        )
        self.breaker.reset()

    def test_initial_state_closed(self) -> None:
        """Circuit should start in CLOSED state."""
        status = self.breaker.get_status("openai")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0

    def test_check_passes_when_closed(self) -> None:
        """Check should pass when circuit is closed."""
        assert self.breaker.check("openai") is True

    def test_record_success(self) -> None:
        """Record success should increment counter."""
        self.breaker.record_success("openai")
        status = self.breaker.get_status("openai")
        assert status["success_count"] == 1

    def test_record_failure_increments_count(self) -> None:
        """Record failure should increment failure count."""
        self.breaker.record_failure("openai", Exception("test error"))
        status = self.breaker.get_status("openai")
        assert status["failure_count"] == 1
        assert status["state"] == "closed"

    def test_circuit_opens_after_threshold(self) -> None:
        """Circuit should open after reaching failure threshold."""
        for i in range(3):
            self.breaker.record_failure("openai", Exception(f"error {i}"))

        status = self.breaker.get_status("openai")
        assert status["state"] == "open"
        assert status["failure_count"] == 3

    def test_check_fails_when_open(self) -> None:
        """Check should fail when circuit is open."""
        from services.circuit_breaker import CircuitBreakerError

        # Trip the circuit
        for i in range(3):
            self.breaker.record_failure("openai")

        with pytest.raises(CircuitBreakerError) as exc_info:
            self.breaker.check("openai")

        assert exc_info.value.provider == "openai"
        assert exc_info.value.retry_after > 0

    def test_circuit_transitions_to_half_open(self) -> None:
        """Circuit should transition to half-open after reset timeout."""
        # Trip the circuit
        for i in range(3):
            self.breaker.record_failure("openai")

        # Wait for reset timeout
        time.sleep(2.5)

        # Check should now pass (half-open)
        assert self.breaker.check("openai") is True
        status = self.breaker.get_status("openai")
        assert status["state"] == "half_open"

    def test_half_open_success_closes_circuit(self) -> None:
        """Success in half-open state should close circuit."""
        # Trip and wait
        for i in range(3):
            self.breaker.record_failure("openai")
        time.sleep(2.5)

        # Transition to half-open
        self.breaker.check("openai")

        # Record success
        self.breaker.record_success("openai")

        status = self.breaker.get_status("openai")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0

    def test_half_open_failure_reopens_circuit(self) -> None:
        """Failure in half-open state should reopen circuit."""
        # Trip and wait
        for i in range(3):
            self.breaker.record_failure("openai")
        time.sleep(2.5)

        # Transition to half-open
        self.breaker.check("openai")

        # Record failure
        self.breaker.record_failure("openai")

        status = self.breaker.get_status("openai")
        assert status["state"] == "open"

    def test_multiple_providers(self) -> None:
        """Each provider should have independent state."""
        self.breaker.record_failure("openai")
        self.breaker.record_failure("openai")
        self.breaker.record_failure("openai")

        openai_status = self.breaker.get_status("openai")
        anthropic_status = self.breaker.get_status("anthropic")

        assert openai_status["state"] == "open"
        assert anthropic_status["state"] == "closed"

    def test_sliding_window_expires_old_failures(self) -> None:
        """Old failures should expire from sliding window."""
        breaker = self.CircuitBreaker(
            failure_threshold=3,
            reset_timeout=2,
            window_seconds=1,  # Very short window
            state_file="/tmp/test_circuit_breaker2.json",
        )
        breaker.reset()

        # Record 2 failures
        breaker.record_failure("test")
        breaker.record_failure("test")

        # Wait for window to expire
        time.sleep(1.5)

        # This should not trip circuit (old failures expired)
        breaker.record_failure("test")

        status = breaker.get_status("test")
        assert status["state"] == "closed"
        assert status["failure_count"] == 1

    def test_force_open(self) -> None:
        """Force open should immediately open circuit."""
        self.breaker.force_open("openai")
        status = self.breaker.get_status("openai")
        assert status["state"] == "open"

    def test_reset_clears_state(self) -> None:
        """Reset should clear all state."""
        self.breaker.record_failure("openai")
        self.breaker.record_failure("openai")

        self.breaker.reset("openai")

        status = self.breaker.get_status("openai")
        assert status["failure_count"] == 0
        assert status["state"] == "closed"


class TestCircuitProtectedDecorator:
    """Test the circuit_protected decorator."""

    def setup_method(self) -> None:
        from services.circuit_breaker import get_circuit_breaker
        self.breaker = get_circuit_breaker()
        self.breaker.reset()

    def test_decorator_records_success(self) -> None:
        """Decorator should record success on normal return."""
        from services.circuit_breaker import circuit_protected

        @circuit_protected("test_provider")
        def successful_call() -> str:
            return "success"

        result = successful_call()
        assert result == "success"

        status = self.breaker.get_status("test_provider")
        assert status["success_count"] >= 1

    def test_decorator_records_failure(self) -> None:
        """Decorator should record failure on exception."""
        from services.circuit_breaker import circuit_protected

        @circuit_protected("test_provider2")
        def failing_call() -> str:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            failing_call()

        status = self.breaker.get_status("test_provider2")
        assert status["failure_count"] >= 1
