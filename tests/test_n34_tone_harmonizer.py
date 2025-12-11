# -*- coding: utf-8 -*-
"""
SPRINT N3.4: Tests for Tone Harmonizer v3 - Big-Four Consulting Style.

Tests consulting tone replacements and avoid list.
"""
import pytest


class TestConsultingAvoidList:
    """Test the CONSULTING_AVOID_LIST constant."""

    def test_avoid_list_exists(self):
        """CONSULTING_AVOID_LIST should exist."""
        from services.micro_correction_engine import CONSULTING_AVOID_LIST

        assert isinstance(CONSULTING_AVOID_LIST, list)
        assert len(CONSULTING_AVOID_LIST) > 10

    def test_contains_gpt_phrases(self):
        """Avoid list should contain common GPT phrases."""
        from services.micro_correction_engine import CONSULTING_AVOID_LIST

        assert "kannst du" in CONSULTING_AVOID_LIST
        assert "du solltest" in CONSULTING_AVOID_LIST
        assert "wie kann ich helfen" in CONSULTING_AVOID_LIST
        assert "könnte hilfreich sein" in CONSULTING_AVOID_LIST

    def test_contains_filler_phrases(self):
        """Avoid list should contain filler phrases."""
        from services.micro_correction_engine import CONSULTING_AVOID_LIST

        assert "es wäre wichtig zu beachten" in CONSULTING_AVOID_LIST
        assert "zusammenfassend lässt sich sagen" in CONSULTING_AVOID_LIST


class TestBigFourReplacements:
    """Test the BIG_FOUR_REPLACEMENTS dictionary."""

    def test_replacements_exist(self):
        """BIG_FOUR_REPLACEMENTS should exist."""
        from services.micro_correction_engine import BIG_FOUR_REPLACEMENTS

        assert isinstance(BIG_FOUR_REPLACEMENTS, dict)
        assert len(BIG_FOUR_REPLACEMENTS) > 15

    def test_weak_to_strong(self):
        """Should have weak → strong formulation replacements."""
        from services.micro_correction_engine import BIG_FOUR_REPLACEMENTS

        assert BIG_FOUR_REPLACEMENTS.get("könnte sinnvoll sein") == "empfiehlt sich"
        assert BIG_FOUR_REPLACEMENTS.get("wäre empfehlenswert") == "ist empfehlenswert"

    def test_passive_to_active(self):
        """Should have passive → active voice replacements."""
        from services.micro_correction_engine import BIG_FOUR_REPLACEMENTS

        assert BIG_FOUR_REPLACEMENTS.get("es wird empfohlen") == "empfehlenswert ist"
        assert BIG_FOUR_REPLACEMENTS.get("es ist wichtig") == "zentral ist"

    def test_gpt_support_phrases_removed(self):
        """GPT support phrases should map to empty string."""
        from services.micro_correction_engine import BIG_FOUR_REPLACEMENTS

        assert BIG_FOUR_REPLACEMENTS.get("Gerne helfe ich") == ""
        assert BIG_FOUR_REPLACEMENTS.get("gerne erkläre ich") == ""


class TestHarmonizeConsultingTone:
    """Test the harmonize_consulting_tone function."""

    def test_function_exists(self):
        """harmonize_consulting_tone should exist."""
        from services.micro_correction_engine import harmonize_consulting_tone

        assert callable(harmonize_consulting_tone)

    def test_removes_avoid_phrases(self):
        """Should remove phrases from avoid list."""
        from services.micro_correction_engine import harmonize_consulting_tone

        text = "Es wäre wichtig zu beachten, dass KI wichtig ist."
        result, count = harmonize_consulting_tone(text)

        assert "es wäre wichtig zu beachten" not in result.lower()
        assert count > 0

    def test_applies_big_four_replacements(self):
        """Should apply Big-Four style replacements."""
        from services.micro_correction_engine import harmonize_consulting_tone

        text = "Es könnte sinnvoll sein, hier zu investieren."
        result, count = harmonize_consulting_tone(text)

        assert "empfiehlt sich" in result
        assert "könnte sinnvoll sein" not in result

    def test_removes_gpt_support_phrases(self):
        """Should remove GPT support phrases."""
        from services.micro_correction_engine import harmonize_consulting_tone

        text = "Gerne helfe ich Ihnen. Hier sind die Empfehlungen."
        result, count = harmonize_consulting_tone(text)

        assert "Gerne helfe ich" not in result
        assert "Empfehlungen" in result

    def test_preserves_case(self):
        """Should preserve capitalization."""
        from services.micro_correction_engine import harmonize_consulting_tone

        text = "Es ist wichtig, das zu beachten."
        result, count = harmonize_consulting_tone(text)

        # "Es ist wichtig" → "Zentral ist"
        assert "Zentral ist" in result or "zentral ist" in result

    def test_cleans_artifacts(self):
        """Should clean up double spaces and empty paragraphs."""
        from services.micro_correction_engine import harmonize_consulting_tone

        text = "Text  mit   Leerzeichen.. und Punkten."
        result, count = harmonize_consulting_tone(text)

        assert "  " not in result
        assert ".." not in result

    def test_handles_empty_text(self):
        """Should handle empty text gracefully."""
        from services.micro_correction_engine import harmonize_consulting_tone

        result, count = harmonize_consulting_tone("")
        assert result == ""
        assert count == 0


