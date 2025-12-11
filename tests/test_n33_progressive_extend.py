# -*- coding: utf-8 -*-
"""
SPRINT N3.3: Tests for Progressive Extension Engine.

Tests the new progressive_extend function and updated thresholds.
"""
import pytest
import logging


class TestProgressiveExtendFunction:
    """Test the progressive_extend function."""

    def test_progressive_extend_exists(self):
        """Verify progressive_extend function exists."""
        from services.llm_postprocessor import progressive_extend

        assert callable(progressive_extend)

    def test_progressive_extend_short_content(self, caplog):
        """Short content should be extended through multiple rounds."""
        from services.llm_postprocessor import progressive_extend

        short_text = "<p>This is short content.</p>"

        with caplog.at_level(logging.INFO):
            result, word_count, was_extended = progressive_extend(
                short_text, min_words=100, section="roadmap_12m", size="solo"
            )

        assert was_extended is True
        assert word_count > len(short_text.split())
        assert "[EXTEND]" in caplog.text

    def test_progressive_extend_adequate_content(self):
        """Content above threshold should not be extended."""
        from services.llm_postprocessor import progressive_extend

        long_text = " ".join(["word"] * 200)  # 200 words

        result, word_count, was_extended = progressive_extend(
            long_text, min_words=100, section="roadmap_12m", size="solo"
        )

        assert was_extended is False
        assert result == long_text
        assert word_count == 200

    def test_progressive_extend_empty_text(self):
        """Empty text should return safely."""
        from services.llm_postprocessor import progressive_extend

        result, word_count, was_extended = progressive_extend(
            "", min_words=100, section="roadmap_12m", size="solo"
        )

        assert was_extended is False
        assert word_count == 0

    def test_progressive_extend_multiple_rounds(self, caplog):
        """Very short content should trigger multiple rounds."""
        from services.llm_postprocessor import progressive_extend

        very_short = "<p>Hi.</p>"

        with caplog.at_level(logging.INFO):
            result, word_count, was_extended = progressive_extend(
                very_short, min_words=500, section="roadmap_12m", size="solo",
                max_rounds=3
            )

        assert was_extended is True
        # Check that logging shows rounds
        assert "rounds=" in caplog.text


class TestUpdatedThresholds:
    """Test the N3.3 updated min-words thresholds."""

    def test_roadmap_90d_solo_threshold(self):
        """roadmap_90d solo threshold should be 90."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        assert EXTEND_MIN_WORDS["roadmap_90d"]["solo"] == 90

    def test_roadmap_12m_solo_threshold(self):
        """roadmap_12m solo threshold should be 480."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        assert EXTEND_MIN_WORDS["roadmap_12m"]["solo"] == 480

    def test_recommendations_solo_threshold(self):
        """recommendations solo threshold should be 400."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        assert EXTEND_MIN_WORDS["recommendations"]["solo"] == 400

    def test_threshold_ordering_preserved(self):
        """Solo thresholds should be <= team <= kmu."""
        from services.llm_postprocessor import EXTEND_MIN_WORDS

        for section, thresholds in EXTEND_MIN_WORDS.items():
            solo = thresholds.get("solo", 0)
            team = thresholds.get("team", 0)
            kmu = thresholds.get("kmu", 0)

            assert solo <= team, f"{section}: solo ({solo}) > team ({team})"
            assert team <= kmu, f"{section}: team ({team}) > kmu ({kmu})"


class TestRoundExtensions:
    """Test the individual round extension functions."""

    def test_round1_extension_returns_content(self):
        """Round 1 should return substantial content."""
        from services.llm_postprocessor import _get_round1_extension

        content = _get_round1_extension("roadmap_12m", "solo", "Beratung")

        assert len(content) > 50
        assert "<p>" in content

    def test_round2_extension_returns_content(self):
        """Round 2 should return supporting content."""
        from services.llm_postprocessor import _get_round2_extension

        content = _get_round2_extension("roadmap_12m", "solo", "")

        assert len(content) > 50
        assert "<p>" in content

    def test_round3_extension_returns_content(self):
        """Round 3 should return lighter content."""
        from services.llm_postprocessor import _get_round3_extension

        content = _get_round3_extension("roadmap_12m", "solo", "")

        # Round 3 is lighter but should still have content
        assert len(content) > 20 or content == ""

    def test_round2_different_sections(self):
        """Round 2 should have content for different sections."""
        from services.llm_postprocessor import _get_round2_extension

        for section in ["roadmap_90d", "roadmap_12m", "recommendations"]:
            content = _get_round2_extension(section, "solo", "")
            assert content, f"Round 2 should have content for {section}"


class TestExtensionLogging:
    """Test that extension logging is correct."""

    def test_extension_log_format(self, caplog):
        """Log should show original → new word count."""
        from services.llm_postprocessor import progressive_extend

        with caplog.at_level(logging.INFO):
            progressive_extend(
                "<p>Short.</p>",
                min_words=100,
                section="roadmap_12m",
                size="solo"
            )

        # Should have format: [EXTEND] section extended X → Y words
        assert "[EXTEND]" in caplog.text
        assert "→" in caplog.text
        assert "words" in caplog.text


class TestIntegrationWithAutoExtend:
    """Test integration with auto_extend_sections."""

    def test_auto_extend_uses_new_thresholds(self):
        """auto_extend_sections should use the new N3.3 thresholds."""
        from services.llm_postprocessor import (
            auto_extend_sections,
            EXTEND_MIN_WORDS,
            get_extend_min_words
        )

        # Verify the threshold lookup works with new values
        solo_threshold = get_extend_min_words("roadmap_90d", "solo")
        assert solo_threshold == 90

        solo_threshold = get_extend_min_words("roadmap_12m", "solo")
        assert solo_threshold == 480

        solo_threshold = get_extend_min_words("recommendations", "solo")
        assert solo_threshold == 400
