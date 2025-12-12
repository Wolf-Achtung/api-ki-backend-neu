"""
Tests for N4.5 Risk Specialist Agent.

Tests cover:
- Risk grade enum
- Gap severity enum
- Control category enum
- Data structures
- RiskSpecialistAgent behavior
- Module functions
"""

import pytest
from typing import Dict, Any

from services.expert_agents.risk_specialist_agent import (
    RiskGrade,
    GapSeverity,
    ControlCategory,
    CriticalGap,
    VendorRiskHotspot,
    AIActControl,
    RiskSpecialistFinding,
    RiskSpecialistAgent,
    run_risk_analysis,
    assess_risk_grade,
    identify_control_gaps,
    MOCK_RISK_DATA,
)
from services.expert_agents.expert_orchestrator import (
    ExpertType,
    ExpertStatus,
    FindingPriority,
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
def sample_gap() -> CriticalGap:
    """Sample critical gap."""
    return CriticalGap(
        gap_id="GAP-001",
        title="Test Gap",
        description="Test gap description",
        severity=GapSeverity.HIGH,
        source="Test Source",
        remediation="Fix the gap",
        deadline_days=30,
    )


@pytest.fixture
def sample_hotspot() -> VendorRiskHotspot:
    """Sample vendor risk hotspot."""
    return VendorRiskHotspot(
        vendor_name="Test Vendor",
        risk_area="Security",
        risk_score=0.7,
        concerns=["Concern 1", "Concern 2"],
        mitigation="Address concerns",
    )


@pytest.fixture
def sample_control() -> AIActControl:
    """Sample AI Act control."""
    return AIActControl(
        control_id="AIA-01",
        category=ControlCategory.TRANSPARENCY,
        requirement="Transparency requirement",
        current_status="Partial",
        gap_description="Gap in transparency",
        priority=GapSeverity.HIGH,
    )


# =============================================================================
# Test Risk Grade Enum
# =============================================================================


class TestRiskGrade:
    """Tests for RiskGrade enum."""

    def test_grade_a(self):
        assert RiskGrade.A.value == "A"

    def test_grade_b(self):
        assert RiskGrade.B.value == "B"

    def test_grade_c(self):
        assert RiskGrade.C.value == "C"

    def test_grade_d(self):
        assert RiskGrade.D.value == "D"

    def test_grade_e(self):
        assert RiskGrade.E.value == "E"

    def test_grade_f(self):
        assert RiskGrade.F.value == "F"

    def test_grade_count(self):
        assert len(RiskGrade) == 6


# =============================================================================
# Test Gap Severity Enum
# =============================================================================


class TestGapSeverity:
    """Tests for GapSeverity enum."""

    def test_critical_value(self):
        assert GapSeverity.CRITICAL.value == "critical"

    def test_high_value(self):
        assert GapSeverity.HIGH.value == "high"

    def test_medium_value(self):
        assert GapSeverity.MEDIUM.value == "medium"

    def test_low_value(self):
        assert GapSeverity.LOW.value == "low"


# =============================================================================
# Test Control Category Enum
# =============================================================================


class TestControlCategory:
    """Tests for ControlCategory enum."""

    def test_transparency(self):
        assert ControlCategory.TRANSPARENCY.value == "transparency"

    def test_data_governance(self):
        assert ControlCategory.DATA_GOVERNANCE.value == "data_governance"

    def test_human_oversight(self):
        assert ControlCategory.HUMAN_OVERSIGHT.value == "human_oversight"

    def test_documentation(self):
        assert ControlCategory.DOCUMENTATION.value == "documentation"

    def test_category_count(self):
        assert len(ControlCategory) == 8


# =============================================================================
# Test Data Structures
# =============================================================================


class TestCriticalGap:
    """Tests for CriticalGap dataclass."""

    def test_gap_creation(self, sample_gap):
        assert sample_gap.gap_id == "GAP-001"
        assert sample_gap.severity == GapSeverity.HIGH
        assert sample_gap.deadline_days == 30

    def test_gap_to_dict(self, sample_gap):
        result = sample_gap.to_dict()
        assert result["gap_id"] == "GAP-001"
        assert result["severity"] == "high"


class TestVendorRiskHotspot:
    """Tests for VendorRiskHotspot dataclass."""

    def test_hotspot_creation(self, sample_hotspot):
        assert sample_hotspot.vendor_name == "Test Vendor"
        assert sample_hotspot.risk_score == 0.7

    def test_hotspot_risk_score_clamp(self):
        hotspot = VendorRiskHotspot(
            vendor_name="Test",
            risk_area="Test",
            risk_score=1.5,
            concerns=[],
            mitigation="Fix",
        )
        assert hotspot.risk_score == 1.0

    def test_hotspot_to_dict(self, sample_hotspot):
        result = sample_hotspot.to_dict()
        assert result["vendor_name"] == "Test Vendor"
        assert result["risk_score"] == 0.7


class TestAIActControl:
    """Tests for AIActControl dataclass."""

    def test_control_creation(self, sample_control):
        assert sample_control.control_id == "AIA-01"
        assert sample_control.category == ControlCategory.TRANSPARENCY

    def test_control_to_dict(self, sample_control):
        result = sample_control.to_dict()
        assert result["control_id"] == "AIA-01"
        assert result["category"] == "transparency"


class TestRiskSpecialistFinding:
    """Tests for RiskSpecialistFinding dataclass."""

    def test_finding_creation(self, sample_gap, sample_hotspot, sample_control):
        finding = RiskSpecialistFinding(
            risk_grade=RiskGrade.C,
            critical_gaps=[sample_gap],
            vendor_risk_hotspots=[sample_hotspot],
            ai_act_controls_required=[sample_control],
            suggested_next_steps=["Step 1"],
            residual_risk_insights=["Insight 1"],
            gdpr_scope_issues=["Issue 1"],
        )
        assert finding.risk_grade == RiskGrade.C
        assert len(finding.critical_gaps) == 1

    def test_finding_confidence_clamp(self):
        finding = RiskSpecialistFinding(
            risk_grade=RiskGrade.A,
            critical_gaps=[],
            vendor_risk_hotspots=[],
            ai_act_controls_required=[],
            suggested_next_steps=[],
            residual_risk_insights=[],
            gdpr_scope_issues=[],
            confidence=1.5,
        )
        assert finding.confidence == 1.0


# =============================================================================
# Test Risk Specialist Agent
# =============================================================================


class TestRiskSpecialistAgent:
    """Tests for RiskSpecialistAgent class."""

    def test_agent_init(self, sample_briefing):
        agent = RiskSpecialistAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = RiskSpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.status == ExpertStatus.COMPLETED
        assert result.expert_type == ExpertType.RISK_SPECIALIST

    def test_agent_produces_findings(self, sample_briefing):
        agent = RiskSpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.findings) > 0

    def test_agent_findings_have_priorities(self, sample_briefing):
        agent = RiskSpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        for finding in result.findings:
            assert finding.priority in FindingPriority

    def test_agent_summary_generated(self, sample_briefing):
        agent = RiskSpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.summary) > 0


