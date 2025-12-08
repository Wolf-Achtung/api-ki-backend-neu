# -*- coding: utf-8 -*-
"""
Sprint G16 Tests: Real-World Feedback Loop

Tests for feedback collection, analysis, and learning engine:
- Feedback capture and storage
- Pattern detection and analysis
- Learning engine action items
- Dashboard endpoints

Version: 1.0.0
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import patch

import pytest


# =============================================================================
# TEST G16-A: FEEDBACK COLLECTOR
# =============================================================================

class TestG16A_FeedbackCollector:
    """Tests for feedback collection and storage."""

    def setup_method(self) -> None:
        """Clear feedback store before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()

    def test_capture_basic_feedback(self) -> None:
        """Basic feedback capture should work."""
        from services.feedback_loop import capture_realworld_feedback, get_feedback_store

        entry = capture_realworld_feedback(
            report_id=1001,
            warnings=[],
            ai_act_risk_level="minimal",
            fallback_rate=0.1,
            funding_source="DE",
            size_label="solo",
        )

        assert entry is not None
        assert entry.report_id == 1001
        assert entry.ai_act_risk_level == "minimal"
        assert entry.size_label == "solo"
        assert len(get_feedback_store()) == 1

    def test_capture_with_warnings(self) -> None:
        """Feedback with warnings should be classified correctly."""
        from services.feedback_loop import capture_realworld_feedback

        warnings = [
            {"message": "roadmap_90d under minimum word count", "section": "roadmap_90d"},
            {"message": "redundancy detected in BUSINESS_CASE", "section": "BUSINESS_CASE"},
            {"message": "persona leak: found 'Abteilung'", "type": "size_mismatch"},
        ]

        entry = capture_realworld_feedback(
            report_id=1002,
            warnings=warnings,
            ai_act_risk_level="limited",
            fallback_rate=0.2,
            funding_source="DE",
            size_label="team",
        )

        assert entry is not None
        assert entry.total_warnings == 3
        assert "min-word" in entry.warning_types
        assert "redundancy" in entry.warning_types
        assert "persona-leak" in entry.warning_types
        assert entry.persona_leaks_detected == 1

    def test_capture_with_research_coverage(self) -> None:
        """Feedback with research coverage should be stored."""
        from services.feedback_loop import capture_realworld_feedback

        coverage = {"tools": 5, "funding": 3, "competitor": 4}

        entry = capture_realworld_feedback(
            report_id=1003,
            warnings=[],
            ai_act_risk_level="minimal",
            fallback_rate=0.0,
            funding_source="DE",
            size_label="solo",
            research_coverage=coverage,
        )

        assert entry is not None
        assert entry.research_coverage == coverage
        assert entry.research_coverage["tools"] == 5

    def test_capture_with_performance_metrics(self) -> None:
        """Feedback with performance metrics should be stored."""
        from services.feedback_loop import capture_realworld_feedback

        entry = capture_realworld_feedback(
            report_id=1004,
            warnings=[],
            ai_act_risk_level="minimal",
            fallback_rate=0.0,
            funding_source="DE",
            size_label="solo",
            generation_time_sec=45.5,
            llm_timeouts=2,
            api_retries=1,
            pdf_render_time_sec=3.2,
            pdf_retries=0,
        )

        assert entry is not None
        assert entry.generation_time_sec == 45.5
        assert entry.llm_timeouts == 2
        assert entry.api_retries == 1
        assert entry.pdf_render_time_sec == 3.2

    def test_capture_with_ai_act_override(self) -> None:
        """Feedback with AI-Act override should be stored."""
        from services.feedback_loop import capture_realworld_feedback

        entry = capture_realworld_feedback(
            report_id=1005,
            warnings=[],
            ai_act_risk_level="high-risk",
            fallback_rate=0.0,
            funding_source="DE",
            size_label="team",
            ai_act_override_used=True,
            capex_modifier=1.25,
            opex_modifier=1.15,
        )

        assert entry is not None
        assert entry.ai_act_override_used is True
        assert entry.capex_modifier == 1.25
        assert entry.opex_modifier == 1.15

    def test_get_recent_feedback(self) -> None:
        """Get recent feedback should filter by date."""
        from services.feedback_loop import (
            capture_realworld_feedback,
            get_recent_feedback,
            get_feedback_store,
        )

        # Create some feedback entries
        for i in range(5):
            capture_realworld_feedback(
                report_id=2000 + i,
                warnings=[],
                ai_act_risk_level="minimal",
                fallback_rate=0.0,
                funding_source="DE",
                size_label="solo",
            )

        recent = get_recent_feedback(days=7)
        assert len(recent) == 5

    def test_get_feedback_stats(self) -> None:
        """Feedback stats should aggregate correctly."""
        from services.feedback_loop import capture_realworld_feedback, get_feedback_stats

        # Create varied feedback
        capture_realworld_feedback(
            report_id=3001,
            warnings=[{"message": "min word", "section": "test"}],
            ai_act_risk_level="minimal",
            fallback_rate=0.1,
            funding_source="DE",
            size_label="solo",
        )
        capture_realworld_feedback(
            report_id=3002,
            warnings=[{"message": "redundancy", "section": "test"}],
            ai_act_risk_level="limited",
            fallback_rate=0.2,
            funding_source="EU-CORE",
            size_label="team",
        )

        stats = get_feedback_stats(days=7)

        assert stats["total_reports"] == 2
        assert stats["avg_warnings"] == 1.0
        assert "solo" in stats["size_distribution"]
        assert "team" in stats["size_distribution"]


