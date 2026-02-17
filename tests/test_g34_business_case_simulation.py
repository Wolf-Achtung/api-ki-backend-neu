# -*- coding: utf-8 -*-
"""
Sprint G34: Business Case Monte Carlo Simulation Tests
=======================================================

Comprehensive test suite for Business Case Simulation Engine with 50+ tests covering:
- Data structures (SimulationAssumptions, SimulationDistribution, BusinessCaseSimulationReport)
- Monte Carlo simulation logic
- Percentile calculations
- Assumption generation from G30 baseline
- LLM response parsing
- HTML generation
- G22 Consistency Engine integration (BCSIM_001-BCSIM_006)
- Size-awareness
- Risk adjustment

Version: 1.0.0 (Sprint G34)
"""
from __future__ import annotations

import json
import math
import pytest
from typing import Any, Dict, List, Optional


# =============================================================================
# TEST: Data Structures - SimulationAssumptions
# =============================================================================

class TestSimulationAssumptions:
    """Tests for SimulationAssumptions dataclass."""

    def test_basic_creation(self) -> None:
        """Test SimulationAssumptions can be instantiated with basic values."""
        from services.business_case_simulation import SimulationAssumptions

        assumptions = SimulationAssumptions(
            monthly_savings_min=1000.0,
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
            investment_min=5000.0,
            investment_mode=8000.0,
            investment_max=12000.0,
        )

        assert assumptions.monthly_savings_min == 1000.0
        assert assumptions.monthly_savings_mode == 2000.0
        assert assumptions.monthly_savings_max == 3000.0
        assert assumptions.investment_min == 5000.0
        assert assumptions.investment_mode == 8000.0
        assert assumptions.investment_max == 12000.0

    def test_default_values(self) -> None:
        """Test SimulationAssumptions has sensible defaults."""
        from services.business_case_simulation import SimulationAssumptions

        assumptions = SimulationAssumptions()

        assert assumptions.speed_factor_min == 0.7
        assert assumptions.speed_factor_mode == 1.0
        assert assumptions.speed_factor_max == 1.2
        assert assumptions.risk_factor_mode == 1.0

    def test_min_mode_max_validation(self) -> None:
        """Test min <= mode <= max is enforced."""
        from services.business_case_simulation import SimulationAssumptions

        # Create with invalid ordering (min > mode)
        assumptions = SimulationAssumptions(
            monthly_savings_min=5000.0,  # Greater than mode
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
        )

        # Should be normalized so min <= mode
        assert assumptions.monthly_savings_min <= assumptions.monthly_savings_mode

    def test_funding_probability_clamped(self) -> None:
        """Test funding probability is clamped to [0, 1]."""
        from services.business_case_simulation import SimulationAssumptions

        assumptions = SimulationAssumptions(
            funding_success_probability=1.5,  # Above 1
        )

        assert assumptions.funding_success_probability == 1.0

        assumptions2 = SimulationAssumptions(
            funding_success_probability=-0.5,  # Below 0
        )

        assert assumptions2.funding_success_probability == 0.0

    def test_is_valid_property(self) -> None:
        """Test is_valid returns True for valid assumptions."""
        from services.business_case_simulation import SimulationAssumptions

        assumptions = SimulationAssumptions(
            monthly_savings_min=1000.0,
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
            investment_min=5000.0,
            investment_mode=8000.0,
            investment_max=12000.0,
        )

        assert assumptions.is_valid is True

    def test_is_valid_false_for_zero_max(self) -> None:
        """Test is_valid returns False when max values are zero."""
        from services.business_case_simulation import SimulationAssumptions

        assumptions = SimulationAssumptions(
            monthly_savings_max=0.0,
            investment_max=0.0,
        )

        assert assumptions.is_valid is False

    def test_to_dict_serialization(self) -> None:
        """Test SimulationAssumptions serialization to dict."""
        from services.business_case_simulation import SimulationAssumptions

        assumptions = SimulationAssumptions(
            monthly_savings_min=1000.0,
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
            funding_success_probability=0.6,
        )

        result = assumptions.to_dict()

        assert isinstance(result, dict)
        assert "monthly_savings" in result
        assert result["monthly_savings"]["min"] == 1000.0
        assert result["monthly_savings"]["mode"] == 2000.0
        assert result["monthly_savings"]["max"] == 3000.0
        assert result["funding_success_probability"] == 0.6

    def test_from_dict_deserialization(self) -> None:
        """Test SimulationAssumptions deserialization from dict."""
        from services.business_case_simulation import SimulationAssumptions

        data = {
            "monthly_savings": {"min": 500, "mode": 1000, "max": 1500},
            "investment_total": {"min": 3000, "mode": 5000, "max": 7000},
            "speed_factor": {"min": 0.8, "mode": 1.0, "max": 1.1},
            "funding_success_probability": 0.5,
        }

        assumptions = SimulationAssumptions.from_dict(data)

        assert assumptions.monthly_savings_min == 500.0
        assert assumptions.monthly_savings_mode == 1000.0
        assert assumptions.monthly_savings_max == 1500.0
        assert assumptions.funding_success_probability == 0.5


