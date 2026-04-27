# -*- coding: utf-8 -*-
"""
SPRINT N3.8 PACKAGE E: Zero-Redundancy Engine.

Ensures 0 duplicate content in the report:
- Semantic similarity search (cosine-like)
- Redundant paragraph detection
- Automatic summarization/shortening
- "New Insight" replacement for repetitions
- Cross-section deduplication

Version: 1.0.0 (N3.8 - PLATIN++ v4.24)
"""
from __future__ import annotations

import logging
import re
import hashlib
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import Counter

log = logging.getLogger(__name__)

# Type alias
SectionDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

# Similarity thresholds
SENTENCE_SIMILARITY_THRESHOLD = 0.85  # For sentence-level redundancy
PARAGRAPH_SIMILARITY_THRESHOLD = 0.80  # For paragraph-level redundancy
EXACT_MATCH_THRESHOLD = 0.95  # Near-exact duplicates

# Minimum lengths for analysis
MIN_SENTENCE_LENGTH = 30  # characters
MIN_PARAGRAPH_LENGTH = 100  # characters
MIN_WORDS_FOR_ANALYSIS = 10

# Maximum redundancy score before healing is required
MAX_REDUNDANCY_SCORE = 20

# Sections to analyze for redundancy
REDUNDANCY_SECTIONS: List[str] = [
    "exec_summary",
    "executive_summary",
    "ki_stack_summary",
    "recommendations",
    "risks",
    "risk_report",
    "roadmap_90d",
    "roadmap_12m",
    "strategie_governance",
    "wettbewerb_benchmark",
    "gamechanger",
    "foerderpotenzial",
    "tools_empfehlungen",
    "business_case",
    "unternehmensprofil_markt",
    "branch_deep_dive",
    "org_change",
    "data_readiness",
    "roadmap_90d_decision",
]

# Phrases that indicate intentional repetition (allowed)
ALLOWED_REPETITION_MARKERS: List[str] = [
    "wie bereits erwähnt",
    "as mentioned",
    "zusammenfassend",
    "in summary",
    "zur erinnerung",
    "as a reminder",
]

# New insight phrase templates (German)
NEW_INSIGHT_TEMPLATES: List[str] = [
    "Ergänzend hierzu:",
    "Ein weiterer Aspekt:",
    "Zusätzlich zu beachten:",
    "Darüber hinaus:",
    "Als weitere Perspektive:",
    "Im Detail bedeutet dies:",
    "Konkret ergibt sich:",
    "Speziell für diesen Kontext:",
]

# Stop words for similarity calculation (German + English)
STOP_WORDS: Set[str] = {
    # German
    "der", "die", "das", "ein", "eine", "und", "oder", "aber", "in", "im",
    "zu", "für", "von", "mit", "auf", "ist", "sind", "wird", "werden",
    "kann", "können", "bei", "durch", "als", "auch", "nach", "über",
    "unter", "vor", "zwischen", "sowie", "dass", "wenn", "da", "weil",
    "um", "aus", "an", "es", "sich", "nicht", "nur", "noch", "schon",
    "sehr", "mehr", "wie", "was", "welche", "welcher", "welches",
    # English
    "the", "a", "an", "and", "or", "but", "in", "to", "for", "of",
    "with", "on", "is", "are", "will", "be", "can", "at", "by", "as",
    "also", "after", "about", "between", "that", "if", "because",
    "from", "it", "not", "only", "still", "already", "very", "more",
    "how", "what", "which",
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RedundancyMatch:
    """A redundancy match found during analysis."""
    section1: str
    section2: str
    text1: str
    text2: str
    similarity: float
    match_type: str  # 'exact', 'near', 'semantic', 'partial'
    line_number1: int = 0
    line_number2: int = 0
    healed: bool = False
    healing_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "section1": self.section1,
            "section2": self.section2,
            "text1_preview": self.text1[:100] + "..." if len(self.text1) > 100 else self.text1,
            "text2_preview": self.text2[:100] + "..." if len(self.text2) > 100 else self.text2,
            "similarity": self.similarity,
            "match_type": self.match_type,
            "healed": self.healed,
            "healing_action": self.healing_action,
        }