class TestApplyConsultingToneToSections:
    """Test the apply_consulting_tone_to_sections function."""

    def test_function_exists(self):
        """apply_consulting_tone_to_sections should exist."""
        from services.micro_correction_engine import apply_consulting_tone_to_sections

        assert callable(apply_consulting_tone_to_sections)

    def test_processes_all_sections(self):
        """Should process all sections when no target specified."""
        from services.micro_correction_engine import apply_consulting_tone_to_sections

        sections = {
            "exec_summary": "Es könnte sinnvoll sein zu investieren.",
            "recommendations": "Es wäre empfehlenswert, dies umzusetzen.",
        }

        result, count = apply_consulting_tone_to_sections(sections)

        assert "empfiehlt sich" in result["exec_summary"]
        assert "ist empfehlenswert" in result["recommendations"]
        assert count >= 2

    def test_filters_by_target_sections(self):
        """Should only process target sections when specified."""
        from services.micro_correction_engine import apply_consulting_tone_to_sections

        sections = {
            "exec_summary": "Es könnte sinnvoll sein zu investieren.",
            "other_section": "Es könnte sinnvoll sein hier auch.",
        }

        result, count = apply_consulting_tone_to_sections(
            sections,
            target_sections={"exec_summary"}
        )

        # exec_summary should be processed
        assert "empfiehlt sich" in result["exec_summary"]
        # other_section should be unchanged
        assert "könnte sinnvoll sein" in result["other_section"]

    def test_handles_empty_sections(self):
        """Should handle empty sections gracefully."""
        from services.micro_correction_engine import apply_consulting_tone_to_sections

        sections = {
            "exec_summary": "",
            "recommendations": None,
        }

        result, count = apply_consulting_tone_to_sections(sections)

        assert result["exec_summary"] == ""
        assert count == 0


class TestConsultingStyleOutput:
    """Test that output has consulting style."""

    def test_no_weak_formulations(self):
        """Output should not have weak formulations."""
        from services.micro_correction_engine import harmonize_consulting_tone

        text = """
        Es könnte sinnvoll sein, hier zu investieren.
        Es wäre empfehlenswert, diese Maßnahmen umzusetzen.
        Man sollte bedenken, dass dies wichtig ist.
        """
        result, count = harmonize_consulting_tone(text)

        weak_phrases = [
            "könnte sinnvoll sein",
            "wäre empfehlenswert",
            "sollte bedenken",
        ]

        for phrase in weak_phrases:
            assert phrase not in result

    def test_has_strong_formulations(self):
        """Output should have strong consulting formulations."""
        from services.micro_correction_engine import harmonize_consulting_tone

        text = "Es könnte sinnvoll sein. Es wäre empfehlenswert."
        result, count = harmonize_consulting_tone(text)

        # Should have consulting-style replacements
        assert "empfiehlt sich" in result or "ist empfehlenswert" in result

    def test_multiple_replacements(self):
        """Should handle multiple replacements in same text."""
        from services.micro_correction_engine import harmonize_consulting_tone

        text = """
        Es ist wichtig, dies zu beachten.
        Es wird empfohlen, zu investieren.
        Zusammenfassend lässt sich sagen: alles gut.
        """
        result, count = harmonize_consulting_tone(text)

        assert count >= 2
        # Should not have GPT phrases
        assert "es ist wichtig" not in result.lower() or "zentral ist" in result.lower()


class TestSentenceTargets:
    """Test sentence length target constants."""

    def test_targets_exist(self):
        """Sentence length targets should exist."""
        from services.micro_correction_engine import (
            CONSULTING_SENTENCE_TARGET_MIN,
            CONSULTING_SENTENCE_TARGET_MAX,
        )

        assert CONSULTING_SENTENCE_TARGET_MIN == 18
        assert CONSULTING_SENTENCE_TARGET_MAX == 24

    def test_target_range_valid(self):
        """Target range should be valid."""
        from services.micro_correction_engine import (
            CONSULTING_SENTENCE_TARGET_MIN,
            CONSULTING_SENTENCE_TARGET_MAX,
        )

        assert CONSULTING_SENTENCE_TARGET_MIN < CONSULTING_SENTENCE_TARGET_MAX
        assert CONSULTING_SENTENCE_TARGET_MIN > 0
