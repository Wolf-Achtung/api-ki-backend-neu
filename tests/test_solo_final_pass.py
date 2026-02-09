#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-554: Tests for Solo Final Pass

Tests:
1. Enterprise term elimination (Governance, Audit-Trail, Stakeholder, etc.)
2. Duz→Sie conversion (du/dir/dein → Sie/Ihnen/Ihr)
3. KPI → Kennzahlen replacement
4. Platzhalter validator exception for technical context
5. Tag-split resilience (Gover</span><span>nance)
6. Verification function
7. Integration with solo_leak_scanner updates

Version: 1.0.0 (FIX-554)
"""
import re
import pytest
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.solo_final_pass import (
    apply_solo_final_pass,
    apply_solo_final_pass_to_sections,
    eliminate_enterprise_terms,
    convert_duz_to_sie,
    replace_kpi_terms,
    verify_solo_report_clean,
    FORBIDDEN_SOLO_TOKENS,
)


# =============================================================================
# TEST: Enterprise Term Elimination
# =============================================================================

class TestEnterpriseTermElimination:
    """Test elimination of enterprise terms from solo report HTML."""

    def test_governance_simple(self):
        """Governance in plain text is replaced."""
        html = "<p>Die Governance des Projekts ist wichtig.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Governance" not in result
        assert "Spielregeln" in result or "Leitplanken" in result
        assert count > 0

    def test_governance_with_adjective_dativ(self):
        """'starker Governance' → 'klaren Spielregeln' (Dativ)."""
        html = "<p>Dank starker Governance gelingt die Umsetzung.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Governance" not in result
        assert "klaren Spielregeln" in result

    def test_governance_with_adjective_nominativ(self):
        """'starke Governance' → 'klare Spielregeln' (Nominativ)."""
        html = "<p>Eine starke Governance ist die Basis.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Governance" not in result
        assert "klare Spielregeln" in result

    def test_governance_framework(self):
        """'Governance-Framework' → 'Grundregeln'."""
        html = "<p>Ein Governance-Framework ist notwendig.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Governance" not in result
        assert "Grundregeln" in result

    def test_governance_tag_split(self):
        """Governance split across HTML tags is caught."""
        html = '<p>Die <span class="bold">Gover</span><span>nance</span> ist wichtig.</p>'
        result, count = eliminate_enterprise_terms(html)
        assert "Governance" not in result.replace("</span><span>", "")
        # The catch-all regex should replace it
        assert count > 0

    def test_governance_soft_hyphen(self):
        """Governance with soft-hyphen is caught by catch-all."""
        # Soft hyphen is \u00AD - the catch-all handles this
        html = "<p>Die Gover\u00ADnance ist wichtig.</p>"
        result, count = eliminate_enterprise_terms(html)
        # The catch-all should match through soft-hyphens
        text = re.sub(r'<[^>]+>', '', result)
        assert "overnance" not in text.lower()
        assert count > 0

    def test_audit_trail(self):
        """Audit-Trail is replaced."""
        html = "<p>Der Audit-Trail ist wichtig.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Audit-Trail" not in result
        assert count > 0

    def test_stakeholder(self):
        """Stakeholder is replaced."""
        html = "<p>Die Stakeholder müssen eingebunden werden.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Stakeholder" not in result
        assert "wichtige Personen" in result

    def test_stack_standalone(self):
        """Stack as standalone term is replaced."""
        html = "<p>Der Stack muss modernisiert werden.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert count > 0

    def test_tech_stack(self):
        """Tech-Stack is replaced."""
        html = "<p>Der Tech-Stack besteht aus modernen Tools.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Tech-Stack" not in result
        assert "Werkzeugkasten" in result

    def test_layer(self):
        """Layer is replaced."""
        html = "<p>Der Application Layer kommuniziert mit dem Data Layer.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Layer" not in result
        assert "Ebene" in result

    def test_architektur(self):
        """Architektur is replaced."""
        html = "<p>Die Architektur des Systems muss überarbeitet werden.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Architektur" not in result
        assert "Aufbau" in result

    def test_rollout(self):
        """Rollout is replaced."""
        html = "<p>Der Rollout erfolgt im März.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Rollout" not in result
        assert "Einführung" in result

    def test_prozesslandschaft(self):
        """Prozesslandschaft is replaced."""
        html = "<p>Die Prozesslandschaft muss vereinfacht werden.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Prozesslandschaft" not in result
        assert "Arbeitsabläufe" in result

    def test_no_replacement_in_html_tags(self):
        """Replacements should NOT happen inside HTML tag attributes."""
        html = '<div class="governance-section"><p>Text hier</p></div>'
        result, count = eliminate_enterprise_terms(html)
        # Class attribute should be preserved (tag content is not modified)
        assert 'class="governance-section"' in result
        # No replacements should have been made (only text in attributes, no text nodes)
        assert count == 0

    def test_multiple_terms_in_one_text(self):
        """Multiple enterprise terms in one block are all replaced."""
        html = "<p>Die Governance und der Stakeholder steuern den Rollout.</p>"
        result, count = eliminate_enterprise_terms(html)
        assert "Governance" not in result
        assert "Stakeholder" not in result
        assert "Rollout" not in result
        assert count >= 3


# =============================================================================
# TEST: Duz→Sie Conversion
# =============================================================================

class TestDuzToSieConversion:
    """Test conversion of informal Du-forms to formal Sie-forms."""

    def test_dir_to_ihnen(self):
        """'dir' → 'Ihnen'."""
        html = "<p>Dann skizziere ich dir den Plan.</p>"
        result, count = convert_duz_to_sie(html)
        assert "dir" not in result.lower().split()  # word boundary check
        assert "Ihnen" in result
        assert count > 0

    def test_du_to_sie(self):
        """'du' → 'Sie'."""
        html = "<p>Wenn du das Tool nutzt, sparst du Zeit.</p>"
        result, count = convert_duz_to_sie(html)
        assert count > 0
        # Check that 'du' is replaced
        text = re.sub(r'<[^>]+>', '', result)
        assert not re.search(r'\bdu\b', text, re.IGNORECASE)

    def test_dein_to_ihr(self):
        """'dein/deine/deinen...' → 'Ihr/Ihre/Ihren...'."""
        html = "<p>Das ist dein Vorteil und deine Chance.</p>"
        result, count = convert_duz_to_sie(html)
        assert count >= 2
        text = re.sub(r'<[^>]+>', '', result)
        assert not re.search(r'\bdein\b', text, re.IGNORECASE)
        assert not re.search(r'\bdeine\b', text, re.IGNORECASE)

    def test_dich_to_sie(self):
        """'dich' → 'Sie'."""
        html = "<p>Das betrifft dich direkt.</p>"
        result, count = convert_duz_to_sie(html)
        assert "dich" not in re.sub(r'<[^>]+>', '', result).lower().split()
        assert count > 0

    def test_euch_to_ihnen(self):
        """'euch' → 'Ihnen'."""
        html = "<p>Wir empfehlen euch folgendes Vorgehen.</p>"
        result, count = convert_duz_to_sie(html)
        assert "euch" not in re.sub(r'<[^>]+>', '', result).lower().split()
        assert "Ihnen" in result
        assert count > 0

    def test_euer_to_ihr(self):
        """'euer/eure/euren...' → 'Ihr/Ihre/Ihren...'."""
        html = "<p>In eurer Branche ist das üblich.</p>"
        result, count = convert_duz_to_sie(html)
        text = re.sub(r'<[^>]+>', '', result)
        assert not re.search(r'\beurer\b', text, re.IGNORECASE)
        assert count > 0

    def test_von_dir_geprueft(self):
        """'wird von dir geprüft' → 'wird von Ihnen geprüft' or passive."""
        html = "<p>Dies wird von dir fachlich geprüft.</p>"
        result, count = convert_duz_to_sie(html)
        assert "dir" not in re.sub(r'<[^>]+>', '', result).lower().split()
        assert count > 0

    def test_no_false_positive_in_words(self):
        """Don't replace 'dir' inside words like 'direkt', 'Direktor'."""
        html = "<p>Der direkte Weg zum Direktor ist effektiv.</p>"
        result, count = convert_duz_to_sie(html)
        assert "direkte" in result
        assert "Direktor" in result
        assert count == 0

    def test_mixed_case_preservation(self):
        """Capital 'Du' at sentence start → 'Sie'."""
        html = "<p>Du kannst das Tool sofort nutzen.</p>"
        result, count = convert_duz_to_sie(html)
        assert "Sie" in result
        assert count > 0

    def test_no_replacement_in_tags(self):
        """Don't replace inside HTML tag attributes."""
        html = '<div data-direction="up"><p>Test</p></div>'
        result, count = convert_duz_to_sie(html)
        assert 'data-direction="up"' in result
        assert count == 0


