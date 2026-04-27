# -*- coding: utf-8 -*-
"""
SPRINT N3.8 PACKAGE F: Performance Layer v5.

No variability + reduced costs + faster analysis:
- Retry: 7 stages (max 200s)
- Prioritized LLM pipeline (critical sections first)
- Adaptive complexity (large companies → comprehensive, solo → compact)
- Full parallelization with CPU-awareness
- Cache-aware PromptBuilder (no redundant calculations)

Version: 1.1.0 (N3.8 - PLATIN++ v4.24 + Phase 5C)

Phase 5C (2026-01-06): Final Polish & Optimizations
- Enhanced docstrings with all 13 Branchen documented
- Improved edge-case handling for company size
- Type hints completed
- Constants for size values

Supported Company Sizes (aligned with questionnaire):
    - "1" → "solo" (Solo-Selbstständig)
    - "2–10" → "small" (Kleines Team)
    - "11–100" → "medium" (KMU)

Note: Only solo/small/medium are valid - questionnaire does not support
larger company sizes (enterprise/large removed).
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union
import threading

log = logging.getLogger(__name__)

# Type alias
T = TypeVar('T')
SectionDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

# Retry configuration (7 stages, max 200s total)
class RetryConfig:
    """Retry configuration with exponential backoff."""
    MAX_RETRIES = 7
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 60.0  # seconds
    MAX_TOTAL_TIME = 200.0  # seconds
    BACKOFF_MULTIPLIER = 2.0

    # Delays for each retry stage
    STAGE_DELAYS = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0]  # Total: ~123s


# Company size thresholds
# NOTE: Only solo/small/medium are used - these map to questionnaire values:
# "1" → solo, "2-10" → small, "11-100" → medium
class CompanySize(Enum):
    """Company size classification (aligned with questionnaire)."""
    SOLO = "solo"  # 1 person (Solo-Selbstständig/Freiberuflich)
    SMALL = "small"  # 2-10 employees (Kleines Team)
    MEDIUM = "medium"  # 11-100 employees (KMU)
    # LARGE and ENTERPRISE removed - not in questionnaire


# Complexity settings by company size
# Keys must match: "solo", "small", "medium" (from questionnaire)
COMPLEXITY_SETTINGS: Dict[str, Dict[str, Any]] = {
    "solo": {
        "max_sections": 15,
        "max_words_per_section": 200,
        "detail_level": 1,
        "include_advanced_analytics": False,
        "parallel_tasks": 2,
        "llm_temperature": 0.3,
    },
    "small": {  # Maps to "2-10" from questionnaire
        "max_sections": 20,
        "max_words_per_section": 300,
        "detail_level": 2,
        "include_advanced_analytics": False,
        "parallel_tasks": 3,
        "llm_temperature": 0.25,
    },
    "medium": {  # Maps to "11-100" from questionnaire
        "max_sections": 25,
        "max_words_per_section": 400,
        "detail_level": 3,
        "include_advanced_analytics": True,
        "parallel_tasks": 4,
        "llm_temperature": 0.2,
    },
    # "large" and "enterprise" removed - not valid questionnaire values
}

# Section priorities (higher = more important = process first)
SECTION_PRIORITIES: Dict[str, int] = {
    "exec_summary": 100,
    "executive_summary": 100,
    "ki_stack_summary": 95,
    "recommendations": 90,
    "business_case": 85,
    "risks": 80,
    "risk_report": 80,
    "roadmap_90d": 75,
    "roadmap_12m": 70,
    "tools_empfehlungen": 65,
    "gamechanger": 60,
    "foerderpotenzial": 55,
    "strategie_governance": 50,
    "wettbewerb_benchmark": 45,
    "unternehmensprofil_markt": 40,
    "branch_deep_dive": 35,
}

# Default CPU count for parallelization
DEFAULT_CPU_COUNT = 4


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RetryResult:
    """Result of a retry operation."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    total_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "error": self.error,
            "attempts": self.attempts,
            "total_time": self.total_time,
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for tracking."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_retries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_time: float = 0.0
    parallel_tasks_completed: int = 0
    sections_processed: int = 0
    sections_by_priority: Dict[str, int] = field(default_factory=dict)

    def add_request(self, success: bool, retries: int, time_taken: float) -> None:
        """Record a request."""
        self.total_requests += 1
        self.total_time += time_taken
        self.total_retries += retries

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def record_cache(self, hit: bool) -> None:
        """Record cache hit/miss."""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100

    @property
    def avg_time_per_request(self) -> float:
        """Calculate average time per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_time / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "total_retries": self.total_retries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            "total_time": self.total_time,
            "avg_time_per_request": self.avg_time_per_request,
            "parallel_tasks_completed": self.parallel_tasks_completed,
            "sections_processed": self.sections_processed,
            "sections_by_priority": self.sections_by_priority,
        }


# Global metrics instance
_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """Get global performance metrics."""
    return _metrics


def reset_metrics() -> None:
    """Reset global performance metrics."""
    global _metrics
    _metrics = PerformanceMetrics()


# =============================================================================
# RETRY MECHANISM (7 STAGES)
# =============================================================================

def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = RetryConfig.MAX_RETRIES,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_total_time: float = RetryConfig.MAX_TOTAL_TIME,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> RetryResult:
    """
    N3.8: Execute function with 7-stage exponential backoff retry.

    Args:
        func: Function to execute
        max_retries: Maximum number of retries (default: 7)
        base_delay: Base delay in seconds
        max_total_time: Maximum total time for all retries
        on_retry: Optional callback on each retry

    Returns:
        RetryResult with success status and result/error
    """
    start_time = time.time()
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        elapsed = time.time() - start_time

        # Check if we've exceeded max total time
        if elapsed >= max_total_time:
            log.warning(
                "[N3.8-Retry] Max total time exceeded: %.1fs >= %.1fs",
                elapsed, max_total_time
            )
            break

        try:
            result = func()
            return RetryResult(
                success=True,
                result=result,
                attempts=attempt + 1,
                total_time=time.time() - start_time,
            )
        except Exception as e:
            last_error = e
            log.warning(
                "[N3.8-Retry] Attempt %d/%d failed: %s",
                attempt + 1, max_retries + 1, str(e)
            )

            if on_retry:
                on_retry(attempt, e)

            if attempt < max_retries:
                # Calculate delay for this stage
                delay = min(
                    RetryConfig.STAGE_DELAYS[min(attempt, len(RetryConfig.STAGE_DELAYS) - 1)],
                    RetryConfig.MAX_DELAY
                )

                # Don't exceed max total time
                remaining_time = max_total_time - (time.time() - start_time)
                delay = min(delay, remaining_time)

                if delay > 0:
                    log.info("[N3.8-Retry] Waiting %.1fs before retry...", delay)
                    time.sleep(delay)

    return RetryResult(
        success=False,
        error=str(last_error) if last_error else "Max retries exceeded",
        attempts=max_retries + 1,
        total_time=time.time() - start_time,
    )


async def retry_with_backoff_async(
    func: Callable[[], T],
    max_retries: int = RetryConfig.MAX_RETRIES,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_total_time: float = RetryConfig.MAX_TOTAL_TIME,
) -> RetryResult:
    """
    N3.8: Async version of retry with backoff.
    """
    start_time = time.time()
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        elapsed = time.time() - start_time

        if elapsed >= max_total_time:
            break

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func()
            else:
                result = func()
            return RetryResult(
                success=True,
                result=result,
                attempts=attempt + 1,
                total_time=time.time() - start_time,
            )
        except Exception as e:
            last_error = e

            if attempt < max_retries:
                delay = min(
                    RetryConfig.STAGE_DELAYS[min(attempt, len(RetryConfig.STAGE_DELAYS) - 1)],
                    max_total_time - (time.time() - start_time)
                )

                if delay > 0:
                    await asyncio.sleep(delay)

    return RetryResult(
        success=False,
        error=str(last_error) if last_error else "Max retries exceeded",
        attempts=max_retries + 1,
        total_time=time.time() - start_time,
    )


# =============================================================================
# ADAPTIVE COMPLEXITY
# =============================================================================

def determine_company_size(employees: int) -> CompanySize:
    """
    Determine company size category.

    Maps employee counts to questionnaire-aligned categories:
    - 1 → solo
    - 2-10 → small
    - 11+ → medium

    Note: Questionnaire only supports up to 100 employees (11-100 = medium).
    Any larger company is treated as medium for complexity settings.

    Args:
        employees: Number of employees

    Returns:
        CompanySize enum value (solo, small, or medium)
    """
    if employees <= 1:
        return CompanySize.SOLO
    elif employees <= 10:
        return CompanySize.SMALL
    else:
        return CompanySize.MEDIUM  # Covers 11-100 and any larger


def get_complexity_settings(
    briefing: Dict[str, Any]
) -> Dict[str, Any]:
    """
    N3.8: Get complexity settings based on company profile.

    Args:
        briefing: Briefing dictionary with company info

    Returns:
        Complexity settings dictionary
    """
    # Extract employee count from briefing
    employees = briefing.get("employees", 50)
    if isinstance(employees, str):
        try:
            employees = int(employees.replace(",", "").replace(".", ""))
        except ValueError:
            employees = 50

    company_size = determine_company_size(employees)

    log.info(
        "[N3.8-Performance] Company size: %s (%d employees)",
        company_size.value, employees
    )

    settings = COMPLEXITY_SETTINGS.get(company_size.value, COMPLEXITY_SETTINGS["medium"])

    # Adjust based on other factors
    branch = briefing.get("branch", "").lower()

    # Finance/Consulting branches get more detail
    if any(b in branch for b in ["finanz", "finance", "banking", "beratung", "consulting"]):
        settings = dict(settings)
        settings["detail_level"] = min(settings["detail_level"] + 1, 5)
        settings["max_words_per_section"] += 100

    return settings


# =============================================================================
# PRIORITIZED LLM PIPELINE
# =============================================================================

def get_section_priority(section: str) -> int:
    """Get priority for a section (higher = more important)."""
    return SECTION_PRIORITIES.get(section.lower(), 20)


def prioritize_sections(sections: List[str]) -> List[str]:
    """
    N3.8: Sort sections by priority (highest first).

    Args:
        sections: List of section names

    Returns:
        Sorted list with highest priority first
    """
    return sorted(sections, key=get_section_priority, reverse=True)


def create_prioritized_pipeline(
    sections: List[str],
    processor: Callable[[str], Any],
) -> List[Tuple[str, int, Callable]]:
    """
    N3.8: Create prioritized processing pipeline.

    Args:
        sections: List of section names
        processor: Function to process each section

    Returns:
        List of (section_name, priority, processor_func) tuples
    """
    pipeline = []

    for section in prioritize_sections(sections):
        priority = get_section_priority(section)
        pipeline.append((section, priority, lambda s=section: processor(s)))

    return pipeline


# =============================================================================
# PARALLELIZATION WITH CPU-AWARENESS
# =============================================================================

def get_optimal_parallelism(
    task_count: int,
    complexity_settings: Optional[Dict[str, Any]] = None,
) -> int:
    """
    N3.8: Determine optimal parallelism based on CPU and task count.

    Args:
        task_count: Number of tasks to process
        complexity_settings: Optional complexity settings

    Returns:
        Optimal number of parallel workers
    """
    # Get CPU count
    cpu_count = os.cpu_count() or DEFAULT_CPU_COUNT

    # Get max parallel tasks from settings
    max_parallel = DEFAULT_CPU_COUNT
    if complexity_settings:
        max_parallel = complexity_settings.get("parallel_tasks", DEFAULT_CPU_COUNT)

    # Don't exceed CPU count
    max_parallel = min(max_parallel, cpu_count)

    # Don't create more workers than tasks
    optimal = min(max_parallel, task_count)

    log.info(
        "[N3.8-Performance] Parallelism: tasks=%d cpus=%d max=%d optimal=%d",
        task_count, cpu_count, max_parallel, optimal
    )

    return max(1, optimal)


async def process_parallel_async(
    tasks: List[Tuple[str, Callable[[], Any]]],
    max_workers: int,
    metrics: Optional[PerformanceMetrics] = None,
) -> Dict[str, Any]:
    """
    N3.8: Process tasks in parallel with async.

    Args:
        tasks: List of (name, callable) tuples
        max_workers: Maximum parallel workers
        metrics: Optional metrics tracker

    Returns:
        Dictionary of {name: result}
    """
    if metrics is None:
        metrics = get_metrics()

    results: Dict[str, Any] = {}
    semaphore = asyncio.Semaphore(max_workers)

    async def process_task(name: str, func: Callable) -> Tuple[str, Any]:
        async with semaphore:
            start = time.time()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func()
                else:
                    result = func()
                metrics.add_request(True, 0, time.time() - start)
                return name, result
            except Exception as e:
                log.error("[N3.8-Performance] Task %s failed: %s", name, str(e))
                metrics.add_request(False, 0, time.time() - start)
                return name, None

    # Create tasks
    async_tasks = [
        process_task(name, func)
        for name, func in tasks
    ]

    # Execute in parallel
    completed = await asyncio.gather(*async_tasks)
    metrics.parallel_tasks_completed += len(completed)

    for name, result in completed:
        results[name] = result

    return results


def process_parallel_sync(
    tasks: List[Tuple[str, Callable[[], Any]]],
    max_workers: int,
    metrics: Optional[PerformanceMetrics] = None,
) -> Dict[str, Any]:
    """
    N3.8: Process tasks in parallel with threads.

    Args:
        tasks: List of (name, callable) tuples
        max_workers: Maximum parallel workers
        metrics: Optional metrics tracker

    Returns:
        Dictionary of {name: result}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if metrics is None:
        metrics = get_metrics()

    results: Dict[str, Any] = {}

    def process_task(name: str, func: Callable) -> Tuple[str, Any]:
        start = time.time()
        try:
            result = func()
            metrics.add_request(True, 0, time.time() - start)
            return name, result
        except Exception as e:
            log.error("[N3.8-Performance] Task %s failed: %s", name, str(e))
            metrics.add_request(False, 0, time.time() - start)
            return name, None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_task, name, func): name
            for name, func in tasks
        }

        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result
            metrics.parallel_tasks_completed += 1

    return results


