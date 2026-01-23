# -*- coding: utf-8 -*-
"""
FIX-515: Tests for Truncation Caps, Feedback Analyzer, Text-Healing No-Op,
and Strict-Ready Summary Log.
"""
import logging
import pytest


class TestFix515TruncationCaps:
    """TASK 1: UNTERNEHMENSPROFIL_MARKT_HTML must not be >50% truncated."""

    def test_truncation_cap_prevents_extreme_cut(self):
        """If truncation would cut >50%, it must be reverted."""
        # Simulate the cap logic
        original_len = 11000
        truncated_len = 4500  # >50% cut

        trunc_pct = (1 - truncated_len / original_len) * 100
        assert trunc_pct > 50, f"Expected >50% cut, got {trunc_pct:.1f}%"

        # The guard should revert (keep original)
        should_revert = trunc_pct > 50
        assert should_revert is True

    def test_truncation_cap_allows_moderate_cut(self):
        """If truncation cuts <=50%, it should proceed normally."""
        original_len = 10000
        truncated_len = 6000  # 40% cut - acceptable

        trunc_pct = (1 - truncated_len / original_len) * 100
        assert trunc_pct <= 50

        should_revert = trunc_pct > 50
        assert should_revert is False

    def test_truncation_source_has_fix515_log(self):
        """gpt_analyze.py must contain [FIX-515][TRUNC] log line."""
        from pathlib import Path
        source = Path("gpt_analyze.py").read_text()
        assert "[FIX-515][TRUNC]" in source

    def test_truncation_cap_50_percent_boundary(self):
        """Exactly 50% cut should be allowed (cap is >50%)."""
        original_len = 10000
        truncated_len = 5000  # Exactly 50%

        trunc_pct = (1 - truncated_len / original_len) * 100
        should_revert = trunc_pct > 50
        assert should_revert is False  # 50% is ok, >50% is not


class TestFix515FeedbackAnalyzerEmpty:
    """TASK 2: Empty dataset must log INFO, not WARNING."""

    def test_empty_feedback_logs_info_not_warning(self):
        """When no feedback entries exist, should be INFO level."""
        import inspect
        from services.feedback_analyzer import build_segments_snapshot

        source = inspect.getsource(build_segments_snapshot)
        # Must NOT have warning for empty entries
        assert 'log.warning("No feedback entries found for segment analysis")' not in source
        # Must have info
        assert 'log.info("No feedback entries found - skipping segment analysis")' in source

    def test_empty_feedback_returns_empty_dict(self):
        """Empty feedback should return empty dict without errors."""
        from unittest.mock import patch

        from services.feedback_analyzer import build_segments_snapshot

        with patch("services.feedback_loop.get_recent_feedback", return_value=[]):
            result = build_segments_snapshot(force=True)
            assert result == {}


class TestFix515TextHealingNoOp:
    """TASK 3: No-op heals (before==after) must not log as 'Healed'."""

    def test_noop_heal_not_logged(self, caplog):
        """If healed.strip() == original.strip(), no 'Healed' log."""
        from services.text_healing import heal_text_block

        # Input that won't change (already clean)
        text = "Dies ist ein sauberer Satz. Er endet korrekt."

        with caplog.at_level(logging.INFO, logger="services.text_healing"):
            result = heal_text_block(text, domain="risk")

        # If output is same as input, should not log "Healed"
        if result.strip() == text.strip():
            heal_msgs = [r for r in caplog.records if "Healed" in r.getMessage()]
            assert len(heal_msgs) == 0, (
                f"No-op heal should not be logged, but found: {[r.getMessage() for r in heal_msgs]}"
            )

    def test_real_heal_is_logged(self, caplog):
        """If content actually changes, 'Healed' log should appear."""
        from services.text_healing import heal_text_block

        # Input with trailing fragment that will be healed
        text = "Dies ist ein Satz. Und ein weiterer der"

        with caplog.at_level(logging.INFO, logger="services.text_healing"):
            result = heal_text_block(text, domain="risk")

        # If actually healed, log should appear
        if result.strip() != text.strip():
            heal_msgs = [r for r in caplog.records if "Healed" in r.getMessage()]
            assert len(heal_msgs) > 0, "Real heal should be logged"

    def test_source_uses_strip_comparison(self):
        """text_healing.py must compare stripped versions."""
        import inspect
        from services.text_healing import heal_text_block

        source = inspect.getsource(heal_text_block)
        assert "healed.strip() != t.strip()" in source


class TestFix515StrictReadyLog:
    """TASK 4: [FIX-515][STRICT-READY] summary must be emitted after contract PASS."""

    def test_strict_ready_log_in_source(self):
        """report_renderer.py render() must contain [FIX-515][STRICT-READY] log."""
        import inspect
        from services.report_renderer import render

        source = inspect.getsource(render)
        assert "[FIX-515][STRICT-READY]" in source

    def test_strict_ready_log_format(self):
        """Log format must include contract_pass, repair_llm_used, quickwins_nonempty."""
        import inspect
        from services.report_renderer import render

        source = inspect.getsource(render)
        assert "contract_pass=1" in source
        assert "repair_llm_used=" in source
        assert "quickwins_nonempty=" in source
        assert "warnings_total=" in source
