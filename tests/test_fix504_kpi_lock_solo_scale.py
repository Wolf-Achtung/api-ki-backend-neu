# -*- coding: utf-8 -*-
"""
FIX-504: Test Suite for Canonical KPI Lock + Solo-Scale Rewrite + QuickWins Premium Layout

Tests cover:
- TASK 1: Canonical KPI enforcer for Kennzahlenblock
- TASK 2: Typography/spacing fixes in KPI patterns
- TASK 3: Solo-scale term replacements
- TASK 4: QuickWins LEFT_ONLY full-width layout
- TASK 5: RELEASE_STRICT_MODE preparation utilities
"""

import os
import pytest


class TestTask1CanonicalKPIEnforcer:
    """TASK 1: Test canonical KPI value enforcement in Kennzahlenblock."""

    def test_enforce_kennzahlenblock_kpis_payback(self):
        """Test that payback values are enforced to canonical value."""
        from services.content_quality_enforcer import enforce_kennzahlenblock_kpis

        html = '<div>Payback: 11 Monate</div>'
        canonical = {"PAYBACK_MONTHS": 3.5}

        result, count = enforce_kennzahlenblock_kpis(html, canonical)

        assert count == 1
        assert "3,5 Monate" in result
        assert "11" not in result

    def test_enforce_kennzahlenblock_kpis_roi(self):
        """Test that ROI values are enforced to canonical value."""
        from services.content_quality_enforcer import enforce_kennzahlenblock_kpis

        html = '<div>ROI-Rate: 85%</div>'
        canonical = {"ROI_PLANWERT": 200}

        result, count = enforce_kennzahlenblock_kpis(html, canonical)

        assert count == 1
        assert "200" in result
        assert "85" not in result

    def test_enforce_kennzahlenblock_kpis_time_savings(self):
        """Test that time savings are enforced to canonical value."""
        from services.content_quality_enforcer import enforce_kennzahlenblock_kpis

        html = '<div>Zeitersparnis/Monat: 210 Std</div>'
        canonical = {"monatsersparnis_stunden": 20}

        result, count = enforce_kennzahlenblock_kpis(html, canonical)

        assert count == 1
        assert "20 Std" in result
        assert "210" not in result

    def test_enforce_skips_scenario_context(self):
        """Test that scenario/simulation context is not modified."""
        from services.content_quality_enforcer import enforce_kennzahlenblock_kpis

        html = '<div>Im konservativen Szenario: Payback: 9 Monate</div>'
        canonical = {"PAYBACK_MONTHS": 3.5}

        result, count = enforce_kennzahlenblock_kpis(html, canonical)

        # Should NOT be modified (scenario context)
        assert count == 0
        assert "9 Monate" in result

    def test_enforce_skips_within_tolerance(self):
        """Test that values within 20% tolerance are not modified."""
        from services.content_quality_enforcer import enforce_kennzahlenblock_kpis

        html = '<div>Payback: 3,7 Monate</div>'
        canonical = {"PAYBACK_MONTHS": 3.5}

        result, count = enforce_kennzahlenblock_kpis(html, canonical)

        # 3.7 is within 20% of 3.5, should not be modified
        assert count == 0
        assert "3,7" in result


