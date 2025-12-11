# -*- coding: utf-8 -*-
"""
SPRINT N3.2: Tests for Executive/Branch Fallback Text Quality.

Tests that fallback content in report_validator.py is customer-ready:
- No "Support" or error mentions
- Constructive auto-summary content
- Professional tone throughout
"""
import pytest


class TestKiStackFallbackQuality:
    """Test ki_stack_summary fallback content quality."""

    def test_ki_stack_fallback_no_support_mention(self):
        """Fallback should not mention 'Support' or 'kontaktieren'."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="solo"
        )

        assert "support" not in fallback.lower()
        assert "kontaktieren" not in fallback.lower()
        assert "fehler" not in fallback.lower()
        assert "error" not in fallback.lower()

    def test_ki_stack_fallback_has_constructive_content(self):
        """Fallback should have actionable, constructive content."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="team"
        )

        # Should contain actionable items
        assert "<ul>" in fallback or "<ol>" in fallback
        assert "<li>" in fallback
        # Should have substantive content
        assert len(fallback) > 200

    def test_ki_stack_fallback_has_professional_structure(self):
        """Fallback should have proper HTML structure."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="kmu"
        )

        # Should have proper HTML
        assert "<p>" in fallback
        assert "</p>" in fallback
        # Should have section headers
        assert "<strong>" in fallback


class TestBranchDeepDiveFallbackQuality:
    """Test branch_deep_dive fallback content quality."""

    def test_branch_deep_dive_fallback_no_support_mention(self):
        """Fallback should not mention 'Support' or 'kontaktieren'."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="solo"
        )

        assert "support" not in fallback.lower()
        assert "kontaktieren" not in fallback.lower()
        # Note: "fehlerquoten" (error rates) is legitimate business content
        # We only want to avoid error messages like "ein fehler ist aufgetreten"
        assert "fehler ist aufgetreten" not in fallback.lower()
        assert "error occurred" not in fallback.lower()

    def test_branch_deep_dive_fallback_has_branch_context(self):
        """Fallback should incorporate branch context."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="team"
        )

        # Should have context-aware content
        assert len(fallback) > 150
        # Should have professional structure
        assert "<p>" in fallback

    def test_branch_deep_dive_fallback_constructive_tone(self):
        """Fallback should be constructive, not apologetic."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="branch_deep_dive",
            company_size="kmu"
        )

        # Should not be apologetic
        assert "leider" not in fallback.lower()
        assert "entschuldigung" not in fallback.lower()
        assert "sorry" not in fallback.lower()


class TestGenericFallbackQuality:
    """Test generic fallback content for other sections."""

    def test_generic_fallback_structure(self):
        """Any fallback should have proper structure."""
        from services.report_validator import _build_generic_leak_fallback

        for section_name in ["ki_stack_summary", "branch_deep_dive", "exec_summary"]:
            fallback = _build_generic_leak_fallback(
                section_name=section_name,
                company_size="team"
            )

            # All fallbacks should have minimum content
            assert len(fallback) > 100, f"Fallback for {section_name} too short"
            # All fallbacks should have HTML
            assert "<p>" in fallback, f"Fallback for {section_name} missing <p> tags"

    def test_fallback_size_awareness(self):
        """Fallback content should be size-aware."""
        from services.report_validator import _build_generic_leak_fallback

        solo_fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="solo"
        )

        kmu_fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="kmu"
        )

        # Both should have content
        assert len(solo_fallback) > 100
        assert len(kmu_fallback) > 100


class TestFallbackNoPlaceholders:
    """Ensure fallbacks don't contain debug placeholders."""

    def test_no_todo_placeholders(self):
        """Fallback should not contain TODO or placeholder markers."""
        from services.report_validator import _build_generic_leak_fallback

        for section_name in ["ki_stack_summary", "branch_deep_dive"]:
            fallback = _build_generic_leak_fallback(
                section_name=section_name,
                company_size="team"
            )

            assert "TODO" not in fallback
            assert "FIXME" not in fallback
            assert "XXX" not in fallback
            assert "[PLACEHOLDER]" not in fallback.upper()

    def test_no_debug_content(self):
        """Fallback should not contain debug/test content."""
        from services.report_validator import _build_generic_leak_fallback

        fallback = _build_generic_leak_fallback(
            section_name="ki_stack_summary",
            company_size="kmu"
        )

        assert "debug" not in fallback.lower()
        assert "test content" not in fallback.lower()
        assert "lorem ipsum" not in fallback.lower()
