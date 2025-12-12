"""
Multi-Model Strategy Layer (N4.0)

PLATIN+++ v5.0 - Autonomous Engine Layer

This module provides intelligent model selection and dual-generation
capabilities for optimal output quality.

Model Selection Strategy:
- Claude: Risk Engines, Narrative, Governance (nuanced reasoning)
- GPT: Tables, KPI calculations, Business Case Details (structured output)
- Dual Generation: executive_summary, roadmap_12m, recommendations

Features:
- Automatic model selection based on section and complexity
- Dual generation with semantic merging
- Contradiction detection and resolution
- Redundancy elimination
- Tone harmonization
"""

import logging
import hashlib
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypedDict,
    Union,
)

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class ModelProvider(Enum):
    """Available model providers."""
    GPT = "gpt"
    CLAUDE = "claude"
    DUAL = "dual"  # Both models with semantic merge


class SectionType(Enum):
    """Report section types."""
    EXECUTIVE_SUMMARY = "executive_summary"
    RISK_ASSESSMENT = "risk_assessment"
    BUSINESS_CASE = "business_case"
    KPI_CALCULATIONS = "kpi_calculations"
    TOOLS_ANALYSIS = "tools_analysis"
    ROADMAP = "roadmap"
    RECOMMENDATIONS = "recommendations"
    NARRATIVE = "narrative"
    GOVERNANCE = "governance"
    BENCHMARK = "benchmark"
    TABLES = "tables"
    AUTOMATION = "automation"


class ComplexityLevel(Enum):
    """Content complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MergeStrategy(Enum):
    """Strategies for merging dual-generated content."""
    PREFER_CLAUDE = "prefer_claude"
    PREFER_GPT = "prefer_gpt"
    WEIGHTED_BLEND = "weighted_blend"
    BEST_OF_BOTH = "best_of_both"
    CONSENSUS = "consensus"


# Model selection rules
MODEL_SELECTION_RULES: Dict[SectionType, ModelProvider] = {
    # Claude excels at nuanced reasoning
    SectionType.RISK_ASSESSMENT: ModelProvider.CLAUDE,
    SectionType.NARRATIVE: ModelProvider.CLAUDE,
    SectionType.GOVERNANCE: ModelProvider.CLAUDE,

    # GPT excels at structured output
    SectionType.TABLES: ModelProvider.GPT,
    SectionType.KPI_CALCULATIONS: ModelProvider.GPT,
    SectionType.BUSINESS_CASE: ModelProvider.GPT,
    SectionType.TOOLS_ANALYSIS: ModelProvider.GPT,
    SectionType.AUTOMATION: ModelProvider.GPT,
    SectionType.BENCHMARK: ModelProvider.GPT,

    # Dual generation for critical sections
    SectionType.EXECUTIVE_SUMMARY: ModelProvider.DUAL,
    SectionType.ROADMAP: ModelProvider.DUAL,
    SectionType.RECOMMENDATIONS: ModelProvider.DUAL,
}

# Complexity thresholds for model override
COMPLEXITY_THRESHOLDS: Dict[ComplexityLevel, float] = {
    ComplexityLevel.LOW: 0.3,
    ComplexityLevel.MEDIUM: 0.5,
    ComplexityLevel.HIGH: 0.7,
    ComplexityLevel.CRITICAL: 0.9,
}

# Claude weight for blending (higher = prefer Claude)
CLAUDE_WEIGHT_BY_SECTION: Dict[SectionType, float] = {
    SectionType.EXECUTIVE_SUMMARY: 0.6,  # Slightly prefer Claude for tone
    SectionType.ROADMAP: 0.5,  # Equal weight
    SectionType.RECOMMENDATIONS: 0.55,  # Slightly prefer Claude
}


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class TenantProfile(TypedDict, total=False):
    """Tenant profile for model selection."""
    tenant_id: str
    preferred_model: str
    industry: str
    complexity_bias: float
    quality_threshold: float


class GenerationResult(TypedDict):
    """Result of content generation."""
    content: str
    model: str
    generation_time_ms: int
    token_count: int
    confidence: float
    metadata: Dict[str, Any]


class MergeResult(TypedDict):
    """Result of semantic merge."""
    merged_content: str
    source_models: List[str]
    merge_strategy: str
    contradictions_found: int
    redundancies_removed: int
    quality_score: float


class ModelStrategyResult(TypedDict):
    """Full result of model strategy processing."""
    section: str
    selected_model: str
    generation_result: GenerationResult
    merge_result: Optional[MergeResult]
    decision_reason: str


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ContradictionReport:
    """Report of detected contradictions."""
    source_a: str
    source_b: str
    text_a: str
    text_b: str
    contradiction_type: str
    severity: str
    resolution: Optional[str] = None


@dataclass
class RedundancyReport:
    """Report of detected redundancies."""
    text_a: str
    text_b: str
    similarity_score: float
    kept_version: str
    removed_version: str


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model."""
    model: ModelProvider
    avg_generation_time_ms: float = 0.0
    avg_token_count: float = 0.0
    success_rate: float = 1.0
    quality_score: float = 0.8
    call_count: int = 0


