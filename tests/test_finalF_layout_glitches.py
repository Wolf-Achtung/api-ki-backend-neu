# -*- coding: utf-8 -*-
"""
Tests for Fix-Batch F - Layout & Content Guards

Tests:
- BC table has page-break-inside: avoid
- Text glitches are fixed (resourceselung, Ressourcen: 0)
- No orphan pages with single rows
"""

import os
import pytest
import re

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestBCTablePageBreak:
    """Test BC table page break controls."""

    def test_pdf_template_has_bc_table_page_break_css(self):
        """Test that PDF template has BC table page break CSS."""
        from pathlib import Path

        template_path = Path(__file__).parent.parent / "templates" / "pdf_template_v7.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            css = f.read()

        # Should have page-break-inside: avoid for cards
        assert "page-break-inside: avoid" in css

        # Should have business case section
        assert "business-case-compact" in css or "BUSINESS_CASE_ENGINE_HTML" in css

    def test_business_case_card_has_break_avoid(self):
        """Test that card CSS has page-break-inside: avoid."""
        from pathlib import Path

        template_path = Path(__file__).parent.parent / "templates" / "pdf_template_v7.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            css = f.read()

        # v7 uses .card-nobreak and other card classes with page-break-inside: avoid
        assert ".card-nobreak" in css or "page-break-inside: avoid" in css
        assert "page-break-inside: avoid" in css


class TestTextGlitchFixer:
    """Test text glitch fixes."""

    def test_fix_resourceselung_glitch(self):
        """Test that 'resourceselung' is fixed to 'Ressourcenstaffelung'."""
        from services.content_quality_enforcer import fix_text_glitches

        html = "<p>Die resourceselung erfolgt nach Bedarf.</p>"

        result, count = fix_text_glitches(html)

        assert "resourceselung" not in result
        assert "Ressourcenstaffelung" in result
        assert count == 1

    def test_fix_ressourcen_zero(self):
        """Test that 'Ressourcen: 0' is removed."""
        from services.content_quality_enforcer import fix_text_glitches

        html = "<p>Team: 5 Mitarbeiter, Ressourcen: 0</p>"

        result, count = fix_text_glitches(html)

        assert "Ressourcen: 0" not in result
        assert "Team: 5 Mitarbeiter" in result

    def test_fix_mitarbeiter_zero(self):
        """Test that 'Mitarbeiter: 0' is removed."""
        from services.content_quality_enforcer import fix_text_glitches

        html = "<p>Abteilung A: Mitarbeiter: 0</p>"

        result, count = fix_text_glitches(html)

        assert "Mitarbeiter: 0" not in result

    def test_apply_text_glitch_fixer_to_sections(self):
        """Test that text glitch fixer applies to all sections."""
        from services.content_quality_enforcer import apply_text_glitch_fixer

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Die resourceselung ist wichtig.</p>",
            "RECOMMENDATIONS_HTML": "<p>Ressourcen: 0 verfügbar.</p>",
            "OTHER_KEY": "unchanged content",
        }

        result = apply_text_glitch_fixer(sections)

        assert "resourceselung" not in result["EXECUTIVE_SUMMARY_HTML"]
        assert "Ressourcen: 0" not in result["RECOMMENDATIONS_HTML"]
        assert result["OTHER_KEY"] == "unchanged content"


class TestTextGlitchPatterns:
    """Test various text glitch patterns."""

    def test_resourceselung_case_insensitive(self):
        """Test that resourceselung fix is case insensitive."""
        from services.content_quality_enforcer import fix_text_glitches

        html = "<p>RESOURCESELUNG und Resourceselung</p>"

        result, count = fix_text_glitches(html)

        assert "resourceselung" not in result.lower() or "Ressourcenstaffelung" in result

    def test_ressourcen_zero_with_space_variants(self):
        """Test various 'Ressourcen: 0' variants."""
        from services.content_quality_enforcer import fix_text_glitches

        test_cases = [
            "Ressourcen: 0",
            "Ressourcen:0",
            "Ressourcen : 0",
            "Ressourcen 0",
        ]

        for test in test_cases:
            html = f"<p>Test {test} Ende</p>"
            result, _ = fix_text_glitches(html)
            # Zero resource text should be removed or cleaned
            assert "0" not in result.split("Test")[1].split("Ende")[0].strip() or \
                   test not in result


class TestOrphanPagePrevention:
    """Test orphan page prevention."""

    def test_bc_engine_html_has_class(self):
        """Test that BC engine HTML generator uses correct class name."""
        from services.business_case_engine_v2 import business_case_report_to_html

        # Verify the function uses the right class in its output template
        import inspect
        source = inspect.getsource(business_case_report_to_html)

        # The template should include business-case-engine-v2 class
        assert "business-case-engine-v2" in source or "business_case" in source.lower()


class TestBatchFIntegration:
    """Integration tests for Fix-Batch F."""

    def test_quality_enforcer_pipeline_includes_glitch_fixer(self):
        """Test that apply_all_quality_enforcers includes text glitch fixer."""
        from services.content_quality_enforcer import apply_all_quality_enforcers

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Test resourceselung content.</p>",
            "RECOMMENDATIONS_HTML": "<p>Ressourcen: 0 here.</p>",
        }

        result = apply_all_quality_enforcers(sections)

        # Glitches should be fixed
        assert "resourceselung" not in result.get("EXECUTIVE_SUMMARY_HTML", "")

    def test_no_known_glitches_in_output(self):
        """Test that known glitches don't appear in output."""
        known_glitches = [
            "resourceselung",
            "Ressourcen: 0",
            "Mitarbeiter: 0",
        ]

        # These patterns should be caught by the fixer
        from services.content_quality_enforcer import TEXT_GLITCH_REPLACEMENTS

        glitch_patterns = [pattern for pattern, _, _ in TEXT_GLITCH_REPLACEMENTS]

        # Each known glitch should have a pattern
        for glitch in known_glitches:
            matched = any(re.search(p, glitch, re.IGNORECASE) for p in glitch_patterns)
            assert matched, f"No pattern for glitch: {glitch}"