# =============================================================================
# TEST: Data Structures - SimulationDistribution
# =============================================================================

class TestSimulationDistribution:
    """Tests for SimulationDistribution dataclass."""

    def test_basic_creation_with_samples(self) -> None:
        """Test SimulationDistribution calculates statistics from samples."""
        from services.business_case_simulation import SimulationDistribution

        roi_samples = [100.0, 120.0, 140.0, 160.0, 180.0]
        payback_samples = [4.0, 5.0, 6.0, 7.0, 8.0]

        dist = SimulationDistribution(
            roi_samples=roi_samples,
            payback_samples=payback_samples,
        )

        # Should calculate statistics
        dist._calculate_statistics()

        assert dist.simulation_runs == 5
        assert dist.roi_min == 100.0
        assert dist.roi_max == 180.0
        assert dist.payback_min == 4.0
        assert dist.payback_max == 8.0

    def test_percentile_calculation_p50(self) -> None:
        """Test P50 (median) calculation."""
        from services.business_case_simulation import SimulationDistribution

        # With 5 samples, P50 should be the middle value
        roi_samples = [100.0, 120.0, 140.0, 160.0, 180.0]

        dist = SimulationDistribution(roi_samples=roi_samples)
        dist._calculate_statistics()

        # P50 of [100, 120, 140, 160, 180] = 140
        assert dist.roi_p50 == 140.0

    def test_percentile_calculation_p80(self) -> None:
        """Test P80 calculation."""
        from services.business_case_simulation import SimulationDistribution

        roi_samples = list(range(0, 101, 10))  # [0, 10, 20, ..., 100]

        dist = SimulationDistribution(roi_samples=[float(x) for x in roi_samples])
        dist._calculate_statistics()

        # P80 should be around 80
        assert 75.0 <= dist.roi_p80 <= 85.0

    def test_mean_calculation(self) -> None:
        """Test mean calculation."""
        from services.business_case_simulation import SimulationDistribution

        roi_samples = [100.0, 200.0, 300.0]

        dist = SimulationDistribution(roi_samples=roi_samples)
        dist._calculate_statistics()

        assert dist.roi_mean == 200.0

    def test_std_calculation(self) -> None:
        """Test standard deviation calculation."""
        from services.business_case_simulation import SimulationDistribution

        # Known std for [2, 4, 4, 4, 5, 5, 7, 9] = 2.138...
        roi_samples = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]

        dist = SimulationDistribution(roi_samples=roi_samples)
        dist._calculate_statistics()

        assert 2.0 <= dist.roi_std <= 2.5

    def test_confidence_interval_80(self) -> None:
        """Test 80% confidence interval calculation."""
        from services.business_case_simulation import SimulationDistribution

        roi_samples = list(range(0, 101))  # 0 to 100

        dist = SimulationDistribution(roi_samples=[float(x) for x in roi_samples])
        dist._calculate_statistics()

        ci = dist.roi_confidence_interval_80
        assert ci[0] < ci[1]  # Lower < Upper
        assert 5.0 <= ci[0] <= 15.0  # P10 around 10
        assert 85.0 <= ci[1] <= 95.0  # P90 around 90

    def test_to_dict_serialization(self) -> None:
        """Test SimulationDistribution serialization."""
        from services.business_case_simulation import SimulationDistribution

        dist = SimulationDistribution(
            roi_samples=[100.0, 150.0, 200.0],
            payback_samples=[3.0, 4.0, 5.0],
        )
        dist._calculate_statistics()

        result = dist.to_dict()

        assert "roi" in result
        assert "payback" in result
        assert result["simulation_runs"] == 3

    def test_from_dict_deserialization(self) -> None:
        """Test SimulationDistribution deserialization."""
        from services.business_case_simulation import SimulationDistribution

        data = {
            "roi": {"p50": 150.0, "p80": 180.0, "p90": 200.0, "min": 100.0, "max": 250.0, "mean": 155.0, "std": 30.0, "p20": 120.0},
            "payback": {"p50": 5.0, "p80": 6.0, "p90": 7.0, "min": 3.0, "max": 10.0, "mean": 5.5, "std": 1.5, "p20": 4.0},
            "simulation_runs": 1000,
        }

        dist = SimulationDistribution.from_dict(data)

        assert dist.roi_p50 == 150.0
        assert dist.roi_p80 == 180.0
        assert dist.payback_p50 == 5.0
        assert dist.simulation_runs == 1000


# =============================================================================
# TEST: Data Structures - BusinessCaseSimulationReport
# =============================================================================

