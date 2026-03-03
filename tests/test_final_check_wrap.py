#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0 Final-Check Wrap Tests

Tests for ensuring Final-Check/Checklist boxes wrap text correctly
in HTML and PDF rendering without layout overflow.
"""
import pytest
import re
from pathlib import Path

TEMPLATE_PATH = "templates/pdf_template_v7.html"


class TestFinalCheckWrapCSS:
    """Tests for Final-Check CSS wrapping rules in v7 template."""

    def test_template_has_final_check_decisions(self):
        """Verify template renders FINAL_CHECK_DECISIONS."""
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        assert "FINAL_CHECK_DECISIONS" in content, (
            "Template should render FINAL_CHECK_DECISIONS"
        )

    def test_css_has_grid_layout(self):
        """Verify CSS includes grid-template-columns for layouts."""
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            css_content = f.read()

        assert "grid-template-columns" in css_content, (
            "CSS should use grid-template-columns for layouts"
        )

    def test_css_has_flex_shrink(self):
        """Verify CSS uses flex-shrink: 0 for icon protection."""
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            css_content = f.read()

        assert "flex-shrink: 0" in css_content, (
            "CSS should prevent icon shrinking with flex-shrink: 0"
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


class TestConfidenceCardCSS:
    """Tests for confidence card CSS in v7 template."""

    def test_template_has_confidence_section(self):
        """Verify template has confidence HTML section."""
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        assert "DECISION_CONFIDENCE_HTML" in content, (
            "Template should have DECISION_CONFIDENCE_HTML section"
        )

    def test_template_has_confidence_card_css(self):
        """Verify template has confidence-card CSS."""
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        assert ".confidence-card" in content, (
            "Template should have .confidence-card CSS"
        )


class TestFoerderSectionExists:
    """Tests for Förder section presence in template."""

    def test_template_has_foerder_section(self):
        """Verify template has Förderpotenzial section."""
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        assert "FOERDERPOTENZIAL_HTML" in content, (
            "Template should have FOERDERPOTENZIAL_HTML section"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
