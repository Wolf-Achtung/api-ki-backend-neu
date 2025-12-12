"""
Insight Compression Engine - N4.1 PLATIN+++ Executive Experience Layer.

McKinsey Pyramid Builder providing:
- MECE compression of long paragraphs
- "Top-Line → Sub-Argument → Evidence" automatic generation
- Each section receives: 1 Key Insight + 3 Evidence Points + 1 Leadership Action

Integrates with Knowledge Fusion Engine for signal filtering.
Board-Ready. Investment-Ready. C-Level-Perfect.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypedDict

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPE DEFINITIONS
# =============================================================================


class PyramidLevel(Enum):
    """Pyramid hierarchy levels."""
    TOP_LINE = "top_line"
    SUB_ARGUMENT = "sub_argument"
    EVIDENCE = "evidence"


class InsightType(Enum):
    """Types of insights."""
    STRATEGIC = "strategic"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class ActionUrgency(Enum):
    """Leadership action urgency levels."""
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    STRATEGIC = "strategic"


class PyramidNode(TypedDict):
    """Node in the pyramid structure."""
    id: str
    level: str
    content: str
    supporting_nodes: List[str]
    evidence_strength: float


class CompressedInsight(TypedDict):
    """Compressed insight structure."""
    key_insight: str
    evidence_points: List[str]
    leadership_action: str
    insight_type: str
    confidence: float


class SectionPyramid(TypedDict):
    """Complete pyramid for a section."""
    section_id: str
    top_line: str
    sub_arguments: List[str]
    evidence_items: List[str]
    compressed_insight: CompressedInsight
    mece_score: float


class CompressionResult(TypedDict):
    """Overall compression result."""
    total_sections: int
    compression_ratio: float
    pyramids: List[SectionPyramid]
    quality_score: float


# =============================================================================
# CONFIGURATION
# =============================================================================


COMPRESSION_CONFIG: Dict[str, Any] = {
    "max_top_line_words": 25,
    "max_sub_argument_words": 40,
    "max_evidence_words": 60,
    "target_sub_arguments": 3,
    "target_evidence_points": 3,
    "min_mece_score": 0.7,
    "deduplication_threshold": 0.8,
}


# Insight extraction patterns
INSIGHT_PATTERNS: Dict[InsightType, List[str]] = {
    InsightType.STRATEGIC: [
        r"strateg\w+", r"wettbewerb\w+", r"markt\w+", r"position\w+",
        r"differenzier\w+", r"vorteil\w+",
    ],
    InsightType.FINANCIAL: [
        r"roi", r"ebit", r"kosten\w*", r"invest\w+", r"rendite",
        r"ersparnis\w*", r"budget", r"\d+\s*(mio|tsd|%|eur)",
    ],
    InsightType.OPERATIONAL: [
        r"prozess\w*", r"effizienz\w*", r"automat\w+", r"produkt\w+",
        r"workflow", r"optimier\w+",
    ],
    InsightType.RISK: [
        r"risik\w+", r"compliance", r"governance", r"regulat\w+",
        r"ai.?act", r"dsgvo", r"gefahr\w*",
    ],
    InsightType.OPPORTUNITY: [
        r"chance\w*", r"potenzial\w*", r"möglichkeit\w*", r"wachstum\w*",
        r"innovation\w*", r"zukunft\w*",
    ],
}


# Leadership action templates by insight type
ACTION_TEMPLATES: Dict[InsightType, List[str]] = {
    InsightType.STRATEGIC: [
        "Strategische Ausrichtung im Vorstand bestätigen",
        "Wettbewerbspositionierung überprüfen und anpassen",
        "Marktchancen priorisieren und Ressourcen zuweisen",
    ],
    InsightType.FINANCIAL: [
        "Investitionsfreigabe im nächsten Budget-Zyklus einplanen",
        "ROI-Tracking und KPI-Dashboard etablieren",
        "Business Case für Aufsichtsgremien finalisieren",
    ],
    InsightType.OPERATIONAL: [
        "Prozessoptimierung als Pilotprojekt initiieren",
        "Automatisierungsroadmap verabschieden",
        "Effizienzpotenziale in Quarterly Review verfolgen",
    ],
    InsightType.RISK: [
        "Compliance-Roadmap in nächster Vorstandssitzung vorstellen",
        "Risk Mitigation Plan implementieren",
        "Governance-Framework etablieren und kommunizieren",
    ],
    InsightType.OPPORTUNITY: [
        "Chancen in strategische Planung integrieren",
        "Innovation-Pipeline mit identifizierten Potenzialen befüllen",
        "Quick-Win-Projekte priorisieren und starten",
    ],
}


# =============================================================================
# TEXT ANALYSIS UTILITIES
# =============================================================================


class TextAnalyzer:
    """Utilities for text analysis and extraction."""

    def __init__(self) -> None:
        self._sentence_pattern = re.compile(r"[.!?]\s+")
        self._word_pattern = re.compile(r"\b\w+\b")

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = self._sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def count_words(self, text: str) -> int:
        """Count words in text."""
        return len(self._word_pattern.findall(text))

    def truncate_to_words(self, text: str, max_words: int) -> str:
        """Truncate text to maximum word count."""
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "..."

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word-based similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def extract_key_terms(self, text: str, top_n: int = 5) -> List[str]:
        """Extract key terms from text."""
        # Simple stopword filtering
        stopwords = {
            "der", "die", "das", "und", "oder", "in", "von", "mit", "für",
            "auf", "ist", "sind", "wird", "werden", "kann", "können",
            "ein", "eine", "einer", "eines", "zu", "zur", "zum", "als",
            "auch", "bei", "durch", "nach", "über", "unter", "an", "aus",
        }

        words = self._word_pattern.findall(text.lower())
        filtered = [w for w in words if w not in stopwords and len(w) > 3]

        # Count frequencies
        freq: Dict[str, int] = {}
        for word in filtered:
            freq[word] = freq.get(word, 0) + 1

        # Sort by frequency
        sorted_terms = sorted(freq.items(), key=lambda x: x[1], reverse=True)

        return [term for term, _ in sorted_terms[:top_n]]


# =============================================================================
# PYRAMID STRUCTURE BUILDER
# =============================================================================


class PyramidStructureBuilder:
    """
    Builds MECE pyramid structure from content.

    Implements McKinsey Pyramid Principle:
    - Top-Line: Main message (1 sentence)
    - Sub-Arguments: Supporting points (typically 3)
    - Evidence: Data and facts supporting each argument
    """

    def __init__(self) -> None:
        self._analyzer = TextAnalyzer()

    def build_pyramid(
        self,
        section_id: str,
        content: str,
    ) -> SectionPyramid:
        """
        Build pyramid structure for a section.

        Args:
            section_id: Section identifier
            content: Section content

        Returns:
            SectionPyramid structure
        """
        # Extract components
        top_line = self._extract_top_line(content)
        sub_arguments = self._extract_sub_arguments(content)
        evidence = self._extract_evidence(content)

        # Create compressed insight
        insight = self._create_compressed_insight(
            top_line, sub_arguments, evidence, content,
        )

        # Calculate MECE score
        mece_score = self._calculate_mece_score(sub_arguments, evidence)

        return SectionPyramid(
            section_id=section_id,
            top_line=top_line,
            sub_arguments=sub_arguments,
            evidence_items=evidence,
            compressed_insight=insight,
            mece_score=mece_score,
        )

    def _extract_top_line(self, content: str) -> str:
        """Extract the top-line message."""
        sentences = self._analyzer.split_sentences(content)

        if not sentences:
            return "Keine Kernaussage identifiziert."

        # Look for sentences with strong indicators
        strong_indicators = [
            "fazit", "zusammenfassung", "kernaussage", "entscheidend",
            "hauptergebnis", "ergebnis zeigt", "analyse zeigt",
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(ind in sentence_lower for ind in strong_indicators):
                return self._analyzer.truncate_to_words(
                    sentence, COMPRESSION_CONFIG["max_top_line_words"],
                )

        # Fall back to first substantive sentence
        for sentence in sentences[:3]:
            if self._analyzer.count_words(sentence) >= 8:
                return self._analyzer.truncate_to_words(
                    sentence, COMPRESSION_CONFIG["max_top_line_words"],
                )

        return self._analyzer.truncate_to_words(
            sentences[0], COMPRESSION_CONFIG["max_top_line_words"],
        )

    def _extract_sub_arguments(self, content: str) -> List[str]:
        """Extract sub-arguments from content."""
        sentences = self._analyzer.split_sentences(content)
        sub_arguments: List[str] = []

        # Patterns indicating argumentation
        argument_patterns = [
            r"erstens|zweitens|drittens",
            r"zum einen|zum anderen",
            r"einerseits|andererseits",
            r"zusätzlich|darüber hinaus|weiterhin",
            r"ein weiterer aspekt|ein wichtiger punkt",
            r"\d+\.\s+\w+",  # Numbered points
        ]

        # Find sentences matching argument patterns
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for pattern in argument_patterns:
                if re.search(pattern, sentence_lower):
                    truncated = self._analyzer.truncate_to_words(
                        sentence, COMPRESSION_CONFIG["max_sub_argument_words"],
                    )
                    if truncated not in sub_arguments:
                        sub_arguments.append(truncated)
                    break

        # If not enough, extract by topic clustering
        if len(sub_arguments) < COMPRESSION_CONFIG["target_sub_arguments"]:
            additional = self._extract_by_topic(
                sentences,
                COMPRESSION_CONFIG["target_sub_arguments"] - len(sub_arguments),
            )
            sub_arguments.extend(additional)

        return sub_arguments[:COMPRESSION_CONFIG["target_sub_arguments"]]

    def _extract_evidence(self, content: str) -> List[str]:
        """Extract evidence items from content."""
        sentences = self._analyzer.split_sentences(content)
        evidence: List[str] = []

        # Patterns indicating evidence/data
        evidence_patterns = [
            r"\d+\s*%",  # Percentages
            r"\d+\s*(mio|tsd|million|thousand)",  # Numbers
            r"studie|untersuchung|analyse zeigt",
            r"laut|gemäß|entsprechend",
            r"beispiel|konkret|insbesondere",
            r"\d+\s*(€|eur|euro)",  # Currency
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            for pattern in evidence_patterns:
                if re.search(pattern, sentence_lower, re.IGNORECASE):
                    truncated = self._analyzer.truncate_to_words(
                        sentence, COMPRESSION_CONFIG["max_evidence_words"],
                    )
                    if truncated not in evidence:
                        evidence.append(truncated)
                    break

        return evidence[:COMPRESSION_CONFIG["target_evidence_points"]]

    def _extract_by_topic(
        self,
        sentences: List[str],
        count: int,
    ) -> List[str]:
        """Extract sentences by topic diversity."""
        if not sentences:
            return []

        # Simple approach: take sentences with unique key terms
        selected: List[str] = []
        used_terms: set = set()

        for sentence in sentences:
            terms = self._analyzer.extract_key_terms(sentence, 3)
            new_terms = [t for t in terms if t not in used_terms]

            if new_terms:
                truncated = self._analyzer.truncate_to_words(
                    sentence, COMPRESSION_CONFIG["max_sub_argument_words"],
                )
                selected.append(truncated)
                used_terms.update(terms)

            if len(selected) >= count:
                break

        return selected

    def _create_compressed_insight(
        self,
        top_line: str,
        sub_arguments: List[str],
        evidence: List[str],
        full_content: str,
    ) -> CompressedInsight:
        """Create compressed insight structure."""
        insight_type = self._classify_insight_type(full_content)
        action = self._generate_leadership_action(insight_type, top_line)
        confidence = self._calculate_confidence(sub_arguments, evidence)

        return CompressedInsight(
            key_insight=top_line,
            evidence_points=evidence[:3],
            leadership_action=action,
            insight_type=insight_type.value,
            confidence=confidence,
        )

    def _classify_insight_type(self, content: str) -> InsightType:
        """Classify the type of insight."""
        content_lower = content.lower()
        scores: Dict[InsightType, int] = {}

        for insight_type, patterns in INSIGHT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, content_lower)
                score += len(matches)
            scores[insight_type] = score

        if not scores or max(scores.values()) == 0:
            return InsightType.STRATEGIC

        return max(scores, key=lambda x: scores[x])

    def _generate_leadership_action(
        self,
        insight_type: InsightType,
        top_line: str,
    ) -> str:
        """Generate appropriate leadership action."""
        templates = ACTION_TEMPLATES.get(insight_type, ACTION_TEMPLATES[InsightType.STRATEGIC])

        # Select template based on content hints
        for template in templates:
            # Simple matching - could be enhanced
            return template

        return templates[0]

    def _calculate_confidence(
        self,
        sub_arguments: List[str],
        evidence: List[str],
    ) -> float:
        """Calculate confidence score for the insight."""
        # Based on argument and evidence completeness
        target_args = int(COMPRESSION_CONFIG["target_sub_arguments"])
        target_evidence = int(COMPRESSION_CONFIG["target_evidence_points"])
        arg_score = len(sub_arguments) / target_args
        evidence_score = len(evidence) / target_evidence

        return float(min(1.0, (arg_score * 0.4 + evidence_score * 0.6)))

    def _calculate_mece_score(
        self,
        sub_arguments: List[str],
        evidence: List[str],
    ) -> float:
        """
        Calculate MECE (Mutually Exclusive, Collectively Exhaustive) score.

        Checks for:
        - Low overlap between arguments (Mutually Exclusive)
        - Sufficient coverage (Collectively Exhaustive)
        """
        if not sub_arguments:
            return 0.0

        # Check mutual exclusivity (low similarity between arguments)
        total_similarity = 0.0
        comparisons = 0

        for i, arg1 in enumerate(sub_arguments):
            for arg2 in sub_arguments[i + 1:]:
                similarity = self._analyzer.calculate_similarity(arg1, arg2)
                total_similarity += similarity
                comparisons += 1

        me_score = 1.0 - (total_similarity / comparisons) if comparisons > 0 else 1.0

        # Check collective exhaustiveness (coverage based on argument/evidence count)
        ce_score = min(1.0, (len(sub_arguments) + len(evidence)) / 6)

        return (me_score * 0.5 + ce_score * 0.5)


# =============================================================================
# DUPLICATE SIGNAL FILTER
# =============================================================================


class DuplicateSignalFilter:
    """
    Filters duplicate signals across sections.

    Ensures no redundant insights in the compressed output.
    """

    def __init__(self) -> None:
        self._analyzer = TextAnalyzer()
        self._seen_insights: List[str] = []
        self._threshold = COMPRESSION_CONFIG["deduplication_threshold"]

    def reset(self) -> None:
        """Reset the filter state."""
        self._seen_insights = []

    def is_duplicate(self, insight: str) -> bool:
        """Check if insight is a duplicate."""
        for seen in self._seen_insights:
            if self._analyzer.calculate_similarity(insight, seen) >= self._threshold:
                return True
        return False

    def register(self, insight: str) -> None:
        """Register a new insight."""
        self._seen_insights.append(insight)

    def filter_pyramids(
        self,
        pyramids: List[SectionPyramid],
    ) -> List[SectionPyramid]:
        """
        Filter duplicate pyramids.

        Args:
            pyramids: List of section pyramids

        Returns:
            Filtered list with duplicates removed
        """
        self.reset()
        filtered: List[SectionPyramid] = []

        for pyramid in pyramids:
            top_line = pyramid["top_line"]

            if not self.is_duplicate(top_line):
                self.register(top_line)
                filtered.append(pyramid)
            else:
                log.debug(
                    "[N4.1-Compression] Filtered duplicate insight: %s",
                    top_line[:50],
                )

        return filtered


# =============================================================================
# TONE HARMONIZER
# =============================================================================


class ToneHarmonizer:
    """
    Harmonizes tone across compressed insights.

    Ensures consistent executive-level language.
    """

    TONE_REPLACEMENTS: Dict[str, str] = {
        "man sollte": "es empfiehlt sich",
        "man könnte": "es bietet sich an",
        "vielleicht": "möglicherweise",
        "irgendwie": "",
        "eigentlich": "",
        "quasi": "",
        "sozusagen": "",
        "echt": "",
        "total": "",
        "mega": "erheblich",
        "super": "hervorragend",
    }

    EXECUTIVE_PATTERNS: List[Tuple[str, str]] = [
        (r"\bkann\s+man\b", "lässt sich"),
        (r"\bsollte\s+man\b", "empfiehlt sich"),
        (r"\bwir\s+denken\b", "die Analyse zeigt"),
        (r"\bich\s+glaube\b", "die Evidenz deutet darauf hin"),
        (r"\bwahrscheinlich\b", "mit hoher Wahrscheinlichkeit"),
    ]

    def harmonize(self, text: str) -> str:
        """
        Harmonize text tone.

        Args:
            text: Input text

        Returns:
            Harmonized text
        """
        result = text

        # Apply word replacements
        for informal, formal in self.TONE_REPLACEMENTS.items():
            result = result.replace(informal, formal)

        # Apply pattern replacements
        for pattern, replacement in self.EXECUTIVE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Clean up whitespace
        result = re.sub(r"\s+", " ", result).strip()

        return result

    def harmonize_pyramid(self, pyramid: SectionPyramid) -> SectionPyramid:
        """
        Harmonize tone in a pyramid structure.

        Args:
            pyramid: Section pyramid

        Returns:
            Harmonized pyramid
        """
        return SectionPyramid(
            section_id=pyramid["section_id"],
            top_line=self.harmonize(pyramid["top_line"]),
            sub_arguments=[self.harmonize(arg) for arg in pyramid["sub_arguments"]],
            evidence_items=[self.harmonize(ev) for ev in pyramid["evidence_items"]],
            compressed_insight=CompressedInsight(
                key_insight=self.harmonize(pyramid["compressed_insight"]["key_insight"]),
                evidence_points=[
                    self.harmonize(ep)
                    for ep in pyramid["compressed_insight"]["evidence_points"]
                ],
                leadership_action=self.harmonize(
                    pyramid["compressed_insight"]["leadership_action"],
                ),
                insight_type=pyramid["compressed_insight"]["insight_type"],
                confidence=pyramid["compressed_insight"]["confidence"],
            ),
            mece_score=pyramid["mece_score"],
        )


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================


class InsightCompressionEngine:
    """
    Main engine for insight compression.

    Orchestrates:
    - Pyramid structure building
    - MECE validation
    - Duplicate filtering
    - Tone harmonization
    """

    def __init__(self) -> None:
        self._pyramid_builder = PyramidStructureBuilder()
        self._duplicate_filter = DuplicateSignalFilter()
        self._tone_harmonizer = ToneHarmonizer()
        self._analyzer = TextAnalyzer()

    def compress_sections(
        self,
        sections: List[Dict[str, Any]],
    ) -> CompressionResult:
        """
        Compress all sections into pyramid structures.

        Args:
            sections: List of section dicts with id and content

        Returns:
            CompressionResult with all pyramids
        """
        log.info(
            "[N4.1-Compression] Compressing %d sections...",
            len(sections),
        )

        # Build pyramids for all sections
        pyramids: List[SectionPyramid] = []
        original_word_count = 0
        compressed_word_count = 0

        for section in sections:
            section_id = section.get("id", f"section_{len(pyramids)}")
            content = section.get("content", section.get("text", ""))

            if not content:
                continue

            original_word_count += self._analyzer.count_words(content)

            pyramid = self._pyramid_builder.build_pyramid(section_id, content)
            pyramids.append(pyramid)

            # Count compressed words
            compressed_word_count += self._count_pyramid_words(pyramid)

        # Filter duplicates
        filtered_pyramids = self._duplicate_filter.filter_pyramids(pyramids)

        # Harmonize tone
        harmonized_pyramids = [
            self._tone_harmonizer.harmonize_pyramid(p)
            for p in filtered_pyramids
        ]

        # Calculate metrics
        compression_ratio = (
            compressed_word_count / original_word_count
            if original_word_count > 0 else 0
        )

        quality_score = self._calculate_quality_score(harmonized_pyramids)

        log.info(
            "[N4.1-Compression] Compression complete: %d pyramids, "
            "%.1f%% ratio, %.2f quality score",
            len(harmonized_pyramids),
            compression_ratio * 100,
            quality_score,
        )

        return CompressionResult(
            total_sections=len(sections),
            compression_ratio=compression_ratio,
            pyramids=harmonized_pyramids,
            quality_score=quality_score,
        )

    def compress_single_section(
        self,
        section_id: str,
        content: str,
    ) -> SectionPyramid:
        """
        Compress a single section.

        Args:
            section_id: Section identifier
            content: Section content

        Returns:
            SectionPyramid structure
        """
        pyramid = self._pyramid_builder.build_pyramid(section_id, content)
        return self._tone_harmonizer.harmonize_pyramid(pyramid)

    def get_key_insights(
        self,
        sections: List[Dict[str, Any]],
    ) -> List[CompressedInsight]:
        """
        Get just the key insights from all sections.

        Args:
            sections: List of section dicts

        Returns:
            List of CompressedInsight structures
        """
        result = self.compress_sections(sections)
        return [p["compressed_insight"] for p in result["pyramids"]]

    def validate_mece(
        self,
        pyramids: List[SectionPyramid],
    ) -> Dict[str, Any]:
        """
        Validate MECE compliance across pyramids.

        Args:
            pyramids: List of section pyramids

        Returns:
            Validation result with scores and issues
        """
        issues: List[str] = []
        total_score = 0.0

        for pyramid in pyramids:
            score = pyramid["mece_score"]
            total_score += score

            if score < COMPRESSION_CONFIG["min_mece_score"]:
                issues.append(
                    f"Section {pyramid['section_id']}: MECE score {score:.2f} "
                    f"below threshold {COMPRESSION_CONFIG['min_mece_score']}",
                )

        avg_score = total_score / len(pyramids) if pyramids else 0

        return {
            "is_valid": len(issues) == 0,
            "average_mece_score": avg_score,
            "issues": issues,
            "total_sections": len(pyramids),
            "sections_below_threshold": len(issues),
        }

    def _count_pyramid_words(self, pyramid: SectionPyramid) -> int:
        """Count total words in a pyramid."""
        count = self._analyzer.count_words(pyramid["top_line"])

        for arg in pyramid["sub_arguments"]:
            count += self._analyzer.count_words(arg)

        for ev in pyramid["evidence_items"]:
            count += self._analyzer.count_words(ev)

        return count

    def _calculate_quality_score(
        self,
        pyramids: List[SectionPyramid],
    ) -> float:
        """Calculate overall quality score."""
        if not pyramids:
            return 0.0

        # Average MECE score
        mece_avg = sum(p["mece_score"] for p in pyramids) / len(pyramids)

        # Average confidence
        confidence_avg = sum(
            p["compressed_insight"]["confidence"] for p in pyramids
        ) / len(pyramids)

        # Completeness (all sections have required elements)
        complete_count = sum(
            1 for p in pyramids
            if len(p["sub_arguments"]) >= 2 and len(p["evidence_items"]) >= 2
        )
        completeness = complete_count / len(pyramids)

        return (mece_avg * 0.4 + confidence_avg * 0.3 + completeness * 0.3)


# =============================================================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =============================================================================


_engine_instance: Optional[InsightCompressionEngine] = None


def get_compression_engine() -> InsightCompressionEngine:
    """Get or create the singleton engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = InsightCompressionEngine()
    return _engine_instance


def compress_to_pyramid(
    sections: List[Dict[str, Any]],
) -> CompressionResult:
    """
    Compress sections to pyramid structure.

    Convenience function for external use.

    Args:
        sections: List of section dicts

    Returns:
        CompressionResult with all pyramids
    """
    engine = get_compression_engine()
    return engine.compress_sections(sections)


def get_key_insight(
    section_id: str,
    content: str,
) -> CompressedInsight:
    """
    Get key insight for a single section.

    Convenience function for external use.

    Args:
        section_id: Section identifier
        content: Section content

    Returns:
        CompressedInsight structure
    """
    engine = get_compression_engine()
    pyramid = engine.compress_single_section(section_id, content)
    return pyramid["compressed_insight"]


def validate_mece_compliance(
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate MECE compliance.

    Convenience function for external use.

    Args:
        sections: List of section dicts

    Returns:
        Validation result
    """
    engine = get_compression_engine()
    result = engine.compress_sections(sections)
    return engine.validate_mece(result["pyramids"])
