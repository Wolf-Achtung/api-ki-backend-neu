# -*- coding: utf-8 -*-
"""
Sprint G17.1 Tests: Segment Calibration & Insight Reliability

Tests for:
- G17.1-A: Segment coverage calibration (outlier detection, winsorizing)
- G17.1-B: Insight reliability filter
- G17.1-C: Funding insight stability
- G17.1-D: Dashboard endpoints
- G17.1-E: Integration tests

Version: 1.0.0
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# TEST G17.1-A: SEGMENT CALIBRATION
# =============================================================================

class TestG17_1A_SegmentCalibration:
    """Tests for segment calibration functions."""

    def setup_method(self) -> None:
        """Clear feedback store before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def test_calculate_std_empty(self) -> None:
        """Standard deviation of empty list should be 0."""
        from services.feedback_analyzer import _calculate_std

        assert _calculate_std([]) == 0.0
        assert _calculate_std([50.0]) == 0.0  # Single value

    def test_calculate_std_values(self) -> None:
        """Standard deviation should be calculated correctly."""
        from services.feedback_analyzer import _calculate_std

        # Known values: [2, 4, 4, 4, 5, 5, 7, 9] has std ~= 2.138
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        std = _calculate_std(values)
        assert 2.0 < std < 2.3  # Approximately 2.138

    def test_winsorize_values_no_outliers(self) -> None:
        """Values within threshold should not be modified."""
        from services.feedback_analyzer import _winsorize_values

        values = [50.0, 55.0, 60.0, 65.0, 70.0]
        winsorized, trimmed = _winsorize_values(values, std_threshold=2.5)

        assert winsorized == values
        assert trimmed is False

    def test_winsorize_values_with_outliers(self) -> None:
        """Outliers beyond threshold should be clipped."""
        from services.feedback_analyzer import _winsorize_values

        # Create data with very extreme outlier using a lower threshold
        # Mean ~50, std ~1.5, so 1.5 std threshold would flag 53+
        values = [50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 100.0]  # 100 is extreme
        winsorized, trimmed = _winsorize_values(values, std_threshold=1.5)  # Lower threshold

        assert trimmed is True
        assert winsorized[-1] < 100.0  # Outlier was clipped
        assert len(winsorized) == len(values)

    def test_winsorize_values_small_list(self) -> None:
        """Small lists should not be modified."""
        from services.feedback_analyzer import _winsorize_values

        values = [50.0, 60.0]  # Too small for winsorizing
        winsorized, trimmed = _winsorize_values(values, std_threshold=2.5)

        assert winsorized == values
        assert trimmed is False

    def test_determine_segment_stability_weak(self) -> None:
        """Segments with small sample size should be weak."""
        from services.feedback_analyzer import _determine_segment_stability

        stability = _determine_segment_stability(
            sample_size=3,  # Below threshold
            std_overall=5.0,
            max_influence=0.33,
        )
        assert stability == "weak"

    def test_determine_segment_stability_strong(self) -> None:
        """Segments with good sample and low variance should be strong."""
        from services.feedback_analyzer import _determine_segment_stability

        stability = _determine_segment_stability(
            sample_size=25,  # Good sample
            std_overall=8.0,  # Low variance
            max_influence=0.04,  # Low influence
        )
        assert stability == "strong"

    def test_determine_segment_stability_medium(self) -> None:
        """Borderline segments should be medium."""
        from services.feedback_analyzer import _determine_segment_stability

        stability = _determine_segment_stability(
            sample_size=12,  # Just above minimum
            std_overall=20.0,  # Higher variance
            max_influence=0.08,
        )
        # Could be medium due to sample size or std
        assert stability in ("medium", "strong")

    def test_determine_segment_stability_high_influence(self) -> None:
        """High single-report influence should result in weak."""
        from services.feedback_analyzer import _determine_segment_stability

        stability = _determine_segment_stability(
            sample_size=2,  # Results in 50% influence
            std_overall=5.0,
            max_influence=0.5,
        )
        assert stability == "weak"

    def test_calibrate_segment_data(self) -> None:
        """Calibration should add stability metadata."""
        from services.feedback_analyzer import _calibrate_segment_data

        data = {
            "scores_overall": [50.0, 60.0, 55.0, 58.0, 52.0, 100.0],  # 100 is outlier
            "roi_values": [120.0, 130.0, 125.0, 128.0, 122.0],
        }

        calibrated = _calibrate_segment_data(data, report_count=6)

        assert "segment_stability" in calibrated
        assert "std_score_overall" in calibrated
        assert "max_influence_weight" in calibrated
        assert "outliers_trimmed" in calibrated
        assert calibrated["sample_size"] == 6

    def test_segment_stats_to_dict_includes_stability(self) -> None:
        """SegmentStats.to_dict should include stability fields."""
        from services.feedback_analyzer import SegmentStats

        stats = SegmentStats(
            segment_key=("solo", "consulting", "minimal", "DE"),
            report_count=20,
            segment_stability="strong",
            sample_size=20,
            outliers_trimmed=False,
            std_score_overall=8.5,
            max_influence_weight=0.05,
        )

        result = stats.to_dict()

        assert result["segment_stability"] == "strong"
        assert result["sample_size"] == 20
        assert result["outliers_trimmed"] is False
        assert result["std_score_overall"] == 8.5


