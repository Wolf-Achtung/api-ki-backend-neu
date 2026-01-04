# -*- coding: utf-8 -*-
"""
Tests für Sprint B2.2 – Tools × Funding Alignment.

Prüft:
1. tools_funding_alignment.py: Matching Engine
2. tools_starter_kits.py: Starter-Kit Generator
3. gpt_analyze.py Integration
4. Dashboard Endpoints
5. ENV-Variablen

Version: 1.0.0 (Sprint B2.2)
"""
import os
import sys
import pytest

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestToolsFundingAlignmentEngine:
    """Test TASK A: Tools-Funding Alignment Matching Engine."""

    def test_module_imports(self):
        """tools_funding_alignment module should be importable."""
        from services import tools_funding_alignment
        assert tools_funding_alignment is not None

    def test_match_tool_to_funding_returns_match(self):
        """match_tool_to_funding should return ToolFundingMatch."""
        from services.tools_funding_alignment import match_tool_to_funding, ToolFundingMatch

        program = {
            "id": "go_digital",
            "name": "go-digital",
            "ki_relevance": "high",
            "complexity": "low",
            "branches": ["all"],
        }
        tool = {
            "name": "Make (Integromat)",
            "category": "Workflow-Automation",
            "best_for_size": ["solo", "team", "kmu"],
            "best_for_industries": ["alle"],
        }

        match = match_tool_to_funding(program, tool, size_label="solo")

        assert isinstance(match, ToolFundingMatch)
        assert match.tool_name == "Make (Integromat)"
        assert match.funding_program_id == "go_digital"
        assert 0.0 <= match.alignment_score <= 1.0

    def test_calculate_alignment_for_profile_solo(self):
        """Solo profile should get alignment results."""
        from services.tools_funding_alignment import calculate_alignment_for_profile, AlignmentResult

        profile = {
            "unternehmensgroesse": "solo",
            "branche": "beratung",
            "region": "DE",
        }

        result = calculate_alignment_for_profile(profile)

        assert isinstance(result, AlignmentResult)
        assert result.segment_context.get("size_label") == "solo"

    def test_calculate_alignment_for_profile_team(self):
        """Team profile should get alignment results."""
        from services.tools_funding_alignment import calculate_alignment_for_profile

        profile = {
            "unternehmensgroesse": "team",
            "branche": "finanzen",
        }

        result = calculate_alignment_for_profile(profile)

        assert result.segment_context.get("size_label") == "team"

    def test_calculate_alignment_for_profile_kmu(self):
        """KMU profile should get alignment results."""
        from services.tools_funding_alignment import calculate_alignment_for_profile

        profile = {
            "unternehmensgroesse": "kmu",
            "branche": "it_software",
        }

        result = calculate_alignment_for_profile(profile)

        assert result.segment_context.get("size_label") == "kmu"

    def test_alignment_scores_bounded(self):
        """Alignment scores should be between 0 and 1."""
        from services.tools_funding_alignment import calculate_alignment_for_profile

        profile = {"unternehmensgroesse": "team", "branche": "beratung"}
        result = calculate_alignment_for_profile(profile)

        for match in result.matches:
            assert 0.0 <= match.alignment_score <= 1.0
            assert 0.0 <= match.combined_score <= 1.0

    def test_alignment_type_categories(self):
        """Alignment type should be direct, complementary, or prerequisite."""
        from services.tools_funding_alignment import calculate_alignment_for_profile

        profile = {"unternehmensgroesse": "team"}
        result = calculate_alignment_for_profile(profile)

        valid_types = {"direct", "complementary", "prerequisite"}
        for match in result.matches:
            assert match.alignment_type in valid_types

    def test_generate_alignment_html_de(self):
        """Should generate German HTML output."""
        from services.tools_funding_alignment import (
            calculate_alignment_for_profile,
            generate_alignment_html,
        )

        profile = {"unternehmensgroesse": "team"}
        result = calculate_alignment_for_profile(profile)
        html = generate_alignment_html(result, lang="de")

        if result.matches:
            assert "Tool- &amp; Förder-Alignment" in html or "Alignment" in html
            assert "html" in html.lower() or "<" in html

    def test_generate_alignment_compact_html(self):
        """Should generate compact HTML output."""
        from services.tools_funding_alignment import (
            calculate_alignment_for_profile,
            generate_alignment_compact_html,
        )

        profile = {"unternehmensgroesse": "solo"}
        result = calculate_alignment_for_profile(profile)
        html = generate_alignment_compact_html(result, lang="de")

        # May be empty if no matches
        assert isinstance(html, str)

    def test_inject_alignment_into_sections(self):
        """Should inject alignment HTML into sections dict."""
        from services.tools_funding_alignment import inject_alignment_into_sections

        sections = {"SIZE_LABEL": "team", "BRANCH_LABEL": "beratung"}
        result = inject_alignment_into_sections(sections, lang="de")

        assert "TOOLS_FUNDING_ALIGNMENT_HTML" in result
        assert "TOOLS_FUNDING_ALIGNMENT_COMPACT_HTML" in result


