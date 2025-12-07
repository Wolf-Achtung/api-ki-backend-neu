#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprint G9.2: E2E Test for AI Act Business Case Modifiers

Tests the complete flow from:
1. Risk classification (high-risk/limited/minimal)
2. AI Act modifier calculation
3. Business case adjustment
4. Metrics tracking via monitoring layer
5. Final report section values

Version: 1.0.0 (Sprint G9)
"""

import pytest
from typing import Dict, Any
from copy import deepcopy


# =============================================================================
# FIXTURE: Sample Business Case & AI Act Data
# =============================================================================

@pytest.fixture
def sample_business_case() -> Dict[str, Any]:
    """Standard business case for testing."""
    return {
        "CAPEX_REALISTISCH_EUR": 10000,
        "OPEX_REALISTISCH_EUR": 500,
        "EINSPARUNG_MONAT_EUR": 2000,
        "PAYBACK_MONTHS": 5.0,
        "ROI_12M": 140.0,
        "ROI_12M_EUR": 14000,
        "BUSINESS_CASE_TABLE_HTML": "<table><tr><td>Original</td></tr></table>",
    }


@pytest.fixture
def high_risk_modifiers() -> Dict[str, float]:
    """Modifiers for high-risk classification."""
    return {
        "CAPEX_MODIFIER": 1.25,
        "OPEX_MODIFIER": 1.15,
    }


@pytest.fixture
def limited_risk_modifiers() -> Dict[str, float]:
    """Modifiers for limited risk classification."""
    return {
        "CAPEX_MODIFIER": 1.10,
        "OPEX_MODIFIER": 1.05,
    }


@pytest.fixture
def minimal_risk_modifiers() -> Dict[str, float]:
    """Modifiers for minimal risk (no change)."""
    return {
        "CAPEX_MODIFIER": 1.0,
        "OPEX_MODIFIER": 1.0,
    }


# =============================================================================
# G9.2.1: E2E Flow - High Risk Complete Path
# =============================================================================

class TestE2EHighRiskFlow:
    """E2E tests for high-risk classification complete flow."""

    def test_high_risk_complete_flow(
        self, sample_business_case: Dict[str, Any], high_risk_modifiers: Dict[str, float]
    ):
        """Test complete high-risk flow from classification to final values."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case
        from services.monitoring_ai_act import track_bc_modification, AIActBCMetrics

        # Setup sections dict (simulating gpt_analyze.py sections)
        sections: Dict[str, Any] = {}
        original_bc = deepcopy(sample_business_case)

        # Step 1: Apply modifiers (as in gpt_analyze.py)
        adjusted_bc = apply_ai_act_modifiers_to_business_case(
            original_bc,
            high_risk_modifiers,
            "high-risk"
        )

        # Step 2: Update sections
        sections.update(adjusted_bc)

        # Step 3: Track with monitoring layer
        metrics = track_bc_modification(
            sections=sections,
            original_bc=original_bc,
            adjusted_bc=adjusted_bc,
            risk_level="high-risk",
            modifiers=high_risk_modifiers
        )

        # Verify CAPEX adjustment: 10000 * 1.25 = 12500
        assert sections["CAPEX_REALISTISCH_EUR"] == 12500
        assert adjusted_bc["CAPEX_REALISTISCH_EUR"] == 12500

        # Verify OPEX adjustment: 500 * 1.15 = 575
        assert sections["OPEX_REALISTISCH_EUR"] == 575
        assert adjusted_bc["OPEX_REALISTISCH_EUR"] == 575

        # Verify AI Act tracking keys
        assert sections["AI_ACT_BC_APPLIED"] is True
        assert sections["AI_ACT_BC_CAPEX_FACTOR"] == 1.25
        assert sections["AI_ACT_BC_OPEX_FACTOR"] == 1.15
        assert sections["AI_ACT_BC_PAYBACK_DELTA"] == 2.0

        # Verify monitoring metrics stored
        assert "_ai_act_bc_metrics" in sections
        stored_metrics = sections["_ai_act_bc_metrics"]
        assert stored_metrics["risk_level"] == "high-risk"
        assert stored_metrics["capex_before"] == 10000
        assert stored_metrics["capex_after"] == 12500
        assert stored_metrics["modifiers_applied"] is True

        # Verify metrics object
        assert isinstance(metrics, AIActBCMetrics)
        assert metrics.capex_delta_pct == pytest.approx(25.0, rel=0.01)
        assert metrics.opex_delta_pct == pytest.approx(15.0, rel=0.01)

    def test_high_risk_payback_includes_delta(
        self, sample_business_case: Dict[str, Any], high_risk_modifiers: Dict[str, float]
    ):
        """High-risk should add 2 months to payback calculation."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case

        original_payback = sample_business_case["PAYBACK_MONTHS"]

        adjusted = apply_ai_act_modifiers_to_business_case(
            sample_business_case,
            high_risk_modifiers,
            "high-risk"
        )

        # Payback should increase due to:
        # 1. Higher CAPEX (numerator increases)
        # 2. Higher OPEX (monthly benefit decreases)
        # 3. +2 months delta for high-risk compliance
        assert adjusted["PAYBACK_MONTHS"] > original_payback
        assert adjusted["AI_ACT_BC_PAYBACK_DELTA"] == 2.0

    def test_high_risk_table_html_updated(
        self, sample_business_case: Dict[str, Any], high_risk_modifiers: Dict[str, float]
    ):
        """Table HTML should contain AI Act compliance note."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case

        adjusted = apply_ai_act_modifiers_to_business_case(
            sample_business_case,
            high_risk_modifiers,
            "high-risk"
        )

        table_html = adjusted["BUSINESS_CASE_TABLE_HTML"]
        assert "AI Act" in table_html or "Compliance" in table_html
        assert "12.500" in table_html or "12500" in table_html  # Adjusted CAPEX


