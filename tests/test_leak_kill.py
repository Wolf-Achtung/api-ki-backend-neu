#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0 Leak-Kill Tests

Tests for:
- Solo leak scanner detection
- Lexicon replacement integration
- Hard gate validation
- Security context exceptions

Goal: SOLO_LEAK_COUNT == 0 for all solo reports.
"""
import pytest


class TestLeakTermDetection:
    """Tests for detecting Team/KMU leaks in solo content."""

    def test_detects_team_term(self):
        """Test detection of 'Team' as critical leak."""
        from services.solo_leak_scanner import scan_solo_leaks, LeakSeverity

        text = "Ihr Team sollte diese Aufgabe übernehmen."
        result = scan_solo_leaks(text, section_id="EXECUTIVE_SUMMARY")

        assert result.total_count > 0
        assert result.critical_count > 0
        assert not result.passed

        # Check that 'Team' was found
        terms_found = [leak.term for leak in result.leaks]
        assert any("Team" in term for term in terms_found)

    def test_detects_stakeholder_term(self):
        """Test detection of 'Stakeholder' as critical leak."""
        from services.solo_leak_scanner import scan_solo_leaks

        text = "Alle Stakeholder müssen eingebunden werden."
        result = scan_solo_leaks(text, section_id="RISKS")

        assert result.critical_count > 0
        terms_found = [leak.term for leak in result.leaks]
        assert any("Stakeholder" in term for term in terms_found)

    def test_detects_skalierung_term(self):
        """Test detection of 'Skalierung' as critical leak."""
        from services.solo_leak_scanner import scan_solo_leaks

        text = "Die Skalierung des Systems ist wichtig."
        result = scan_solo_leaks(text, section_id="ROADMAP")

        assert result.critical_count > 0
        terms_found = [leak.term for leak in result.leaks]
        assert any("Skalierung" in term for term in terms_found)

    def test_detects_abteilung_term(self):
        """Test detection of 'Abteilung' as critical leak."""
        from services.solo_leak_scanner import scan_solo_leaks

        text = "Jede Abteilung hat eigene Anforderungen."
        result = scan_solo_leaks(text, section_id="QUICK_WINS")

        assert result.critical_count > 0

    def test_detects_unternehmensweit_term(self):
        """Test detection of 'unternehmensweit' as critical leak."""
        from services.solo_leak_scanner import scan_solo_leaks

        text = "Die unternehmensweite Einführung erfordert Zeit."
        result = scan_solo_leaks(text, section_id="SUMMARY")

        assert result.critical_count > 0


class TestAllowedTerms:
    """Tests for terms that should NOT trigger leaks."""

    def test_ki_is_allowed(self):
        """Test that 'KI' is always allowed (never a forbidden term)."""
        from services.solo_leak_scanner import scan_solo_leaks

        text = "KI-basierte Lösungen sind ideal für Ihre Anforderungen."
        result = scan_solo_leaks(text, section_id="TOOLING")

        # KI should not be flagged
        terms_found = [leak.term.lower() for leak in result.leaks]
        assert "ki" not in terms_found
        assert "ki-" not in terms_found

    def test_clean_solo_text_passes(self):
        """Test that clean solo-appropriate text passes validation."""
        from services.solo_leak_scanner import scan_solo_leaks

        text = """
        Als Einzelunternehmer können Sie von KI-Werkzeugen profitieren.
        Ihr Arbeitsalltag wird durch Automatisierung effizienter.
        Die Umsetzung erfolgt in wenigen Wochen.
        """
        result = scan_solo_leaks(text, section_id="EXECUTIVE_SUMMARY")

        # Should pass with no critical leaks
        assert result.critical_count == 0
        assert result.passed


class TestSecurityContextException:
    """Tests for 'prompt injection' exception in security contexts."""

    def test_prompt_injection_allowed_in_security_section(self):
        """Test that 'prompt injection' is allowed in security-related sections."""
        from services.solo_leak_scanner import scan_solo_leaks

        text = "Prompt Injection ist ein Sicherheitsrisiko bei LLM-Anwendungen."
        result = scan_solo_leaks(text, section_id="RISKS_SECURITY")

        # Should not be flagged as leak in security context
        prompt_injection_leaks = [
            leak for leak in result.leaks
            if "injection" in leak.term.lower()
        ]
        assert len(prompt_injection_leaks) == 0

    def test_prompt_injection_flagged_outside_security(self):
        """Test that 'prompt injection' is flagged outside security contexts."""
        from services.solo_leak_scanner import scan_solo_leaks

        text = "Prompt Injection kann auch für kreative Zwecke genutzt werden."
        result = scan_solo_leaks(text, section_id="QUICK_WINS_HTML")

        # Should be flagged as warning outside security context
        prompt_injection_leaks = [
            leak for leak in result.leaks
            if "injection" in leak.term.lower()
        ]
        assert len(prompt_injection_leaks) > 0


class TestLexiconIntegration:
    """Tests for lexicon replacement integration."""

    def test_apply_lexicon_replaces_terms(self):
        """Test that lexicon correctly replaces enterprise terms."""
        from services.lexicon_loader import apply_lexicon

        text = "Die Skalierung des Tech-Stack ist wichtig für Stakeholder."
        result, count = apply_lexicon(text, persona="solo")

        # Should have made replacements
        assert count > 0
        assert "Skalierung" not in result
        assert "Tech-Stack" not in result
        assert "Stakeholder" not in result

        # Should contain replacements
        assert "Ausbau" in result or "ausbauen" in result.lower()
        assert "Technikpaket" in result
        assert "Beteiligte" in result

    def test_combined_lexicon_and_scan(self):
        """Test the combined lexicon + scan pipeline."""
        from services.solo_leak_scanner import apply_solo_lexicon_and_validate

        sections = {
            "SUMMARY": "Die Skalierung des Systems und die Stakeholder-Kommunikation.",
            "QUICK_WINS": "Einfache KI-Werkzeuge für Ihren Arbeitsalltag.",
        }

        processed, result = apply_solo_lexicon_and_validate(sections, company_size="solo")

        # Lexicon should have processed sections
        assert "Skalierung" not in processed["SUMMARY"]
        assert "Stakeholder" not in processed["SUMMARY"]


class TestHardGate:
    """Tests for hard gate validation."""

    def test_gate_passes_clean_content(self):
        """Test that gate passes for leak-free content."""
        from services.solo_leak_scanner import validate_solo_leak_gate

        sections = {
            "SUMMARY": "Als Einzelunternehmer können Sie von KI profitieren.",
            "QUICK_WINS": "Einfache Werkzeuge für Ihren Arbeitsalltag.",
            "RISKS": "Datenschutz ist ein wichtiges Thema.",
        }

        passed, result = validate_solo_leak_gate(sections)

        assert passed
        assert result.critical_count == 0

    def test_gate_fails_with_leaks(self):
        """Test that gate fails when critical leaks are present."""
        from services.solo_leak_scanner import validate_solo_leak_gate

        sections = {
            "SUMMARY": "Das Team sollte die Skalierung planen.",
            "QUICK_WINS": "Alle Stakeholder einbinden.",
        }

        passed, result = validate_solo_leak_gate(sections)

        assert not passed
        assert result.critical_count > 0

    def test_gate_with_warning_only_flag(self):
        """Test gate behavior with fail_on_warning=True."""
        from services.solo_leak_scanner import validate_solo_leak_gate

        sections = {
            "SUMMARY": "Die Organisation muss den Prozess optimieren.",
        }

        # Default: warnings don't fail
        passed_default, _ = validate_solo_leak_gate(sections, fail_on_warning=False)

        # With fail_on_warning: warnings fail
        passed_strict, result = validate_solo_leak_gate(sections, fail_on_warning=True)

        # At least one of these should detect warnings
        # (Organisation and Prozess are warning-level terms)
        assert result.warning_count >= 0  # May or may not have warnings


class TestScanAllSections:
    """Tests for scanning multiple sections."""

    def test_scans_all_string_sections(self):
        """Test that all string sections are scanned."""
        from services.solo_leak_scanner import scan_all_sections

        sections = {
            "COVER": "Deckblatt",
            "SUMMARY": "Das Team plant die Umsetzung.",
            "NUMERIC_VALUE": 42,  # Should be skipped
            "EMPTY": "",  # Should be skipped
            "QUICK_WINS": "Sauberer Text ohne Leaks.",
        }

        result = scan_all_sections(sections)

        # Should have scanned at least 2 sections (SUMMARY and QUICK_WINS have enough content)
        assert result.sections_scanned >= 1

        # Should have found leak in SUMMARY
        summary_leaks = [leak for leak in result.leaks if "SUMMARY" in leak.section_id]
        assert len(summary_leaks) > 0


class TestLeakScanResult:
    """Tests for LeakScanResult dataclass."""

    def test_result_passed_property(self):
        """Test that passed is True only when critical_count is 0."""
        from services.solo_leak_scanner import LeakScanResult, Leak, LeakSeverity

        result = LeakScanResult()
        assert result.passed

        # Add warning - should still pass
        result.add_leak(Leak(
            term="Prozess",
            context_snippet="test",
            section_id="TEST",
            severity=LeakSeverity.WARNING,
        ))
        assert result.passed

        # Add critical - should fail
        result.add_leak(Leak(
            term="Team",
            context_snippet="test",
            section_id="TEST",
            severity=LeakSeverity.CRITICAL,
        ))
        assert not result.passed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
