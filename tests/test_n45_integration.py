"""
Tests for N4.5 Integration Module.

Tests cover:
- N45ProcessResult data structure
- InjectionPayload data structure
- process_n45_experts function
- inject_expert_findings function
- validate_n45_dod function
- Helper functions
"""

import pytest
from typing import Dict, Any, List

from services.expert_agents.n45_integration import (
    N45_VERSION,
    INJECTION_TARGETS,
    N45ProcessResult,
    InjectionPayload,
    process_n45_experts,
    inject_expert_findings,
    validate_n45_dod,
    get_expert_findings_for_section,
    create_n45_block_output,
)
from services.expert_agents.expert_orchestrator import (
    ExpertType,
    ExpertStatus,
    ExpertFinding,
    ExpertResult,
    FindingPriority,
)
from services.expert_agents.knowledge_fusion_engine_v3 import (
    ExecutiveImpactSummary,
    ImpactPoint,
    ImpactCategory,
    ExpertContradiction,
    ContradictionSeverity,
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
        "employees": 500,
    }


@pytest.fixture
def sample_expert_result() -> ExpertResult:
    """Sample expert result."""
    finding = ExpertFinding(
        finding_id="RISK-001",
        expert_type=ExpertType.RISK_SPECIALIST,
        title="Risk Finding",
        content="Risk content",
        priority=FindingPriority.HIGH,
        confidence=0.85,
    )
    return ExpertResult(
        expert_id="risk_specialist",
        expert_type=ExpertType.RISK_SPECIALIST,
        status=ExpertStatus.COMPLETED,
        findings=[finding],
        summary="Risk analysis complete",
        confidence=0.85,
    )


@pytest.fixture
def sample_expert_results() -> Dict[str, ExpertResult]:
    """Sample expert results dict."""
    experts = ["risk_specialist", "roi_specialist", "benchmark_specialist",
               "governance_advisor", "transformation_analyst"]
    results = {}
    for expert_id in experts:
        finding = ExpertFinding(
            finding_id=f"{expert_id.upper()}-001",
            expert_type=ExpertType(expert_id),
            title=f"{expert_id} Finding",
            content="Content",
            priority=FindingPriority.HIGH,
            confidence=0.85,
        )
        results[expert_id] = ExpertResult(
            expert_id=expert_id,
            expert_type=ExpertType(expert_id),
            status=ExpertStatus.COMPLETED,
            findings=[finding],
            summary=f"{expert_id} complete",
            confidence=0.85,
        )
    return results


@pytest.fixture
def sample_impact_summary() -> ExecutiveImpactSummary:
    """Sample executive impact summary."""
    points = [
        ImpactPoint(
            impact_id=f"IMPACT-{i:03d}",
            category=list(ImpactCategory)[i % len(ImpactCategory)],
            headline=f"Impact point {i}",
            description=f"Description {i}",
            supporting_experts=[ExpertType.RISK_SPECIALIST],
            confidence=0.85,
            priority=i,
            action_required=i < 3,
        )
        for i in range(5)
    ]
    return ExecutiveImpactSummary(
        summary_id="SUMMARY-001",
        title="Test Summary",
        impact_points=points,
        overall_confidence=0.85,
        key_themes=["Theme 1", "Theme 2"],
        immediate_actions=["Action 1"],
        strategic_implications=["Implication 1"],
    )


@pytest.fixture
def sample_contradictions() -> List[ExpertContradiction]:
    """Sample contradictions list."""
    return [
        ExpertContradiction(
            contradiction_id="CONTRA-001",
            expert_a=ExpertType.RISK_SPECIALIST,
            expert_b=ExpertType.ROI_SPECIALIST,
            finding_a_id="A",
            finding_b_id="B",
            topic="investment",
            description="Minor difference",
            severity=ContradictionSeverity.MINOR,
            resolution="Resolved",
            confidence=0.7,
        )
    ]


# =============================================================================
# Test Constants
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_n45_version(self):
        assert N45_VERSION == "5.5.0"

    def test_injection_targets(self):
        assert "executive_summary_v6" in INJECTION_TARGETS
        assert "strategy_engine" in INJECTION_TARGETS
        assert "governance_engine" in INJECTION_TARGETS
        assert "transformation_roadmap" in INJECTION_TARGETS
        assert "risk_engine_addons" in INJECTION_TARGETS
        assert len(INJECTION_TARGETS) == 5


# =============================================================================
# Test Data Structures
# =============================================================================


