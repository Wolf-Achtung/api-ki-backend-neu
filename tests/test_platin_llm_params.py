"""
Tests für PLATIN+ LLM-Parameter-Konfiguration.

Prüft, dass _llm_params_for() die korrekten PLATIN+-Werte zurückgibt
für kritische Sections (foerderpotenzial, risks, recommendations, etc.).
"""
import pytest
from unittest.mock import patch
import os
import sys

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPlatinCriticalSections:
    """Test PLATIN+ configuration for critical sections."""

    def test_platin_config_exists_for_all_critical_sections(self):
        """Verify PLATIN_CRITICAL_SECTIONS contains all expected sections."""
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        # PDF-SLIMDOWN v2.0: Extended list includes new compact sections
        expected_sections = [
            "foerderpotenzial",
            "risks",
            "recommendations",
            "roadmap_12m",
            "roadmap_90d",      # NEW: PDF-SLIMDOWN
            "quick_wins",       # NEW: PDF-SLIMDOWN
            "gamechanger",
            "unternehmensprofil_markt",
            "transparency_box",      # NEW: PDF-SLIMDOWN
            "technologie_prozesse",  # NEW: PDF-SLIMDOWN
        ]

        for section in expected_sections:
            assert section in PLATIN_CRITICAL_SECTIONS, f"Missing section: {section}"

    def test_platin_config_has_required_fields(self):
        """Verify each PLATIN config has all required fields."""
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        required_fields = ["max_tokens", "temperature", "min_words"]

        for section, config in PLATIN_CRITICAL_SECTIONS.items():
            for field in required_fields:
                assert field in config, f"Section {section} missing field: {field}"

    def test_platin_max_tokens_in_valid_range(self):
        """Verify all PLATIN sections have max_tokens in valid range (PDF-SLIMDOWN v2.0).

        PDF-SLIMDOWN reduced token limits by 20-30% for shorter outputs.
        Valid range: 1500-3200 depending on section complexity.
        """
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        # PDF-SLIMDOWN v2.0: Expected token limits per section
        # G17.R: roadmap_90d increased for Roadmap-Booster sections
        # FIX 178969e: Increased limits to prevent text truncation
        expected_tokens = {
            "foerderpotenzial": 3200,
            "risks": 6000,            # v14.30: Increased for complete Risk-Cards
            "recommendations": 6000,  # v14.30: Increased for complete Recommendation-Cards
            "roadmap_12m": 4000,      # FIX: Increased from 2800 to prevent truncation
            "roadmap_90d": 4000,      # FIX: Increased from 2800 to prevent truncation
            "quick_wins": 4500,       # FIX: Increased from 3500 to prevent truncation
            "gamechanger": 3000,
            "unternehmensprofil_markt": 3000,
            "transparency_box": 1500,
            "technologie_prozesse": 2000,
        }

        for section, config in PLATIN_CRITICAL_SECTIONS.items():
            expected = expected_tokens.get(section)
            if expected:
                assert config["max_tokens"] == expected, (
                    f"Section {section} should have max_tokens={expected}, got {config['max_tokens']}"
                )
            else:
                # Any section not in expected_tokens should still be in valid range
                # v14.30: Extended range to [1500, 7000] for Risk/Recommendation cards
                assert 1500 <= config["max_tokens"] <= 7000, (
                    f"Section {section} max_tokens={config['max_tokens']} not in valid range [1500, 7000]"
                )

    def test_platin_temperature_is_reasonable(self):
        """Verify temperature is in valid range (0.3-0.5)."""
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        for section, config in PLATIN_CRITICAL_SECTIONS.items():
            temp = config["temperature"]
            assert 0.3 <= temp <= 0.5, (
                f"Section {section} temperature {temp} not in range [0.3, 0.5]"
            )

    def test_platin_min_words_thresholds(self):
        """Verify min_words thresholds are set correctly (PDF-SLIMDOWN v2.0).

        PDF-SLIMDOWN reduced min_words to allow for more compact outputs
        while maintaining quality.
        """
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        # PDF-SLIMDOWN v2.0: Reduced min_words for compact outputs
        expected_min_words = {
            "foerderpotenzial": 700,      # Reduced from 900
            "risks": 600,                  # Reduced from 800
            "recommendations": 400,        # Reduced from 800
            "roadmap_12m": 350,           # Reduced from 900
            "roadmap_90d": 320,           # G17.R: Increased from 250 for Booster sections
            "quick_wins": 150,            # NEW
            "gamechanger": 500,           # Reduced from 700
            "unternehmensprofil_markt": 400,  # Reduced from 500
            "transparency_box": 150,      # NEW
            "technologie_prozesse": 200,  # NEW
        }

        for section, expected in expected_min_words.items():
            config = PLATIN_CRITICAL_SECTIONS.get(section)
            assert config is not None, f"Missing section: {section}"
            assert config["min_words"] == expected, (
                f"Section {section} min_words should be {expected}, got {config['min_words']}"
            )


