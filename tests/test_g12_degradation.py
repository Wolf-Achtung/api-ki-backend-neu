# -*- coding: utf-8 -*-
"""
Tests for Sprint G12: Degradation Monitor

Tests health scoring, event tracking, and status calculation.
"""
import os
import time
import pytest

# Set test environment
os.environ["DEGRADATION_MONITORING_ENABLED"] = "1"
os.environ["DEGRADATION_HARD_STOP_THRESHOLD"] = "30"
os.environ["DEGRADATION_WARN_THRESHOLD"] = "60"
os.environ["DEGRADATION_WINDOW_SECONDS"] = "10"


class TestDegradationMonitor:
    """Test suite for degradation monitoring."""

    def setup_method(self) -> None:
        """Reset monitor before each test."""
        from services.degradation_monitor import DegradationMonitor, HealthStatus
        self.HealthStatus = HealthStatus

        # Create fresh instance by clearing singleton
        DegradationMonitor._instance = None
        self.monitor = DegradationMonitor()
        self.monitor.reset()

    def test_initial_score_is_100(self) -> None:
        """Initial health score should be 100."""
        assert self.monitor.get_current_score() == 100

    def test_initial_status_is_healthy(self) -> None:
        """Initial status should be HEALTHY."""
        assert self.monitor.get_status() == self.HealthStatus.HEALTHY

    def test_record_fallback_reduces_score(self) -> None:
        """Recording fallback should reduce score."""
        self.monitor.record_fallback("TEST_SECTION", "test reason")

        score = self.monitor.get_current_score()
        assert score < 100

    def test_record_timeout_reduces_score_more(self) -> None:
        """Timeouts should have greater impact than fallbacks."""
        # Create two fresh monitors
        from services.degradation_monitor import DegradationMonitor
        DegradationMonitor._instance = None
        monitor1 = DegradationMonitor()
        monitor1.reset()

        DegradationMonitor._instance = None
        monitor2 = DegradationMonitor()
        monitor2.reset()

        # Record fallback in first
        monitor1.record_fallback("TEST")

        # Record timeout in second
        monitor2.record_timeout("TEST", 30)

        # Timeout should have bigger impact
        assert monitor2.get_current_score() < monitor1.get_current_score()

    def test_multiple_events_cumulative(self) -> None:
        """Multiple events should have cumulative effect."""
        score1 = self.monitor.get_current_score()

        self.monitor.record_fallback("SECTION1")
        score2 = self.monitor.get_current_score()

        self.monitor.record_fallback("SECTION2")
        score3 = self.monitor.get_current_score()

        assert score1 > score2 > score3

    def test_status_degrades_with_events(self) -> None:
        """Status should degrade as events accumulate."""
        # Start healthy
        assert self.monitor.get_status() == self.HealthStatus.HEALTHY

        # Add events to reach degraded
        for i in range(10):
            self.monitor.record_fallback(f"SECTION_{i}")

        status = self.monitor.get_status()
        assert status in (self.HealthStatus.DEGRADED, self.HealthStatus.CRITICAL)

    def test_is_critical_detection(self) -> None:
        """is_critical should return True when score below threshold."""
        # Add many events
        for i in range(5):
            self.monitor.record_timeout(f"SECTION_{i}")
            self.monitor.record_section_disabled(f"SECTION_{i}")

        assert self.monitor.is_critical() is True

    def test_full_status_contains_details(self) -> None:
        """get_full_status should return complete details."""
        self.monitor.record_fallback("TEST", "fallback reason")
        self.monitor.record_timeout("TEST2", 30)

        status = self.monitor.get_full_status()

        assert "enabled" in status
        assert "score" in status
        assert "status" in status
        assert "event_counts" in status
        assert "affected_sections" in status
        assert "recent_events" in status

    def test_request_tracking(self) -> None:
        """Request tracking should work correctly."""
        self.monitor.start_request("req_123")

        self.monitor.record_fallback("SECTION1")
        self.monitor.record_fallback("SECTION2")

        result = self.monitor.end_request("req_123", success=True)

        assert "metrics" in result
        assert "score" in result
        assert "status" in result
        assert result["metrics"]["fallback_count"] == 2

    def test_degradation_status_for_report(self) -> None:
        """get_degradation_status_for_report should return report-friendly format."""
        status = self.monitor.get_degradation_status_for_report()

        assert "score" in status
        assert "status" in status
        assert "healthy" in status

        # When healthy, no warning
        assert status["healthy"] is True

    def test_degraded_status_includes_warning(self) -> None:
        """Degraded status should include warning message."""
        # Add events to degrade
        for i in range(10):
            self.monitor.record_fallback(f"SECTION_{i}")

        status = self.monitor.get_degradation_status_for_report()

        if not status["healthy"]:
            assert "warning" in status

    def test_old_events_expire(self) -> None:
        """Events outside window should expire."""
        from services.degradation_monitor import DegradationMonitor
        DegradationMonitor._instance = None

        # Create monitor with very short window
        os.environ["DEGRADATION_WINDOW_SECONDS"] = "1"
        monitor = DegradationMonitor()
        monitor.reset()

        monitor.record_fallback("TEST")
        assert monitor.get_current_score() < 100

        # Wait for expiry
        time.sleep(1.5)

        # Score should be back to 100
        assert monitor.get_current_score() == 100

        # Reset env
        os.environ["DEGRADATION_WINDOW_SECONDS"] = "10"

    def test_reset_clears_all(self) -> None:
        """Reset should clear all events."""
        self.monitor.record_fallback("TEST")
        self.monitor.record_timeout("TEST")

        self.monitor.reset()

        assert self.monitor.get_current_score() == 100
        status = self.monitor.get_full_status()
        assert status["total_events"] == 0


class TestDegradationHelperFunctions:
    """Test helper functions."""

    def setup_method(self) -> None:
        from services.degradation_monitor import get_degradation_monitor
        get_degradation_monitor().reset()

    def test_record_fallback_helper(self) -> None:
        """Helper function should work."""
        from services.degradation_monitor import record_fallback, get_degradation_score

        record_fallback("TEST", "reason")

        assert get_degradation_score() < 100

    def test_is_system_critical_helper(self) -> None:
        """is_system_critical helper should work."""
        from services.degradation_monitor import (
            is_system_critical,
            record_timeout,
            record_section_disabled,
        )

        # Initially not critical
        assert is_system_critical() is False

        # Add many events
        for i in range(5):
            record_timeout(f"SEC_{i}")
            record_section_disabled(f"SEC_{i}")

        # Should be critical now
        assert is_system_critical() is True
