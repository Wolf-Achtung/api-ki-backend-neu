# -*- coding: utf-8 -*-
"""
Sprint G19: Branch Intelligence & Market Logic 2.0 Test Suite
==============================================================

Comprehensive tests for:
- Branch Profile Generator
- Branch Drivers presence
- Risk/Opportunity mapping
- Funding × Branch Alignment
- Tools × Branch Boost
- Section injection correctness
- HTML output validation

Version: 1.0.0 (Sprint G19)
"""
from __future__ import annotations

import os
import sys
import pytest
from typing import Any, Dict, List

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_briefing_beratung() -> Dict[str, Any]:
    """Sample briefing for Beratung (Consulting) branch."""
    return {
        "unternehmensgroesse": "Solo-Selbststaendige/r (1)",
        "branche": "Beratung & Dienstleistungen",
        "BRANCH_LABEL": "beratung",
        "ai_act_risk_level": "minimal",
        "hauptleistung": "Unternehmensberatung"
    }


@pytest.fixture
def sample_briefing_it() -> Dict[str, Any]:
    """Sample briefing for IT/Software branch."""
    return {
        "unternehmensgroesse": "Kleines Team (2-10)",
        "branche": "IT & Softwareentwicklung",
        "BRANCH_LABEL": "it",
        "ai_act_risk_level": "limited",
        "hauptleistung": "Software Development"
    }


@pytest.fixture
def sample_briefing_handel() -> Dict[str, Any]:
    """Sample briefing for Handel (Retail) branch."""
    return {
        "unternehmensgroesse": "KMU (11-250)",
        "branche": "Handel & E-Commerce",
        "BRANCH_LABEL": "handel",
        "ai_act_risk_level": "minimal",
        "hauptleistung": "Online Shop"
    }


@pytest.fixture
def sample_briefing_finanzen() -> Dict[str, Any]:
    """Sample briefing for Finanzen (Finance) branch."""
    return {
        "unternehmensgroesse": "KMU (11-250)",
        "branche": "Finanzdienstleistungen",
        "BRANCH_LABEL": "finanzen",
        "ai_act_risk_level": "high-risk",
        "bundesland": "BY",
        "hauptleistung": "Vermögensverwaltung"
    }


@pytest.fixture
def sample_briefing_gesundheit() -> Dict[str, Any]:
    """Sample briefing for Gesundheit (Health) branch."""
    return {
        "unternehmensgroesse": "Kleines Team (2-10)",
        "branche": "Gesundheitswesen",
        "BRANCH_LABEL": "gesundheit",
        "ai_act_risk_level": "high-risk",
        "hauptleistung": "Arztpraxis"
    }


# =============================================================================
# BRANCH PROFILE ENGINE TESTS
# =============================================================================

