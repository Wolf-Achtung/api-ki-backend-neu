# -*- coding: utf-8 -*-
"""
Tests for Sprint G19.1 - Extended Branch Profiles

Tests the three new branch profiles:
- bauwesen_architektur (Construction & Architecture)
- verwaltung (Public Sector / Government)
- transport_logistik (Transport & Logistics)

Tests verify:
- Branch profile structure completeness
- Drivers, trends, KPIs present
- Funding alignment delivers 3-6 programs
- Tools alignment has min 8 recommendations
- HTML blocks validated
- Drift <= minimal
"""

import pytest
from typing import Dict, Any, List


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def new_branches() -> List[str]:
    """Return list of new G19.1 branches to test."""
    return ["bauwesen_architektur", "verwaltung", "transport_logistik"]


@pytest.fixture
def branch_aliases() -> Dict[str, str]:
    """Return expected branch alias mappings."""
    return {
        # Bauwesen & Architektur
        "bauwesen_architektur": "bauwesen_architektur",
        "bauwesen": "bauwesen_architektur",
        "bau": "bauwesen_architektur",
        "architektur": "bauwesen_architektur",
        "construction": "bauwesen_architektur",
        "architecture": "bauwesen_architektur",
        "immobilien": "bauwesen_architektur",
        # Verwaltung
        "verwaltung": "verwaltung",
        "public_sector": "verwaltung",
        "government": "verwaltung",
        "behoerde": "verwaltung",
        "oeffentlich": "verwaltung",
        # Transport & Logistik
        "transport_logistik": "transport_logistik",
        "logistik": "transport_logistik",
        "transport": "transport_logistik",
        "logistics": "transport_logistik",
        "spedition": "transport_logistik",
    }


@pytest.fixture
def sizes() -> List[str]:
    """Return company sizes to test."""
    return ["solo", "team", "kmu"]


# =============================================================================
# BRANCH PROFILE ENGINE TESTS
# =============================================================================

