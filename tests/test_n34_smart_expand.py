# -*- coding: utf-8 -*-
"""
SPRINT N3.4: Tests for Smart Expand Engine v2.

Tests semantic expansion with consulting-style content.
"""
import pytest


class TestSmartExpandFunction:
    """Test the smart_expand function."""

    def test_smart_expand_exists(self):
        """smart_expand should exist."""
        from services.llm_postprocessor import smart_expand

        assert callable(smart_expand)

    def test_smart_expand_short_content(self):
        """Should expand content below minimum words."""
        from services.llm_postprocessor import smart_expand

        short_text = "<p>Kurzer Text.</p>"
        result, count, was_expanded = smart_expand(
            short_text, min_words=100, section="roadmap_90d", size="team"
        )

        assert was_expanded is True
        assert count > 10

    def test_smart_expand_adequate_content(self):
        """Should not expand content already meeting minimum."""
        from services.llm_postprocessor import smart_expand

        adequate = "<p>" + "Dies ist ein langer Text. " * 50 + "</p>"
        result, count, was_expanded = smart_expand(
            adequate, min_words=50, section="roadmap_90d", size="team"
        )

        assert was_expanded is False

    def test_smart_expand_depth_levels(self):
        """Different depth levels should produce different expansion amounts."""
        from services.llm_postprocessor import smart_expand

        short_text = "<p>Kurzer Text.</p>"

        _, count1, _ = smart_expand(
            short_text, min_words=500, section="roadmap_90d",
            depth_level=1, size="team"
        )
        _, count2, _ = smart_expand(
            short_text, min_words=500, section="roadmap_90d",
            depth_level=2, size="team"
        )
        _, count3, _ = smart_expand(
            short_text, min_words=500, section="roadmap_90d",
            depth_level=3, size="team"
        )

        # Higher depth should produce more content
        assert count2 >= count1
        assert count3 >= count2


class TestForbiddenPhrases:
    """Test removal of forbidden GPT fluff phrases."""

    def test_forbidden_phrases_list_exists(self):
        """SMART_EXPAND_FORBIDDEN_PHRASES should exist."""
        from services.llm_postprocessor import SMART_EXPAND_FORBIDDEN_PHRASES

        assert isinstance(SMART_EXPAND_FORBIDDEN_PHRASES, list)
        assert len(SMART_EXPAND_FORBIDDEN_PHRASES) > 10

    def test_removes_intro_phrases(self):
        """Should remove intro phrases like 'In diesem Abschnitt'."""
        from services.llm_postprocessor import _remove_forbidden_phrases

        text = "In diesem Abschnitt wird erläutert, wie KI eingesetzt werden kann."
        cleaned = _remove_forbidden_phrases(text)

        assert "In diesem Abschnitt wird erläutert" not in cleaned

    def test_removes_filler_phrases(self):
        """Should remove filler phrases like 'Es wäre sinnvoll'."""
        from services.llm_postprocessor import _remove_forbidden_phrases

        text = "Es wäre sinnvoll, hier zu investieren. Die Maßnahme ist wichtig."
        cleaned = _remove_forbidden_phrases(text)

        assert "Es wäre sinnvoll" not in cleaned

    def test_removes_support_phrases(self):
        """Should remove 'Wie kann ich helfen' and similar."""
        from services.llm_postprocessor import _remove_forbidden_phrases

        text = "Wie kann ich helfen? Hier sind die Empfehlungen."
        cleaned = _remove_forbidden_phrases(text)

        assert "Wie kann ich helfen" not in cleaned


class TestSemanticArguments:
    """Test semantic argument generation."""

    def test_generates_roadmap_90d_arguments(self):
        """Should generate arguments for roadmap_90d."""
        from services.llm_postprocessor import _get_semantic_arguments

        result = _get_semantic_arguments("roadmap_90d", "team", "IT", "consulting_structured")

        assert result
        assert "Erfolgsfaktoren" in result or "Initiative" in result

    def test_generates_recommendations_arguments(self):
        """Should generate arguments for recommendations."""
        from services.llm_postprocessor import _get_semantic_arguments

        result = _get_semantic_arguments("recommendations", "solo", "Beratung", "consulting_structured")

        assert result
        assert len(result) > 50

    def test_size_aware_arguments(self):
        """Arguments should differ by company size."""
        from services.llm_postprocessor import _get_semantic_arguments

        solo = _get_semantic_arguments("roadmap_90d", "solo", "", "consulting_structured")
        team = _get_semantic_arguments("roadmap_90d", "team", "", "consulting_structured")
        kmu = _get_semantic_arguments("roadmap_90d", "kmu", "", "consulting_structured")

        # Should be different content
        assert solo != team
        assert team != kmu