@dataclass
class RedundancyReport:
    """Report from redundancy analysis."""
    sections_analyzed: int = 0
    sentences_checked: int = 0
    paragraphs_checked: int = 0
    exact_duplicates: int = 0
    near_duplicates: int = 0
    semantic_duplicates: int = 0
    matches: List[RedundancyMatch] = field(default_factory=list)
    healed_matches: int = 0
    redundancy_score: float = 0.0

    def add_match(self, match: RedundancyMatch) -> None:
        """Add a match to the report."""
        self.matches.append(match)

        if match.match_type == "exact":
            self.exact_duplicates += 1
            self.redundancy_score += 10
        elif match.match_type == "near":
            self.near_duplicates += 1
            self.redundancy_score += 5
        elif match.match_type == "semantic":
            self.semantic_duplicates += 1
            self.redundancy_score += 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sections_analyzed": self.sections_analyzed,
            "sentences_checked": self.sentences_checked,
            "paragraphs_checked": self.paragraphs_checked,
            "exact_duplicates": self.exact_duplicates,
            "near_duplicates": self.near_duplicates,
            "semantic_duplicates": self.semantic_duplicates,
            "total_matches": len(self.matches),
            "matches": [m.to_dict() for m in self.matches],
            "healed_matches": self.healed_matches,
            "redundancy_score": self.redundancy_score,
            "grade": self.get_grade(),
        }

    def get_grade(self) -> str:
        """Get grade based on redundancy score."""
        if self.redundancy_score <= 5:
            return "A"
        elif self.redundancy_score <= 15:
            return "B"
        elif self.redundancy_score <= 30:
            return "C"
        elif self.redundancy_score <= 50:
            return "D"
        else:
            return "F"


# =============================================================================
# TEXT UTILITIES
# =============================================================================

def extract_text_from_html(html: str) -> str:
    """Extract plain text from HTML."""
    if not html:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text."""
    if not text:
        return []

    # Split by sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter and clean
    result = []
    for s in sentences:
        s = s.strip()
        if len(s) >= MIN_SENTENCE_LENGTH:
            result.append(s)

    return result


def extract_paragraphs(text: str) -> List[str]:
    """Extract paragraphs from text."""
    if not text:
        return []

    # Split by double newlines or <p> tags
    paragraphs = re.split(r'\n\n+|<p[^>]*>|</p>', text)

    # Filter and clean
    result = []
    for p in paragraphs:
        p = extract_text_from_html(p).strip()
        if len(p) >= MIN_PARAGRAPH_LENGTH:
            result.append(p)

    return result


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Lowercase
    text = text.lower()

    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def get_content_hash(text: str) -> str:
    """Get hash of normalized text."""
    normalized = normalize_text(text)
    return hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()


def get_word_set(text: str) -> Set[str]:
    """Get set of significant words from text."""
    words = normalize_text(text).split()
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


# =============================================================================
# SIMILARITY CALCULATION
# =============================================================================

def calculate_sequence_similarity(text1: str, text2: str) -> float:
    """Calculate sequence-based similarity."""
    if not text1 or not text2:
        return 0.0

    t1 = normalize_text(text1)
    t2 = normalize_text(text2)

    return SequenceMatcher(None, t1, t2).ratio()


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity based on word sets."""
    words1 = get_word_set(text1)
    words2 = get_word_set(text2)

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def calculate_combined_similarity(text1: str, text2: str) -> float:
    """Calculate combined similarity score."""
    seq_sim = calculate_sequence_similarity(text1, text2)
    jaccard_sim = calculate_jaccard_similarity(text1, text2)

    # Weighted combination
    return 0.6 * seq_sim + 0.4 * jaccard_sim


def determine_match_type(similarity: float) -> str:
    """Determine the type of match based on similarity."""
    if similarity >= EXACT_MATCH_THRESHOLD:
        return "exact"
    elif similarity >= SENTENCE_SIMILARITY_THRESHOLD:
        return "near"
    elif similarity >= PARAGRAPH_SIMILARITY_THRESHOLD:
        return "semantic"
    else:
        return "partial"


# =============================================================================
# REDUNDANCY DETECTION
# =============================================================================

