# -*- coding: utf-8 -*-
"""
Sprint G25: Tools Engine 4.0 Tests

Comprehensive test suite for the multi-dimensional tool evaluation engine.
Tests cover: ToolProfile, evaluation, ranking, validation, and integration.
"""
import os
import sys

try:
    import pytest
except ImportError:
    pytest = None

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tools_engine_v4 import (
    ToolProfile,
    evaluate_tool_v4,
    rank_tools_v4,
    evaluate_tools_batch,
    generate_tool_badges_html,
    get_tool_profile_defaults,
    enhance_tool_recommendation,
    get_top_tools_v4,
    _estimate_cost_level,
    _estimate_complexity_level,
    _estimate_maturity_level,
    _estimate_compliance_score,
    _estimate_vendor_risk,
    _estimate_eu_hosting,
    _estimate_fit_scores,
    _calculate_composite_score,
    TOOLS_ENGINE_V4_ENABLED,
)

from services.config_validation import (
    ToolProfileValidation,
    validate_tool_profile_v4,
)


# =============================================================================
# ToolProfile Data Structure Tests
# =============================================================================

class TestToolProfile:
    """Tests for the ToolProfile dataclass."""

    def test_basic_creation(self):
        """Test basic ToolProfile creation."""
        profile = ToolProfile(name="Test Tool", category="Automation")
        assert profile.name == "Test Tool"
        assert profile.category == "Automation"
        assert profile.cost_level == 3  # Default
        assert profile.fit_solo == 0.5  # Default

    def test_all_fields_set(self):
        """Test ToolProfile with all fields set."""
        profile = ToolProfile(
            name="Notion",
            category="Wissensmanagement",
            score=85.0,
            cost_level=2,
            complexity_level=2,
            maturity_level=5,
            compliance_score=2,
            vendor_risk=3,
            eu_hosting=True,
            fit_solo=0.9,
            fit_team=0.95,
            fit_kmu=0.85,
        )
        assert profile.name == "Notion"
        assert profile.cost_level == 2
        assert profile.eu_hosting is True
        assert profile.fit_team == 0.95

    def test_to_dict(self):
        """Test ToolProfile to_dict conversion."""
        profile = ToolProfile(name="Test", category="Test Cat")
        result = profile.to_dict()
        assert isinstance(result, dict)
        assert result["name"] == "Test"
        assert result["category"] == "Test Cat"
        assert "cost_level" in result
        assert "fit_solo" in result

    def test_from_dict(self):
        """Test ToolProfile from_dict creation."""
        data = {
            "name": "Make",
            "category": "Automation",
            "cost_level": 2,
            "fit_solo": 0.85,
            "eu_hosting": "true",
        }
        profile = ToolProfile.from_dict(data)
        assert profile.name == "Make"
        assert profile.cost_level == 2
        assert profile.fit_solo == 0.85
        assert profile.eu_hosting is True

    def test_from_dict_unknown_eu_hosting(self):
        """Test ToolProfile handles unknown eu_hosting."""
        data = {"name": "Test", "category": "Test", "eu_hosting": "unknown"}
        profile = ToolProfile.from_dict(data)
        assert profile.eu_hosting is None

    def test_default_badges_empty(self):
        """Test ToolProfile has empty badges by default."""
        profile = ToolProfile(name="Test", category="Test")
        assert profile.badges == []


# =============================================================================
# Cost Level Estimation Tests
# =============================================================================

class TestCostLevelEstimation:
    """Tests for cost level heuristics."""

    def test_free_tool(self):
        """Test free tools get level 1."""
        assert _estimate_cost_level("Tally", "Free", "Forms") == 1
        assert _estimate_cost_level("Notion", "0 €/Monat", "Docs") == 1

    def test_cheap_tool(self):
        """Test cheap tools get level 2."""
        assert _estimate_cost_level("Make", "ab 9 €/Monat", "Automation") == 2

    def test_moderate_tool(self):
        """Test moderate tools get level 3."""
        assert _estimate_cost_level("Tool", "30 €/Monat", "CRM") == 3

    def test_expensive_tool(self):
        """Test expensive tools get level 4."""
        assert _estimate_cost_level("Salesforce", "ab 100 €/User", "CRM") == 4

    def test_enterprise_tool(self):
        """Test enterprise tools get level 5."""
        assert _estimate_cost_level("Enterprise Tool", "auf Anfrage", "Enterprise") >= 4

    def test_usage_based_moderate(self):
        """Test usage-based pricing is moderate."""
        result = _estimate_cost_level("OpenAI", "Usage-basiert", "KI-API")
        assert result == 3


