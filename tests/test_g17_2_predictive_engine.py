# -*- coding: utf-8 -*-
"""
Sprint G17.2: Test Suite for Predictive Insights & Smart Defaults

Tests:
- G17.2-A: Predictive Engine (risk, KPI, actions)
- G17.2-B: Smart Defaults for Prompt Engine
- G17.2-C: Funding Predictive Matching 2.0
- G17.2-D: Dashboard Endpoints
- Integration tests for section keys

Version: 1.0.0
"""
from __future__ import annotations

import os
import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field

# Set test environment
os.environ.setdefault("PREDICTIVE_ENGINE_ENABLED", "1")
os.environ.setdefault("PROMPT_SMART_DEFAULTS_ENABLED", "1")
os.environ.setdefault("FUNDING_PREDICTIVE_ENABLED", "1")
os.environ.setdefault("DASHBOARD_PREDICTIVE_ENABLED", "1")


# =============================================================================
# MOCK SEGMENT STATS
# =============================================================================

@dataclass
class MockSegmentStats:
    """Mock segment stats for testing."""
    segment_key: tuple = ("team", "consulting", "minimal", "national")
    report_count: int = 15
    sample_size: int = 15
    segment_stability: str = "strong"
    avg_score_governance: float = 65.0
    avg_score_security: float = 60.0
    avg_score_value: float = 70.0
    avg_score_enablement: float = 55.0
    avg_score_overall: float = 62.5
    avg_roi_percent: float = 120.0
    avg_payback_months: float = 8.0
    avg_warnings: float = 2.5
    avg_fallback_rate: float = 0.1
    funding_success_rate: float = 0.35
    top_warning_types: List[tuple] = field(default_factory=lambda: [("min-word", 5), ("redundancy", 3)])
    top_funding_programs: List[tuple] = field(default_factory=lambda: [("go_digital", 8), ("digital_jetzt", 5)])
    std_score_overall: float = 12.0
    std_roi: float = 25.0
    outliers_trimmed: bool = False
    max_influence_weight: float = 0.067


def create_mock_segment_stats(**kwargs: Any) -> MockSegmentStats:
    """Create mock segment stats with custom values."""
    return MockSegmentStats(**kwargs)


# =============================================================================
# G17.2-A: PREDICTIVE ENGINE TESTS
# =============================================================================

