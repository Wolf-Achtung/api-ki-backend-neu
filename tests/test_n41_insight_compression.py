"""
Tests for Insight Compression Engine - N4.1 PLATIN+++ Executive Experience Layer.

Tests cover:
- Pyramid structure building
- MECE validation
- Duplicate filtering
- Tone harmonization
- Key insight extraction

25 comprehensive tests for McKinsey-quality compression.
"""

import pytest
from typing import Any, Dict, List

from services.insight_compression_engine import (
    InsightCompressionEngine,
    PyramidStructureBuilder,
    DuplicateSignalFilter,
    ToneHarmonizer,
    TextAnalyzer,
    InsightType,
    get_compression_engine,
    compress_to_pyramid,
    get_key_insight,
    validate_mece_compliance,
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
                "Die Analyse zeigt erhebliche Automatisierungspotenziale von 45%. "
                "Erstens können Dokumentenprozesse vollständig automatisiert werden. "
                "Zweitens bietet die Datenverarbeitung signifikante Effizienzgewinne. "
                "Drittens ermöglicht KI-Integration Kosteneinsparungen von 3.2 Mio EUR. "
                "Die ROI-Prognose liegt bei 145% über 3 Jahre. "
                "Empfehlung: Sofortige Investitionsfreigabe."
            ),
        },
        {
            "id": "G5",
            "content": (
                "Die strategische Positionierung erfordert proaktives Handeln. "
                "Der Wettbewerb investiert massiv in KI-Lösungen. "
                "Marktanteile können um 15% gesteigert werden. "
                "Die Kernempfehlung lautet: Differenzierung durch Prozessexzellenz."
            ),
        },
        {
            "id": "G10",
            "content": (
                "Die Risikobewertung identifiziert moderate Compliance-Anforderungen. "
                "AI Act Risikoklasse: LIMITED. "
                "DSGVO-Compliance steht bei 80%. "
                "Governance-Strukturen müssen etabliert werden."
            ),
        },
    ]


@pytest.fixture
def engine() -> InsightCompressionEngine:
    """Fresh compression engine."""
    return InsightCompressionEngine()


@pytest.fixture
def pyramid_builder() -> PyramidStructureBuilder:
    """Fresh pyramid builder."""
    return PyramidStructureBuilder()


@pytest.fixture
def text_analyzer() -> TextAnalyzer:
    """Fresh text analyzer."""
    return TextAnalyzer()


# =============================================================================
# TEXT ANALYZER TESTS
# =============================================================================


class TestTextAnalyzer:
    """Tests for TextAnalyzer."""

    def test_split_sentences(self, text_analyzer: TextAnalyzer) -> None:
        """Test sentence splitting."""
        text = "Erster Satz. Zweiter Satz! Dritter Satz?"
        sentences = text_analyzer.split_sentences(text)

        assert len(sentences) == 3

    def test_count_words(self, text_analyzer: TextAnalyzer) -> None:
        """Test word counting."""
        text = "Dies ist ein einfacher Test"
        count = text_analyzer.count_words(text)

        assert count == 5

    def test_truncate_to_words(self, text_analyzer: TextAnalyzer) -> None:
        """Test word truncation."""
        text = "Eins zwei drei vier fünf sechs sieben acht"
        truncated = text_analyzer.truncate_to_words(text, 5)

        assert truncated.endswith("...")
        assert "sechs" not in truncated

    def test_calculate_similarity(self, text_analyzer: TextAnalyzer) -> None:
        """Test similarity calculation."""
        text1 = "Die Analyse zeigt Potenziale"
        text2 = "Die Analyse zeigt Ergebnisse"

        similarity = text_analyzer.calculate_similarity(text1, text2)

        assert 0 < similarity < 1

    def test_extract_key_terms(self, text_analyzer: TextAnalyzer) -> None:
        """Test key term extraction."""
        text = "Automatisierung Automatisierung Prozesse Effizienz Automatisierung"
        terms = text_analyzer.extract_key_terms(text, 3)

        assert "automatisierung" in terms
        assert len(terms) <= 3


