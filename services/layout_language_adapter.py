# -*- coding: utf-8 -*-
"""
N4.2: Layout Language Adapter v4
================================

PLATIN+++ v5.2 - Multi-Language Intelligence Layer

Language-specific layout adjustments for PDF generation:
- Hyphenation rules per language
- Dynamic table widths for longer Romance language terms
- Orphan line prevention
- Consistent card layout heights across languages
- Page break optimization per language

Supported Languages: DE, EN, FR, IT, ES

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
Author: Claude + Wolf
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from services.types import SectionDict, BriefingDict, EngineReport
from services.language_strategy_engine import SupportedLanguage

log = logging.getLogger(__name__)

__all__ = [
    "LayoutElement",
    "PageBreakRule",
    "HyphenationMode",
    "LayoutIssue",
    "LayoutAdaptation",
    "LayoutLanguageAdapter",
    "adapt_layout_for_language",
    "calculate_text_expansion",
    "apply_hyphenation",
    "optimize_page_breaks",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class LayoutElement(Enum):
    """Types of layout elements."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    TABLE_CELL = "table_cell"
    CARD = "card"
    LIST = "list"
    KPI_BOX = "kpi_box"
    ROADMAP_ITEM = "roadmap_item"
    QUOTE = "quote"
    CALLOUT = "callout"


class PageBreakRule(Enum):
    """Page break rules for elements."""
    ALWAYS_BEFORE = "always_before"
    NEVER_BREAK = "never_break"
    PREFER_BEFORE = "prefer_before"
    ALLOW_BREAK = "allow_break"
    KEEP_WITH_NEXT = "keep_with_next"
    AVOID_ORPHAN = "avoid_orphan"


class HyphenationMode(Enum):
    """Hyphenation modes per language."""
    NONE = "none"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class CardLayout(Enum):
    """Card layout modes."""
    FIXED_HEIGHT = "fixed_height"
    CONTENT_FIT = "content_fit"
    BALANCED = "balanced"


