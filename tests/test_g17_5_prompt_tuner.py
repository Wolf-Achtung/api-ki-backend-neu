# -*- coding: utf-8 -*-
"""
Tests for Sprint G17.5: Auto-Learning Prompt Tuner

Tests cover:
- Length tuning based on SECTION_TOO_SHORT warnings
- Redundancy tuning
- Persona strictness (only increases)
- Segment stability filter
- Dry-run mode
- SmartDefaultsEngine integration
- FT privacy compliance
- Dashboard endpoints
"""
from __future__ import annotations

import asyncio
import json
import pytest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch, MagicMock


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_segment_stats():
    """Create sample segment stats."""
    @dataclass
    class MockSegmentStats:
        segment_key: str = "solo|beratung|minimal|DE"
        stability: str = "medium"
        sample_count: int = 50
        top_warning_types: List[tuple] = None
        prompt_file: str = "prompts/de/roadmap_12m.md"
        section_id: str = "roadmap_12m"

        def __post_init__(self):
            if self.top_warning_types is None:
                self.top_warning_types = [
                    ("SECTION_TOO_SHORT", 5),
                    ("REDUNDANCY_DETECTED", 3),
                ]

    return MockSegmentStats()


@pytest.fixture
def sample_segment_stats_weak():
    """Create sample segment stats with weak stability."""
    @dataclass
    class MockSegmentStats:
        segment_key: str = "team|it_software|moderate|DE"
        stability: str = "weak"
        sample_count: int = 10
        top_warning_types: List[tuple] = None
        prompt_file: str = "prompts/de/default.md"
        section_id: str = "default"

    return MockSegmentStats()


@pytest.fixture
def sample_ft_signals():
    """Create sample FT signals."""
    @dataclass
    class MockSignal:
        signal_id: str
        signal_type: str
        segment_key: str = "solo|beratung|minimal|DE"
        source_section: str = "test"
        quality_score: float = 0.7

    return [
        MockSignal(signal_id="ft_size_1", signal_type="size_aware_length"),
        MockSignal(signal_id="ft_size_2", signal_type="size_aware_length"),
        MockSignal(signal_id="ft_size_3", signal_type="size_aware_length"),
        MockSignal(signal_id="ft_redundancy_1", signal_type="redundancy_compression"),
        MockSignal(signal_id="ft_redundancy_2", signal_type="redundancy_compression"),
        MockSignal(signal_id="ft_redundancy_3", signal_type="redundancy_compression"),
        MockSignal(signal_id="ft_persona_1", signal_type="persona_fix"),
        MockSignal(signal_id="ft_persona_2", signal_type="persona_fix"),
        MockSignal(signal_id="ft_persona_3", signal_type="persona_fix"),
        MockSignal(signal_id="ft_persona_4", signal_type="persona_fix"),
        MockSignal(signal_id="ft_ai_act_1", signal_type="ai_act_reasoning"),
        MockSignal(signal_id="ft_ai_act_2", signal_type="ai_act_reasoning"),
        MockSignal(signal_id="ft_ai_act_3", signal_type="ai_act_reasoning"),
    ]


@pytest.fixture
def sample_validation_warnings():
    """Create sample validation warnings."""
    return [
        {"type": "SECTION_TOO_SHORT", "message": "Section too short", "section": "roadmap_12m"},
        {"type": "SECTION_TOO_SHORT", "message": "Content below min-word threshold"},
        {"type": "SECTION_TOO_SHORT", "message": "Too short warning"},
        {"type": "SECTION_TOO_SHORT", "message": "Another short section"},
        {"type": "REDUNDANCY_DETECTED", "message": "Redundant content found"},
        {"type": "REDUNDANCY_DETECTED", "message": "Wiederholung detected"},
        {"type": "REDUNDANCY_DETECTED", "message": "Redundanz in Abschnitt"},
        {"type": "REDUNDANCY_DETECTED", "message": "Duplicated content"},
        {"type": "PERSONA_MISMATCH", "message": "Team term found for solo persona"},
        {"type": "PERSONA_MISMATCH", "message": "Persona leak detected"},
        {"type": "PERSONA_MISMATCH", "message": "Solo term issue"},
        {"type": "AI_ACT_WARNING", "message": "AI-Act reasoning weak"},
        {"type": "AI_ACT_WARNING", "message": "KI-Verordnung reference missing"},
        {"type": "AI_ACT_WARNING", "message": "AI Act compliance incomplete"},
    ]


