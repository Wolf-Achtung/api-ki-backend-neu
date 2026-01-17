# -*- coding: utf-8 -*-
"""
Tests for P0.10 - Branch Context Card Type Mapping

Tests:
- Branch context cards have correct type labels (not all "Risiko")
- Opportunities labeled as "Chance" not "Risiko"
- Resources field doesn't show "0" when empty
"""

import os
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestBranchContextCardTypeMapping:
    """Test that branch context cards have correct type labels."""

    def test_opportunities_have_distinct_styling(self):
        """Test that opportunities are styled differently from risks."""
        from services.branch_profile_engine import (
            generate_branch_opportunities_html,
            generate_branch_risks_html,
            get_branch_risk_opportunity_map,
        )

        # Get risk/opportunity map for a sample branch
        risk_map = get_branch_risk_opportunity_map("beratung", "de")

        opp_html = generate_branch_opportunities_html(risk_map, "de")
        risk_html = generate_branch_risks_html(risk_map, "de")

        # Opportunities should have green styling (#22c55e)
        if opp_html:
            assert "#22c55e" in opp_html, "Opportunities should have green accent color"
            assert "Branchenchancen" in opp_html, "Should have opportunity title"

        # Risks should have amber/orange styling (#f59e0b)
        if risk_html and risk_map.risks:
            assert "#f59e0b" in risk_html, "Risks should have amber accent color"
            assert "Branchenrisiken" in risk_html, "Should have risk title"

    def test_opportunity_cards_not_labeled_risiko(self):
        """Test that opportunity cards are not mislabeled as 'Risiko'."""
        from services.branch_profile_engine import (
            generate_branch_opportunities_html,
            get_branch_risk_opportunity_map,
        )

        risk_map = get_branch_risk_opportunity_map("it", "de")
        opp_html = generate_branch_opportunities_html(risk_map, "de")

        if opp_html:
            # The word "Risiko" should NOT appear in opportunity section
            # Allow for compound words like "Branchenrisiken" if they're in different sections
            assert opp_html.count("Risiko") == 0, \
                "Opportunity section should not contain 'Risiko' label"

    def test_card_types_are_differentiated(self):
        """Test that different card types have different visual styling."""
        from services.executive_layout_engine import CardType, CARD_STYLES

        # Each card type should have unique accent color
        accent_colors = set()
        for card_type in CardType:
            style = CARD_STYLES.get(card_type)
            if style:
                accent_colors.add(style.get("accent_color"))

        # At least 3 distinct colors should exist
        assert len(accent_colors) >= 3, \
            f"Should have at least 3 distinct card type colors, got {len(accent_colors)}"


class TestResourcesDisplayNotZero:
    """Test that Resources field doesn't show '0' when empty."""

    def test_risk_map_has_data_or_is_empty(self):
        """Test that risk map either has data or is properly empty."""
        from services.branch_profile_engine import get_branch_risk_opportunity_map

        # Test various branches
        for branch in ["beratung", "it", "handel", "produktion"]:
            risk_map = get_branch_risk_opportunity_map(branch, "de")

            # Either has opportunities or is empty list (not 0)
            assert risk_map.opportunities is not None
            assert isinstance(risk_map.opportunities, list)

            # Either has risks or is empty list (not 0)
            assert risk_map.risks is not None
            assert isinstance(risk_map.risks, list)

    def test_html_output_hides_empty_sections(self):
        """Test that HTML output hides sections when empty."""
        from services.branch_profile_engine import (
            generate_branch_opportunities_html,
            RiskOpportunityMap,
        )

        # Create empty risk map
        empty_map = RiskOpportunityMap(
            branch_id="test",
            opportunities=[],
            risks=[],
            bottlenecks=[],
        )

        opp_html = generate_branch_opportunities_html(empty_map, "de")

        # Empty sections should return empty string, not "0" or placeholder
        assert "0" not in opp_html, "Should not display '0' for empty data"
        assert opp_html == "", "Empty opportunities should return empty string"


class TestBranchProfileRenderingConsistency:
    """Test that branch profile rendering is consistent."""

    def test_branch_profile_sections_exist(self):
        """Test that branch profile generates all required sections."""
        from services.branch_profile_engine import get_branch_profile_html_sections

        briefing = {"branche": "beratung", "unternehmensgroesse": "team"}
        sections = get_branch_profile_html_sections(briefing, "de")

        # Should have profile HTML
        assert "BRANCH_PROFILE_HTML" in sections
        assert sections["BRANCH_PROFILE_HTML"]

        # Should have opportunities HTML
        assert "BRANCH_OPPORTUNITIES_HTML" in sections

        # Should have risks HTML
        assert "BRANCH_RISKS_HTML" in sections

    def test_branch_profile_has_correct_labels(self):
        """Test that branch profile HTML has correct German labels."""
        from services.branch_profile_engine import generate_branch_profile_html, build_branch_profile

        profile = build_branch_profile("beratung", "team", "de")
        html = generate_branch_profile_html(profile, "de")

        # Should have German labels
        assert "Branchenkontext" in html or "Profil" in html or "beratung" in html.lower(), \
            "Should have German profile header or branch name"


class TestP10Integration:
    """Integration tests for P0.10."""

    def test_full_branch_context_generation(self):
        """Test complete branch context generation."""
        from services.branch_profile_engine import get_branch_profile_html_sections

        test_cases = [
            {"branche": "beratung", "unternehmensgroesse": "solo"},
            {"branche": "it", "unternehmensgroesse": "team"},
            {"branche": "handel", "unternehmensgroesse": "kmu"},
        ]

        for briefing in test_cases:
            sections = get_branch_profile_html_sections(briefing, "de")

            # All sections should be strings (not None or 0)
            for key in ["BRANCH_PROFILE_HTML", "BRANCH_OPPORTUNITIES_HTML", "BRANCH_RISKS_HTML"]:
                assert key in sections
                assert isinstance(sections[key], str), f"{key} should be string"

    def test_english_branch_context(self):
        """Test branch context in English."""
        from services.branch_profile_engine import (
            generate_branch_opportunities_html,
            get_branch_risk_opportunity_map,
        )

        risk_map = get_branch_risk_opportunity_map("consulting", "en")
        opp_html = generate_branch_opportunities_html(risk_map, "en")

        if opp_html:
            assert "Industry Opportunities" in opp_html, \
                "Should have English title for opportunities"