# =============================================================================
# CACHE-AWARE PROMPT BUILDER
# =============================================================================

class CacheAwarePromptBuilder:
    """
    N3.8: Cache-aware prompt builder to avoid redundant calculations.
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value."""
        with self._lock:
            if key in self._cache:
                get_metrics().record_cache(True)
                return self._cache[key]
            get_metrics().record_cache(False)
            return None

    def set_cached(self, key: str, value: Any) -> None:
        """Set cached value."""
        with self._lock:
            self._cache[key] = value

    def clear_cache(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    @property
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def build_branch_profile(
        self,
        briefing: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build branch profile (cached).
        """
        key = self._get_cache_key("branch_profile", briefing.get("branch", ""))

        cached = self.get_cached(key)
        if cached is not None:
            return dict(cached)

        # Build profile
        profile: Dict[str, Any] = {
            "branch": briefing.get("branch", ""),
            "sub_branch": briefing.get("sub_branch", ""),
            "market_segment": briefing.get("market_segment", ""),
            "competitive_position": briefing.get("competitive_position", ""),
        }

        self.set_cached(key, profile)
        return profile

    def build_kpi_context(
        self,
        briefing: Dict[str, Any],
        sections: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build KPI context (cached).
        """
        key = self._get_cache_key(
            "kpi_context",
            briefing.get("branch", ""),
            briefing.get("employees", 0),
        )

        cached = self.get_cached(key)
        if cached is not None:
            return dict(cached)

        # Build KPI context
        context: Dict[str, Any] = {
            "company_size": determine_company_size(
                briefing.get("employees", 50)
            ).value,
            "branch": briefing.get("branch", ""),
            "typical_roi_range": (15, 40),  # Placeholder
            "typical_payback_months": (12, 24),  # Placeholder
        }

        self.set_cached(key, context)
        return context

    def build_prompt(
        self,
        template: str,
        briefing: Dict[str, Any],
        section: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build prompt from template (cached based on inputs).
        """
        key = self._get_cache_key(
            "prompt",
            template[:50],
            briefing.get("branch", ""),
            section,
        )

        cached = self.get_cached(key)
        if cached is not None:
            return str(cached)

        # Get branch profile and KPI context
        branch_profile = self.build_branch_profile(briefing)
        kpi_context = self.build_kpi_context(briefing, {})

        # Build prompt
        prompt = template.format(
            branch=branch_profile.get("branch", ""),
            company_size=kpi_context.get("company_size", "medium"),
            section=section,
            **(context or {}),
        )

        self.set_cached(key, prompt)
        return prompt


# Global prompt builder instance
_prompt_builder = CacheAwarePromptBuilder()


def get_prompt_builder() -> CacheAwarePromptBuilder:
    """Get global prompt builder."""
    return _prompt_builder


# =============================================================================
# MAIN PROCESSING PIPELINE
# =============================================================================

def process_with_performance_layer(
    sections: SectionDict,
    briefing: Dict[str, Any],
    processor: Callable[[str, SectionDict, Dict[str, Any]], Any],
) -> Tuple[SectionDict, PerformanceMetrics]:
    """
    N3.8: Process sections with full performance layer.

    Features:
    - Adaptive complexity
    - Prioritized pipeline
    - Parallel execution
    - 7-stage retry
    - Cache-aware building

    Args:
        sections: Section dictionary
        briefing: Briefing dictionary
        processor: Function to process each section

    Returns:
        Tuple of (processed_sections, metrics)
    """
    log.info("[N3.8-Performance] Starting performance layer processing...")

    metrics = PerformanceMetrics()
    start_time = time.time()

    # Get complexity settings
    complexity = get_complexity_settings(briefing)

    # Get sections to process
    section_names = [
        key for key in sections.keys()
        if not key.startswith("_") and isinstance(sections[key], str)
    ]

    # Prioritize sections
    prioritized = prioritize_sections(section_names)

    log.info(
        "[N3.8-Performance] Processing %d sections with complexity level %d",
        len(prioritized),
        complexity.get("detail_level", 3)
    )

    # Create tasks
    tasks: List[Tuple[str, Callable[[], Any]]] = []

    for section in prioritized:
        priority = get_section_priority(section)
        metrics.sections_by_priority[section] = priority

        def create_processor(s: str) -> Callable:
            def process_with_retry() -> Any:
                result = retry_with_backoff(
                    lambda: processor(s, sections, briefing)
                )
                metrics.add_request(
                    result.success,
                    result.attempts - 1,
                    result.total_time
                )
                return result.result if result.success else None
            return process_with_retry

        tasks.append((section, create_processor(section)))

    # Determine parallelism
    max_workers = get_optimal_parallelism(len(tasks), complexity)

    # Process in parallel
    results = process_parallel_sync(tasks, max_workers, metrics)

    # Merge results
    processed = dict(sections)
    for section, result in results.items():
        if result is not None:
            processed[section] = result
            metrics.sections_processed += 1

    metrics.total_time = time.time() - start_time

    # Add performance metadata
    processed["_performance_metrics"] = metrics.to_dict()
    processed["_complexity_settings"] = complexity

    log.info(
        "[N3.8-Performance] Complete: sections=%d time=%.1fs success=%.1f%% cache=%.1f%%",
        metrics.sections_processed,
        metrics.total_time,
        metrics.success_rate,
        metrics.cache_hit_rate
    )

    return processed, metrics


def get_performance_summary(metrics: PerformanceMetrics) -> str:
    """
    Generate human-readable performance summary.

    Args:
        metrics: PerformanceMetrics

    Returns:
        Summary string
    """
    return (
        f"Performance Summary:\n"
        f"  Requests: {metrics.total_requests} ({metrics.success_rate:.1f}% success)\n"
        f"  Retries: {metrics.total_retries}\n"
        f"  Cache: {metrics.cache_hits}/{metrics.cache_hits + metrics.cache_misses} hits ({metrics.cache_hit_rate:.1f}%)\n"
        f"  Time: {metrics.total_time:.1f}s (avg {metrics.avg_time_per_request:.2f}s/req)\n"
        f"  Sections: {metrics.sections_processed} processed"
    )
