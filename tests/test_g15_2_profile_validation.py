# -*- coding: utf-8 -*-
"""
Sprint G15.2 Tests: Profile Sanity & AI-Act Override Validation

Tests for profile validation including:
- AI-Act override validation
- Persona/size consistency
- Funding flow validation
- Word minimum checks

Version: 1.0.0
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import pytest


PROFILES_DIR = Path("data/test_profiles_gold")


# =============================================================================
# TEST G15.2-A: AI-ACT OVERRIDE VALIDATION
# =============================================================================

class TestG152A_AIActOverride:
    """Tests for AI-Act override validation."""

    def test_solo_profile_has_override(self) -> None:
        """Solo profile should have ai_act_override_risk_level."""
        profile_path = PROFILES_DIR / "solo_beratung_ki_assessments.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        assert "ai_act_override_risk_level" in profile
        assert profile["ai_act_override_risk_level"] == "minimal"

    def test_kmu_profile_has_override(self) -> None:
        """KMU profile should have ai_act_override_risk_level."""
        profile_path = PROFILES_DIR / "kmu_france_eu_core_en_gold.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        assert "ai_act_override_risk_level" in profile
        assert profile["ai_act_override_risk_level"] == "limited"

    def test_team_finance_has_high_risk_override(self) -> None:
        """Finance team profile should have high-risk override."""
        profile_path = PROFILES_DIR / "team_finance_insurance_advisory.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        assert "ai_act_override_risk_level" in profile
        assert profile["ai_act_override_risk_level"] == "high-risk"

    def test_finance_branch_triggers_high_risk(self) -> None:
        """Finance branch with regulatory compliance should be high-risk."""
        from scripts.validate_profiles_g15_2 import determine_risk_level

        profile = {
            "answers": {
                "branche": "finanzen",
                "unternehmensgroesse": "team",
                "regulierte_branche": ["finanzen", "versicherung"],
                "ki_einsatz": ["risikoanalyse", "reporting"],
            }
        }

        risk_level, reasons = determine_risk_level(profile)
        assert risk_level == "high-risk"

    def test_solo_beratung_is_minimal(self) -> None:
        """Solo consulting without regulated branch should be minimal."""
        from scripts.validate_profiles_g15_2 import determine_risk_level

        profile = {
            "answers": {
                "branche": "beratung",
                "unternehmensgroesse": "solo",
                "regulierte_branche": ["keine_regulierung"],
                "ki_einsatz": ["dokumentenerstellung"],
            }
        }

        risk_level, reasons = determine_risk_level(profile)
        assert risk_level == "minimal"


# =============================================================================
# TEST G15.2-B: PERSONA CONSISTENCY
# =============================================================================

class TestG152B_PersonaConsistency:
    """Tests for persona/size consistency."""

    def test_solo_persona_check(self) -> None:
        """Solo profile should pass persona check."""
        from scripts.validate_profiles_g15_2 import check_persona_consistency

        profile_path = PROFILES_DIR / "solo_beratung_ki_assessments.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        result = check_persona_consistency(profile)
        assert result.expected_persona == "solo"
        assert result.is_consistent, f"Persona issues: {result.forbidden_terms_found}"

    def test_team_persona_check(self) -> None:
        """Team profile should pass persona check."""
        from scripts.validate_profiles_g15_2 import check_persona_consistency

        profile_path = PROFILES_DIR / "team_finance_insurance_advisory.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        result = check_persona_consistency(profile)
        assert result.expected_persona == "team"
        assert result.is_consistent

    def test_kmu_persona_check(self) -> None:
        """KMU profile should pass persona check."""
        from scripts.validate_profiles_g15_2 import check_persona_consistency

        profile_path = PROFILES_DIR / "kmu_france_eu_core_en_gold.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        result = check_persona_consistency(profile)
        assert result.expected_persona == "kmu"
        assert result.is_consistent


# =============================================================================
# TEST G15.2-C: FUNDING FLOW
# =============================================================================

class TestG152C_FundingFlow:
    """Tests for funding flow validation."""

    def test_german_solo_gets_de_funding(self) -> None:
        """German Solo profile should get DE funding flow."""
        from scripts.validate_profiles_g15_2 import validate_funding_flow

        profile_path = PROFILES_DIR / "solo_beratung_ki_assessments.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        result = validate_funding_flow(profile)
        assert result.expected_flow == "DE"

    def test_french_kmu_gets_eu_core_funding(self) -> None:
        """French KMU (EN) should get EU-Core funding flow."""
        from scripts.validate_profiles_g15_2 import validate_funding_flow

        profile_path = PROFILES_DIR / "kmu_france_eu_core_en_gold.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        result = validate_funding_flow(profile)
        assert result.expected_flow == "EN-EU-Core"

    def test_german_team_gets_de_funding(self) -> None:
        """German Team profile should get DE funding flow."""
        from scripts.validate_profiles_g15_2 import validate_funding_flow

        profile_path = PROFILES_DIR / "team_finance_insurance_advisory.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        result = validate_funding_flow(profile)
        assert result.expected_flow == "DE"


# =============================================================================
# TEST G15.2-D: WORD MINIMUMS
# =============================================================================

class TestG152D_WordMinimums:
    """Tests for word minimum configuration."""

    def test_solo_word_mins_defined(self) -> None:
        """Solo word minimums should be defined."""
        from scripts.validate_profiles_g15_2 import SECTION_MIN_WORDS

        assert "solo" in SECTION_MIN_WORDS
        solo_mins = SECTION_MIN_WORDS["solo"]

        assert solo_mins["roadmap_90d"] == 250
        assert solo_mins["executive_summary"] == 150

    def test_team_word_mins_defined(self) -> None:
        """Team word minimums should be defined."""
        from scripts.validate_profiles_g15_2 import SECTION_MIN_WORDS

        assert "team" in SECTION_MIN_WORDS
        team_mins = SECTION_MIN_WORDS["team"]

        assert team_mins["roadmap_90d"] == 320
        assert team_mins["executive_summary"] == 180

    def test_kmu_word_mins_defined(self) -> None:
        """KMU word minimums should be defined."""
        from scripts.validate_profiles_g15_2 import SECTION_MIN_WORDS

        assert "kmu" in SECTION_MIN_WORDS
        kmu_mins = SECTION_MIN_WORDS["kmu"]

        assert kmu_mins["roadmap_90d"] == 340
        assert kmu_mins["executive_summary"] == 200


# =============================================================================
# TEST G15.2-E: BC MODIFIERS
# =============================================================================

class TestG152E_BCModifiers:
    """Tests for Business Case modifier calculation."""

    def test_high_risk_modifiers(self) -> None:
        """High-risk should have highest modifiers."""
        from scripts.validate_profiles_g15_2 import get_ai_act_modifiers

        mods = get_ai_act_modifiers("high-risk")
        assert mods["capex"] == 1.25
        assert mods["opex"] == 1.15
        assert mods["payback_delta"] == 2.0

    def test_limited_modifiers(self) -> None:
        """Limited risk should have moderate modifiers."""
        from scripts.validate_profiles_g15_2 import get_ai_act_modifiers

        mods = get_ai_act_modifiers("limited")
        assert mods["capex"] == 1.10
        assert mods["opex"] == 1.05
        assert mods["payback_delta"] == 0.5

    def test_minimal_modifiers(self) -> None:
        """Minimal risk should have no modifiers."""
        from scripts.validate_profiles_g15_2 import get_ai_act_modifiers

        mods = get_ai_act_modifiers("minimal")
        assert mods["capex"] == 1.0
        assert mods["opex"] == 1.0
        assert mods["payback_delta"] == 0.0


# =============================================================================
# TEST G15.2: INTEGRATION
# =============================================================================

class TestG152_Integration:
    """Integration tests for profile validation."""

    def test_validation_script_runs(self) -> None:
        """Validation script should run without errors."""
        from scripts.validate_profiles_g15_2 import validate_profile

        profile_path = PROFILES_DIR / "solo_beratung_ki_assessments.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        result = validate_profile(profile)

        assert result.profile_id == "solo_beratung_ki_assessments"
        assert result.ai_act.effective_risk_level == "minimal"
        assert result.funding.expected_flow == "DE"

    def test_optimized_profiles_exist(self) -> None:
        """Optimized profiles should exist."""
        optimized_dir = Path("data/test_profiles_gold_optimized")

        expected_files = [
            "solo_beratung_ki_assessments_optimized.json",
            "kmu_france_eu_core_en_gold_optimized.json",
            "team_finance_insurance_advisory_optimized.json",
        ]

        for filename in expected_files:
            filepath = optimized_dir / filename
            assert filepath.exists(), f"Missing: {filepath}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
