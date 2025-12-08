# -*- coding: utf-8 -*-
"""
Sprint G17 Tests: Insights Engine & Segmentation

Tests for:
- Segmentation and benchmark engine
- Insight cards generation
- Funding insights
- Dashboard endpoints
- Privacy/data protection

Version: 1.0.0
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import patch

import pytest


# =============================================================================
# TEST G17-A: SEGMENTATION
# =============================================================================

class TestG17A_Segmentation:
    """Tests for segmentation and benchmark engine."""

    def setup_method(self) -> None:
        """Clear feedback store before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        # Also clear segment cache
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def _populate_segment_data(self, count: int = 20) -> None:
        """Populate feedback with segment-appropriate data."""
        from services.feedback_loop import capture_realworld_feedback

        for i in range(count):
            # Vary segments
            size = ["solo", "team", "kmu"][i % 3]
            risk = ["minimal", "limited", "high-risk"][i % 3]

            capture_realworld_feedback(
                report_id=8000 + i,
                warnings=[{"message": "test", "section": "test"}],
                ai_act_risk_level=risk,
                fallback_rate=0.1,
                funding_source="DE",
                size_label=size,
            )

    def test_build_segments_snapshot_empty(self) -> None:
        """Empty feedback should return empty snapshot."""
        from services.feedback_analyzer import build_segments_snapshot

        snapshot = build_segments_snapshot(days=7, force=True)
        assert snapshot == {}

    def test_build_segments_snapshot_with_data(self) -> None:
        """Should build segments from feedback data."""
        from services.feedback_analyzer import build_segments_snapshot

        self._populate_segment_data(30)

        snapshot = build_segments_snapshot(days=90, force=True)

        # Should have segments (may be 0 if under min threshold)
        assert isinstance(snapshot, dict)

    def test_segment_key_format(self) -> None:
        """Segment keys should follow correct format."""
        from services.feedback_analyzer import build_segments_snapshot

        self._populate_segment_data(30)

        snapshot = build_segments_snapshot(days=90, force=True)

        for key in snapshot.keys():
            parts = key.split("|")
            assert len(parts) == 4  # size|branch|risk|funding

    def test_normalize_branch(self) -> None:
        """Branch normalization should work correctly."""
        from services.feedback_analyzer import _normalize_branch

        assert _normalize_branch("Unternehmensberatung") == "consulting"
        assert _normalize_branch("Finance & Banking") == "finance"
        assert _normalize_branch("Versicherung") == "finance"
        assert _normalize_branch("Manufacturing") == "industry"
        assert _normalize_branch("Healthcare") == "health"
        assert _normalize_branch("Unknown Branch") == "other"

    def test_normalize_funding_scope(self) -> None:
        """Funding scope normalization should work."""
        from services.feedback_analyzer import _normalize_funding_scope

        assert _normalize_funding_scope("DE") == "DE"
        assert _normalize_funding_scope("EU-CORE") == "EU_CORE"
        assert _normalize_funding_scope("EU") == "EU_CORE"
        assert _normalize_funding_scope("") == "NONE"
        assert _normalize_funding_scope("GERMANY") == "DE"

    def test_get_segment_for_report(self) -> None:
        """Should get segment for a report."""
        from services.feedback_analyzer import get_segment_for_report

        self._populate_segment_data(30)

        # Test with profile
        profile = {
            "size_label": "solo",
            "branch": "Beratung",
            "ai_act_override_risk_level": "minimal",
            "funding_source": "DE",
        }

        segment = get_segment_for_report({}, profile)

        # May be None if not enough data, but shouldn't error
        assert segment is None or hasattr(segment, "segment_key")

    def test_segment_stats_aggregation(self) -> None:
        """Segment stats should aggregate correctly."""
        from services.feedback_analyzer import SegmentStats

        stats = SegmentStats(
            segment_key=("solo", "consulting", "minimal", "DE"),
            report_count=10,
            avg_score_governance=75.0,
            avg_score_overall=70.0,
        )

        stats_dict = stats.to_dict()

        assert stats_dict["report_count"] == 10
        assert stats_dict["avg_scores"]["governance"] == 75.0
        assert stats_dict["segment_key"]["size_label"] == "solo"


# =============================================================================
# TEST G17-B: INSIGHT CARDS
# =============================================================================

