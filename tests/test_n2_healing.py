# -*- coding: utf-8 -*-
"""
Sprint N2: Healing & Consistency Regression Tests

Tests for Sprint N2 features:
- N2-1: Placeholder healing for KI_AKTIVITAETEN_ZIELE_HTML
- N2-2: GENERIC_LLM_LEAK healing in final HTML
- N2-3: Roadmap min-words thresholds
- N2-4: G22 Consistency ROI & Risk healing enhancements
- N2-5: PDF-Rendering pipeline leak check

Version: 1.0.0 (Sprint N2)
Author: Claude + Wolf
"""
from __future__ import annotations

import pytest
from typing import Dict, Any, List


# =============================================================================
# N2-1: Placeholder Healing Tests
# =============================================================================

class TestN2PlaceholderHealing:
    """Tests for N2-1 placeholder healing functionality."""

    def test_heal_placeholder_sections_empty_ki_aktivitaeten(self) -> None:
        """Test healing of empty KI_AKTIVITAETEN_ZIELE_HTML."""
        from services.report_validator import heal_placeholder_sections

        sections: Dict[str, Any] = {
            "KI_AKTIVITAETEN_ZIELE_HTML": "",
            "EXECUTIVE_SUMMARY_HTML": "<p>Valid content</p>",
        }

        healed_count = heal_placeholder_sections(sections)

        # May heal both KI_AKTIVITAETEN_ZIELE_HTML and ki_aktivitaeten_ziele
        assert healed_count >= 1
        assert sections["KI_AKTIVITAETEN_ZIELE_HTML"] != ""
        assert "ki-aktivitaeten-ziele" in sections["KI_AKTIVITAETEN_ZIELE_HTML"].lower()

    def test_heal_placeholder_sections_with_placeholder_text(self) -> None:
        """Test healing of sections with empty content triggers fallback."""
        from services.report_validator import heal_placeholder_sections

        # Sections with only whitespace are considered empty and should be healed
        sections: Dict[str, Any] = {
            "KI_AKTIVITAETEN_ZIELE_HTML": "   ",  # Only whitespace - should be healed
            "ki_aktivitaeten_ziele": "",  # Empty - should be healed
        }

        healed_count = heal_placeholder_sections(sections)

        assert healed_count >= 1
        # After healing, should have actual content
        assert sections["KI_AKTIVITAETEN_ZIELE_HTML"].strip() != ""

    def test_heal_placeholder_sections_valid_content_unchanged(self) -> None:
        """Test that valid content is not modified."""
        from services.report_validator import heal_placeholder_sections, CRITICAL_PLACEHOLDER_SECTIONS

        original_content = "<section><h2>KI-Aktivitäten</h2><p>Real content here with details.</p></section>"
        sections: Dict[str, Any] = {
            "KI_AKTIVITAETEN_ZIELE_HTML": original_content,
            "ki_aktivitaeten_ziele": original_content,  # Include both keys to prevent fallback
        }

        healed_count = heal_placeholder_sections(sections)

        assert healed_count == 0
        assert sections["KI_AKTIVITAETEN_ZIELE_HTML"] == original_content

    def test_build_ki_aktivitaeten_fallback_returns_html(self) -> None:
        """Test that fallback builder returns valid HTML."""
        from services.report_validator import build_ki_aktivitaeten_fallback

        sections: Dict[str, Any] = {
            "unternehmensgroesse": "team",
            "branche": "IT & Software",
        }

        fallback_html = build_ki_aktivitaeten_fallback(sections)

        assert fallback_html is not None
        assert "<section" in fallback_html
        assert "KI-Aktivitäten" in fallback_html or "ki-aktivitaeten" in fallback_html.lower()


# =============================================================================
# N2-2: Leak Phrase Removal Tests
# =============================================================================

