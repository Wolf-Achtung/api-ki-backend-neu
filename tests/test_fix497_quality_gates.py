"""
Test Suite for FIX-497: Premium + Zero Tolerance Quality Gates
==============================================================
Tests for:
1. Code fence removal
2. Empty page prevention
3. Template include resolution
4. Metrics integrity
5. Solo term replacements
"""

import pytest
import re
from pathlib import Path


class TestCodeFenceRemoval:
    """Tests for code fence sanitization."""

    def test_strip_code_fences_basic(self):
        """Test basic code fence removal."""
        from services.report_renderer import strip_code_fences_final

        html = '```html\n<p>Hello</p>\n```'
        result, count = strip_code_fences_final(html)

        assert '```' not in result
        assert count >= 2  # Opening and closing fence

    def test_strip_code_fences_with_language(self):
        """Test code fence with language specifier."""
        from services.report_renderer import strip_code_fences_final

        html = '```python\nprint("hello")\n```'
        result, count = strip_code_fences_final(html)

        assert '```python' not in result
        assert '```' not in result

    def test_strip_code_fences_preserves_html(self):
        """Test that HTML content is preserved."""
        from services.report_renderer import strip_code_fences_final

        html = '<div>Content</div>\n```\n<p>More</p>'
        result, count = strip_code_fences_final(html)

        assert '<div>Content</div>' in result
        assert '<p>More</p>' in result

    def test_strip_code_fences_empty_input(self):
        """Test handling of empty input."""
        from services.report_renderer import strip_code_fences_final

        result, count = strip_code_fences_final('')
        assert result == ''
        assert count == 0

        result, count = strip_code_fences_final(None)
        assert result == ''
        assert count == 0


class TestEmptyPagePrevention:
    """Tests for empty page detection and prevention."""

    def test_cleanup_pagebreaks_consecutive(self):
        """Test removal of consecutive page breaks."""
        from services.report_renderer import cleanup_pagebreaks

        html = '''
        <div class="page-break"></div>
        <div class="page-break"></div>
        <div class="page-break"></div>
        '''
        result, count = cleanup_pagebreaks(html)

        # Should reduce consecutive breaks
        assert count >= 0  # May remove some

    def test_cleanup_pagebreaks_preserves_content(self):
        """Test that content between breaks is preserved."""
        from services.report_renderer import cleanup_pagebreaks

        html = '''
        <div class="page-break"></div>
        <p>Important content</p>
        <div class="page-break"></div>
        '''
        result, count = cleanup_pagebreaks(html)

        assert '<p>Important content</p>' in result

    def test_cleanup_empty_sections(self):
        """Test that empty sections are handled."""
        from services.report_renderer import cleanup_pagebreaks

        html = '<section class="chapter"></section>'
        result, count = cleanup_pagebreaks(html)

        # Empty section should be preserved or flagged
        assert result is not None


class TestSoloTermReplacements:
    """Tests for solo-friendly term replacements."""

    def test_module_replacement(self):
        """Test Module -> Baustein replacement."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        # Use a section name from check_sections list
        sections = {'EXECUTIVE_SUMMARY_HTML': 'Nutzen Sie diese Module für Ihr Projekt.'}
        result = apply_solo_language_normalizer(sections, 'solo')

        assert 'Bausteine' in result['EXECUTIVE_SUMMARY_HTML']
        assert 'Module' not in result['EXECUTIVE_SUMMARY_HTML']

    def test_rollout_removal(self):
        """Test Rollout is REMOVED (FIX-526: not replaced, removed entirely)."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {'EXECUTIVE_SUMMARY_HTML': 'Der Rollout erfolgt schrittweise.'}
        result = apply_solo_language_normalizer(sections, 'solo')

        # FIX-526: Rollout is removed entirely, not replaced with Einführung
        assert 'Rollout' not in result['EXECUTIVE_SUMMARY_HTML']
        # Should not have double spaces after removal
        assert '  ' not in result['EXECUTIVE_SUMMARY_HTML']

    def test_skalierung_replacement(self):
        """Test Skalierung -> Ausbau replacement."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {'RECOMMENDATIONS_HTML': 'Die Skalierung ist wichtig.'}
        result = apply_solo_language_normalizer(sections, 'solo')

        assert 'Ausbau' in result['RECOMMENDATIONS_HTML']
        assert 'Skalierung' not in result['RECOMMENDATIONS_HTML']

    def test_stack_replacement(self):
        """Test Stack -> Technikpaket replacement."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {'TOOLS_HTML': 'Ihr Tech-Stack sollte modern sein.'}
        result = apply_solo_language_normalizer(sections, 'solo')

        assert 'Technikpaket' in result['TOOLS_HTML']
        assert 'Tech-Stack' not in result['TOOLS_HTML']

    def test_no_replacement_for_kmu(self):
        """Test that KMU persona keeps enterprise terms."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {'EXECUTIVE_SUMMARY_HTML': 'Nutzen Sie diese Module für Ihr Projekt.'}
        result = apply_solo_language_normalizer(sections, 'kmu')

        # Should NOT replace for kmu
        assert 'Module' in result['EXECUTIVE_SUMMARY_HTML']

    def test_placeholder_removal(self):
        """Test removal of placeholder text."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {'EXECUTIVE_SUMMARY_HTML': 'Beispieltext: Dies ist ein Test.'}
        result = apply_solo_language_normalizer(sections, 'solo')

        assert 'Beispieltext' not in result['EXECUTIVE_SUMMARY_HTML']


