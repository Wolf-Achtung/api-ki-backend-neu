# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Knowledge Fusion Layer v2
==========================================

Tests for services/research_agents/knowledge_fusion.py

Coverage:
- Enums (FusionStrategy, InjectionTarget)
- KnowledgeFusionLayerV2
- Module functions

Target: ~10 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from typing import Dict

from services.research_agents.knowledge_fusion import (
    FusionStrategy,
    InjectionTarget,
    InjectionHook,
    KnowledgeFusionLayerV2,
)
from services.research_agents.orchestrator import (
    AgentResult,
    AgentSignalType,
    AgentStatus,
    ResearchInsight,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_insight() -> ResearchInsight:
    return ResearchInsight(
        insight_id="TEST-001",
        signal_type=AgentSignalType.MARKET,
        title="Test Insight",
        content="Test content for market analysis.",
        confidence=0.85,
        source="Test Source",
    )


@pytest.fixture
def sample_result(sample_insight) -> AgentResult:
    return AgentResult(
        agent_id="test_agent",
        signal=AgentSignalType.MARKET,
        insights=[sample_insight],
        confidence=0.85,
        sources=["Test Source"],
        status=AgentStatus.COMPLETED,
    )


@pytest.fixture
def multiple_results_dict() -> Dict[str, AgentResult]:
    """Results as dict keyed by agent_id (matching add_agent_results API)."""
    return {
        "market_agent": AgentResult(
            agent_id="market_agent",
            signal=AgentSignalType.MARKET,
            insights=[
                ResearchInsight(
                    insight_id="M1",
                    signal_type=AgentSignalType.MARKET,
                    title="Market Trend",
                    content="Growing AI adoption",
                    confidence=0.9,
                    source="Market Report",
                )
            ],
            confidence=0.9,
            sources=["Market Report"],
            status=AgentStatus.COMPLETED,
        ),
        "tech_agent": AgentResult(
            agent_id="tech_agent",
            signal=AgentSignalType.TECH,
            insights=[
                ResearchInsight(
                    insight_id="T1",
                    signal_type=AgentSignalType.TECH,
                    title="Tech Stack",
                    content="GPT-4 recommended",
                    confidence=0.85,
                    source="Tech Analysis",
                )
            ],
            confidence=0.85,
            sources=["Tech Analysis"],
            status=AgentStatus.COMPLETED,
        ),
    }


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestFusionEnums:
    """Tests for fusion layer enums."""

    def test_fusion_strategy_values(self):
        assert FusionStrategy.WEIGHTED_AVERAGE.value == "weighted_average"
        assert FusionStrategy.HIGHEST_CONFIDENCE.value == "highest_confidence"
        assert FusionStrategy.CLAUDE_PREFERRED.value == "claude_preferred"

    def test_injection_target_values(self):
        assert InjectionTarget.EXECUTIVE_SUMMARY.value == "executive_summary"
        assert InjectionTarget.STRATEGY.value == "strategy"
        assert InjectionTarget.KI_STACK.value == "ki_stack"
        assert InjectionTarget.RISKS.value == "risks"


# =============================================================================
# TEST CLASS: Data Structures
# =============================================================================

class TestDataStructures:
    """Tests for fusion data structures."""

    def test_injection_hook_creation(self):
        hook = InjectionHook(
            hook_id="HK-001",
            target=InjectionTarget.EXECUTIVE_SUMMARY,
            content="Injected insight",
            priority=1,
        )
        assert hook.target == InjectionTarget.EXECUTIVE_SUMMARY
        assert hook.priority == 1


# =============================================================================
# TEST CLASS: Fusion Layer
# =============================================================================

class TestKnowledgeFusionLayer:
    """Tests for KnowledgeFusionLayerV2."""

    def test_layer_init(self):
        layer = KnowledgeFusionLayerV2(
            language="de",
            strategy=FusionStrategy.WEIGHTED_AVERAGE,
        )
        assert layer.language == "de"
        assert layer.strategy == FusionStrategy.WEIGHTED_AVERAGE

    def test_layer_add_results(self, multiple_results_dict):
        layer = KnowledgeFusionLayerV2()
        layer.add_agent_results(multiple_results_dict)
        assert len(layer._agent_results) == 2

    def test_layer_fuse(self, multiple_results_dict):
        layer = KnowledgeFusionLayerV2()
        layer.add_agent_results(multiple_results_dict)
        result = layer.fuse()
        assert "fused_signals" in result
        assert "theses" in result

    def test_layer_get_theses(self, multiple_results_dict):
        layer = KnowledgeFusionLayerV2()
        layer.add_agent_results(multiple_results_dict)
        layer.fuse()
        theses = layer.get_theses()
        assert isinstance(theses, list)

    def test_layer_get_hooks(self, multiple_results_dict):
        layer = KnowledgeFusionLayerV2()
        layer.add_agent_results(multiple_results_dict)
        layer.fuse()
        hooks = layer.get_all_hooks()
        assert isinstance(hooks, dict)