# =============================================================================
# TEST: KPI → Kennzahlen
# =============================================================================

class TestKPIReplacement:
    """Test KPI → Kennzahlen replacement."""

    def test_kpi_forecasts(self):
        """'KPI-Forecasts' → 'Kennzahlen-Prognosen'."""
        html = "<th>KPI-Forecasts</th>"
        result, count = replace_kpi_terms(html)
        assert "KPI-Forecasts" not in result
        assert "Kennzahlen-Prognosen" in result

    def test_kpi_dashboard(self):
        """'KPI-Dashboard' → 'Kennzahlen-Übersicht'."""
        html = "<p>Das KPI-Dashboard zeigt die Fortschritte.</p>"
        result, count = replace_kpi_terms(html)
        assert "KPI-Dashboard" not in result
        assert "Kennzahlen-Übersicht" in result

    def test_kpis_plural(self):
        """'KPIs' → 'Kennzahlen'."""
        html = "<p>Die wichtigsten KPIs sind:</p>"
        result, count = replace_kpi_terms(html)
        assert "KPIs" not in result
        assert "Kennzahlen" in result

    def test_kpi_singular(self):
        """'KPI' → 'Kennzahl'."""
        html = "<p>Jede KPI wird monatlich gemessen.</p>"
        result, count = replace_kpi_terms(html)
        assert count > 0
        text = re.sub(r'<[^>]+>', '', result)
        assert "Kennzahl" in text


