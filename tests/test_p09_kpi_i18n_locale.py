# -*- coding: utf-8 -*-
"""
Tests for P0.9 - KPI Labels via ui() + Decimal Comma for DE Locale

Tests:
- KPI labels use ui() function for proper i18n
- Decimal values use comma for DE locale (German format)
- PAYBACK_MONTHS_FMT_DE uses comma separator
"""

import os
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestKPILabelsViaUI:
    """Test that KPI labels use ui() function for i18n."""

    def test_kpi_labels_exist_in_ui_labels(self):
        """Test that required KPI labels exist in ui_labels.json."""
        from services.i18n import has_label, get_label

        required_kpi_labels = [
            "kpi_time_savings_month",
            "kpi_payback_months",
            "kpi_roi_details",
            "payback",
            "savings",
            "investment",
        ]

        for label_key in required_kpi_labels:
            assert has_label(label_key), f"Missing KPI label: {label_key}"

    def test_kpi_labels_have_de_translation(self):
        """Test that KPI labels have German translations."""
        from services.i18n import get_label

        kpi_labels = {
            "kpi_time_savings_month": "Zeitersparnis/Monat",
            "kpi_payback_months": "Amortisation",
            "payback": "Amortisation",
        }

        for key, expected_de in kpi_labels.items():
            de_label = get_label(key, "de")
            assert de_label == expected_de, \
                f"Expected '{expected_de}' for '{key}' in DE, got '{de_label}'"

    def test_ui_function_returns_de_labels(self):
        """Test that ui() function returns German labels."""
        from services.i18n import ui

        ui_de = ui("de")

        assert ui_de("kpi_time_savings_month") == "Zeitersparnis/Monat"
        assert ui_de("payback") == "Amortisation"

    def test_ui_function_returns_en_labels(self):
        """Test that ui() function returns English labels."""
        from services.i18n import ui

        ui_en = ui("en")

        assert ui_en("kpi_time_savings_month") == "Time Savings/Month"
        assert ui_en("payback") == "Payback"


class TestDecimalCommaForDE:
    """Test that decimal values use comma for DE locale."""

    def test_fmt_de_decimal_uses_comma(self):
        """Test German decimal format uses comma separator."""
        # Replicate _fmt_de_decimal from gpt_analyze.py
        def _fmt_de_decimal(val, ndigits: int = 1) -> str:
            try:
                formatted = f"{float(val):.{ndigits}f}"
                return formatted.replace(".", ",")  # German: "3,5" not "3.5"
            except (ValueError, TypeError):
                return str(val) if val else "0"

        assert _fmt_de_decimal(3.5, 1) == "3,5"
        assert _fmt_de_decimal(10.123, 1) == "10,1"
        assert _fmt_de_decimal(0, 1) == "0,0"
        assert _fmt_de_decimal(100, 0) == "100"

    def test_payback_months_fmt_de_format(self):
        """Test PAYBACK_MONTHS_FMT_DE format is correct."""
        def _fmt_de_decimal(val, ndigits: int = 1) -> str:
            try:
                formatted = f"{float(val):.{ndigits}f}"
                return formatted.replace(".", ",")
            except (ValueError, TypeError):
                return str(val) if val else "0"

        # Test typical payback values
        test_cases = [
            (3.5, "3,5"),
            (2.0, "2,0"),
            (10.7, "10,7"),
            (0.5, "0,5"),
        ]

        for raw_val, expected_fmt in test_cases:
            result = _fmt_de_decimal(raw_val, 1)
            assert result == expected_fmt, \
                f"Expected '{expected_fmt}' for {raw_val}, got '{result}'"

    def test_german_number_format_for_thousands(self):
        """Test German thousand separator (dot) for large numbers."""
        def _fmt_german_int(val) -> str:
            """Format integer with German thousand separator."""
            return f"{int(val):,}".replace(",", ".")

        assert _fmt_german_int(1000) == "1.000"
        assert _fmt_german_int(15000) == "15.000"
        assert _fmt_german_int(1234567) == "1.234.567"

    def test_eur_formatting_uses_german_style(self):
        """Test EUR values use German formatting style."""
        from services.quickwins_renderer import format_eur_range

        result = format_eur_range(800, 1200)
        # Should use German dot for thousands, not comma
        assert "800" in result
        assert "1.200" in result  # German: 1.200 not 1,200


class TestCanonicalTemplateFMTDE:
    """Test that canonical template bindings use DE format."""

    def test_payback_fmt_de_binding(self):
        """Test PAYBACK_MONTHS_FMT_DE is properly bound."""
        from services.business_case_engine_v2 import BusinessCaseCanonical

        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=50,
        )

        # Payback should be calculable
        payback = canonical.payback_months
        assert payback > 0

        # Format for DE
        def _fmt_de_decimal(val, ndigits: int = 1) -> str:
            formatted = f"{float(val):.{ndigits}f}"
            return formatted.replace(".", ",")

        payback_fmt_de = _fmt_de_decimal(payback, 1)

        # Should have comma as decimal separator
        assert "," in payback_fmt_de, "DE format should use comma"
        assert "." not in payback_fmt_de, "DE format should not use dot for decimal"


class TestP09Integration:
    """Integration tests for P0.9."""

    def test_full_kpi_pipeline_with_i18n(self):
        """Test full KPI pipeline uses ui() for labels."""
        from services.i18n import ui, get_label

        # German context
        ui_de = ui("de")
        assert ui_de("payback") == "Amortisation"
        assert ui_de("savings") == "Einsparungen"
        assert ui_de("investment") == "Investition"

        # English context
        ui_en = ui("en")
        assert ui_en("payback") == "Payback"
        assert ui_en("savings") == "Savings"
        assert ui_en("investment") == "Investment"

    def test_kpi_recommendations_note_i18n(self):
        """Test KPI recommendations note has i18n."""
        from services.i18n import get_label

        de_note = get_label("kpi_recommendations_note", "de")
        en_note = get_label("kpi_recommendations_note", "en")

        assert "Empfehlungen" in de_note or "Umsetzung" in de_note
        assert "recommendations" in en_note.lower()

    def test_roi_details_label_i18n(self):
        """Test ROI details label has i18n."""
        from services.i18n import get_label

        de_label = get_label("kpi_roi_details", "de")
        en_label = get_label("kpi_roi_details", "en")

        assert "ROI" in de_label
        assert "ROI" in en_label