class TestGetPlatinConfig:
    """Test get_platin_config() helper function."""

    def test_get_platin_config_returns_config_for_critical_section(self):
        """Verify get_platin_config returns config for critical sections (PDF-SLIMDOWN v2.0)."""
        from services.prompt_enhancer import get_platin_config

        config = get_platin_config("foerderpotenzial")
        assert config is not None
        assert config["max_tokens"] == 3200  # PDF-SLIMDOWN: reduced from 4096
        assert config["temperature"] == 0.4
        assert config["min_words"] == 700    # PDF-SLIMDOWN: reduced from 900

    def test_get_platin_config_returns_none_for_non_critical_section(self):
        """Verify get_platin_config returns None for non-critical sections."""
        from services.prompt_enhancer import get_platin_config

        config = get_platin_config("executive_summary")
        assert config is None

        # PDF-SLIMDOWN v2.0: quick_wins is now a critical section
        config = get_platin_config("business_case")
        assert config is None

    def test_get_platin_config_is_case_insensitive(self):
        """Verify get_platin_config is case-insensitive."""
        from services.prompt_enhancer import get_platin_config

        config1 = get_platin_config("FOERDERPOTENZIAL")
        config2 = get_platin_config("Foerderpotenzial")
        config3 = get_platin_config("foerderpotenzial")

        assert config1 == config2 == config3


class TestIsPlatinCriticalSection:
    """Test is_platin_critical_section() helper function."""

    def test_is_platin_critical_section_true(self):
        """Verify is_platin_critical_section returns True for critical sections."""
        from services.prompt_enhancer import is_platin_critical_section

        critical_sections = [
            "foerderpotenzial",
            "risks",
            "recommendations",
            "roadmap_12m",
            "gamechanger",
        ]

        for section in critical_sections:
            assert is_platin_critical_section(section), f"Should be critical: {section}"

    def test_is_platin_critical_section_false(self):
        """Verify is_platin_critical_section returns False for non-critical sections."""
        from services.prompt_enhancer import is_platin_critical_section

        # PDF-SLIMDOWN v2.0: quick_wins is now critical, removed from this list
        non_critical = ["executive_summary", "business_case", "data_readiness"]

        for section in non_critical:
            assert not is_platin_critical_section(section), f"Should not be critical: {section}"


class TestGetPlatinMinWords:
    """Test get_platin_min_words() helper function."""

    def test_get_platin_min_words_returns_correct_value(self):
        """Verify get_platin_min_words returns correct min_words (PDF-SLIMDOWN v2.0)."""
        from services.prompt_enhancer import get_platin_min_words

        # PDF-SLIMDOWN v2.0: Reduced min_words
        assert get_platin_min_words("foerderpotenzial") == 700
        assert get_platin_min_words("risks") == 600
        assert get_platin_min_words("recommendations") == 400
        assert get_platin_min_words("roadmap_12m") == 350
        assert get_platin_min_words("quick_wins") == 150  # Now critical

    def test_get_platin_min_words_returns_zero_for_non_critical(self):
        """Verify get_platin_min_words returns 0 for non-critical sections."""
        from services.prompt_enhancer import get_platin_min_words

        assert get_platin_min_words("executive_summary") == 0
        # PDF-SLIMDOWN v2.0: quick_wins is now critical, use business_case instead
        assert get_platin_min_words("business_case") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