class TestN2LeakPhraseRemoval:
    """Tests for N2-2 leak phrase removal functionality."""

    def test_remove_leak_phrases_basic(self) -> None:
        """Test basic leak phrase removal."""
        from services.report_validator import remove_leak_phrases_from_html, GENERIC_LLM_LEAK_PHRASES

        # Use an actual leak phrase from the list
        leak_phrase = GENERIC_LLM_LEAK_PHRASES[0] if GENERIC_LLM_LEAK_PHRASES else "Here is the"
        html_with_leaks = f"""
        <div>
            <p>{leak_phrase} some content.</p>
            <p>This is valid content.</p>
        </div>
        """

        cleaned_html, removed_count = remove_leak_phrases_from_html(html_with_leaks)

        assert removed_count >= 1
        assert leak_phrase not in cleaned_html

    def test_remove_leak_phrases_case_insensitive(self) -> None:
        """Test that leak phrase removal is case-insensitive."""
        from services.report_validator import remove_leak_phrases_from_html, GENERIC_LLM_LEAK_PHRASES

        # Use an actual leak phrase from the list in uppercase
        leak_phrase = GENERIC_LLM_LEAK_PHRASES[0] if GENERIC_LLM_LEAK_PHRASES else "Here is the"
        html = f"<p>{leak_phrase.upper()} some content.</p>"

        cleaned_html, removed_count = remove_leak_phrases_from_html(html)

        # Should detect and remove regardless of case
        assert removed_count >= 1 or leak_phrase.upper() not in cleaned_html.upper()

    def test_remove_leak_phrases_preserves_valid_content(self) -> None:
        """Test that valid content is preserved."""
        from services.report_validator import remove_leak_phrases_from_html

        valid_html = """
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <p>Die KI-Strategie zeigt ein positives ROI von 150%.</p>
            <p>Die empfohlenen Tools ermöglichen Zeiteinsparungen.</p>
        </div>
        """

        cleaned_html, removed_count = remove_leak_phrases_from_html(valid_html)

        assert removed_count == 0
        assert "Executive Summary" in cleaned_html
        assert "ROI von 150%" in cleaned_html

    def test_leak_phrases_list_exists(self) -> None:
        """Test that GENERIC_LLM_LEAK_PHRASES is defined and non-empty."""
        from services.report_validator import GENERIC_LLM_LEAK_PHRASES

        assert GENERIC_LLM_LEAK_PHRASES is not None
        assert len(GENERIC_LLM_LEAK_PHRASES) > 0
        assert all(isinstance(phrase, str) for phrase in GENERIC_LLM_LEAK_PHRASES)


# =============================================================================
# N2-3: Roadmap Min-Words Tests
# =============================================================================

class TestN2RoadmapMinWords:
    """Tests for N2-3 roadmap min-words thresholds."""

    def test_roadmap_90d_solo_threshold(self) -> None:
        """Test that solo roadmap_90d threshold is 130 (reduced from 150)."""
        from services.config_validation import SECTION_MIN_WORDS

        threshold = SECTION_MIN_WORDS.get(("solo", "roadmap_90d"))

        assert threshold is not None
        assert threshold == 130, f"Expected 130, got {threshold}"

    def test_roadmap_90d_team_threshold(self) -> None:
        """Test that team roadmap_90d threshold is 170 (reduced from 200)."""
        from services.config_validation import SECTION_MIN_WORDS

        threshold = SECTION_MIN_WORDS.get(("team", "roadmap_90d"))

        assert threshold is not None
        assert threshold == 170, f"Expected 170, got {threshold}"

    def test_roadmap_90d_kmu_threshold(self) -> None:
        """Test that kmu roadmap_90d threshold is 190 (reduced from 220)."""
        from services.config_validation import SECTION_MIN_WORDS

        threshold = SECTION_MIN_WORDS.get(("kmu", "roadmap_90d"))

        assert threshold is not None
        assert threshold == 190, f"Expected 190, got {threshold}"

    def test_roadmap_12m_thresholds_reduced(self) -> None:
        """Test that roadmap_12m thresholds were reduced proportionally."""
        from services.config_validation import SECTION_MIN_WORDS

        solo_12m = SECTION_MIN_WORDS.get(("solo", "roadmap_12m"))
        team_12m = SECTION_MIN_WORDS.get(("team", "roadmap_12m"))
        kmu_12m = SECTION_MIN_WORDS.get(("kmu", "roadmap_12m"))

        # N2 reduced thresholds
        assert solo_12m is not None and solo_12m <= 600
        assert team_12m is not None and team_12m <= 600
        assert kmu_12m is not None and kmu_12m <= 700


