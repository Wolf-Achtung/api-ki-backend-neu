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
    apply_size_final_pass,
    apply_size_final_pass_to_sections,
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


# =============================================================================
# WP0: Regression-Schutz Solo – Full Report Scan
# =============================================================================

# Realistic sample Solo report HTML (simulates a post-render Solo report)
_SAMPLE_SOLO_REPORT_HTML = """
<!DOCTYPE html>
<html lang="de">
<head><title>KI-Status-Report – Solo</title></head>
<body>
<div class="report-container" data-size="solo" data-variant="solo_compact">

<section class="executive-summary">
  <h2>Zusammenfassung</h2>
  <p>Ihr Unternehmen kann durch den Einsatz von KI-Werkzeugen erhebliche
  Zeitersparnis erzielen. Die wichtigsten Kennzahlen zeigen ein positives Bild
  für Ihre nächsten Schritte.</p>
  <p>Wir empfehlen Ihnen, mit drei konkreten Maßnahmen zu starten, die sich
  innerhalb von 3 Monaten amortisieren.</p>
</section>

<section class="quick-wins">
  <h2>Schnelle Erfolge</h2>
  <div class="quick-win-card">
    <h3>E-Mail-Automatisierung mit KI</h3>
    <p><strong>PROBLEM:</strong> Sie verbringen täglich 2 Stunden mit
    wiederkehrenden E-Mails.</p>
    <p><strong>WIRKUNG:</strong> Zeitersparnis von ca. 8 Stunden pro Monat.</p>
    <p><strong>UMSETZUNG:</strong> Nutzen Sie ein einfaches Automatisierungstool
    wie Make oder Zapier, um Standardantworten vorzubereiten.</p>
  </div>
</section>

<section class="roadmap-90d">
  <h2>Ihr 90-Tage-Fahrplan</h2>
  <p>In den ersten 30 Tagen richten Sie Ihre Grundausstattung ein.
  Danach erweitern Sie schrittweise Ihre Arbeitsabläufe.</p>
  <table class="roadmap-table">
    <tr><th>Zeitraum</th><th>Maßnahme</th><th>Erwartetes Ergebnis</th></tr>
    <tr><td>Monat 1</td><td>Einrichtung Werkzeugkasten</td><td>Basis steht</td></tr>
    <tr><td>Monat 2</td><td>Arbeitsabläufe optimieren</td><td>Erste Ersparnisse</td></tr>
    <tr><td>Monat 3</td><td>Evaluation &amp; Ausbau</td><td>Stabilisierung</td></tr>
  </table>
</section>

<section class="tools">
  <h2>Empfohlene Werkzeuge</h2>
  <p>Für Sie als Einzelperson sind diese Tools besonders geeignet:</p>
  <ul>
    <li>ChatGPT Plus – für Texterstellung und Recherche</li>
    <li>Make.com – für Arbeitsabläufe und Automatisierung</li>
    <li>Notion – für Ihr Wissensmanagement</li>
  </ul>
</section>

<section class="risks">
  <h2>Risiken und Hinweise</h2>
  <p>Beachten Sie folgende Punkte bei der Einführung:</p>
  <ul>
    <li>Datenschutz: Nutzen Sie nur DSGVO-konforme Anbieter.</li>
    <li>Abhängigkeit: Vermeiden Sie Einzelabhängigkeiten.</li>
    <li>Qualitätskontrolle: Prüfen Sie KI-generierte Inhalte stets manuell.</li>
  </ul>
</section>

</div>
</body>
</html>
"""


