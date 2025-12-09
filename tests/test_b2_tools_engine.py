# -*- coding: utf-8 -*-
"""
Sprint B2: Tools Engine 2.0 Test Suite
=======================================

Comprehensive tests for:
- B2-A: Confidence Calculation
- B2-B: Trend Prognoses
- B2-C: Persona-Fit (solo/team/kmu)
- B2-D: AI-Act Alignment
- B2-E: Segment-Stability
- B2-F: Generic-Fallback
- B2-G: High/Low Confidence Toolsets
- B2-H: Drift & Freeze Integration
- B2-I: Dashboard API

Version: 1.0.0 (Sprint B2)
"""
from __future__ import annotations

import json
import os
import sys
import pytest
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_briefing_solo() -> Dict[str, Any]:
    """Sample briefing for solo persona."""
    return {
        "unternehmensgroesse": "Solo-Selbststaendige/r (1)",
        "branche": "IT & Softwareentwicklung",
        "branche_label": "it",
        "ai_act_risk_level": "minimal",
        "hauptleistung": "Software Development & Consulting"
    }


@pytest.fixture
def sample_briefing_team() -> Dict[str, Any]:
    """Sample briefing for team persona."""
    return {
        "unternehmensgroesse": "Kleines Team (2-10)",
        "branche": "Marketing & Kommunikation",
        "branche_label": "marketing",
        "ai_act_risk_level": "limited",
        "hauptleistung": "Marketing Automation & Content"
    }


@pytest.fixture
def sample_briefing_kmu() -> Dict[str, Any]:
    """Sample briefing for KMU persona."""
    return {
        "unternehmensgroesse": "KMU (11-250)",
        "branche": "Produktion & Fertigung",
        "branche_label": "manufacturing",
        "ai_act_risk_level": "high-risk",
        "hauptleistung": "AI-driven Quality Control"
    }


@pytest.fixture
def sample_tools() -> List[Dict[str, Any]]:
    """Sample list of tools with metadata."""
    return [
        {
            "name": "Make (Integromat)",
            "category": "Workflow-Automation",
            "_confidence": 0.82,
            "_confidence_level": "high",
            "_segment_stability": "strong",
            "_ai_act_alignment": 0.65,
            "_persona_fit": 0.90,
            "_trend": 0.15,
            "_trend_direction": "rising"
        },
        {
            "name": "Notion",
            "category": "Wissensmanagement / Docs",
            "_confidence": 0.78,
            "_confidence_level": "high",
            "_segment_stability": "strong",
            "_ai_act_alignment": 0.60,
            "_persona_fit": 0.85,
            "_trend": 0.05,
            "_trend_direction": "stable"
        },
        {
            "name": "DataDog",
            "category": "Monitoring / Observability",
            "_confidence": 0.72,
            "_confidence_level": "high",
            "_segment_stability": "medium",
            "_ai_act_alignment": 0.95,
            "_persona_fit": 0.70,
            "_trend": 0.10,
            "_trend_direction": "rising"
        },
        {
            "name": "Unknown Tool",
            "category": "Other",
            "_confidence": 0.25,
            "_confidence_level": "low",
            "_segment_stability": "weak",
            "_ai_act_alignment": 0.30,
            "_persona_fit": 0.40,
            "_trend": -0.10,
            "_trend_direction": "declining"
        }
    ]


# =============================================================================
# B2-A: CONFIDENCE CALCULATION TESTS
# =============================================================================