class IssueSeverity(Enum):
    """Issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Text expansion factors per language (relative to German baseline)
# Romance languages typically expand 10-25% from German
TEXT_EXPANSION_FACTORS: Dict[SupportedLanguage, float] = {
    SupportedLanguage.DE: 1.00,  # Baseline
    SupportedLanguage.EN: 0.95,  # English is typically shorter
    SupportedLanguage.FR: 1.20,  # French expands ~20%
    SupportedLanguage.IT: 1.15,  # Italian expands ~15%
    SupportedLanguage.ES: 1.18,  # Spanish expands ~18%
}

# Hyphenation rules per language
HYPHENATION_RULES: Dict[SupportedLanguage, Dict[str, Any]] = {
    SupportedLanguage.DE: {
        "mode": HyphenationMode.MODERATE,
        "min_prefix": 3,  # Minimum characters before hyphen
        "min_suffix": 3,  # Minimum characters after hyphen
        "min_word_length": 6,  # Minimum word length to hyphenate
        "compound_aware": True,  # German compound word handling
        "exceptions": {"keine", "nicht", "sowie", "durch"},
    },
    SupportedLanguage.EN: {
        "mode": HyphenationMode.CONSERVATIVE,
        "min_prefix": 2,
        "min_suffix": 3,
        "min_word_length": 5,
        "compound_aware": False,
        "exceptions": {"the", "and", "but", "for", "with"},
    },
    SupportedLanguage.FR: {
        "mode": HyphenationMode.AGGRESSIVE,
        "min_prefix": 2,
        "min_suffix": 2,
        "min_word_length": 5,
        "compound_aware": False,
        "exceptions": {"que", "qui", "les", "des", "aux"},
    },
    SupportedLanguage.IT: {
        "mode": HyphenationMode.MODERATE,
        "min_prefix": 2,
        "min_suffix": 2,
        "min_word_length": 5,
        "compound_aware": False,
        "exceptions": {"che", "chi", "gli", "per", "con"},
    },
    SupportedLanguage.ES: {
        "mode": HyphenationMode.MODERATE,
        "min_prefix": 2,
        "min_suffix": 2,
        "min_word_length": 5,
        "compound_aware": False,
        "exceptions": {"que", "con", "por", "para", "los"},
    },
}

# Table column width adjustments per language
TABLE_WIDTH_ADJUSTMENTS: Dict[SupportedLanguage, Dict[str, float]] = {
    SupportedLanguage.DE: {
        "name_column": 1.0,
        "description_column": 1.0,
        "value_column": 1.0,
        "action_column": 1.0,
    },
    SupportedLanguage.EN: {
        "name_column": 0.95,
        "description_column": 0.95,
        "value_column": 1.0,
        "action_column": 0.95,
    },
    SupportedLanguage.FR: {
        "name_column": 1.15,
        "description_column": 1.20,
        "value_column": 1.0,
        "action_column": 1.15,
    },
    SupportedLanguage.IT: {
        "name_column": 1.10,
        "description_column": 1.15,
        "value_column": 1.0,
        "action_column": 1.10,
    },
    SupportedLanguage.ES: {
        "name_column": 1.12,
        "description_column": 1.18,
        "value_column": 1.0,
        "action_column": 1.12,
    },
}

# Card height minimums per language (in approximate line counts)
CARD_HEIGHT_MINIMUMS: Dict[SupportedLanguage, int] = {
    SupportedLanguage.DE: 3,
    SupportedLanguage.EN: 3,
    SupportedLanguage.FR: 4,  # More lines needed for longer text
    SupportedLanguage.IT: 4,
    SupportedLanguage.ES: 4,
}

# Page break preferences per section type and language
PAGE_BREAK_RULES: Dict[str, Dict[SupportedLanguage, PageBreakRule]] = {
    "executive_summary": {
        SupportedLanguage.DE: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.EN: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.FR: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.IT: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.ES: PageBreakRule.ALWAYS_BEFORE,
    },
    "roadmap_90d": {
        SupportedLanguage.DE: PageBreakRule.PREFER_BEFORE,
        SupportedLanguage.EN: PageBreakRule.PREFER_BEFORE,
        SupportedLanguage.FR: PageBreakRule.ALWAYS_BEFORE,  # Longer in French
        SupportedLanguage.IT: PageBreakRule.PREFER_BEFORE,
        SupportedLanguage.ES: PageBreakRule.PREFER_BEFORE,
    },
    "roadmap_12m": {
        SupportedLanguage.DE: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.EN: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.FR: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.IT: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.ES: PageBreakRule.ALWAYS_BEFORE,
    },
    "recommendations": {
        SupportedLanguage.DE: PageBreakRule.PREFER_BEFORE,
        SupportedLanguage.EN: PageBreakRule.PREFER_BEFORE,
        SupportedLanguage.FR: PageBreakRule.ALWAYS_BEFORE,
        SupportedLanguage.IT: PageBreakRule.PREFER_BEFORE,
        SupportedLanguage.ES: PageBreakRule.PREFER_BEFORE,
    },
    "ki_stack_summary": {
        SupportedLanguage.DE: PageBreakRule.NEVER_BREAK,
        SupportedLanguage.EN: PageBreakRule.NEVER_BREAK,
        SupportedLanguage.FR: PageBreakRule.ALLOW_BREAK,
        SupportedLanguage.IT: PageBreakRule.NEVER_BREAK,
        SupportedLanguage.ES: PageBreakRule.NEVER_BREAK,
    },
}

# Orphan prevention settings
ORPHAN_SETTINGS: Dict[SupportedLanguage, Dict[str, int]] = {
    SupportedLanguage.DE: {
        "min_lines_before_break": 2,
        "min_lines_after_break": 2,
        "widow_threshold": 3,
    },
    SupportedLanguage.EN: {
        "min_lines_before_break": 2,
        "min_lines_after_break": 2,
        "widow_threshold": 3,
    },
    SupportedLanguage.FR: {
        "min_lines_before_break": 3,  # French needs more context
        "min_lines_after_break": 2,
        "widow_threshold": 4,
    },
    SupportedLanguage.IT: {
        "min_lines_before_break": 2,
        "min_lines_after_break": 2,
        "widow_threshold": 3,
    },
    SupportedLanguage.ES: {
        "min_lines_before_break": 2,
        "min_lines_after_break": 2,
        "widow_threshold": 3,
    },
}

# Long word threshold (characters) for reduction strategies
LONG_WORD_THRESHOLDS: Dict[SupportedLanguage, int] = {
    SupportedLanguage.DE: 25,  # German compound words can be very long
    SupportedLanguage.EN: 18,
    SupportedLanguage.FR: 20,
    SupportedLanguage.IT: 18,
    SupportedLanguage.ES: 18,
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class LayoutIssue:
    """Single layout issue."""

    issue_id: str
    severity: IssueSeverity
    element_type: LayoutElement
    section: str
    message: str
    suggestion: str = ""
    auto_fixed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_id": self.issue_id,
            "severity": self.severity.value,
            "element_type": self.element_type.value,
            "section": self.section,
            "message": self.message,
            "suggestion": self.suggestion,
            "auto_fixed": self.auto_fixed,
        }


@dataclass
class LayoutAdaptation:
    """Record of a layout adaptation applied."""

    adaptation_type: str
    section: str
    element: LayoutElement
    original_value: Any
    adapted_value: Any
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "adaptation_type": self.adaptation_type,
            "section": self.section,
            "element": self.element.value,
            "original_value": str(self.original_value),
            "adapted_value": str(self.adapted_value),
            "reason": self.reason,
        }


@dataclass
class LayoutAnalysisResult:
    """Result of layout analysis for a section."""

    section: str
    language: SupportedLanguage
    estimated_lines: int
    estimated_pages: float
    long_words_count: int
    orphan_risk: bool
    table_overflow_risk: bool
    card_height_issues: int
    recommended_breaks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "section": self.section,
            "language": self.language.value,
            "estimated_lines": self.estimated_lines,
            "estimated_pages": round(self.estimated_pages, 2),
            "long_words_count": self.long_words_count,
            "orphan_risk": self.orphan_risk,
            "table_overflow_risk": self.table_overflow_risk,
            "card_height_issues": self.card_height_issues,
            "recommended_breaks": self.recommended_breaks,
        }


@dataclass
class LayoutAdapterReport:
    """Complete layout adapter report."""

    engine_id: str = "LAYOUT_ADAPTER_V4"
    success: bool = True
    language: Optional[str] = None
    sections_analyzed: int = 0
    sections_adapted: int = 0
    adaptations_applied: int = 0
    issues_found: int = 0
    issues_fixed: int = 0
    page_breaks_optimized: int = 0
    hyphenations_applied: int = 0
    issues: List[LayoutIssue] = field(default_factory=list)
    adaptations: List[LayoutAdaptation] = field(default_factory=list)
    section_analyses: Dict[str, LayoutAnalysisResult] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_issue(self, issue: LayoutIssue) -> None:
        """Add an issue."""
        self.issues.append(issue)
        self.issues_found += 1
        if issue.auto_fixed:
            self.issues_fixed += 1

    def add_adaptation(self, adaptation: LayoutAdaptation) -> None:
        """Add an adaptation."""
        self.adaptations.append(adaptation)
        self.adaptations_applied += 1

    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "language": self.language,
            "sections_analyzed": self.sections_analyzed,
            "sections_adapted": self.sections_adapted,
            "adaptations_applied": self.adaptations_applied,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "page_breaks_optimized": self.page_breaks_optimized,
            "hyphenations_applied": self.hyphenations_applied,
            "issues": [i.to_dict() for i in self.issues],
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# LAYOUT LANGUAGE ADAPTER
# =============================================================================

class LayoutLanguageAdapter:
    """
    N4.2: Language-Aware Layout Adapter v4.

    Adapts layout for language-specific requirements:
    - Text expansion compensation
    - Hyphenation optimization
    - Table width adjustment
    - Card height balancing
    - Orphan/widow prevention
    - Page break optimization
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        language: str = "de",
    ) -> None:
        """
        Initialize Layout Language Adapter.

        Args:
            sections: Section dictionary to adapt
            briefing: Briefing data for context
            language: Target language code
        """
        self.sections = sections
        self.briefing = briefing

        try:
            self._language = SupportedLanguage(language.lower())
        except ValueError:
            self._language = SupportedLanguage.DE

        self._report = LayoutAdapterReport(language=self._language.value)
        self._expansion_factor = TEXT_EXPANSION_FACTORS.get(
            self._language, 1.0
        )
        self._hyphenation_rules = HYPHENATION_RULES.get(
            self._language, HYPHENATION_RULES[SupportedLanguage.DE]
        )

        log.info(
            "[N4.2-Layout] Adapter initialized for %s (expansion: %.2f)",
            self._language.value,
            self._expansion_factor,
        )

    def process(self) -> Tuple[SectionDict, LayoutAdapterReport]:
        """
        Process all sections with layout adaptations.

        Returns:
            Tuple of (adapted_sections, report)
        """
        log.info("[N4.2-Layout] Processing started for %s", self._language.value)

        adapted_sections: SectionDict = {}

        for section_key, section_content in self.sections.items():
            # Skip internal keys
            if section_key.startswith("_"):
                adapted_sections[section_key] = section_content
                continue

            # Skip non-string content
            if not isinstance(section_content, str):
                adapted_sections[section_key] = section_content
                continue

            # Analyze section
            analysis = self._analyze_section(section_key, section_content)
            self._report.section_analyses[section_key] = analysis
            self._report.sections_analyzed += 1

            # Apply adaptations
            adapted_content = self._adapt_section(section_key, section_content, analysis)

            if adapted_content != section_content:
                self._report.sections_adapted += 1

            adapted_sections[section_key] = adapted_content

        # Store metadata
        adapted_sections["_layout_report"] = self._report.to_dict()
        adapted_sections["_layout_language"] = self._language.value

        log.info(
            "[N4.2-Layout] Complete: %d analyzed, %d adapted, %d issues",
            self._report.sections_analyzed,
            self._report.sections_adapted,
            self._report.issues_found,
        )

        return adapted_sections, self._report

    def _analyze_section(
        self,
        section_key: str,
        content: str,
    ) -> LayoutAnalysisResult:
        """
        Analyze a section for layout issues.

        Args:
            section_key: Section identifier
            content: Section content

        Returns:
            LayoutAnalysisResult
        """
        # Estimate line count (rough: ~80 chars per line)
        char_count = len(content)
        adjusted_chars = int(char_count * self._expansion_factor)
        estimated_lines = adjusted_chars // 80

        # Estimate page count (~50 lines per page)
        estimated_pages = estimated_lines / 50

        # Count long words
        words = content.split()
        long_word_threshold = LONG_WORD_THRESHOLDS.get(self._language, 20)
        long_words = [w for w in words if len(w) > long_word_threshold]

        # Check orphan risk
        orphan_settings = ORPHAN_SETTINGS.get(
            self._language, ORPHAN_SETTINGS[SupportedLanguage.DE]
        )
        paragraphs = content.split("\n\n")
        orphan_risk = any(
            len(p.split("\n")) < orphan_settings["min_lines_before_break"]
            for p in paragraphs
        )

        # Check table overflow risk
        table_overflow = self._check_table_overflow(content)

        # Check card height issues
        card_issues = self._count_card_height_issues(content)

        # Get recommended breaks
        recommended_breaks = self._get_recommended_breaks(section_key)

        return LayoutAnalysisResult(
            section=section_key,
            language=self._language,
            estimated_lines=estimated_lines,
            estimated_pages=estimated_pages,
            long_words_count=len(long_words),
            orphan_risk=orphan_risk,
            table_overflow_risk=table_overflow,
            card_height_issues=card_issues,
            recommended_breaks=recommended_breaks,
        )

    def _adapt_section(
        self,
        section_key: str,
        content: str,
        analysis: LayoutAnalysisResult,
    ) -> str:
        """
        Apply adaptations to a section.

        Args:
            section_key: Section identifier
            content: Section content
            analysis: Analysis result

        Returns:
            Adapted content
        """
        adapted = content

        # Apply hyphenation hints for long words
        if analysis.long_words_count > 0:
            adapted = self._apply_hyphenation_hints(section_key, adapted)

        # Apply table width adjustments
        if "<table" in adapted.lower():
            adapted = self._adapt_table_widths(section_key, adapted)

        # Apply card height balancing
        if "card" in adapted.lower():
            adapted = self._balance_card_heights(section_key, adapted)

        # Apply orphan prevention
        if analysis.orphan_risk:
            adapted = self._prevent_orphans(section_key, adapted)

        # Apply page break hints
        if analysis.recommended_breaks:
            adapted = self._apply_page_break_hints(section_key, adapted, analysis)

        return adapted

    def _apply_hyphenation_hints(
        self,
        section_key: str,
        content: str,
    ) -> str:
        """Apply hyphenation hints to long words."""
        rules = self._hyphenation_rules
        mode = rules.get("mode", HyphenationMode.CONSERVATIVE)
        min_word_length = rules.get("min_word_length", 6)
        exceptions = rules.get("exceptions", set())

        if mode == HyphenationMode.NONE:
            return content

        words = re.findall(r"\b\w+\b", content)
        hyphenation_count = 0

        for word in words:
            if len(word) < min_word_length:
                continue

            if word.lower() in exceptions:
                continue

            # Add soft hyphen hints for long words
            hyphenated = self._hyphenate_word(word, rules)
            if hyphenated != word:
                content = content.replace(word, hyphenated, 1)
                hyphenation_count += 1

        if hyphenation_count > 0:
            self._report.hyphenations_applied += hyphenation_count
            self._report.add_adaptation(LayoutAdaptation(
                adaptation_type="hyphenation",
                section=section_key,
                element=LayoutElement.PARAGRAPH,
                original_value=f"{hyphenation_count} words",
                adapted_value="hyphenation hints added",
                reason=f"Language {self._language.value} requires hyphenation",
            ))

        return content

    def _hyphenate_word(
        self,
        word: str,
        rules: Dict[str, Any],
    ) -> str:
        """
        Add soft hyphen hints to a word.

        This is a simplified implementation - actual hyphenation
        would use language-specific dictionaries.
        """
        min_prefix = rules.get("min_prefix", 2)
        min_suffix = rules.get("min_suffix", 2)

        if len(word) < min_prefix + min_suffix + 2:
            return word

        # Simple syllable-based hyphenation for demonstration
        # Real implementation would use pyphen or similar
        vowels = "aeiouäöüàèéêëîïôûùAEIOUÄÖÜÀÈÉÊËÎÏÔÛÙ"

        # Find potential break points (between consonant clusters)
        result = []
        i = 0

        while i < len(word):
            result.append(word[i])

            # Check for hyphenation opportunity after vowel + consonant
            if (
                i >= min_prefix - 1 and
                i < len(word) - min_suffix and
                word[i] in vowels and
                i + 1 < len(word) and
                word[i + 1] not in vowels
            ):
                # Add soft hyphen (&#173; or \u00AD)
                result.append("\u00AD")

            i += 1

        return "".join(result)

    def _adapt_table_widths(
        self,
        section_key: str,
        content: str,
    ) -> str:
        """Adapt table column widths for language."""
        adjustments = TABLE_WIDTH_ADJUSTMENTS.get(
            self._language, TABLE_WIDTH_ADJUSTMENTS[SupportedLanguage.DE]
        )

        # Check if any adjustment is needed
        if all(v == 1.0 for v in adjustments.values()):
            return content

        # Add CSS class hints for table width adjustment
        if "<table" in content and "lang-adjusted" not in content:
            content = content.replace(
                "<table",
                f'<table class="lang-adjusted lang-{self._language.value}"',
                1,
            )

            self._report.add_adaptation(LayoutAdaptation(
                adaptation_type="table_width",
                section=section_key,
                element=LayoutElement.TABLE,
                original_value="standard",
                adapted_value=f"lang-{self._language.value}",
                reason=f"Text expansion factor {self._expansion_factor:.2f}",
            ))

        return content

    def _balance_card_heights(
        self,
        section_key: str,
        content: str,
    ) -> str:
        """Balance card heights for consistent layout."""
        min_height = CARD_HEIGHT_MINIMUMS.get(self._language, 3)

        # Add minimum height class hint
        if "card" in content.lower() and "min-height-adjusted" not in content:
            # Add CSS class for minimum height
            content = re.sub(
                r'class="([^"]*card[^"]*)"',
                f'class="\\1 min-height-{min_height}"',
                content,
            )

            self._report.add_adaptation(LayoutAdaptation(
                adaptation_type="card_height",
                section=section_key,
                element=LayoutElement.CARD,
                original_value="auto",
                adapted_value=f"min-height-{min_height}",
                reason=f"Language {self._language.value} requires minimum {min_height} lines",
            ))

        return content

    def _prevent_orphans(
        self,
        section_key: str,
        content: str,
    ) -> str:
        """Add orphan prevention hints."""
        settings = ORPHAN_SETTINGS.get(
            self._language, ORPHAN_SETTINGS[SupportedLanguage.DE]
        )

        # Add CSS class for orphan prevention
        if "orphan-protected" not in content:
            # Wrap short paragraphs in orphan-protected div
            min_lines = settings["min_lines_before_break"]

            # Add protection hint to content
            content = f'<div class="orphan-protected min-before-{min_lines}">{content}</div>'

            self._report.add_issue(LayoutIssue(
                issue_id=f"ORPHAN_{section_key}",
                severity=IssueSeverity.INFO,
                element_type=LayoutElement.PARAGRAPH,
                section=section_key,
                message="Orphan risk detected",
                suggestion=f"Minimum {min_lines} lines before break",
                auto_fixed=True,
            ))

        return content

    def _apply_page_break_hints(
        self,
        section_key: str,
        content: str,
        analysis: LayoutAnalysisResult,
    ) -> str:
        """Apply page break hints based on rules."""
        rule = PAGE_BREAK_RULES.get(section_key, {}).get(
            self._language, PageBreakRule.ALLOW_BREAK
        )

        if rule == PageBreakRule.ALWAYS_BEFORE:
            if "page-break-before" not in content:
                content = f'<div class="page-break-before">{content}</div>'
                self._report.page_breaks_optimized += 1
        elif rule == PageBreakRule.NEVER_BREAK:
            if "page-break-inside-avoid" not in content:
                content = f'<div class="page-break-inside-avoid">{content}</div>'
                self._report.page_breaks_optimized += 1
        elif rule == PageBreakRule.KEEP_WITH_NEXT:
            if "keep-with-next" not in content:
                content = f'<div class="keep-with-next">{content}</div>'
                self._report.page_breaks_optimized += 1

        return content

    def _check_table_overflow(self, content: str) -> bool:
        """Check if tables might overflow."""
        if "<table" not in content.lower():
            return False

        # Check for long cell content
        cell_pattern = r"<td[^>]*>([^<]+)</td>"
        cells = re.findall(cell_pattern, content, re.IGNORECASE)

        threshold = 50 * self._expansion_factor
        return any(len(cell) > threshold for cell in cells)

    def _count_card_height_issues(self, content: str) -> int:
        """Count cards with potential height issues."""
        if "card" not in content.lower():
            return 0

        # Simple heuristic: count cards with short content
        card_pattern = r'class="[^"]*card[^"]*"[^>]*>([^<]{0,50})<'
        short_cards = re.findall(card_pattern, content, re.IGNORECASE)

        return len(short_cards)

    def _get_recommended_breaks(self, section_key: str) -> List[str]:
        """Get recommended page breaks for section."""
        rules = PAGE_BREAK_RULES.get(section_key, {})
        rule = rules.get(self._language, PageBreakRule.ALLOW_BREAK)

        if rule in (PageBreakRule.ALWAYS_BEFORE, PageBreakRule.PREFER_BEFORE):
            return ["before_section"]
        return []


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def adapt_layout_for_language(
    sections: SectionDict,
    language: str,
    briefing: Optional[Dict[str, Any]] = None,
) -> Tuple[SectionDict, LayoutAdapterReport]:
    """
    Adapt layout for a specific language.

    Args:
        sections: Section dictionary
        language: Target language code
        briefing: Optional briefing data

    Returns:
        Tuple of (adapted_sections, report)
    """
    adapter = LayoutLanguageAdapter(
        sections=sections,
        briefing=briefing or {},
        language=language,
    )

    return adapter.process()


