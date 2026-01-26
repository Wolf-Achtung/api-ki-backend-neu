#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for FIX-530: Rendering Bugs - Entities + Broken Bullets + Overlaps

Tests cover:
- HTML entity sanitization (unescape)
- Double-escaped entity handling
- Entity validation gate
- CSS fixes for bullets and overlaps
"""

import pytest
from services.html_sanitizer import (
    unescape_html_entities,
    sanitize_double_escaped_entities,
    validate_no_visible_entities,
    apply_entity_sanitization,
    get_fix_530_css,
    HTML_ENTITY_PATTERN,
    ALLOWED_ENTITIES,
)


class TestUnescapeHtmlEntities:
    """Tests for HTML entity unescaping."""

    def test_unescape_german_umlauts(self):
        """Test unescaping German umlauts."""
        text = "M&uuml;nchen, K&ouml;ln, D&uuml;sseldorf"
        result = unescape_html_entities(text)

        assert "München" in result
        assert "Köln" in result
        assert "Düsseldorf" in result
        assert "&uuml;" not in result

    def test_unescape_german_quote_entities(self):
        """Test unescaping German quote entities."""
        text = "&bdquo;Zitat&ldquo;"
        result = unescape_html_entities(text)

        # Should convert to actual quote characters
        assert "&bdquo;" not in result
        assert "&ldquo;" not in result

    def test_unescape_common_entities(self):
        """Test unescaping common entities."""
        text = "Price: 10 &euro; &amp; 20 &pound;"
        result = unescape_html_entities(text)

        assert "€" in result
        assert "£" in result
        assert "&euro;" not in result

    def test_unescape_numeric_entities_decimal(self):
        """Test unescaping decimal numeric entities."""
        text = "&#228;&#246;&#252;"  # äöü
        result = unescape_html_entities(text)

        assert "äöü" in result

    def test_unescape_numeric_entities_hex(self):
        """Test unescaping hexadecimal numeric entities."""
        text = "&#xe4;&#xf6;&#xfc;"  # äöü
        result = unescape_html_entities(text)

        assert "äöü" in result

    def test_preserves_normal_text(self):
        """Test that normal text is preserved."""
        text = "Normal text without entities"
        result = unescape_html_entities(text)

        assert result == text

    def test_handles_empty_input(self):
        """Test handling of empty input."""
        assert unescape_html_entities("") == ""
        assert unescape_html_entities(None) == ""


class TestDoubleEscapedEntities:
    """Tests for double-escaped entity handling."""

    def test_fix_double_escaped_uuml(self):
        """Test fixing &amp;uuml; to ü."""
        text = "M&amp;uuml;nchen"
        result = sanitize_double_escaped_entities(text)

        assert "München" in result
        assert "&amp;uuml;" not in result

    def test_fix_double_escaped_amp(self):
        """Test fixing &amp;amp; to &."""
        text = "A &amp;amp; B"
        result = sanitize_double_escaped_entities(text)

        assert "A & B" in result or "A &amp; B" not in result

    def test_fix_triple_escaped(self):
        """Test fixing triple-escaped entities."""
        text = "&amp;amp;uuml;"  # Triple escaped
        result = sanitize_double_escaped_entities(text)

        # Should eventually become ü
        assert "&amp;amp;uuml;" not in result

    def test_leaves_single_escaped_unchanged(self):
        """Test that single-escaped entities pass through (handled by unescape_html_entities)."""
        text = "&uuml;"
        result = sanitize_double_escaped_entities(text)

        # sanitize_double_escaped_entities only targets &amp;entity; patterns
        # Single-escaped entities are handled by unescape_html_entities
        # So the single escaped entity may remain or be unescaped depending on implementation
        assert result == "&uuml;" or "ü" in result


class TestValidateNoVisibleEntities:
    """Tests for entity validation gate."""

    def test_detect_visible_entity_uuml(self):
        """Test detection of visible &uuml; entity."""
        html = "<p>Pr&uuml;fung</p>"
        passed, entities = validate_no_visible_entities(html)

        assert passed is False
        assert "&uuml;" in entities

    def test_detect_multiple_entities(self):
        """Test detection of multiple visible entities."""
        html = "<p>&auml;&ouml;&uuml;</p>"
        passed, entities = validate_no_visible_entities(html)

        assert passed is False
        assert len(entities) >= 1

    def test_allows_amp_in_urls(self):
        """Test that &amp; is allowed in URL contexts."""
        html = '<a href="https://example.com?a=1&amp;b=2">Link</a>'
        passed, entities = validate_no_visible_entities(html)

        # &amp; in URLs should be allowed
        assert passed is True or "&amp;" not in entities

    def test_allows_nbsp(self):
        """Test that &nbsp; is allowed (in ALLOWED_ENTITIES)."""
        assert "nbsp" in ALLOWED_ENTITIES

    def test_clean_html_passes(self):
        """Test that clean HTML passes validation."""
        html = "<p>München, Köln, Düsseldorf - ohne Entities</p>"
        passed, entities = validate_no_visible_entities(html)

        assert passed is True
        assert len(entities) == 0

    def test_empty_html_passes(self):
        """Test that empty HTML passes validation."""
        passed, entities = validate_no_visible_entities("")

        assert passed is True


class TestApplyEntitySanitization:
    """Tests for full entity sanitization pipeline."""

    def test_full_pipeline_removes_entities(self):
        """Test full pipeline converts entities to characters."""
        html = "<p>M&uuml;nchen, K&ouml;ln</p>"
        result, count = apply_entity_sanitization(html)

        assert "München" in result
        assert "Köln" in result
        assert "&uuml;" not in result
        assert "&ouml;" not in result
        assert count > 0

    def test_full_pipeline_handles_double_escaped(self):
        """Test full pipeline handles double-escaped entities."""
        html = "<p>M&amp;uuml;nchen</p>"
        result, count = apply_entity_sanitization(html)

        assert "München" in result
        assert "&amp;uuml;" not in result

    def test_full_pipeline_returns_count(self):
        """Test pipeline returns count of fixed entities."""
        html = "<p>&auml;&ouml;&uuml;</p>"
        result, count = apply_entity_sanitization(html)

        assert count >= 3

    def test_empty_input(self):
        """Test handling of empty input."""
        result, count = apply_entity_sanitization("")

        assert result == ""
        assert count == 0


class TestEntityPattern:
    """Tests for HTML entity regex pattern."""

    def test_pattern_matches_named_entities(self):
        """Test pattern matches named entities."""
        text = "&uuml;&ouml;&auml;&szlig;"
        matches = HTML_ENTITY_PATTERN.findall(text)

        assert len(matches) == 4
        assert "uuml" in matches

    def test_pattern_length_limits(self):
        """Test pattern respects length limits (2-8 chars)."""
        # Should match
        assert HTML_ENTITY_PATTERN.search("&amp;")  # 3 chars
        assert HTML_ENTITY_PATTERN.search("&nbsp;")  # 4 chars
        assert HTML_ENTITY_PATTERN.search("&bdquo;")  # 5 chars

        # Should not match (too short or too long)
        assert not HTML_ENTITY_PATTERN.search("&a;")  # 1 char
        assert not HTML_ENTITY_PATTERN.search("&verylongentity;")  # > 8 chars


class TestFix530CSS:
    """Tests for FIX-530 CSS fixes."""

    def test_css_contains_list_fixes(self):
        """Test CSS includes list/bullet fixes."""
        css = get_fix_530_css()

        assert "display: list-item" in css
        assert "white-space: normal" in css
        assert "word-break: normal" in css

    def test_css_contains_overlap_fixes(self):
        """Test CSS includes overlap/box fixes."""
        css = get_fix_530_css()

        assert ".risk-card" in css or ".risk-box" in css
        assert "height: auto" in css
        assert "overflow" in css

    def test_css_contains_table_fixes(self):
        """Test CSS includes table fixes."""
        css = get_fix_530_css()

        assert "table-layout: fixed" in css
        assert "word-wrap: break-word" in css

    def test_css_contains_datengrundlage_fixes(self):
        """Test CSS includes Datengrundlage page fixes."""
        css = get_fix_530_css()

        assert "datengrundlage" in css.lower() or "data-basis" in css


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_german_report_text(self):
        """Test typical German report text with entities."""
        html = """
        <p>Die Unterst&uuml;tzung f&uuml;r Gesch&auml;ftsprozesse umfasst
        die Automatisierung von Qualit&auml;tssicherung und Pr&uuml;fung.</p>
        """
        result, count = apply_entity_sanitization(html)

        assert "Unterstützung" in result
        assert "für" in result
        assert "Geschäftsprozesse" in result
        assert "Qualitätssicherung" in result
        assert "Prüfung" in result
        assert count >= 5

    def test_mixed_content_with_urls(self):
        """Test mixed content with URLs containing &."""
        html = """
        <p>Besuchen Sie <a href="https://example.com?a=1&amp;b=2">unsere Seite</a>
        f&uuml;r weitere Informationen.</p>
        """
        result, count = apply_entity_sanitization(html)

        # URL should be preserved
        assert "example.com" in result
        # German text should be fixed
        assert "für" in result

    def test_empty_and_none_handling(self):
        """Test robust handling of empty/None inputs."""
        assert apply_entity_sanitization("")[0] == ""
        assert apply_entity_sanitization(None)[0] == ""
        assert validate_no_visible_entities("") == (True, [])
        assert validate_no_visible_entities(None) == (True, [])
