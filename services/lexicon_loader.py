#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-529: Lexicon Loader for Size-Aware Term Replacements

This module loads replacement lexicons from JSON files and provides
functions to apply them based on company size/persona.

Lexicon Files:
- data/lexicon/solo_replacements.json
- data/lexicon/team_replacements.json

Goal: SIZE_MISMATCH = 0 in production

Version: 1.0.0 (FIX-529)
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Base path for lexicon files
LEXICON_DIR = Path(__file__).parent.parent / "data" / "lexicon"

# Supported personas and their lexicon files
PERSONA_LEXICONS = {
    "solo": "solo_replacements.json",
    "team": "team_replacements.json",
}


@dataclass
class ReplacementRule:
    """A single replacement rule from the lexicon."""
    pattern: str
    replacement: str
    description: str
    compiled_pattern: Optional[re.Pattern[str]] = None

    def compile(self) -> None:
        """Compile the regex pattern for performance."""
        if self.compiled_pattern is None:
            try:
                self.compiled_pattern = re.compile(self.pattern, re.UNICODE)
            except re.error as e:
                log.warning(
                    "[FIX-529][LEXICON] Invalid regex pattern '%s': %s",
                    self.pattern, e
                )


@dataclass
class Lexicon:
    """A loaded lexicon with metadata and rules."""
    version: str
    description: str
    target_persona: str
    rules: List[ReplacementRule] = field(default_factory=list)

    @property
    def rule_count(self) -> int:
        return len(self.rules)


# =============================================================================
# LOADING FUNCTIONS
# =============================================================================

@lru_cache(maxsize=10)
def load_lexicon(persona: str) -> Optional[Lexicon]:
    """
    Load a lexicon for the given persona.

    Args:
        persona: Target persona (solo, team)

    Returns:
        Lexicon object or None if not found
    """
    filename = PERSONA_LEXICONS.get(persona.lower())
    if not filename:
        log.debug("[FIX-529][LEXICON] No lexicon defined for persona: %s", persona)
        return None

    filepath = LEXICON_DIR / filename

    if not filepath.exists():
        log.warning(
            "[FIX-529][LEXICON] Lexicon file not found: %s",
            filepath
        )
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Parse metadata
        meta = data.get("_meta", {})
        rules_data = data.get("replacements", [])

        # Create rules
        rules = []
        for rule_data in rules_data:
            rule = ReplacementRule(
                pattern=rule_data.get("pattern", ""),
                replacement=rule_data.get("replacement", ""),
                description=rule_data.get("description", ""),
            )
            rule.compile()
            if rule.compiled_pattern:
                rules.append(rule)

        lexicon = Lexicon(
            version=meta.get("version", "1.0.0"),
            description=meta.get("description", ""),
            target_persona=meta.get("target_persona", persona),
            rules=rules,
        )

        log.info(
            "[FIX-529][LEXICON] Loaded lexicon for '%s': %d rules (v%s)",
            persona, len(rules), lexicon.version
        )

        return lexicon

    except json.JSONDecodeError as e:
        log.error(
            "[FIX-529][LEXICON] Invalid JSON in %s: %s",
            filepath, e
        )
        return None
    except Exception as e:
        log.error(
            "[FIX-529][LEXICON] Error loading %s: %s",
            filepath, e
        )
        return None


def get_all_lexicons() -> Dict[str, Lexicon]:
    """
    Load all available lexicons.

    Returns:
        Dict mapping persona to Lexicon
    """
    lexicons = {}
    for persona in PERSONA_LEXICONS.keys():
        lex = load_lexicon(persona)
        if lex:
            lexicons[persona] = lex
    return lexicons


# =============================================================================
# APPLICATION FUNCTIONS
# =============================================================================

def apply_lexicon(
    text: str,
    persona: str,
    section_name: str = "",
) -> Tuple[str, int]:
    """
    Apply lexicon replacements to text.

    Args:
        text: Input text
        persona: Target persona (solo, team)
        section_name: Section name for logging

    Returns:
        Tuple of (processed_text, replacement_count)
    """
    if not text:
        return text, 0

    lexicon = load_lexicon(persona)
    if not lexicon:
        return text, 0

    total_replacements = 0
    result = text

    for rule in lexicon.rules:
        if rule.compiled_pattern:
            new_text, count = rule.compiled_pattern.subn(rule.replacement, result)
            if count > 0:
                result = new_text
                total_replacements += count
                log.debug(
                    "[FIX-529][LEXICON] %s: %s (%dx)",
                    section_name or "text",
                    rule.description,
                    count
                )

    # Clean up double spaces from removals
    if total_replacements > 0:
        result = re.sub(r'\s{2,}', ' ', result)
        result = re.sub(r'\s+([.,;:!?])', r'\1', result)

    if total_replacements > 0:
        log.info(
            "[FIX-529][LEXICON] Applied %d replacements to %s (persona=%s)",
            total_replacements,
            section_name or "text",
            persona
        )

    return result, total_replacements


def apply_lexicon_to_sections(
    sections: Dict[str, Any],
    persona: str,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Apply lexicon replacements to all sections.

    Args:
        sections: Dict of section_key -> content
        persona: Target persona (solo, team)

    Returns:
        Tuple of (processed_sections, stats)
    """
    lexicon = load_lexicon(persona)
    if not lexicon:
        return sections, {"total_replacements": 0, "sections_processed": 0}

    processed = dict(sections)
    stats = {
        "total_replacements": 0,
        "sections_processed": 0,
    }

    for key, content in sections.items():
        if not isinstance(content, str):
            continue

        if len(content) < 50:  # Skip very short content
            continue

        new_content, count = apply_lexicon(content, persona, section_name=key)

        if count > 0:
            processed[key] = new_content
            stats["total_replacements"] += count
            stats["sections_processed"] += 1

    if stats["total_replacements"] > 0:
        log.info(
            "[FIX-529][LEXICON] Total: %d replacements in %d sections (persona=%s)",
            stats["total_replacements"],
            stats["sections_processed"],
            persona
        )

    return processed, stats


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_size_mismatch(
    text: str,
    persona: str,
) -> Tuple[bool, List[str]]:
    """
    Check if text contains terms that don't match the persona.

    Args:
        text: Text to validate
        persona: Expected persona

    Returns:
        Tuple of (is_valid, list_of_mismatches)
    """
    if not text:
        return True, []

    lexicon = load_lexicon(persona)
    if not lexicon:
        return True, []

    mismatches = []
    for rule in lexicon.rules:
        if rule.compiled_pattern:
            matches = rule.compiled_pattern.findall(text)
            if matches:
                mismatches.extend(matches[:3])  # Limit to first 3 per rule

    is_valid = len(mismatches) == 0

    if not is_valid:
        log.warning(
            "[FIX-529][SIZE-MISMATCH] Found %d mismatches for persona=%s: %s",
            len(mismatches),
            persona,
            mismatches[:10]
        )

    return is_valid, mismatches


# =============================================================================
# INITIALIZATION
# =============================================================================

# Pre-load lexicons on module import for faster first access
def _init_lexicons() -> None:
    """Initialize lexicons on module load."""
    for persona in PERSONA_LEXICONS.keys():
        lex = load_lexicon(persona)
        if lex:
            log.debug(
                "[FIX-529][LEXICON] Pre-loaded: %s (%d rules)",
                persona, lex.rule_count
            )


# Run initialization
_init_lexicons()

log.info(
    "[FIX-529] lexicon_loader initialized: %d personas available",
    len(PERSONA_LEXICONS)
)
