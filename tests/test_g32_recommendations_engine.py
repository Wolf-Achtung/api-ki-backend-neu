# -*- coding: utf-8 -*-
"""
Sprint G32: Recommendations Engine Tests
========================================

Comprehensive test suite for Recommendations Engine with 40+ tests covering:
- Data structures (Recommendation, RecommendationsReport)
- Priority scoring and phase grouping
- Size constraints validation
- HTML generation
- Consistency Engine integration (RECO_001-RECO_005)

Version: 1.0.0 (Sprint G32)
"""
from __future__ import annotations

import pytest
from typing import Dict, Any, List, Optional


# =============================================================================
# TEST: Data Structures - Recommendation
# =============================================================================

class TestRecommendation:
    """Tests for Recommendation dataclass."""

    def test_basic_creation(self) -> None:
        """Test Recommendation can be instantiated with basic values."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Implement ChatGPT",
            description="Start with ChatGPT for documentation.",
            reason="Highest fit score for your company.",
            impact_level="high",
            urgency_level="high",
            risk_relation="neutral",
            required_investment=5000.0,
            related_tools=["ChatGPT"],
            related_funding=["go-digital"],
            related_risks=[],
            timeline_phase="phase_1",
        )

        assert rec.id == "rec1"
        assert rec.title == "Implement ChatGPT"
        assert rec.impact_level == "high"
        assert rec.urgency_level == "high"
        assert rec.risk_relation == "neutral"
        assert rec.required_investment == 5000.0
        assert rec.timeline_phase == "phase_1"

    def test_invalid_impact_level_normalized(self) -> None:
        """Test invalid impact_level is normalized to medium."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="invalid",
            urgency_level="high",
            risk_relation="neutral",
        )

        assert rec.impact_level == "medium"

    def test_invalid_urgency_level_normalized(self) -> None:
        """Test invalid urgency_level is normalized to medium."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="high",
            urgency_level="super_urgent",
            risk_relation="neutral",
        )

        assert rec.urgency_level == "medium"

    def test_invalid_risk_relation_normalized(self) -> None:
        """Test invalid risk_relation is normalized to neutral."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="high",
            urgency_level="high",
            risk_relation="unknown",
        )

        assert rec.risk_relation == "neutral"

    def test_invalid_timeline_phase_normalized(self) -> None:
        """Test invalid timeline_phase is normalized to phase_1."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="high",
            urgency_level="high",
            risk_relation="neutral",
            timeline_phase="phase_99",
        )

        assert rec.timeline_phase == "phase_1"

    def test_negative_investment_normalized(self) -> None:
        """Test negative investment is normalized to zero."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="high",
            urgency_level="high",
            risk_relation="neutral",
            required_investment=-1000.0,
        )

        assert rec.required_investment == 0.0

    def test_none_investment_remains_none(self) -> None:
        """Test None investment remains None."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="high",
            urgency_level="high",
            risk_relation="neutral",
            required_investment=None,
        )

        assert rec.required_investment is None

    def test_priority_score_high_high(self) -> None:
        """Test priority score for high impact and high urgency."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="high",
            urgency_level="high",
            risk_relation="neutral",
        )

        assert rec.priority_score == 9  # 3 * 3

    def test_priority_score_medium_medium(self) -> None:
        """Test priority score for medium impact and medium urgency."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="medium",
            urgency_level="medium",
            risk_relation="neutral",
        )

        assert rec.priority_score == 4  # 2 * 2

    def test_priority_score_low_low(self) -> None:
        """Test priority score for low impact and low urgency."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="low",
            urgency_level="low",
            risk_relation="neutral",
        )

        assert rec.priority_score == 1  # 1 * 1

    def test_priority_score_high_low(self) -> None:
        """Test priority score for high impact and low urgency."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Test",
            reason="Test",
            impact_level="high",
            urgency_level="low",
            risk_relation="neutral",
        )

        assert rec.priority_score == 3  # 3 * 1

    def test_phase_number_property(self) -> None:
        """Test phase_number property for all phases."""
        from services.recommendations_engine import Recommendation

        for phase, expected_num in [("phase_1", 1), ("phase_2", 2), ("phase_3", 3)]:
            rec = Recommendation(
                id="rec1",
                title="Test",
                description="Test",
                reason="Test",
                impact_level="high",
                urgency_level="high",
                risk_relation="neutral",
                timeline_phase=phase,
            )
            assert rec.phase_number == expected_num

    def test_to_dict_serialization(self) -> None:
        """Test Recommendation serialization to dict."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test Title",
            description="Test Description",
            reason="Test Reason",
            impact_level="high",
            urgency_level="medium",
            risk_relation="reduces_risk",
            required_investment=5000.0,
            related_tools=["Tool A"],
            related_funding=["Funding A"],
            related_risks=["Risk A"],
            timeline_phase="phase_2",
        )

        data = rec.to_dict()

        assert data["id"] == "rec1"
        assert data["title"] == "Test Title"
        assert data["impact_level"] == "high"
        assert data["urgency_level"] == "medium"
        assert data["risk_relation"] == "reduces_risk"
        assert data["required_investment"] == 5000.0
        assert data["related_tools"] == ["Tool A"]
        assert data["timeline_phase"] == "phase_2"
        assert data["priority_score"] == 6  # 3 * 2

    def test_from_dict_deserialization(self) -> None:
        """Test Recommendation creation from dict."""
        from services.recommendations_engine import Recommendation

        data = {
            "id": "rec2",
            "title": "Test from Dict",
            "description": "Description",
            "reason": "Reason",
            "impact_level": "low",
            "urgency_level": "high",
            "risk_relation": "requires_mitigation",
            "required_investment": 1000.0,
            "related_tools": ["Tool B"],
            "related_funding": [],
            "related_risks": ["Risk B"],
            "timeline_phase": "phase_3",
        }

        rec = Recommendation.from_dict(data)

        assert rec.id == "rec2"
        assert rec.title == "Test from Dict"
        assert rec.impact_level == "low"
        assert rec.urgency_level == "high"
        assert rec.required_investment == 1000.0
        assert rec.timeline_phase == "phase_3"

    def test_from_dict_with_missing_fields(self) -> None:
        """Test Recommendation creation from partial dict."""
        from services.recommendations_engine import Recommendation

        data = {
            "id": "rec3",
            "title": "Partial",
        }

        rec = Recommendation.from_dict(data)

        assert rec.id == "rec3"
        assert rec.impact_level == "medium"  # Default
        assert rec.urgency_level == "medium"  # Default
        assert rec.risk_relation == "neutral"  # Default
        assert rec.timeline_phase == "phase_1"  # Default


