"""
Tests for FIX-52x Final Polish functions.

These tests verify the final pipeline steps that run LAST to catch
any artifacts introduced by earlier LLM-powered or template-based steps.
"""

import pytest
from services.content_quality_enforcer import (
    strip_template_phrases_final,
    _dedupe_long_paragraphs,
    strip_trailing_sentence_fragments,
    apply_solo_terms_final,
    apply_all_quality_enforcers,
)


# =============================================================================
# PRIO 1: strip_template_phrases_final
# =============================================================================

class TestStripTemplatePhrasesFinal:
    """Tests for comprehensive template phrase stripping."""

    def test_removes_platzhalter(self):
        """Should remove 'Platzhalter' from content."""
        sections = {
            "QUICK_WINS_HTML": "<p>Hier ist ein Platzhalter für Text.</p>"
        }
        result = strip_template_phrases_final(sections)
        assert "Platzhalter" not in result["QUICK_WINS_HTML"]

    def test_removes_bracketed_placeholders(self):
        """Should remove [TODO] and [Platzhalter...] patterns."""
        sections = {
            "BUSINESS_CASE_HTML": "<p>Text [TODO: add details] here [Platzhalter einfügen].</p>"
        }
        result = strip_template_phrases_final(sections)
        assert "[TODO" not in result["BUSINESS_CASE_HTML"]
        assert "[Platzhalter" not in result["BUSINESS_CASE_HTML"]

    def test_removes_jinja2_artifacts(self):
        """Should remove Jinja2 template markers that leaked."""
        sections = {
            "PILOT_PLAN_HTML": "<p>Text with {{variable}} and {% if condition %}.</p>"
        }
        result = strip_template_phrases_final(sections)
        assert "{{" not in result["PILOT_PLAN_HTML"]
        assert "{%" not in result["PILOT_PLAN_HTML"]

    def test_skips_internal_keys(self):
        """Should not process keys starting with underscore."""
        sections = {
            "_VALIDATOR_WARNING_LIST": ["Platzhalter warning"],
            "QUICK_WINS_HTML": "<p>Clean content</p>"
        }
        result = strip_template_phrases_final(sections)
        assert "Platzhalter" in str(result["_VALIDATOR_WARNING_LIST"])

    def test_removes_prompt_echo_patterns(self):
        """Should remove leaked prompt instructions."""
        sections = {
            "RECOMMENDATIONS_HTML": "Erstelle mir einen detaillierten Abschnitt über KI.\n<p>Actual content.</p>"
        }
        result = strip_template_phrases_final(sections)
        assert "Erstelle mir" not in result["RECOMMENDATIONS_HTML"]


# =============================================================================
# PRIO 2: apply_solo_terms_final
# =============================================================================

class TestApplySoloTermsFinal:
    """Tests for final solo term replacement."""

    def test_replaces_enterprise_terms_for_solo(self):
        """Should replace enterprise terms for solo persona."""
        sections = {
            "QUICK_WINS_HTML": "<p>Nutzen Sie unsere Skalierung und Stakeholder-Management.</p>"
        }
        result = apply_solo_terms_final(sections, "solo")
        assert "Skalierung" not in result["QUICK_WINS_HTML"]
        assert "Stakeholder" not in result["QUICK_WINS_HTML"]
        assert "Ausbau" in result["QUICK_WINS_HTML"]
        assert "Beteiligte" in result["QUICK_WINS_HTML"]

    def test_skips_non_solo_personas(self):
        """Should not modify content for non-solo personas."""
        sections = {
            "QUICK_WINS_HTML": "<p>Nutzen Sie unsere Skalierung.</p>"
        }
        result = apply_solo_terms_final(sections, "team")
        assert "Skalierung" in result["QUICK_WINS_HTML"]

        result = apply_solo_terms_final(sections, "kmu")
        assert "Skalierung" in result["QUICK_WINS_HTML"]

    def test_replaces_engine_terms(self):
        """Should replace Engine-related terms."""
        sections = {
            "RECOMMENDATIONS_HTML": "<p>Die Risk-Engine und Business-Case-Engine.</p>"
        }
        result = apply_solo_terms_final(sections, "solo")
        assert "Risk-Engine" not in result["RECOMMENDATIONS_HTML"]
        assert "Business-Case-Engine" not in result["RECOMMENDATIONS_HTML"]

    def test_replaces_stack_terms(self):
        """Should replace Stack-related terms."""
        sections = {
            "PILOT_PLAN_HTML": "<p>Tech-Stack und Tool-Stack aufbauen.</p>"
        }
        result = apply_solo_terms_final(sections, "solo")
        assert "Tech-Stack" not in result["PILOT_PLAN_HTML"]
        assert "Tool-Stack" not in result["PILOT_PLAN_HTML"]


# =============================================================================
# PRIO 3: _dedupe_long_paragraphs
# =============================================================================