class TestBusinessCaseSimulationReport:
    """Tests for BusinessCaseSimulationReport dataclass."""

    def test_basic_creation(self) -> None:
        """Test BusinessCaseSimulationReport can be created."""
        from services.business_case_simulation import BusinessCaseSimulationReport

        report = BusinessCaseSimulationReport(
            size_label="team",
            risk_grade="C",
            simulation_runs=1000,
        )

        assert report.size_label == "team"
        assert report.risk_grade == "C"
        assert report.simulation_runs == 1000

    def test_is_simulation_valid_property(self) -> None:
        """Test is_simulation_valid property."""
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution(
            roi_samples=[100.0, 150.0, 200.0],
        )
        dist._calculate_statistics()

        report = BusinessCaseSimulationReport(distribution=dist)

        assert report.is_simulation_valid is True

    def test_variance_level_low(self) -> None:
        """Test variance_level returns 'low' for low CV."""
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        # Low variance: std / mean < 0.2
        dist = SimulationDistribution()
        dist.roi_mean = 100.0
        dist.roi_std = 10.0  # CV = 0.1

        report = BusinessCaseSimulationReport(distribution=dist)

        assert report.variance_level == "low"

    def test_variance_level_medium(self) -> None:
        """Test variance_level returns 'medium' for medium CV."""
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_mean = 100.0
        dist.roi_std = 35.0  # CV = 0.35

        report = BusinessCaseSimulationReport(distribution=dist)

        assert report.variance_level == "medium"

    def test_variance_level_high(self) -> None:
        """Test variance_level returns 'high' for high CV."""
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_mean = 100.0
        dist.roi_std = 60.0  # CV = 0.6

        report = BusinessCaseSimulationReport(distribution=dist)

        assert report.variance_level == "high"

    def test_to_dict_serialization(self) -> None:
        """Test BusinessCaseSimulationReport serialization."""
        from services.business_case_simulation import BusinessCaseSimulationReport

        report = BusinessCaseSimulationReport(
            size_label="kmu",
            risk_grade="B",
            simulation_runs=500,
        )

        result = report.to_dict()

        assert result["size_label"] == "kmu"
        assert result["risk_grade"] == "B"
        assert result["simulation_runs"] == 500


# =============================================================================
# TEST: Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""

    def test_percentile_calculation(self) -> None:
        """Test _percentile function."""
        from services.business_case_simulation import _percentile

        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        p50 = _percentile(data, 50)
        assert 5.0 <= p50 <= 6.0

        p0 = _percentile(data, 0)
        assert p0 == 1.0

        p100 = _percentile(data, 100)
        assert p100 == 10.0

    def test_percentile_empty_list(self) -> None:
        """Test _percentile with empty list."""
        from services.business_case_simulation import _percentile

        result = _percentile([], 50)
        assert result == 0.0

    def test_percentile_single_element(self) -> None:
        """Test _percentile with single element."""
        from services.business_case_simulation import _percentile

        result = _percentile([42.0], 50)
        assert result == 42.0

    def test_calculate_std(self) -> None:
        """Test _calculate_std function."""
        from services.business_case_simulation import _calculate_std

        data = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        mean = sum(data) / len(data)

        std = _calculate_std(data, mean)
        assert 2.0 <= std <= 2.2  # Known std ≈ 2.138

    def test_calculate_std_single_element(self) -> None:
        """Test _calculate_std with single element."""
        from services.business_case_simulation import _calculate_std

        result = _calculate_std([5.0], 5.0)
        assert result == 0.0

    def test_triangular_sample(self) -> None:
        """Test _triangular_sample returns values in range."""
        from services.business_case_simulation import _triangular_sample

        for _ in range(100):
            result = _triangular_sample(10.0, 50.0, 100.0)
            assert 10.0 <= result <= 100.0

    def test_triangular_sample_equal_bounds(self) -> None:
        """Test _triangular_sample with equal min/max."""
        from services.business_case_simulation import _triangular_sample

        result = _triangular_sample(50.0, 50.0, 50.0)
        assert result == 50.0

    def test_uniform_sample(self) -> None:
        """Test _uniform_sample returns values in range."""
        from services.business_case_simulation import _uniform_sample

        for _ in range(100):
            result = _uniform_sample(0.0, 100.0)
            assert 0.0 <= result <= 100.0

    def test_determine_size_label(self) -> None:
        """Test _determine_size_label function."""
        from services.business_case_simulation import _determine_size_label

        assert _determine_size_label({"unternehmensgroesse": "solo"}) == "solo"
        assert _determine_size_label({"unternehmensgroesse": "freiberufler"}) == "solo"
        # Phase 5A: "team" now maps to "small" (questionnaire alignment)
        assert _determine_size_label({"unternehmensgroesse": "team"}) == "small"
        assert _determine_size_label({"unternehmensgroesse": "klein"}) == "small"
        # Phase 5A: "kmu" now maps to "medium" (questionnaire alignment)
        assert _determine_size_label({"unternehmensgroesse": "kmu"}) == "medium"
        assert _determine_size_label({"unternehmensgroesse": "mittel"}) == "medium"
        assert _determine_size_label(None) == "small"  # Default is now "small"


# =============================================================================
# TEST: Assumption Generation
# =============================================================================