class TestSoloRegressionScan:
    """WP0: Regression tests ensuring Solo reports are free of forbidden tokens."""

    def test_sample_solo_report_passes_scan(self):
        """A clean Solo report HTML must pass verify_solo_report_clean."""
        result = verify_solo_report_clean(_SAMPLE_SOLO_REPORT_HTML)
        assert result["passed"] is True, (
            f"Sample solo report should be clean but found violations: "
            f"enterprise={result['enterprise_violations']}, "
            f"duz={result['duz_violations']}"
        )
        assert result["total_violations"] == 0

    def test_sample_report_no_enterprise_terms(self):
        """Sample Solo report must not contain any FORBIDDEN_SOLO_TOKENS."""
        text = re.sub(r'<[^>]+>', ' ', _SAMPLE_SOLO_REPORT_HTML)
        text = re.sub(r'\s+', ' ', text)
        for token in FORBIDDEN_SOLO_TOKENS:
            assert not re.search(
                re.escape(token), text, re.IGNORECASE
            ), f"Forbidden token '{token}' found in sample report"

    def test_sample_report_no_duz_forms(self):
        """Sample Solo report must not contain any Duz-forms."""
        text = re.sub(r'<[^>]+>', ' ', _SAMPLE_SOLO_REPORT_HTML)
        duz_pattern = re.compile(
            r"\b(du|dir|dein|deine|deinem|deinen|deiner|deines|dich"
            r"|euch|euer|eure|eurem|euren|eurer|eures)\b",
            re.IGNORECASE,
        )
        matches = duz_pattern.findall(text)
        assert len(matches) == 0, f"Duz-forms found in sample report: {matches}"

    def test_dirty_report_gets_cleaned_by_pipeline(self):
        """A report with violations gets cleaned by apply_solo_final_pass."""
        dirty_html = """
        <div class="report">
          <h2>Governance-Übersicht</h2>
          <p>Die Governance-Struktur und der Stakeholder steuern den Rollout
          des Tech-Stacks. Du musst dir dein KPI-Dashboard einrichten.</p>
          <p>Die Architektur des Layers wird durch den Audit-Trail gesichert.</p>
          <p>Die Prozesslandschaft zeigt euer Baukasten-Prinzip.</p>
        </div>
        """
        # Verify it's dirty first
        pre_check = verify_solo_report_clean(dirty_html, check_kpi=True)
        assert pre_check["passed"] is False, "Pre-check should find violations"
        assert pre_check["total_violations"] >= 5

        # Clean it
        cleaned, stats = apply_solo_final_pass(dirty_html)
        assert stats["total"] > 0, "Pipeline should have made replacements"

        # Verify it's clean after pipeline
        post_check = verify_solo_report_clean(cleaned, check_kpi=True)
        assert post_check["passed"] is True, (
            f"Post-pipeline should be clean but found: "
            f"enterprise={post_check['enterprise_violations']}, "
            f"duz={post_check['duz_violations']}, "
            f"kpi={post_check['kpi_violations']}"
        )

    def test_forbidden_tokens_cover_validator_size_forbidden(self):
        """FORBIDDEN_SOLO_TOKENS must cover key terms from validator SIZE_FORBIDDEN."""
        # These are the critical enterprise terms that the validator also bans
        critical_terms_from_validator = [
            "Governance",  # Governance-Struktur partial
            "Stakeholder",
            "Stack",
            "Layer",
            "Architektur",
            "Rollout",
            "Audit-Trail",
            "Prozesslandschaft",
        ]
        for term in critical_terms_from_validator:
            found = any(
                term.lower() in ft.lower() for ft in FORBIDDEN_SOLO_TOKENS
            )
            assert found, (
                f"Critical validator term '{term}' not covered by FORBIDDEN_SOLO_TOKENS"
            )

    def test_full_pipeline_idempotent(self):
        """Running the pipeline twice produces the same result."""
        html = "<p>Die Governance und dein Stakeholder steuern den Rollout.</p>"
        first_pass, stats1 = apply_solo_final_pass(html)
        second_pass, stats2 = apply_solo_final_pass(first_pass)
        assert first_pass == second_pass, "Pipeline should be idempotent"
        assert stats2["total"] == 0, "Second pass should find nothing to replace"

    def test_verify_scan_context_output(self):
        """Verification function provides useful context for violations."""
        html = "<p>Die Governance ist wichtig für den Stakeholder.</p>"
        result = verify_solo_report_clean(html)
        assert not result["passed"]
        for violation in result["enterprise_violations"]:
            assert "token" in violation
            assert "context" in violation
            assert "..." in violation["context"]  # Has context markers

    def test_solo_final_pass_preserves_sie_ansprache(self):
        """Pipeline preserves correct Sie-Ansprache that's already present."""
        html = "<p>Für Sie als Selbstständige ist Ihr Zeitbudget entscheidend.</p>"
        result, stats = apply_solo_final_pass(html)
        text = re.sub(r'<[^>]+>', '', result)
        assert "Sie" in text
        assert "Ihr" in text


# =============================================================================
# WP1: Company Size Normalization Tests
# =============================================================================