class TestN45ProcessResult:
    """Tests for N45ProcessResult dataclass."""

    def test_result_creation(
        self,
        sample_expert_results,
        sample_impact_summary,
        sample_contradictions,
    ):
        result = N45ProcessResult(
            version=N45_VERSION,
            expert_results=sample_expert_results,
            fusion_result={"fused_insights": []},
            impact_summary=sample_impact_summary,
            contradictions=sample_contradictions,
            injections={},
            dod_validation={"passed": True},
            processing_time_ms=1000,
        )
        assert result.version == "5.5.0"
        assert len(result.expert_results) == 5

    def test_result_to_dict(
        self,
        sample_expert_results,
        sample_impact_summary,
        sample_contradictions,
    ):
        result = N45ProcessResult(
            version=N45_VERSION,
            expert_results=sample_expert_results,
            fusion_result={},
            impact_summary=sample_impact_summary,
            contradictions=sample_contradictions,
            injections={},
            dod_validation={},
            processing_time_ms=500,
        )
        result_dict = result.to_dict()
        assert result_dict["version"] == "5.5.0"
        assert "expert_results" in result_dict


class TestInjectionPayload:
    """Tests for InjectionPayload dataclass."""

    def test_payload_creation(self):
        payload = InjectionPayload(
            target="executive_summary_v6",
            findings=[{"id": "1", "content": "test"}],
            summary="Test summary",
            confidence=0.85,
            metadata={"key": "value"},
        )
        assert payload.target == "executive_summary_v6"
        assert len(payload.findings) == 1

    def test_payload_to_dict(self):
        payload = InjectionPayload(
            target="strategy_engine",
            findings=[],
            summary="Test",
            confidence=0.75,
        )
        result = payload.to_dict()
        assert result["target"] == "strategy_engine"
        assert result["confidence"] == 0.75


# =============================================================================
# Test Main Processing Function
# =============================================================================


class TestProcessN45Experts:
    """Tests for process_n45_experts function."""

    def test_process_mock_mode(self, sample_briefing):
        result = process_n45_experts(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert result.version == N45_VERSION
        assert len(result.expert_results) == 5

    def test_process_returns_all_experts(self, sample_briefing):
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )
        expected_experts = [
            "risk_specialist",
            "roi_specialist",
            "benchmark_specialist",
            "governance_advisor",
            "transformation_analyst",
        ]
        for expert_id in expected_experts:
            assert expert_id in result.expert_results

    def test_process_fusion_result(self, sample_briefing):
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert "fused_insights" in result.fusion_result

    def test_process_impact_summary(self, sample_briefing):
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.impact_summary is not None

    def test_process_injections_created(self, sample_briefing):
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert len(result.injections) > 0

    def test_process_dod_validation(self, sample_briefing):
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert "dod_passed" in result.dod_validation

    def test_process_with_research_signals(self, sample_briefing):
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
            research_signals={"market": {"trend": "growth"}},
        )
        assert result.version == N45_VERSION


# =============================================================================
# Test Injection Functions
# =============================================================================


class TestInjectExpertFindings:
    """Tests for inject_expert_findings function."""

    def test_inject_creates_all_targets(
        self,
        sample_expert_results,
        sample_impact_summary,
    ):
        injections = inject_expert_findings(
            expert_results=sample_expert_results,
            impact_summary=sample_impact_summary,
            language="de",
        )
        assert "executive_summary_v6" in injections
        assert "strategy_engine" in injections
        assert "governance_engine" in injections

    def test_inject_executive_summary(
        self,
        sample_expert_results,
        sample_impact_summary,
    ):
        injections = inject_expert_findings(
            expert_results=sample_expert_results,
            impact_summary=sample_impact_summary,
        )
        exec_injection = injections["executive_summary_v6"]
        assert "findings" in exec_injection
        assert "summary" in exec_injection

    def test_inject_without_impact_summary(self, sample_expert_results):
        injections = inject_expert_findings(
            expert_results=sample_expert_results,
            impact_summary=None,
        )
        assert "executive_summary_v6" in injections


# =============================================================================
# Test DoD Validation
# =============================================================================