class TestAssumptionGeneration:
    """Tests for assumption generation from G30 baseline."""

    def test_generate_default_assumptions_basic(self) -> None:
        """Test generate_default_assumptions with basic business case."""
        from services.business_case_simulation import generate_default_assumptions
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs

        bc = BusinessCaseReport(
            investment_total=10000.0,
            scenarios=[
                ScenarioKPIs(name="optimistic", roi_12m=200.0, payback_months=4.0,
                            monthly_savings=3500.0, annual_savings=42000.0, investment_total=8000.0),
                ScenarioKPIs(name="realistic", roi_12m=150.0, payback_months=6.0,
                            monthly_savings=2500.0, annual_savings=30000.0, investment_total=10000.0),
                ScenarioKPIs(name="conservative", roi_12m=80.0, payback_months=10.0,
                            monthly_savings=1500.0, annual_savings=18000.0, investment_total=12000.0),
            ],
        )

        assumptions = generate_default_assumptions(bc)

        assert assumptions.is_valid
        assert assumptions.monthly_savings_mode == 2500.0  # From realistic
        assert assumptions.monthly_savings_min == 1500.0  # From conservative
        assert assumptions.monthly_savings_max == 3500.0  # From optimistic

    def test_generate_default_assumptions_risk_adjustment(self) -> None:
        """Test assumptions are adjusted based on risk grade."""
        from services.business_case_simulation import generate_default_assumptions
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs
        from dataclasses import dataclass

        @dataclass
        class MockRiskReport:
            residual_risk_grade: str = "D"
            residual_risk_score: float = 75.0

        bc = BusinessCaseReport(
            investment_total=10000.0,
            scenarios=[
                ScenarioKPIs(name="optimistic", roi_12m=200.0, payback_months=4.0,
                            monthly_savings=3000.0, annual_savings=36000.0, investment_total=8000.0),
                ScenarioKPIs(name="realistic", roi_12m=150.0, payback_months=6.0,
                            monthly_savings=2000.0, annual_savings=24000.0, investment_total=10000.0),
                ScenarioKPIs(name="conservative", roi_12m=80.0, payback_months=10.0,
                            monthly_savings=1000.0, annual_savings=12000.0, investment_total=12000.0),
            ],
        )

        assumptions = generate_default_assumptions(bc, risk_report_v3=MockRiskReport())

        # High risk should result in lower risk_factor
        assert assumptions.risk_factor_mode < 1.0

    def test_generate_default_assumptions_size_solo(self) -> None:
        """Test assumptions adjusted for solo company size."""
        from services.business_case_simulation import generate_default_assumptions
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs

        bc = BusinessCaseReport(
            investment_total=2000.0,
            scenarios=[
                ScenarioKPIs(name="optimistic", roi_12m=180.0, payback_months=3.0,
                            monthly_savings=1000.0, annual_savings=12000.0, investment_total=1500.0),
                ScenarioKPIs(name="realistic", roi_12m=120.0, payback_months=5.0,
                            monthly_savings=600.0, annual_savings=7200.0, investment_total=2000.0),
                ScenarioKPIs(name="conservative", roi_12m=60.0, payback_months=8.0,
                            monthly_savings=400.0, annual_savings=4800.0, investment_total=2500.0),
            ],
        )

        assumptions = generate_default_assumptions(bc, size_label="solo")

        # Solo should have wider variance
        assert assumptions.is_valid


# =============================================================================
# TEST: LLM Response Parsing
# =============================================================================

class TestLLMResponseParsing:
    """Tests for LLM response parsing."""

    def test_parse_llm_assumptions_valid_json(self) -> None:
        """Test parsing valid LLM JSON response."""
        from services.business_case_simulation import parse_llm_assumptions

        json_str = json.dumps({
            "assumptions": {
                "monthly_savings": {"min": 1000, "mode": 2000, "max": 3000},
                "investment_total": {"min": 5000, "mode": 8000, "max": 12000},
                "speed_factor": {"min": 0.7, "mode": 1.0, "max": 1.2},
                "risk_factor": {"min": 0.8, "mode": 1.0, "max": 1.1},
                "funding_success_probability": 0.5,
            }
        })

        result = parse_llm_assumptions(json_str)

        assert result is not None
        assert result.monthly_savings_min == 1000.0
        assert result.monthly_savings_mode == 2000.0
        assert result.monthly_savings_max == 3000.0

    def test_parse_llm_assumptions_without_wrapper(self) -> None:
        """Test parsing JSON without 'assumptions' wrapper."""
        from services.business_case_simulation import parse_llm_assumptions

        json_str = json.dumps({
            "monthly_savings": {"min": 500, "mode": 1000, "max": 1500},
            "investment_total": {"min": 2000, "mode": 3000, "max": 4000},
        })

        result = parse_llm_assumptions(json_str)

        assert result is not None
        assert result.monthly_savings_mode == 1000.0

    def test_parse_llm_assumptions_invalid_json(self) -> None:
        """Test parsing invalid JSON returns None."""
        from services.business_case_simulation import parse_llm_assumptions

        result = parse_llm_assumptions("not valid json {")

        assert result is None

    def test_parse_llm_assumptions_empty_string(self) -> None:
        """Test parsing empty string returns None."""
        from services.business_case_simulation import parse_llm_assumptions

        result = parse_llm_assumptions("")

        assert result is None

    def test_parse_llm_assumptions_none(self) -> None:
        """Test parsing None returns None."""
        from services.business_case_simulation import parse_llm_assumptions

        result = parse_llm_assumptions(None)  # type: ignore

        assert result is None


