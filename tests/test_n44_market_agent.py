# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Market Intelligence Agent
==========================================

Tests for services/research_agents/market_agent.py

Coverage:
- Enums (MarketTrendType)
- MarketInsight creation and conversion
- MarketIntelligenceAgent
- Mock data handling
- Language support (DE/EN)

Target: ~12 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from typing import Dict, Any

from services.research_agents.market_agent import (
    MarketTrendType,
    MarketInsight,
    MarketIntelligenceAgent,
    run_market_research,
    MOCK_MARKET_DATA,
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
def sample_insight() -> MarketInsight:
    return MarketInsight(
        insight_id="MARKET-001",
        title="KI-Integration",
        content="Test trend description",
        source="Test Source",
        trend_type=MarketTrendType.GROWTH,
        confidence=0.85,
    )


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestMarketEnums:
    """Tests for market agent enums."""

    def test_trend_type_growth(self):
        assert MarketTrendType.GROWTH.value == "growth"

    def test_trend_type_decline(self):
        assert MarketTrendType.DECLINE.value == "decline"

    def test_trend_type_emerging(self):
        assert MarketTrendType.EMERGING.value == "emerging"

    def test_trend_type_disruption(self):
        assert MarketTrendType.DISRUPTION.value == "disruption"


# =============================================================================
# TEST CLASS: MarketInsight
# =============================================================================

class TestMarketInsight:
    """Tests for MarketInsight dataclass."""

    def test_insight_creation(self, sample_insight):
        assert sample_insight.insight_id == "MARKET-001"
        assert sample_insight.trend_type == MarketTrendType.GROWTH

    def test_insight_to_research_insight(self, sample_insight):
        research_insight = sample_insight.to_research_insight()
        assert research_insight.signal_type == AgentSignalType.MARKET
        assert "KI-Integration" in research_insight.title
        assert research_insight.confidence == 0.85


# =============================================================================
# TEST CLASS: Market Agent
# =============================================================================

class TestMarketAgent:
    """Tests for MarketIntelligenceAgent."""

    def test_agent_init(self, sample_briefing):
        agent = MarketIntelligenceAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = MarketIntelligenceAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.agent_id == "market_agent"
        assert result.signal == AgentSignalType.MARKET
        assert result.status == AgentStatus.COMPLETED

    def test_agent_produces_insights(self, sample_briefing):
        agent = MarketIntelligenceAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.insights) >= 1

    def test_agent_english_mode(self):
        agent = MarketIntelligenceAgent(
            briefing={"lang": "en"},
            language="en",
            mock_mode=True,
        )
        result = agent.run()
        assert result.status == AgentStatus.COMPLETED


# =============================================================================
# TEST CLASS: Module Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_market_research(self, sample_briefing):
        result = run_market_research(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.agent_id == "market_agent"
        assert result.status == AgentStatus.COMPLETED

    def test_mock_data_exists(self):
        assert "de" in MOCK_MARKET_DATA
        assert "en" in MOCK_MARKET_DATA
        assert len(MOCK_MARKET_DATA["de"]) >= 1
