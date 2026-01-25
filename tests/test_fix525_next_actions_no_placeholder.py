#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-525 Test: NEXT_ACTIONS_HTML No Platzhalter

Validates that NEXT_ACTIONS_HTML content doesn't contain 'Platzhalter'
after the content quality enforcer has processed it.
"""

import re
import pytest


class TestNextActionsNoPlaceholder:
    """Test that NEXT_ACTIONS_HTML doesn't contain Platzhalter after enforcer."""

    def test_placeholder_scrub_removes_platzhalter(self):
        """Test that apply_placeholder_scrub removes Platzhalter from NEXT_ACTIONS_HTML."""
        from services.content_quality_enforcer import apply_placeholder_scrub

        # Simulate input with Platzhalter
        sections = {
            "NEXT_ACTIONS_HTML": """
                <ul>
                    <li><strong>Platzhalter für erste Aktion</strong></li>
                    <li>Konkrete zweite Aktion</li>
                    <li>[Platzhalter: dritte Aktion]</li>
                </ul>
            """,
            "RECOMMENDATIONS_HTML": """
                <p>Some recommendations with Platzhalter text.</p>
            """,
        }

        result = apply_placeholder_scrub(sections)

        # Check NEXT_ACTIONS_HTML has no Platzhalter
        next_actions = result.get("NEXT_ACTIONS_HTML", "")
        assert "platzhalter" not in next_actions.lower(), (
            f"NEXT_ACTIONS_HTML still contains 'Platzhalter' after scrub: {next_actions[:200]}"
        )

        # Check RECOMMENDATIONS_HTML also cleaned
        recommendations = result.get("RECOMMENDATIONS_HTML", "")
        assert "platzhalter" not in recommendations.lower(), (
            f"RECOMMENDATIONS_HTML still contains 'Platzhalter' after scrub"
        )

    def test_placeholder_replaced_with_neutral_text(self):
        """Test that standalone Platzhalter is replaced with neutral text."""
        from services.content_quality_enforcer import apply_placeholder_scrub

        sections = {
            "NEXT_ACTIONS_HTML": """
                <p>Der Platzhalter wird durch konkrete Schritte ersetzt.</p>
            """,
        }

        result = apply_placeholder_scrub(sections)
        next_actions = result.get("NEXT_ACTIONS_HTML", "")

        # Should be replaced with "konkreter Vorschlag"
        assert "konkreter vorschlag" in next_actions.lower() or "platzhalter" not in next_actions.lower(), (
            f"Platzhalter should be replaced or removed: {next_actions}"
        )

    def test_full_pipeline_removes_platzhalter(self):
        """Test that full quality enforcement pipeline removes Platzhalter."""
        from services.content_quality_enforcer import apply_all_quality_enforcers

        sections = {
            "NEXT_ACTIONS_HTML": """
                <section class="next-actions">
                    <h2>Nächste Schritte</h2>
                    <ul>
                        <li>Platzhalter für erste Maßnahme</li>
                        <li>Echte zweite Maßnahme</li>
                    </ul>
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

        next_actions = result.get("NEXT_ACTIONS_HTML", "")
        assert "platzhalter" not in next_actions.lower(), (
            f"NEXT_ACTIONS_HTML still contains 'Platzhalter' after full pipeline"
        )

    def test_template_phrase_patterns_include_platzhalter(self):
        """Test that template phrase patterns include Platzhalter variants."""
        from services.content_quality_enforcer import _TEMPLATE_PHRASE_PATTERNS

        # Check patterns include Platzhalter
        pattern_strs = [p[0].pattern for p in _TEMPLATE_PHRASE_PATTERNS]

        has_platzhalter_pattern = any("platzhalter" in p.lower() for p in pattern_strs)
        assert has_platzhalter_pattern, (
            "Template phrase patterns should include 'Platzhalter' pattern"
        )


class TestNextActionsInScrubSections:
    """Test that NEXT_ACTIONS_HTML is in the template scrub sections list."""

    def test_next_actions_in_template_scrub_sections(self):
        """Verify NEXT_ACTIONS_HTML is in the sections list for template scrubbing."""
        from services.content_quality_enforcer import _TEMPLATE_SCRUB_SECTIONS

        assert "NEXT_ACTIONS_HTML" in _TEMPLATE_SCRUB_SECTIONS, (
            "NEXT_ACTIONS_HTML should be in _TEMPLATE_SCRUB_SECTIONS list"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