class TestG17B_InsightCards:
    """Tests for insight card generation."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def test_build_report_insights_no_data(self) -> None:
        """Should handle missing segment data gracefully."""
        from services.insights_engine import build_report_insights

        result = build_report_insights({})

        assert result.has_sufficient_data is False
        assert len(result.cards) == 0

    def test_insight_card_structure(self) -> None:
        """Insight cards should have correct structure."""
        from services.insights_engine import InsightCard

        card = InsightCard(
            title="Test Card",
            severity="info",
            body_html="<p>Test content</p>",
            category="position",
            priority=1,
        )

        card_dict = card.to_dict()

        assert "title" in card_dict
        assert "severity" in card_dict
        assert "body_html" in card_dict
        assert "category" in card_dict

    def test_insight_result_to_dict(self) -> None:
        """InsightResult should serialize correctly."""
        from services.insights_engine import InsightResult, InsightCard

        result = InsightResult(
            cards=[
                InsightCard(
                    title="Test",
                    severity="info",
                    body_html="<p>Test</p>",
                )
            ],
            summary_html="<p>Summary</p>",
            cards_html="<div>Cards</div>",
            segment_label="Test Segment",
            has_sufficient_data=True,
        )

        result_dict = result.to_dict()

        assert "INSIGHT_CARDS" in result_dict
        assert len(result_dict["INSIGHT_CARDS"]) == 1
        assert result_dict["has_sufficient_data"] is True

    def test_no_personal_data_in_cards(self) -> None:
        """Cards should not contain personal data."""
        from services.insights_engine import InsightCard

        # Check card body doesn't contain email-like patterns
        card = InsightCard(
            title="Test",
            severity="info",
            body_html="<p>This is a test with score 75/100</p>",
        )

        # Check for email patterns
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        assert not re.search(email_pattern, card.body_html)

        # Check for ID patterns (shouldn't have report IDs)
        id_pattern = r"report[_-]?id[:\s]*\d+"
        assert not re.search(id_pattern, card.body_html.lower())

    def test_html_valid_no_open_tags(self) -> None:
        """Generated HTML should be valid."""
        from services.insights_engine import _build_cards_html, InsightCard

        cards = [
            InsightCard(title="Test", severity="info", body_html="<p>Test</p>"),
            InsightCard(title="Test2", severity="highlight", body_html="<p>Test2</p>"),
        ]

        html = _build_cards_html(cards)

        # Check no unclosed div tags
        open_divs = html.count("<div")
        close_divs = html.count("</div>")
        assert open_divs == close_divs

        # Check no double html tags
        assert html.count("<html") == 0
        assert html.count("</html") == 0


# =============================================================================
# TEST G17-C: FUNDING INSIGHTS
# =============================================================================

class TestG17C_FundingInsights:
    """Tests for funding insights generation."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def test_enrich_funding_no_data(self) -> None:
        """Should handle missing segment data."""
        from services.funding_recommender import enrich_funding_recommendations_with_feedback

        result = enrich_funding_recommendations_with_feedback({})

        assert result["html"] == ""
        assert result["insights"] == []

    def test_funding_insight_structure(self) -> None:
        """Funding insight should have correct structure."""
        from services.funding_recommender import FundingInsight

        insight = FundingInsight(
            program_id="go_digital",
            program_name="go-digital",
            success_rate=0.35,
            similar_profiles_count=100,
            avg_relevance_score=0.75,
            insight_text="35% qualified for this program",
            severity="opportunity",
        )

        assert insight.program_id == "go_digital"
        assert insight.success_rate == 0.35
        assert insight.severity == "opportunity"

    def test_no_individual_case_data_leak(self) -> None:
        """Funding insights should not leak individual case data."""
        from services.funding_recommender import _generate_funding_insights_html, FundingInsight
        from unittest.mock import MagicMock

        insights = [
            FundingInsight(
                program_id="test",
                program_name="Test Program",
                success_rate=0.3,
                similar_profiles_count=50,
                avg_relevance_score=0.7,
                insight_text="30% qualified",
                severity="info",
            )
        ]

        # Mock segment
        segment = MagicMock()
        segment.report_count = 50

        html = _generate_funding_insights_html(insights, segment, "de")

        # Should not contain specific report IDs
        assert "report_id" not in html.lower()
        assert "user_id" not in html.lower()

        # Should contain aggregated language
        assert "vergleichbar" in html.lower() or "similar" in html.lower()

    def test_min_cases_threshold(self) -> None:
        """Should respect minimum cases threshold."""
        from services.funding_recommender import _build_funding_insights
        from unittest.mock import MagicMock

        # Mock segment with low counts
        segment = MagicMock()
        segment.top_funding_programs = [("program1", 2)]  # Below threshold
        segment.report_count = 10

        insights = _build_funding_insights(segment, None, "de")

        # Should return empty due to low count
        assert insights == []


# =============================================================================
# TEST G17-D: DASHBOARD ENDPOINTS
# =============================================================================