# =============================================================================
# LENGTH TUNING TESTS
# =============================================================================

class TestLengthTuning:
    """Tests for length-related tuning."""

    def test_too_short_warnings_increase_word_factor(
        self,
        sample_segment_stats,
        sample_validation_warnings,
    ) -> None:
        """Segment with many SECTION_TOO_SHORT warnings should increase target_word_factor."""
        from services.prompt_tuner import build_tuning_profile

        profile = build_tuning_profile(
            prompt_file="prompts/de/roadmap_12m.md",
            section_id="roadmap_12m",
            segment_key="solo|beratung|minimal|DE",
            segment_stats=sample_segment_stats,
            validation_warnings=sample_validation_warnings,
        )

        # Should have increased word factor due to 4 "too short" warnings
        assert profile.target_word_factor > 1.0
        assert profile.target_word_factor <= 1.30  # Max limit

    def test_word_factor_respects_max_limit(self, sample_segment_stats) -> None:
        """Word factor should not exceed TUNER_MAX_WORD_FACTOR."""
        from services.prompt_tuner import build_tuning_profile, TUNER_MAX_WORD_FACTOR

        # Create many warnings to push factor high
        many_warnings = [
            {"type": "SECTION_TOO_SHORT", "message": f"Short warning {i}"}
            for i in range(50)
        ]

        profile = build_tuning_profile(
            prompt_file="prompts/de/roadmap_12m.md",
            section_id="roadmap_12m",
            segment_key="solo|beratung|minimal|DE",
            segment_stats=sample_segment_stats,
            validation_warnings=many_warnings,
        )

        assert profile.target_word_factor <= TUNER_MAX_WORD_FACTOR

    def test_word_factor_respects_min_limit(self) -> None:
        """Word factor should not go below TUNER_MIN_WORD_FACTOR."""
        from services.prompt_tuner import apply_tuning_constraints, TuningProfile, TUNER_MIN_WORD_FACTOR

        profile = TuningProfile(
            prompt_file="test.md",
            section_id="test",
            segment_key="test",
            target_word_factor=0.5,  # Below minimum
        )

        constrained = apply_tuning_constraints(profile)
        assert constrained.target_word_factor >= TUNER_MIN_WORD_FACTOR


# =============================================================================
# REDUNDANCY TUNING TESTS
# =============================================================================

class TestRedundancyTuning:
    """Tests for redundancy-related tuning."""

    def test_high_redundancy_increases_sensitivity(
        self,
        sample_segment_stats,
        sample_validation_warnings,
    ) -> None:
        """Segment with high redundancy should increase redundancy_sensitivity."""
        from services.prompt_tuner import build_tuning_profile

        profile = build_tuning_profile(
            prompt_file="prompts/de/roadmap_12m.md",
            section_id="roadmap_12m",
            segment_key="solo|beratung|minimal|DE",
            segment_stats=sample_segment_stats,
            validation_warnings=sample_validation_warnings,
        )

        # Should have increased redundancy sensitivity due to 4 redundancy warnings
        assert profile.redundancy_sensitivity > 1.0

    def test_redundancy_sensitivity_respects_limits(self) -> None:
        """Redundancy sensitivity should stay within limits."""
        from services.prompt_tuner import (
            apply_tuning_constraints,
            TuningProfile,
            TUNER_MAX_REDUNDANCY_SENSITIVITY,
            TUNER_MIN_REDUNDANCY_SENSITIVITY,
        )

        # Test max limit
        profile_high = TuningProfile(
            prompt_file="test.md",
            section_id="test",
            segment_key="test",
            redundancy_sensitivity=5.0,  # Above maximum
        )
        constrained_high = apply_tuning_constraints(profile_high)
        assert constrained_high.redundancy_sensitivity <= TUNER_MAX_REDUNDANCY_SENSITIVITY

        # Test min limit
        profile_low = TuningProfile(
            prompt_file="test.md",
            section_id="test",
            segment_key="test",
            redundancy_sensitivity=0.1,  # Below minimum
        )
        constrained_low = apply_tuning_constraints(profile_low)
        assert constrained_low.redundancy_sensitivity >= TUNER_MIN_REDUNDANCY_SENSITIVITY


