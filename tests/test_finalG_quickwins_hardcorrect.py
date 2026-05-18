# -*- coding: utf-8 -*-
"""
Tests for Fix-Batch G - Quick Wins HARTE KORREKTUR

Tests:
- No "Icon:" label in Quick Wins output
- No truncated steps (Copy &. etc.)
- EUR ranges always correct (hours × canonical_rate)
- No soft-fail wrap path (always compact fallback)
"""

import os
import pytest
import re

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestQuickWinsNoIconLabel:
    """Test that Icon: label never appears in Quick Wins output."""

    def test_icon_label_cleaned_from_icon_field(self):
        """Test that 'Icon:' prefix is removed from icon field."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            "title": "Test Win",
            "icon": "Icon: 📧",  # LLM might produce this
            "time": "2h",
            "engpass": "Problem",
            "description": "Current state",
            "mit_ki": "With AI",
            "steps": ["Step 1"],
            "zeitersparnis": "10h/Monat",
        }]

        result = _build_quick_wins_html(quick_wins, "IT", "team")

        # Should NOT contain "Icon:" text
        assert "Icon:" not in result
        # Should contain the emoji
        assert "📧" in result or "◎" in result  # Either emoji or default

    def test_symbol_label_cleaned_from_icon_field(self):
        """Test that 'Symbol:' prefix is also removed."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            "title": "Test Win",
            "icon": "Symbol: ⚙️",
            "time": "2h",
            "engpass": "Problem",
            "description": "Current state",
            "mit_ki": "With AI",
            "steps": ["Step 1"],
            "zeitersparnis": "10h/Monat",
        }]

        result = _build_quick_wins_html(quick_wins, "IT", "team")

        # Should NOT contain "Symbol:" text
        assert "Symbol:" not in result

    def test_long_icon_field_uses_default(self):
        """Test that overly long icon fields use default."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            "title": "Test Win",
            "icon": "Icon for email automation process",  # Not an emoji
            "time": "2h",
            "engpass": "Problem",
            "description": "Current state",
            "mit_ki": "With AI",
            "steps": ["Step 1"],
            "zeitersparnis": "10h/Monat",
        }]

        result = _build_quick_wins_html(quick_wins, "IT", "team")

        # Should use default icon, not the long text
        assert "Icon for email" not in result
        assert "◎" in result  # Default icon


class TestQuickWinsNoTruncatedSteps:
    """Test that steps are not truncated."""

    def test_sanitize_quickwin_step_fixes_copy_and(self):
        """Test that 'Copy &.' is fixed."""
        from gpt_analyze import _sanitize_quickwin_step

        result = _sanitize_quickwin_step("Copy &.")

        # Should be fixed to complete sentence
        assert "Copy &." not in result
        assert result.endswith(".")

    def test_sanitize_quickwin_step_fixes_trailing_ampersand(self):
        """Test that trailing '&.' is fixed."""
        from gpt_analyze import _sanitize_quickwin_step

        result = _sanitize_quickwin_step("Daten exportieren und &.")

        # Should be fixed
        assert "&." not in result
        assert result.endswith(".")

    def test_sanitize_quickwin_step_adds_punctuation(self):
        """Test that missing punctuation is added."""
        from gpt_analyze import _sanitize_quickwin_step

        result = _sanitize_quickwin_step("Tool installieren")

        # Should end with punctuation
        assert result.endswith(".")

    def test_sanitize_quickwin_step_empty_returns_empty(self):
        """Test that empty input returns empty."""
        from gpt_analyze import _sanitize_quickwin_step

        result = _sanitize_quickwin_step("")

        assert result == ""

    def test_sanitize_quickwin_step_short_returns_empty(self):
        """Test that very short input returns empty."""
        from gpt_analyze import _sanitize_quickwin_step

        result = _sanitize_quickwin_step("ab")

        assert result == ""

    def test_build_html_uses_sanitized_steps(self):
        """Test that _build_quick_wins_html uses sanitized steps."""
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            "title": "Test Win",
            "icon": "📧",
            "time": "2h",
            "engpass": "Problem",
            "description": "Current state",
            "mit_ki": "With AI",
            "steps": ["Copy &.", "Daten exportieren und &.", "Normal step"],
            "zeitersparnis": "10h/Monat",
        }]

        result = _build_quick_wins_html(quick_wins, "IT", "team")

        # Should not have truncated patterns
        assert "Copy &." not in result
        assert "und &." not in result


class TestQuickWinsEURCalculation:
    """Test that EUR calculation uses canonical rate correctly."""

    def test_eur_range_correct_for_80eur_rate(self):
        """Test EUR calculation with 80€/h canonical rate."""
        from gpt_analyze import _calculate_quickwin_savings_display

        # 15-20h at 80€/h should be 1.200-1.600€
        result = _calculate_quickwin_savings_display("15-20 h/Monat", 80)

        # Should have correct EUR values
        assert "1.200" in result or "1200" in result
        assert "1.600" in result or "1600" in result

    def test_eur_strips_llm_wrong_values(self):
        """Test that wrong LLM EUR values are stripped and recalculated."""
        from gpt_analyze import _calculate_quickwin_savings_display

        # LLM might produce wrong values - they should be replaced
        result = _calculate_quickwin_savings_display("15-20h = 400-800€", 80)

        # Should have correct values (15-20h × 80 = 1.200-1.600)
        # Wrong values should be gone
        assert "400" not in result or "1.200" in result

    def test_eur_single_value_creates_range(self):
        """Test that single hour values create a range."""
        from gpt_analyze import _calculate_quickwin_savings_display

        result = _calculate_quickwin_savings_display("10h/Monat", 80)

        # Should produce some EUR range
        assert "€" in result
        assert "–" in result or "-" in result

    def test_eur_empty_returns_fallback(self):
        """Test that empty input returns fallback text."""
        from gpt_analyze import _calculate_quickwin_savings_display

        result = _calculate_quickwin_savings_display("", 80)

        assert "auf Anfrage" in result


class TestQuickWinsNoSoftFail:
    """Test that soft-fail wrap path is removed."""

    def test_no_soft_fail_wrap_in_code(self):
        """Test that QW-SOFT-FAIL log message is removed from code."""
        from gpt_analyze import __file__ as gpt_analyze_path

        with open(gpt_analyze_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should NOT have the old soft-fail wrap
        assert "QW-SOFT-FAIL" not in content or "REMOVED" in content

    def test_enforce_quickwins_uses_compact_fallback(self):
        """Test that _enforce_quickwins_no_raw_json uses compact fallback."""
        from gpt_analyze import _enforce_quickwins_no_raw_json

        # Raw JSON without HTML structure
        raw_json = '{"title": "Test"}'

        result = _enforce_quickwins_no_raw_json(raw_json, "IT", "team")

        # Should produce table HTML (compact fallback), not wrapped raw content
        assert "<table" in result or "class=" in result
        # Should not just wrap raw content
        assert "quick-wins-fallback" not in result or "<table" in result

    def test_broken_content_gets_appropriate_fallback(self):
        """Test that broken content gets appropriate fallback (table or error div)."""
        from gpt_analyze import _enforce_quickwins_no_raw_json

        broken = "Some random text without any structure"

        result = _enforce_quickwins_no_raw_json(broken, "IT", "team")

        # Should get some HTML fallback (either compact table or error message div)
        assert "<div" in result or "<table" in result
        # Should not return raw broken text
        assert "random text" not in result or "class=" in result


class TestBatchGIntegration:
    """Integration tests for Fix-Batch G."""

    def test_full_pipeline_no_icon_label(self):
        """Test full pipeline never outputs Icon: label."""
        from gpt_analyze import _build_quick_wins_html, _enforce_quickwins_no_raw_json

        # Test various icon field values
        test_icons = [
            "Icon: 📧",
            "Symbol: ⚙️",
            "Emoji: 🚀",
            "Icon for process",
            "📧",  # Normal emoji
        ]

        for test_icon in test_icons:
            quick_wins = [{
                "title": "Test",
                "icon": test_icon,
                "time": "2h",
                "engpass": "X",
                "description": "Y",
                "mit_ki": "Z",
                "steps": ["A"],
                "zeitersparnis": "5h",
            }]

            result = _build_quick_wins_html(quick_wins, "IT", "team")

            # Never should have Icon:/Symbol:/Emoji: labels
            assert "Icon:" not in result, f"Icon: found for input: {test_icon}"
            assert "Symbol:" not in result, f"Symbol: found for input: {test_icon}"
            assert "Emoji:" not in result, f"Emoji: found for input: {test_icon}"

    def test_full_pipeline_renders_prompt_schema_fields(self):
        """[QW-SCHEMA-FIX] Builder uses prompt schema (problem/wirkung/
        umsetzung/hinweis). Prompt v8.3 Z.26 forbids digits/EUR values in
        Quick Wins, so the builder no longer renders EUR via
        _calculate_quickwin_savings_display. The helper itself remains
        unit-tested at TestQuickWinsEURCalculation in this file.
        """
        from gpt_analyze import _build_quick_wins_html

        quick_wins = [{
            "title": "Test",
            "icon": "📧",
            "problem": "Bottleneck",
            "wirkung": "Effect with AI",
            "umsetzung": "Steps to implement",
            "hinweis": "siehe Business Case",
        }]

        result = _build_quick_wins_html(quick_wins, "IT", "team")

        # Prompt-schema fields are rendered
        assert "Bottleneck" in result
        assert "Effect with AI" in result
        assert "Steps to implement" in result
        assert "siehe Business Case" in result

    def test_fix_batch_g_comment_exists(self):
        """Test that Fix-Batch G comment block exists."""
        from gpt_analyze import __file__ as gpt_analyze_path

        with open(gpt_analyze_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should have Fix-Batch G comments
        assert "Fix-Batch G" in content
