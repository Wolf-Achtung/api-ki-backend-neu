# -*- coding: utf-8 -*-
"""
SPRINT N3.9 PACKAGE C: Load & Stress Resilience v2 (Performance Layer v6).

Enterprise-grade performance management:
- Adaptive parallelization (CPU-core aware)
- Priority queue for report processing
- Overload protection with automatic complexity reduction
- Dynamic token reduction under load
- Enhanced retry strategies

Version: 1.0.0 (N3.9 - PLATIN++ v4.28)
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, TypeVar

log = logging.getLogger(__name__)

# Type aliases
T = TypeVar("T")
ConfigDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

class ReportPriority(Enum):
    """Report processing priority levels."""
    CRITICAL = 1
    PREMIUM = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class LoadLevel(Enum):
    """System load levels."""
    IDLE = "idle"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    OVERLOADED = "overloaded"


class ComplexityLevel(Enum):
    """Report complexity levels."""
    MINIMAL = "minimal"
    REDUCED = "reduced"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    FULL = "full"


# CPU detection
def get_cpu_count() -> int:
    """Get available CPU count."""
    try:
        return os.cpu_count() or 4
    except Exception:
        return 4


CPU_COUNT = get_cpu_count()

# Cluster size calculation
DEFAULT_CLUSTER_MULTIPLIER = 1.5
MAX_CLUSTER_SIZE = 16
MIN_CLUSTER_SIZE = 2

# Load thresholds
LOAD_THRESHOLDS: Dict[str, float] = {
    "idle": 0.0,
    "low": 0.25,
    "moderate": 0.50,
    "high": 0.75,
    "critical": 0.90,
    "overloaded": 1.0,
}

# Complexity reduction settings by load level
COMPLEXITY_BY_LOAD: Dict[str, ConfigDict] = {
    "idle": {
        "complexity": ComplexityLevel.FULL,
        "max_tokens_multiplier": 1.0,
        "parallel_tasks": CPU_COUNT,
        "retry_attempts": 7,
        "enable_advanced": True,
    },
    "low": {
        "complexity": ComplexityLevel.ENHANCED,
        "max_tokens_multiplier": 1.0,
        "parallel_tasks": max(CPU_COUNT - 1, 2),
        "retry_attempts": 6,
        "enable_advanced": True,
    },
    "moderate": {
        "complexity": ComplexityLevel.STANDARD,
        "max_tokens_multiplier": 0.9,
        "parallel_tasks": max(CPU_COUNT // 2, 2),
        "retry_attempts": 5,
        "enable_advanced": True,
    },
    "high": {
        "complexity": ComplexityLevel.REDUCED,
        "max_tokens_multiplier": 0.75,
        "parallel_tasks": max(CPU_COUNT // 3, 2),
        "retry_attempts": 4,
        "enable_advanced": False,
    },
    "critical": {
        "complexity": ComplexityLevel.MINIMAL,
        "max_tokens_multiplier": 0.5,
        "parallel_tasks": 2,
        "retry_attempts": 3,
        "enable_advanced": False,
    },
    "overloaded": {
        "complexity": ComplexityLevel.MINIMAL,
        "max_tokens_multiplier": 0.3,
        "parallel_tasks": 1,
        "retry_attempts": 2,
        "enable_advanced": False,
    },
}

# Priority queue settings
PRIORITY_WEIGHTS: Dict[int, float] = {
    1: 4.0,  # CRITICAL: 4x weight
    2: 2.0,  # PREMIUM: 2x weight
    3: 1.0,  # NORMAL: 1x weight
    4: 0.5,  # LOW: 0.5x weight
    5: 0.25,  # BACKGROUND: 0.25x weight
}

# Retry configuration (enhanced from v5)
class RetryConfigV6:
    """Enhanced retry configuration for v6."""
    MAX_RETRIES = 8
    BASE_DELAY = 0.5  # seconds
    MAX_DELAY = 90.0  # seconds
    MAX_TOTAL_TIME = 300.0  # seconds (5 minutes)
    BACKOFF_MULTIPLIER = 2.0
    JITTER_FACTOR = 0.1

    # Delays for each retry stage
    STAGE_DELAYS = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]


# Token limits by complexity
TOKEN_LIMITS: Dict[str, ConfigDict] = {
    "minimal": {
        "max_input_tokens": 2000,
        "max_output_tokens": 500,
        "max_sections": 10,
    },
    "reduced": {
        "max_input_tokens": 4000,
        "max_output_tokens": 1000,
        "max_sections": 15,
    },
    "standard": {
        "max_input_tokens": 8000,
        "max_output_tokens": 2000,
        "max_sections": 25,
    },
    "enhanced": {
        "max_input_tokens": 16000,
        "max_output_tokens": 4000,
        "max_sections": 35,
    },
    "full": {
        "max_input_tokens": 32000,
        "max_output_tokens": 8000,
        "max_sections": 50,
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class QueuedReport:
    """A report queued for processing."""
    report_id: str
    priority: ReportPriority
    briefing: ConfigDict
    queued_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "queued"
    retries: int = 0
    error_message: str = ""

    def __lt__(self, other: "QueuedReport") -> bool:
        """Compare by priority for queue ordering."""
        return self.priority.value < other.priority.value


@dataclass
class LoadMetrics:
    """Current system load metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    queue_depth: int = 0
    active_tasks: int = 0
    total_capacity: int = 0
    load_level: LoadLevel = LoadLevel.IDLE
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def compute_load_factor(self) -> float:
        """Compute overall load factor (0.0 - 1.0+)."""
        if self.total_capacity == 0:
            return 0.0

        task_factor = self.active_tasks / max(self.total_capacity, 1)
        queue_factor = min(self.queue_depth / 10.0, 1.0)  # Normalize to max 1.0
        cpu_factor = self.cpu_usage

        # Weighted combination
        return (task_factor * 0.5) + (queue_factor * 0.3) + (cpu_factor * 0.2)

    def determine_load_level(self) -> LoadLevel:
        """Determine load level from metrics."""
        factor = self.compute_load_factor()

        if factor >= LOAD_THRESHOLDS["overloaded"]:
            return LoadLevel.OVERLOADED
        elif factor >= LOAD_THRESHOLDS["critical"]:
            return LoadLevel.CRITICAL
        elif factor >= LOAD_THRESHOLDS["high"]:
            return LoadLevel.HIGH
        elif factor >= LOAD_THRESHOLDS["moderate"]:
            return LoadLevel.MODERATE
        elif factor >= LOAD_THRESHOLDS["low"]:
            return LoadLevel.LOW
        else:
            return LoadLevel.IDLE

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "cpu_usage": round(self.cpu_usage, 2),
            "memory_usage": round(self.memory_usage, 2),
            "queue_depth": self.queue_depth,
            "active_tasks": self.active_tasks,
            "total_capacity": self.total_capacity,
            "load_factor": round(self.compute_load_factor(), 2),
            "load_level": self.load_level.value,
            "timestamp": self.timestamp,
        }