# =============================================================================
# TEST: Monte Carlo Simulation
# =============================================================================

class TestMonteCarloSimulation:
    """Tests for Monte Carlo simulation logic."""

    def test_run_simulation_basic(self) -> None:
        """Test basic Monte Carlo simulation runs correctly."""
        from services.business_case_simulation import (
            run_monte_carlo_simulation,
            SimulationAssumptions,
        )

        assumptions = SimulationAssumptions(
            monthly_savings_min=1000.0,
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
            investment_min=8000.0,
            investment_mode=10000.0,
            investment_max=12000.0,
        )

        result = run_monte_carlo_simulation(assumptions, runs=100)

        assert result.simulation_runs == 100
        assert len(result.roi_samples) == 100
        assert len(result.payback_samples) == 100

    def test_run_simulation_roi_within_bounds(self) -> None:
        """Test simulation ROI values are within expected bounds."""
        from services.business_case_simulation import (
            run_monte_carlo_simulation,
            SimulationAssumptions,
            MIN_ROI,
            MAX_ROI,
        )

        assumptions = SimulationAssumptions(
            monthly_savings_min=500.0,
            monthly_savings_mode=1000.0,
            monthly_savings_max=2000.0,
            investment_min=5000.0,
            investment_mode=8000.0,
            investment_max=10000.0,
        )

        result = run_monte_carlo_simulation(assumptions, runs=500)

        # All ROI values should be within bounds
        # R1-FIX: MC now uses apply_cap=False, so ROI can exceed MAX_ROI (200%)
        # up to SIMULATION_ROI_CAP (500%)
        SIMULATION_ROI_CAP = 500.0
        for roi in result.roi_samples:
            assert MIN_ROI <= roi <= SIMULATION_ROI_CAP

    def test_run_simulation_payback_positive(self) -> None:
        """Test simulation payback values are positive."""
        from services.business_case_simulation import (
            run_monte_carlo_simulation,
            SimulationAssumptions,
        )

        assumptions = SimulationAssumptions(
            monthly_savings_min=1000.0,
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
            investment_min=5000.0,
            investment_mode=8000.0,
            investment_max=10000.0,
        )

        result = run_monte_carlo_simulation(assumptions, runs=200)

        # All payback values should be positive
        for payback in result.payback_samples:
            assert payback > 0

    def test_run_simulation_with_funding_effect(self) -> None:
        """Test simulation with funding effect applied."""
        from services.business_case_simulation import (
            run_monte_carlo_simulation,
            SimulationAssumptions,
        )

        assumptions = SimulationAssumptions(
            monthly_savings_min=1000.0,
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
            investment_min=10000.0,
            investment_mode=15000.0,
            investment_max=20000.0,
            funding_success_probability=1.0,  # Always apply funding
        )

        result_with_funding = run_monte_carlo_simulation(
            assumptions, funding_effect_base=5000.0, runs=100
        )

        # With 100% funding success, effective investment should be lower
        # resulting in higher ROI on average
        assert result_with_funding.roi_mean > 0

    def test_run_simulation_min_runs_enforced(self) -> None:
        """Test minimum simulation runs is enforced."""
        from services.business_case_simulation import (
            run_monte_carlo_simulation,
            SimulationAssumptions,
            MIN_SIMULATION_RUNS,
        )

        assumptions = SimulationAssumptions(
            monthly_savings_min=1000.0,
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
            investment_min=5000.0,
            investment_mode=8000.0,
            investment_max=10000.0,
        )

        result = run_monte_carlo_simulation(assumptions, runs=10)  # Below minimum

        assert result.simulation_runs >= MIN_SIMULATION_RUNS

    def test_run_simulation_max_runs_enforced(self) -> None:
        """Test maximum simulation runs is enforced."""
        from services.business_case_simulation import (
            run_monte_carlo_simulation,
            SimulationAssumptions,
            MAX_SIMULATION_RUNS,
        )

        assumptions = SimulationAssumptions(
            monthly_savings_min=1000.0,
            monthly_savings_mode=2000.0,
            monthly_savings_max=3000.0,
            investment_min=5000.0,
            investment_mode=8000.0,
            investment_max=10000.0,
        )

        result = run_monte_carlo_simulation(assumptions, runs=100000)  # Above max

        assert result.simulation_runs <= MAX_SIMULATION_RUNS


# =============================================================================
# TEST: Main Generation Function
# =============================================================================

