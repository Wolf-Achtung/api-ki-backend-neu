# -*- coding: utf-8 -*-
"""Tests for Session 11: Admin Re-Test Endpoints.

Tests sanitizer dry-run logic, re-render behavior, and raw_sections storage.
"""

import copy
import os
import pytest

# Set admin key before any import attempts
os.environ.setdefault("STRATEGY_ADMIN_KEY", "test-admin-key-123")

from services.strategy_sanitizer import sanitize_strategy_sections

# Check if full app dependencies are available
try:
    from models import StrategyReport
    from routes.strategy import _verify_admin_key
    _HAS_APP_DEPS = True
except ImportError:
    _HAS_APP_DEPS = False

needs_app = pytest.mark.skipif(not _HAS_APP_DEPS, reason="Full app dependencies not available")


# ── Unit tests for sanitizer dry-run logic ───────────────────────────


def _make_sections() -> dict:
    """Create realistic strategy sections with both ROI and adoption values."""
    return {
        "S2": (
            '<table><tr><td>EU-Unternehmen: KI-Nutzung (2025)</td>'
            '<td>104%</td><td>Eurostat</td></tr>'
            '<tr><td>Deutsche Unternehmen</td>'
            '<td>25%</td><td>Bitkom</td></tr></table>'
        ),
        "S5": (
            '<table>'
            '<tr><td>Konservativ</td><td>104% ROI</td><td>Break-Even Monat 6</td></tr>'
            '<tr><td>Realistisch</td><td>239% ROI</td><td>Break-Even Monat 4</td></tr>'
            '<tr><td>Optimistisch</td><td>375% ROI</td><td>Break-Even Monat 3</td></tr>'
            '</table>'
        ),
    }


class TestSanitizerDryRunLogic:
    """Test the sanitizer dry-run behavior that powers the endpoint."""

    def test_sanitizer_patches_adoption_not_roi(self):
        """Sanitizer patches adoption >100% but skips ROI >100%."""
        sections = _make_sections()
        result = sanitize_strategy_sections(copy.deepcopy(sections), report_year=2026)

        report = result.pop('_strategy_sanitizer_report', {})

        # S2: 104% in adoption context should be patched
        assert "104%" not in result["S2"]
        assert "\u2013*" in result["S2"]

        # S5: ROI values should NOT be patched
        assert "104%" in result["S5"]
        assert "239%" in result["S5"]
        assert "375%" in result["S5"]

        # Only 1 patch (the adoption one)
        assert report["patches_applied"] == 1

    def test_dry_run_does_not_modify_original(self):
        """Dry-run (deepcopy) must not modify the original sections."""
        sections = _make_sections()
        original_s2 = sections["S2"]

        test_copy = copy.deepcopy(sections)
        sanitize_strategy_sections(test_copy, report_year=2026)

        # Original must be unchanged
        assert sections["S2"] == original_s2
        assert "104%" in sections["S2"]

    def test_re_sanitize_idempotent(self):
        """Running sanitizer twice on same data yields same result."""
        sections = _make_sections()

        # First pass
        result1 = sanitize_strategy_sections(copy.deepcopy(sections), report_year=2026)
        result1.pop('_strategy_sanitizer_report', None)

        # Second pass on already-sanitized data
        result2 = sanitize_strategy_sections(copy.deepcopy(result1), report_year=2026)
        report2 = result2.pop('_strategy_sanitizer_report', {})

        # Should be identical — no new patches
        assert result1 == result2
        assert report2["patches_applied"] == 0

    def test_skip_logging_captures_roi_context(self):
        """Sanitizer skip logging must capture ROI context details."""
        import logging

        skip_records: list = []

        class _SkipCapture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                if "[FIX-SF1-SKIP]" in record.getMessage():
                    skip_records.append(record.getMessage())

        handler = _SkipCapture()
        handler.setLevel(logging.DEBUG)
        logger = logging.getLogger("services.strategy_sanitizer")
        logger.addHandler(handler)
        orig_level = logger.level
        logger.setLevel(logging.DEBUG)

        try:
            sections = _make_sections()
            sanitize_strategy_sections(copy.deepcopy(sections), report_year=2026)
        finally:
            logger.removeHandler(handler)
            logger.setLevel(orig_level)

        # S5 has 3 ROI values >100%: 104%, 239%, 375%
        assert len(skip_records) == 3
        assert any("roi" in r.lower() for r in skip_records)

    def test_mixed_section_roi_context_takes_priority(self):
        """When ROI keywords are within ±200 chars, ROI context takes priority (no patch).
        This is correct: it's safer to keep a potentially valid value than to destroy it."""
        html = (
            '<p>Die Nutzung von KI liegt bei 104% der Unternehmen.</p>'
            '<p>Die Investition ergibt eine Rendite von 239% über 12 Monate.</p>'
        )
        sections = {"S_MIXED": html}
        result = sanitize_strategy_sections(copy.deepcopy(sections), report_year=2026)
        result.pop('_strategy_sanitizer_report', None)

        # Both values preserved because "Investition"/"Rendite" ROI context is within ±200 chars
        assert "104%" in result["S_MIXED"]
        assert "239%" in result["S_MIXED"]

    def test_separated_sections_patch_adoption_keep_roi(self):
        """When adoption and ROI are in separate sections, each is handled correctly."""
        sections = {
            "S_ADOPT": '<p>Die Nutzung von KI liegt bei 104% der Unternehmen.</p>' + 'x' * 50,
            "S_ROI": '<p>Die Investition ergibt eine Rendite von 239% über 12 Monate.</p>' + 'y' * 50,
        }
        result = sanitize_strategy_sections(copy.deepcopy(sections), report_year=2026)
        result.pop('_strategy_sanitizer_report', None)

        # Adoption context: patched
        assert "104%" not in result["S_ADOPT"]
        assert "\u2013*" in result["S_ADOPT"]
        # ROI context: preserved
        assert "239%" in result["S_ROI"]


@needs_app
class TestVerifyAdminKey:
    """Test admin key verification logic."""

    def test_rejects_wrong_key(self):
        """Wrong admin key must be rejected."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _verify_admin_key("wrong-key")
        assert exc_info.value.status_code == 403

    def test_accepts_correct_key(self):
        """Correct admin key must pass."""
        _verify_admin_key("test-admin-key-123")

    def test_rejects_empty_env(self):
        """Missing STRATEGY_ADMIN_KEY must return 500."""
        from unittest.mock import patch as mock_patch
        from fastapi import HTTPException

        with mock_patch.dict(os.environ, {"STRATEGY_ADMIN_KEY": ""}):
            with pytest.raises(HTTPException) as exc_info:
                _verify_admin_key("any-key")
            assert exc_info.value.status_code == 500


@needs_app
class TestRawSectionsModel:
    """Test that raw_sections field exists on StrategyReport model."""

    def test_raw_sections_field_exists(self):
        """StrategyReport must have raw_sections field."""
        assert hasattr(StrategyReport, 'raw_sections')

    def test_raw_sections_in_columns(self):
        """raw_sections must be a mapped column."""
        columns = [c.name for c in StrategyReport.__table__.columns]
        assert 'raw_sections' in columns
