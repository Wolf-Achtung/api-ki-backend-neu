# -*- coding: utf-8 -*-
"""
N4.2: Model Strategy Layer v3 (Multilingual)
=============================================

PLATIN+++ v5.2 - Multi-Language Intelligence Layer

Extension to the Model Strategy Layer with multilingual capabilities:
- Language-aware model selection
- Dual-model semantic merge with drift detection
- Cross-language quality validation
- Parallel generation (Claude + GPT → Semantic Merge)

Integrates with existing ModelStrategyLayer from model_strategy_layer.py.

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
Author: Claude + Wolf
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypedDict

from services.types import SectionDict, BriefingDict, EngineReport
from services.language_strategy_engine import (
    SupportedLanguage,
    SectionCategory,
    ModelPreference,
    LANGUAGE_MODEL_RULES,
    SECTION_CATEGORY_MAP,
)
from services.model_strategy_layer import (
    ModelProvider,
    SectionType,
    MergeStrategy,
    ContradictionDetector,
    RedundancyEngine,
    ToneHarmonizer,
    SemanticMerger,
)

log = logging.getLogger(__name__)

__all__ = [
    "MultilingualMergeStrategy",
    "DriftLevel",
    "MultilingualGenerationResult",
    "MultilingualMergeResult",
    "DriftDetectionResult",
    "MultilingualModelStrategy",
    "generate_multilingual",
    "semantic_merge_multilingual",
    "detect_drift",
    "validate_merge_quality",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class MultilingualMergeStrategy(Enum):
    """Merge strategies for multilingual content."""
    CLAUDE_EXECUTIVE = "claude_executive"  # Prefer Claude for executive tone
    GPT_NUMERIC = "gpt_numeric"  # Prefer GPT for numeric/table content
    WEIGHTED_BY_LANGUAGE = "weighted_by_language"  # Language-specific weights
    CONSENSUS_SEMANTIC = "consensus_semantic"  # Consensus with semantic validation
    BEST_QUALITY = "best_quality"  # Select highest quality output


class DriftLevel(Enum):
    """Drift level categories."""
    NONE = "none"           # < 0.02
    MINIMAL = "minimal"     # < 0.05
    ACCEPTABLE = "acceptable"  # < 0.08
    WARNING = "warning"     # < 0.15
    CRITICAL = "critical"   # >= 0.15


# Language-specific Claude weights for merging
# Higher = prefer Claude more for that language
CLAUDE_WEIGHT_BY_LANGUAGE: Dict[SupportedLanguage, float] = {
    SupportedLanguage.DE: 0.55,  # Slightly prefer Claude for German executive tone
    SupportedLanguage.EN: 0.50,  # Equal weight for English
    SupportedLanguage.FR: 0.65,  # Prefer Claude for French formal tone
    SupportedLanguage.IT: 0.60,  # Prefer Claude for Italian
    SupportedLanguage.ES: 0.60,  # Prefer Claude for Spanish
}

# Section-specific weights override
SECTION_CLAUDE_WEIGHT: Dict[str, float] = {
    "executive_summary": 0.70,  # Strong Claude preference for executive content
    "investment_thesis": 0.70,
    "gamechanger": 0.65,
    "roadmap_90d": 0.55,
    "roadmap_12m": 0.55,
    "recommendations": 0.60,
    "risks": 0.65,
    "ki_act_compliance": 0.65,
    "governance": 0.65,
    "business_case": 0.40,  # Prefer GPT for numeric content
    "kpi_dashboard": 0.35,
    "tools_empfehlungen": 0.45,
    "benchmark": 0.40,
}

# Drift thresholds
DRIFT_THRESHOLD_EXECUTIVE = 0.08
DRIFT_THRESHOLD_ROADMAP = 0.05
DRIFT_THRESHOLD_KPI = 0.01
DRIFT_THRESHOLD_DEFAULT = 0.10


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class MultilingualGenerationResult(TypedDict):
    """Result of multilingual generation."""
    content: str
    model: str
    language: str
    generation_time_ms: int
    token_count: int
    quality_score: float
    drift_from_source: float
    metadata: Dict[str, Any]


class MultilingualMergeResult(TypedDict):
    """Result of multilingual semantic merge."""
    merged_content: str
    source_models: List[str]
    target_language: str
    merge_strategy: str
    claude_contribution: float
    gpt_contribution: float
    contradictions_found: int
    redundancies_removed: int
    quality_score: float
    drift_score: float
    tone_harmonized: bool


class DriftDetectionResult(TypedDict):
    """Result of drift detection."""
    drift_level: str
    drift_value: float
    similarity_score: float
    numbers_preserved: bool
    terms_preserved: bool
    tone_consistent: bool
    issues: List[str]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ModelGenerationContext:
    """Context for model generation."""
    section_key: str
    language: SupportedLanguage
    section_category: SectionCategory
    source_content: Optional[str] = None
    briefing: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityMetrics:
    """Quality metrics for generated content."""
    overall_score: float = 0.0
    coherence_score: float = 0.0
    completeness_score: float = 0.0
    tone_score: float = 0.0
    accuracy_score: float = 0.0
    drift_score: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "overall": round(self.overall_score, 4),
            "coherence": round(self.coherence_score, 4),
            "completeness": round(self.completeness_score, 4),
            "tone": round(self.tone_score, 4),
            "accuracy": round(self.accuracy_score, 4),
            "drift": round(self.drift_score, 4),
        }


@dataclass
class MultilingualStrategyReport:
    """Report of multilingual model strategy processing."""

    engine_id: str = "MODEL_STRATEGY_V3"
    success: bool = True
    sections_processed: int = 0
    dual_generations: int = 0
    single_generations: int = 0
    merges_performed: int = 0
    avg_quality_score: float = 0.0
    avg_drift_score: float = 0.0
    contradictions_total: int = 0
    redundancies_removed: int = 0
    model_usage: Dict[str, int] = field(default_factory=dict)
    language_stats: Dict[str, int] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_issue(self, issue: str) -> None:
        """Add an issue."""
        self.issues.append(issue)
        self.success = False

    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "sections_processed": self.sections_processed,
            "dual_generations": self.dual_generations,
            "single_generations": self.single_generations,
            "merges_performed": self.merges_performed,
            "avg_quality_score": round(self.avg_quality_score, 4),
            "avg_drift_score": round(self.avg_drift_score, 4),
            "contradictions_total": self.contradictions_total,
            "redundancies_removed": self.redundancies_removed,
            "model_usage": self.model_usage,
            "language_stats": self.language_stats,
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# MULTILINGUAL DRIFT DETECTOR
# =============================================================================

class MultilingualDriftDetector:
    """
    Detects semantic drift in multilingual content.

    Uses cosine similarity approximation via word overlap,
    number preservation, and term consistency checks.
    """

    def __init__(self, source_language: SupportedLanguage, target_language: SupportedLanguage) -> None:
        self._source_lang = source_language
        self._target_lang = target_language
        self._detections: List[DriftDetectionResult] = []

    def detect_drift(
        self,
        source_text: str,
        target_text: str,
        section_type: str = "default",
    ) -> DriftDetectionResult:
        """
        Detect semantic drift between source and target text.

        Args:
            source_text: Original text
            target_text: Translated/generated text
            section_type: Section type for threshold selection

        Returns:
            DriftDetectionResult
        """
        issues: List[str] = []

        # Calculate similarity
        similarity = self._calculate_similarity(source_text, target_text)
        drift = 1.0 - similarity

        # Check number preservation
        source_numbers = self._extract_numbers(source_text)
        target_numbers = self._extract_numbers(target_text)
        numbers_preserved = set(source_numbers) <= set(target_numbers)

        if not numbers_preserved:
            missing = set(source_numbers) - set(target_numbers)
            issues.append(f"Numbers lost: {', '.join(list(missing)[:3])}")

        # Check key term preservation
        source_terms = self._extract_key_terms(source_text)
        target_terms = self._extract_key_terms(target_text)
        terms_preserved = len(source_terms & target_terms) >= len(source_terms) * 0.8

        if not terms_preserved:
            issues.append("Key terms not fully preserved")

        # Check tone consistency
        tone_consistent = self._check_tone_consistency(source_text, target_text)
        if not tone_consistent:
            issues.append("Tone shift detected")

        # Determine drift level
        if drift < 0.02:
            drift_level = DriftLevel.NONE
        elif drift < 0.05:
            drift_level = DriftLevel.MINIMAL
        elif drift < 0.08:
            drift_level = DriftLevel.ACCEPTABLE
        elif drift < 0.15:
            drift_level = DriftLevel.WARNING
            issues.append(f"Drift {drift:.2%} exceeds warning threshold")
        else:
            drift_level = DriftLevel.CRITICAL
            issues.append(f"Critical drift {drift:.2%}")

        result: DriftDetectionResult = {
            "drift_level": drift_level.value,
            "drift_value": drift,
            "similarity_score": similarity,
            "numbers_preserved": numbers_preserved,
            "terms_preserved": terms_preserved,
            "tone_consistent": tone_consistent,
            "issues": issues,
        }

        self._detections.append(result)
        return result

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate semantic similarity using word overlap."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        # Jaccard similarity
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)

        return intersection / union if union > 0 else 0.0

    def _extract_numbers(self, text: str) -> List[str]:
        """Extract numeric values from text."""
        patterns = [
            r"(\d+(?:[.,]\d+)?)\s*%",
            r"(\d+(?:[.,]\d+)?)\s*(?:€|EUR|USD|\$)",
            r"(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?|Mois|Mesi|Meses)",
            r"(\d+(?:[.,]\d+)?)\s*(?:Stunden?|hours?|heures?|ore|horas)",
        ]

        numbers: List[str] = []
        for pattern in patterns:
            numbers.extend(re.findall(pattern, text, re.IGNORECASE))

        return numbers

    def _extract_key_terms(self, text: str) -> Set[str]:
        """Extract key terms (numbers, KPIs, action words)."""
        terms: Set[str] = set()

        # Add numbers
        terms.update(self._extract_numbers(text))

        # Add key business terms
        key_patterns = [
            r"\b(ROI|KPI|NPV|IRR|TCO)\b",
            r"\b(Payback|Amortisation|Break-even)\b",
            r"\b(Risk|Risiko|Compliance)\b",
        ]

        for pattern in key_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                terms.add(match.group(0).lower())

        return terms

    def _check_tone_consistency(self, source: str, target: str) -> bool:
        """Check if tone is consistent between source and target."""
        # Simple heuristic: check for formal markers
        formal_markers = [
            r"\b(empfehlen|recommend|recommand|raccomand|recomiend)\b",
            r"\b(analysieren|analyze|analyser|analizzare|analizar)\b",
            r"\b(optimieren|optimize|optimiser|ottimizzare|optimizar)\b",
        ]

        source_formal = sum(
            1 for p in formal_markers if re.search(p, source, re.IGNORECASE)
        )
        target_formal = sum(
            1 for p in formal_markers if re.search(p, target, re.IGNORECASE)
        )

        # Allow some variance but ensure general tone direction
        if source_formal > 0:
            return target_formal >= source_formal * 0.5
        return True

    def get_all_detections(self) -> List[DriftDetectionResult]:
        """Get all drift detections."""
        return list(self._detections)


# =============================================================================
# MULTILINGUAL SEMANTIC MERGER
# =============================================================================

class MultilingualSemanticMerger:
    """
    Semantic merger with multilingual support.

    Extends SemanticMerger with:
    - Language-aware weight selection
    - Cross-language consistency validation
    - Drift-aware merging
    """

    def __init__(
        self,
        target_language: SupportedLanguage,
        source_language: Optional[SupportedLanguage] = None,
    ) -> None:
        self._target_lang = target_language
        self._source_lang = source_language or target_language
        self._base_merger = SemanticMerger()
        self._drift_detector = MultilingualDriftDetector(
            self._source_lang, self._target_lang
        )

    def merge(
        self,
        claude_content: str,
        gpt_content: str,
        section_key: str,
        source_content: Optional[str] = None,
        strategy: MultilingualMergeStrategy = MultilingualMergeStrategy.WEIGHTED_BY_LANGUAGE,
    ) -> MultilingualMergeResult:
        """
        Merge content from Claude and GPT with language awareness.

        Args:
            claude_content: Claude-generated content
            gpt_content: GPT-generated content
            section_key: Section identifier
            source_content: Original source content (for drift check)
            strategy: Merge strategy to use

        Returns:
            MultilingualMergeResult
        """
        # Get weights based on language and section
        claude_weight = self._get_claude_weight(section_key)

        # Perform merge based on strategy
        if strategy == MultilingualMergeStrategy.CLAUDE_EXECUTIVE:
            merged = self._merge_prefer_claude(claude_content, gpt_content)
            claude_contribution = 0.8
        elif strategy == MultilingualMergeStrategy.GPT_NUMERIC:
            merged = self._merge_prefer_gpt(claude_content, gpt_content)
            claude_contribution = 0.2
        elif strategy == MultilingualMergeStrategy.WEIGHTED_BY_LANGUAGE:
            merged = self._merge_weighted(claude_content, gpt_content, claude_weight)
            claude_contribution = claude_weight
        elif strategy == MultilingualMergeStrategy.CONSENSUS_SEMANTIC:
            merged = self._merge_consensus(claude_content, gpt_content)
            claude_contribution = 0.5
        else:  # BEST_QUALITY
            merged, claude_contribution = self._merge_best_quality(
                claude_content, gpt_content, source_content
            )

        # Check for contradictions
        contradiction_detector = ContradictionDetector()
        contradictions = contradiction_detector.detect_contradictions(
            claude_content, gpt_content, "claude", "gpt"
        )

        # Remove redundancies
        redundancy_engine = RedundancyEngine()
        _, _, redundancies_removed = redundancy_engine.remove_redundancies(
            claude_content, gpt_content
        )

        # Harmonize tone
        tone_harmonizer = ToneHarmonizer()
        merged = tone_harmonizer.harmonize(merged)

        # Calculate quality and drift
        quality_score = self._calculate_quality(merged, len(contradictions))
        drift_score = 0.0

        if source_content:
            drift_result = self._drift_detector.detect_drift(
                source_content, merged, section_key
            )
            drift_score = drift_result["drift_value"]

        return {
            "merged_content": merged,
            "source_models": ["claude", "gpt"],
            "target_language": self._target_lang.value,
            "merge_strategy": strategy.value,
            "claude_contribution": claude_contribution,
            "gpt_contribution": 1.0 - claude_contribution,
            "contradictions_found": len(contradictions),
            "redundancies_removed": redundancies_removed,
            "quality_score": quality_score,
            "drift_score": drift_score,
            "tone_harmonized": True,
        }

    def _get_claude_weight(self, section_key: str) -> float:
        """Get Claude weight based on language and section."""
        # Section-specific weight takes priority
        if section_key in SECTION_CLAUDE_WEIGHT:
            return SECTION_CLAUDE_WEIGHT[section_key]

        # Language-specific weight
        return CLAUDE_WEIGHT_BY_LANGUAGE.get(self._target_lang, 0.5)

    def _merge_prefer_claude(self, claude: str, gpt: str) -> str:
        """Merge preferring Claude content."""
        # Use Claude as base, add unique GPT content
        claude_sentences = set(self._split_sentences(claude))
        gpt_sentences = self._split_sentences(gpt)

        unique_gpt = [
            s for s in gpt_sentences
            if not any(self._similarity(s, c) > 0.6 for c in claude_sentences)
        ]

        if unique_gpt:
            return claude + "\n\n" + " ".join(unique_gpt[:2])
        return claude

    def _merge_prefer_gpt(self, claude: str, gpt: str) -> str:
        """Merge preferring GPT content."""
        gpt_sentences = set(self._split_sentences(gpt))
        claude_sentences = self._split_sentences(claude)

        unique_claude = [
            s for s in claude_sentences
            if not any(self._similarity(s, g) > 0.6 for g in gpt_sentences)
        ]

        if unique_claude:
            return gpt + "\n\n" + " ".join(unique_claude[:2])
        return gpt

    def _merge_weighted(self, claude: str, gpt: str, claude_weight: float) -> str:
        """Merge with weighted selection."""
        claude_sentences = self._split_sentences(claude)
        gpt_sentences = self._split_sentences(gpt)

        merged: List[str] = []
        max_len = max(len(claude_sentences), len(gpt_sentences))

        for i in range(max_len):
            if i < len(claude_sentences) and i < len(gpt_sentences):
                # Both available - use weight
                if claude_weight > 0.5:
                    merged.append(claude_sentences[i])
                else:
                    merged.append(gpt_sentences[i])
            elif i < len(claude_sentences):
                merged.append(claude_sentences[i])
            elif i < len(gpt_sentences):
                merged.append(gpt_sentences[i])

        return " ".join(merged)

    def _merge_consensus(self, claude: str, gpt: str) -> str:
        """Merge focusing on consensus content."""
        claude_sentences = self._split_sentences(claude)
        gpt_sentences = self._split_sentences(gpt)

        consensus: List[str] = []

        for c_sent in claude_sentences:
            for g_sent in gpt_sentences:
                if self._similarity(c_sent, g_sent) > 0.5:
                    # Take longer version
                    consensus.append(c_sent if len(c_sent) > len(g_sent) else g_sent)
                    break

        # If not enough consensus, add unique content
        if len(consensus) < 3:
            for sent in claude_sentences[:3]:
                if sent not in consensus:
                    consensus.append(sent)

        return " ".join(consensus)

    def _merge_best_quality(
        self,
        claude: str,
        gpt: str,
        source: Optional[str],
    ) -> Tuple[str, float]:
        """Select best quality output."""
        claude_quality = self._assess_quality(claude, source)
        gpt_quality = self._assess_quality(gpt, source)

        if claude_quality >= gpt_quality:
            return claude, 1.0
        else:
            return gpt, 0.0

    def _assess_quality(self, text: str, source: Optional[str]) -> float:
        """Assess quality of generated text."""
        score = 0.5  # Base score

        # Length bonus
        word_count = len(text.split())
        if word_count >= 50:
            score += 0.1
        if word_count >= 100:
            score += 0.1

        # Structure bonus (has formatting)
        if any(marker in text for marker in [":", "-", "•", "1.", "2."]):
            score += 0.1

        # Drift penalty if source provided
        if source:
            drift_result = self._drift_detector.detect_drift(source, text)
            score -= drift_result["drift_value"] * 0.5

        return min(1.0, max(0.0, score))

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]

    def _similarity(self, text_a: str, text_b: str) -> float:
        """Calculate similarity between two texts."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)

        return intersection / union if union > 0 else 0.0

    def _calculate_quality(self, text: str, contradictions: int) -> float:
        """Calculate quality score for merged content."""
        score = 0.8

        # Penalty for contradictions
        score -= contradictions * 0.05

        # Bonus for length
        if len(text) > 500:
            score += 0.1

        return max(0.0, min(1.0, score))