@dataclass
class PerformanceReport:
    """Performance statistics report."""
    total_reports_processed: int = 0
    total_retries: int = 0
    total_fallbacks: int = 0
    average_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    min_processing_time_ms: float = float("inf")
    queue_peak_depth: int = 0
    load_peak_factor: float = 0.0
    complexity_reductions: int = 0
    token_reductions: int = 0
    period_start: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    period_end: str = ""

    # Processing times history (for percentile calculation)
    _processing_times: List[float] = field(default_factory=list)

    def record_processing(self, duration_ms: float) -> None:
        """Record a processing time."""
        self._processing_times.append(duration_ms)
        self.total_reports_processed += 1

        # Update statistics
        total = sum(self._processing_times)
        self.average_processing_time_ms = total / len(self._processing_times)
        self.max_processing_time_ms = max(self.max_processing_time_ms, duration_ms)
        self.min_processing_time_ms = min(self.min_processing_time_ms, duration_ms)

    def get_percentile(self, percentile: float) -> float:
        """Get processing time percentile."""
        if not self._processing_times:
            return 0.0

        sorted_times = sorted(self._processing_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "total_reports_processed": self.total_reports_processed,
            "total_retries": self.total_retries,
            "total_fallbacks": self.total_fallbacks,
            "average_processing_time_ms": round(self.average_processing_time_ms, 2),
            "max_processing_time_ms": round(self.max_processing_time_ms, 2),
            "min_processing_time_ms": round(self.min_processing_time_ms, 2) if self.min_processing_time_ms != float("inf") else 0,
            "p50_processing_time_ms": round(self.get_percentile(50), 2),
            "p95_processing_time_ms": round(self.get_percentile(95), 2),
            "p99_processing_time_ms": round(self.get_percentile(99), 2),
            "queue_peak_depth": self.queue_peak_depth,
            "load_peak_factor": round(self.load_peak_factor, 2),
            "complexity_reductions": self.complexity_reductions,
            "token_reductions": self.token_reductions,
            "period_start": self.period_start,
            "period_end": self.period_end or datetime.utcnow().isoformat(),
        }