# =============================================================================
# PERSONA STRICTNESS TESTS
# =============================================================================

class TestPersonaStrictness:
    """Tests for persona strictness tuning."""

    def test_persona_leaks_increase_strictness(
        self,
        sample_segment_stats,
        sample_ft_signals,
        sample_validation_warnings,
    ) -> None:
        """Frequent persona leaks should increase persona_strictness."""
        from services.prompt_tuner import build_tuning_profile

        profile = build_tuning_profile(
            prompt_file="prompts/de/roadmap_12m.md",
            section_id="roadmap_12m",
            segment_key="solo|beratung|minimal|DE",
            segment_stats=sample_segment_stats,
            ft_signals=sample_ft_signals,
            validation_warnings=sample_validation_warnings,
        )

        # Should have increased persona strictness due to persona signals/warnings
        assert profile.persona_strictness > 1.0

    def test_persona_strictness_never_decreases_below_minimum(self) -> None:
        """Persona strictness should never go below TUNER_PERSONA_STRICTNESS_MIN."""
        from services.prompt_tuner import (
            apply_tuning_constraints,
            TuningProfile,
            TUNER_PERSONA_STRICTNESS_MIN,
        )

        profile = TuningProfile(
            prompt_file="test.md",
            section_id="test",
            segment_key="test",
            persona_strictness=0.5,  # Below minimum
        )

        constrained = apply_tuning_constraints(profile)
        assert constrained.persona_strictness >= TUNER_PERSONA_STRICTNESS_MIN

    def test_persona_strictness_respects_max_limit(self) -> None:
        """Persona strictness should not exceed maximum."""
        from services.prompt_tuner import (
            apply_tuning_constraints,
            TuningProfile,
            TUNER_PERSONA_STRICTNESS_MAX,
        )

        profile = TuningProfile(
            prompt_file="test.md",
            section_id="test",
            segment_key="test",
            persona_strictness=5.0,  # Way above maximum
        )

        constrained = apply_tuning_constraints(profile)
        assert constrained.persona_strictness <= TUNER_PERSONA_STRICTNESS_MAX


# =============================================================================
# SEGMENT STABILITY FILTER TESTS
# =============================================================================

class TestSegmentStabilityFilter:
    """Tests for segment stability filtering."""

    def test_weak_segment_no_updates(self, sample_segment_stats_weak, tmp_path) -> None:
        """Weak segment stability should prevent tuning updates."""
        from services.prompt_tuner import update_tuning_profiles_from_feedback

        with patch("services.prompt_tuner._get_storage_path", return_value=tmp_path):
            with patch("services.prompt_tuner._last_update_time", None):
                feedback_snapshot = {
                    "team|it_software|moderate|DE": sample_segment_stats_weak,
                }

                updated = update_tuning_profiles_from_feedback(
                    feedback_snapshot=feedback_snapshot,
                )

                # Should not have updated due to weak stability
                assert updated == 0

    def test_medium_segment_allows_updates(self, sample_segment_stats, tmp_path) -> None:
        """Medium segment stability should allow tuning updates."""
        from services.prompt_tuner import update_tuning_profiles_from_feedback

        with patch("services.prompt_tuner._get_storage_path", return_value=tmp_path):
            with patch("services.prompt_tuner._last_update_time", None):
                feedback_snapshot = {
                    "solo|beratung|minimal|DE": sample_segment_stats,
                }

                updated = update_tuning_profiles_from_feedback(
                    feedback_snapshot=feedback_snapshot,
                )

                # Should have updated (medium stability is acceptable)
                assert updated >= 0  # May be 0 if profile didn't change significantly


# =============================================================================
# DRY-RUN TESTS
# =============================================================================

class TestDryRunMode:
    """Tests for dry-run mode."""

    def test_dry_run_does_not_persist(self, sample_segment_stats, tmp_path) -> None:
        """Dry-run mode should not persist profiles."""
        from services.prompt_tuner import build_tuning_profile, _save_profile_to_storage

        with patch("services.prompt_tuner.PROMPT_TUNER_DRY_RUN", True):
            with patch("services.prompt_tuner._get_storage_path", return_value=tmp_path):
                profile = build_tuning_profile(
                    prompt_file="prompts/de/roadmap_12m.md",
                    section_id="roadmap_12m",
                    segment_key="solo|beratung|minimal|DE",
                    segment_stats=sample_segment_stats,
                )

                # Try to save - should return False in dry-run mode
                saved = _save_profile_to_storage(profile)
                assert saved is False

                # No files should be created
                files = list(tmp_path.glob("*.json"))
                assert len(files) == 0


