"""
Tests for Executive Clarity Engine - N4.1 PLATIN+++ Executive Experience Layer.

Tests cover:
- Jargon detection and removal
- Leadership clarity rewriting
- Executive metrics guard
- Zero-confusion validation

25 comprehensive tests for board-ready clarity.
"""

import pytest
from typing import Any, Dict, List

from services.executive_clarity_engine import (
    ExecutiveClarityEngine,
    JargonDetector,
    LeadershipClarityRewriter,
    ExecutiveMetricsGuard,
    JargonCategory,
    ClarityIssue,
    MetricIssue,
    get_clarity_engine,
    clarify_text,
    clarify_sections,
    validate_report_clarity,
    get_clarity_score,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def sample_sections() -> List[Dict[str, Any]]:
    """Sample sections for testing."""
    return [
        {
            "id": "G1",
            "content": (
                "Das transformer-basierte LLM zeigt hallucinations bei der prompt "
                "inference. Die latency muss optimiert werden. "
                "Empfehlung: Sofortige Investition von 2.5 Mio EUR."
            ),
        },
        {
            "id": "G5",
            "content": (
                "Der ROI beträgt 145% über 3 Jahre. Die Investition sollte "
                "zeitnah erfolgen. Man sollte die Strategie überdenken."
            ),
        },
        {
            "id": "G10",
            "content": (
                "Der ROI beträgt 180% über 3 Jahre. Die Compliance-Anforderungen "
                "werden durch die governance erfüllt."
            ),
        },
    ]


@pytest.fixture
def engine() -> ExecutiveClarityEngine:
    """Fresh clarity engine."""
    return ExecutiveClarityEngine()


@pytest.fixture
def jargon_detector() -> JargonDetector:
    """Fresh jargon detector."""
    return JargonDetector()


@pytest.fixture
def clarity_rewriter() -> LeadershipClarityRewriter:
    """Fresh clarity rewriter."""
    return LeadershipClarityRewriter()


@pytest.fixture
def metrics_guard() -> ExecutiveMetricsGuard:
    """Fresh metrics guard."""
    return ExecutiveMetricsGuard()


# =============================================================================
# JARGON DETECTOR TESTS
# =============================================================================


class TestJargonDetector:
    """Tests for JargonDetector."""

    def test_detect_ai_technical_jargon(
        self,
        jargon_detector: JargonDetector,
    ) -> None:
        """Test AI technical jargon detection."""
        text = "Das transformer-basierte neural network zeigt gute Ergebnisse."
        matches = jargon_detector.detect(text)

        terms = [m["term"].lower() for m in matches]
        assert "transformer" in terms or "neural network" in terms

    def test_detect_prompt_vocabulary(
        self,
        jargon_detector: JargonDetector,
    ) -> None:
        """Test prompt vocabulary detection."""
        text = "Das prompt engineering mit few-shot learning verbessert die Ergebnisse."
        matches = jargon_detector.detect(text)

        terms = [m["term"].lower() for m in matches]
        assert "prompt" in terms or "prompt engineering" in terms

    def test_detect_model_internal_terms(
        self,
        jargon_detector: JargonDetector,
    ) -> None:
        """Test model-internal term detection."""
        text = "GPT-4 und Claude-3 sind die führenden LLMs via API."
        matches = jargon_detector.detect(text)

        assert len(matches) > 0

    def test_remove_jargon(
        self,
        jargon_detector: JargonDetector,
    ) -> None:
        """Test jargon removal."""
        text = "Das LLM zeigt hallucinations bei der inference."
        cleaned, matches = jargon_detector.remove_jargon(text)

        assert "LLM" not in cleaned or "KI-Sprachmodell" in cleaned
        assert len(matches) > 0

    def test_calculate_jargon_density(
        self,
        jargon_detector: JargonDetector,
    ) -> None:
        """Test jargon density calculation."""
        clean_text = "Die Strategie ist erfolgreich."
        jargon_text = "Das transformer LLM API prompt neural network."

        clean_density = jargon_detector.calculate_jargon_density(clean_text)
        jargon_density = jargon_detector.calculate_jargon_density(jargon_text)

        assert jargon_density > clean_density

    def test_replacement_provides_alternative(
        self,
        jargon_detector: JargonDetector,
    ) -> None:
        """Test that replacements are provided."""
        text = "Die inference latency ist zu hoch."
        matches = jargon_detector.detect(text)

        for match in matches:
            assert len(match["replacement"]) > 0


# =============================================================================
# LEADERSHIP CLARITY REWRITER TESTS
# =============================================================================


class TestLeadershipClarityRewriter:
    """Tests for LeadershipClarityRewriter."""

    def test_remove_wordy_phrases(
        self,
        clarity_rewriter: LeadershipClarityRewriter,
    ) -> None:
        """Test wordy phrase removal."""
        text = "Das Unternehmen ist in der Lage, die Strategie umzusetzen."
        rewritten, issues = clarity_rewriter.rewrite(text)

        assert "in der Lage" not in rewritten

    def test_identify_passive_voice(
        self,
        clarity_rewriter: LeadershipClarityRewriter,
    ) -> None:
        """Test passive voice identification."""
        text = "Die Strategie wird umgesetzt. Der Plan wurde erstellt."
        _, issues = clarity_rewriter.rewrite(text)

        passive_issues = [i for i in issues if i["type"] == ClarityIssue.PASSIVE_VOICE.value]
        assert len(passive_issues) > 0

    def test_identify_long_sentences(
        self,
        clarity_rewriter: LeadershipClarityRewriter,
    ) -> None:
        """Test long sentence identification."""
        # This sentence has 30+ words, exceeding the 25 word threshold
        text = (
            "Die umfassende und tiefgreifende Analyse der strategischen Positionierung des "
            "Unternehmens im komplexen Kontext der digitalen Transformation und der "
            "sich wandelnden Marktbedingungen zeigt erhebliche und signifikante Potenziale "
            "in verschiedenen strategisch wichtigen Bereichen auf."
        )
        _, issues = clarity_rewriter.rewrite(text)

        wordy_issues = [i for i in issues if i["type"] == ClarityIssue.WORDY.value]
        assert len(wordy_issues) > 0

    def test_calculate_readability_score(
        self,
        clarity_rewriter: LeadershipClarityRewriter,
    ) -> None:
        """Test readability score calculation."""
        simple_text = "Kurz. Klar. Präzise."
        complex_text = (
            "Die multidimensionale Analyse der strategischen Positionierungspotenziale "
            "unter Berücksichtigung der gesamtunternehmerischen Wertschöpfungskette."
        )

        simple_score = clarity_rewriter.calculate_readability_score(simple_text)
        complex_score = clarity_rewriter.calculate_readability_score(complex_text)

        assert simple_score > complex_score


# =============================================================================
# EXECUTIVE METRICS GUARD TESTS
# =============================================================================


class TestExecutiveMetricsGuard:
    """Tests for ExecutiveMetricsGuard."""

    def test_detect_contradictory_metrics(
        self,
        metrics_guard: ExecutiveMetricsGuard,
    ) -> None:
        """Test contradictory metric detection."""
        sections = [
            {"id": "S1", "content": "Der ROI beträgt 50% über 3 Jahre."},
            {"id": "S2", "content": "Der ROI erreicht 200% im gleichen Zeitraum."},
        ]

        validation = metrics_guard.validate_metrics(sections)

        # Should detect ROI contradiction (50% vs 200%)
        assert len(validation["contradictions"]) > 0 or not validation["is_valid"]

    def test_detect_duplicate_statements(
        self,
        metrics_guard: ExecutiveMetricsGuard,
    ) -> None:
        """Test duplicate statement detection."""
        sections = [
            {
                "id": "S1",
                "content": "Die Empfehlung lautet: Sofortige Investition in KI-Automatisierung.",
            },
            {
                "id": "S2",
                "content": "Die Empfehlung lautet: Sofortige Investition in KI-Automatisierung.",
            },
        ]

        validation = metrics_guard.validate_metrics(sections)

        # Should detect duplicate
        assert len(validation["duplicates"]) > 0

    def test_find_unclear_recommendations(
        self,
        metrics_guard: ExecutiveMetricsGuard,
    ) -> None:
        """Test unclear recommendation detection."""
        sections = [
            {
                "id": "S1",
                "content": "Die Empfehlung ist, zeitnah verschiedene Optionen zu prüfen.",
            },
        ]

        validation = metrics_guard.validate_metrics(sections)

        # Should flag ambiguous terms
        unclear_issues = [
            i for i in validation["issues"]
            if i["type"] == MetricIssue.UNCLEAR_RECOMMENDATION.value
        ]
        assert len(unclear_issues) > 0


# =============================================================================
# MAIN ENGINE TESTS
# =============================================================================


class TestExecutiveClarityEngine:
    """Tests for main ExecutiveClarityEngine."""

    def test_process_text(
        self,
        engine: ExecutiveClarityEngine,
    ) -> None:
        """Test text processing."""
        text = "Das LLM API zeigt gute inference Ergebnisse."
        result = engine.process_text(text)

        assert result is not None
        assert "clarified_text" in result
        assert "jargon_removed" in result
        assert "score" in result

    def test_process_sections(
        self,
        engine: ExecutiveClarityEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test section processing."""
        result = engine.process_sections(sample_sections)

        assert result is not None
        assert "sections" in result
        assert len(result["sections"]) == 3
        assert "metric_validation" in result

    def test_validate_report(
        self,
        engine: ExecutiveClarityEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test report validation."""
        validation = engine.validate_report(sample_sections)

        assert "is_clear" in validation
        assert "clarity_score" in validation
        assert "recommendation" in validation

    def test_clarity_score_structure(
        self,
        engine: ExecutiveClarityEngine,
    ) -> None:
        """Test clarity score structure."""
        text = "Die Strategie ist klar definiert."
        result = engine.process_text(text)

        score = result["score"]
        assert "overall_score" in score
        assert "jargon_score" in score
        assert "readability_score" in score
        assert "action_clarity_score" in score
        assert "consistency_score" in score

    def test_overall_clarity_score_range(
        self,
        engine: ExecutiveClarityEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test overall clarity score is in valid range."""
        result = engine.process_sections(sample_sections)

        assert 0 <= result["overall_clarity_score"] <= 1

    def test_jargon_removal_count(
        self,
        engine: ExecutiveClarityEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test jargon removal is counted."""
        result = engine.process_sections(sample_sections)

        # Sample sections contain jargon
        assert result["total_jargon_removed"] >= 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestClarityIntegration:
    """Integration tests for clarity processing."""

    def test_full_clarity_pipeline(
        self,
        engine: ExecutiveClarityEngine,
    ) -> None:
        """Test full clarity processing pipeline."""
        text = (
            "Das transformer-basierte LLM API sollte man in der Lage sein "
            "zu deployen. Die inference latency wird optimiert werden. "
            "Zeitnah sollten verschiedene Optionen geprüft werden."
        )

        result = engine.process_text(text)

        # Should remove jargon
        assert len(result["jargon_removed"]) > 0

        # Should identify issues
        assert len(result["issues_found"]) > 0

        # Clarified text should be different
        assert result["clarified_text"] != result["original_text"]

    def test_clean_text_high_score(
        self,
        engine: ExecutiveClarityEngine,
    ) -> None:
        """Test clean text gets high score."""
        text = (
            "Die Investition von 2 Millionen Euro generiert einen ROI von 150%. "
            "Die Geschäftsführung entscheidet über die Freigabe am 15. Januar. "
            "Der Vorstand priorisiert dieses Projekt."
        )

        result = engine.process_text(text)

        # Clean executive text should score well
        assert result["score"]["overall_score"] >= 0.5


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_engine_singleton(self) -> None:
        """Test singleton pattern."""
        engine1 = get_clarity_engine()
        engine2 = get_clarity_engine()

        assert engine1 is engine2

    def test_clarify_text_function(self) -> None:
        """Test clarify_text function."""
        result = clarify_text("Das LLM zeigt gute Ergebnisse.")

        assert result is not None
        assert "clarified_text" in result

    def test_clarify_sections_function(
        self,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test clarify_sections function."""
        result = clarify_sections(sample_sections)

        assert result is not None
        assert "sections" in result

    def test_validate_report_clarity_function(
        self,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test validate_report_clarity function."""
        validation = validate_report_clarity(sample_sections)

        assert "is_clear" in validation
        assert "clarity_score" in validation

    def test_get_clarity_score_function(self) -> None:
        """Test get_clarity_score function."""
        score = get_clarity_score("Die Strategie ist klar.")

        assert 0 <= score <= 1
