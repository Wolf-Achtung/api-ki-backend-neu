"""
Tests for N4.5 Governance Advisor Agent.

Tests cover:
- Compliance framework enum
- Maturity level enum
- Mandate timeframe enum
- Data structures
- GovernanceAdvisorAgent behavior
- Module functions
"""

import pytest
from typing import Dict, Any

from services.expert_agents.governance_advisor_agent import (
    ComplianceFramework,
    MaturityLevel,
    MandateTimeframe,
    ComplianceMapping,
    MaturityGap,
    GovernanceMandate,
    GovernanceAdvisorFinding,
    GovernanceAdvisorAgent,
    run_governance_analysis,
    map_compliance_requirements,
    identify_maturity_gaps,
    MOCK_GOVERNANCE_DATA,
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
def sample_mapping() -> ComplianceMapping:
    """Sample compliance mapping."""
    return ComplianceMapping(
        framework=ComplianceFramework.EU_AI_ACT,
        requirement_id="AIA-01",
        requirement="Transparency requirement",
        current_status="Partial",
        gap_description="Missing notifications",
        remediation_effort="Medium",
        priority=1,
        mapped_to=["ISO_42001-5.3"],
    )


@pytest.fixture
def sample_gap() -> MaturityGap:
    """Sample maturity gap."""
    return MaturityGap(
        domain="AI Governance",
        current_level=MaturityLevel.DEVELOPING,
        target_level=MaturityLevel.MANAGED,
        gap_description="Governance framework needs formalization",
        improvement_actions=["Establish committee"],
        estimated_effort="6 months",
        dependencies=["Executive support"],
    )


@pytest.fixture
def sample_mandate() -> GovernanceMandate:
    """Sample governance mandate."""
    return GovernanceMandate(
        timeframe=MandateTimeframe.SHORT_TERM,
        title="AI Governance Foundation",
        objectives=["Establish committee"],
        key_actions=["Appoint lead"],
        success_metrics=["Committee operational"],
        resources_required="1 FTE",
        risks=["Resource availability"],
        owner="CDO",
    )


# =============================================================================
# Test Compliance Framework Enum
# =============================================================================


class TestComplianceFramework:
    """Tests for ComplianceFramework enum."""

    def test_eu_ai_act(self):
        assert ComplianceFramework.EU_AI_ACT.value == "eu_ai_act"

    def test_iso_42001(self):
        assert ComplianceFramework.ISO_42001.value == "iso_42001"

    def test_nis2(self):
        assert ComplianceFramework.NIS2.value == "nis2"

    def test_gdpr(self):
        assert ComplianceFramework.GDPR.value == "gdpr"

    def test_iso_27001(self):
        assert ComplianceFramework.ISO_27001.value == "iso_27001"

    def test_soc2(self):
        assert ComplianceFramework.SOC2.value == "soc2"


# =============================================================================
# Test Maturity Level Enum
# =============================================================================


class TestMaturityLevel:
    """Tests for MaturityLevel enum."""

    def test_initial(self):
        assert MaturityLevel.INITIAL.value == "initial"

    def test_developing(self):
        assert MaturityLevel.DEVELOPING.value == "developing"

    def test_defined(self):
        assert MaturityLevel.DEFINED.value == "defined"

    def test_managed(self):
        assert MaturityLevel.MANAGED.value == "managed"

    def test_optimizing(self):
        assert MaturityLevel.OPTIMIZING.value == "optimizing"


# =============================================================================
# Test Mandate Timeframe Enum
# =============================================================================


class TestMandateTimeframe:
    """Tests for MandateTimeframe enum."""

    def test_immediate(self):
        assert MandateTimeframe.IMMEDIATE.value == "immediate"

    def test_short_term(self):
        assert MandateTimeframe.SHORT_TERM.value == "short_term"

    def test_medium_term(self):
        assert MandateTimeframe.MEDIUM_TERM.value == "medium_term"

    def test_long_term(self):
        assert MandateTimeframe.LONG_TERM.value == "long_term"

    def test_strategic(self):
        assert MandateTimeframe.STRATEGIC.value == "strategic"


# =============================================================================
# Test Data Structures
# =============================================================================


class TestComplianceMapping:
    """Tests for ComplianceMapping dataclass."""

    def test_mapping_creation(self, sample_mapping):
        assert sample_mapping.framework == ComplianceFramework.EU_AI_ACT
        assert sample_mapping.requirement_id == "AIA-01"
        assert sample_mapping.priority == 1

    def test_mapping_to_dict(self, sample_mapping):
        result = sample_mapping.to_dict()
        assert result["framework"] == "eu_ai_act"
        assert result["requirement_id"] == "AIA-01"


class TestMaturityGap:
    """Tests for MaturityGap dataclass."""

    def test_gap_creation(self, sample_gap):
        assert sample_gap.domain == "AI Governance"
        assert sample_gap.current_level == MaturityLevel.DEVELOPING
        assert sample_gap.target_level == MaturityLevel.MANAGED

    def test_gap_to_dict(self, sample_gap):
        result = sample_gap.to_dict()
        assert result["domain"] == "AI Governance"
        assert result["current_level"] == "developing"


class TestGovernanceMandate:
    """Tests for GovernanceMandate dataclass."""

    def test_mandate_creation(self, sample_mandate):
        assert sample_mandate.timeframe == MandateTimeframe.SHORT_TERM
        assert sample_mandate.title == "AI Governance Foundation"
        assert sample_mandate.owner == "CDO"

    def test_mandate_to_dict(self, sample_mandate):
        result = sample_mandate.to_dict()
        assert result["timeframe"] == "short_term"
        assert result["owner"] == "CDO"


class TestGovernanceAdvisorFinding:
    """Tests for GovernanceAdvisorFinding dataclass."""

    def test_finding_creation(self, sample_mapping, sample_gap, sample_mandate):
        finding = GovernanceAdvisorFinding(
            compliance_mappings=[sample_mapping],
            maturity_gaps=[sample_gap],
            mandate_90_day=sample_mandate,
            mandate_12_month=sample_mandate,
            overall_maturity=MaturityLevel.DEVELOPING,
            priority_frameworks=[ComplianceFramework.EU_AI_ACT],
            quick_wins=["Update notifications"],
            strategic_initiatives=["Build CoE"],
        )
        assert finding.overall_maturity == MaturityLevel.DEVELOPING
        assert len(finding.compliance_mappings) == 1


# =============================================================================
# Test Governance Advisor Agent
# =============================================================================


class TestGovernanceAdvisorAgent:
    """Tests for GovernanceAdvisorAgent class."""

    def test_agent_init(self, sample_briefing):
        agent = GovernanceAdvisorAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = GovernanceAdvisorAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.status == ExpertStatus.COMPLETED
        assert result.expert_type == ExpertType.GOVERNANCE_ADVISOR

    def test_agent_produces_findings(self, sample_briefing):
        agent = GovernanceAdvisorAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.findings) > 0

    def test_agent_summary_generated(self, sample_briefing):
        agent = GovernanceAdvisorAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.summary) > 0

    def test_agent_findings_include_mandates(self, sample_briefing):
        agent = GovernanceAdvisorAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        mandate_findings = [
            f for f in result.findings
            if "mandate" in f.title.lower()
        ]
        assert len(mandate_findings) >= 2


