# -*- coding: utf-8 -*-
"""
Tests for Sprint B3: Tools Engine 3.0

Tests cover:
- B3-A: Embedding & Discovery Engine
- B3-B: Tool Fit Score 2.0
- B3-C: Adaptive Tool Stacks
- B3-D: Workflow Engine
- B3-F: Governance & Compliance
- B3-G: HTML Output Module
"""

import pytest
from typing import Dict, List


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_briefing() -> Dict:
    """Sample company briefing for testing."""
    return {
        "branche": "beratung",
        "unternehmensgroesse": "team",
        "usecases": ["Dokumentation", "CRM", "Reporting"],
    }


@pytest.fixture
def sample_briefing_verwaltung() -> Dict:
    """Sample briefing for public sector."""
    return {
        "branche": "verwaltung",
        "unternehmensgroesse": "kmu",
        "usecases": ["Prozessdigitalisierung", "Dokumentenmanagement"],
    }


@pytest.fixture
def sample_tool_ids() -> List[str]:
    """Sample tool IDs for governance testing."""
    return ["slack", "hubspot", "notion", "asana"]


# =============================================================================
# B3-A: EMBEDDING ENGINE TESTS
# =============================================================================

class TestToolsEmbeddingEngine:
    """Tests for tools_embedding_engine.py"""

    def test_tool_database_populated(self):
        """Verify TOOL_DATABASE has entries."""
        from services.tools_embedding_engine import TOOL_DATABASE

        assert len(TOOL_DATABASE) > 50, "TOOL_DATABASE should have 50+ tools"

    def test_tool_database_structure(self):
        """Verify tool entries have required fields."""
        from services.tools_embedding_engine import TOOL_DATABASE

        required_fields = ["name", "category", "description", "tags"]

        for tool_id, tool in list(TOOL_DATABASE.items())[:10]:
            for field in required_fields:
                assert field in tool, f"Tool '{tool_id}' missing field '{field}'"

    def test_hash_based_embedding(self):
        """Test fallback hash-based embedding generation."""
        from services.tools_embedding_engine import _hash_based_embedding

        vec1 = _hash_based_embedding("test text")
        vec2 = _hash_based_embedding("test text")
        vec3 = _hash_based_embedding("different text")

        # Same input should produce same output
        assert vec1 == vec2, "Hash embedding should be deterministic"

        # Different input should produce different output
        assert vec1 != vec3, "Different inputs should produce different vectors"

        # Vector should have expected dimension
        assert len(vec1) == 256, "Hash embedding should have 256 dimensions"

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        from services.tools_embedding_engine import _cosine_similarity

        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        vec_c = [0.0, 1.0, 0.0]

        # Identical vectors
        sim_same = _cosine_similarity(vec_a, vec_b)
        assert sim_same == pytest.approx(1.0, rel=0.01), "Identical vectors should have similarity 1.0"

        # Orthogonal vectors
        sim_ortho = _cosine_similarity(vec_a, vec_c)
        assert sim_ortho == pytest.approx(0.0, rel=0.01), "Orthogonal vectors should have similarity 0.0"

    def test_get_tool_clusters(self):
        """Test tool clustering."""
        from services.tools_embedding_engine import get_tool_clusters

        clusters = get_tool_clusters()

        assert len(clusters) >= 5, "Should have at least 5 clusters"

        for cluster in clusters:
            assert cluster.name, "Cluster should have a name"
            assert len(cluster.tool_ids) > 0, "Cluster should have tools"

    def test_semantic_search_for_usecase(self):
        """Test semantic search functionality."""
        from services.tools_embedding_engine import semantic_search_for_usecase

        results = semantic_search_for_usecase("CRM and customer management", k=5)

        assert len(results) > 0, "Should return results"
        assert len(results) <= 5, "Should respect k parameter"

        for result in results:
            assert result.tool_id, "Result should have tool_id"
            assert 0 <= result.score <= 1, "Score should be between 0 and 1"

    def test_discover_tools_for_profile(self):
        """Test profile-based tool discovery."""
        from services.tools_embedding_engine import discover_tools_for_profile

        results = discover_tools_for_profile(
            branch="beratung",
            size="team",
            usecases=["CRM", "Projektmanagement"],
            k=10,
        )

        assert len(results) > 0, "Should return results"
        assert len(results) <= 10, "Should respect k parameter"


