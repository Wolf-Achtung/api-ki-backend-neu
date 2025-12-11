# -*- coding: utf-8 -*-
"""
SPRINT N3.6 PACKAGE D: Final Tone Harmonizer v5.

End-pass tone cleanup applied after HTML minification but before PDF render:
- Sentence length homogenization
- Big-Four consulting style enforcement
- GPT flair sentence removal
- End-sentence floskel cleanup

Version: 1.0.0 (N3.6 - PLATIN++ v4.21)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Target sentence length for Big-Four consulting style
SENTENCE_LENGTH_MIN = 12  # words
SENTENCE_LENGTH_MAX = 28  # words
SENTENCE_LENGTH_TARGET = 20  # words

# GPT flair sentences to remove entirely
GPT_FLAIR_SENTENCES: List[str] = [
    "In der heutigen Zeit",
    "KI ist ein wichtiges Thema",
    "Abschließend lässt sich sagen",
    "Zusammenfassend lässt sich festhalten",
    "Es ist wichtig zu beachten",
    "Wie bereits erwähnt",
    "Im Folgenden wird erläutert",
    "Nachfolgend werden",
    "An dieser Stelle sei erwähnt",
    "Es sei darauf hingewiesen",
    "Nicht zuletzt",
    "Last but not least",
    "Im Großen und Ganzen",
    "Alles in allem",
    "Unter dem Strich",
    "Grundsätzlich gilt",
    "Generell kann man sagen",
    "In diesem Zusammenhang",
    "In diesem Kontext",
    "Was das betrifft",
    "Diesbezüglich",
    "Hinsichtlich dessen",
]

# End-sentence floskeln to remove
END_SENTENCE_FLOSKELN: List[str] = [
    "insgesamt",
    "abschließend",
    "zusammenfassend",
    "im Endeffekt",
    "letztendlich",
    "schlussendlich",
    "im Ergebnis",
    "summa summarum",
]

# Weak formulations to strengthen
WEAK_TO_STRONG: Dict[str, str] = {
    "könnte man überlegen": "empfiehlt sich",
    "wäre es sinnvoll": "ist empfehlenswert",
    "sollte man bedenken": "ist zu berücksichtigen",
    "könnte hilfreich sein": "unterstützt",
    "wäre empfehlenswert": "ist prioritär",
    "man sollte": "empfohlen wird",
    "es wäre gut": "zielführend ist",
    "vielleicht": "potenziell",
    "eventuell": "gegebenenfalls",
    "möglicherweise": "nach Analyse",
}

# Du-forms that may have slipped through
DU_FORMS_FINAL: Dict[str, str] = {
    "du kannst": "es besteht die Möglichkeit",
    "du solltest": "empfehlenswert ist",
    "du musst": "erforderlich ist",
    "du wirst": "es wird",
    "du hast": "es bestehen",
    "dein": "das entsprechende",
    "deine": "die entsprechende",
    "deinen": "den entsprechenden",
    "deinem": "dem entsprechenden",
    "deiner": "der entsprechenden",
    "dir": "der verantwortlichen Stelle",
    "dich": "sich",
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ToneHarmonizerReport:
    """Report of tone harmonization."""
    sentences_processed: int = 0
    sentences_shortened: int = 0
    sentences_lengthened: int = 0
    flair_sentences_removed: int = 0
    floskeln_removed: int = 0
    weak_forms_strengthened: int = 0
    du_forms_replaced: int = 0
    avg_sentence_length_before: float = 0.0
    avg_sentence_length_after: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sentences_processed": self.sentences_processed,
            "sentences_shortened": self.sentences_shortened,
            "sentences_lengthened": self.sentences_lengthened,
            "flair_sentences_removed": self.flair_sentences_removed,
            "floskeln_removed": self.floskeln_removed,
            "weak_forms_strengthened": self.weak_forms_strengthened,
            "du_forms_replaced": self.du_forms_replaced,
            "avg_sentence_length_before": round(self.avg_sentence_length_before, 1),
            "avg_sentence_length_after": round(self.avg_sentence_length_after, 1),
        }


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def _get_sentences(text: str) -> List[str]:
    """Extract sentences from text."""
    # Simple sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def _calculate_avg_sentence_length(sentences: List[str]) -> float:
    """Calculate average sentence length."""
    if not sentences:
        return 0.0
    total_words = sum(_word_count(s) for s in sentences)
    return total_words / len(sentences)


def remove_gpt_flair_sentences(text: str) -> Tuple[str, int]:
    """
    Remove entire sentences that start with GPT flair phrases.

    Args:
        text: Input text

    Returns:
        Tuple of (cleaned_text, sentences_removed)
    """
    if not text:
        return text, 0

    sentences = _get_sentences(text)
    cleaned_sentences: List[str] = []
    removed_count = 0

    for sentence in sentences:
        sentence_lower = sentence.lower()

        # Check if sentence starts with flair phrase
        is_flair = False
        for flair in GPT_FLAIR_SENTENCES:
            if sentence_lower.startswith(flair.lower()):
                is_flair = True
                removed_count += 1
                break

        if not is_flair:
            cleaned_sentences.append(sentence)

    return ' '.join(cleaned_sentences), removed_count


def remove_end_floskeln(text: str) -> Tuple[str, int]:
    """
    Remove end-sentence floskeln.

    Args:
        text: Input text

    Returns:
        Tuple of (cleaned_text, floskeln_removed)
    """
    if not text:
        return text, 0

    cleaned = text
    removed_count = 0

    for floskel in END_SENTENCE_FLOSKELN:
        # Match floskel at sentence boundaries
        pattern = re.compile(
            rf',?\s*{re.escape(floskel)}\s*[,.]',
            re.IGNORECASE
        )
        if pattern.search(cleaned):
            cleaned = pattern.sub('.', cleaned)
            removed_count += 1

    # Cleanup double periods
    cleaned = re.sub(r'\.{2,}', '.', cleaned)

    return cleaned, removed_count


def strengthen_weak_forms(text: str) -> Tuple[str, int]:
    """
    Replace weak formulations with strong consulting language.

    Args:
        text: Input text

    Returns:
        Tuple of (strengthened_text, replacements_made)
    """
    if not text:
        return text, 0

    strengthened = text
    replaced_count = 0

    for weak, strong in WEAK_TO_STRONG.items():
        pattern = re.compile(re.escape(weak), re.IGNORECASE)
        if pattern.search(strengthened):
            # Preserve case
            def replace_preserve_case(match: re.Match) -> str:
                original = match.group(0)
                if original[0].isupper():
                    return strong[0].upper() + strong[1:]
                return strong

            strengthened = pattern.sub(replace_preserve_case, strengthened)
            replaced_count += 1

    return strengthened, replaced_count


def replace_final_du_forms(text: str) -> Tuple[str, int]:
    """
    Final pass to replace any remaining Du-forms.

    Args:
        text: Input text

    Returns:
        Tuple of (cleaned_text, replacements_made)
    """
    if not text:
        return text, 0

    cleaned = text
    replaced_count = 0

    for du_form, replacement in DU_FORMS_FINAL.items():
        pattern = re.compile(rf'\b{re.escape(du_form)}\b', re.IGNORECASE)
        if pattern.search(cleaned):
            cleaned = pattern.sub(replacement, cleaned)
            replaced_count += 1

    return cleaned, replaced_count


def homogenize_sentence_lengths(text: str) -> Tuple[str, int, int]:
    """
    Homogenize sentence lengths to target range.

    Very long sentences are not modified (would require semantic understanding).
    Very short sentences are flagged but not modified to avoid breaking meaning.

    Args:
        text: Input text

    Returns:
        Tuple of (text, shortened_count, lengthened_count)
    """
    # This is a detection function - actual modification requires more context
    sentences = _get_sentences(text)
    shortened = 0
    lengthened = 0

    for sentence in sentences:
        word_count = _word_count(sentence)
        if word_count > SENTENCE_LENGTH_MAX:
            shortened += 1  # Flag for potential shortening
        elif word_count < SENTENCE_LENGTH_MIN:
            lengthened += 1  # Flag for potential extension

    # Return unchanged - modifications need more context
    return text, shortened, lengthened


def apply_tone_harmonizer_final(html: str) -> Tuple[str, ToneHarmonizerReport]:
    """
    N3.6 PACKAGE D: Apply final tone harmonization pass.

    This function runs AFTER HTML minification but BEFORE PDF render.

    Applies:
    1. GPT flair sentence removal
    2. End-sentence floskel cleanup
    3. Weak → Strong formulation replacement
    4. Final Du-form replacement
    5. Sentence length analysis

    Args:
        html: Input HTML

    Returns:
        Tuple of (harmonized_html, report)
    """
    report = ToneHarmonizerReport()

    if not html:
        return html, report

    harmonized = html

    # Extract text content for analysis
    text_only = re.sub(r'<[^>]+>', ' ', harmonized)
    sentences_before = _get_sentences(text_only)
    report.avg_sentence_length_before = _calculate_avg_sentence_length(sentences_before)
    report.sentences_processed = len(sentences_before)

    # Step 1: Remove GPT flair sentences
    harmonized, flair_removed = remove_gpt_flair_sentences(harmonized)
    report.flair_sentences_removed = flair_removed

    # Step 2: Remove end-sentence floskeln
    harmonized, floskeln_removed = remove_end_floskeln(harmonized)
    report.floskeln_removed = floskeln_removed

    # Step 3: Strengthen weak formulations
    harmonized, weak_replaced = strengthen_weak_forms(harmonized)
    report.weak_forms_strengthened = weak_replaced

    # Step 4: Final Du-form replacement
    harmonized, du_replaced = replace_final_du_forms(harmonized)
    report.du_forms_replaced = du_replaced

    # Step 5: Analyze sentence lengths (detection only)
    _, shortened, lengthened = homogenize_sentence_lengths(harmonized)
    report.sentences_shortened = shortened
    report.sentences_lengthened = lengthened

    # Calculate final average
    text_after = re.sub(r'<[^>]+>', ' ', harmonized)
    sentences_after = _get_sentences(text_after)
    report.avg_sentence_length_after = _calculate_avg_sentence_length(sentences_after)

    # Cleanup artifacts
    harmonized = re.sub(r'\s{2,}', ' ', harmonized)
    harmonized = re.sub(r'<p>\s*</p>', '', harmonized)

    total_changes = (
        flair_removed + floskeln_removed + weak_replaced + du_replaced
    )

    if total_changes > 0:
        log.info(
            "[N3.6-ToneFinal] Harmonized: flair=%d, floskeln=%d, weak=%d, du=%d",
            flair_removed, floskeln_removed, weak_replaced, du_replaced
        )

    return harmonized.strip(), report


def process_sections_tone_final(
    sections: Dict[str, Any],
) -> Tuple[Dict[str, Any], ToneHarmonizerReport]:
    """
    N3.6: Apply final tone harmonization to all sections.

    Args:
        sections: Section dictionary

    Returns:
        Tuple of (harmonized_sections, aggregated_report)
    """
    harmonized = dict(sections)
    total_report = ToneHarmonizerReport()

    for section_id, content in sections.items():
        # Skip metadata
        if section_id.startswith("_"):
            continue

        # Skip non-string content
        if not isinstance(content, str):
            continue

        harmonized_content, report = apply_tone_harmonizer_final(content)
        harmonized[section_id] = harmonized_content

        # Aggregate report
        total_report.sentences_processed += report.sentences_processed
        total_report.flair_sentences_removed += report.flair_sentences_removed
        total_report.floskeln_removed += report.floskeln_removed
        total_report.weak_forms_strengthened += report.weak_forms_strengthened
        total_report.du_forms_replaced += report.du_forms_replaced

    if total_report.flair_sentences_removed > 0 or total_report.weak_forms_strengthened > 0:
        log.info(
            "[N3.6-ToneFinal] Sections harmonized: %d flair, %d weak forms",
            total_report.flair_sentences_removed,
            total_report.weak_forms_strengthened
        )

    return harmonized, total_report
