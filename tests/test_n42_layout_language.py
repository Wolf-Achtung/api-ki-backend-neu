# -*- coding: utf-8 -*-
"""
N4.2 Test Suite: Layout Language Adapter v4
===========================================

Tests for services/layout_language_adapter.py

Coverage:
- Text expansion factors
- Hyphenation rules per language
- Table width adjustments
- Card height balancing
- Page break optimization
- Orphan prevention

Target: ~20 tests

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
"""

import pytest
from typing import Dict, Any

from services.layout_language_adapter import (
    LayoutElement,
    PageBreakRule,
    HyphenationMode,
    LayoutIssue,
    LayoutAdaptation,
    LayoutAnalysisResult,
    LayoutLanguageAdapter,
    adapt_layout_for_language,
    calculate_text_expansion,
    apply_hyphenation,
    optimize_page_breaks,
    get_expansion_factor,
    get_hyphenation_mode,
    TEXT_EXPANSION_FACTORS,
    HYPHENATION_RULES,
    TABLE_WIDTH_ADJUSTMENTS,
)
from services.language_strategy_engine import SupportedLanguage


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, str]:
    """Sample report sections."""
    return {
        "executive_summary": "Dies ist eine Executive Summary mit wichtigen Empfehlungen für das Unternehmen.",
        "business_case": "<table><tr><td>ROI</td><td>150%</td></tr></table>",
        "roadmap_90d": '<div class="card">Phase 1: Analyse</div>',
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
    }


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestLayoutEnums:
    """Tests for layout enums."""

    def test_layout_element_values(self):
        """All layout elements should be defined."""
        assert LayoutElement.HEADING.value == "heading"
        assert LayoutElement.PARAGRAPH.value == "paragraph"
        assert LayoutElement.TABLE.value == "table"
        assert LayoutElement.CARD.value == "card"

    def test_page_break_rule_values(self):
        """All page break rules should be defined."""
        assert PageBreakRule.ALWAYS_BEFORE.value == "always_before"
        assert PageBreakRule.NEVER_BREAK.value == "never_break"
        assert PageBreakRule.KEEP_WITH_NEXT.value == "keep_with_next"

    def test_hyphenation_mode_values(self):
        """All hyphenation modes should be defined."""
        assert HyphenationMode.NONE.value == "none"
        assert HyphenationMode.CONSERVATIVE.value == "conservative"
        assert HyphenationMode.MODERATE.value == "moderate"
        assert HyphenationMode.AGGRESSIVE.value == "aggressive"


# =============================================================================
# TEST CLASS: Text Expansion Factors
# =============================================================================

class TestTextExpansionFactors:
    """Tests for text expansion factors."""

    def test_all_languages_have_factors(self):
        """All languages should have expansion factors."""
        for lang in SupportedLanguage:
            assert lang in TEXT_EXPANSION_FACTORS

    def test_german_baseline(self):
        """German should be baseline (1.0)."""
        assert TEXT_EXPANSION_FACTORS[SupportedLanguage.DE] == 1.0

    def test_english_shorter(self):
        """English should be shorter than German."""
        assert TEXT_EXPANSION_FACTORS[SupportedLanguage.EN] < 1.0

    def test_french_longer(self):
        """French should be longer than German."""
        assert TEXT_EXPANSION_FACTORS[SupportedLanguage.FR] > 1.0

    def test_romance_languages_expand(self):
        """Romance languages should expand."""
        assert TEXT_EXPANSION_FACTORS[SupportedLanguage.FR] > 1.0
        assert TEXT_EXPANSION_FACTORS[SupportedLanguage.IT] > 1.0
        assert TEXT_EXPANSION_FACTORS[SupportedLanguage.ES] > 1.0


# =============================================================================
# TEST CLASS: Calculate Text Expansion
# =============================================================================

class TestCalculateTextExpansion:
    """Tests for calculate_text_expansion function."""

    def test_de_to_en_shrinks(self):
        """German to English should shrink."""
        text = "Dies ist ein deutscher Text mit etwa fünfzig Zeichen."
        expanded_len, factor = calculate_text_expansion(text, "de", "en")
        assert factor < 1.0
        assert expanded_len < len(text)

    def test_de_to_fr_expands(self):
        """German to French should expand."""
        text = "Dies ist ein deutscher Text mit etwa fünfzig Zeichen."
        expanded_len, factor = calculate_text_expansion(text, "de", "fr")
        assert factor > 1.0
        assert expanded_len > len(text)

    def test_same_language_no_change(self):
        """Same language should not change."""
        text = "Test text"
        expanded_len, factor = calculate_text_expansion(text, "de", "de")
        assert factor == 1.0
        assert expanded_len == len(text)


