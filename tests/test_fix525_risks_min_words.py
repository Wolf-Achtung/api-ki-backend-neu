#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-525 Test: Risks Section Minimum Words for Solo

Validates that RISKS_HTML has at least 500 words for solo persona
after the content quality enforcer has processed it.
"""

import re
import pytest


def count_words(html: str) -> int:
    """Count words in HTML content (strip tags first)."""
    text = re.sub(r'<[^>]+>', ' ', html)
    return len(text.split())


class TestRisksSoloMinimumWords:
    """Test that RISKS_HTML meets minimum word count for solo persona."""

    def test_risks_padding_applied_when_too_short(self):
        """Test that padding is applied when RISKS_HTML is too short for solo."""
        from services.content_quality_enforcer import apply_risks_solo_padding

        # Create a short risks section (less than 500 words)
        short_risks = """
            <section class="risks">
                <h2>Risiken</h2>
                <ul>
                    <li>Datenschutzrisiko: DSGVO-Konformität sicherstellen.</li>
                    <li>Qualitätsrisiko: KI-Ausgaben regelmäßig prüfen.</li>
                    <li>Abhängigkeitsrisiko: Backup-Prozesse definieren.</li>
                </ul>
            </section>
        """

        sections = {"RISKS_HTML": short_risks}
        initial_words = count_words(short_risks)
        assert initial_words < 500, f"Test setup error: initial words ({initial_words}) should be < 500"

        result = apply_risks_solo_padding(sections, "solo")

        final_html = result.get("RISKS_HTML", "")
        final_words = count_words(final_html)

        assert final_words >= 500, (
            f"RISKS_HTML should have >= 500 words for solo after padding. "
            f"Initial: {initial_words}, Final: {final_words}"
        )

    def test_risks_padding_not_applied_when_sufficient(self):
        """Test that padding is NOT applied when RISKS_HTML already has enough words."""
        from services.content_quality_enforcer import apply_risks_solo_padding

        # Create a long risks section (more than 500 words)
        long_risks = "<section class='risks'><h2>Risiken</h2><p>" + " ".join(["Risiko"] * 600) + "</p></section>"

        sections = {"RISKS_HTML": long_risks}
        initial_words = count_words(long_risks)
        assert initial_words >= 500, f"Test setup error: initial words ({initial_words}) should be >= 500"

        result = apply_risks_solo_padding(sections, "solo")

        final_html = result.get("RISKS_HTML", "")
        final_words = count_words(final_html)

        # Should be approximately the same (no padding added)
        assert abs(final_words - initial_words) < 10, (
            f"RISKS_HTML should not be padded when already sufficient. "
            f"Initial: {initial_words}, Final: {final_words}"
        )

    def test_risks_padding_not_applied_for_team(self):
        """Test that padding is NOT applied for team persona."""
        from services.content_quality_enforcer import apply_risks_solo_padding

        short_risks = "<p>Short risks content.</p>"
        sections = {"RISKS_HTML": short_risks}
        initial_words = count_words(short_risks)

        result = apply_risks_solo_padding(sections, "team")

        final_html = result.get("RISKS_HTML", "")
        final_words = count_words(final_html)

        assert final_words == initial_words, (
            f"RISKS_HTML should not be padded for team persona. "
            f"Initial: {initial_words}, Final: {final_words}"
        )

    def test_risks_padding_not_applied_for_kmu(self):
        """Test that padding is NOT applied for kmu persona."""
        from services.content_quality_enforcer import apply_risks_solo_padding

        short_risks = "<p>Short risks content.</p>"
        sections = {"RISKS_HTML": short_risks}
        initial_words = count_words(short_risks)

        result = apply_risks_solo_padding(sections, "kmu")

        final_html = result.get("RISKS_HTML", "")
        final_words = count_words(final_html)

        assert final_words == initial_words, (
            f"RISKS_HTML should not be padded for kmu persona. "
            f"Initial: {initial_words}, Final: {final_words}"
        )

    def test_full_pipeline_ensures_risks_minimum(self):
        """Test that full quality enforcement ensures risks minimum for solo."""
        from services.content_quality_enforcer import apply_all_quality_enforcers

        sections = {
            "RISKS_HTML": """
                <section class="risks">
                    <h2>Risiken</h2>
                    <p>Kurze Risikobewertung für Solo.</p>
                </section>
            """,
            "EXECUTIVE_SUMMARY_HTML": "<p>Summary</p>",
        }

        result = apply_all_quality_enforcers(
            sections=sections,
            hauptleistung="KI-Beratung",
            bundesland="Bayern",
            company_size="solo"
        )

        risks_html = result.get("RISKS_HTML", "")
        word_count = count_words(risks_html)

        assert word_count >= 500, (
            f"RISKS_HTML should have >= 500 words for solo after full pipeline. "
            f"Actual: {word_count} words"
        )


class TestRisksPaddingContent:
    """Test the content quality of risks padding."""

    def test_padding_contains_no_forbidden_tokens(self):
        """Test that padding content has no forbidden tokens."""
        from services.content_quality_enforcer import _RISKS_SOLO_PADDING_HTML

        forbidden_patterns = [
            r'\brollout\b',
            r'\bskalierung\b',
            r'\bstack\b',
            r'\bmodul\b',
            r'\bstakeholder\b',
        ]

        padding_lower = _RISKS_SOLO_PADDING_HTML.lower()

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, padding_lower, re.IGNORECASE)
            assert len(matches) == 0, (
                f"Risks padding contains forbidden token '{pattern}'"
            )

    def test_padding_is_valid_html(self):
        """Test that padding content is valid HTML structure."""
        from services.content_quality_enforcer import _RISKS_SOLO_PADDING_HTML

        # Should have opening and closing div
        assert "<div" in _RISKS_SOLO_PADDING_HTML, "Padding should have div container"
        assert "</div>" in _RISKS_SOLO_PADDING_HTML, "Padding should have closing div"

        # Should have list items
        assert "<li>" in _RISKS_SOLO_PADDING_HTML, "Padding should have list items"
        assert "</li>" in _RISKS_SOLO_PADDING_HTML, "Padding should have closing list items"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
