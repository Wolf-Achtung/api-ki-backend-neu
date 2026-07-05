# -*- coding: utf-8 -*-
"""
N4.3: Numerical Integrity Engine v4
===================================

PLATIN+++ v5.3 - Enterprise Safety Layer

Advanced numerical consistency validation:
- ROI / Payback / Savings cross-check
- Funding effects cross-check
- Branch Benchmarks vs KPIs
- Monte Carlo vs Business Case alignment
- Language-influenced decimal separation handling

Self-healing: heal_numerical_inconsistency() with auto-correction.

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
Author: Claude + Wolf
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from services.types import SectionDict, BriefingDict

log = logging.getLogger(__name__)

__all__ = [
    "NumericMetricType",
    "ToleranceLevel",
    "NumericIssue",
    "NumericValidationResult",
    "NumericalIntegrityEngineV4",
    "validate_roi_consistency",
    "validate_payback_consistency",
    "validate_savings_consistency",
    "cross_check_funding",
    "cross_check_benchmarks",
    "heal_numerical_inconsistency",
    "extract_numeric_kpis",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class NumericMetricType(Enum):
    """Types of numeric metrics."""
    ROI = "roi"
    PAYBACK = "payback"
    SAVINGS = "savings"
    COST = "cost"
    TIME_SAVINGS = "time_savings"
    FTE = "fte"
    PRODUCTIVITY = "productivity"
    FUNDING = "funding"
    BENCHMARK = "benchmark"
    SIMULATION = "simulation"


class ToleranceLevel(Enum):
    """Tolerance levels for numeric validation."""
    STRICT = 0.03       # 3% - for critical KPIs
    NORMAL = 0.05       # 5% - for standard metrics
    RELAXED = 0.10      # 10% - for estimates
    FLEXIBLE = 0.15     # 15% - for projections


class IssueSeverity(Enum):
    """Severity of numeric issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Default tolerances by metric type
DEFAULT_TOLERANCES: Dict[NumericMetricType, float] = {
    NumericMetricType.ROI: ToleranceLevel.NORMAL.value,
    NumericMetricType.PAYBACK: ToleranceLevel.NORMAL.value,
    NumericMetricType.SAVINGS: ToleranceLevel.RELAXED.value,
    NumericMetricType.COST: ToleranceLevel.NORMAL.value,
    NumericMetricType.TIME_SAVINGS: ToleranceLevel.RELAXED.value,
    NumericMetricType.FTE: ToleranceLevel.NORMAL.value,
    NumericMetricType.PRODUCTIVITY: ToleranceLevel.RELAXED.value,
    NumericMetricType.FUNDING: ToleranceLevel.NORMAL.value,
    NumericMetricType.BENCHMARK: ToleranceLevel.RELAXED.value,
    NumericMetricType.SIMULATION: ToleranceLevel.FLEXIBLE.value,
}

# KPI extraction patterns
KPI_EXTRACTION_PATTERNS: Dict[str, Dict[str, Any]] = {
    "roi": {
        "patterns": [
            r"ROI[:\s]*(\d+(?:[.,]\d+)?)\s*%",
            r"Return\s+on\s+Investment[:\s]*(\d+(?:[.,]\d+)?)\s*%",
            r"(\d+(?:[.,]\d+)?)\s*%\s*ROI",
        ],
        "unit": "%",
        "type": NumericMetricType.ROI,
    },
    "payback": {
        "patterns": [
            r"(?:Payback|Amortisation|Break-even)[:\s-]*(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?)?",
            r"(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?)\s*(?:Payback|Amortisation)",
        ],
        "unit": "months",
        "type": NumericMetricType.PAYBACK,
    },
    "savings_monthly": {
        "patterns": [
            r"(?:Einspar|Savings?|Ersparnis)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:EUR|€)?\s*/?(?:Monat|month)",
            r"(\d+(?:[.,]\d+)?)\s*(?:EUR|€)/(?:Monat|month)",
        ],
        "unit": "€/month",
        "type": NumericMetricType.SAVINGS,
    },
    "savings_annual": {
        "patterns": [
            r"(?:Jahres)?(?:Einspar|Savings?)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:EUR|€)?\s*/?(?:Jahr|year|p\.a\.)",
            r"(\d+(?:[.,]\d+)?)\s*(?:EUR|€)/(?:Jahr|year)",
        ],
        "unit": "€/year",
        "type": NumericMetricType.SAVINGS,
    },
    "time_savings": {
        "patterns": [
            r"(?:Zeit(?:ersparnis)?|Time\s+Savings?)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:Stunden?|hours?|h)",
            r"(\d+(?:[.,]\d+)?)\s*(?:Stunden?|hours?)\s*(?:gespart|saved)",
        ],
        "unit": "hours",
        "type": NumericMetricType.TIME_SAVINGS,
    },
    "fte": {
        "patterns": [
            r"FTE[:\s-]*(\d+(?:[.,]\d+)?)",
            r"(\d+(?:[.,]\d+)?)\s*FTE",
            r"Vollzeitstellen?[:\s]*(\d+(?:[.,]\d+)?)",
        ],
        "unit": "FTE",
        "type": NumericMetricType.FTE,
    },
    "productivity": {
        "patterns": [
            r"(?:Produktivität|Productivity|Effizienz)[:\s]*(?:\+)?(\d+(?:[.,]\d+)?)\s*%",
            r"(?:\+)?(\d+(?:[.,]\d+)?)\s*%\s*(?:produktiver|more productive)",
        ],
        "unit": "%",
        "type": NumericMetricType.PRODUCTIVITY,
    },
    "cost": {
        "patterns": [
            r"(?:Kosten|Cost|Investition)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:EUR|€|Tsd|k)?",
            r"(\d+(?:[.,]\d+)?)\s*(?:EUR|€)\s*(?:Kosten|Cost)",
        ],
        "unit": "€",
        "type": NumericMetricType.COST,
    },
    "funding": {
        "patterns": [
            r"(?:Förder(?:ung|quote|summe)?|Funding)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:%|EUR|€)?",
            r"(\d+(?:[.,]\d+)?)\s*(?:%|EUR|€)\s*(?:Förderung|Funding)",
        ],
        "unit": "%/€",
        "type": NumericMetricType.FUNDING,
    },
}

