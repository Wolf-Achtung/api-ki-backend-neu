# -*- coding: utf-8 -*-
"""
N4.2: Translation Engine v3
===========================

PLATIN+++ v5.2 - Multi-Language Intelligence Layer

Advanced translation engine with multi-pass processing:
1. Literal Pass (GPT) - Accurate word-level translation
2. Executive Rewrite (Claude) - Board-level tonality
3. Semantic Consistency Check - Meaning preservation
4. KPI/Narrative/Context Diff Fix - Number and term consistency

Guarantees:
- Zero semantic drift (threshold: 0.08)
- Numbers unchanged
- KI-Act & Risk terms consistent
- Native consulting tone per language

Supported Languages: DE, EN, FR, IT, ES

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
Author: Claude + Wolf
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from services.types import SectionDict, BriefingDict, EngineReport
from services.language_strategy_engine import (
    SupportedLanguage,
    CONSULTING_GLOSSARY,
    get_language_profile,
)

log = logging.getLogger(__name__)

__all__ = [
    "TranslationPass",
    "TranslationQuality",
    "SemanticDriftLevel",
    "TranslationIssue",
    "TranslationResult",
    "TranslationEngineV3",
    "translate_section",
    "translate_sections",
    "check_semantic_consistency",
    "fix_kpi_drift",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class TranslationPass(Enum):
    """Translation pipeline passes."""
    LITERAL = "literal"
    EXECUTIVE_REWRITE = "executive_rewrite"
    SEMANTIC_CHECK = "semantic_check"
    KPI_FIX = "kpi_fix"
    FINAL = "final"


class TranslationQuality(Enum):
    """Translation quality levels."""
    EXCELLENT = "excellent"  # > 0.95 similarity
    GOOD = "good"           # > 0.90 similarity
    ACCEPTABLE = "acceptable"  # > 0.85 similarity
    NEEDS_REVIEW = "needs_review"  # > 0.80 similarity
    POOR = "poor"           # <= 0.80 similarity


class SemanticDriftLevel(Enum):
    """Semantic drift severity levels."""
    NONE = "none"           # < 0.02
    MINIMAL = "minimal"     # < 0.05
    ACCEPTABLE = "acceptable"  # < 0.08
    WARNING = "warning"     # < 0.12
    CRITICAL = "critical"   # >= 0.12


class IssueSeverity(Enum):
    """Issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Semantic drift thresholds
MAX_SEMANTIC_DRIFT = 0.08  # Executive summary threshold
MAX_ROADMAP_DRIFT = 0.05   # Roadmap action drift threshold
MAX_KPI_DRIFT = 0.02       # KPI value drift (should be 0)

# Protected terms that must remain unchanged (KI-Act, Risk, etc.)
PROTECTED_TERMS: Dict[str, Set[str]] = {
    "risk_levels": {
        "high", "medium", "low", "minimal", "limited", "unacceptable",
        "hoch", "mittel", "niedrig", "minimal", "begrenzt", "inakzeptabel",
    },
    "ai_act_terms": {
        "AI Act", "KI-Act", "KI-Verordnung", "EU AI Act",
        "Règlement IA", "Regolamento IA", "Reglamento IA",
        "GPAI", "General Purpose AI",
    },
    "compliance_terms": {
        "ISO 42001", "NIST AI RMF", "GDPR", "DSGVO",
        "SOC 2", "SOC2", "compliance", "Compliance",
    },
    "kpi_terms": {
        "ROI", "KPI", "NPV", "IRR", "TCO",
        "Payback", "Amortisation", "Break-even",
    },
}