class TestCompanySizeNormalization:
    """WP1: Test that company size normalization is consistent."""

    def test_solo_values_normalize_correctly(self):
        """All solo-indicating values map to solo bucket."""
        from services.company_size_normalizer import normalize_company_size
        for val in ["1", "solo", "Einzelunternehmer", "Selbstständig", "Freiberufler"]:
            result = normalize_company_size(val)
            assert result["bucket"] == "solo", f"'{val}' should map to solo, got {result['bucket']}"

    def test_team_values_normalize_correctly(self):
        """All team-indicating values map to small_team bucket."""
        from services.company_size_normalizer import normalize_company_size
        for val in ["2-10", "2\u201310", "team", "kleines team"]:
            result = normalize_company_size(val)
            assert result["bucket"] == "small_team", f"'{val}' should map to small_team, got {result['bucket']}"

    def test_kmu_values_normalize_correctly(self):
        """All KMU-indicating values map to kmu bucket."""
        from services.company_size_normalizer import normalize_company_size
        for val in ["11-100", "11\u2013100", "kmu", "mittelstand"]:
            result = normalize_company_size(val)
            assert result["bucket"] == "kmu", f"'{val}' should map to kmu, got {result['bucket']}"

    def test_normalizer_returns_segment_field(self):
        """Normalizer result includes segment field mapping to healer-compatible values."""
        from services.company_size_normalizer import normalize_company_size
        # Solo
        assert normalize_company_size("1")["segment"] == "solo"
        # Team
        assert normalize_company_size("2-10")["segment"] == "team"
        # KMU
        assert normalize_company_size("11-100")["segment"] == "kmu"

    def test_empty_value_defaults_to_solo(self):
        """Empty or missing value defaults to solo."""
        from services.company_size_normalizer import normalize_company_size
        result = normalize_company_size("")
        assert result["bucket"] == "solo"


# =============================================================================
# WP2: Size Profiles Configuration Tests
# =============================================================================

class TestSizeProfiles:
    """WP2: Test centralized size profile configuration."""

    def test_all_three_profiles_exist(self):
        """solo, team, kmu profiles must all be defined."""
        from config.size_profiles import SIZE_PROFILES
        assert "solo" in SIZE_PROFILES
        assert "team" in SIZE_PROFILES
        assert "kmu" in SIZE_PROFILES

    def test_profile_has_required_keys(self):
        """Each profile must have tonality, forbidden_terms, section_budgets, min_words."""
        from config.size_profiles import SIZE_PROFILES
        required_keys = ["tonality", "forbidden_enterprise_terms", "section_budgets", "min_words", "max_pages"]
        for size, profile in SIZE_PROFILES.items():
            for key in required_keys:
                assert key in profile, f"Profile '{size}' missing key '{key}'"

    def test_solo_has_strict_forbidden_terms(self):
        """Solo profile must have the most forbidden enterprise terms."""
        from config.size_profiles import SIZE_PROFILES
        solo_terms = SIZE_PROFILES["solo"]["forbidden_enterprise_terms"]
        team_terms = SIZE_PROFILES["team"]["forbidden_enterprise_terms"]
        assert len(solo_terms) > len(team_terms), (
            f"Solo should have more forbidden terms ({len(solo_terms)}) than Team ({len(team_terms)})"
        )

    def test_solo_tonality_is_sie(self):
        """Solo tonality must enforce Sie-Ansprache."""
        from config.size_profiles import SIZE_PROFILES
        assert SIZE_PROFILES["solo"]["tonality"]["ansprache"] == "Sie"

    def test_kmu_allows_enterprise_terms(self):
        """KMU profile allows terms that Solo bans."""
        from config.size_profiles import SIZE_PROFILES
        kmu_terms = SIZE_PROFILES["kmu"]["forbidden_enterprise_terms"]
        # KMU should allow Governance, Stakeholder, Architektur etc
        assert "Governance" not in kmu_terms, "KMU should allow Governance"
        assert "Stakeholder" not in kmu_terms, "KMU should allow Stakeholder"

    def test_get_profile_function(self):
        """get_size_profile() returns correct profile for any raw size value."""
        from config.size_profiles import get_size_profile
        assert get_size_profile("1")["tonality"]["ansprache"] == "Sie"
        assert get_size_profile("2-10")["max_pages"] > 0
        assert get_size_profile("11-100")["max_pages"] > 0

    def test_section_budgets_increase_with_size(self):
        """Section budgets should generally increase from solo → team → kmu."""
        from config.size_profiles import SIZE_PROFILES
        solo_default = SIZE_PROFILES["solo"]["section_budgets"].get("_default", 0)
        team_default = SIZE_PROFILES["team"]["section_budgets"].get("_default", 0)
        kmu_default = SIZE_PROFILES["kmu"]["section_budgets"].get("_default", 0)
        assert solo_default <= team_default <= kmu_default