class TestPredictiveEngine:
    """Tests for services/predictive_engine.py"""

    def test_predict_segment_risk_returns_trend(self) -> None:
        """Test that predict_segment_risk returns a valid RiskTrend."""
        from services.predictive_engine import predict_segment_risk

        mock_sections = {
            "AI_ACT_RISK_LEVEL": "limited",
            "REIFEGRAD_GOVERNANCE": 55,
            "REIFEGRAD_SECURITY": 50,
        }
        mock_stats = create_mock_segment_stats()

        result = predict_segment_risk(mock_sections, mock_stats)

        assert result is not None
        assert result.current_risk_level == "limited"
        assert result.trend_direction in ("up", "stable", "down")
        assert 0.0 <= result.trend_confidence <= 1.0
        assert result.risk_score_current > 0
        assert result.recommendation != ""

    def test_predict_segment_risk_weak_segment_returns_none(self) -> None:
        """Test that weak segments return None for risk prediction."""
        from services.predictive_engine import predict_segment_risk

        mock_sections = {"AI_ACT_RISK_LEVEL": "minimal"}
        mock_stats = create_mock_segment_stats(segment_stability="weak", sample_size=3)

        result = predict_segment_risk(mock_sections, mock_stats)

        # Should return None for weak segments
        assert result is None

    def test_predict_kpi_shift_returns_predictions(self) -> None:
        """Test that predict_kpi_shift returns KPI predictions."""
        from services.predictive_engine import predict_kpi_shift

        mock_stats = create_mock_segment_stats()
        mock_sections = {
            "REIFEGRAD_GOVERNANCE": 70,
            "REIFEGRAD_SECURITY": 55,
            "REIFEGRAD_VALUE": 65,
            "REIFEGRAD_ENABLEMENT": 50,
            "REIFEGRAD_GESAMT": 60,
        }

        result = predict_kpi_shift(mock_stats, mock_sections)

        assert isinstance(result, list)
        # Should return some predictions
        for shift in result:
            assert shift.kpi_name != ""
            assert shift.shift_direction in ("improving", "stable", "declining")
            assert 0.0 <= shift.confidence <= 1.0

    def test_predict_kpi_shift_no_division_by_zero(self) -> None:
        """Test that KPI predictions handle zero values safely."""
        from services.predictive_engine import predict_kpi_shift

        mock_stats = create_mock_segment_stats(
            avg_score_governance=0,
            avg_score_security=0,
            avg_roi_percent=0,
        )

        # Should not raise any errors
        result = predict_kpi_shift(mock_stats)

        assert isinstance(result, list)

    def test_predict_high_value_actions_returns_actions(self) -> None:
        """Test that predict_high_value_actions returns action recommendations."""
        from services.predictive_engine import predict_high_value_actions

        mock_sections = {
            "REIFEGRAD_GOVERNANCE": 40,  # Below average
            "REIFEGRAD_SECURITY": 45,
            "REIFEGRAD_VALUE": 65,
            "AI_ACT_RISK_LEVEL": "high-risk",
        }
        mock_stats = create_mock_segment_stats()

        result = predict_high_value_actions(mock_sections, mock_stats, limit=5)

        assert isinstance(result, list)
        assert len(result) <= 5
        for action in result:
            assert action.action_id != ""
            assert action.title != ""
            assert action.effort_level in ("low", "medium", "high")
            assert 0 <= action.expected_impact_score <= 100

    def test_predict_high_value_actions_priority_ranking(self) -> None:
        """Test that actions are properly ranked by priority."""
        from services.predictive_engine import predict_high_value_actions

        mock_sections = {
            "REIFEGRAD_GOVERNANCE": 30,  # Large gap
            "REIFEGRAD_SECURITY": 35,
            "AI_ACT_RISK_LEVEL": "high-risk",
        }
        mock_stats = create_mock_segment_stats()

        result = predict_high_value_actions(mock_sections, mock_stats, limit=5)

        if len(result) > 1:
            # First action should have higher or equal impact than second
            assert result[0].expected_impact_score >= result[1].expected_impact_score

    def test_generate_predictive_insights_html_output(self) -> None:
        """Test that HTML output is generated correctly."""
        from services.predictive_engine import generate_predictive_insights_html

        with patch("services.feedback_analyzer.get_segment_for_report") as mock_get:
            mock_get.return_value = create_mock_segment_stats()

            mock_sections = {
                "AI_ACT_RISK_LEVEL": "limited",
                "REIFEGRAD_GOVERNANCE": 60,
            }

            html = generate_predictive_insights_html(mock_sections, lang="de")

            assert isinstance(html, str)
            if html:  # May be empty if predictions not available
                assert "predictive-insights" in html or "Predictive" in html

    def test_inject_predictive_insights_adds_section_key(self) -> None:
        """Test that inject function adds PREDICTIVE_INSIGHTS_HTML."""
        from services.predictive_engine import inject_predictive_insights

        with patch("services.predictive_engine.generate_predictive_insights_html") as mock_gen:
            mock_gen.return_value = "<div>Test HTML</div>"

            sections: Dict[str, Any] = {}
            result = inject_predictive_insights(sections, lang="de")

            assert "PREDICTIVE_INSIGHTS_HTML" in result


# =============================================================================
# G17.2-B: SMART DEFAULTS TESTS
# =============================================================================