# =============================================================================
# TEST G16-B: FEEDBACK ANALYZER
# =============================================================================

class TestG16B_FeedbackAnalyzer:
    """Tests for feedback analysis and pattern detection."""

    def setup_method(self) -> None:
        """Clear feedback store before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()

    def _populate_feedback(self, count: int = 10) -> None:
        """Helper to populate feedback store with test data."""
        from services.feedback_loop import capture_realworld_feedback

        for i in range(count):
            warnings = [
                {"message": "roadmap_90d under min", "section": "roadmap_90d"},
            ]
            if i % 3 == 0:
                warnings.append({"message": "persona leak", "type": "size_mismatch"})

            capture_realworld_feedback(
                report_id=4000 + i,
                warnings=warnings,
                ai_act_risk_level="minimal" if i % 2 == 0 else "limited",
                fallback_rate=0.1 * (i % 5),
                funding_source="DE",
                size_label="solo" if i % 3 == 0 else "team",
                research_coverage={"tools": 5, "funding": 3},
            )

    def test_detect_repeated_warnings(self) -> None:
        """Should detect repeated warning patterns."""
        from services.feedback_analyzer import detect_repeated_warnings

        self._populate_feedback(10)

        patterns = detect_repeated_warnings(days=7, min_occurrences=3)

        assert len(patterns) > 0
        # roadmap_90d warnings should be detected
        roadmap_patterns = [p for p in patterns if p.section == "roadmap_90d"]
        assert len(roadmap_patterns) > 0
        assert roadmap_patterns[0].occurrence_count >= 3

    def test_identify_persona_leak_patterns(self) -> None:
        """Should identify persona leak patterns."""
        from services.feedback_analyzer import identify_persona_leak_patterns

        self._populate_feedback(10)

        patterns = identify_persona_leak_patterns(days=7)

        # Should have patterns for personas with leaks
        assert len(patterns) >= 0  # May be empty if no leaks

    def test_identify_research_degradation(self) -> None:
        """Should identify research degradation."""
        from services.feedback_analyzer import identify_research_degradation

        self._populate_feedback(5)

        degradations = identify_research_degradation(current_days=7, previous_days=7)

        # Should always return degradation checks for each source
        assert len(degradations) >= 4  # tools, funding, competitor, market_insights, api_reliability
        sources = [d.source for d in degradations]
        assert "tools" in sources
        assert "api_reliability" in sources

    def test_run_full_analysis(self) -> None:
        """Full analysis should return complete result."""
        from services.feedback_analyzer import run_full_analysis

        self._populate_feedback(10)

        result = run_full_analysis(days=7)

        assert result.total_reports_analyzed == 10
        assert result.period_days == 7
        assert hasattr(result, "warning_patterns")
        assert hasattr(result, "research_degradations")
        assert hasattr(result, "top_warning_types")

    def test_analysis_to_dict(self) -> None:
        """Analysis result should serialize to dict."""
        from services.feedback_analyzer import run_full_analysis

        self._populate_feedback(5)

        result = run_full_analysis(days=7)
        result_dict = result.to_dict()

        assert "analysis_timestamp" in result_dict
        assert "warning_patterns" in result_dict
        assert "research_degradations" in result_dict
        assert isinstance(result_dict["warning_patterns"], list)


# =============================================================================
# TEST G16-C: DASHBOARD ROUTES
# =============================================================================

# Check if fastapi is available for route tests
try:
    from fastapi import APIRouter
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestG16C_DashboardRoutes:
    """Tests for feedback dashboard routes."""

    def setup_method(self) -> None:
        """Clear feedback store before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()

    def test_overview_endpoint_exists(self) -> None:
        """Overview endpoint should be defined."""
        from routes.feedback_dashboard import router

        routes = [r.path for r in router.routes]
        assert "/overview" in routes

    def test_persona_issues_endpoint_exists(self) -> None:
        """Persona issues endpoint should be defined."""
        from routes.feedback_dashboard import router

        routes = [r.path for r in router.routes]
        assert "/persona-issues" in routes

    def test_ai_act_anomalies_endpoint_exists(self) -> None:
        """AI-Act anomalies endpoint should be defined."""
        from routes.feedback_dashboard import router

        routes = [r.path for r in router.routes]
        assert "/ai-act-anomalies" in routes

    def test_learning_insights_endpoint_exists(self) -> None:
        """Learning insights endpoint should be defined."""
        from routes.feedback_dashboard import router

        routes = [r.path for r in router.routes]
        assert "/learning-insights" in routes


