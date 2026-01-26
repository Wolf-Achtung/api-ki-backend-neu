#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-527 Tests: Report Facts - Single Source of Truth

Tests for:
- ReportFacts canonical value container
- Payback audit consistency
- Open inputs marker collection
- Platzhalter text validation
"""

import unittest


class TestReportFacts(unittest.TestCase):
    """Test ReportFacts dataclass and factory methods."""

    def test_from_briefing_basic(self):
        """Test basic ReportFacts creation from briefing."""
        from services.report_facts import ReportFacts

        briefing = {
            "PAYBACK_MONTHS": 11,
            "ROI_12M": 150,
            "unternehmensgroesse": "solo",
            "hauptleistung": "KI-Beratung",
        }

        facts = ReportFacts.from_briefing(briefing)

        self.assertEqual(facts.payback_months, 11.0)
        self.assertEqual(facts.roi_12m, 150.0)
        self.assertEqual(facts.company_size, "solo")
        self.assertEqual(facts.hauptleistung, "KI-Beratung")

    def test_payback_months_de_integer(self):
        """Test German formatting for integer payback."""
        from services.report_facts import ReportFacts

        facts = ReportFacts(
            payback_months=11.0,
            roi_12m=100.0,
            capex_eur=5000.0,
            opex_monthly_eur=200.0,
            savings_monthly_eur=1000.0,
            company_size="solo",
            hauptleistung="Test",
        )

        self.assertEqual(facts.payback_months_de, "11")
        self.assertEqual(facts.payback_display_de, "11 Monate")

    def test_payback_months_de_decimal(self):
        """Test German formatting for decimal payback."""
        from services.report_facts import ReportFacts

        facts = ReportFacts(
            payback_months=3.5,
            roi_12m=100.0,
            capex_eur=5000.0,
            opex_monthly_eur=200.0,
            savings_monthly_eur=1000.0,
            company_size="solo",
            hauptleistung="Test",
        )

        self.assertEqual(facts.payback_months_de, "3,5")
        self.assertEqual(facts.payback_display_de, "3,5 Monate")
        self.assertEqual(facts.payback_approx_de, "~3,5 Monate")

    def test_company_size_normalization(self):
        """Test company size is normalized correctly."""
        from services.report_facts import ReportFacts

        # Solo variants
        for size in ["solo", "Solo", "1", "freiberufler", "FREIBERUFLICH"]:
            facts = ReportFacts.from_briefing({"unternehmensgroesse": size})
            self.assertEqual(facts.company_size, "solo", f"Failed for: {size}")

        # Team variants
        for size in ["team", "Team", "kleinunternehmen", "2"]:
            facts = ReportFacts.from_briefing({"unternehmensgroesse": size})
            self.assertEqual(facts.company_size, "team", f"Failed for: {size}")

        # KMU (default)
        for size in ["kmu", "KMU", "mittelstand", "50"]:
            facts = ReportFacts.from_briefing({"unternehmensgroesse": size})
            self.assertEqual(facts.company_size, "kmu", f"Failed for: {size}")

    def test_sections_override_briefing(self):
        """Test that sections values take priority over briefing."""
        from services.report_facts import ReportFacts

        briefing = {"PAYBACK_MONTHS": 5}
        sections = {"PAYBACK_MONTHS": 11}

        facts = ReportFacts.from_briefing(briefing, sections)

        self.assertEqual(facts.payback_months, 11.0)


class TestPaybackAudit(unittest.TestCase):
    """Test payback consistency audit."""

    def test_audit_passes_with_consistent_values(self):
        """Test audit passes when all values match canonical."""
        from services.report_facts import ReportFacts, audit_payback_consistency

        facts = ReportFacts(
            payback_months=11.0,
            roi_12m=100.0,
            capex_eur=5000.0,
            opex_monthly_eur=200.0,
            savings_monthly_eur=1000.0,
            company_size="solo",
            hauptleistung="Test",
        )

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Mit einem Payback von 11 Monaten ist das Projekt wirtschaftlich.</p>",
            "BUSINESS_CASE_HTML": "<p>Die Amortisation: 11 Monate.</p>",
        }

        passed, violations = audit_payback_consistency(sections, facts)

        self.assertTrue(passed)
        self.assertEqual(len(violations), 0)

    def test_audit_fails_with_inconsistent_values(self):
        """Test audit fails when values differ significantly."""
        from services.report_facts import ReportFacts, audit_payback_consistency

        facts = ReportFacts(
            payback_months=11.0,
            roi_12m=100.0,
            capex_eur=5000.0,
            opex_monthly_eur=200.0,
            savings_monthly_eur=1000.0,
            company_size="solo",
            hauptleistung="Test",
        )

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Mit einem Payback von 3,5 Monaten ist das Projekt wirtschaftlich.</p>",
        }

        passed, violations = audit_payback_consistency(sections, facts)

        self.assertFalse(passed)
        self.assertEqual(len(violations), 1)
        self.assertIn("3,5", violations[0])

    def test_audit_tolerates_minor_differences(self):
        """Test audit allows values within 20% tolerance."""
        from services.report_facts import ReportFacts, audit_payback_consistency

        facts = ReportFacts(
            payback_months=10.0,
            roi_12m=100.0,
            capex_eur=5000.0,
            opex_monthly_eur=200.0,
            savings_monthly_eur=1000.0,
            company_size="solo",
            hauptleistung="Test",
        )

        sections = {
            # 11 is within 20% of 10
            "EXECUTIVE_SUMMARY_HTML": "<p>Payback 11 Monate.</p>",
        }

        passed, violations = audit_payback_consistency(sections, facts)

        self.assertTrue(passed)


class TestOpenInputsCollection(unittest.TestCase):
    """Test open inputs marker collection."""

    def test_collect_unicode_markers(self):
        """Test collection of Unicode markers ⟦INPUT:...⟧."""
        from services.report_facts import collect_open_inputs

        sections = {
            "EXECUTIVE_SUMMARY_HTML": (
                "<p>Die ⟦INPUT:umsatz_ziel|Umsatzziel 2025|Bitte aus Finanzplanung⟧ "
                "werden analysiert.</p>"
            ),
        }

        inputs, html = collect_open_inputs(sections)

        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0].key, "umsatz_ziel")
        self.assertEqual(inputs[0].label, "Umsatzziel 2025")
        self.assertEqual(inputs[0].hint, "Bitte aus Finanzplanung")
        self.assertIn("Offene Inputs", html)

    def test_collect_ascii_markers(self):
        """Test collection of ASCII markers [[INPUT:...]]."""
        from services.report_facts import collect_open_inputs

        sections = {
            "ROADMAP_HTML": (
                "<p>Phase 1: [[INPUT:timeline|Zeitrahmen|Aus Projektplan]] festlegen.</p>"
            ),
        }

        inputs, html = collect_open_inputs(sections)

        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0].key, "timeline")
        self.assertEqual(inputs[0].label, "Zeitrahmen")

    def test_empty_when_no_markers(self):
        """Test returns empty when no markers found."""
        from services.report_facts import collect_open_inputs

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Normaler Text ohne Marker.</p>",
        }

        inputs, html = collect_open_inputs(sections)

        self.assertEqual(len(inputs), 0)
        self.assertEqual(html, "")


class TestPlatzhalterValidation(unittest.TestCase):
    """Test Platzhalter text validation."""

    def test_passes_when_no_platzhalter(self):
        """Test validation passes when no Platzhalter text found."""
        from services.report_facts import validate_no_platzhalter_text

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Normaler Text ohne verbotene Wörter.</p>",
            "RECOMMENDATIONS_HTML": "<p>Empfehlungen hier.</p>",
        }

        passed, violations = validate_no_platzhalter_text(sections)

        self.assertTrue(passed)
        self.assertEqual(len(violations), 0)

    def test_fails_when_platzhalter_found(self):
        """Test validation fails when Platzhalter text found."""
        from services.report_facts import validate_no_platzhalter_text

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Dieser Platzhalter muss ersetzt werden.</p>",
        }

        passed, violations = validate_no_platzhalter_text(sections)

        self.assertFalse(passed)
        self.assertEqual(len(violations), 1)

    def test_allows_platzhalter_in_open_inputs(self):
        """Test Platzhalter is allowed in OPEN_INPUTS section."""
        from services.report_facts import validate_no_platzhalter_text

        sections = {
            "OPEN_INPUTS_HTML": "<h2>Offene Platzhalter</h2>",  # Allowed here
            "EXECUTIVE_SUMMARY_HTML": "<p>Normaler Text.</p>",
        }

        passed, violations = validate_no_platzhalter_text(sections)

        self.assertTrue(passed)


class TestIntegration(unittest.TestCase):
    """Integration tests for report_facts module."""

    def test_full_workflow(self):
        """Test full workflow: create facts, audit, collect inputs."""
        from services.report_facts import (
            ReportFacts,
            audit_payback_consistency,
            collect_open_inputs,
            validate_no_platzhalter_text,
        )

        briefing = {
            "PAYBACK_MONTHS": 11,
            "unternehmensgroesse": "solo",
            "hauptleistung": "KI-Beratung",
        }

        sections = {
            "PAYBACK_MONTHS": 11,
            "EXECUTIVE_SUMMARY_HTML": (
                "<p>Mit einem Payback von 11 Monaten rechnet sich die Investition. "
                "Die ⟦INPUT:roi_details|ROI-Details|Aus Controlling⟧ werden nachgereicht.</p>"
            ),
        }

        # Create facts
        facts = ReportFacts.from_briefing(briefing, sections)
        self.assertEqual(facts.payback_months, 11.0)
        self.assertEqual(facts.company_size, "solo")

        # Audit payback
        payback_ok, payback_violations = audit_payback_consistency(sections, facts)
        self.assertTrue(payback_ok)

        # Collect inputs
        inputs, open_html = collect_open_inputs(sections)
        self.assertEqual(len(inputs), 1)

        # Validate no Platzhalter
        platzhalter_ok, _ = validate_no_platzhalter_text(sections)
        self.assertTrue(platzhalter_ok)


if __name__ == "__main__":
    unittest.main()
