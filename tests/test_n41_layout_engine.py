"""
Tests for Executive Layout Engine - N4.1 PLATIN+++ Executive Experience Layer.

Tests cover:
- Height estimation
- Page break optimization
- White space management
- Card layout building
- Font specifications

20 comprehensive tests for PDF experience.
"""

import pytest
from typing import Any, Dict, List

from services.executive_layout_engine import (
    ExecutiveLayoutEngine,
    HeightEstimator,
    PageBreakOptimizer,
    WhiteSpaceManager,
    CardLayoutBuilder,
    ElementType,
    CardType,
    PageBreakRule,
    get_layout_engine,
    process_layout,
    create_card,
    get_font_spec,
    LAYOUT_CONFIG,
    FONT_SCALE,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def sample_elements() -> List[Dict[str, Any]]:
    """Sample content elements for testing."""
    return [
        {"type": "section_head", "content": "Executive Summary"},
        {"type": "paragraph", "content": "Dies ist ein Absatz mit wichtigen Informationen. " * 5},
        {"type": "table", "content": {"rows": 5, "columns": 4}},
        {"type": "kpi_visual", "content": {"count": 6}},
        {"type": "subsection", "content": "Strategische Analyse"},
        {"type": "paragraph", "content": "Weitere Details zur Analyse. " * 10},
        {"type": "roadmap", "content": {"phases": 4}},
    ]


@pytest.fixture
def engine() -> ExecutiveLayoutEngine:
    """Fresh layout engine."""
    return ExecutiveLayoutEngine()


@pytest.fixture
def height_estimator() -> HeightEstimator:
    """Fresh height estimator."""
    return HeightEstimator()


@pytest.fixture
def card_builder() -> CardLayoutBuilder:
    """Fresh card builder."""
    return CardLayoutBuilder()


# =============================================================================
# HEIGHT ESTIMATOR TESTS
# =============================================================================


class TestHeightEstimator:
    """Tests for HeightEstimator."""

    def test_estimate_section_head(self, height_estimator: HeightEstimator) -> None:
        """Test section head height estimation."""
        height = height_estimator.estimate(ElementType.SECTION_HEAD, "Test Heading")

        assert height > 0
        assert height < 100

    def test_estimate_paragraph(self, height_estimator: HeightEstimator) -> None:
        """Test paragraph height estimation."""
        short_text = "Short paragraph."
        long_text = "Long paragraph with many words. " * 20

        short_height = height_estimator.estimate(ElementType.PARAGRAPH, short_text)
        long_height = height_estimator.estimate(ElementType.PARAGRAPH, long_text)

        assert long_height > short_height

    def test_estimate_table(self, height_estimator: HeightEstimator) -> None:
        """Test table height estimation."""
        content = {"rows": 10, "columns": 4}
        height = height_estimator.estimate(ElementType.TABLE, content)

        assert height > 200  # Tables should have significant height

    def test_estimate_kpi_visual(self, height_estimator: HeightEstimator) -> None:
        """Test KPI visual height estimation."""
        content = {"count": 9}  # 3 rows of 3
        height = height_estimator.estimate(ElementType.KPI_VISUAL, content)

        assert height > 200


# =============================================================================
# PAGE BREAK OPTIMIZER TESTS
# =============================================================================


class TestPageBreakOptimizer:
    """Tests for PageBreakOptimizer."""

    def test_optimize_breaks_creates_pages(self) -> None:
        """Test that optimizer creates pages."""
        optimizer = PageBreakOptimizer()

        elements = [
            {
                "id": "elem_1",
                "element_type": "section_head",
                "content": "Test",
                "height_estimate": 50,
                "page_break_rule": PageBreakRule.ALWAYS_BEFORE.value,
                "margin_before": 36,
                "margin_after": 18,
            },
            {
                "id": "elem_2",
                "element_type": "paragraph",
                "content": "Content",
                "height_estimate": 100,
                "page_break_rule": PageBreakRule.ALLOW_BREAK.value,
                "margin_before": 6,
                "margin_after": 6,
            },
        ]

        pages = optimizer.optimize_breaks(elements)

        assert len(pages) >= 1
        assert pages[0]["page_number"] == 1

    def test_section_head_forces_page_break(self) -> None:
        """Test that section heads force page breaks."""
        optimizer = PageBreakOptimizer()

        elements = [
            {
                "id": "elem_1",
                "element_type": "paragraph",
                "content": "First content",
                "height_estimate": 100,
                "page_break_rule": PageBreakRule.ALLOW_BREAK.value,
                "margin_before": 6,
                "margin_after": 6,
            },
            {
                "id": "elem_2",
                "element_type": "section_head",
                "content": "New Section",
                "height_estimate": 50,
                "page_break_rule": PageBreakRule.ALWAYS_BEFORE.value,
                "margin_before": 36,
                "margin_after": 18,
            },
        ]

        pages = optimizer.optimize_breaks(elements)

        # Section head should be on second page
        assert len(pages) >= 2

    def test_page_fill_percentage(self) -> None:
        """Test page fill percentage calculation."""
        optimizer = PageBreakOptimizer()

        elements = [
            {
                "id": "elem_1",
                "element_type": "paragraph",
                "content": "Content",
                "height_estimate": 200,
                "page_break_rule": PageBreakRule.ALLOW_BREAK.value,
                "margin_before": 10,
                "margin_after": 10,
            },
        ]

        pages = optimizer.optimize_breaks(elements)

        assert 0 < pages[0]["fill_percentage"] < 1


# =============================================================================
# WHITE SPACE MANAGER TESTS
# =============================================================================


class TestWhiteSpaceManager:
    """Tests for WhiteSpaceManager."""

    def test_calculate_overall_score(self) -> None:
        """Test overall white space score calculation."""
        manager = WhiteSpaceManager()

        pages = [
            {"page_number": 1, "elements": [], "fill_percentage": 0.75, "white_space_score": 0.8},
            {"page_number": 2, "elements": [], "fill_percentage": 0.80, "white_space_score": 0.9},
        ]

        score = manager.calculate_overall_score(pages)

        assert 0 <= score <= 1
        assert score == pytest.approx(0.85)  # Average of 0.8 and 0.9

    def test_empty_pages_score(self) -> None:
        """Test score for empty pages list."""
        manager = WhiteSpaceManager()
        score = manager.calculate_overall_score([])

        assert score == 0.0


# =============================================================================
# CARD LAYOUT BUILDER TESTS
# =============================================================================


class TestCardLayoutBuilder:
    """Tests for CardLayoutBuilder."""

    def test_build_tool_card(self, card_builder: CardLayoutBuilder) -> None:
        """Test tool card building."""
        card = card_builder.build_tool_card(
            tool_name="ChatGPT",
            description="KI-Assistent für Textgenerierung",
            category="Text",
            score=85,
        )

        assert card["card_type"] == CardType.TOOL_CARD.value
        assert card["title"] == "ChatGPT"
        assert len(card["content_blocks"]) >= 3

    def test_build_funding_card(self, card_builder: CardLayoutBuilder) -> None:
        """Test funding card building."""
        card = card_builder.build_funding_card(
            program_name="KI-Förderprogramm",
            amount="500.000 EUR",
            deadline="31.12.2024",
            eligibility="KMU",
        )

        assert card["card_type"] == CardType.FUNDING_CARD.value
        assert card["title"] == "KI-Förderprogramm"

    def test_build_kpi_card(self, card_builder: CardLayoutBuilder) -> None:
        """Test KPI card building."""
        card = card_builder.build_kpi_card(
            kpi_name="ROI",
            value="145%",
            trend="steigend",
            benchmark="100%",
        )

        assert card["card_type"] == CardType.KPI_CARD.value
        assert card["title"] == "ROI"

    def test_build_risk_card(self, card_builder: CardLayoutBuilder) -> None:
        """Test risk card building."""
        card = card_builder.build_risk_card(
            risk_name="AI Act Compliance",
            severity="hoch",
            probability="mittel",
            mitigation="Governance Framework",
        )

        assert card["card_type"] == CardType.RISK_CARD.value

    def test_card_has_accent_color(self, card_builder: CardLayoutBuilder) -> None:
        """Test cards have accent colors."""
        card = card_builder.build_kpi_card(
            kpi_name="Test",
            value="100",
            trend="neutral",
        )

        assert "accent_color" in card
        assert card["accent_color"].startswith("#")


# =============================================================================
# MAIN ENGINE TESTS
# =============================================================================


class TestExecutiveLayoutEngine:
    """Tests for main ExecutiveLayoutEngine."""

    def test_process_layout(
        self,
        engine: ExecutiveLayoutEngine,
        sample_elements: List[Dict[str, Any]],
    ) -> None:
        """Test complete layout processing."""
        result = engine.process_layout(sample_elements)

        assert result is not None
        assert "total_pages" in result
        assert "pages" in result
        assert "layout_score" in result

    def test_create_element(self, engine: ExecutiveLayoutEngine) -> None:
        """Test element creation."""
        element = engine.create_element(
            ElementType.SECTION_HEAD,
            "Test Heading",
        )

        assert element["element_type"] == ElementType.SECTION_HEAD.value
        assert element["height_estimate"] > 0

    def test_create_card(self, engine: ExecutiveLayoutEngine) -> None:
        """Test card creation through engine."""
        card = engine.create_card(
            CardType.KPI_CARD,
            kpi_name="ROI",
            value="145%",
            trend="steigend",
        )

        assert card["card_type"] == CardType.KPI_CARD.value

    def test_get_font_spec(self, engine: ExecutiveLayoutEngine) -> None:
        """Test font specification retrieval."""
        headline_spec = engine.get_font_spec("headline")
        body_spec = engine.get_font_spec("body")

        assert headline_spec["effective_size"] > body_spec["effective_size"]

    def test_layout_score_range(
        self,
        engine: ExecutiveLayoutEngine,
        sample_elements: List[Dict[str, Any]],
    ) -> None:
        """Test layout score is in valid range."""
        result = engine.process_layout(sample_elements)

        assert 0 <= result["layout_score"] <= 1

    def test_white_space_score_range(
        self,
        engine: ExecutiveLayoutEngine,
        sample_elements: List[Dict[str, Any]],
    ) -> None:
        """Test white space score is in valid range."""
        result = engine.process_layout(sample_elements)

        assert 0 <= result["white_space_score"] <= 1


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_engine_singleton(self) -> None:
        """Test singleton pattern."""
        engine1 = get_layout_engine()
        engine2 = get_layout_engine()

        assert engine1 is engine2

    def test_process_layout_function(
        self,
        sample_elements: List[Dict[str, Any]],
    ) -> None:
        """Test process_layout function."""
        result = process_layout(sample_elements)

        assert result is not None
        assert "pages" in result

    def test_create_card_function(self) -> None:
        """Test create_card function."""
        card = create_card(
            CardType.TOOL_CARD,
            tool_name="Test Tool",
            description="A test tool",
            category="Testing",
        )

        assert card is not None
        assert card["card_type"] == CardType.TOOL_CARD.value

    def test_get_font_spec_function(self) -> None:
        """Test get_font_spec function."""
        spec = get_font_spec("headline")

        assert spec is not None
        assert "effective_size" in spec
        assert spec["scale_factor"] == 1.06  # +6% for headlines