class TestValidateN45DoD:
    """Tests for validate_n45_dod function."""

    def test_validate_all_experts_delivered(self, sample_expert_results):
        validation = validate_n45_dod(
            expert_results=sample_expert_results,
            contradictions=[],
            fusion_result={"fused_insights": [], "impact_summary": {}},
        )
        assert validation["all_experts_delivered"] is True

    def test_validate_no_expert_conflicts(self, sample_expert_results):
        validation = validate_n45_dod(
            expert_results=sample_expert_results,
            contradictions=[],
            fusion_result={"fused_insights": [], "impact_summary": {}},
        )
        assert validation["no_expert_conflicts"] is True

    def test_validate_with_critical_contradiction(self, sample_expert_results):
        critical_contradiction = ExpertContradiction(
            contradiction_id="CRITICAL-001",
            expert_a=ExpertType.RISK_SPECIALIST,
            expert_b=ExpertType.ROI_SPECIALIST,
            finding_a_id="A",
            finding_b_id="B",
            topic="test",
            description="Critical issue",
            severity=ContradictionSeverity.CRITICAL,
            resolution="",
            confidence=0.9,
        )
        validation = validate_n45_dod(
            expert_results=sample_expert_results,
            contradictions=[critical_contradiction],
            fusion_result={"fused_insights": [], "impact_summary": {}},
        )
        assert validation["no_expert_conflicts"] is False

    def test_validate_consistent_output(self, sample_expert_results):
        validation = validate_n45_dod(
            expert_results=sample_expert_results,
            contradictions=[],
            fusion_result={"fused_insights": [], "impact_summary": {}},
        )
        assert validation["consistent_json_output"] is True

    def test_validate_dod_passed(self, sample_expert_results):
        validation = validate_n45_dod(
            expert_results=sample_expert_results,
            contradictions=[],
            fusion_result={"fused_insights": [], "impact_summary": {}},
        )
        assert "dod_passed" in validation


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_expert_findings_for_section_risk(self, sample_expert_results):
        findings = get_expert_findings_for_section(
            expert_results=sample_expert_results,
            section="risk",
        )
        assert isinstance(findings, list)

    def test_get_expert_findings_for_section_strategy(self, sample_expert_results):
        findings = get_expert_findings_for_section(
            expert_results=sample_expert_results,
            section="strategy",
        )
        assert isinstance(findings, list)

    def test_get_expert_findings_for_unknown_section(self, sample_expert_results):
        findings = get_expert_findings_for_section(
            expert_results=sample_expert_results,
            section="unknown",
        )
        # Should return findings from all experts
        assert isinstance(findings, list)

    def test_create_n45_block_output(
        self,
        sample_expert_results,
        sample_impact_summary,
        sample_contradictions,
    ):
        process_result = N45ProcessResult(
            version=N45_VERSION,
            expert_results=sample_expert_results,
            fusion_result={},
            impact_summary=sample_impact_summary,
            contradictions=sample_contradictions,
            injections={"exec": {}},
            dod_validation={"dod_passed": True},
            processing_time_ms=1000,
        )
        block_output = create_n45_block_output(process_result)
        assert block_output["block_id"] == "N4_5_RUN_EXPERT_AGENTS"
        assert block_output["version"] == N45_VERSION
        assert block_output["expert_count"] == 5

    def test_create_n45_block_output_status(
        self,
        sample_expert_results,
        sample_impact_summary,
        sample_contradictions,
    ):
        # Test completed status
        process_result = N45ProcessResult(
            version=N45_VERSION,
            expert_results=sample_expert_results,
            fusion_result={},
            impact_summary=sample_impact_summary,
            contradictions=sample_contradictions,
            injections={},
            dod_validation={"dod_passed": True},
            processing_time_ms=500,
        )
        block_output = create_n45_block_output(process_result)
        assert block_output["status"] == "completed"

    def test_create_n45_block_output_warnings_status(
        self,
        sample_expert_results,
        sample_impact_summary,
        sample_contradictions,
    ):
        # Test completed_with_warnings status
        process_result = N45ProcessResult(
            version=N45_VERSION,
            expert_results=sample_expert_results,
            fusion_result={},
            impact_summary=sample_impact_summary,
            contradictions=sample_contradictions,
            injections={},
            dod_validation={"dod_passed": False},
            processing_time_ms=500,
        )
        block_output = create_n45_block_output(process_result)
        assert block_output["status"] == "completed_with_warnings"


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for N4.5 module."""

    def test_full_pipeline(self, sample_briefing):
        """Test the full N4.5 processing pipeline."""
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )

        # Verify all components
        assert result.version == N45_VERSION
        assert len(result.expert_results) == 5
        assert result.impact_summary is not None
        assert len(result.injections) > 0
        assert result.dod_validation.get("dod_passed") is True

    def test_deterministic_results(self, sample_briefing):
        """Test that mock mode produces deterministic results."""
        result1 = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result2 = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )

        # Expert counts should match
        assert len(result1.expert_results) == len(result2.expert_results)

    def test_no_contradictions_between_experts(self, sample_briefing):
        """Test that experts produce aligned results."""
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )

        # Check for critical contradictions
        critical = [
            c for c in result.contradictions
            if c.severity == ContradictionSeverity.CRITICAL
        ]
        assert len(critical) == 0

    def test_governance_advisor_compatible_output(self, sample_briefing):
        """Test that Governance Advisor output is compatible with Governance Engine v2."""
        result = process_n45_experts(
            briefing=sample_briefing,
            mock_mode=True,
        )

        gov_result = result.expert_results.get("governance_advisor")
        assert gov_result is not None
        assert gov_result.status == ExpertStatus.COMPLETED

        # Check injection payload exists
        assert "governance_engine" in result.injections