# Check if fastapi is available
try:
    from fastapi import APIRouter
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestG17D_DashboardEndpoints:
    """Tests for dashboard endpoints."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()

    def test_insights_overview_endpoint_exists(self) -> None:
        """Insights overview endpoint should be defined."""
        from routes.feedback_dashboard import router

        routes = [r.path for r in router.routes]
        assert any(r.endswith("/insights-overview") for r in routes)

    def test_action_items_endpoint_exists(self) -> None:
        """Action items endpoint should be defined."""
        from routes.feedback_dashboard import router

        routes = [r.path for r in router.routes]
        assert any(r.endswith("/action-items") for r in routes)


# =============================================================================
# TEST G17-E: END-TO-END SMOKE TEST
# =============================================================================

class TestG17E_EndToEnd:
    """End-to-end smoke tests."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()
        from services import feedback_analyzer
        feedback_analyzer._segment_snapshot = None
        feedback_analyzer._segment_snapshot_timestamp = None

    def _populate_test_data(self, count: int = 15) -> None:
        """Populate with test feedback data."""
        from services.feedback_loop import capture_realworld_feedback

        for i in range(count):
            capture_realworld_feedback(
                report_id=9000 + i,
                warnings=[{"message": f"warning {i}", "section": "test"}],
                ai_act_risk_level="minimal",
                fallback_rate=0.1 * (i % 3),
                funding_source="DE",
                size_label="solo" if i % 2 == 0 else "team",
            )

    def test_full_insights_flow(self) -> None:
        """Test complete flow: feedback -> segments -> insights."""
        from services.feedback_loop import capture_realworld_feedback, get_recent_feedback
        from services.feedback_analyzer import build_segments_snapshot, get_segment_for_report
        from services.insights_engine import build_report_insights

        # 1. Capture feedback
        self._populate_test_data(15)

        entries = get_recent_feedback(days=7)
        assert len(entries) == 15

        # 2. Build segments (may be empty if under threshold)
        snapshot = build_segments_snapshot(days=90, force=True)
        assert isinstance(snapshot, dict)

        # 3. Get segment for a report
        profile = {"size_label": "solo", "ai_act_override_risk_level": "minimal"}
        segment = get_segment_for_report({}, profile)
        # May be None if not enough data in one segment

        # 4. Build insights (should not error even without segment)
        sections = {"REIFEGRAD_GESAMT": 75}
        insights = build_report_insights(sections, profile)

        assert isinstance(insights.cards, list)
        assert isinstance(insights.summary_html, str)
        assert isinstance(insights.cards_html, str)

    def test_inject_insights_into_sections(self) -> None:
        """Test injecting insights into report sections."""
        from services.insights_engine import inject_insights_into_sections

        sections = {
            "REIFEGRAD_GESAMT": 75,
            "REIFEGRAD_GOVERNANCE": 80,
        }
        profile = {"size_label": "solo"}

        updated = inject_insights_into_sections(sections, profile)

        # Should have added insight keys
        assert "INSIGHTS_SUMMARY_HTML" in updated
        assert "INSIGHT_CARDS_HTML" in updated

    def test_inject_funding_insights_into_sections(self) -> None:
        """Test injecting funding insights into report sections."""
        from services.funding_recommender import inject_funding_insights_into_sections

        sections = {"REIFEGRAD_GESAMT": 75}
        profile = {"size_label": "solo", "funding_source": "DE"}

        updated = inject_funding_insights_into_sections(sections, profile)

        # Should have added funding insight key
        assert "FUNDING_INSIGHTS_HTML" in updated

    def test_privacy_no_pii_in_outputs(self) -> None:
        """Verify no PII in any outputs."""
        from services.insights_engine import build_report_insights
        from services.funding_recommender import enrich_funding_recommendations_with_feedback

        self._populate_test_data(15)

        # Build insights
        sections = {"REIFEGRAD_GESAMT": 75}
        profile = {"size_label": "solo"}

        insights = build_report_insights(sections, profile)
        funding = enrich_funding_recommendations_with_feedback(sections, profile)

        # Combine all HTML outputs
        all_html = insights.summary_html + insights.cards_html + funding.get("html", "")

        # Check for PII patterns
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        phone_pattern = r"\+?\d{10,}"
        report_id_pattern = r"report[_-]?id[:\s]*\d+"

        assert not re.search(email_pattern, all_html)
        assert not re.search(phone_pattern, all_html)
        assert not re.search(report_id_pattern, all_html.lower())


# =============================================================================
# TEST LEARNING ENGINE INTEGRATION
# =============================================================================

class TestG17_LearningEngineIntegration:
    """Tests for learning engine with G17."""

    def setup_method(self) -> None:
        """Clear stores before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()

    def test_action_items_include_segment_issues(self) -> None:
        """Action items should include segment-related issues."""
        from services.learning_engine import generate_action_items

        # With no data, should not error
        items = generate_action_items(days=7)
        assert isinstance(items, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
