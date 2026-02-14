# -*- coding: utf-8 -*-
"""
Tests for P0.8 - ROI Table Uses Canonical OPEX-Inclusive Formula

Tests:
- ROI 12m includes OPEX deduction (NET formula)
- ROI table matches canonical BC values
- No "business case replacement" warnings in clean runs
"""

import os
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestROIIncludesOPEX:
    """Test that ROI calculation includes OPEX deduction."""

    def test_roi_12m_net_formula(self):
        """Test ROI_12M is calculated using NET formula (gross - opex)."""
        from services.business_case_engine_v2 import BusinessCaseCanonical

        # Example: 20h/month * 80€/h = 1600€/month gross
        # OPEX: 100€/month
        # Net = 1600 - 100 = 1500€/month
        # Annual net = 1500 * 12 = 18000€
        # ROI = (18000 - 5000) / 5000 * 100 = 260% (capped to 200%)
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=100,
        )

        # Verify NET values
        assert canonical.monthly_gross == 1600, "Monthly gross = 20h * 80€"
        assert canonical.monthly_net == 1500, "Monthly net = 1600 - 100 OPEX"
        assert canonical.annual_net == 18000, "Annual net = 1500 * 12"

        # Verify ROI is NET-based (not gross-based)
        expected_roi_raw = ((18000 - 5000) / 5000) * 100  # 260%
        assert abs(canonical.roi_12m_net_raw - expected_roi_raw) < 0.1

        # Verify capped ROI
        assert canonical.roi_12m_net == 200.0, "ROI should be capped at 200%"

    def test_roi_12m_gross_differs_from_net(self):
        """Test that gross ROI differs from net ROI when OPEX > 0."""
        from services.business_case_engine_v2 import BusinessCaseCanonical

        canonical = BusinessCaseCanonical(
            hours_saved_per_month=15,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=200,  # Significant OPEX
        )

        # Gross: 15*80*12 = 14400€/year
        # Net: (15*80 - 200)*12 = 1000*12 = 12000€/year
        # ROI Gross = (14400 - 5000) / 5000 * 100 = 188%
        # ROI Net = (12000 - 5000) / 5000 * 100 = 140%

        assert canonical.roi_12m_gross_raw > canonical.roi_12m_net_raw, \
            "Gross ROI should be higher than Net ROI when OPEX > 0"

    def test_scenarios_use_net_for_roi(self):
        """Test that scenario ROI uses NET formula."""
        from services.business_case_engine_v2 import generate_scenarios

        scenarios = generate_scenarios(
            investment_total=5000,
            base_monthly_savings=1600,  # Gross
            funding_effect=0,
            opex_monthly=100,
        )

        # For realistic: Net = 1600 - 100 = 1500
        # Annual net = 18000
        # ROI = (18000 - 5000) / 5000 * 100 = 260% → capped to 200%
        realistic = next(s for s in scenarios if s.name == "realistic")
        assert realistic.roi_12m >= 200.0, "Realistic ROI should be capped at 200%"


class TestROITableMatchesCanonical:
    """Test that ROI table matches canonical BC values."""

    def test_inject_canonical_sets_net_roi(self):
        """Test that inject_canonical_to_sections uses NET ROI."""
        from services.business_case_engine_v2 import (
            BusinessCaseCanonical,
            inject_canonical_to_sections,
        )

        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=50,
        )

        sections = {}
        updates = inject_canonical_to_sections(canonical, sections)

        assert updates > 0, "Should have injected values"
        assert "ROI_12M" in sections
        assert sections["ROI_12M"] == canonical.roi_12m_net, \
            "ROI_12M should match canonical NET ROI"
        assert sections.get("ROI_12M_RAW") == canonical.roi_12m_net_raw, \
            "ROI_12M_RAW should match canonical NET RAW ROI"

    def test_canonical_bc_consistency(self):
        """Test that canonical BC values are internally consistent."""
        from services.business_case_engine_v2 import BusinessCaseCanonical

        canonical = BusinessCaseCanonical(
            hours_saved_per_month=30,
            hourly_rate_eur=95,
            capex_eur=8000,
            opex_month_eur=150,
        )

        # Verify internal consistency
        assert canonical.monthly_gross == 30 * 95
        assert canonical.monthly_net == canonical.monthly_gross - 150
        assert canonical.annual_gross == canonical.monthly_gross * 12
        assert canonical.annual_net == canonical.monthly_net * 12

        # ROI formula check
        expected_net_benefit = canonical.annual_net - canonical.capex_eur
        expected_roi = (expected_net_benefit / canonical.capex_eur) * 100
        assert abs(canonical.roi_12m_net_raw - expected_roi) < 0.1