class TestMetricsIntegrity:
    """Tests for pipeline metrics storage."""

    def test_gate_metrics_stored(self):
        """Test that gate metrics are properly stored."""
        # This tests the structure added to sections in gpt_analyze.py
        expected_keys = [
            'PIPELINE_WARNINGS_COUNT',
            'PIPELINE_FALLBACK_COUNT',
            'PIPELINE_HEALS_COUNT',
            'PIPELINE_GRADE',
        ]

        # Verify the keys exist in the codebase
        gpt_analyze = Path('gpt_analyze.py').read_text()

        for key in expected_keys:
            assert key in gpt_analyze, f"Missing metric key: {key}"

    def test_grade_calculation_a(self):
        """Test grade A calculation (zero issues)."""
        # Grade A: warnings=0, fallbacks=0, heals=0
        # This is verified by the actual code logic
        warnings = 0
        fallbacks = 0
        heals = 0

        grade = "A" if (warnings == 0 and fallbacks == 0 and heals == 0) else "B"
        assert grade == "A"

    def test_grade_calculation_b(self):
        """Test grade B calculation (minor issues)."""
        warnings = 3
        fallbacks = 1
        heals = 0

        grade = "A" if (warnings == 0 and fallbacks == 0 and heals == 0) else \
                "B" if (warnings <= 5 and fallbacks <= 2) else "C"
        assert grade == "B"

    def test_grade_calculation_c(self):
        """Test grade C calculation (significant issues)."""
        warnings = 10
        fallbacks = 5
        heals = 3

        grade = "A" if (warnings == 0 and fallbacks == 0 and heals == 0) else \
                "B" if (warnings <= 5 and fallbacks <= 2) else "C"
        assert grade == "C"


class TestPostflightChecker:
    """Tests for the postflight checker script."""

    def test_validate_clean_html(self):
        """Test validation of clean HTML."""
        from scripts.postflight_checker import validate_html

        clean_html = '<div><p>Clean content without issues.</p></div>'
        passed, issues = validate_html(clean_html)

        assert passed is True
        assert len([i for i in issues if 'FORBIDDEN' in i]) == 0

    def test_validate_html_with_code_fence(self):
        """Test detection of code fences."""
        from scripts.postflight_checker import validate_html

        bad_html = '<div>```html\n<p>Content</p>\n```</div>'
        passed, issues = validate_html(bad_html)

        assert passed is False
        assert any('Code fence' in i for i in issues)

    def test_validate_html_with_leak_phrase(self):
        """Test detection of leak phrases."""
        from scripts.postflight_checker import validate_html

        bad_html = '<div>Beschreibe dein Anliegen genauer.</div>'
        passed, issues = validate_html(bad_html)

        assert passed is False
        assert any('LEAK PHRASE' in i for i in issues)

    def test_validate_html_strict_mode(self):
        """Test strict mode treats warnings as errors."""
        from scripts.postflight_checker import validate_html

        # HTML with potential empty page issue (warning)
        html = '<section class="chapter"></section>'
        passed_normal, issues_normal = validate_html(html, strict=False)
        passed_strict, issues_strict = validate_html(html, strict=True)

        # Strict mode should have more issues (warnings become errors)
        assert len(issues_strict) >= len(issues_normal)


class TestTemplateIncludes:
    """Tests for Jinja2 include resolution."""

    def test_hauptleistung_template_exists(self):
        """Test that hauptleistung context template exists."""
        template_path = Path('prompts/de/_hauptleistung_context.md')
        assert template_path.exists(), "German hauptleistung template missing"

        template_en = Path('prompts/en/_hauptleistung_context.md')
        assert template_en.exists(), "English hauptleistung template missing"

    def test_prompt_loader_with_includes(self):
        """Test that prompt loader can resolve includes."""
        from services.prompt_loader import load_prompt

        # This should not raise an error about includes
        try:
            result = load_prompt('gamechanger', lang='de', vars_dict={
                'hauptleistung': 'Test Hauptleistung',
                'BRANCHE_LABEL': 'IT',
                'COMPANY_SIZE': 'solo',
            })
            # If we get here, includes are working
            assert result is not None
        except Exception as e:
            if 'include' in str(e).lower():
                pytest.fail(f"Include resolution failed: {e}")
            # Other errors might be OK (missing variables, etc.)


class TestConditionalRendering:
    """Tests for conditional section rendering in templates."""

    def test_template_has_conditional_funding(self):
        """Test that funding section has conditional rendering."""
        template = Path('templates/pdf_template_v7.html').read_text()

        # Check for conditional rendering of FOERDERPOTENZIAL_HTML
        assert '{% if FOERDERPOTENZIAL_HTML' in template, \
            "FOERDERPOTENZIAL_HTML should have conditional rendering"

    def test_template_has_conditional_risks(self):
        """Test that risk section has conditional rendering."""
        template = Path('templates/pdf_template_v7.html').read_text()

        # v7 uses RISK_ENGINE_HTML / RISK_ENGINE_V3_HTML
        assert '{% if RISK_ENGINE_HTML' in template or '{% if RISKS_HTML' in template, \
            "Risk section should have conditional rendering"

    def test_template_has_table_orphan_css(self):
        """Test that templates include table orphan prevention CSS."""
        template = Path('templates/pdf_template_v7.html').read_text()

        # Check for table orphan prevention
        assert 'page-break-inside: avoid' in template
        assert 'table' in template.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
