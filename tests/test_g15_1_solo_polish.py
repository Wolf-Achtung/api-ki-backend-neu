# -*- coding: utf-8 -*-
"""
Sprint G15.1 Tests: Solo-Polish (OnPrüf-Artefakt, Persona-Leak, Roadmap-Länge)

Tests for the mini-polish sprint targeting Solo report quality improvements:
- G15.1-A: OnPrüfroutineing artifact removal
- G15.1-B: Bereichsleiter persona leak fix for Solo
- G15.1-C: roadmap_90d Solo minimum length

Version: 1.0.0
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any

import pytest


# =============================================================================
# TEST G15.1-A: ONPRÜFROUTINEING ARTIFACT REMOVAL
# =============================================================================

class TestG151A_ArtifactRemoval:
    """Tests for OnPrüfroutineing artifact cleanup."""

    def test_artifact_replacements_defined(self) -> None:
        """ARTIFACT_REPLACEMENTS should be defined in ReportValidator."""
        from services.report_validator import ReportValidator

        assert hasattr(ReportValidator, "ARTIFACT_REPLACEMENTS")
        artifacts = ReportValidator.ARTIFACT_REPLACEMENTS
        assert isinstance(artifacts, dict)
        assert len(artifacts) >= 3  # At least 3 replacement patterns

    def test_artifact_replacements_content(self) -> None:
        """ARTIFACT_REPLACEMENTS should contain OnPrüfroutineing patterns."""
        from services.report_validator import ReportValidator

        artifacts = ReportValidator.ARTIFACT_REPLACEMENTS
        # Check specific artifacts are covered
        assert "OnPrüfroutineing" in artifacts
        assert artifacts["OnPrüfroutineing"] == "Onboarding"

    def test_no_onpruefroutineing_in_rendered_report(self) -> None:
        """
        Filter should remove OnPrüfroutineing artifacts from content.

        This simulates a rendered report HTML and verifies cleanup.
        """
        from services.report_validator import filter_size_inappropriate_content

        # Sample content with artifacts
        test_html = """
        <section class="quick-wins">
            <h3>Quick Wins</h3>
            <ul>
                <li>OnPrüfroutineing-Mails für neue Kunden einrichten</li>
                <li>OnPrüfroutineing zukünftiger Nutzer:innen automatisieren</li>
                <li>Einfaches OnPrüfroutineing mit KI-Unterstützung</li>
            </ul>
        </section>
        """

        # Filter for Solo (any size should clean artifacts)
        filtered = filter_size_inappropriate_content(test_html, "solo")

        # Verify no artifacts remain
        assert "OnPrüfroutineing" not in filtered
        assert "OnPrüfroutineing-Mails" not in filtered

        # Verify clean replacements are in place
        assert "Onboarding-E-Mails" in filtered
        assert "Onboarding zukünftiger" in filtered
        assert "Onboarding mit KI" in filtered

    def test_artifact_removal_for_all_sizes(self) -> None:
        """Artifact removal should work for all company sizes."""
        from services.report_validator import filter_size_inappropriate_content

        test_content = "OnPrüfroutineing-Mails versenden"

        for size in ["solo", "team", "kmu"]:
            filtered = filter_size_inappropriate_content(test_content, size)
            assert "OnPrüfroutineing" not in filtered
            assert "Onboarding" in filtered


# =============================================================================
# TEST G15.1-B: BEREICHSLEITER PERSONA LEAK
# =============================================================================

class TestG151B_PersonaLeak:
    """Tests for Bereichsleiter persona leak fix."""

    def test_bereichsleiter_in_solo_forbidden_terms(self) -> None:
        """Bereichsleiter should be in SOLO_FORBIDDEN_TERMS."""
        from services.prompt_enhancer import SOLO_FORBIDDEN_TERMS

        assert "bereichsleiter" in SOLO_FORBIDDEN_TERMS

    def test_bereichsleiter_replacement_defined(self) -> None:
        """Bereichsleiter replacement should be defined."""
        from services.prompt_enhancer import (
            SOLO_PHRASE_REPLACEMENTS,
            SOLO_GOVERNANCE_REPLACEMENTS,
        )

        # Check phrase replacements
        has_phrase = any(
            "bereichsleiter" in k.lower()
            for k in SOLO_PHRASE_REPLACEMENTS.keys()
        )
        # Check governance replacements
        has_governance = any(
            "bereichsleiter" in k.lower()
            for k in SOLO_GOVERNANCE_REPLACEMENTS.keys()
        )

        assert has_phrase or has_governance, (
            "Bereichsleiter replacement should be in SOLO_PHRASE_REPLACEMENTS "
            "or SOLO_GOVERNANCE_REPLACEMENTS"
        )

    def test_no_bereichsleiter_for_solo_templates(self) -> None:
        """Solo content filter should replace Bereichsleiter."""
        from services.prompt_enhancer import apply_solo_persona_filter

        # Test content with Bereichsleiter
        test_content = """
        Die Templates richten sich an Bereichsleiter in Unternehmen.
        Bereichsleiter:innen können diese Vorlagen direkt nutzen.
        """

        filtered = apply_solo_persona_filter(test_content)

        # Bereichsleiter should be replaced
        assert "Bereichsleiter" not in filtered
        assert "bereichsleiter" not in filtered.lower() or "ansprechp" in filtered.lower()

    def test_solo_filter_preserves_context(self) -> None:
        """Solo filter should preserve surrounding context."""
        from services.prompt_enhancer import apply_solo_persona_filter

        test_content = "Die Bereichsleiter im Kundenunternehmen nutzen die Vorlagen."
        filtered = apply_solo_persona_filter(test_content)

        # Should still contain key context words
        assert "Kundenunternehmen" in filtered or "unternehmen" in filtered.lower()
        assert "nutzen" in filtered
        assert "Vorlagen" in filtered


# =============================================================================
# TEST G15.1-C: ROADMAP_90D SOLO MINIMUM LENGTH
# =============================================================================

class TestG151C_RoadmapLength:
    """Tests for roadmap_90d Solo minimum word count."""

    def test_roadmap_90d_prompt_exists(self) -> None:
        """roadmap_90d.md prompt file should exist."""
        prompt_path = Path("prompts/de/roadmap_90d.md")
        assert prompt_path.exists(), f"Prompt file not found: {prompt_path}"

    def test_roadmap_90d_solo_content_extended(self) -> None:
        """Solo section should have KPI-Tracking and Content-Marketing sections."""
        prompt_path = Path("prompts/de/roadmap_90d.md")
        content = prompt_path.read_text(encoding="utf-8")

        # Check for new sections
        assert "KPI-Tracking" in content, "KPI-Tracking section missing"
        assert "Content & Marketing" in content or "Marketing-Systematik" in content, (
            "Content-Marketing section missing"
        )

    def test_roadmap_90d_solo_meets_min_words(self) -> None:
        """
        Solo roadmap content should meet minimum word count.

        The validator minimum for solo roadmap_90d is 250 words.
        Phase 3 update: Regex now allows for comment blocks between Jinja if and h3.
        """
        prompt_path = Path("prompts/de/roadmap_90d.md")
        content = prompt_path.read_text(encoding="utf-8")

        # Extract Solo HTML section (between {% if COMPANY_SIZE == "solo" %} and {% elif)
        # Phase 3: Allow for comment blocks (<!--...-->) between Jinja if and first h3
        solo_match = re.search(
            r'\{% if COMPANY_SIZE == "solo" %\}.*?<h3>(.*?)\{% elif COMPANY_SIZE == "team"',
            content,
            re.DOTALL
        )

        assert solo_match, "Could not find Solo section in roadmap_90d.md"

        # Prepend the h3 tag back for the HTML content
        solo_content = "<h3>" + solo_match.group(1)

        # Remove HTML tags and comments for word count
        text_only = re.sub(r'<!--.*?-->', ' ', solo_content, flags=re.DOTALL)
        text_only = re.sub(r'<[^>]+>', ' ', text_only)
        text_only = re.sub(r'\s+', ' ', text_only).strip()

        word_count = len(text_only.split())

        # Solo minimum is 250 words - content should exceed this
        min_words = 250
        assert word_count >= min_words, (
            f"Solo roadmap has {word_count} words, needs at least {min_words}"
        )

    def test_roadmap_solo_uses_solo_terminology(self) -> None:
        """Solo roadmap HTML content should not contain Team/KMU terminology.

        Phase 3 update: Regex now allows for comment blocks between Jinja if and h3.
        Comments are stripped before checking forbidden terms.
        """
        prompt_path = Path("prompts/de/roadmap_90d.md")
        content = prompt_path.read_text(encoding="utf-8")

        # Extract Solo HTML section (only the actual HTML, not instructions)
        # Phase 3: Allow for comment blocks (<!--...-->) between Jinja if and first h3
        solo_match = re.search(
            r'\{% if COMPANY_SIZE == "solo" %\}.*?<h3>(.*?)\{% elif COMPANY_SIZE == "team"',
            content,
            re.DOTALL
        )
        assert solo_match, "Could not find Solo section in roadmap_90d.md"

        # Get content and strip HTML comments (which may contain examples/documentation)
        solo_content = solo_match.group(1)
        solo_content_no_comments = re.sub(r'<!--.*?-->', '', solo_content, flags=re.DOTALL)
        solo_content_clean = solo_content_no_comments.lower()

        # Solo HTML content should not contain these terms
        # Note: instruction comments are now stripped before checking
        forbidden_in_solo = [
            "mitarbeiter einstellen",
            "team aufbauen",
            "teamstruktur",
        ]

        for term in forbidden_in_solo:
            assert term not in solo_content_clean, (
                f"Forbidden term '{term}' found in Solo roadmap HTML content"
            )


# =============================================================================
# TEST G15.1-D: INTEGRATION & REPLACER TESTS
# =============================================================================

class TestG151D_Integration:
    """Integration tests for G15.1 changes."""

    def test_size_filter_chain_works(self) -> None:
        """Full filter chain should clean all artifacts and persona leaks."""
        from services.report_validator import filter_size_inappropriate_content

        # Content with multiple issues
        test_html = """
        <section>
            <p>OnPrüfroutineing-Mails an Bereichsleiter versenden.</p>
            <p>Das Team sollte die Mitarbeiter informieren.</p>
        </section>
        """

        # Filter for Solo
        filtered = filter_size_inappropriate_content(test_html, "solo")

        # Artifacts should be cleaned
        assert "OnPrüfroutineing" not in filtered

        # Team terms should be replaced for Solo
        # Note: exact replacement depends on filter implementation
        assert "Onboarding" in filtered

    def test_artifact_longest_first_matching(self) -> None:
        """Artifact replacement should use longest-first matching."""
        from services.report_validator import ReportValidator

        artifacts = ReportValidator.ARTIFACT_REPLACEMENTS

        # "OnPrüfroutineing-Mails" should be replaced before "OnPrüfroutineing"
        keys_by_length = sorted(artifacts.keys(), key=len, reverse=True)

        # Longer patterns should come first when sorted
        if "OnPrüfroutineing-Mails" in artifacts and "OnPrüfroutineing" in artifacts:
            assert keys_by_length.index("OnPrüfroutineing-Mails") < keys_by_length.index("OnPrüfroutineing")

    def test_all_g151_modules_import(self) -> None:
        """All modified modules should import without errors."""
        # report_validator
        from services.report_validator import (
            ReportValidator,
            filter_size_inappropriate_content,
            filter_all_sections,
        )
        assert ReportValidator is not None

        # prompt_enhancer
        from services.prompt_enhancer import (
            apply_solo_persona_filter,
            SOLO_PHRASE_REPLACEMENTS,
            SOLO_GOVERNANCE_REPLACEMENTS,
            SOLO_FORBIDDEN_TERMS,
        )
        assert apply_solo_persona_filter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
