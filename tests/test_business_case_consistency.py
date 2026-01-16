# -*- coding: utf-8 -*-
"""
Business Case Consistency Test - Single Source of Truth
=========================================================

v14.35.24: Tests for Business Case metric consistency across all sections.

Ensures:
1. Hourly rate is consistent across all sources (canonical from business_case_engine_v2)
2. Payback formatting doesn't contain long floats
3. ROI values are derived consistently
4. Both raw (computed) and capped (planning) ROI values are available (Option A)

Ref: TASK - Business Case Consistency – Single Source of Truth (3 Fixes)
     TASK - Option A: ROI „berechnet" + ROI „gedeckelt" überall konsistent
"""
import os
import re
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestBusinessCaseConsistency:
    """Tests for business case metric consistency."""

    def test_canonical_hourly_rates_defined(self):
        """Verify canonical hourly rates are defined in business_case_engine_v2."""
        from services.business_case_engine_v2 import HOURLY_RATES_BY_SIZE, get_hourly_rate

        # Check that all sizes have rates
        assert "solo" in HOURLY_RATES_BY_SIZE
        assert "team" in HOURLY_RATES_BY_SIZE
        assert "kmu" in HOURLY_RATES_BY_SIZE
        assert "enterprise" in HOURLY_RATES_BY_SIZE

        # Check specific values
        assert HOURLY_RATES_BY_SIZE["solo"] == 80, "Solo rate should be 80"
        assert HOURLY_RATES_BY_SIZE["team"] == 95, "Team rate should be 95"
        assert HOURLY_RATES_BY_SIZE["kmu"] == 110, "KMU rate should be 110"

    def test_get_hourly_rate_returns_canonical_values(self):
        """Verify get_hourly_rate returns the canonical values."""
        from services.business_case_engine_v2 import get_hourly_rate

        rate_solo, _ = get_hourly_rate("solo")
        rate_team, _ = get_hourly_rate("team")
        rate_kmu, _ = get_hourly_rate("kmu")

        assert rate_solo == 80
        assert rate_team == 95
        assert rate_kmu == 110

    def test_extra_sections_uses_canonical_rates(self):
        """Verify extra_sections.py uses canonical rates via import."""
        from services.extra_sections import get_size_constraints

        # Test solo constraints
        solo_constraints = get_size_constraints("solo", "100k_500k", "2000_10000")
        assert solo_constraints["hourly_rate"] == 80, "Solo should use canonical rate 80"

        # Test klein (maps to team)
        klein_constraints = get_size_constraints("klein", "100k_500k", "2000_10000")
        assert klein_constraints["hourly_rate"] == 95, "Klein should use canonical team rate 95"

    def test_roi_calculator_uses_canonical_rates(self):
        """Verify roi_calculator uses canonical rates."""
        from services.roi_calculator import _estimate_hourly_rate

        # Solo company
        solo_briefing = {"unternehmensgroesse": "solo"}
        rate = _estimate_hourly_rate(solo_briefing)
        assert rate == 80.0, f"Solo should get canonical rate 80, got {rate}"

        # Team company
        team_briefing = {"unternehmensgroesse": "team"}
        rate = _estimate_hourly_rate(team_briefing)
        assert rate == 95.0, f"Team should get canonical rate 95, got {rate}"

    def test_business_case_canonical_payback_format(self):
        """Verify payback values are formatted correctly (no long floats)."""
        from services.business_case_engine_v2 import BusinessCaseCanonical

        # Create a canonical business case
        bc = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        # Get the dict representation
        bc_dict = bc.to_dict()

        # Check payback is rounded
        payback = bc_dict["payback_months"]
        assert isinstance(payback, float)
        assert payback == round(payback, 1), f"Payback should be rounded to 1 decimal: {payback}"

        # Verify it doesn't have long floating point representation
        payback_str = str(payback)
        decimal_places = len(payback_str.split(".")[-1]) if "." in payback_str else 0
        assert decimal_places <= 1, f"Payback should have at most 1 decimal place: {payback_str}"

    def test_business_case_canonical_roi_consistency(self):
        """Verify ROI values are computed consistently."""
        from services.business_case_engine_v2 import BusinessCaseCanonical, MAX_ROI

        # Create a canonical business case
        bc = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        # Expected values:
        # monthly_gross = 20 * 80 = 1600
        # monthly_net = 1600 - 180 = 1420
        # annual_net = 1420 * 12 = 17040
        # roi_12m_net_raw = ((17040 - 5000) / 5000) * 100 = 240.8%
        # roi_12m_net = min(MAX_ROI, 240.8) = 200.0% (capped)

        assert bc.monthly_gross == 1600
        assert bc.monthly_net == 1420
        assert bc.annual_net == 17040
        # ROI is capped at MAX_ROI (200%) for conservative estimates
        assert round(bc.roi_12m_net, 1) == MAX_ROI, f"ROI should be capped at {MAX_ROI}%"

    def test_roi_raw_vs_capped_values(self):
        """Verify ROI raw (uncapped) and capped values are both available (Option A)."""
        from services.business_case_engine_v2 import BusinessCaseCanonical, MAX_ROI

        # Create a case with high ROI that will be capped
        bc = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        # Raw ROI should be uncapped (~240.8%)
        assert bc.roi_12m_net_raw > MAX_ROI, "Raw ROI should exceed MAX_ROI cap"
        assert round(bc.roi_12m_net_raw, 1) == 240.8, f"Raw ROI should be 240.8%, got {bc.roi_12m_net_raw}"

        # Capped ROI should be exactly MAX_ROI
        assert bc.roi_12m_net == MAX_ROI, f"Capped ROI should be {MAX_ROI}%, got {bc.roi_12m_net}"

        # Both values should be in to_dict()
        bc_dict = bc.to_dict()
        assert "roi_12m_net" in bc_dict, "to_dict should include roi_12m_net"
        assert "roi_12m_net_raw" in bc_dict, "to_dict should include roi_12m_net_raw"
        assert "roi_was_capped" in bc_dict, "to_dict should include roi_was_capped"
        assert bc_dict["roi_was_capped"] is True, "roi_was_capped should be True when ROI exceeds MAX_ROI"

    def test_roi_uncapped_when_below_max(self):
        """Verify ROI is not capped when below MAX_ROI."""
        from services.business_case_engine_v2 import BusinessCaseCanonical, MAX_ROI

        # Create a case with low ROI that won't be capped
        bc = BusinessCaseCanonical(
            hours_saved_per_month=5,
            hourly_rate_eur=80,
            capex_eur=10000,
            opex_month_eur=200,
        )

        # Both raw and capped should be the same when below MAX_ROI
        assert bc.roi_12m_net_raw < MAX_ROI, "This test requires ROI below MAX_ROI"
        assert bc.roi_12m_net == bc.roi_12m_net_raw, "ROI should not be capped when below MAX_ROI"

        # roi_was_capped should be False
        bc_dict = bc.to_dict()
        assert bc_dict["roi_was_capped"] is False, "roi_was_capped should be False when ROI is below MAX_ROI"

    def test_inject_canonical_includes_both_roi_values(self):
        """Verify inject_canonical_to_sections includes both raw and capped ROI."""
        from services.business_case_engine_v2 import BusinessCaseCanonical, inject_canonical_to_sections, MAX_ROI

        # Create a case with capped ROI
        bc = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        sections = {}
        inject_canonical_to_sections(bc, sections)

        # Check all ROI keys are injected
        assert "ROI_12M" in sections, "ROI_12M should be injected"
        assert "ROI_12M_RAW" in sections, "ROI_12M_RAW should be injected"
        assert "ROI_12M_CAPPED" in sections, "ROI_12M_CAPPED should be injected"
        assert "ROI_WAS_CAPPED" in sections, "ROI_WAS_CAPPED should be injected"

        # Verify values
        assert sections["ROI_12M"] == MAX_ROI, f"ROI_12M should be capped at {MAX_ROI}"
        assert round(sections["ROI_12M_RAW"], 1) == 240.8, "ROI_12M_RAW should be 240.8"
        assert sections["ROI_12M_CAPPED"] == MAX_ROI, f"ROI_12M_CAPPED should be {MAX_ROI}"
        assert sections["ROI_WAS_CAPPED"] is True, "ROI_WAS_CAPPED should be True"

    def test_no_hardcoded_81_hourly_rate(self):
        """Ensure there are no hardcoded 81€/h rates in the codebase."""
        import glob

        # Files to check
        files_to_check = [
            "gpt_analyze.py",
            "services/extra_sections.py",
            "services/roi_calculator.py",
            "services/business_case_engine_v2.py",
        ]

        for filepath in files_to_check:
            full_path = os.path.join(os.path.dirname(__file__), "..", filepath)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Check for 81€/h pattern
                    matches = re.findall(r'\b81\s*€', content)
                    assert len(matches) == 0, f"Found hardcoded 81€ in {filepath}: {matches}"


class TestPaybackFormatting:
    """Tests for payback value formatting."""

    def test_payback_german_decimal_format(self):
        """Test that German payback uses comma as decimal separator."""
        # Simulate the formatting logic from gpt_analyze.py
        payback_raw = 3.5
        payback_en = f"{float(payback_raw):.1f}"
        payback_de = payback_en.replace(".", ",")

        assert payback_en == "3.5"
        assert payback_de == "3,5"

    def test_payback_no_long_float(self):
        """Test that payback formatting prevents long floats."""
        # Test values that could produce long floats
        test_values = [3.333333, 10/3, 2.999999, 4.500001]

        for val in test_values:
            formatted = f"{float(val):.1f}"
            # Should have at most 1 decimal place
            assert len(formatted.split(".")[-1]) <= 1, f"Long float detected: {formatted}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