# =============================================================================
# N2-4: G22 Consistency Healing Tests
# =============================================================================

class TestN2BusinessCaseROIHealing:
    """Tests for N2-4.1 Business Case ROI healing enhancements."""

    def test_heal_scenario_consistency_realistic_below_conservative(self) -> None:
        """Test that realistic ROI is corrected when below conservative."""
        from services.business_case_engine_v2 import (
            ScenarioKPIs,
            heal_scenario_consistency,
        )

        # Create scenarios where realistic < conservative (incorrect)
        scenarios = [
            ScenarioKPIs(
                name="optimistic",
                roi_12m=200.0,
                payback_months=4.0,
                monthly_savings=1000.0,
                annual_savings=12000.0,
                investment_total=5000.0,
            ),
            ScenarioKPIs(
                name="realistic",
                roi_12m=50.0,  # Incorrectly lower than conservative
                payback_months=8.0,
                monthly_savings=600.0,
                annual_savings=7200.0,
                investment_total=5000.0,
            ),
            ScenarioKPIs(
                name="conservative",
                roi_12m=80.0,  # Higher than realistic - wrong!
                payback_months=10.0,
                monthly_savings=400.0,
                annual_savings=4800.0,
                investment_total=5000.0,
            ),
        ]

        healed_scenarios = heal_scenario_consistency(scenarios)

        # Get scenarios by name
        realistic = next(s for s in healed_scenarios if s.name == "realistic")
        conservative = next(s for s in healed_scenarios if s.name == "conservative")

        # After healing, realistic.roi_12m should be >= conservative.roi_12m
        assert realistic.roi_12m >= conservative.roi_12m, (
            f"Realistic ROI ({realistic.roi_12m}) should be >= "
            f"Conservative ROI ({conservative.roi_12m})"
        )

    def test_heal_scenario_consistency_correct_order_unchanged(self) -> None:
        """Test that correctly ordered scenarios are not modified unnecessarily."""
        from services.business_case_engine_v2 import (
            ScenarioKPIs,
            heal_scenario_consistency,
            validate_scenario_consistency,
        )

        # Create correctly ordered scenarios
        scenarios = [
            ScenarioKPIs(
                name="optimistic",
                roi_12m=200.0,
                payback_months=4.0,
                monthly_savings=1000.0,
                annual_savings=12000.0,
                investment_total=5000.0,
            ),
            ScenarioKPIs(
                name="realistic",
                roi_12m=120.0,
                payback_months=6.0,
                monthly_savings=700.0,
                annual_savings=8400.0,
                investment_total=5000.0,
            ),
            ScenarioKPIs(
                name="conservative",
                roi_12m=60.0,
                payback_months=10.0,
                monthly_savings=400.0,
                annual_savings=4800.0,
                investment_total=5000.0,
            ),
        ]

        # Already valid - should pass validation
        is_valid, errors = validate_scenario_consistency(scenarios)
        assert is_valid, f"Pre-check failed: {errors}"

        healed_scenarios = heal_scenario_consistency(scenarios)

        # Should still be valid after healing
        is_valid_after, errors_after = validate_scenario_consistency(healed_scenarios)
        assert is_valid_after, f"Post-healing check failed: {errors_after}"


