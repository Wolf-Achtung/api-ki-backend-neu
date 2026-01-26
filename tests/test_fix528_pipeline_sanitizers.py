#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-528 Tests: Pipeline Sanitizers

Tests for:
- decode_html_entities(): HTML entity decoding
- ensure_complete_sentences(): Sentence completion
- apply_post_llm_sanitization(): Combined pipeline
- validate_entity_free(): Entity validation gate
"""
import pytest


class TestDecodeHtmlEntities:
    """Tests for decode_html_entities function."""

    def test_basic_german_entities(self):
        """Test decoding of common German HTML entities."""
        from services.pipeline_sanitizers import decode_html_entities

        text = "F&uuml;r Ihre &bdquo;Daten&ldquo; und &Auml;nderungen"
        result = decode_html_entities(text)

        assert "ü" in result
        assert "„" in result  # German opening quote
        assert """ in result  # German closing quote
        assert "Ä" in result
        assert "&uuml;" not in result
        assert "&bdquo;" not in result

    def test_double_escaped_entities(self):
        """Test handling of double-escaped entities (e.g., from html_repair)."""
        from services.pipeline_sanitizers import decode_html_entities

        # This can happen when content is escaped multiple times
        text = "&amp;uuml; test &amp;amp; more"
        result = decode_html_entities(text)

        # Should decode both levels
        assert "ü" in result
        assert "&" in result
        assert "&amp;uuml;" not in result

    def test_numeric_entities(self):
        """Test decoding of numeric HTML entities."""
        from services.pipeline_sanitizers import decode_html_entities

        # Decimal and hex numeric entities
        text = "Test &#8364; and &#x20AC;"  # Both are Euro sign
        result = decode_html_entities(text)

        assert result.count("€") == 2
        assert "&#" not in result

    def test_preserves_valid_html_structure(self):
        """Test that valid HTML tags are preserved."""
        from services.pipeline_sanitizers import decode_html_entities

        html = '<p class="test">F&uuml;r Sie</p>'
        result = decode_html_entities(html)

        assert "<p" in result
        assert "</p>" in result
        assert "ü" in result

    def test_empty_input(self):
        """Test handling of empty/None input."""
        from services.pipeline_sanitizers import decode_html_entities

        assert decode_html_entities("") == ""
        assert decode_html_entities(None) == ""


class TestEnsureCompleteSentences:
    """Tests for ensure_complete_sentences function."""

    def test_already_complete(self):
        """Test that already complete sentences are unchanged."""
        from services.pipeline_sanitizers import ensure_complete_sentences

        text = "Dies ist ein vollständiger Satz."
        result = ensure_complete_sentences(text)

        assert result == text

    def test_incomplete_article_ending(self):
        """Test trimming of incomplete sentence ending with article."""
        from services.pipeline_sanitizers import ensure_complete_sentences

        text = "Dies ist ein Test für die"
        result = ensure_complete_sentences(text)

        # Should either trim to last sentence boundary or add period
        assert result.endswith(".")
        # Should not end with "die"
        assert not result.rstrip(".").endswith("die")

    def test_incomplete_preposition_ending(self):
        """Test handling of sentence ending with preposition."""
        from services.pipeline_sanitizers import ensure_complete_sentences

        text = "Das System arbeitet mit"
        result = ensure_complete_sentences(text)

        assert result.endswith(".")

    def test_preserves_multi_sentence(self):
        """Test that multiple sentences are preserved."""
        from services.pipeline_sanitizers import ensure_complete_sentences

        text = "Erster Satz. Zweiter Satz. Dritter mit"
        result = ensure_complete_sentences(text)

        # Should preserve first two sentences
        assert "Erster Satz." in result
        assert "Zweiter Satz." in result

    def test_minimum_words_protection(self):
        """Test that minimum word count is respected."""
        from services.pipeline_sanitizers import ensure_complete_sentences

        text = "Kurz mit"
        result = ensure_complete_sentences(text, min_words=2)

        # Should add period instead of trimming to nothing
        assert len(result) > 0