# =============================================================================
# Test Module Functions
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_governance_analysis(self, sample_briefing):
        result = run_governance_analysis(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.expert_id == "governance_advisor"

    def test_map_compliance_requirements_with_gaps(self):
        gaps = map_compliance_requirements(
            framework=ComplianceFramework.EU_AI_ACT,
            requirements=["req_a", "req_b", "req_c"],
            current_controls=["req_a"],
        )
        assert "req_b" in gaps
        assert "req_c" in gaps
        assert "req_a" not in gaps

    def test_map_compliance_requirements_no_gaps(self):
        gaps = map_compliance_requirements(
            framework=ComplianceFramework.EU_AI_ACT,
            requirements=["req_a", "req_b"],
            current_controls=["REQ_A", "REQ_B"],  # Case insensitive
        )
        assert len(gaps) == 0

    def test_identify_maturity_gaps_two_levels(self):
        gap = identify_maturity_gaps(
            current_level=MaturityLevel.DEVELOPING,
            target_level=MaturityLevel.MANAGED,
        )
        assert gap == 2

    def test_identify_maturity_gaps_zero(self):
        gap = identify_maturity_gaps(
            current_level=MaturityLevel.MANAGED,
            target_level=MaturityLevel.MANAGED,
        )
        assert gap == 0

    def test_identify_maturity_gaps_negative(self):
        gap = identify_maturity_gaps(
            current_level=MaturityLevel.OPTIMIZING,
            target_level=MaturityLevel.INITIAL,
        )
        assert gap == 0

    def test_mock_data_exists(self):
        assert "compliance_mappings" in MOCK_GOVERNANCE_DATA
        assert "maturity_gaps" in MOCK_GOVERNANCE_DATA
        assert "mandate_90_day" in MOCK_GOVERNANCE_DATA
        assert "mandate_12_month" in MOCK_GOVERNANCE_DATA
