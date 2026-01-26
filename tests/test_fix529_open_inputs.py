#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for FIX-529: Offene Inputs Sammelseite + Marker-only

Tests cover:
- Marker parsing (⟦INPUT:...⟧ and [[INPUT:...]])
- Forbidden text validation (TBD, Lorem, ???)
- Open inputs page rendering
- Marker CSS styling
"""

import pytest
from services.report_facts import (
    OpenInput,
    collect_open_inputs,
    validate_no_forbidden_text,
    validate_no_platzhalter_text,
    generate_open_inputs_html,
    collect_and_render_open_inputs,
    MARKER_PATTERN,
    MARKER_PATTERN_ASCII,
    FORBIDDEN_TEXT_PATTERNS,
    MARKER_CSS,
)


class TestMarkerParsing:
    """Tests for marker pattern parsing."""

    def test_unicode_marker_pattern(self):
        """Test parsing of Unicode markers ⟦INPUT:...⟧."""
        text = "Some text ⟦INPUT:company_name|Firmenname|Bitte den Firmennamen eintragen⟧ more text"
        matches = MARKER_PATTERN.findall(text)

        assert len(matches) == 1
        assert matches[0][0] == "company_name"
        assert matches[0][1] == "Firmenname"
        assert "Firmennamen" in matches[0][2]

    def test_ascii_marker_pattern(self):
        """Test parsing of ASCII markers [[INPUT:...]]."""
        text = "Some text [[INPUT:revenue|Umsatz|Optional hint]] more text"
        matches = MARKER_PATTERN_ASCII.findall(text)

        assert len(matches) == 1
        assert matches[0][0] == "revenue"
        assert matches[0][1] == "Umsatz"

    def test_marker_with_empty_hint(self):
        """Test marker with empty hint field."""
        text = "⟦INPUT:email|E-Mail|⟧"
        matches = MARKER_PATTERN.findall(text)

        assert len(matches) == 1
        assert matches[0][0] == "email"
        assert matches[0][2] == ""

    def test_multiple_markers(self):
        """Test parsing multiple markers in same text."""
        text = """
        <p>⟦INPUT:name|Name|Enter name⟧</p>
        <p>⟦INPUT:phone|Telefon|Enter phone⟧</p>
        """
        matches = MARKER_PATTERN.findall(text)

        assert len(matches) == 2


class TestCollectOpenInputs:
    """Tests for collect_open_inputs function."""

    def test_collect_from_html_sections(self):
        """Test collecting markers from HTML sections."""
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Text ⟦INPUT:goal|Hauptziel|Beschreiben Sie das Ziel⟧</p>",
            "RISKS_HTML": "<p>Risk ⟦INPUT:risk_level|Risikostufe|⟧</p>",
            "non_html_key": "⟦INPUT:ignored|Ignored|This is not HTML⟧",
        }

        inputs, html = collect_open_inputs(sections)

        assert len(inputs) == 2
        assert inputs[0].key == "goal"
        assert inputs[0].label == "Hauptziel"
        assert inputs[0].section_id == "EXECUTIVE_SUMMARY_HTML"
        assert inputs[1].key == "risk_level"

    def test_collect_both_marker_types(self):
        """Test collecting both Unicode and ASCII markers."""
        sections = {
            "SUMMARY_HTML": """
                <p>⟦INPUT:unicode_key|Unicode Label|hint1⟧</p>
                <p>[[INPUT:ascii_key|ASCII Label|hint2]]</p>
            """,
        }

        inputs, html = collect_open_inputs(sections)

        assert len(inputs) == 2
        keys = [inp.key for inp in inputs]
        assert "unicode_key" in keys
        assert "ascii_key" in keys

    def test_empty_sections_return_empty(self):
        """Test that empty sections return empty results."""
        sections = {
            "SUMMARY_HTML": "<p>No markers here</p>",
        }

        inputs, html = collect_open_inputs(sections)

        assert len(inputs) == 0
        assert html == ""


class TestForbiddenTextValidation:
    """Tests for forbidden text validation (TBD, Lorem, ???, etc.)."""

    def test_detect_tbd(self):
        """Test detection of TBD text."""
        sections = {
            "SUMMARY_HTML": "<p>This section is TBD.</p>",
        }

        passed, violations = validate_no_forbidden_text(sections)

        assert passed is False
        assert any("TBD" in v for v in violations)

    def test_detect_triple_question_marks(self):
        """Test detection of ??? placeholder."""
        sections = {
            "RISKS_HTML": "<p>Risk level: ???</p>",
        }

        passed, violations = validate_no_forbidden_text(sections)

        assert passed is False
        assert any("???" in v for v in violations)

    def test_detect_lorem_ipsum(self):
        """Test detection of Lorem ipsum sample text."""
        sections = {
            "SUMMARY_HTML": "<p>Lorem ipsum dolor sit amet</p>",
        }

        passed, violations = validate_no_forbidden_text(sections)

        assert passed is False
        assert any("Lorem ipsum" in v for v in violations)

    def test_detect_xxx_marker(self):
        """Test detection of XXX marker."""
        sections = {
            "SUMMARY_HTML": "<p>Content XXX placeholder</p>",
        }

        passed, violations = validate_no_forbidden_text(sections)

        assert passed is False

    def test_detect_todo_marker(self):
        """Test detection of TODO marker."""
        sections = {
            "RISKS_HTML": "<p>TODO: Add risk details</p>",
        }

        passed, violations = validate_no_forbidden_text(sections)

        assert passed is False
        assert any("TODO" in v for v in violations)

    def test_detect_template_variable(self):
        """Test detection of template variable leaks ${...}."""
        sections = {
            "SUMMARY_HTML": "<p>Company: ${COMPANY_NAME}</p>",
        }

        passed, violations = validate_no_forbidden_text(sections)

        assert passed is False

    def test_clean_text_passes(self):
        """Test that clean text passes validation."""
        sections = {
            "SUMMARY_HTML": "<p>This is a complete summary with no placeholders.</p>",
            "RISKS_HTML": "<p>Risk analysis shows moderate exposure.</p>",
        }

        passed, violations = validate_no_forbidden_text(sections)

        assert passed is True
        assert len(violations) == 0

    def test_skips_open_inputs_section(self):
        """Test that OPEN_INPUTS section is skipped."""
        sections = {
            "OPEN_INPUTS_HTML": "<p>TBD ??? Lorem ipsum TODO</p>",
        }

        passed, violations = validate_no_forbidden_text(sections)

        assert passed is True  # Skipped


class TestPlatzhalterValidation:
    """Tests for Platzhalter text validation."""

    def test_detect_platzhalter_word(self):
        """Test detection of 'Platzhalter' word."""
        sections = {
            "SUMMARY_HTML": "<p>Dies ist ein Platzhalter-Text.</p>",
        }

        passed, violations = validate_no_platzhalter_text(sections)

        assert passed is False
        assert any("Platzhalter" in v for v in violations)

    def test_case_insensitive_detection(self):
        """Test case-insensitive detection of Platzhalter."""
        sections = {
            "SUMMARY_HTML": "<p>PLATZHALTER text here</p>",
        }

        passed, violations = validate_no_platzhalter_text(sections)

        assert passed is False

    def test_clean_text_without_platzhalter(self):
        """Test that text without Platzhalter passes."""
        sections = {
            "SUMMARY_HTML": "<p>Vollständiger Text ohne Lücken.</p>",
        }

        passed, violations = validate_no_platzhalter_text(sections)

        assert passed is True


class TestOpenInputsHtmlGeneration:
    """Tests for Open Inputs page HTML generation."""

    def test_generate_html_with_inputs(self):
        """Test HTML generation with open inputs."""
        inputs = [
            OpenInput(key="name", label="Firmenname", hint="Enter company name", section_id="SUMMARY_HTML"),
            OpenInput(key="revenue", label="Umsatz", hint="", section_id="BUSINESS_CASE_HTML"),
        ]

        html = generate_open_inputs_html(inputs)

        assert '<section class="open-inputs' in html
        assert 'Offene Inputs' in html
        assert '<table class="open-inputs-table"' in html
        assert 'marker-pill' in html
        assert 'Firmenname' in html
        assert 'Umsatz' in html

    def test_generate_html_empty_inputs(self):
        """Test HTML generation with no inputs returns empty."""
        inputs = []

        html = generate_open_inputs_html(inputs)

        assert html == ""

    def test_html_contains_marker_count(self):
        """Test HTML footer contains marker count."""
        inputs = [
            OpenInput(key="a", label="A", hint="", section_id="X_HTML"),
            OpenInput(key="b", label="B", hint="", section_id="Y_HTML"),
            OpenInput(key="c", label="C", hint="", section_id="Z_HTML"),
        ]

        html = generate_open_inputs_html(inputs)

        assert "3" in html  # Count of markers

    def test_section_display_formatting(self):
        """Test section names are formatted nicely."""
        inputs = [
            OpenInput(key="x", label="X", hint="", section_id="EXECUTIVE_SUMMARY_HTML"),
        ]

        html = generate_open_inputs_html(inputs)

        # Should show "Executive Summary" not "EXECUTIVE_SUMMARY_HTML"
        assert "Executive Summary" in html


class TestCollectAndRenderOpenInputs:
    """Tests for combined collect and render function."""

    def test_collect_and_render_full_pipeline(self):
        """Test full collection and rendering pipeline."""
        sections = {
            "SUMMARY_HTML": "<p>Text ⟦INPUT:test_key|Test Label|Test hint⟧</p>",
        }

        inputs, html = collect_and_render_open_inputs(sections)

        assert len(inputs) == 1
        assert "open-inputs-table" in html
        assert "Test Label" in html


class TestMarkerCSS:
    """Tests for marker CSS styling."""

    def test_css_contains_marker_pill_style(self):
        """Test CSS includes marker-pill styling."""
        assert ".marker-pill" in MARKER_CSS
        assert "border-radius" in MARKER_CSS

    def test_css_contains_table_styles(self):
        """Test CSS includes table styling."""
        assert ".open-inputs-table" in MARKER_CSS
        assert "border-collapse" in MARKER_CSS

    def test_css_contains_inline_marker_style(self):
        """Test CSS includes inline marker styling."""
        assert ".inline-marker" in MARKER_CSS
