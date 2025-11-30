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

        expected_sections = [
            "foerderpotenzial",
            "risks",
            "recommendations",
            "roadmap_12m",
            "gamechanger",
            "unternehmensprofil_markt",
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

    def test_platin_max_tokens_is_4096(self):
        """Verify all PLATIN sections have explicit max_tokens=4096."""
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        for section, config in PLATIN_CRITICAL_SECTIONS.items():
            assert config["max_tokens"] == 4096, (
                f"Section {section} should have max_tokens=4096, got {config['max_tokens']}"
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
        """Verify min_words thresholds are set correctly."""
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        expected_min_words = {
            "foerderpotenzial": 900,
            "risks": 800,
            "recommendations": 800,
            "roadmap_12m": 900,
            "gamechanger": 700,
            "unternehmensprofil_markt": 500,
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
        """Verify get_platin_config returns config for critical sections."""
        from services.prompt_enhancer import get_platin_config

        config = get_platin_config("foerderpotenzial")
        assert config is not None
        assert config["max_tokens"] == 4096
        assert config["temperature"] == 0.4
        assert config["min_words"] == 900

    def test_get_platin_config_returns_none_for_non_critical_section(self):
        """Verify get_platin_config returns None for non-critical sections."""
        from services.prompt_enhancer import get_platin_config

        config = get_platin_config("executive_summary")
        assert config is None

        config = get_platin_config("quick_wins")
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

        non_critical = ["executive_summary", "quick_wins", "business_case", "data_readiness"]

        for section in non_critical:
            assert not is_platin_critical_section(section), f"Should not be critical: {section}"


class TestGetPlatinMinWords:
    """Test get_platin_min_words() helper function."""

    def test_get_platin_min_words_returns_correct_value(self):
        """Verify get_platin_min_words returns correct min_words."""
        from services.prompt_enhancer import get_platin_min_words

        assert get_platin_min_words("foerderpotenzial") == 900
        assert get_platin_min_words("risks") == 800
        assert get_platin_min_words("recommendations") == 800
        assert get_platin_min_words("roadmap_12m") == 900

    def test_get_platin_min_words_returns_zero_for_non_critical(self):
        """Verify get_platin_min_words returns 0 for non-critical sections."""
        from services.prompt_enhancer import get_platin_min_words

        assert get_platin_min_words("executive_summary") == 0
        assert get_platin_min_words("quick_wins") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