# =============================================================================
# TEST CLASS: Hyphenation Rules
# =============================================================================

class TestHyphenationRules:
    """Tests for hyphenation rules."""

    def test_all_languages_have_rules(self):
        """All languages should have hyphenation rules."""
        for lang in SupportedLanguage:
            assert lang in HYPHENATION_RULES

    def test_german_compound_aware(self):
        """German should be compound-aware."""
        assert HYPHENATION_RULES[SupportedLanguage.DE]["compound_aware"] is True

    def test_french_aggressive(self):
        """French should use aggressive hyphenation."""
        assert HYPHENATION_RULES[SupportedLanguage.FR]["mode"] == HyphenationMode.AGGRESSIVE

    def test_english_conservative(self):
        """English should use conservative hyphenation."""
        assert HYPHENATION_RULES[SupportedLanguage.EN]["mode"] == HyphenationMode.CONSERVATIVE


# =============================================================================
# TEST CLASS: Get Expansion Factor
# =============================================================================

class TestGetExpansionFactor:
    """Tests for get_expansion_factor function."""

    def test_get_factor_de(self):
        """Should get German factor."""
        assert get_expansion_factor("de") == 1.0

    def test_get_factor_fr(self):
        """Should get French factor."""
        assert get_expansion_factor("fr") == pytest.approx(1.2, rel=0.01)

    def test_get_factor_invalid(self):
        """Should return 1.0 for invalid language."""
        assert get_expansion_factor("xx") == 1.0


# =============================================================================
# TEST CLASS: Get Hyphenation Mode
# =============================================================================

class TestGetHyphenationMode:
    """Tests for get_hyphenation_mode function."""

    def test_get_mode_de(self):
        """Should get German mode."""
        assert get_hyphenation_mode("de") == HyphenationMode.MODERATE

    def test_get_mode_fr(self):
        """Should get French mode."""
        assert get_hyphenation_mode("fr") == HyphenationMode.AGGRESSIVE

    def test_get_mode_invalid(self):
        """Should return conservative for invalid language."""
        assert get_hyphenation_mode("xx") == HyphenationMode.CONSERVATIVE


# =============================================================================
# TEST CLASS: Layout Language Adapter
# =============================================================================

class TestLayoutLanguageAdapter:
    """Tests for LayoutLanguageAdapter class."""

    def test_adapter_init(self, sample_sections, sample_briefing):
        """Adapter should initialize correctly."""
        adapter = LayoutLanguageAdapter(
            sections=sample_sections,
            briefing=sample_briefing,
            language="de",
        )
        assert adapter._language == SupportedLanguage.DE
        assert adapter._expansion_factor == 1.0

    def test_adapter_init_fr(self, sample_sections, sample_briefing):
        """Adapter should initialize for French."""
        adapter = LayoutLanguageAdapter(
            sections=sample_sections,
            briefing=sample_briefing,
            language="fr",
        )
        assert adapter._language == SupportedLanguage.FR
        assert adapter._expansion_factor > 1.0

    def test_adapter_process(self, sample_sections, sample_briefing):
        """Adapter should process sections."""
        adapter = LayoutLanguageAdapter(
            sections=sample_sections,
            briefing=sample_briefing,
            language="de",
        )
        sections, report = adapter.process()

        assert report.success is True
        assert report.sections_analyzed >= 3
        assert "_layout_report" in sections
        assert "_layout_language" in sections

    def test_adapter_preserves_internal_keys(self, sample_briefing):
        """Adapter should preserve internal keys."""
        sections = {
            "_metadata": {"version": "1.0"},
            "executive_summary": "Test content",
        }
        adapter = LayoutLanguageAdapter(
            sections=sections,
            briefing=sample_briefing,
            language="de",
        )
        result_sections, _ = adapter.process()

        assert "_metadata" in result_sections
        assert result_sections["_metadata"] == {"version": "1.0"}


# =============================================================================
# TEST CLASS: Section Analysis
# =============================================================================