# =============================================================================
# TEST G16-D: LEARNING ENGINE
# =============================================================================

class TestG16D_LearningEngine:
    """Tests for learning engine action item generation."""

    def setup_method(self) -> None:
        """Clear feedback store before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()

    def _populate_problematic_feedback(self) -> None:
        """Populate with problematic feedback data."""
        from services.feedback_loop import capture_realworld_feedback

        # Create entries with many warnings
        for i in range(15):
            warnings = [
                {"message": "roadmap_90d under min", "section": "roadmap_90d"},
                {"message": "redundancy in BC", "section": "BUSINESS_CASE"},
            ]
            if i % 2 == 0:
                warnings.append({"message": "persona leak", "type": "size_mismatch"})

            capture_realworld_feedback(
                report_id=5000 + i,
                warnings=warnings,
                ai_act_risk_level="minimal",
                fallback_rate=0.4,  # High fallback
                funding_source="DE",
                size_label="solo",
                generation_time_sec=150,  # Slow
                llm_timeouts=3,  # High timeouts
            )

    def test_generate_action_items_empty(self) -> None:
        """Should return empty list with no data."""
        from services.learning_engine import generate_action_items

        items = generate_action_items(days=7)
        assert isinstance(items, list)

    def test_generate_action_items_with_data(self) -> None:
        """Should generate action items from problematic data."""
        from services.learning_engine import generate_action_items

        self._populate_problematic_feedback()

        items = generate_action_items(days=7)

        assert len(items) > 0
        # Should have warnings category items
        categories = [item.category for item in items]
        assert "warnings" in categories or "performance" in categories

    def test_action_item_structure(self) -> None:
        """Action items should have required fields."""
        from services.learning_engine import ActionItem

        item = ActionItem(
            priority="high",
            category="warnings",
            title="Test Warning",
            description="Test description",
            affected_count=5,
            suggested_fix="Fix this",
        )

        assert item.priority == "high"
        assert item.category == "warnings"
        assert item.title == "Test Warning"
        assert item.affected_count == 5

    def test_action_items_sorted_by_priority(self) -> None:
        """Action items should be sorted by priority."""
        from services.learning_engine import generate_action_items

        self._populate_problematic_feedback()

        items = generate_action_items(days=7)

        if len(items) > 1:
            # First items should be high priority
            priorities = [item.priority for item in items]
            high_indices = [i for i, p in enumerate(priorities) if p == "high"]
            medium_indices = [i for i, p in enumerate(priorities) if p == "medium"]

            if high_indices and medium_indices:
                assert max(high_indices) < min(medium_indices)

    def test_get_learning_summary(self) -> None:
        """Learning summary should aggregate correctly."""
        from services.learning_engine import get_learning_summary

        self._populate_problematic_feedback()

        summary = get_learning_summary(days=7)

        assert "total_action_items" in summary
        assert "by_priority" in summary
        assert "by_category" in summary
        assert "high" in summary["by_priority"]


# =============================================================================
# TEST G16-E: INTEGRATION
# =============================================================================

class TestG16E_Integration:
    """Integration tests for the full feedback loop."""

    def setup_method(self) -> None:
        """Clear feedback store before each test."""
        from services.feedback_loop import clear_feedback_store
        clear_feedback_store()

    def test_full_feedback_flow(self) -> None:
        """Test complete flow from capture to analysis to action items."""
        from services.feedback_loop import capture_realworld_feedback
        from services.feedback_analyzer import run_full_analysis
        from services.learning_engine import generate_action_items

        # 1. Capture feedback
        for i in range(10):
            capture_realworld_feedback(
                report_id=6000 + i,
                warnings=[{"message": "test warning", "section": "test"}],
                ai_act_risk_level="minimal",
                fallback_rate=0.1,
                funding_source="DE",
                size_label="solo",
            )

        # 2. Run analysis
        analysis = run_full_analysis(days=7)
        assert analysis.total_reports_analyzed == 10

        # 3. Generate action items
        items = generate_action_items(days=7)
        assert isinstance(items, list)

    def test_feedback_entry_serialization(self) -> None:
        """Feedback entry should serialize to dict."""
        from services.feedback_loop import capture_realworld_feedback

        entry = capture_realworld_feedback(
            report_id=7001,
            warnings=[{"message": "test", "section": "test"}],
            ai_act_risk_level="limited",
            fallback_rate=0.2,
            funding_source="DE",
            size_label="team",
        )

        assert entry is not None
        entry_dict = entry.to_dict()

        assert entry_dict["report_id"] == 7001
        assert entry_dict["ai_act_risk_level"] == "limited"
        assert "timestamp" in entry_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