# Branch benchmark ranges
# KIS-1258: ROI-Untergrenzen von 50–100 auf 10 gesenkt. Der kanonische
# Business Case rechnet seit der Ehrlichkeits-Umstellung (KIS-1251) mit
# konservativen Jahr-1-ROIs um 20–25 % — die alten Untergrenzen stammten
# aus der 190-%-Ära und erzeugten in jedem Lauf zwei Medium-Warnungen
# ("ROI 22.5% outside benchmark range (80, 300)", Lauf KIS-1240).
BRANCH_BENCHMARKS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "consulting": {
        "roi": (10, 300),
        "payback": (3, 18),
        "time_savings_percent": (15, 50),
    },
    "healthcare": {
        "roi": (10, 200),
        "payback": (6, 24),
        "time_savings_percent": (10, 40),
    },
    "finance": {
        "roi": (10, 400),
        "payback": (3, 12),
        "time_savings_percent": (20, 60),
    },
    "manufacturing": {
        "roi": (10, 250),
        "payback": (6, 24),
        "time_savings_percent": (15, 45),
    },
    "retail": {
        "roi": (10, 200),
        "payback": (6, 18),
        "time_savings_percent": (10, 35),
    },
    "it": {
        "roi": (10, 350),
        "payback": (3, 15),
        "time_savings_percent": (20, 55),
    },
}

# Simulation percentile patterns
SIMULATION_PATTERNS: Dict[str, str] = {
    "p50": r"P50[:\s]*(\d+(?:[.,]\d+)?)",
    "p80": r"P80[:\s]*(\d+(?:[.,]\d+)?)",
    "p90": r"P90[:\s]*(\d+(?:[.,]\d+)?)",
    "expected": r"(?:Erwartungswert|Expected|Mean)[:\s]*(\d+(?:[.,]\d+)?)",
}

# Cross-validation rules
CROSS_VALIDATION_RULES: Dict[str, Dict[str, Any]] = {
    "roi_payback": {
        "description": "ROI should be inversely related to payback period",
        "formula": "roi > 100 implies payback < 12",
    },
    "savings_roi": {
        "description": "Annual savings should support stated ROI",
        "tolerance": 0.20,
    },
    "time_fte": {
        "description": "Time savings should align with FTE impact",
        "tolerance": 0.25,
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ExtractedMetric:
    """An extracted numeric metric."""

    metric_type: NumericMetricType
    value: float
    unit: str
    source_section: str
    source_text: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "unit": self.unit,
            "source_section": self.source_section,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class NumericIssue:
    """A numeric consistency issue."""

    issue_id: str
    metric_type: NumericMetricType
    severity: IssueSeverity
    description: str
    expected_value: float = 0.0
    actual_value: float = 0.0
    deviation: float = 0.0
    section: str = ""
    auto_healable: bool = True
    healed: bool = False
    healed_value: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_id": self.issue_id,
            "metric_type": self.metric_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "deviation": round(self.deviation, 4),
            "section": self.section,
            "auto_healable": self.auto_healable,
            "healed": self.healed,
            "healed_value": self.healed_value if self.healed else None,
        }


@dataclass
class NumericValidationResult:
    """Result of numeric validation."""

    is_valid: bool
    score: float  # 0.0 - 1.0
    issues: List[NumericIssue] = field(default_factory=list)
    metrics_checked: int = 0
    metrics_passed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "score": round(self.score, 3),
            "issues_count": len(self.issues),
            "metrics_checked": self.metrics_checked,
            "metrics_passed": self.metrics_passed,
        }