# =============================================================================
# TEST: Full Pipeline
# =============================================================================

class TestFullPipeline:
    """Test the complete solo final pass pipeline."""

    def test_all_passes_combined(self):
        """All three passes run and clean the HTML."""
        html = """
        <h2>Governance & KPI-Dashboard</h2>
        <p>Die Governance-Struktur hilft dir, den Überblick zu behalten.</p>
        <p>Der Tech-Stack und die KPIs werden regelmäßig geprüft.</p>
        <p>Deine KPI-Forecasts zeigen positive Trends.</p>
        """
        result, stats = apply_solo_final_pass(html)
        text = re.sub(r'<[^>]+>', ' ', result)

        # Enterprise terms gone
        assert "Governance" not in text
        assert "Tech-Stack" not in text
        assert "KPIs" not in text
        assert "KPI-Forecasts" not in text

        # Duz-forms gone
        assert not re.search(r'\bdir\b', text, re.IGNORECASE)
        assert not re.search(r'\bdeine\b', text, re.IGNORECASE)

        # Stats recorded
        assert stats["enterprise"] > 0
        assert stats["duz_sie"] > 0
        assert stats["kpi"] > 0
        assert stats["total"] == stats["enterprise"] + stats["duz_sie"] + stats["kpi"]

    def test_empty_html(self):
        """Empty HTML returns empty with zero stats."""
        result, stats = apply_solo_final_pass("")
        assert result == ""
        assert stats["total"] == 0

    def test_clean_html_no_changes(self):
        """Already clean HTML returns unchanged."""
        html = "<p>Ihre Spielregeln sind klar definiert.</p>"
        result, stats = apply_solo_final_pass(html)
        assert result == html
        assert stats["total"] == 0

    def test_sections_pass(self):
        """Section-level pass processes all string sections."""
        sections = {
            "EXEC_SUMMARY_HTML": "<p>Die Governance ist stark.</p>",
            "RISKS_HTML": "<p>Du musst das Risiko beachten.</p>",
            "SCORES": {"value": 42},  # Non-string, should be skipped
            "_internal": "should be skipped",
        }
        result, stats = apply_solo_final_pass_to_sections(sections)
        assert "Governance" not in result["EXEC_SUMMARY_HTML"]
        assert "Du" not in re.sub(r'<[^>]+>', '', result["RISKS_HTML"]).split()
        assert result["SCORES"] == {"value": 42}  # Unchanged
        assert stats["total"] > 0


