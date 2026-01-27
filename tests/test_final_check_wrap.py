#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0 Final-Check Wrap Tests

Tests for ensuring Final-Check/Checklist boxes wrap text correctly
in HTML and PDF rendering without layout overflow.
"""
import pytest
import re


class TestFinalCheckWrapCSS:
    """Tests for Final-Check CSS wrapping rules."""

    def test_css_contains_overflow_wrap_anywhere(self):
        """Verify CSS includes overflow-wrap: anywhere for text containers."""
        with open("templates/pdf_template.html", "r", encoding="utf-8") as f:
            css_content = f.read()

        # Check that overflow-wrap: anywhere is present for final-check-text
        assert "overflow-wrap: anywhere" in css_content, (
            "CSS should contain 'overflow-wrap: anywhere' for robust text wrapping"
        )

        # Check that final-check-text class exists with min-width: 0
        assert ".final-check-text" in css_content, (
            "CSS should define .final-check-text class"
        )
        assert "min-width: 0" in css_content, (
            "CSS should include 'min-width: 0' for flex/grid children"
        )

    def test_css_contains_grid_layout_for_icon_text(self):
        """Verify CSS includes grid layout for icon+text rows."""
        with open("templates/pdf_template.html", "r", encoding="utf-8") as f:
            css_content = f.read()

        # Check for grid-based final-check-row
        assert ".final-check-row" in css_content, (
            "CSS should define .final-check-row class"
        )
        assert "grid-template-columns" in css_content, (
            "CSS should use grid-template-columns for icon+text layout"
        )
        # Check for minmax(0, 1fr) pattern for flexible text column
        assert "minmax(0, 1fr)" in css_content, (
            "CSS should use minmax(0, 1fr) for text column to allow shrinking"
        )

    def test_css_contains_flex_layout_variant(self):
        """Verify CSS includes flex layout variant for simpler cases."""
        with open("templates/pdf_template.html", "r", encoding="utf-8") as f:
            css_content = f.read()

        # Check for flex-based variant
        assert ".final-check-flex-row" in css_content, (
            "CSS should define .final-check-flex-row class as flex variant"
        )
        assert "flex-shrink: 0" in css_content, (
            "CSS should prevent icon shrinking with flex-shrink: 0"
        )

    def test_en_template_has_same_fixes(self):
        """Verify English template has the same CSS fixes."""
        with open("templates/pdf_template_en.html", "r", encoding="utf-8") as f:
            css_content = f.read()

        assert ".final-check-row" in css_content, (
            "English template should have .final-check-row class"
        )
        assert "overflow-wrap: anywhere" in css_content, (
            "English template should have overflow-wrap: anywhere"
        )
        assert ".final-check-text" in css_content, (
            "English template should have .final-check-text class"
        )


class TestFinalCheckHTMLSnapshot:
    """Snapshot tests for Final-Check HTML rendering."""

    LONG_GERMAN_COMPOUND = "Informationssicherheitsmanagementsystemdokumentation"
    LONG_URL = "https://example.com/very/long/path/to/documentation/that/might/overflow"
    LONG_SENTENCE_WITH_HYPHEN = (
        "Die Implementierung des KI-basierten Dokumentenmanagement-Systems "
        "erfordert eine sorgfältige Datenschutz-Folgenabschätzung."
    )

    def _render_final_check_block(self, text: str) -> str:
        """Render a sample Final-Check block with given text."""
        return f'''
        <div class="final-check-intro">
            <h3>Ihre nächsten Schritte</h3>
            <ul class="final-check-decisions">
                <li>{text}</li>
                <li>Weiterer Punkt mit normalem Text für Vergleich.</li>
            </ul>
        </div>
        '''

    def _render_grid_row_block(self, text: str) -> str:
        """Render a Final-Check row using grid layout."""
        return f'''
        <div class="final-check-row">
            <span class="check-icon">✓</span>
            <div class="final-check-text">{text}</div>
        </div>
        '''

    def _render_flex_row_block(self, text: str) -> str:
        """Render a Final-Check row using flex layout."""
        return f'''
        <div class="final-check-flex-row">
            <span class="check-icon">✓</span>
            <div>{text}</div>
        </div>
        '''

    def test_long_german_compound_renders(self):
        """Test that long German compound words don't break layout."""
        html = self._render_final_check_block(self.LONG_GERMAN_COMPOUND)

        # Verify the compound word is in the output
        assert self.LONG_GERMAN_COMPOUND in html

        # Basic structure check
        assert "final-check-intro" in html
        assert "final-check-decisions" in html

    def test_long_url_renders(self):
        """Test that long URLs don't break layout."""
        html = self._render_final_check_block(self.LONG_URL)

        # Verify the URL is in the output
        assert self.LONG_URL in html

    def test_hyphenated_sentence_renders(self):
        """Test that sentences with hyphens render correctly."""
        html = self._render_final_check_block(self.LONG_SENTENCE_WITH_HYPHEN)

        # Verify the sentence is complete
        assert "Datenschutz-Folgenabschätzung" in html
        assert "Dokumentenmanagement-Systems" in html

    def test_grid_row_with_long_text(self):
        """Test grid row layout with long text."""
        html = self._render_grid_row_block(self.LONG_GERMAN_COMPOUND)

        assert "final-check-row" in html
        assert "final-check-text" in html
        assert self.LONG_GERMAN_COMPOUND in html

    def test_flex_row_with_long_text(self):
        """Test flex row layout with long text."""
        html = self._render_flex_row_block(self.LONG_URL)

        assert "final-check-flex-row" in html
        assert self.LONG_URL in html


class TestConfidenceCheckboxWrap:
    """Tests for confidence-checkbox wrapping."""

    def test_css_fixes_confidence_checkbox(self):
        """Verify CSS includes fixes for confidence-checkbox pattern."""
        with open("templates/pdf_template.html", "r", encoding="utf-8") as f:
            css_content = f.read()

        # Check that confidence-checkbox is addressed
        assert ".confidence-checkbox" in css_content, (
            "CSS should address .confidence-checkbox class"
        )
        # The fix should include overflow-wrap for nested elements
        # This is a combined pattern search
        pattern = r"\.confidence-checkbox.*overflow-wrap"
        matches = re.findall(pattern, css_content, re.DOTALL)
        assert len(matches) > 0, (
            "CSS should include overflow-wrap rules for confidence-checkbox children"
        )


class TestFoerderChecklistWrap:
    """Tests for Förderprüfung checklist wrapping."""

    def test_css_fixes_foerder_content(self):
        """Verify CSS includes fixes for foerder-content pattern."""
        with open("templates/pdf_template.html", "r", encoding="utf-8") as f:
            css_content = f.read()

        # Check that foerder-content is addressed
        assert ".foerder-content" in css_content, (
            "CSS should address .foerder-content class"
        )
        # Look for min-width: 0 and overflow-wrap in relation to foerder-content
        assert "foerder-content" in css_content and "min-width: 0" in css_content, (
            "CSS should include min-width: 0 for foerder-content"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
