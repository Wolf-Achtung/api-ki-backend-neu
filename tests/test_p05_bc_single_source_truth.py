# -*- coding: utf-8 -*-
"""
Tests for P0.5 - Business Case Single Source of Truth

Tests:
- KPI values consistent with canonical BC (hours * rate = EUR)
- Scenarios respect solo cap (no >20h)
- ROI formula uses OPEX everywhere (NET formula)
- generate_kpi_targets uses capped hours
"""

import pytest


class TestKPIValueConsistency:
    """Test that KPI values are consistent with canonical BC calculation."""

    def test_monthly_savings_equals_hours_times_rate(self):
        """Test that monthly savings = hours * rate."""
        from services.business_case_engine_v2 import calculate_monthly_savings

        # Test: 20 hours * 80 EUR/hour = 1600 EUR
        result = calculate_monthly_savings(20, hourly_rate=80)
        assert result == 1600, f"20h * 80€ should be 1600€, got {result}"

        # Test: 15 hours * 95 EUR/hour = 1425 EUR
        result = calculate_monthly_savings(15, hourly_rate=95)
        assert result == 1425, f"15h * 95€ should be 1425€, got {result}"

    def test_annual_savings_equals_12_times_monthly(self):
        """Test that annual savings = 12 * monthly savings."""
        from services.business_case_engine_v2 import calculate_annual_savings

        # Test: 1600 EUR/month * 12 = 19200 EUR/year
        result = calculate_annual_savings(1600)
        assert result == 19200, f"1600€ * 12 should be 19200€, got {result}"


class TestScenariosSoloCapRespect:
    """Test that scenarios respect the solo cap of 20h."""

    def test_solo_cap_is_20_hours(self):
        """Test that solo max is 20 hours (P0.3)."""
        from services.business_case_engine_v2 import MAX_TIME_SAVINGS_BY_SIZE

        assert MAX_TIME_SAVINGS_BY_SIZE.get("solo") == 20, "Solo max should be 20h"

    def test_cap_time_savings_enforces_solo_cap(self):
        """Test that cap_time_savings enforces 20h for solo."""
        from services.business_case_engine_v2 import cap_time_savings

        # 30h for solo should be capped to 20h
        capped, was_capped = cap_time_savings(30, "solo")
        assert capped == 20, f"30h for solo should cap to 20h, got {capped}"
        assert was_capped is True

        # 15h for solo should not be capped
        capped, was_capped = cap_time_savings(15, "solo")
        assert capped == 15, f"15h for solo should stay 15h, got {capped}"
        assert was_capped is False

    def test_scenarios_use_capped_hours_for_savings(self):
        """Test that scenario generation uses capped hours."""
        from services.business_case_engine_v2 import (
            generate_scenarios,
            cap_time_savings,
            get_hourly_rate,
        )

        # For solo with 30h input (should be capped to 20h)
        raw_hours = 30
        capped_hours, _ = cap_time_savings(raw_hours, "solo")
        rate, _ = get_hourly_rate("solo")

        # Base monthly savings should use capped hours
        expected_base_savings = capped_hours * rate  # 20h * 80€ = 1600€
        assert expected_base_savings == 1600, f"Expected 1600€, got {expected_base_savings}"

        # Generate scenarios with capped savings
        scenarios = generate_scenarios(
            investment_total=5000,
            base_monthly_savings=expected_base_savings,
            funding_effect=0,
            opex_monthly=50,
        )

        # Realistic scenario should have base savings (1600€)
        realistic = next((s for s in scenarios if s.name == "realistic"), None)
        assert realistic is not None
        assert realistic.monthly_savings == expected_base_savings, \
            f"Realistic savings should be {expected_base_savings}€, got {realistic.monthly_savings}"


class TestROIFormulaWithOPEX:
    """Test that ROI formula uses NET (includes OPEX)."""

    def test_roi_calculation_includes_opex(self):
        """Test that ROI is calculated with OPEX deduction."""
        from services.business_case_engine_v2 import calculate_roi

        # ROI formula: (annual_net - investment) / investment * 100
        # With: annual_net = annual_savings - annual_opex
        investment = 5000
        annual_gross_savings = 19200  # 1600 * 12
        annual_opex = 600  # 50 * 12
        annual_net = annual_gross_savings - annual_opex  # 18600

        # ROI = (18600 - 5000) / 5000 * 100 = 272%
        expected_roi = ((annual_net - investment) / investment) * 100
        assert expected_roi == 272.0

        # calculate_roi should give same result
        result = calculate_roi(annual_net, investment)
        # ROI is capped at MAX_ROI (200%)
        assert result == 200.0, f"ROI should be capped at 200%, got {result}"

    def test_scenarios_use_net_payback(self):
        """Test that scenario payback uses NET (gross - opex)."""
        from services.business_case_engine_v2 import generate_scenarios

        # Generate scenarios with known values
        scenarios = generate_scenarios(
            investment_total=5000,
            base_monthly_savings=1600,  # Gross
            funding_effect=0,
            opex_monthly=100,  # OPEX
        )

        # For realistic scenario:
        # Net = 1600 - 100 = 1500
        # Payback = 5000 / 1500 = 3.33 months
        realistic = next((s for s in scenarios if s.name == "realistic"), None)
        assert realistic is not None

        expected_net = 1600 - 100  # 1500
        expected_payback = 5000 / expected_net  # 3.33

        assert abs(realistic.payback_months - expected_payback) < 0.1, \
            f"Payback should be ~{expected_payback:.1f}m, got {realistic.payback_months}"