# =============================================================================
# PRIORITY QUEUE MANAGER
# =============================================================================

class PriorityQueueManager:
    """
    Priority-based queue manager for report processing.

    Features:
    - Multiple priority levels
    - Fair scheduling with priority weights
    - Overload protection
    """

    def __init__(self, max_size: int = 100):
        self._queues: Dict[int, Deque[QueuedReport]] = {
            p.value: deque() for p in ReportPriority
        }
        self._lock = threading.Lock()
        self._max_size = max_size
        self._total_queued = 0

    def enqueue(self, report: QueuedReport) -> bool:
        """
        Add a report to the queue.

        Args:
            report: Report to queue

        Returns:
            True if queued, False if queue full
        """
        with self._lock:
            if self._total_queued >= self._max_size:
                log.warning("[N3.9-Perf] Queue full, rejecting report: %s", report.report_id)
                return False

            priority = report.priority.value
            self._queues[priority].append(report)
            self._total_queued += 1

            log.debug(
                "[N3.9-Perf] Queued report %s with priority %s (depth=%d)",
                report.report_id,
                report.priority.name,
                self._total_queued,
            )
            return True

    def dequeue(self) -> Optional[QueuedReport]:
        """
        Get next report from queue (weighted by priority).

        Returns:
            Next QueuedReport or None if empty
        """
        with self._lock:
            if self._total_queued == 0:
                return None

            # Check queues in priority order
            for priority in sorted(self._queues.keys()):
                q = self._queues[priority]
                if q:
                    report = q.popleft()
                    self._total_queued -= 1
                    report.started_at = datetime.utcnow().isoformat()
                    report.status = "processing"
                    return report

            return None

    def get_depth(self) -> int:
        """Get total queue depth."""
        return self._total_queued

    def get_depth_by_priority(self) -> Dict[str, int]:
        """Get queue depth by priority level."""
        with self._lock:
            return {
                ReportPriority(p).name: len(q)
                for p, q in self._queues.items()
            }

    def clear(self) -> int:
        """Clear all queues. Returns number of items cleared."""
        with self._lock:
            count = self._total_queued
            for q in self._queues.values():
                q.clear()
            self._total_queued = 0
            return count


# =============================================================================
# ADAPTIVE PARALLELIZATION
# =============================================================================

class AdaptiveParallelizer:
    """
    CPU-aware adaptive parallelization manager.

    Adjusts parallelism based on:
    - Available CPU cores
    - Current system load
    - Task priority
    """

    def __init__(self):
        self._cpu_count = CPU_COUNT
        self._base_cluster_size = min(
            max(int(self._cpu_count * DEFAULT_CLUSTER_MULTIPLIER), MIN_CLUSTER_SIZE),
            MAX_CLUSTER_SIZE,
        )
        self._current_cluster_size = self._base_cluster_size
        self._active_tasks = 0
        self._lock = threading.Lock()

    def get_cluster_size(self, load_level: LoadLevel = LoadLevel.IDLE) -> int:
        """
        Get cluster size for current load level.

        Args:
            load_level: Current system load level

        Returns:
            Recommended cluster size
        """
        config = COMPLEXITY_BY_LOAD.get(load_level.value, COMPLEXITY_BY_LOAD["moderate"])
        return int(config["parallel_tasks"])

    def acquire_slots(self, requested: int, load_level: LoadLevel = LoadLevel.IDLE) -> int:
        """
        Acquire parallel processing slots.

        Args:
            requested: Number of slots requested
            load_level: Current load level

        Returns:
            Number of slots granted
        """
        max_slots = self.get_cluster_size(load_level)

        with self._lock:
            available = max_slots - self._active_tasks
            granted = min(requested, max(available, 0))
            self._active_tasks += granted

            log.debug(
                "[N3.9-Perf] Acquired %d slots (requested=%d, active=%d, max=%d)",
                granted,
                requested,
                self._active_tasks,
                max_slots,
            )
            return int(granted)

    def release_slots(self, count: int) -> None:
        """Release processing slots."""
        with self._lock:
            self._active_tasks = max(0, self._active_tasks - count)
            log.debug("[N3.9-Perf] Released %d slots (active=%d)", count, self._active_tasks)

    def get_active_tasks(self) -> int:
        """Get number of active tasks."""
        return int(self._active_tasks)

    def get_capacity(self) -> int:
        """Get total capacity."""
        return int(self._base_cluster_size)


