# -*- coding: utf-8 -*-
"""
SPRINT N3.3: Tests for Timeout & Retry Optimization.

Tests the updated timeout configurations and retry logic.
"""
import pytest


class TestTimeoutConfiguration:
    """Test the timeout configuration constants."""

    def test_default_max_retries(self):
        """Default max retries should be 3."""
        from services.llm_client import LLM_MAX_RETRIES

        assert LLM_MAX_RETRIES == 3

    def test_default_backoff_base(self):
        """Default backoff base should be 2.0s for 2s, 4s, 8s sequence."""
        from services.llm_client import LLM_RETRY_BACKOFF_BASE

        assert LLM_RETRY_BACKOFF_BASE == 2.0

    def test_default_backoff_multiplier(self):
        """Default backoff multiplier should be 2.0."""
        from services.llm_client import LLM_RETRY_BACKOFF_MULTIPLIER

        assert LLM_RETRY_BACKOFF_MULTIPLIER == 2.0


class TestBackoffSequence:
    """Test the exponential backoff sequence."""

    def test_backoff_sequence_2_4_8(self):
        """Backoff sequence should be 2s, 4s, 8s."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()

        # Attempt 0 (first retry) -> 2s
        assert calculate_backoff(0, config) == 2.0

        # Attempt 1 (second retry) -> 4s
        assert calculate_backoff(1, config) == 4.0

        # Attempt 2 (third retry) -> 8s
        assert calculate_backoff(2, config) == 8.0


class TestPremiumSections:
    """Test premium section configuration."""

    def test_premium_sections_include_exec(self):
        """Premium sections should include exec_summary."""
        from services.llm_client import PREMIUM_SECTIONS

        assert "exec_summary" in PREMIUM_SECTIONS

    def test_premium_sections_include_ki_stack(self):
        """Premium sections should include ki_stack_summary."""
        from services.llm_client import PREMIUM_SECTIONS

        assert "ki_stack_summary" in PREMIUM_SECTIONS

    def test_premium_sections_include_branch(self):
        """Premium sections should include branch_deep_dive."""
        from services.llm_client import PREMIUM_SECTIONS

        assert "branch_deep_dive" in PREMIUM_SECTIONS

    def test_premium_sections_include_risk(self):
        """Premium sections should include risk_report."""
        from services.llm_client import PREMIUM_SECTIONS

        assert "risk_report" in PREMIUM_SECTIONS or "risks" in PREMIUM_SECTIONS

    def test_premium_sections_include_roadmap(self):
        """Premium sections should include roadmap_12m."""
        from services.llm_client import PREMIUM_SECTIONS

        assert "roadmap_12m" in PREMIUM_SECTIONS

    def test_is_premium_section_function(self):
        """is_premium_section should correctly identify premium sections."""
        from services.llm_client import is_premium_section

        assert is_premium_section("exec_summary") is True
        assert is_premium_section("ki_stack_summary") is True
        assert is_premium_section("branch_deep_dive") is True
        assert is_premium_section("roadmap_12m") is True

        # Non-premium sections
        assert is_premium_section("unknown_section") is False


class TestSectionTimeoutOverrides:
    """Test section-specific timeout overrides."""

    def test_exec_summary_timeout(self):
        """exec_summary should have 90s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("exec_summary") == 90.0

    def test_ki_stack_summary_timeout(self):
        """ki_stack_summary should have 90s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("ki_stack_summary") == 90.0

    def test_branch_deep_dive_timeout(self):
        """branch_deep_dive should have 90s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("branch_deep_dive") == 90.0

    def test_risk_report_timeout(self):
        """risk_report should have 90s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("risk_report") == 90.0

    def test_roadmap_12m_timeout(self):
        """roadmap_12m should have 90s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("roadmap_12m") == 90.0

    def test_get_section_timeout_premium(self):
        """get_section_timeout should return correct timeout for premium sections."""
        from services.llm_client import get_section_timeout

        assert get_section_timeout("exec_summary") == 90.0
        assert get_section_timeout("ki_stack_summary") == 90.0
        assert get_section_timeout("branch_deep_dive") == 90.0

    def test_get_section_timeout_default(self):
        """get_section_timeout should return default for unknown sections."""
        from services.llm_client import get_section_timeout, LLM_TIMEOUT

        assert get_section_timeout("unknown_section") == LLM_TIMEOUT


class TestRetryConfig:
    """Test RetryConfig defaults."""

    def test_retry_config_max_retries(self):
        """RetryConfig should use 3 max retries by default."""
        from services.llm_client import RetryConfig

        config = RetryConfig()
        assert config.max_retries == 3

    def test_retry_config_backoff_base(self):
        """RetryConfig should use 2.0s backoff base."""
        from services.llm_client import RetryConfig

        config = RetryConfig()
        assert config.backoff_base == 2.0

    def test_retry_config_backoff_multiplier(self):
        """RetryConfig should use 2.0 multiplier."""
        from services.llm_client import RetryConfig

        config = RetryConfig()
        assert config.backoff_multiplier == 2.0


class TestAllPremiumSectionsHaveTimeouts:
    """Ensure all premium sections have timeout overrides."""

    def test_all_n33_premium_sections_have_timeouts(self):
        """All N3.3 premium sections should have timeout overrides."""
        from services.llm_client import (
            PREMIUM_SECTIONS,
            SECTION_TIMEOUT_OVERRIDES,
        )

        n33_sections = [
            "exec_summary",
            "ki_stack_summary",
            "branch_deep_dive",
            "risk_report",
            "roadmap_12m",
        ]

        for section in n33_sections:
            assert section in PREMIUM_SECTIONS, f"{section} not in PREMIUM_SECTIONS"
            assert section in SECTION_TIMEOUT_OVERRIDES, f"{section} not in SECTION_TIMEOUT_OVERRIDES"
            assert SECTION_TIMEOUT_OVERRIDES[section] >= 90.0, f"{section} timeout < 90s"