class TestBranchProfileEngine:
    """Tests for services/branch_profile_engine.py"""

    def test_build_branch_profile_beratung(self, sample_briefing_beratung: Dict[str, Any]):
        """Test profile generation for Beratung (consulting)."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="beratung",
            size="solo",
            language="de"
        )

        assert profile is not None
        assert profile.branch_id == "beratung"
        assert profile.size_context == "solo"
        assert profile.language == "de"
        assert profile.maturity_score > 0
        assert profile.maturity_score <= 100

    def test_build_branch_profile_it(self, sample_briefing_it: Dict[str, Any]):
        """Test profile generation for IT/Software."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="it",
            size="team",
            language="de"
        )

        assert profile is not None
        assert profile.branch_id == "it"
        assert profile.maturity_score >= 70  # IT should be high maturity
        assert profile.ai_adoption_rate == "mainstream"

    def test_branch_drivers_present(self):
        """Test that branch drivers are present in profile."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="beratung",
            size="team",
            language="de"
        )

        assert len(profile.drivers) >= 4
        assert all(d.title for d in profile.drivers)
        assert all(d.description for d in profile.drivers)

    def test_market_trends_present(self):
        """Test that market trends are present in profile."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="marketing",
            size="team",
            language="de"
        )

        assert len(profile.market_trends) >= 4
        for trend in profile.market_trends:
            assert trend.title
            assert trend.relevance_score >= 0.0
            assert trend.relevance_score <= 1.0

    def test_regulatory_factors_for_high_risk_branch(self):
        """Test regulatory factors for high-risk branches like finance/health."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="finanzen",
            size="kmu",
            language="de"
        )

        assert len(profile.regulatory_factors) >= 2
        # Finance should have high urgency regulatory factors
        high_urgency = [r for r in profile.regulatory_factors if r.urgency == "high"]
        assert len(high_urgency) >= 1

    def test_use_cases_present(self):
        """Test that use cases are present in profile."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="handel",
            size="kmu",
            language="de"
        )

        assert len(profile.use_cases) >= 3
        for uc in profile.use_cases:
            assert uc.title
            assert uc.complexity in ("low", "medium", "high")
            assert uc.roi_potential in ("low", "medium", "high")
            assert uc.implementation_months > 0

    def test_english_language_support(self):
        """Test English language profile generation."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="it",
            size="team",
            language="en"
        )

        assert profile.language == "en"
        # Check that drivers are in English
        if profile.drivers:
            # English drivers should not contain typical German words
            assert not any("und" in d.description.lower()[:20] for d in profile.drivers)

    def test_branch_normalization(self):
        """Test that branch names are normalized correctly."""
        from services.branch_profile_engine import build_branch_profile

        # Test various aliases
        aliases = [
            ("consulting", "beratung"),
            ("software", "it"),
            ("ecommerce", "handel"),
            ("finance", "finanzen"),
            ("healthcare", "gesundheit"),
        ]

        for alias, expected in aliases:
            profile = build_branch_profile(branch=alias, size="team", language="de")
            assert profile.branch_id == expected, f"Expected {expected} for {alias}"


# =============================================================================
# RISK/OPPORTUNITY MAPPING TESTS
# =============================================================================

class TestRiskOpportunityMapping:
    """Tests for risk and opportunity mapping."""

    def test_get_risk_opportunity_map(self):
        """Test risk/opportunity map generation."""
        from services.branch_profile_engine import get_branch_risk_opportunity_map

        risk_map = get_branch_risk_opportunity_map(
            branch="beratung",
            language="de"
        )

        assert risk_map is not None
        assert risk_map.branch_id == "beratung"
        assert len(risk_map.opportunities) == 3
        assert len(risk_map.risks) == 3
        assert len(risk_map.bottlenecks) == 3

    def test_opportunities_structure(self):
        """Test opportunity structure."""
        from services.branch_profile_engine import get_branch_risk_opportunity_map

        risk_map = get_branch_risk_opportunity_map(
            branch="it",
            language="de"
        )

        for opp in risk_map.opportunities:
            assert "title" in opp
            assert "description" in opp
            assert opp["title"]
            assert opp["description"]

    def test_risks_structure(self):
        """Test risk structure."""
        from services.branch_profile_engine import get_branch_risk_opportunity_map

        risk_map = get_branch_risk_opportunity_map(
            branch="finanzen",
            language="de"
        )

        for risk in risk_map.risks:
            assert "title" in risk
            assert "description" in risk

    def test_bottlenecks_structure(self):
        """Test bottleneck structure."""
        from services.branch_profile_engine import get_branch_risk_opportunity_map

        risk_map = get_branch_risk_opportunity_map(
            branch="gesundheit",
            language="en"
        )

        assert len(risk_map.bottlenecks) == 3
        for bn in risk_map.bottlenecks:
            assert "title" in bn


# =============================================================================
# FUNDING × BRANCH ALIGNMENT TESTS
# =============================================================================

class TestFundingBranchAlignment:
    """Tests for funding × branch alignment."""

    def test_get_branch_funding_priorities(self):
        """Test branch funding priorities retrieval."""
        from services.funding_recommender import get_branch_funding_priorities

        priorities = get_branch_funding_priorities("beratung")

        assert len(priorities) >= 2
        for p in priorities:
            assert len(p) == 3  # (program_id, boost, reason)
            assert p[1] > 1.0  # Boost should be > 1.0

    def test_get_branch_funding_hits(self):
        """Test branch funding hits generation."""
        from services.funding_recommender import get_branch_funding_hits

        hits = get_branch_funding_hits(
            branch="it",
            size="team",
            region="DE",
            lang="de"
        )

        assert len(hits) >= 1
        for hit in hits:
            assert hit.program_name
            assert hit.relevance_score >= 0.0
            assert hit.relevance_score <= 1.0
            assert hit.branch_boost >= 1.0

    def test_funding_branch_alignment_html_generation(self, sample_briefing_finanzen: Dict[str, Any]):
        """Test HTML generation for funding branch alignment."""
        from services.funding_recommender import generate_funding_branch_alignment_html

        html = generate_funding_branch_alignment_html(
            briefing=sample_briefing_finanzen,
            lang="de"
        )

        assert html
        assert "funding-branch-alignment" in html
        assert "Branchenspezifische" in html or "Branchen" in html

    def test_funding_branch_alignment_injection(self, sample_briefing_beratung: Dict[str, Any]):
        """Test section injection for funding branch alignment."""
        from services.funding_recommender import inject_funding_branch_alignment_into_sections

        sections: Dict[str, Any] = {}
        result = inject_funding_branch_alignment_into_sections(
            sections=sections,
            briefing=sample_briefing_beratung,
            lang="de"
        )

        assert "FUNDING_BRANCH_ALIGNMENT_HTML" in result


# =============================================================================
# TOOLS × BRANCH BOOST TESTS
# =============================================================================

class TestToolsBranchBoost:
    """Tests for tools × branch boost functionality."""

    def test_calculate_branch_relevance_score(self):
        """Test branch relevance score calculation."""
        from services.tools_analytics import calculate_branch_relevance_score

        # Test high-relevance tool for branch
        score, category, boost = calculate_branch_relevance_score(
            tool_name="ChatGPT",
            branch="beratung"
        )

        assert score > 0.5
        assert category in ["text_automation", "content", "general"]
        assert boost >= 1.0

    def test_get_branch_tool_recommendations(self):
        """Test branch tool recommendations."""
        from services.tools_analytics import get_branch_tool_recommendations

        recommendations = get_branch_tool_recommendations(
            branch="marketing",
            size="team",
            limit=10
        )

        assert len(recommendations) > 0
        for rec in recommendations:
            assert rec.tool_name
            assert rec.branch_relevance_score >= 0.0
            assert rec.branch_relevance_score <= 1.0
            assert rec.category

    def test_tools_branch_alignment_html_generation(self, sample_briefing_handel: Dict[str, Any]):
        """Test HTML generation for tools branch alignment."""
        from services.tools_analytics import generate_tools_branch_alignment_html

        html = generate_tools_branch_alignment_html(
            briefing=sample_briefing_handel,
            lang="de"
        )

        assert html
        assert "tools-branch-alignment" in html
        assert "Branchenoptimiert" in html or "Branchen" in html

    def test_tools_branch_alignment_injection(self, sample_briefing_it: Dict[str, Any]):
        """Test section injection for tools branch alignment."""
        from services.tools_analytics import inject_tools_branch_alignment_into_sections

        sections: Dict[str, Any] = {}
        result = inject_tools_branch_alignment_into_sections(
            sections=sections,
            briefing=sample_briefing_it,
            lang="de"
        )

        assert "TOOLS_BRANCH_ALIGNMENT_HTML" in result


# =============================================================================
# HTML SECTION TESTS
# =============================================================================

class TestHTMLSectionGeneration:
    """Tests for HTML section generation."""

    def test_branch_profile_html_generation(self):
        """Test BRANCH_PROFILE_HTML generation."""
        from services.branch_profile_engine import (
            build_branch_profile,
            generate_branch_profile_html
        )

        profile = build_branch_profile("beratung", "solo", "de")
        html = generate_branch_profile_html(profile, "de")

        assert html
        assert "branch-profile" in html
        assert "Branchenprofil" in html or "Industry" in html
        assert str(profile.maturity_score) in html

    def test_branch_opportunities_html_generation(self):
        """Test BRANCH_OPPORTUNITIES_HTML generation."""
        from services.branch_profile_engine import (
            get_branch_risk_opportunity_map,
            generate_branch_opportunities_html
        )

        risk_map = get_branch_risk_opportunity_map("it", "de")
        html = generate_branch_opportunities_html(risk_map, "de")

        assert html
        assert "branch-opportunities" in html

    def test_branch_risks_html_generation(self):
        """Test BRANCH_RISKS_HTML generation."""
        from services.branch_profile_engine import (
            get_branch_risk_opportunity_map,
            generate_branch_risks_html
        )

        risk_map = get_branch_risk_opportunity_map("finanzen", "de")
        html = generate_branch_risks_html(risk_map, "de")

        assert html
        assert "branch-risks" in html

    def test_get_branch_profile_html_sections(self, sample_briefing_beratung: Dict[str, Any]):
        """Test combined HTML sections retrieval."""
        from services.branch_profile_engine import get_branch_profile_html_sections

        sections = get_branch_profile_html_sections(sample_briefing_beratung, "de")

        assert "BRANCH_PROFILE_HTML" in sections
        assert "BRANCH_OPPORTUNITIES_HTML" in sections
        assert "BRANCH_RISKS_HTML" in sections
        assert "branch_profile" in sections
        assert "branch_risk_map" in sections

    def test_html_sections_have_proper_css_classes(self, sample_briefing_handel: Dict[str, Any]):
        """Test that HTML sections have proper CSS classes."""
        from services.branch_profile_engine import get_branch_profile_html_sections

        sections = get_branch_profile_html_sections(sample_briefing_handel, "de")

        profile_html = sections.get("BRANCH_PROFILE_HTML", "")
        if profile_html:
            assert "style=" in profile_html
            assert "border-radius" in profile_html


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestG19Integration:
    """Integration tests for G19 components working together."""

    def test_full_branch_intelligence_flow(self, sample_briefing_finanzen: Dict[str, Any]):
        """Test the complete branch intelligence flow."""
        from services.branch_profile_engine import get_branch_profile_html_sections
        from services.funding_recommender import inject_funding_branch_alignment_into_sections
        from services.tools_analytics import inject_tools_branch_alignment_into_sections

        # Start with empty sections
        sections: Dict[str, Any] = {}

        # Add branch profile sections
        branch_sections = get_branch_profile_html_sections(sample_briefing_finanzen, "de")
        sections.update(branch_sections)

        # Add funding branch alignment
        sections = inject_funding_branch_alignment_into_sections(
            sections, sample_briefing_finanzen, "de"
        )

        # Add tools branch alignment
        sections = inject_tools_branch_alignment_into_sections(
            sections, sample_briefing_finanzen, "de"
        )

        # Verify all G19 sections are present
        g19_sections = [
            "BRANCH_PROFILE_HTML",
            "BRANCH_OPPORTUNITIES_HTML",
            "BRANCH_RISKS_HTML",
            "FUNDING_BRANCH_ALIGNMENT_HTML",
            "TOOLS_BRANCH_ALIGNMENT_HTML",
        ]

        for section in g19_sections:
            assert section in sections, f"Missing section: {section}"

    def test_branch_specific_content_varies(self):
        """Test that different branches produce different content."""
        from services.branch_profile_engine import build_branch_profile

        profile_beratung = build_branch_profile("beratung", "team", "de")
        profile_it = build_branch_profile("it", "team", "de")
        profile_handel = build_branch_profile("handel", "team", "de")

        # Maturity scores should differ
        scores = [
            profile_beratung.maturity_score,
            profile_it.maturity_score,
            profile_handel.maturity_score
        ]
        assert len(set(scores)) > 1, "Maturity scores should vary by branch"

        # Drivers should differ
        beratung_drivers = {d.title for d in profile_beratung.drivers}
        it_drivers = {d.title for d in profile_it.drivers}
        assert beratung_drivers != it_drivers, "Drivers should differ by branch"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Edge case tests for G19 components."""

    def test_unknown_branch_falls_back_gracefully(self):
        """Test that unknown branches get default data."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="unbekannte_branche_xyz",
            size="team",
            language="de"
        )

        assert profile is not None
        assert profile.maturity_score > 0
        assert len(profile.drivers) >= 2

    def test_empty_branch_handled(self):
        """Test that empty branch is handled."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile(
            branch="",
            size="team",
            language="de"
        )

        assert profile is not None
        assert profile.branch_id == "beratung"  # Default

    def test_empty_briefing_handled(self):
        """Test that empty briefing is handled."""
        from services.branch_profile_engine import get_branch_profile_html_sections

        sections = get_branch_profile_html_sections({}, "de")

        assert "BRANCH_PROFILE_HTML" in sections

    def test_size_normalization(self):
        """Test company size normalization."""
        from services.branch_profile_engine import build_branch_profile

        sizes = [
            ("Solo-Selbststaendige/r (1)", "solo"),
            ("Kleines Team (2-10)", "team"),
            ("KMU (11-250)", "kmu"),
            ("solo", "solo"),
            ("", "team"),  # Default
        ]

        for input_size, expected in sizes:
            profile = build_branch_profile("beratung", input_size, "de")
            assert profile.size_context == expected, f"Expected {expected} for {input_size}"