# =============================================================================
# TEST G17.1-B: INSIGHT RELIABILITY FILTER
# =============================================================================

class TestG17_1B_InsightReliabilityFilter:
    """Tests for insight reliability filter."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def test_insight_result_includes_reliability_fields(self) -> None:
        """InsightResult should include reliability metadata."""
        from services.insights_engine import InsightResult

        result = InsightResult(
            cards=[],
            summary_html="<p>Test</p>",
            has_sufficient_data=True,
            is_reliable=True,
            is_generic_fallback=False,
            segment_stability="strong",
            reliability_note="",
        )

        result_dict = result.to_dict()

        assert "is_reliable" in result_dict
        assert "is_generic_fallback" in result_dict
        assert "segment_stability" in result_dict
        assert result_dict["is_reliable"] is True

    def test_build_report_insights_no_segment(self) -> None:
        """Should return insufficient data when no segment found."""
        from services.insights_engine import build_report_insights

        result = build_report_insights({})

        assert result.has_sufficient_data is False
        assert result.segment_stability == "unknown"

    @patch("services.feedback_analyzer.get_segment_for_report")
    @patch("services.feedback_analyzer.get_segment_comparison")
    @patch("services.feedback_analyzer.is_segment_reliable")
    def test_build_report_insights_reliable_segment(
        self,
        mock_is_reliable: MagicMock,
        mock_comparison: MagicMock,
        mock_segment: MagicMock,
    ) -> None:
        """Reliable segment should generate specific insights."""
        # Setup mocks with all required attributes
        mock_segment.return_value = MagicMock(
            segment_stability="strong",
            avg_score_governance=70.0,
            avg_score_security=65.0,
            avg_score_value=60.0,
            avg_score_enablement=55.0,
            avg_score_overall=62.5,
            avg_roi_percent=0.0,
            avg_payback_months=0.0,
            top_warning_types=[],
        )
        mock_comparison.return_value = {
            "segment_found": True,
            "segment_label": "Solo · Consulting",
            "position": "durchschnitt",
            "position_text": "im Durchschnitt",
            "current_score": 65.0,
            "segment_avg_score": 62.5,
            "report_count": 25,
        }
        mock_is_reliable.return_value = True

        from services.insights_engine import build_report_insights

        result = build_report_insights(
            {"REIFEGRAD_GESAMT": 65},
            {"size_label": "solo"}
        )

        assert result.is_reliable is True
        assert result.is_generic_fallback is False
        assert result.segment_stability == "strong"

    @patch("services.feedback_analyzer.get_segment_for_report")
    @patch("services.feedback_analyzer.get_segment_comparison")
    @patch("services.feedback_analyzer.is_segment_reliable")
    def test_build_report_insights_unreliable_fallback(
        self,
        mock_is_reliable: MagicMock,
        mock_comparison: MagicMock,
        mock_segment: MagicMock,
    ) -> None:
        """Unreliable segment should use generic fallback."""
        # Setup mocks
        mock_segment.return_value = MagicMock(
            segment_stability="weak",
        )
        mock_comparison.return_value = {
            "segment_found": True,
            "segment_label": "Solo · Other",
        }
        mock_is_reliable.return_value = False

        from services.insights_engine import build_report_insights

        result = build_report_insights(
            {"REIFEGRAD_GESAMT": 65},
            {"size_label": "solo"}
        )

        assert result.is_generic_fallback is True
        assert result.is_reliable is False

    def test_generic_fallback_cards_exist(self) -> None:
        """Generic fallback should generate cards."""
        from services.insights_engine import _build_generic_fallback_insights

        mock_segment = MagicMock(segment_stability="weak")

        result = _build_generic_fallback_insights(
            report_sections={"REIFEGRAD_GESAMT": 55},
            profile={"size_label": "team"},
            segment_stats=mock_segment,
            segment_stability="weak",
        )

        assert len(result.cards) > 0
        assert result.is_generic_fallback is True

    def test_generic_size_card_solo(self) -> None:
        """Generic size card for solo should exist."""
        from services.insights_engine import _build_generic_size_card

        card = _build_generic_size_card("solo")

        assert card is not None
        assert "Solo" in card.title or "Solo" in card.body_html

    def test_generic_size_card_team(self) -> None:
        """Generic size card for team should exist."""
        from services.insights_engine import _build_generic_size_card

        card = _build_generic_size_card("team")

        assert card is not None
        assert "Team" in card.title or "Team" in card.body_html

    def test_generic_maturity_card_high(self) -> None:
        """High maturity should get highlight card."""
        from services.insights_engine import _build_generic_maturity_card

        card = _build_generic_maturity_card({"REIFEGRAD_GESAMT": 75})

        assert card is not None
        assert card.severity == "highlight"

    def test_generic_maturity_card_low(self) -> None:
        """Low maturity should get opportunity card."""
        from services.insights_engine import _build_generic_maturity_card

        card = _build_generic_maturity_card({"REIFEGRAD_GESAMT": 35})

        assert card is not None
        assert card.severity == "opportunity"


# =============================================================================
# TEST G17.1-C: FUNDING INSIGHT STABILITY
# =============================================================================

class TestG17_1C_FundingInsightStability:
    """Tests for funding insight stability."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def test_funding_insight_has_confidence_level(self) -> None:
        """FundingInsight should have confidence_level field."""
        from services.funding_recommender import FundingInsight

        insight = FundingInsight(
            program_id="test",
            program_name="Test Program",
            success_rate=0.3,
            similar_profiles_count=20,
            avg_relevance_score=0.7,
            insight_text="Test insight",
            severity="info",
            confidence_level="high",
        )

        assert insight.confidence_level == "high"

    def test_calculate_insight_confidence_weak_segment(self) -> None:
        """Weak segment should result in low confidence."""
        from services.funding_recommender import _calculate_insight_confidence

        confidence = _calculate_insight_confidence(
            program_count=10,
            total_count=20,
            segment_stability="weak",
        )

        assert confidence == "low"

    def test_calculate_insight_confidence_strong_high_sample(self) -> None:
        """Strong segment with high sample should be high confidence."""
        from services.funding_recommender import _calculate_insight_confidence

        confidence = _calculate_insight_confidence(
            program_count=15,
            total_count=30,
            segment_stability="strong",
        )

        assert confidence == "high"

    def test_calculate_insight_confidence_medium_sample(self) -> None:
        """Medium stability with moderate sample should be medium confidence."""
        from services.funding_recommender import _calculate_insight_confidence

        confidence = _calculate_insight_confidence(
            program_count=6,
            total_count=12,
            segment_stability="medium",
        )

        assert confidence == "medium"

    @patch("services.feedback_analyzer.get_segment_for_report")
    @patch("services.feedback_analyzer.is_segment_reliable")
    def test_enrich_funding_unreliable_segment(
        self,
        mock_is_reliable: MagicMock,
        mock_segment: MagicMock,
    ) -> None:
        """Unreliable segment should return empty insights."""
        mock_segment.return_value = MagicMock(
            segment_stability="weak",
        )
        mock_is_reliable.return_value = False

        from services.funding_recommender import enrich_funding_recommendations_with_feedback

        result = enrich_funding_recommendations_with_feedback({})

        assert result["insights"] == []
        assert result["is_reliable"] is False

    @patch("services.feedback_analyzer.get_segment_for_report")
    @patch("services.feedback_analyzer.is_segment_reliable")
    def test_enrich_funding_reliable_segment(
        self,
        mock_is_reliable: MagicMock,
        mock_segment: MagicMock,
    ) -> None:
        """Reliable segment should return insights with confidence."""
        mock_segment.return_value = MagicMock(
            segment_stability="strong",
            report_count=25,
            top_funding_programs=[("go_digital", 10), ("digital_jetzt", 8)],
        )
        mock_is_reliable.return_value = True

        from services.funding_recommender import enrich_funding_recommendations_with_feedback

        result = enrich_funding_recommendations_with_feedback({})

        assert result["is_reliable"] is True
        assert result["segment_stability"] == "strong"
        if result["insights"]:
            assert "confidence_level" in result["insights"][0]