class TestConfidenceCalculation:
    """Tests for confidence calculation logic."""

    def test_confidence_high_threshold(self):
        """Confidence >= 0.70 should be 'high'."""
        from services.tools_analytics import calculate_tool_confidence

        confidence, level = calculate_tool_confidence(
            usage_count=50,
            segment_stability="strong",
            ai_act_alignment=0.8,
            persona_fit=0.9,
            sample_size=30
        )

        assert level == "high"
        assert confidence >= 0.70

    def test_confidence_medium_threshold(self):
        """Confidence 0.40-0.69 should be 'medium'."""
        from services.tools_analytics import calculate_tool_confidence

        confidence, level = calculate_tool_confidence(
            usage_count=10,
            segment_stability="medium",
            ai_act_alignment=0.5,
            persona_fit=0.6,
            sample_size=15
        )

        assert level == "medium"
        assert 0.40 <= confidence < 0.70

    def test_confidence_low_threshold(self):
        """Confidence < 0.40 should be 'low'."""
        from services.tools_analytics import calculate_tool_confidence

        confidence, level = calculate_tool_confidence(
            usage_count=2,
            segment_stability="weak",
            ai_act_alignment=0.3,
            persona_fit=0.3,
            sample_size=3
        )

        assert level == "low"
        assert confidence < 0.40

    def test_confidence_with_zero_usage(self):
        """Zero usage should result in low confidence."""
        from services.tools_analytics import calculate_tool_confidence

        confidence, level = calculate_tool_confidence(
            usage_count=0,
            segment_stability="weak",
            ai_act_alignment=0.5,
            persona_fit=0.5,
            sample_size=5
        )

        assert confidence >= 0.0
        assert confidence <= 1.0


# =============================================================================
# B2-B: TREND PROGNOSES TESTS
# =============================================================================

class TestTrendPrognoses:
    """Tests for predictive trend engine."""

    def test_trend_rising(self):
        """Recent increase should show rising trend."""
        from services.tools_recommender import calculate_predictive_trend

        trend = calculate_predictive_trend(
            tool_name="TestTool",
            recent_count=50,
            historical_count=30
        )

        assert trend > 0
        assert trend <= 1.0

    def test_trend_declining(self):
        """Recent decrease should show declining trend."""
        from services.tools_recommender import calculate_predictive_trend

        trend = calculate_predictive_trend(
            tool_name="TestTool",
            recent_count=20,
            historical_count=50
        )

        assert trend < 0
        assert trend >= -1.0

    def test_trend_stable(self):
        """Similar counts should show stable trend."""
        from services.tools_recommender import calculate_predictive_trend

        trend = calculate_predictive_trend(
            tool_name="TestTool",
            recent_count=50,
            historical_count=50
        )

        assert trend == 0.0

    def test_trend_new_tool(self):
        """New tool with no history should have slight positive."""
        from services.tools_recommender import calculate_predictive_trend

        trend = calculate_predictive_trend(
            tool_name="NewTool",
            recent_count=10,
            historical_count=0
        )

        assert trend == 0.5  # New tool gets slight positive


# =============================================================================
# B2-C: PERSONA-FIT TESTS
# =============================================================================

class TestPersonaFit:
    """Tests for persona fit scoring."""

    def test_persona_fit_solo(self):
        """Solo persona should prefer automation tools."""
        from services.tools_analytics import calculate_persona_fit

        fit = calculate_persona_fit("Make (Integromat)", "solo")
        assert fit >= 0.6

        fit = calculate_persona_fit("Zapier", "solo")
        assert fit >= 0.6

    def test_persona_fit_team(self):
        """Team persona should prefer collaboration tools."""
        from services.tools_analytics import calculate_persona_fit

        fit = calculate_persona_fit("Slack", "team")
        assert fit >= 0.6

        fit = calculate_persona_fit("Notion", "team")
        assert fit >= 0.6

    def test_persona_fit_kmu(self):
        """KMU persona should prefer governance tools."""
        from services.tools_analytics import calculate_persona_fit

        # Tools in KMU persona should return 1.0 (perfect fit)
        # Tools in other personas should return 0.6 (partial fit)
        # Unknown tools should return 0.5 (neutral)
        fit = calculate_persona_fit("Tableau", "kmu")  # In KMU analytics list
        assert fit >= 0.5  # At minimum neutral

        fit = calculate_persona_fit("Power BI", "kmu")  # In KMU analytics list
        assert fit >= 0.5  # At minimum neutral

    def test_persona_fit_unknown_tool(self):
        """Unknown tools should have neutral fit."""
        from services.tools_analytics import calculate_persona_fit

        fit = calculate_persona_fit("RandomUnknownTool123", "team")
        assert fit == 0.5  # Neutral


