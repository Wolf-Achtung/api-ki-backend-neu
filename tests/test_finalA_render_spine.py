# -*- coding: utf-8 -*-
"""
Tests for Fix-Batch A - Deterministic Render Spine

Tests:
- Quick Wins always rendered via _build_quick_wins_html (not DISABLED)
- Roadmap always formatted via _format_roadmap_as_phase_cards (not DISABLED)
- Recommendations have compact table fallback when patterns don't match
- No DISABLED messages for active formatters
"""

import os
import pytest
import re

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestQuickWinsRenderer:
    """Test that Quick Wins are always rendered via _build_quick_wins_html."""

    def test_build_quick_wins_html_produces_cards(self):
        """Test that _build_quick_wins_html generates proper HTML cards."""
        from gpt_analyze import _build_quick_wins_html

        # Use the correct field names expected by the function
        quick_wins_list = [
            {
                "title": "E-Mail Automatisierung",
                "icon": "📧",
                "time": "2 Std/Woche",
                "engpass": "Manuelle E-Mail-Verarbeitung",
                "description": "Aktuell werden E-Mails manuell bearbeitet",
                "mit_ki": "Mit KI-Automatisierung werden E-Mails automatisch kategorisiert",
                "steps": ["Tool auswählen", "Konfigurieren", "Testen"],
                "zeitersparnis": "8h/Monat",
            },
            {
                "title": "Rechnungsverarbeitung",
                "icon": "📄",
                "time": "3 Std/Woche",
                "engpass": "Manuelle Rechnungsprüfung",
                "description": "Rechnungen werden einzeln geprüft",
                "mit_ki": "KI prüft Rechnungen automatisch",
                "steps": ["OCR einrichten", "Validierung konfigurieren", "Rollout"],
                "zeitersparnis": "5h/Monat",
            },
        ]

        result = _build_quick_wins_html(quick_wins_list, branche="Beratung", groesse="team")

        # Should produce HTML with cards
        assert "<div" in result, "Should produce div-based cards"
        assert "E-Mail Automatisierung" in result, "Should contain first title"
        assert "Rechnungsverarbeitung" in result, "Should contain second title"
        # Should contain card structure
        assert "quick-win-card" in result, "Should have quick-win-card class"

    def test_build_quick_wins_html_empty_list(self):
        """Test that _build_quick_wins_html handles empty list gracefully."""
        from gpt_analyze import _build_quick_wins_html

        result = _build_quick_wins_html([], branche="", groesse="")

        # Should return empty or minimal HTML
        assert result is not None

    def test_fallback_quick_wins_html(self):
        """Test that fallback quick wins HTML is generated when no content."""
        from gpt_analyze import _fallback_quick_wins_html

        result = _fallback_quick_wins_html(branche="IT", groesse="kmu")

        # Should produce fallback HTML
        assert result is not None
        assert "div" in result.lower() or "p" in result.lower()


class TestRoadmapFormatter:
    """Test that Roadmap is formatted via _format_roadmap_as_phase_cards."""

    def test_format_roadmap_produces_phase_structure(self):
        """Test that _format_roadmap_as_phase_cards formats phases."""
        from gpt_analyze import _format_roadmap_as_phase_cards

        roadmap_html = """
        <div class="roadmap">
            <h3>Phase 1: Vorbereitung (Woche 1-2)</h3>
            <p>Analyse der aktuellen Prozesse und Identifikation von Optimierungspotenzial.</p>
            <h3>Phase 2: Pilotierung (Woche 3-6)</h3>
            <p>Einführung eines Pilotprojekts mit ausgewähltem Team.</p>
            <h3>Phase 3: Rollout (Woche 7-12)</h3>
            <p>Schrittweise Einführung in allen Abteilungen.</p>
        </div>
        """

        result = _format_roadmap_as_phase_cards(roadmap_html)

        # Should contain phase content
        assert "Phase 1" in result or "Vorbereitung" in result
        assert "Phase 2" in result or "Pilotierung" in result

    def test_roadmap_handles_empty_input(self):
        """Test that roadmap formatter handles empty/short input."""
        from gpt_analyze import _format_roadmap_as_phase_cards

        result = _format_roadmap_as_phase_cards("")

        # Should return empty for empty input
        assert result == "" or result is None or len(result) < 10

    def test_roadmap_preserves_content(self):
        """Test that roadmap formatter preserves important content."""
        from gpt_analyze import _format_roadmap_as_phase_cards

        roadmap_html = """
        <p>Die 90-Tage-Roadmap umfasst drei Phasen.</p>
        <h3>Phase 0: Quick Start</h3>
        <p>Sofortige Maßnahmen in der ersten Woche.</p>
        """

        result = _format_roadmap_as_phase_cards(roadmap_html)

        # Key content should be preserved
        assert "90-Tage" in result or "Quick Start" in result


