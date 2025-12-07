#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprint G9: Integration Smoke Test

Quick verification that all G9 components work together.
Run with: python tests/test_g9_integration_smoke.py

Version: 1.0.0 (Sprint G9)
"""


def test_g91_monitoring_module():
    """G9.1: Verify monitoring module loads and works."""
    from services.monitoring_ai_act import (
        AIActBCMetrics,
        track_bc_modification,
        calculate_bc_metrics,
        normalize_risk_level,
        get_expected_modifiers,
    )

    # Test metrics creation
    metrics = AIActBCMetrics(
        risk_level="high-risk",
        capex_before=10000,
        capex_after=12500,
        capex_modifier=1.25,
    )
    assert metrics.risk_level == "high-risk"
    assert metrics.capex_after == 12500

    # Test risk normalization
    assert normalize_risk_level("HIGH-RISK") == "high-risk"
    assert normalize_risk_level("hoch") == "high-risk"
    assert normalize_risk_level("begrenzt") == "limited"

    # Test expected modifiers
    mods = get_expected_modifiers("high-risk")
    assert mods["CAPEX_MODIFIER"] == 1.25
    assert mods["OPEX_MODIFIER"] == 1.15

    print("✅ G9.1: Monitoring module OK")


def test_g92_bc_modifier_e2e():
    """G9.2: Verify BC modifiers work end-to-end."""
    from services.extra_sections import apply_ai_act_modifiers_to_business_case

    bc = {
        "CAPEX_REALISTISCH_EUR": 10000,
        "OPEX_REALISTISCH_EUR": 500,
        "EINSPARUNG_MONAT_EUR": 2000,
        "PAYBACK_MONTHS": 5.0,
        "ROI_12M": 120.0,
        "BUSINESS_CASE_TABLE_HTML": "<table></table>",
    }

    modifiers = {"CAPEX_MODIFIER": 1.25, "OPEX_MODIFIER": 1.15}

    adjusted = apply_ai_act_modifiers_to_business_case(bc, modifiers, "high-risk")

    assert adjusted["CAPEX_REALISTISCH_EUR"] == 12500
    assert adjusted["OPEX_REALISTISCH_EUR"] == 575
    assert adjusted["AI_ACT_BC_APPLIED"] is True
    assert adjusted["AI_ACT_BC_PAYBACK_DELTA"] == 2.0

    print("✅ G9.2: BC Modifier E2E OK")


def test_g94_min_length_unification():
    """G9.4: Verify min-length unification works."""
    from services.config_validation import get_min_words
    from services.prompt_enhancer import get_platin_min_words

    # Central config
    assert get_min_words("solo", "executive_summary") == 150
    assert get_min_words("kmu", "roadmap_12m") == 700

    # Prompt enhancer uses central config
    pe_min = get_platin_min_words("roadmap_12m", "kmu")
    assert pe_min == 700

    print("✅ G9.4: Min-Length Unification OK")


def test_g95_import_chain():
    """G9.5: Verify all imports work."""
    # Core modules
    from services.config_validation import ValidationConfig
    from services.monitoring_ai_act import AIActBCMetrics
    from services.extra_sections import apply_ai_act_modifiers_to_business_case
    from services.prompt_enhancer import get_platin_min_words

    # Verify config loaded
    assert ValidationConfig.AI_ACT_ENABLED in (True, False)
    assert ValidationConfig.MAX_REDUNDANCY_WARNINGS >= 1

    print("✅ G9.5: Import Chain OK")


def run_all():
    """Run all smoke tests."""
    print("=" * 60)
    print("Sprint G9 Integration Smoke Test")
    print("=" * 60)

    test_g91_monitoring_module()
    test_g92_bc_modifier_e2e()
    test_g94_min_length_unification()
    test_g95_import_chain()

    print("=" * 60)
    print("✅ ALL G9 SMOKE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