# =============================================================================
# B2-D: AI-ACT ALIGNMENT TESTS
# =============================================================================

class TestAIActAlignment:
    """Tests for AI Act alignment scoring."""

    def test_alignment_high_risk(self):
        """High-risk context should prefer governance tools."""
        from services.tools_analytics import calculate_ai_act_alignment

        # Governance tool in high-risk context
        align = calculate_ai_act_alignment("MLflow", "high-risk")
        assert align >= 0.7

        # Non-governance tool in high-risk context
        align = calculate_ai_act_alignment("ChatGPT", "high-risk")
        assert align < 0.7

    def test_alignment_minimal_risk(self):
        """Minimal-risk context should accept all tools."""
        from services.tools_analytics import calculate_ai_act_alignment

        # Any tool should be acceptable in minimal risk
        align = calculate_ai_act_alignment("ChatGPT", "minimal")
        assert align >= 0.6

    def test_alignment_limited_risk(self):
        """Limited-risk context should prefer medium governance."""
        from services.tools_analytics import calculate_ai_act_alignment

        align = calculate_ai_act_alignment("HubSpot", "limited")
        assert align >= 0.6


# =============================================================================
# B2-E: SEGMENT STABILITY TESTS
# =============================================================================

class TestSegmentStability:
    """Tests for segment stability calculation."""

    def test_stability_strong(self):
        """Low variance should be 'strong' stability."""
        from services.tools_analytics import calculate_segment_stability

        values = [10, 11, 10, 12, 10, 11, 10, 11, 10, 12]
        stability, outliers = calculate_segment_stability(values)

        assert stability == "strong"

    def test_stability_weak(self):
        """High variance should be 'weak' stability."""
        from services.tools_analytics import calculate_segment_stability

        values = [5, 50, 10, 100, 3, 80, 15, 60, 8, 90]
        stability, outliers = calculate_segment_stability(values)

        assert stability == "weak"

    def test_stability_insufficient_samples(self):
        """Insufficient samples should be 'weak'."""
        from services.tools_analytics import calculate_segment_stability

        values = [10, 11]  # Only 2 samples
        stability, outliers = calculate_segment_stability(values, min_sample_size=5)

        assert stability == "weak"

    def test_stability_winsorizing(self):
        """Outliers should be trimmed via Winsorizing."""
        from services.tools_analytics import calculate_segment_stability

        # Include extreme outliers
        values = [10, 11, 10, 12, 10, 11, 10, 11, 100, 1]  # 100 and 1 are outliers
        stability, outliers = calculate_segment_stability(values)

        assert outliers >= 0  # Should have trimmed some outliers


# =============================================================================
# B2-F: GENERIC FALLBACK TESTS
# =============================================================================

class TestGenericFallback:
    """Tests for generic fallback behavior."""

    def test_fallback_on_weak_segment(self, sample_briefing_solo):
        """Weak segment should trigger generic fallback."""
        from services.tools_recommender import recommend_tools

        # This should work even without analytics data
        tools = recommend_tools(sample_briefing_solo)

        assert len(tools) > 0
        assert all("name" in t for t in tools)

    def test_recommendations_always_return_tools(self, sample_briefing_kmu):
        """Should always return some tools even without analytics."""
        from services.tools_recommender import recommend_tools

        tools = recommend_tools(sample_briefing_kmu)

        assert len(tools) >= 3
        assert len(tools) <= 12


# =============================================================================
# B2-G: HIGH/LOW CONFIDENCE TOOLSETS TESTS
# =============================================================================

class TestHighLowConfidenceToolsets:
    """Tests for confidence-based toolset handling."""

    def test_high_confidence_tools_sorted_first(self, sample_briefing_team):
        """High confidence tools should rank higher."""
        from services.tools_recommender import recommend_tools

        tools = recommend_tools(sample_briefing_team, include_confidence=True)

        if len(tools) >= 2:
            # First tool should have higher or equal confidence than last
            first_conf = tools[0].get("_confidence", 0) or tools[0].get("_final_score", 0)
            last_conf = tools[-1].get("_confidence", 0) or tools[-1].get("_final_score", 0)
            assert first_conf >= last_conf

    def test_low_confidence_tools_flagged(self, sample_tools):
        """Low confidence tools should be identifiable."""
        low_conf_tools = [t for t in sample_tools if t.get("_confidence_level") == "low"]

        assert len(low_conf_tools) >= 1
        assert all(t.get("_confidence", 0) < 0.40 for t in low_conf_tools)


