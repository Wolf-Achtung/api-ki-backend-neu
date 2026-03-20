"""
Tests for KIS-1013 Blocker B1 (grammar enforcement) and B3 (scenario card ROI rendering).

B3: All 3 scenario cards must render ROI (12M) row — verified via HTML output.
B1: Grammar rules must catch "Ich haben" → "Ich habe" / "Wir haben",
    including inside truncation-repair patterns.
"""
import re
import pytest


class TestB3ScenarioCardROI:
    """B3: Ensure all 3 scenario cards contain the ROI (12M) metric row."""

    def _make_scenarios(self):
        from services.business_case_engine_v2 import ScenarioKPIs
        return [
            ScenarioKPIs(
                name="optimistic", roi_12m=200.0, payback_months=2.5,
                monthly_savings=5148, annual_savings=61776, investment_total=9600,
            ),
            ScenarioKPIs(
                name="realistic", roi_12m=200.0, payback_months=3.9,
                monthly_savings=3960, annual_savings=47520, investment_total=12000,
            ),
            ScenarioKPIs(
                name="conservative", roi_12m=64.0, payback_months=6.2,
                monthly_savings=2772, annual_savings=33264, investment_total=14400,
            ),
        ]

    def test_all_three_scenario_cards_have_roi(self) -> None:
        """Each scenario card (Optimistisch, Realistisch, Konservativ) must show ROI (12M)."""
        from services.business_case_engine_v2 import (
            BusinessCaseReport, business_case_report_to_html,
        )

        report = BusinessCaseReport(
            scenarios=self._make_scenarios(),
            kpi_targets_6m={"roi_progress": 50, "hours_saved": 100},
            kpi_targets_12m={"roi_progress": 100, "hours_saved": 200},
            narrative_summary="Test summary",
        )

        html = business_case_report_to_html(report)

        # Count ROI (12M) labels — must be exactly 3 (one per card)
        roi_labels = re.findall(r"ROI \(12M\)", html)
        assert len(roi_labels) == 3, (
            f"Expected 3 ROI (12M) labels (one per scenario card), got {len(roi_labels)}"
        )

    def test_realistic_card_has_roi_when_capped(self) -> None:
        """When realistic ROI equals the cap (200%), it must still render."""
        from services.business_case_engine_v2 import (
            BusinessCaseReport, business_case_report_to_html,
        )

        report = BusinessCaseReport(
            scenarios=self._make_scenarios(),
            kpi_targets_6m={}, kpi_targets_12m={},
            narrative_summary="Test",
        )

        html = business_case_report_to_html(report)

        # Extract the Realistisch card specifically
        cards = re.findall(r'<div class="scenario-card".*?</div>\s*</div>', html, re.DOTALL)
        assert len(cards) == 3, f"Expected 3 scenario cards, got {len(cards)}"

        # Find the Realistisch card
        realistic_card = None
        for card in cards:
            if "Realistisch" in card:
                realistic_card = card
                break

        assert realistic_card is not None, "Realistisch card not found"
        assert "ROI (12M)" in realistic_card, "ROI (12M) missing from Realistisch card"
        assert "200%" in realistic_card, "200% ROI value missing from Realistisch card"

    def test_strip_redundant_blocks_preserves_roi(self) -> None:
        """KIS-1013-B3 ROOT CAUSE: strip_redundant_blocks must NOT remove identical ROI divs.

        When Optimistisch and Realistisch both have ROI 200% (capped), the ROI
        divs are pixel-identical. strip_redundant_blocks treated them as duplicates
        and removed the second occurrence, causing missing ROI on Realistisch card.
        """
        from services.business_case_engine_v2 import (
            BusinessCaseReport, business_case_report_to_html,
        )
        from services.pipeline_sanitizers import sanitize_all_sections

        report = BusinessCaseReport(
            scenarios=self._make_scenarios(),
            kpi_targets_6m={}, kpi_targets_12m={},
            narrative_summary="Test",
        )

        html = business_case_report_to_html(report)
        assert len(re.findall(r"ROI \(12M\)", html)) == 3

        # Run through sanitize_all_sections (which calls strip_redundant_blocks)
        sections = {"BUSINESS_CASE_ENGINE_HTML": html}
        result_sections, _ = sanitize_all_sections(sections)
        result_html = result_sections["BUSINESS_CASE_ENGINE_HTML"]

        roi_labels = re.findall(r"ROI \(12M\)", result_html)
        assert len(roi_labels) == 3, (
            f"sanitize_all_sections destroyed ROI divs: expected 3, got {len(roi_labels)}"
        )


