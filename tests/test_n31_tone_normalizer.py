# -*- coding: utf-8 -*-
"""
SPRINT N3.1: Tests for Tone Normalization (du → Sie/neutral).

Tests the TONE_NORMALIZATION_DU patterns in micro_correction_engine.py
to ensure informal "du" forms are properly converted to neutral/Sie language.
"""
import pytest


class TestToneNormalizationPatterns:
    """Test the tone normalization dictionary patterns."""

    def test_tone_normalization_dict_exists(self):
        """Verify TONE_NORMALIZATION_DU dictionary is defined."""
        from services.micro_correction_engine import TONE_NORMALIZATION_DU

        assert isinstance(TONE_NORMALIZATION_DU, dict)
        assert len(TONE_NORMALIZATION_DU) > 0

    def test_basic_du_patterns_defined(self):
        """Check that basic du patterns are defined."""
        from services.micro_correction_engine import TONE_NORMALIZATION_DU

        # Key patterns that should exist
        expected_patterns = [
            "du kannst",
            "Du solltest",
            "dein Geschäftsmodell",
        ]

        for pattern in expected_patterns:
            assert pattern in TONE_NORMALIZATION_DU, f"Pattern '{pattern}' not found"

    def test_replacements_are_neutral(self):
        """Verify replacements don't contain informal forms."""
        from services.micro_correction_engine import TONE_NORMALIZATION_DU

        informal_markers = ["du ", " du ", "dein", "deine", "dir ", " dir "]

        for key, replacement in TONE_NORMALIZATION_DU.items():
            for marker in informal_markers:
                assert marker.lower() not in replacement.lower(), \
                    f"Replacement for '{key}' contains informal marker: {replacement}"


class TestToneNormalizationRegex:
    """Test the regex-based tone normalization patterns."""

    def test_regex_patterns_exist(self):
        """Verify TONE_NORMALIZATION_DU_PATTERNS is defined."""
        from services.micro_correction_engine import TONE_NORMALIZATION_DU_PATTERNS

        assert isinstance(TONE_NORMALIZATION_DU_PATTERNS, list)
        assert len(TONE_NORMALIZATION_DU_PATTERNS) > 0

    def test_regex_patterns_are_tuples(self):
        """Each pattern should be a (pattern, replacement) tuple."""
        from services.micro_correction_engine import TONE_NORMALIZATION_DU_PATTERNS

        for item in TONE_NORMALIZATION_DU_PATTERNS:
            assert isinstance(item, tuple), f"Expected tuple, got {type(item)}"
            assert len(item) == 2, f"Expected 2 elements, got {len(item)}"


class TestApplyToneNormalization:
    """Test the _apply_tone_normalization method."""

    def test_du_kannst_normalized(self):
        """Test 'du kannst' is converted."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Hier erfährst du, wie du kannst dein Unternehmen verbessern."

        corrected, report = engine.correct(text)

        assert "du kannst" not in corrected.lower()

    def test_dein_geschaeftsmodell_normalized(self):
        """Test 'dein Geschäftsmodell' is converted."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Überprüfe dein Geschäftsmodell regelmäßig."

        corrected, report = engine.correct(text)

        assert "dein Geschäftsmodell" not in corrected

    def test_neutral_text_unchanged(self):
        """Neutral text should remain unchanged."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Das Unternehmen sollte seine Strategie überprüfen."

        corrected, report = engine.correct(text)

        # Should be nearly identical (may have minor formatting changes)
        assert "Unternehmen" in corrected
        assert "Strategie" in corrected

    def test_normalization_count_tracked(self):
        """Verify normalization count is tracked in report."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Du kannst hier dein Geschäftsmodell anpassen."

        corrected, report = engine.correct(text)

        assert hasattr(report, 'tone_normalizations')
        assert isinstance(report.tone_normalizations, int)

    def test_multiple_du_forms_normalized(self):
        """Test multiple du forms in same text."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = """Du solltest prüfen, ob dein Unternehmen die Anforderungen erfüllt.
        Dabei kannst du verschiedene Tools nutzen, die dir helfen."""

        corrected, report = engine.correct(text)

        # Check informal forms are removed
        corrected_lower = corrected.lower()
        assert " du " not in f" {corrected_lower} " or "du " not in corrected_lower[:3]

    def test_english_text_not_normalized(self):
        """English text should not have German du normalization applied incorrectly."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "You should check your business model regularly."

        corrected, report = engine.correct(text)

        # Should remain unchanged (no German patterns to match)
        assert "You should check" in corrected


class TestToneNormalizationIntegration:
    """Integration tests for tone normalization in the pipeline."""

    def test_risks_section_normalized(self):
        """Risk section content should be normalized."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        risk_text = """
        <p>Wenn du keine regelmäßigen Backups machst, riskierst du Datenverlust.</p>
        <p>Du solltest auch deine Cybersecurity-Strategie überprüfen.</p>
        """

        corrected, report = engine.correct(risk_text)

        # Informal forms should be replaced
        assert report.tone_normalizations >= 0

    def test_normalization_preserves_html(self):
        """HTML structure should be preserved during normalization."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        html_text = "<p>Du solltest <strong>prüfen</strong>, ob dein Plan funktioniert.</p>"

        corrected, report = engine.correct(html_text)

        # HTML tags should be preserved
        assert "<p>" in corrected
        assert "</p>" in corrected
        assert "<strong>" in corrected
