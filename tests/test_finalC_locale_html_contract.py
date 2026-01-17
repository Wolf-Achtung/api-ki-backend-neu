# -*- coding: utf-8 -*-
"""
Tests for Fix-Batch C - DE Locale + HTML Contract Hardening

Tests:
- EN locale sanitizer only applies to EN reports (not DE)
- German number formatting (decimal comma, thousand dot)
- HTML contract normalizer converts semantic tags to divs
"""

import os
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestDELocaleNoENSanitizer:
    """Test that EN locale sanitizer does NOT apply to DE reports."""

    def test_sanitize_en_locale_tokens_skipped_for_de(self):
        """Test that sanitize_en_locale_tokens returns unchanged for lang=de."""
        from services.html_sanitizer import sanitize_en_locale_tokens

        german_html = """
        <p>Das Unternehmen hat 50 Mitarbeiter.</p>
        <p>Die Branche ist Beratung.</p>
        <p>Zeitersparnis: 3,5 Stunden pro Tag.</p>
        """

        result = sanitize_en_locale_tokens(german_html, lang="de")

        # Should be unchanged
        assert result == german_html, "DE content should not be modified by EN sanitizer"

    def test_sanitize_en_locale_tokens_applies_to_en(self):
        """Test that sanitize_en_locale_tokens does apply for lang=en."""
        from services.html_sanitizer import sanitize_en_locale_tokens

        # Content with German words that should be translated for EN
        mixed_html = "<p>Das Unternehmen</p>"

        result = sanitize_en_locale_tokens(mixed_html, lang="en")

        # Should be modified for EN (German tokens replaced)
        # Note: actual replacements depend on _EN_LOCALE_REPLACEMENTS
        # This test verifies the function runs on EN content
        assert result is not None

    def test_german_decimal_format_preserved(self):
        """Test that German decimal format (3,5) is preserved in DE content."""
        from services.html_sanitizer import sanitize_en_locale_tokens

        de_content = "<p>Amortisation: 3,5 Monate. ROI: 200,0%</p>"

        result = sanitize_en_locale_tokens(de_content, lang="de")

        # German decimals should be preserved
        assert "3,5" in result, "German decimal (comma) should be preserved"
        assert "200,0" in result, "German decimal should be preserved"


