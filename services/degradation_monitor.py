# -*- coding: utf-8 -*-
"""
Sprint G12: Degradation Monitor

Tracks system health metrics and automatically detects degradation:
- Fallback usage count
- Timeout occurrences
- Disabled sections
- Overall health score (0-100)

Status levels:
- HEALTHY (60-100): Normal operation
- DEGRADED (30-59): Reduced functionality, warnings active
- CRITICAL (0-29): Hard stop, minimal functionality

Version: 1.0.0 (Sprint G12)
"""
from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

DEGRADATION_ENABLED = os.getenv("DEGRADATION_MONITORING_ENABLED", "1").lower() in ("1", "true", "yes")
DEGRADATION_HARD_STOP_THRESHOLD = int(os.getenv("DEGRADATION_HARD_STOP_THRESHOLD", "30"))
DEGRADATION_WARN_THRESHOLD = int(os.getenv("DEGRADATION_WARN_THRESHOLD", "60"))
DEGRADATION_WINDOW_SECONDS = int(os.getenv("DEGRADATION_WINDOW_SECONDS", "300"))  # 5 minutes


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class DegradationEvent:
    """Single degradation event."""
    event_type: str  # fallback, timeout, section_disabled, error
    section: str
    timestamp: float
    details: str = ""


@dataclass
class DegradationMetrics:
    """Aggregated degradation metrics."""
    fallback_count: int = 0
    timeout_count: int = 0
    disabled_sections: int = 0
    error_count: int = 0
    total_requests: int = 0
    successful_requests: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fallback_count": self.fallback_count,
            "timeout_count": self.timeout_count,
            "disabled_sections": self.disabled_sections,
            "error_count": self.error_count,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
        }


# =============================================================================
# DEGRADATION MONITOR
# =============================================================================