# =============================================================================
# Test Module Functions
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_risk_analysis(self, sample_briefing):
        result = run_risk_analysis(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.expert_id == "risk_specialist"

    def test_assess_risk_grade_critical(self):
        grade = assess_risk_grade(
            critical_count=3,
            high_count=0,
            medium_count=0,
        )
        assert grade == RiskGrade.F

    def test_assess_risk_grade_high(self):
        grade = assess_risk_grade(
            critical_count=0,
            high_count=4,
            medium_count=0,
        )
        assert grade == RiskGrade.D

    def test_assess_risk_grade_medium(self):
        grade = assess_risk_grade(
            critical_count=0,
            high_count=0,
            medium_count=5,
        )
        assert grade == RiskGrade.C

    def test_assess_risk_grade_low(self):
        grade = assess_risk_grade(
            critical_count=0,
            high_count=0,
            medium_count=2,
        )
        assert grade == RiskGrade.B

    def test_assess_risk_grade_excellent(self):
        grade = assess_risk_grade(
            critical_count=0,
            high_count=0,
            medium_count=0,
        )
        assert grade == RiskGrade.A

    def test_identify_control_gaps(self):
        current = ["control_a", "control_b"]
        required = ["control_a", "control_c", "control_d"]
        gaps = identify_control_gaps(current, required)
        assert "control_c" in gaps
        assert "control_d" in gaps
        assert "control_a" not in gaps

    def test_mock_data_exists(self):
        assert "risk_grade" in MOCK_RISK_DATA
        assert "critical_gaps" in MOCK_RISK_DATA
        assert "vendor_risk_hotspots" in MOCK_RISK_DATA
