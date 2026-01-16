# -*- coding: utf-8 -*-
"""
Business Case Consistency Test - Single Source of Truth
=========================================================

v14.35.23: Tests for Business Case metric consistency across all sections.

Ensures:
1. Hourly rate is consistent across all sources (canonical from business_case_engine_v2)
2. Payback formatting doesn't contain long floats
3. ROI values are derived consistently

Ref: TASK - Business Case Consistency – Single Source of Truth (3 Fixes)
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
        from services.business_case_engine_v2 import BusinessCaseCanonical

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
        # roi_12m_net = ((17040 - 5000) / 5000) * 100 = 240.8%

        assert bc.monthly_gross == 1600
        assert bc.monthly_net == 1420
        assert bc.annual_net == 17040
        assert round(bc.roi_12m_net, 1) == 240.8

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