class DegradationMonitor:
    """
    Monitors system degradation and calculates health score.

    The health score is calculated based on:
    - Fallback usage (each fallback reduces score)
    - Timeouts (each timeout reduces score significantly)
    - Disabled sections (major score reduction)
    - Error rate (affects overall score)
    """

    _instance: Optional["DegradationMonitor"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DegradationMonitor":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, '_initialized', False):
            return

        self._events: List[DegradationEvent] = []
        self._events_lock = threading.Lock()
        self._current_request_id: Optional[str] = None
        self._request_metrics: Dict[str, DegradationMetrics] = {}
        self._initialized = True

    def start_request(self, request_id: str) -> None:
        """Start tracking a new request."""
        self._current_request_id = request_id
        self._request_metrics[request_id] = DegradationMetrics()

    def end_request(self, request_id: str, success: bool = True) -> Dict[str, Any]:
        """End request tracking and return metrics."""
        metrics = self._request_metrics.get(request_id, DegradationMetrics())
        metrics.total_requests = 1
        if success:
            metrics.successful_requests = 1

        result = {
            "metrics": metrics.to_dict(),
            "score": self._calculate_request_score(metrics),
            "status": self._get_status_for_score(self._calculate_request_score(metrics)).value,
        }

        # Cleanup old request metrics
        if request_id in self._request_metrics:
            del self._request_metrics[request_id]

        return result

    def record_fallback(self, section: str, reason: str = "") -> None:
        """Record a fallback event."""
        if not DEGRADATION_ENABLED:
            return

        event = DegradationEvent(
            event_type="fallback",
            section=section,
            timestamp=time.time(),
            details=reason,
        )

        with self._events_lock:
            self._events.append(event)
            self._clean_old_events()

        # Update current request metrics
        if self._current_request_id and self._current_request_id in self._request_metrics:
            self._request_metrics[self._current_request_id].fallback_count += 1

        log.warning("[G12-Degrade] Fallback recorded: section=%s reason=%s", section, reason)

    def record_timeout(self, section: str, timeout_seconds: float = 0) -> None:
        """Record a timeout event."""
        if not DEGRADATION_ENABLED:
            return

        event = DegradationEvent(
            event_type="timeout",
            section=section,
            timestamp=time.time(),
            details=f"timeout={timeout_seconds}s",
        )

        with self._events_lock:
            self._events.append(event)
            self._clean_old_events()

        if self._current_request_id and self._current_request_id in self._request_metrics:
            self._request_metrics[self._current_request_id].timeout_count += 1

        log.error("[G12-Degrade] Timeout recorded: section=%s", section)

    def record_section_disabled(self, section: str, reason: str = "") -> None:
        """Record a section being disabled."""
        if not DEGRADATION_ENABLED:
            return

        event = DegradationEvent(
            event_type="section_disabled",
            section=section,
            timestamp=time.time(),
            details=reason,
        )

        with self._events_lock:
            self._events.append(event)
            self._clean_old_events()

        if self._current_request_id and self._current_request_id in self._request_metrics:
            self._request_metrics[self._current_request_id].disabled_sections += 1

        log.warning("[G12-Degrade] Section disabled: section=%s reason=%s", section, reason)

    def record_error(self, section: str, error: str = "") -> None:
        """Record a general error event."""
        if not DEGRADATION_ENABLED:
            return

        event = DegradationEvent(
            event_type="error",
            section=section,
            timestamp=time.time(),
            details=error[:200],
        )

        with self._events_lock:
            self._events.append(event)
            self._clean_old_events()

        if self._current_request_id and self._current_request_id in self._request_metrics:
            self._request_metrics[self._current_request_id].error_count += 1

    def _clean_old_events(self) -> None:
        """Remove events outside the monitoring window."""
        cutoff = time.time() - DEGRADATION_WINDOW_SECONDS
        self._events = [e for e in self._events if e.timestamp > cutoff]

    def _calculate_request_score(self, metrics: DegradationMetrics) -> int:
        """Calculate health score for a single request (0-100)."""
        score = 100

        # Fallbacks: -5 points each (max -30)
        fallback_penalty = min(metrics.fallback_count * 5, 30)
        score -= fallback_penalty

        # Timeouts: -15 points each (max -45)
        timeout_penalty = min(metrics.timeout_count * 15, 45)
        score -= timeout_penalty

        # Disabled sections: -10 points each (max -40)
        disabled_penalty = min(metrics.disabled_sections * 10, 40)
        score -= disabled_penalty

        # Errors: -8 points each (max -24)
        error_penalty = min(metrics.error_count * 8, 24)
        score -= error_penalty

        return max(0, score)

    def get_current_score(self) -> int:
        """Calculate current overall health score based on recent events."""
        if not DEGRADATION_ENABLED:
            return 100

        with self._events_lock:
            self._clean_old_events()

            if not self._events:
                return 100

            # Aggregate metrics from recent events
            metrics = DegradationMetrics()
            for event in self._events:
                if event.event_type == "fallback":
                    metrics.fallback_count += 1
                elif event.event_type == "timeout":
                    metrics.timeout_count += 1
                elif event.event_type == "section_disabled":
                    metrics.disabled_sections += 1
                elif event.event_type == "error":
                    metrics.error_count += 1

            return self._calculate_request_score(metrics)

    def _get_status_for_score(self, score: int) -> HealthStatus:
        """Get health status for given score."""
        if score >= DEGRADATION_WARN_THRESHOLD:
            return HealthStatus.HEALTHY
        elif score >= DEGRADATION_HARD_STOP_THRESHOLD:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.CRITICAL

    def get_status(self) -> HealthStatus:
        """Get current health status."""
        return self._get_status_for_score(self.get_current_score())

    def is_critical(self) -> bool:
        """Check if system is in critical state."""
        return self.get_current_score() < DEGRADATION_HARD_STOP_THRESHOLD

    def is_degraded(self) -> bool:
        """Check if system is degraded or critical."""
        return self.get_current_score() < DEGRADATION_WARN_THRESHOLD

    def get_full_status(self) -> Dict[str, Any]:
        """Get complete degradation status."""
        with self._events_lock:
            self._clean_old_events()

            # Count events by type
            event_counts: Dict[str, int] = {}
            section_counts: Dict[str, int] = {}

            for event in self._events:
                event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
                section_counts[event.section] = section_counts.get(event.section, 0) + 1

            score = self.get_current_score()

            return {
                "enabled": DEGRADATION_ENABLED,
                "score": score,
                "status": self._get_status_for_score(score).value,
                "thresholds": {
                    "warn": DEGRADATION_WARN_THRESHOLD,
                    "critical": DEGRADATION_HARD_STOP_THRESHOLD,
                },
                "window_seconds": DEGRADATION_WINDOW_SECONDS,
                "event_counts": event_counts,
                "affected_sections": section_counts,
                "total_events": len(self._events),
                "recent_events": [
                    {
                        "type": e.event_type,
                        "section": e.section,
                        "details": e.details,
                        "age_seconds": int(time.time() - e.timestamp),
                    }
                    for e in self._events[-10:]  # Last 10 events
                ],
            }

    def reset(self) -> None:
        """Reset all degradation tracking (for testing/admin)."""
        with self._events_lock:
            self._events = []
            self._request_metrics = {}
        log.info("[G12-Degrade] Monitor reset")

    def get_degradation_status_for_report(self) -> Dict[str, Any]:
        """
        Get degradation status formatted for inclusion in report sections.

        This is what gets added to sections["DEGRADATION_STATUS"].
        """
        score = self.get_current_score()
        status = self._get_status_for_score(score)

        result: Dict[str, Any] = {
            "score": score,
            "status": status.value,
            "healthy": status == HealthStatus.HEALTHY,
        }

        if status != HealthStatus.HEALTHY:
            result["warning"] = (
                "System operating in degraded mode. Some sections may use fallback content."
                if status == HealthStatus.DEGRADED
                else "System in critical state. Report may be incomplete."
            )

        return result


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

def get_degradation_monitor() -> DegradationMonitor:
    """Get singleton degradation monitor instance."""
    return DegradationMonitor()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def record_fallback(section: str, reason: str = "") -> None:
    """Convenience function to record fallback."""
    get_degradation_monitor().record_fallback(section, reason)


def record_timeout(section: str, timeout_seconds: float = 0) -> None:
    """Convenience function to record timeout."""
    get_degradation_monitor().record_timeout(section, timeout_seconds)


def record_section_disabled(section: str, reason: str = "") -> None:
    """Convenience function to record section disabled."""
    get_degradation_monitor().record_section_disabled(section, reason)


def get_degradation_score() -> int:
    """Convenience function to get current score."""
    return get_degradation_monitor().get_current_score()


def is_system_critical() -> bool:
    """Check if system is in critical state."""
    return get_degradation_monitor().is_critical()


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G12] Degradation Monitor loaded - enabled=%s warn=%d critical=%d window=%ds",
    DEGRADATION_ENABLED,
    DEGRADATION_WARN_THRESHOLD,
    DEGRADATION_HARD_STOP_THRESHOLD,
    DEGRADATION_WINDOW_SECONDS,
)
