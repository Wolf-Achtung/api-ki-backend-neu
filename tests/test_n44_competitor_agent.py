# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Competitor Intelligence Agent
==============================================

Tests for services/research_agents/competitor_agent.py

Coverage:
- Enums (CompetitorType)
- CompetitorIntelligenceAgent
- Zero-dupe guarantee
- Module functions

Target: ~12 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from typing import Dict, Any

from services.research_agents.competitor_agent import (
    CompetitorType,
    CompetitiveStrength,
    CompetitorInsight,
    CompetitorIntelligenceAgent,
    run_competitor_research,
    MOCK_COMPETITOR_DATA,
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
        "lang": "de",
    }


@pytest.fixture
def sample_insight() -> CompetitorInsight:
    return CompetitorInsight(
        insight_id="COMP-001",
        competitor_name="Acme Corp",
        competitor_type=CompetitorType.DIRECT,
        strength=CompetitiveStrength.STRONG,
        features=["Feature A", "Feature B"],
        differentiator="Market leader",
        weakness="High prices",
        confidence=0.85,
    )


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestCompetitorEnums:
    """Tests for competitor agent enums."""

    def test_competitor_type_direct(self):
        assert CompetitorType.DIRECT.value == "direct"

    def test_competitor_type_indirect(self):
        assert CompetitorType.INDIRECT.value == "indirect"

    def test_competitor_type_emerging(self):
        assert CompetitorType.EMERGING.value == "emerging"

    def test_competitor_type_substitute(self):
        assert CompetitorType.SUBSTITUTE.value == "substitute"


# =============================================================================
# TEST CLASS: Data Structures
# =============================================================================

class TestDataStructures:
    """Tests for data structures."""

    def test_competitor_insight_creation(self, sample_insight):
        assert sample_insight.competitor_name == "Acme Corp"
        assert sample_insight.competitor_type == CompetitorType.DIRECT

    def test_competitor_to_research_insight(self, sample_insight):
        research = sample_insight.to_research_insight()
        assert research.signal_type == AgentSignalType.COMPETITOR
        assert "Acme Corp" in research.title


# =============================================================================
# TEST CLASS: Competitor Agent
# =============================================================================

class TestCompetitorAgent:
    """Tests for CompetitorIntelligenceAgent."""

    def test_agent_init(self, sample_briefing):
        agent = CompetitorIntelligenceAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = CompetitorIntelligenceAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.agent_id == "competitor_agent"
        assert result.signal == AgentSignalType.COMPETITOR
        assert result.status == AgentStatus.COMPLETED

    def test_agent_produces_insights(self, sample_briefing):
        agent = CompetitorIntelligenceAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.insights) >= 1

    def test_agent_zero_dupe_guarantee(self, sample_briefing):
        """Test that no duplicate competitors are returned."""
        agent = CompetitorIntelligenceAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        # Check for unique competitor names in metadata
        if result.metadata and "competitors" in result.metadata:
            competitors = result.metadata["competitors"]
            assert len(competitors) == len(set(competitors))


# =============================================================================
# TEST CLASS: Module Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_competitor_research(self, sample_briefing):
        result = run_competitor_research(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.agent_id == "competitor_agent"
        assert result.status == AgentStatus.COMPLETED

    def test_mock_data_exists(self):
        assert "de" in MOCK_COMPETITOR_DATA
        assert "en" in MOCK_COMPETITOR_DATA
        assert len(MOCK_COMPETITOR_DATA["de"]) >= 1