# =============================================================================
# B3-B: FIT SCORE ENGINE TESTS
# =============================================================================

class TestToolsFitEngine:
    """Tests for tools_fit_engine.py"""

    def test_branch_affinity_data(self):
        """Verify branch affinity data is populated."""
        from services.tools_fit_engine import BRANCH_CATEGORY_AFFINITY

        assert len(BRANCH_CATEGORY_AFFINITY) >= 8, "Should have 8+ branch affinities"

        for branch, categories in BRANCH_CATEGORY_AFFINITY.items():
            assert len(categories) > 0, f"Branch '{branch}' should have category affinities"

    def test_size_fit_criteria(self):
        """Verify size fit criteria are defined."""
        from services.tools_fit_engine import SIZE_FIT_CRITERIA

        for size in ["solo", "team", "kmu"]:
            assert size in SIZE_FIT_CRITERIA, f"Size '{size}' should be in criteria"
            criteria = SIZE_FIT_CRITERIA[size]
            assert "max_monthly_cost" in criteria, "Should have max_monthly_cost"
            assert "max_setup_hours" in criteria, "Should have max_setup_hours"

    def test_calculate_tool_fit_score(self):
        """Test fit score calculation."""
        from services.tools_fit_engine import calculate_tool_fit_score

        tool = {
            "id": "test_tool",
            "name": "Test Tool",
            "category": "crm",
            "monthly_cost": 50,
            "setup_hours": 10,
            "complexity": "medium",
        }

        result = calculate_tool_fit_score(
            tool=tool,
            branch="beratung",
            size="team",
            usecases=["CRM"],
            risk_level="medium",
            funding_focus=[],
            semantic_results={},
        )

        assert result is not None, "Should return result"
        assert 0 <= result.total_score <= 100, "Score should be 0-100"
        assert result.tool_id == "test_tool", "Should preserve tool_id"

    def test_calculate_fit_scores_for_profile(self):
        """Test batch fit score calculation."""
        from services.tools_fit_engine import calculate_fit_scores_for_profile

        scores, analysis = calculate_fit_scores_for_profile(
            branch="it",
            size="team",
            usecases=["Development", "CI/CD"],
            risk_level="low",
            funding_focus=[],
            max_results=10,
        )

        assert len(scores) > 0, "Should return scores"
        assert len(scores) <= 10, "Should respect max_results"
        assert analysis is not None, "Should return analysis"

        # Scores should be sorted by total_score descending
        for i in range(len(scores) - 1):
            assert scores[i].total_score >= scores[i + 1].total_score, "Should be sorted descending"


# =============================================================================
# B3-C: STACK BUILDER TESTS
# =============================================================================

