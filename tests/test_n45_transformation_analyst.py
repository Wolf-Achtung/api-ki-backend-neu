"""
Tests for N4.5 Transformation Analyst Agent.

Tests cover:
- Transformation track enum
- Scenario type enum
- Change readiness enum
- Data structures
- TransformationAnalystAgent behavior
- Module functions
"""

import pytest
from typing import Dict, Any

from services.expert_agents.transformation_analyst_agent import (
    TransformationTrack,
    ScenarioType,
    ChangeReadiness,
    TransformationScenario,
    OrgChangeSignal,
    TransformationAnalystFinding,
    TransformationAnalystAgent,
    run_transformation_analysis,
    generate_scenarios,
    assess_change_readiness,
    MOCK_TRANSFORMATION_DATA,
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
def sample_scenario() -> TransformationScenario:
    """Sample transformation scenario."""
    return TransformationScenario(
        track=TransformationTrack.OPERATIONAL,
        scenario_type=ScenarioType.CONSERVATIVE,
        title="Process Excellence",
        description="Focus on automation",
        key_initiatives=["Automate workflows"],
        milestones=["Q1: Pilot"],
        risks=["Limited impact"],
        success_factors=["Process documentation"],
        timeline_months=12,
        investment_range="500k-800k",
        expected_outcomes=["30% efficiency gain"],
    )


@pytest.fixture
def sample_signal() -> OrgChangeSignal:
    """Sample org change signal."""
    return OrgChangeSignal(
        signal_type="Leadership Alignment",
        description="Executive team committed",
        impact="Positive",
        readiness=ChangeReadiness.HIGH,
        affected_areas=["Strategy"],
        mitigation="Maintain engagement",
    )


# =============================================================================
# Test Transformation Track Enum
# =============================================================================


class TestTransformationTrack:
    """Tests for TransformationTrack enum."""

    def test_operational(self):
        assert TransformationTrack.OPERATIONAL.value == "operational"

    def test_organizational(self):
        assert TransformationTrack.ORGANIZATIONAL.value == "organizational"

    def test_strategic(self):
        assert TransformationTrack.STRATEGIC.value == "strategic"

    def test_track_count(self):
        assert len(TransformationTrack) == 3


# =============================================================================
# Test Scenario Type Enum
# =============================================================================


class TestScenarioType:
    """Tests for ScenarioType enum."""

    def test_conservative(self):
        assert ScenarioType.CONSERVATIVE.value == "conservative"

    def test_moderate(self):
        assert ScenarioType.MODERATE.value == "moderate"

    def test_aggressive(self):
        assert ScenarioType.AGGRESSIVE.value == "aggressive"


# =============================================================================
# Test Change Readiness Enum
# =============================================================================


class TestChangeReadiness:
    """Tests for ChangeReadiness enum."""

    def test_high(self):
        assert ChangeReadiness.HIGH.value == "high"

    def test_moderate(self):
        assert ChangeReadiness.MODERATE.value == "moderate"

    def test_low(self):
        assert ChangeReadiness.LOW.value == "low"

    def test_resistant(self):
        assert ChangeReadiness.RESISTANT.value == "resistant"


# =============================================================================
# Test Data Structures
# =============================================================================


class TestTransformationScenario:
    """Tests for TransformationScenario dataclass."""

    def test_scenario_creation(self, sample_scenario):
        assert sample_scenario.track == TransformationTrack.OPERATIONAL
        assert sample_scenario.scenario_type == ScenarioType.CONSERVATIVE
        assert sample_scenario.timeline_months == 12

    def test_scenario_to_dict(self, sample_scenario):
        result = sample_scenario.to_dict()
        assert result["track"] == "operational"
        assert result["scenario_type"] == "conservative"


class TestOrgChangeSignal:
    """Tests for OrgChangeSignal dataclass."""

    def test_signal_creation(self, sample_signal):
        assert sample_signal.signal_type == "Leadership Alignment"
        assert sample_signal.readiness == ChangeReadiness.HIGH

    def test_signal_to_dict(self, sample_signal):
        result = sample_signal.to_dict()
        assert result["signal_type"] == "Leadership Alignment"
        assert result["readiness"] == "high"


class TestTransformationAnalystFinding:
    """Tests for TransformationAnalystFinding dataclass."""

    def test_finding_creation(self, sample_scenario, sample_signal):
        finding = TransformationAnalystFinding(
            operational_scenario=sample_scenario,
            organizational_scenario=sample_scenario,
            strategic_scenario=sample_scenario,
            change_signals=[sample_signal],
            overall_readiness=ChangeReadiness.MODERATE,
            recommended_track=TransformationTrack.ORGANIZATIONAL,
            change_enablers=["Executive support"],
            change_barriers=["Legacy systems"],
            roadmap_inputs={"priority_initiatives": []},
        )
        assert finding.overall_readiness == ChangeReadiness.MODERATE
        assert finding.recommended_track == TransformationTrack.ORGANIZATIONAL

    def test_finding_confidence_clamp(self, sample_scenario, sample_signal):
        finding = TransformationAnalystFinding(
            operational_scenario=sample_scenario,
            organizational_scenario=sample_scenario,
            strategic_scenario=sample_scenario,
            change_signals=[sample_signal],
            overall_readiness=ChangeReadiness.HIGH,
            recommended_track=TransformationTrack.STRATEGIC,
            change_enablers=[],
            change_barriers=[],
            roadmap_inputs={},
            confidence=1.5,
        )
        assert finding.confidence == 1.0


# =============================================================================
# Test Transformation Analyst Agent
# =============================================================================


class TestTransformationAnalystAgent:
    """Tests for TransformationAnalystAgent class."""

    def test_agent_init(self, sample_briefing):
        agent = TransformationAnalystAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = TransformationAnalystAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.status == ExpertStatus.COMPLETED
        assert result.expert_type == ExpertType.TRANSFORMATION_ANALYST

    def test_agent_produces_findings(self, sample_briefing):
        agent = TransformationAnalystAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.findings) > 0

    def test_agent_summary_generated(self, sample_briefing):
        agent = TransformationAnalystAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.summary) > 0

    def test_agent_produces_three_scenarios(self, sample_briefing):
        agent = TransformationAnalystAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        scenario_findings = [
            f for f in result.findings
            if "scenario" in f.finding_id.lower()
        ]
        assert len(scenario_findings) == 3


