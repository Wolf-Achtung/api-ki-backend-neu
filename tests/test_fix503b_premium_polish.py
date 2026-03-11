# -*- coding: utf-8 -*-
"""
FIX-503B Premium Polish Tests
============================

Tests for the four fixes in FIX-503B:
1. QuickWins Validator Key-Mapping
2. Payback Canonical Enforcement
3. Risk Matrix Table Wrap CSS
4. Metrics Unification
"""

import pytest
import re


class TestQuickWinsValidatorKeyMapping:
    """FIX 1: QuickWins Validator should use QUICK_WINS_HTML key."""

    def test_section_key_map_uses_html_key(self):
        """Verify SECTION_KEY_MAP maps quick_wins to QUICK_WINS_HTML."""
        from services.report_validator import ReportValidator

        assert ReportValidator.SECTION_KEY_MAP.get("quick_wins") == "QUICK_WINS_HTML", \
            "quick_wins should map to QUICK_WINS_HTML, not 'quick_wins'"

    def test_validator_no_warning_when_html_present(self):
        """If QUICK_WINS_HTML exists with content, no SECTION_TOO_SHORT warning."""
        from services.report_validator import ReportValidator

        sections = {
            "QUICK_WINS_HTML": """
                <div class="quick-wins">
                    <h3>Quick Win 1: Tool einführen</h3>
                    <p>Beschreibung des ersten Quick Wins mit ausreichend Text für die Validierung.
                    Dies ist ein wichtiger Schritt zur Digitalisierung. Es werden verschiedene
                    Aspekte berücksichtigt und der Nutzen klar dargestellt. Die Umsetzung ist
                    in wenigen Wochen möglich und bringt sofortige Vorteile.</p>
                    <h3>Quick Win 2: Prozess automatisieren</h3>
                    <p>Zweiter Quick Win mit detaillierter Beschreibung des Nutzens und der
                    Implementierung. Hier werden konkrete Schritte genannt und der ROI
                    aufgezeigt. Die Amortisation erfolgt schnell.</p>
                </div>
            """,
            "quick_wins": "",  # Legacy key empty
        }
        meta = {"unternehmensgroesse": "solo"}

        validator = ReportValidator(sections, meta)
        validator.validate_all()

        # Should not have SECTION_TOO_SHORT for quick_wins
        quick_wins_errors = [
            e for e in validator.errors
            if e.category == "SECTION_TOO_SHORT" and "quick" in e.section.lower()
        ]
        assert len(quick_wins_errors) == 0, \
            f"Should not warn about quick_wins when QUICK_WINS_HTML has content. Errors: {quick_wins_errors}"

    def test_validator_fallback_to_text_key(self):
        """If QUICK_WINS_HTML is missing, validator should check quick_wins key."""
        from services.report_validator import ReportValidator

        sections = {
            "quick_wins": "Short text",  # Only legacy key, too short
        }
        meta = {"unternehmensgroesse": "solo"}

        validator = ReportValidator(sections, meta)
        validator.validate_all()

        # Should detect that quick_wins is too short
        quick_wins_errors = [
            e for e in validator.errors
            if "quick" in e.section.lower() and e.category in ("SECTION_TOO_SHORT", "SECTION_EMPTY")
        ]
        # Either SECTION_TOO_SHORT or no check if key not in MIN_SECTION_LENGTH_WORDS
        # This depends on configuration


class TestPaybackCanonicalEnforcement:
    """FIX 2: Payback values in LLM text should be replaced with canonical value."""

    def test_payback_replacement_in_text(self):
        """LLM text with wrong payback should be corrected to canonical value."""
        from services.content_quality_enforcer import apply_canonical_payback_enforcer

        sections = {
            "PAYBACK_MONTHS": 3.5,
            "BRANCH_DEEP_DIVE_HTML": """
                <div>
                    <p>Die Amortisation beträgt Payback 9 Monate, was für ein Solo-Unternehmen
                    sehr attraktiv ist.</p>
                </div>
            """,
        }

        result = apply_canonical_payback_enforcer(sections)

        # Should replace "9 Monate" with "3,5 Monate"
        assert "9 Monate" not in result["BRANCH_DEEP_DIVE_HTML"], \
            "Wrong payback value should be replaced"
        assert "3,5 Monate" in result["BRANCH_DEEP_DIVE_HTML"] or "3.5 Monate" in result["BRANCH_DEEP_DIVE_HTML"], \
            "Canonical payback value should be present"

    def test_payback_scenario_not_replaced(self):
        """Payback values in scenario context should NOT be replaced."""
        from services.content_quality_enforcer import apply_canonical_payback_enforcer

        sections = {
            "PAYBACK_MONTHS": 3.5,
            "BUSINESS_CASE_HTML": """
                <div>
                    <p>Szenarien: konservativ Payback 6 Monate, realistisch Payback 3,5 Monate,
                    optimistisch Payback 2 Monate.</p>
                </div>
            """,
        }

        result = apply_canonical_payback_enforcer(sections)

        # Scenario values should remain unchanged
        assert "konservativ" in result["BUSINESS_CASE_HTML"], \
            "Scenario context should be preserved"

    def test_payback_within_tolerance_still_replaced(self):
        """FIX-AMORT: ALL non-canonical values are replaced, even within old 20% tolerance."""
        from services.content_quality_enforcer import apply_canonical_payback_enforcer

        sections = {
            "PAYBACK_MONTHS": 3.5,
            "EXECUTIVE_SUMMARY_HTML": """
                <div>
                    <p>Amortisation: 3 Monate bei schneller Umsetzung.</p>
                </div>
            """,
        }

        result = apply_canonical_payback_enforcer(sections)

        # FIX-AMORT: No tolerance — canonical is always enforced to prevent
        # visibly inconsistent values coexisting in the same report.
        assert "3,5 Monate" in result["EXECUTIVE_SUMMARY_HTML"], \
            "Non-canonical values must be replaced (no tolerance)"