class TestStarterKitGenerator:
    """Test TASK B: Starter-Kit Generator."""

    def test_module_imports(self):
        """tools_starter_kits module should be importable."""
        from services import tools_starter_kits
        assert tools_starter_kits is not None

    def test_generate_starter_kit_solo(self):
        """Solo should get appropriate starter kit."""
        from services.tools_starter_kits import generate_starter_kit, StarterKit

        profile = {"unternehmensgroesse": "solo", "branche": "beratung"}
        kit = generate_starter_kit(profile)

        assert isinstance(kit, StarterKit)
        assert "solo" in kit.segment_label.lower()
        assert len(kit.tools) > 0

    def test_generate_starter_kit_team(self):
        """Team should get appropriate starter kit."""
        from services.tools_starter_kits import generate_starter_kit

        profile = {"unternehmensgroesse": "team", "branche": "it"}
        kit = generate_starter_kit(profile)

        assert "team" in kit.segment_label.lower()
        assert len(kit.tools) > 0
        assert len(kit.funding) > 0

    def test_generate_starter_kit_kmu(self):
        """KMU should get appropriate starter kit."""
        from services.tools_starter_kits import generate_starter_kit

        profile = {"unternehmensgroesse": "kmu", "branche": "finanzen"}
        kit = generate_starter_kit(profile)

        assert "kmu" in kit.segment_label.lower()
        assert len(kit.tools) > 0
        assert kit.estimated_total_days > 0

    def test_starter_kit_tools_have_required_fields(self):
        """Starter kit tools should have all required fields."""
        from services.tools_starter_kits import generate_starter_kit

        profile = {"unternehmensgroesse": "team"}
        kit = generate_starter_kit(profile)

        for tool in kit.tools:
            assert tool.name
            assert tool.category
            assert tool.purpose
            assert tool.priority in [1, 2, 3]
            assert tool.estimated_setup_days >= 0

    def test_starter_kit_funding_have_required_fields(self):
        """Starter kit funding programs should have all required fields."""
        from services.tools_starter_kits import generate_starter_kit

        profile = {"unternehmensgroesse": "team"}
        kit = generate_starter_kit(profile)

        for funding in kit.funding:
            assert funding.program_id
            assert funding.name
            assert funding.provider
            assert funding.max_amount
            assert funding.application_complexity in ["low", "medium", "high"]

    def test_starter_kit_checklist_ordered(self):
        """Checklist steps should be ordered."""
        from services.tools_starter_kits import generate_starter_kit

        profile = {"unternehmensgroesse": "kmu"}
        kit = generate_starter_kit(profile)

        steps = [c.step for c in kit.checklist]
        assert steps == sorted(steps)

    def test_generate_starter_kit_html(self):
        """Should generate HTML output for starter kit."""
        from services.tools_starter_kits import generate_starter_kit, generate_starter_kit_html

        profile = {"unternehmensgroesse": "solo"}
        kit = generate_starter_kit(profile)
        html = generate_starter_kit_html(kit, lang="de")

        assert "Starter" in html or "Kit" in html
        assert "<" in html  # Contains HTML

    def test_generate_starter_kit_compact_html(self):
        """Should generate compact HTML output."""
        from services.tools_starter_kits import generate_starter_kit, generate_starter_kit_compact_html

        profile = {"unternehmensgroesse": "team"}
        kit = generate_starter_kit(profile)
        html = generate_starter_kit_compact_html(kit, lang="de")

        assert isinstance(html, str)

    def test_inject_starter_kit_into_sections(self):
        """Should inject starter kit HTML into sections dict."""
        from services.tools_starter_kits import inject_starter_kit_into_sections

        sections = {"SIZE_LABEL": "solo", "BRANCH_LABEL": "beratung"}
        result = inject_starter_kit_into_sections(sections, lang="de")

        assert "STARTER_KIT_HTML" in result
        assert "STARTER_KIT_COMPACT_HTML" in result

    def test_starter_kit_to_dict(self):
        """StarterKit.to_dict() should work correctly."""
        from services.tools_starter_kits import generate_starter_kit

        profile = {"unternehmensgroesse": "team"}
        kit = generate_starter_kit(profile)
        data = kit.to_dict()

        assert "kit_id" in data
        assert "kit_name" in data
        assert "tools" in data
        assert "funding" in data
        assert "checklist" in data
        assert isinstance(data["tools"], list)