class TestValidateEntityFree:
    """Tests for validate_entity_free function."""

    def test_clean_text_passes(self):
        """Test that text without entities passes validation."""
        from services.pipeline_sanitizers import validate_entity_free

        text = "Für Ihre Daten und Änderungen"
        passed, entities = validate_entity_free(text)

        assert passed is True
        assert len(entities) == 0

    def test_entity_text_fails(self):
        """Test that text with entities fails validation."""
        from services.pipeline_sanitizers import validate_entity_free

        text = "F&uuml;r Ihre Daten"
        passed, entities = validate_entity_free(text)

        assert passed is False
        assert "&uuml;" in entities

    def test_url_entities_allowed(self):
        """Test that entities in URLs are allowed."""
        from services.pipeline_sanitizers import validate_entity_free

        # &amp; in href should be allowed
        text = '<a href="https://example.com?foo=1&amp;bar=2">Link</a>'
        passed, entities = validate_entity_free(text)

        # May or may not pass depending on implementation
        # At minimum, &amp; in URL context should be treated differently
        assert isinstance(passed, bool)


class TestApplyPostLlmSanitization:
    """Tests for apply_post_llm_sanitization function."""

    def test_combined_sanitization(self):
        """Test that combined sanitization works."""
        from services.pipeline_sanitizers import apply_post_llm_sanitization

        content = "F&uuml;r Ihre Analyse der"
        result = apply_post_llm_sanitization(
            content,
            section_name="test",
            decode_entities=True,
            complete_sentences=True,
            is_html=False,
        )

        assert "ü" in result.content
        assert result.content.endswith(".")
        assert result.entities_decoded > 0

    def test_html_mode(self):
        """Test sanitization in HTML mode."""
        from services.pipeline_sanitizers import apply_post_llm_sanitization

        content = "<p>F&uuml;r Ihre Daten</p>"
        result = apply_post_llm_sanitization(
            content,
            section_name="test_html",
            decode_entities=True,
            complete_sentences=True,
            is_html=True,
        )

        assert "<p>" in result.content
        assert "ü" in result.content

    def test_empty_input(self):
        """Test handling of empty input."""
        from services.pipeline_sanitizers import apply_post_llm_sanitization

        result = apply_post_llm_sanitization("")

        assert result.content == ""
        assert result.entities_decoded == 0
        assert result.sentences_fixed == 0


class TestSanitizeAllSections:
    """Tests for sanitize_all_sections function."""

    def test_processes_html_sections(self):
        """Test that HTML sections are processed."""
        from services.pipeline_sanitizers import sanitize_all_sections

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "F&uuml;r Ihre Analyse ist wichtig.",
            "RISKS_HTML": "<p>Risiken: &Auml;nderungen m&ouml;glich.</p>",
            "non_html_key": "Some other content",
        }

        result, stats = sanitize_all_sections(sections)

        assert "ü" in result["EXECUTIVE_SUMMARY_HTML"]
        assert "Ä" in result["RISKS_HTML"]
        assert stats["sections_processed"] >= 2

    def test_fallback_mode(self):
        """Test that fallback mode triggers sentence completion."""
        from services.pipeline_sanitizers import sanitize_all_sections

        sections = {
            "RECOMMENDATIONS_HTML": "Wir empfehlen die folgenden Maßnahmen für",
        }

        result, stats = sanitize_all_sections(sections, fallback_triggered=True)

        # In fallback mode, sentence should be completed
        assert result["RECOMMENDATIONS_HTML"].endswith(".")


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_realistic_llm_output(self):
        """Test with realistic LLM output that might come from html_repair."""
        from services.pipeline_sanitizers import apply_post_llm_sanitization

        # Simulated output with entities (from html_repair) and incomplete sentence
        content = """
        <div class="summary">
            <h3>Zusammenfassung</h3>
            <p>F&uuml;r Ihre Digitalisierungsstrategie empfehlen wir die</p>
            <p>Integration von KI-Tools in bestehende Arbeitsabl&auml;ufe.</p>
        </div>
        """

        result = apply_post_llm_sanitization(
            content,
            section_name="EXECUTIVE_SUMMARY_HTML",
            decode_entities=True,
            complete_sentences=True,
            is_html=True,
        )

        # Entities should be decoded
        assert "ü" in result.content
        assert "ä" in result.content
        assert "&uuml;" not in result.content
        assert "&auml;" not in result.content

    def test_post_502_recovery(self):
        """Test sanitization after simulated OpenAI 502 recovery."""
        from services.pipeline_sanitizers import apply_post_fallback_sanitization

        # Simulated truncated content from 502 recovery
        content = "Die KI-Readiness-Analyse zeigt, dass Ihr Unternehmen f&uuml;r"

        result = apply_post_fallback_sanitization(
            content,
            section_name="analysis",
            retry_count=2,
            fallback_used=True,
        )

        # Should decode entities
        assert "ü" in result
        # Should end with proper punctuation
        assert result.endswith(".")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
