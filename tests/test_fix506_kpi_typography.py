# -*- coding: utf-8 -*-
"""
FIX-506 TASK 2: Test Kennzahlenblock typography fixes.

Tests for KPI spacing patterns that fix glitches like:
- "Payback11 Mon." → "Payback: 11 Mon."
- "ROI-Rate165%nach 24 Monaten" → "ROI-Rate: 165 % (nach 24 Monaten)"
- "Zeitersparnis/Monat180 Std." → "Zeitersparnis/Monat: 180 Std."
- "AI Act RisikoMittel" → "AI Act Risiko: Mittel"
"""

import pytest
from services.content_quality_enforcer import (
    fix_kennzahlen_spacing,
    KPI_SPACING_PATTERNS,
)


class TestPaybackSpacing:
    """Tests for Payback KPI spacing fixes."""

    def test_payback_glued_number(self):
        """'Payback11 Monate' → 'Payback: 11 Monate'"""
        html = "<p>Payback11 Monate</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "Payback: 11 Monate" in result
        assert count > 0

    def test_payback_short_suffix(self):
        """'Payback11 Mon.' → 'Payback: 11 Mon.'"""
        html = "<p>Payback11 Mon.</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "Payback: 11 Mon." in result

    def test_payback_decimal(self):
        """'Payback3,5 Monate' → 'Payback: 3,5 Monate'"""
        html = "<p>Payback3,5 Monate</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "Payback: 3,5 Monate" in result

    def test_payback_already_correct(self):
        """'Payback: 11 Monate' stays unchanged."""
        html = "<p>Payback: 11 Monate</p>"
        result, count = fix_kennzahlen_spacing(html)
        # Should normalize but not introduce errors
        assert "Payback" in result and "11" in result

    def test_amortisation_glued(self):
        """'Amortisation9,5 Monate' → 'Amortisation: 9,5 Monate'"""
        html = "<span>Amortisation9,5 Monate</span>"
        result, count = fix_kennzahlen_spacing(html)
        assert "Amortisation: 9,5 Monate" in result


class TestROISpacing:
    """Tests for ROI-Rate KPI spacing fixes."""

    def test_roi_rate_glued_percent(self):
        """'ROI-Rate165%' → 'ROI-Rate: 165 %'"""
        html = "<p>ROI-Rate165%</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "ROI-Rate: 165 %" in result
        assert count > 0

    def test_roi_rate_with_nach_suffix(self):
        """'ROI-Rate165%nach 24 Monaten' → 'ROI-Rate: 165 % (nach 12 Monaten)' (KIS-1034-D4: force 12m)"""
        html = "<p>ROI-Rate165%nach 24 Monaten</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "ROI-Rate: 165 % (nach 12 Monaten)" in result

    def test_roi_rate_decimal(self):
        """'ROI-Rate85,5%' → 'ROI-Rate: 85,5 %'"""
        html = "<p>ROI-Rate85,5%</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "ROI-Rate: 85,5 %" in result

    def test_roi_with_auf_suffix(self):
        """'ROI85%auf 12 Monate' → 'ROI: 85 % auf 12 Monate'"""
        html = "<p>ROI85%auf 12 Monate</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "ROI: 85 %" in result


class TestZeitersparnisSpacing:
    """Tests for Zeitersparnis KPI spacing fixes."""

    def test_zeitersparnis_monat_glued(self):
        """'Zeitersparnis/Monat180 Std.' → 'Zeitersparnis/Monat: 180 Std.'"""
        html = "<p>Zeitersparnis/Monat180 Std.</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "Zeitersparnis/Monat: 180 Std." in result
        assert count > 0

    def test_zeitersparnis_simple_glued(self):
        """'Zeitersparnis210Std' → 'Zeitersparnis: 210 Std'"""
        html = "<p>Zeitersparnis210Std</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "Zeitersparnis: 210 Std" in result

    def test_zeitersparnis_stunden(self):
        """'Zeitersparnis/Monat25 Stunden' → 'Zeitersparnis/Monat: 25 Stunden'"""
        html = "<p>Zeitersparnis/Monat25 Stunden</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "Zeitersparnis/Monat: 25 Stunden" in result


class TestAIActRisikoSpacing:
    """Tests for AI Act Risiko KPI spacing fixes."""

    def test_ai_act_risiko_mittel(self):
        """'AI Act RisikoMittel' → 'AI Act Risiko: Mittel'"""
        html = "<p>AI Act RisikoMittel</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "AI Act Risiko: Mittel" in result
        assert count > 0

    def test_ai_act_risiko_hoch(self):
        """'AI Act RisikoHoch' → 'AI Act Risiko: Hoch'"""
        html = "<p>AI Act RisikoHoch</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "AI Act Risiko: Hoch" in result

    def test_ai_act_risiko_gering(self):
        """'AI Act Risikogering' → 'AI Act Risiko: gering'"""
        html = "<p>AI Act Risikogering</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "AI Act Risiko: gering" in result

    def test_ai_act_risiko_minimal(self):
        """'AI Act Risikominimal' → 'AI Act Risiko: minimal'"""
        html = "<p>AI Act Risikominimal</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert "AI Act Risiko: minimal" in result


class TestMixedKPIBlocks:
    """Tests for realistic KPI blocks with multiple issues."""

    def test_full_kpi_block_from_report_504(self):
        """Realistic KPI block from Report-504 with multiple issues."""
        html = """
        <div class="kpi-card">
            <div>Payback11 Mon.</div>
            <div>ROI-Rate165%nach 24 Monaten</div>
            <div>Zeitersparnis/Monat180 Std.</div>
            <div>AI Act RisikoMittel</div>
        </div>
        """
        result, count = fix_kennzahlen_spacing(html)

        assert "Payback: 11 Mon." in result
        assert "ROI-Rate: 165 % (nach 12 Monaten)" in result
        assert "Zeitersparnis/Monat: 180 Std." in result
        assert "AI Act Risiko: Mittel" in result
        assert count >= 4

    def test_preserve_correct_formatting(self):
        """Already correctly formatted values should not be corrupted."""
        html = """
        <div class="kennzahlen">
            <div>Payback: 3,5 Monate</div>
            <div>ROI-Rate: 165 %</div>
            <div>Zeitersparnis/Monat: 180 Std.</div>
            <div>AI Act Risiko: Mittel</div>
        </div>
        """
        result, count = fix_kennzahlen_spacing(html)

        # Values should still be intact
        assert "3,5" in result
        assert "165" in result
        assert "180" in result
        assert "Mittel" in result

    def test_no_double_colons(self):
        """Ensure no double colons are introduced."""
        html = "<p>Payback: 11 Mon.</p>"
        result, count = fix_kennzahlen_spacing(html)
        assert ": :" not in result
        assert "::" not in result
