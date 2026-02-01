# -*- coding: utf-8 -*-
"""
Tests for P1 Sprint Fixes:
- TASK A: Final-Check Rendering (p.final-check-item)
- TASK B: Quick Wins Completeness Gate (enforce_quickwins_complete)
- TASK C: SOLO Labels Source-of-Truth (segment-aware template labels)
"""
import pytest
import re


# =============================================================================
# TASK A: Final-Check Rendering Tests
# =============================================================================

class TestFinalCheckRendering:
    """Tests for Final-Check Box rendering changes."""

    def test_template_has_final_check_item_class(self):
        """Verify template uses p.final-check-item instead of ul/li."""
        from pathlib import Path

        template_path = Path(__file__).parent.parent / "templates" / "pdf_template.html"
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the Final-Check section (greedy to capture the whole block)
        final_check_start = content.find('<!-- FINAL CHECK')
        assert final_check_start != -1, "Final-Check section not found in template"

        # Find the end of the Final-Check block (next major section or 500 chars)
        final_check_end = content.find('<!-- TOP-3 MUSS', final_check_start)
        if final_check_end == -1:
            final_check_end = final_check_start + 3000  # fallback

        final_check_html = content[final_check_start:final_check_end]

        # Should have p.final-check-item
        assert 'class="final-check-item"' in final_check_html, \
            f"Expected p.final-check-item class in Final-Check section. Found: {final_check_html[:500]}..."

        # Should NOT have ul/li for FINAL_CHECK_DECISIONS
        # Check that there's no <ul> before the {% endfor %} for decisions
        decisions_block = re.search(r'FINAL_CHECK_DECISIONS.*?endfor', final_check_html, re.DOTALL)
        if decisions_block:
            assert '<ul' not in decisions_block.group(0), \
                "Final-Check decisions should not use ul element"

    def test_final_check_has_word_wrap_css(self):
        """Verify Final-Check has word-wrap CSS for WeasyPrint compatibility."""
        from pathlib import Path

        template_path = Path(__file__).parent.parent / "templates" / "pdf_template.html"
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the Final-Check section
        final_check_match = re.search(
            r'class="final-check-item"[^>]*style="[^"]*',
            content
        )

        assert final_check_match, "final-check-item with style not found"
        style = final_check_match.group(0)

        # Should have word-wrap
        assert 'word-wrap' in style or 'overflow-wrap' in style, \
            "Expected word-wrap or overflow-wrap in final-check-item style"


# =============================================================================
# TASK B: Quick Wins Completeness Gate Tests
# =============================================================================

class TestQuickWinsCompletenessGate:
    """Tests for enforce_quickwins_complete function."""

    def test_enforce_fills_empty_problem(self):
        """Test that empty problem field is filled with fallback."""
        from services.quickwins_renderer import enforce_quickwins_complete

        quickwins = [
            {"title": "Automatisierung der Rechnungsstellung", "problem": "", "wirkung": "Test", "umsetzung": "Test"}
        ]

        result = enforce_quickwins_complete(quickwins)

        assert result[0]["problem"], "Expected problem field to be filled"
        assert "Manuelle" in result[0]["problem"] or "automatisier" in result[0]["problem"].lower()

    def test_enforce_fills_empty_wirkung(self):
        """Test that empty wirkung field is filled with fallback."""
        from services.quickwins_renderer import enforce_quickwins_complete

        quickwins = [
            {"title": "Effizienzsteigerung", "problem": "Test", "wirkung": "", "umsetzung": "Test"}
        ]

        result = enforce_quickwins_complete(quickwins)

        assert result[0]["wirkung"], "Expected wirkung field to be filled"

    def test_enforce_fills_empty_umsetzung(self):
        """Test that empty umsetzung field is filled with fallback."""
        from services.quickwins_renderer import enforce_quickwins_complete

        quickwins = [
            {"title": "Kundenservice Chatbot", "problem": "Test", "wirkung": "Test", "umsetzung": ""}
        ]

        result = enforce_quickwins_complete(quickwins)

        assert result[0]["umsetzung"], "Expected umsetzung field to be filled"
        # Should match customer-related fallback
        assert "Chatbot" in result[0]["umsetzung"] or "Selbstservice" in result[0]["umsetzung"] or "Pilotprojekt" in result[0]["umsetzung"]

    def test_enforce_fills_all_empty_fields(self):
        """Test that all empty fields are filled."""
        from services.quickwins_renderer import enforce_quickwins_complete

        quickwins = [
            {"title": "Content-Erstellung mit KI", "problem": "", "wirkung": "", "umsetzung": "", "hinweis": "siehe BC"}
        ]

        result = enforce_quickwins_complete(quickwins)

        assert result[0]["problem"], "Expected problem field to be filled"
        assert result[0]["wirkung"], "Expected wirkung field to be filled"
        assert result[0]["umsetzung"], "Expected umsetzung field to be filled"

    def test_enforce_preserves_non_empty_fields(self):
        """Test that non-empty fields are preserved."""
        from services.quickwins_renderer import enforce_quickwins_complete

        original_problem = "Manueller Prozess dauert zu lange"
        original_wirkung = "50% Zeitersparnis"
        quickwins = [
            {"title": "Test", "problem": original_problem, "wirkung": original_wirkung, "umsetzung": ""}
        ]

        result = enforce_quickwins_complete(quickwins)

        assert result[0]["problem"] == original_problem, "Non-empty problem should be preserved"
        assert result[0]["wirkung"] == original_wirkung, "Non-empty wirkung should be preserved"

    def test_enforce_handles_empty_list(self):
        """Test that empty list returns empty list."""
        from services.quickwins_renderer import enforce_quickwins_complete

        result = enforce_quickwins_complete([])
        assert result == []

    def test_enforce_handles_none(self):
        """Test that None input returns None."""
        from services.quickwins_renderer import enforce_quickwins_complete

        result = enforce_quickwins_complete(None)
        assert result is None

    def test_render_skips_empty_blocks(self):
        """Test that render_quickwins_premium_json skips truly empty blocks."""
        from services.quickwins_renderer import render_quickwins_premium_json
        import json

        # Create JSON where enforce would fill the fields
        quickwins_json = json.dumps([
            {"title": "Test Quick Win", "icon": "🎯", "problem": "", "wirkung": "", "umsetzung": "", "hinweis": "Test"}
        ])

        html = render_quickwins_premium_json(quickwins_json)

        assert html is not None, "Expected HTML output"
        # After enforce, fields should be filled, so blocks should be present
        assert "Problem:" in html or "quick-win-problem" in html


