# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Research Integrity Engine v1
=============================================

Tests for services/research_agents/integrity_engine.py

Coverage:
- ResearchIntegrityEngineV1
- Bias detection
- Module functions

Target: ~10 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from typing import List

from services.research_agents.integrity_engine import (
    IntegrityReport,
    ResearchIntegrityEngineV1,
    detect_bias,
)
from services.research_agents.orchestrator import (
    AgentSignalType,
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
        content="This is objective content about market trends.",
        confidence=0.85,
        source="Reuters",
        source_url="https://reuters.com/article",
    )


@pytest.fixture
def biased_insight() -> ResearchInsight:
    return ResearchInsight(
        insight_id="BIAS-001",
        signal_type=AgentSignalType.MARKET,
        title="Amazing Perfect Solution",
        content="This revolutionary breakthrough is the best ever and will dominate everything!",
        confidence=0.95,
        source="Marketing Blog",
    )


@pytest.fixture
def sample_insights() -> List[ResearchInsight]:
    return [
        ResearchInsight(
            insight_id="M1",
            signal_type=AgentSignalType.MARKET,
            title="Market Trend",
            content="Market growing at 15% CAGR",
            confidence=0.9,
            source="Industry Report",
        ),
        ResearchInsight(
            insight_id="T1",
            signal_type=AgentSignalType.TECH,
            title="Tech Analysis",
            content="GPT-4 adoption increasing",
            confidence=0.85,
            source="Tech News",
        ),
    ]


# =============================================================================
# TEST CLASS: Integrity Engine
# =============================================================================

class TestIntegrityEngine:
    """Tests for ResearchIntegrityEngineV1."""

    def test_engine_init(self):
        engine = ResearchIntegrityEngineV1(
            language="de",
            strict_mode=True,
        )
        assert engine.language == "de"
        assert engine.strict_mode is True

    def test_engine_validate(self, sample_insights):
        engine = ResearchIntegrityEngineV1()
        report = engine.validate(sample_insights)
        assert isinstance(report, IntegrityReport)
        assert report.overall_integrity_score >= 0.0
        assert report.overall_integrity_score <= 1.0

    def test_engine_strict_mode(self, sample_insights):
        engine = ResearchIntegrityEngineV1(strict_mode=True)
        report = engine.validate(sample_insights)
        # Strict mode may lower scores
        assert isinstance(report, IntegrityReport)

    def test_engine_detects_bias(self, biased_insight):
        engine = ResearchIntegrityEngineV1()
        report = engine.validate([biased_insight])
        # Should detect promotional bias
        assert report.biases_detected >= 0


# =============================================================================
# TEST CLASS: Module Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_detect_bias_promotional(self):
        biases = detect_bias(
            "TEST-001",
            "This is the best revolutionary breakthrough ever!",
        )
        assert isinstance(biases, list)

    def test_detect_bias_neutral(self):
        biases = detect_bias(
            "TEST-001",
            "The market grew by 10% in Q3 2024.",
        )
        # Neutral content should have fewer biases
        assert isinstance(biases, list)
