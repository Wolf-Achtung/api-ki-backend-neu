# -*- coding: utf-8 -*-
"""
P3.2 Test - Quick Wins Solo Threshold
======================================

Verifies that quick_wins minimum word count for solo is 30 (not 60).
This prevents [SECTION_TOO_SHORT] quick_wins warnings for typical solo outputs.

Ref: P3.2 – Quick-Wins Minimum für Solo neu definieren (Produktregel)
"""
import os
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestQuickWinsSoloThreshold:
    """Tests for P3.2: quick_wins solo threshold = 30 words."""

    def test_quick_wins_solo_threshold_is_30(self):
        """Verify solo quick_wins min_words is 30 (P3.2 requirement)."""
        from services.report_validator import ReportValidator

        # Direct check on MIN_SECTION_LENGTH_BY_SIZE
        solo_thresholds = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE.get("solo", {})
        quick_wins_solo = solo_thresholds.get("quick_wins")

        assert quick_wins_solo == 30, (
            f"quick_wins solo threshold should be 30, got {quick_wins_solo}"
        )

    def test_quick_wins_team_threshold_unchanged(self):
        """Verify team quick_wins min_words is still 90 (unchanged)."""
        from services.report_validator import ReportValidator

        team_thresholds = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE.get("team", {})
        quick_wins_team = team_thresholds.get("quick_wins")

        assert quick_wins_team == 90, (
            f"quick_wins team threshold should be 90, got {quick_wins_team}"
        )

    def test_quick_wins_kmu_threshold_unchanged(self):
        """Verify kmu quick_wins min_words is still 120 (unchanged)."""
        from services.report_validator import ReportValidator

        kmu_thresholds = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE.get("kmu", {})
        quick_wins_kmu = kmu_thresholds.get("quick_wins")

        assert quick_wins_kmu == 120, (
            f"quick_wins kmu threshold should be 120, got {quick_wins_kmu}"
        )

    def test_validator_uses_correct_threshold_for_solo(self):
        """Verify ReportValidator._get_min_words_for_section returns 30 for solo quick_wins."""
        from services.report_validator import ReportValidator

        # Create validator with solo company size (via meta dict)
        validator = ReportValidator(
            sections={"QUICK_WINS_HTML": "<p>Test content</p>"},
            meta={"unternehmensgroesse": "solo"}
        )

        min_words = validator._get_min_words_for_section("quick_wins")
        assert min_words == 30, (
            f"_get_min_words_for_section('quick_wins') for solo should be 30, got {min_words}"
        )

    def test_validator_uses_correct_threshold_for_freiberufler(self):
        """Verify ReportValidator detects 'Freiberufler' as solo."""
        from services.report_validator import ReportValidator

        # Create validator with Freiberufler company size (should map to solo)
        validator = ReportValidator(
            sections={"QUICK_WINS_HTML": "<p>Test content</p>"},
            meta={"unternehmensgroesse": "Freiberufler"}
        )

        min_words = validator._get_min_words_for_section("quick_wins")
        assert min_words == 30, (
            f"_get_min_words_for_section('quick_wins') for Freiberufler should be 30, got {min_words}"
        )

    def test_validator_uses_correct_threshold_for_1_person(self):
        """Verify ReportValidator detects '1 (Solo)' as solo."""
        from services.report_validator import ReportValidator

        # Create validator with "1 (Solo)" company size (should map to solo)
        validator = ReportValidator(
            sections={"QUICK_WINS_HTML": "<p>Test content</p>"},
            meta={"unternehmensgroesse": "1 (Solo)"}
        )

        min_words = validator._get_min_words_for_section("quick_wins")
        assert min_words == 30, (
            f"_get_min_words_for_section('quick_wins') for '1 (Solo)' should be 30, got {min_words}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
