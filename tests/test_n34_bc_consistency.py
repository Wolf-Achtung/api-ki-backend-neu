# -*- coding: utf-8 -*-
"""
SPRINT N3.4: Tests for Business Case Consistency Kernel v4.

Tests scenario normalization and ROI inversion fixes.
"""
import pytest


class TestNormalizeScenarioOrder:
    """Test the normalize_scenario_order function."""

    def test_function_exists(self):
        """normalize_scenario_order should exist."""
        from services.business_case_engine_v2 import normalize_scenario_order

        assert callable(normalize_scenario_order)

    def test_normalizes_realistic_below_conservative(self):
        """If conservative > realistic, conservative should be reduced to realistic * 0.9."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 200.0},
            "realistic": {"roi_12m": 80.0},  # Below conservative!
            "conservative": {"roi_12m": 100.0},
        }

        result = normalize_scenario_order(scenarios)

        # Conservative should now be 80 * 0.9 = 72.0
        assert result["conservative"]["roi_12m"] == 72.0
        assert result["realistic"]["roi_12m"] == 80.0  # Realistic unchanged
        assert result["_bc_consistency_normalized"] is True

    def test_normalizes_realistic_above_optimistic(self):
        """If realistic > optimistic, realistic should be set to optimistic * 0.9."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 150.0},
            "realistic": {"roi_12m": 180.0},  # Above optimistic!
            "conservative": {"roi_12m": 100.0},
        }

        result = normalize_scenario_order(scenarios)

        # Realistic should now be 150 * 0.9 = 135
        assert result["realistic"]["roi_12m"] == 135.0
        assert result["_bc_consistency_normalized"] is True

    def test_no_change_when_ordered_correctly(self):
        """Should not modify correctly ordered scenarios."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 200.0},
            "realistic": {"roi_12m": 150.0},
            "conservative": {"roi_12m": 100.0},
        }

        result = normalize_scenario_order(scenarios)

        # Values should remain unchanged
        assert result["optimistic"]["roi_12m"] == 200.0
        assert result["realistic"]["roi_12m"] == 150.0
        assert result["conservative"]["roi_12m"] == 100.0
        assert result["_bc_consistency_normalized"] is True

    def test_sets_flag_in_sections(self):
        """Should set _bc_consistency_normalized flag in sections dict."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 200.0},
            "realistic": {"roi_12m": 80.0},
            "conservative": {"roi_12m": 100.0},
        }
        sections = {}

        normalize_scenario_order(scenarios, sections)

        assert sections.get("_bc_consistency_normalized") is True
        assert sections.get("_bc_healed") is True

    def test_rounds_roi_values(self):
        """Should round ROI values to 1 decimal."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 200.123456},
            "realistic": {"roi_12m": 150.987654},
            "conservative": {"roi_12m": 100.555555},
        }

        result = normalize_scenario_order(scenarios)

        assert result["optimistic"]["roi_12m"] == 200.1
        assert result["realistic"]["roi_12m"] == 151.0
        assert result["conservative"]["roi_12m"] == 100.6

    def test_handles_empty_scenarios(self):
        """Should handle empty or None scenarios gracefully."""
        from services.business_case_engine_v2 import normalize_scenario_order

        result_empty = normalize_scenario_order({})
        assert result_empty == {}

        result_none = normalize_scenario_order(None)
        assert result_none is None


class TestEnsureScenarioConsistency:
    """Test the ensure_scenario_consistency function."""

    def test_function_exists(self):
        """ensure_scenario_consistency should exist."""
        from services.business_case_engine_v2 import ensure_scenario_consistency

        assert callable(ensure_scenario_consistency)

    def test_heals_and_normalizes(self):
        """Should heal and normalize business case scenarios."""
        from services.business_case_engine_v2 import ensure_scenario_consistency

        business_case = {
            "scenarios": [
                {"name": "optimistic", "roi_12m": 200.0, "payback_months": 6.0,
                 "monthly_savings": 1000.0, "annual_savings": 12000.0, "investment_total": 5000.0},
                {"name": "realistic", "roi_12m": 80.0, "payback_months": 12.0,
                 "monthly_savings": 500.0, "annual_savings": 6000.0, "investment_total": 5000.0},
                {"name": "conservative", "roi_12m": 100.0, "payback_months": 10.0,
                 "monthly_savings": 600.0, "annual_savings": 7200.0, "investment_total": 5000.0},
            ]
        }
        sections = {}

        result = ensure_scenario_consistency(business_case, sections)

        assert result.get("_bc_healed") is True
        assert result.get("_bc_consistency_normalized") is True
        assert sections.get("_bc_healed") is True

    def test_handles_empty_business_case(self):
        """Should handle empty business case gracefully."""
        from services.business_case_engine_v2 import ensure_scenario_consistency

        result = ensure_scenario_consistency({})
        assert result == {}


class TestROIInversionScenarios:
    """Test specific ROI inversion edge cases."""

    def test_extreme_inversion(self):
        """Should handle extreme ROI inversions."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 50.0},  # Low!
            "realistic": {"roi_12m": 200.0},   # Very high - wrong!
            "conservative": {"roi_12m": 100.0},
        }

        result = normalize_scenario_order(scenarios)

        # Realistic should be capped to optimistic * 0.9 = 45
        assert result["realistic"]["roi_12m"] == 45.0

    def test_all_same_roi(self):
        """Should handle scenarios with identical ROI."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 100.0},
            "realistic": {"roi_12m": 100.0},
            "conservative": {"roi_12m": 100.0},
        }

        result = normalize_scenario_order(scenarios)

        # Should remain unchanged
        assert result["optimistic"]["roi_12m"] == 100.0
        assert result["realistic"]["roi_12m"] == 100.0
        assert result["conservative"]["roi_12m"] == 100.0

    def test_negative_roi(self):
        """Should handle negative ROI scenarios."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 50.0},
            "realistic": {"roi_12m": -20.0},  # Negative but OK
            "conservative": {"roi_12m": -50.0},
        }

        result = normalize_scenario_order(scenarios)

        # realistic > conservative so should be OK
        # realistic < optimistic so should be OK
        assert result["realistic"]["roi_12m"] == -20.0