class TestGenerateBusinessCaseSimulation:
    """Tests for main simulation generation function."""

    def test_generate_simulation_basic(self) -> None:
        """Test basic simulation generation."""
        from services.business_case_simulation import generate_business_case_simulation
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs

        bc = BusinessCaseReport(
            investment_total=10000.0,
            scenarios=[
                ScenarioKPIs(name="optimistic", roi_12m=200.0, payback_months=4.0,
                            monthly_savings=3000.0, annual_savings=36000.0, investment_total=8000.0),
                ScenarioKPIs(name="realistic", roi_12m=150.0, payback_months=6.0,
                            monthly_savings=2000.0, annual_savings=24000.0, investment_total=10000.0),
                ScenarioKPIs(name="conservative", roi_12m=80.0, payback_months=10.0,
                            monthly_savings=1000.0, annual_savings=12000.0, investment_total=12000.0),
            ],
        )

        result = generate_business_case_simulation(business_case=bc, runs=100)

        assert result.is_simulation_valid
        assert result.distribution.simulation_runs == 100
        assert result.baseline_report == bc

    def test_generate_simulation_without_baseline(self) -> None:
        """Test simulation generation without baseline creates empty report."""
        from services.business_case_simulation import generate_business_case_simulation

        result = generate_business_case_simulation(runs=100)

        # Should still work but with default assumptions
        assert result is not None

    def test_generate_simulation_with_briefing(self) -> None:
        """Test simulation uses briefing data."""
        from services.business_case_simulation import generate_business_case_simulation
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs

        bc = BusinessCaseReport(
            investment_total=5000.0,
            scenarios=[
                ScenarioKPIs(name="optimistic", roi_12m=180.0, payback_months=3.0,
                            monthly_savings=2000.0, annual_savings=24000.0, investment_total=4000.0),
                ScenarioKPIs(name="realistic", roi_12m=120.0, payback_months=5.0,
                            monthly_savings=1500.0, annual_savings=18000.0, investment_total=5000.0),
                ScenarioKPIs(name="conservative", roi_12m=60.0, payback_months=8.0,
                            monthly_savings=1000.0, annual_savings=12000.0, investment_total=6000.0),
            ],
        )

        briefing = {"unternehmensgroesse": "solo", "language": "en"}

        result = generate_business_case_simulation(
            business_case=bc,
            briefing=briefing,
            runs=100,
        )

        assert result.size_label == "solo"

    def test_generate_simulation_narrative_generated(self) -> None:
        """Test simulation generates narrative summary."""
        from services.business_case_simulation import generate_business_case_simulation
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs

        bc = BusinessCaseReport(
            investment_total=10000.0,
            scenarios=[
                ScenarioKPIs(name="optimistic", roi_12m=200.0, payback_months=4.0,
                            monthly_savings=3000.0, annual_savings=36000.0, investment_total=8000.0),
                ScenarioKPIs(name="realistic", roi_12m=150.0, payback_months=6.0,
                            monthly_savings=2000.0, annual_savings=24000.0, investment_total=10000.0),
                ScenarioKPIs(name="conservative", roi_12m=80.0, payback_months=10.0,
                            monthly_savings=1000.0, annual_savings=12000.0, investment_total=12000.0),
            ],
        )

        result = generate_business_case_simulation(business_case=bc, runs=100)

        assert len(result.narrative_summary) > 0


# =============================================================================
# TEST: HTML Generation
# =============================================================================

