# -*- coding: utf-8 -*-
"""
N4.2 Test Suite: Model Strategy Layer v3 (Dual-Model Merge)
===========================================================

Tests for services/model_strategy_layer_v3.py

Coverage:
- Language-aware model selection
- Dual-model semantic merge
- Drift detection
- Quality validation
- Multilingual merge strategies

Target: ~20 tests

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
"""

import pytest
from typing import Dict, Any

from services.model_strategy_layer_v3 import (
    MultilingualMergeStrategy,
    DriftLevel,
    MultilingualDriftDetector,
    MultilingualSemanticMerger,
    MultilingualModelStrategy,
    generate_multilingual,
    semantic_merge_multilingual,
    detect_drift,
    validate_merge_quality,
    CLAUDE_WEIGHT_BY_LANGUAGE,
    SECTION_CLAUDE_WEIGHT,
)
from services.language_strategy_engine import SupportedLanguage


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def claude_content() -> str:
    """Sample Claude-generated content."""
    return """
    Executive Summary: Das Unternehmen zeigt ein erhebliches Potenzial für
    KI-Transformation. Mit einem ROI von 150% und einer Amortisationszeit
    von 6 Monaten empfehlen wir eine strategische Implementierung.
    """


@pytest.fixture
def gpt_content() -> str:
    """Sample GPT-generated content."""
    return """
    Executive Summary: The company shows significant AI transformation potential.
    ROI: 150%. Payback: 6 months. Strategic implementation recommended.
    Key metrics indicate positive trajectory.
    """


@pytest.fixture
def source_content() -> str:
    """Original source content."""
    return """
    ROI: 150% über 12 Monate. Payback: 6 Monate. Risiko: niedrig.
    Empfehlung: KI-Tools einführen für maximale Effizienz.
    """


# =============================================================================
# TEST CLASS: Merge Strategy Enum
# =============================================================================

class TestMergeStrategyEnum:
    """Tests for MultilingualMergeStrategy enum."""

    def test_all_strategies_defined(self):
        """All merge strategies should be defined."""
        assert MultilingualMergeStrategy.CLAUDE_EXECUTIVE.value == "claude_executive"
        assert MultilingualMergeStrategy.GPT_NUMERIC.value == "gpt_numeric"
        assert MultilingualMergeStrategy.WEIGHTED_BY_LANGUAGE.value == "weighted_by_language"
        assert MultilingualMergeStrategy.CONSENSUS_SEMANTIC.value == "consensus_semantic"
        assert MultilingualMergeStrategy.BEST_QUALITY.value == "best_quality"


# =============================================================================
# TEST CLASS: Drift Level Enum
# =============================================================================

class TestDriftLevelEnum:
    """Tests for DriftLevel enum."""

    def test_all_levels_defined(self):
        """All drift levels should be defined."""
        assert DriftLevel.NONE.value == "none"
        assert DriftLevel.MINIMAL.value == "minimal"
        assert DriftLevel.ACCEPTABLE.value == "acceptable"
        assert DriftLevel.WARNING.value == "warning"
        assert DriftLevel.CRITICAL.value == "critical"


# =============================================================================
# TEST CLASS: Language Weights
# =============================================================================

class TestLanguageWeights:
    """Tests for language weight constants."""

    def test_all_languages_have_weights(self):
        """All languages should have Claude weights."""
        for lang in SupportedLanguage:
            assert lang in CLAUDE_WEIGHT_BY_LANGUAGE

    def test_weights_in_range(self):
        """Weights should be between 0 and 1."""
        for lang, weight in CLAUDE_WEIGHT_BY_LANGUAGE.items():
            assert 0.0 <= weight <= 1.0

    def test_romance_languages_prefer_claude(self):
        """Romance languages should prefer Claude."""
        assert CLAUDE_WEIGHT_BY_LANGUAGE[SupportedLanguage.FR] > 0.5
        assert CLAUDE_WEIGHT_BY_LANGUAGE[SupportedLanguage.IT] > 0.5
        assert CLAUDE_WEIGHT_BY_LANGUAGE[SupportedLanguage.ES] > 0.5


# =============================================================================
# TEST CLASS: Section Weights
# =============================================================================

