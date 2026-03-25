# -*- coding: utf-8 -*-
"""
Tests for Fix-Batch B - Canonical Business Case Table Binding

Tests:
- BC table ROI includes OPEX (NET formula)
- No placeholder patterns in BUSINESS_CASE_TABLE_HTML
- ROI calculation matches canonical BC
"""

import os
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestBCTableOPEXInclusive:
    """Test that BC table ROI uses OPEX-inclusive (NET) formula."""

    def test_roi_12m_includes_opex(self):
        """Test ROI calculation: net_12m = (monthly_savings - opex)*12 - capex."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "team",
            "jahresumsatz": "100k_500k",
            "investitionsbudget": "5000_10000",
            "qw_hours_total": 20,
        }
        env = {}

        bc = calc_business_case(answers, env)

        # Extract values
        monthly_savings = bc.get("EINSPARUNG_MONAT_EUR", 0)
        opex = bc.get("OPEX_REALISTISCH_EUR", 0)
        capex = bc.get("CAPEX_REALISTISCH_EUR", 0)
        roi_12m_eur = bc.get("ROI_12M_EUR", 0)

        # Calculate expected NET ROI
        annual_opex = opex * 12
        net_savings_12m = monthly_savings * 12 - annual_opex
        expected_roi_12m_eur = net_savings_12m - capex

        # ROI_12M_EUR should match NET formula
        assert roi_12m_eur == expected_roi_12m_eur, \
            f"ROI_12M_EUR should be {expected_roi_12m_eur} (NET), got {roi_12m_eur}"

    def test_roi_table_formula_shows_opex(self):
        """Test that BC table HTML shows OPEX in ROI formula."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "solo",
            "jahresumsatz": "unter_100k",
            "investitionsbudget": "2000_5000",
            "qw_hours_total": 15,
        }
        env = {}

        bc = calc_business_case(answers, env)
        table_html = bc.get("BUSINESS_CASE_TABLE_HTML", "")

        # Table should show OPEX-inclusive formula
        assert "OPEX" in table_html, \
            "ROI formula in table should mention OPEX"
        assert "Einsparung" in table_html and "CAPEX" in table_html, \
            "ROI formula should show full calculation"

    def test_roi_matches_canonical_bc(self):
        """Test that ROI calculation matches canonical BusinessCaseCanonical."""
        from services.business_case_engine_v2 import BusinessCaseCanonical
        from services.extra_sections import calc_business_case

        # Use same parameters
        answers = {
            "unternehmensgroesse": "team",
            "jahresumsatz": "100k_500k",
            "investitionsbudget": "5000_10000",
            "qw_hours_total": 20,
        }
        env = {}

        bc = calc_business_case(answers, env)

        # Create canonical BC with same values
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=bc.get("CAPPED_HOURS", 20),
            hourly_rate_eur=95,  # team rate
            capex_eur=bc.get("CAPEX_REALISTISCH_EUR", 6000),
            opex_month_eur=bc.get("OPEX_REALISTISCH_EUR", 350),
        )

        # Both should use NET formula - ROI percentages should be close
        bc_roi_pct = bc.get("ROI_12M", 0)
        canonical_roi_pct = canonical.roi_12m_net

        # Allow small difference due to rounding
        assert abs(bc_roi_pct - canonical_roi_pct) < 5, \
            f"BC ROI ({bc_roi_pct}%) should be close to canonical ({canonical_roi_pct}%)"


class TestNoPlaceholderPatterns:
    """Test that BC table has no unresolved placeholders."""

    def test_no_brace_placeholders_in_table(self):
        """Test that BC table HTML contains no {placeholder} patterns."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "kmu",
            "jahresumsatz": "500k_1m",
            "investitionsbudget": "10000_25000",
            "qw_hours_total": 30,
        }
        env = {}

        bc = calc_business_case(answers, env)
        table_html = bc.get("BUSINESS_CASE_TABLE_HTML", "")

        # No placeholder patterns
        assert "{ROI" not in table_html, "Found {ROI placeholder"
        assert "{{ROI" not in table_html, "Found {{ROI placeholder"
        assert "{CAPEX" not in table_html, "Found {CAPEX placeholder"
        assert "{OPEX" not in table_html, "Found {OPEX placeholder"
        assert "{PAYBACK" not in table_html, "Found {PAYBACK placeholder"
        assert "{{" not in table_html, "Found {{ placeholder"

    def test_table_has_actual_values(self):
        """Test that BC table HTML contains actual numeric values."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "team",
            "jahresumsatz": "100k_500k",
            "investitionsbudget": "5000_10000",
            "qw_hours_total": 18,
        }
        env = {}

        bc = calc_business_case(answers, env)
        table_html = bc.get("BUSINESS_CASE_TABLE_HTML", "")

        # Should contain actual values
        assert "€" in table_html, "Table should contain € symbol"
        assert "%" in table_html, "Table should contain % for ROI"
        assert "Monate" in table_html, "Table should show payback in months"


class TestBatchBIntegration:
    """Integration tests for Fix-Batch B."""

    def test_example_from_briefing(self):
        """Test CAPEX is canonical and NET ROI formula is correct.

        FIX-S25-FINAL-CAPEX: Team CAPEX is always 24k (canonical), not budget-band-derived.
        With 17h * 95€ = 1615€/month savings and canonical CAPEX, ROI may be negative.
        """
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "team",
            "jahresumsatz": "100k_500k",
            "investitionsbudget": "2000_10000",
            "qw_hours_total": 17,  # 17h * 95€ = 1615€
        }
        env = {}

        bc = calc_business_case(answers, env)

        monthly_savings = bc.get("EINSPARUNG_MONAT_EUR", 0)
        opex = bc.get("OPEX_REALISTISCH_EUR", 0)
        capex = bc.get("CAPEX_REALISTISCH_EUR", 0)
        roi_12m_eur = bc.get("ROI_12M_EUR", 0)

        # FIX-S25-FINAL-CAPEX: Team CAPEX is always canonical 24k
        assert capex == 24_000, f"Team CAPEX should be canonical 24000, got {capex}"

        # Verify NET formula is used
        expected_net_12m = (monthly_savings - opex) * 12 - capex
        assert roi_12m_eur == expected_net_12m, \
            f"ROI_12M_EUR ({roi_12m_eur}) should equal NET formula ({expected_net_12m})"

        # ROI is within bounds (-100% to 200%)
        roi_pct = bc.get("ROI_12M", 0)
        assert -100 <= roi_pct <= 200, f"ROI should be -100 to 200%, got {roi_pct}%"

    def test_net_roi_lower_than_gross(self):
        """Test that NET ROI is lower than GROSS ROI when OPEX > 0."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "team",
            "jahresumsatz": "100k_500k",
            "investitionsbudget": "5000_10000",
            "qw_hours_total": 20,
        }
        env = {}

        bc = calc_business_case(answers, env)

        monthly_savings = bc.get("EINSPARUNG_MONAT_EUR", 0)
        opex = bc.get("OPEX_REALISTISCH_EUR", 0)
        capex = bc.get("CAPEX_REALISTISCH_EUR", 0)
        roi_12m_eur = bc.get("ROI_12M_EUR", 0)

        # Calculate what GROSS would be (without OPEX deduction)
        gross_roi_eur = monthly_savings * 12 - capex

        # NET should be lower than GROSS when OPEX > 0
        if opex > 0:
            assert roi_12m_eur < gross_roi_eur, \
                f"NET ROI ({roi_12m_eur}) should be less than GROSS ({gross_roi_eur}) when OPEX > 0"
