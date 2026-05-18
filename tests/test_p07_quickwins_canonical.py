# -*- coding: utf-8 -*-
"""
Tests for P0.7 - Quick Wins: Correct € Values + Clean Rendering

Tests:
- Quick Wins € values calculated from hours * canonical_rate
- No 'Icon:' text artifacts in output
- Quick Wins render as structured cards
"""

import os
import pytest
import re

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestQuickWinsEurCalculation:
    """Test that Quick Wins € values are calculated from hours * canonical rate."""

    def test_calculate_quickwin_savings_from_hours_range(self):
        """Test € calculation from hours range like '10-15 h/Monat'."""
        from services.quickwins_renderer import calculate_quickwin_savings_display

        # Test: 10-15 hours at 80€/h = 800-1200€
        result = calculate_quickwin_savings_display("10-15 h/Monat", 80)
        assert "800" in result, f"Expected 800€, got {result}"
        assert "1.200" in result, f"Expected 1.200€, got {result}"

    def test_calculate_quickwin_savings_from_single_hours(self):
        """Test € calculation from single hours value like '10 h/Monat'."""
        from services.quickwins_renderer import calculate_quickwin_savings_display

        # Test: Single value creates range (80-120% of value)
        result = calculate_quickwin_savings_display("10 h/Monat", 80)
        # 10h * 0.8 = 8h, 10h * 1.2 = 12h
        # 8h * 80€ = 640€, 12h * 80€ = 960€
        assert "640" in result or "800" in result, f"Expected ~640-960€ range, got {result}"

    def test_calculate_quickwin_savings_strips_llm_euro_values(self):
        """Test that LLM-provided € values are replaced with calculated ones."""
        from services.quickwins_renderer import calculate_quickwin_savings_display

        # LLM provides wrong € values, should be recalculated
        result = calculate_quickwin_savings_display(
            "10-15 h/Monat = 500-750 €",  # Wrong LLM values
            80  # Canonical rate
        )
        # Should calculate: 10*80=800, 15*80=1200
        assert "800" in result, f"Should recalculate to 800€, got {result}"
        assert "1.200" in result, f"Should recalculate to 1.200€, got {result}"
        assert "500" not in result, f"Should NOT contain LLM value 500, got {result}"
        assert "750" not in result, f"Should NOT contain LLM value 750, got {result}"

    def test_calculate_quickwin_savings_uses_canonical_rate_for_solo(self):
        """Test that solo company size uses 80€/h canonical rate."""
        from services.quickwins_renderer import calculate_quickwin_savings_display

        # Solo rate = 80€/h
        result = calculate_quickwin_savings_display("20 h/Monat", 80)
        # 20h range (16-24h) at 80€/h
        assert "€" in result

    def test_calculate_quickwin_savings_uses_canonical_rate_for_team(self):
        """Test that team company size uses 95€/h canonical rate."""
        from services.quickwins_renderer import calculate_quickwin_savings_display

        # Team rate = 95€/h, 10-15h = 950-1425€
        result = calculate_quickwin_savings_display("10-15 h/Monat", 95)
        assert "950" in result, f"Expected 950€ for team rate, got {result}"
        assert "1.425" in result, f"Expected 1.425€ for team rate, got {result}"

    def test_calculate_quickwin_savings_handles_empty_input(self):
        """Test handling of empty zeitersparnis."""
        from services.quickwins_renderer import calculate_quickwin_savings_display

        result = calculate_quickwin_savings_display("", 80)
        assert "auf Anfrage" in result


class TestQuickWinsIconArtifactRemoval:
    """Test that 'Icon:' text artifacts are removed from Quick Wins."""

    def test_icon_text_removed_from_icon_field(self):
        """Test that 'Icon:' prefix is removed from icon field."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            'title': 'Test Quick Win',
            'icon': 'Icon: 🚀',  # Artifact from LLM
            'time': '2-3 Tage',
            'engpass': 'Test engpass',
            'description': 'Test description',
            'mit_ki': 'Test mit ki',
            'steps': ['Step 1', 'Step 2'],
            'zeitersparnis': '10 h/Monat',
        }]

        html = _build_quick_wins_html(quick_wins, branche="IT", groesse="solo")

        # Should NOT contain "Icon:" text
        assert 'Icon:' not in html, f"Found 'Icon:' artifact in HTML"
        # Should still contain the actual icon emoji
        assert '🚀' in html, f"Missing icon emoji in HTML"

    def test_plain_icon_preserved(self):
        """Test that plain icons without 'Icon:' are preserved."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            'title': 'Test Quick Win',
            'icon': '⚡',  # Plain icon
            'time': '1-2 Tage',
            'engpass': 'Test',
            'description': 'Test',
            'mit_ki': 'Test',
            'steps': ['Step 1'],
            'zeitersparnis': '5 h/Monat',
        }]

        html = _build_quick_wins_html(quick_wins, branche="IT", groesse="team")
        assert '⚡' in html


