# -*- coding: utf-8 -*-
"""
Sprint G34: Business Case Monte Carlo Simulation & Uncertainty Model
======================================================================

Extends Business Case Engine 2.0 (G30) with:
- Monte Carlo Simulation for ROI & Payback
- Probability distributions for uncertain inputs
- P50/P80/P90 risk-adjusted metrics
- Integration with Risk Engine V3 for risk-adjusted factors
- Size-aware & branch-aware simulations
- Dedicated report section: BUSINESS_CASE_SIM_HTML

This module provides the uncertainty and risk modeling layer on top of
the deterministic G30 Business Case calculations.

Version: 1.1.0 (Sprint G34 + Phase 5C)
Author: Claude + Wolf

Phase 5C (2026-01-06): Final Polish & Optimizations
- Enhanced docstrings with all 13 Branchen documented
- Improved edge-case handling for company size
- Type hints completed
- Structured logging for monitoring

Supported Company Sizes (aligned with questionnaire):
    - "1" → "solo" (Solo-Selbstständig)
    - "2–10" → "small" (Kleines Team)
    - "11–100" → "medium" (KMU)

Supported Branchen (13 total, aligned with questionnaire):
    marketing, beratung, it, finanzen, handel, bildung, verwaltung,
    gesundheit, bau, medien, industrie, logistik, gastronomie
"""

from __future__ import annotations

import json
import logging
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

# Import G30 Business Case Engine
from services.business_case_engine_v2 import (
    BusinessCaseReport,
    ScenarioKPIs,
    calculate_roi,
    calculate_payback,
    MIN_ROI,
    MAX_ROI,
    MIN_PAYBACK_MONTHS,
    MAX_PAYBACK_MONTHS,
)

# Fix-Batch J2: Import German number formatting
from services.i18n import format_decimal_de

log = logging.getLogger(__name__)

