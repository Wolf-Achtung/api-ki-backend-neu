# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Research Agent Orchestrator
============================================

Tests for services/research_agents/orchestrator.py

Coverage:
- Agent Registry
- Priority Scheduling
- Audit Chain
- Deduplication
- Hash computation

Target: ~20 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from typing import Dict, Any

from services.research_agents.orchestrator import (
    AgentPriority,
    AgentSignalType,
    AgentStatus,
    ModelPreference,
    ResearchInsight,
    AgentResult,
    AgentConfig,
    AgentRegistry,
    AuditChain,
    ResearchAgentOrchestrator,
    compute_result_hash,
    schedule_agents,
    get_agent_status,
    deduplicate_insights,
    compute_insight_similarity,
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
def sample_insight() -> ResearchInsight:
    return ResearchInsight(
        insight_id="TEST-001",
        signal_type=AgentSignalType.MARKET,
        title="Test Insight",
        content="This is test content for market analysis.",
        confidence=0.85,
        source="Test Source",
        tags=["test", "market"],
    )


@pytest.fixture
def sample_result(sample_insight) -> AgentResult:
    return AgentResult(
        agent_id="test_agent",
        signal=AgentSignalType.MARKET,
        insights=[sample_insight],
        confidence=0.85,
        sources=["Test Source"],
    )


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestOrchestratorEnums:
    """Tests for orchestrator enums."""

    def test_agent_priority_values(self):
        assert AgentPriority.CRITICAL.value == 1
        assert AgentPriority.HIGH.value == 2
        assert AgentPriority.NORMAL.value == 3
        assert AgentPriority.LOW.value == 4

    def test_agent_signal_type_values(self):
        assert AgentSignalType.MARKET.value == "market"
        assert AgentSignalType.COMPETITOR.value == "competitor"
        assert AgentSignalType.FUNDING.value == "funding"
        assert AgentSignalType.TECH.value == "tech"

    def test_model_preference_values(self):
        assert ModelPreference.GPT.value == "gpt"
        assert ModelPreference.CLAUDE.value == "claude"
        assert ModelPreference.AUTO.value == "auto"

    def test_agent_status_values(self):
        assert AgentStatus.PENDING.value == "pending"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"


# =============================================================================
# TEST CLASS: Data Structures
# =============================================================================

class TestDataStructures:
    """Tests for data structures."""

    def test_research_insight_creation(self, sample_insight):
        assert sample_insight.insight_id == "TEST-001"
        assert sample_insight.signal_type == AgentSignalType.MARKET
        assert sample_insight.confidence == 0.85

    def test_research_insight_confidence_clamp(self):
        insight = ResearchInsight(
            insight_id="TEST",
            signal_type=AgentSignalType.MARKET,
            title="Test",
            content="Test",
            confidence=1.5,  # Over 1.0
            source="Test",
        )
        assert insight.confidence == 1.0

    def test_research_insight_to_dict(self, sample_insight):
        d = sample_insight.to_dict()
        assert d["insight_id"] == "TEST-001"
        assert d["signal_type"] == "market"

    def test_research_insight_hash(self, sample_insight):
        h = sample_insight.compute_hash()
        assert isinstance(h, str)
        assert len(h) == 64  # SHA256

    def test_agent_result_creation(self, sample_result):
        assert sample_result.agent_id == "test_agent"
        assert sample_result.signal == AgentSignalType.MARKET
        assert len(sample_result.insights) == 1

    def test_agent_result_to_dict(self, sample_result):
        d = sample_result.to_dict()
        assert d["signal"] == "market"
        assert "hash" in d

    def test_agent_config_creation(self):
        config = AgentConfig(
            agent_id="test",
            signal_type=AgentSignalType.MARKET,
            priority=AgentPriority.HIGH,
        )
        assert config.agent_id == "test"
        assert config.priority == AgentPriority.HIGH


# =============================================================================
# TEST CLASS: Agent Registry
# =============================================================================

class TestAgentRegistry:
    """Tests for agent registry."""

    def test_registry_register(self):
        registry = AgentRegistry()
        registry.register(
            agent_id="test_agent",
            signal_type=AgentSignalType.MARKET,
            priority=AgentPriority.HIGH,
        )
        assert registry.get_config("test_agent") is not None

    def test_registry_unregister(self):
        registry = AgentRegistry()
        registry.register("test", AgentSignalType.MARKET)
        assert registry.unregister("test") is True
        assert registry.get_config("test") is None

    def test_registry_get_status(self):
        registry = AgentRegistry()
        registry.register("test", AgentSignalType.MARKET)
        assert registry.get_status("test") == AgentStatus.PENDING

    def test_registry_set_status(self):
        registry = AgentRegistry()
        registry.register("test", AgentSignalType.MARKET)
        registry.set_status("test", AgentStatus.RUNNING)
        assert registry.get_status("test") == AgentStatus.RUNNING

    def test_registry_get_by_priority(self):
        registry = AgentRegistry()
        registry.register("low", AgentSignalType.MARKET, priority=AgentPriority.LOW)
        registry.register("high", AgentSignalType.TECH, priority=AgentPriority.HIGH)

        sorted_agents = registry.get_agents_by_priority()
        assert sorted_agents[0].agent_id == "high"


# =============================================================================
# TEST CLASS: Audit Chain
# =============================================================================

class TestAuditChain:
    """Tests for audit chain."""

    def test_audit_chain_init(self):
        chain = AuditChain()
        assert len(chain.get_chain()) == 0

    def test_audit_chain_add_entry(self, sample_result):
        chain = AuditChain()
        cascaded_hash = chain.add_entry(sample_result)
        assert isinstance(cascaded_hash, str)
        assert len(chain.get_chain()) == 1

    def test_audit_chain_verify(self, sample_result):
        chain = AuditChain()
        chain.add_entry(sample_result)
        is_valid, invalid_indices = chain.verify_chain()
        assert is_valid is True
        assert len(invalid_indices) == 0

    def test_audit_chain_multiple_entries(self, sample_result):
        chain = AuditChain()
        chain.add_entry(sample_result)

        result2 = AgentResult(
            agent_id="agent2",
            signal=AgentSignalType.TECH,
            confidence=0.9,
        )
        chain.add_entry(result2)

        assert len(chain.get_chain()) == 2
        is_valid, _ = chain.verify_chain()
        assert is_valid

    def test_audit_chain_to_dict(self, sample_result):
        chain = AuditChain()
        chain.add_entry(sample_result)
        d = chain.to_dict()
        assert "chain_length" in d
        assert d["chain_length"] == 1


# =============================================================================
# TEST CLASS: Deduplication
# =============================================================================

class TestDeduplication:
    """Tests for deduplication."""

    def test_compute_similarity_identical(self):
        insight_a = ResearchInsight(
            insight_id="A",
            signal_type=AgentSignalType.MARKET,
            title="Test",
            content="This is the same content",
            confidence=0.8,
            source="Test",
        )
        insight_b = ResearchInsight(
            insight_id="B",
            signal_type=AgentSignalType.MARKET,
            title="Test",
            content="This is the same content",
            confidence=0.7,
            source="Test",
        )
        similarity = compute_insight_similarity(insight_a, insight_b)
        assert similarity == 1.0

    def test_compute_similarity_different(self):
        insight_a = ResearchInsight(
            insight_id="A",
            signal_type=AgentSignalType.MARKET,
            title="Test",
            content="Alpha beta gamma",
            confidence=0.8,
            source="Test",
        )
        insight_b = ResearchInsight(
            insight_id="B",
            signal_type=AgentSignalType.MARKET,
            title="Test",
            content="Delta epsilon zeta",
            confidence=0.7,
            source="Test",
        )
        similarity = compute_insight_similarity(insight_a, insight_b)
        assert similarity < 0.5

    def test_deduplicate_insights(self):
        insights = [
            ResearchInsight(
                insight_id="A",
                signal_type=AgentSignalType.MARKET,
                title="Test",
                content="Same content here",
                confidence=0.8,
                source="Test",
            ),
            ResearchInsight(
                insight_id="B",
                signal_type=AgentSignalType.MARKET,
                title="Test",
                content="Same content here",
                confidence=0.9,
                source="Test",
            ),
        ]
        unique = deduplicate_insights(insights)
        assert len(unique) == 1
        assert unique[0].confidence == 0.9  # Higher confidence kept


# =============================================================================
# TEST CLASS: Orchestrator
# =============================================================================

class TestOrchestrator:
    """Tests for orchestrator."""

    def test_orchestrator_init(self, sample_briefing):
        orchestrator = ResearchAgentOrchestrator(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert orchestrator.language == "de"
        assert orchestrator.mock_mode is True

    def test_orchestrator_register_defaults(self, sample_briefing):
        orchestrator = ResearchAgentOrchestrator(
            briefing=sample_briefing,
            mock_mode=True,
        )
        orchestrator.register_default_agents()
        assert orchestrator.registry.get_config("market_agent") is not None

    def test_orchestrator_run_all(self, sample_briefing):
        orchestrator = ResearchAgentOrchestrator(
            briefing=sample_briefing,
            mock_mode=True,
        )
        orchestrator.register_default_agents()
        results = orchestrator.run_all_agents()
        assert len(results) >= 1

    def test_orchestrator_execution_summary(self, sample_briefing):
        orchestrator = ResearchAgentOrchestrator(
            briefing=sample_briefing,
            mock_mode=True,
        )
        orchestrator.register_default_agents()
        orchestrator.run_all_agents()
        summary = orchestrator.get_execution_summary()
        assert "agents_run" in summary
        assert "audit_chain_valid" in summary


# =============================================================================
# TEST CLASS: Module Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_compute_result_hash(self, sample_result):
        h = compute_result_hash(sample_result)
        assert isinstance(h, str)
        assert len(h) == 64

    def test_schedule_agents(self):
        registry = AgentRegistry()
        registry.register("a", AgentSignalType.MARKET, priority=AgentPriority.LOW)
        registry.register("b", AgentSignalType.TECH, priority=AgentPriority.HIGH)

        scheduled = schedule_agents(registry)
        assert scheduled[0].priority == AgentPriority.HIGH

    def test_get_agent_status(self):
        registry = AgentRegistry()
        registry.register("test", AgentSignalType.MARKET)
        status = get_agent_status(registry, "test")
        assert status == AgentStatus.PENDING
