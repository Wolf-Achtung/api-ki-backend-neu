# -*- coding: utf-8 -*-
"""
Guardrails Detection Service - Confidence-based guardrail detection.

This module provides intelligent detection of guardrails (constraints, no-gos,
sensitive areas) in user-provided freetext fields, with confidence scoring
for better ranking and reduced false positives.

Version: 5.0.0 - Added confidence scoring
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Types
# =============================================================================

GuardrailReason = Literal["explicit_keyword", "negation_action", "sensitive_area"]


@dataclass
class GuardrailHit:
    """
    Represents a detected guardrail with confidence scoring.

    Attributes:
        sentence: The detected sentence containing the guardrail
        reason: Why this was flagged (keyword, negation+action, or sensitive area)
        confidence: Confidence score from 0.0 to 1.0
        lang: Language of detection ("de" or "en")
        field: Source field where the guardrail was found
    """

    sentence: str
    reason: GuardrailReason
    confidence: float
    lang: str = "de"
    field: str = ""

    def __post_init__(self) -> None:
        """Validate confidence is in valid range."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence detection (>= 0.8)."""
        return self.confidence >= 0.8

    @property
    def is_medium_confidence(self) -> bool:
        """Check if this is medium confidence (0.5 - 0.8)."""
        return 0.5 <= self.confidence < 0.8

    def to_display_string(self) -> str:
        """Format for display in reports."""
        return f"- {self.sentence}"


# =============================================================================
# Detection Keywords (v5.0)
# =============================================================================

# German guardrail keywords
GUARDRAIL_KEYWORDS_DE = [
    "no-gos",
    "no go",
    "leitplanken",
    "grenzen",
    "tabu",
    "verboten",
    "ausgeschlossen",
    "rote linien",
    "ethische grenzen",
    "nicht verhandelbar",
    "sensible themen",
    "datenschutz",
    "dsgvo",
    "compliance",
    "regulierung",
    "audit",
    "gesetzlich",
    "rechtlich",
]

# German negation words
NEGATION_WORDS_DE = ["nicht", "kein", "keine", "ohne", "niemals", "nie"]

# German action words (combined with negation indicates guardrails)
ACTION_WORDS_DE = [
    "weitergeben",
    "freigeben",
    "automatisieren",
    "delegieren",
    "ersetzen",
    "entscheiden",
    "speichern",
    "verarbeiten",
]

# German sensitive areas (imply guardrails without negation)
SENSITIVE_AREAS_DE = [
    "kundendaten",
    "personendaten",
    "personenbezogen",
    "gehalt",
    "finanzdaten",
    "gesundheitsdaten",
    "bewerberdaten",
    "mitarbeiterdaten",
]

# English guardrail keywords
GUARDRAIL_KEYWORDS_EN = [
    "no-gos",
    "no go",
    "guardrails",
    "red lines",
    "sensitive topics",
    "off-limits",
    "prohibited",
    "excluded",
    "ethical boundaries",
    "non-negotiable",
    "sensitive data",
    "privacy",
    "gdpr",
    "compliance",
    "regulation",
    "audit",
    "legal",
    "regulatory",
    "confidential",
    "restricted",
    "must not",
    "forbidden",
]

# English negation words
NEGATION_WORDS_EN = ["no", "not", "never", "without", "none", "don't", "cannot", "must not"]

# English action words
ACTION_WORDS_EN = [
    "share",
    "delegate",
    "automate",
    "replace",
    "decide",
    "store",
    "process",
]

# English sensitive areas
SENSITIVE_AREAS_EN = [
    "customer data",
    "personal data",
    "personally identifiable",
    "salary",
    "financial data",
    "health data",
    "employee data",
    "applicant data",
    "pii",
]

# Fields to scan for guardrails
FREETEXT_FIELDS = [
    "bedenken",
    "no_go",
    "besondere_anforderungen",
    "compliance_anforderungen",
    "datenschutz_bedenken",
    "ethische_grundsaetze",
    "vision_3_jahre",
    "ki_projekte",
]


# =============================================================================
# Confidence Scoring
# =============================================================================

# Base confidence scores by detection reason
CONFIDENCE_SCORES: Dict[GuardrailReason, float] = {
    "explicit_keyword": 0.7,
    "negation_action": 0.9,
    "sensitive_area": 0.6,
}

# Confidence boost for multiple signals in same sentence
MULTI_SIGNAL_BOOST = 0.15

# Confidence boost for explicit field (like "no_go" field)
EXPLICIT_FIELD_BOOST = 0.1


def _calculate_confidence(
    reason: GuardrailReason,
    sentence: str,
    field: str,
    lang: str,
    has_multiple_signals: bool = False,
) -> float:
    """
    Calculate confidence score for a guardrail detection.

    Args:
        reason: Primary reason for detection
        sentence: The detected sentence
        field: Source field name
        lang: Language code
        has_multiple_signals: Whether multiple detection methods triggered

    Returns:
        Confidence score between 0.0 and 1.0
    """
    base_score = CONFIDENCE_SCORES.get(reason, 0.5)

    # Boost for multiple signals
    if has_multiple_signals:
        base_score += MULTI_SIGNAL_BOOST

    # Boost for explicit guardrail fields
    if field.lower() in ("no_go", "bedenken", "ki_guardrails"):
        base_score += EXPLICIT_FIELD_BOOST

    # Cap at 1.0
    return min(1.0, base_score)