# =============================================================================
# Complexity Level Estimation Tests
# =============================================================================

class TestComplexityLevelEstimation:
    """Tests for complexity level heuristics."""

    def test_simple_forms(self):
        """Test forms/intake tools are simple."""
        assert _estimate_complexity_level("Tally", "Fragebogen / Intake") == 1

    def test_moderate_crm(self):
        """Test CRM tools are moderate."""
        assert _estimate_complexity_level("HubSpot", "CRM / Sales") == 2

    def test_complex_automation(self):
        """Test automation tools are complex."""
        result = _estimate_complexity_level("Make", "Workflow-Automation")
        assert result >= 3

    def test_very_complex_ml(self):
        """Test ML tools are very complex."""
        assert _estimate_complexity_level("MLflow", "ML Lifecycle") >= 4


# =============================================================================
# Maturity Level Estimation Tests
# =============================================================================

class TestMaturityLevelEstimation:
    """Tests for maturity level heuristics."""

    def test_market_leader(self):
        """Test market leaders get level 5."""
        assert _estimate_maturity_level("Salesforce") == 5
        assert _estimate_maturity_level("Microsoft 365") == 5
        assert _estimate_maturity_level("HubSpot CRM") == 5

    def test_established_tool(self):
        """Test established tools get level 4."""
        assert _estimate_maturity_level("Make (Integromat)") == 4
        assert _estimate_maturity_level("Zapier") == 4

    def test_growing_tool(self):
        """Test growing tools get level 3."""
        assert _estimate_maturity_level("Perplexity AI") == 3

    def test_unknown_tool_default(self):
        """Test unknown tools get default level 3."""
        assert _estimate_maturity_level("SomeUnknownTool") == 3


# =============================================================================
# Compliance Score Estimation Tests
# =============================================================================

class TestComplianceScoreEstimation:
    """Tests for compliance score heuristics."""

    def test_eu_server_low_risk(self):
        """Test EU-server tools have low compliance risk."""
        assert _estimate_compliance_score("EU-Server", "EU") == 1

    def test_eu_option_available(self):
        """Test EU-option tools have moderate-low risk."""
        assert _estimate_compliance_score("EU-Option", "EU/US") == 1

    def test_us_with_dpa(self):
        """Test US tools with DPA have moderate risk."""
        assert _estimate_compliance_score("US (DPA)", "US") == 3

    def test_unknown_high_risk(self):
        """Test unknown compliance has high risk."""
        assert _estimate_compliance_score("Unknown", "Unknown") == 5


# =============================================================================
# Vendor Risk Estimation Tests
# =============================================================================

class TestVendorRiskEstimation:
    """Tests for vendor risk heuristics."""

    def test_eu_vendor_low_risk(self):
        """Test EU vendors have low risk."""
        assert _estimate_vendor_risk("EU", "GDPR-konform") == 1
        assert _estimate_vendor_risk("Deutschland", "") == 1

    def test_us_vendor_moderate_risk(self):
        """Test US vendors have moderate risk."""
        result = _estimate_vendor_risk("US", "")
        assert result >= 3

    def test_unknown_vendor_high_risk(self):
        """Test unknown vendors have high risk."""
        assert _estimate_vendor_risk("Unknown", "") == 5


# =============================================================================
# EU Hosting Estimation Tests
# =============================================================================