# =============================================================================
# Test Module Functions
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_transformation_analysis(self, sample_briefing):
        result = run_transformation_analysis(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.expert_id == "transformation_analyst"

    def test_generate_scenarios_strategic(self):
        track = generate_scenarios(
            readiness=ChangeReadiness.HIGH,
            enablers=["A", "B", "C", "D"],
            barriers=["X"],
        )
        assert track == TransformationTrack.STRATEGIC

    def test_generate_scenarios_organizational(self):
        track = generate_scenarios(
            readiness=ChangeReadiness.MODERATE,
            enablers=["A", "B"],
            barriers=["X", "Y"],
        )
        assert track == TransformationTrack.ORGANIZATIONAL

    def test_generate_scenarios_operational(self):
        track = generate_scenarios(
            readiness=ChangeReadiness.LOW,
            enablers=["A"],
            barriers=["X", "Y", "Z"],
        )
        assert track == TransformationTrack.OPERATIONAL

    def test_assess_change_readiness_high(self):
        result = assess_change_readiness(
            leadership_score=0.9,
            workforce_score=0.8,
            technical_score=0.85,
            cultural_score=0.75,
        )
        assert result == ChangeReadiness.HIGH

    def test_assess_change_readiness_moderate(self):
        result = assess_change_readiness(
            leadership_score=0.7,
            workforce_score=0.6,
            technical_score=0.5,
            cultural_score=0.5,
        )
        assert result == ChangeReadiness.MODERATE

    def test_assess_change_readiness_low(self):
        result = assess_change_readiness(
            leadership_score=0.4,
            workforce_score=0.3,
            technical_score=0.3,
            cultural_score=0.3,
        )
        assert result == ChangeReadiness.LOW

    def test_assess_change_readiness_resistant(self):
        result = assess_change_readiness(
            leadership_score=0.1,
            workforce_score=0.1,
            technical_score=0.1,
            cultural_score=0.1,
        )
        assert result == ChangeReadiness.RESISTANT

    def test_mock_data_exists(self):
        assert "operational_scenario" in MOCK_TRANSFORMATION_DATA
        assert "organizational_scenario" in MOCK_TRANSFORMATION_DATA
        assert "strategic_scenario" in MOCK_TRANSFORMATION_DATA
        assert "change_signals" in MOCK_TRANSFORMATION_DATA