# =============================================================================
# OVERLOAD PROTECTION
# =============================================================================

class OverloadProtector:
    """
    Overload protection with automatic complexity/token reduction.

    Features:
    - Automatic complexity level adjustment
    - Dynamic token reduction
    - Circuit breaker pattern
    """

    def __init__(self):
        self._current_load = LoadLevel.IDLE
        self._circuit_open = False
        self._circuit_open_until: Optional[float] = None
        self._recent_failures: Deque[float] = deque(maxlen=10)
        self._lock = threading.Lock()

    def update_load(self, metrics: LoadMetrics) -> None:
        """Update current load level from metrics."""
        with self._lock:
            self._current_load = metrics.determine_load_level()
            metrics.load_level = self._current_load

            # Check circuit breaker
            if self._circuit_open:
                if self._circuit_open_until and time.time() > self._circuit_open_until:
                    self._circuit_open = False
                    self._circuit_open_until = None
                    log.info("[N3.9-Perf] Circuit breaker closed")

    def get_complexity_config(self) -> ConfigDict:
        """Get current complexity configuration based on load."""
        with self._lock:
            load_key = self._current_load.value
            return COMPLEXITY_BY_LOAD.get(load_key, COMPLEXITY_BY_LOAD["moderate"])

    def get_token_limits(self) -> ConfigDict:
        """Get current token limits based on load."""
        config = self.get_complexity_config()
        complexity = config["complexity"].value
        base_limits = TOKEN_LIMITS.get(complexity, TOKEN_LIMITS["standard"])

        multiplier = config["max_tokens_multiplier"]
        return {
            "max_input_tokens": int(base_limits["max_input_tokens"] * multiplier),
            "max_output_tokens": int(base_limits["max_output_tokens"] * multiplier),
            "max_sections": base_limits["max_sections"],
        }

    def should_reduce_complexity(self) -> bool:
        """Check if complexity should be reduced."""
        return self._current_load in (LoadLevel.HIGH, LoadLevel.CRITICAL, LoadLevel.OVERLOADED)

    def record_failure(self) -> None:
        """Record a processing failure."""
        with self._lock:
            self._recent_failures.append(time.time())

            # Check if circuit should open
            recent = sum(1 for t in self._recent_failures if time.time() - t < 60)
            if recent >= 5:  # 5 failures in last minute
                self._circuit_open = True
                self._circuit_open_until = time.time() + 30  # Open for 30 seconds
                log.warning("[N3.9-Perf] Circuit breaker opened (5 failures in 60s)")

    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        return bool(self._circuit_open)

    def get_load_level(self) -> LoadLevel:
        """Get current load level."""
        return LoadLevel(self._current_load.value)


# =============================================================================
# ENHANCED RETRY MANAGER
# =============================================================================