# =============================================================================
# G9.2.2: E2E Flow - Limited Risk Complete Path
# =============================================================================

class TestE2ELimitedRiskFlow:
    """E2E tests for limited risk classification."""

    def test_limited_risk_complete_flow(
        self, sample_business_case: Dict[str, Any], limited_risk_modifiers: Dict[str, float]
    ):
        """Test complete limited risk flow."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case
        from services.monitoring_ai_act import track_bc_modification

        sections: Dict[str, Any] = {}
        original_bc = deepcopy(sample_business_case)

        adjusted_bc = apply_ai_act_modifiers_to_business_case(
            original_bc,
            limited_risk_modifiers,
            "limited"
        )

        sections.update(adjusted_bc)

        metrics = track_bc_modification(
            sections=sections,
            original_bc=original_bc,
            adjusted_bc=adjusted_bc,
            risk_level="limited",
            modifiers=limited_risk_modifiers
        )

        # Verify CAPEX adjustment: 10000 * 1.10 = 11000
        assert sections["CAPEX_REALISTISCH_EUR"] == 11000

        # Verify OPEX adjustment: 500 * 1.05 = 525
        assert sections["OPEX_REALISTISCH_EUR"] == 525

        # Verify payback delta for limited
        assert sections["AI_ACT_BC_PAYBACK_DELTA"] == 0.5

        # Verify metrics
        assert metrics.risk_level == "limited"
        assert metrics.capex_delta_pct == pytest.approx(10.0, rel=0.01)


# =============================================================================
# G9.2.3: E2E Flow - Minimal Risk (No Change)
# =============================================================================

class TestE2EMinimalRiskFlow:
    """E2E tests for minimal risk (no modifications)."""

    def test_minimal_risk_no_changes(
        self, sample_business_case: Dict[str, Any], minimal_risk_modifiers: Dict[str, float]
    ):
        """Minimal risk should not modify values."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case
        from services.monitoring_ai_act import track_bc_modification

        sections: Dict[str, Any] = {}
        original_bc = deepcopy(sample_business_case)

        adjusted_bc = apply_ai_act_modifiers_to_business_case(
            original_bc,
            minimal_risk_modifiers,
            "minimal"
        )

        sections.update(adjusted_bc)

        metrics = track_bc_modification(
            sections=sections,
            original_bc=original_bc,
            adjusted_bc=adjusted_bc,
            risk_level="minimal",
            modifiers=minimal_risk_modifiers
        )

        # Values should remain unchanged
        assert sections["CAPEX_REALISTISCH_EUR"] == 10000
        assert sections["OPEX_REALISTISCH_EUR"] == 500
        assert sections["AI_ACT_BC_PAYBACK_DELTA"] == 0.0

        # Metrics should show no modifiers applied
        assert metrics.modifiers_applied is False
        assert metrics.capex_delta_pct == 0.0


# =============================================================================
# G9.2.4: Monitoring Layer Tests
# =============================================================================