def detect_sentence_redundancy(
    sections: SectionDict,
    report: RedundancyReport
) -> List[RedundancyMatch]:
    """
    Detect sentence-level redundancy across sections.
    """
    matches: List[RedundancyMatch] = []
    sentence_cache: Dict[str, Dict[str, List[Tuple[str, int]]]] = {}  # section -> hash -> [(text, line)]

    log.info("[N3.8-Redundancy] Detecting sentence-level redundancy...")

    # Extract sentences from all sections
    for section in REDUNDANCY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = sections.get(html_key) or sections.get(section, "")

        if not isinstance(content, str) or not content:
            continue

        text = extract_text_from_html(content)
        sentences = extract_sentences(text)

        sentence_cache[section] = {}
        for idx, sent in enumerate(sentences):
            report.sentences_checked += 1
            sent_hash = get_content_hash(sent)

            if sent_hash not in sentence_cache[section]:
                sentence_cache[section][sent_hash] = []
            sentence_cache[section][sent_hash].append((sent, idx))

    # Compare sentences across sections
    section_list = list(sentence_cache.keys())
    checked_pairs: Set[Tuple[str, str]] = set()

    for i, sec1 in enumerate(section_list):
        for sec2 in section_list[i:]:
            sorted_pair = sorted([sec1, sec2])
            pair_key: Tuple[str, str] = (sorted_pair[0], sorted_pair[1])
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            # Check for hash collisions (exact matches)
            for hash1, items1 in sentence_cache[sec1].items():
                if sec1 == sec2:
                    # Same section - check for duplicate sentences
                    if len(items1) > 1:
                        for j, (text1, line1) in enumerate(items1):
                            for text2, line2 in items1[j + 1:]:
                                match = RedundancyMatch(
                                    section1=sec1,
                                    section2=sec1,
                                    text1=text1,
                                    text2=text2,
                                    similarity=1.0,
                                    match_type="exact",
                                    line_number1=line1,
                                    line_number2=line2,
                                )
                                matches.append(match)
                                report.add_match(match)
                else:
                    # Different sections
                    if hash1 in sentence_cache[sec2]:
                        for text1, line1 in items1:
                            for text2, line2 in sentence_cache[sec2][hash1]:
                                match = RedundancyMatch(
                                    section1=sec1,
                                    section2=sec2,
                                    text1=text1,
                                    text2=text2,
                                    similarity=1.0,
                                    match_type="exact",
                                    line_number1=line1,
                                    line_number2=line2,
                                )
                                matches.append(match)
                                report.add_match(match)

            # Check for near-matches (similarity-based)
            for hash1, items1 in sentence_cache[sec1].items():
                for hash2, items2 in sentence_cache.get(sec2, {}).items():
                    if hash1 == hash2:
                        continue  # Already handled exact matches

                    for text1, line1 in items1:
                        for text2, line2 in items2:
                            similarity = calculate_combined_similarity(text1, text2)

                            if similarity >= SENTENCE_SIMILARITY_THRESHOLD:
                                match = RedundancyMatch(
                                    section1=sec1,
                                    section2=sec2,
                                    text1=text1,
                                    text2=text2,
                                    similarity=similarity,
                                    match_type=determine_match_type(similarity),
                                    line_number1=line1,
                                    line_number2=line2,
                                )
                                matches.append(match)
                                report.add_match(match)

    return matches


def detect_paragraph_redundancy(
    sections: SectionDict,
    report: RedundancyReport
) -> List[RedundancyMatch]:
    """
    Detect paragraph-level redundancy across sections.
    """
    matches: List[RedundancyMatch] = []
    paragraph_cache: Dict[str, List[Tuple[str, int]]] = {}  # section -> [(text, idx)]

    log.info("[N3.8-Redundancy] Detecting paragraph-level redundancy...")

    # Extract paragraphs from all sections
    for section in REDUNDANCY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = sections.get(html_key) or sections.get(section, "")

        if not isinstance(content, str) or not content:
            continue

        text = extract_text_from_html(content)
        paragraphs = extract_paragraphs(text)

        paragraph_cache[section] = [(p, idx) for idx, p in enumerate(paragraphs)]
        report.paragraphs_checked += len(paragraphs)

    # Compare paragraphs across sections
    section_list = list(paragraph_cache.keys())

    for i, sec1 in enumerate(section_list):
        for sec2 in section_list[i + 1:]:
            for para1, idx1 in paragraph_cache[sec1]:
                for para2, idx2 in paragraph_cache[sec2]:
                    similarity = calculate_combined_similarity(para1, para2)

                    if similarity >= PARAGRAPH_SIMILARITY_THRESHOLD:
                        match = RedundancyMatch(
                            section1=sec1,
                            section2=sec2,
                            text1=para1,
                            text2=para2,
                            similarity=similarity,
                            match_type=determine_match_type(similarity),
                            line_number1=idx1,
                            line_number2=idx2,
                        )
                        matches.append(match)
                        report.add_match(match)

    return matches