class TestHTMLGeneration:
    """Tests for HTML generation."""

    def test_html_generation_basic(self) -> None:
        """Test basic HTML generation."""
        from services.business_case_simulation import (
            business_case_simulation_to_html,
            BusinessCaseSimulationReport,
            SimulationDistribution,
            SimulationAssumptions,
        )
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs

        dist = SimulationDistribution()
        dist.roi_p50 = 150.0
        dist.roi_p80 = 180.0
        dist.roi_p90 = 200.0
        dist.roi_p20 = 100.0
        dist.roi_min = 80.0
        dist.roi_max = 250.0
        dist.roi_std = 30.0
        dist.payback_p50 = 6.0
        dist.payback_p80 = 7.0
        dist.payback_p90 = 8.0
        dist.payback_p20 = 5.0
        dist.payback_min = 3.0
        dist.payback_max = 12.0
        dist.simulation_runs = 1000

        bc = BusinessCaseReport(
            scenarios=[
                ScenarioKPIs(name="realistic", roi_12m=150.0, payback_months=6.0,
                            monthly_savings=2000.0, annual_savings=24000.0, investment_total=10000.0),
            ]
        )

        report = BusinessCaseSimulationReport(
            baseline_report=bc,
            distribution=dist,
            assumptions=SimulationAssumptions(
                monthly_savings_min=1000.0,
                monthly_savings_mode=2000.0,
                monthly_savings_max=3000.0,
            ),
            narrative_summary="Test narrative",
        )

        html = business_case_simulation_to_html(report, lang="de")

        assert "150" in html  # P50 ROI
        assert "P50" in html or "Median" in html
        assert "P80" in html
        assert "P90" in html
        assert "business-case-simulation" in html

    def test_html_generation_english(self) -> None:
        """Test HTML generation in English."""
        from services.business_case_simulation import (
            business_case_simulation_to_html,
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_p50 = 120.0
        dist.payback_p50 = 5.0
        dist.simulation_runs = 500

        report = BusinessCaseSimulationReport(distribution=dist)

        html = business_case_simulation_to_html(report, lang="en")

        # Check for English labels
        assert "months" in html or "Months" in html

    def test_html_contains_percentile_table(self) -> None:
        """Test HTML contains percentile table."""
        from services.business_case_simulation import (
            business_case_simulation_to_html,
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_p50 = 150.0
        dist.roi_p80 = 180.0
        dist.roi_p90 = 200.0
        dist.roi_p20 = 100.0
        dist.payback_p50 = 6.0
        dist.payback_p80 = 7.0
        dist.payback_p90 = 8.0
        dist.payback_p20 = 5.0
        dist.simulation_runs = 1000

        report = BusinessCaseSimulationReport(distribution=dist)

        html = business_case_simulation_to_html(report)

        assert "<table" in html
        assert "</table>" in html

    def test_html_contains_assumptions_section(self) -> None:
        """Test HTML contains assumptions section."""
        from services.business_case_simulation import (
            business_case_simulation_to_html,
            BusinessCaseSimulationReport,
            SimulationAssumptions,
        )

        report = BusinessCaseSimulationReport(
            assumptions=SimulationAssumptions(
                monthly_savings_min=1000.0,
                monthly_savings_mode=2000.0,
                monthly_savings_max=3000.0,
            )
        )

        html = business_case_simulation_to_html(report)

        # Should mention assumptions values
        assert "1.000" in html or "1,000" in html or "1000" in html


# =============================================================================
# TEST: Consistency Rules Integration
# =============================================================================

class TestConsistencyRules:
    """Tests for BCSIM_001-BCSIM_006 consistency rules."""

    def test_bcsim_001_p50_near_realistic(self) -> None:
        """Test BCSIM_001: P50 ROI should be near realistic scenario."""
        from services.consistency_engine import ConsistencyEngine
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_p50 = 100.0  # 33% deviation from 150
        dist.roi_p80 = 120.0
        dist.simulation_runs = 1000

        sections = {
            "BUSINESS_CASE_SIM_HTML": "<div>P50 ROI: 100%</div>",
            "BUSINESS_CASE_ENGINE_HTML": """
                <div>optimistic ROI: 200%</div>
                <div>realistic ROI: 150%</div>
                <div>conservative ROI: 80%</div>
            """,
            "_business_case_simulation_report": BusinessCaseSimulationReport(distribution=dist),
        }

        engine = ConsistencyEngine(sections, {})
        engine._check_business_case_simulation_consistency()

        # Should find BCSIM_001 issue due to >25% deviation
        bcsim_001_issues = [i for i in engine.report.issues if i.rule_id == "BCSIM_001"]
        assert len(bcsim_001_issues) >= 1

    def test_bcsim_002_p80_above_conservative(self) -> None:
        """Test BCSIM_002: P80 ROI should not be below conservative."""
        from services.consistency_engine import ConsistencyEngine
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_p50 = 150.0
        dist.roi_p80 = 50.0  # Below conservative (80)
        dist.simulation_runs = 1000

        sections = {
            "BUSINESS_CASE_SIM_HTML": "<div>P80 ROI: 50%</div>",
            "BUSINESS_CASE_ENGINE_HTML": """
                <div>optimistic ROI: 200%</div>
                <div>realistic ROI: 150%</div>
                <div>conservative ROI: 80%</div>
            """,
            "_business_case_simulation_report": BusinessCaseSimulationReport(distribution=dist),
        }

        engine = ConsistencyEngine(sections, {})
        engine._check_business_case_simulation_consistency()

        bcsim_002_issues = [i for i in engine.report.issues if i.rule_id == "BCSIM_002"]
        assert len(bcsim_002_issues) >= 1

    def test_bcsim_004_negative_payback_error(self) -> None:
        """Test BCSIM_004: Negative payback should trigger error."""
        from services.consistency_engine import ConsistencyEngine
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_p50 = 150.0
        dist.roi_p80 = 180.0
        dist.payback_p50 = -5.0  # Negative!
        dist.simulation_runs = 1000

        sections = {
            "BUSINESS_CASE_SIM_HTML": "<div>Payback P50: -5 months</div>",
            "BUSINESS_CASE_ENGINE_HTML": "<div>realistic ROI: 150%</div>",
            "_business_case_simulation_report": BusinessCaseSimulationReport(distribution=dist),
        }

        engine = ConsistencyEngine(sections, {})
        engine._check_business_case_simulation_consistency()

        bcsim_004_issues = [i for i in engine.report.issues if i.rule_id == "BCSIM_004"]
        assert any(i.severity == "ERROR" for i in bcsim_004_issues)

    def test_bcsim_005_high_risk_variance(self) -> None:
        """Test BCSIM_005: High risk should have wider variance."""
        from services.consistency_engine import ConsistencyEngine
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_p50 = 150.0
        dist.roi_p80 = 180.0
        dist.roi_mean = 150.0
        dist.roi_std = 10.0  # Very low variance (CV = 0.067)
        dist.simulation_runs = 1000

        sections = {
            "BUSINESS_CASE_SIM_HTML": "<div>ROI: 150%</div>",
            "BUSINESS_CASE_ENGINE_HTML": "<div>realistic ROI: 150%</div>",
            "RISK_ENGINE_V3_HTML": "<div>Risk Grade: D</div>",  # High risk
            "_business_case_simulation_report": BusinessCaseSimulationReport(distribution=dist),
        }

        engine = ConsistencyEngine(sections, {})
        engine._check_business_case_simulation_consistency()

        bcsim_005_issues = [i for i in engine.report.issues if i.rule_id == "BCSIM_005"]
        assert len(bcsim_005_issues) >= 1

    def test_consistency_rules_pass_valid_data(self) -> None:
        """Test consistency rules pass with valid, consistent data."""
        from services.consistency_engine import ConsistencyEngine
        from services.business_case_simulation import (
            BusinessCaseSimulationReport,
            SimulationDistribution,
        )

        dist = SimulationDistribution()
        dist.roi_p50 = 150.0  # Close to realistic (150)
        dist.roi_p80 = 180.0
        dist.roi_p90 = 200.0
        dist.roi_p20 = 100.0
        dist.payback_p50 = 6.0
        dist.roi_mean = 155.0
        dist.roi_std = 45.0  # Medium variance (CV ≈ 0.29)
        dist.simulation_runs = 1000

        sections = {
            "BUSINESS_CASE_SIM_HTML": "<div>P50 ROI: 150%</div>",
            "BUSINESS_CASE_ENGINE_HTML": """
                <div>optimistic ROI: 200%</div>
                <div>realistic ROI: 150%</div>
                <div>conservative ROI: 80%</div>
            """,
            "RISK_ENGINE_V3_HTML": "<div>Risk Grade: C</div>",
            "_business_case_simulation_report": BusinessCaseSimulationReport(distribution=dist),
        }

        engine = ConsistencyEngine(sections, {})
        engine._check_business_case_simulation_consistency()

        # Should have no or few issues
        error_issues = [i for i in engine.report.issues if i.severity == "ERROR"]
        assert len(error_issues) == 0


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_simulation_with_zero_savings(self) -> None:
        """Test simulation handles zero savings gracefully."""
        from services.business_case_simulation import (
            run_monte_carlo_simulation,
            SimulationAssumptions,
        )

        assumptions = SimulationAssumptions(
            monthly_savings_min=0.0,
            monthly_savings_mode=0.0,
            monthly_savings_max=0.0,
            investment_min=5000.0,
            investment_mode=8000.0,
            investment_max=10000.0,
        )

        # Should not crash
        result = run_monte_carlo_simulation(assumptions, runs=100)
        assert result is not None

    def test_simulation_with_very_high_investment(self) -> None:
        """Test simulation with very high investment values."""
        from services.business_case_simulation import (
            run_monte_carlo_simulation,
            SimulationAssumptions,
        )

        assumptions = SimulationAssumptions(
            monthly_savings_min=5000.0,
            monthly_savings_mode=10000.0,
            monthly_savings_max=20000.0,
            investment_min=500000.0,
            investment_mode=1000000.0,
            investment_max=2000000.0,
        )

        result = run_monte_carlo_simulation(assumptions, runs=100)

        # Should calculate negative ROI (investment > savings)
        assert result.roi_min < 0

    def test_html_generation_empty_report(self) -> None:
        """Test HTML generation with empty report."""
        from services.business_case_simulation import (
            business_case_simulation_to_html,
            BusinessCaseSimulationReport,
        )

        report = BusinessCaseSimulationReport()

        # Should not crash
        html = business_case_simulation_to_html(report)
        assert "business-case-simulation" in html

    def test_generate_narrative_german(self) -> None:
        """Test narrative generation in German."""
        from services.business_case_simulation import (
            generate_narrative_summary,
            SimulationDistribution,
            SimulationAssumptions,
        )
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs

        dist = SimulationDistribution()
        dist.roi_p50 = 150.0
        dist.roi_std = 30.0
        dist.payback_p50 = 6.0

        bc = BusinessCaseReport(
            scenarios=[
                ScenarioKPIs(name="realistic", roi_12m=150.0, payback_months=6.0,
                            monthly_savings=2000.0, annual_savings=24000.0, investment_total=10000.0),
            ]
        )

        narrative = generate_narrative_summary(dist, bc, SimulationAssumptions(), lang="de")

        # Should contain German text
        assert "Monte-Carlo" in narrative or "Simulation" in narrative

    def test_generate_narrative_english(self) -> None:
        """Test narrative generation in English."""
        from services.business_case_simulation import (
            generate_narrative_summary,
            SimulationDistribution,
            SimulationAssumptions,
        )
        from services.business_case_engine_v2 import BusinessCaseReport, ScenarioKPIs

        dist = SimulationDistribution()
        dist.roi_p50 = 150.0
        dist.roi_std = 30.0
        dist.payback_p50 = 6.0

        bc = BusinessCaseReport(
            scenarios=[
                ScenarioKPIs(name="realistic", roi_12m=150.0, payback_months=6.0,
                            monthly_savings=2000.0, annual_savings=24000.0, investment_total=10000.0),
            ]
        )

        narrative = generate_narrative_summary(dist, bc, SimulationAssumptions(), lang="en")

        # Should contain English text
        assert "Monte Carlo" in narrative or "simulation" in narrative