# =============================================================================
# GOLD PROFILE TESTS
# =============================================================================

class TestGoldProfiles:
    """Tests using gold standard profiles."""

    def test_beratung_solo_gold_profile(self):
        """Test Beratung Solo gold profile generation."""
        from services.branch_profile_engine import build_branch_profile, get_branch_risk_opportunity_map

        profile = build_branch_profile("beratung", "solo", "de")
        risk_map = get_branch_risk_opportunity_map("beratung", "de")

        # Beratung should have specific characteristics
        assert profile.maturity_score >= 60
        assert profile.maturity_score <= 75
        assert profile.competitive_density == "high"
        assert len(profile.drivers) >= 4
        assert len(risk_map.opportunities) == 3
        assert len(risk_map.risks) == 3

    def test_it_team_gold_profile(self):
        """Test IT Team gold profile generation."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile("it", "team", "de")

        # IT should be high maturity
        assert profile.maturity_score >= 75
        assert profile.ai_adoption_rate == "mainstream"
        assert profile.digitalization_level == "high"

    def test_handel_kmu_gold_profile(self):
        """Test Handel KMU gold profile generation."""
        from services.branch_profile_engine import build_branch_profile

        profile = build_branch_profile("handel", "kmu", "de")

        # Handel should have medium maturity
        assert profile.maturity_score >= 50
        assert profile.maturity_score <= 65
        assert profile.ai_adoption_rate == "growing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