# =============================================================================
# CONTRADICTION DETECTOR
# =============================================================================

class ContradictionDetector:
    """
    Detects contradictions between two generated texts.

    Uses pattern matching and semantic analysis to find
    conflicting statements.
    """

    # Contradiction patterns (word pairs that often indicate conflict)
    CONTRADICTION_PAIRS: List[Tuple[str, str]] = [
        ("erhöhen", "senken"),
        ("steigern", "reduzieren"),
        ("wachstum", "rückgang"),
        ("positiv", "negativ"),
        ("empfehlen", "abraten"),
        ("chancen", "risiken"),
        ("stärken", "schwächen"),
        ("vorteile", "nachteile"),
        ("zunahme", "abnahme"),
        ("verbesserung", "verschlechterung"),
        ("hoch", "niedrig"),
        ("mehr", "weniger"),
        ("steigt", "sinkt"),
        ("wächst", "schrumpft"),
        ("optimistisch", "pessimistisch"),
        ("kurzfristig", "langfristig"),
        ("intern", "extern"),
        ("automatisiert", "manuell"),
    ]

    # Numeric patterns
    NUMERIC_PATTERN = re.compile(
        r"(\d+(?:[.,]\d+)?)\s*(%|prozent|euro|€|mio|tsd|k)",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        self._contradictions: List[ContradictionReport] = []

    def detect_contradictions(
        self,
        text_a: str,
        text_b: str,
        source_a: str = "model_a",
        source_b: str = "model_b",
    ) -> List[ContradictionReport]:
        """
        Detect contradictions between two texts.

        Returns list of detected contradictions.
        """
        contradictions: List[ContradictionReport] = []

        text_a_lower = text_a.lower()
        text_b_lower = text_b.lower()

        # Check word-based contradictions
        for word_a, word_b in self.CONTRADICTION_PAIRS:
            # Check if text_a has word_a and text_b has word_b (or vice versa)
            a_has_first = word_a in text_a_lower
            a_has_second = word_b in text_a_lower
            b_has_first = word_a in text_b_lower
            b_has_second = word_b in text_b_lower

            if (a_has_first and b_has_second) or (a_has_second and b_has_first):
                # Find context around the words
                context_a = self._extract_context(text_a, word_a if a_has_first else word_b)
                context_b = self._extract_context(text_b, word_b if b_has_second else word_a)

                contradiction = ContradictionReport(
                    source_a=source_a,
                    source_b=source_b,
                    text_a=context_a,
                    text_b=context_b,
                    contradiction_type="semantic",
                    severity="medium",
                )
                contradictions.append(contradiction)

        # Check numeric contradictions
        numeric_contradictions = self._check_numeric_contradictions(
            text_a, text_b, source_a, source_b
        )
        contradictions.extend(numeric_contradictions)

        self._contradictions.extend(contradictions)
        return contradictions

    def _extract_context(self, text: str, word: str, window: int = 50) -> str:
        """Extract context around a word."""
        text_lower = text.lower()
        pos = text_lower.find(word)
        if pos == -1:
            return ""

        start = max(0, pos - window)
        end = min(len(text), pos + len(word) + window)

        context = text[start:end]
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context

    def _check_numeric_contradictions(
        self,
        text_a: str,
        text_b: str,
        source_a: str,
        source_b: str,
    ) -> List[ContradictionReport]:
        """Check for contradicting numeric values."""
        contradictions: List[ContradictionReport] = []

        matches_a = self.NUMERIC_PATTERN.findall(text_a)
        matches_b = self.NUMERIC_PATTERN.findall(text_b)

        # Compare similar metrics (same unit)
        for num_a, unit_a in matches_a:
            for num_b, unit_b in matches_b:
                if unit_a.lower() == unit_b.lower():
                    try:
                        val_a = float(num_a.replace(",", "."))
                        val_b = float(num_b.replace(",", "."))

                        # Check for significant difference (>10%)
                        if val_a != 0:
                            diff = abs(val_b - val_a) / abs(val_a)
                            if diff > 0.1:
                                contradiction = ContradictionReport(
                                    source_a=source_a,
                                    source_b=source_b,
                                    text_a=f"{num_a} {unit_a}",
                                    text_b=f"{num_b} {unit_b}",
                                    contradiction_type="numeric",
                                    severity="high" if diff > 0.25 else "medium",
                                )
                                contradictions.append(contradiction)
                    except ValueError:
                        pass

        return contradictions

    def get_all_contradictions(self) -> List[ContradictionReport]:
        """Get all detected contradictions."""
        return list(self._contradictions)

    def clear(self) -> None:
        """Clear contradiction history."""
        self._contradictions.clear()


# =============================================================================
# REDUNDANCY ENGINE
# =============================================================================

class RedundancyEngine:
    """
    Detects and removes redundant content.

    Uses text similarity to find duplicate or near-duplicate
    statements between generated outputs.
    """

    SIMILARITY_THRESHOLD = 0.7  # 70% similarity = redundant

    def __init__(self) -> None:
        self._redundancies: List[RedundancyReport] = []

    def detect_redundancies(
        self,
        text_a: str,
        text_b: str,
    ) -> List[RedundancyReport]:
        """
        Detect redundant sentences between two texts.

        Returns list of redundancy reports.
        """
        redundancies: List[RedundancyReport] = []

        sentences_a = self._split_sentences(text_a)
        sentences_b = self._split_sentences(text_b)

        for sent_a in sentences_a:
            for sent_b in sentences_b:
                similarity = self._calculate_similarity(sent_a, sent_b)
                if similarity >= self.SIMILARITY_THRESHOLD:
                    # Prefer longer/more detailed version
                    kept = sent_a if len(sent_a) >= len(sent_b) else sent_b
                    removed = sent_b if len(sent_a) >= len(sent_b) else sent_a

                    redundancy = RedundancyReport(
                        text_a=sent_a,
                        text_b=sent_b,
                        similarity_score=similarity,
                        kept_version=kept,
                        removed_version=removed,
                    )
                    redundancies.append(redundancy)

        self._redundancies.extend(redundancies)
        return redundancies

    def remove_redundancies(
        self,
        text_a: str,
        text_b: str,
    ) -> Tuple[str, str, int]:
        """
        Remove redundant content from texts.

        Returns (cleaned_text_a, cleaned_text_b, removed_count)
        """
        redundancies = self.detect_redundancies(text_a, text_b)

        removed_count = 0
        cleaned_a = text_a
        cleaned_b = text_b

        for redundancy in redundancies:
            # Remove the shorter/less detailed version
            if redundancy.removed_version in cleaned_a:
                cleaned_a = cleaned_a.replace(redundancy.removed_version, "")
                removed_count += 1
            elif redundancy.removed_version in cleaned_b:
                cleaned_b = cleaned_b.replace(redundancy.removed_version, "")
                removed_count += 1

        # Clean up extra whitespace
        cleaned_a = re.sub(r"\s+", " ", cleaned_a).strip()
        cleaned_b = re.sub(r"\s+", " ", cleaned_b).strip()

        return cleaned_a, cleaned_b, removed_count

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate Jaccard similarity between two texts."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)

        return intersection / union if union > 0 else 0.0

    def get_all_redundancies(self) -> List[RedundancyReport]:
        """Get all detected redundancies."""
        return list(self._redundancies)

    def clear(self) -> None:
        """Clear redundancy history."""
        self._redundancies.clear()


# =============================================================================
# TONE HARMONIZER
# =============================================================================

class ToneHarmonizer:
    """
    Harmonizes tone between merged outputs.

    Ensures consistent professional tone throughout the document.
    """

    # Informal words to replace with formal alternatives
    TONE_REPLACEMENTS: Dict[str, str] = {
        "super": "hervorragend",
        "toll": "ausgezeichnet",
        "schlecht": "suboptimal",
        "gut": "positiv",
        "ok": "akzeptabel",
        "halt": "",  # Remove filler words
        "quasi": "gewissermaßen",
        "irgendwie": "",
        "eigentlich": "",
        "echt": "tatsächlich",
        "total": "vollständig",
        "mega": "erheblich",
        "krass": "bemerkenswert",
    }

    # Professional phrases to ensure
    PROFESSIONAL_PATTERNS: List[Tuple[str, str]] = [
        (r"\bman\b", "das Unternehmen"),
        (r"\bdie firma\b", "das Unternehmen"),
        (r"\bwir empfehlen\b", "es wird empfohlen"),
        (r"\bsie sollten\b", "es empfiehlt sich"),
    ]

    def __init__(self) -> None:
        self._replacements_made: int = 0

    def harmonize(self, text: str) -> str:
        """
        Harmonize tone of text to professional standard.

        Returns harmonized text.
        """
        result = text
        self._replacements_made = 0

        # Apply word replacements
        for informal, formal in self.TONE_REPLACEMENTS.items():
            pattern = re.compile(rf"\b{informal}\b", re.IGNORECASE)
            if pattern.search(result):
                result = pattern.sub(formal, result)
                self._replacements_made += 1

        # Apply professional pattern replacements
        for pattern_str, replacement in self.PROFESSIONAL_PATTERNS:
            regex = re.compile(pattern_str, re.IGNORECASE)
            if regex.search(result):
                result = regex.sub(replacement, result)
                self._replacements_made += 1

        # Clean up extra whitespace
        result = re.sub(r"\s+", " ", result).strip()

        return result

    def get_replacements_count(self) -> int:
        """Get number of replacements made."""
        return self._replacements_made


# =============================================================================
# SEMANTIC MERGER
# =============================================================================

class SemanticMerger:
    """
    Merges content from two models semantically.

    Combines:
    - Contradiction detection
    - Redundancy removal
    - Tone harmonization
    - Quality scoring
    """

    def __init__(self) -> None:
        self._contradiction_detector = ContradictionDetector()
        self._redundancy_engine = RedundancyEngine()
        self._tone_harmonizer = ToneHarmonizer()

    def merge(
        self,
        content_a: str,
        content_b: str,
        model_a: str = "claude",
        model_b: str = "gpt",
        strategy: MergeStrategy = MergeStrategy.WEIGHTED_BLEND,
        section_type: Optional[SectionType] = None,
    ) -> MergeResult:
        """
        Merge content from two models.

        Returns merged result with metadata.
        """
        # Detect contradictions
        contradictions = self._contradiction_detector.detect_contradictions(
            content_a, content_b, model_a, model_b
        )

        # Remove redundancies
        cleaned_a, cleaned_b, redundancies_removed = self._redundancy_engine.remove_redundancies(
            content_a, content_b
        )

        # Merge based on strategy
        if strategy == MergeStrategy.PREFER_CLAUDE:
            merged = self._merge_prefer(cleaned_a, cleaned_b, prefer_first=True)
        elif strategy == MergeStrategy.PREFER_GPT:
            merged = self._merge_prefer(cleaned_a, cleaned_b, prefer_first=False)
        elif strategy == MergeStrategy.WEIGHTED_BLEND:
            weight = CLAUDE_WEIGHT_BY_SECTION.get(section_type, 0.5) if section_type else 0.5
            merged = self._merge_weighted(cleaned_a, cleaned_b, weight)
        elif strategy == MergeStrategy.BEST_OF_BOTH:
            merged = self._merge_best_of_both(cleaned_a, cleaned_b)
        else:  # CONSENSUS
            merged = self._merge_consensus(cleaned_a, cleaned_b, contradictions)

        # Harmonize tone
        merged = self._tone_harmonizer.harmonize(merged)

        # Calculate quality score
        quality_score = self._calculate_quality_score(
            merged, len(contradictions), redundancies_removed
        )

        return {
            "merged_content": merged,
            "source_models": [model_a, model_b],
            "merge_strategy": strategy.value,
            "contradictions_found": len(contradictions),
            "redundancies_removed": redundancies_removed,
            "quality_score": quality_score,
        }

    def _merge_prefer(
        self,
        text_a: str,
        text_b: str,
        prefer_first: bool,
    ) -> str:
        """Merge preferring one source over the other."""
        primary = text_a if prefer_first else text_b
        secondary = text_b if prefer_first else text_a

        # Use primary as base, add unique content from secondary
        sentences_primary = set(self._split_sentences(primary))
        sentences_secondary = self._split_sentences(secondary)

        # Find unique sentences in secondary
        unique_secondary = [
            s for s in sentences_secondary
            if not any(
                self._redundancy_engine._calculate_similarity(s, p) > 0.5
                for p in sentences_primary
            )
        ]

        # Combine
        if unique_secondary:
            return primary + "\n\n" + " ".join(unique_secondary)
        return primary

    def _merge_weighted(
        self,
        text_a: str,
        text_b: str,
        weight_a: float,
    ) -> str:
        """Merge with weighted selection of sentences."""
        sentences_a = self._split_sentences(text_a)
        sentences_b = self._split_sentences(text_b)

        merged_sentences: List[str] = []

        # Interleave based on weight
        max_len = max(len(sentences_a), len(sentences_b))
        for i in range(max_len):
            # Select based on weight probability
            if i < len(sentences_a) and i < len(sentences_b):
                # Both available - weight determines selection
                if weight_a > 0.5:
                    merged_sentences.append(sentences_a[i])
                else:
                    merged_sentences.append(sentences_b[i])
            elif i < len(sentences_a):
                merged_sentences.append(sentences_a[i])
            elif i < len(sentences_b):
                merged_sentences.append(sentences_b[i])

        return " ".join(merged_sentences)

    def _merge_best_of_both(
        self,
        text_a: str,
        text_b: str,
    ) -> str:
        """Select best sentences from both sources."""
        sentences_a = self._split_sentences(text_a)
        sentences_b = self._split_sentences(text_b)

        all_sentences = sentences_a + sentences_b

        # Score sentences by length and information density
        scored = [
            (s, len(s) * self._information_density(s))
            for s in all_sentences
        ]

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Take top sentences, avoiding redundancy
        selected: List[str] = []
        for sentence, _ in scored:
            if not any(
                self._redundancy_engine._calculate_similarity(sentence, s) > 0.6
                for s in selected
            ):
                selected.append(sentence)

            if len(selected) >= len(sentences_a):
                break

        return " ".join(selected)

    def _merge_consensus(
        self,
        text_a: str,
        text_b: str,
        contradictions: List[ContradictionReport],
    ) -> str:
        """Merge focusing on consensus points."""
        sentences_a = self._split_sentences(text_a)
        sentences_b = self._split_sentences(text_b)

        # Find sentences that appear in both (consensus)
        consensus: List[str] = []
        for sent_a in sentences_a:
            for sent_b in sentences_b:
                similarity = self._redundancy_engine._calculate_similarity(sent_a, sent_b)
                if similarity > 0.5:
                    # Take longer version
                    consensus.append(sent_a if len(sent_a) > len(sent_b) else sent_b)
                    break

        # If not enough consensus, add unique important points
        if len(consensus) < 3:
            for sent_a in sentences_a[:3]:
                if sent_a not in consensus:
                    consensus.append(sent_a)

        return " ".join(consensus)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]

    def _information_density(self, text: str) -> float:
        """Calculate information density of text."""
        words = text.split()
        if not words:
            return 0.0

        # Count unique words relative to total
        unique_ratio = len(set(words)) / len(words)

        # Bonus for numbers (data-rich)
        number_bonus = len(re.findall(r"\d+", text)) * 0.1

        return unique_ratio + number_bonus

    def _calculate_quality_score(
        self,
        merged: str,
        contradictions: int,
        redundancies: int,
    ) -> float:
        """Calculate quality score for merged content."""
        base_score = 0.8

        # Penalty for contradictions
        base_score -= contradictions * 0.05

        # Small penalty for redundancies (they were removed)
        base_score -= redundancies * 0.02

        # Bonus for length (more comprehensive)
        if len(merged) > 500:
            base_score += 0.1

        return max(0.0, min(1.0, base_score))