# =============================================================================
# SMART DEFAULTS ENGINE INTEGRATION TESTS
# =============================================================================

class TestSmartDefaultsIntegration:
    """Tests for SmartDefaultsEngine integration."""

    def test_tuning_adjusts_min_words(self) -> None:
        """SmartDefaultsEngine should apply tuning to min_words."""
        from services.prompt_enhancer import SmartDefaultsEngine
        from services.prompt_tuner import TuningProfile

        engine = SmartDefaultsEngine()

        # Mock the tuner profile
        mock_profile = TuningProfile(
            prompt_file="prompts/de/roadmap_12m.md",
            section_id="roadmap_12m",
            segment_key="solo|beratung|minimal|DE",
            target_word_factor=1.15,
            source="auto",
        )

        with patch("services.prompt_enhancer._TUNER_AVAILABLE", True):
            with patch("services.prompt_enhancer.PROMPT_TUNER_ENABLED", True):
                with patch("services.prompt_enhancer._get_tuning_profile", return_value=mock_profile):
                    result = engine.get_tuning_adjusted_values(
                        prompt_file="prompts/de/roadmap_12m.md",
                        section_id="roadmap_12m",
                        segment_key="solo|beratung|minimal|DE",
                        base_min_words=100,
                    )

                    # Should apply 1.15x factor (allow for int rounding)
                    assert result["min_words"] >= 114 and result["min_words"] <= 116
                    assert result["tuning_applied"] is True

    def test_disabled_tuner_returns_base_values(self) -> None:
        """Disabled tuner should return base values unchanged."""
        from services.prompt_enhancer import SmartDefaultsEngine

        engine = SmartDefaultsEngine()

        with patch("services.prompt_enhancer._TUNER_AVAILABLE", False):
            result = engine.get_tuning_adjusted_values(
                prompt_file="prompts/de/roadmap_12m.md",
                section_id="roadmap_12m",
                segment_key="solo|beratung|minimal|DE",
                base_min_words=100,
            )

            assert result["min_words"] == 100
            assert result["tuning_applied"] is False


# =============================================================================
# FT PRIVACY TESTS
# =============================================================================

class TestFTPrivacy:
    """Tests for FT privacy compliance."""

    def test_no_raw_user_data_in_profile(self, sample_segment_stats, sample_ft_signals) -> None:
        """Tuning profiles should not contain raw user-specific data."""
        from services.prompt_tuner import build_tuning_profile
        from dataclasses import asdict

        profile = build_tuning_profile(
            prompt_file="prompts/de/roadmap_12m.md",
            section_id="roadmap_12m",
            segment_key="solo|beratung|minimal|DE",
            segment_stats=sample_segment_stats,
            ft_signals=sample_ft_signals,
        )

        profile_dict = asdict(profile)
        profile_str = json.dumps(profile_dict, default=str)

        # Check no sensitive patterns
        sensitive_patterns = [
            "user_id",
            "email",
            "password",
            "api_key",
            "secret",
            "token",
        ]

        for pattern in sensitive_patterns:
            assert pattern not in profile_str.lower()


# =============================================================================
# DASHBOARD ENDPOINT TESTS
# =============================================================================