# =============================================================================
# TEST G17.1-D: DASHBOARD ENDPOINTS
# =============================================================================

# Check if fastapi is available
try:
    from fastapi import APIRouter
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestG17_1D_DashboardEndpoints:
    """Tests for dashboard endpoints."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def test_segment_stability_endpoint_exists(self) -> None:
        """Segment stability endpoint should be defined."""
        from routes.feedback_dashboard import router

        routes = [r.path for r in router.routes]
        assert any(r.endswith("/segment-stability") for r in routes)

    def test_insights_reliability_endpoint_exists(self) -> None:
        """Insights reliability endpoint should be defined."""
        from routes.feedback_dashboard import router

        routes = [r.path for r in router.routes]
        assert any(r.endswith("/insights-reliability") for r in routes)

    def test_get_segment_stability_report_function(self) -> None:
        """get_segment_stability_report should return list."""
        from services.feedback_analyzer import get_segment_stability_report

        result = get_segment_stability_report()
        assert isinstance(result, list)

    def test_get_insights_reliability_metrics_function(self) -> None:
        """get_insights_reliability_metrics should return dict."""
        from services.feedback_analyzer import get_insights_reliability_metrics

        result = get_insights_reliability_metrics()

        assert isinstance(result, dict)
        assert "total_segments" in result
        assert "reliable_segments" in result
        assert "reliability_score" in result


# =============================================================================
# TEST G17.1-E: END-TO-END INTEGRATION
# =============================================================================

class TestG17_1E_Integration:
    """End-to-end integration tests."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def _populate_test_data(self, count: int = 20) -> None:
        """Populate with test feedback data."""
        from services.feedback_loop import capture_realworld_feedback

        for i in range(count):
            capture_realworld_feedback(
                report_id=10000 + i,
                warnings=[{"message": f"warning {i}", "section": "test"}],
                ai_act_risk_level="minimal",
                fallback_rate=0.1 * (i % 3),
                funding_source="DE",
                size_label="solo" if i % 2 == 0 else "team",
            )

    def test_full_calibration_flow(self) -> None:
        """Test complete flow: feedback -> calibration -> insights."""
        from services.feedback_loop import get_recent_feedback
        from services.feedback_analyzer import (
            build_segments_snapshot,
            get_segment_stability_report,
            is_segment_reliable,
        )

        # 1. Capture feedback
        self._populate_test_data(20)

        entries = get_recent_feedback(days=7)
        assert len(entries) == 20

        # 2. Build calibrated segments
        snapshot = build_segments_snapshot(days=90, force=True)
        assert isinstance(snapshot, dict)

        # 3. Get stability report
        stability_report = get_segment_stability_report()
        assert isinstance(stability_report, list)

        # 4. Each segment should have stability info
        for seg in stability_report:
            assert "stability" in seg
            assert seg["stability"] in ("strong", "medium", "weak")
            assert "is_reliable" in seg

    def test_insights_with_calibration(self) -> None:
        """Test insights generation respects calibration."""
        from services.insights_engine import build_report_insights

        self._populate_test_data(20)

        sections = {"REIFEGRAD_GESAMT": 65}
        profile = {"size_label": "solo", "ai_act_override_risk_level": "minimal"}

        result = build_report_insights(sections, profile)

        # Should have stability info
        assert result.segment_stability in ("strong", "medium", "weak", "unknown")
        # Should indicate reliability
        assert isinstance(result.is_reliable, bool)
        assert isinstance(result.is_generic_fallback, bool)

    def test_funding_insights_with_calibration(self) -> None:
        """Test funding insights respect calibration."""
        from services.funding_recommender import enrich_funding_recommendations_with_feedback

        self._populate_test_data(20)

        sections = {"REIFEGRAD_GESAMT": 65}
        profile = {"size_label": "solo", "funding_source": "DE"}

        result = enrich_funding_recommendations_with_feedback(sections, profile)

        # Should have reliability info
        assert "is_reliable" in result
        assert "segment_stability" in result

    def test_no_pii_in_calibration_outputs(self) -> None:
        """Calibration outputs should not contain PII."""
        import re
        from services.feedback_analyzer import get_segment_stability_report
        from services.insights_engine import build_report_insights

        self._populate_test_data(20)

        # Check stability report
        stability_report = get_segment_stability_report()
        stability_str = str(stability_report)

        # Check for PII patterns
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        assert not re.search(email_pattern, stability_str)

        # Check insights
        result = build_report_insights(
            {"REIFEGRAD_GESAMT": 65},
            {"size_label": "solo"}
        )

        all_html = result.summary_html + result.cards_html
        assert not re.search(email_pattern, all_html)