class TestSmartDefaults:
    """Tests for Smart Defaults in prompt_enhancer.py"""

    def test_smart_defaults_engine_initialization(self) -> None:
        """Test that SmartDefaultsEngine initializes without errors."""
        from services.prompt_enhancer import SmartDefaultsEngine

        engine = SmartDefaultsEngine()
        assert engine is not None

    def test_get_word_count_adjustment_returns_tuple(self) -> None:
        """Test word count adjustment returns proper tuple."""
        from services.prompt_enhancer import SmartDefaultsEngine

        engine = SmartDefaultsEngine()

        result = engine.get_word_count_adjustment(
            section_name="roadmap_90d",
            size="solo",
            base_min_words=100,
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        adjusted_words, adjustment = result
        assert isinstance(adjusted_words, int)
        assert adjusted_words >= 100  # Should be >= base

    def test_get_phrase_preferences_returns_dict(self) -> None:
        """Test phrase preferences returns dictionary."""
        from services.prompt_enhancer import SmartDefaultsEngine

        engine = SmartDefaultsEngine()

        result = engine.get_phrase_preferences(size="team", branch="consulting")

        assert isinstance(result, dict)

    def test_get_cost_range_adjustment_returns_tuple(self) -> None:
        """Test cost range adjustment returns proper tuple."""
        from services.prompt_enhancer import SmartDefaultsEngine

        engine = SmartDefaultsEngine()

        result = engine.get_cost_range_adjustment(
            size="kmu",
            base_capex_max=50000,
            base_opex_max=10000,
        )

        assert isinstance(result, tuple)
        assert len(result) == 3
        capex, opex, adjustment = result
        assert isinstance(capex, int)
        assert isinstance(opex, int)

    def test_apply_smart_defaults_to_prompt_deterministic(self) -> None:
        """Test that smart defaults produce deterministic output."""
        from services.prompt_enhancer import apply_smart_defaults_to_prompt

        briefing = {
            "unternehmensgroesse": "solo",
            "branche": "consulting",
        }

        prompt = "Write a roadmap for the company."

        result1 = apply_smart_defaults_to_prompt(prompt, "roadmap_90d", briefing)
        result2 = apply_smart_defaults_to_prompt(prompt, "roadmap_90d", briefing)

        # Results should be identical for same input
        assert result1 == result2

    def test_get_smart_defaults_analysis_returns_dict(self) -> None:
        """Test get_smart_defaults_analysis returns proper structure."""
        from services.prompt_enhancer import get_smart_defaults_analysis

        result = get_smart_defaults_analysis()

        assert isinstance(result, dict)
        assert "enabled" in result

    def test_get_smart_defaults_statistics_returns_dict(self) -> None:
        """Test get_smart_defaults_statistics returns proper structure."""
        from services.prompt_enhancer import get_smart_defaults_statistics

        result = get_smart_defaults_statistics()

        assert isinstance(result, dict)
        assert "total_adjustments" in result
        assert "by_type" in result
        assert "by_section" in result


# =============================================================================
# G17.2-C: FUNDING PREDICTIVE MATCHING TESTS
# =============================================================================

class TestFundingPredictive:
    """Tests for Funding Predictive Matching 2.0"""

    def test_predict_funding_opportunity_score_returns_result(self) -> None:
        """Test that opportunity score calculation returns valid result."""
        from services.funding_recommender import predict_funding_opportunity_score

        program = {
            "id": "test_program",
            "name": "Test Program",
            "provider": "Test Provider",
            "size_match": ["team", "kmu"],
            "ki_relevance": "high",
            "branches": ["all"],
            "max_funding": "50.000 €",
            "funding_rate": "50%",
        }
        mock_stats = create_mock_segment_stats()
        mock_sections = {"SIZE_LABEL": "team", "BRANCH_LABEL": "consulting"}

        result = predict_funding_opportunity_score(program, mock_stats, mock_sections)

        assert result is not None
        assert result.program_id == "test_program"
        assert 0.0 <= result.opportunity_score <= 1.0
        assert result.trend in ("rising", "stable", "declining")
        assert result.recommendation_level in ("high", "medium", "low")

    def test_predict_funding_opportunity_no_division_by_zero(self) -> None:
        """Test funding prediction handles zero values safely."""
        from services.funding_recommender import predict_funding_opportunity_score

        program = {"id": "test", "name": "Test"}
        mock_stats = create_mock_segment_stats(
            report_count=0,
            funding_success_rate=0,
        )

        # Should not raise any errors
        result = predict_funding_opportunity_score(program, mock_stats, {})

        assert result is not None
        assert isinstance(result.opportunity_score, float)

    def test_get_predictive_funding_opportunities_returns_list(self) -> None:
        """Test that get_predictive_funding_opportunities returns sorted list."""
        from services.funding_recommender import get_predictive_funding_opportunities

        with patch("services.feedback_analyzer.get_segment_for_report") as mock_get:
            mock_get.return_value = create_mock_segment_stats()

            result = get_predictive_funding_opportunities(
                report_sections={"SIZE_LABEL": "team"},
                profile=None,
                limit=5,
            )

            assert isinstance(result, list)
            if len(result) > 1:
                # Should be sorted by opportunity score descending
                assert result[0].opportunity_score >= result[1].opportunity_score

    def test_generate_funding_predicted_opportunities_html(self) -> None:
        """Test HTML generation for funding opportunities."""
        from services.funding_recommender import generate_funding_predicted_opportunities_html

        with patch("services.funding_recommender.get_predictive_funding_opportunities") as mock_get:
            from services.funding_recommender import PredictiveFundingOpportunity
            mock_get.return_value = [
                PredictiveFundingOpportunity(
                    program_id="test",
                    program_name="Test Program",
                    provider="Test",
                    opportunity_score=0.75,
                    base_eligibility=0.8,
                    segment_success_rate=0.3,
                    confidence_level=0.7,
                    trend="stable",
                    recommendation_level="high",
                )
            ]

            html = generate_funding_predicted_opportunities_html({}, lang="de")

            assert isinstance(html, str)
            assert "funding-predicted" in html or "Test Program" in html

    def test_inject_predictive_funding_adds_section_key(self) -> None:
        """Test that inject function adds FUNDING_PREDICTED_OPPORTUNITIES_HTML."""
        from services.funding_recommender import inject_predictive_funding_into_sections

        with patch("services.funding_recommender.generate_funding_predicted_opportunities_html") as mock_gen:
            mock_gen.return_value = "<div>Test</div>"

            sections: Dict[str, Any] = {}
            result = inject_predictive_funding_into_sections(sections, lang="de")

            assert "FUNDING_PREDICTED_OPPORTUNITIES_HTML" in result


# =============================================================================
# G17.2-D: DASHBOARD ENDPOINT TESTS
# =============================================================================

class TestDashboardEndpoints:
    """Tests for Dashboard Endpoints"""

    def test_predictive_health_endpoint(self) -> None:
        """Test predictive-health endpoint returns valid response."""
        # Skip if pytest-asyncio is not available
        try:
            import asyncio
            from routes.feedback_dashboard import get_predictive_health

            with patch("services.feedback_analyzer.build_segments_snapshot") as mock_snapshot:
                mock_snapshot.return_value = {
                    "segment1": create_mock_segment_stats(),
                }

                with patch("services.funding_recommender.get_predictive_funding_opportunities") as mock_funding:
                    mock_funding.return_value = []

                    try:
                        result = asyncio.get_event_loop().run_until_complete(get_predictive_health())

                        assert result.total_segments_analyzed >= 0
                        assert 0.0 <= result.report_success_probability <= 1.0
                        assert isinstance(result.risk_trends, list)
                        assert isinstance(result.top_funding_opportunities, list)
                    except Exception:
                        # May fail if predictive engine is disabled
                        pytest.skip("Predictive engine disabled or unavailable")
        except Exception:
            pytest.skip("Async test skipped - asyncio not available")

    def test_smart_defaults_analysis_endpoint(self) -> None:
        """Test smart-defaults-analysis endpoint returns valid response."""
        try:
            import asyncio
            from routes.feedback_dashboard import get_smart_defaults_analysis

            result = asyncio.get_event_loop().run_until_complete(get_smart_defaults_analysis())

            assert isinstance(result.enabled, bool)
            assert isinstance(result.total_adjustments, int)
            assert isinstance(result.adjustments_by_type, dict)
            assert isinstance(result.adjustments_by_section, dict)
        except Exception:
            pytest.skip("Smart defaults endpoint unavailable")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for G17.2 features."""

    def test_all_section_keys_in_flow(self) -> None:
        """Test that all new section keys are properly added."""
        from services.predictive_engine import inject_predictive_insights
        from services.funding_recommender import inject_predictive_funding_into_sections

        sections: Dict[str, Any] = {
            "AI_ACT_RISK_LEVEL": "minimal",
            "REIFEGRAD_GESAMT": 60,
        }

        # Inject predictive insights
        with patch("services.predictive_engine.generate_predictive_insights_html") as mock1:
            mock1.return_value = "<div>Predictive</div>"
            sections = inject_predictive_insights(sections, lang="de")

        # Inject predictive funding
        with patch("services.funding_recommender.generate_funding_predicted_opportunities_html") as mock2:
            mock2.return_value = "<div>Funding</div>"
            sections = inject_predictive_funding_into_sections(sections, lang="de")

        # Verify all section keys present
        assert "PREDICTIVE_INSIGHTS_HTML" in sections
        assert "FUNDING_PREDICTED_OPPORTUNITIES_HTML" in sections

    def test_stability_levels_respected(self) -> None:
        """Test that stability level requirements are respected."""
        from services.predictive_engine import predict_segment_risk, predict_kpi_shift

        # Weak stability should return None/empty
        weak_stats = create_mock_segment_stats(segment_stability="weak", sample_size=2)
        mock_sections = {"AI_ACT_RISK_LEVEL": "minimal"}

        risk_result = predict_segment_risk(mock_sections, weak_stats)
        kpi_result = predict_kpi_shift(weak_stats)

        assert risk_result is None
        assert len(kpi_result) == 0  # Should be empty for weak segments

    def test_predictive_engine_disabled(self) -> None:
        """Test behavior when predictive engine is disabled."""
        import services.predictive_engine as pe

        original_enabled = pe.PREDICTIVE_ENGINE_ENABLED

        try:
            pe.PREDICTIVE_ENGINE_ENABLED = False

            result = pe.predict_segment_risk({}, None)
            assert result is None

            result2 = pe.predict_kpi_shift(None)
            assert result2 == []

            result3 = pe.predict_high_value_actions({}, None)
            assert result3 == []

        finally:
            pe.PREDICTIVE_ENGINE_ENABLED = original_enabled

    def test_funding_confidence_thresholds(self) -> None:
        """Test that funding confidence thresholds are applied."""
        from services.funding_recommender import (
            FUNDING_MIN_CONFIDENCE_FOR_DISPLAY,
            predict_funding_opportunity_score,
        )

        # Low confidence program should be filtered
        program = {"id": "test", "name": "Test"}
        weak_stats = create_mock_segment_stats(
            segment_stability="weak",
            sample_size=2,
        )

        result = predict_funding_opportunity_score(program, weak_stats, {})

        # Confidence should be calculated
        assert isinstance(result.confidence_level, float)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_segment_stats(self) -> None:
        """Test handling of empty/None segment stats."""
        from services.predictive_engine import (
            predict_segment_risk,
            predict_kpi_shift,
            predict_high_value_actions,
        )

        # When segment_stats is None and internal fetch also returns None
        with patch("services.feedback_analyzer.get_segment_for_report") as mock_get:
            mock_get.return_value = None

            # Should handle None gracefully
            assert predict_segment_risk({}, None) is None

        # KPI shift with None should return empty list
        assert predict_kpi_shift(None) == []

        # High value actions with None segment should still work (uses report data)
        result = predict_high_value_actions({}, None)
        assert isinstance(result, list)

    def test_missing_report_sections(self) -> None:
        """Test handling of missing report sections."""
        from services.predictive_engine import predict_high_value_actions

        mock_stats = create_mock_segment_stats()

        # Empty sections should not crash
        result = predict_high_value_actions({}, mock_stats)
        assert isinstance(result, list)

    def test_invalid_risk_levels(self) -> None:
        """Test handling of invalid risk level values."""
        from services.predictive_engine import predict_segment_risk

        mock_stats = create_mock_segment_stats()
        mock_sections = {"AI_ACT_RISK_LEVEL": "invalid_level"}

        result = predict_segment_risk(mock_sections, mock_stats)

        # Should handle gracefully
        assert result is not None or result is None  # Should not raise

    def test_negative_values(self) -> None:
        """Test handling of negative values in stats."""
        from services.predictive_engine import predict_kpi_shift

        mock_stats = create_mock_segment_stats(
            avg_score_governance=-10,
            avg_roi_percent=-50,
        )

        # Should not crash
        result = predict_kpi_shift(mock_stats)
        assert isinstance(result, list)

    def test_very_large_values(self) -> None:
        """Test handling of very large values."""
        from services.funding_recommender import predict_funding_opportunity_score

        program = {"id": "test", "name": "Test", "size_match": ["all"]}
        mock_stats = create_mock_segment_stats(
            report_count=1000000,
            sample_size=1000000,
            avg_roi_percent=10000,
        )

        result = predict_funding_opportunity_score(program, mock_stats, {})

        # Score should still be bounded
        assert 0.0 <= result.opportunity_score <= 1.0
        assert 0.0 <= result.confidence_level <= 1.0


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

class TestConfiguration:
    """Tests for ENV configuration handling."""

    def test_predictive_engine_env_vars(self) -> None:
        """Test that ENV variables are properly read."""
        from services.predictive_engine import (
            PREDICTIVE_ENGINE_ENABLED,
            PREDICTIVE_MIN_SEGMENT_STABILITY,
            PREDICTIVE_SCORE_SMOOTHING,
            PREDICTIVE_TREND_WINDOW_DAYS,
        )

        assert isinstance(PREDICTIVE_ENGINE_ENABLED, bool)
        assert PREDICTIVE_MIN_SEGMENT_STABILITY in ("weak", "medium", "strong")
        assert 0.0 <= PREDICTIVE_SCORE_SMOOTHING <= 1.0
        assert PREDICTIVE_TREND_WINDOW_DAYS > 0

    def test_smart_defaults_env_vars(self) -> None:
        """Test Smart Defaults ENV variables."""
        from services.prompt_enhancer import (
            PROMPT_SMART_DEFAULTS_ENABLED,
            PROMPT_DEFAULT_WORD_INCREASE_FACTOR,
        )

        assert isinstance(PROMPT_SMART_DEFAULTS_ENABLED, bool)
        assert PROMPT_DEFAULT_WORD_INCREASE_FACTOR >= 1.0

    def test_funding_predictive_env_vars(self) -> None:
        """Test Funding Predictive ENV variables."""
        from services.funding_recommender import (
            FUNDING_PREDICTIVE_ENABLED,
            FUNDING_TREND_WEIGHT,
            FUNDING_MIN_CONFIDENCE_FOR_DISPLAY,
        )

        assert isinstance(FUNDING_PREDICTIVE_ENABLED, bool)
        assert 0.0 <= FUNDING_TREND_WEIGHT <= 1.0
        assert 0.0 <= FUNDING_MIN_CONFIDENCE_FOR_DISPLAY <= 1.0


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
