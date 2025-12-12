"""
Tests for N4.5 ROI Specialist Agent.

Tests cover:
- Investment recommendation enum
- Simulation scenario enum
- Misalignment type enum
- Data structures
- ROISpecialistAgent behavior
- Module functions
"""

import pytest
from typing import Dict, Any

from services.expert_agents.roi_specialist_agent import (
    InvestmentRecommendation,
    SimulationScenario,
    MisalignmentType,
    ROIMetrics,
    SimulationResult,
    MisalignmentFinding,
    ROISpecialistFinding,
    ROISpecialistAgent,
    run_roi_analysis,
    detect_misalignment,
    apply_financial_truth_filter,
    MOCK_ROI_DATA,
)
from services.expert_agents.expert_orchestrator import (
    ExpertType,
    ExpertStatus,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample company briefing."""
    return {
        "company_name": "Test GmbH",
        "industry": "Technology",
    }


@pytest.fixture
def sample_metrics() -> ROIMetrics:
    """Sample ROI metrics."""
    return ROIMetrics(
        baseline_roi=0.15,
        projected_roi=0.35,
        payback_months=18,
        npv=500000.0,
        irr=0.25,
        total_investment=1000000.0,
        annual_savings=400000.0,
        confidence_level=0.8,
    )


@pytest.fixture
def sample_simulation() -> SimulationResult:
    """Sample simulation result."""
    return SimulationResult(
        scenario=SimulationScenario.P50,
        roi=0.30,
        probability=0.5,
        assumptions=["Adoption rate 75%"],
        risks=["Integration delays"],
    )


@pytest.fixture
def sample_misalignment() -> MisalignmentFinding:
    """Sample misalignment finding."""
    return MisalignmentFinding(
        misalignment_type=MisalignmentType.TIMELINE_OPTIMISM,
        description="Timeline is too optimistic",
        impact="Delayed ROI realization",
        severity=0.6,
        evidence=["Industry benchmarks"],
        correction="Extend timeline by 3 months",
    )


# =============================================================================
# Test Investment Recommendation Enum
# =============================================================================


class TestInvestmentRecommendation:
    """Tests for InvestmentRecommendation enum."""

    def test_strong_invest(self):
        assert InvestmentRecommendation.STRONG_INVEST.value == "strong_invest"

    def test_invest(self):
        assert InvestmentRecommendation.INVEST.value == "invest"

    def test_conditional_invest(self):
        assert InvestmentRecommendation.CONDITIONAL_INVEST.value == "conditional_invest"

    def test_hold(self):
        assert InvestmentRecommendation.HOLD.value == "hold"

    def test_reduce(self):
        assert InvestmentRecommendation.REDUCE.value == "reduce"

    def test_divest(self):
        assert InvestmentRecommendation.DIVEST.value == "divest"


# =============================================================================
# Test Simulation Scenario Enum
# =============================================================================


class TestSimulationScenario:
    """Tests for SimulationScenario enum."""

    def test_p50(self):
        assert SimulationScenario.P50.value == "p50"

    def test_p80(self):
        assert SimulationScenario.P80.value == "p80"

    def test_p90(self):
        assert SimulationScenario.P90.value == "p90"

    def test_conservative(self):
        assert SimulationScenario.CONSERVATIVE.value == "conservative"

    def test_aggressive(self):
        assert SimulationScenario.AGGRESSIVE.value == "aggressive"


# =============================================================================
# Test Misalignment Type Enum
# =============================================================================


class TestMisalignmentType:
    """Tests for MisalignmentType enum."""

    def test_timeline_optimism(self):
        assert MisalignmentType.TIMELINE_OPTIMISM.value == "timeline_optimism"

    def test_cost_underestimate(self):
        assert MisalignmentType.COST_UNDERESTIMATE.value == "cost_underestimate"

    def test_benefit_overestimate(self):
        assert MisalignmentType.BENEFIT_OVERESTIMATE.value == "benefit_overestimate"

    def test_risk_ignored(self):
        assert MisalignmentType.RISK_IGNORED.value == "risk_ignored"


# =============================================================================
# Test Data Structures
# =============================================================================


class TestROIMetrics:
    """Tests for ROIMetrics dataclass."""

    def test_metrics_creation(self, sample_metrics):
        assert sample_metrics.baseline_roi == 0.15
        assert sample_metrics.projected_roi == 0.35
        assert sample_metrics.payback_months == 18

    def test_metrics_confidence_clamp(self):
        metrics = ROIMetrics(
            baseline_roi=0.1,
            projected_roi=0.2,
            payback_months=12,
            npv=100000,
            irr=0.15,
            total_investment=500000,
            annual_savings=200000,
            confidence_level=1.5,
        )
        assert metrics.confidence_level == 1.0

    def test_metrics_to_dict(self, sample_metrics):
        result = sample_metrics.to_dict()
        assert result["baseline_roi"] == 0.15
        assert result["npv"] == 500000.0


class TestSimulationResult:
    """Tests for SimulationResult dataclass."""

    def test_simulation_creation(self, sample_simulation):
        assert sample_simulation.scenario == SimulationScenario.P50
        assert sample_simulation.roi == 0.30
        assert sample_simulation.probability == 0.5

    def test_simulation_to_dict(self, sample_simulation):
        result = sample_simulation.to_dict()
        assert result["scenario"] == "p50"
        assert result["probability"] == 0.5


class TestMisalignmentFinding:
    """Tests for MisalignmentFinding dataclass."""

    def test_misalignment_creation(self, sample_misalignment):
        assert sample_misalignment.misalignment_type == MisalignmentType.TIMELINE_OPTIMISM
        assert sample_misalignment.severity == 0.6

    def test_misalignment_severity_clamp(self):
        finding = MisalignmentFinding(
            misalignment_type=MisalignmentType.COST_UNDERESTIMATE,
            description="Test",
            impact="Test",
            severity=1.5,
            evidence=[],
            correction="Fix",
        )
        assert finding.severity == 1.0

    def test_misalignment_to_dict(self, sample_misalignment):
        result = sample_misalignment.to_dict()
        assert result["misalignment_type"] == "timeline_optimism"


class TestROISpecialistFinding:
    """Tests for ROISpecialistFinding dataclass."""

    def test_finding_creation(self, sample_metrics, sample_simulation, sample_misalignment):
        finding = ROISpecialistFinding(
            recommendation=InvestmentRecommendation.INVEST,
            roi_metrics=sample_metrics,
            simulation_results=[sample_simulation],
            misalignments=[sample_misalignment],
            investment_thesis="Invest based on strong ROI",
            truth_filter_adjustments=["Adjusted timeline"],
            risk_adjusted_roi=0.28,
        )
        assert finding.recommendation == InvestmentRecommendation.INVEST
        assert finding.risk_adjusted_roi == 0.28


# =============================================================================
# Test ROI Specialist Agent
# =============================================================================


class TestROISpecialistAgent:
    """Tests for ROISpecialistAgent class."""

    def test_agent_init(self, sample_briefing):
        agent = ROISpecialistAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = ROISpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.status == ExpertStatus.COMPLETED
        assert result.expert_type == ExpertType.ROI_SPECIALIST

    def test_agent_produces_findings(self, sample_briefing):
        agent = ROISpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.findings) > 0

    def test_agent_summary_generated(self, sample_briefing):
        agent = ROISpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.summary) > 0

    def test_agent_confidence(self, sample_briefing):
        agent = ROISpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert 0 <= result.confidence <= 1


# =============================================================================
# Test Module Functions
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_roi_analysis(self, sample_briefing):
        result = run_roi_analysis(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.expert_id == "roi_specialist"

    def test_detect_misalignment_overestimate(self):
        result = detect_misalignment(
            projected=100.0,
            actual=80.0,
            threshold=0.15,
        )
        assert result == MisalignmentType.BENEFIT_OVERESTIMATE

    def test_detect_misalignment_underestimate(self):
        result = detect_misalignment(
            projected=100.0,
            actual=120.0,
            threshold=0.15,
        )
        assert result == MisalignmentType.COST_UNDERESTIMATE

    def test_detect_misalignment_within_threshold(self):
        result = detect_misalignment(
            projected=100.0,
            actual=95.0,
            threshold=0.15,
        )
        assert result is None

    def test_detect_misalignment_zero_projected(self):
        result = detect_misalignment(
            projected=0.0,
            actual=100.0,
        )
        assert result is None

    def test_apply_financial_truth_filter_high_roi(self):
        result = apply_financial_truth_filter(
            roi=0.50,
            confidence=0.6,
            market_average=0.15,
        )
        assert result < 0.50

    def test_apply_financial_truth_filter_normal_roi(self):
        result = apply_financial_truth_filter(
            roi=0.20,
            confidence=0.8,
            market_average=0.15,
        )
        assert result == 0.20

    def test_mock_data_exists(self):
        assert "recommendation" in MOCK_ROI_DATA
        assert "roi_metrics" in MOCK_ROI_DATA
        assert "simulation_results" in MOCK_ROI_DATA
