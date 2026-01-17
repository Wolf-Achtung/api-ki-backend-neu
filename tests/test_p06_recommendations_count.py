# -*- coding: utf-8 -*-
"""
Tests for P0.6 - Recommendations Count Consistency

Tests:
- Count in summary matches displayed items
- top_3 + others = total count
- validate_count_consistency method works correctly
"""

import pytest


class TestRecommendationsCountConsistency:
    """Test that recommendations count matches displayed items."""

    def test_displayed_count_equals_total(self):
        """Test that displayed_count (top3 + others) equals total."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
        )

        # Create 5 recommendations
        recommendations = [
            Recommendation(
                id=f"rec_{i}",
                title=f"Recommendation {i}",
                description=f"Description {i}",
                reason=f"Reason {i}",
                impact_level="high" if i < 2 else "medium",
                urgency_level="high" if i < 2 else "medium",
                risk_relation="neutral",
                timeline_phase="phase_1",
            )
            for i in range(5)
        ]

        report = RecommendationsReport(
            recommendations=recommendations,
            summary="5 konkrete Empfehlungen wurden identifiziert.",
            top_3_ids=["rec_0", "rec_1", "rec_2"],
        )

        # displayed_count = top_3 + others = 5
        assert report.displayed_count == 5
        assert len(report.top_3_recommendations) == 3
        assert len(report.other_recommendations) == 2
        assert report.displayed_count == len(report.recommendations)

    def test_validate_count_consistency_passes(self):
        """Test validation passes when counts match."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
        )

        recommendations = [
            Recommendation(
                id=f"rec_{i}",
                title=f"Recommendation {i}",
                description=f"Description {i}",
                reason=f"Reason {i}",
                impact_level="medium",
                urgency_level="medium",
                risk_relation="neutral",
            )
            for i in range(4)
        ]

        report = RecommendationsReport(
            recommendations=recommendations,
            summary="Für Ihr Team wurden 4 konkrete Handlungsempfehlungen identifiziert.",
            top_3_ids=["rec_0", "rec_1", "rec_2"],
        )

        is_valid, error = report.validate_count_consistency()
        assert is_valid is True, f"Should be valid, got error: {error}"

    def test_validate_count_consistency_fails_on_summary_mismatch(self):
        """Test validation fails when summary count doesn't match actual."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
        )

        recommendations = [
            Recommendation(
                id=f"rec_{i}",
                title=f"Recommendation {i}",
                description=f"Description {i}",
                reason=f"Reason {i}",
                impact_level="medium",
                urgency_level="medium",
                risk_relation="neutral",
            )
            for i in range(3)  # Only 3 recommendations
        ]

        # Summary says 5 but we only have 3
        report = RecommendationsReport(
            recommendations=recommendations,
            summary="Für Ihr Team wurden 5 konkrete Handlungsempfehlungen identifiziert.",
            top_3_ids=["rec_0", "rec_1", "rec_2"],
        )

        is_valid, error = report.validate_count_consistency()
        assert is_valid is False, "Should fail due to summary mismatch"
        assert "5" in error and "3" in error

    def test_top_3_ids_filtered_to_existing(self):
        """Test that invalid top_3_ids are filtered out."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
        )

        recommendations = [
            Recommendation(
                id="rec_0",
                title="Recommendation 0",
                description="Description 0",
                reason="Reason 0",
                impact_level="high",
                urgency_level="high",
                risk_relation="neutral",
            ),
            Recommendation(
                id="rec_1",
                title="Recommendation 1",
                description="Description 1",
                reason="Reason 1",
                impact_level="medium",
                urgency_level="medium",
                risk_relation="neutral",
            ),
        ]

        # top_3_ids includes non-existent IDs
        report = RecommendationsReport(
            recommendations=recommendations,
            summary="2 konkrete Empfehlungen",
            top_3_ids=["rec_0", "rec_1", "rec_invalid", "rec_missing"],
        )

        # Should only have 2 valid top_3
        assert len(report.top_3_recommendations) == 2
        assert len(report.other_recommendations) == 0
        assert report.displayed_count == 2

    def test_english_summary_validation(self):
        """Test validation works with English summary."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
        )

        recommendations = [
            Recommendation(
                id=f"rec_{i}",
                title=f"Recommendation {i}",
                description=f"Description {i}",
                reason=f"Reason {i}",
                impact_level="medium",
                urgency_level="medium",
                risk_relation="neutral",
            )
            for i in range(6)
        ]

        report = RecommendationsReport(
            recommendations=recommendations,
            summary="For your company, 6 concrete recommendations were identified.",
            top_3_ids=["rec_0", "rec_1", "rec_2"],
        )

        is_valid, error = report.validate_count_consistency()
        assert is_valid is True, f"Should be valid for EN summary, got error: {error}"


class TestRecommendationsReportProperties:
    """Test RecommendationsReport properties."""

    def test_to_dict_includes_count(self):
        """Test that to_dict includes count field."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
        )

        recommendations = [
            Recommendation(
                id=f"rec_{i}",
                title=f"Test {i}",
                description="Desc",
                reason="Reason",
                impact_level="medium",
                urgency_level="medium",
                risk_relation="neutral",
            )
            for i in range(4)
        ]

        report = RecommendationsReport(
            recommendations=recommendations,
            summary="Summary",
            top_3_ids=["rec_0", "rec_1", "rec_2"],
        )

        data = report.to_dict()
        assert "count" in data
        assert data["count"] == 4


