#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-529 Tests: Lexicon Loader

Tests for:
- Lexicon loading from JSON files
- Term replacement application
- Size mismatch validation
"""
import pytest


class TestLexiconLoading:
    """Tests for lexicon loading."""

    def test_load_solo_lexicon(self):
        """Test loading solo lexicon."""
        from services.lexicon_loader import load_lexicon

        lexicon = load_lexicon("solo")

        assert lexicon is not None
        assert lexicon.target_persona == "solo"
        assert lexicon.rule_count > 0

    def test_load_team_lexicon(self):
        """Test loading team lexicon."""
        from services.lexicon_loader import load_lexicon

        lexicon = load_lexicon("team")

        assert lexicon is not None
        assert lexicon.target_persona == "team"
        assert lexicon.rule_count > 0

    def test_load_invalid_persona(self):
        """Test loading with invalid persona."""
        from services.lexicon_loader import load_lexicon

        lexicon = load_lexicon("invalid_persona")

        assert lexicon is None


class TestLexiconApplication:
    """Tests for lexicon application."""

    def test_apply_solo_replacements(self):
        """Test applying solo lexicon replacements."""
        from services.lexicon_loader import apply_lexicon

        text = "Die Module der Architektur basieren auf einem Stack."
        result, count = apply_lexicon(text, "solo")

        assert count > 0
        assert "Bausteine" in result  # Module -> Bausteine
        assert "Struktur" in result   # Architektur -> Struktur
        assert "Technikpaket" in result  # Stack -> Technikpaket

    def test_apply_no_changes_needed(self):
        """Test when no replacements are needed."""
        from services.lexicon_loader import apply_lexicon

        text = "Dies ist ein einfacher Satz ohne Fachbegriffe."
        result, count = apply_lexicon(text, "solo")

        assert count == 0
        assert result == text

    def test_apply_to_empty_text(self):
        """Test application to empty text."""
        from services.lexicon_loader import apply_lexicon

        result, count = apply_lexicon("", "solo")

        assert count == 0
        assert result == ""


class TestSizeMismatchValidation:
    """Tests for size mismatch validation."""

    def test_validate_clean_text(self):
        """Test validation of text without mismatches."""
        from services.lexicon_loader import validate_size_mismatch

        text = "Einfacher Text ohne Fachbegriffe fuer Solo-Nutzer."
        is_valid, mismatches = validate_size_mismatch(text, "solo")

        assert is_valid is True
        assert len(mismatches) == 0

    def test_validate_text_with_mismatches(self):
        """Test validation of text with size mismatches."""
        from services.lexicon_loader import validate_size_mismatch

        text = "Die Stakeholder analysieren die Pipeline der Architektur."
        is_valid, mismatches = validate_size_mismatch(text, "solo")

        assert is_valid is False
        assert len(mismatches) > 0


class TestSectionApplication:
    """Tests for section-level application."""

    def test_apply_to_sections(self):
        """Test applying lexicon to multiple sections."""
        from services.lexicon_loader import apply_lexicon_to_sections

        sections = {
            "SUMMARY_HTML": "<p>Die Module des Projekts sind in einem Stack organisiert.</p>" * 3,
            "RISKS_HTML": "<p>Risiken der Architektur werden analysiert.</p>" * 3,
            "SHORT_TEXT": "Kurz",  # Too short, should be skipped
        }

        processed, stats = apply_lexicon_to_sections(sections, "solo")

        assert stats["total_replacements"] > 0
        assert stats["sections_processed"] >= 2
        assert "Bausteine" in processed["SUMMARY_HTML"]
        assert processed["SHORT_TEXT"] == "Kurz"  # Unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