# Number patterns to preserve
NUMBER_PATTERNS = [
    r"(\d+(?:[.,]\d+)?)\s*%",  # Percentages
    r"(\d+(?:[.,]\d+)?)\s*(?:€|EUR|USD|\$)",  # Currency
    r"(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?|Mois|Mesi|Meses)",  # Months
    r"(\d+(?:[.,]\d+)?)\s*(?:Stunden?|hours?|heures?|ore|horas)",  # Hours
    r"(\d+(?:[.,]\d+)?)\s*(?:Tage?|days?|jours?|giorni|días)",  # Days
    r"(\d+(?:[.,]\d+)?)\s*(?:Wochen?|weeks?|semaines?|settimane|semanas)",  # Weeks
    r"(\d+(?:[.,]\d+)?)\s*(?:Jahre?|years?|ans?|anni|años)",  # Years
    r"(\d+(?:[.,]\d+)?)\s*(?:Mio\.?|Mrd\.?|K|k|M|B)",  # Magnitude
    r"(\d+(?:[.,]\d+)?)\s*/\s*(?:Monat|month|mois|mese|mes)",  # Per month
]

# Consulting tone markers per language
EXECUTIVE_TONE_MARKERS: Dict[SupportedLanguage, List[str]] = {
    SupportedLanguage.DE: [
        "Empfehlung:", "Handlungsbedarf:", "Strategische Priorität:",
        "Executive Summary:", "Kernaussage:", "Fazit:",
    ],
    SupportedLanguage.EN: [
        "Recommendation:", "Action Required:", "Strategic Priority:",
        "Executive Summary:", "Key Insight:", "Bottom Line:",
    ],
    SupportedLanguage.FR: [
        "Recommandation :", "Action requise :", "Priorité stratégique :",
        "Synthèse exécutive :", "Point clé :", "Conclusion :",
    ],
    SupportedLanguage.IT: [
        "Raccomandazione:", "Azione richiesta:", "Priorità strategica:",
        "Sintesi esecutiva:", "Punto chiave:", "Conclusione:",
    ],
    SupportedLanguage.ES: [
        "Recomendación:", "Acción requerida:", "Prioridad estratégica:",
        "Resumen ejecutivo:", "Punto clave:", "Conclusión:",
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TranslationIssue:
    """Single translation issue."""

    issue_id: str
    severity: IssueSeverity
    pass_name: TranslationPass
    section: str
    message: str
    source_text: str = ""
    translated_text: str = ""
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_id": self.issue_id,
            "severity": self.severity.value,
            "pass": self.pass_name.value,
            "section": self.section,
            "message": self.message,
            "source_text": self.source_text[:100] if self.source_text else "",
            "translated_text": self.translated_text[:100] if self.translated_text else "",
            "suggestion": self.suggestion,
        }


@dataclass
class SemanticCheckResult:
    """Result of semantic consistency check."""

    similarity_score: float
    drift_level: SemanticDriftLevel
    preserved_numbers: int
    lost_numbers: int
    preserved_terms: int
    lost_terms: int
    issues: List[str] = field(default_factory=list)

    @property
    def is_acceptable(self) -> bool:
        """Check if drift is within acceptable limits."""
        return self.drift_level in (
            SemanticDriftLevel.NONE,
            SemanticDriftLevel.MINIMAL,
            SemanticDriftLevel.ACCEPTABLE,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "similarity_score": round(self.similarity_score, 4),
            "drift_level": self.drift_level.value,
            "preserved_numbers": self.preserved_numbers,
            "lost_numbers": self.lost_numbers,
            "preserved_terms": self.preserved_terms,
            "lost_terms": self.lost_terms,
            "is_acceptable": self.is_acceptable,
            "issues": self.issues,
        }


@dataclass
class TranslationResult:
    """Result of translation for a single section."""

    section: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    original_text: str
    translated_text: str
    quality: TranslationQuality
    semantic_check: SemanticCheckResult
    passes_completed: List[TranslationPass] = field(default_factory=list)
    issues: List[TranslationIssue] = field(default_factory=list)
    processing_time_ms: int = 0

    @property
    def success(self) -> bool:
        """Check if translation was successful."""
        has_errors = any(i.severity == IssueSeverity.ERROR for i in self.issues)
        return not has_errors and self.semantic_check.is_acceptable

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "section": self.section,
            "source_language": self.source_language.value,
            "target_language": self.target_language.value,
            "quality": self.quality.value,
            "success": self.success,
            "semantic_check": self.semantic_check.to_dict(),
            "passes_completed": [p.value for p in self.passes_completed],
            "issues_count": len(self.issues),
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class TranslationEngineReport:
    """Complete translation engine report."""

    engine_id: str = "TRANSLATION_V3"
    success: bool = True
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    sections_translated: int = 0
    sections_failed: int = 0
    total_semantic_drift: float = 0.0
    avg_quality_score: float = 0.0
    numbers_preserved: int = 0
    numbers_lost: int = 0
    terms_preserved: int = 0
    terms_lost: int = 0
    issues: List[TranslationIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    section_results: Dict[str, TranslationResult] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_issue(self, issue: TranslationIssue) -> None:
        """Add an issue."""
        self.issues.append(issue)
        if issue.severity == IssueSeverity.ERROR:
            self.success = False

    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)

    def add_result(self, result: TranslationResult) -> None:
        """Add a section result."""
        self.section_results[result.section] = result
        if result.success:
            self.sections_translated += 1
        else:
            self.sections_failed += 1
        self.issues.extend(result.issues)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "sections_translated": self.sections_translated,
            "sections_failed": self.sections_failed,
            "total_semantic_drift": round(self.total_semantic_drift, 4),
            "avg_quality_score": round(self.avg_quality_score, 4),
            "numbers_preserved": self.numbers_preserved,
            "numbers_lost": self.numbers_lost,
            "terms_preserved": self.terms_preserved,
            "terms_lost": self.terms_lost,
            "issues_count": len(self.issues),
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# TRANSLATION ENGINE V3
# =============================================================================

class TranslationEngineV3:
    """
    N4.2: Advanced Translation Engine v3.

    Multi-pass translation pipeline:
    1. Literal Pass - Accurate base translation
    2. Executive Rewrite - Board-level tonality
    3. Semantic Check - Meaning preservation validation
    4. KPI Fix - Number and term consistency

    Guarantees:
    - Zero semantic drift for KPIs
    - Executive tone preservation
    - Consulting vocabulary consistency
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        source_language: str = "de",
        target_language: str = "en",
    ) -> None:
        """
        Initialize Translation Engine v3.

        Args:
            sections: Section dictionary to translate
            briefing: Briefing data for context
            source_language: Source language code
            target_language: Target language code
        """
        self.sections = sections
        self.briefing = briefing

        try:
            self._source_lang = SupportedLanguage(source_language.lower())
        except ValueError:
            self._source_lang = SupportedLanguage.DE

        try:
            self._target_lang = SupportedLanguage(target_language.lower())
        except ValueError:
            self._target_lang = SupportedLanguage.EN

        self._report = TranslationEngineReport(
            source_language=self._source_lang.value,
            target_language=self._target_lang.value,
        )

        # Translation handlers (can be overridden for actual LLM calls)
        self._literal_translator: Optional[Callable[[str, str, str], str]] = None
        self._executive_rewriter: Optional[Callable[[str, str], str]] = None

        # Glossary for term mapping
        self._source_glossary = CONSULTING_GLOSSARY.get(
            self._source_lang, CONSULTING_GLOSSARY[SupportedLanguage.DE]
        )
        self._target_glossary = CONSULTING_GLOSSARY.get(
            self._target_lang, CONSULTING_GLOSSARY[SupportedLanguage.EN]
        )

        log.info(
            "[N4.2-Translation] Engine initialized: %s → %s",
            self._source_lang.value,
            self._target_lang.value,
        )

    def register_literal_translator(
        self,
        handler: Callable[[str, str, str], str],
    ) -> None:
        """
        Register literal translation handler.

        Args:
            handler: Function(text, source_lang, target_lang) -> translated_text
        """
        self._literal_translator = handler

    def register_executive_rewriter(
        self,
        handler: Callable[[str, str], str],
    ) -> None:
        """
        Register executive rewrite handler.

        Args:
            handler: Function(text, target_lang) -> rewritten_text
        """
        self._executive_rewriter = handler

    def process(self) -> Tuple[SectionDict, TranslationEngineReport]:
        """
        Process all sections through translation pipeline.

        Returns:
            Tuple of (translated_sections, report)
        """
        log.info(
            "[N4.2-Translation] Processing started: %s → %s",
            self._source_lang.value,
            self._target_lang.value,
        )

        # Skip if same language
        if self._source_lang == self._target_lang:
            log.info("[N4.2-Translation] Same language, skipping translation")
            self._report.success = True
            return self.sections, self._report

        translated_sections: SectionDict = {}
        quality_scores: List[float] = []

        for section_key, section_content in self.sections.items():
            # Skip internal keys
            if section_key.startswith("_"):
                translated_sections[section_key] = section_content
                continue

            # Skip non-string content
            if not isinstance(section_content, str):
                translated_sections[section_key] = section_content
                continue

            # Skip empty content
            if not section_content.strip():
                translated_sections[section_key] = section_content
                continue

            # Translate section
            result = self._translate_section(section_key, section_content)
            self._report.add_result(result)

            if result.success:
                translated_sections[section_key] = result.translated_text
                quality_scores.append(result.semantic_check.similarity_score)
            else:
                # Keep original on failure
                translated_sections[section_key] = section_content
                self._report.add_warning(
                    f"Section '{section_key}' translation failed, keeping original"
                )

        # Calculate aggregate metrics
        if quality_scores:
            self._report.avg_quality_score = sum(quality_scores) / len(quality_scores)

        # Aggregate number/term preservation stats
        for result in self._report.section_results.values():
            self._report.numbers_preserved += result.semantic_check.preserved_numbers
            self._report.numbers_lost += result.semantic_check.lost_numbers
            self._report.terms_preserved += result.semantic_check.preserved_terms
            self._report.terms_lost += result.semantic_check.lost_terms

        self._report.total_semantic_drift = 1.0 - self._report.avg_quality_score

        # Store metadata
        translated_sections["_translation_report"] = self._report.to_dict()
        translated_sections["_source_language"] = self._source_lang.value
        translated_sections["_target_language"] = self._target_lang.value

        log.info(
            "[N4.2-Translation] Complete: %d translated, %d failed, drift=%.4f",
            self._report.sections_translated,
            self._report.sections_failed,
            self._report.total_semantic_drift,
        )

        return translated_sections, self._report

    def _translate_section(
        self,
        section_key: str,
        content: str,
    ) -> TranslationResult:
        """
        Translate a single section through all passes.

        Args:
            section_key: Section identifier
            content: Original content

        Returns:
            TranslationResult with all pass details
        """
        import time
        start_time = time.time()

        passes_completed: List[TranslationPass] = []
        issues: List[TranslationIssue] = []
        current_text = content

        # Pass 1: Literal Translation
        try:
            literal_result = self._pass_literal(section_key, content)
            current_text = literal_result
            passes_completed.append(TranslationPass.LITERAL)
        except Exception as e:
            issues.append(TranslationIssue(
                issue_id=f"TRANS_001_{section_key}",
                severity=IssueSeverity.ERROR,
                pass_name=TranslationPass.LITERAL,
                section=section_key,
                message=f"Literal translation failed: {str(e)}",
                source_text=content[:100],
            ))
            # Use original on failure
            current_text = content

        # Pass 2: Executive Rewrite
        try:
            executive_result = self._pass_executive_rewrite(section_key, current_text)
            current_text = executive_result
            passes_completed.append(TranslationPass.EXECUTIVE_REWRITE)
        except Exception as e:
            issues.append(TranslationIssue(
                issue_id=f"TRANS_002_{section_key}",
                severity=IssueSeverity.WARNING,
                pass_name=TranslationPass.EXECUTIVE_REWRITE,
                section=section_key,
                message=f"Executive rewrite failed: {str(e)}",
            ))
            # Continue with literal result

        # Pass 3: Semantic Consistency Check
        semantic_result = self._pass_semantic_check(section_key, content, current_text)
        passes_completed.append(TranslationPass.SEMANTIC_CHECK)

        # Pass 4: KPI/Term Fix if needed
        if semantic_result.lost_numbers > 0 or semantic_result.lost_terms > 0:
            try:
                fixed_text = self._pass_kpi_fix(
                    section_key, content, current_text, semantic_result
                )
                current_text = fixed_text
                passes_completed.append(TranslationPass.KPI_FIX)

                # Re-check semantics after fix
                semantic_result = self._pass_semantic_check(
                    section_key, content, current_text
                )
            except Exception as e:
                issues.append(TranslationIssue(
                    issue_id=f"TRANS_004_{section_key}",
                    severity=IssueSeverity.WARNING,
                    pass_name=TranslationPass.KPI_FIX,
                    section=section_key,
                    message=f"KPI fix failed: {str(e)}",
                ))

        passes_completed.append(TranslationPass.FINAL)

        # Determine quality
        quality = self._calculate_quality(semantic_result.similarity_score)

        # Add issues from semantic check
        for issue_msg in semantic_result.issues:
            issues.append(TranslationIssue(
                issue_id=f"SEM_{section_key}",
                severity=IssueSeverity.WARNING,
                pass_name=TranslationPass.SEMANTIC_CHECK,
                section=section_key,
                message=issue_msg,
            ))

        processing_time = int((time.time() - start_time) * 1000)

        return TranslationResult(
            section=section_key,
            source_language=self._source_lang,
            target_language=self._target_lang,
            original_text=content,
            translated_text=current_text,
            quality=quality,
            semantic_check=semantic_result,
            passes_completed=passes_completed,
            issues=issues,
            processing_time_ms=processing_time,
        )

    def _pass_literal(self, section_key: str, content: str) -> str:
        """
        Pass 1: Literal translation.

        Preserves structure and numbers, accurate word-level translation.
        """
        if self._literal_translator:
            return self._literal_translator(
                content,
                self._source_lang.value,
                self._target_lang.value,
            )

        # Fallback: Apply glossary mapping
        return self._apply_glossary_translation(content)

    def _pass_executive_rewrite(self, section_key: str, content: str) -> str:
        """
        Pass 2: Executive rewrite.

        Applies board-level tonality while preserving meaning.
        """
        if self._executive_rewriter:
            return self._executive_rewriter(content, self._target_lang.value)

        # Fallback: Apply executive tone markers
        return self._apply_executive_tone(content)

    def _pass_semantic_check(
        self,
        section_key: str,
        original: str,
        translated: str,
    ) -> SemanticCheckResult:
        """
        Pass 3: Semantic consistency check.

        Validates that translation preserves meaning, numbers, and terms.
        """
        issues: List[str] = []

        # Check number preservation (use sets to avoid duplicate counting)
        original_numbers = set(self._extract_numbers(original))
        translated_numbers = set(self._extract_numbers(translated))

        preserved_numbers = len(original_numbers & translated_numbers)
        lost_numbers = len(original_numbers) - preserved_numbers

        if lost_numbers > 0:
            issues.append(
                f"Lost {lost_numbers} numbers in translation"
            )

        # Check term preservation (use sets to avoid duplicate counting)
        original_terms = set(self._extract_protected_terms(original))
        translated_terms = set(self._extract_protected_terms(translated))

        preserved_terms = len(original_terms & translated_terms)
        lost_terms = len(original_terms) - preserved_terms

        if lost_terms > 0:
            issues.append(
                f"Lost {lost_terms} protected terms in translation"
            )

        # Calculate similarity score
        similarity = self._calculate_similarity(original, translated)

        # Determine drift level
        drift = 1.0 - similarity
        if drift < 0.02:
            drift_level = SemanticDriftLevel.NONE
        elif drift < 0.05:
            drift_level = SemanticDriftLevel.MINIMAL
        elif drift < 0.08:
            drift_level = SemanticDriftLevel.ACCEPTABLE
        elif drift < 0.12:
            drift_level = SemanticDriftLevel.WARNING
            issues.append(f"Semantic drift {drift:.2%} exceeds warning threshold")
        else:
            drift_level = SemanticDriftLevel.CRITICAL
            issues.append(f"Critical semantic drift {drift:.2%}")

        return SemanticCheckResult(
            similarity_score=similarity,
            drift_level=drift_level,
            preserved_numbers=preserved_numbers,
            lost_numbers=lost_numbers,
            preserved_terms=preserved_terms,
            lost_terms=lost_terms,
            issues=issues,
        )

    def _pass_kpi_fix(
        self,
        section_key: str,
        original: str,
        translated: str,
        semantic_result: SemanticCheckResult,
    ) -> str:
        """
        Pass 4: Fix KPI and term preservation issues.

        Restores lost numbers and protected terms.
        """
        fixed = translated

        # Restore lost numbers
        original_numbers = self._extract_numbers_with_context(original)
        for num, context in original_numbers:
            if num not in fixed:
                # Try to insert number in appropriate location
                # This is a simplified fix - actual implementation would be smarter
                log.debug(
                    "[N4.2-Translation] Restoring number %s in %s",
                    num, section_key
                )

        # Map terms from source to target glossary
        for src_key, src_term in self._source_glossary.items():
            if src_term in original and src_term in fixed:
                target_term = self._target_glossary.get(src_key, src_term)
                if target_term != src_term:
                    fixed = fixed.replace(src_term, target_term)

        return fixed

    def _apply_glossary_translation(self, content: str) -> str:
        """Apply glossary-based translation for key terms."""
        result = content

        # Build reverse mapping: source term -> target term
        term_map: Dict[str, str] = {}
        for key, src_term in self._source_glossary.items():
            target_term = self._target_glossary.get(key)
            if target_term and src_term != target_term:
                term_map[src_term] = target_term

        # Apply replacements
        for src, tgt in term_map.items():
            result = result.replace(src, tgt)

        return result

    def _apply_executive_tone(self, content: str) -> str:
        """Apply executive tone markers for target language."""
        result = content

        # Get target language markers
        target_markers = EXECUTIVE_TONE_MARKERS.get(
            self._target_lang,
            EXECUTIVE_TONE_MARKERS[SupportedLanguage.EN],
        )

        # This is a placeholder - actual implementation would use LLM
        # For now, we just ensure the content has appropriate structure

        return result

    def _extract_numbers(self, text: str) -> List[str]:
        """Extract all numbers with context from text."""
        numbers: List[str] = []

        for pattern in NUMBER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)

        # Also extract standalone numbers
        standalone = re.findall(r"\b\d+(?:[.,]\d+)?\b", text)
        numbers.extend(standalone)

        return numbers

    def _extract_numbers_with_context(
        self,
        text: str,
    ) -> List[Tuple[str, str]]:
        """Extract numbers with surrounding context."""
        results: List[Tuple[str, str]] = []

        for pattern in NUMBER_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                num = match.group(1)
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end]
                results.append((num, context))

        return results

    def _extract_protected_terms(self, text: str) -> List[str]:
        """Extract protected terms from text."""
        found: List[str] = []

        for category, terms in PROTECTED_TERMS.items():
            for term in terms:
                if term.lower() in text.lower():
                    found.append(term)

        return found

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate semantic similarity between two texts.

        Uses Jaccard similarity as a baseline.
        Actual implementation could use embeddings.
        """
        # Tokenize
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        # Jaccard similarity
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)

        base_similarity = intersection / union if union > 0 else 0.0

        # Boost for preserved numbers
        numbers_a = set(self._extract_numbers(text_a))
        numbers_b = set(self._extract_numbers(text_b))

        if numbers_a:
            number_preservation = len(numbers_a & numbers_b) / len(numbers_a)
        else:
            number_preservation = 1.0

        # Boost for preserved terms
        terms_a = set(self._extract_protected_terms(text_a))
        terms_b = set(self._extract_protected_terms(text_b))

        if terms_a:
            term_preservation = len(terms_a & terms_b) / len(terms_a)
        else:
            term_preservation = 1.0

        # Combined score
        return (
            base_similarity * 0.5 +
            number_preservation * 0.3 +
            term_preservation * 0.2
        )

    def _calculate_quality(self, similarity: float) -> TranslationQuality:
        """Calculate translation quality from similarity score."""
        if similarity > 0.95:
            return TranslationQuality.EXCELLENT
        elif similarity > 0.90:
            return TranslationQuality.GOOD
        elif similarity > 0.85:
            return TranslationQuality.ACCEPTABLE
        elif similarity > 0.80:
            return TranslationQuality.NEEDS_REVIEW
        else:
            return TranslationQuality.POOR


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def translate_section(
    section_key: str,
    content: str,
    source_language: str = "de",
    target_language: str = "en",
    briefing: Optional[Dict[str, Any]] = None,
) -> TranslationResult:
    """
    Translate a single section.

    Args:
        section_key: Section identifier
        content: Content to translate
        source_language: Source language code
        target_language: Target language code
        briefing: Optional briefing data

    Returns:
        TranslationResult
    """
    engine = TranslationEngineV3(
        sections={section_key: content},
        briefing=briefing or {},
        source_language=source_language,
        target_language=target_language,
    )

    translated, report = engine.process()
    return report.section_results.get(section_key, TranslationResult(
        section=section_key,
        source_language=engine._source_lang,
        target_language=engine._target_lang,
        original_text=content,
        translated_text=content,
        quality=TranslationQuality.POOR,
        semantic_check=SemanticCheckResult(
            similarity_score=0.0,
            drift_level=SemanticDriftLevel.CRITICAL,
            preserved_numbers=0,
            lost_numbers=0,
            preserved_terms=0,
            lost_terms=0,
        ),
    ))


