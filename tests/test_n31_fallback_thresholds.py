# -*- coding: utf-8 -*-
"""
SPRINT N3.1: Tests for Reduced Fallback Thresholds.

Tests the updated EXTEND_MIN_WORDS thresholds in llm_postprocessor.py
to verify that Solo thresholds have been reduced to avoid unnecessary fallbacks.
"""
import pytest


class TestExtendMinWordsThresholds:
    """Test the EXTEND_MIN_WORDS configuration."""

    def test_extend_min_words_exists(self):
        """Verify EXTEND_MIN_WORDS dictionary exists."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        assert isinstance(EXTEND_MIN_WORDS, dict)
        assert len(EXTEND_MIN_WORDS) > 0

    def test_roadmap_12m_solo_reduced(self):
        """Solo threshold for roadmap_12m should be reduced (≤550)."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        roadmap_12m = EXTEND_MIN_WORDS.get("roadmap_12m", {})
        solo_threshold = roadmap_12m.get("solo", 999)

        assert solo_threshold <= 550, \
            f"roadmap_12m solo threshold should be ≤550, got {solo_threshold}"

    def test_recommendations_solo_reduced(self):
        """Solo threshold for recommendations should be reduced (≤500)."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        recommendations = EXTEND_MIN_WORDS.get("recommendations", {})
        solo_threshold = recommendations.get("solo", 999)

        assert solo_threshold <= 500, \
            f"recommendations solo threshold should be ≤500, got {solo_threshold}"

    def test_roadmap_90d_solo_reduced(self):
        """Solo threshold for roadmap_90d should be reduced (≤110)."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        roadmap_90d = EXTEND_MIN_WORDS.get("roadmap_90d", {})
        solo_threshold = roadmap_90d.get("solo", 999)

        assert solo_threshold <= 110, \
            f"roadmap_90d solo threshold should be ≤110, got {solo_threshold}"

    def test_all_sizes_defined(self):
        """Each section should have solo, team, kmu thresholds."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        required_sizes = ["solo", "team", "kmu"]

        for section, thresholds in EXTEND_MIN_WORDS.items():
            for size in required_sizes:
                assert size in thresholds, \
                    f"Section '{section}' missing '{size}' threshold"

    def test_solo_lower_than_team_kmu(self):
        """Solo thresholds should generally be lower than team/kmu."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        for section, thresholds in EXTEND_MIN_WORDS.items():
            solo = thresholds.get("solo", 0)
            team = thresholds.get("team", 0)
            kmu = thresholds.get("kmu", 0)

            # Solo should be <= team <= kmu (or at least not higher)
            assert solo <= team, \
                f"Section '{section}': solo ({solo}) > team ({team})"
            assert team <= kmu, \
                f"Section '{section}': team ({team}) > kmu ({kmu})"


class TestGetExtendMinWords:
    """Test the get_extend_min_words function."""

    def test_returns_correct_value_for_solo(self):
        """Should return correct threshold for solo size."""
        from services.llm_postprocessor import get_extend_min_words

        result = get_extend_min_words("roadmap_12m", "solo")
        assert isinstance(result, int)
        assert result > 0

    def test_returns_zero_for_unknown_section(self):
        """Should return 0 for unknown sections."""
        from services.llm_postprocessor import get_extend_min_words

        result = get_extend_min_words("nonexistent_section", "solo")
        assert result == 0

    def test_case_insensitive_size(self):
        """Size parameter should be case-insensitive."""
        from services.llm_postprocessor import get_extend_min_words

        result_lower = get_extend_min_words("roadmap_12m", "solo")
        result_upper = get_extend_min_words("roadmap_12m", "SOLO")
        result_mixed = get_extend_min_words("roadmap_12m", "Solo")

        assert result_lower == result_upper == result_mixed

    def test_invalid_size_defaults_to_team(self):
        """Invalid size should default to team threshold."""
        from services.llm_postprocessor import get_extend_min_words

        result_invalid = get_extend_min_words("roadmap_12m", "invalid_size")
        result_team = get_extend_min_words("roadmap_12m", "team")

        assert result_invalid == result_team


class TestExtendToMinWords:
    """Test the extend_to_min_words function."""

    def test_extends_short_content(self):
        """Content below threshold should be extended."""
        from services.llm_postprocessor import extend_to_min_words

        short_text = "<p>This is short.</p>"
        result, word_count, was_extended = extend_to_min_words(
            short_text, min_words=50, section="roadmap_12m", size="solo"
        )

        assert was_extended is True
        assert word_count > len(short_text.split())
        assert len(result) > len(short_text)

    def test_long_content_unchanged(self):
        """Content above threshold should not be changed."""
        from services.llm_postprocessor import extend_to_min_words

        long_text = " ".join(["word"] * 100)  # 100 words
        result, word_count, was_extended = extend_to_min_words(
            long_text, min_words=50, section="roadmap_12m", size="solo"
        )

        assert was_extended is False
        assert result == long_text

    def test_empty_text_handled(self):
        """Empty text should return safely."""
        from services.llm_postprocessor import extend_to_min_words

        result, word_count, was_extended = extend_to_min_words(
            "", min_words=50, section="roadmap_12m", size="solo"
        )

        assert was_extended is False
        assert word_count == 0

    def test_multiple_extension_attempts(self):
        """N3.1: Should try multiple extensions if needed."""
        from services.llm_postprocessor import extend_to_min_words

        very_short = "<p>Hi.</p>"
        result, word_count, was_extended = extend_to_min_words(
            very_short, min_words=200, section="roadmap_12m", size="solo",
            max_attempts=2
        )

        # Should have attempted multiple extensions
        assert was_extended is True


class TestAutoExtendSections:
    """Test the auto_extend_sections function."""

    def test_extends_undersized_sections(self):
        """Should extend sections below minimum."""
        from services.llm_postprocessor import auto_extend_sections

        sections = {
            "roadmap_12m": "<p>Short content.</p>",
        }

        stats = auto_extend_sections(sections, size="solo", branche="beratung")

        # Should have extended roadmap_12m
        assert isinstance(stats, dict)

    def test_leaves_adequate_sections(self):
        """Should not extend sections above minimum."""
        from services.llm_postprocessor import auto_extend_sections

        # Create content well above minimum
        long_content = "<p>" + " ".join(["word"] * 1000) + "</p>"

        sections = {
            "roadmap_12m": long_content,
        }

        stats = auto_extend_sections(sections, size="solo", branche="beratung")

        # roadmap_12m should have 0 words added
        roadmap_stat = stats.get("roadmap_12m", 0)
        assert roadmap_stat == 0


class TestPromptManifestTokens:
    """Test token limits in prompt_manifest.json."""

    def test_roadmap_12m_tokens_increased(self):
        """roadmap_12m should have increased token budget (≥4800)."""
        import json
        import os

        manifest_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "prompt_manifest.json"
        )

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Check DE section
        de_roadmap = manifest.get("de", {}).get("roadmap_12m", {})
        de_tokens = de_roadmap.get("tokens", {})
        base_tokens = de_tokens.get("base", 0)

        assert base_tokens >= 4800, \
            f"roadmap_12m base tokens should be ≥4800, got {base_tokens}"

    def test_manifest_version_updated(self):
        """Manifest version should reflect N3.1 changes."""
        import json
        import os

        manifest_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "prompt_manifest.json"
        )

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        meta = manifest.get("_meta", {})
        version = meta.get("version", "")
        sprint = meta.get("sprint", "")

        # Should mention N3.1
        assert "5.5" in version or "N3.1" in sprint, \
            f"Manifest should be updated for N3.1, got version={version}, sprint={sprint}"