class TestP06Integration:
    """Integration tests for P0.6."""

    def test_generate_recommendations_validates_consistency(self):
        """Test that generate_recommendations_report validates count."""
        from services.recommendations_engine import generate_recommendations_report

        # Generate with minimal context
        report = generate_recommendations_report(
            briefing={"UNTERNEHMENSGRÖSSE": "team", "BRANCHE": "IT"},
        )

        # Validation should pass
        is_valid, error = report.validate_count_consistency()
        assert is_valid is True, f"Generated report should be consistent, got: {error}"

        # Count should be positive
        assert len(report.recommendations) > 0
        assert report.displayed_count == len(report.recommendations)

    def test_html_renders_all_recommendations(self):
        """Test that HTML contains all recommendations."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
            recommendations_report_to_html,
        )

        recommendations = [
            Recommendation(
                id=f"rec_{i}",
                title=f"Unique Title {i}",
                description=f"Unique Description {i}",
                reason=f"Unique Reason {i}",
                impact_level="medium",
                urgency_level="medium",
                risk_relation="neutral",
            )
            for i in range(5)
        ]

        report = RecommendationsReport(
            recommendations=recommendations,
            summary="5 konkrete Empfehlungen",
            top_3_ids=["rec_0", "rec_1", "rec_2"],
        )

        html = recommendations_report_to_html(report, lang="de")

        # All 5 titles should appear in HTML
        for i in range(5):
            assert f"Unique Title {i}" in html, f"Title {i} should be in HTML"

    def test_html_with_exclude_top3(self):
        """Test that exclude_top_3 option works correctly."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
            recommendations_report_to_html,
        )

        recommendations = [
            Recommendation(
                id=f"rec_{i}",
                title=f"Title {i}",
                description=f"Description {i}",
                reason=f"Reason {i}",
                impact_level="medium",
                urgency_level="medium",
                risk_relation="neutral",
            )
            for i in range(5)
        ]

        report = RecommendationsReport(
            recommendations=recommendations,
            summary="5 Empfehlungen",
            top_3_ids=["rec_0", "rec_1", "rec_2"],
        )

        # With exclude_top_3=True, only other 2 should be rendered
        html = recommendations_report_to_html(report, lang="de", exclude_top_3=True)

        # Top-3 titles should NOT appear (or only in "other" section)
        # Others (rec_3, rec_4) should appear
        assert "Title 3" in html
        assert "Title 4" in html