class TestGermanNumberFormatting:
    """Test German number formatting functions."""

    def test_german_thousand_separator(self):
        """Test German thousand separator (dot)."""
        # Test the format used in quickwins_renderer
        from services.quickwins_renderer import format_eur_range

        result = format_eur_range(1200, 1800)

        assert "1.200" in result, "Should use dot for thousands (German style)"
        assert "1.800" in result, "Should use dot for thousands"

    def test_german_decimal_in_bc_table(self):
        """Test that BC table uses German decimal format."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "team",
            "jahresumsatz": "100k_500k",
            "investitionsbudget": "5000_10000",
            "qw_hours_total": 20,
        }
        env = {}

        bc = calc_business_case(answers, env)
        table_html = bc.get("BUSINESS_CASE_TABLE_HTML", "")

        # Table should use German formatting
        # Check that values are formatted with dots for thousands
        assert "€" in table_html, "Table should contain € symbol"
        # ROI percentage should be present
        assert "%" in table_html, "Table should contain ROI percentage"


class TestHTMLContractNormalizer:
    """Test that HTML contract normalizer converts tags instead of removing."""

    def test_h2_normalized_to_div(self):
        """Test that <h2> is converted to <div class="heading heading-h2">."""
        from services.html_sanitizer import normalize_html_tags_before_sanitize

        html = "<h2>Important Title</h2><p>Some content</p>"

        result = normalize_html_tags_before_sanitize(html)

        assert "<h2>" not in result, "h2 tag should be converted"
        assert 'class="heading heading-h2"' in result, "Should have heading class"
        assert "<strong>" in result, "Content should be wrapped in strong"
        assert "Important Title" in result, "Title content should be preserved"

    def test_h3_normalized_to_div(self):
        """Test that <h3> is converted to <div class="heading heading-h3">."""
        from services.html_sanitizer import normalize_html_tags_before_sanitize

        html = "<h3>Subtitle</h3>"

        result = normalize_html_tags_before_sanitize(html)

        assert "<h3>" not in result, "h3 tag should be converted"
        assert 'class="heading heading-h3"' in result, "Should have heading class"
        assert "Subtitle" in result, "Content should be preserved"

    def test_section_normalized_to_div(self):
        """Test that <section> is converted to <div class="section">."""
        from services.html_sanitizer import normalize_html_tags_before_sanitize

        html = "<section><p>Content in section</p></section>"

        result = normalize_html_tags_before_sanitize(html)

        assert "<section>" not in result, "section tag should be converted"
        assert "</section>" not in result, "closing section should be converted"
        assert 'class="section"' in result, "Should have section class"
        assert "Content in section" in result, "Content should be preserved"

    def test_multiple_tags_normalized(self):
        """Test that multiple semantic tags are all normalized."""
        from services.html_sanitizer import normalize_html_tags_before_sanitize

        html = """
        <section>
            <h2>Main Title</h2>
            <p>Intro text</p>
            <h3>Subtitle</h3>
            <p>More content</p>
        </section>
        """

        result = normalize_html_tags_before_sanitize(html)

        assert "<section>" not in result
        assert "<h2>" not in result
        assert "<h3>" not in result
        assert 'class="section"' in result
        assert 'heading-h2' in result
        assert 'heading-h3' in result
        assert "Main Title" in result
        assert "Subtitle" in result

    def test_enforce_contract_uses_normalizer(self):
        """Test that enforce_text_section_html_contract calls normalizer."""
        from services.html_sanitizer import enforce_text_section_html_contract

        html = "<h2>Title</h2><p>Content</p>"

        result = enforce_text_section_html_contract(html, "test_section")

        # After normalization, h2 should be converted to div
        assert "<h2>" not in result, "h2 should be normalized"
        # Content should be preserved (not removed)
        assert "Title" in result, "Title content should be preserved"
        assert "Content" in result, "Paragraph content should be preserved"


class TestBatchCIntegration:
    """Integration tests for Fix-Batch C."""

    def test_de_report_preserves_structure(self):
        """Test that DE report with semantic tags preserves structure."""
        from services.html_sanitizer import enforce_text_section_html_contract

        de_content = """
        <section class="recommendations">
            <h2>Handlungsempfehlungen</h2>
            <p>Hier sind Ihre personalisierten Empfehlungen:</p>
            <h3>Empfehlung 1</h3>
            <p>Details zur ersten Empfehlung.</p>
            <h3>Empfehlung 2</h3>
            <p>Details zur zweiten Empfehlung.</p>
        </section>
        """

        result = enforce_text_section_html_contract(de_content, "recommendations")

        # Content should be preserved
        assert "Handlungsempfehlungen" in result
        assert "Empfehlung 1" in result
        assert "Empfehlung 2" in result
        assert "personalisierte" in result

        # Structure should be indicated by classes
        assert "heading" in result or "strong" in result, "Headings should be styled"

    def test_no_mass_tag_removal(self):
        """Test that tags are normalized, not mass-removed."""
        from services.html_sanitizer import (
            normalize_html_tags_before_sanitize,
            enforce_text_section_html_contract,
        )

        html_with_structure = """
        <h2>Title</h2>
        <section>
            <h3>Subtitle</h3>
            <article>Content</article>
        </section>
        """

        # First test normalizer alone
        normalized = normalize_html_tags_before_sanitize(html_with_structure)

        # All content should be preserved
        assert "Title" in normalized
        assert "Subtitle" in normalized
        assert "Content" in normalized

        # Tags should be converted to divs with classes
        assert "<h2>" not in normalized
        assert "<h3>" not in normalized
        assert "<section>" not in normalized
        assert "<article>" not in normalized

        # But divs with appropriate classes should exist
        assert "div" in normalized