class TestAlignmentDataModels:
    """Test data models for alignment."""

    def test_tool_funding_match_to_dict(self):
        """ToolFundingMatch.to_dict() should work correctly."""
        from services.tools_funding_alignment import ToolFundingMatch

        match = ToolFundingMatch(
            tool_name="Test Tool",
            tool_category="Test Category",
            funding_program_id="test_prog",
            funding_program_name="Test Program",
            alignment_score=0.75,
            match_reasons=["Reason 1"],
            alignment_type="direct",
        )

        data = match.to_dict()

        assert data["tool_name"] == "Test Tool"
        assert data["alignment_score"] == 0.75
        assert "match_reasons" in data

    def test_alignment_result_to_dict(self):
        """AlignmentResult.to_dict() should work correctly."""
        from services.tools_funding_alignment import calculate_alignment_for_profile

        profile = {"unternehmensgroesse": "solo"}
        result = calculate_alignment_for_profile(profile)
        data = result.to_dict()

        assert "matches" in data
        assert "segment_context" in data
        assert "recommended_starter_tools" in data
        assert "recommended_funding_programs" in data


class TestCategoryMappings:
    """Test tool category to funding area mappings."""

    def test_tool_category_mapping_exists(self):
        """TOOL_CATEGORY_TO_FUNDING_AREA should have entries."""
        from services.tools_funding_alignment import TOOL_CATEGORY_TO_FUNDING_AREA

        assert len(TOOL_CATEGORY_TO_FUNDING_AREA) > 0
        assert "workflow-automation" in TOOL_CATEGORY_TO_FUNDING_AREA
        assert "ki-api" in TOOL_CATEGORY_TO_FUNDING_AREA

    def test_funding_focus_areas_exists(self):
        """FUNDING_FOCUS_AREAS should have entries."""
        from services.tools_funding_alignment import FUNDING_FOCUS_AREAS

        assert len(FUNDING_FOCUS_AREAS) > 0
        assert "go_digital" in FUNDING_FOCUS_AREAS
        assert "zim" in FUNDING_FOCUS_AREAS

    def test_size_compatibility_matrix(self):
        """SIZE_COMPATIBILITY should have all sizes."""
        from services.tools_funding_alignment import SIZE_COMPATIBILITY

        assert "solo" in SIZE_COMPATIBILITY
        assert "team" in SIZE_COMPATIBILITY
        assert "kmu" in SIZE_COMPATIBILITY