# =============================================================================
# TEST: Data Structures - RecommendationsReport
# =============================================================================

class TestRecommendationsReport:
    """Tests for RecommendationsReport dataclass."""

    def test_basic_creation(self) -> None:
        """Test RecommendationsReport can be instantiated."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        rec1 = Recommendation(
            id="rec1", title="Test1", description="D1", reason="R1",
            impact_level="high", urgency_level="high", risk_relation="neutral",
        )
        rec2 = Recommendation(
            id="rec2", title="Test2", description="D2", reason="R2",
            impact_level="medium", urgency_level="medium", risk_relation="neutral",
        )

        report = RecommendationsReport(
            recommendations=[rec1, rec2],
            summary="Test summary",
            top_3_ids=["rec1"],
        )

        assert len(report.recommendations) == 2
        assert report.summary == "Test summary"
        assert report.top_3_ids == ["rec1"]

    def test_top_3_ids_validated(self) -> None:
        """Test top_3_ids is validated against recommendation IDs."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        rec1 = Recommendation(
            id="rec1", title="Test1", description="D1", reason="R1",
            impact_level="high", urgency_level="high", risk_relation="neutral",
        )

        report = RecommendationsReport(
            recommendations=[rec1],
            summary="Test",
            top_3_ids=["rec1", "rec_invalid", "rec_another_invalid"],
        )

        # Only valid IDs should remain
        assert report.top_3_ids == ["rec1"]

    def test_top_3_ids_limited_to_3(self) -> None:
        """Test top_3_ids is limited to exactly 3 entries."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        recs = [
            Recommendation(id=f"rec{i}", title=f"Test{i}", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral")
            for i in range(5)
        ]

        report = RecommendationsReport(
            recommendations=recs,
            summary="Test",
            top_3_ids=["rec0", "rec1", "rec2", "rec3", "rec4"],
        )

        assert len(report.top_3_ids) == 3
        assert report.top_3_ids == ["rec0", "rec1", "rec2"]

    def test_top_3_recommendations_property(self) -> None:
        """Test top_3_recommendations property."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        recs = [
            Recommendation(id=f"rec{i}", title=f"Test{i}", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral")
            for i in range(5)
        ]

        report = RecommendationsReport(
            recommendations=recs,
            summary="Test",
            top_3_ids=["rec0", "rec2", "rec4"],
        )

        top_3 = report.top_3_recommendations
        assert len(top_3) == 3
        assert all(r.id in ["rec0", "rec2", "rec4"] for r in top_3)

    def test_other_recommendations_property(self) -> None:
        """Test other_recommendations property."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        recs = [
            Recommendation(id=f"rec{i}", title=f"Test{i}", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral")
            for i in range(5)
        ]

        report = RecommendationsReport(
            recommendations=recs,
            summary="Test",
            top_3_ids=["rec0", "rec2", "rec4"],
        )

        others = report.other_recommendations
        assert len(others) == 2
        assert all(r.id in ["rec1", "rec3"] for r in others)

    def test_phase_recommendations_properties(self) -> None:
        """Test phase_1/2/3_recommendations properties."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        recs = [
            Recommendation(id="rec1", title="P1", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral",
                          timeline_phase="phase_1"),
            Recommendation(id="rec2", title="P1b", description="D", reason="R",
                          impact_level="high", urgency_level="medium", risk_relation="neutral",
                          timeline_phase="phase_1"),
            Recommendation(id="rec3", title="P2", description="D", reason="R",
                          impact_level="medium", urgency_level="medium", risk_relation="neutral",
                          timeline_phase="phase_2"),
            Recommendation(id="rec4", title="P3", description="D", reason="R",
                          impact_level="low", urgency_level="low", risk_relation="neutral",
                          timeline_phase="phase_3"),
        ]

        report = RecommendationsReport(recommendations=recs, summary="Test", top_3_ids=["rec1"])

        assert len(report.phase_1_recommendations) == 2
        assert len(report.phase_2_recommendations) == 1
        assert len(report.phase_3_recommendations) == 1

    def test_total_investment_property(self) -> None:
        """Test total_investment property calculation."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        recs = [
            Recommendation(id="rec1", title="T1", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral",
                          required_investment=5000.0),
            Recommendation(id="rec2", title="T2", description="D", reason="R",
                          impact_level="medium", urgency_level="medium", risk_relation="neutral",
                          required_investment=3000.0),
            Recommendation(id="rec3", title="T3", description="D", reason="R",
                          impact_level="low", urgency_level="low", risk_relation="neutral",
                          required_investment=None),  # Should be treated as 0
        ]

        report = RecommendationsReport(recommendations=recs, summary="Test", top_3_ids=["rec1"])

        assert report.total_investment == 8000.0

    def test_high_impact_count_property(self) -> None:
        """Test high_impact_count property."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        recs = [
            Recommendation(id="rec1", title="T1", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral"),
            Recommendation(id="rec2", title="T2", description="D", reason="R",
                          impact_level="high", urgency_level="medium", risk_relation="neutral"),
            Recommendation(id="rec3", title="T3", description="D", reason="R",
                          impact_level="medium", urgency_level="medium", risk_relation="neutral"),
            Recommendation(id="rec4", title="T4", description="D", reason="R",
                          impact_level="low", urgency_level="low", risk_relation="neutral"),
        ]

        report = RecommendationsReport(recommendations=recs, summary="Test", top_3_ids=["rec1"])

        assert report.high_impact_count == 2

    def test_get_recommendation_by_id(self) -> None:
        """Test get_recommendation method."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        recs = [
            Recommendation(id="rec1", title="T1", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral"),
            Recommendation(id="rec2", title="T2", description="D", reason="R",
                          impact_level="medium", urgency_level="medium", risk_relation="neutral"),
        ]

        report = RecommendationsReport(recommendations=recs, summary="Test", top_3_ids=["rec1"])

        assert report.get_recommendation("rec1").title == "T1"
        assert report.get_recommendation("rec2").title == "T2"
        assert report.get_recommendation("rec_invalid") is None

    def test_to_dict_serialization(self) -> None:
        """Test RecommendationsReport serialization to dict."""
        from services.recommendations_engine import Recommendation, RecommendationsReport

        recs = [
            Recommendation(id="rec1", title="T1", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral",
                          required_investment=5000.0),
        ]

        report = RecommendationsReport(
            recommendations=recs,
            summary="Summary text",
            top_3_ids=["rec1"],
        )

        data = report.to_dict()

        assert data["summary"] == "Summary text"
        assert data["top_3_ids"] == ["rec1"]
        assert data["count"] == 1
        assert data["total_investment"] == 5000.0
        assert data["high_impact_count"] == 1
        assert len(data["recommendations"]) == 1

    def test_from_dict_deserialization(self) -> None:
        """Test RecommendationsReport creation from dict."""
        from services.recommendations_engine import RecommendationsReport

        data = {
            "recommendations": [
                {"id": "rec1", "title": "T1", "description": "D", "reason": "R",
                 "impact_level": "high", "urgency_level": "high", "risk_relation": "neutral"},
            ],
            "summary": "From dict",
            "top_3_ids": ["rec1"],
        }

        report = RecommendationsReport.from_dict(data)

        assert report.summary == "From dict"
        assert len(report.recommendations) == 1
        assert report.recommendations[0].id == "rec1"


# =============================================================================
# TEST: Size Constraints
# =============================================================================

class TestSizeConstraints:
    """Tests for company size constraints."""

    def test_size_constraints_exist(self) -> None:
        """Test SIZE_CONSTRAINTS dict contains all sizes."""
        from services.recommendations_engine import SIZE_CONSTRAINTS

        assert "solo" in SIZE_CONSTRAINTS
        assert "team" in SIZE_CONSTRAINTS
        assert "kmu" in SIZE_CONSTRAINTS

    def test_solo_constraints(self) -> None:
        """Test Solo constraints are correct."""
        from services.recommendations_engine import SIZE_CONSTRAINTS

        solo = SIZE_CONSTRAINTS["solo"]
        assert solo["max_recommendations"] == 5
        assert solo["max_high_impact"] == 2
        assert solo["max_parallel_initiatives"] == 2

    def test_team_constraints(self) -> None:
        """Test Team constraints are correct."""
        from services.recommendations_engine import SIZE_CONSTRAINTS

        team = SIZE_CONSTRAINTS["team"]
        assert team["max_recommendations"] == 8
        assert team["max_high_impact"] == 4
        assert team["max_parallel_initiatives"] == 3

    def test_kmu_constraints(self) -> None:
        """Test KMU constraints are correct."""
        from services.recommendations_engine import SIZE_CONSTRAINTS

        kmu = SIZE_CONSTRAINTS["kmu"]
        assert kmu["max_recommendations"] == 10
        assert kmu["max_high_impact"] == 6
        assert kmu["max_parallel_initiatives"] == 5


# =============================================================================
# TEST: Validation Functions
# =============================================================================

class TestValidationFunctions:
    """Tests for validation helper functions."""

    def test_validate_recommendations_for_size_solo_valid(self) -> None:
        """Test validation passes for valid Solo report."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, validate_recommendations_for_size
        )

        recs = [
            Recommendation(id=f"rec{i}", title=f"T{i}", description="D", reason="R",
                          impact_level="medium", urgency_level="medium", risk_relation="neutral")
            for i in range(3)
        ]

        report = RecommendationsReport(recommendations=recs, summary="Test", top_3_ids=["rec0"])

        is_valid, errors = validate_recommendations_for_size(report, "solo")
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_recommendations_for_size_solo_too_many(self) -> None:
        """Test validation fails for Solo with too many recommendations."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, validate_recommendations_for_size
        )

        recs = [
            Recommendation(id=f"rec{i}", title=f"T{i}", description="D", reason="R",
                          impact_level="medium", urgency_level="medium", risk_relation="neutral")
            for i in range(7)  # More than 5
        ]

        report = RecommendationsReport(recommendations=recs, summary="Test", top_3_ids=["rec0"])

        is_valid, errors = validate_recommendations_for_size(report, "solo")
        assert is_valid is False
        assert len(errors) >= 1
        assert "Zu viele Empfehlungen" in errors[0]

    def test_validate_recommendations_for_size_solo_too_many_high_impact(self) -> None:
        """Test validation fails for Solo with too many high impact recommendations."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, validate_recommendations_for_size
        )

        recs = [
            Recommendation(id=f"rec{i}", title=f"T{i}", description="D", reason="R",
                          impact_level="high", urgency_level="medium", risk_relation="neutral")
            for i in range(4)  # 4 high impact, max is 2 for Solo
        ]

        report = RecommendationsReport(recommendations=recs, summary="Test", top_3_ids=["rec0"])

        is_valid, errors = validate_recommendations_for_size(report, "solo")
        assert is_valid is False
        assert any("High-Impact" in e for e in errors)

    def test_validate_recommendations_for_size_kmu_valid(self) -> None:
        """Test validation passes for valid KMU report."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, validate_recommendations_for_size
        )

        recs = [
            Recommendation(id=f"rec{i}", title=f"T{i}", description="D", reason="R",
                          impact_level="high", urgency_level="high", risk_relation="neutral")
            for i in range(6)  # 6 high impact, max is 6 for KMU
        ]

        report = RecommendationsReport(recommendations=recs, summary="Test", top_3_ids=["rec0"])

        is_valid, errors = validate_recommendations_for_size(report, "kmu")
        assert is_valid is True


# =============================================================================
# TEST: Report Generation
# =============================================================================

class TestReportGeneration:
    """Tests for report generation function."""

    def test_generate_with_empty_input(self) -> None:
        """Test report generation with minimal input."""
        from services.recommendations_engine import generate_recommendations_report

        report = generate_recommendations_report(
            briefing={"unternehmensgroesse": "Team", "branche": "IT"}
        )

        assert report is not None
        assert isinstance(report.recommendations, list)
        assert isinstance(report.summary, str)

    def test_generate_with_tools_data(self) -> None:
        """Test report generation with tools data."""
        from services.recommendations_engine import generate_recommendations_report

        tools_data = [
            {"name": "ChatGPT Enterprise", "fit_solo": 0.9, "fit_team": 0.8, "fit_kmu": 0.7,
             "vendor_risk": 2, "cost_level": 3},
            {"name": "Microsoft Copilot", "fit_solo": 0.7, "fit_team": 0.9, "fit_kmu": 0.9,
             "vendor_risk": 2, "cost_level": 4},
        ]

        report = generate_recommendations_report(
            tools_data=tools_data,
            briefing={"unternehmensgroesse": "Team", "branche": "IT"}
        )

        # Should include tool-related recommendation
        tool_recs = [r for r in report.recommendations if r.related_tools]
        assert len(tool_recs) >= 1

    def test_generate_with_funding_data(self) -> None:
        """Test report generation with funding data."""
        from services.recommendations_engine import generate_recommendations_report

        funding_data = {"programmes": [{"name": "go-digital"}]}

        report = generate_recommendations_report(
            funding_data=funding_data,
            briefing={"unternehmensgroesse": "KMU", "branche": "Produktion"}
        )

        # Should include funding-related recommendation
        funding_recs = [r for r in report.recommendations if r.related_funding]
        assert len(funding_recs) >= 1

    def test_generate_respects_solo_limits(self) -> None:
        """Test generated recommendations respect Solo size limits."""
        from services.recommendations_engine import generate_recommendations_report

        tools_data = [{"name": f"Tool{i}", "fit_solo": 0.8, "fit_team": 0.8, "fit_kmu": 0.8,
                       "vendor_risk": 2, "cost_level": 2} for i in range(10)]

        report = generate_recommendations_report(
            tools_data=tools_data,
            briefing={"unternehmensgroesse": "Solo/Freelancer", "branche": "IT"}
        )

        assert len(report.recommendations) <= 5

    def test_generate_selects_top_3(self) -> None:
        """Test top_3_ids is populated."""
        from services.recommendations_engine import generate_recommendations_report

        report = generate_recommendations_report(
            briefing={"unternehmensgroesse": "Team", "branche": "IT"}
        )

        # If we have at least 3 recommendations, we should have 3 top IDs
        if len(report.recommendations) >= 3:
            assert len(report.top_3_ids) == 3

    def test_generate_summary_not_empty(self) -> None:
        """Test summary is generated."""
        from services.recommendations_engine import generate_recommendations_report

        report = generate_recommendations_report(
            briefing={"unternehmensgroesse": "Team", "branche": "Beratung"}
        )

        assert len(report.summary) > 0


# =============================================================================
# TEST: HTML Generation
# =============================================================================

class TestHTMLGeneration:
    """Tests for HTML rendering function."""

    def test_html_contains_summary(self) -> None:
        """Test HTML includes summary section."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, recommendations_report_to_html
        )

        rec = Recommendation(id="rec1", title="Test", description="Desc", reason="Reason",
                            impact_level="high", urgency_level="high", risk_relation="neutral")
        report = RecommendationsReport(
            recommendations=[rec],
            summary="This is the summary",
            top_3_ids=["rec1"],
        )

        html = recommendations_report_to_html(report, lang="de")

        assert "This is the summary" in html

    def test_html_contains_top_priorities(self) -> None:
        """Test HTML includes top priorities section."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, recommendations_report_to_html
        )

        rec = Recommendation(id="rec1", title="Priority One", description="Desc", reason="Reason",
                            impact_level="high", urgency_level="high", risk_relation="neutral")
        report = RecommendationsReport(
            recommendations=[rec],
            summary="Summary",
            top_3_ids=["rec1"],
        )

        html = recommendations_report_to_html(report, lang="de")

        assert "Priority One" in html
        assert "Top-Prioritäten" in html

    def test_html_german_labels(self) -> None:
        """Test HTML uses German labels."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, recommendations_report_to_html
        )

        rec = Recommendation(id="rec1", title="Test", description="Desc", reason="Reason",
                            impact_level="high", urgency_level="high", risk_relation="reduces_risk")
        report = RecommendationsReport(recommendations=[rec], summary="S", top_3_ids=["rec1"])

        html = recommendations_report_to_html(report, lang="de")

        assert "Auswirkung" in html
        assert "Dringlichkeit" in html

    def test_html_english_labels(self) -> None:
        """Test HTML uses English labels."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, recommendations_report_to_html
        )

        rec = Recommendation(id="rec1", title="Test", description="Desc", reason="Reason",
                            impact_level="high", urgency_level="high", risk_relation="reduces_risk")
        report = RecommendationsReport(recommendations=[rec], summary="S", top_3_ids=["rec1"])

        html = recommendations_report_to_html(report, lang="en")

        assert "Impact" in html
        assert "Urgency" in html

    def test_html_includes_investment(self) -> None:
        """Test HTML includes investment amount when specified."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, recommendations_report_to_html
        )

        rec = Recommendation(id="rec1", title="Test", description="Desc", reason="Reason",
                            impact_level="high", urgency_level="high", risk_relation="neutral",
                            required_investment=5000.0)
        report = RecommendationsReport(recommendations=[rec], summary="S", top_3_ids=["rec1"])

        html = recommendations_report_to_html(report, lang="de")

        assert "5,000" in html or "5.000" in html or "5000" in html

    def test_html_includes_related_tools(self) -> None:
        """Test HTML includes related tools."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, recommendations_report_to_html
        )

        rec = Recommendation(id="rec1", title="Test", description="Desc", reason="Reason",
                            impact_level="high", urgency_level="high", risk_relation="neutral",
                            related_tools=["ChatGPT Enterprise", "Microsoft Copilot"])
        report = RecommendationsReport(recommendations=[rec], summary="S", top_3_ids=["rec1"])

        html = recommendations_report_to_html(report, lang="de")

        assert "ChatGPT Enterprise" in html

    def test_html_includes_phase_badge(self) -> None:
        """Test HTML includes phase badges."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, recommendations_report_to_html
        )

        rec = Recommendation(id="rec1", title="Test", description="Desc", reason="Reason",
                            impact_level="high", urgency_level="high", risk_relation="neutral",
                            timeline_phase="phase_2")
        report = RecommendationsReport(recommendations=[rec], summary="S", top_3_ids=["rec1"])

        html = recommendations_report_to_html(report, lang="de")

        assert "Phase 2" in html

    def test_html_g32_badge(self) -> None:
        """Test HTML includes G32 sprint badge."""
        from services.recommendations_engine import (
            RecommendationsReport, recommendations_report_to_html
        )

        report = RecommendationsReport(recommendations=[], summary="Empty", top_3_ids=[])
        html = recommendations_report_to_html(report, lang="de")

        assert "G32" in html

    def test_html_other_recommendations_section(self) -> None:
        """Test HTML includes 'other recommendations' section."""
        from services.recommendations_engine import (
            Recommendation, RecommendationsReport, recommendations_report_to_html
        )

        recs = [
            Recommendation(id=f"rec{i}", title=f"Rec {i}", description="D", reason="R",
                          impact_level="medium", urgency_level="medium", risk_relation="neutral")
            for i in range(5)
        ]
        report = RecommendationsReport(
            recommendations=recs,
            summary="S",
            top_3_ids=["rec0", "rec1", "rec2"],
        )

        html = recommendations_report_to_html(report, lang="de")

        assert "Weitere Empfehlungen" in html
        assert "Rec 3" in html
        assert "Rec 4" in html


