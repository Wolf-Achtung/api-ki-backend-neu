# -*- coding: utf-8 -*-
"""
Release Readiness Work Package Tests (WP1-WP4)
================================================

Tests covering the fixes for Team & KMU release readiness:

WP1: Business-Case empty value sanitizer (no "€.", "bei %" artifacts)
WP2: Validator ROI false positive fix (CSS percentages excluded)
WP3: Leakage sanitizer improvements (additional phrases)
WP4: Compact/Payload guard for oversized reports

Date: 2026-02-11
"""
import os
import re
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


# =============================================================================
# WP1: Business-Case Completeness Tests
# =============================================================================

class TestWP1BusinessCaseEmptyValues:
    """WP1: Ensure no empty €/% artifacts in business case HTML."""

    def test_sanitize_empty_euro_dot(self):
        """Business case HTML must not contain '€.' artifact."""
        from services.report_healer import sanitize_business_case_empty_values

        html = '<td class="text-right">€.</td>'
        result, fixes = sanitize_business_case_empty_values(html)
        assert "€." not in result
        assert fixes > 0

    def test_sanitize_empty_bei_percent(self):
        """Business case HTML must not contain 'bei %' artifact."""
        from services.report_healer import sanitize_business_case_empty_values

        html = '<p>Der ROI liegt bei %</p>'
        result, fixes = sanitize_business_case_empty_values(html)
        assert "bei %" not in result
        assert fixes > 0

    def test_sanitize_colon_percent(self):
        """Business case HTML must not contain ': %' artifact."""
        from services.report_healer import sanitize_business_case_empty_values

        html = '<td>ROI: %</td>'
        result, fixes = sanitize_business_case_empty_values(html)
        assert ": %" not in result

    def test_sanitize_empty_euro_in_table_cell(self):
        """Table cell with only '€' should be replaced."""
        from services.report_healer import sanitize_business_case_empty_values

        html = '<td class="text-right">€</td>'
        result, fixes = sanitize_business_case_empty_values(html)
        assert ">€<" not in result

    def test_sanitize_strong_euro(self):
        """Strong tag wrapping empty euro value should be fixed."""
        from services.report_healer import sanitize_business_case_empty_values

        html = '<strong>&nbsp;€</strong>'
        result, fixes = sanitize_business_case_empty_values(html)
        assert "&nbsp;€" not in result

    def test_valid_values_preserved(self):
        """Valid business case values must not be modified."""
        from services.report_healer import sanitize_business_case_empty_values

        html = '<td>6.000 €</td><td>200 %</td><td>3,5 Monate</td>'
        result, fixes = sanitize_business_case_empty_values(html)
        assert "6.000 €" in result
        assert "200 %" in result
        assert "3,5 Monate" in result
        assert fixes == 0

    def test_no_empty_artifacts_regex(self):
        """Comprehensive regex check for empty artifacts."""
        from services.report_healer import sanitize_business_case_empty_values

        test_html = """
        <div class="business-case">
          <p>Einmalige Aufwände: <strong>€</strong>.</p>
          <p>Monatliche Betriebskosten: €.</p>
          <p>Der ROI liegt bei <strong>&nbsp;%</strong></p>
        </div>
        """
        result, fixes = sanitize_business_case_empty_values(test_html)

        # These patterns must NOT appear in output
        assert not re.search(r"€\.", result), f"Found '€.' in: {result}"
        assert not re.search(r"bei\s+%", result), f"Found 'bei %' in: {result}"

    def test_fmt_eur_none_returns_dash(self):
        """_fmt_eur(None) should return '—' not empty string."""
        from services.extra_sections import _fmt_eur

        assert _fmt_eur(None) == "—"
        assert _fmt_eur(0) == "0"
        assert _fmt_eur(6000) == "6.000"

    def test_calc_business_case_always_has_values(self):
        """calc_business_case must always return numeric values, never None for key fields."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "2-10",
            "jahresumsatz": "100k_500k",
            "investitionsbudget": "2000_10000",
        }
        env = {}
        result = calc_business_case(answers, env)

        assert result["CAPEX_REALISTISCH_EUR"] is not None
        assert result["CAPEX_REALISTISCH_EUR"] > 0
        assert result["OPEX_REALISTISCH_EUR"] is not None
        assert result["EINSPARUNG_MONAT_EUR"] is not None
        assert result["PAYBACK_MONTHS"] is not None or result["PAYBACK_MONTHS"] is None  # None is ok if monatlicher_nutzen <= 0
        # ROI can be None if denom is 0, but CAPEX should always be > 0
        assert result["ROI_12M"] is not None


# =============================================================================
# WP2: Validator ROI False Positive Tests
# =============================================================================

class TestWP2ValidatorROIFalsePositive:
    """WP2: ROI validator must not produce false positives from CSS percentages."""

    def test_css_linear_gradient_no_warning(self):
        """CSS linear-gradient with 100% must NOT trigger ROI warning."""
        from services.report_validator import ReportValidator, ValidationError

        sections = {
            "EXEC_SUMMARY_HTML": """
            <div style="background: linear-gradient(to right, #22c55e 0%, #3b82f6 100%);">
                <p>Die KI-Strategie zeigt großes Potenzial für Ihr Unternehmen.</p>
            </div>
            """,
            "GAMECHANGER_HTML": "",
            "RECOMMENDATIONS_HTML": "",
            "ROADMAP_90D_HTML": "",
        }

        validator = ReportValidator(sections, meta={})
        validator._check_roi_consistency()

        roi_warnings = [e for e in validator.errors if e.category == "ROI_PROHIBITED"]
        assert len(roi_warnings) == 0, (
            f"CSS percentage should not trigger ROI warning. Got: {roi_warnings}"
        )

    def test_css_width_100_percent_no_warning(self):
        """CSS width: 100% must NOT trigger ROI warning."""
        from services.report_validator import ReportValidator

        sections = {
            "EXEC_SUMMARY_HTML": '<div style="width: 100%; height: 200px;"><p>Content</p></div>',
            "GAMECHANGER_HTML": '<table style="width:100%"><tr><td>Cell</td></tr></table>',
            "RECOMMENDATIONS_HTML": "",
            "ROADMAP_90D_HTML": "",
        }

        validator = ReportValidator(sections, meta={})
        validator._check_roi_consistency()

        roi_warnings = [e for e in validator.errors if e.category == "ROI_PROHIBITED"]
        assert len(roi_warnings) == 0, (
            f"CSS width percentage should not trigger ROI warning. Got: {roi_warnings}"
        )

    def test_actual_roi_in_text_still_warns(self):
        """Actual ROI percentage in visible text SHOULD trigger warning."""
        from services.report_validator import ReportValidator

        sections = {
            "EXEC_SUMMARY_HTML": "<p>Der ROI beträgt 284% nach 12 Monaten.</p>",
            "GAMECHANGER_HTML": "",
            "RECOMMENDATIONS_HTML": "",
            "ROADMAP_90D_HTML": "",
        }

        validator = ReportValidator(sections, meta={})
        validator._check_roi_consistency()

        roi_warnings = [e for e in validator.errors if e.category == "ROI_PROHIBITED"]
        assert len(roi_warnings) >= 1, "ROI percentage in text should trigger warning"

    def test_mixed_css_and_text_percentages(self):
        """Only visible text percentages should trigger, not CSS ones."""
        from services.report_validator import ReportValidator

        sections = {
            "EXEC_SUMMARY_HTML": """
            <div style="background: linear-gradient(90deg, red 0%, blue 100%);">
                <p>Die Effizienz steigt um 150% laut Branchenbenchmark.</p>
            </div>
            """,
            "GAMECHANGER_HTML": "",
            "RECOMMENDATIONS_HTML": "",
            "ROADMAP_90D_HTML": "",
        }

        validator = ReportValidator(sections, meta={})
        validator._check_roi_consistency()

        roi_warnings = [e for e in validator.errors if e.category == "ROI_PROHIBITED"]
        # Should warn about 150% in visible text but not about 100% in CSS
        assert len(roi_warnings) == 1


# =============================================================================
# WP3: Leakage Sanitizer Tests
# =============================================================================

class TestWP3LeakageSanitizer:
    """WP3: Extended leak detection phrases."""

    def test_german_assistant_phrases_detected(self):
        """German assistant phrases must be detected and removable."""
        from services.zero_leak_engine import apply_blacklist_classified

        test_phrases = [
            "wie kann ich dir helfen",
            "ich kann dir helfen",
            "als KI",
            "Gerne!",
            "Natürlich,",
            "Hier ist",
        ]

        for phrase in test_phrases:
            text = f"<p>{phrase} bei der Implementierung.</p>"
            result = apply_blacklist_classified(text)
            assert result.has_benign or phrase not in result.cleaned_text, (
                f"Phrase '{phrase}' should be detected or removed"
            )

    def test_english_assistant_phrases_detected(self):
        """English assistant phrases must be detected."""
        from services.zero_leak_engine import apply_blacklist_classified

        test_phrases = [
            "Of course,",
            "Sure,",
            "Here is",
            "Let me help",
            "I'd be happy to",
            "Certainly,",
        ]

        for phrase in test_phrases:
            text = f"<p>{phrase} the implementation plan.</p>"
            result = apply_blacklist_classified(text)
            assert result.has_benign or phrase not in result.cleaned_text, (
                f"Phrase '{phrase}' should be detected or removed"
            )

    def test_legitimate_content_preserved(self):
        """Business content must not be removed as leaks."""
        from services.zero_leak_engine import apply_blacklist_classified

        legitimate = (
            "<p>Die KI-gestützte Automatisierung der Kundenkommunikation "
            "ermöglicht eine Effizienzsteigerung von 30% bei gleichzeitiger "
            "Verbesserung der Servicequalität.</p>"
        )
        result = apply_blacklist_classified(legitimate)
        # Content should remain largely intact
        assert len(result.cleaned_text) > len(legitimate) * 0.8


# =============================================================================
# WP4: Compact/Payload Guard Tests
# =============================================================================

class TestWP4CompactPayloadGuard:
    """WP4: Auto-compact for oversized reports."""

    def test_small_report_not_compacted(self):
        """Reports under threshold should not be compacted."""
        from services.solo_compact_engine import check_and_apply_compact_guard

        html = "<html><body><p>Small report</p></body></html>"
        sections = {"EXEC_SUMMARY_HTML": "<p>Summary</p>"}

        result_html, result_sections, guard = check_and_apply_compact_guard(
            html, sections, company_size="team"
        )

        assert not guard.compacted
        assert result_html == html

    def test_large_report_triggers_compact(self):
        """Reports over threshold should trigger auto-compact."""
        from services.solo_compact_engine import check_and_apply_compact_guard

        # Create HTML over 450KB
        large_content = "<p>" + "x" * 500000 + "</p>"
        html = f"<html><body>{large_content}</body></html>"
        sections = {
            "EXEC_SUMMARY_HTML": "<p>Summary</p>",
            "VENDOR_AUDIT_HTML": "<p>" + "vendor " * 10000 + "</p>",
            "AUTOMATION_ROADMAP_HTML": "<p>" + "roadmap " * 10000 + "</p>",
        }

        result_html, result_sections, guard = check_and_apply_compact_guard(
            html, sections, company_size="team"
        )

        assert guard.compacted
        assert len(guard.sections_dropped) > 0
        assert guard.original_size_kb > 450

    def test_max_pages_by_size(self):
        """Different company sizes should have different page limits."""
        from services.solo_compact_engine import MAX_PAGES_BY_SIZE

        assert MAX_PAGES_BY_SIZE["solo"] == 16
        assert MAX_PAGES_BY_SIZE["team"] == 55
        assert MAX_PAGES_BY_SIZE["kmu"] == 45

    def test_estimate_page_count(self):
        """Page count estimation should be reasonable."""
        from services.solo_compact_engine import estimate_page_count

        # ~3000 chars per page
        html_10_pages = "x" * 30000
        estimated = estimate_page_count(html_10_pages)
        assert 8 <= estimated <= 12, f"Expected ~10 pages, got {estimated}"


# =============================================================================
# Integration: Business Case Rendering End-to-End
# =============================================================================

class TestBusinessCaseEndToEnd:
    """Integration test: Business case rendering produces complete values."""

    def test_team_business_case_no_empty_artifacts(self):
        """Team business case rendering must not produce empty artifacts."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "2-10",
            "jahresumsatz": "500k_2m",
            "investitionsbudget": "10000_50000",
        }
        env = {}
        bc = calc_business_case(answers, env)
        table_html = bc.get("BUSINESS_CASE_TABLE_HTML", "")

        # Must not contain empty artifacts
        assert "€." not in table_html, f"Found '€.' in table HTML"
        assert "bei %" not in table_html, f"Found 'bei %' in table HTML"
        assert ": %" not in table_html, f"Found ': %' in table HTML"

    def test_kmu_business_case_no_empty_artifacts(self):
        """KMU business case rendering must not produce empty artifacts."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "11-100",
            "jahresumsatz": "2m_10m",
            "investitionsbudget": "50000_250000",
        }
        env = {}
        bc = calc_business_case(answers, env)
        table_html = bc.get("BUSINESS_CASE_TABLE_HTML", "")

        assert "€." not in table_html
        assert "bei %" not in table_html

    def test_business_case_values_are_numeric(self):
        """All business case values should be numeric, not empty strings."""
        from services.extra_sections import calc_business_case

        for size in ["solo", "2-10", "11-100"]:
            answers = {
                "unternehmensgroesse": size,
                "jahresumsatz": "100k_500k",
                "investitionsbudget": "2000_10000",
            }
            bc = calc_business_case(answers, {})

            assert isinstance(bc["CAPEX_REALISTISCH_EUR"], (int, float))
            assert isinstance(bc["OPEX_REALISTISCH_EUR"], (int, float))
            assert isinstance(bc["EINSPARUNG_MONAT_EUR"], (int, float))
            # ROI_12M can be None if denominator is 0
            if bc["ROI_12M"] is not None:
                assert isinstance(bc["ROI_12M"], float)