class TestFloatArtifactRemoval:
    """Test removal of floating point artifacts."""

    def test_removes_excess_decimals(self):
        """Should round to appropriate decimal places."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {
                "roi_12m": 150.123456789,
                "payback_months": 6.7891234,
                "monthly_savings": 1234.56789,
                "annual_savings": 14815.4321,
            },
            "realistic": {"roi_12m": 120.0},
            "conservative": {"roi_12m": 100.0},
        }

        result = normalize_scenario_order(scenarios)

        # ROI and payback: 1 decimal
        assert result["optimistic"]["roi_12m"] == 150.1
        assert result["optimistic"]["payback_months"] == 6.8

        # Savings: 2 decimals
        assert result["optimistic"]["monthly_savings"] == 1234.57
        assert result["optimistic"]["annual_savings"] == 14815.43


class TestG22Integration:
    """Test that normalized scenarios don't trigger G22 warnings."""

    def test_normalized_scenarios_skip_bc001(self):
        """G22 BC_001 should skip when _bc_consistency_normalized is True."""
        from services.business_case_engine_v2 import normalize_scenario_order

        scenarios = {
            "optimistic": {"roi_12m": 200.0},
            "realistic": {"roi_12m": 80.0},
            "conservative": {"roi_12m": 100.0},
        }
        sections = {}

        normalize_scenario_order(scenarios, sections)

        # Flag should be set
        assert sections.get("_bc_consistency_normalized") is True

        # This flag should prevent G22 from flagging
        # (Actual G22 integration test in separate file)