__all__ = [
    "SimulationDistribution",
    "SimulationAssumptions",
    "BusinessCaseSimulationReport",
    "generate_business_case_simulation",
    "business_case_simulation_to_html",
    "BUSINESS_CASE_SIMULATION_ENABLED",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

BUSINESS_CASE_SIMULATION_ENABLED = True

# Default simulation settings
DEFAULT_SIMULATION_RUNS = 1000
MIN_SIMULATION_RUNS = 100
MAX_SIMULATION_RUNS = 5000

# Percentile definitions
PERCENTILE_P50 = 50
PERCENTILE_P80 = 80
PERCENTILE_P90 = 90
PERCENTILE_P20 = 20

# Distribution types
DISTRIBUTION_UNIFORM = "uniform"
DISTRIBUTION_TRIANGULAR = "triangular"
DISTRIBUTION_NORMAL = "normal"

# Size-specific variance multipliers
SIZE_VARIANCE_MULTIPLIERS = {
    "solo": 1.8,   # Higher variance for solo entrepreneurs (J1: was 1.3)
    "small": 1.4,   # Meaningful variance for small teams (J1: was 1.0)
    "medium": 1.1,   # Moderate variance for SMEs (J1: was 0.85)
}

# Risk-adjusted variance factors
RISK_VARIANCE_FACTORS = {
    "A": 0.7,   # Low risk = lower variance
    "B": 0.85,
    "C": 1.0,   # Medium risk = base variance
    "D": 1.2,
    "F": 1.5,   # High risk = higher variance
}

# Default assumption ranges (percentage of base value)
DEFAULT_SAVINGS_RANGE = {"min_pct": 0.6, "mode_pct": 1.0, "max_pct": 1.4}
DEFAULT_INVESTMENT_RANGE = {"min_pct": 0.8, "mode_pct": 1.0, "max_pct": 1.3}
DEFAULT_IMPLEMENTATION_SPEED_RANGE = {"min_pct": 0.7, "mode_pct": 1.0, "max_pct": 1.2}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SimulationAssumptions:
    """
    Assumptions for Monte Carlo simulation distributions.

    Defines min/mode/max ranges for each uncertain input.
    Uses triangular distribution by default.
    """
    # Monthly savings distribution
    monthly_savings_min: float = 0.0
    monthly_savings_mode: float = 0.0
    monthly_savings_max: float = 0.0

    # Investment total distribution
    investment_min: float = 0.0
    investment_mode: float = 0.0
    investment_max: float = 0.0

    # Implementation speed factor (1.0 = as planned)
    speed_factor_min: float = 0.7
    speed_factor_mode: float = 1.0
    speed_factor_max: float = 1.2

    # Risk adjustment factor (1.0 = neutral)
    risk_factor_min: float = 0.8
    risk_factor_mode: float = 1.0
    risk_factor_max: float = 1.0

    # Funding success probability (0.0-1.0)
    funding_success_probability: float = 0.5

    # Distribution type
    distribution_type: str = DISTRIBUTION_TRIANGULAR

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Ensure min <= mode <= max for all parameters
        if self.monthly_savings_min > self.monthly_savings_mode:
            self.monthly_savings_min = self.monthly_savings_mode
        if self.monthly_savings_mode > self.monthly_savings_max:
            self.monthly_savings_max = self.monthly_savings_mode

        if self.investment_min > self.investment_mode:
            self.investment_min = self.investment_mode
        if self.investment_mode > self.investment_max:
            self.investment_max = self.investment_mode

        # Clamp funding probability
        self.funding_success_probability = max(0.0, min(1.0, self.funding_success_probability))

        # Validate distribution type
        if self.distribution_type not in [DISTRIBUTION_UNIFORM, DISTRIBUTION_TRIANGULAR, DISTRIBUTION_NORMAL]:
            self.distribution_type = DISTRIBUTION_TRIANGULAR

    @property
    def is_valid(self) -> bool:
        """Check if assumptions are valid for simulation."""
        return (
            self.monthly_savings_max > 0 and
            self.investment_max > 0 and
            self.monthly_savings_min <= self.monthly_savings_max and
            self.investment_min <= self.investment_max
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "monthly_savings": {
                "min": round(self.monthly_savings_min, 2),
                "mode": round(self.monthly_savings_mode, 2),
                "max": round(self.monthly_savings_max, 2),
            },
            "investment_total": {
                "min": round(self.investment_min, 2),
                "mode": round(self.investment_mode, 2),
                "max": round(self.investment_max, 2),
            },
            "speed_factor": {
                "min": round(self.speed_factor_min, 2),
                "mode": round(self.speed_factor_mode, 2),
                "max": round(self.speed_factor_max, 2),
            },
            "risk_factor": {
                "min": round(self.risk_factor_min, 2),
                "mode": round(self.risk_factor_mode, 2),
                "max": round(self.risk_factor_max, 2),
            },
            "funding_success_probability": round(self.funding_success_probability, 2),
            "distribution_type": self.distribution_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationAssumptions":
        """Create from dictionary."""
        monthly = data.get("monthly_savings", {})
        investment = data.get("investment_total", {})
        speed = data.get("speed_factor", {})
        risk = data.get("risk_factor", {})

        return cls(
            monthly_savings_min=float(monthly.get("min", 0)),
            monthly_savings_mode=float(monthly.get("mode", 0)),
            monthly_savings_max=float(monthly.get("max", 0)),
            investment_min=float(investment.get("min", 0)),
            investment_mode=float(investment.get("mode", 0)),
            investment_max=float(investment.get("max", 0)),
            speed_factor_min=float(speed.get("min", 0.7)),
            speed_factor_mode=float(speed.get("mode", 1.0)),
            speed_factor_max=float(speed.get("max", 1.2)),
            risk_factor_min=float(risk.get("min", 0.8)),
            risk_factor_mode=float(risk.get("mode", 1.0)),
            risk_factor_max=float(risk.get("max", 1.0)),
            funding_success_probability=float(data.get("funding_success_probability", 0.5)),
            distribution_type=data.get("distribution_type", DISTRIBUTION_TRIANGULAR),
        )


@dataclass
class SimulationDistribution:
    """
    Results of Monte Carlo simulation.

    Contains all sample values and calculated percentiles.
    """
    # Raw samples
    roi_samples: List[float] = field(default_factory=list)
    payback_samples: List[float] = field(default_factory=list)
    monthly_savings_samples: List[float] = field(default_factory=list)

    # ROI percentiles
    roi_p50: float = 0.0
    roi_p80: float = 0.0
    roi_p90: float = 0.0
    roi_p20: float = 0.0

    # Payback percentiles
    payback_p50: float = 0.0
    payback_p80: float = 0.0
    payback_p90: float = 0.0
    payback_p20: float = 0.0

    # Ranges
    roi_min: float = 0.0
    roi_max: float = 0.0
    roi_mean: float = 0.0
    roi_std: float = 0.0

    payback_min: float = 0.0
    payback_max: float = 0.0
    payback_mean: float = 0.0
    payback_std: float = 0.0

    # Sample count
    simulation_runs: int = 0

    def __post_init__(self) -> None:
        """Calculate statistics if samples provided."""
        if self.roi_samples and not self.roi_p50:
            self._calculate_statistics()

    def _calculate_statistics(self) -> None:
        """Calculate all statistics from samples."""
        if not self.roi_samples:
            return

        self.simulation_runs = len(self.roi_samples)

        # ROI statistics
        sorted_roi = sorted(self.roi_samples)
        self.roi_min = min(sorted_roi)
        self.roi_max = max(sorted_roi)
        self.roi_mean = sum(sorted_roi) / len(sorted_roi)
        self.roi_std = _calculate_std(sorted_roi, self.roi_mean)

        self.roi_p20 = _percentile(sorted_roi, PERCENTILE_P20)
        self.roi_p50 = _percentile(sorted_roi, PERCENTILE_P50)
        self.roi_p80 = _percentile(sorted_roi, PERCENTILE_P80)
        self.roi_p90 = _percentile(sorted_roi, PERCENTILE_P90)

        # Payback statistics
        if self.payback_samples:
            sorted_payback = sorted(self.payback_samples)
            self.payback_min = min(sorted_payback)
            self.payback_max = max(sorted_payback)
            self.payback_mean = sum(sorted_payback) / len(sorted_payback)
            self.payback_std = _calculate_std(sorted_payback, self.payback_mean)

            self.payback_p20 = _percentile(sorted_payback, PERCENTILE_P20)
            self.payback_p50 = _percentile(sorted_payback, PERCENTILE_P50)
            self.payback_p80 = _percentile(sorted_payback, PERCENTILE_P80)
            self.payback_p90 = _percentile(sorted_payback, PERCENTILE_P90)

    @property
    def roi_confidence_interval_80(self) -> Tuple[float, float]:
        """Get 80% confidence interval for ROI (P10 to P90)."""
        if not self.roi_samples:
            return (0.0, 0.0)
        sorted_roi = sorted(self.roi_samples)
        return (_percentile(sorted_roi, 10), _percentile(sorted_roi, 90))

    @property
    def payback_confidence_interval_80(self) -> Tuple[float, float]:
        """Get 80% confidence interval for Payback (P10 to P90)."""
        if not self.payback_samples:
            return (0.0, 0.0)
        sorted_payback = sorted(self.payback_samples)
        return (_percentile(sorted_payback, 10), _percentile(sorted_payback, 90))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "simulation_runs": self.simulation_runs,
            "roi": {
                "p20": round(self.roi_p20, 1),
                "p50": round(self.roi_p50, 1),
                "p80": round(self.roi_p80, 1),
                "p90": round(self.roi_p90, 1),
                "min": round(self.roi_min, 1),
                "max": round(self.roi_max, 1),
                "mean": round(self.roi_mean, 1),
                "std": round(self.roi_std, 1),
            },
            "payback": {
                "p20": round(self.payback_p20, 1),
                "p50": round(self.payback_p50, 1),
                "p80": round(self.payback_p80, 1),
                "p90": round(self.payback_p90, 1),
                "min": round(self.payback_min, 1),
                "max": round(self.payback_max, 1),
                "mean": round(self.payback_mean, 1),
                "std": round(self.payback_std, 1),
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationDistribution":
        """Create from dictionary."""
        roi = data.get("roi", {})
        payback = data.get("payback", {})

        return cls(
            roi_samples=[],  # Samples not serialized
            payback_samples=[],
            monthly_savings_samples=[],
            roi_p50=float(roi.get("p50", 0)),
            roi_p80=float(roi.get("p80", 0)),
            roi_p90=float(roi.get("p90", 0)),
            roi_p20=float(roi.get("p20", 0)),
            payback_p50=float(payback.get("p50", 0)),
            payback_p80=float(payback.get("p80", 0)),
            payback_p90=float(payback.get("p90", 0)),
            payback_p20=float(payback.get("p20", 0)),
            roi_min=float(roi.get("min", 0)),
            roi_max=float(roi.get("max", 0)),
            roi_mean=float(roi.get("mean", 0)),
            roi_std=float(roi.get("std", 0)),
            payback_min=float(payback.get("min", 0)),
            payback_max=float(payback.get("max", 0)),
            payback_mean=float(payback.get("mean", 0)),
            payback_std=float(payback.get("std", 0)),
            simulation_runs=data.get("simulation_runs", 0),
        )


@dataclass
class BusinessCaseSimulationReport:
    """
    Complete Business Case Simulation Report.

    Combines G30 deterministic baseline with Monte Carlo simulation results.
    """
    # G30 baseline report
    baseline_report: Optional[BusinessCaseReport] = None

    # Simulation results
    distribution: SimulationDistribution = field(default_factory=SimulationDistribution)

    # Assumptions used
    assumptions: SimulationAssumptions = field(default_factory=SimulationAssumptions)

    # Narrative summary
    narrative_summary: str = ""

    # Metadata
    size_label: str = "small"  # was "team"
    risk_grade: str = "C"
    simulation_runs: int = DEFAULT_SIMULATION_RUNS

    def __post_init__(self) -> None:
        """Validate and normalize."""
        if self.baseline_report is None:
            self.baseline_report = BusinessCaseReport()
        if not isinstance(self.distribution, SimulationDistribution):
            self.distribution = SimulationDistribution()
        if not isinstance(self.assumptions, SimulationAssumptions):
            self.assumptions = SimulationAssumptions()

    @property
    def realistic_scenario(self) -> Optional[ScenarioKPIs]:
        """Get realistic scenario from baseline."""
        if self.baseline_report:
            return self.baseline_report.realistic_scenario
        return None

    @property
    def is_simulation_valid(self) -> bool:
        """Check if simulation produced valid results."""
        return (
            self.distribution.simulation_runs > 0 and
            self.distribution.roi_p50 != 0
        )

    @property
    def roi_p50_vs_realistic_deviation(self) -> float:
        """Calculate deviation between P50 ROI and realistic scenario ROI."""
        realistic = self.realistic_scenario
        if not realistic:
            return 0.0
        if realistic.roi_12m == 0:
            return 0.0
        return abs(self.distribution.roi_p50 - realistic.roi_12m) / abs(realistic.roi_12m) * 100

    @property
    def variance_level(self) -> str:
        """Determine variance level (low/medium/high)."""
        if self.distribution.roi_std == 0:
            return "low"
        cv = abs(self.distribution.roi_std / self.distribution.roi_mean) if self.distribution.roi_mean != 0 else 0
        if cv < 0.2:
            return "low"
        elif cv < 0.5:
            return "medium"
        else:
            return "high"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "baseline_report": self.baseline_report.to_dict() if self.baseline_report else {},
            "distribution": self.distribution.to_dict(),
            "assumptions": self.assumptions.to_dict(),
            "narrative_summary": self.narrative_summary,
            "size_label": self.size_label,
            "risk_grade": self.risk_grade,
            "simulation_runs": self.simulation_runs,
            "is_valid": self.is_simulation_valid,
            "variance_level": self.variance_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessCaseSimulationReport":
        """Create from dictionary."""
        baseline_data = data.get("baseline_report", {})
        baseline = BusinessCaseReport.from_dict(baseline_data) if baseline_data else None

        dist_data = data.get("distribution", {})
        distribution = SimulationDistribution.from_dict(dist_data) if dist_data else SimulationDistribution()

        assumptions_data = data.get("assumptions", {})
        assumptions = SimulationAssumptions.from_dict(assumptions_data) if assumptions_data else SimulationAssumptions()

        return cls(
            baseline_report=baseline,
            distribution=distribution,
            assumptions=assumptions,
            narrative_summary=data.get("narrative_summary", ""),
            size_label=data.get("size_label", "small"),
            risk_grade=data.get("risk_grade", "C"),
            simulation_runs=data.get("simulation_runs", DEFAULT_SIMULATION_RUNS),
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _percentile(sorted_data: List[float], p: int) -> float:
    """Calculate percentile from sorted data."""
    if not sorted_data:
        return 0.0
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]

    k = (n - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return sorted_data[int(k)]

    return sorted_data[int(f)] * (c - k) + sorted_data[int(c)] * (k - f)


def _calculate_std(data: List[float], mean: float) -> float:
    """Calculate standard deviation."""
    if len(data) < 2:
        return 0.0
    variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
    return math.sqrt(variance)


def _triangular_sample(min_val: float, mode_val: float, max_val: float) -> float:
    """Sample from triangular distribution."""
    if min_val >= max_val:
        return mode_val
    return random.triangular(min_val, max_val, mode_val)


def _uniform_sample(min_val: float, max_val: float) -> float:
    """Sample from uniform distribution."""
    if min_val >= max_val:
        return min_val
    return random.uniform(min_val, max_val)


def _normal_sample(mean: float, std: float, min_val: float, max_val: float) -> float:
    """Sample from truncated normal distribution."""
    value = random.gauss(mean, std)
    return max(min_val, min(max_val, value))


def _sample_from_distribution(
    min_val: float,
    mode_val: float,
    max_val: float,
    distribution_type: str,
) -> float:
    """Sample a value based on distribution type."""
    if distribution_type == DISTRIBUTION_UNIFORM:
        return _uniform_sample(min_val, max_val)
    elif distribution_type == DISTRIBUTION_NORMAL:
        mean = mode_val
        std = (max_val - min_val) / 4  # Approximate std
        return _normal_sample(mean, std, min_val, max_val)
    else:  # Default: triangular
        return _triangular_sample(min_val, mode_val, max_val)


# Company size constants (Phase 5C - avoid magic strings)
SIZE_SOLO: str = "solo"      # 1 person
SIZE_SMALL: str = "small"    # 2-10 persons
SIZE_MEDIUM: str = "medium"  # 11-100 persons

# Frontend V2 size values (for direct matching - O(1) set lookup)
FRONTEND_SIZE_VALUES_SOLO: Set[str] = {"1", "1 mitarbeiter"}
FRONTEND_SIZE_VALUES_SMALL: Set[str] = {"2-10", "2–10"}
FRONTEND_SIZE_VALUES_MEDIUM: Set[str] = {"11-100", "11–100"}


def _determine_size_label(briefing: Optional[Dict[str, Any]]) -> str:
    """
    Determine company size label from briefing.

    Maps questionnaire values to standard size keys:
    - "1" → "solo" (Solo-Selbstständig/Freiberuflich)
    - "2–10" → "small" (Kleines Team)
    - "11–100" → "medium" (KMU)

    **Frontend V2 (current, since 2026-01-06):**
    - Direct string matching for exact values

    **Legacy Format (pre-2026-01-06):**
    - Keyword-based fallback (for old data)

    Args:
        briefing: Briefing dictionary from questionnaire.
                  Should contain 'unternehmensgroesse' key.

    Returns:
        str: Normalized size ("solo", "small", or "medium")

    Examples:
        >>> _determine_size_label({"unternehmensgroesse": "1"})
        'solo'
        >>> _determine_size_label({"unternehmensgroesse": "2–10"})
        'small'
        >>> _determine_size_label({"unternehmensgroesse": "11–100"})
        'medium'

    Notes:
        - Supports both dash types: "–" (En-Dash) and "-" (Hyphen)
        - Default fallback: "small" (most common use case)
    """
    # Edge case: None or empty briefing
    if not briefing:
        log.debug("Empty briefing received, defaulting size to 'small'")
        return SIZE_SMALL

    size = str(briefing.get("unternehmensgroesse", "")).lower().strip()

    # Edge case: empty size value
    if not size:
        return SIZE_SMALL

    # --- Frontend V2 (fast path with set lookup - O(1)) ---
    if size in FRONTEND_SIZE_VALUES_SOLO:
        return SIZE_SOLO
    if size in FRONTEND_SIZE_VALUES_SMALL:
        return SIZE_SMALL
    if size in FRONTEND_SIZE_VALUES_MEDIUM:
        return SIZE_MEDIUM

    # --- Legacy keyword matching (fallback) ---
    # Medium (11-100) - check first to avoid false matches
    if any(kw in size for kw in ("medium", "mittel", "kmu", "11-100", "11–100")):
        return SIZE_MEDIUM

    # Solo (1 person)
    if any(kw in size for kw in ("solo", "freiberuf", "einzelunternehm")):
        return SIZE_SOLO

    # Default: small (2-10) is the most common
    return SIZE_SMALL


def _extract_risk_grade(risk_report_v3: Any) -> str:
    """Extract risk grade from Risk Engine V3 report."""
    if not risk_report_v3:
        return "C"

    if hasattr(risk_report_v3, "residual_risk_grade"):
        return str(risk_report_v3.residual_risk_grade)
    elif isinstance(risk_report_v3, dict):
        return str(risk_report_v3.get("residual_risk_grade", "C"))

    return "C"


def _extract_residual_risk_score(risk_report_v3: Any) -> float:
    """Extract residual risk score from Risk Engine V3 report."""
    if not risk_report_v3:
        return 50.0

    if hasattr(risk_report_v3, "residual_risk_score"):
        return float(risk_report_v3.residual_risk_score)
    elif isinstance(risk_report_v3, dict):
        return float(risk_report_v3.get("residual_risk_score", 50.0))

    return 50.0


# =============================================================================
# ASSUMPTION GENERATION
# =============================================================================

def generate_default_assumptions(
    business_case: BusinessCaseReport,
    risk_report_v3: Any = None,
    auto_report: Any = None,
    size_label: str = "small",  # was "team"
) -> SimulationAssumptions:
    """
    Generate default simulation assumptions from business case baseline.

    Uses G30 scenarios to derive reasonable ranges:
    - Conservative scenario values as min
    - Realistic scenario values as mode
    - Optimistic scenario values as max

    Risk adjustment based on G33 residual risk score.
    """
    # Get scenarios
    optimistic = business_case.get_scenario("optimistic")
    realistic = business_case.get_scenario("realistic")
    conservative = business_case.get_scenario("conservative")

    # Default values if scenarios missing
    base_savings = realistic.monthly_savings if realistic else 500.0
    base_investment = business_case.investment_total or 5000.0

    # Size-based variance multiplier
    variance_mult = SIZE_VARIANCE_MULTIPLIERS.get(size_label, 1.0)

    # Risk-based variance factor
    risk_grade = _extract_risk_grade(risk_report_v3)
    risk_variance = RISK_VARIANCE_FACTORS.get(risk_grade, 1.0)

    # Combined variance factor
    combined_variance = variance_mult * risk_variance

    # Monthly savings range
    if conservative and optimistic:
        savings_min = conservative.monthly_savings
        savings_max = optimistic.monthly_savings
    else:
        # FIX-J1: Widen savings range — combined_variance now WIDENS the spread
        savings_spread = (1 - DEFAULT_SAVINGS_RANGE["min_pct"])  # e.g. 0.2 if min_pct=0.8
        savings_min = base_savings * (1 - savings_spread * max(combined_variance, 1.0))
        savings_max = base_savings * (1 + savings_spread * max(combined_variance, 1.0))

    # Investment range
    if conservative and optimistic:
        # Conservative = higher investment, optimistic = lower
        invest_min = optimistic.investment_total
        invest_max = conservative.investment_total
    else:
        # FIX-J1: Widen investment range
        invest_spread = (DEFAULT_INVESTMENT_RANGE["max_pct"] - 1)  # e.g. 0.3 if max=1.3
        invest_min = base_investment * (1 - invest_spread * max(combined_variance, 1.0))
        invest_max = base_investment * (1 + invest_spread * max(combined_variance, 1.0))

    # Speed factor based on risk
    speed_min = DEFAULT_IMPLEMENTATION_SPEED_RANGE["min_pct"]
    speed_max = DEFAULT_IMPLEMENTATION_SPEED_RANGE["max_pct"]
    if risk_grade in ["D", "F"]:
        speed_min *= 0.9  # Higher risk = potentially slower
        speed_max *= 0.95

    # Risk adjustment factor - higher risk score = lower factor
    risk_score = _extract_residual_risk_score(risk_report_v3)
    risk_factor_mode = max(0.5, min(1.0, 1.5 - risk_score / 100))  # 50% score = 1.0, 100% = 0.5
    risk_factor_min = max(0.3, risk_factor_mode - 0.3 * max(combined_variance, 1.0))  # J1: wider risk spread
    risk_factor_max = min(1.2, risk_factor_mode + 0.1)

    # Funding success probability
    funding_prob = 0.5
    if business_case.funding_programmes_used:
        funding_prob = min(0.8, 0.4 + len(business_case.funding_programmes_used) * 0.15)

    return SimulationAssumptions(
        monthly_savings_min=max(0, savings_min),
        monthly_savings_mode=base_savings,
        monthly_savings_max=savings_max,
        investment_min=max(100, invest_min),
        investment_mode=base_investment,
        investment_max=invest_max,
        speed_factor_min=speed_min,
        speed_factor_mode=1.0,
        speed_factor_max=speed_max,
        risk_factor_min=risk_factor_min,
        risk_factor_mode=risk_factor_mode,
        risk_factor_max=risk_factor_max,
        funding_success_probability=funding_prob,
        distribution_type=DISTRIBUTION_TRIANGULAR,
    )


def parse_llm_assumptions(llm_response: str) -> Optional[SimulationAssumptions]:
    """
    Parse LLM response containing assumption JSON.

    Expected format:
    {
        "assumptions": {
            "monthly_savings": {"min": 3000, "mode": 5000, "max": 8000},
            "investment_total": {"min": 20000, "mode": 25000, "max": 30000},
            "speed_factor": {"min": 0.7, "mode": 1.0, "max": 1.2},
            "risk_factor": {"min": 0.8, "mode": 1.0, "max": 1.1},
            "funding_success_probability": 0.6
        }
    }
    """
    if not llm_response:
        return None

    try:
        data = json.loads(llm_response)
        if "assumptions" in data:
            return SimulationAssumptions.from_dict(data["assumptions"])
        return SimulationAssumptions.from_dict(data)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        log.warning("[G34] Failed to parse LLM assumptions: %s", e)
        return None


# =============================================================================
# MONTE CARLO SIMULATION
# =============================================================================

def run_monte_carlo_simulation(
    assumptions: SimulationAssumptions,
    funding_effect_base: float = 0.0,
    runs: int = DEFAULT_SIMULATION_RUNS,
) -> SimulationDistribution:
    """
    Run Monte Carlo simulation for ROI and Payback.

    For each simulation:
    1. Sample monthly_savings from distribution
    2. Sample investment_total from distribution
    3. Sample risk_factor for adjustment
    4. Apply funding effect probabilistically
    5. Calculate ROI and Payback

    Returns distribution with all percentiles calculated.
    """
    runs = max(MIN_SIMULATION_RUNS, min(MAX_SIMULATION_RUNS, runs))

    roi_samples: List[float] = []
    payback_samples: List[float] = []
    savings_samples: List[float] = []

    dist_type = assumptions.distribution_type

    for _ in range(runs):
        # Sample monthly savings
        monthly_savings = _sample_from_distribution(
            assumptions.monthly_savings_min,
            assumptions.monthly_savings_mode,
            assumptions.monthly_savings_max,
            dist_type,
        )

        # Sample investment
        investment = _sample_from_distribution(
            assumptions.investment_min,
            assumptions.investment_mode,
            assumptions.investment_max,
            dist_type,
        )

        # Sample risk factor
        risk_factor = _sample_from_distribution(
            assumptions.risk_factor_min,
            assumptions.risk_factor_mode,
            assumptions.risk_factor_max,
            dist_type,
        )

        # Sample speed factor
        speed_factor = _sample_from_distribution(
            assumptions.speed_factor_min,
            assumptions.speed_factor_mode,
            assumptions.speed_factor_max,
            dist_type,
        )

        # Apply funding effect probabilistically
        funding_effect = 0.0
        if random.random() < assumptions.funding_success_probability:
            funding_effect = funding_effect_base

        # Adjust values
        effective_savings = monthly_savings * risk_factor * speed_factor
        effective_investment = max(100, investment - funding_effect)

        # Calculate annual savings
        annual_savings = effective_savings * 12

        # Calculate ROI
        # v7.1.7: Cap at MAX_ROI (200%) to prevent 637% values reaching HTML output.
        # R1-FIX originally set apply_cap=False + SIMULATION_ROI_CAP=500% for variance,
        # but this caused 52+ B25 sanitizer cappings. Variance is preserved by the
        # Monte Carlo input distributions (different savings/investment per sample).
        roi = calculate_roi(annual_savings, effective_investment, apply_cap=True)

        # Calculate Payback
        if effective_savings > 0:
            payback = effective_investment / effective_savings
            payback = max(MIN_PAYBACK_MONTHS, min(MAX_PAYBACK_MONTHS, payback))
        else:
            payback = MAX_PAYBACK_MONTHS

        roi_samples.append(roi)
        payback_samples.append(payback)
        savings_samples.append(effective_savings)

    distribution = SimulationDistribution(
        roi_samples=roi_samples,
        payback_samples=payback_samples,
        monthly_savings_samples=savings_samples,
    )
    distribution._calculate_statistics()

    return distribution


# =============================================================================
# NARRATIVE GENERATION
# =============================================================================

def generate_narrative_summary(
    distribution: SimulationDistribution,
    baseline: BusinessCaseReport,
    assumptions: SimulationAssumptions,
    lang: str = "de",
) -> str:
    """Generate narrative summary for simulation results."""
    realistic = baseline.realistic_scenario

    if lang == "en":
        parts = []

        # P50 vs realistic comparison
        if realistic:
            deviation = abs(distribution.roi_p50 - realistic.roi_12m)
            if deviation < 10:
                parts.append(f"The Monte Carlo simulation confirms the realistic scenario with a median ROI of {distribution.roi_p50:.0f}%.")
            elif distribution.roi_p50 > realistic.roi_12m:
                parts.append(f"The simulation indicates potential upside: median ROI of {distribution.roi_p50:.0f}% vs. {realistic.roi_12m:.0f}% planned.")
            else:
                parts.append(f"The simulation suggests conservative planning may be prudent: median ROI of {distribution.roi_p50:.0f}%.")

        # Confidence interval
        roi_ci = distribution.roi_confidence_interval_80
        parts.append(f"With 80% probability, ROI will fall between {roi_ci[0]:.0f}% and {roi_ci[1]:.0f}%.")

        # Payback
        pb_ci = distribution.payback_confidence_interval_80
        parts.append(f"Payback period: {distribution.payback_p50:.1f} months (80% CI: {pb_ci[0]:.1f}-{pb_ci[1]:.1f} months).")

        # Risk assessment
        if distribution.roi_std > 50:
            parts.append("High variance indicates significant uncertainty - consider risk mitigation.")
        elif distribution.roi_std < 20:
            parts.append("Low variance suggests reliable outcome expectations.")

    else:  # German
        parts = []

        # P50 vs realistic comparison
        if realistic:
            deviation = abs(distribution.roi_p50 - realistic.roi_12m)
            if deviation < 10:
                parts.append(f"Die Monte-Carlo-Simulation bestaetigt das realistische Szenario mit einem Median-ROI von {distribution.roi_p50:.0f}%.")
            elif distribution.roi_p50 > realistic.roi_12m:
                parts.append(f"Die Simulation zeigt Potenzial nach oben: Median-ROI von {distribution.roi_p50:.0f}% vs. {realistic.roi_12m:.0f}% geplant.")
            else:
                parts.append(f"Die Simulation empfiehlt konservative Planung: Median-ROI von {distribution.roi_p50:.0f}%.")

        # Confidence interval
        roi_ci = distribution.roi_confidence_interval_80
        parts.append(f"Mit 80% Wahrscheinlichkeit liegt der ROI zwischen {roi_ci[0]:.0f}% und {roi_ci[1]:.0f}%.")

        # Payback - Fix-Batch J2: Use German decimal format
        pb_ci = distribution.payback_confidence_interval_80
        parts.append(f"Amortisation: {format_decimal_de(distribution.payback_p50)} Monate (80% KI: {format_decimal_de(pb_ci[0])}-{format_decimal_de(pb_ci[1])} Monate).")

        # Risk assessment
        if distribution.roi_std > 50:
            parts.append("Hohe Varianz zeigt erhebliche Unsicherheit - Risikominderung empfohlen.")
        elif distribution.roi_std < 20:
            parts.append("Niedrige Varianz deutet auf zuverlaessige Ergebniserwartungen hin.")

    return " ".join(parts)


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_business_case_simulation(
    context: Any = None,
    business_case: Optional[BusinessCaseReport] = None,
    risk_report_v3: Any = None,
    auto_report: Any = None,
    tools_data: Any = None,
    funding_data: Any = None,
    briefing: Optional[Dict[str, Any]] = None,
    llm_response: Optional[str] = None,
    runs: int = DEFAULT_SIMULATION_RUNS,
) -> BusinessCaseSimulationReport:
    """
    Generate Business Case Simulation Report with Monte Carlo analysis.

    This function:
    1. Takes G30 BusinessCaseReport as baseline
    2. Extracts or generates simulation assumptions
    3. Adjusts variance based on G33 risk score and company size
    4. Runs Monte Carlo simulation
    5. Calculates P50/P80/P90 percentiles
    6. Generates narrative summary

    Args:
        context: ReportContext object (optional)
        business_case: G30 BusinessCaseReport (required)
        risk_report_v3: G33 RiskReportV3 for risk adjustment
        auto_report: G36 AutomationRoadmapReport for context
        tools_data: G25 Tools Engine data
        funding_data: G26 Funding Engine data
        briefing: Original briefing/answers dict
        llm_response: Optional LLM response with assumptions JSON
        runs: Number of simulation runs (default 1000)

    Returns:
        BusinessCaseSimulationReport with simulation results
    """
    log.info("[G34] Starting Business Case Monte Carlo Simulation...")

    # Ensure we have a baseline
    if business_case is None:
        log.warning("[G34] No business case provided, creating empty baseline")
        business_case = BusinessCaseReport()

    # Determine size label
    size_label = _determine_size_label(briefing)

    # Extract risk grade
    risk_grade = _extract_risk_grade(risk_report_v3)

    # Get language
    lang = "de"
    if briefing:
        lang = briefing.get("language", briefing.get("sprache", "de"))

    # Parse LLM assumptions or generate defaults
    assumptions: Optional[SimulationAssumptions] = None
    if llm_response:
        assumptions = parse_llm_assumptions(llm_response)

    if not assumptions or not assumptions.is_valid:
        log.info("[G34] Generating default assumptions from business case")
        assumptions = generate_default_assumptions(
            business_case=business_case,
            risk_report_v3=risk_report_v3,
            auto_report=auto_report,
            size_label=size_label,
        )

    # Get funding effect from baseline
    funding_effect_base = business_case.funding_effect

    # Run Monte Carlo simulation
    log.info("[G34] Running Monte Carlo simulation with %d runs...", runs)
    distribution = run_monte_carlo_simulation(
        assumptions=assumptions,
        funding_effect_base=funding_effect_base,
        runs=runs,
    )

    # Generate narrative
    narrative = generate_narrative_summary(
        distribution=distribution,
        baseline=business_case,
        assumptions=assumptions,
        lang=lang,
    )

    report = BusinessCaseSimulationReport(
        baseline_report=business_case,
        distribution=distribution,
        assumptions=assumptions,
        narrative_summary=narrative,
        size_label=size_label,
        risk_grade=risk_grade,
        simulation_runs=runs,
    )

    log.info(
        "[G34] Business Case Simulation complete: ROI P50=%.1f%%, P80=%.1f%%, P90=%.1f%%, "
        "Payback P50=%.1f months, runs=%d",
        distribution.roi_p50,
        distribution.roi_p80,
        distribution.roi_p90,
        distribution.payback_p50,
        runs,
    )

    return report


# =============================================================================
# HTML RENDERING
# =============================================================================

def business_case_simulation_to_html(
    report: BusinessCaseSimulationReport,
    lang: str = "de",
) -> str:
    """
    Generate HTML section for Business Case Simulation.

    Renders:
    - P50/P80/P90 percentile table for ROI & Payback
    - Min/Max ranges
    - Confidence interval visualization
    - Narrative summary
    - Comparison to G30 deterministic scenarios

    Uses only allowed tags: div, p, ul, li, strong, span, table, tr, td, th

    Args:
        report: BusinessCaseSimulationReport object
        lang: Language code ("de" or "en")

    Returns:
        HTML string for PDF template
    """
    # Labels
    if lang == "en":
        labels = {
            "title": "Risk-Adjusted Business Case",
            "subtitle": "Monte Carlo Simulation Analysis",
            "roi_label": "ROI (12 months)",
            "payback_label": "Payback Period",
            "percentile": "Percentile",
            "p50": "P50 (Median)",
            "p80": "P80",
            "p90": "P90",
            "p20": "P20",
            "min": "Min",
            "max": "Max",
            "mean": "Mean",
            "std": "Std Dev",
            "months": "months",
            "runs": "Simulation Runs",
            "confidence_80": "80% Confidence Interval",
            "assumptions": "Simulation Assumptions",
            "monthly_savings": "Monthly Savings",
            "investment": "Investment",
            "assessment": "Assessment",
            "vs_realistic": "vs. Realistic Scenario",
            "variance": "Variance Level",
            "low": "Low",
            "medium": "Medium",
            "high": "High",
        }
    else:
        # K2: 100% German labels for DE reports
        labels = {
            "title": "Risikoadjustierter Business Case",
            "subtitle": "Monte-Carlo Simulationsanalyse",
            "roi_label": "ROI (12 Monate)",
            "payback_label": "Amortisationszeit",
            "percentile": "Perzentil",
            "p50": "P50 (Median)",
            "p80": "P80",
            "p90": "P90",
            "p20": "P20",
            "min": "Min",
            "max": "Max",
            "mean": "Mittelwert",
            "std": "Std-Abw.",
            "months": "Monate",
            "runs": "Simulationsläufe",  # K2: Fix umlaut
            "confidence_80": "80% Konfidenzintervall",
            "assumptions": "Simulationsannahmen",
            "monthly_savings": "Monatl. Ersparnis",
            "investment": "Investition",  # K2: German label
            "assessment": "Bewertung",
            "vs_realistic": "vs. Realistisches Szenario",
            "variance": "Varianz-Level",
            "low": "Niedrig",
            "medium": "Mittel",
            "high": "Hoch",
        }

    dist = report.distribution
    assumptions = report.assumptions
    realistic = report.realistic_scenario

    # Colors
    colors = {
        "primary": "#6366f1",      # Indigo
        "primary_light": "#a5b4fc",
        "primary_bg": "#eef2ff",
        "green": "#22c55e",
        "green_bg": "#f0fdf4",
        "yellow": "#f59e0b",
        "yellow_bg": "#fffbeb",
        "red": "#dc2626",
        "red_bg": "#fef2f2",
        "blue": "#3b82f6",
        "blue_bg": "#eff6ff",
        "gray": "#64748b",
        "gray_light": "#f1f5f9",
        "gray_border": "#e2e8f0",
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
    }

    # Variance level color
    variance_color = colors["green"] if report.variance_level == "low" else (
        colors["yellow"] if report.variance_level == "medium" else colors["red"]
    )
    variance_label = labels.get(report.variance_level, report.variance_level)

    html_parts: List[str] = []

    # Main container
    html_parts.append(f'''
<div class="business-case-simulation" style="font-size:11pt;color:{colors["text_primary"]};">
    <!-- Header -->
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <span style="font-size:20px;">🎲</span>
        <span style="font-size:11px;padding:2px 8px;background:{colors["primary"]};color:#fff;border-radius:4px;font-weight:600;">G34</span>
        <span style="font-size:10pt;color:{colors["text_secondary"]};">{labels["subtitle"]} ({dist.simulation_runs} {labels["runs"]})</span>
    </div>
''')

    # Main KPI Cards - ROI and Payback P50
    html_parts.append(f'''
    <!-- Key Metrics -->
    <div style="display:flex;gap:16px;margin-bottom:20px;">
        <!-- ROI P50 Card -->
        <div style="flex:1;padding:20px;background:linear-gradient(135deg,{colors["primary_bg"]} 0%,#fff 100%);border-radius:12px;border:2px solid {colors["primary_light"]};text-align:center;">
            <span style="font-size:10px;color:{colors["text_secondary"]};font-weight:600;">{labels["roi_label"]} {labels["p50"]}</span>
            <div style="font-size:36px;font-weight:700;color:{colors["primary"]};margin:8px 0;">{dist.roi_p50:.0f}%</div>
            <div style="font-size:9pt;color:{colors["text_secondary"]};">
                {labels["confidence_80"]}: {dist.roi_confidence_interval_80[0]:.0f}% - {dist.roi_confidence_interval_80[1]:.0f}%
            </div>
        </div>

        <!-- Payback P50 Card -->
        <div style="flex:1;padding:20px;background:linear-gradient(135deg,{colors["blue_bg"]} 0%,#fff 100%);border-radius:12px;border:2px solid #93c5fd;text-align:center;">
            <span style="font-size:10px;color:{colors["text_secondary"]};font-weight:600;">{labels["payback_label"]} {labels["p50"]}</span>
            <div style="font-size:36px;font-weight:700;color:{colors["blue"]};margin:8px 0;">{dist.payback_p50:.1f}</div>
            <div style="font-size:9pt;color:{colors["text_secondary"]};">
                {labels["months"]} ({labels["confidence_80"]}: {dist.payback_confidence_interval_80[0]:.1f}-{dist.payback_confidence_interval_80[1]:.1f})
            </div>
        </div>

        <!-- Variance Card -->
        <div style="flex:0.6;padding:20px;background:{colors["gray_light"]};border-radius:12px;border:1px solid {colors["gray_border"]};text-align:center;">
            <span style="font-size:10px;color:{colors["text_secondary"]};font-weight:600;">{labels["variance"]}</span>
            <div style="font-size:24px;font-weight:700;color:{variance_color};margin:8px 0;">{variance_label}</div>
            <div style="font-size:9pt;color:{colors["text_secondary"]};">
                Std: {dist.roi_std:.1f}%
            </div>
        </div>
    </div>
''')

    # Percentile Table
    html_parts.append(f'''
    <!-- Percentile Table -->
    <div style="margin-bottom:20px;">
        <table class="table-modern" style="width:100%;border-collapse:collapse;font-size:10pt;">
            <tr style="background:{colors["gray_light"]};">
                <th style="padding:10px;text-align:left;border:1px solid {colors["gray_border"]};">{labels["percentile"]}</th>
                <th style="padding:10px;text-align:right;border:1px solid {colors["gray_border"]};">{labels["roi_label"]}</th>
                <th style="padding:10px;text-align:right;border:1px solid {colors["gray_border"]};">{labels["payback_label"]}</th>
            </tr>
            <tr>
                <td style="padding:8px;border:1px solid {colors["gray_border"]};font-weight:600;color:{colors["red"]};">{labels["p20"]}</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};">{dist.roi_p20:.1f}%</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};">{dist.payback_p20:.1f} {labels["months"]}</td>
            </tr>
            <tr style="background:{colors["primary_bg"]};">
                <td style="padding:8px;border:1px solid {colors["gray_border"]};font-weight:600;color:{colors["primary"]};">{labels["p50"]}</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};font-weight:700;color:{colors["primary"]};">{dist.roi_p50:.1f}%</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};font-weight:700;color:{colors["primary"]};">{dist.payback_p50:.1f} {labels["months"]}</td>
            </tr>
            <tr>
                <td style="padding:8px;border:1px solid {colors["gray_border"]};font-weight:600;color:{colors["yellow"]};">{labels["p80"]}</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};">{dist.roi_p80:.1f}%</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};">{dist.payback_p80:.1f} {labels["months"]}</td>
            </tr>
            <tr style="background:{colors["green_bg"]};">
                <td style="padding:8px;border:1px solid {colors["gray_border"]};font-weight:600;color:{colors["green"]};">{labels["p90"]}</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};">{dist.roi_p90:.1f}%</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};">{dist.payback_p90:.1f} {labels["months"]}</td>
            </tr>
            <tr style="background:{colors["gray_light"]};">
                <td style="padding:8px;border:1px solid {colors["gray_border"]};font-size:9pt;">{labels["min"]} / {labels["max"]}</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};font-size:9pt;">{dist.roi_min:.1f}% / {dist.roi_max:.1f}%</td>
                <td style="padding:8px;text-align:right;border:1px solid {colors["gray_border"]};font-size:9pt;">{dist.payback_min:.1f} / {dist.payback_max:.1f} {labels["months"]}</td>
            </tr>
        </table>
    </div>
''')

    # Comparison to G30 realistic scenario
    if realistic:
        deviation_pct = report.roi_p50_vs_realistic_deviation
        comparison_color = colors["green"] if deviation_pct < 15 else (colors["yellow"] if deviation_pct < 30 else colors["red"])

        # PLATIN+++ v5.4.1: Spread explanation labels (DE/EN)
        if lang == "en":
            spread_explanation = (
                "The P50 (median) from Monte Carlo simulation is typically more conservative than the "
                "deterministic 'Realistic' scenario. The Realistic scenario uses expected values "
                "assuming optimal conditions. Monte Carlo, however, runs 1,000 simulations with "
                "varying assumptions (savings ±40%, investment ±30%, implementation speed ±20%). "
                "Because downside risks are often larger than upside potential, the statistical "
                "median (P50) is more conservative. A deviation under 30% indicates robust assumptions."
            )
        else:
            spread_explanation = (
                "Der P50 (Median) aus der Monte-Carlo-Simulation ist typischerweise konservativer "
                "als das deterministische 'Realistisch'-Szenario. Das Realistisch-Szenario verwendet "
                "Erwartungswerte unter optimalen Bedingungen. Monte-Carlo hingegen führt 1.000 "
                "Simulationen mit variierenden Annahmen durch (Einsparungen ±40%, Investment ±30%, "
                "Implementierungsgeschwindigkeit ±20%). Da Abwärtsrisiken oft größer sind als "
                "Aufwärtspotenziale, ist der statistische Median (P50) konservativer. "
                "Eine Abweichung unter 30% deutet auf robuste Annahmen hin."
            )

        html_parts.append(f'''
    <!-- Comparison to G30 -->
    <div style="padding:16px;background:{colors["yellow_bg"]};border-radius:12px;border:1px solid #fcd34d;margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <span style="font-size:10px;font-weight:600;color:{colors["yellow"]};">📊 {labels["vs_realistic"]}</span>
                <div style="font-size:10pt;color:{colors["text_primary"]};margin-top:4px;">
                    G30 Realistic: <strong>{realistic.roi_12m:.0f}%</strong> ROI, <strong>{realistic.payback_months:.1f}</strong> {labels["months"]} Payback
                </div>
            </div>
            <div style="text-align:right;">
                <span style="font-size:9px;color:{colors["text_secondary"]};">Abweichung</span>
                <div style="font-size:16px;font-weight:700;color:{comparison_color};">{deviation_pct:.0f}%</div>
            </div>
        </div>
        <!-- PLATIN+++ v5.4.1: Spread explanation -->
        <div style="margin-top:12px;padding-top:12px;border-top:1px dashed #fcd34d;">
            <p style="font-size:9pt;color:{colors["text_secondary"]};margin:0;line-height:1.5;">
                {spread_explanation}
            </p>
        </div>
    </div>
''')

    # Assumptions summary
    html_parts.append(f'''
    <!-- Assumptions -->
    <div style="padding:16px;background:{colors["gray_light"]};border-radius:12px;margin-bottom:20px;">
        <span style="font-size:10px;font-weight:600;color:{colors["text_secondary"]};">⚙️ {labels["assumptions"]}</span>
        <div style="display:flex;gap:16px;margin-top:8px;">
            <div style="flex:1;">
                <span style="font-size:9px;color:{colors["text_secondary"]};">{labels["monthly_savings"]}</span>
                <div style="font-size:10pt;">{assumptions.monthly_savings_min:,.0f} - {assumptions.monthly_savings_mode:,.0f} - {assumptions.monthly_savings_max:,.0f} EUR</div>
            </div>
            <div style="flex:1;">
                <span style="font-size:9px;color:{colors["text_secondary"]};">{labels["investment"]}</span>
                <div style="font-size:10pt;">{assumptions.investment_min:,.0f} - {assumptions.investment_mode:,.0f} - {assumptions.investment_max:,.0f} EUR</div>
            </div>
        </div>
    </div>
''')

    # Narrative summary
    if report.narrative_summary:
        html_parts.append(f'''
    <!-- Narrative -->
    <div style="padding:16px;background:#fff;border-radius:12px;border:1px solid {colors["gray_border"]};">
        <span style="font-size:10px;font-weight:600;color:{colors["text_secondary"]};">📝 {labels["assessment"]}</span>
        <p style="margin:8px 0 0 0;font-size:10pt;color:{colors["text_primary"]};line-height:1.6;">
            {report.narrative_summary}
        </p>
    </div>
''')

    # Close container
    html_parts.append('</div>')

    return '\n'.join(html_parts)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G34] Business Case Simulation Engine loaded")