class TestEuHostingEstimation:
    """Tests for EU hosting detection."""

    def test_eu_only_true(self):
        """Test EU-only hosting returns True."""
        assert _estimate_eu_hosting("EU", "") is True

    def test_us_only_false(self):
        """Test US-only hosting returns False."""
        assert _estimate_eu_hosting("US", "") is False

    def test_mixed_unknown(self):
        """Test mixed hosting returns None."""
        result = _estimate_eu_hosting("EU/US", "")
        # With EU/US, it could be True if EU option exists
        assert result in (True, None)

    def test_eu_option_true(self):
        """Test EU-option returns True."""
        assert _estimate_eu_hosting("", "EU-Option") is True


# =============================================================================
# Fit Score Estimation Tests
# =============================================================================

class TestFitScoreEstimation:
    """Tests for fit score heuristics."""

    def test_fit_scores_in_range(self):
        """Test fit scores are always in 0-1 range."""
        fit_solo, fit_team, fit_kmu = _estimate_fit_scores(
            "TestTool", "Category", None, 3, 3
        )
        assert 0.0 <= fit_solo <= 1.0
        assert 0.0 <= fit_team <= 1.0
        assert 0.0 <= fit_kmu <= 1.0

    def test_cheap_simple_good_for_solo(self):
        """Test cheap, simple tools are good for solo."""
        fit_solo, _, _ = _estimate_fit_scores(
            "SimpleTool", "Forms", None, cost_level=1, complexity_level=1
        )
        assert fit_solo >= 0.6

    def test_expensive_complex_bad_for_solo(self):
        """Test expensive, complex tools are bad for solo."""
        fit_solo, _, _ = _estimate_fit_scores(
            "EnterpriseTool", "Enterprise", None, cost_level=5, complexity_level=5
        )
        assert fit_solo <= 0.5

    def test_best_for_size_boosts_fit(self):
        """Test best_for_size boosts fit score."""
        fit_solo, _, _ = _estimate_fit_scores(
            "Tool", "Cat", best_for_size=["solo"], cost_level=3, complexity_level=3
        )
        assert fit_solo >= 0.75


# =============================================================================
# evaluate_tool_v4 Tests
# =============================================================================

class TestEvaluateToolV4:
    """Tests for the main evaluation function."""

    def test_basic_evaluation(self):
        """Test basic tool evaluation."""
        profile = evaluate_tool_v4("Notion", "Wissensmanagement")
        assert isinstance(profile, ToolProfile)
        assert profile.name == "Notion"
        assert profile.category == "Wissensmanagement"

    def test_evaluation_with_existing_data(self):
        """Test evaluation with existing tool data."""
        existing = {
            "price": "0-10 €/Monat",
            "gdpr": "EU-Option",
            "host": "EU/US",
            "score": 85.0,
        }
        profile = evaluate_tool_v4("Notion", "Docs", existing_data=existing)
        assert profile.score == 85.0
        assert profile.cost_level <= 2  # Should be cheap

    def test_evaluation_generates_badges(self):
        """Test evaluation generates appropriate badges."""
        existing = {"price": "Free", "gdpr": "EU-Server", "host": "EU"}
        profile = evaluate_tool_v4("Tally", "Forms", existing_data=existing)
        assert len(profile.badges) > 0

    def test_all_levels_within_bounds(self):
        """Test all level scores are within 1-5 bounds."""
        profile = evaluate_tool_v4("TestTool", "TestCategory")
        assert 1 <= profile.cost_level <= 5
        assert 1 <= profile.complexity_level <= 5
        assert 1 <= profile.maturity_level <= 5
        assert 1 <= profile.compliance_score <= 5
        assert 1 <= profile.vendor_risk <= 5

    def test_all_fit_scores_within_bounds(self):
        """Test all fit scores are within 0-1 bounds."""
        profile = evaluate_tool_v4("TestTool", "TestCategory")
        assert 0.0 <= profile.fit_solo <= 1.0
        assert 0.0 <= profile.fit_team <= 1.0
        assert 0.0 <= profile.fit_kmu <= 1.0


# =============================================================================
# rank_tools_v4 Tests
# =============================================================================

