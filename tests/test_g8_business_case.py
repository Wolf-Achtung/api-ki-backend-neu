#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprint G8 Tests: Business Case Modifiers & Config Validation

Tests for:
- G8.1: CAPEX_MODIFIER integration
- G8.2: ENV externalization
- G8.3: Centralized min-lengths

Version: 1.0.0 (Sprint G8)
"""

import pytest
import os
from typing import Dict, Any


class TestG81BusinessCaseModifiers:
    """G8.1: Test AI Act Business Case Modifiers."""

    def test_high_risk_capex_modifier(self):
        """High-risk should increase CAPEX by 25%."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case

        original_bc = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "PAYBACK_MONTHS": 5.0,
            "ROI_12M": 120.0,
            "BUSINESS_CASE_TABLE_HTML": "<table></table>",
        }

        modifiers = {
            "CAPEX_MODIFIER": 1.25,  # +25%
            "OPEX_MODIFIER": 1.15,   # +15%
        }

        adjusted = apply_ai_act_modifiers_to_business_case(
            original_bc, modifiers, "high-risk"
        )

        assert adjusted["CAPEX_REALISTISCH_EUR"] == 12500  # 10000 * 1.25
        assert adjusted["OPEX_REALISTISCH_EUR"] == 575     # 500 * 1.15 = 575
        assert adjusted["AI_ACT_BC_APPLIED"] is True
        assert adjusted["AI_ACT_BC_CAPEX_FACTOR"] == 1.25
        assert adjusted["AI_ACT_BC_OPEX_FACTOR"] == 1.15
        assert adjusted["AI_ACT_BC_PAYBACK_DELTA"] == 2.0  # high-risk adds 2 months

    def test_limited_risk_capex_modifier(self):
        """Limited risk should increase CAPEX by 10%."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case

        original_bc = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "PAYBACK_MONTHS": 5.0,
            "ROI_12M": 120.0,
            "BUSINESS_CASE_TABLE_HTML": "<table></table>",
        }

        modifiers = {
            "CAPEX_MODIFIER": 1.10,  # +10%
            "OPEX_MODIFIER": 1.05,   # +5%
        }

        adjusted = apply_ai_act_modifiers_to_business_case(
            original_bc, modifiers, "limited"
        )

        assert adjusted["CAPEX_REALISTISCH_EUR"] == 11000  # 10000 * 1.10
        assert adjusted["OPEX_REALISTISCH_EUR"] == 525     # 500 * 1.05
        assert adjusted["AI_ACT_BC_PAYBACK_DELTA"] == 0.5  # limited adds 0.5 months

    def test_minimal_risk_no_modifier(self):
        """Minimal risk should not modify CAPEX/OPEX."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case

        original_bc = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "PAYBACK_MONTHS": 5.0,
            "ROI_12M": 120.0,
            "BUSINESS_CASE_TABLE_HTML": "<table></table>",
        }

        modifiers = {
            "CAPEX_MODIFIER": 1.0,  # No change
            "OPEX_MODIFIER": 1.0,   # No change
        }

        adjusted = apply_ai_act_modifiers_to_business_case(
            original_bc, modifiers, "minimal"
        )

        assert adjusted["CAPEX_REALISTISCH_EUR"] == 10000
        assert adjusted["OPEX_REALISTISCH_EUR"] == 500
        assert adjusted["AI_ACT_BC_PAYBACK_DELTA"] == 0.0

    def test_adjusted_table_contains_compliance_note(self):
        """High-risk adjusted table should contain compliance note."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case

        original_bc = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "PAYBACK_MONTHS": 5.0,
            "ROI_12M": 120.0,
            "BUSINESS_CASE_TABLE_HTML": "<table></table>",
        }

        modifiers = {"CAPEX_MODIFIER": 1.25, "OPEX_MODIFIER": 1.15}

        adjusted = apply_ai_act_modifiers_to_business_case(
            original_bc, modifiers, "high-risk"
        )

        table_html = adjusted["BUSINESS_CASE_TABLE_HTML"]
        assert "AI Act Compliance" in table_html
        assert "CAPEX +25%" in table_html
        assert "OPEX +15%" in table_html


class TestG82EnvExternalization:
    """G8.2: Test ENV externalization."""

    def test_validation_config_loads_defaults(self):
        """ValidationConfig should load with sensible defaults."""
        from services.config_validation import ValidationConfig

        assert ValidationConfig.HARD_STOP_ON_SIZE_MISMATCH in (True, False)
        assert ValidationConfig.MAX_REDUNDANCY_WARNINGS >= 1
        # Note: AI_ACT_MIN_REASONING_WORDS may be overridden by other tests via ENV
        # Default is 60, but test_g12_ai_act_validator sets it to 10 for validation tests
        assert ValidationConfig.AI_ACT_MIN_REASONING_WORDS >= 1
        assert ValidationConfig.REDUNDANCY_WORD_THRESHOLD >= 10

    def test_get_bool_env_helper(self):
        """Test get_bool_env helper function."""
        from services.config_validation import get_bool_env

        # Test with no ENV set (uses default)
        assert get_bool_env("TEST_NONEXISTENT_VAR", True) is True
        assert get_bool_env("TEST_NONEXISTENT_VAR", False) is False

        # Test with ENV set
        os.environ["TEST_G8_BOOL"] = "1"
        assert get_bool_env("TEST_G8_BOOL", False) is True

        os.environ["TEST_G8_BOOL"] = "true"
        assert get_bool_env("TEST_G8_BOOL", False) is True

        os.environ["TEST_G8_BOOL"] = "0"
        assert get_bool_env("TEST_G8_BOOL", True) is False

        # Cleanup
        del os.environ["TEST_G8_BOOL"]

    def test_get_int_env_helper(self):
        """Test get_int_env helper function."""
        from services.config_validation import get_int_env

        # Test with no ENV set
        assert get_int_env("TEST_NONEXISTENT_INT", 42) == 42

        # Test with valid int
        os.environ["TEST_G8_INT"] = "100"
        assert get_int_env("TEST_G8_INT", 42) == 100

        # Test with invalid int (should return default)
        os.environ["TEST_G8_INT"] = "not_a_number"
        assert get_int_env("TEST_G8_INT", 42) == 42

        # Cleanup
        del os.environ["TEST_G8_INT"]


class TestG83CentralizedMinLengths:
    """G8.3: Test centralized min-length configuration."""

    def test_get_min_words_solo(self):
        """Test min words retrieval for Solo size."""
        from services.config_validation import get_min_words

        assert get_min_words("Solo-Selbstständig", "executive_summary") == 150
        assert get_min_words("solo", "roadmap_12m") == 500
        assert get_min_words("Freiberufler", "quick_wins") == 60

    def test_get_min_words_team(self):
        """Test min words retrieval for Team size."""
        from services.config_validation import get_min_words

        assert get_min_words("Team (2-10 MA)", "executive_summary") == 180
        assert get_min_words("team", "roadmap_12m") == 600
        assert get_min_words("klein", "quick_wins") == 90

    def test_get_min_words_kmu(self):
        """Test min words retrieval for KMU size."""
        from services.config_validation import get_min_words

        assert get_min_words("KMU (11-50 MA)", "executive_summary") == 200
        assert get_min_words("kmu", "roadmap_12m") == 700
        assert get_min_words("Mittelstand", "quick_wins") == 120

    def test_get_all_min_words_for_size(self):
        """Test retrieving all min words for a size."""
        from services.config_validation import get_all_min_words_for_size

        solo_mins = get_all_min_words_for_size("solo")
        assert "executive_summary" in solo_mins
        assert "roadmap_12m" in solo_mins
        assert solo_mins["executive_summary"] == 150

        kmu_mins = get_all_min_words_for_size("kmu")
        assert kmu_mins["executive_summary"] == 200


class TestG8BusinessCaseValidation:
    """Test business case validation with AI Act modifiers."""

    def test_validate_positive_values(self):
        """Validation should pass for positive values."""
        from services.config_validation import validate_business_case_with_ai_act

        bc = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "PAYBACK_MONTHS": 6.0,
            "ROI_12M": 100.0,
        }

        warnings = validate_business_case_with_ai_act(bc, "high-risk")
        assert len(warnings) == 0

    def test_validate_warns_on_negative_capex(self):
        """Validation should warn on negative CAPEX."""
        from services.config_validation import validate_business_case_with_ai_act

        bc = {
            "CAPEX_REALISTISCH_EUR": -1000,
            "OPEX_REALISTISCH_EUR": 500,
            "PAYBACK_MONTHS": 6.0,
            "ROI_12M": 100.0,
        }

        warnings = validate_business_case_with_ai_act(bc, "high-risk")
        assert len(warnings) > 0
        assert any("Negative CAPEX" in w for w in warnings)

    def test_validate_warns_on_high_roi_with_high_risk(self):
        """Very high ROI with high-risk classification should trigger warning."""
        from services.config_validation import validate_business_case_with_ai_act

        bc = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "PAYBACK_MONTHS": 6.0,
            "ROI_12M": 500.0,  # Very high ROI
        }

        warnings = validate_business_case_with_ai_act(bc, "high-risk")
        assert len(warnings) > 0
        assert any("High ROI" in w for w in warnings)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
