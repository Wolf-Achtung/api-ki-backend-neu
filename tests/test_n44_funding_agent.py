# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Funding Intelligence Agent
===========================================

Tests for services/research_agents/funding_agent.py

Coverage:
- Enums (FundingType, FundingStatus)
- FundingProgram and FundingInsight
- FundingIntelligenceAgent
- Deadline filtering
- Region filtering

Target: ~15 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from services.research_agents.funding_agent import (
    FundingType,
    FundingStatus,
    FundingProgram,
    FundingInsight,
    FundingIntelligenceAgent,
    run_funding_research,
    filter_by_deadline,
    filter_by_region,
    MOCK_FUNDING_DATA,
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
        "region": "Deutschland",
        "lang": "de",
    }


@pytest.fixture
def sample_program() -> FundingProgram:
    return FundingProgram(
        program_id="FUND-001",
        name="go-digital",
        provider="BMWK",
        funding_type=FundingType.GRANT,
        max_amount=16500,
        quota_percent=50,
        region="Deutschland",
        deadline=(datetime.now() + timedelta(days=60)).isoformat(),
        status=FundingStatus.OPEN,
        description="Test funding program",
    )


@pytest.fixture
def sample_insight(sample_program) -> FundingInsight:
    return FundingInsight(
        insight_id="FI-001",
        program=sample_program,
        confidence=0.9,
        relevance_score=0.8,
    )


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestFundingEnums:
    """Tests for funding agent enums."""

    def test_funding_type_values(self):
        assert FundingType.GRANT.value == "grant"
        assert FundingType.LOAN.value == "loan"
        assert FundingType.TAX_CREDIT.value == "tax_credit"
        assert FundingType.VOUCHER.value == "voucher"

    def test_funding_status_values(self):
        assert FundingStatus.OPEN.value == "open"
        assert FundingStatus.CLOSING_SOON.value == "closing_soon"
        assert FundingStatus.CLOSED.value == "closed"


# =============================================================================
# TEST CLASS: Data Structures
# =============================================================================

class TestDataStructures:
    """Tests for data structures."""

    def test_program_creation(self, sample_program):
        assert sample_program.name == "go-digital"
        assert sample_program.funding_type == FundingType.GRANT
        assert sample_program.max_amount == 16500

    def test_program_days_until_deadline(self, sample_program):
        days = sample_program.days_until_deadline()
        assert 55 <= days <= 65  # Around 60 days

    def test_program_to_dict(self, sample_program):
        d = sample_program.to_dict()
        assert d["name"] == "go-digital"
        assert d["type"] == "grant"
        assert "days_until_deadline" in d

    def test_funding_insight_creation(self, sample_insight):
        assert sample_insight.insight_id == "FI-001"
        assert sample_insight.confidence == 0.9

    def test_funding_insight_confidence_clamp(self, sample_program):
        insight = FundingInsight(
            insight_id="TEST",
            program=sample_program,
            confidence=1.5,
        )
        assert insight.confidence == 1.0

    def test_funding_to_research_insight(self, sample_insight):
        research = sample_insight.to_research_insight()
        assert research.signal_type == AgentSignalType.FUNDING
        assert "go-digital" in research.title


# =============================================================================
# TEST CLASS: Funding Agent
# =============================================================================

class TestFundingAgent:
    """Tests for FundingIntelligenceAgent."""

    def test_agent_init(self, sample_briefing):
        agent = FundingIntelligenceAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = FundingIntelligenceAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.agent_id == "funding_agent"
        assert result.signal == AgentSignalType.FUNDING
        assert result.status == AgentStatus.COMPLETED

    def test_agent_produces_insights(self, sample_briefing):
        agent = FundingIntelligenceAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.insights) >= 1

    def test_agent_metadata_total_potential(self, sample_briefing):
        agent = FundingIntelligenceAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert "total_potential" in result.metadata


# =============================================================================
# TEST CLASS: Module Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_funding_research(self, sample_briefing):
        result = run_funding_research(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.agent_id == "funding_agent"
        assert result.status == AgentStatus.COMPLETED

    def test_filter_by_deadline(self, sample_program):
        insights = [
            FundingInsight(
                insight_id="A",
                program=sample_program,
                confidence=0.8,
            ),
        ]
        filtered = filter_by_deadline(insights, max_days=90)
        assert len(filtered) == 1

    def test_filter_by_region(self, sample_program):
        insights = [
            FundingInsight(
                insight_id="A",
                program=sample_program,
                confidence=0.8,
            ),
        ]
        filtered = filter_by_region(insights, "Deutschland")
        assert len(filtered) == 1

    def test_mock_data_exists(self):
        assert "de" in MOCK_FUNDING_DATA
        assert "en" in MOCK_FUNDING_DATA
        assert len(MOCK_FUNDING_DATA["de"]) >= 1