# =============================================================================
# TEST: Verification Function
# =============================================================================

class TestVerification:
    """Test the verification/token scan function."""

    def test_clean_report_passes(self):
        """Clean report passes verification."""
        html = "<p>Ihre Spielregeln und Kennzahlen sind gut.</p>"
        result = verify_solo_report_clean(html)
        assert result["passed"] is True
        assert result["total_violations"] == 0

    def test_enterprise_violations_detected(self):
        """Enterprise terms are detected as violations."""
        html = "<p>Die Governance und der Stakeholder steuern den Rollout.</p>"
        result = verify_solo_report_clean(html)
        assert result["passed"] is False
        assert len(result["enterprise_violations"]) >= 3

    def test_duz_violations_detected(self):
        """Duz-forms are detected as violations."""
        html = "<p>Du musst dir das anschauen, denn dein Tool ist wichtig.</p>"
        result = verify_solo_report_clean(html)
        assert result["passed"] is False
        assert len(result["duz_violations"]) >= 3

    def test_kpi_violations_optional(self):
        """KPI violations only detected when check_kpi=True."""
        html = "<p>Die KPI zeigt den Fortschritt.</p>"
        result_without = verify_solo_report_clean(html, check_kpi=False)
        result_with = verify_solo_report_clean(html, check_kpi=True)
        assert result_without["passed"] is True
        assert len(result_with["kpi_violations"]) > 0

    def test_forbidden_tokens_list_complete(self):
        """All required forbidden tokens are in the list."""
        required = [
            "Governance", "Audit-Trail", "Stakeholder", "Stack",
            "Layer", "Architektur", "Rollout", "Prozesslandschaft",
        ]
        for token in required:
            assert token in FORBIDDEN_SOLO_TOKENS, f"Missing forbidden token: {token}"


# =============================================================================
# TEST: Platzhalter Validator Exception
# =============================================================================

class TestPlatzhalterValidatorException:
    """Test that 'Platzhalter' in technical context doesn't trigger warnings."""

    def test_platzhalter_in_technical_context(self):
        """'Platzhalter' near template/variable terms should be allowed."""
        from services.report_validator import ReportValidator

        # Create validator with section containing technical use of "Platzhalter"
        sections = {
            "TEMPLATES_START_HTML": (
                '<p>Diese Vorlagen enthalten Variablenfelder mit Platzhaltern '
                '(z. B. {{KUNDENNAME}}, {{DATUM}}) für Ihre individuellen Angaben.</p>'
            ),
        }
        meta = {"unternehmensgroesse": "1"}
        validator = ReportValidator(sections, meta)
        validator._check_template_phrases()

        # Should NOT have a warning for standalone "Platzhalter" in technical context
        # Note: "Platzhalter" might still match other TEMPLATE_PHRASES entries like
        # "Platzhalter für" - we only check that standalone "Platzhalter" is allowed
        platzhalter_standalone_warnings = [
            e for e in validator.errors
            if e.category == "TEMPLATE_PHRASE"
            and e.message == "Template-Phrase noch enthalten: 'Platzhalter'"
            and "TEMPLATES_START_HTML" in e.section
        ]
        assert len(platzhalter_standalone_warnings) == 0, (
            f"Standalone 'Platzhalter' in technical context should not trigger warning, "
            f"but got: {platzhalter_standalone_warnings}"
        )

    def test_platzhalter_without_context_still_triggers(self):
        """'Platzhalter' without technical context should still trigger."""
        from services.report_validator import ReportValidator

        sections = {
            "EXEC_SUMMARY_HTML": (
                '<p>Hier ist ein Platzhalter für echten Inhalt.</p>'
            ),
        }
        meta = {"unternehmensgroesse": "1"}
        validator = ReportValidator(sections, meta)
        validator._check_template_phrases()

        # Should still trigger because it's "Platzhalter für echten Inhalt"
        # (which matches a specific TEMPLATE_PHRASES entry)
        platzhalter_warnings = [
            e for e in validator.errors
            if e.category == "TEMPLATE_PHRASE" and "Platzhalter" in e.message
        ]
        # At minimum "Platzhalter für echten Inhalt" should still match
        assert len(platzhalter_warnings) >= 1