class TestSectionWeights:
    """Tests for section weight constants."""

    def test_executive_prefers_claude(self):
        """Executive sections should prefer Claude."""
        assert SECTION_CLAUDE_WEIGHT["executive_summary"] > 0.5
        assert SECTION_CLAUDE_WEIGHT["investment_thesis"] > 0.5

    def test_numeric_prefers_gpt(self):
        """Numeric sections should prefer GPT."""
        assert SECTION_CLAUDE_WEIGHT["business_case"] < 0.5
        assert SECTION_CLAUDE_WEIGHT["kpi_dashboard"] < 0.5


# =============================================================================
# TEST CLASS: Multilingual Drift Detector
# =============================================================================

class TestMultilingualDriftDetector:
    """Tests for MultilingualDriftDetector."""

    def test_detector_init(self):
        """Detector should initialize correctly."""
        detector = MultilingualDriftDetector(
            SupportedLanguage.DE,
            SupportedLanguage.EN,
        )
        assert detector._source_lang == SupportedLanguage.DE
        assert detector._target_lang == SupportedLanguage.EN

    def test_detect_no_drift(self):
        """Identical texts should have no drift."""
        detector = MultilingualDriftDetector(
            SupportedLanguage.DE,
            SupportedLanguage.DE,
        )
        result = detector.detect_drift(
            "ROI 150%, Payback 6 Monate",
            "ROI 150%, Payback 6 Monate",
        )

        assert result["drift_level"] == DriftLevel.NONE.value
        assert result["similarity_score"] >= 0.99

    def test_detect_high_drift(self):
        """Very different texts should have high drift."""
        detector = MultilingualDriftDetector(
            SupportedLanguage.DE,
            SupportedLanguage.EN,
        )
        result = detector.detect_drift(
            "ROI 150%, Payback 6 Monate, Risiko niedrig",
            "The weather is nice today.",
        )

        assert result["drift_value"] > 0.5  # High drift

    def test_numbers_preserved(self, source_content):
        """Should detect number preservation."""
        detector = MultilingualDriftDetector(
            SupportedLanguage.DE,
            SupportedLanguage.EN,
        )
        result = detector.detect_drift(
            "ROI: 150%, Payback: 6 Monate",
            "ROI: 150%, Payback: 6 months",
        )

        assert result["numbers_preserved"] is True


# =============================================================================
# TEST CLASS: Multilingual Semantic Merger
# =============================================================================

class TestMultilingualSemanticMerger:
    """Tests for MultilingualSemanticMerger."""

    def test_merger_init(self):
        """Merger should initialize correctly."""
        merger = MultilingualSemanticMerger(
            target_language=SupportedLanguage.DE,
        )
        assert merger._target_lang == SupportedLanguage.DE

    def test_merge_claude_executive(self, claude_content, gpt_content):
        """Should merge with Claude preference."""
        merger = MultilingualSemanticMerger(SupportedLanguage.DE)
        result = merger.merge(
            claude_content=claude_content,
            gpt_content=gpt_content,
            section_key="executive_summary",
            strategy=MultilingualMergeStrategy.CLAUDE_EXECUTIVE,
        )

        assert result["merged_content"] is not None
        assert result["claude_contribution"] > 0.5
        assert "claude" in result["source_models"]
        assert "gpt" in result["source_models"]

    def test_merge_gpt_numeric(self, claude_content, gpt_content):
        """Should merge with GPT preference."""
        merger = MultilingualSemanticMerger(SupportedLanguage.DE)
        result = merger.merge(
            claude_content=claude_content,
            gpt_content=gpt_content,
            section_key="business_case",
            strategy=MultilingualMergeStrategy.GPT_NUMERIC,
        )

        assert result["gpt_contribution"] > 0.5

    def test_merge_weighted(self, claude_content, gpt_content):
        """Should merge with language-based weights."""
        merger = MultilingualSemanticMerger(SupportedLanguage.FR)  # French prefers Claude
        result = merger.merge(
            claude_content=claude_content,
            gpt_content=gpt_content,
            section_key="roadmap_90d",
            strategy=MultilingualMergeStrategy.WEIGHTED_BY_LANGUAGE,
        )

        assert result["target_language"] == "fr"

    def test_merge_tracks_quality(self, claude_content, gpt_content):
        """Should track quality score."""
        merger = MultilingualSemanticMerger(SupportedLanguage.DE)
        result = merger.merge(
            claude_content=claude_content,
            gpt_content=gpt_content,
            section_key="executive_summary",
        )

        assert 0.0 <= result["quality_score"] <= 1.0


# =============================================================================
# TEST CLASS: Multilingual Model Strategy
# =============================================================================