class TestB1GrammarEnforcement:
    """B1: Grammar rules must catch 'Ich haben' and related errors."""

    def test_ich_haben_to_ich_habe(self) -> None:
        """'Ich haben' must be corrected to 'Ich habe'."""
        from services.content_quality_enforcer import apply_grammar_fixes

        html = '<p>"Ich haben das gemacht."</p>'
        result, count = apply_grammar_fixes(html)
        assert "Ich habe" in result
        assert "Ich haben" not in result
        assert count > 0

    def test_ich_haben_lowercase(self) -> None:
        """'ich haben' (lowercase) must also be corrected."""
        from services.content_quality_enforcer import apply_grammar_fixes

        html = "<p>Das habe ich haben wollen, aber eigentlich sollte ich habe sagen.</p>"
        result, _ = apply_grammar_fixes(html)
        assert "ich habe" in result

    def test_koennen_ich_to_kann_ich(self) -> None:
        """'können ich' must be corrected to 'kann ich' (NEU-3)."""
        from services.content_quality_enforcer import apply_grammar_fixes

        html = "<p>Was können ich besser machen?</p>"
        result, count = apply_grammar_fixes(html)
        assert "kann ich" in result
        assert "können ich" not in result
        assert count > 0

    def test_ich_haben_in_truncation_repair_context(self) -> None:
        """Grammar fix must work inside truncation-repair Text.</ Text. patterns."""
        from services.content_quality_enforcer import apply_grammar_fixes

        # Simulates the truncation-repair pattern from the issue report
        html = (
            '<div style="font-size:14px;color:#334155;font-style:italic">'
            '"Ich haben keinen Mitarbeiter eingestellt, sondern KI.</ '
            '"Ich haben keinen Mitarbeiter eingestellt, sondern KI. Beste Entscheidung." >'
            '</div>'
        )
        result, count = apply_grammar_fixes(html)
        assert "Ich haben" not in result, (
            f"Grammar fix did not catch 'Ich haben' in truncation-repair context: {result}"
        )

    def test_known_truncation_fixes_ich_haben(self) -> None:
        """KNOWN_TRUNCATION_FIXES must replace 'Ich haben keinen Mitarbeiter'."""
        from services.content_quality_enforcer import cleanup_truncation_artifacts

        html = '<p>"Ich haben keinen Mitarbeiter eingestellt"</p>'
        result = cleanup_truncation_artifacts(html)
        assert "Wir haben keinen Mitarbeiter" in result

    def test_known_truncation_fixes_koennen_ich(self) -> None:
        """KNOWN_TRUNCATION_FIXES must replace 'können ich besser machen'."""
        from services.content_quality_enforcer import cleanup_truncation_artifacts

        html = '<p>Was können ich besser machen?</p>'
        result = cleanup_truncation_artifacts(html)
        assert "kann ich besser machen" in result

    def test_grammar_fixer_processes_sofort_start(self) -> None:
        """Grammar fixer must process SOFORT_START_HTML section (>100 chars)."""
        from services.content_quality_enforcer import apply_grammar_fixer

        # Must be >100 chars for apply_grammar_fixer to process it
        long_content = (
            '<div style="padding:20px;margin:16px;background:#f8fafc;border-radius:12px;">'
            '<p style="font-size:14px;color:#334155;font-style:italic;">'
            '"Ich haben keinen Mitarbeiter eingestellt, sondern KI. Beste Entscheidung."'
            '</p></div>'
        )
        assert len(long_content) > 100, f"Test content must be >100 chars, got {len(long_content)}"

        sections = {
            "SOFORT_START_HTML": long_content,
            "OTHER_HTML": "short",
        }

        result = apply_grammar_fixer(sections)
        assert "Ich haben" not in result["SOFORT_START_HTML"], (
            f"Grammar fixer did not fix 'Ich haben' in SOFORT_START_HTML: {result['SOFORT_START_HTML']}"
        )

    def test_final_grammar_pass_in_pipeline(self) -> None:
        """apply_all_quality_enforcers must catch grammar errors at the end of pipeline."""
        from services.content_quality_enforcer import apply_all_quality_enforcers

        sections = {
            "SOFORT_START_HTML": (
                '<div style="padding:20px;margin:16px;background:#f8fafc;border-radius:12px;">'
                '<p style="font-size:14px;color:#334155;font-style:italic;">'
                '"Ich haben keinen Mitarbeiter eingestellt, sondern KI. '
                'Beste Entscheidung."</p>'
                '</div>'
            ),
        }

        result = apply_all_quality_enforcers(sections)
        assert "Ich haben" not in result.get("SOFORT_START_HTML", ""), (
            "Final grammar pass did not catch 'Ich haben' in SOFORT_START_HTML"
        )