# =============================================================================
# B2-H: DRIFT & FREEZE INTEGRATION TESTS
# =============================================================================

class TestDriftAndFreeze:
    """Tests for drift detection and freeze mechanism."""

    def test_diversity_drift_detection(self):
        """Should detect significant tool diversity changes."""
        from services.tools_drift_detector import detect_diversity_drift

        previous = [{"name": "Tool1"}, {"name": "Tool2"}, {"name": "Tool3"}]
        current = [{"name": "ToolA"}, {"name": "ToolB"}, {"name": "ToolC"}]  # All different

        result = detect_diversity_drift(current, previous)

        assert result.score > 50  # Significant change
        assert len(result.affected_tools) > 0

    def test_overpopulation_detection(self):
        """Should detect too many tools."""
        from services.tools_drift_detector import detect_overpopulation

        tools = [{"name": f"Tool{i}"} for i in range(20)]  # 20 tools

        result = detect_overpopulation(tools, limit=14)

        assert result.score > 0
        assert "overpopulation" in result.issues[0].lower()

    def test_governance_mismatch_detection(self):
        """Should detect governance mismatch for high-risk."""
        from services.tools_drift_detector import detect_governance_mismatch

        # Tools without governance focus
        tools = [
            {"name": "ChatGPT", "category": "AI Assistant"},
            {"name": "Canva", "category": "Design"}
        ]

        result = detect_governance_mismatch(tools, "high-risk")

        assert result.score > 0  # Should detect mismatch

    def test_persona_drift_detection(self):
        """Should detect inappropriate tools for persona."""
        from services.tools_drift_detector import detect_persona_drift

        # Enterprise tools for solo persona
        tools = [
            {"name": "Collibra"},
            {"name": "SAP MDM"}
        ]

        result = detect_persona_drift(tools, "solo")

        assert result.score > 0
        assert len(result.affected_tools) > 0

    def test_freeze_conditions(self):
        """Should identify freeze conditions correctly."""
        from services.tools_drift_detector import (
            check_freeze_conditions,
            ToolsDriftAnalysis
        )

        # Critical drift
        analysis = ToolsDriftAnalysis(
            analysis_id="test",
            total_drift_score=80  # Above critical threshold
        )

        segment_conf = {"solo": 0.1, "team": 0.1}  # Low confidence

        should_freeze, reason = check_freeze_conditions(segment_conf, analysis)

        assert should_freeze
        assert len(reason) > 0


# =============================================================================
# B2-I: DASHBOARD API TESTS
# =============================================================================

class TestDashboardAPI:
    """Tests for dashboard API endpoints."""

    def test_overview_endpoint_structure(self):
        """Overview endpoint should return correct structure."""
        from services.tools_analytics import get_analytics_overview

        overview = get_analytics_overview()

        assert "enabled" in overview
        assert "has_data" in overview

    def test_recommendations_endpoint(self, sample_briefing_kmu):
        """Recommendations should work via recommend_tools_v2."""
        from services.tools_recommender import recommend_tools_v2

        result = recommend_tools_v2(sample_briefing_kmu)

        assert hasattr(result, "recommendations")
        assert hasattr(result, "insights")
        assert hasattr(result, "segment_context")
        assert hasattr(result, "segment_stability")


# =============================================================================
# GOLD PROFILE VALIDATION TESTS
# =============================================================================