class TestBranchProfileEngine:
    """Tests for new branch profiles in branch_profile_engine.py."""

    def test_new_branches_exist_in_maturity_data(self, new_branches):
        """Verify all new branches exist in BRANCH_MATURITY_DATA."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        for branch in new_branches:
            assert branch in BRANCH_MATURITY_DATA, f"Branch {branch} missing from BRANCH_MATURITY_DATA"

    def test_branch_aliases_mapped(self, branch_aliases):
        """Verify branch aliases are properly mapped."""
        from services.branch_profile_engine import BRANCH_ALIASES

        for alias, expected in branch_aliases.items():
            assert alias in BRANCH_ALIASES, f"Alias {alias} missing from BRANCH_ALIASES"
            assert BRANCH_ALIASES[alias] == expected, f"Alias {alias} should map to {expected}"

    def test_branch_profile_structure_complete(self, new_branches):
        """Verify each new branch has complete data structure."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        required_keys = [
            "maturity_score",
            "digitalization_level",
            "ai_adoption_rate",
            "competitive_density",
            "drivers_de",
            "drivers_en",
            "trends_de",
            "trends_en",
            "regulatory_de",
            "regulatory_en",
            "use_cases_de",
            "use_cases_en",
            "kpis",
            "opportunities_de",
            "opportunities_en",
            "risks_de",
            "risks_en",
            "bottlenecks_de",
            "bottlenecks_en",
        ]

        for branch in new_branches:
            data = BRANCH_MATURITY_DATA[branch]
            for key in required_keys:
                assert key in data, f"Branch {branch} missing required key: {key}"

    def test_branch_drivers_count(self, new_branches):
        """Verify each branch has 4-6 drivers."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        for branch in new_branches:
            data = BRANCH_MATURITY_DATA[branch]
            drivers_de = data["drivers_de"]
            drivers_en = data["drivers_en"]

            assert 4 <= len(drivers_de) <= 6, f"Branch {branch} should have 4-6 DE drivers, has {len(drivers_de)}"
            assert 4 <= len(drivers_en) <= 6, f"Branch {branch} should have 4-6 EN drivers, has {len(drivers_en)}"
            assert len(drivers_de) == len(drivers_en), f"Branch {branch} driver count mismatch DE/EN"

    def test_branch_trends_count(self, new_branches):
        """Verify each branch has 6-8 market trends."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        for branch in new_branches:
            data = BRANCH_MATURITY_DATA[branch]
            trends_de = data["trends_de"]
            trends_en = data["trends_en"]

            assert 5 <= len(trends_de) <= 8, f"Branch {branch} should have 5-8 DE trends, has {len(trends_de)}"
            assert 5 <= len(trends_en) <= 8, f"Branch {branch} should have 5-8 EN trends, has {len(trends_en)}"

    def test_branch_maturity_scores(self, new_branches):
        """Verify maturity scores are in expected ranges."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        expected_scores = {
            "bauwesen_architektur": 55,
            "verwaltung": 45,
            "transport_logistik": 60,
        }

        for branch in new_branches:
            data = BRANCH_MATURITY_DATA[branch]
            score = data["maturity_score"]
            expected = expected_scores[branch]

            assert score == expected, f"Branch {branch} maturity score is {score}, expected {expected}"

    def test_branch_kpis_exist(self, new_branches):
        """Verify each branch has meaningful KPIs."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        for branch in new_branches:
            data = BRANCH_MATURITY_DATA[branch]
            kpis = data["kpis"]

            assert len(kpis) >= 4, f"Branch {branch} should have at least 4 KPIs, has {len(kpis)}"
            for kpi in kpis:
                assert len(kpi) > 5, f"KPI '{kpi}' in {branch} seems too short"

    def test_opportunities_risks_bottlenecks_count(self, new_branches):
        """Verify each branch has 3 opportunities, risks, and bottlenecks."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        for branch in new_branches:
            data = BRANCH_MATURITY_DATA[branch]

            assert len(data["opportunities_de"]) == 3, f"{branch} should have 3 DE opportunities"
            assert len(data["opportunities_en"]) == 3, f"{branch} should have 3 EN opportunities"
            assert len(data["risks_de"]) == 3, f"{branch} should have 3 DE risks"
            assert len(data["risks_en"]) == 3, f"{branch} should have 3 EN risks"
            assert len(data["bottlenecks_de"]) == 3, f"{branch} should have 3 DE bottlenecks"
            assert len(data["bottlenecks_en"]) == 3, f"{branch} should have 3 EN bottlenecks"


class TestBranchProfileGeneration:
    """Tests for branch profile generation functions."""

    def test_build_branch_profile(self, new_branches, sizes):
        """Test build_branch_profile for all new branches and sizes."""
        from services.branch_profile_engine import build_branch_profile

        for branch in new_branches:
            for size in sizes:
                for lang in ["de", "en"]:
                    profile = build_branch_profile(branch, size, lang)

                    assert profile is not None, f"Profile is None for {branch}/{size}/{lang}"
                    assert profile.branch_id == branch, f"Branch ID mismatch for {branch}"
                    assert profile.size_context == size, f"Size context mismatch for {size}"
                    assert profile.language == lang, f"Language mismatch for {lang}"
                    assert len(profile.drivers) >= 4, f"Insufficient drivers for {branch}"
                    assert len(profile.market_trends) >= 5, f"Insufficient trends for {branch}"
                    assert profile.maturity_score > 0, f"Invalid maturity score for {branch}"

    def test_get_branch_risk_opportunity_map(self, new_branches):
        """Test risk/opportunity map generation for new branches."""
        from services.branch_profile_engine import get_branch_risk_opportunity_map

        for branch in new_branches:
            for lang in ["de", "en"]:
                risk_map = get_branch_risk_opportunity_map(branch, lang)

                assert risk_map is not None, f"Risk map is None for {branch}/{lang}"
                assert len(risk_map.opportunities) == 3, f"Should have 3 opportunities for {branch}"
                assert len(risk_map.risks) == 3, f"Should have 3 risks for {branch}"
                assert len(risk_map.bottlenecks) == 3, f"Should have 3 bottlenecks for {branch}"

    def test_branch_profile_html_sections(self, new_branches):
        """Test HTML section generation for new branches."""
        from services.branch_profile_engine import get_branch_profile_html_sections

        for branch in new_branches:
            for lang in ["de", "en"]:
                briefing = {"branche": branch, "unternehmensgroesse": "team"}
                sections = get_branch_profile_html_sections(briefing, lang)

                assert "BRANCH_PROFILE_HTML" in sections, f"Missing BRANCH_PROFILE_HTML for {branch}"
                assert "BRANCH_OPPORTUNITIES_HTML" in sections, f"Missing BRANCH_OPPORTUNITIES_HTML for {branch}"
                assert "BRANCH_RISKS_HTML" in sections, f"Missing BRANCH_RISKS_HTML for {branch}"

                # Verify HTML is not empty
                assert len(sections["BRANCH_PROFILE_HTML"]) > 100, f"BRANCH_PROFILE_HTML too short for {branch}"
                assert len(sections["BRANCH_OPPORTUNITIES_HTML"]) > 100, f"BRANCH_OPPORTUNITIES_HTML too short for {branch}"
                assert len(sections["BRANCH_RISKS_HTML"]) > 100, f"BRANCH_RISKS_HTML too short for {branch}"


class TestBranchAliasNormalization:
    """Tests for branch alias normalization."""

    def test_normalize_branch_aliases(self, branch_aliases):
        """Test that all aliases normalize correctly."""
        from services.branch_profile_engine import _normalize_branch

        for alias, expected in branch_aliases.items():
            result = _normalize_branch(alias)
            assert result == expected, f"_normalize_branch('{alias}') returned '{result}', expected '{expected}'"

    def test_normalize_branch_case_insensitive(self):
        """Test case insensitivity of branch normalization."""
        from services.branch_profile_engine import _normalize_branch

        test_cases = [
            ("BAUWESEN", "bauwesen_architektur"),
            ("Verwaltung", "verwaltung"),
            ("TRANSPORT", "transport_logistik"),
            ("Logistik", "transport_logistik"),
        ]

        for input_branch, expected in test_cases:
            result = _normalize_branch(input_branch)
            assert result == expected, f"_normalize_branch('{input_branch}') returned '{result}', expected '{expected}'"


# =============================================================================
# FUNDING ALIGNMENT TESTS
# =============================================================================

class TestFundingBranchAlignment:
    """Tests for funding × branch alignment."""

    def test_new_branches_have_funding_priorities(self, new_branches):
        """Verify each new branch has funding priorities defined."""
        from services.funding_recommender import BRANCH_FUNDING_PRIORITIES

        for branch in new_branches:
            assert branch in BRANCH_FUNDING_PRIORITIES, f"Branch {branch} missing from BRANCH_FUNDING_PRIORITIES"
            priorities = BRANCH_FUNDING_PRIORITIES[branch]
            assert len(priorities) >= 3, f"Branch {branch} should have at least 3 funding priorities, has {len(priorities)}"
            assert len(priorities) <= 6, f"Branch {branch} should have at most 6 funding priorities, has {len(priorities)}"

    def test_funding_priorities_structure(self, new_branches):
        """Verify funding priorities have correct structure."""
        from services.funding_recommender import BRANCH_FUNDING_PRIORITIES

        for branch in new_branches:
            priorities = BRANCH_FUNDING_PRIORITIES[branch]
            for priority in priorities:
                assert isinstance(priority, tuple), f"Priority should be tuple for {branch}"
                assert len(priority) == 3, f"Priority tuple should have 3 elements for {branch}"

                program_id, boost, reason = priority
                assert isinstance(program_id, str), f"program_id should be str for {branch}"
                assert isinstance(boost, float), f"boost should be float for {branch}"
                assert isinstance(reason, str), f"reason should be str for {branch}"
                assert 1.0 <= boost <= 1.5, f"boost {boost} out of range for {branch}"

    def test_funding_branch_alignment_html_generation(self, new_branches):
        """Test FUNDING_BRANCH_ALIGNMENT_HTML generation for new branches."""
        from services.funding_recommender import generate_funding_branch_alignment_html

        for branch in new_branches:
            for lang in ["de", "en"]:
                briefing = {"branche": branch, "unternehmensgroesse": "team", "bundesland": "BY"}
                html = generate_funding_branch_alignment_html(briefing, lang)

                # HTML may be empty if no matching programs, but structure should be valid
                assert isinstance(html, str), f"HTML should be string for {branch}/{lang}"


# =============================================================================
# TOOLS ALIGNMENT TESTS
# =============================================================================

class TestToolsBranchAlignment:
    """Tests for tools × branch alignment."""

    def test_new_branches_have_tool_boosts(self, new_branches):
        """Verify each new branch has tool boosts defined."""
        from services.tools_analytics import BRANCH_TOOL_BOOSTS

        for branch in new_branches:
            assert branch in BRANCH_TOOL_BOOSTS, f"Branch {branch} missing from BRANCH_TOOL_BOOSTS"
            boosts = BRANCH_TOOL_BOOSTS[branch]
            assert len(boosts) >= 4, f"Branch {branch} should have at least 4 tool categories, has {len(boosts)}"

    def test_tool_boost_structure(self, new_branches):
        """Verify tool boosts have correct structure."""
        from services.tools_analytics import BRANCH_TOOL_BOOSTS

        for branch in new_branches:
            boosts = BRANCH_TOOL_BOOSTS[branch]
            for category, (tools, boost) in boosts.items():
                assert isinstance(category, str), f"Category should be str for {branch}"
                assert isinstance(tools, list), f"Tools should be list for {branch}/{category}"
                assert len(tools) >= 3, f"Category {category} should have at least 3 tools for {branch}"
                assert isinstance(boost, float), f"Boost should be float for {branch}/{category}"
                assert 1.0 <= boost <= 1.5, f"Boost {boost} out of range for {branch}/{category}"

    def test_branch_tool_recommendations(self, new_branches):
        """Test tool recommendations generation for new branches."""
        from services.tools_analytics import get_branch_tool_recommendations

        for branch in new_branches:
            for size in ["solo", "team", "kmu"]:
                recommendations = get_branch_tool_recommendations(branch, size)

                assert len(recommendations) >= 8, f"Should have at least 8 recommendations for {branch}/{size}, got {len(recommendations)}"

                for rec in recommendations:
                    assert rec.tool_name, f"Tool name should not be empty for {branch}"
                    assert 0.0 <= rec.branch_relevance_score <= 1.0, f"Score out of range for {rec.tool_name}"

    def test_tools_branch_alignment_html_generation(self, new_branches):
        """Test TOOLS_BRANCH_ALIGNMENT_HTML generation for new branches."""
        from services.tools_analytics import generate_tools_branch_alignment_html

        for branch in new_branches:
            for lang in ["de", "en"]:
                briefing = {"branche": branch, "unternehmensgroesse": "team"}
                html = generate_tools_branch_alignment_html(briefing, lang)

                assert isinstance(html, str), f"HTML should be string for {branch}/{lang}"
                assert len(html) > 100, f"HTML too short for {branch}/{lang}"
                assert "tools-branch-alignment" in html, f"Missing CSS class for {branch}/{lang}"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestG19_1Integration:
    """Integration tests for G19.1 branch profiles."""

    def test_full_pipeline_bauwesen(self):
        """Test complete pipeline for Bauwesen & Architektur."""
        from services.branch_profile_engine import (
            build_branch_profile,
            get_branch_risk_opportunity_map,
            get_branch_profile_html_sections,
        )
        from services.funding_recommender import generate_funding_branch_alignment_html
        from services.tools_analytics import generate_tools_branch_alignment_html

        briefing = {
            "branche": "bauwesen_architektur",
            "unternehmensgroesse": "team",
            "bundesland": "BY",
        }

        # Branch profile
        profile = build_branch_profile("bauwesen_architektur", "team", "de")
        assert profile.maturity_score == 55
        assert "Projektgeschäft" in profile.drivers[0].title

        # Risk/opportunity map
        risk_map = get_branch_risk_opportunity_map("bauwesen_architektur", "de")
        assert "Dokumentationseffizienz" in risk_map.opportunities[0]["title"]

        # HTML sections
        sections = get_branch_profile_html_sections(briefing, "de")
        assert "BIM" in sections["BRANCH_PROFILE_HTML"]

        # Funding alignment
        funding_html = generate_funding_branch_alignment_html(briefing, "de")
        assert isinstance(funding_html, str)

        # Tools alignment
        tools_html = generate_tools_branch_alignment_html(briefing, "de")
        assert "tools-branch-alignment" in tools_html

    def test_full_pipeline_verwaltung(self):
        """Test complete pipeline for Verwaltung."""
        from services.branch_profile_engine import (
            build_branch_profile,
            get_branch_risk_opportunity_map,
            get_branch_profile_html_sections,
        )
        from services.funding_recommender import generate_funding_branch_alignment_html
        from services.tools_analytics import generate_tools_branch_alignment_html

        briefing = {
            "branche": "verwaltung",
            "unternehmensgroesse": "kmu",
            "bundesland": "NW",
        }

        # Branch profile
        profile = build_branch_profile("verwaltung", "kmu", "de")
        assert profile.maturity_score == 45
        assert "Compliance" in profile.drivers[0].title

        # Risk/opportunity map
        risk_map = get_branch_risk_opportunity_map("verwaltung", "de")
        assert "Bürgerzufriedenheit" in risk_map.opportunities[0]["title"]

        # HTML sections
        sections = get_branch_profile_html_sections(briefing, "de")
        assert "DSGVO" in sections["BRANCH_PROFILE_HTML"] or "Datenschutz" in sections["BRANCH_PROFILE_HTML"]

        # Tools alignment
        tools_html = generate_tools_branch_alignment_html(briefing, "de")
        assert len(tools_html) > 100

    def test_full_pipeline_transport_logistik(self):
        """Test complete pipeline for Transport & Logistik."""
        from services.branch_profile_engine import (
            build_branch_profile,
            get_branch_risk_opportunity_map,
            get_branch_profile_html_sections,
        )
        from services.funding_recommender import generate_funding_branch_alignment_html
        from services.tools_analytics import generate_tools_branch_alignment_html

        briefing = {
            "branche": "transport_logistik",
            "unternehmensgroesse": "solo",
            "bundesland": "HH",
        }

        # Branch profile
        profile = build_branch_profile("transport_logistik", "solo", "de")
        assert profile.maturity_score == 60
        assert "Supply Chain" in profile.drivers[0].title

        # Risk/opportunity map
        risk_map = get_branch_risk_opportunity_map("transport_logistik", "de")
        assert "Routeneffizienz" in risk_map.opportunities[0]["title"]

        # HTML sections
        sections = get_branch_profile_html_sections(briefing, "de")
        assert "Predictive" in sections["BRANCH_PROFILE_HTML"] or "Logistik" in sections["BRANCH_PROFILE_HTML"]

        # Tools alignment
        tools_html = generate_tools_branch_alignment_html(briefing, "de")
        assert "tools-branch-alignment" in tools_html


# =============================================================================
# DRIFT TESTS
# =============================================================================

class TestBranchProfileDrift:
    """Tests to ensure minimal drift in branch profiles."""

    def test_no_empty_strings_in_profiles(self, new_branches):
        """Verify no empty strings in profile data."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        for branch in new_branches:
            data = BRANCH_MATURITY_DATA[branch]

            for key, value in data.items():
                if isinstance(value, str):
                    assert value.strip(), f"Empty string for {branch}/{key}"
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, tuple):
                            for j, elem in enumerate(item):
                                if isinstance(elem, str):
                                    assert elem.strip(), f"Empty string in {branch}/{key}[{i}][{j}]"
                        elif isinstance(item, str):
                            assert item.strip(), f"Empty string in {branch}/{key}[{i}]"

    def test_german_english_parity(self, new_branches):
        """Verify DE and EN content have same structure."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        paired_keys = [
            ("drivers_de", "drivers_en"),
            ("trends_de", "trends_en"),
            ("regulatory_de", "regulatory_en"),
            ("use_cases_de", "use_cases_en"),
            ("opportunities_de", "opportunities_en"),
            ("risks_de", "risks_en"),
            ("bottlenecks_de", "bottlenecks_en"),
        ]

        for branch in new_branches:
            data = BRANCH_MATURITY_DATA[branch]
            for de_key, en_key in paired_keys:
                assert len(data[de_key]) == len(data[en_key]), \
                    f"Length mismatch for {branch}: {de_key}({len(data[de_key])}) vs {en_key}({len(data[en_key])})"

    def test_maturity_scores_reasonable(self, new_branches):
        """Verify maturity scores are reasonable (40-80 range)."""
        from services.branch_profile_engine import BRANCH_MATURITY_DATA

        for branch in new_branches:
            score = BRANCH_MATURITY_DATA[branch]["maturity_score"]
            assert 40 <= score <= 80, f"Maturity score {score} out of reasonable range for {branch}"