class TestStarterKitTemplates:
    """Test starter kit templates."""

    def test_tool_templates_exist(self):
        """TOOL_TEMPLATES should have all sizes."""
        from services.tools_starter_kits import TOOL_TEMPLATES

        assert "solo" in TOOL_TEMPLATES
        assert "team" in TOOL_TEMPLATES
        assert "kmu" in TOOL_TEMPLATES

    def test_funding_templates_exist(self):
        """FUNDING_TEMPLATES should have all sizes."""
        from services.tools_starter_kits import FUNDING_TEMPLATES

        assert "solo" in FUNDING_TEMPLATES
        assert "team" in FUNDING_TEMPLATES
        assert "kmu" in FUNDING_TEMPLATES

    def test_checklist_templates_exist(self):
        """CHECKLIST_TEMPLATES should have all sizes."""
        from services.tools_starter_kits import CHECKLIST_TEMPLATES

        assert "solo" in CHECKLIST_TEMPLATES
        assert "team" in CHECKLIST_TEMPLATES
        assert "kmu" in CHECKLIST_TEMPLATES


class TestAPIResponse:
    """Test API response functions."""

    def test_get_alignment_api_response(self):
        """get_alignment_api_response should return valid dict."""
        from services.tools_funding_alignment import get_alignment_api_response

        response = get_alignment_api_response(
            briefing={"unternehmensgroesse": "team"},
            lang="de"
        )

        assert "enabled" in response
        assert "matches" in response or "error" in response

    def test_get_starter_kit_api_response(self):
        """get_starter_kit_api_response should return valid dict."""
        from services.tools_starter_kits import get_starter_kit_api_response

        response = get_starter_kit_api_response(
            briefing={"unternehmensgroesse": "solo"},
            lang="de"
        )

        assert "enabled" in response
        assert "kit" in response or "error" in response


class TestENVConfiguration:
    """Test ENV variable configuration."""

    def test_alignment_min_score_env(self):
        """ALIGNMENT_MIN_SCORE should be configurable."""
        from services.tools_funding_alignment import ALIGNMENT_MIN_SCORE

        assert isinstance(ALIGNMENT_MIN_SCORE, float)
        assert 0.0 <= ALIGNMENT_MIN_SCORE <= 1.0

    def test_alignment_max_recommendations_env(self):
        """ALIGNMENT_MAX_RECOMMENDATIONS should be configurable."""
        from services.tools_funding_alignment import ALIGNMENT_MAX_RECOMMENDATIONS

        assert isinstance(ALIGNMENT_MAX_RECOMMENDATIONS, int)
        assert ALIGNMENT_MAX_RECOMMENDATIONS > 0

    def test_starter_kits_enabled_env(self):
        """STARTER_KITS_ENABLED should be configurable."""
        from services.tools_starter_kits import STARTER_KITS_ENABLED

        assert isinstance(STARTER_KITS_ENABLED, bool)

    def test_starter_kit_max_tools_env(self):
        """STARTER_KIT_MAX_TOOLS should be configurable."""
        from services.tools_starter_kits import STARTER_KIT_MAX_TOOLS

        assert isinstance(STARTER_KIT_MAX_TOOLS, int)
        assert STARTER_KIT_MAX_TOOLS > 0


def _has_fastapi():
    """Check if fastapi is available."""
    try:
        import fastapi  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _has_fastapi(), reason="FastAPI not installed")
class TestDashboardEndpointModels:
    """Test dashboard route response models."""

    def test_alignment_response_model_import(self):
        """AlignmentResponse model should be importable."""
        from routes.tools_dashboard import AlignmentResponse
        assert AlignmentResponse is not None

    def test_starter_kit_response_model_import(self):
        """StarterKitResponse model should be importable."""
        from routes.tools_dashboard import StarterKitResponse
        assert StarterKitResponse is not None

    def test_alignment_match_response_model_import(self):
        """AlignmentMatchResponse model should be importable."""
        from routes.tools_dashboard import AlignmentMatchResponse
        assert AlignmentMatchResponse is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