class TestDedupeLongParagraphs:
    """Tests for paragraph deduplication."""

    def test_removes_duplicate_paragraphs(self):
        """Should remove second occurrence of duplicate long paragraphs."""
        # Long text without any < characters (as the regex requires [^<]{150,})
        # Must be at least 150 characters
        long_text = "Dies ist ein langer Absatz mit mehr als 150 Zeichen, der mehrfach vorkommt. Er enthaelt viele Woerter und ist lang genug um erkannt zu werden. Zusaetzlicher Text."
        assert len(long_text) >= 150, f"Test text must be >= 150 chars, got {len(long_text)}"
        sections = {
            "BUSINESS_CASE_HTML": f"<p>{long_text}</p><p>Different content here.</p><p>{long_text}</p>"
        }
        result = _dedupe_long_paragraphs(sections)
        # Should have only one occurrence of the long paragraph
        count = result["BUSINESS_CASE_HTML"].count(long_text)
        assert count == 1, f"Expected 1 occurrence but found {count}"

    def test_keeps_short_duplicate_paragraphs(self):
        """Should not remove duplicates shorter than 150 chars."""
        short_text = "Kurzer Text."
        sections = {
            "QUICK_WINS_HTML": f"<p>{short_text}</p><p>Other content.</p><p>{short_text}</p>"
        }
        result = _dedupe_long_paragraphs(sections)
        # Both short paragraphs should remain
        assert result["QUICK_WINS_HTML"].count(short_text) == 2

    def test_removes_cross_section_duplicates(self):
        """Should detect duplicates across different sections."""
        # Long text without any < characters (minimum 150 chars)
        long_text = "Dieser Absatz ist lang genug um als Duplikat erkannt zu werden und sollte entfernt werden. Er enthaelt genug Zeichen um die Mindestlaenge zu erreichen."
        sections = {
            "BUSINESS_CASE_HTML": f"<p>{long_text}</p>",
            "PILOT_PLAN_HTML": f"<p>{long_text}</p>"
        }
        result = _dedupe_long_paragraphs(sections)
        # One section should have it removed
        total_occurrences = (
            result["BUSINESS_CASE_HTML"].count(long_text) +
            result["PILOT_PLAN_HTML"].count(long_text)
        )
        assert total_occurrences == 1, f"Expected 1 total occurrence but found {total_occurrences}"


# =============================================================================
# PRIO 4: strip_trailing_sentence_fragments
# =============================================================================

class TestStripTrailingSentenceFragments:
    """Tests for trailing fragment stripping."""

    def test_fixes_trailing_conjunction(self):
        """Should fix sentences ending with dangling conjunctions."""
        sections = {
            "BUSINESS_CASE_HTML": "<p>Dies ist ein längerer Satz der mit und</p>"
        }
        result = strip_trailing_sentence_fragments(sections)
        assert result["BUSINESS_CASE_HTML"].endswith(".</p>")
        assert "und</p>" not in result["BUSINESS_CASE_HTML"]

    def test_fixes_trailing_colon(self):
        """Should fix sentences ending with colon."""
        sections = {
            "PILOT_PLAN_HTML": "<p>Hier folgen die nächsten Schritte:</p>"
        }
        result = strip_trailing_sentence_fragments(sections)
        assert result["PILOT_PLAN_HTML"].endswith(".</p>")

    def test_fixes_trailing_comma(self):
        """Should fix sentences ending with comma."""
        sections = {
            "RECOMMENDATIONS_HTML": "<li>Erstens, zweitens, drittens,</li>"
        }
        result = strip_trailing_sentence_fragments(sections)
        assert result["RECOMMENDATIONS_HTML"].endswith(".</li>")

    def test_preserves_proper_sentences(self):
        """Should not modify properly ended sentences."""
        sections = {
            "QUICK_WINS_HTML": "<p>Dies ist ein vollständiger Satz.</p>"
        }
        original = sections["QUICK_WINS_HTML"]
        result = strip_trailing_sentence_fragments(sections)
        assert result["QUICK_WINS_HTML"] == original


# =============================================================================
# Integration: Full Pipeline
# =============================================================================

class TestFullPipelineIntegration:
    """Integration tests for the full quality enforcer pipeline."""

    def test_pipeline_applies_final_polish(self):
        """Should apply all FIX-52x final polish steps."""
        sections = {
            "QUICK_WINS_HTML": "<p>Nutzen Sie unsere Skalierung mit Platzhalter.</p>",
            "BUSINESS_CASE_HTML": "<p>Der Tech-Stack bietet und</p>",
        }
        result = apply_all_quality_enforcers(sections, company_size="solo")

        # Template phrases removed
        assert "Platzhalter" not in result.get("QUICK_WINS_HTML", "")

        # Solo terms replaced
        assert "Skalierung" not in result.get("QUICK_WINS_HTML", "")
        assert "Tech-Stack" not in result.get("BUSINESS_CASE_HTML", "")

    def test_pipeline_runs_solo_terms_last(self):
        """Solo terms should be replaced even if introduced by earlier steps."""
        # This simulates a scenario where earlier steps might introduce enterprise terms
        sections = {
            "RECOMMENDATIONS_HTML": "<p>Empfehlung: Nutzen Sie Module und Pipelines.</p>",
        }
        result = apply_all_quality_enforcers(sections, company_size="solo")

        # Module should be replaced with Baustein
        assert "Module" not in result.get("RECOMMENDATIONS_HTML", "")
        # Pipeline should be replaced with Ablauf
        assert "Pipeline" not in result.get("RECOMMENDATIONS_HTML", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
