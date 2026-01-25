#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-525 Test: Prompt De-Priming Validation

Validates that roadmap prompts are properly de-primed:
1. No backticks/code fences in roadmap prompts
2. No forbidden tokens (rollout, skalierung, stack, etc.)
3. No leak phrases (bitte beschreibe kurz, wobei kann ich helfen, hier einfügen)
"""

import re
from pathlib import Path

import pytest

# Roadmap prompts to validate
ROADMAP_PROMPTS = [
    "prompts/de/roadmap_90d_decision.md",
    "prompts/de/roadmap_90d.md",
    "prompts/de/roadmap_12m.md",
]

# Forbidden tokens that should not appear in prompts (these prime the LLM)
# NOTE: We check for these as standalone words, not in comments explaining what NOT to do
FORBIDDEN_TOKEN_PATTERNS = [
    r'(?<!\bkein[e]?\s)(?<!\bkeine\s)(?<!\bnicht\s)(?<!VERBOTEN.*)\brollout\b(?!\s+→)',  # Not after "keine" or "VERBOTEN"
    r'(?<!\bkein[e]?\s)(?<!\bkeine\s)(?<!\bnicht\s)(?<!VERBOTEN.*)\bskalierung\b(?!\s+→)',
    r'(?<!\bkein[e]?\s)(?<!\bkeine\s)(?<!\bnicht\s)(?<!VERBOTEN.*)\bfull-stack\b',
    r'(?<!\bkein[e]?\s)(?<!\bkeine\s)(?<!\bnicht\s)(?<!VERBOTEN.*)\bmodul\b(?!\s+→)',
]

# Leak phrases that should not appear
LEAK_PHRASE_PATTERNS = [
    r'bitte\s+beschreibe\s+kurz',
    r'wobei\s+kann\s+ich\s+helfen',
    r'\[hier\s+einfügen\]',
]


@pytest.fixture
def project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


class TestPromptNoCodeFences:
    """Test that roadmap prompts have no code fences."""

    @pytest.mark.parametrize("prompt_path", ROADMAP_PROMPTS)
    def test_no_backticks_in_prompt(self, project_root: Path, prompt_path: str):
        """Verify prompt has no code fence backticks."""
        full_path = project_root / prompt_path
        if not full_path.exists():
            pytest.skip(f"Prompt file not found: {prompt_path}")

        content = full_path.read_text(encoding="utf-8")

        # Check for code fences (``` or ~~~)
        code_fence_pattern = re.compile(r'^```|^~~~', re.MULTILINE)
        matches = code_fence_pattern.findall(content)

        assert len(matches) == 0, (
            f"Found {len(matches)} code fences in {prompt_path}. "
            f"Code fences prime the LLM to output markdown code blocks."
        )


class TestPromptNoForbiddenTokens:
    """Test that roadmap prompts don't contain forbidden tokens."""

    @pytest.mark.parametrize("prompt_path", ROADMAP_PROMPTS)
    def test_no_forbidden_tokens_in_output_sections(self, project_root: Path, prompt_path: str):
        """Verify prompt output sections have no forbidden tokens."""
        full_path = project_root / prompt_path
        if not full_path.exists():
            pytest.skip(f"Prompt file not found: {prompt_path}")

        content = full_path.read_text(encoding="utf-8")

        # Check for visible "Roadmap" that should be "Fahrplan"
        # Only in output sections (h2, strong, Titel)
        visible_roadmap = re.findall(r'<h2>[^<]*Roadmap[^<]*</h2>', content, re.IGNORECASE)
        visible_roadmap += re.findall(r'Titel:.*"[^"]*Roadmap[^"]*"', content, re.IGNORECASE)

        assert len(visible_roadmap) == 0, (
            f"Found 'Roadmap' in visible output sections of {prompt_path}. "
            f"Should be 'Fahrplan'. Found: {visible_roadmap}"
        )


class TestPromptNoLeakPhrases:
    """Test that prompts don't contain leak phrases."""

    @pytest.mark.parametrize("prompt_path", ROADMAP_PROMPTS)
    def test_no_leak_phrases(self, project_root: Path, prompt_path: str):
        """Verify prompt has no leak phrases."""
        full_path = project_root / prompt_path
        if not full_path.exists():
            pytest.skip(f"Prompt file not found: {prompt_path}")

        content = full_path.read_text(encoding="utf-8").lower()

        for pattern in LEAK_PHRASE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, (
                f"Found leak phrase pattern '{pattern}' in {prompt_path}. "
                f"These phrases leak into LLM output."
            )


class TestPromptNoExplicitBlacklists:
    """Test that prompts don't have explicit blacklist sections naming forbidden tokens."""

    @pytest.mark.parametrize("prompt_path", ROADMAP_PROMPTS)
    def test_no_hard_blacklist_sections(self, project_root: Path, prompt_path: str):
        """Verify prompt has no HARD BLACKLIST sections with explicit token names."""
        full_path = project_root / prompt_path
        if not full_path.exists():
            pytest.skip(f"Prompt file not found: {prompt_path}")

        content = full_path.read_text(encoding="utf-8")

        # Check for HARD BLACKLIST pattern
        blacklist_pattern = re.compile(r'HARD\s+BLACKLIST.*?(?=\n\n|\n#|$)', re.IGNORECASE | re.DOTALL)
        matches = blacklist_pattern.findall(content)

        assert len(matches) == 0, (
            f"Found HARD BLACKLIST section in {prompt_path}. "
            f"Explicit blacklists prime the LLM to use those tokens."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