def calculate_text_expansion(
    text: str,
    source_language: str,
    target_language: str,
) -> Tuple[int, float]:
    """
    Calculate expected text expansion.

    Args:
        text: Original text
        source_language: Source language code
        target_language: Target language code

    Returns:
        Tuple of (expanded_char_count, expansion_factor)
    """
    try:
        src_lang = SupportedLanguage(source_language.lower())
        tgt_lang = SupportedLanguage(target_language.lower())
    except ValueError:
        return len(text), 1.0

    src_factor = TEXT_EXPANSION_FACTORS.get(src_lang, 1.0)
    tgt_factor = TEXT_EXPANSION_FACTORS.get(tgt_lang, 1.0)

    # Relative expansion
    relative_expansion = tgt_factor / src_factor

    original_length = len(text)
    expanded_length = int(original_length * relative_expansion)

    return expanded_length, relative_expansion


def apply_hyphenation(
    text: str,
    language: str,
) -> str:
    """
    Apply hyphenation to text.

    Args:
        text: Text to hyphenate
        language: Language code

    Returns:
        Text with soft hyphens
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        return text

    adapter = LayoutLanguageAdapter(
        sections={"temp": text},
        briefing={},
        language=language,
    )

    return adapter._apply_hyphenation_hints("temp", text)


def optimize_page_breaks(
    sections: SectionDict,
    language: str,
) -> Dict[str, PageBreakRule]:
    """
    Get optimized page break rules for sections.

    Args:
        sections: Section dictionary
        language: Language code

    Returns:
        Dict mapping section to recommended page break rule
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    result: Dict[str, PageBreakRule] = {}

    for section_key in sections:
        if section_key.startswith("_"):
            continue

        rules = PAGE_BREAK_RULES.get(section_key, {})
        rule = rules.get(lang, PageBreakRule.ALLOW_BREAK)
        result[section_key] = rule

    return result


def get_expansion_factor(language: str) -> float:
    """Get text expansion factor for a language."""
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        return 1.0

    return TEXT_EXPANSION_FACTORS.get(lang, 1.0)


def get_hyphenation_mode(language: str) -> HyphenationMode:
    """Get hyphenation mode for a language."""
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        return HyphenationMode.CONSERVATIVE

    rules = HYPHENATION_RULES.get(lang, HYPHENATION_RULES[SupportedLanguage.DE])
    mode = rules.get("mode", HyphenationMode.CONSERVATIVE)
    if isinstance(mode, HyphenationMode):
        return mode
    return HyphenationMode.CONSERVATIVE