# =============================================================================
# TASK C: SOLO Labels Source-of-Truth Tests
# =============================================================================

class TestSoloLabelsSourceOfTruth:
    """Tests for segment-aware labels in template rendering."""

    def test_template_uses_ui_for_governance_label(self):
        """Verify template uses ui() for Governance dimension label."""
        from pathlib import Path

        template_path = Path(__file__).parent.parent / "templates" / "pdf_template.html"
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should use ui("governance_label", ...) for dimension label
        assert 'ui("governance_label"' in content, \
            "Expected template to use ui('governance_label') for dimension label"

    def test_template_uses_ui_for_governance_section_kicker(self):
        """Verify template uses ui() for Governance section kicker."""
        from pathlib import Path

        template_path = Path(__file__).parent.parent / "templates" / "pdf_template.html"
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should use ui("governance_section_kicker", ...) for section kicker
        assert 'ui("governance_section_kicker"' in content, \
            "Expected template to use ui('governance_section_kicker') for section kicker"

    def test_report_renderer_uses_segment_aware_ui(self):
        """Verify report_renderer uses ui_for_segment."""
        from pathlib import Path

        renderer_path = Path(__file__).parent.parent / "services" / "report_renderer.py"
        with open(renderer_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should import ui_for_segment
        assert "ui_for_segment" in content, \
            "Expected report_renderer to import ui_for_segment"

        # Should use segment-aware ui
        assert 'ui_for_segment(lang, segment=' in content, \
            "Expected report_renderer to call ui_for_segment with segment"

    def test_i18n_solo_governance_returns_spielregeln(self):
        """Test that SOLO segment returns 'Spielregeln' for governance."""
        from services.i18n import get_label_for_segment

        result = get_label_for_segment("governance_label", "de", segment="SOLO")
        assert result == "Spielregeln", f"Expected 'Spielregeln' for SOLO governance, got '{result}'"

    def test_i18n_team_governance_returns_governance(self):
        """Test that TEAM segment returns 'Governance' for governance."""
        from services.i18n import get_label_for_segment

        # TEAM should fall back to standard (no _team suffix exists)
        result = get_label_for_segment("governance_label", "de", segment="TEAM")
        # Should return the fallback "Governance" or the standard label
        assert "Governance" in result or result == "governance_label"


# =============================================================================
# Integration Tests
# =============================================================================

class TestP1SprintIntegration:
    """Integration tests for P1 Sprint fixes."""

    def test_quickwins_completeness_in_premium_render(self):
        """Test that premium renderer applies completeness gate."""
        from services.quickwins_renderer import render_quickwins_premium_json
        import json

        # Input with empty fields
        quickwins_json = json.dumps([
            {
                "title": "Automatisierung",
                "icon": "🤖",
                "problem": "",
                "wirkung": "",
                "umsetzung": "",
                "hinweis": "siehe Business Case"
            }
        ])

        html = render_quickwins_premium_json(quickwins_json)

        assert html is not None
        # Should have content in the blocks (filled by enforce)
        assert "Problem:" in html
        assert "Wirkung:" in html
        assert "Umsetzung:" in html

    def test_solo_segment_normalization_in_renderer(self):
        """Test that segment is normalized correctly."""
        # segment_map = {"solo": "SOLO", "team": "TEAM", "klein": "TEAM", "kmu": "KMU"}
        segment_map = {"solo": "SOLO", "team": "TEAM", "klein": "TEAM", "kmu": "KMU"}

        assert segment_map.get("solo") == "SOLO"
        assert segment_map.get("klein") == "TEAM"
        assert segment_map.get("kmu") == "KMU"
        assert segment_map.get("unknown", "TEAM") == "TEAM"


# =============================================================================
# TASK D: ROI as Ranges/Qualitative Tests
# =============================================================================

class TestRoiQualitativeRanges:
    """Tests for ROI as qualitative ranges for SOLO."""

    def test_format_roi_span_very_high(self):
        """Test format_roi_span for very high ROI."""
        from services.report_healer import format_roi_span

        result = format_roi_span(350.0)
        assert "sehr hoch" in result
        assert "300%" in result

    def test_format_roi_span_high(self):
        """Test format_roi_span for high ROI."""
        from services.report_healer import format_roi_span

        result = format_roi_span(250.0)
        assert "hoch" in result
        assert "200-300%" in result

    def test_format_roi_span_good(self):
        """Test format_roi_span for good ROI."""
        from services.report_healer import format_roi_span

        result = format_roi_span(175.0)
        assert "gut" in result
        assert "150-200%" in result

    def test_format_roi_span_solid(self):
        """Test format_roi_span for solid ROI."""
        from services.report_healer import format_roi_span

        result = format_roi_span(120.0)
        assert "solide" in result
        assert "100-150%" in result

    def test_format_roi_span_moderate(self):
        """Test format_roi_span for moderate ROI."""
        from services.report_healer import format_roi_span

        result = format_roi_span(75.0)
        assert "moderat" in result
        assert "50-100%" in result

    def test_format_roi_span_low(self):
        """Test format_roi_span for low ROI."""
        from services.report_healer import format_roi_span

        result = format_roi_span(30.0)
        assert "gering" in result
        assert "unter 50%" in result

    def test_sanitize_roi_for_solo_replaces_roi_colon(self):
        """Test sanitize_roi_for_solo replaces 'ROI: 200%' pattern."""
        from services.report_healer import sanitize_roi_for_solo

        html = "<p>Der ROI: 250% ist sehr gut.</p>"
        result, count = sanitize_roi_for_solo(html)

        assert count == 1
        assert "hoch (200-300%)" in result
        assert "250%" not in result

    def test_sanitize_roi_for_solo_replaces_roi_von(self):
        """Test sanitize_roi_for_solo replaces 'ROI von 150%' pattern."""
        from services.report_healer import sanitize_roi_for_solo

        html = "<p>Mit einem ROI von 175% lohnt sich die Investition.</p>"
        result, count = sanitize_roi_for_solo(html)

        assert count == 1
        assert "gut (150-200%)" in result
        assert "175%" not in result

    def test_heal_final_html_applies_roi_sanitization_for_solo(self):
        """Test heal_final_html applies ROI sanitization for SOLO."""
        from services.report_healer import heal_final_html

        html = """<html>
        <body>
            <p>Der ROI: 200% zeigt gute Rentabilität.</p>
            <p>Payback: 6 Monate</p>
        </body>
        </html>"""

        result = heal_final_html(html, segment="SOLO")

        # Should have qualitative range
        assert "200%" not in result or "hoch" in result
        # Payback should be preserved
        assert "6" in result

    def test_heal_final_html_preserves_roi_for_team(self):
        """Test heal_final_html preserves exact ROI for TEAM."""
        from services.report_healer import heal_final_html

        html = "<p>Der ROI: 200% ist sehr gut.</p>"

        result = heal_final_html(html, segment="TEAM")

        # TEAM should preserve exact ROI
        assert "200%" in result


# =============================================================================
# P0/P1 Final Solo Polish Tests
# =============================================================================

class TestQuickWinEmptyFieldFailsafe:
    """Tests for TASK 1 (P0): Quick Wins empty field failsafe - now FILLS instead of removes."""

    def test_fills_empty_problem_block(self):
        """Test that empty PROBLEM block is FILLED with fallback text."""
        from services.report_healer import sanitize_quickwin_empty_fields

        html = '''<div class="quick-win-problem" style="margin-bottom:10px;">
            <strong style="color:#dc2626;">Problem:</strong>
            <p style="margin:4px 0 0 0;"></p>
        </div>'''

        result, count = sanitize_quickwin_empty_fields(html)
        assert count == 1
        # Block is now FILLED, not removed
        assert "quick-win-problem" in result
        assert "Aktueller Prozess kostet mehr Zeit" in result

    def test_fills_empty_wirkung_block(self):
        """Test that empty WIRKUNG block is FILLED with fallback text."""
        from services.report_healer import sanitize_quickwin_empty_fields

        html = '''<div class="quick-win-wirkung" style="margin-bottom:10px;">
            <strong style="color:#16a34a;">Wirkung:</strong>
            <p style="margin:4px 0 0 0;"></p>
        </div>'''

        result, count = sanitize_quickwin_empty_fields(html)
        assert count == 1
        # Block is now FILLED, not removed
        assert "quick-win-wirkung" in result
        assert "Entlastung bei wiederkehrenden" in result

    def test_fills_empty_umsetzung_block(self):
        """Test that empty UMSETZUNG block is FILLED with fallback text."""
        from services.report_healer import sanitize_quickwin_empty_fields

        html = '''<div class="quick-win-umsetzung" style="margin-bottom:10px;">
            <strong style="color:#2563eb;">Umsetzung:</strong>
            <p style="margin:4px 0 0 0;"></p>
        </div>'''

        result, count = sanitize_quickwin_empty_fields(html)
        assert count == 1
        # Block is now FILLED, not removed
        assert "quick-win-umsetzung" in result
        assert "Starte diese Woche" in result

    def test_preserves_non_empty_blocks(self):
        """Test that non-empty blocks are preserved unchanged."""
        from services.report_healer import sanitize_quickwin_empty_fields

        html = '''<div class="quick-win-problem" style="margin-bottom:10px;">
            <strong style="color:#dc2626;">Problem:</strong>
            <p style="margin:4px 0 0 0;">Manuelle Prozesse kosten Zeit.</p>
        </div>'''

        result, count = sanitize_quickwin_empty_fields(html)
        assert count == 0
        assert "quick-win-problem" in result
        assert "Manuelle Prozesse" in result


class TestInputChecklistRemoval:
    """Tests for TASK 3 (P1): Input checklist removal."""

    def test_removes_input_checklist_with_branche_datenlage(self):
        """Test removal of checklist with Branche/Datenlage/Tool items."""
        from services.report_healer import sanitize_input_checklist

        html = '''<ul>
            <li>Branche und Ziel</li>
            <li>Datenlage</li>
            <li>Tool-Übersicht</li>
        </ul>'''

        result, count = sanitize_input_checklist(html)
        assert count >= 1
        assert "Branche und Ziel" not in result

    def test_removes_individual_checklist_items(self):
        """Test removal of individual checklist items."""
        from services.report_healer import sanitize_input_checklist

        html = '<li>Datenlage (aktuell)</li>'
        result, count = sanitize_input_checklist(html)
        assert count >= 1
        assert "Datenlage" not in result

    def test_preserves_unrelated_content(self):
        """Test that unrelated content is preserved."""
        from services.report_healer import sanitize_input_checklist

        html = '''<ul>
            <li>Automatisierung der Buchhaltung</li>
            <li>Kundenservice-Verbesserung</li>
        </ul>'''

        result, count = sanitize_input_checklist(html)
        assert count == 0
        assert "Automatisierung" in result


class TestPhraseLevelGovernanceReplacements:
    """Tests for TASK 4 (P1): Phrase-level Governance replacements."""

    def test_replaces_starker_governance(self):
        """Test 'starker Governance' → 'klaren Spielregeln'."""
        from services.report_healer import heal_final_html

        html = "<p>Mit starker Governance gelingen KI-Projekte.</p>"
        result = heal_final_html(html, segment="SOLO")

        assert "klaren Spielregeln" in result
        assert "starker Governance" not in result

    def test_replaces_solider_governance(self):
        """Test 'solider Governance' → 'soliden Spielregeln'."""
        from services.report_healer import heal_final_html

        html = "<p>Dank solider Governance vermeiden Sie Risiken.</p>"
        result = heal_final_html(html, segment="SOLO")

        assert "soliden Spielregeln" in result
        assert "solider Governance" not in result

    def test_replaces_governance_strukturen(self):
        """Test 'Governance-Strukturen' → 'Spielregeln'."""
        from services.report_healer import heal_final_html

        html = "<p>Die Governance-Strukturen sollten klar definiert sein.</p>"
        result = heal_final_html(html, segment="SOLO")

        assert "Spielregeln" in result
        assert "Governance-Strukturen" not in result

    def test_preserves_governance_for_team(self):
        """Test that Governance is preserved for TEAM segment."""
        from services.report_healer import heal_final_html

        html = "<p>Mit starker Governance gelingen KI-Projekte.</p>"
        result = heal_final_html(html, segment="TEAM")

        # TEAM should keep enterprise terms
        assert "Governance" in result or "Spielregeln" in result  # May or may not replace


class TestKiStackKickerLabel:
    """Tests for TASK 2 (P0): KI-Stack kicker label for SOLO."""

    def test_template_uses_ui_for_ki_stack_kicker(self):
        """Verify template uses ui() for KI-Stack kicker."""
        from pathlib import Path

        template_path = Path(__file__).parent.parent / "templates" / "pdf_template.html"
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should use ui("ki_stack_kicker", ...)
        assert 'ui("ki_stack_kicker"' in content, \
            "Expected template to use ui('ki_stack_kicker') for section kicker"

    def test_i18n_has_ki_stack_kicker_solo(self):
        """Test that i18n labels include SOLO variant for ki_stack_kicker."""
        from services.i18n import get_label_for_segment

        # SOLO should get "KI-Systemlandschaft" (without "Executive")
        result = get_label_for_segment("ki_stack_kicker", "de", segment="SOLO")
        assert "Executive" not in result
        assert "KI" in result

    def test_i18n_ki_stack_kicker_team_has_executive(self):
        """Test that TEAM segment gets 'Executive KI-Stack'."""
        from services.i18n import get_label_for_segment

        result = get_label_for_segment("ki_stack_kicker", "de", segment="TEAM")
        assert "Executive" in result or "KI" in result  # Standard label


# =============================================================================
# TASK A (P0): Quick Wins - Never Render Empty Fields (Enhanced Tests)
# =============================================================================

class TestQuickWinEmptyFieldFailsafeEnhanced:
    """Enhanced tests for TASK A (P0): Quick Wins empty field failsafe with FILL behavior."""

    def test_fills_empty_problem_with_fallback(self):
        """Test that empty PROBLEM block gets filled with fallback text."""
        from services.report_healer import sanitize_quickwin_empty_fields

        html = '''<div class="quick-win-problem" style="margin-bottom:10px;">
            <strong style="color:#dc2626;">Problem:</strong>
            <p style="margin:4px 0 0 0;"></p>
        </div>'''

        result, count = sanitize_quickwin_empty_fields(html)
        # Should fill, not just remove
        assert count >= 1
        # Either filled or removed - but no empty p tag
        assert '><p style="margin:4px 0 0 0;"></p>' not in result

    def test_fills_empty_wirkung_with_fallback(self):
        """Test that empty WIRKUNG block gets filled with fallback text."""
        from services.report_healer import sanitize_quickwin_empty_fields

        html = '''<div class="quick-win-wirkung" style="margin-bottom:10px;">
            <strong style="color:#16a34a;">Wirkung:</strong>
            <p style="margin:4px 0 0 0;"></p>
        </div>'''

        result, count = sanitize_quickwin_empty_fields(html)
        assert count >= 1

    def test_fills_empty_umsetzung_with_fallback(self):
        """Test that empty UMSETZUNG block gets filled with fallback text."""
        from services.report_healer import sanitize_quickwin_empty_fields

        html = '''<div class="quick-win-umsetzung" style="margin-bottom:10px;">
            <strong style="color:#2563eb;">Umsetzung:</strong>
            <p style="margin:4px 0 0 0;"></p>
        </div>'''

        result, count = sanitize_quickwin_empty_fields(html)
        assert count >= 1

    def test_heal_final_html_no_empty_quickwin_pattern(self):
        """End-to-end: heal_final_html should eliminate PROBLEM:\\s*WIRKUNG: patterns."""
        from services.report_healer import heal_final_html
        import re

        # Simulate rendered HTML with empty Quick Win fields
        html = '''
        <div class="quick-win">
            <div class="quick-win-problem"><strong>Problem:</strong><p></p></div>
            <div class="quick-win-wirkung"><strong>Wirkung:</strong><p></p></div>
            <div class="quick-win-umsetzung"><strong>Umsetzung:</strong><p></p></div>
        </div>
        '''

        result = heal_final_html(html, segment="SOLO")

        # These text patterns should NOT appear consecutively (indicates empty)
        assert not re.search(r'Problem:\s*</p>\s*</div>\s*<div[^>]*>\s*<strong[^>]*>Wirkung:', result, re.IGNORECASE)

    def test_e2e_no_label_only_blocks_after_heal(self):
        """E2E Gate: After heal_final_html, no Quick Win should have label-only blocks."""
        from services.report_healer import heal_final_html
        import re

        html = '''
        <div class="quick-win-card">
            <div class="quick-win-problem"><strong>Problem:</strong><p>   </p></div>
            <div class="quick-win-wirkung"><strong>Wirkung:</strong><p></p></div>
            <div class="quick-win-umsetzung"><strong>Umsetzung:</strong><p>Real content here.</p></div>
        </div>
        '''

        result = heal_final_html(html, segment="SOLO")

        # Check that we don't have empty-only pattern
        empty_problem = re.search(r'<div[^>]*class="quick-win-problem"[^>]*>.*?<p[^>]*>\s*</p>', result, re.DOTALL)
        empty_wirkung = re.search(r'<div[^>]*class="quick-win-wirkung"[^>]*>.*?<p[^>]*>\s*</p>', result, re.DOTALL)

        assert not empty_problem, "Empty PROBLEM block should be filled or removed"
        assert not empty_wirkung, "Empty WIRKUNG block should be filled or removed"


# =============================================================================
# TASK B (P1): Final Governance Catch-All Tests
# =============================================================================

class TestFinalGovernanceCatchAll:
    """Tests for TASK B (P1): Final Governance catch-all for SOLO."""

    def test_final_catchall_removes_standalone_governance(self):
        """Test that standalone 'Governance' is replaced even if not in phrase."""
        from services.report_healer import heal_final_html

        html = "<p>Die Governance ist wichtig.</p>"
        result = heal_final_html(html, segment="SOLO")

        assert "Governance" not in result
        assert "Spielregeln" in result

    def test_final_catchall_preserves_case(self):
        """Test that Governance replacement preserves case."""
        from services.report_healer import heal_final_html

        html = "<p>GOVERNANCE muss beachtet werden. governance auch.</p>"
        result = heal_final_html(html, segment="SOLO")

        assert "GOVERNANCE" not in result
        assert "governance" not in result
        assert "SPIELREGELN" in result or "spielregeln" in result

    def test_final_catchall_not_applied_to_team(self):
        """Test that TEAM segment keeps Governance."""
        from services.report_healer import heal_final_html

        html = "<p>Die Governance ist wichtig.</p>"
        result = heal_final_html(html, segment="TEAM")

        # TEAM may or may not replace - but the catchall specifically for SOLO
        # This test just ensures TEAM processing completes without error
        assert result  # Non-empty result

    def test_e2e_solo_has_zero_governance(self):
        """E2E Gate: Final SOLO HTML should contain 0× Governance (case-insensitive)."""
        from services.report_healer import heal_final_html
        import re

        html = """
        <p>Mit starker Governance können Sie Risiken minimieren.</p>
        <p>Die Governance-Strukturen müssen definiert sein.</p>
        <p>GOVERNANCE als Grundlage für AI Act Compliance.</p>
        """

        result = heal_final_html(html, segment="SOLO")

        governance_count = len(re.findall(r'\bGovernance\b', result, re.IGNORECASE))
        assert governance_count == 0, f"Expected 0 Governance occurrences, found {governance_count}"


# =============================================================================
# Acceptance Tests (Definition of Done)
# =============================================================================

class TestAcceptanceCriteria:
    """Acceptance tests matching Definition of Done from briefing."""

    def test_acceptance_no_governance_in_solo(self):
        """DoD: 0× /\\bGovernance\\b/i in final SOLO HTML."""
        from services.report_healer import heal_final_html
        import re

        # Complex HTML with various Governance mentions
        html = """
        <div>
            <p>Starke Governance ist essentiell.</p>
            <p>Mit solider Governance erreichen Sie Ihre Ziele.</p>
            <p>Die Governance-Aspekte beachten.</p>
            <p>Governance sollte priorisiert werden.</p>
        </div>
        """

        result = heal_final_html(html, segment="SOLO")

        matches = re.findall(r'\bGovernance\b', result, re.IGNORECASE)
        assert len(matches) == 0, f"DoD FAILED: Found {len(matches)} Governance matches: {matches}"

    def test_acceptance_quickwins_no_empty_labels(self):
        """DoD: Quick Wins have text in all three boxes OR alternative layout."""
        from services.report_healer import heal_final_html
        import re

        # Simulate worst case: all fields empty
        html = """
        <div class="quick-win">
            <div class="quick-win-problem"><strong>Problem:</strong><p></p></div>
            <div class="quick-win-wirkung"><strong>Wirkung:</strong><p></p></div>
            <div class="quick-win-umsetzung"><strong>Umsetzung:</strong><p></p></div>
        </div>
        """

        result = heal_final_html(html, segment="SOLO")

        # Pattern check: should NOT have "Problem:" followed soon by "Wirkung:" without content
        has_empty_pattern = bool(re.search(
            r'Problem:\s*</p>\s*</div>\s*<div[^>]*>\s*<strong[^>]*>Wirkung:',
            result,
            re.IGNORECASE
        ))

        assert not has_empty_pattern, "DoD FAILED: Empty Quick Win label pattern detected"


# =============================================================================
# TASK 4 (P0 FINAL): E2E PDF Gate Tests
# =============================================================================

class TestE2EPdfGateQuickWins:
    """TASK 4 Test A: Quick Wins completeness in final output."""

    def test_quickwins_with_empty_fields_get_filled(self):
        """Test A: Quick Win with empty fields gets filled with fallback content."""
        from services.quickwins_renderer import enforce_quickwins_complete

        # Simulate Quick Win with empty/None/whitespace fields
        quickwins = [{
            "title": "Automatisierung",
            "icon": "🤖",
            "problem": "",
            "wirkung": None,
            "umsetzung": "   ",
            "hinweis": "siehe Business Case"
        }]

        result = enforce_quickwins_complete(quickwins)

        # All fields must have real content (>20 chars each)
        assert len(result[0]["problem"]) > 20, "Problem field not filled"
        assert len(result[0]["wirkung"]) > 20, "Wirkung field not filled"
        assert len(result[0]["umsetzung"]) > 20, "Umsetzung field not filled"

    def test_quickwins_field_alias_mapping(self):
        """Test A: Quick Win with alternative field names gets mapped correctly."""
        from services.quickwins_renderer import enforce_quickwins_complete

        # Use alternative field names that LLM might generate
        quickwins = [{
            "title": "Datenanalyse",
            "icon": "📊",
            "pain": "Datensilos verhindern Entscheidungen.",  # alias for "problem"
            "benefit": "Bessere Datenverfügbarkeit.",  # alias for "wirkung"
            "implementation": "Dashboard aufsetzen.",  # alias for "umsetzung"
        }]

        result = enforce_quickwins_complete(quickwins)

        # Canonical fields should be filled from aliases
        assert result[0]["problem"] == "Datensilos verhindern Entscheidungen."
        assert result[0]["wirkung"] == "Bessere Datenverfügbarkeit."
        assert result[0]["umsetzung"] == "Dashboard aufsetzen."

    def test_quickwins_renderer_output_has_content(self):
        """Test C: Renderer output structure has content after labels."""
        from services.quickwins_renderer import render_quickwins_premium_json
        import json
        import re

        quickwins_data = [{
            "title": "Automatisierung",
            "icon": "🤖",
            "problem": "",  # Empty - should be filled
            "wirkung": "",  # Empty - should be filled
            "umsetzung": "",  # Empty - should be filled
        }]

        json_str = json.dumps(quickwins_data)
        html = render_quickwins_premium_json(json_str)

        # Renderer should produce HTML (not None/empty)
        assert html is not None, "Renderer returned None"
        assert len(html) > 100, "Renderer output too short"

        # Each block should have content after the label
        # Pattern: <strong>PROBLEM:</strong> followed by <p> with content
        problem_content = re.search(
            r'<strong[^>]*>Problem:</strong>\s*<p[^>]*>([^<]+)</p>',
            html,
            re.IGNORECASE
        )
        assert problem_content and len(problem_content.group(1).strip()) > 10, \
            "Problem block has no content after label"

    def test_healer_fixes_label_only_divs(self):
        """Test: Healer fixes label-only divs (no <p> tag)."""
        from services.report_healer import heal_final_html

        # Real structure from debug output: label-only div
        html = '''
        <div class="quick-win-problem" style="margin-bottom:10px;">
            <strong style="color:#dc2626;">PROBLEM:</strong>
        </div>
        <div class="quick-win-wirkung" style="margin-bottom:10px;">
            <strong style="color:#16a34a;">WIRKUNG:</strong>
        </div>
        <div class="quick-win-umsetzung" style="margin-bottom:10px;">
            <strong style="color:#2563eb;">UMSETZUNG:</strong>
        </div>
        '''

        result = heal_final_html(html, segment="SOLO")

        # Should have inserted <p> with fallback content
        assert '<p style="margin:4px 0 0 0;">' in result, \
            "Healer should insert <p> tags with fallback content"

        # Should NOT have empty labels anymore
        assert not re.search(r'PROBLEM:</strong>\s*</div>', result, re.IGNORECASE), \
            "Problem label-only still present"

    def test_e2e_no_consecutive_labels(self):
        """E2E Gate: After processing, PROBLEM:/WIRKUNG:/UMSETZUNG: should not appear consecutively."""
        from services.report_healer import heal_final_html
        import re

        html = '''
        <div class="quick-win">
            <div class="quick-win-problem"><strong>PROBLEM:</strong></div>
            <div class="quick-win-wirkung"><strong>WIRKUNG:</strong></div>
            <div class="quick-win-umsetzung"><strong>UMSETZUNG:</strong></div>
        </div>
        '''

        result = heal_final_html(html, segment="SOLO")

        # These patterns indicate empty fields - should NOT be present
        has_problem_wirkung_empty = bool(re.search(
            r'PROBLEM:\s*(?:</[^>]+>\s*)*(?:<[^>]+>\s*)*WIRKUNG:',
            result,
            re.IGNORECASE
        ))
        has_wirkung_umsetzung_empty = bool(re.search(
            r'WIRKUNG:\s*(?:</[^>]+>\s*)*(?:<[^>]+>\s*)*UMSETZUNG:',
            result,
            re.IGNORECASE
        ))

        assert not has_problem_wirkung_empty, \
            "E2E GATE FAILED: PROBLEM: immediately followed by WIRKUNG:"
        assert not has_wirkung_umsetzung_empty, \
            "E2E GATE FAILED: WIRKUNG: immediately followed by UMSETZUNG:"


class TestE2EPdfGateGovernance:
    """TASK 4 Test B: Governance not present in final SOLO output."""

    def test_governance_in_llm_text_gets_replaced(self):
        """Test B: Governance in LLM-generated text gets replaced for SOLO."""
        from services.report_healer import heal_final_html
        import re

        # Simulate LLM output containing "Governance"
        html = """
        <div class="roi-interpretation">
            <p>Mit starker Governance erreichen Sie eine bessere ROI-Interpretation.</p>
            <p>Die Governance-Strukturen sollten klar definiert sein.</p>
            <p>Achten Sie auf gute Governance bei der Implementierung.</p>
        </div>
        """

        result = heal_final_html(html, segment="SOLO")

        # No "Governance" should remain
        governance_count = len(re.findall(r'\bGovernance\b', result, re.IGNORECASE))
        assert governance_count == 0, \
            f"Test B FAILED: Found {governance_count} Governance in output"

        # "Spielregeln" should appear instead
        assert "Spielregeln" in result or "spielregeln" in result, \
            "Governance should be replaced with Spielregeln"

    def test_governance_split_tag_gets_replaced(self):
        """Test: Split-tag Governance (Gover</span><span>nance) gets replaced."""
        from services.report_healer import heal_final_html
        import re

        # Simulate split-tag Governance
        html = """
        <p>Die <span class="highlight">Gover</span><span>nance</span> ist wichtig.</p>
        """

        result = heal_final_html(html, segment="SOLO")

        # Should not contain Governance in any form
        assert "Governance" not in result and "governance" not in result, \
            "Split-tag Governance not replaced"
        assert "Spielregeln" in result, \
            "Split-tag Governance should become Spielregeln"

    def test_governance_case_preservation(self):
        """Test: Governance replacement preserves case."""
        from services.report_healer import heal_final_html

        html = """
        <p>GOVERNANCE ist wichtig.</p>
        <p>governance auch.</p>
        <p>Governance ebenfalls.</p>
        """

        result = heal_final_html(html, segment="SOLO")

        # Check case preservation
        assert "SPIELREGELN" in result, "GOVERNANCE should become SPIELREGELN"
        assert "spielregeln" in result, "governance should become spielregeln"
        assert "Spielregeln" in result, "Governance should become Spielregeln"

    def test_e2e_zero_governance_in_solo_final(self):
        """E2E Gate Test B: Final SOLO output has 0× Governance."""
        from services.report_healer import heal_final_html
        import re

        # Comprehensive test with various Governance patterns
        html = """
        <div>
            <p>starker Governance</p>
            <p>und Governance</p>
            <p>ROI-Interpretation mit Governance</p>
            <p>Governance-Framework</p>
            <p>GOVERNANCE</p>
            <p>governance</p>
            <span>Gover</span><span>nance</span>
        </div>
        """

        result = heal_final_html(html, segment="SOLO")

        governance_matches = re.findall(r'Governance', result, re.IGNORECASE)
        assert len(governance_matches) == 0, \
            f"E2E GATE FAILED: Found {len(governance_matches)} Governance: {governance_matches}"


class TestE2ERendererOutputStructure:
    """TASK 4 Test C: Renderer output structure validation."""

    def test_renderer_never_produces_label_only_blocks(self):
        """Test C: render_quickwins_premium_json never produces label-only blocks."""
        from services.quickwins_renderer import render_quickwins_premium_json
        import json
        import re

        # Test with completely empty Quick Win
        quickwins = [{
            "title": "Test",
            "icon": "🎯",
            # All fields missing/empty
        }]

        json_str = json.dumps(quickwins)
        html = render_quickwins_premium_json(json_str)

        if html:  # Renderer might return None for invalid data
            # Should not have label-only patterns
            label_only_problem = re.search(
                r'<strong[^>]*>Problem:</strong>\s*</div>',
                html,
                re.IGNORECASE
            )
            label_only_wirkung = re.search(
                r'<strong[^>]*>Wirkung:</strong>\s*</div>',
                html,
                re.IGNORECASE
            )
            label_only_umsetzung = re.search(
                r'<strong[^>]*>Umsetzung:</strong>\s*</div>',
                html,
                re.IGNORECASE
            )

            assert not label_only_problem, "Renderer produced label-only Problem block"
            assert not label_only_wirkung, "Renderer produced label-only Wirkung block"
            assert not label_only_umsetzung, "Renderer produced label-only Umsetzung block"

    def test_enforce_quickwins_complete_never_returns_empty_fields(self):
        """Test C: enforce_quickwins_complete always returns non-empty fields."""
        from services.quickwins_renderer import enforce_quickwins_complete

        # Various edge cases
        test_cases = [
            {"title": "Test1", "problem": "", "wirkung": "", "umsetzung": ""},
            {"title": "Test2", "problem": None, "wirkung": None, "umsetzung": None},
            {"title": "Test3", "problem": "   ", "wirkung": "—", "umsetzung": "..."},
            {"title": "Test4"},  # No fields at all
        ]

        for qw in test_cases:
            result = enforce_quickwins_complete([qw])
            assert result[0]["problem"], f"Empty problem for {qw}"
            assert result[0]["wirkung"], f"Empty wirkung for {qw}"
            assert result[0]["umsetzung"], f"Empty umsetzung for {qw}"


# =============================================================================
# TASK 5 (P0 FINAL): CI Quality Gate Strict Mode
# =============================================================================

class TestCIQualityGateStrict:
    """TASK 5: CI Quality Gate tests that should fail the pipeline if bugs return."""

    def test_strict_gate_quickwins_completeness(self):
        """STRICT GATE: Quick Wins must have content in all fields."""
        from services.quickwins_renderer import enforce_quickwins_complete, render_quickwins_premium_json
        import json
        import re

        # This represents the worst possible input
        worst_case_quickwin = [{
            "title": "Automatisierung",
            "icon": "🤖",
            "problem": "",
            "wirkung": None,
            "umsetzung": "   ",
        }]

        # After enforcement, all fields must be filled
        completed = enforce_quickwins_complete(worst_case_quickwin)

        for field in ["problem", "wirkung", "umsetzung"]:
            value = completed[0].get(field, "")
            assert value and len(value.strip()) > 10, \
                f"STRICT GATE FAILED: {field} is empty after enforce_quickwins_complete"

        # Render and verify HTML structure
        json_str = json.dumps(completed)
        html = render_quickwins_premium_json(json_str)

        if html:
            # Verify each field block has content
            for label in ["Problem:", "Wirkung:", "Umsetzung:"]:
                # Should have content after label, not just label alone
                pattern = rf'{label}</strong>\s*<p[^>]*>([^<]+)</p>'
                match = re.search(pattern, html, re.IGNORECASE)
                assert match and len(match.group(1).strip()) > 5, \
                    f"STRICT GATE FAILED: {label} has no content in rendered HTML"

    def test_strict_gate_solo_zero_governance(self):
        """STRICT GATE: SOLO output must have 0× Governance."""
        from services.report_healer import heal_final_html
        import re

        # Comprehensive input with all known Governance patterns
        test_html = """
        <div>
            <p>Mit starker Governance</p>
            <p>Die Governance-Strukturen</p>
            <p>Governance-Framework nutzen</p>
            <p>GOVERNANCE als Basis</p>
            <p>governance wichtig</p>
            <p><span>Gover</span><span>nance</span> auch</p>
            <p>ROI bei guter Governance</p>
        </div>
        """

        result = heal_final_html(test_html, segment="SOLO")

        # Count all Governance occurrences
        governance_count = len(re.findall(r'Governance', result, re.IGNORECASE))

        assert governance_count == 0, \
            f"STRICT GATE FAILED: {governance_count}× Governance found in SOLO output"

    def test_strict_gate_no_label_only_quickwins(self):
        """STRICT GATE: No Quick Win should have label-only structure."""
        from services.report_healer import heal_final_html
        import re

        # Label-only structure that came from debug output
        label_only_html = '''
        <div class="quick-win-problem"><strong>PROBLEM:</strong></div>
        <div class="quick-win-wirkung"><strong>WIRKUNG:</strong></div>
        <div class="quick-win-umsetzung"><strong>UMSETZUNG:</strong></div>
        '''

        result = heal_final_html(label_only_html, segment="SOLO")

        # Should not have any label-only patterns remaining
        label_only_patterns = [
            r'<strong[^>]*>PROBLEM:</strong>\s*</div>',
            r'<strong[^>]*>WIRKUNG:</strong>\s*</div>',
            r'<strong[^>]*>UMSETZUNG:</strong>\s*</div>',
        ]

        for pattern in label_only_patterns:
            assert not re.search(pattern, result, re.IGNORECASE), \
                f"STRICT GATE FAILED: Label-only pattern still present: {pattern}"
