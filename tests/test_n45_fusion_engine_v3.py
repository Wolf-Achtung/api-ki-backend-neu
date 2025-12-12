"""
Tests for N4.5 Knowledge Fusion Engine v3.

Tests cover:
- Contradiction severity enum
- Impact category enum
- Fusion strategy enum
- Data structures
- ContradictionMiner behavior
- KnowledgeFusionEngineV3 behavior
- Module functions
"""

import pytest
from typing import Dict, Any, List

from services.expert_agents.knowledge_fusion_engine_v3 import (
    ContradictionSeverity,
    ImpactCategory,
    FusionStrategy,
    ExpertContradiction,
    ImpactPoint,
    ExecutiveImpactSummary,
    FusedExpertInsight,
    ContradictionMiner,
    KnowledgeFusionEngineV3,
    fuse_expert_findings,
    mine_contradictions,
    generate_impact_summary,
)
from services.expert_agents.expert_orchestrator import (
    ExpertType,
    ExpertStatus,
    ExpertFinding,
    ExpertResult,
    FindingPriority,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_finding() -> ExpertFinding:
    """Sample expert finding."""
    return ExpertFinding(
        finding_id="TEST-001",
        expert_type=ExpertType.RISK_SPECIALIST,
        title="Critical Risk Finding",
        content="Risk identified",
        priority=FindingPriority.CRITICAL,
        confidence=0.85,
    )


@pytest.fixture
def sample_result(sample_finding) -> ExpertResult:
    """Sample expert result."""
    return ExpertResult(
        expert_id="risk_specialist",
        expert_type=ExpertType.RISK_SPECIALIST,
        status=ExpertStatus.COMPLETED,
        findings=[sample_finding],
        summary="Risk analysis complete",
        confidence=0.85,
    )


@pytest.fixture
def multiple_results() -> Dict[str, ExpertResult]:
    """Multiple expert results for testing."""
    risk_finding = ExpertFinding(
        finding_id="RISK-001",
        expert_type=ExpertType.RISK_SPECIALIST,
        title="High Risk Identified",
        content="Risk content",
        priority=FindingPriority.HIGH,
        confidence=0.8,
    )
    roi_finding = ExpertFinding(
        finding_id="ROI-001",
        expert_type=ExpertType.ROI_SPECIALIST,
        title="High Investment Return",
        content="ROI content",
        priority=FindingPriority.CRITICAL,
        confidence=0.9,
    )

    return {
        "risk_specialist": ExpertResult(
            expert_id="risk_specialist",
            expert_type=ExpertType.RISK_SPECIALIST,
            status=ExpertStatus.COMPLETED,
            findings=[risk_finding],
            confidence=0.8,
        ),
        "roi_specialist": ExpertResult(
            expert_id="roi_specialist",
            expert_type=ExpertType.ROI_SPECIALIST,
            status=ExpertStatus.COMPLETED,
            findings=[roi_finding],
            confidence=0.9,
        ),
    }


@pytest.fixture
def sample_contradiction() -> ExpertContradiction:
    """Sample expert contradiction."""
    return ExpertContradiction(
        contradiction_id="CONTRA-001",
        expert_a=ExpertType.RISK_SPECIALIST,
        expert_b=ExpertType.ROI_SPECIALIST,
        finding_a_id="RISK-001",
        finding_b_id="ROI-001",
        topic="investment",
        description="Risk vs ROI assessment differs",
        severity=ContradictionSeverity.MINOR,
        resolution="Defer to risk specialist",
        confidence=0.7,
    )


@pytest.fixture
def sample_impact_point() -> ImpactPoint:
    """Sample impact point."""
    return ImpactPoint(
        impact_id="IMPACT-001",
        category=ImpactCategory.STRATEGIC,
        headline="Strategic action required",
        description="Key strategic decision needed",
        supporting_experts=[ExpertType.BENCHMARK_SPECIALIST],
        confidence=0.85,
        priority=1,
        action_required=True,
    )


@pytest.fixture
def sample_fused_insight() -> FusedExpertInsight:
    """Sample fused insight."""
    return FusedExpertInsight(
        insight_id="FUSED-001",
        topic="AI Transformation",
        synthesis="Combined analysis shows opportunity",
        contributing_findings=["RISK-001", "ROI-001"],
        contributing_experts=[ExpertType.RISK_SPECIALIST, ExpertType.ROI_SPECIALIST],
        confidence=0.85,
        priority=FindingPriority.HIGH,
        recommendations=["Proceed with investment"],
    )


# =============================================================================
# Test Contradiction Severity Enum
# =============================================================================


class TestContradictionSeverity:
    """Tests for ContradictionSeverity enum."""

    def test_critical(self):
        assert ContradictionSeverity.CRITICAL.value == "critical"

    def test_major(self):
        assert ContradictionSeverity.MAJOR.value == "major"

    def test_minor(self):
        assert ContradictionSeverity.MINOR.value == "minor"

    def test_informational(self):
        assert ContradictionSeverity.INFORMATIONAL.value == "informational"


# =============================================================================
# Test Impact Category Enum
# =============================================================================


class TestImpactCategory:
    """Tests for ImpactCategory enum."""

    def test_strategic(self):
        assert ImpactCategory.STRATEGIC.value == "strategic"

    def test_financial(self):
        assert ImpactCategory.FINANCIAL.value == "financial"

    def test_operational(self):
        assert ImpactCategory.OPERATIONAL.value == "operational"

    def test_risk(self):
        assert ImpactCategory.RISK.value == "risk"

    def test_compliance(self):
        assert ImpactCategory.COMPLIANCE.value == "compliance"

    def test_transformation(self):
        assert ImpactCategory.TRANSFORMATION.value == "transformation"


# =============================================================================
# Test Fusion Strategy Enum
# =============================================================================


class TestFusionStrategy:
    """Tests for FusionStrategy enum."""

    def test_highest_confidence(self):
        assert FusionStrategy.HIGHEST_CONFIDENCE.value == "highest_confidence"

    def test_expert_priority(self):
        assert FusionStrategy.EXPERT_PRIORITY.value == "expert_priority"

    def test_consensus(self):
        assert FusionStrategy.CONSENSUS.value == "consensus"

    def test_weighted_average(self):
        assert FusionStrategy.WEIGHTED_AVERAGE.value == "weighted_average"


# =============================================================================
# Test Data Structures
# =============================================================================


class TestExpertContradiction:
    """Tests for ExpertContradiction dataclass."""

    def test_contradiction_creation(self, sample_contradiction):
        assert sample_contradiction.contradiction_id == "CONTRA-001"
        assert sample_contradiction.expert_a == ExpertType.RISK_SPECIALIST
        assert sample_contradiction.severity == ContradictionSeverity.MINOR

    def test_contradiction_confidence_clamp(self):
        contra = ExpertContradiction(
            contradiction_id="TEST",
            expert_a=ExpertType.RISK_SPECIALIST,
            expert_b=ExpertType.ROI_SPECIALIST,
            finding_a_id="A",
            finding_b_id="B",
            topic="test",
            description="test",
            severity=ContradictionSeverity.MINOR,
            resolution="test",
            confidence=1.5,
        )
        assert contra.confidence == 1.0

    def test_contradiction_to_dict(self, sample_contradiction):
        result = sample_contradiction.to_dict()
        assert result["contradiction_id"] == "CONTRA-001"
        assert result["severity"] == "minor"


class TestImpactPoint:
    """Tests for ImpactPoint dataclass."""

    def test_impact_point_creation(self, sample_impact_point):
        assert sample_impact_point.impact_id == "IMPACT-001"
        assert sample_impact_point.category == ImpactCategory.STRATEGIC
        assert sample_impact_point.action_required is True

    def test_impact_point_confidence_clamp(self):
        point = ImpactPoint(
            impact_id="TEST",
            category=ImpactCategory.RISK,
            headline="Test",
            description="Test",
            supporting_experts=[],
            confidence=1.5,
            priority=1,
            action_required=False,
        )
        assert point.confidence == 1.0

    def test_impact_point_to_dict(self, sample_impact_point):
        result = sample_impact_point.to_dict()
        assert result["impact_id"] == "IMPACT-001"
        assert result["category"] == "strategic"


class TestExecutiveImpactSummary:
    """Tests for ExecutiveImpactSummary dataclass."""

    def test_summary_creation(self, sample_impact_point):
        summary = ExecutiveImpactSummary(
            summary_id="SUMMARY-001",
            title="Executive Summary",
            impact_points=[sample_impact_point],
            overall_confidence=0.85,
            key_themes=["Theme 1"],
            immediate_actions=["Action 1"],
            strategic_implications=["Implication 1"],
        )
        assert summary.summary_id == "SUMMARY-001"
        assert len(summary.impact_points) == 1

    def test_summary_confidence_clamp(self):
        summary = ExecutiveImpactSummary(
            summary_id="TEST",
            title="Test",
            impact_points=[],
            overall_confidence=1.5,
            key_themes=[],
            immediate_actions=[],
            strategic_implications=[],
        )
        assert summary.overall_confidence == 1.0

    def test_summary_to_dict(self, sample_impact_point):
        summary = ExecutiveImpactSummary(
            summary_id="SUMMARY-001",
            title="Test",
            impact_points=[sample_impact_point],
            overall_confidence=0.8,
            key_themes=[],
            immediate_actions=[],
            strategic_implications=[],
        )
        result = summary.to_dict()
        assert result["summary_id"] == "SUMMARY-001"


class TestFusedExpertInsight:
    """Tests for FusedExpertInsight dataclass."""

    def test_insight_creation(self, sample_fused_insight):
        assert sample_fused_insight.insight_id == "FUSED-001"
        assert sample_fused_insight.topic == "AI Transformation"
        assert len(sample_fused_insight.contributing_experts) == 2

    def test_insight_confidence_clamp(self):
        insight = FusedExpertInsight(
            insight_id="TEST",
            topic="Test",
            synthesis="Test",
            contributing_findings=[],
            contributing_experts=[],
            confidence=1.5,
            priority=FindingPriority.MEDIUM,
            recommendations=[],
        )
        assert insight.confidence == 1.0

    def test_insight_to_dict(self, sample_fused_insight):
        result = sample_fused_insight.to_dict()
        assert result["insight_id"] == "FUSED-001"
        assert result["priority"] == "high"


# =============================================================================
# Test Contradiction Miner
# =============================================================================


class TestContradictionMiner:
    """Tests for ContradictionMiner class."""

    def test_miner_init(self):
        miner = ContradictionMiner()
        assert len(miner.get_contradictions()) == 0

    def test_miner_mine(self, multiple_results):
        miner = ContradictionMiner()
        contradictions = miner.mine(multiple_results)
        # May or may not find contradictions depending on findings
        assert isinstance(contradictions, list)

    def test_miner_get_critical_contradictions(self):
        miner = ContradictionMiner()
        miner._contradictions = [
            ExpertContradiction(
                contradiction_id="C1",
                expert_a=ExpertType.RISK_SPECIALIST,
                expert_b=ExpertType.ROI_SPECIALIST,
                finding_a_id="A",
                finding_b_id="B",
                topic="test",
                description="test",
                severity=ContradictionSeverity.CRITICAL,
                resolution="test",
                confidence=0.8,
            ),
            ExpertContradiction(
                contradiction_id="C2",
                expert_a=ExpertType.RISK_SPECIALIST,
                expert_b=ExpertType.ROI_SPECIALIST,
                finding_a_id="A",
                finding_b_id="B",
                topic="test",
                description="test",
                severity=ContradictionSeverity.MINOR,
                resolution="test",
                confidence=0.8,
            ),
        ]
        critical = miner.get_critical_contradictions()
        assert len(critical) == 1
        assert critical[0].severity == ContradictionSeverity.CRITICAL


# =============================================================================
# Test Knowledge Fusion Engine V3
# =============================================================================


class TestKnowledgeFusionEngineV3:
    """Tests for KnowledgeFusionEngineV3 class."""

    def test_engine_init(self):
        engine = KnowledgeFusionEngineV3(
            language="de",
            strategy=FusionStrategy.HIGHEST_CONFIDENCE,
        )
        assert engine.language == "de"
        assert engine.strategy == FusionStrategy.HIGHEST_CONFIDENCE

    def test_engine_add_expert_results(self, multiple_results):
        engine = KnowledgeFusionEngineV3()
        engine.add_expert_results(multiple_results)
        assert len(engine._expert_results) == 2

    def test_engine_add_research_signals(self):
        engine = KnowledgeFusionEngineV3()
        engine.add_research_signals({"market": {"signal": "growth"}})
        assert "market" in engine._research_signals

    def test_engine_fuse(self, multiple_results):
        engine = KnowledgeFusionEngineV3()
        engine.add_expert_results(multiple_results)
        result = engine.fuse()
        assert "fused_insights" in result
        assert "contradictions" in result
        assert "impact_summary" in result

    def test_engine_get_fused_insights(self, multiple_results):
        engine = KnowledgeFusionEngineV3()
        engine.add_expert_results(multiple_results)
        engine.fuse()
        insights = engine.get_fused_insights()
        assert isinstance(insights, list)

    def test_engine_get_contradictions(self, multiple_results):
        engine = KnowledgeFusionEngineV3()
        engine.add_expert_results(multiple_results)
        engine.fuse()
        contradictions = engine.get_contradictions()
        assert isinstance(contradictions, list)

    def test_engine_get_impact_summary(self, multiple_results):
        engine = KnowledgeFusionEngineV3()
        engine.add_expert_results(multiple_results)
        engine.fuse()
        summary = engine.get_impact_summary()
        assert summary is not None
        assert len(summary.impact_points) >= 3


# =============================================================================
# Test Module Functions
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_fuse_expert_findings(self, multiple_results):
        result = fuse_expert_findings(
            expert_results=multiple_results,
            language="de",
        )
        assert "fused_insights" in result
        assert "impact_summary" in result

    def test_fuse_expert_findings_with_signals(self, multiple_results):
        result = fuse_expert_findings(
            expert_results=multiple_results,
            research_signals={"market": {}},
            language="en",
        )
        assert "fused_insights" in result

    def test_mine_contradictions(self, multiple_results):
        contradictions = mine_contradictions(multiple_results)
        assert isinstance(contradictions, list)

    def test_generate_impact_summary(self, sample_fused_insight):
        summary = generate_impact_summary(
            fused_insights=[sample_fused_insight],
            language="de",
        )
        assert summary is not None
        assert len(summary.impact_points) >= 3