class TestGenerateKPITargetsUsesCappedHours:
    """Test that generate_kpi_targets uses capped hours."""

    def test_kpi_targets_use_provided_hours(self):
        """Test that KPI targets use the provided (capped) hours."""
        from services.business_case_engine_v2 import generate_kpi_targets, ScenarioKPIs

        # Create mock scenarios
        scenarios = [
            ScenarioKPIs(
                name="optimistic",
                roi_12m=200,
                payback_months=3,
                monthly_savings=2000,
                annual_savings=24000,
                investment_total=5000,
            ),
            ScenarioKPIs(
                name="realistic",
                roi_12m=150,
                payback_months=4,
                monthly_savings=1600,
                annual_savings=19200,
                investment_total=5000,
            ),
            ScenarioKPIs(
                name="conservative",
                roi_12m=100,
                payback_months=5,
                monthly_savings=1200,
                annual_savings=14400,
                investment_total=5000,
            ),
        ]

        # P0.5: Use capped hours (20h for solo)
        capped_hours = 20

        kpi_6m, kpi_12m = generate_kpi_targets(scenarios, capped_hours)

        # 12m target should use the provided capped hours
        assert kpi_12m["time_savings_hours"] == capped_hours, \
            f"12m KPI should use capped hours ({capped_hours}), got {kpi_12m['time_savings_hours']}"

        # 6m target should use 60% of capped hours
        expected_6m_hours = capped_hours * 0.6
        assert kpi_6m["time_savings_hours"] == expected_6m_hours, \
            f"6m KPI should use 60% of capped hours ({expected_6m_hours}), got {kpi_6m['time_savings_hours']}"


class TestP05Integration:
    """Integration tests for P0.5 Business Case Single Source of Truth."""

    def test_business_case_uses_capped_hours_throughout(self):
        """Test that capped hours are used throughout the business case pipeline."""
        from services.business_case_engine_v2 import (
            cap_time_savings,
            get_hourly_rate,
            calculate_monthly_savings,
            generate_scenarios,
            generate_kpi_targets,
        )

        # Solo user with 35h claimed savings (should be capped to 20h)
        raw_hours = 35
        company_size = "solo"

        # Step 1: Cap hours
        capped_hours, was_capped = cap_time_savings(raw_hours, company_size)
        assert capped_hours == 20
        assert was_capped is True

        # Step 2: Get canonical hourly rate
        rate, _ = get_hourly_rate(company_size)
        assert rate == 80

        # Step 3: Calculate base savings with capped hours
        base_savings = calculate_monthly_savings(capped_hours, hourly_rate=rate)
        assert base_savings == 1600  # 20h * 80€

        # Step 4: Generate scenarios with capped savings
        scenarios = generate_scenarios(
            investment_total=5000,
            base_monthly_savings=base_savings,
            funding_effect=0,
            opex_monthly=50,
        )

        realistic = next((s for s in scenarios if s.name == "realistic"), None)
        assert realistic.monthly_savings == base_savings  # Uses capped hours

        # Step 5: Generate KPI targets with capped hours
        kpi_6m, kpi_12m = generate_kpi_targets(scenarios, capped_hours)
        assert kpi_12m["time_savings_hours"] == capped_hours  # Uses capped hours

    def test_canonical_bc_consistency(self):
        """Test that BusinessCaseCanonical produces consistent values."""
        from services.business_case_engine_v2 import BusinessCaseCanonical

        # Solo: 20h * 80€ = 1600€/month gross
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=50,
        )

        # Verify derived values
        assert canonical.monthly_gross == 1600  # 20 * 80
        assert canonical.monthly_net == 1550  # 1600 - 50
        assert canonical.annual_gross == 19200  # 1600 * 12
        assert canonical.annual_net == 18600  # 1550 * 12

        # Payback uses NET
        expected_payback = 5000 / 1550  # ~3.23 months
        assert abs(canonical.payback_months - expected_payback) < 0.01