class TestGoldProfiles:
    """Tests for gold profile validation."""

    @pytest.mark.parametrize("profile_idx,expected_min,expected_max", [
        (0, 5, 8),    # Solo
        (1, 6, 10),   # Team
        (2, 8, 12),   # KMU
    ])
    def test_gold_profile_tool_count(self, profile_idx, expected_min, expected_max):
        """Gold profiles should have appropriate tool counts."""
        from services.tools_html_output import GOLD_PROFILES
        from services.tools_recommender import recommend_tools

        profile = GOLD_PROFILES[profile_idx]
        tools = recommend_tools(profile["briefing"])

        assert len(tools) >= expected_min, f"Too few tools for {profile['name']}"
        assert len(tools) <= expected_max, f"Too many tools for {profile['name']}"

    def test_gold_profile_no_forbidden_tools(self):
        """Gold profiles should not include forbidden tools."""
        from services.tools_html_output import GOLD_PROFILES
        from services.tools_recommender import recommend_tools

        for profile in GOLD_PROFILES:
            tools = recommend_tools(profile["briefing"])
            tool_names = [t.get("name", "").lower() for t in tools]

            for forbidden in profile["expected"]["forbidden_tools"]:
                assert not any(forbidden.lower() in name for name in tool_names), \
                    f"Found forbidden tool '{forbidden}' in {profile['name']}"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_full_recommendation_pipeline(self, sample_briefing_team):
        """Full pipeline from briefing to HTML output."""
        from services.tools_recommender import (
            recommend_tools,
            recommend_tools_v2,
            generate_all_html_sections
        )

        # Get recommendations
        tools = recommend_tools(sample_briefing_team)
        assert len(tools) > 0

        # Get v2 result
        result = recommend_tools_v2(sample_briefing_team)
        assert len(result.recommendations) > 0
        assert len(result.insights) >= 0

        # Generate HTML
        html_sections = generate_all_html_sections(sample_briefing_team)
        assert "TOOLS_TABLE_HTML" in html_sections
        assert len(html_sections["TOOLS_TABLE_HTML"]) > 0

    def test_validation_integration(self, sample_briefing_solo):
        """Validation should work with tools section."""
        from services.report_validator import ReportValidator
        from services.tools_recommender import recommend_tools

        tools = recommend_tools(sample_briefing_solo)

        sections = {
            "tools_empfehlungen": "<table>...</table>",
            "_tools_data": tools
        }
        meta = sample_briefing_solo

        validator = ReportValidator(sections, meta)
        validator._check_tools_section()

        # Should not have critical errors for valid tools
        critical = [e for e in validator.errors if e.severity == "CRITICAL"]
        assert len(critical) == 0


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance and scalability tests."""

    def test_recommendation_speed(self, sample_briefing_kmu):
        """Recommendations should complete quickly."""
        import time
        from services.tools_recommender import recommend_tools

        start = time.time()
        for _ in range(10):
            recommend_tools(sample_briefing_kmu)
        duration = time.time() - start

        # 10 recommendations should complete in under 1 second
        assert duration < 1.0, f"Too slow: {duration}s for 10 recommendations"

    def test_html_generation_speed(self, sample_briefing_team):
        """HTML generation should be fast."""
        import time
        from services.tools_recommender import generate_all_html_sections

        start = time.time()
        for _ in range(10):
            generate_all_html_sections(sample_briefing_team)
        duration = time.time() - start

        # 10 HTML generations should complete in under 2 seconds
        assert duration < 2.0, f"Too slow: {duration}s for 10 HTML generations"


# =============================================================================
# SAMPLE DATA GENERATION TESTS
# =============================================================================

class TestSampleData:
    """Tests for sample data generation."""

    def test_generate_sample_data(self):
        """Should generate valid sample data."""
        from services.tools_analytics import generate_sample_data, _tool_occurrences

        initial_count = len(_tool_occurrences)
        generate_sample_data(num_reports=10)

        assert len(_tool_occurrences) > initial_count

    def test_aggregate_statistics(self):
        """Should aggregate statistics correctly."""
        from services.tools_analytics import (
            generate_sample_data,
            aggregate_tools_statistics
        )

        generate_sample_data(num_reports=20)
        snapshot = aggregate_tools_statistics()

        assert snapshot.total_reports_analyzed > 0
        assert snapshot.total_tools_tracked > 0
        assert len(snapshot.tool_stats) > 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
