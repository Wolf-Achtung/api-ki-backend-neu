# -*- coding: utf-8 -*-
"""
Unit test for Roadmap Phase Cards regex transformation.

Regression test for the "no such group" error that occurred when
phase_pattern_h4 (3 groups) used replace_phase_h3 (expected 4 groups).
"""
import pytest


class TestRoadmapPhaseCardsRegex:
    """Tests for _format_roadmap_as_phase_cards function."""

    def test_h4_pattern_does_not_raise_no_such_group(self):
        """
        Regression test: h4 pattern with 3 groups must not raise 'no such group'.

        The h4 pattern has only 3 capture groups, but the replacement function
        previously accessed group(4), causing: re.error: no such group
        """
        from gpt_analyze import _format_roadmap_as_phase_cards

        # Sample HTML using h4 format (the problematic pattern)
        sample_html = """
        <div class="roadmap-content">
            <h4>Phase 1: Grundlagen</h4>
            <p>Aufbau der KI-Infrastruktur</p>
            <ul>
                <li>Datenbankanbindung</li>
                <li>API-Integration</li>
            </ul>
            <h4>Phase 2: Pilotprojekt</h4>
            <p>Erste Implementierung</p>
            <ul>
                <li>Prototyp entwickeln</li>
                <li>Testing durchführen</li>
            </ul>
        </div>
        """

        # Must not raise any exception
        result = _format_roadmap_as_phase_cards(sample_html)

        # Basic assertions
        assert result is not None, "Result should not be None"
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"

    def test_h3_pattern_creates_phase_cards(self):
        """Test that h3 pattern successfully creates phase cards."""
        from gpt_analyze import _format_roadmap_as_phase_cards

        sample_html = """
        <div class="roadmap">
            <h3>Phase 1: Initialisierung</h3>
            <p><strong>Ziel:</strong> Grundstein legen</p>
            <ul>
                <li>Team aufbauen</li>
                <li>Ressourcen sichern</li>
            </ul>
            <p>Meilenstein: Kick-off Meeting</p>
        </div>
        """

        result = _format_roadmap_as_phase_cards(sample_html)

        assert result is not None
        assert "roadmap-phase-card" in result, "Should contain phase-card class"
        assert "phase-badge" in result, "Should contain phase badge"

    def test_short_content_returns_unchanged(self):
        """Test that content shorter than 200 chars is returned unchanged."""
        from gpt_analyze import _format_roadmap_as_phase_cards

        short_html = "<p>Too short</p>"
        result = _format_roadmap_as_phase_cards(short_html)

        assert result == short_html, "Short content should be returned unchanged"

    def test_empty_content_returns_unchanged(self):
        """Test that empty/None content is handled gracefully."""
        from gpt_analyze import _format_roadmap_as_phase_cards

        assert _format_roadmap_as_phase_cards("") == ""
        assert _format_roadmap_as_phase_cards(None) is None