class TestMultilingualModelStrategy:
    """Tests for MultilingualModelStrategy."""

    def test_strategy_init(self):
        """Strategy should initialize correctly."""
        strategy = MultilingualModelStrategy(
            target_language="de",
        )
        assert strategy._target_lang == SupportedLanguage.DE

    def test_strategy_init_with_source(self):
        """Strategy should initialize with source language."""
        strategy = MultilingualModelStrategy(
            target_language="en",
            source_language="de",
        )
        assert strategy._source_lang == SupportedLanguage.DE
        assert strategy._target_lang == SupportedLanguage.EN

    def test_select_model_executive(self):
        """Should select Claude for executive sections."""
        strategy = MultilingualModelStrategy(target_language="de")
        model, reason = strategy.select_model("executive_summary")

        assert model == "claude" or model == "dual"

    def test_select_model_kpi(self):
        """Should select GPT for KPI sections."""
        strategy = MultilingualModelStrategy(target_language="de")
        model, reason = strategy.select_model("kpi_dashboard")

        assert model == "gpt"

    def test_validate_quality(self, source_content):
        """Should validate content quality."""
        strategy = MultilingualModelStrategy(target_language="de")
        metrics = strategy.validate_quality(
            content="ROI: 150%, Payback: 6 Monate. Empfehlung: KI-Tools einführen.",
            source_content=source_content,
            section_key="executive_summary",
        )

        assert metrics.overall_score >= 0.0
        assert metrics.drift_score >= 0.0


# =============================================================================
# TEST CLASS: Module Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_generate_multilingual(self):
        """generate_multilingual should return result."""
        result = generate_multilingual(
            section_key="executive_summary",
            prompt="Generate executive summary",
            context={"company_name": "Test GmbH"},
            target_language="de",
        )

        assert "merged_content" in result
        assert "quality_score" in result

    def test_semantic_merge_multilingual(self, claude_content, gpt_content):
        """semantic_merge_multilingual should merge content."""
        result = semantic_merge_multilingual(
            claude_content=claude_content,
            gpt_content=gpt_content,
            section_key="executive_summary",
            target_language="de",
        )

        assert result["merged_content"] is not None

    def test_detect_drift_function(self, source_content):
        """detect_drift should return drift result."""
        result = detect_drift(
            source_text=source_content,
            target_text="ROI: 150%, Payback: 6 months. Recommendation: Introduce AI tools.",
            source_language="de",
            target_language="en",
        )

        assert "drift_level" in result
        assert "similarity_score" in result

    def test_validate_merge_quality_function(self, source_content):
        """validate_merge_quality should return metrics."""
        metrics = validate_merge_quality(
            content="ROI: 150%, Payback: 6 Monate.",
            source_content=source_content,
            target_language="de",
        )

        assert "overall" in metrics
        assert "drift" in metrics


# =============================================================================
# TEST CLASS: Quality Metrics
# =============================================================================

class TestQualityMetrics:
    """Tests for quality metrics."""

    def test_metrics_structure(self):
        """Quality metrics should have correct structure."""
        strategy = MultilingualModelStrategy(target_language="de")
        metrics = strategy.validate_quality(
            content="Test content with some words.",
        )

        d = metrics.to_dict()
        assert "overall" in d
        assert "coherence" in d
        assert "completeness" in d
        assert "tone" in d
        assert "drift" in d

    def test_longer_content_better_completeness(self):
        """Longer content should have better completeness."""
        strategy = MultilingualModelStrategy(target_language="de")

        short_metrics = strategy.validate_quality(content="Short.")
        long_metrics = strategy.validate_quality(
            content=" ".join(["Word"] * 100)
        )

        assert long_metrics.completeness_score >= short_metrics.completeness_score


# =============================================================================
# TEST CLASS: Strategy Report
# =============================================================================

class TestStrategyReport:
    """Tests for MultilingualStrategyReport."""

    def test_report_initial_state(self):
        """Report should have correct initial state."""
        strategy = MultilingualModelStrategy(target_language="de")
        report = strategy.get_report()

        assert report.success is True
        assert report.sections_processed == 0
        assert report.dual_generations == 0

    def test_report_to_dict(self):
        """Report should serialize to dict."""
        strategy = MultilingualModelStrategy(target_language="de")
        report = strategy.get_report()
        d = report.to_dict()

        assert d["engine_id"] == "MODEL_STRATEGY_V3"
        assert "timestamp" in d