def detect_key_phrase_repetition(
    sections: SectionDict,
    report: RedundancyReport
) -> List[RedundancyMatch]:
    """
    Detect repeated key phrases across sections.
    """
    matches: List[RedundancyMatch] = []

    log.info("[N3.8-Redundancy] Detecting key phrase repetition...")

    # Extract all content
    all_text = ""
    for section in REDUNDANCY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = sections.get(html_key) or sections.get(section, "")
        if isinstance(content, str):
            all_text += " " + extract_text_from_html(content)

    # Find repeated phrases (3-6 words)
    words = all_text.lower().split()
    phrase_counts: Counter[str] = Counter()

    for n in range(3, 7):  # 3 to 6 word phrases
        for i in range(len(words) - n + 1):
            phrase = ' '.join(words[i:i + n])
            # Skip if contains only stop words
            if all(w in STOP_WORDS for w in words[i:i + n]):
                continue
            phrase_counts[phrase] += 1

    # Report phrases that appear more than twice
    for phrase, count in phrase_counts.most_common(20):
        if count >= 3:
            # Find which sections contain this phrase
            sections_with_phrase = []
            for section in REDUNDANCY_SECTIONS:
                html_key = f"{section.upper()}_HTML"
                content = sections.get(html_key) or sections.get(section, "")
                if isinstance(content, str) and phrase in content.lower():
                    sections_with_phrase.append(section)

            if len(sections_with_phrase) >= 2:
                match = RedundancyMatch(
                    section1=sections_with_phrase[0],
                    section2=sections_with_phrase[1],
                    text1=phrase,
                    text2=f"Appears {count} times across {len(sections_with_phrase)} sections",
                    similarity=1.0,
                    match_type="semantic",
                )
                matches.append(match)
                # Don't add to report score - this is informational

    return matches


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def analyze_redundancy(sections: SectionDict) -> RedundancyReport:
    """
    N3.8: Full redundancy analysis.

    Detects:
    - Exact sentence duplicates
    - Near-duplicate sentences
    - Paragraph-level redundancy
    - Key phrase repetition

    Args:
        sections: Dictionary of section contents

    Returns:
        RedundancyReport with findings
    """
    report = RedundancyReport()

    log.info("[N3.8-Redundancy] Starting redundancy analysis...")

    # Count analyzable sections
    for section in REDUNDANCY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        if sections.get(html_key) or sections.get(section):
            report.sections_analyzed += 1

    # Run detection algorithms
    detect_sentence_redundancy(sections, report)
    detect_paragraph_redundancy(sections, report)
    detect_key_phrase_repetition(sections, report)

    log.info(
        "[N3.8-Redundancy] Analysis complete: sections=%d sentences=%d exact=%d near=%d semantic=%d score=%.1f",
        report.sections_analyzed,
        report.sentences_checked,
        report.exact_duplicates,
        report.near_duplicates,
        report.semantic_duplicates,
        report.redundancy_score
    )

    return report


# =============================================================================
# HEALING FUNCTIONS
# =============================================================================

def remove_duplicate_sentences(
    sections: SectionDict,
    report: RedundancyReport
) -> SectionDict:
    """
    Remove exact duplicate sentences, keeping first occurrence.
    """
    healed = dict(sections)

    log.info("[N3.8-Redundancy] Removing duplicate sentences...")

    # Group matches by section
    exact_matches = [m for m in report.matches if m.match_type == "exact" and not m.healed]

    for match in exact_matches:
        # Remove from second occurrence section
        target_section = match.section2
        html_key = f"{target_section.upper()}_HTML"
        content = healed.get(html_key) or healed.get(target_section, "")

        if not isinstance(content, str):
            continue

        # Remove the duplicate text
        if match.text2 in content:
            content = content.replace(match.text2, "", 1)
            # Clean up any resulting empty paragraphs
            content = re.sub(r'<p>\s*</p>', '', content)
            content = re.sub(r'\s{2,}', ' ', content)

            if html_key in healed:
                healed[html_key] = content
            else:
                healed[target_section] = content

            match.healed = True
            match.healing_action = "removed"
            report.healed_matches += 1

    return healed


