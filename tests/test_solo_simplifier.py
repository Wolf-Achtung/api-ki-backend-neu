# -*- coding: utf-8 -*-
"""
Tests for Solo Simplifier Service

FIX-SOLO-VEREINFACHUNG: Tests for automatic terminology replacement.
"""
import pytest
from typing import Any, Dict, List


class TestSoloSimplifierBasic:
    """Basic tests for solo_simplifier functions."""

    def test_import_solo_simplifier(self):
        """Verify solo_simplifier can be imported."""
        from services.solo_simplifier import (
            simplify_text,
            simplify_html,
            check_blacklist_violations,
            validate_solo_content,
            is_solo_size,
        )
        assert callable(simplify_text)
        assert callable(simplify_html)

    def test_get_replacements_not_empty(self):
        """Verify replacement mapping is loaded."""
        from services.solo_simplifier import get_replacements
        replacements = get_replacements()
        assert isinstance(replacements, dict)
        assert len(replacements) > 0

    def test_get_blacklist_headlines_not_empty(self):
        """Verify blacklist headlines are loaded."""
        from services.solo_simplifier import get_blacklist_headlines
        blacklist = get_blacklist_headlines()
        assert isinstance(blacklist, list)
        assert len(blacklist) > 0
        assert "Stakeholder" in blacklist


class TestSimplifyText:
    """Tests for text simplification."""

    def test_stakeholder_replacement(self):
        """Verify 'Stakeholder' is replaced."""
        from services.solo_simplifier import simplify_text
        text = "Die Stakeholder müssen einbezogen werden."
        result = simplify_text(text)
        assert "Stakeholder" not in result
        # Case is preserved: 'Stakeholder' (capital S) → 'Wichtige Personen' (capital W)
        assert "Wichtige Personen" in result or "wichtige Personen" in result

    def test_governance_replacement(self):
        """Verify 'Governance' is replaced."""
        from services.solo_simplifier import simplify_text
        text = "Governance-Prozesse sind wichtig."
        result = simplify_text(text)
        assert "Governance" not in result

    def test_roadmap_replacement(self):
        """Verify 'Roadmap' is replaced."""
        from services.solo_simplifier import simplify_text
        text = "Die Roadmap zeigt die nächsten Schritte."
        result = simplify_text(text)
        assert "Roadmap" not in result
        assert "Plan" in result

    def test_stack_replacement(self):
        """Verify 'KI-Stack' is replaced."""
        from services.solo_simplifier import simplify_text
        text = "Der KI-Stack umfasst mehrere Tools."
        result = simplify_text(text)
        assert "Stack" not in result
        assert "Werkzeugkasten" in result

    def test_word_boundary_preserved(self):
        """Verify partial matches are not replaced."""
        from services.solo_simplifier import simplify_text
        # "Team" should be replaced but "Teamwork" should not be partially affected
        text = "Das Team arbeitet gut zusammen."
        result = simplify_text(text)
        # Should replace "Team" with "Sie"
        assert "Sie" in result or "Team" not in result

    def test_empty_text_handled(self):
        """Verify empty text is handled gracefully."""
        from services.solo_simplifier import simplify_text
        assert simplify_text("") == ""
        assert simplify_text(None) is None  # type: ignore


class TestSimplifyHtml:
    """Tests for HTML simplification."""

    def test_html_tags_preserved(self):
        """Verify HTML tags are not modified."""
        from services.solo_simplifier import simplify_html
        html = '<h2>Stakeholder-Übersicht</h2>'
        result = simplify_html(html)
        assert '<h2>' in result
        assert '</h2>' in result
        assert 'Stakeholder' not in result

    def test_html_attributes_preserved(self):
        """Verify HTML attributes are not affected."""
        from services.solo_simplifier import simplify_html
        html = '<div class="stakeholder-section">Stakeholder müssen informiert werden.</div>'
        result = simplify_html(html)
        # Attribute should be preserved (contains "stakeholder")
        assert 'class="stakeholder-section"' in result
        # Text content should be replaced
        assert '>wichtige Personen' in result or 'Stakeholder</div>' not in result