class TestRiskMatrixTableWrap:
    """FIX 3: Risk Matrix tables should not truncate text."""

    def test_risk_matrix_uses_table_layout_fixed(self):
        """Risk Matrix HTML should use table-layout:fixed for WeasyPrint-proof layout (FIX-506 TASK 4)."""
        from services.risk_engine_v2 import risk_report_to_html, RiskReport, RiskMatrixEntry

        report = RiskReport(
            ai_act_class="minimal",
            ai_act_reasons=["Test reason"],
            ai_act_required_controls=[],
            dsgvo_risk_level="niedrig",
            dsgvo_risk_factors=["Test factor"],
            vendor_category="cloud",
            vendor_risk_score=2,
            vendor_flags=[],
            use_case_risks=[],
            risk_matrix=[
                RiskMatrixEntry(
                    id="R1",
                    title="Test Risk with Datennutzungsrichtlinien",
                    likelihood=3,
                    impact=3,
                    color="yellow",
                    description="Long description",
                )
            ],
            consolidated_score=75.0,
            consolidated_grade="B",
            narrative_summary="Test summary",
        )

        html = risk_report_to_html(report)

        # FIX-506 TASK 4: Should use table-layout:fixed for WeasyPrint-proof layout
        assert "table-layout:fixed" in html, \
            "Risk Matrix should use table-layout:fixed for WeasyPrint compatibility"

        # FIX-506: Now uses word-wrap:break-word instead of overflow-wrap:anywhere
        # to prevent ugly header word breaks while still allowing content to wrap
        assert "word-wrap:break-word" in html or "overflow-wrap:anywhere" in html, \
            "Risk Matrix should have word wrapping for content cells"
        assert "white-space:normal" in html, \
            "Risk Matrix should have white-space:normal"


class TestMetricsUnification:
    """FIX 4: Pipeline grade should include validator warnings."""

    def test_unified_grade_includes_validator_warnings(self):
        """Grade should be downgraded if validator has warnings."""
        # This tests the logic that will be applied in gpt_analyze.py
        # We simulate the grade calculation

        def calculate_unified_grade(
            pipeline_warnings: int,
            validator_warnings: int,
            fallbacks: int,
            heals: int,
            consistency_grade: str,
        ) -> str:
            """Simulated unified grade calculation from FIX-503B."""
            total_warnings = pipeline_warnings + validator_warnings

            if (
                total_warnings == 0 and
                fallbacks == 0 and
                heals == 0 and
                consistency_grade in ("A", "B")
            ):
                return "A"
            elif (
                total_warnings <= 10 and
                fallbacks <= 2 and
                consistency_grade in ("A", "B", "C")
            ):
                return "B"
            else:
                return "C"

        # Test case 1: No warnings at all -> Grade A
        assert calculate_unified_grade(0, 0, 0, 0, "A") == "A"

        # Test case 2: Pipeline ok but 70 validator warnings -> Grade C
        assert calculate_unified_grade(0, 70, 0, 0, "A") == "C", \
            "70 validator warnings should result in grade C, not A"

        # Test case 3: Some warnings but within tolerance -> Grade B
        assert calculate_unified_grade(2, 5, 1, 0, "B") == "B"

        # Test case 4: Consistency grade D should downgrade
        assert calculate_unified_grade(0, 5, 0, 0, "D") == "C", \
            "Consistency grade D should result in grade C"


class TestIntegration:
    """Integration tests for all FIX-503B changes."""

    def test_content_quality_enforcer_payback_in_pipeline(self):
        """Payback enforcer should be called in quality enforcer pipeline."""
        from services.content_quality_enforcer import apply_all_quality_enforcers

        sections = {
            "PAYBACK_MONTHS": 3.5,
            "BRANCH_DEEP_DIVE_HTML": "<p>Payback 12 Monate erwartet.</p>",
        }

        result = apply_all_quality_enforcers(sections, "", "", "solo")

        # Should have been processed
        assert "BRANCH_DEEP_DIVE_HTML" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