def replace_with_new_insight(
    sections: SectionDict,
    report: RedundancyReport
) -> SectionDict:
    """
    Replace near-duplicate content with new insight phrases.
    """
    healed = dict(sections)

    log.info("[N3.8-Redundancy] Replacing with new insights...")

    near_matches = [m for m in report.matches if m.match_type == "near" and not m.healed]
    insight_idx = 0

    for match in near_matches:
        # Get a new insight template
        insight = NEW_INSIGHT_TEMPLATES[insight_idx % len(NEW_INSIGHT_TEMPLATES)]
        insight_idx += 1

        target_section = match.section2
        html_key = f"{target_section.upper()}_HTML"
        content = healed.get(html_key) or healed.get(target_section, "")

        if not isinstance(content, str):
            continue

        # Replace near-duplicate with insight marker
        if match.text2 in content:
            # Find unique aspects of text2 not in text1
            words1 = get_word_set(match.text1)
            words2 = get_word_set(match.text2)
            unique_words = words2 - words1

            if unique_words:
                # Create a shortened version focusing on unique content
                replacement = f"{insight} {' '.join(list(unique_words)[:10])}"
                content = content.replace(match.text2, replacement, 1)

                if html_key in healed:
                    healed[html_key] = content
                else:
                    healed[target_section] = content

                match.healed = True
                match.healing_action = "replaced_with_insight"
                report.healed_matches += 1

    return healed


def summarize_redundant_paragraphs(
    sections: SectionDict,
    report: RedundancyReport
) -> SectionDict:
    """
    Summarize redundant paragraphs.
    """
    healed = dict(sections)

    log.info("[N3.8-Redundancy] Summarizing redundant paragraphs...")

    semantic_matches = [m for m in report.matches if m.match_type == "semantic" and not m.healed]

    for match in semantic_matches:
        target_section = match.section2
        html_key = f"{target_section.upper()}_HTML"
        content = healed.get(html_key) or healed.get(target_section, "")

        if not isinstance(content, str):
            continue

        if match.text2 in content:
            # Create a summary (first sentence + reference)
            sentences = extract_sentences(match.text2)
            if sentences:
                summary = f"{sentences[0]} (Details siehe {match.section1})"
                content = content.replace(match.text2, summary, 1)

                if html_key in healed:
                    healed[html_key] = content
                else:
                    healed[target_section] = content

                match.healed = True
                match.healing_action = "summarized"
                report.healed_matches += 1

    return healed


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_redundancy(sections: SectionDict) -> Tuple[SectionDict, RedundancyReport]:
    """
    N3.8: Full redundancy processing pipeline.

    1. Analyze redundancy
    2. Remove exact duplicates
    3. Replace near-duplicates with insights
    4. Summarize semantic duplicates

    Args:
        sections: Dictionary of section contents

    Returns:
        Tuple of (processed_sections, report)
    """
    log.info("[N3.8-Redundancy] Starting full redundancy processing...")

    # Step 1: Analyze
    report = analyze_redundancy(sections)

    # Step 2: Remove exact duplicates
    healed = remove_duplicate_sentences(sections, report)

    # Step 3: Replace near-duplicates
    healed = replace_with_new_insight(healed, report)

    # Step 4: Summarize semantic duplicates
    healed = summarize_redundant_paragraphs(healed, report)

    # Set redundancy flag
    healed["_redundancy_processed"] = True
    healed["_redundancy_report"] = report.to_dict()

    log.info(
        "[N3.8-Redundancy] Complete: score=%.1f grade=%s healed=%d/%d",
        report.redundancy_score,
        report.get_grade(),
        report.healed_matches,
        len(report.matches)
    )

    return healed, report


def get_redundancy_summary(report: RedundancyReport) -> str:
    """
    Generate human-readable redundancy summary.

    Args:
        report: RedundancyReport

    Returns:
        Summary string
    """
    return (
        f"Redundancy Score: {report.redundancy_score:.1f} (Grade: {report.get_grade()})\n"
        f"Sections: {report.sections_analyzed} | Sentences: {report.sentences_checked} | Paragraphs: {report.paragraphs_checked}\n"
        f"Exact: {report.exact_duplicates} | Near: {report.near_duplicates} | Semantic: {report.semantic_duplicates}\n"
        f"Healed: {report.healed_matches}/{len(report.matches)}"
    )