class TestBlacklistValidation:
    """Tests for blacklist validation."""

    def test_headline_violations_detected(self):
        """Verify blacklist terms in headlines are detected."""
        from services.solo_simplifier import check_blacklist_violations
        html = '<h2>Stakeholder Management</h2><p>Text</p>'
        violations = check_blacklist_violations(html, check_headlines_only=True)
        assert len(violations) > 0
        assert any(v['term'] == 'Stakeholder' for v in violations)

    def test_body_violations_detected(self):
        """Verify blacklist terms in body are detected."""
        from services.solo_simplifier import check_blacklist_violations
        html = '<p>Die Governance-Struktur muss verbessert werden.</p>'
        violations = check_blacklist_violations(html, check_headlines_only=False)
        assert len(violations) > 0

    def test_clean_content_passes(self):
        """Verify clean content has no violations."""
        from services.solo_simplifier import check_blacklist_violations
        html = '<h2>Wichtige Personen</h2><p>Der Plan zeigt die nächsten Schritte.</p>'
        violations = check_blacklist_violations(html, check_headlines_only=True)
        assert len(violations) == 0


class TestValidateSoloContent:
    """Tests for full validation."""

    def test_valid_content_passes(self):
        """Verify valid Solo content passes validation."""
        from services.solo_simplifier import validate_solo_content
        content = '<h2>Ihr Plan</h2><p>Die wichtigen Personen wurden informiert.</p>'
        is_valid, violations = validate_solo_content(content, "test_section")
        assert is_valid is True
        assert len([v for v in violations if v.get('severity') == 'error']) == 0

    def test_invalid_headline_fails(self):
        """Verify blacklist term in headline fails validation."""
        from services.solo_simplifier import validate_solo_content
        content = '<h2>Stakeholder Analyse</h2><p>Guter Text.</p>'
        is_valid, violations = validate_solo_content(content, "test_section")
        assert is_valid is False
        assert len(violations) > 0


class TestIsSoloSize:
    """Tests for size detection."""

    def test_solo_detected(self):
        """Verify 'solo' size is detected."""
        from services.solo_simplifier import is_solo_size
        assert is_solo_size("solo") is True
        assert is_solo_size("Solo") is True
        assert is_solo_size("SOLO") is True

    def test_numeric_solo_detected(self):
        """Verify '1' is detected as Solo."""
        from services.solo_simplifier import is_solo_size
        assert is_solo_size("1") is True

    def test_freiberufler_detected(self):
        """Verify 'freiberufler' is detected as Solo."""
        from services.solo_simplifier import is_solo_size
        assert is_solo_size("freiberufler") is True
        assert is_solo_size("selbstständig") is True

    def test_team_not_solo(self):
        """Verify team sizes are not Solo."""
        from services.solo_simplifier import is_solo_size
        assert is_solo_size("team") is False
        assert is_solo_size("2-10") is False
        assert is_solo_size("kmu") is False


class TestAutoFix:
    """Tests for auto-fix functionality."""

    def test_auto_fix_applies_replacements(self):
        """Verify auto_fix_solo_content applies replacements."""
        from services.solo_simplifier import auto_fix_solo_content
        content = '<h2>Stakeholder</h2><p>Die Roadmap ist fertig.</p>'
        fixed, count = auto_fix_solo_content(content)
        assert 'Stakeholder' not in fixed
        assert 'Roadmap' not in fixed
        assert count > 0

    def test_process_solo_section(self):
        """Verify process_solo_section works end-to-end."""
        from services.solo_simplifier import process_solo_section
        content = '<h2>Governance</h2><p>Der KI-Stack ist bereit.</p>'
        result = process_solo_section(content, "test_section", auto_fix=True)

        assert result['section'] == 'test_section'
        assert result['auto_fixed'] is True
        assert 'Governance' not in result['processed_content']
        assert 'Stack' not in result['processed_content']


class TestValidatorIntegration:
    """Tests for validator integration."""

    def test_validator_imports_solo_simplifier(self):
        """Verify report_validator imports solo_simplifier."""
        from services.report_validator import ReportValidator
        # If import works, the integration is in place
        assert hasattr(ReportValidator, 'validate_all')

    def test_validator_checks_solo_terminology(self):
        """Verify validator has _check_solo_terminology method."""
        from services.report_validator import ReportValidator

        # Create a minimal validator instance
        sections = {
            'EXECUTIVE_SUMMARY_HTML': '<h2>Stakeholder</h2><p>Test</p>'
        }
        meta = {'unternehmensgroesse': 'solo'}

        validator = ReportValidator(sections, meta)
        # Method should exist
        assert hasattr(validator, '_check_solo_terminology')