# =============================================================================
# MODEL STRATEGY LAYER
# =============================================================================

class ModelStrategyLayer:
    """
    Main class for multi-model strategy management.

    Provides:
    - Model selection based on section and complexity
    - Dual generation with semantic merge
    - Performance tracking
    """

    def __init__(self) -> None:
        self._merger = SemanticMerger()
        self._performance: Dict[ModelProvider, ModelPerformanceMetrics] = {
            ModelProvider.GPT: ModelPerformanceMetrics(model=ModelProvider.GPT),
            ModelProvider.CLAUDE: ModelPerformanceMetrics(model=ModelProvider.CLAUDE),
        }
        self._model_handlers: Dict[ModelProvider, Callable[..., GenerationResult]] = {}
        self._lock = threading.RLock()

        log.info("[N4.0-ModelStrategy] ModelStrategyLayer initialized")

    def register_model_handler(
        self,
        model: ModelProvider,
        handler: Callable[..., GenerationResult],
    ) -> None:
        """Register a handler for a model provider."""
        self._model_handlers[model] = handler
        log.debug("[N4.0-ModelStrategy] Registered handler for %s", model.value)

    def select_model(
        self,
        section: SectionType,
        complexity_score: float,
        tenant_profile: Optional[TenantProfile] = None,
    ) -> Tuple[ModelProvider, str]:
        """
        Select the best model for a section.

        Returns (selected_model, reason)
        """
        # Check tenant preference
        if tenant_profile and tenant_profile.get("preferred_model"):
            preferred = tenant_profile["preferred_model"]
            if preferred == "claude":
                return ModelProvider.CLAUDE, "tenant_preference"
            elif preferred == "gpt":
                return ModelProvider.GPT, "tenant_preference"

        # Get default model for section
        default_model = MODEL_SELECTION_RULES.get(section, ModelProvider.GPT)

        # Override based on complexity
        if complexity_score >= COMPLEXITY_THRESHOLDS[ComplexityLevel.CRITICAL]:
            # Critical complexity -> prefer Claude for nuanced reasoning
            if default_model == ModelProvider.GPT:
                return ModelProvider.CLAUDE, "complexity_override"

        elif complexity_score <= COMPLEXITY_THRESHOLDS[ComplexityLevel.LOW]:
            # Low complexity -> prefer GPT for speed
            if default_model == ModelProvider.CLAUDE:
                return ModelProvider.GPT, "simplicity_override"

        return default_model, "default_selection"

    def generate(
        self,
        section: SectionType,
        prompt: str,
        context: Dict[str, Any],
        complexity_score: float = 0.5,
        tenant_profile: Optional[TenantProfile] = None,
    ) -> ModelStrategyResult:
        """
        Generate content for a section using optimal model.

        Handles single-model and dual-model generation.
        """
        selected_model, reason = self.select_model(
            section, complexity_score, tenant_profile
        )

        log.info(
            "[N4.0-ModelStrategy] Selected %s for %s (reason: %s)",
            selected_model.value,
            section.value,
            reason,
        )

        if selected_model == ModelProvider.DUAL:
            return self._dual_generate(section, prompt, context, tenant_profile)

        # Single model generation
        result = self._generate_with_model(selected_model, prompt, context)

        return {
            "section": section.value,
            "selected_model": selected_model.value,
            "generation_result": result,
            "merge_result": None,
            "decision_reason": reason,
        }

    def _dual_generate(
        self,
        section: SectionType,
        prompt: str,
        context: Dict[str, Any],
        tenant_profile: Optional[TenantProfile] = None,
    ) -> ModelStrategyResult:
        """Generate with both models and merge."""
        log.info("[N4.0-ModelStrategy] Dual generation for %s", section.value)

        # Generate with both models
        result_claude = self._generate_with_model(ModelProvider.CLAUDE, prompt, context)
        result_gpt = self._generate_with_model(ModelProvider.GPT, prompt, context)

        # Determine merge strategy
        strategy = MergeStrategy.WEIGHTED_BLEND

        # Merge results
        merge_result = self._merger.merge(
            result_claude["content"],
            result_gpt["content"],
            model_a="claude",
            model_b="gpt",
            strategy=strategy,
            section_type=section,
        )

        # Create combined generation result
        combined_result: GenerationResult = {
            "content": merge_result["merged_content"],
            "model": "dual",
            "generation_time_ms": (
                result_claude["generation_time_ms"] +
                result_gpt["generation_time_ms"]
            ),
            "token_count": (
                result_claude["token_count"] +
                result_gpt["token_count"]
            ),
            "confidence": merge_result["quality_score"],
            "metadata": {
                "claude_confidence": result_claude["confidence"],
                "gpt_confidence": result_gpt["confidence"],
                "merge_strategy": strategy.value,
            },
        }

        return {
            "section": section.value,
            "selected_model": "dual",
            "generation_result": combined_result,
            "merge_result": merge_result,
            "decision_reason": "dual_generation_section",
        }

    def _generate_with_model(
        self,
        model: ModelProvider,
        prompt: str,
        context: Dict[str, Any],
    ) -> GenerationResult:
        """Generate content with a specific model."""
        handler = self._model_handlers.get(model)

        if handler:
            start_time = time.time()
            try:
                result = handler(prompt, context)
                generation_time = int((time.time() - start_time) * 1000)
                result["generation_time_ms"] = generation_time
                self._update_performance(model, generation_time, True)
                return result
            except Exception as e:
                log.error(
                    "[N4.0-ModelStrategy] Generation failed for %s: %s",
                    model.value,
                    str(e),
                )
                self._update_performance(model, 0, False)

        # Return stub result if no handler
        log.warning(
            "[N4.0-ModelStrategy] No handler for %s, using stub",
            model.value,
        )
        return {
            "content": f"[Stub content for {model.value}]",
            "model": model.value,
            "generation_time_ms": 0,
            "token_count": 0,
            "confidence": 0.5,
            "metadata": {"stub": True},
        }

    def _update_performance(
        self,
        model: ModelProvider,
        generation_time_ms: int,
        success: bool,
    ) -> None:
        """Update performance metrics for a model."""
        with self._lock:
            metrics = self._performance.get(model)
            if metrics:
                metrics.call_count += 1

                if success:
                    # Update moving average
                    n = metrics.call_count
                    metrics.avg_generation_time_ms = (
                        (metrics.avg_generation_time_ms * (n - 1) + generation_time_ms) / n
                    )
                    metrics.success_rate = (
                        (metrics.success_rate * (n - 1) + 1.0) / n
                    )
                else:
                    metrics.success_rate = (
                        (metrics.success_rate * (metrics.call_count - 1)) /
                        metrics.call_count
                    )

    def dual_generate(
        self,
        section: SectionType,
        prompt: str,
        context: Dict[str, Any],
    ) -> MergeResult:
        """
        Explicitly perform dual generation.

        Convenience method for sections that always need both models.
        """
        result = self._dual_generate(section, prompt, context)
        return result["merge_result"] or {
            "merged_content": result["generation_result"]["content"],
            "source_models": ["claude", "gpt"],
            "merge_strategy": "default",
            "contradictions_found": 0,
            "redundancies_removed": 0,
            "quality_score": 0.8,
        }

    def semantic_merge(
        self,
        content_a: str,
        content_b: str,
        strategy: MergeStrategy = MergeStrategy.WEIGHTED_BLEND,
    ) -> MergeResult:
        """
        Perform semantic merge of two contents.

        Direct access to merger for external use.
        """
        return self._merger.merge(
            content_a,
            content_b,
            strategy=strategy,
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all models."""
        with self._lock:
            return {
                model.value: {
                    "avg_generation_time_ms": metrics.avg_generation_time_ms,
                    "success_rate": metrics.success_rate,
                    "call_count": metrics.call_count,
                    "quality_score": metrics.quality_score,
                }
                for model, metrics in self._performance.items()
            }

    def get_model_strategy_map(self) -> Dict[str, str]:
        """Get mapping of sections to selected models."""
        return {
            section.value: model.value
            for section, model in MODEL_SELECTION_RULES.items()
        }


# =============================================================================
# SINGLETON & HELPER FUNCTIONS
# =============================================================================

_strategy_instance: Optional[ModelStrategyLayer] = None
_strategy_lock = threading.Lock()


def get_model_strategy() -> ModelStrategyLayer:
    """Get or create the singleton strategy instance."""
    global _strategy_instance

    if _strategy_instance is None:
        with _strategy_lock:
            if _strategy_instance is None:
                _strategy_instance = ModelStrategyLayer()

    return _strategy_instance


def select_model(
    section: str,
    complexity_score: float = 0.5,
    tenant_profile: Optional[TenantProfile] = None,
) -> Tuple[str, str]:
    """
    Select optimal model for a section.

    Convenience function for external use.
    """
    strategy = get_model_strategy()

    try:
        section_type = SectionType(section)
    except ValueError:
        section_type = SectionType.NARRATIVE  # Default

    model, reason = strategy.select_model(section_type, complexity_score, tenant_profile)
    return model.value, reason


def dual_generate(
    section: str,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
) -> MergeResult:
    """
    Perform dual generation for a section.

    Convenience function for external use.
    """
    strategy = get_model_strategy()

    try:
        section_type = SectionType(section)
    except ValueError:
        section_type = SectionType.EXECUTIVE_SUMMARY

    return strategy.dual_generate(section_type, prompt, context or {})


def semantic_merge(
    content_a: str,
    content_b: str,
    strategy: str = "weighted_blend",
) -> MergeResult:
    """
    Merge two contents semantically.

    Convenience function for external use.
    """
    model_strategy = get_model_strategy()

    try:
        merge_strategy = MergeStrategy(strategy)
    except ValueError:
        merge_strategy = MergeStrategy.WEIGHTED_BLEND

    return model_strategy.semantic_merge(content_a, content_b, merge_strategy)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ModelProvider",
    "SectionType",
    "ComplexityLevel",
    "MergeStrategy",
    # Classes
    "ModelStrategyLayer",
    "SemanticMerger",
    "ContradictionDetector",
    "RedundancyEngine",
    "ToneHarmonizer",
    # Data classes
    "ContradictionReport",
    "RedundancyReport",
    "ModelPerformanceMetrics",
    # Type definitions
    "TenantProfile",
    "GenerationResult",
    "MergeResult",
    "ModelStrategyResult",
    # Functions
    "get_model_strategy",
    "select_model",
    "dual_generate",
    "semantic_merge",
    # Constants
    "MODEL_SELECTION_RULES",
    "CLAUDE_WEIGHT_BY_SECTION",
]
