"""
Tests for FIX-SF1: Strategy Fact Sanitizer
Validates plausibility checks for LLM-generated strategy sections.
"""

import pytest
from services.strategy_sanitizer import (
    _check_percent_plausibility,
    _check_year_data_freshness,
    sanitize_strategy_sections,
)


# ── Pass 1: Percent plausibility ─────────────────────────────────────


class TestPercentPlausibility:
    """Prozentwerte >100% in Adoptions-Kontexten müssen gepatcht werden."""

    def test_patches_104_percent_in_adoption_context(self):
        """Der konkrete Bug: '104%' Eurostat-Adoptionsrate."""
        html = (
            '<tr><td>EU-Unternehmen: KI-Nutzung (2025)</td>'
            '<td>104%</td>'
            '<td>Eurostat Referenzwert</td></tr>'
        )
        patched, warnings = _check_percent_plausibility(html, "S2")
        assert "104%" not in patched
        assert "\u2013*" in patched  # – replacement marker
        assert len(warnings) == 1
        assert "104.0%" in warnings[0]

    def test_patches_150_percent_nutzung(self):
        html = '<p>Die Nutzung von KI liegt bei 150% der Unternehmen.</p>'
        patched, warnings = _check_percent_plausibility(html, "S2")
        assert "150%" not in patched
        assert len(warnings) == 1

    def test_patches_200_percent_adoption(self):
        html = '<p>Adoption rate reached 200% in 2025.</p>'
        patched, warnings = _check_percent_plausibility(html, "S2")
        assert "200%" not in patched
        assert len(warnings) == 1

    def test_keeps_valid_19_percent(self):
        """Korrekte Werte <100% dürfen NICHT angefasst werden."""
        html = '<td>KI-Nutzung: 19,95%</td>'
        patched, warnings = _check_percent_plausibility(html, "S2")
        assert "19,95%" in patched
        assert len(warnings) == 0

    def test_keeps_valid_85_percent(self):
        html = '<p>85% der Unternehmen nutzen bereits KI-Tools.</p>'
        patched, warnings = _check_percent_plausibility(html, "S2")
        assert "85%" in patched
        assert len(warnings) == 0

    def test_keeps_100_percent_exactly(self):
        """Genau 100% ist valide (z.B. 'vollständige Implementierung')."""
        html = '<p>Die Implementierung ist zu 100% abgeschlossen.</p>'
        patched, warnings = _check_percent_plausibility(html, "S3")
        assert "100%" in patched
        assert len(warnings) == 0

    def test_ignores_high_percent_without_adoption_context(self):
        """Hohe Prozentwerte OHNE Adoptions-Kontext: kein Patch.
        z.B. 'Steigerung um 250%' ist valide (Wachstumsrate)."""
        html = '<p>Umsatzsteigerung um 250% im Vergleich zum Vorjahr.</p>'
        patched, warnings = _check_percent_plausibility(html, "S5")
        assert "250%" in patched
        assert len(warnings) == 0

    def test_patches_comma_decimal_percent(self):
        """Komma-Dezimalwerte wie '104,5%' auch erkennen."""
        html = '<td>Einsatz von KI: 104,5%</td>'
        patched, warnings = _check_percent_plausibility(html, "S2")
        assert "104,5%" not in patched
        assert len(warnings) == 1

    def test_patches_percent_with_space(self):
        """'104 %' (mit Leerzeichen) auch erkennen."""
        html = '<td>Verbreitung: 104 % der Firmen</td>'
        patched, warnings = _check_percent_plausibility(html, "S2")
        assert len(warnings) == 1

    def test_multiple_values_only_patches_implausible(self):
        """Wenn mehrere Prozentwerte: nur die >100% im Adoptionskontext patchen."""
        html = (
            '<p>Die Nutzung stieg von 45% auf 104% laut Studie. '
            'Der Umsatz beträgt 12%.</p>'
        )
        patched, warnings = _check_percent_plausibility(html, "S2")
        assert "45%" in patched
        assert "12%" in patched
        assert "104%" not in patched
        assert len(warnings) == 1


# ── Pass 1b: ROI context whitelist (FIX-SF1v2) ──────────────────────