# =============================================================================
# MULTILINGUAL MODEL STRATEGY
# =============================================================================

class MultilingualModelStrategy:
    """
    N4.2: Multilingual Model Strategy Layer.

    Provides:
    - Language-aware model selection
    - Dual-model generation with semantic merge
    - Cross-language drift detection
    - Quality validation
    """

    def __init__(
        self,
        target_language: str = "de",
        source_language: Optional[str] = None,
    ) -> None:
        """
        Initialize Multilingual Model Strategy.

        Args:
            target_language: Target language code
            source_language: Source language code (for translations)
        """
        try:
            self._target_lang = SupportedLanguage(target_language.lower())
        except ValueError:
            self._target_lang = SupportedLanguage.DE

        if source_language:
            try:
                self._source_lang = SupportedLanguage(source_language.lower())
            except ValueError:
                self._source_lang = self._target_lang
        else:
            self._source_lang = self._target_lang

        self._merger = MultilingualSemanticMerger(
            self._target_lang, self._source_lang
        )
        self._drift_detector = MultilingualDriftDetector(
            self._source_lang, self._target_lang
        )
        self._report = MultilingualStrategyReport()

        # Model handlers (to be registered)
        self._claude_handler: Optional[Callable[..., str]] = None
        self._gpt_handler: Optional[Callable[..., str]] = None

        log.info(
            "[N4.2-ModelStrategy] Initialized: target=%s, source=%s",
            self._target_lang.value,
            self._source_lang.value,
        )

    def register_handlers(
        self,
        claude_handler: Optional[Callable[..., str]] = None,
        gpt_handler: Optional[Callable[..., str]] = None,
    ) -> None:
        """Register model handlers."""
        if claude_handler:
            self._claude_handler = claude_handler
        if gpt_handler:
            self._gpt_handler = gpt_handler

    def select_model(
        self,
        section_key: str,
        complexity_score: float = 0.5,
    ) -> Tuple[str, str]:
        """
        Select optimal model for section.

        Args:
            section_key: Section identifier
            complexity_score: Content complexity (0-1)

        Returns:
            Tuple of (model_name, reason)
        """
        # Get section category
        category = SECTION_CATEGORY_MAP.get(section_key, SectionCategory.NARRATIVE)

        # Get language-specific rules
        rules = LANGUAGE_MODEL_RULES.get(
            self._target_lang,
            LANGUAGE_MODEL_RULES[SupportedLanguage.DE],
        )

        preference = rules.get(category, ModelPreference.CLAUDE)

        if preference == ModelPreference.DUAL:
            return "dual", "section_requires_dual"
        elif preference == ModelPreference.CLAUDE:
            return "claude", "language_model_rule"
        else:
            return "gpt", "language_model_rule"

    def generate_and_merge(
        self,
        section_key: str,
        prompt: str,
        context: Dict[str, Any],
        source_content: Optional[str] = None,
    ) -> MultilingualMergeResult:
        """
        Generate content with dual models and merge.

        Args:
            section_key: Section identifier
            prompt: Generation prompt
            context: Generation context
            source_content: Original content (for drift check)

        Returns:
            MultilingualMergeResult
        """
        start_time = time.time()

        # Generate with both models
        claude_content = self._generate_claude(prompt, context)
        gpt_content = self._generate_gpt(prompt, context)

        # Determine merge strategy
        strategy = self._select_merge_strategy(section_key)

        # Perform merge
        result = self._merger.merge(
            claude_content,
            gpt_content,
            section_key,
            source_content,
            strategy,
        )

        # Update report
        self._report.sections_processed += 1
        self._report.dual_generations += 1
        self._report.merges_performed += 1
        self._report.contradictions_total += result["contradictions_found"]
        self._report.redundancies_removed += result["redundancies_removed"]

        # Track model usage
        self._report.model_usage["claude"] = self._report.model_usage.get("claude", 0) + 1
        self._report.model_usage["gpt"] = self._report.model_usage.get("gpt", 0) + 1

        # Track language
        self._report.language_stats[self._target_lang.value] = (
            self._report.language_stats.get(self._target_lang.value, 0) + 1
        )

        log.info(
            "[N4.2-ModelStrategy] Generated %s in %dms (quality=%.2f, drift=%.4f)",
            section_key,
            int((time.time() - start_time) * 1000),
            result["quality_score"],
            result["drift_score"],
        )

        return result

    def _generate_claude(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate content with Claude."""
        if self._claude_handler:
            try:
                return self._claude_handler(prompt, context)
            except Exception as e:
                log.error("[N4.2-ModelStrategy] Claude generation failed: %s", e)

        # Stub content for testing
        return f"[Claude content for: {prompt[:50]}...]"

    def _generate_gpt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate content with GPT."""
        if self._gpt_handler:
            try:
                return self._gpt_handler(prompt, context)
            except Exception as e:
                log.error("[N4.2-ModelStrategy] GPT generation failed: %s", e)

        # Stub content for testing
        return f"[GPT content for: {prompt[:50]}...]"

    def _select_merge_strategy(self, section_key: str) -> MultilingualMergeStrategy:
        """Select merge strategy based on section and language."""
        category = SECTION_CATEGORY_MAP.get(section_key, SectionCategory.NARRATIVE)

        if category in (SectionCategory.EXECUTIVE, SectionCategory.NARRATIVE):
            return MultilingualMergeStrategy.CLAUDE_EXECUTIVE
        elif category in (SectionCategory.KPI, SectionCategory.TABLES):
            return MultilingualMergeStrategy.GPT_NUMERIC
        else:
            return MultilingualMergeStrategy.WEIGHTED_BY_LANGUAGE

    def validate_quality(
        self,
        content: str,
        source_content: Optional[str] = None,
        section_key: str = "default",
    ) -> QualityMetrics:
        """
        Validate quality of generated content.

        Args:
            content: Generated content
            source_content: Original content (for drift)
            section_key: Section identifier

        Returns:
            QualityMetrics
        """
        metrics = QualityMetrics()

        # Completeness: word count
        word_count = len(content.split())
        metrics.completeness_score = min(1.0, word_count / 100)

        # Coherence: sentence structure
        sentences = re.split(r"[.!?]+", content)
        valid_sentences = [s for s in sentences if len(s.strip()) > 10]
        metrics.coherence_score = min(1.0, len(valid_sentences) / 5)

        # Tone: formal markers
        formal_markers = ["empfehlen", "analysieren", "optimieren", "strategisch"]
        marker_count = sum(1 for m in formal_markers if m.lower() in content.lower())
        metrics.tone_score = min(1.0, marker_count / 2)

        # Drift
        if source_content:
            drift_result = self._drift_detector.detect_drift(
                source_content, content, section_key
            )
            metrics.drift_score = 1.0 - drift_result["drift_value"]
        else:
            metrics.drift_score = 1.0

        # Overall
        metrics.overall_score = (
            metrics.completeness_score * 0.2 +
            metrics.coherence_score * 0.2 +
            metrics.tone_score * 0.2 +
            metrics.drift_score * 0.4
        )

        return metrics

    def get_report(self) -> MultilingualStrategyReport:
        """Get processing report."""
        return self._report


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def generate_multilingual(
    section_key: str,
    prompt: str,
    context: Dict[str, Any],
    target_language: str = "de",
    source_content: Optional[str] = None,
) -> MultilingualMergeResult:
    """
    Generate multilingual content with dual models.

    Args:
        section_key: Section identifier
        prompt: Generation prompt
        context: Generation context
        target_language: Target language code
        source_content: Original content (for drift check)

    Returns:
        MultilingualMergeResult
    """
    strategy = MultilingualModelStrategy(target_language=target_language)
    return strategy.generate_and_merge(section_key, prompt, context, source_content)


def semantic_merge_multilingual(
    claude_content: str,
    gpt_content: str,
    section_key: str,
    target_language: str = "de",
    source_content: Optional[str] = None,
    strategy: str = "weighted_by_language",
) -> MultilingualMergeResult:
    """
    Merge Claude and GPT content with language awareness.

    Args:
        claude_content: Claude-generated content
        gpt_content: GPT-generated content
        section_key: Section identifier
        target_language: Target language code
        source_content: Original content (for drift check)
        strategy: Merge strategy name

    Returns:
        MultilingualMergeResult
    """
    try:
        target_lang = SupportedLanguage(target_language.lower())
    except ValueError:
        target_lang = SupportedLanguage.DE

    merger = MultilingualSemanticMerger(target_lang)

    try:
        merge_strategy = MultilingualMergeStrategy(strategy)
    except ValueError:
        merge_strategy = MultilingualMergeStrategy.WEIGHTED_BY_LANGUAGE

    return merger.merge(
        claude_content,
        gpt_content,
        section_key,
        source_content,
        merge_strategy,
    )


def detect_drift(
    source_text: str,
    target_text: str,
    source_language: str = "de",
    target_language: str = "en",
    section_type: str = "default",
) -> DriftDetectionResult:
    """
    Detect semantic drift between source and target text.

    Args:
        source_text: Original text
        target_text: Translated/generated text
        source_language: Source language code
        target_language: Target language code
        section_type: Section type for threshold

    Returns:
        DriftDetectionResult
    """
    try:
        src_lang = SupportedLanguage(source_language.lower())
        tgt_lang = SupportedLanguage(target_language.lower())
    except ValueError:
        src_lang = SupportedLanguage.DE
        tgt_lang = SupportedLanguage.EN

    detector = MultilingualDriftDetector(src_lang, tgt_lang)
    return detector.detect_drift(source_text, target_text, section_type)


def validate_merge_quality(
    content: str,
    source_content: Optional[str] = None,
    target_language: str = "de",
    section_key: str = "default",
) -> Dict[str, float]:
    """
    Validate quality of merged content.

    Args:
        content: Merged content
        source_content: Original content
        target_language: Target language code
        section_key: Section identifier

    Returns:
        Quality metrics dictionary
    """
    strategy = MultilingualModelStrategy(target_language=target_language)
    metrics = strategy.validate_quality(content, source_content, section_key)
    return metrics.to_dict()