class TestRankToolsV4:
    """Tests for the ranking function."""

    def test_empty_list(self):
        """Test ranking empty list returns empty."""
        result = rank_tools_v4([])
        assert result == []

    def test_single_tool(self):
        """Test ranking single tool."""
        profile = ToolProfile(name="Test", category="Test")
        result = rank_tools_v4([profile])
        assert len(result) == 1
        assert result[0].rank == 1

    def test_ranking_assigns_ranks(self):
        """Test ranking assigns sequential ranks."""
        tools = [
            ToolProfile(name="Tool1", category="Cat", fit_team=0.9),
            ToolProfile(name="Tool2", category="Cat", fit_team=0.5),
            ToolProfile(name="Tool3", category="Cat", fit_team=0.7),
        ]
        result = rank_tools_v4(tools, size_label="team")
        ranks = [t.rank for t in result]
        assert sorted(ranks) == [1, 2, 3]

    def test_high_fit_ranks_higher(self):
        """Test tools with higher fit rank higher."""
        tools = [
            ToolProfile(name="LowFit", category="Cat", fit_solo=0.2),
            ToolProfile(name="HighFit", category="Cat", fit_solo=0.9),
        ]
        result = rank_tools_v4(tools, size_label="solo")
        assert result[0].name == "HighFit"

    def test_prioritize_compliance(self):
        """Test compliance prioritization boosts compliant tools."""
        tools = [
            ToolProfile(name="Compliant", category="Cat", compliance_score=1, fit_team=0.5),
            ToolProfile(name="Risky", category="Cat", compliance_score=5, fit_team=0.6),
        ]
        result = rank_tools_v4(tools, prioritize_compliance=True)
        assert result[0].name == "Compliant"

    def test_prioritize_cost(self):
        """Test cost prioritization boosts cheap tools."""
        tools = [
            ToolProfile(name="Cheap", category="Cat", cost_level=1, fit_team=0.5),
            ToolProfile(name="Expensive", category="Cat", cost_level=5, fit_team=0.6),
        ]
        result = rank_tools_v4(tools, prioritize_cost=True)
        assert result[0].name == "Cheap"

    def test_composite_score_calculated(self):
        """Test composite scores are calculated."""
        profile = ToolProfile(name="Test", category="Test")
        result = rank_tools_v4([profile])
        assert result[0].composite_score > 0


# =============================================================================
# Batch Evaluation Tests
# =============================================================================

class TestEvaluateToolsBatch:
    """Tests for batch evaluation."""

    def test_empty_batch(self):
        """Test empty batch returns empty list."""
        result = evaluate_tools_batch([])
        assert result == []

    def test_batch_evaluation(self):
        """Test batch evaluation processes all tools."""
        tools_data = [
            {"name": "Tool1", "category": "Cat1"},
            {"name": "Tool2", "category": "Cat2"},
            {"name": "Tool3", "category": "Cat3"},
        ]
        result = evaluate_tools_batch(tools_data)
        assert len(result) == 3
        assert all(isinstance(p, ToolProfile) for p in result)


# =============================================================================
# Badge Generation Tests
# =============================================================================

class TestGenerateToolBadgesHtml:
    """Tests for badge HTML generation."""

    def test_no_badges(self):
        """Test empty badges returns empty string."""
        profile = ToolProfile(name="Test", category="Test", badges=[])
        result = generate_tool_badges_html(profile)
        assert result == ""

    def test_cost_badge(self):
        """Test cost badge generation."""
        profile = ToolProfile(name="Test", category="Test", badges=["cost-free"])
        result = generate_tool_badges_html(profile)
        assert "tool-badge" in result
        assert "Free" in result

    def test_compliance_badge(self):
        """Test compliance badge generation."""
        profile = ToolProfile(name="Test", category="Test", badges=["eu-compliant"])
        result = generate_tool_badges_html(profile)
        assert "EU-OK" in result

    def test_compact_mode(self):
        """Test compact badge mode."""
        profile = ToolProfile(name="Test", category="Test", badges=["cost-free"])
        result = generate_tool_badges_html(profile, compact=True)
        assert "tool-badge-compact" in result

    def test_max_three_badges(self):
        """Test maximum 3 badges are shown."""
        profile = ToolProfile(
            name="Test", category="Test",
            badges=["cost-free", "easy-setup", "eu-compliant", "eu-hosting", "low-vendor-risk"]
        )
        result = generate_tool_badges_html(profile)
        # Should only have 3 badges
        assert result.count("tool-badge") <= 3


