# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Regulatory Agent
=================================

Tests for services/research_agents/regulatory_agent.py

Coverage:
- Enums (RegulationType, ComplianceStatus, ImpactLevel)
- RegulatoryInsight and GovernanceInjectionTemplate
- RegulatoryAgent
- Module functions

Target: ~12 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from typing import Dict, Any

from services.research_agents.regulatory_agent import (
    RegulationType,
    ImpactLevel,
    ComplianceStatus,
    RegulatoryInsight,
    RegulatoryAgent,
    run_regulatory_research,
    MOCK_REGULATORY_DATA,
)
from services.research_agents.orchestrator import (
    AgentSignalType,
    AgentStatus,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    return {
        "company_name": "TechCorp GmbH",
        "branch": "consulting",
        "region": "EU",
        "lang": "de",
    }


@pytest.fixture
def sample_insight() -> RegulatoryInsight:
    return RegulatoryInsight(
        insight_id="REG-001",
        title="EU AI Act",
        regulation=RegulationType.EU_AI_ACT,
        summary="EU AI Act compliance requirements",
        impact_level=ImpactLevel.HIGH,
        requirements=["Transparency", "Documentation"],
        compliance_status=ComplianceStatus.PARTIAL,
        confidence=0.9,
    )


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestRegulatoryEnums:
    """Tests for regulatory agent enums."""

    def test_regulation_type_ai_act(self):
        assert RegulationType.EU_AI_ACT.value == "eu_ai_act"

    def test_regulation_type_gdpr(self):
        assert RegulationType.GDPR.value == "gdpr"

    def test_regulation_type_nis2(self):
        assert RegulationType.NIS2.value == "nis2"

    def test_compliance_status_values(self):
        assert ComplianceStatus.COMPLIANT.value == "compliant"
        assert ComplianceStatus.PARTIAL.value == "partial"
        assert ComplianceStatus.NON_COMPLIANT.value == "non_compliant"

    def test_impact_level_values(self):
        assert ImpactLevel.CRITICAL.value == "critical"
        assert ImpactLevel.HIGH.value == "high"
        assert ImpactLevel.MEDIUM.value == "medium"
        assert ImpactLevel.LOW.value == "low"


# =============================================================================
# TEST CLASS: Data Structures
# =============================================================================

class TestDataStructures:
    """Tests for data structures."""

    def test_regulatory_insight_creation(self, sample_insight):
        assert sample_insight.title == "EU AI Act"
        assert sample_insight.regulation == RegulationType.EU_AI_ACT
        assert sample_insight.compliance_status == ComplianceStatus.PARTIAL

    def test_regulatory_to_research_insight(self, sample_insight):
        research = sample_insight.to_research_insight()
        assert research.signal_type == AgentSignalType.REGULATORY
        assert "EU AI Act" in research.title


# =============================================================================
# TEST CLASS: Regulatory Agent
# =============================================================================

class TestRegulatoryAgent:
    """Tests for RegulatoryAgent."""

    def test_agent_init(self, sample_briefing):
        agent = RegulatoryAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = RegulatoryAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.agent_id == "regulatory_agent"
        assert result.signal == AgentSignalType.REGULATORY
        assert result.status == AgentStatus.COMPLETED

    def test_agent_produces_insights(self, sample_briefing):
        agent = RegulatoryAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.insights) >= 1


# =============================================================================
# TEST CLASS: Module Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_regulatory_research(self, sample_briefing):
        result = run_regulatory_research(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.agent_id == "regulatory_agent"
        assert result.status == AgentStatus.COMPLETED

    def test_mock_data_exists(self):
        assert "de" in MOCK_REGULATORY_DATA
        assert "en" in MOCK_REGULATORY_DATA