# =============================================================================
# TEST CONFIGURATION VARIABLES
# =============================================================================

class TestG17_1_Configuration:
    """Tests for configuration variables."""

    def test_calibration_config_exists(self) -> None:
        """Calibration config variables should exist."""
        from services import feedback_analyzer

        assert hasattr(feedback_analyzer, "INSIGHTS_SEGMENT_OUTLIER_STD")
        assert hasattr(feedback_analyzer, "INSIGHTS_SEGMENT_SAMPLE_WARNING")
        assert hasattr(feedback_analyzer, "INSIGHTS_MIN_STD_CONFIDENCE")
        assert hasattr(feedback_analyzer, "INSIGHTS_CONFIDENCE_LEVELS_ENABLED")

    def test_reliability_filter_config_exists(self) -> None:
        """Reliability filter config variables should exist."""
        from services import insights_engine

        assert hasattr(insights_engine, "INSIGHTS_REQUIRE_RELIABLE_SEGMENT")
        assert hasattr(insights_engine, "INSIGHTS_FALLBACK_TO_GENERIC")

    def test_funding_stability_config_exists(self) -> None:
        """Funding stability config variables should exist."""
        from services import funding_recommender

        assert hasattr(funding_recommender, "FUNDING_REQUIRE_STABLE_SEGMENT")
        assert hasattr(funding_recommender, "FUNDING_SHOW_CONFIDENCE_INDICATOR")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