class TestMonitoringLayerIntegration:
    """Test monitoring layer functionality."""

    def test_metrics_stored_in_sections(
        self, sample_business_case: Dict[str, Any], high_risk_modifiers: Dict[str, float]
    ):
        """Metrics should be stored in sections['_ai_act_bc_metrics']."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case
        from services.monitoring_ai_act import track_bc_modification, get_bc_metrics_summary

        sections: Dict[str, Any] = {}
        original_bc = deepcopy(sample_business_case)

        adjusted_bc = apply_ai_act_modifiers_to_business_case(
            original_bc, high_risk_modifiers, "high-risk"
        )
        sections.update(adjusted_bc)

        track_bc_modification(
            sections=sections,
            original_bc=original_bc,
            adjusted_bc=adjusted_bc,
            risk_level="high-risk",
            modifiers=high_risk_modifiers
        )

        # Retrieve stored metrics
        stored = get_bc_metrics_summary(sections)
        assert stored is not None
        assert stored["risk_level"] == "high-risk"
        assert stored["capex_before"] == 10000
        assert stored["capex_after"] == 12500
        assert "timestamp" in stored

    def test_anomaly_detection_negative_values(self):
        """Anomaly detection should flag negative values."""
        from services.monitoring_ai_act import calculate_bc_metrics

        original = {"CAPEX_REALISTISCH_EUR": 100, "OPEX_REALISTISCH_EUR": 50}
        adjusted = {"CAPEX_REALISTISCH_EUR": -100, "OPEX_REALISTISCH_EUR": 50}
        modifiers = {"CAPEX_MODIFIER": 1.0, "OPEX_MODIFIER": 1.0}

        metrics = calculate_bc_metrics(original, adjusted, "minimal", modifiers)

        assert metrics.is_anomaly is True
        assert "Negative CAPEX" in metrics.anomaly_reason
        assert len(metrics.warnings) > 0

    def test_risk_level_normalization(self):
        """Risk level should be normalized correctly."""
        from services.monitoring_ai_act import normalize_risk_level

        assert normalize_risk_level("high-risk") == "high-risk"
        assert normalize_risk_level("HIGH-RISK") == "high-risk"
        assert normalize_risk_level("high") == "high-risk"
        assert normalize_risk_level("hoch") == "high-risk"
        assert normalize_risk_level("limited") == "limited"
        assert normalize_risk_level("begrenzt") == "limited"
        assert normalize_risk_level("minimal") == "minimal"
        assert normalize_risk_level("gering") == "minimal"
        assert normalize_risk_level("none") == "none"
        assert normalize_risk_level("unknown_value") == "minimal"

    def test_expected_modifiers_lookup(self):
        """Expected modifiers should match risk level."""
        from services.monitoring_ai_act import get_expected_modifiers

        high_risk = get_expected_modifiers("high-risk")
        assert high_risk["CAPEX_MODIFIER"] == 1.25
        assert high_risk["OPEX_MODIFIER"] == 1.15

        limited = get_expected_modifiers("limited")
        assert limited["CAPEX_MODIFIER"] == 1.10
        assert limited["OPEX_MODIFIER"] == 1.05

        minimal = get_expected_modifiers("minimal")
        assert minimal["CAPEX_MODIFIER"] == 1.0
        assert minimal["OPEX_MODIFIER"] == 1.0


# =============================================================================
# G9.2.5: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases in BC modifier flow."""

    def test_zero_capex_handling(self):
        """Zero CAPEX should not cause division errors."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case
        from services.monitoring_ai_act import calculate_bc_metrics

        bc = {
            "CAPEX_REALISTISCH_EUR": 0,
            "OPEX_REALISTISCH_EUR": 100,
            "EINSPARUNG_MONAT_EUR": 500,
            "PAYBACK_MONTHS": 0,
            "ROI_12M": None,
            "BUSINESS_CASE_TABLE_HTML": "",
        }

        modifiers = {"CAPEX_MODIFIER": 1.25, "OPEX_MODIFIER": 1.15}

        adjusted = apply_ai_act_modifiers_to_business_case(bc, modifiers, "high-risk")

        assert adjusted["CAPEX_REALISTISCH_EUR"] == 0  # 0 * 1.25 = 0
        assert adjusted["OPEX_REALISTISCH_EUR"] == 115  # 100 * 1.15

        # Metrics should handle zero gracefully
        metrics = calculate_bc_metrics(bc, adjusted, "high-risk", modifiers)
        assert metrics.capex_delta_pct == 0.0  # No division error

    def test_negative_monthly_benefit(self):
        """Negative monthly benefit should handle payback calculation."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case

        bc = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 3000,  # OPEX > Einsparung
            "EINSPARUNG_MONAT_EUR": 2000,
            "PAYBACK_MONTHS": None,
            "ROI_12M": -20.0,
            "BUSINESS_CASE_TABLE_HTML": "",
        }

        modifiers = {"CAPEX_MODIFIER": 1.25, "OPEX_MODIFIER": 1.15}

        adjusted = apply_ai_act_modifiers_to_business_case(bc, modifiers, "high-risk")

        # With OPEX (3450) > Einsparung (2000), payback should be None
        assert adjusted["PAYBACK_MONTHS"] is None

    def test_very_high_modifiers(self):
        """Very high modifiers should trigger warnings."""
        from services.monitoring_ai_act import calculate_bc_metrics

        original = {"CAPEX_REALISTISCH_EUR": 10000, "OPEX_REALISTISCH_EUR": 500}
        adjusted = {"CAPEX_REALISTISCH_EUR": 20000, "OPEX_REALISTISCH_EUR": 1000}
        modifiers = {"CAPEX_MODIFIER": 2.0, "OPEX_MODIFIER": 2.0}

        metrics = calculate_bc_metrics(original, adjusted, "high-risk", modifiers)

        assert len(metrics.warnings) > 0
        assert any("High CAPEX modifier" in w for w in metrics.warnings)


