#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-529 Tests: Open Inputs Marker System

Tests for:
- Marker extraction from text
- Marker deduplication
- Inline marker rendering
- OPEN_INPUTS_HTML generation
"""
import pytest


class TestMarkerExtraction:
    """Tests for marker extraction functions."""

    def test_extract_single_marker(self):
        """Test extraction of a single marker."""
        from services.open_inputs_marker import extract_markers_from_text

        text = "Die Analyse zeigt [INPUT:mitarbeiter|Mitarbeiterzahl|Bitte angeben] Ergebnisse."
        markers = extract_markers_from_text(text, "TEST_SECTION")

        assert len(markers) == 1
        assert markers[0].key == "mitarbeiter"
        assert markers[0].label == "Mitarbeiterzahl"
        assert markers[0].hint == "Bitte angeben"
        assert markers[0].section == "TEST_SECTION"

    def test_extract_multiple_markers(self):
        """Test extraction of multiple markers."""
        from services.open_inputs_marker import extract_markers_from_text

        text = """
        Umsatz: [INPUT:umsatz|Jahresumsatz|EUR-Betrag erforderlich]
        Team: [INPUT:team_size|Teamgroesse|Anzahl Personen]
        """
        markers = extract_markers_from_text(text)

        assert len(markers) == 2
        assert markers[0].key == "umsatz"
        assert markers[1].key == "team_size"

    def test_extract_no_markers(self):
        """Test extraction when no markers present."""
        from services.open_inputs_marker import extract_markers_from_text

        text = "Dies ist normaler Text ohne Marker."
        markers = extract_markers_from_text(text)

        assert len(markers) == 0

    def test_extract_empty_input(self):
        """Test extraction with empty/None input."""
        from services.open_inputs_marker import extract_markers_from_text

        assert extract_markers_from_text("") == []
        assert extract_markers_from_text(None) == []


class TestMarkerDeduplication:
    """Tests for marker deduplication."""

    def test_deduplicate_by_key(self):
        """Test that markers with same key are deduplicated."""
        from services.open_inputs_marker import extract_markers_from_sections

        sections = {
            "SECTION_A": "Value: [INPUT:value|Wert|Hint A]",
            "SECTION_B": "Value: [INPUT:value|Wert|Hint B]",
            "SECTION_C": "Other: [INPUT:other|Anderer|Hint C]",
        }

        result = extract_markers_from_sections(sections)

        assert result.unique_marker_count == 2
        assert result.total_marker_count == 3

        keys = [m.key for m in result.markers]
        assert "value" in keys
        assert "other" in keys


class TestInlineRendering:
    """Tests for inline marker rendering."""

    def test_render_inline_marker(self):
        """Test inline marker HTML rendering."""
        from services.open_inputs_marker import render_inline_marker, OpenInputMarker

        marker = OpenInputMarker(
            key="test_key",
            label="Test Label",
            hint="Test Hint",
        )

        html = render_inline_marker(marker)

        assert 'class="input-marker"' in html
        assert 'data-key="test_key"' in html
        assert 'title="Test Hint"' in html
        assert "Test Label" in html

    def test_replace_markers_with_inline(self):
        """Test replacing markers with inline HTML."""
        from services.open_inputs_marker import replace_markers_with_inline

        text = "Umsatz: [INPUT:umsatz|Jahresumsatz|Betrag] betraegt X Euro."
        result = replace_markers_with_inline(text)

        assert "[INPUT:" not in result
        assert 'class="input-marker"' in result
        assert "Jahresumsatz" in result


class TestOpenInputsHtmlGeneration:
    """Tests for OPEN_INPUTS_HTML generation."""

    def test_generate_html_with_markers(self):
        """Test HTML generation with markers."""
        from services.open_inputs_marker import (
            generate_open_inputs_html,
            OpenInputsResult,
            OpenInputMarker,
        )

        markers = [
            OpenInputMarker("key1", "Label 1", "Hint 1", "SECTION_A"),
            OpenInputMarker("key2", "Label 2", "Hint 2", "SECTION_B"),
        ]
        result = OpenInputsResult(
            markers=markers,
            unique_marker_count=2,
        )

        html = generate_open_inputs_html(result)

        assert 'class="open-inputs' in html
        assert "Offene Inputs" in html
        assert "Label 1" in html
        assert "Label 2" in html
        assert "Hint 1" in html
        assert "Hint 2" in html

    def test_generate_html_empty(self):
        """Test HTML generation with no markers."""
        from services.open_inputs_marker import (
            generate_open_inputs_html,
            OpenInputsResult,
        )

        result = OpenInputsResult()
        html = generate_open_inputs_html(result)

        assert html == ""


class TestProcessOpenInputs:
    """Tests for main integration function."""

    def test_process_open_inputs_full(self):
        """Test complete open inputs processing."""
        from services.open_inputs_marker import process_open_inputs

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Summary with [INPUT:budget|Budget|EUR-Betrag]</p>",
            "QUICK_WINS_HTML": "<p>Quick wins text</p>",
            "ROI_HTML": "<p>ROI needs [INPUT:budget|Budget|EUR] and [INPUT:roi_target|Ziel-ROI|Prozent]</p>",
        }

        updated, result = process_open_inputs(sections)

        assert result.unique_marker_count == 2
        assert result.total_marker_count == 3

        assert "[INPUT:" not in updated["EXECUTIVE_SUMMARY_HTML"]
        assert 'class="input-marker"' in updated["EXECUTIVE_SUMMARY_HTML"]

        assert "OPEN_INPUTS_HTML" in updated
        assert "Budget" in updated["OPEN_INPUTS_HTML"]
        assert "Ziel-ROI" in updated["OPEN_INPUTS_HTML"]

    def test_process_open_inputs_no_markers(self):
        """Test processing when no markers present."""
        from services.open_inputs_marker import process_open_inputs

        sections = {
            "SUMMARY_HTML": "<p>Normal summary without markers</p>",
        }

        updated, result = process_open_inputs(sections)

        assert result.unique_marker_count == 0
        assert "OPEN_INPUTS_HTML" not in updated


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_marker(self):
        """Test marker string creation."""
        from services.open_inputs_marker import create_marker

        marker = create_marker("test_key", "Test Label", "Test Hint")

        assert marker == "[INPUT:test_key|Test Label|Test Hint]"

    def test_create_marker_invalid_key(self):
        """Test marker creation with invalid key."""
        from services.open_inputs_marker import create_marker

        with pytest.raises(ValueError):
            create_marker("123invalid", "Label", "Hint")

        with pytest.raises(ValueError):
            create_marker("has-dash", "Label", "Hint")

    def test_has_markers(self):
        """Test marker presence detection."""
        from services.open_inputs_marker import has_markers

        assert has_markers("[INPUT:key|label|hint]") is True
        assert has_markers("No markers here") is False
        assert has_markers("") is False
        assert has_markers(None) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
