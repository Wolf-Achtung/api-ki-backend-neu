# -*- coding: utf-8 -*-
"""
SPRINT N3.3/N3.6/N3.7: Tests for Timeout & Retry Optimization.

Tests the updated timeout configurations and retry logic.

N3.7 PACKAGE F Updates:
- Premium sections timeout → 165s (from 140s)
- Retries → 6 stages (from 5)
- Backoff timing → 3s → 6s → 12s → 24s → 48s → 96s
"""
import pytest


class TestTimeoutConfiguration:
    """Test the timeout configuration constants."""

    def test_default_max_retries(self):
        """N3.7: Default max retries should be 6."""
        from services.llm_client import LLM_MAX_RETRIES

        assert LLM_MAX_RETRIES == 6

    def test_default_backoff_base(self):
        """N3.6: Default backoff base should be 3.0s for 3s, 6s, 12s, 24s, 48s sequence."""
        from services.llm_client import LLM_RETRY_BACKOFF_BASE

        assert LLM_RETRY_BACKOFF_BASE == 3.0

    def test_default_backoff_multiplier(self):
        """Default backoff multiplier should be 2.0."""
        from services.llm_client import LLM_RETRY_BACKOFF_MULTIPLIER

        assert LLM_RETRY_BACKOFF_MULTIPLIER == 2.0


class TestBackoffSequence:
    """Test the exponential backoff sequence."""

    def test_backoff_sequence_3_6_12_24_48_96(self):
        """N3.7: Backoff sequence should be 3s, 6s, 12s, 24s, 48s, 96s."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()

        # Attempt 0 (first retry) -> 3s
        assert calculate_backoff(0, config) == 3.0

        # Attempt 1 (second retry) -> 6s
        assert calculate_backoff(1, config) == 6.0

        # Attempt 2 (third retry) -> 12s
        assert calculate_backoff(2, config) == 12.0

        # Attempt 3 (fourth retry) -> 24s
        assert calculate_backoff(3, config) == 24.0

        # Attempt 4 (fifth retry) -> 48s
        assert calculate_backoff(4, config) == 48.0

        # Attempt 5 (sixth retry) -> 96s
        assert calculate_backoff(5, config) == 96.0


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
        """N3.7: exec_summary should have 165s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("exec_summary") == 165.0

    def test_ki_stack_summary_timeout(self):
        """N3.7: ki_stack_summary should have 165s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("ki_stack_summary") == 165.0

    def test_branch_deep_dive_timeout(self):
        """N3.7: branch_deep_dive should have 165s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("branch_deep_dive") == 165.0

    def test_risk_report_timeout(self):
        """N3.7: risk_report should have 165s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("risk_report") == 165.0

    def test_roadmap_12m_timeout(self):
        """N3.7: roadmap_12m should have 165s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES.get("roadmap_12m") == 165.0

    def test_get_section_timeout_premium(self):
        """N3.7: get_section_timeout should return 165s for premium sections."""
        from services.llm_client import get_section_timeout

        assert get_section_timeout("exec_summary") == 165.0
        assert get_section_timeout("ki_stack_summary") == 165.0
        assert get_section_timeout("branch_deep_dive") == 165.0

    def test_get_section_timeout_default(self):
        """get_section_timeout should return default for unknown sections."""
        from services.llm_client import get_section_timeout, LLM_TIMEOUT

        assert get_section_timeout("unknown_section") == LLM_TIMEOUT


class TestRetryConfig:
    """Test RetryConfig defaults."""

    def test_retry_config_max_retries(self):
        """N3.7: RetryConfig should use 6 max retries by default."""
        from services.llm_client import RetryConfig

        config = RetryConfig()
        assert config.max_retries == 6

    def test_retry_config_backoff_base(self):
        """N3.6: RetryConfig should use 3.0s backoff base."""
        from services.llm_client import RetryConfig

        config = RetryConfig()
        assert config.backoff_base == 3.0

    def test_retry_config_backoff_multiplier(self):
        """RetryConfig should use 2.0 multiplier."""
        from services.llm_client import RetryConfig

        config = RetryConfig()
        assert config.backoff_multiplier == 2.0


class TestAllPremiumSectionsHaveTimeouts:
    """Ensure all premium sections have timeout overrides."""

    def test_all_premium_sections_have_165s_timeouts(self):
        """N3.7: All premium sections should have 165s timeout overrides."""
        from services.llm_client import (
            PREMIUM_SECTIONS,
            SECTION_TIMEOUT_OVERRIDES,
        )

        n37_sections = [
            "exec_summary",
            "ki_stack_summary",
            "branch_deep_dive",
            "risk_report",
            "roadmap_12m",
        ]

        for section in n37_sections:
            assert section in PREMIUM_SECTIONS, f"{section} not in PREMIUM_SECTIONS"
            assert section in SECTION_TIMEOUT_OVERRIDES, f"{section} not in SECTION_TIMEOUT_OVERRIDES"
            assert SECTION_TIMEOUT_OVERRIDES[section] == 165.0, f"{section} timeout != 165s"