class RetryManagerV6:
    """
    Enhanced retry manager with adaptive strategies.

    Features:
    - Exponential backoff with jitter
    - Load-aware retry limits
    - Per-operation retry tracking
    """

    def __init__(self):
        self._retry_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    def get_retry_config(self, load_level: LoadLevel = LoadLevel.IDLE) -> ConfigDict:
        """Get retry configuration for current load level."""
        config = COMPLEXITY_BY_LOAD.get(load_level.value, COMPLEXITY_BY_LOAD["moderate"])
        return {
            "max_retries": config["retry_attempts"],
            "delays": RetryConfigV6.STAGE_DELAYS[: config["retry_attempts"]],
        }

    def should_retry(self, operation_id: str, load_level: LoadLevel = LoadLevel.IDLE) -> bool:
        """
        Check if operation should be retried.

        Args:
            operation_id: Unique operation identifier
            load_level: Current load level

        Returns:
            True if retry is allowed
        """
        config = self.get_retry_config(load_level)
        max_retries = int(config["max_retries"])

        with self._lock:
            current = self._retry_counts.get(operation_id, 0)
            return bool(current < max_retries)

    def get_delay(self, operation_id: str, load_level: LoadLevel = LoadLevel.IDLE) -> float:
        """
        Get delay before next retry.

        Args:
            operation_id: Unique operation identifier
            load_level: Current load level

        Returns:
            Delay in seconds
        """
        config = self.get_retry_config(load_level)
        delays = config["delays"]

        with self._lock:
            retry_num = self._retry_counts.get(operation_id, 0)
            if retry_num < len(delays):
                base_delay = float(delays[retry_num])
            else:
                base_delay = float(delays[-1]) if delays else RetryConfigV6.BASE_DELAY

        # Add jitter
        import random
        jitter = base_delay * RetryConfigV6.JITTER_FACTOR * random.random()
        return float(min(base_delay + jitter, RetryConfigV6.MAX_DELAY))

    def record_retry(self, operation_id: str) -> int:
        """
        Record a retry attempt.

        Args:
            operation_id: Unique operation identifier

        Returns:
            New retry count
        """
        with self._lock:
            current = self._retry_counts.get(operation_id, 0)
            self._retry_counts[operation_id] = current + 1
            return current + 1

    def reset(self, operation_id: str) -> None:
        """Reset retry count for an operation."""
        with self._lock:
            if operation_id in self._retry_counts:
                del self._retry_counts[operation_id]

    def clear_all(self) -> None:
        """Clear all retry counts."""
        with self._lock:
            self._retry_counts.clear()


# =============================================================================
# PERFORMANCE LAYER V6 ENGINE
# =============================================================================