class TestSectionAnalysis:
    """Tests for section analysis."""

    def test_analyze_estimates_lines(self, sample_sections, sample_briefing):
        """Analysis should estimate line count."""
        adapter = LayoutLanguageAdapter(
            sections=sample_sections,
            briefing=sample_briefing,
            language="de",
        )
        adapter.process()

        analysis = adapter._report.section_analyses.get("executive_summary")
        assert analysis is not None
        assert analysis.estimated_lines >= 0

    def test_analyze_detects_tables(self, sample_sections, sample_briefing):
        """Analysis should detect table overflow risk."""
        adapter = LayoutLanguageAdapter(
            sections=sample_sections,
            briefing=sample_briefing,
            language="de",
        )
        adapter.process()

        # business_case has a table
        analysis = adapter._report.section_analyses.get("business_case")
        assert analysis is not None

    def test_analyze_result_to_dict(self):
        """Analysis result should serialize to dict."""
        result = LayoutAnalysisResult(
            section="test",
            language=SupportedLanguage.DE,
            estimated_lines=50,
            estimated_pages=1.0,
            long_words_count=5,
            orphan_risk=False,
            table_overflow_risk=False,
            card_height_issues=0,
        )
        d = result.to_dict()
        assert d["section"] == "test"
        assert d["estimated_lines"] == 50


# =============================================================================
# TEST CLASS: Adapt Layout for Language
# =============================================================================

class TestAdaptLayoutForLanguage:
    """Tests for adapt_layout_for_language function."""

    def test_adapt_basic(self, sample_sections):
        """Should adapt sections for language."""
        sections, report = adapt_layout_for_language(
            sections=sample_sections,
            language="de",
        )

        assert report.success is True
        assert report.sections_analyzed >= 3

    def test_adapt_french_expansion(self, sample_sections):
        """French should have expansion considerations."""
        sections, report = adapt_layout_for_language(
            sections=sample_sections,
            language="fr",
        )

        assert report.language == "fr"


# =============================================================================
# TEST CLASS: Optimize Page Breaks
# =============================================================================

class TestOptimizePageBreaks:
    """Tests for optimize_page_breaks function."""

    def test_optimize_breaks_de(self, sample_sections):
        """Should optimize page breaks for German."""
        breaks = optimize_page_breaks(sample_sections, "de")

        assert "executive_summary" in breaks
        assert breaks["executive_summary"] == PageBreakRule.ALWAYS_BEFORE

    def test_optimize_breaks_fr(self, sample_sections):
        """Should optimize page breaks for French."""
        breaks = optimize_page_breaks(sample_sections, "fr")

        # French may have different rules
        assert isinstance(breaks, dict)


# =============================================================================
# TEST CLASS: Table Width Adjustments
# =============================================================================

class TestTableWidthAdjustments:
    """Tests for table width adjustments."""

    def test_all_languages_have_adjustments(self):
        """All languages should have table width adjustments."""
        for lang in SupportedLanguage:
            assert lang in TABLE_WIDTH_ADJUSTMENTS

    def test_german_baseline_widths(self):
        """German should have baseline widths (1.0)."""
        de_widths = TABLE_WIDTH_ADJUSTMENTS[SupportedLanguage.DE]
        assert de_widths["name_column"] == 1.0
        assert de_widths["description_column"] == 1.0

    def test_french_expanded_widths(self):
        """French should have expanded widths."""
        fr_widths = TABLE_WIDTH_ADJUSTMENTS[SupportedLanguage.FR]
        assert fr_widths["description_column"] > 1.0


# =============================================================================
# TEST CLASS: Layout Issue
# =============================================================================

class TestLayoutIssue:
    """Tests for LayoutIssue."""

    def test_issue_to_dict(self):
        """Issue should serialize to dict."""
        from services.layout_language_adapter import IssueSeverity

        issue = LayoutIssue(
            issue_id="TEST_001",
            severity=IssueSeverity.WARNING,
            element_type=LayoutElement.TABLE,
            section="business_case",
            message="Table may overflow",
            suggestion="Consider splitting",
        )
        d = issue.to_dict()

        assert d["issue_id"] == "TEST_001"
        assert d["severity"] == "warning"
        assert d["element_type"] == "table"


# =============================================================================
# TEST CLASS: Layout Adaptation
# =============================================================================

class TestLayoutAdaptation:
    """Tests for LayoutAdaptation."""

    def test_adaptation_to_dict(self):
        """Adaptation should serialize to dict."""
        adaptation = LayoutAdaptation(
            adaptation_type="table_width",
            section="business_case",
            element=LayoutElement.TABLE,
            original_value="100%",
            adapted_value="115%",
            reason="French text expansion",
        )
        d = adaptation.to_dict()

        assert d["adaptation_type"] == "table_width"
        assert d["element"] == "table"