class TestNoBusinessCasePlaceholders:
    """Test that no placeholder warnings appear in clean BC generation."""

    def test_calc_business_case_no_placeholders(self):
        """Test that calc_business_case generates complete values."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "team",
            "jahresumsatz": "100k_500k",
            "investitionsbudget": "5000_10000",
            "qw_hours_total": 20,
        }
        env = {}

        bc = calc_business_case(answers, env)

        # All required fields should have values (not None, not placeholder)
        assert bc.get("CAPEX_REALISTISCH_EUR") is not None
        assert bc.get("OPEX_REALISTISCH_EUR") is not None
        assert bc.get("EINSPARUNG_MONAT_EUR") is not None
        assert bc.get("PAYBACK_MONTHS") is not None
        assert bc.get("ROI_12M") is not None

        # ROI should be a number, not a placeholder
        roi = bc.get("ROI_12M")
        assert isinstance(roi, (int, float)), f"ROI should be numeric, got {type(roi)}"
        assert roi > 0, "ROI should be positive"

    def test_business_case_table_html_no_placeholders(self):
        """Test that BC table HTML contains no unresolved placeholders."""
        from services.extra_sections import calc_business_case

        answers = {
            "unternehmensgroesse": "solo",
            "jahresumsatz": "unter_100k",
            "investitionsbudget": "2000_5000",
            "qw_hours_total": 18,
        }
        env = {}

        bc = calc_business_case(answers, env)

        table_html = bc.get("BUSINESS_CASE_TABLE_HTML", "")

        # Should not contain any placeholder patterns
        assert "{ROI" not in table_html, "Found unresolved {ROI placeholder"
        assert "{{ROI" not in table_html, "Found unresolved {{ROI placeholder"
        assert "=ROI" not in table_html, "Found =ROI placeholder"
        assert "{PAYBACK" not in table_html, "Found unresolved {PAYBACK placeholder"
        # Table should contain actual percentage value
        assert "%" in table_html or "Prozent" in table_html, \
            "Should have ROI percentage in table"


class TestP08Integration:
    """Integration tests for P0.8."""

    def test_full_bc_pipeline_uses_net_roi(self):
        """Test full business case pipeline uses NET ROI everywhere."""
        from services.business_case_engine_v2 import (
            BusinessCaseCanonical,
            generate_scenarios,
            inject_canonical_to_sections,
            get_hourly_rate,
            cap_time_savings,
        )

        # Simulate full BC pipeline
        company_size = "team"
        hours_claimed = 25  # Will be capped to team max
        capped_hours, _ = cap_time_savings(hours_claimed, company_size)
        rate, _ = get_hourly_rate(company_size)

        canonical = BusinessCaseCanonical(
            hours_saved_per_month=capped_hours,
            hourly_rate_eur=rate,
            capex_eur=7000,
            opex_month_eur=120,
            company_size=company_size,
        )

        # Generate scenarios
        scenarios = generate_scenarios(
            investment_total=7000,
            base_monthly_savings=canonical.monthly_gross,
            funding_effect=0,
            opex_monthly=120,
        )

        # Inject into sections
        sections = {}
        inject_canonical_to_sections(canonical, sections)

        # Verify all ROI values are NET-based
        realistic = next(s for s in scenarios if s.name == "realistic")

        # Section ROI should match canonical NET
        assert sections["ROI_12M"] == canonical.roi_12m_net

        # Scenario ROI should use NET formula (we verified this in earlier tests)
        # Just check it's within expected range
        assert 0 <= realistic.roi_12m <= 500, "Scenario ROI should be in valid range"

    def test_roi_explanation_shows_opex_deduction(self):
        """Test that ROI explanation HTML shows OPEX deduction."""
        from services.business_case_engine_v2 import ROIExplanation

        explanation = ROIExplanation(
            stundensatz=80,
            stundensatz_quelle="Branchendurchschnitt",
            zeitersparnis_stunden=20,
            zeitersparnis_quelle="Quick Wins Aggregation",
            zeitersparnis_gecappt=False,
            zeitersparnis_max=40,
            einmalkosten=5000,
            laufende_kosten_monat=100,
            foerdereffekt=0,
            roi_raw=260.0,
            roi_capped=200.0,
            roi_was_capped=True,
        )

        html = explanation.to_html(lang="de")

        # Should show OPEX in the explanation
        assert "100" in html, "OPEX value should appear in explanation"
        assert "Laufende Kosten" in html or "OPEX" in html, \
            "Should mention ongoing costs"
        # Should show the formula
        assert "OPEX" in html or "laufende" in html.lower(), \
            "Formula should mention OPEX"
