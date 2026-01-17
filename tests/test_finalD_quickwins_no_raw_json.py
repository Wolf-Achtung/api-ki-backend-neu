# -*- coding: utf-8 -*-
"""
Tests for Fix-Batch D - Quick Wins No Raw JSON

Tests:
- Quick Wins never contain raw JSON in output
- EUR values are calculated from hours × canonical_rate
- Compact fallback generated when JSON recovery fails
"""

import os
import pytest
import re

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestQuickWinsNoRawJSON:
    """Test that Quick Wins never output raw JSON."""

    def test_enforce_quickwins_no_raw_json_clean_html(self):
        """Test that clean HTML passes through unchanged."""
        from gpt_analyze import _enforce_quickwins_no_raw_json

        clean_html = '''
        <div class="quick-win-card">
            <h3>E-Mail Automatisierung</h3>
            <p>Zeitersparnis: 10h/Monat = 800 €</p>
        </div>
        '''

        result = _enforce_quickwins_no_raw_json(clean_html, "IT", "team")

        assert "quick-win-card" in result
        assert '"title":' not in result

    def test_enforce_quickwins_no_raw_json_detects_json(self):
        """Test that raw JSON is detected and converted."""
        from gpt_analyze import _enforce_quickwins_no_raw_json

        raw_json = '''
        [{"title": "E-Mail Automatisierung", "icon": "📧", "zeitersparnis": "10h"}]
        '''

        result = _enforce_quickwins_no_raw_json(raw_json, "IT", "team")

        # Should NOT contain raw JSON markers in final output
        assert '"title":' not in result or 'class="quick-win' in result

    def test_enforce_quickwins_no_raw_json_fallback(self):
        """Test that fallback is generated when JSON can't be parsed."""
        from gpt_analyze import _enforce_quickwins_no_raw_json

        broken_json = '''
        {"title": "Test", broken json here
        '''

        result = _enforce_quickwins_no_raw_json(broken_json, "IT", "team")

        # Should produce some HTML output (not raw JSON)
        assert '<div' in result or '<table' in result
        # Should not have raw broken JSON
        assert 'broken json here' not in result or 'class=' in result

    def test_generate_quickwins_compact_fallback(self):
        """Test compact fallback generation from raw JSON."""
        from gpt_analyze import _generate_quickwins_compact_fallback

        raw_json = '''
        [{"title": "Automatisierung"}, {"title": "Dokumentation"}, {"title": "Reporting"}]
        '''

        result = _generate_quickwins_compact_fallback(raw_json, "Beratung", "team")

        # Should extract titles
        assert "Automatisierung" in result
        assert "Dokumentation" in result
        # Should be in table format
        assert "<table" in result


class TestQuickWinsEURCalculation:
    """Test that EUR values are calculated correctly."""

    def test_calculate_quickwin_savings_display_range(self):
        """Test EUR calculation for hour range."""
        from gpt_analyze import _calculate_quickwin_savings_display

        # 15-20h at 80€/h should be 1.200-1.600€
        result = _calculate_quickwin_savings_display("15-20 h/Monat", 80)

        assert "15" in result
        assert "20" in result
        # EUR values should be 1200-1600
        assert "1.200" in result or "1200" in result
        assert "1.600" in result or "1600" in result

    def test_calculate_quickwin_savings_display_single(self):
        """Test EUR calculation for single hour value."""
        from gpt_analyze import _calculate_quickwin_savings_display

        # 10h at 80€/h should produce a range around 800€
        result = _calculate_quickwin_savings_display("10 h/Monat", 80)

        assert "€" in result
        # Should have some EUR value

    def test_calculate_quickwin_savings_strips_llm_eur(self):
        """Test that existing LLM EUR values are stripped."""
        from gpt_analyze import _calculate_quickwin_savings_display

        # LLM might produce wrong EUR values - these should be replaced
        result = _calculate_quickwin_savings_display("15-20h = 400-800€", 80)

        # Should recalculate to correct values
        # 15-20h at 80€/h = 1.200-1.600€, not 400-800€
        assert "400" not in result or "1.200" in result

    def test_calculate_quickwin_savings_empty(self):
        """Test fallback for empty input."""
        from gpt_analyze import _calculate_quickwin_savings_display

        result = _calculate_quickwin_savings_display("", 80)

        assert "auf Anfrage" in result


class TestQuickWinsCompactFallback:
    """Test compact fallback generation."""

    def test_compact_fallback_extracts_titles(self):
        """Test that compact fallback extracts title content."""
        from gpt_analyze import _generate_quickwins_compact_fallback

        content = '''
        {"title": "Process Automation", "description": "Automate workflows"}
        {"title": "Data Analysis", "description": "Analyze data"}
        '''

        result = _generate_quickwins_compact_fallback(content, "IT", "team")

        assert "Process Automation" in result or "Data Analysis" in result

    def test_compact_fallback_max_3_items(self):
        """Test that compact fallback limits to 3 items."""
        from gpt_analyze import _generate_quickwins_compact_fallback

        content = '''
        {"title": "Item 1"}, {"title": "Item 2"}, {"title": "Item 3"},
        {"title": "Item 4"}, {"title": "Item 5"}
        '''

        result = _generate_quickwins_compact_fallback(content, "IT", "team")

        # Count table rows
        row_count = result.count('<tr')
        # Should have max 4 rows (1 header implied + 3 data)
        assert row_count <= 4


class TestBatchDIntegration:
    """Integration tests for Fix-Batch D."""

    def test_full_pipeline_no_json_leak(self):
        """Test that the full Quick Wins pipeline never leaks JSON."""
        from gpt_analyze import (
            _enforce_quickwins_no_raw_json,
            _build_quick_wins_html,
            _parse_quick_wins_json,
        )

        # Simulate various inputs
        test_cases = [
            # Clean JSON
            '[{"title": "Test", "icon": "📧", "time": "1h", "engpass": "x", "description": "y", "mit_ki": "z", "steps": ["a"], "zeitersparnis": "5h"}]',
            # Broken JSON
            '{"title": incomplete',
            # Mixed content
            '<div>Some HTML</div> {"title": "Mixed"}',
            # Empty
            '',
        ]

        for test_input in test_cases:
            result = _enforce_quickwins_no_raw_json(test_input, "IT", "team")

            # Key assertion: No raw JSON should appear in output
            # (unless it's inside properly rendered HTML)
            if result and '"title":' in result:
                # If JSON markers exist, they must be inside HTML structure
                assert 'class="' in result, f"Raw JSON leaked: {result[:200]}"

    def test_build_quick_wins_html_always_produces_cards(self):
        """Test that _build_quick_wins_html always produces proper cards."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [
            {
                "title": "Test Win",
                "icon": "📧",
                "time": "2h",
                "engpass": "Problem",
                "description": "Current state",
                "mit_ki": "With AI",
                "steps": ["Step 1"],
                "zeitersparnis": "10h/Monat",
            }
        ]

        result = _build_quick_wins_html(quick_wins, "IT", "team")

        # Must produce card HTML
        assert "quick-win-card" in result
        # Must contain title
        assert "Test Win" in result