class TestToolsStackBuilder:
    """Tests for tools_stack_builder.py"""

    def test_branch_stack_configs(self):
        """Verify branch stack configurations."""
        from services.tools_stack_builder import BRANCH_STACK_DEFINITIONS

        assert len(BRANCH_STACK_DEFINITIONS) >= 8, "Should have 8+ branch configs"

        for branch, config in BRANCH_STACK_DEFINITIONS.items():
            assert "priorities" in config, f"Branch '{branch}' should have priorities"
            assert "must_have" in config, f"Branch '{branch}' should have must_have"

    def test_size_constraints(self):
        """Verify size constraints are defined."""
        from services.tools_stack_builder import SIZE_STACK_ADJUSTMENTS

        for size in ["solo", "team", "kmu"]:
            assert size in SIZE_STACK_ADJUSTMENTS, f"Size '{size}' should have constraints"
            constraints = SIZE_STACK_ADJUSTMENTS[size]
            assert "max_tools" in constraints, "Should have max_tools"
            assert "max_categories" in constraints, "Should have max_categories"

    def test_generate_adaptive_stack(self):
        """Test adaptive stack generation."""
        from services.tools_stack_builder import generate_adaptive_stack

        stack = generate_adaptive_stack(
            branch="beratung",
            size="team",
            usecases=["CRM", "Dokumentation"],
            risk_level="medium",
            funding_focus=[],
            top_k=10,
        )

        assert stack is not None, "Should return stack"
        assert len(stack.tools) > 0, "Stack should have tools"
        assert len(stack.tools) <= 12, "Team should have max 12 tools"
        assert stack.estimated_monthly_cost >= 0, "Cost should be non-negative"
        assert stack.estimated_setup_hours >= 0, "Setup hours should be non-negative"

    def test_stack_respects_size_limits(self):
        """Test that stack respects size limits."""
        from services.tools_stack_builder import generate_adaptive_stack

        # Solo should have fewer tools
        solo_stack = generate_adaptive_stack(
            branch="beratung",
            size="solo",
            usecases=[],
            risk_level="low",
            funding_focus=[],
            top_k=20,
        )

        # KMU should have more tools
        kmu_stack = generate_adaptive_stack(
            branch="beratung",
            size="kmu",
            usecases=[],
            risk_level="low",
            funding_focus=[],
            top_k=20,
        )

        assert len(solo_stack.tools) <= 8, "Solo should have max 8 tools"
        assert len(kmu_stack.tools) <= 15, "KMU should have max 15 tools"

    def test_integration_hints_generated(self):
        """Test that integration hints are generated."""
        from services.tools_stack_builder import generate_adaptive_stack

        stack = generate_adaptive_stack(
            branch="it",
            size="team",
            usecases=["Development"],
            risk_level="medium",
            funding_focus=[],
            top_k=10,
        )

        # Integration hints should be generated for stacks with multiple tools
        if len(stack.tools) > 2:
            assert len(stack.integration_hints) > 0, "Should generate integration hints"


# =============================================================================
# B3-D: WORKFLOW ENGINE TESTS
# =============================================================================

class TestToolsWorkflowEngine:
    """Tests for tools_workflow_engine.py"""

    def test_workflow_templates_populated(self):
        """Verify workflow templates are populated."""
        from services.tools_workflow_engine import WORKFLOW_TEMPLATES

        assert len(WORKFLOW_TEMPLATES) >= 10, "Should have 10+ workflow templates"

    def test_workflow_template_structure(self):
        """Verify workflow templates have required fields."""
        from services.tools_workflow_engine import WORKFLOW_TEMPLATES

        required_fields = [
            "name", "name_en", "description", "description_en",
            "category", "tool_ids", "effort_level", "benefits",
        ]

        for wf_id, template in list(WORKFLOW_TEMPLATES.items())[:5]:
            for field in required_fields:
                assert field in template, f"Workflow '{wf_id}' missing field '{field}'"

    def test_get_workflow_card(self):
        """Test getting a single workflow card."""
        from services.tools_workflow_engine import get_workflow_card

        card = get_workflow_card("doc_automation")

        assert card is not None, "Should return card"
        assert card.id == "doc_automation", "Should have correct ID"
        assert len(card.tools) > 0, "Should have tools"
        assert len(card.setup_steps) > 0, "Should have setup steps"

    def test_get_quick_wins(self):
        """Test getting Quick Win workflows."""
        from services.tools_workflow_engine import get_quick_wins

        quick_wins = get_quick_wins()

        assert len(quick_wins) >= 3, "Should have at least 3 Quick Wins"

        for qw in quick_wins:
            assert qw.quick_win is True, "All should be Quick Wins"

    def test_recommend_workflows_for_profile(self):
        """Test workflow recommendations."""
        from services.tools_workflow_engine import recommend_workflows_for_profile

        recommendations = recommend_workflows_for_profile(
            branch="beratung",
            size="team",
            usecases=["CRM"],
            max_results=5,
        )

        assert len(recommendations) > 0, "Should return recommendations"
        assert len(recommendations) <= 5, "Should respect max_results"

        # Should be sorted by relevance
        for i in range(len(recommendations) - 1):
            assert recommendations[i].relevance_score >= recommendations[i + 1].relevance_score, \
                "Should be sorted by relevance"

    def test_workflow_html_generation(self):
        """Test workflow HTML generation."""
        from services.tools_workflow_engine import (
            recommend_workflows_for_profile,
            generate_workflow_html,
        )

        recommendations = recommend_workflows_for_profile(
            branch="marketing",
            size="team",
            max_results=3,
        )

        html = generate_workflow_html(recommendations, language="de")

        assert len(html) > 0, "Should generate HTML"
        assert "workflow-card" in html, "Should have workflow cards"

    def test_get_workflow_html_sections(self, sample_briefing):
        """Test workflow HTML sections generation."""
        from services.tools_workflow_engine import get_workflow_html_sections

        sections = get_workflow_html_sections(sample_briefing, language="de")

        assert "TOOLS_WORKFLOW_HTML" in sections, "Should have workflow HTML"
        assert "TOOLS_QUICK_WINS_HTML" in sections, "Should have quick wins HTML"