class TestTask2TypographySpacingFix:
    """TASK 2: Test typography/spacing fixes in KPI patterns."""

    def test_fix_payback_without_space(self):
        """Test fixing 'Payback11 Monate' -> 'Payback: 11 Monate'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = 'Payback11 Monate'
        result, count = fix_kennzahlen_spacing(html)

        assert count >= 1
        assert "Payback: 11 Monate" in result

    def test_fix_roi_rate_without_space(self):
        """Test fixing 'ROI-Rate85%' -> 'ROI-Rate: 85 %'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = 'ROI-Rate85%'
        result, count = fix_kennzahlen_spacing(html)

        assert count >= 1
        assert "ROI-Rate: 85" in result

    def test_fix_zeitersparnis_without_space(self):
        """Test fixing 'Zeitersparnis/Monat210 Std' -> 'Zeitersparnis/Monat: 210 Std'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = 'Zeitersparnis/Monat210 Std'
        result, count = fix_kennzahlen_spacing(html)

        assert count >= 1
        assert ": 210 Std" in result

    def test_fix_ai_act_risiko_without_space(self):
        """Test fixing 'AI Act RisikoMittel' -> 'AI Act Risiko: Mittel'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = 'AI Act RisikoMittel'
        result, count = fix_kennzahlen_spacing(html)

        assert count >= 1
        assert "Risiko: Mittel" in result

    def test_fix_real_problem_strings_from_report_501(self):
        """Test fixing real problem strings from Report-501."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        # Real examples from Report-501
        test_cases = [
            ("Payback11 Monate", ": 11"),
            ("ROI-Rate85%auf", ": 85"),
            ("Zeitersparnis/Monat210 Std", ": 210"),
        ]

        for input_str, expected_substring in test_cases:
            result, count = fix_kennzahlen_spacing(input_str)
            assert count >= 1, f"Expected fix for '{input_str}'"
            assert expected_substring in result, f"Expected '{expected_substring}' in '{result}'"


class TestTask3SoloTermReplacements:
    """TASK 3: Test extended solo-scale term replacements."""

    def test_skalierung_replacement(self):
        """Test 'Skalierung' -> 'Ausbau'."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {"EXECUTIVE_SUMMARY_HTML": "Die Skalierung erfolgt in Phasen."}
        result = apply_solo_language_normalizer(sections, "solo")

        assert "Ausbau" in result["EXECUTIVE_SUMMARY_HTML"]
        assert "Skalierung" not in result["EXECUTIVE_SUMMARY_HTML"]

    def test_stack_replacement(self):
        """Test 'Stack' -> 'Technikpaket'."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {"EXECUTIVE_SUMMARY_HTML": "Der Tech-Stack umfasst Tools."}
        result = apply_solo_language_normalizer(sections, "solo")

        assert "Technikpaket" in result["EXECUTIVE_SUMMARY_HTML"]

    def test_modul_replacement(self):
        """Test 'Modul' -> 'Baustein'."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {"EXECUTIVE_SUMMARY_HTML": "Das Modul wird erweitert."}
        result = apply_solo_language_normalizer(sections, "solo")

        assert "Baustein" in result["EXECUTIVE_SUMMARY_HTML"]
        assert "Modul" not in result["EXECUTIVE_SUMMARY_HTML"]

    def test_1000_plus_kunden_replacement(self):
        """Test '1000+ Kunden' -> 'neue Mandanten'."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {"ROADMAP_12M_HTML": "Ziel: 1000+ Kunden erreichen"}
        result = apply_solo_language_normalizer(sections, "solo")

        assert "neue Mandanten" in result["ROADMAP_12M_HTML"]
        assert "1000" not in result["ROADMAP_12M_HTML"]

    def test_no_replacement_for_non_solo(self):
        """Test that replacements only apply for solo persona."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {"EXECUTIVE_SUMMARY_HTML": "Die Skalierung erfolgt in Phasen."}

        # Test with "team" persona - should NOT replace
        result = apply_solo_language_normalizer(sections.copy(), "team")
        assert "Skalierung" in result["EXECUTIVE_SUMMARY_HTML"]

        # Test with empty persona - should NOT replace
        result = apply_solo_language_normalizer(sections.copy(), "")
        assert "Skalierung" in result["EXECUTIVE_SUMMARY_HTML"]

    def test_rollout_replacement(self):
        """Test 'Rollout' -> 'Einführung'."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {"ROADMAP_90D_HTML": "Der Rollout startet in Q1."}
        result = apply_solo_language_normalizer(sections, "solo")

        assert "Einführung" in result["ROADMAP_90D_HTML"]
        assert "Rollout" not in result["ROADMAP_90D_HTML"]


class TestTask4QuickWinsFullWidthLayout:
    """TASK 4: Test QuickWins LEFT_ONLY full-width layout enhancement."""

    def test_detect_template_mode_left_only(self):
        """Test detection of LEFT_ONLY template mode."""
        from services.quickwins_renderer import detect_quickwins_template_mode

        sections = {
            "QUICK_WINS_HTML": "",
            "QUICK_WINS_HTML_LEFT": "<div>Content</div>",
            "QUICK_WINS_HTML_RIGHT": "",
        }
        mode = detect_quickwins_template_mode(sections)
        assert mode == "LEFT_ONLY"

    def test_detect_template_mode_full(self):
        """Test detection of FULL template mode."""
        from services.quickwins_renderer import detect_quickwins_template_mode

        sections = {
            "QUICK_WINS_HTML": "<div>Content</div>",
            "QUICK_WINS_HTML_LEFT": "",
            "QUICK_WINS_HTML_RIGHT": "",
        }
        mode = detect_quickwins_template_mode(sections)
        assert mode == "FULL"

    def test_detect_template_mode_left_right(self):
        """Test detection of LEFT_RIGHT template mode."""
        from services.quickwins_renderer import detect_quickwins_template_mode

        sections = {
            "QUICK_WINS_HTML": "",
            "QUICK_WINS_HTML_LEFT": "<div>Left</div>",
            "QUICK_WINS_HTML_RIGHT": "<div>Right</div>",
        }
        mode = detect_quickwins_template_mode(sections)
        assert mode == "LEFT_RIGHT"

    def test_count_quickwin_cards(self):
        """Test counting QuickWin cards in HTML."""
        from services.quickwins_renderer import count_quickwin_cards

        html = '''
        <div class="quick-win-card">Card 1</div>
        <div class="quick-win-card">Card 2</div>
        <div class="quick-win-card">Card 3</div>
        '''
        count = count_quickwin_cards(html)
        assert count == 3

    def test_enhance_quickwins_adds_css(self):
        """Test that enhancement adds CSS for full-width layout."""
        from services.quickwins_renderer import enhance_quickwins_for_fullwidth

        html = '<div class="quick-win-card">Card 1</div>'
        result = enhance_quickwins_for_fullwidth(html)

        assert "quickwins-fullwidth-grid" in result
        assert "grid-template-columns" in result

    def test_enhance_quickwins_no_double_wrap(self):
        """Test that already enhanced HTML is not double-wrapped."""
        from services.quickwins_renderer import enhance_quickwins_for_fullwidth

        html = '<div class="quickwins-fullwidth-grid"><div class="quick-win-card">Card</div></div>'
        result = enhance_quickwins_for_fullwidth(html)

        # Should not add another grid wrapper
        assert result.count("quickwins-fullwidth-grid") == 1

    def test_apply_enhancement_only_for_fullwidth_modes(self):
        """Test that enhancement only applies for LEFT_ONLY/FULL modes."""
        from services.quickwins_renderer import apply_quickwins_fullwidth_enhancement

        # LEFT_RIGHT mode - should NOT enhance
        sections = {
            "QUICK_WINS_HTML": "<div>Content</div>",
            "QUICK_WINS_HTML_LEFT": "<div>Left</div>",
            "QUICK_WINS_HTML_RIGHT": "<div>Right</div>",
        }
        result = apply_quickwins_fullwidth_enhancement(sections.copy())
        assert "quickwins-fullwidth-grid" not in result.get("QUICK_WINS_HTML", "")

        # FULL mode - should enhance
        sections_full = {
            "QUICK_WINS_HTML": "<div>Content</div>",
            "QUICK_WINS_HTML_LEFT": "",
            "QUICK_WINS_HTML_RIGHT": "",
        }
        result = apply_quickwins_fullwidth_enhancement(sections_full)
        assert "quickwins-fullwidth-grid" in result.get("QUICK_WINS_HTML", "")


class TestTask5StrictModePreparation:
    """TASK 5: Test RELEASE_STRICT_MODE preparation utilities."""

    def test_check_strict_mode_readiness_no_warnings(self):
        """Test readiness check with no warnings."""
        from services.content_quality_enforcer import check_strict_mode_readiness

        result = check_strict_mode_readiness([])

        assert result["ready"] is True
        assert result["blocking_count"] == 0

    def test_check_strict_mode_readiness_with_blocking(self):
        """Test readiness check with blocking warnings."""
        from services.content_quality_enforcer import check_strict_mode_readiness

        warnings = [
            "[SIZE_MISMATCH] Solo report contains enterprise language",
            "[PERSONA_LEAK] Wrong persona detected",
        ]
        result = check_strict_mode_readiness(warnings)

        assert result["ready"] is False
        assert result["blocking_count"] == 2
        assert len(result["blocking_warnings"]) == 2

    def test_check_strict_mode_readiness_with_acceptable(self):
        """Test readiness check with acceptable warnings."""
        from services.content_quality_enforcer import check_strict_mode_readiness

        warnings = [
            "[SOLO-LANGUAGE] replaced_terms=15 in 5 sections",
            "[KPI-ENFORCER] Fixed 3 inconsistent KPI values",
        ]
        result = check_strict_mode_readiness(warnings)

        assert result["ready"] is True
        assert result["acceptable_count"] == 2
        assert result["blocking_count"] == 0

    def test_get_strict_mode_status(self):
        """Test getting current strict mode status."""
        from services.content_quality_enforcer import get_strict_mode_status

        # Test with RELEASE_STRICT_MODE=0
        os.environ["RELEASE_STRICT_MODE"] = "0"
        status = get_strict_mode_status()
        assert status["enabled"] is False

        # Test with RELEASE_STRICT_MODE=1
        os.environ["RELEASE_STRICT_MODE"] = "1"
        status = get_strict_mode_status()
        assert status["enabled"] is True

        # Cleanup
        os.environ.pop("RELEASE_STRICT_MODE", None)


class TestIntegration:
    """Integration tests for the full FIX-504 pipeline."""

    def test_full_kennzahlenblock_fix_pipeline(self):
        """Test the full Kennzahlenblock fix pipeline."""
        from services.content_quality_enforcer import apply_kennzahlenblock_enforcer

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "Payback11 Monate, ROI-Rate85%",
            "PAYBACK_MONTHS": 3.5,
            "ROI_PLANWERT": 200,
        }

        result = apply_kennzahlenblock_enforcer(sections)

        # Should have fixed spacing
        assert ": " in result["EXECUTIVE_SUMMARY_HTML"]
        # Should have enforced canonical values
        assert "3,5" in result["EXECUTIVE_SUMMARY_HTML"]
        assert "200" in result["EXECUTIVE_SUMMARY_HTML"]

    def test_solo_normalizer_with_new_terms(self):
        """Test solo normalizer with new FIX-504 terms."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {
            "ROADMAP_12M_HTML": (
                "Phase 1: Skalierung auf 1000+ Kunden. "
                "Der Tech-Stack wird mit neuen Modulen erweitert. "
                "Der Rollout erfolgt schrittweise."
            ),
        }

        result = apply_solo_language_normalizer(sections, "solo")
        content = result["ROADMAP_12M_HTML"]

        # All enterprise terms should be replaced
        assert "Skalierung" not in content
        assert "1000" not in content
        assert "Tech-Stack" not in content
        assert "Modul" not in content
        assert "Rollout" not in content

        # Solo-friendly terms should be present
        assert "Ausbau" in content
        assert "Mandanten" in content
        assert "Baustein" in content or "Technikpaket" in content
        assert "Einführung" in content


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_html_handling(self):
        """Test that empty HTML is handled gracefully."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing, enforce_kennzahlenblock_kpis

        # Empty string
        result1, count1 = fix_kennzahlen_spacing("")
        assert result1 == ""
        assert count1 == 0

        # None value
        result2, count2 = fix_kennzahlen_spacing(None)
        assert result2 is None
        assert count2 == 0

        # Empty canonical KPIs
        result3, count3 = enforce_kennzahlenblock_kpis("<div>Test</div>", {})
        assert count3 == 0

    def test_decimal_comma_handling(self):
        """Test German decimal comma handling in values."""
        from services.content_quality_enforcer import enforce_kennzahlenblock_kpis

        html = '<div>Payback: 3,5 Monate</div>'
        canonical = {"PAYBACK_MONTHS": "3,5"}  # German format input

        result, count = enforce_kennzahlenblock_kpis(html, canonical)

        # Should not modify - same value
        assert count == 0 or "3,5" in result

    def test_multiple_kpis_in_same_section(self):
        """Test fixing multiple KPIs in the same HTML section."""
        from services.content_quality_enforcer import apply_kennzahlenblock_enforcer

        sections = {
            "BUSINESS_CASE_HTML": (
                "Payback11 Monate. ROI-Rate85%. "
                "Zeitersparnis/Monat210 Std."
            ),
            "PAYBACK_MONTHS": 3.5,
            "ROI_PLANWERT": 200,
            "monatsersparnis_stunden": 20,
        }

        result = apply_kennzahlenblock_enforcer(sections)
        content = result["BUSINESS_CASE_HTML"]

        # All should be fixed
        assert "3,5" in content
        assert "200" in content
        assert "20" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