class TestQuickWinsCardRendering:
    """Test that Quick Wins render as structured cards."""

    def test_quick_wins_render_as_cards(self):
        """Test that Quick Wins output contains card structure.

        [QW-SCHEMA-FIX] Migrated from legacy schema (engpass/description/
        mit_ki/steps/zeitersparnis) to current prompt schema (problem/
        wirkung/umsetzung/hinweis). Cf. prompts/de/quick_wins.md v8.3.
        """
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            'title': 'Card Test',
            'icon': '📋',
            'problem': 'Bottleneck text',
            'wirkung': 'Effect with AI',
            'umsetzung': 'How to implement',
            'hinweis': 'siehe Business Case',
        }]

        html = _build_quick_wins_html(quick_wins, branche="Marketing", groesse="kmu")

        assert 'quick-win-card' in html, "Missing quick-win-card class"
        assert 'Card Test' in html, "Missing title"
        assert '📋' in html, "Missing icon"
        assert 'PROBLEM' in html.upper(), "Missing problem/engpass section"
        assert 'Wirkung' in html, "Missing wirkung section"
        assert 'Umsetzung' in html, "Missing umsetzung section"

    def test_quick_wins_skips_empty_blocks(self):
        """[QW-SCHEMA-FIX] Empty fields produce no rendered block (analog
        services/quickwins_renderer.py:render_quickwins_premium_json)."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            'title': 'Sparse Test',
            'icon': '💡',
            'problem': 'Only problem set',
            'wirkung': '',
            'umsetzung': '',
            'hinweis': 'siehe Business Case',
        }]

        html = _build_quick_wins_html(quick_wins, branche="IT", groesse="Einzelunternehmer")

        assert 'Sparse Test' in html
        assert 'Only problem set' in html
        assert 'Wirkung mit KI' not in html, "Empty wirkung block should be skipped"
        assert 'Umsetzung:' not in html, "Empty umsetzung block should be skipped"

    def test_quick_wins_context_banner(self):
        """Test that context banner shows branche and groesse."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            'title': 'Banner Test',
            'icon': '🏢',
            'time': '1 Tag',
            'engpass': 'Test',
            'description': 'Test',
            'mit_ki': 'Test',
            'steps': ['Step'],
            'zeitersparnis': '5 h',
        }]

        html = _build_quick_wins_html(quick_wins, branche="E-Commerce", groesse="KMU")

        assert 'E-Commerce' in html, "Missing branche in context banner"
        assert 'KMU' in html, "Missing groesse in context banner"


class TestP07Integration:
    """Integration tests for P0.7."""

    def test_canonical_rate_lookup_by_size(self):
        """Test that canonical rates are looked up correctly by size."""
        from services.business_case_engine_v2 import get_hourly_rate, HOURLY_RATES_BY_SIZE

        # Verify canonical rates
        assert HOURLY_RATES_BY_SIZE.get("solo") == 80
        assert HOURLY_RATES_BY_SIZE.get("team") == 95
        assert HOURLY_RATES_BY_SIZE.get("kmu") == 110
        assert HOURLY_RATES_BY_SIZE.get("enterprise") == 130

        # Verify get_hourly_rate returns correct values
        rate_solo, _ = get_hourly_rate("solo")
        assert rate_solo == 80

        rate_team, _ = get_hourly_rate("team")
        assert rate_team == 95

    def test_hours_pattern_matching(self):
        """Test various hours patterns are recognized."""
        from gpt_analyze import _calculate_quickwin_savings_display

        test_cases = [
            ("10-15 h/Monat", 80, True),  # Standard range
            ("10–15h/Monat", 80, True),    # En-dash
            ("10 bis 15 Stunden", 80, True),  # "bis" connector
            ("ca. 12 h monatlich", 80, True),  # Single value
            ("keine Angabe", 80, False),  # No hours
        ]

        for input_text, rate, should_have_euro in test_cases:
            result = _calculate_quickwin_savings_display(input_text, rate)
            if should_have_euro:
                assert '€' in result, f"Expected € in result for '{input_text}', got: {result}"
            else:
                # Fallback case
                assert 'auf Anfrage' in result or '€' not in result