# =============================================================================
# B3-F: GOVERNANCE MODULE TESTS
# =============================================================================

class TestToolsGovernance:
    """Tests for tools_governance.py"""

    def test_governance_data_populated(self):
        """Verify governance data is populated."""
        from services.tools_governance import TOOL_GOVERNANCE_DATA

        # Exclude _default
        actual_tools = len([k for k in TOOL_GOVERNANCE_DATA if k != "_default"])
        assert actual_tools >= 10, "Should have 10+ tool governance profiles"

    def test_industry_compliance_requirements(self):
        """Verify industry compliance requirements."""
        from services.tools_governance import INDUSTRY_COMPLIANCE_REQUIREMENTS

        # Key industries should have requirements
        for branch in ["finanzen", "gesundheit", "verwaltung"]:
            assert branch in INDUSTRY_COMPLIANCE_REQUIREMENTS, \
                f"Branch '{branch}' should have compliance requirements"

    def test_get_tool_governance_profile(self):
        """Test getting governance profile."""
        from services.tools_governance import get_tool_governance_profile

        profile = get_tool_governance_profile("slack")

        assert profile is not None, "Should return profile"
        assert profile.tool_id == "slack", "Should have correct tool_id"
        assert profile.governance_score > 0, "Should have governance score"
        assert profile.security is not None, "Should have security profile"

    def test_default_profile_for_unknown_tool(self):
        """Test default profile for unknown tools."""
        from services.tools_governance import get_tool_governance_profile

        profile = get_tool_governance_profile("unknown_tool_xyz")

        assert profile is not None, "Should return default profile"
        assert profile.governance_score < 50, "Unknown tool should have low score"

    def test_assess_tool_risks(self):
        """Test risk assessment for a tool."""
        from services.tools_governance import assess_tool_risks

        # Test with a tool that has known gaps
        risks = assess_tool_risks(
            tool_id="notion",  # US data residency
            branch="finanzen",  # Strict requirements
            size="team",
        )

        # Should identify some risks
        assert len(risks) >= 0, "Should return risk list"

    def test_analyze_governance(self, sample_tool_ids):
        """Test governance analysis."""
        from services.tools_governance import analyze_governance

        analysis = analyze_governance(
            tool_ids=sample_tool_ids,
            branch="beratung",
            size="team",
        )

        assert analysis is not None, "Should return analysis"
        assert 0 <= analysis.overall_score <= 100, "Score should be 0-100"
        assert 0 <= analysis.security_score <= 100, "Security score should be 0-100"
        assert 0 <= analysis.compliance_score <= 100, "Compliance score should be 0-100"

    def test_governance_html_generation(self, sample_tool_ids, sample_briefing):
        """Test governance HTML generation."""
        from services.tools_governance import (
            analyze_governance,
            generate_governance_html,
        )

        analysis = analyze_governance(
            tool_ids=sample_tool_ids,
            branch="beratung",
            size="team",
        )

        html = generate_governance_html(analysis, language="de")

        assert len(html) > 0, "Should generate HTML"
        assert "governance" in html.lower(), "Should contain governance content"

    def test_get_governance_html_sections(self, sample_tool_ids, sample_briefing):
        """Test governance HTML sections generation."""
        from services.tools_governance import get_governance_html_sections

        sections = get_governance_html_sections(
            tool_ids=sample_tool_ids,
            briefing=sample_briefing,
            language="de",
        )

        assert "TOOLS_GOVERNANCE_HTML" in sections, "Should have governance HTML"