# =============================================================================
# G9.2.6: Full Integration Test
# =============================================================================

class TestFullIntegration:
    """Full integration test simulating gpt_analyze.py flow."""

    def test_full_gpt_analyze_simulation(self):
        """Simulate the full gpt_analyze.py BC modifier flow."""
        from services.extra_sections import apply_ai_act_modifiers_to_business_case
        from services.monitoring_ai_act import track_bc_modification
        from services.config_validation import validate_business_case_with_ai_act

        # Initial sections (as if populated by earlier gpt_analyze steps)
        sections = {
            "AI_ACT_RISK_LEVEL": "high-risk",
            "CAPEX_MODIFIER": 1.25,
            "OPEX_MODIFIER": 1.15,
            "CAPEX_REALISTISCH_EUR": 15000,
            "OPEX_REALISTISCH_EUR": 800,
            "EINSPARUNG_MONAT_EUR": 3000,
            "PAYBACK_MONTHS": 5.5,
            "ROI_12M": 120.0,
            "BUSINESS_CASE_TABLE_HTML": "<table>Original</table>",
        }

        # Extract modifiers
        risk_level = sections.get("AI_ACT_RISK_LEVEL", "minimal")
        ai_act_bc_modifiers = {
            "CAPEX_MODIFIER": sections.get("CAPEX_MODIFIER", 1.0),
            "OPEX_MODIFIER": sections.get("OPEX_MODIFIER", 1.0),
        }

        # Build current BC dict
        current_bc = {
            "CAPEX_REALISTISCH_EUR": sections.get("CAPEX_REALISTISCH_EUR", 0),
            "OPEX_REALISTISCH_EUR": sections.get("OPEX_REALISTISCH_EUR", 0),
            "EINSPARUNG_MONAT_EUR": sections.get("EINSPARUNG_MONAT_EUR", 0),
            "PAYBACK_MONTHS": sections.get("PAYBACK_MONTHS", 0),
            "ROI_12M": sections.get("ROI_12M", 0),
            "BUSINESS_CASE_TABLE_HTML": sections.get("BUSINESS_CASE_TABLE_HTML", ""),
        }

        # Apply modifiers
        adjusted_bc = apply_ai_act_modifiers_to_business_case(
            current_bc,
            ai_act_bc_modifiers,
            risk_level
        )

        # Update sections
        sections.update(adjusted_bc)

        # Track with monitoring
        metrics = track_bc_modification(
            sections=sections,
            original_bc=current_bc,
            adjusted_bc=adjusted_bc,
            risk_level=risk_level,
            modifiers=ai_act_bc_modifiers
        )

        # Validate
        warnings = validate_business_case_with_ai_act(adjusted_bc, risk_level)

        # Assertions
        assert sections["CAPEX_REALISTISCH_EUR"] == 18750  # 15000 * 1.25
        assert sections["OPEX_REALISTISCH_EUR"] == 920     # 800 * 1.15
        assert sections["AI_ACT_BC_APPLIED"] is True
        assert "_ai_act_bc_metrics" in sections
        assert metrics.risk_level == "high-risk"
        assert metrics.modifiers_applied is True

        # No validation warnings expected for these reasonable values
        # (ROI might trigger warning if > 300)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