# =============================================================================
# Detection Functions
# =============================================================================


def _check_negation_action(sentence_lower: str, lang: str = "de") -> bool:
    """Check if sentence contains negation + action word combination."""
    if lang == "en":
        negation_words = NEGATION_WORDS_EN
        action_words = ACTION_WORDS_EN
    else:
        negation_words = NEGATION_WORDS_DE
        action_words = ACTION_WORDS_DE

    has_negation = any(neg in sentence_lower for neg in negation_words)
    has_action = any(act in sentence_lower for act in action_words)

    return has_negation and has_action


def _check_explicit_keyword(sentence_lower: str, lang: str = "de") -> bool:
    """Check if sentence contains explicit guardrail keyword."""
    keywords = GUARDRAIL_KEYWORDS_EN if lang == "en" else GUARDRAIL_KEYWORDS_DE
    return any(kw in sentence_lower for kw in keywords)


def _check_sensitive_area(sentence_lower: str, lang: str = "de") -> bool:
    """Check if sentence mentions sensitive data areas."""
    areas = SENSITIVE_AREAS_EN if lang == "en" else SENSITIVE_AREAS_DE
    return any(area in sentence_lower for area in areas)


def detect_guardrails_v5(
    answers: Dict[str, str],
    lang: str = "de",
) -> Tuple[bool, List[GuardrailHit]]:
    """
    Detect guardrails in freetext fields with confidence scoring.

    This is the v5 implementation with structured GuardrailHit results
    and confidence-based ranking.

    Args:
        answers: Dictionary of user answers
        lang: Language code ("de" or "en")

    Returns:
        Tuple of (has_guardrails: bool, hits: List[GuardrailHit])
    """
    hits: List[GuardrailHit] = []
    seen_sentences: set = set()

    for field_name in FREETEXT_FIELDS:
        text = answers.get(field_name, "")
        if not text or text == "—":
            continue

        # Split into sentences (simple split on . ! ? and newlines)
        sentences = []
        for part in text.replace("\n", ". ").split("."):
            part = part.strip()
            if len(part) > 10:  # Skip very short fragments
                sentences.append(part)

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Skip duplicates
            if sentence_lower in seen_sentences:
                continue

            # Check all detection methods
            has_explicit = _check_explicit_keyword(sentence_lower, lang)
            has_negation_action = _check_negation_action(sentence_lower, lang)
            has_sensitive = _check_sensitive_area(sentence_lower, lang)

            # Count signals for multi-signal boost
            signal_count = sum([has_explicit, has_negation_action, has_sensitive])

            if signal_count > 0:
                # Determine primary reason (priority: negation_action > explicit > sensitive)
                if has_negation_action:
                    reason: GuardrailReason = "negation_action"
                elif has_explicit:
                    reason = "explicit_keyword"
                else:
                    reason = "sensitive_area"

                # Calculate confidence
                confidence = _calculate_confidence(
                    reason=reason,
                    sentence=sentence,
                    field=field_name,
                    lang=lang,
                    has_multiple_signals=(signal_count > 1),
                )

                hit = GuardrailHit(
                    sentence=sentence,
                    reason=reason,
                    confidence=confidence,
                    lang=lang,
                    field=field_name,
                )
                hits.append(hit)
                seen_sentences.add(sentence_lower)

    # Sort by confidence (highest first)
    hits.sort(key=lambda h: h.confidence, reverse=True)

    has_guardrails = len(hits) > 0

    if has_guardrails:
        logger.info(
            "🛡️ Guardrails v5: detected %d hits (lang=%s, high_conf=%d)",
            len(hits),
            lang,
            sum(1 for h in hits if h.is_high_confidence),
        )

    return has_guardrails, hits


def format_guardrail_hits_for_context(hits: List[GuardrailHit], max_hits: int = 5) -> str:
    """
    Format guardrail hits for inclusion in strategic context block.

    Args:
        hits: List of GuardrailHit objects (should be pre-sorted by confidence)
        max_hits: Maximum number of hits to include

    Returns:
        Formatted string for context injection
    """
    if not hits:
        return ""

    # Take top hits by confidence
    top_hits = hits[:max_hits]

    lines = ["Erkannte No-Gos & Leitplanken:"]
    for hit in top_hits:
        lines.append(hit.to_display_string())

    return "\n".join(lines)


# =============================================================================
# Backwards Compatibility
# =============================================================================


def detect_guardrails_in_freetext_v5(
    answers: Dict[str, str],
    lang: str = "de",
) -> Tuple[bool, List[str], List[GuardrailHit]]:
    """
    Backwards-compatible wrapper that returns both string list and hits.

    This allows gradual migration from the old string-based API to the new
    GuardrailHit-based API.

    Args:
        answers: Dictionary of user answers
        lang: Language code

    Returns:
        Tuple of (has_guardrails, snippet_strings, guardrail_hits)
    """
    has_guardrails, hits = detect_guardrails_v5(answers, lang)

    # Extract just the sentences for backwards compatibility
    snippets = [hit.sentence for hit in hits]

    return has_guardrails, snippets, hits