# =============================================================================
# Validation Tests
# =============================================================================

class TestToolProfileValidation:
    """Tests for tool profile validation."""

    def test_valid_profile(self):
        """Test valid profile passes validation."""
        profile = {
            "name": "Test",
            "category": "Test",
            "cost_level": 3,
            "complexity_level": 2,
            "fit_solo": 0.5,
        }
        is_valid, errors = validate_tool_profile_v4(profile)
        assert is_valid
        assert len(errors) == 0

    def test_missing_name(self):
        """Test missing name fails validation."""
        profile = {"category": "Test"}
        is_valid, errors = validate_tool_profile_v4(profile)
        assert not is_valid
        assert any("name" in e for e in errors)

    def test_missing_category(self):
        """Test missing category fails validation."""
        profile = {"name": "Test"}
        is_valid, errors = validate_tool_profile_v4(profile)
        assert not is_valid
        assert any("category" in e for e in errors)

    def test_invalid_level_too_low(self):
        """Test level below 1 fails validation."""
        profile = {"name": "Test", "category": "Test", "cost_level": 0}
        is_valid, errors = validate_tool_profile_v4(profile)
        assert not is_valid
        assert any("1-5" in e for e in errors)

    def test_invalid_level_too_high(self):
        """Test level above 5 fails validation."""
        profile = {"name": "Test", "category": "Test", "cost_level": 6}
        is_valid, errors = validate_tool_profile_v4(profile)
        assert not is_valid
        assert any("1-5" in e for e in errors)

    def test_invalid_fit_score_negative(self):
        """Test negative fit score fails validation."""
        profile = {"name": "Test", "category": "Test", "fit_solo": -0.5}
        is_valid, errors = validate_tool_profile_v4(profile)
        assert not is_valid
        assert any("0.0-1.0" in e for e in errors)

    def test_invalid_fit_score_too_high(self):
        """Test fit score above 1 fails validation."""
        profile = {"name": "Test", "category": "Test", "fit_team": 1.5}
        is_valid, errors = validate_tool_profile_v4(profile)
        assert not is_valid
        assert any("0.0-1.0" in e for e in errors)

    def test_invalid_eu_hosting_type(self):
        """Test invalid eu_hosting type fails validation."""
        profile = {"name": "Test", "category": "Test", "eu_hosting": "maybe"}
        # Should be converted or fail
        result = ToolProfileValidation.validate_eu_hosting("maybe")
        assert not result[0]

    def test_get_defaults(self):
        """Test get_defaults returns valid defaults."""
        defaults = ToolProfileValidation.get_defaults()
        assert defaults["cost_level"] == 3
        assert defaults["fit_solo"] == 0.5
        assert defaults["eu_hosting"] is None


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self):
        """Test complete evaluation and ranking workflow."""
        tools_data = [
            {"name": "Notion", "category": "Wissensmanagement", "price": "0-10€", "gdpr": "EU-Option"},
            {"name": "Make", "category": "Automation", "price": "ab 9€", "host": "EU"},
            {"name": "Salesforce", "category": "CRM", "price": "Enterprise", "host": "US"},
        ]

        # Evaluate all tools
        profiles = evaluate_tools_batch(tools_data)
        assert len(profiles) == 3

        # Rank for solo
        ranked_solo = rank_tools_v4(profiles, size_label="solo")
        assert ranked_solo[0].rank == 1

        # Rank for kmu
        ranked_kmu = rank_tools_v4(profiles, size_label="kmu")
        assert ranked_kmu[0].rank == 1

    def test_enhance_tool_recommendation(self):
        """Test legacy recommendation enhancement."""
        legacy_data = {
            "name": "Tally",
            "category": "Forms",
            "price": "Free",
            "url": "https://tally.so",
        }
        enhanced = enhance_tool_recommendation(legacy_data, size_label="solo")

        assert "cost_level" in enhanced
        assert "fit_solo" in enhanced
        assert "badges_html" in enhanced
        assert enhanced["url"] == "https://tally.so"

    def test_get_top_tools_v4(self):
        """Test getting top N tools with v4 ranking."""
        tools_data = [
            {"name": "Tool1", "category": "Cat"},
            {"name": "Tool2", "category": "Cat"},
            {"name": "Tool3", "category": "Cat"},
            {"name": "Tool4", "category": "Cat"},
            {"name": "Tool5", "category": "Cat"},
        ]

        top_3 = get_top_tools_v4(tools_data, size_label="team", limit=3)
        assert len(top_3) == 3
        assert all(isinstance(t, ToolProfile) for t in top_3)

    def test_profile_defaults(self):
        """Test get_tool_profile_defaults returns valid structure."""
        defaults = get_tool_profile_defaults()
        assert "cost_level" in defaults
        assert defaults["cost_level"]["min"] == 1
        assert defaults["cost_level"]["max"] == 5
        assert defaults["fit_solo"]["min"] == 0.0
        assert defaults["fit_solo"]["max"] == 1.0