# =============================================================================
# TEST: Consistency Engine Integration
# =============================================================================

class TestConsistencyEngineIntegration:
    """Tests for consistency engine RECO_001-RECO_005 rules."""

    def test_reco_domain_in_consistency_engine(self) -> None:
        """Test 'recommendations' domain exists in consistency engine."""
        from services.consistency_engine import ConsistencyEngine

        sections = {"RECOMMENDATIONS_ENGINE_HTML": "<div>test</div>"}
        briefing = {"unternehmensgroesse": "Team"}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Domain should be calculated
        assert "recommendations" in report.domain_scores

    def test_consistency_skips_without_reco_html(self) -> None:
        """Test consistency check skips when no recommendations HTML."""
        from services.consistency_engine import ConsistencyEngine

        sections = {}
        briefing = {"unternehmensgroesse": "Team"}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # No RECO issues when section missing
        reco_issues = [i for i in report.issues if i.rule_id.startswith("RECO_")]
        assert len(reco_issues) == 0


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_recommendations_list(self) -> None:
        """Test report with empty recommendations list."""
        from services.recommendations_engine import RecommendationsReport

        report = RecommendationsReport(
            recommendations=[],
            summary="No recommendations",
            top_3_ids=[],
        )

        assert len(report.recommendations) == 0
        assert report.total_investment == 0.0
        assert report.high_impact_count == 0

    def test_recommendation_with_empty_lists(self) -> None:
        """Test recommendation with empty related lists."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Desc",
            reason="Reason",
            impact_level="high",
            urgency_level="high",
            risk_relation="neutral",
            related_tools=[],
            related_funding=[],
            related_risks=[],
        )

        assert rec.related_tools == []
        assert rec.related_funding == []
        assert rec.related_risks == []

    def test_recommendation_lists_normalized(self) -> None:
        """Test non-list related fields are normalized to empty lists."""
        from services.recommendations_engine import Recommendation

        rec = Recommendation(
            id="rec1",
            title="Test",
            description="Desc",
            reason="Reason",
            impact_level="high",
            urgency_level="high",
            risk_relation="neutral",
            related_tools=None,  # type: ignore
            related_funding=None,  # type: ignore
            related_risks=None,  # type: ignore
        )

        assert rec.related_tools == []
        assert rec.related_funding == []
        assert rec.related_risks == []

    def test_determine_size_label_solo(self) -> None:
        """Test size label determination for Solo."""
        from services.recommendations_engine import _determine_size_label

        assert _determine_size_label({"unternehmensgroesse": "Solo/Freelancer"}) == "solo"
        assert _determine_size_label({"unternehmensgroesse": "Freiberufler"}) == "solo"
        assert _determine_size_label({"unternehmensgroesse": "Einzelunternehmen"}) == "solo"

    def test_determine_size_label_kmu(self) -> None:
        """Test size label determination for KMU."""
        from services.recommendations_engine import _determine_size_label

        assert _determine_size_label({"unternehmensgroesse": "KMU (>10 Mitarbeiter)"}) == "kmu"
        assert _determine_size_label({"unternehmensgroesse": "Mittelstand"}) == "kmu"

    def test_determine_size_label_team(self) -> None:
        """Test size label determination for Team (default)."""
        from services.recommendations_engine import _determine_size_label

        assert _determine_size_label({"unternehmensgroesse": "Team (2-10 MA)"}) == "team"
        assert _determine_size_label({"unternehmensgroesse": "Unknown"}) == "team"
        assert _determine_size_label({}) == "team"
        assert _determine_size_label(None) == "team"


# =============================================================================
# TEST: Module Loading
# =============================================================================

class TestModuleLoading:
    """Tests for module loading and exports."""

    def test_module_exports(self) -> None:
        """Test all expected exports are available."""
        from services.recommendations_engine import (
            Recommendation,
            RecommendationsReport,
            generate_recommendations_report,
            recommendations_report_to_html,
            RECOMMENDATIONS_ENGINE_ENABLED,
        )

        assert Recommendation is not None
        assert RecommendationsReport is not None
        assert generate_recommendations_report is not None
        assert recommendations_report_to_html is not None
        assert RECOMMENDATIONS_ENGINE_ENABLED is True

    def test_constants_defined(self) -> None:
        """Test constants are properly defined."""
        from services.recommendations_engine import (
            IMPACT_LEVELS,
            URGENCY_LEVELS,
            RISK_RELATIONS,
            TIMELINE_PHASES,
        )

        assert "low" in IMPACT_LEVELS
        assert "medium" in IMPACT_LEVELS
        assert "high" in IMPACT_LEVELS

        assert "low" in URGENCY_LEVELS
        assert "medium" in URGENCY_LEVELS
        assert "high" in URGENCY_LEVELS

        assert "reduces_risk" in RISK_RELATIONS
        assert "requires_mitigation" in RISK_RELATIONS
        assert "neutral" in RISK_RELATIONS

        assert "phase_1" in TIMELINE_PHASES
        assert "phase_2" in TIMELINE_PHASES
        assert "phase_3" in TIMELINE_PHASES