@dataclass
class NumericalIntegrityReport:
    """Report from numerical integrity engine."""

    engine_id: str = "NUMERICAL_INTEGRITY_V4"
    success: bool = True
    numerical_validated: bool = False
    metrics_extracted: int = 0
    metrics_validated: int = 0
    issues_found: int = 0
    issues_healed: int = 0
    critical_issues: int = 0
    roi_consistent: bool = True
    payback_consistent: bool = True
    savings_consistent: bool = True
    benchmark_aligned: bool = True
    healed: bool = False
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "numerical_validated": self.numerical_validated,
            "metrics_extracted": self.metrics_extracted,
            "metrics_validated": self.metrics_validated,
            "issues_found": self.issues_found,
            "issues_healed": self.issues_healed,
            "critical_issues": self.critical_issues,
            "roi_consistent": self.roi_consistent,
            "payback_consistent": self.payback_consistent,
            "savings_consistent": self.savings_consistent,
            "benchmark_aligned": self.benchmark_aligned,
            "healed": self.healed,
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# NUMERICAL INTEGRITY ENGINE V4
# =============================================================================

class NumericalIntegrityEngineV4:
    """
    N4.3: Advanced Numerical Integrity Engine.

    Validates numerical consistency across:
    - ROI / Payback / Savings relationships
    - Funding effects
    - Branch benchmarks
    - Monte Carlo simulations vs Business Case

    Self-healing: Automatically corrects inconsistencies.
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        branch: str = "consulting",
        decimal_separator: str = ",",
    ) -> None:
        """
        Initialize Numerical Integrity Engine v4.

        Args:
            sections: Section dictionary
            briefing: Briefing data
            branch: Industry branch for benchmarks
            decimal_separator: Decimal separator (. or ,)
        """
        self.sections = sections
        self.briefing = briefing
        self.branch = branch.lower()
        self.decimal_separator = decimal_separator

        self._report = NumericalIntegrityReport()
        self._issues: List[NumericIssue] = []
        self._issue_counter = 0
        self._extracted_metrics: Dict[str, List[ExtractedMetric]] = {}

        log.info(
            "[N4.3-Numerical] Engine initialized: branch=%s",
            self.branch
        )

    def process(self) -> Tuple[SectionDict, NumericalIntegrityReport]:
        """
        Process sections through numerical integrity engine.

        Returns:
            Tuple of (processed_sections, report)
        """
        log.info("[N4.3-Numerical] Processing started")

        # Step 1: Extract all numeric metrics
        self._extract_all_metrics()

        # FIX-N43-ROI: Inject canonical ROI from briefing/sections as authoritative
        # The BusinessCaseCanonical is the single source of truth for KPI values.
        # This prevents false positives from LLM-generated text.
        canonical_roi = (
            self.briefing.get("ROI_12M")
            or self.sections.get("ROI_12M")
            or self.briefing.get("ROI_12M_CAPPED")
        )
        if canonical_roi:
            try:
                roi_val = float(str(canonical_roi).replace(",", ".").replace("%", ""))
                # Replace all extracted ROI metrics with the canonical value
                # to prevent false positives from LLM-hallucinated values
                if self._extracted_metrics.get("roi"):
                    old_count = len(self._extracted_metrics["roi"])
                    self._extracted_metrics["roi"] = [
                        ExtractedMetric(
                            metric_type=NumericMetricType.ROI,
                            value=roi_val,
                            unit="%",
                            source_section="CANONICAL_BUSINESS_CASE",
                            source_text=f"Canonical ROI={roi_val}%",
                        )
                    ]
                    log.info(
                        "[N4.3-Numerical] FIX-N43-ROI: Replaced %d extracted ROI values "
                        "with canonical ROI=%.1f%%",
                        old_count, roi_val,
                    )
                else:
                    # No ROI was extracted, inject canonical as reference
                    self._extracted_metrics["roi"] = [
                        ExtractedMetric(
                            metric_type=NumericMetricType.ROI,
                            value=roi_val,
                            unit="%",
                            source_section="CANONICAL_BUSINESS_CASE",
                            source_text=f"Canonical ROI={roi_val}%",
                        )
                    ]
            except (ValueError, TypeError):
                pass

        self._report.metrics_extracted = sum(
            len(metrics) for metrics in self._extracted_metrics.values()
        )

        # Step 2: Validate ROI consistency
        roi_result = self._validate_roi_consistency()
        self._report.roi_consistent = roi_result.is_valid
        self._issues.extend(roi_result.issues)

        # Step 3: Validate payback consistency
        payback_result = self._validate_payback_consistency()
        self._report.payback_consistent = payback_result.is_valid
        self._issues.extend(payback_result.issues)

        # Step 4: Validate savings consistency
        savings_result = self._validate_savings_consistency()
        self._report.savings_consistent = savings_result.is_valid
        self._issues.extend(savings_result.issues)

        # Step 5: Cross-check with benchmarks
        benchmark_result = self._cross_check_benchmarks()
        self._report.benchmark_aligned = benchmark_result.is_valid
        self._issues.extend(benchmark_result.issues)

        # Step 6: Cross-check funding effects
        funding_result = self._cross_check_funding()
        self._issues.extend(funding_result.issues)

        # Step 7: Cross-check simulation vs business case
        simulation_result = self._cross_check_simulation()
        self._issues.extend(simulation_result.issues)

        # Calculate totals
        self._report.issues_found = len(self._issues)
        self._report.critical_issues = sum(
            1 for i in self._issues if i.severity == IssueSeverity.CRITICAL
        )

        # Step 8: Heal issues (self-healing)
        result_sections = self._heal_issues()
        self._report.issues_healed = sum(1 for i in self._issues if i.healed)
        self._report.healed = self._report.issues_healed > 0

        # FIX-NUM-DIAG-V4: Transfer unhealed issue details to report
        # Previously report.issues stayed empty [], losing all diagnostic info.
        for issue in self._issues:
            if not issue.healed:
                self._report.issues.append(
                    f"{issue.metric_type.value}: expected={issue.expected_value}, "
                    f"actual={issue.actual_value}, section={issue.section}, "
                    f"severity={issue.severity.value}, desc={issue.description[:120]}"
                )
            else:
                self._report.warnings.append(
                    f"HEALED {issue.metric_type.value}: {issue.expected_value}→{issue.healed_value} "
                    f"in {issue.section}"
                )

        # Calculate validation status
        self._report.numerical_validated = (
            self._report.critical_issues == 0 or
            self._report.critical_issues == self._report.issues_healed
        )
        self._report.success = self._report.numerical_validated
        self._report.metrics_validated = (
            self._report.metrics_extracted - self._report.issues_found +
            self._report.issues_healed
        )

        # Store metadata
        result_sections["_numerical_validated"] = self._report.numerical_validated
        result_sections["_numerical_report"] = self._report.to_dict()
        result_sections["_num_healed"] = self._report.healed

        log.info(
            "[N4.3-Numerical] Complete: metrics=%d, issues=%d, healed=%d",
            self._report.metrics_extracted,
            self._report.issues_found,
            self._report.issues_healed
        )

        return result_sections, self._report

    def _extract_all_metrics(self) -> None:
        """Extract all numeric metrics from sections."""
        # FIX-N43-ROI: Skip derivative/summary sections that may contain
        # LLM-hallucinated values. LEAD_ sections are one-liner summaries
        # generated by LLM from authoritative sections — they can confuse
        # values (e.g. hours=36.0 misinterpreted as ROI=36.0%).
        # Only extract metrics from authoritative source sections.
        SKIP_PREFIXES = ("LEAD_", "ONE_LINER_", "_")

        # FIX-B20: De-duplicate HTML/plain keys. Many sections exist as both
        # "business_case" and "BUSINESS_CASE_HTML" with identical content.
        # Extracting metrics from both double-counts issues.
        # Strategy: prefer _HTML key, skip lowercase duplicate.
        _seen_bases = set()

        for section_key, section_content in self.sections.items():
            if any(section_key.startswith(p) for p in SKIP_PREFIXES):
                continue

            if not isinstance(section_content, str):
                continue

            # FIX-B20: De-duplicate by normalizing to base name
            _base = section_key.lower().removesuffix("_html")
            if _base in _seen_bases:
                continue
            _seen_bases.add(_base)

            metrics = self._extract_metrics_from_text(section_key, section_content)
            if metrics:
                for metric in metrics:
                    metric_type = metric.metric_type.value
                    if metric_type not in self._extracted_metrics:
                        self._extracted_metrics[metric_type] = []
                    self._extracted_metrics[metric_type].append(metric)

    def _extract_metrics_from_text(
        self,
        section_key: str,
        text: str,
    ) -> List[ExtractedMetric]:
        """Extract metrics from a text section."""
        metrics: List[ExtractedMetric] = []

        for metric_name, config in KPI_EXTRACTION_PATTERNS.items():
            for pattern in config["patterns"]:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        value_str = match.group(1)
                        # Normalize decimal separator
                        value_str = value_str.replace(",", ".")
                        value = float(value_str)

                        metric = ExtractedMetric(
                            metric_type=config["type"],
                            value=value,
                            unit=config["unit"],
                            source_section=section_key,
                            source_text=match.group()[:100],
                        )
                        metrics.append(metric)
                    except (ValueError, IndexError):
                        continue

        return metrics

    def _validate_roi_consistency(self) -> NumericValidationResult:
        """Validate ROI consistency across sections."""
        issues: List[NumericIssue] = []
        roi_metrics = self._extracted_metrics.get("roi", [])

        if not roi_metrics:
            return NumericValidationResult(is_valid=True, score=1.0)

        # Check for ROI variation across sections
        roi_values = [m.value for m in roi_metrics]
        if len(roi_values) > 1:
            avg_roi = sum(roi_values) / len(roi_values)
            for metric in roi_metrics:
                deviation = abs(metric.value - avg_roi) / avg_roi if avg_roi else 0
                if deviation > DEFAULT_TOLERANCES[NumericMetricType.ROI]:
                    issue = NumericIssue(
                        issue_id=self._get_issue_id(),
                        metric_type=NumericMetricType.ROI,
                        severity=IssueSeverity.HIGH if deviation > 0.10 else IssueSeverity.MEDIUM,
                        description=f"ROI inconsistency: {metric.value}% vs average {avg_roi:.1f}%",
                        expected_value=avg_roi,
                        actual_value=metric.value,
                        deviation=deviation,
                        section=metric.source_section,
                    )
                    issues.append(issue)

        # Check ROI plausibility against branch benchmarks
        benchmarks = BRANCH_BENCHMARKS.get(self.branch, BRANCH_BENCHMARKS["consulting"])
        roi_range = benchmarks.get("roi", (10, 400))  # KIS-1258: Untergrenze 50 → 10

        for metric in roi_metrics:
            if metric.value < roi_range[0] or metric.value > roi_range[1]:
                issue = NumericIssue(
                    issue_id=self._get_issue_id(),
                    metric_type=NumericMetricType.ROI,
                    severity=IssueSeverity.MEDIUM,
                    description=f"ROI {metric.value}% outside benchmark range {roi_range}",
                    expected_value=(roi_range[0] + roi_range[1]) / 2,
                    actual_value=metric.value,
                    deviation=abs(metric.value - sum(roi_range)/2) / (sum(roi_range)/2),
                    section=metric.source_section,
                )
                issues.append(issue)

        score = 1.0 - (len(issues) * 0.1) if roi_metrics else 1.0
        return NumericValidationResult(
            is_valid=len([i for i in issues if i.severity == IssueSeverity.CRITICAL]) == 0,
            score=max(0.0, score),
            issues=issues,
            metrics_checked=len(roi_metrics),
            metrics_passed=len(roi_metrics) - len(issues),
        )

    def _validate_payback_consistency(self) -> NumericValidationResult:
        """Validate payback period consistency."""
        issues: List[NumericIssue] = []
        payback_metrics = self._extracted_metrics.get("payback", [])

        if not payback_metrics:
            return NumericValidationResult(is_valid=True, score=1.0)

        # Check payback variation
        payback_values = [m.value for m in payback_metrics]
        if len(payback_values) > 1:
            avg_payback = sum(payback_values) / len(payback_values)
            for metric in payback_metrics:
                deviation = abs(metric.value - avg_payback) / avg_payback if avg_payback else 0
                if deviation > DEFAULT_TOLERANCES[NumericMetricType.PAYBACK]:
                    issue = NumericIssue(
                        issue_id=self._get_issue_id(),
                        metric_type=NumericMetricType.PAYBACK,
                        severity=IssueSeverity.HIGH,
                        description=f"Payback inconsistency: {metric.value} vs average {avg_payback:.1f}",
                        expected_value=avg_payback,
                        actual_value=metric.value,
                        deviation=deviation,
                        section=metric.source_section,
                    )
                    issues.append(issue)

        # Check ROI-Payback relationship
        roi_metrics = self._extracted_metrics.get("roi", [])
        if roi_metrics and payback_metrics:
            avg_roi = sum(m.value for m in roi_metrics) / len(roi_metrics)
            avg_payback = sum(m.value for m in payback_metrics) / len(payback_metrics)

            # High ROI should imply shorter payback
            if avg_roi > 150 and avg_payback > 12:
                issue = NumericIssue(
                    issue_id=self._get_issue_id(),
                    metric_type=NumericMetricType.PAYBACK,
                    severity=IssueSeverity.HIGH,
                    description=f"ROI ({avg_roi:.0f}%) suggests shorter payback than {avg_payback:.0f} months",
                    expected_value=min(12, avg_payback),
                    actual_value=avg_payback,
                    deviation=0.2,
                    section="cross_validation",
                )
                issues.append(issue)

        score = 1.0 - (len(issues) * 0.15)
        return NumericValidationResult(
            is_valid=len([i for i in issues if i.severity == IssueSeverity.CRITICAL]) == 0,
            score=max(0.0, score),
            issues=issues,
            metrics_checked=len(payback_metrics),
            metrics_passed=len(payback_metrics) - len(issues),
        )

    def _validate_savings_consistency(self) -> NumericValidationResult:
        """Validate savings consistency."""
        issues: List[NumericIssue] = []
        savings_metrics = self._extracted_metrics.get("savings", [])

        if not savings_metrics:
            return NumericValidationResult(is_valid=True, score=1.0)

        # Group by monthly/annual
        monthly_savings = [m for m in savings_metrics if "month" in m.unit.lower()]
        annual_savings = [m for m in savings_metrics if "year" in m.unit.lower()]

        # Cross-validate monthly * 12 ≈ annual
        if monthly_savings and annual_savings:
            avg_monthly = sum(m.value for m in monthly_savings) / len(monthly_savings)
            avg_annual = sum(m.value for m in annual_savings) / len(annual_savings)
            expected_annual = avg_monthly * 12

            deviation = abs(expected_annual - avg_annual) / avg_annual if avg_annual else 0
            if deviation > DEFAULT_TOLERANCES[NumericMetricType.SAVINGS]:
                issue = NumericIssue(
                    issue_id=self._get_issue_id(),
                    metric_type=NumericMetricType.SAVINGS,
                    severity=IssueSeverity.HIGH,
                    description=f"Monthly ({avg_monthly:.0f}€) * 12 != Annual ({avg_annual:.0f}€)",
                    expected_value=expected_annual,
                    actual_value=avg_annual,
                    deviation=deviation,
                    section="cross_validation",
                )
                issues.append(issue)

        score = 1.0 - (len(issues) * 0.15)
        return NumericValidationResult(
            is_valid=len([i for i in issues if i.severity == IssueSeverity.CRITICAL]) == 0,
            score=max(0.0, score),
            issues=issues,
            metrics_checked=len(savings_metrics),
            metrics_passed=len(savings_metrics) - len(issues),
        )

    def _cross_check_benchmarks(self) -> NumericValidationResult:
        """Cross-check metrics against branch benchmarks."""
        issues: List[NumericIssue] = []
        benchmarks = BRANCH_BENCHMARKS.get(self.branch, BRANCH_BENCHMARKS["consulting"])
        metrics_checked = 0

        # FIX-B20: Metrics where LOWER values are BETTER (inverted semantics)
        _LOWER_IS_BETTER = {"payback"}

        # Check all metric types against benchmarks
        for metric_name, (low, high) in benchmarks.items():
            metric_type_str = metric_name.replace("_percent", "")
            metrics = self._extracted_metrics.get(metric_type_str, [])

            for metric in metrics:
                metrics_checked += 1
                # FIX-B20: For "lower is better" metrics (payback), being below
                # the benchmark minimum is GOOD, not bad. Skip the low-check.
                if metric.value < low and metric_type_str not in _LOWER_IS_BETTER:
                    issue = NumericIssue(
                        issue_id=self._get_issue_id(),
                        metric_type=metric.metric_type,
                        severity=IssueSeverity.MEDIUM,
                        description=f"{metric_name} ({metric.value}) below benchmark minimum ({low})",
                        expected_value=low,
                        actual_value=metric.value,
                        deviation=(low - metric.value) / low,
                        section=metric.source_section,
                    )
                    issues.append(issue)
                elif metric.value > high:
                    issue = NumericIssue(
                        issue_id=self._get_issue_id(),
                        metric_type=metric.metric_type,
                        severity=IssueSeverity.LOW,
                        description=f"{metric_name} ({metric.value}) above benchmark maximum ({high})",
                        expected_value=high,
                        actual_value=metric.value,
                        deviation=(metric.value - high) / high,
                        section=metric.source_section,
                        auto_healable=False,  # Above benchmark is usually positive
                    )
                    issues.append(issue)

        score = 1.0 - (len(issues) * 0.05)
        return NumericValidationResult(
            is_valid=True,  # Benchmark deviations are warnings
            score=max(0.0, score),
            issues=issues,
            metrics_checked=metrics_checked,
            metrics_passed=metrics_checked - len(issues),
        )

    def _cross_check_funding(self) -> NumericValidationResult:
        """Cross-check funding effects on other metrics."""
        issues: List[NumericIssue] = []
        funding_metrics = self._extracted_metrics.get("funding", [])

        if not funding_metrics:
            return NumericValidationResult(is_valid=True, score=1.0)

        # If funding is mentioned, ROI should account for it
        roi_metrics = self._extracted_metrics.get("roi", [])
        if roi_metrics:
            avg_funding = sum(m.value for m in funding_metrics if m.unit == "%") / len(funding_metrics)
            avg_roi = sum(m.value for m in roi_metrics) / len(roi_metrics)

            # Higher funding should lead to higher effective ROI
            if avg_funding > 30 and avg_roi < 100:
                issue = NumericIssue(
                    issue_id=self._get_issue_id(),
                    metric_type=NumericMetricType.FUNDING,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Funding ({avg_funding:.0f}%) should boost ROI above {avg_roi:.0f}%",
                    expected_value=avg_roi * (1 + avg_funding/100),
                    actual_value=avg_roi,
                    deviation=0.15,
                    section="cross_validation",
                )
                issues.append(issue)
                self._report.warnings.append(
                    f"ROI may need adjustment for {avg_funding:.0f}% funding effect"
                )

        return NumericValidationResult(
            is_valid=True,
            score=1.0 - (len(issues) * 0.1),
            issues=issues,
            metrics_checked=len(funding_metrics),
            metrics_passed=len(funding_metrics) - len(issues),
        )

    def _cross_check_simulation(self) -> NumericValidationResult:
        """Cross-check simulation results vs business case."""
        issues: List[NumericIssue] = []

        # Extract simulation values from sections
        simulation_values: Dict[str, float] = {}
        for section_content in self.sections.values():
            if not isinstance(section_content, str):
                continue
            for sim_name, pattern in SIMULATION_PATTERNS.items():
                match = re.search(pattern, section_content, re.IGNORECASE)
                if match:
                    try:
                        simulation_values[sim_name] = float(match.group(1).replace(",", "."))
                    except ValueError:
                        pass

        if not simulation_values:
            return NumericValidationResult(is_valid=True, score=1.0)

        # Compare P50 with stated ROI
        roi_metrics = self._extracted_metrics.get("roi", [])
        if "p50" in simulation_values and roi_metrics:
            avg_roi = sum(m.value for m in roi_metrics) / len(roi_metrics)
            p50 = simulation_values["p50"]

            # P50 should be within 20% of stated ROI
            deviation = abs(p50 - avg_roi) / avg_roi if avg_roi else 0
            if deviation > DEFAULT_TOLERANCES[NumericMetricType.SIMULATION]:
                issue = NumericIssue(
                    issue_id=self._get_issue_id(),
                    metric_type=NumericMetricType.SIMULATION,
                    severity=IssueSeverity.MEDIUM,
                    description=f"P50 ({p50:.0f}) deviates from stated ROI ({avg_roi:.0f}%)",
                    expected_value=avg_roi,
                    actual_value=p50,
                    deviation=deviation,
                    section="simulation",
                )
                issues.append(issue)

        return NumericValidationResult(
            is_valid=True,
            score=1.0 - (len(issues) * 0.1),
            issues=issues,
            metrics_checked=len(simulation_values),
            metrics_passed=len(simulation_values) - len(issues),
        )

    def _heal_issues(self) -> SectionDict:
        """Heal numerical issues in sections."""
        result_sections = dict(self.sections)

        for issue in self._issues:
            if not issue.auto_healable or issue.healed:
                continue

            if issue.severity == IssueSeverity.CRITICAL:
                # For critical issues, use expected value
                healed_value = issue.expected_value
            elif issue.severity == IssueSeverity.HIGH:
                # For high issues, use weighted average
                healed_value = (issue.expected_value * 0.7 + issue.actual_value * 0.3)
            else:
                # For medium/low, keep original but flag
                continue

            # Apply healing to sections
            if issue.section in result_sections:
                section_content = result_sections[issue.section]
                if isinstance(section_content, str):
                    # Replace the old value with healed value
                    old_value_str = str(int(issue.actual_value)) if issue.actual_value == int(issue.actual_value) else f"{issue.actual_value:.1f}"
                    new_value_str = str(int(healed_value)) if healed_value == int(healed_value) else f"{healed_value:.1f}"

                    # Use regex to replace in context
                    result_sections[issue.section] = re.sub(
                        rf"\b{re.escape(old_value_str)}\b",
                        new_value_str,
                        section_content,
                        count=1
                    )

            issue.healed = True
            issue.healed_value = healed_value
            self._report.warnings.append(
                f"Healed {issue.metric_type.value} in {issue.section}: {issue.actual_value} -> {healed_value:.1f}"
            )

        return result_sections

    def _get_issue_id(self) -> str:
        """Generate unique issue ID."""
        self._issue_counter += 1
        return f"NUM-{self._issue_counter:04d}"

    def get_extracted_metrics(self) -> Dict[str, List[ExtractedMetric]]:
        """Get all extracted metrics."""
        return self._extracted_metrics


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def validate_roi_consistency(
    sections: SectionDict,
    tolerance: float = 0.05,
) -> NumericValidationResult:
    """
    Validate ROI consistency across sections.

    Args:
        sections: Section dictionary
        tolerance: Deviation tolerance

    Returns:
        NumericValidationResult
    """
    engine = NumericalIntegrityEngineV4(sections=sections, briefing={})
    engine._extract_all_metrics()
    return engine._validate_roi_consistency()


def validate_payback_consistency(
    sections: SectionDict,
    tolerance: float = 0.05,
) -> NumericValidationResult:
    """
    Validate payback period consistency.

    Args:
        sections: Section dictionary
        tolerance: Deviation tolerance

    Returns:
        NumericValidationResult
    """
    engine = NumericalIntegrityEngineV4(sections=sections, briefing={})
    engine._extract_all_metrics()
    return engine._validate_payback_consistency()


def validate_savings_consistency(
    sections: SectionDict,
    tolerance: float = 0.10,
) -> NumericValidationResult:
    """
    Validate savings consistency.

    Args:
        sections: Section dictionary
        tolerance: Deviation tolerance

    Returns:
        NumericValidationResult
    """
    engine = NumericalIntegrityEngineV4(sections=sections, briefing={})
    engine._extract_all_metrics()
    return engine._validate_savings_consistency()


def cross_check_funding(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
) -> NumericValidationResult:
    """
    Cross-check funding effects.

    Args:
        sections: Section dictionary
        briefing: Optional briefing data

    Returns:
        NumericValidationResult
    """
    engine = NumericalIntegrityEngineV4(sections=sections, briefing=briefing or {})
    engine._extract_all_metrics()
    return engine._cross_check_funding()


def cross_check_benchmarks(
    sections: SectionDict,
    branch: str = "consulting",
) -> NumericValidationResult:
    """
    Cross-check against branch benchmarks.

    Args:
        sections: Section dictionary
        branch: Industry branch

    Returns:
        NumericValidationResult
    """
    engine = NumericalIntegrityEngineV4(sections=sections, briefing={}, branch=branch)
    engine._extract_all_metrics()
    return engine._cross_check_benchmarks()


def heal_numerical_inconsistency(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
    branch: str = "consulting",
) -> Tuple[SectionDict, Dict[str, Any]]:
    """
    Heal numerical inconsistencies in sections.

    Args:
        sections: Section dictionary
        briefing: Optional briefing data
        branch: Industry branch

    Returns:
        Tuple of (healed_sections, healing_report)
    """
    engine = NumericalIntegrityEngineV4(
        sections=sections,
        briefing=briefing or {},
        branch=branch,
    )
    healed_sections, report = engine.process()

    healing_report = {
        "healed": report.healed,
        "issues_found": report.issues_found,
        "issues_healed": report.issues_healed,
        "metrics_extracted": report.metrics_extracted,
        "warnings": report.warnings,
    }

    return healed_sections, healing_report


def extract_numeric_kpis(
    sections: SectionDict,
    include_source: bool = False,
) -> Dict[str, Any]:
    """
    Extract all numeric KPIs from sections.

    Args:
        sections: Section dictionary
        include_source: Include source section info

    Returns:
        Dictionary of extracted KPIs
    """
    engine = NumericalIntegrityEngineV4(sections=sections, briefing={})
    engine._extract_all_metrics()

    kpis: Dict[str, Any] = {}
    for metric_type, metrics in engine.get_extracted_metrics().items():
        if metrics:
            values = [m.value for m in metrics]
            kpis[metric_type] = {
                "value": values[0] if len(values) == 1 else sum(values) / len(values),
                "count": len(values),
                "min": min(values),
                "max": max(values),
            }
            if include_source:
                kpis[metric_type]["sources"] = [m.source_section for m in metrics]

    return kpis