# =============================================================================
# TEST: Solo Leak Scanner Updates
# =============================================================================

class TestSoloLeakScannerUpdates:
    """Test that solo_leak_scanner detects the full set of enterprise terms."""

    def test_governance_detected_as_critical(self):
        """Standalone Governance is a critical leak."""
        from services.solo_leak_scanner import scan_solo_leaks, LeakSeverity
        result = scan_solo_leaks("<p>Die Governance ist wichtig.</p>", "test")
        critical = [l for l in result.leaks if l.severity == LeakSeverity.CRITICAL]
        governance_leaks = [l for l in critical if "governance" in l.term.lower()]
        assert len(governance_leaks) > 0, "Governance should be a critical leak"

    def test_architektur_detected(self):
        """Architektur is now a critical leak."""
        from services.solo_leak_scanner import scan_solo_leaks, LeakSeverity
        result = scan_solo_leaks("<p>Die Architektur des Systems.</p>", "test")
        critical = [l for l in result.leaks if l.severity == LeakSeverity.CRITICAL]
        arch_leaks = [l for l in critical if "architektur" in l.term.lower()]
        assert len(arch_leaks) > 0, "Architektur should be a critical leak"

    def test_layer_detected(self):
        """Layer is now a critical leak."""
        from services.solo_leak_scanner import scan_solo_leaks, LeakSeverity
        result = scan_solo_leaks("<p>Der Application Layer.</p>", "test")
        critical = [l for l in result.leaks if l.severity == LeakSeverity.CRITICAL]
        layer_leaks = [l for l in critical if "layer" in l.term.lower()]
        assert len(layer_leaks) > 0, "Layer should be a critical leak"


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and robustness."""

    def test_exception_safety(self):
        """Pipeline never raises, always returns HTML."""
        # None input
        result, stats = apply_solo_final_pass(None)  # type: ignore
        assert result is None
        assert stats["total"] == 0

    def test_no_false_positives_in_common_words(self):
        """Common German words containing 'du' are not affected."""
        html = "<p>Die Industrie produziert Produkte. Das Studium ist individuell.</p>"
        result, count = convert_duz_to_sie(html)
        assert "Industrie" in result
        assert "produziert" in result
        assert "Produkte" in result
        assert "Studium" in result
        assert "individuell" in result
        assert count == 0

    def test_html_structure_preserved(self):
        """HTML structure (tags, attributes) is preserved."""
        html = '''<div class="governance-box" id="main">
            <h2 style="color: red;">Governance & Stakeholder</h2>
            <p>Du musst den Audit-Trail prüfen.</p>
        </div>'''
        result, stats = apply_solo_final_pass(html)
        # Tag attributes should be preserved
        assert 'class="governance-box"' in result
        assert 'id="main"' in result
        assert '</div>' in result
        assert 'style="color: red;"' in result
        # Content in text nodes should be cleaned
        text = re.sub(r'<[^>]+>', ' ', result)
        assert "Governance" not in text
        assert "Stakeholder" not in text
        assert not re.search(r'\bDu\b', text)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