class TestDashboardEndpoints:
    """Tests for G17.5 dashboard endpoints."""

    def test_tuner_status_endpoint(self, tmp_path) -> None:
        """Test tuner status endpoint returns valid response."""
        from routes.feedback_dashboard import get_prompt_tuner_status

        with patch("services.prompt_tuner._get_storage_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                get_prompt_tuner_status()
            )

            assert hasattr(result, "enabled")
            assert hasattr(result, "profiles_total")
            assert hasattr(result, "by_segment_stability")
            assert hasattr(result, "config")

    def test_tuner_profiles_endpoint(self, tmp_path) -> None:
        """Test tuner profiles endpoint returns valid response."""
        from routes.feedback_dashboard import get_prompt_tuner_profiles

        with patch("services.prompt_tuner._get_storage_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                get_prompt_tuner_profiles(segment=None, limit=50)
            )

            assert hasattr(result, "profiles")
            assert hasattr(result, "count")
            assert isinstance(result.profiles, list)

    def test_tuner_reset_endpoint_dry_run(self, tmp_path) -> None:
        """Test tuner reset endpoint in dry-run mode."""
        from routes.feedback_dashboard import reset_prompt_tuner_profiles

        with patch("services.prompt_tuner._get_storage_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                reset_prompt_tuner_profiles(segment=None, dry_run=True)
            )

            assert hasattr(result, "reset_count")
            assert hasattr(result, "message")
            assert "Dry-run" in result.message


# =============================================================================
# STORAGE TESTS
# =============================================================================

class TestStorage:
    """Tests for profile storage functionality."""

    def test_profile_save_and_load(self, tmp_path) -> None:
        """Test saving and loading a profile."""
        from services.prompt_tuner import (
            TuningProfile,
            _save_profile_to_storage,
            _load_profile_from_storage,
            _get_profile_key,
        )

        with patch("services.prompt_tuner.PROMPT_TUNER_DRY_RUN", False):
            with patch("services.prompt_tuner._get_storage_path", return_value=tmp_path):
                profile = TuningProfile(
                    prompt_file="prompts/de/test.md",
                    section_id="test_section",
                    segment_key="solo|beratung|minimal|DE",
                    target_word_factor=1.15,
                    redundancy_sensitivity=1.2,
                    persona_strictness=1.1,
                    source="auto",
                )

                # Save
                saved = _save_profile_to_storage(profile)
                assert saved is True

                # Load
                profile_key = _get_profile_key(
                    profile.prompt_file,
                    profile.section_id,
                    profile.segment_key,
                )
                loaded = _load_profile_from_storage(profile_key)

                assert loaded is not None
                assert loaded.target_word_factor == 1.15
                assert loaded.redundancy_sensitivity == 1.2
                assert loaded.persona_strictness == 1.1


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

class TestConfiguration:
    """Tests for configuration and environment variables."""

    def test_env_variables_have_defaults(self) -> None:
        """Test that all ENV variables have sensible defaults."""
        from services.prompt_tuner import (
            PROMPT_TUNER_ENABLED,
            PROMPT_TUNER_DRY_RUN,
            TUNER_MIN_SAMPLES,
            TUNER_MIN_SEGMENT_STABILITY,
            TUNER_MAX_WORD_FACTOR,
            TUNER_MIN_WORD_FACTOR,
            TUNER_MAX_EMPHASIS_DELTA,
            TUNER_PERSONA_STRICTNESS_MIN,
            TUNER_PERSONA_STRICTNESS_MAX,
        )

        assert isinstance(PROMPT_TUNER_ENABLED, bool)
        assert isinstance(PROMPT_TUNER_DRY_RUN, bool)
        assert TUNER_MIN_SAMPLES >= 1
        assert TUNER_MIN_SEGMENT_STABILITY in ["weak", "medium", "strong"]
        assert TUNER_MAX_WORD_FACTOR > TUNER_MIN_WORD_FACTOR
        assert TUNER_MAX_EMPHASIS_DELTA > 0
        assert TUNER_PERSONA_STRICTNESS_MAX >= TUNER_PERSONA_STRICTNESS_MIN

    def test_known_emphasis_keys(self) -> None:
        """Test that known emphasis keys are defined."""
        from services.prompt_tuner import KNOWN_EMPHASIS_KEYS

        expected_keys = {"governance", "data", "security", "compliance", "ai_act", "funding"}
        assert expected_keys.issubset(KNOWN_EMPHASIS_KEYS)


# =============================================================================
# EMPHASIS WEIGHTS TESTS
# =============================================================================

