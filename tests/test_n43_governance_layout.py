# -*- coding: utf-8 -*-
"""
N4.3 Test Suite: Governance Layout Engine v1
============================================

Tests for services/governance_layout_engine.py

Coverage:
- Policy card rendering
- Governance matrix layout
- Compliance badge positioning
- Page break logic
- Risk visual cues
- Multi-language support

Target: ~15 tests

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
"""

import pytest
from typing import Dict, Any

from services.governance_layout_engine import (
    CardStyle,
    BadgeType,
    LayoutMode,
    RiskVisualStyle,
    PolicyCardLayout,
    MatrixCell,
    GovernanceMatrixLayout,
    ComplianceBadge,
    PageBreakPoint,
    RiskVisualCue,
    GovernanceLayoutEngineV1,
    render_policy_card,
    render_governance_matrix,
    position_compliance_badges,
    calculate_page_breaks,
    generate_risk_visual_cues,
    get_card_template,
    validate_layout,
    RISK_COLORS,
    MATURITY_COLORS,
    LAYOUT_LABELS,
)
from services.language_strategy_engine import SupportedLanguage


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Sample sections for testing."""
    return {
        "executive_summary": "AI implementation with ROI 150%",
        "_governance_score": {
            "overall_score": 75,
            "maturity_level": "defined",
        },
        "_governance_matrix": {
            "risk_class": "minimal",
            "iso42001_mapping": {
                "context": {"compliance_level": "partial", "controls": []},
                "leadership": {"compliance_level": "compliant", "controls": []},
            },
            "nist_rmf_mapping": {
                "govern": {"maturity": "defined"},
                "map": {"maturity": "developing"},
            },
        },
        "_policy_cards": [
            {"card_id": "PC-001", "title": "Risk", "status": "compliant", "score": 80},
        ],
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing for testing."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
    }


@pytest.fixture
def sample_card() -> Dict[str, Any]:
    """Sample policy card data."""
    return {
        "card_id": "PC-001",
        "title": "Risk Classification",
        "summary": "Minimal risk AI system",
        "status": "compliant",
        "score": 85,
        "primary_color": "#28a745",
        "secondary_color": "#d4edda",
    }


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestLayoutEnums:
    """Tests for layout enums."""

    def test_card_style_values(self):
        """All card styles should be defined."""
        assert CardStyle.EXECUTIVE.value == "executive"
        assert CardStyle.DETAILED.value == "detailed"
        assert CardStyle.COMPACT.value == "compact"
        assert CardStyle.BOARD.value == "board"

    def test_badge_type_values(self):
        """All badge types should be defined."""
        assert BadgeType.COMPLIANCE.value == "compliance"
        assert BadgeType.RISK.value == "risk"
        assert BadgeType.MATURITY.value == "maturity"

    def test_layout_mode_values(self):
        """All layout modes should be defined."""
        assert LayoutMode.PDF.value == "pdf"
        assert LayoutMode.HTML.value == "html"
        assert LayoutMode.MARKDOWN.value == "markdown"

    def test_risk_visual_style_values(self):
        """All visual styles should be defined."""
        assert RiskVisualStyle.TRAFFIC_LIGHT.value == "traffic_light"
        assert RiskVisualStyle.BADGE.value == "badge"


# =============================================================================
# TEST CLASS: Constants
# =============================================================================

class TestLayoutConstants:
    """Tests for layout constants."""

    def test_risk_colors_exist(self):
        """Risk colors should be defined."""
        assert "minimal" in RISK_COLORS
        assert "limited" in RISK_COLORS
        assert "high" in RISK_COLORS

    def test_risk_color_structure(self):
        """Risk colors should have required keys."""
        minimal = RISK_COLORS["minimal"]
        assert "primary" in minimal
        assert "secondary" in minimal
        assert "icon" in minimal

    def test_maturity_colors_exist(self):
        """Maturity colors should be defined."""
        assert "initial" in MATURITY_COLORS
        assert "optimizing" in MATURITY_COLORS

    def test_layout_labels_multilanguage(self):
        """Layout labels should support multiple languages."""
        assert SupportedLanguage.DE in LAYOUT_LABELS
        assert SupportedLanguage.EN in LAYOUT_LABELS
        assert "risk_level" in LAYOUT_LABELS[SupportedLanguage.EN]


# =============================================================================
# TEST CLASS: Policy Card Rendering
# =============================================================================

class TestPolicyCardRendering:
    """Tests for policy card rendering."""

    def test_render_card_html(self, sample_card):
        """Should render card as HTML."""
        html = render_policy_card(
            card=sample_card,
            style="executive",
            language="en",
            layout_mode="html",
        )
        assert "policy-card" in html
        assert sample_card["title"] in html

    def test_render_card_markdown(self, sample_card):
        """Should render card as Markdown."""
        md = render_policy_card(
            card=sample_card,
            style="executive",
            language="en",
            layout_mode="markdown",
        )
        assert "###" in md or sample_card["title"] in md

    def test_render_card_german(self, sample_card):
        """Should render card in German."""
        html = render_policy_card(
            card=sample_card,
            style="executive",
            language="de",
            layout_mode="html",
        )
        assert isinstance(html, str)


# =============================================================================
# TEST CLASS: Governance Matrix
# =============================================================================

class TestGovernanceMatrix:
    """Tests for governance matrix rendering."""

    def test_render_matrix_html(self):
        """Should render matrix as HTML."""
        matrix = {
            "matrix_id": "MATRIX_001",
            "title": "ISO 42001 Compliance",
            "headers": ["Domain", "Status", "Score"],
            "rows": 2,
            "cells": [
                {"row": 0, "col": 0, "content": "Context"},
                {"row": 0, "col": 1, "content": "Partial"},
                {"row": 0, "col": 2, "content": "60%"},
                {"row": 1, "col": 0, "content": "Leadership"},
                {"row": 1, "col": 1, "content": "Compliant"},
                {"row": 1, "col": 2, "content": "90%"},
            ],
        }
        html = render_governance_matrix(matrix, format="html", language="en")
        assert "<table" in html
        assert "Context" in html

    def test_render_matrix_markdown(self):
        """Should render matrix as Markdown."""
        matrix = {
            "title": "Test Matrix",
            "headers": ["A", "B"],
            "rows": 1,
            "cells": [
                {"row": 0, "col": 0, "content": "1"},
                {"row": 0, "col": 1, "content": "2"},
            ],
        }
        md = render_governance_matrix(matrix, format="markdown", language="en")
        assert "|" in md


# =============================================================================
# TEST CLASS: Compliance Badges
# =============================================================================

class TestComplianceBadges:
    """Tests for compliance badge positioning."""

    def test_position_badges(self, sample_sections):
        """Should position badges in sections."""
        badges = [
            {"badge_id": "B1", "section": "executive_summary", "label": "Risk"},
            {"badge_id": "B2", "section": "governance", "label": "Maturity"},
        ]
        positioned = position_compliance_badges(sample_sections, badges)
        assert "executive_summary" in positioned
        assert len(positioned["executive_summary"]) == 1


# =============================================================================
# TEST CLASS: Page Breaks
# =============================================================================

class TestPageBreaks:
    """Tests for page break calculation."""

    def test_calculate_page_breaks(self, sample_sections):
        """Should calculate page breaks."""
        breaks = calculate_page_breaks(
            sections=sample_sections,
            max_height=247,
            layout_mode="pdf",
        )
        assert isinstance(breaks, list)


# =============================================================================
# TEST CLASS: Risk Visual Cues
# =============================================================================

class TestRiskVisualCues:
    """Tests for risk visual cue generation."""

    def test_generate_minimal_risk_cue(self):
        """Should generate minimal risk cue."""
        cue = generate_risk_visual_cues(
            risk_class="minimal",
            style="traffic_light",
            language="en",
        )
        assert cue["risk_class"] == "minimal"
        assert cue["color"] == RISK_COLORS["minimal"]["primary"]

    def test_generate_high_risk_cue(self):
        """Should generate high risk cue."""
        cue = generate_risk_visual_cues(
            risk_class="high",
            style="badge",
            language="de",
        )
        assert cue["risk_class"] == "high"


# =============================================================================
# TEST CLASS: Card Templates
# =============================================================================

class TestCardTemplates:
    """Tests for card templates."""

    def test_get_executive_template(self):
        """Should get executive template."""
        template = get_card_template(style="executive", language="en")
        assert template["style"] == "executive"
        assert "dimensions" in template

    def test_get_board_template(self):
        """Should get board template."""
        template = get_card_template(style="board", language="de")
        assert template["style"] == "board"


# =============================================================================
# TEST CLASS: Engine Processing
# =============================================================================

class TestEngineProcessing:
    """Tests for engine processing."""

    def test_engine_init(self, sample_sections, sample_briefing):
        """Engine should initialize."""
        engine = GovernanceLayoutEngineV1(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        assert engine is not None

    def test_engine_process(self, sample_sections, sample_briefing):
        """Engine should process sections."""
        engine = GovernanceLayoutEngineV1(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()

        assert isinstance(result_sections, dict)
        assert report.engine_id == "GOVERNANCE_LAYOUT_V1"

    def test_engine_generates_cards(self, sample_sections, sample_briefing):
        """Engine should generate policy cards."""
        engine = GovernanceLayoutEngineV1(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()

        assert report.cards_rendered >= 0
        assert "_policy_card_layouts" in result_sections


# =============================================================================
# TEST CLASS: Validation
# =============================================================================

class TestLayoutValidation:
    """Tests for layout validation."""

    def test_validate_layout(self, sample_sections):
        """Should validate layout."""
        is_valid, messages = validate_layout(
            sections=sample_sections,
            layout_mode="pdf",
        )
        assert isinstance(is_valid, bool)
        assert isinstance(messages, list)