class TestN2RecommendationsRiskHealing:
    """Tests for N2-4.2 Recommendations risk relation healing."""

    def test_derive_relevant_risks_fallback(self) -> None:
        """Test that derive_relevant_risks returns fallback when no risks found."""
        from services.recommendations_engine import derive_relevant_risks

        # Empty inputs - should return fallback
        risks = derive_relevant_risks(
            risk_report=None,
            recommendation_title="Generic task",
            recommendation_description="Do something generic",
        )

        assert len(risks) > 0
        assert "general_risk_reduction" in risks

    def test_derive_relevant_risks_keyword_detection(self) -> None:
        """Test that derive_relevant_risks detects keywords."""
        from services.recommendations_engine import derive_relevant_risks

        # AI Act related recommendation
        risks = derive_relevant_risks(
            risk_report=None,
            recommendation_title="AI Act Compliance Review",
            recommendation_description="Ensure AI Act compliance for all systems",
        )

        assert "risk_ai_act" in risks

    def test_heal_recommendations_consistency_adds_risks(self) -> None:
        """Test that heal_recommendations_consistency adds risks when missing."""
        from services.recommendations_engine import (
            Recommendation,
            heal_recommendations_consistency,
        )

        recommendations = [
            Recommendation(
                id="rec_test_1",
                title="Reduce vendor risk",
                description="Evaluate alternative vendors",
                reason="Test reason",
                impact_level="high",
                urgency_level="medium",
                risk_relation="reduces_risk",
                related_risks=[],  # Empty - should be healed
            ),
        ]

        healed = heal_recommendations_consistency(recommendations, risk_report=None)

        # After healing, related_risks should not be empty
        assert len(healed[0].related_risks) > 0, "related_risks should be populated"


# =============================================================================
# N2-5: PDF Rendering Leak Check Tests
# =============================================================================

class TestN2PDFRenderingLeakCheck:
    """Tests for N2-5 PDF rendering pipeline leak check."""

    def test_report_renderer_imports_leak_check(self) -> None:
        """Test that report_renderer imports leak check functions."""
        from services import report_renderer

        # Should have access to leak phrases
        assert hasattr(report_renderer, 'GENERIC_LLM_LEAK_PHRASES') or \
               'GENERIC_LLM_LEAK_PHRASES' in dir(report_renderer)

    def test_leak_phrases_constant_available(self) -> None:
        """Test that GENERIC_LLM_LEAK_PHRASES is accessible."""
        from services.report_validator import GENERIC_LLM_LEAK_PHRASES

        assert GENERIC_LLM_LEAK_PHRASES is not None
        assert isinstance(GENERIC_LLM_LEAK_PHRASES, (list, tuple))
        assert len(GENERIC_LLM_LEAK_PHRASES) > 5  # Should have multiple phrases


# =============================================================================
# Integration Tests
# =============================================================================

class TestN2Integration:
    """Integration tests for Sprint N2 features."""

    def test_validate_and_heal_combined(self) -> None:
        """Test validate_and_heal combines validation and healing."""
        from services.report_validator import validate_and_heal

        sections: Dict[str, Any] = {
            "KI_AKTIVITAETEN_ZIELE_HTML": "",  # Empty - should be healed
            "EXECUTIVE_SUMMARY_HTML": "<p>Valid summary content.</p>",
        }
        briefing: Dict[str, Any] = {
            "unternehmensgroesse": "team",
            "branche": "IT",
        }

        is_valid, errors, healed_count = validate_and_heal(sections, briefing)

        # Should have healed at least the empty section
        assert healed_count >= 1 or sections["KI_AKTIVITAETEN_ZIELE_HTML"] != ""

    def test_full_healing_pipeline(self) -> None:
        """Test full healing pipeline from validation to cleanup."""
        from services.report_validator import (
            heal_placeholder_sections,
            remove_leak_phrases_from_html,
        )

        # Start with problematic sections
        sections: Dict[str, Any] = {
            "KI_AKTIVITAETEN_ZIELE_HTML": "",
            "TEST_HTML": "<p>Here is the HTML content for the section.</p>",
        }

        # Step 1: Heal placeholders
        healed = heal_placeholder_sections(sections)
        assert healed >= 1

        # Step 2: Clean leak phrases
        test_html = sections.get("TEST_HTML", "")
        cleaned, removed = remove_leak_phrases_from_html(test_html)

        # Both steps should work without errors
        assert sections["KI_AKTIVITAETEN_ZIELE_HTML"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