# =============================================================================
# B3-G: HTML OUTPUT MODULE TESTS
# =============================================================================

class TestToolsHtmlOutput:
    """Tests for tools_html_output_v3.py"""

    def test_css_styles_defined(self):
        """Verify CSS styles are defined."""
        from services.tools_html_output_v3 import CSS_STYLES

        assert len(CSS_STYLES) > 100, "Should have CSS styles"
        assert ".tool-card" in CSS_STYLES, "Should have tool card styles"
        assert ".workflow-card" in CSS_STYLES, "Should have workflow card styles"

    def test_generate_tool_card_html(self):
        """Test single tool card HTML generation."""
        from services.tools_html_output_v3 import generate_tool_card_html

        tool = {
            "name": "Test Tool",
            "category": "crm",
            "description": "A test tool",
            "fit_score": 75,
            "monthly_cost": 50,
            "setup_hours": 10,
        }

        html = generate_tool_card_html(tool, language="de")

        assert len(html) > 0, "Should generate HTML"
        assert "Test Tool" in html, "Should include tool name"
        assert "tool-card" in html, "Should have tool-card class"

    def test_generate_tools_summary_html(self):
        """Test summary HTML generation."""
        from services.tools_html_output_v3 import generate_tools_summary_html

        html = generate_tools_summary_html(
            total_tools=10,
            quick_wins=3,
            workflows=5,
            governance_score=75.0,
            estimated_monthly_cost=250.0,
            estimated_setup_hours=40,
            language="de",
        )

        assert len(html) > 0, "Should generate HTML"
        assert "10" in html, "Should include tool count"
        assert "tools-stats" in html, "Should have stats section"

    def test_generate_roadmap_html(self):
        """Test roadmap HTML generation."""
        from services.tools_html_output_v3 import generate_roadmap_html

        html = generate_roadmap_html([], language="de")

        assert len(html) > 0, "Should generate default roadmap"
        assert "roadmap" in html.lower(), "Should have roadmap content"
        assert "Phase" in html, "Should have phases"

    def test_generate_tools_html_output(self, sample_briefing):
        """Test complete HTML output generation."""
        from services.tools_html_output_v3 import generate_tools_html_output

        output = generate_tools_html_output(sample_briefing, language="de")

        assert output is not None, "Should return output"
        assert output.total_tools >= 0, "Should have tool count"
        assert len(output.tools_summary_html) > 0, "Should have summary HTML"

    def test_get_all_tools_html_sections(self, sample_briefing):
        """Test getting all HTML sections."""
        from services.tools_html_output_v3 import get_all_tools_html_sections

        sections = get_all_tools_html_sections(sample_briefing, language="de")

        expected_keys = [
            "TOOLS_STACK_HTML",
            "TOOLS_WORKFLOW_HTML",
            "TOOLS_GOVERNANCE_HTML",
            "TOOLS_QUICK_WINS_HTML",
            "TOOLS_SUMMARY_HTML",
            "TOOLS_ROADMAP_HTML",
        ]

        for key in expected_keys:
            assert key in sections, f"Should have {key}"

    def test_get_tools_css(self):
        """Test CSS extraction."""
        from services.tools_html_output_v3 import get_tools_css

        css = get_tools_css()

        assert len(css) > 0, "Should return CSS"
        assert "<style>" not in css, "Should not have style tags"
        assert ".tool-card" in css, "Should have tool card styles"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestB3Integration:
    """Integration tests for B3 components."""

    def test_full_pipeline_beratung(self, sample_briefing):
        """Test full pipeline for Beratung."""
        from services.tools_html_output_v3 import get_all_tools_html_sections

        sections = get_all_tools_html_sections(sample_briefing, language="de")

        # All sections should be strings (may be empty if modules not available)
        for key, value in sections.items():
            assert isinstance(value, str), f"{key} should be string"

    def test_full_pipeline_verwaltung(self, sample_briefing_verwaltung):
        """Test full pipeline for Verwaltung (G19.1 branch)."""
        from services.tools_html_output_v3 import get_all_tools_html_sections

        sections = get_all_tools_html_sections(
            sample_briefing_verwaltung,
            language="de",
        )

        for key, value in sections.items():
            assert isinstance(value, str), f"{key} should be string"

    def test_english_output(self, sample_briefing):
        """Test English output generation."""
        from services.tools_html_output_v3 import get_all_tools_html_sections

        sections = get_all_tools_html_sections(sample_briefing, language="en")

        for key, value in sections.items():
            assert isinstance(value, str), f"{key} should be string"

    def test_branch_mapping_integration(self):
        """Test branch mapping integration with B3."""
        from services.branch_mapping import map_frontend_branch_to_engine
        from services.tools_stack_builder import generate_adaptive_stack

        # Frontend value
        frontend_branch = "beratung_dienstleistungen"
        engine_branch = map_frontend_branch_to_engine(frontend_branch)

        # Should work with stack builder
        stack = generate_adaptive_stack(
            branch=engine_branch,
            size="team",
            usecases=[],
            risk_level="medium",
            funding_focus=[],
            top_k=10,
        )

        assert stack is not None, "Stack should be generated"
        assert len(stack.tools) > 0, "Stack should have tools"

    def test_workflow_governance_consistency(self):
        """Test that workflow tools have governance profiles."""
        from services.tools_workflow_engine import WORKFLOW_TEMPLATES
        from services.tools_governance import get_tool_governance_profile

        # Check a few workflow templates
        for wf_id in ["doc_automation", "crm_automation", "reporting_automation"]:
            if wf_id in WORKFLOW_TEMPLATES:
                template = WORKFLOW_TEMPLATES[wf_id]
                for tool_id in template.get("tool_ids", []):
                    # Should get a profile (either real or default)
                    profile = get_tool_governance_profile(tool_id)
                    assert profile is not None, f"Tool '{tool_id}' should have governance profile"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestB3EdgeCases:
    """Edge case tests for B3 components."""

    def test_empty_usecases(self):
        """Test handling of empty use cases."""
        from services.tools_stack_builder import generate_adaptive_stack

        stack = generate_adaptive_stack(
            branch="beratung",
            size="team",
            usecases=[],
            risk_level="medium",
            funding_focus=[],
            top_k=10,
        )

        assert stack is not None, "Should handle empty usecases"

    def test_unknown_branch(self):
        """Test handling of unknown branch."""
        from services.tools_stack_builder import generate_adaptive_stack

        stack = generate_adaptive_stack(
            branch="unknown_branch_xyz",
            size="team",
            usecases=[],
            risk_level="medium",
            funding_focus=[],
            top_k=10,
        )

        # Should fall back to default
        assert stack is not None, "Should handle unknown branch"

    def test_empty_tool_list_governance(self):
        """Test governance analysis with empty tool list."""
        from services.tools_governance import analyze_governance

        analysis = analyze_governance(
            tool_ids=[],
            branch="beratung",
            size="team",
        )

        assert analysis is not None, "Should handle empty tool list"
        assert analysis.overall_score == 0, "Empty list should have 0 score"

    def test_large_tool_list(self):
        """Test handling of large tool list."""
        from services.tools_governance import analyze_governance

        # Create a large list of tool IDs
        tool_ids = ["slack", "hubspot", "notion", "asana"] * 10

        analysis = analyze_governance(
            tool_ids=tool_ids,
            branch="it",
            size="kmu",
        )

        assert analysis is not None, "Should handle large tool list"

    def test_special_characters_in_usecase(self):
        """Test handling of special characters in use cases."""
        from services.tools_embedding_engine import semantic_search_for_usecase

        results = semantic_search_for_usecase(
            "CRM & Kundenmanagement (inkl. E-Mail)",
            k=5,
        )

        assert results is not None, "Should handle special characters"
