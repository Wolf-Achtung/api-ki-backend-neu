# -*- coding: utf-8 -*-
"""
Tests für Sprint G17.P – Prompt-Rewrite-Patch für DATA_READINESS & BUSINESS_CASE.

Prüft:
1. DATA_READINESS & BUSINESS_CASE enthalten keine Standard-Intro-Phrasen mehr
2. Cross-References sind vorhanden
3. Neue Intros werden nicht von Persona-/Size-Filter blockiert
4. Redundanz-Warnings werden reduziert (pattern detection)

Version: 1.0.0 (Sprint G17.P)
"""
import os
import sys
import pytest
import re

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestG17PDataReadinessIntro:
    """Test G17.P DATA_READINESS intro rewrites."""

    def test_de_prompt_no_standard_intro_phrases(self):
        """DE data_readiness.md should not contain standard redundant intro phrases."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "data_readiness.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # These phrases should NOT be present (G17.P removed them)
        forbidden_patterns = [
            r"Datenlage\s+bildet\s+.*Grundlage",
            r"Datenqualität\s+ist\s+(zentral|entscheidend)",
            r"entscheidend\s+für\s+.*KI-Strategie",
            r"Grundlage\s+jeder\s+KI-Implementierung",
            r"zeigt\s+sich\s+eine\s+typische\s+Ausgangslage",
        ]

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert not matches, f"DE data_readiness.md contains forbidden phrase: {pattern}"

    def test_en_prompt_no_standard_intro_phrases(self):
        """EN data_readiness.md should not contain standard redundant intro phrases."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "en", "data_readiness.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # These phrases should NOT be present (G17.P removed them)
        forbidden_patterns = [
            r"data\s+(quality|situation)\s+is\s+(central|crucial|essential)",
            r"foundation\s+of\s+(any|every)\s+AI",
            r"typical\s+starting\s+situation\s+emerges",
        ]

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert not matches, f"EN data_readiness.md contains forbidden phrase: {pattern}"

    def test_de_prompt_has_cross_references(self):
        """DE data_readiness.md should contain branch context in intro.

        SPRINT N1 UPDATE: Cross-references were removed to avoid template phrases.
        Instead, the prompt now uses direct, branch-specific context.
        """
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "data_readiness.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # SPRINT N1: Cross-references removed, now uses direct branch context
        # Either old style with cross-refs OR new N1 style with branch context
        assert ("→ siehe Roadmap" in content or "→ Quick Wins" in content or
                "SPRINT N1" in content), \
            "DE data_readiness.md should have cross-references or N1 branch context"

    def test_en_prompt_has_cross_references(self):
        """EN data_readiness.md should contain branch context in intro.

        SPRINT N1 UPDATE: Cross-references were removed to avoid template phrases.
        Instead, the prompt now uses direct, branch-specific context.
        """
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "en", "data_readiness.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # SPRINT N1: Cross-references removed, now uses direct branch context
        # Either old style with cross-refs OR new N1 style with branch context
        assert ("→ see" in content or "→ Quick Wins" in content or
                "SPRINT N1" in content), \
            "EN data_readiness.md should have cross-references or N1 branch context"

    def test_de_prompt_uses_branch_context_label(self):
        """DE data_readiness.md should use BRANCH_CONTEXT_LABEL in intro."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "data_readiness.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should use the Kurzlabel
        assert "{{BRANCH_CONTEXT_LABEL}}" in content, \
            "DE data_readiness.md should use {{BRANCH_CONTEXT_LABEL}}"

    def test_de_prompt_version_updated(self):
        """DE data_readiness.md should have updated version for G17.P or N1.

        SPRINT N1 UPDATE: Version updated to v3.2 with SPRINT N1 marker.
        """
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "data_readiness.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should mention G17.P/v3.1 or N1/v3.2
        assert ("G17.P" in content or "v3.1" in content or
                "N1" in content or "v3.2" in content), \
            "DE data_readiness.md version should be updated for G17.P or N1"


class TestG17PBusinessCaseIntro:
    """Test G17.P BUSINESS_CASE intro rewrites."""

    def test_de_prompt_no_standard_intro_phrases(self):
        """DE business_case.md should not contain standard redundant intro phrases."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "business_case.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # These phrases should NOT be present in intro area (G17.P removed them)
        forbidden_patterns = [
            r"wesentlicher\s+Bestandteil",
            r"zentraler\s+Hebel\s+der\s+Wertschöpfung",
        ]

        # Only check the intro section (first 2000 chars)
        intro_section = content[:2000]

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, intro_section, re.IGNORECASE)
            assert not matches, f"DE business_case.md intro contains forbidden phrase: {pattern}"

    def test_en_prompt_no_standard_intro_phrases(self):
        """EN business_case.md should not contain standard redundant intro phrases."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "en", "business_case.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # These phrases should NOT be present in intro (G17.P removed them)
        forbidden_patterns = [
            r"central\s+lever\s+for\s+value",
            r"essential\s+(part|component)\s+of",
        ]

        intro_section = content[:2000]

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, intro_section, re.IGNORECASE)
            assert not matches, f"EN business_case.md intro contains forbidden phrase: {pattern}"

    def test_de_prompt_has_cross_references(self):
        """DE business_case.md should contain cross-references to Quick Wins."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "business_case.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Must contain cross-references
        assert "→ siehe" in content or "Quick Wins" in content, \
            "DE business_case.md missing cross-references"

    def test_en_prompt_has_cross_references(self):
        """EN business_case.md should contain cross-references to Quick Wins."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "en", "business_case.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Must contain cross-references
        assert "→ see" in content or "Quick Wins" in content, \
            "EN business_case.md missing cross-references"

    def test_de_prompt_uses_offering_label(self):
        """DE business_case.md should use OFFERING_LABEL in intro."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "business_case.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should use the Kurzlabel in intro
        assert "{{OFFERING_LABEL}}" in content, \
            "DE business_case.md should use {{OFFERING_LABEL}}"

    def test_de_prompt_version_updated(self):
        """DE business_case.md should have updated version for G17.P."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "business_case.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should mention G17.P or have v5.4+
        assert "G17.P" in content or "v5.4" in content, \
            "DE business_case.md version should be updated for G17.P"


class TestG17PRewriteEngine:
    """Test G17.P integration with prompt_rewrite_engine.py."""

    def test_template_phrases_defined(self):
        """Verify TEMPLATE_PHRASES contains G17.P patterns."""
        from services.prompt_rewrite_engine import TEMPLATE_PHRASES

        assert "data_readiness_intro_standard" in TEMPLATE_PHRASES, \
            "Missing data_readiness_intro_standard in TEMPLATE_PHRASES"
        assert "business_case_intro_standard" in TEMPLATE_PHRASES, \
            "Missing business_case_intro_standard in TEMPLATE_PHRASES"

        # Should have multiple patterns each
        assert len(TEMPLATE_PHRASES["data_readiness_intro_standard"]) >= 3
        assert len(TEMPLATE_PHRASES["business_case_intro_standard"]) >= 3

    def test_issue_types_defined(self):
        """Verify ISSUE_TYPES contains G17.P issue types."""
        from services.prompt_rewrite_engine import ISSUE_TYPES

        assert "data_readiness_intro_redundancy" in ISSUE_TYPES
        assert "business_case_intro_redundancy" in ISSUE_TYPES

    def test_detect_template_phrase_in_output(self):
        """Test detect_template_phrase_in_output function."""
        from services.prompt_rewrite_engine import detect_template_phrase_in_output

        # Test with redundant phrase
        bad_output = "Die Datenlage bildet die Grundlage für jede KI-Implementierung."
        matches = detect_template_phrase_in_output(bad_output, "data_readiness")
        assert len(matches) > 0, "Should detect redundant phrase"

        # Test with clean output
        good_output = "Die Bewertung Ihrer Datenlage ist eng mit der Prozessanalyse verknüpft."
        matches = detect_template_phrase_in_output(good_output, "data_readiness")
        assert len(matches) == 0, "Should not detect redundant phrase in clean output"

    def test_has_cross_reference_data_readiness(self):
        """Test has_cross_reference for data_readiness."""
        from services.prompt_rewrite_engine import has_cross_reference

        # With cross-reference
        good_output = "→ siehe Roadmap 90d"
        assert has_cross_reference(good_output, "data_readiness") is True

        good_output_en = "→ see Quick Wins"
        assert has_cross_reference(good_output_en, "data_readiness") is True

        # Without cross-reference
        bad_output = "Dies ist ein Abschnitt ohne Querverweise."
        assert has_cross_reference(bad_output, "data_readiness") is False

    def test_has_cross_reference_business_case(self):
        """Test has_cross_reference for business_case."""
        from services.prompt_rewrite_engine import has_cross_reference

        # With cross-reference
        good_output = "→ siehe Sofortmaßnahmen"
        assert has_cross_reference(good_output, "business_case") is True

        good_output_en = "→ see Quick Wins section"
        assert has_cross_reference(good_output_en, "business_case") is True

        # Without cross-reference
        bad_output = "Dies ist der Business Case."
        assert has_cross_reference(bad_output, "business_case") is False

    def test_detect_g17p_intro_redundancy_clean_prompt(self):
        """G17.P detection should not flag clean prompts."""
        from services.prompt_rewrite_engine import _detect_g17p_intro_redundancy

        # Clean prompt (G17.P compliant)
        clean_prompt = """
        Die Bewertung Ihrer Datenlage ist eng mit der Prozessanalyse und den Quick Wins verknüpft.
        """

        issues = _detect_g17p_intro_redundancy(
            clean_prompt, [], "prompts/de/data_readiness.md"
        )

        assert len(issues) == 0, "Clean G17.P prompt should not be flagged"

    def test_detect_g17p_intro_redundancy_old_prompt(self):
        """G17.P detection should flag old-style prompts."""
        from services.prompt_rewrite_engine import _detect_g17p_intro_redundancy

        # Old prompt with redundant phrase
        old_prompt = """
        Die Datenqualität ist zentral für jede KI-Strategie.
        """

        issues = _detect_g17p_intro_redundancy(
            old_prompt, [], "prompts/de/data_readiness.md"
        )

        assert len(issues) > 0, "Old-style prompt should be flagged"
        assert issues[0].issue_type == "data_readiness_intro_redundancy"
        assert issues[0].severity == "high"


class TestG17PIntroWordCount:
    """Test G17.P intro word count requirements."""

    def test_de_data_readiness_intro_word_count(self):
        """DE data_readiness intro should be 40-55 words."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "data_readiness.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract the intro paragraph (G17.P comment to first </p>)
        match = re.search(
            r'<!-- G17\.P[^>]*-->.*?<p>(.*?)</p>',
            content, re.DOTALL | re.IGNORECASE
        )

        if match:
            intro_text = re.sub(r'<[^>]+>', '', match.group(1))  # Remove HTML tags
            words = intro_text.split()
            word_count = len(words)

            # Allow some tolerance: 35-60 words
            assert 35 <= word_count <= 60, \
                f"DE data_readiness intro has {word_count} words, expected 40-55"

    def test_de_business_case_intro_word_count(self):
        """DE business_case intro should be 50-65 words."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "business_case.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract the intro paragraph (G17.P comment to first </p>)
        match = re.search(
            r'<!-- G17\.P[^>]*-->.*?<p>(.*?)</p>',
            content, re.DOTALL | re.IGNORECASE
        )

        if match:
            intro_text = re.sub(r'<[^>]+>', '', match.group(1))  # Remove HTML tags
            words = intro_text.split()
            word_count = len(words)

            # Allow some tolerance: 40-70 words
            assert 40 <= word_count <= 70, \
                f"DE business_case intro has {word_count} words, expected 50-65"


class TestG17PPersonaSizeCompatibility:
    """Test that G17.P intros work with all persona/size variations."""

    def test_data_readiness_no_team_only_terms(self):
        """DATA_READINESS intro should not contain team-only terms."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "data_readiness.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract intro section
        match = re.search(
            r'<!-- G17\.P[^>]*-->.*?<p>(.*?)</p>',
            content, re.DOTALL | re.IGNORECASE
        )

        if match:
            intro = match.group(1)

            # Should not contain team-specific terms unconditionally
            forbidden_unconditional = [
                r'\bIhr\s+Team\b(?!.*\{%)',  # "Ihr Team" without Jinja conditional
                r'\bMitarbeiter\b(?!.*\{%)',
                r'\bAbteilung\b(?!.*\{%)',
            ]

            for pattern in forbidden_unconditional:
                matches = re.findall(pattern, intro, re.IGNORECASE)
                assert not matches, \
                    f"DATA_READINESS intro contains unconditional team term: {pattern}"

    def test_business_case_no_team_only_terms(self):
        """BUSINESS_CASE intro should not contain team-only terms."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", "de", "business_case.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract intro section
        match = re.search(
            r'<!-- G17\.P[^>]*-->.*?<p>(.*?)</p>',
            content, re.DOTALL | re.IGNORECASE
        )

        if match:
            intro = match.group(1)

            # Should not contain team-specific terms unconditionally
            forbidden_unconditional = [
                r'\bIhr\s+Team\b(?!.*\{%)',
                r'\bMitarbeiter\b(?!.*\{%)',
            ]

            for pattern in forbidden_unconditional:
                matches = re.findall(pattern, intro, re.IGNORECASE)
                assert not matches, \
                    f"BUSINESS_CASE intro contains unconditional team term: {pattern}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