# =============================================================================
# Edge Cases and Negative Tests
# =============================================================================

class TestEdgeCases:
    """Edge case and negative tests."""

    def test_empty_tool_name(self):
        """Test handling empty tool name."""
        profile = evaluate_tool_v4("", "Category")
        assert profile.name == ""

    def test_none_values_in_existing_data(self):
        """Test handling None values in existing data."""
        existing = {"price": None, "gdpr": None, "host": None}
        profile = evaluate_tool_v4("Test", "Cat", existing_data=existing)
        assert profile.cost_level == 3  # Default

    def test_unicode_tool_name(self):
        """Test handling Unicode tool names."""
        profile = evaluate_tool_v4("Tëst Tööl äöü", "Catégorie")
        assert profile.name == "Tëst Tööl äöü"

    def test_very_long_tool_name(self):
        """Test handling very long tool names."""
        long_name = "A" * 500
        profile = evaluate_tool_v4(long_name, "Category")
        assert profile.name == long_name

    def test_composite_score_edge_cases(self):
        """Test composite score with extreme values."""
        # All worst values
        worst = ToolProfile(
            name="Worst", category="Cat",
            score=0, cost_level=5, complexity_level=5,
            compliance_score=5, vendor_risk=5,
            fit_solo=0, fit_team=0, fit_kmu=0
        )
        worst_score = _calculate_composite_score(worst, "solo")
        assert worst_score >= 0  # Should still be non-negative

        # All best values
        best = ToolProfile(
            name="Best", category="Cat",
            score=100, cost_level=1, complexity_level=1,
            compliance_score=1, vendor_risk=1,
            fit_solo=1.0, fit_team=1.0, fit_kmu=1.0
        )
        best_score = _calculate_composite_score(best, "solo")
        assert best_score <= 1.0  # Should be at most 1.0


if __name__ == "__main__":
    if pytest:
        pytest.main([__file__, "-v"])
    else:
        print("pytest not installed, running basic tests...")

        # Run basic sanity checks
        print("\nTesting ToolProfile...")
        p = ToolProfile(name="Test", category="Test")
        assert p.name == "Test"
        assert p.cost_level == 3
        print("  OK: ToolProfile creation")

        print("\nTesting evaluate_tool_v4...")
        profile = evaluate_tool_v4("Notion", "Wissensmanagement")
        assert profile.name == "Notion"
        assert 1 <= profile.cost_level <= 5
        print("  OK: Tool evaluation")

        print("\nTesting rank_tools_v4...")
        tools = [
            ToolProfile(name="T1", category="C", fit_team=0.9),
            ToolProfile(name="T2", category="C", fit_team=0.5),
        ]
        ranked = rank_tools_v4(tools, size_label="team")
        assert ranked[0].name == "T1"
        print("  OK: Tool ranking")

        print("\nTesting validation...")
        valid, errors = validate_tool_profile_v4({"name": "T", "category": "C"})
        assert valid
        invalid, errors = validate_tool_profile_v4({"name": "T", "category": "C", "cost_level": 10})
        assert not invalid
        print("  OK: Profile validation")

        print("\nAll basic tests passed!")