# =============================================================================
# WP4: Team-Report Final Pass Tests
# =============================================================================

class TestTeamFinalPass:
    """WP4: Test that Team reports get appropriate final pass processing."""

    def test_team_duz_converted_to_sie(self):
        """Team reports also get Duz→Sie conversion."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Wenn du das Tool nutzt, sparst du Zeit für dein Team.</p>"
        result, stats = apply_size_final_pass(html, segment="team")
        text = re.sub(r'<[^>]+>', '', result)
        assert not re.search(r'\bdu\b', text, re.IGNORECASE)
        assert not re.search(r'\bdein\b', text, re.IGNORECASE)
        assert stats["duz_sie"] > 0

    def test_team_allows_governance(self):
        """Team reports allow Governance (it's not in team's forbidden list)."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die Governance ist für Teams wichtig.</p>"
        result, stats = apply_size_final_pass(html, segment="team")
        text = re.sub(r'<[^>]+>', '', result)
        # Governance should remain for team reports
        assert "Governance" in text

    def test_team_allows_stakeholder(self):
        """Team reports allow Stakeholder."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die Stakeholder müssen eingebunden werden.</p>"
        result, stats = apply_size_final_pass(html, segment="team")
        assert "Stakeholder" in result

    def test_team_replaces_matrixorganisation(self):
        """Team reports replace Matrixorganisation (too complex for small teams)."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Eine Matrixorganisation ist nicht empfehlenswert.</p>"
        result, stats = apply_size_final_pass(html, segment="team")
        assert "Matrixorganisation" not in result
        assert stats["enterprise"] > 0

    def test_team_no_kpi_replacement(self):
        """Team reports keep KPI as-is (no KPI→Kennzahl conversion)."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die KPIs zeigen positive Trends im KPI-Dashboard.</p>"
        result, stats = apply_size_final_pass(html, segment="team")
        assert "KPI" in result
        assert stats["kpi"] == 0

    def test_team_allows_architektur(self):
        """Team reports allow Architektur."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die IT-Architektur sollte überprüft werden.</p>"
        result, stats = apply_size_final_pass(html, segment="team")
        assert "Architektur" in result

    def test_team_sample_report_clean(self):
        """A representative Team report passes through with appropriate changes."""
        from services.solo_final_pass import apply_size_final_pass
        html = """
        <section>
          <h2>Zusammenfassung für Ihr Team</h2>
          <p>Die Governance und der Stakeholder-Prozess helfen Ihrem Team,
          die Architektur und den Tech-Stack zu optimieren.</p>
          <p>Folgende KPIs sind relevant für Ihre Roadmap.</p>
        </section>
        """
        result, stats = apply_size_final_pass(html, segment="team")
        text = re.sub(r'<[^>]+>', ' ', result)
        # Governance, Stakeholder, Architektur, KPIs should remain
        assert "Governance" in text
        assert "Stakeholder" in text
        assert "Architektur" in text
        assert "KPIs" in text


# =============================================================================
# WP5: KMU-Report Final Pass Tests
# =============================================================================