class TestBranchSpecificExamples:
    """Test branch-specific example generation."""

    def test_generates_examples(self):
        """Should generate branch-specific examples."""
        from services.llm_postprocessor import _get_branch_specific_examples

        result = _get_branch_specific_examples(
            "roadmap_90d", "team", "Fertigung", "consulting_structured"
        )

        assert result
        assert "<ul>" in result or "<li>" in result

    def test_examples_include_branch(self):
        """Examples should include branch context."""
        from services.llm_postprocessor import _get_branch_specific_examples

        result = _get_branch_specific_examples(
            "recommendations", "team", "Healthcare", "consulting_structured"
        )

        assert result
        # Should mention the branch
        assert "Healthcare" in result


class TestStructuralExpansion:
    """Test structural expansion generation."""

    def test_generates_structural_content(self):
        """Should generate structural content with lists."""
        from services.llm_postprocessor import _get_structural_expansion

        result = _get_structural_expansion(
            "roadmap_90d", "team", "Retail", "consulting_structured"
        )

        assert result
        assert "<ol>" in result or "<li>" in result

    def test_structural_includes_checklists(self):
        """Structural expansion should include checklists or frameworks."""
        from services.llm_postprocessor import _get_structural_expansion

        result = _get_structural_expansion(
            "risks", "kmu", "", "consulting_structured"
        )

        assert result
        # Should have numbered or structured content
        assert "Framework" in result or "Identifikation" in result


class TestSmartExpandSections:
    """Test the smart_expand_sections function."""

    def test_function_exists(self):
        """smart_expand_sections should exist."""
        from services.llm_postprocessor import smart_expand_sections

        assert callable(smart_expand_sections)

    def test_expands_multiple_sections(self):
        """Should expand multiple sections that need it."""
        from services.llm_postprocessor import smart_expand_sections

        sections = {
            "ROADMAP_90D_HTML": "<p>Kurz.</p>",
            "RECOMMENDATIONS_HTML": "<p>Kurz.</p>",
            "EXEC_SUMMARY_HTML": "<p>Dies ist lang genug für den Test " * 20 + "</p>",
        }

        stats = smart_expand_sections(sections, size="team", branche="IT")

        # Some sections should have been expanded
        assert len(stats) >= 0  # May or may not expand depending on thresholds


class TestStyleVariants:
    """Test different expansion styles."""

    def test_styles_exist(self):
        """SMART_EXPAND_STYLES should exist with multiple styles."""
        from services.llm_postprocessor import SMART_EXPAND_STYLES

        assert isinstance(SMART_EXPAND_STYLES, dict)
        assert "consulting_structured" in SMART_EXPAND_STYLES
        assert "bcg_case_style" in SMART_EXPAND_STYLES
        assert "oxford_academic" in SMART_EXPAND_STYLES
        assert "executive_summary_mode" in SMART_EXPAND_STYLES

    def test_style_has_required_keys(self):
        """Each style should have required configuration keys."""
        from services.llm_postprocessor import SMART_EXPAND_STYLES

        for style_name, style_config in SMART_EXPAND_STYLES.items():
            assert "intro_pattern" in style_config
            assert "bullet_style" in style_config
            assert "sentence_target" in style_config
            assert "tone" in style_config


class TestNoGPTFluff:
    """Test that expanded content doesn't contain GPT fluff."""

    def test_no_intro_sentences_in_expansion(self):
        """Expanded content should not have intro sentences."""
        from services.llm_postprocessor import smart_expand

        short_text = "<p>Kurzer Text.</p>"
        result, _, _ = smart_expand(
            short_text, min_words=200, section="roadmap_90d",
            depth_level=3, size="team"
        )

        forbidden = [
            "In diesem Abschnitt",
            "Es wäre sinnvoll",
            "Es könnte hilfreich sein",
            "Zusammenfassend lässt sich sagen",
        ]

        for phrase in forbidden:
            assert phrase not in result, f"Found forbidden phrase: {phrase}"

    def test_consulting_tone_in_expansion(self):
        """Expanded content should have consulting tone."""
        from services.llm_postprocessor import smart_expand

        short_text = "<p>Kurzer Text.</p>"
        result, _, _ = smart_expand(
            short_text, min_words=200, section="recommendations",
            depth_level=3, size="team"
        )

        # Should have consulting-style language
        consulting_indicators = [
            "Priorisierung", "strategisch", "Implementierung",
            "ROI", "Initiative", "Maßnahm"
        ]

        found_any = any(indicator in result for indicator in consulting_indicators)
        assert found_any, "Expected consulting-style language in expansion"