class PerformanceLayerV6:
    """
    Main Performance Layer v6 engine.

    Coordinates all performance management components:
    - Priority queue
    - Adaptive parallelization
    - Overload protection
    - Retry management
    """

    _instance: Optional["PerformanceLayerV6"] = None

    def __new__(cls) -> "PerformanceLayerV6":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize components."""
        self._queue = PriorityQueueManager()
        self._parallelizer = AdaptiveParallelizer()
        self._protector = OverloadProtector()
        self._retry_manager = RetryManagerV6()
        self._stats = PerformanceReport()
        self._metrics_history: Deque[LoadMetrics] = deque(maxlen=100)

    def update_metrics(self, cpu_usage: float = 0.0, memory_usage: float = 0.0) -> LoadMetrics:
        """
        Update system metrics.

        Args:
            cpu_usage: Current CPU usage (0.0-1.0)
            memory_usage: Current memory usage (0.0-1.0)

        Returns:
            Updated LoadMetrics
        """
        metrics = LoadMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            queue_depth=self._queue.get_depth(),
            active_tasks=self._parallelizer.get_active_tasks(),
            total_capacity=self._parallelizer.get_capacity(),
        )

        self._protector.update_load(metrics)
        self._metrics_history.append(metrics)

        # Update stats
        self._stats.queue_peak_depth = max(self._stats.queue_peak_depth, metrics.queue_depth)
        self._stats.load_peak_factor = max(self._stats.load_peak_factor, metrics.compute_load_factor())

        return metrics

    def queue_report(
        self,
        report_id: str,
        briefing: ConfigDict,
        priority: ReportPriority = ReportPriority.NORMAL,
    ) -> bool:
        """
        Queue a report for processing.

        Args:
            report_id: Report identifier
            briefing: Report briefing data
            priority: Processing priority

        Returns:
            True if queued successfully
        """
        report = QueuedReport(
            report_id=report_id,
            priority=priority,
            briefing=briefing,
        )
        return self._queue.enqueue(report)

    def get_next_report(self) -> Optional[QueuedReport]:
        """Get next report from queue."""
        return self._queue.dequeue()

    def acquire_processing_slots(self, requested: int = 1) -> int:
        """Acquire parallel processing slots."""
        load_level = self._protector.get_load_level()
        return self._parallelizer.acquire_slots(requested, load_level)

    def release_processing_slots(self, count: int = 1) -> None:
        """Release processing slots."""
        self._parallelizer.release_slots(count)

    def get_complexity_settings(self) -> ConfigDict:
        """Get current complexity settings."""
        config = self._protector.get_complexity_config()
        token_limits = self._protector.get_token_limits()

        return {
            "complexity_level": config["complexity"].value,
            "max_tokens_multiplier": config["max_tokens_multiplier"],
            "parallel_tasks": config["parallel_tasks"],
            "retry_attempts": config["retry_attempts"],
            "enable_advanced": config["enable_advanced"],
            "token_limits": token_limits,
        }

    def should_reduce_tokens(self) -> bool:
        """Check if tokens should be reduced."""
        if self._protector.should_reduce_complexity():
            self._stats.token_reductions += 1
            return True
        return False

    def apply_token_reduction(self, tokens: int) -> int:
        """
        Apply token reduction based on load.

        Args:
            tokens: Original token count

        Returns:
            Reduced token count
        """
        config = self._protector.get_complexity_config()
        multiplier = config["max_tokens_multiplier"]
        return int(tokens * multiplier)

    def can_retry(self, operation_id: str) -> bool:
        """Check if operation can be retried."""
        load_level = self._protector.get_load_level()
        return self._retry_manager.should_retry(operation_id, load_level)

    def get_retry_delay(self, operation_id: str) -> float:
        """Get delay before retry."""
        load_level = self._protector.get_load_level()
        return self._retry_manager.get_delay(operation_id, load_level)

    def record_retry(self, operation_id: str) -> int:
        """Record a retry attempt."""
        self._stats.total_retries += 1
        return self._retry_manager.record_retry(operation_id)

    def record_fallback(self) -> None:
        """Record a fallback event."""
        self._stats.total_fallbacks += 1

    def record_failure(self) -> None:
        """Record a processing failure."""
        self._protector.record_failure()

    def record_completion(self, duration_ms: float) -> None:
        """Record a successful completion."""
        self._stats.record_processing(duration_ms)

    def is_overloaded(self) -> bool:
        """Check if system is overloaded."""
        return self._protector.is_circuit_open() or self._protector.get_load_level() == LoadLevel.OVERLOADED

    def get_stats(self) -> ConfigDict:
        """Get performance statistics."""
        return self._stats.to_dict()

    def get_current_metrics(self) -> ConfigDict:
        """Get current load metrics."""
        if self._metrics_history:
            return self._metrics_history[-1].to_dict()
        return LoadMetrics().to_dict()

    def get_queue_status(self) -> ConfigDict:
        """Get queue status."""
        return {
            "total_depth": self._queue.get_depth(),
            "by_priority": self._queue.get_depth_by_priority(),
        }


# Singleton instance
_layer = PerformanceLayerV6()


def get_performance_layer() -> PerformanceLayerV6:
    """Get the global performance layer instance."""
    return _layer


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_with_performance_layer(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    report_id: str = "",
) -> Dict[str, Any]:
    """
    Process sections with performance layer management.

    Args:
        sections: Report sections
        briefing: Report briefing
        report_id: Report identifier

    Returns:
        Dict with processed sections and performance metadata
    """
    layer = get_performance_layer()

    # Update metrics
    metrics = layer.update_metrics()

    # Check overload
    if layer.is_overloaded():
        log.warning("[N3.9-Perf] System overloaded, applying emergency reduction")

    # Get settings
    settings = layer.get_complexity_settings()

    # Build result
    result = {
        "sections": sections,
        "performance_metadata": {
            "report_id": report_id,
            "complexity_level": settings["complexity_level"],
            "token_limits": settings["token_limits"],
            "parallel_tasks": settings["parallel_tasks"],
            "load_level": metrics.load_level.value,
            "load_factor": round(metrics.compute_load_factor(), 2),
            "processed_at": datetime.utcnow().isoformat(),
        },
    }

    log.info(
        "[N3.9-Perf] Processing with complexity=%s, load=%s",
        settings["complexity_level"],
        metrics.load_level.value,
    )

    return result


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ReportPriority",
    "LoadLevel",
    "ComplexityLevel",
    # Data classes
    "QueuedReport",
    "LoadMetrics",
    "PerformanceReport",
    # Components
    "PriorityQueueManager",
    "AdaptiveParallelizer",
    "OverloadProtector",
    "RetryManagerV6",
    # Main engine
    "PerformanceLayerV6",
    "get_performance_layer",
    # Processing function
    "process_with_performance_layer",
    # Configuration
    "RetryConfigV6",
    "CPU_COUNT",
]