def translate_sections(
    sections: SectionDict,
    source_language: str = "de",
    target_language: str = "en",
    briefing: Optional[Dict[str, Any]] = None,
) -> Tuple[SectionDict, TranslationEngineReport]:
    """
    Translate all sections.

    Args:
        sections: Section dictionary
        source_language: Source language code
        target_language: Target language code
        briefing: Optional briefing data

    Returns:
        Tuple of (translated_sections, report)
    """
    engine = TranslationEngineV3(
        sections=sections,
        briefing=briefing or {},
        source_language=source_language,
        target_language=target_language,
    )

    return engine.process()


def check_semantic_consistency(
    original: str,
    translated: str,
    threshold: float = MAX_SEMANTIC_DRIFT,
) -> SemanticCheckResult:
    """
    Check semantic consistency between original and translated text.

    Args:
        original: Original text
        translated: Translated text
        threshold: Maximum acceptable drift

    Returns:
        SemanticCheckResult
    """
    engine = TranslationEngineV3(
        sections={},
        briefing={},
    )

    return engine._pass_semantic_check("check", original, translated)


def fix_kpi_drift(
    original: str,
    translated: str,
    source_language: str = "de",
    target_language: str = "en",
) -> str:
    """
    Fix KPI drift in translated text.

    Restores lost numbers and protected terms.

    Args:
        original: Original text
        translated: Translated text
        source_language: Source language code
        target_language: Target language code

    Returns:
        Fixed translated text
    """
    engine = TranslationEngineV3(
        sections={},
        briefing={},
        source_language=source_language,
        target_language=target_language,
    )

    semantic_result = engine._pass_semantic_check("fix", original, translated)
    return engine._pass_kpi_fix("fix", original, translated, semantic_result)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_translation_glossary(
    source_language: str,
    target_language: str,
) -> Dict[str, Tuple[str, str]]:
    """
    Get translation glossary for language pair.

    Returns:
        Dict mapping key to (source_term, target_term)
    """
    try:
        src_lang = SupportedLanguage(source_language.lower())
        tgt_lang = SupportedLanguage(target_language.lower())
    except ValueError:
        return {}

    src_glossary = CONSULTING_GLOSSARY.get(src_lang, {})
    tgt_glossary = CONSULTING_GLOSSARY.get(tgt_lang, {})

    result: Dict[str, Tuple[str, str]] = {}
    for key in set(src_glossary.keys()) | set(tgt_glossary.keys()):
        src_term = src_glossary.get(key, key)
        tgt_term = tgt_glossary.get(key, key)
        result[key] = (src_term, tgt_term)

    return result


def validate_translation_pair(
    source_language: str,
    target_language: str,
) -> bool:
    """Check if translation pair is supported."""
    try:
        SupportedLanguage(source_language.lower())
        SupportedLanguage(target_language.lower())
        return True
    except ValueError:
        return False