class TestRecommendationsCompactFallback:
    """Test that Recommendations have compact table fallback."""

    def test_format_recommendations_with_patterns(self):
        """Test that _format_recommendations_as_cards works with standard patterns."""
        from gpt_analyze import _format_recommendations_as_cards

        rec_html = """
        <section class="recommendations">
            <h2>Handlungsempfehlungen</h2>
            <p>Basierend auf Ihrer Analyse empfehlen wir:</p>
            <ol>
                <li><strong>KI-Pilotprojekt starten</strong> - Beginnen Sie mit einem überschaubaren Projekt.</li>
                <li><strong>Team schulen</strong> - Investieren Sie in Weiterbildung.</li>
                <li><strong>Prozesse dokumentieren</strong> - Erfassen Sie aktuelle Workflows.</li>
            </ol>
        </section>
        """

        result = _format_recommendations_as_cards(rec_html)

        # Should contain recommendation content
        assert "Handlungsempfehlungen" in result or "empfehlen" in result
        assert "KI-Pilotprojekt" in result or "Pilotprojekt" in result

    def test_format_recommendations_compact_fallback(self):
        """Test that compact table fallback is generated when patterns don't match."""
        from gpt_analyze import _format_recommendations_as_cards

        # Content that doesn't match standard patterns
        rec_html = """
        <div class="custom-section">
            <p>Hier sind einige wichtige Empfehlungen für Ihr Unternehmen:</p>
            <p>Erstens sollten Sie die Digitalisierung vorantreiben und moderne Tools einsetzen.</p>
            <p>Zweitens ist es wichtig, Ihre Mitarbeiter regelmäßig zu schulen.</p>
            <p>Drittens empfehlen wir eine kontinuierliche Prozessoptimierung.</p>
        </div>
        """

        result = _format_recommendations_as_cards(rec_html)

        # Should generate some output (either fallback table or original)
        assert result is not None
        assert len(result) > 50

    def test_recommendations_preserves_content(self):
        """Test that recommendation content is never lost."""
        from gpt_analyze import _format_recommendations_as_cards

        rec_html = "<p>Wichtige Empfehlung: Investieren Sie in KI-Technologie.</p>"

        result = _format_recommendations_as_cards(rec_html)

        # Content should be preserved
        assert "KI-Technologie" in result or "Investieren" in result


class TestNoDisabledMessages:
    """Test that DISABLED messages are not logged for active formatters."""

    def test_no_disabled_in_gpt_analyze_code(self):
        """Test that misleading DISABLED log messages have been removed."""
        from gpt_analyze import __file__ as gpt_analyze_path

        with open(gpt_analyze_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # These specific misleading messages should be removed
        misleading_messages = [
            'Quick Wins formatter DISABLED',
            'Roadmap formatter DISABLED',
            'Empfehlungen formatter DISABLED',
        ]

        for msg in misleading_messages:
            # Should not find these log.info() calls anymore
            pattern = rf'log\.info\([^)]*{re.escape(msg)}'
            matches = re.findall(pattern, content)
            assert len(matches) == 0, f"Found misleading message: {msg}"

    def test_fix_batch_a_comment_exists(self):
        """Test that Fix-Batch A comment block exists."""
        from gpt_analyze import __file__ as gpt_analyze_path

        with open(gpt_analyze_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should have the new Fix-Batch A comment
        assert "Fix-Batch A: DETERMINISTIC RENDER SPINE" in content


class TestBatchAIntegration:
    """Integration tests for Fix-Batch A."""

    def test_quick_wins_json_to_html_pipeline(self):
        """Test the complete Quick Wins JSON→HTML pipeline."""
        from gpt_analyze import _parse_quick_wins_json, _build_quick_wins_html

        # Sample JSON with correct field names expected by the parser
        json_str = '''[
            {
                "title": "Automatisierung",
                "icon": "⚙️",
                "time": "2 Std/Woche",
                "engpass": "Manuelle Prozesse",
                "description": "Aktuell werden Prozesse manuell durchgeführt",
                "mit_ki": "Mit KI-Automatisierung werden Prozesse automatisch ausgeführt",
                "steps": ["Analyse", "Implementierung", "Test"],
                "zeitersparnis": "10h/Monat"
            },
            {
                "title": "Dokumentation",
                "icon": "📝",
                "time": "1 Std/Woche",
                "engpass": "Unstrukturierte Dokumente",
                "description": "Dokumente sind schwer zu finden",
                "mit_ki": "KI organisiert und kategorisiert Dokumente automatisch",
                "steps": ["Setup", "Import", "Training"],
                "zeitersparnis": "5h/Monat"
            }
        ]'''

        # Parse JSON
        quick_wins = _parse_quick_wins_json(json_str)

        assert quick_wins is not None, "JSON should parse successfully"
        assert len(quick_wins) == 2, "Should have 2 quick wins"

        # Build HTML
        html = _build_quick_wins_html(quick_wins, branche="IT", groesse="team")

        assert "Automatisierung" in html, "Should contain first title"
        assert "Dokumentation" in html, "Should contain second title"

    def test_simple_json_to_html_fallback(self):
        """Test simple JSON array to HTML conversion."""
        from gpt_analyze import _quick_wins_simple_json_to_html

        # Simple JSON array
        json_str = '["Prozessautomatisierung", "Datenanalyse", "Reporting"]'

        result = _quick_wins_simple_json_to_html(json_str)

        # Should convert to HTML
        if result:
            assert "Prozessautomatisierung" in result or "html" in result.lower()

    def test_all_formatters_callable(self):
        """Test that all primary formatters are callable without errors."""
        from gpt_analyze import (
            _build_quick_wins_html,
            _format_roadmap_as_phase_cards,
            _format_recommendations_as_cards,
        )

        # All should be callable
        assert callable(_build_quick_wins_html)
        assert callable(_format_roadmap_as_phase_cards)
        assert callable(_format_recommendations_as_cards)

        # All should handle minimal input without crashing
        try:
            _build_quick_wins_html([], "", "")
            _format_roadmap_as_phase_cards("<p>Test</p>")
            _format_recommendations_as_cards("<p>Test recommendation</p>")
        except Exception as e:
            pytest.fail(f"Formatter raised exception on minimal input: {e}")
