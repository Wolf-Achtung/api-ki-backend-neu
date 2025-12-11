# -*- coding: utf-8 -*-
"""
SPRINT N3.4 TASK 6: Stress-Test Engine.

Provides systematic stress testing of report generation:
- Temperature variations (0.3, 0.7, 1.0)
- Truncation levels (short, medium, full)
- 9 combinations total
- Consistency validation across runs
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum

log = logging.getLogger(__name__)


# =============================================================================
# STRESS TEST CONFIGURATION
# =============================================================================

class TruncationLevel(Enum):
    """Truncation levels for stress testing."""
    SHORT = "short"  # 30% of normal
    MEDIUM = "medium"  # 60% of normal
    FULL = "full"  # 100% of normal


class TemperatureLevel(Enum):
    """Temperature levels for stress testing."""
    LOW = 0.3  # Deterministic
    MEDIUM = 0.7  # Balanced
    HIGH = 1.0  # Creative


# Standard temperature values for testing
STRESS_TEMPERATURES: List[float] = [0.3, 0.7, 1.0]

# Truncation multipliers for content length
TRUNCATION_MULTIPLIERS: Dict[TruncationLevel, float] = {
    TruncationLevel.SHORT: 0.3,
    TruncationLevel.MEDIUM: 0.6,
    TruncationLevel.FULL: 1.0,
}

# Section word count targets at full truncation
SECTION_WORD_TARGETS: Dict[str, int] = {
    "executive_summary": 200,
    "recommendations": 800,
    "risks": 600,
    "roadmap_90d": 300,
    "roadmap_12m": 500,
    "gamechanger": 600,
    "tools_empfehlungen": 400,
    "wettbewerb_benchmark": 400,
    "unternehmensprofil_markt": 400,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class StressTestConfig:
    """Configuration for a stress test run."""
    temperature: float
    truncation: TruncationLevel
    run_id: str = ""

    def get_word_target(self, section: str) -> int:
        """Get target word count for a section at this truncation level."""
        base = SECTION_WORD_TARGETS.get(section, 200)
        multiplier = TRUNCATION_MULTIPLIERS[self.truncation]
        return int(base * multiplier)

    def __str__(self) -> str:
        return f"T{self.temperature}_{self.truncation.value}"


@dataclass
class StressTestResult:
    """Result of a stress test run."""
    config: StressTestConfig
    success: bool = True
    sections_generated: Dict[str, int] = field(default_factory=dict)  # section: word_count
    sections_failed: List[str] = field(default_factory=list)
    consistency_issues: List[str] = field(default_factory=list)
    error_message: str = ""
    total_words: int = 0
    generation_time_ms: int = 0

    @property
    def passed(self) -> bool:
        """Check if test passed (no failures, no critical issues)."""
        return self.success and len(self.sections_failed) == 0


@dataclass
class StressTestReport:
    """Aggregated report from multiple stress test runs."""
    results: List[StressTestResult] = field(default_factory=list)
    matrix_results: Dict[str, Dict[str, bool]] = field(default_factory=dict)  # temp -> truncation -> passed
    overall_pass_rate: float = 0.0
    worst_combination: Optional[str] = None
    best_combination: Optional[str] = None

    def add_result(self, result: StressTestResult) -> None:
        """Add a test result to the report."""
        self.results.append(result)

        temp_key = str(result.config.temperature)
        trunc_key = result.config.truncation.value

        if temp_key not in self.matrix_results:
            self.matrix_results[temp_key] = {}

        self.matrix_results[temp_key][trunc_key] = result.passed

        # Recalculate stats
        passed = sum(1 for r in self.results if r.passed)
        self.overall_pass_rate = passed / len(self.results) if self.results else 0.0

    def get_combination_key(self, temp: float, trunc: TruncationLevel) -> str:
        """Get string key for a temperature/truncation combination."""
        return f"T{temp}_{trunc.value}"


# =============================================================================
# STRESS TEST ENGINE
# =============================================================================

def get_stress_test_matrix() -> List[StressTestConfig]:
    """
    Generate the 9-combination stress test matrix.

    3 temperatures × 3 truncation levels = 9 combinations

    Returns:
        List of StressTestConfig objects
    """
    matrix: List[StressTestConfig] = []
    run_id = 0

    for temp in STRESS_TEMPERATURES:
        for trunc in TruncationLevel:
            run_id += 1
            config = StressTestConfig(
                temperature=temp,
                truncation=trunc,
                run_id=f"stress_{run_id:02d}"
            )
            matrix.append(config)

    return matrix


def simulate_stress_run(
    briefing: Dict[str, Any],
    temperature: float,
    truncation_level: TruncationLevel,
    generator_fn: Optional[Callable] = None,
) -> StressTestResult:
    """
    N3.4 TASK 6: Simulate a stress test run with specific parameters.

    Args:
        briefing: The company briefing data
        temperature: LLM temperature (0.3, 0.7, or 1.0)
        truncation_level: Content truncation level
        generator_fn: Optional custom generator function for testing

    Returns:
        StressTestResult with test outcome
    """
    config = StressTestConfig(temperature=temperature, truncation=truncation_level)
    result = StressTestResult(config=config)

    try:
        # Validate inputs
        if not briefing:
            result.success = False
            result.error_message = "Empty briefing provided"
            return result

        if temperature not in STRESS_TEMPERATURES:
            log.warning(
                "[STRESS] Non-standard temperature %.1f (expected one of %s)",
                temperature, STRESS_TEMPERATURES
            )

        # Calculate expected word targets per section
        targets: Dict[str, int] = {}
        for section in SECTION_WORD_TARGETS:
            targets[section] = config.get_word_target(section)

        # If custom generator provided, use it
        if generator_fn:
            generated = generator_fn(briefing, temperature, truncation_level)
            if isinstance(generated, dict):
                for section, content in generated.items():
                    word_count = len(content.split()) if content else 0
                    result.sections_generated[section] = word_count
                    result.total_words += word_count

                    # Check if section met target
                    target = targets.get(section, 100)
                    if word_count < target * 0.5:  # Below 50% of target = failed
                        result.sections_failed.append(section)
        else:
            # Simulated generation for testing
            for section, target in targets.items():
                # Simulate generation with some variance
                simulated_count = int(target * (0.8 + 0.4 * (1 - temperature / 2)))
                result.sections_generated[section] = simulated_count
                result.total_words += simulated_count

        # Run consistency checks
        consistency_issues = _check_stress_consistency(result, briefing)
        result.consistency_issues = consistency_issues

        if consistency_issues:
            log.warning(
                "[STRESS] Run %s had %d consistency issues",
                str(config), len(consistency_issues)
            )

        result.success = True

    except Exception as e:
        result.success = False
        result.error_message = str(e)
        log.error("[STRESS] Run failed: %s", e)

    return result


def _check_stress_consistency(
    result: StressTestResult,
    briefing: Dict[str, Any]
) -> List[str]:
    """
    Check consistency of stress test result.

    Args:
        result: The test result to validate
        briefing: Original briefing data

    Returns:
        List of consistency issue descriptions
    """
    issues: List[str] = []

    # Check 1: Total words should be reasonable
    expected_total = sum(
        result.config.get_word_target(s) for s in SECTION_WORD_TARGETS
    )
    if result.total_words < expected_total * 0.3:
        issues.append(
            f"Total words {result.total_words} below 30% of expected {expected_total}"
        )

    # Check 2: No section should be completely empty
    for section, count in result.sections_generated.items():
        if count == 0:
            issues.append(f"Section {section} has 0 words")

    # Check 3: High temperature shouldn't cause extreme variance
    if result.config.temperature >= 1.0:
        # At high temp, variance is expected but shouldn't be extreme
        counts = list(result.sections_generated.values())
        if counts:
            avg = sum(counts) / len(counts)
            max_dev = max(abs(c - avg) for c in counts)
            if max_dev > avg * 2:
                issues.append(
                    f"Extreme variance at high temperature: max deviation {max_dev:.0f}"
                )

    return issues


def run_stress_test_matrix(
    briefing: Dict[str, Any],
    generator_fn: Optional[Callable] = None,
) -> StressTestReport:
    """
    N3.4 TASK 6: Run full 9-combination stress test matrix.

    Args:
        briefing: The company briefing data
        generator_fn: Optional custom generator function

    Returns:
        StressTestReport with aggregated results
    """
    report = StressTestReport()
    matrix = get_stress_test_matrix()

    log.info("[STRESS] Starting stress test matrix with %d combinations", len(matrix))

    for config in matrix:
        result = simulate_stress_run(
            briefing=briefing,
            temperature=config.temperature,
            truncation_level=config.truncation,
            generator_fn=generator_fn,
        )
        report.add_result(result)

        log.info(
            "[STRESS] Run %s: %s (words=%d, issues=%d)",
            str(config),
            "PASS" if result.passed else "FAIL",
            result.total_words,
            len(result.consistency_issues)
        )

    # Find best/worst combinations
    if report.results:
        sorted_results = sorted(
            report.results,
            key=lambda r: (r.passed, r.total_words),
            reverse=True
        )
        report.best_combination = str(sorted_results[0].config)
        report.worst_combination = str(sorted_results[-1].config)

    log.info(
        "[STRESS] Matrix complete: %.0f%% pass rate, best=%s, worst=%s",
        report.overall_pass_rate * 100,
        report.best_combination,
        report.worst_combination
    )

    return report


def validate_stress_result(
    result: StressTestResult,
    min_pass_rate: float = 0.9,
) -> Tuple[bool, List[str]]:
    """
    Validate a stress test result against quality criteria.

    Args:
        result: The stress test result
        min_pass_rate: Minimum acceptable pass rate (default 90%)

    Returns:
        Tuple of (passed, list of issues)
    """
    issues: List[str] = []

    if not result.success:
        issues.append(f"Test failed: {result.error_message}")

    if result.sections_failed:
        issues.append(f"Sections failed: {', '.join(result.sections_failed)}")

    if result.consistency_issues:
        issues.extend(result.consistency_issues)

    # Check minimum word count
    config = result.config
    min_expected = sum(config.get_word_target(s) for s in SECTION_WORD_TARGETS) * 0.5
    if result.total_words < min_expected:
        issues.append(
            f"Total words {result.total_words} below minimum {min_expected:.0f}"
        )

    passed = len(issues) == 0
    return passed, issues


def get_stress_test_summary(report: StressTestReport) -> Dict[str, Any]:
    """
    Get a summary dict of stress test results.

    Args:
        report: The stress test report

    Returns:
        Summary dictionary for logging/reporting
    """
    return {
        "total_runs": len(report.results),
        "passed_runs": sum(1 for r in report.results if r.passed),
        "pass_rate": f"{report.overall_pass_rate * 100:.0f}%",
        "best_combination": report.best_combination,
        "worst_combination": report.worst_combination,
        "matrix": {
            temp: {
                trunc: "PASS" if passed else "FAIL"
                for trunc, passed in truncs.items()
            }
            for temp, truncs in report.matrix_results.items()
        },
        "total_issues": sum(
            len(r.consistency_issues) for r in report.results
        ),
    }