# =============================================================================
# PYRAMID STRUCTURE BUILDER TESTS
# =============================================================================


class TestPyramidStructureBuilder:
    """Tests for PyramidStructureBuilder."""

    def test_build_pyramid_basic(
        self,
        pyramid_builder: PyramidStructureBuilder,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test basic pyramid building."""
        section = sample_sections[0]
        pyramid = pyramid_builder.build_pyramid(section["id"], section["content"])

        assert pyramid is not None
        assert pyramid["section_id"] == "G1"
        assert len(pyramid["top_line"]) > 0

    def test_pyramid_has_sub_arguments(
        self,
        pyramid_builder: PyramidStructureBuilder,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test pyramid contains sub-arguments."""
        section = sample_sections[0]
        pyramid = pyramid_builder.build_pyramid(section["id"], section["content"])

        assert len(pyramid["sub_arguments"]) >= 1

    def test_pyramid_has_evidence(
        self,
        pyramid_builder: PyramidStructureBuilder,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test pyramid contains evidence."""
        section = sample_sections[0]
        pyramid = pyramid_builder.build_pyramid(section["id"], section["content"])

        # Section contains numbers, should have evidence
        assert len(pyramid["evidence_items"]) >= 1

    def test_compressed_insight_structure(
        self,
        pyramid_builder: PyramidStructureBuilder,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test compressed insight structure."""
        section = sample_sections[0]
        pyramid = pyramid_builder.build_pyramid(section["id"], section["content"])

        insight = pyramid["compressed_insight"]
        assert "key_insight" in insight
        assert "evidence_points" in insight
        assert "leadership_action" in insight
        assert "insight_type" in insight
        assert "confidence" in insight

    def test_mece_score_calculation(
        self,
        pyramid_builder: PyramidStructureBuilder,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test MECE score is calculated."""
        section = sample_sections[0]
        pyramid = pyramid_builder.build_pyramid(section["id"], section["content"])

        assert 0 <= pyramid["mece_score"] <= 1

    def test_insight_type_financial(
        self,
        pyramid_builder: PyramidStructureBuilder,
    ) -> None:
        """Test financial insight type detection."""
        content = "ROI von 150%. Kosteneinsparung 5 Mio EUR. EBIT-Verbesserung erwartet."
        pyramid = pyramid_builder.build_pyramid("fin_test", content)

        assert pyramid["compressed_insight"]["insight_type"] == InsightType.FINANCIAL.value

    def test_insight_type_risk(
        self,
        pyramid_builder: PyramidStructureBuilder,
    ) -> None:
        """Test risk insight type detection."""
        content = "Compliance-Risiken durch AI Act. Governance erforderlich. DSGVO-Lücken."
        pyramid = pyramid_builder.build_pyramid("risk_test", content)

        assert pyramid["compressed_insight"]["insight_type"] == InsightType.RISK.value


# =============================================================================
# DUPLICATE SIGNAL FILTER TESTS
# =============================================================================


class TestDuplicateSignalFilter:
    """Tests for DuplicateSignalFilter."""

    def test_filter_duplicates(self) -> None:
        """Test duplicate filtering."""
        filter_instance = DuplicateSignalFilter()

        # Create pyramids with similar top lines
        pyramids = [
            {
                "section_id": "1",
                "top_line": "Die Analyse zeigt erhebliche Automatisierungspotenziale",
                "sub_arguments": [],
                "evidence_items": [],
                "compressed_insight": {
                    "key_insight": "",
                    "evidence_points": [],
                    "leadership_action": "",
                    "insight_type": "",
                    "confidence": 0.5,
                },
                "mece_score": 0.7,
            },
            {
                "section_id": "2",
                "top_line": "Die Analyse zeigt signifikante Automatisierungspotenziale",
                "sub_arguments": [],
                "evidence_items": [],
                "compressed_insight": {
                    "key_insight": "",
                    "evidence_points": [],
                    "leadership_action": "",
                    "insight_type": "",
                    "confidence": 0.5,
                },
                "mece_score": 0.7,
            },
        ]

        filtered = filter_instance.filter_pyramids(pyramids)

        # Should filter one as duplicate
        assert len(filtered) < len(pyramids)

    def test_reset_filter(self) -> None:
        """Test filter reset."""
        filter_instance = DuplicateSignalFilter()

        filter_instance.register("Test insight")
        assert filter_instance.is_duplicate("Test insight")

        filter_instance.reset()
        assert not filter_instance.is_duplicate("Test insight")


# =============================================================================
# TONE HARMONIZER TESTS
# =============================================================================


class TestToneHarmonizer:
    """Tests for ToneHarmonizer."""

    def test_harmonize_informal_phrases(self) -> None:
        """Test informal phrase replacement."""
        harmonizer = ToneHarmonizer()
        text = "Man sollte die Strategie anpassen."

        result = harmonizer.harmonize(text)

        assert "man sollte" not in result.lower()

    def test_harmonize_removes_filler(self) -> None:
        """Test filler word removal."""
        harmonizer = ToneHarmonizer()
        text = "Das ist eigentlich quasi ein wichtiger Punkt."

        result = harmonizer.harmonize(text)

        assert "eigentlich" not in result
        assert "quasi" not in result

    def test_harmonize_preserves_meaning(self) -> None:
        """Test that harmonization preserves core meaning."""
        harmonizer = ToneHarmonizer()
        text = "Die Investition wird empfohlen."

        result = harmonizer.harmonize(text)

        assert "Investition" in result


# =============================================================================
# MAIN ENGINE TESTS
# =============================================================================


class TestInsightCompressionEngine:
    """Tests for main InsightCompressionEngine."""

    def test_compress_sections(
        self,
        engine: InsightCompressionEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test section compression."""
        result = engine.compress_sections(sample_sections)

        assert result is not None
        assert result["total_sections"] == 3
        assert len(result["pyramids"]) > 0

    def test_compression_ratio(
        self,
        engine: InsightCompressionEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test compression ratio is calculated."""
        result = engine.compress_sections(sample_sections)

        assert 0 < result["compression_ratio"] < 1

    def test_quality_score(
        self,
        engine: InsightCompressionEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test quality score is calculated."""
        result = engine.compress_sections(sample_sections)

        assert 0 <= result["quality_score"] <= 1

    def test_compress_single_section(
        self,
        engine: InsightCompressionEngine,
    ) -> None:
        """Test single section compression."""
        content = "Die Empfehlung ist klar: Investition freigeben. ROI von 120%."
        pyramid = engine.compress_single_section("test", content)

        assert pyramid is not None
        assert pyramid["section_id"] == "test"

    def test_get_key_insights(
        self,
        engine: InsightCompressionEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test key insight extraction."""
        insights = engine.get_key_insights(sample_sections)

        assert len(insights) > 0
        assert all("key_insight" in i for i in insights)

    def test_validate_mece(
        self,
        engine: InsightCompressionEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test MECE validation."""
        result = engine.compress_sections(sample_sections)
        validation = engine.validate_mece(result["pyramids"])

        assert "is_valid" in validation
        assert "average_mece_score" in validation


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_engine_singleton(self) -> None:
        """Test singleton pattern."""
        engine1 = get_compression_engine()
        engine2 = get_compression_engine()

        assert engine1 is engine2

    def test_compress_to_pyramid_function(
        self,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test compress_to_pyramid function."""
        result = compress_to_pyramid(sample_sections)

        assert result is not None
        assert "pyramids" in result

    def test_get_key_insight_function(self) -> None:
        """Test get_key_insight function."""
        content = "Die strategische Empfehlung: Investieren. ROI erwartet 150%."
        insight = get_key_insight("test", content)

        assert insight is not None
        assert "key_insight" in insight

    def test_validate_mece_compliance_function(
        self,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test validate_mece_compliance function."""
        validation = validate_mece_compliance(sample_sections)

        assert "is_valid" in validation
        assert "total_sections" in validation