class TestROIContextWhitelist:
    """ROI percentages >100% must NOT be patched."""

    def test_roi_values_not_patched(self):
        """ROI percentages >100% must NOT be patched."""
        html = '<td>239% ROI</td><td>Break-Even Monat 4</td>'
        result, warnings = _check_percent_plausibility(html, "S5")
        assert "239%" in result
        assert "\u2013*" not in result
        assert len(warnings) == 0

    def test_roi_scenario_table_preserved(self):
        """Full ROI scenario table must survive sanitizer."""
        html = (
            '<tr><td>Konservativ</td><td>104% ROI</td><td>Break-Even Monat 6</td></tr>'
            '<tr><td>Realistisch</td><td>239% ROI</td><td>Break-Even Monat 4</td></tr>'
            '<tr><td>Optimistisch</td><td>375% ROI</td><td>Break-Even Monat 3</td></tr>'
        )
        result, warnings = _check_percent_plausibility(html, "S5")
        assert "104%" in result
        assert "239%" in result
        assert "375%" in result
        assert len(warnings) == 0

    def test_roi_in_prose_not_patched(self):
        """ROI mentioned in prose text must not be patched."""
        html = 'Im realistischen Szenario erreichen Sie einen ROI von 239% und den Break-Even in Monat 4.'
        result, warnings = _check_percent_plausibility(html, "S5")
        assert "239%" in result
        assert len(warnings) == 0

    def test_adoption_rate_still_patched(self):
        """Adoption rates >100% must still be patched (regression check)."""
        html = 'Laut Eurostat nutzen 104% der Unternehmen KI-Tools.'
        result, warnings = _check_percent_plausibility(html, "S2")
        assert "\u2013*" in result
        assert "104%" not in result
        assert len(warnings) == 1

    def test_investment_return_not_patched(self):
        """Investitionsrendite context must not be patched."""
        html = 'Die Investition ergibt eine Rendite von 375% über 12 Monate.'
        result, warnings = _check_percent_plausibility(html, "S5")
        assert "375%" in result
        assert len(warnings) == 0


# ── Pass 3: Year data freshness ──────────────────────────────────────


class TestYearDataFreshness:
    """Warnt bei Zukunfts-Jahreszahlen mit Datenwerten."""

    def test_warns_future_year_2028(self):
        html = '<p>Laut Studie 2028 nutzen 45% der Unternehmen KI.</p>'
        warnings = _check_year_data_freshness(html, "S2", report_year=2026)
        assert len(warnings) == 1
        assert "2028" in warnings[0]

    def test_ok_current_year_2026(self):
        html = '<p>Laut Eurostat 2026 nutzen 19,95% der EU-Firmen KI.</p>'
        warnings = _check_year_data_freshness(html, "S2", report_year=2026)
        assert len(warnings) == 0

    def test_ok_past_year_2024(self):
        html = '<p>In 2024 lag die Adoptionsrate bei 15%.</p>'
        warnings = _check_year_data_freshness(html, "S2", report_year=2026)
        assert len(warnings) == 0

    def test_no_warning_for_year_without_percent(self):
        """Jahreszahlen ohne Prozent-Daten → kein Warning."""
        html = '<p>Gegründet im Jahr 2030.</p>'
        warnings = _check_year_data_freshness(html, "S1", report_year=2026)
        assert len(warnings) == 0


# ── Hauptfunktion: sanitize_strategy_sections ─────────────────────────


class TestSanitizeStrategySections:
    """Integration-Tests für die Hauptfunktion."""

    def test_returns_report_key(self):
        sections = {"S1": "x" * 50, "S2": "y" * 200}
        result = sanitize_strategy_sections(sections)
        assert "_strategy_sanitizer_report" in result
        report = result["_strategy_sanitizer_report"]
        assert "warnings" in report
        assert "patches_applied" in report
        assert "sections_scanned" in report

    def test_scans_only_long_sections(self):
        """Sektionen mit <100 Zeichen werden übersprungen."""
        sections = {"S1": "short", "S2": "x" * 200}
        result = sanitize_strategy_sections(sections)
        assert result["_strategy_sanitizer_report"]["sections_scanned"] == 1

    def test_skips_non_string_values(self):
        sections = {"S1": 42, "S2": None, "S3": ["list"], "_meta": {"key": "val"}}
        result = sanitize_strategy_sections(sections)
        assert result["_strategy_sanitizer_report"]["sections_scanned"] == 0

    def test_full_pipeline_patches_hallucinated_value(self):
        """End-to-end: halluzinierter Wert wird gepatcht."""
        sections = {
            "S1": "<p>Unternehmensprofil mit Details</p>" + "x" * 100,
            "S2": (
                '<table><tr><td>EU-Unternehmen: KI-Nutzung (2025)</td>'
                '<td>104%</td><td>Eurostat</td></tr>'
                '<tr><td>Deutsche Unternehmen</td>'
                '<td>25%</td><td>Bitkom</td></tr></table>'
            ),
            "S3": "<p>Handlungsfelder-Analyse</p>" + "y" * 100,
        }
        result = sanitize_strategy_sections(sections)
        assert "104%" not in result["S2"]
        assert "25%" in result["S2"]
        assert result["_strategy_sanitizer_report"]["patches_applied"] == 1

    def test_clean_sections_no_patches(self):
        """Saubere Sektionen → 0 Patches."""
        sections = {
            "S2": (
                '<table><tr><td>KI-Nutzung</td><td>19,95%</td></tr>'
                '<tr><td>Automatisierung</td><td>35%</td></tr></table>'
            ),
        }
        result = sanitize_strategy_sections(sections)
        assert result["_strategy_sanitizer_report"]["patches_applied"] == 0
        assert len(result["_strategy_sanitizer_report"]["warnings"]) == 0