class TestKMUFinalPass:
    """WP5: Test that KMU reports get appropriate final pass processing."""

    def test_kmu_duz_converted_to_sie(self):
        """KMU reports also get Duz→Sie conversion."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Wenn du die Software einführst, profitiert dein Unternehmen.</p>"
        result, stats = apply_size_final_pass(html, segment="kmu")
        text = re.sub(r'<[^>]+>', '', result)
        assert not re.search(r'\bdu\b', text, re.IGNORECASE)
        assert not re.search(r'\bdein\b', text, re.IGNORECASE)
        assert stats["duz_sie"] > 0

    def test_kmu_allows_governance(self):
        """KMU reports fully allow Governance."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die Governance-Struktur ist ein wichtiger Bestandteil.</p>"
        result, stats = apply_size_final_pass(html, segment="kmu")
        assert "Governance" in result

    def test_kmu_allows_stakeholder(self):
        """KMU reports allow Stakeholder."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die Stakeholder des Projekts müssen informiert werden.</p>"
        result, stats = apply_size_final_pass(html, segment="kmu")
        assert "Stakeholder" in result

    def test_kmu_allows_architektur(self):
        """KMU reports allow Architektur."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die Enterprise-Architektur muss geplant werden.</p>"
        result, stats = apply_size_final_pass(html, segment="kmu")
        assert "Architektur" in result

    def test_kmu_allows_kpi(self):
        """KMU reports keep KPI as-is."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Das KPI-Dashboard und die KPIs sind zentral.</p>"
        result, stats = apply_size_final_pass(html, segment="kmu")
        assert "KPI" in result
        assert stats["kpi"] == 0

    def test_kmu_allows_compliance(self):
        """KMU reports allow Compliance and Framework."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Das Compliance-Framework muss beachtet werden.</p>"
        result, stats = apply_size_final_pass(html, segment="kmu")
        assert "Compliance" in result
        assert "Framework" in result

    def test_kmu_replaces_matrixorganisation(self):
        """KMU reports replace Matrixorganisation."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Eine Matrixorganisation ist komplex.</p>"
        result, stats = apply_size_final_pass(html, segment="kmu")
        assert "Matrixorganisation" not in result
        assert stats["enterprise"] > 0

    def test_kmu_sample_report_clean(self):
        """A representative KMU report passes through with Duz→Sie only."""
        from services.solo_final_pass import apply_size_final_pass
        html = """
        <section>
          <h2>Zusammenfassung für Ihr Unternehmen</h2>
          <p>Die Governance und der Stakeholder-Prozess helfen Ihrem Unternehmen,
          die IT-Architektur zu optimieren.</p>
          <p>Ihr Compliance-Framework und die KPI-Dashboards sind zentral.</p>
          <p>Der Roll-out erfolgt planmäßig gemäß der Roadmap.</p>
        </section>
        """
        result, stats = apply_size_final_pass(html, segment="kmu")
        text = re.sub(r'<[^>]+>', ' ', result)
        # All enterprise terms should remain for KMU
        assert "Governance" in text
        assert "Stakeholder" in text
        assert "Architektur" in text
        assert "KPI" in text
        assert "Compliance" in text
        assert "Roll-out" in text or "Rollout" in text


# =============================================================================
# Cross-Size Comparison Tests
# =============================================================================

class TestCrossSizeComparison:
    """Tests comparing behavior across all three sizes."""

    def test_solo_most_restrictive(self):
        """Solo applies the most replacements for the same input."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die Governance und der Stakeholder steuern den Rollout des Tech-Stacks.</p>"
        _, solo_stats = apply_size_final_pass(html, segment="solo")
        _, team_stats = apply_size_final_pass(html, segment="team")
        _, kmu_stats = apply_size_final_pass(html, segment="kmu")
        assert solo_stats["enterprise"] >= team_stats["enterprise"] >= kmu_stats["enterprise"]

    def test_all_sizes_enforce_sie(self):
        """All three sizes convert Duz→Sie."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Wenn du das Tool nutzt, sparst du Zeit.</p>"
        for segment in ("solo", "team", "kmu"):
            result, stats = apply_size_final_pass(html, segment=segment)
            text = re.sub(r'<[^>]+>', '', result)
            assert not re.search(r'\bdu\b', text, re.IGNORECASE), (
                f"Segment '{segment}' should convert du→Sie"
            )
            assert stats["duz_sie"] > 0

    def test_only_solo_replaces_kpi(self):
        """Only Solo replaces KPI→Kennzahlen."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Die KPIs zeigen positive Trends.</p>"
        _, solo_stats = apply_size_final_pass(html, segment="solo")
        _, team_stats = apply_size_final_pass(html, segment="team")
        _, kmu_stats = apply_size_final_pass(html, segment="kmu")
        assert solo_stats["kpi"] > 0
        assert team_stats["kpi"] == 0
        assert kmu_stats["kpi"] == 0

    def test_size_final_pass_unknown_still_converts_duz(self):
        """Unknown segment still converts Duz→Sie at minimum."""
        from services.solo_final_pass import apply_size_final_pass
        html = "<p>Wenn du das Tool nutzt, hilft dir das.</p>"
        result, stats = apply_size_final_pass(html, segment="unknown")
        text = re.sub(r'<[^>]+>', '', result)
        # At minimum, Duz→Sie should be applied
        assert not re.search(r'\bdu\b', text, re.IGNORECASE)
        assert stats["duz_sie"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