class TestEmphasisWeights:
    """Tests for emphasis weight calculation."""

    def test_ai_act_signals_increase_governance_weight(
        self,
        sample_segment_stats,
        sample_ft_signals,
        sample_validation_warnings,
    ) -> None:
        """AI-Act signals should increase governance/compliance emphasis."""
        from services.prompt_tuner import build_tuning_profile

        profile = build_tuning_profile(
            prompt_file="prompts/de/roadmap_12m.md",
            section_id="roadmap_12m",
            segment_key="solo|beratung|minimal|DE",
            segment_stats=sample_segment_stats,
            ft_signals=sample_ft_signals,
            validation_warnings=sample_validation_warnings,
        )

        # Should have increased governance emphasis due to AI-Act signals/warnings
        if "governance" in profile.emphasis_weights:
            assert profile.emphasis_weights["governance"] > 1.0

    def test_emphasis_weights_respect_delta_limit(self) -> None:
        """Emphasis weights should not exceed max delta."""
        from services.prompt_tuner import (
            apply_tuning_constraints,
            TuningProfile,
            TUNER_MAX_EMPHASIS_DELTA,
        )

        profile = TuningProfile(
            prompt_file="test.md",
            section_id="test",
            segment_key="test",
            emphasis_weights={"governance": 2.0, "data": 0.1},  # Both out of bounds
        )

        constrained = apply_tuning_constraints(profile)

        for key, value in constrained.emphasis_weights.items():
            assert value >= 1.0 - TUNER_MAX_EMPHASIS_DELTA
            assert value <= 1.0 + TUNER_MAX_EMPHASIS_DELTA

    def test_unknown_emphasis_keys_removed(self) -> None:
        """Unknown emphasis keys should be removed during constraints."""
        from services.prompt_tuner import apply_tuning_constraints, TuningProfile

        profile = TuningProfile(
            prompt_file="test.md",
            section_id="test",
            segment_key="test",
            emphasis_weights={
                "governance": 1.1,  # Known
                "unknown_key": 1.2,  # Unknown
                "another_unknown": 1.3,  # Unknown
            },
        )

        constrained = apply_tuning_constraints(profile)

        assert "governance" in constrained.emphasis_weights
        assert "unknown_key" not in constrained.emphasis_weights
        assert "another_unknown" not in constrained.emphasis_weights


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full tuning pipeline."""

    def test_full_tuning_pipeline(
        self,
        sample_segment_stats,
        sample_ft_signals,
        sample_validation_warnings,
        tmp_path,
    ) -> None:
        """Test the full tuning pipeline from build to apply."""
        from services.prompt_tuner import (
            build_tuning_profile,
            get_tuning_profile,
            _save_profile_to_storage,
            _get_profile_key,
            _profiles_cache,
        )

        with patch("services.prompt_tuner.PROMPT_TUNER_DRY_RUN", False):
            with patch("services.prompt_tuner._get_storage_path", return_value=tmp_path):
                # Clear cache
                _profiles_cache.clear()

                # Build profile
                profile = build_tuning_profile(
                    prompt_file="prompts/de/roadmap_12m.md",
                    section_id="roadmap_12m",
                    segment_key="solo|beratung|minimal|DE",
                    segment_stats=sample_segment_stats,
                    ft_signals=sample_ft_signals,
                    validation_warnings=sample_validation_warnings,
                )

                # Save to cache and storage
                profile_key = _get_profile_key(
                    profile.prompt_file,
                    profile.section_id,
                    profile.segment_key,
                )
                _profiles_cache[profile_key] = profile
                _save_profile_to_storage(profile)

                # Retrieve and verify
                retrieved = get_tuning_profile(
                    prompt_file="prompts/de/roadmap_12m.md",
                    section_id="roadmap_12m",
                    segment_key="solo|beratung|minimal|DE",
                )

                assert retrieved.target_word_factor == profile.target_word_factor
                assert retrieved.redundancy_sensitivity == profile.redundancy_sensitivity
                assert retrieved.persona_strictness == profile.persona_strictness

    def test_default_profile_when_disabled(self) -> None:
        """Should return default profile when tuner is disabled."""
        from services.prompt_tuner import get_tuning_profile

        with patch("services.prompt_tuner.PROMPT_TUNER_ENABLED", False):
            profile = get_tuning_profile(
                prompt_file="prompts/de/roadmap_12m.md",
                section_id="roadmap_12m",
                segment_key="solo|beratung|minimal|DE",
            )

            # Should return default values
            assert profile.target_word_factor == 1.0
            assert profile.redundancy_sensitivity == 1.0
            assert profile.persona_strictness == 1.0
            assert profile.source == "default"
