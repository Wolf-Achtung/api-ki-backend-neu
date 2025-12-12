# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Tech Stack Agent
=================================

Tests for services/research_agents/tech_agent.py

Coverage:
- Enums (TechCategory, RiskLevel, VendorClassification)
- TechInsight
- TechStackAgent
- Vendor classification
- Security risk assessment

Target: ~15 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from typing import Dict, Any

from services.research_agents.tech_agent import (
    TechCategory,
    RiskLevel,
    VendorClassification,
    TechInsight,
    TechStackAgent,
    run_tech_research,
    classify_vendor,
    assess_security_risk,
    MOCK_TECH_DATA,
    VENDOR_DATABASE,
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
        "use_case": "AI Integration",
        "lang": "de",
    }


@pytest.fixture
def sample_insight() -> TechInsight:
    return TechInsight(
        insight_id="TECH-001",
        name="GPT-4 Turbo",
        vendor="OpenAI",
        category=TechCategory.AI_MODEL,
        description="Latest GPT-4 model",
        use_cases=["Text generation", "Code analysis"],
        risk_level=RiskLevel.LOW,
        confidence=0.9,
    )


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestTechEnums:
    """Tests for tech agent enums."""

    def test_tech_category_values(self):
        assert TechCategory.AI_MODEL.value == "ai_model"
        assert TechCategory.PLATFORM.value == "platform"
        assert TechCategory.FRAMEWORK.value == "framework"
        assert TechCategory.TOOL.value == "tool"

    def test_risk_level_values(self):
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.LOW.value == "low"

    def test_vendor_classification_values(self):
        assert VendorClassification.ENTERPRISE.value == "enterprise"
        assert VendorClassification.ESTABLISHED.value == "established"
        assert VendorClassification.EMERGING.value == "emerging"
        assert VendorClassification.STARTUP.value == "startup"


# =============================================================================
# TEST CLASS: Data Structures
# =============================================================================

class TestDataStructures:
    """Tests for data structures."""

    def test_tech_insight_creation(self, sample_insight):
        assert sample_insight.name == "GPT-4 Turbo"
        assert sample_insight.vendor == "OpenAI"
        assert sample_insight.category == TechCategory.AI_MODEL

    def test_tech_insight_auto_vendor_classification(self, sample_insight):
        # OpenAI should be classified as ENTERPRISE
        assert sample_insight.vendor_classification == VendorClassification.ENTERPRISE

    def test_tech_insight_confidence_clamp(self):
        insight = TechInsight(
            insight_id="TEST",
            name="Test",
            vendor="Test",
            category=TechCategory.TOOL,
            confidence=1.5,
        )
        assert insight.confidence == 1.0

    def test_tech_insight_to_research_insight(self, sample_insight):
        research = sample_insight.to_research_insight()
        assert research.signal_type == AgentSignalType.TECH
        assert "GPT-4 Turbo" in research.title


# =============================================================================
# TEST CLASS: Tech Agent
# =============================================================================

class TestTechAgent:
    """Tests for TechStackAgent."""

    def test_agent_init(self, sample_briefing):
        agent = TechStackAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = TechStackAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.agent_id == "tech_agent"
        assert result.signal == AgentSignalType.TECH
        assert result.status == AgentStatus.COMPLETED

    def test_agent_produces_insights(self, sample_briefing):
        agent = TechStackAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.insights) >= 1

    def test_agent_risk_summary(self, sample_briefing):
        agent = TechStackAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert "risk_summary" in result.metadata


# =============================================================================
# TEST CLASS: Module Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_tech_research(self, sample_briefing):
        result = run_tech_research(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.agent_id == "tech_agent"
        assert result.status == AgentStatus.COMPLETED

    def test_classify_vendor_enterprise(self):
        assert classify_vendor("OpenAI") == VendorClassification.ENTERPRISE
        assert classify_vendor("Anthropic") == VendorClassification.ENTERPRISE
        assert classify_vendor("Google") == VendorClassification.ENTERPRISE

    def test_classify_vendor_established(self):
        assert classify_vendor("HuggingFace") == VendorClassification.ESTABLISHED

    def test_classify_vendor_emerging(self):
        assert classify_vendor("LangChain") == VendorClassification.EMERGING

    def test_classify_vendor_unknown(self):
        assert classify_vendor("UnknownVendor") == VendorClassification.UNKNOWN

    def test_assess_security_risk(self):
        insights = [
            TechInsight(
                insight_id="A",
                name="Test",
                vendor="Test",
                category=TechCategory.TOOL,
                risk_level=RiskLevel.LOW,
            ),
        ]
        assessment = assess_security_risk(insights)
        assert "overall_risk" in assessment
        assert "score" in assessment

    def test_vendor_database_exists(self):
        assert "openai" in VENDOR_DATABASE
        assert "anthropic" in VENDOR_DATABASE

    def test_mock_data_exists(self):
        assert "de" in MOCK_TECH_DATA
        assert "en" in MOCK_TECH_DATA
