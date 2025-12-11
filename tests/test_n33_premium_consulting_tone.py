# -*- coding: utf-8 -*-
"""
SPRINT N3.3: Tests for Premium Consulting Tone Fallbacks.

Tests that KI-Stack and Branch Deep Dive fallbacks follow McKinsey/BCG templates.
"""
import pytest


class TestKiStackMcKinseyStyle:
    """Test KI-Stack fallback uses McKinsey-style structure."""

    def test_ki_stack_has_strengths_section(self):
        """KI-Stack should have Strengths section (McKinsey point 1)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="team"
        )

        assert "Stärken" in fallback or "Strengths" in fallback

    def test_ki_stack_has_gaps_section(self):
        """KI-Stack should have Gaps section (McKinsey point 2)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="team"
        )

        assert "Lücken" in fallback or "Gaps" in fallback

    def test_ki_stack_has_90_day_priorities(self):
        """KI-Stack should have 90-day priorities (McKinsey point 3)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="team"
        )

        assert "90 Tage" in fallback or "90-Day" in fallback or "Prioritäten" in fallback

    def test_ki_stack_has_strategic_leverage(self):
        """KI-Stack should have Strategic Leverage section (McKinsey point 4)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="team"
        )

        assert "Strategische Hebel" in fallback or "Strategic" in fallback

    def test_ki_stack_numbered_sections(self):
        """KI-Stack should use numbered structure."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="team"
        )

        # Should have numbered sections (1., 2., 3., 4.)
        assert "1." in fallback
        assert "2." in fallback
        assert "3." in fallback
        assert "4." in fallback

    def test_ki_stack_has_bullet_points(self):
        """KI-Stack sections should have bullet points."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="team"
        )

        # Should have multiple li elements
        assert fallback.count("<li>") >= 8  # At least 3+3+3+2 bullets


class TestBranchDeepDiveBCGStyle:
    """Test Branch Deep Dive fallback uses BCG-style structure."""

    def test_branch_has_market_dynamics(self):
        """Branch Deep Dive should have Market Dynamics (BCG point 1)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="team"
        )

        assert "Markt" in fallback and "Trend" in fallback

    def test_branch_has_competition(self):
        """Branch Deep Dive should have Competition section (BCG point 2)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="team"
        )

        assert "Wettbewerb" in fallback or "Differenzierung" in fallback

    def test_branch_has_risks(self):
        """Branch Deep Dive should have Risks section (BCG point 3)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="team"
        )

        # "Kernrisiken" contains "risiken" (plural) - case-insensitive check
        assert "risiko" in fallback.lower() or "risiken" in fallback.lower() or "Risk" in fallback

    def test_branch_has_opportunities(self):
        """Branch Deep Dive should have Opportunities section (BCG point 4)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="team"
        )

        assert "Chancen" in fallback or "Wertschöpfung" in fallback

    def test_branch_has_recommendations(self):
        """Branch Deep Dive should have Recommendations (BCG point 5)."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="team"
        )

        assert "Handlungsempfehlungen" in fallback or "Empfehlungen" in fallback

    def test_branch_numbered_sections(self):
        """Branch Deep Dive should use numbered structure."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="team"
        )

        # Should have numbered sections (1., 2., 3., 4., 5.)
        assert "1." in fallback
        assert "2." in fallback
        assert "3." in fallback
        assert "4." in fallback
        assert "5." in fallback


class TestPremiumToneQuality:
    """Test overall premium tone quality."""

    def test_no_generic_sentences(self):
        """Fallbacks should not contain generic filler sentences."""
        from services.report_validator import _build_generic_leak_fallback

        for section in ["ki_stack_summary", "branch_deep_dive"]:
            fallback = _build_generic_leak_fallback(section, "team")

            # Should NOT contain generic phrases
            assert "dieser abschnitt fasst" not in fallback.lower()
            assert "in diesem kapitel" not in fallback.lower()
            assert "im folgenden" not in fallback.lower()

    def test_professional_terminology(self):
        """Fallbacks should use professional consulting terminology."""
        from services.report_validator import _build_generic_leak_fallback

        ki_stack = _build_generic_leak_fallback("ki_stack_summary", "team")
        branch = _build_generic_leak_fallback("branch_deep_dive", "team")

        # KI-Stack should have McKinsey-style terms
        assert "ROI" in ki_stack or "Potenzial" in ki_stack

        # Branch should have BCG-style terms
        assert "Marktrelevanz" in branch or "First-Mover" in branch

    def test_substantive_content_length(self):
        """Premium fallbacks should have substantive content."""
        from services.report_validator import _build_generic_leak_fallback

        for section in ["ki_stack_summary", "branch_deep_dive"]:
            fallback = _build_generic_leak_fallback(section, "team")

            # Should have substantial content (at least 1000 chars)
            assert len(fallback) > 1000, f"{section} content too short"

    def test_no_support_mentions(self):
        """Premium fallbacks should not mention support."""
        from services.report_validator import _build_generic_leak_fallback

        for section in ["ki_stack_summary", "branch_deep_dive"]:
            fallback = _build_generic_leak_fallback(section, "team")

            assert "support" not in fallback.lower()
            assert "kontaktieren" not in fallback.lower()

    def test_no_apologetic_tone(self):
        """Premium fallbacks should not be apologetic."""
        from services.report_validator import _build_generic_leak_fallback

        for section in ["ki_stack_summary", "branch_deep_dive"]:
            fallback = _build_generic_leak_fallback(section, "team")

            assert "leider" not in fallback.lower()
            assert "entschuldigung" not in fallback.lower()
            assert "sorry" not in fallback.lower()


class TestSizeAwareness:
    """Test size-aware personalization in premium templates."""

    def test_solo_context(self):
        """Solo context should use appropriate terminology."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback("ki_stack_summary", "solo")

        # Should reference solo-appropriate context
        assert "Tätigkeit" in fallback or "Arbeitsprozessen" in fallback

    def test_team_context(self):
        """Team context should use team terminology."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback("ki_stack_summary", "team")

        # Should reference team-appropriate context
        assert "Team" in fallback or "Organisation" in fallback

    def test_kmu_context(self):
        """KMU context should use enterprise terminology."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback("ki_stack_summary", "kmu")

        # Should use enterprise context
        assert "Unternehmen" in fallback or "Organisation" in fallback
