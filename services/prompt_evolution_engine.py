"""
Adaptive Prompt Evolution Layer (N4.0)

PLATIN+++ v5.0 - Autonomous Engine Layer

This module enables self-improving prompts based on system feedback.

Features:
- Prompt Genome representation
- Mutation (±7% wording variation)
- Fitness scoring based on:
  - Leak probability
  - Fallback frequency
  - Consistency score
  - Narrative depth
- Evolution cycle: Generate → Evaluate → Select → Replace

The system improves prompts automatically based on:
- Regression results
- Audit traces
- Inconsistency flags
- Performance layer metrics
"""

import logging
import hashlib
import random
import re
import threading
import time
from collections import defaultdict
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
)

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class PromptCategory(Enum):
    """Categories of prompts."""
    ANALYSIS = "analysis"
    NARRATIVE = "narrative"
    EXTRACTION = "extraction"
    FORMATTING = "formatting"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"


class MutationType(Enum):
    """Types of prompt mutations."""
    SYNONYM_REPLACE = "synonym_replace"
    PHRASE_REORDER = "phrase_reorder"
    EMPHASIS_ADJUST = "emphasis_adjust"
    CONSTRAINT_ADD = "constraint_add"
    CONSTRAINT_REMOVE = "constraint_remove"
    EXAMPLE_MODIFY = "example_modify"


class FitnessMetric(Enum):
    """Fitness evaluation metrics."""
    LEAK_PROBABILITY = "leak_probability"
    FALLBACK_FREQUENCY = "fallback_frequency"
    CONSISTENCY_SCORE = "consistency_score"
    NARRATIVE_DEPTH = "narrative_depth"
    RESPONSE_QUALITY = "response_quality"
    EXECUTION_TIME = "execution_time"


class EvolutionPhase(Enum):
    """Phases of the evolution cycle."""
    GENERATE = "generate"
    EVALUATE = "evaluate"
    SELECT = "select"
    REPLACE = "replace"


# Evolution configuration
EVOLUTION_CONFIG = {
    "mutation_rate": 0.07,  # ±7% wording variation
    "population_size": 5,
    "selection_pressure": 0.6,  # Top 60% survive
    "max_generations": 10,
    "fitness_threshold": 0.85,
    "elite_count": 1,  # Best prompt always survives
}

# Fitness weights
FITNESS_WEIGHTS: Dict[FitnessMetric, float] = {
    FitnessMetric.LEAK_PROBABILITY: 0.25,
    FitnessMetric.FALLBACK_FREQUENCY: 0.20,
    FitnessMetric.CONSISTENCY_SCORE: 0.25,
    FitnessMetric.NARRATIVE_DEPTH: 0.15,
    FitnessMetric.RESPONSE_QUALITY: 0.15,
}

# Synonym dictionary for mutations
SYNONYMS: Dict[str, List[str]] = {
    "analysiere": ["untersuche", "evaluiere", "bewerte", "prüfe"],
    "beschreibe": ["erläutere", "erkläre", "stelle dar", "schildere"],
    "identifiziere": ["erkenne", "finde", "lokalisiere", "bestimme"],
    "erstelle": ["generiere", "erzeuge", "entwickle", "formuliere"],
    "wichtig": ["wesentlich", "bedeutsam", "relevant", "kritisch"],
    "detailliert": ["ausführlich", "umfassend", "gründlich", "tiefgehend"],
    "kurz": ["knapp", "prägnant", "kompakt", "zusammengefasst"],
    "klar": ["deutlich", "verständlich", "transparent", "eindeutig"],
    "strukturiert": ["geordnet", "systematisch", "organisiert", "gegliedert"],
    "präzise": ["genau", "exakt", "akkurat", "spezifisch"],
}

# Constraint templates for adding emphasis
CONSTRAINT_TEMPLATES = [
    "WICHTIG: {constraint}",
    "Beachte besonders: {constraint}",
    "Kritisch: {constraint}",
    "Stelle sicher: {constraint}",
]


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class PromptMetrics(TypedDict):
    """Metrics for prompt evaluation."""
    leak_probability: float
    fallback_frequency: float
    consistency_score: float
    narrative_depth: float
    response_quality: float
    execution_time_ms: int


class EvolutionResult(TypedDict):
    """Result of an evolution cycle."""
    generation: int
    best_fitness: float
    avg_fitness: float
    mutations_applied: int
    prompt_replaced: bool
    improvements: List[str]


class PromptGenome(TypedDict):
    """Genome representation of a prompt."""
    genome_id: str
    content: str
    category: str
    version: int
    fitness: float
    metrics: PromptMetrics
    mutations: List[str]
    parent_id: Optional[str]
    created_at: str


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MutationRecord:
    """Record of a mutation operation."""
    mutation_id: str
    mutation_type: MutationType
    original_segment: str
    mutated_segment: str
    position: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EvaluationRecord:
    """Record of a prompt evaluation."""
    evaluation_id: str
    prompt_id: str
    metrics: PromptMetrics
    fitness_score: float
    evaluation_context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EvolutionState:
    """State of the evolution process."""
    evolution_id: str
    started_at: datetime
    current_generation: int = 0
    population: List[PromptGenome] = field(default_factory=list)
    history: List[EvolutionResult] = field(default_factory=list)
    best_ever: Optional[PromptGenome] = None


# =============================================================================
# MUTATION ENGINE
# =============================================================================

class MutationEngine:
    """
    Applies mutations to prompts.

    Mutation types:
    - Synonym replacement
    - Phrase reordering
    - Emphasis adjustment
    - Constraint addition/removal
    - Example modification
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)
        self._mutations_applied: List[MutationRecord] = []

    def mutate(
        self,
        prompt: str,
        mutation_rate: float = 0.07,
        allowed_mutations: Optional[List[MutationType]] = None,
    ) -> Tuple[str, List[MutationRecord]]:
        """
        Apply mutations to a prompt.

        Args:
            prompt: Original prompt text
            mutation_rate: Probability of mutation (default 7%)
            allowed_mutations: Optional list of allowed mutation types

        Returns:
            Tuple of (mutated_prompt, mutation_records)
        """
        if allowed_mutations is None:
            allowed_mutations = list(MutationType)

        mutations: List[MutationRecord] = []
        mutated = prompt

        # Decide which mutations to apply
        for mutation_type in allowed_mutations:
            if self._rng.random() < mutation_rate:
                mutated, record = self._apply_mutation(mutated, mutation_type)
                if record:
                    mutations.append(record)
                    self._mutations_applied.append(record)

        return mutated, mutations

    def _apply_mutation(
        self,
        prompt: str,
        mutation_type: MutationType,
    ) -> Tuple[str, Optional[MutationRecord]]:
        """Apply a specific mutation type."""
        if mutation_type == MutationType.SYNONYM_REPLACE:
            return self._mutate_synonym(prompt)
        elif mutation_type == MutationType.PHRASE_REORDER:
            return self._mutate_reorder(prompt)
        elif mutation_type == MutationType.EMPHASIS_ADJUST:
            return self._mutate_emphasis(prompt)
        elif mutation_type == MutationType.CONSTRAINT_ADD:
            return self._mutate_add_constraint(prompt)
        elif mutation_type == MutationType.CONSTRAINT_REMOVE:
            return self._mutate_remove_constraint(prompt)
        elif mutation_type == MutationType.EXAMPLE_MODIFY:
            return self._mutate_example(prompt)
        return prompt, None

    def _mutate_synonym(
        self,
        prompt: str,
    ) -> Tuple[str, Optional[MutationRecord]]:
        """Replace a word with a synonym."""
        words = prompt.split()
        candidates: List[Tuple[int, str, List[str]]] = []

        for i, word in enumerate(words):
            word_lower = word.lower().strip(".,;:!?")
            if word_lower in SYNONYMS:
                candidates.append((i, word, SYNONYMS[word_lower]))

        if not candidates:
            return prompt, None

        # Select random candidate
        idx, original_word, synonyms = self._rng.choice(candidates)
        replacement = self._rng.choice(synonyms)

        # Preserve capitalization
        if original_word[0].isupper():
            replacement = replacement.capitalize()

        words[idx] = replacement
        mutated = " ".join(words)

        record = MutationRecord(
            mutation_id=self._generate_id(),
            mutation_type=MutationType.SYNONYM_REPLACE,
            original_segment=original_word,
            mutated_segment=replacement,
            position=idx,
        )

        return mutated, record

    def _mutate_reorder(
        self,
        prompt: str,
    ) -> Tuple[str, Optional[MutationRecord]]:
        """Reorder sentences or clauses."""
        sentences = re.split(r"(?<=[.!?])\s+", prompt)

        if len(sentences) < 2:
            return prompt, None

        # Select two sentences to swap
        idx1 = self._rng.randint(0, len(sentences) - 2)
        idx2 = idx1 + 1

        original = f"{sentences[idx1]} {sentences[idx2]}"
        sentences[idx1], sentences[idx2] = sentences[idx2], sentences[idx1]
        mutated_segment = f"{sentences[idx1]} {sentences[idx2]}"

        mutated = " ".join(sentences)

        record = MutationRecord(
            mutation_id=self._generate_id(),
            mutation_type=MutationType.PHRASE_REORDER,
            original_segment=original,
            mutated_segment=mutated_segment,
            position=idx1,
        )

        return mutated, record

    def _mutate_emphasis(
        self,
        prompt: str,
    ) -> Tuple[str, Optional[MutationRecord]]:
        """Adjust emphasis markers."""
        emphasis_patterns = [
            (r"\bwichtig\b", "WICHTIG"),
            (r"\bkritisch\b", "KRITISCH"),
            (r"\bachtung\b", "ACHTUNG"),
            (r"\bWICHTIG\b", "wichtig"),  # Also de-emphasize
        ]

        for pattern, replacement in emphasis_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match and self._rng.random() < 0.5:
                original = match.group()
                mutated = re.sub(pattern, replacement, prompt, count=1, flags=re.IGNORECASE)

                record = MutationRecord(
                    mutation_id=self._generate_id(),
                    mutation_type=MutationType.EMPHASIS_ADJUST,
                    original_segment=original,
                    mutated_segment=replacement,
                    position=match.start(),
                )

                return mutated, record

        return prompt, None

    def _mutate_add_constraint(
        self,
        prompt: str,
    ) -> Tuple[str, Optional[MutationRecord]]:
        """Add a constraint to the prompt."""
        constraints = [
            "Vermeide Wiederholungen",
            "Fokussiere auf Fakten",
            "Halte den professionellen Ton",
            "Priorisiere Klarheit",
            "Beachte die Vollständigkeit",
        ]

        constraint = self._rng.choice(constraints)
        template = self._rng.choice(CONSTRAINT_TEMPLATES)
        addition = template.format(constraint=constraint)

        # Add at the end
        mutated = prompt.rstrip() + "\n\n" + addition

        record = MutationRecord(
            mutation_id=self._generate_id(),
            mutation_type=MutationType.CONSTRAINT_ADD,
            original_segment="",
            mutated_segment=addition,
            position=len(prompt),
        )

        return mutated, record

    def _mutate_remove_constraint(
        self,
        prompt: str,
    ) -> Tuple[str, Optional[MutationRecord]]:
        """Remove an existing constraint from the prompt."""
        # Look for constraint patterns
        patterns = [
            r"WICHTIG:.*?(?:\n|$)",
            r"Beachte besonders:.*?(?:\n|$)",
            r"Kritisch:.*?(?:\n|$)",
            r"Stelle sicher:.*?(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt)
            if match:
                original = match.group()
                mutated = prompt[:match.start()] + prompt[match.end():]
                mutated = mutated.strip()

                record = MutationRecord(
                    mutation_id=self._generate_id(),
                    mutation_type=MutationType.CONSTRAINT_REMOVE,
                    original_segment=original,
                    mutated_segment="",
                    position=match.start(),
                )

                return mutated, record

        return prompt, None

    def _mutate_example(
        self,
        prompt: str,
    ) -> Tuple[str, Optional[MutationRecord]]:
        """Modify an example in the prompt."""
        # Look for example patterns
        example_pattern = r"(Beispiel|z\.B\.|zum Beispiel):\s*([^.]+\.)"
        match = re.search(example_pattern, prompt, re.IGNORECASE)

        if match:
            original = match.group(2)

            # Simplify or elaborate the example
            if len(original) > 30:
                # Simplify: truncate
                mutated_example = original[:30] + "..."
            else:
                # Elaborate: add detail
                mutated_example = original.rstrip(".") + " (und weitere)"

            mutated = prompt[:match.start(2)] + mutated_example + prompt[match.end(2):]

            record = MutationRecord(
                mutation_id=self._generate_id(),
                mutation_type=MutationType.EXAMPLE_MODIFY,
                original_segment=original,
                mutated_segment=mutated_example,
                position=match.start(2),
            )

            return mutated, record

        return prompt, None

    def _generate_id(self) -> str:
        """Generate unique mutation ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:8]

    def get_mutation_history(self) -> List[MutationRecord]:
        """Get mutation history."""
        return list(self._mutations_applied)


# =============================================================================
# FITNESS EVALUATOR
# =============================================================================

class FitnessEvaluator:
    """
    Evaluates prompt fitness based on multiple metrics.

    Metrics:
    - Leak probability (lower is better)
    - Fallback frequency (lower is better)
    - Consistency score (higher is better)
    - Narrative depth (higher is better)
    - Response quality (higher is better)
    """

    def __init__(self) -> None:
        self._evaluations: List[EvaluationRecord] = []
        self._external_evaluator: Optional[Callable[[str, Dict[str, Any]], PromptMetrics]] = None

    def register_external_evaluator(
        self,
        evaluator: Callable[[str, Dict[str, Any]], PromptMetrics],
    ) -> None:
        """Register an external evaluation function."""
        self._external_evaluator = evaluator

    def evaluate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        historical_metrics: Optional[PromptMetrics] = None,
    ) -> Tuple[float, PromptMetrics]:
        """
        Evaluate prompt fitness.

        Args:
            prompt: Prompt text to evaluate
            context: Optional evaluation context
            historical_metrics: Optional historical metrics for comparison

        Returns:
            Tuple of (fitness_score, metrics)
        """
        context = context or {}

        # Get metrics (from external evaluator or estimated)
        if self._external_evaluator:
            metrics = self._external_evaluator(prompt, context)
        else:
            metrics = self._estimate_metrics(prompt, context, historical_metrics)

        # Calculate fitness score
        fitness = self._calculate_fitness(metrics)

        # Record evaluation
        record = EvaluationRecord(
            evaluation_id=self._generate_id(),
            prompt_id=context.get("prompt_id", "unknown"),
            metrics=metrics,
            fitness_score=fitness,
            evaluation_context=context,
        )
        self._evaluations.append(record)

        return fitness, metrics

    def _estimate_metrics(
        self,
        prompt: str,
        context: Dict[str, Any],
        historical: Optional[PromptMetrics],
    ) -> PromptMetrics:
        """Estimate metrics based on prompt characteristics."""
        # Base metrics from historical or defaults
        if historical:
            base_leak = historical["leak_probability"]
            base_fallback = historical["fallback_frequency"]
            base_consistency = historical["consistency_score"]
            base_narrative = historical["narrative_depth"]
            base_quality = historical["response_quality"]
        else:
            base_leak = 0.1
            base_fallback = 0.15
            base_consistency = 0.75
            base_narrative = 0.70
            base_quality = 0.75

        # Adjust based on prompt characteristics

        # Leak probability: more constraints = lower leak
        constraint_count = len(re.findall(r"WICHTIG|Beachte|Kritisch|Stelle sicher", prompt))
        leak_adjustment = -0.02 * constraint_count
        leak_prob = max(0.01, min(0.5, base_leak + leak_adjustment))

        # Fallback: clearer structure = lower fallback
        structure_indicators = len(re.findall(r"\d\.|•|-\s", prompt))
        fallback_adjustment = -0.01 * structure_indicators
        fallback_freq = max(0.01, min(0.5, base_fallback + fallback_adjustment))

        # Consistency: specific instructions = higher consistency
        specificity = len(re.findall(r"genau|spezifisch|präzise|exakt", prompt, re.IGNORECASE))
        consistency_adjustment = 0.02 * specificity
        consistency = max(0.5, min(1.0, base_consistency + consistency_adjustment))

        # Narrative depth: longer prompt with examples = deeper narrative
        length_factor = min(len(prompt) / 1000, 1.0)
        has_examples = 1 if "beispiel" in prompt.lower() or "z.b." in prompt.lower() else 0
        narrative_adjustment = 0.05 * length_factor + 0.05 * has_examples
        narrative = max(0.5, min(1.0, base_narrative + narrative_adjustment))

        # Response quality: balanced prompt = higher quality
        quality = (consistency + narrative + (1 - leak_prob) + (1 - fallback_freq)) / 4

        return {
            "leak_probability": round(leak_prob, 3),
            "fallback_frequency": round(fallback_freq, 3),
            "consistency_score": round(consistency, 3),
            "narrative_depth": round(narrative, 3),
            "response_quality": round(quality, 3),
            "execution_time_ms": context.get("execution_time_ms", 0),
        }

    def _calculate_fitness(self, metrics: PromptMetrics) -> float:
        """Calculate weighted fitness score."""
        # Invert negative metrics (lower is better)
        leak_score = 1 - metrics["leak_probability"]
        fallback_score = 1 - metrics["fallback_frequency"]

        components = {
            FitnessMetric.LEAK_PROBABILITY: leak_score,
            FitnessMetric.FALLBACK_FREQUENCY: fallback_score,
            FitnessMetric.CONSISTENCY_SCORE: metrics["consistency_score"],
            FitnessMetric.NARRATIVE_DEPTH: metrics["narrative_depth"],
            FitnessMetric.RESPONSE_QUALITY: metrics["response_quality"],
        }

        fitness = sum(
            score * FITNESS_WEIGHTS.get(metric, 0)
            for metric, score in components.items()
        )

        return round(fitness, 4)

    def _generate_id(self) -> str:
        """Generate unique evaluation ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:8]

    def get_evaluation_history(self) -> List[EvaluationRecord]:
        """Get evaluation history."""
        return list(self._evaluations)


# =============================================================================
# EVOLUTION ENGINE
# =============================================================================

class EvolutionEngine:
    """
    Manages the evolution cycle for prompts.

    Cycle:
    1. Generate - Create variant population
    2. Evaluate - Score each variant
    3. Select - Keep top performers
    4. Replace - Update prompt if improvement found
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._mutation_engine = MutationEngine(seed)
        self._fitness_evaluator = FitnessEvaluator()
        self._rng = random.Random(seed)
        self._states: Dict[str, EvolutionState] = {}
        self._lock = threading.RLock()

    def initialize_evolution(
        self,
        prompt_id: str,
        initial_prompt: str,
        category: PromptCategory,
        initial_metrics: Optional[PromptMetrics] = None,
    ) -> EvolutionState:
        """
        Initialize evolution for a prompt.

        Args:
            prompt_id: Unique prompt identifier
            initial_prompt: Starting prompt text
            category: Prompt category
            initial_metrics: Optional initial metrics

        Returns:
            EvolutionState for tracking
        """
        evolution_id = f"evo_{prompt_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create initial genome
        initial_genome = self._create_genome(
            initial_prompt,
            category,
            version=0,
            parent_id=None,
            metrics=initial_metrics,
        )

        # Initialize population with the original
        population = [initial_genome]

        state = EvolutionState(
            evolution_id=evolution_id,
            started_at=datetime.now(),
            current_generation=0,
            population=population,
            best_ever=initial_genome,
        )

        with self._lock:
            self._states[prompt_id] = state

        log.info(
            "[N4.0-PromptEvolution] Initialized evolution for %s",
            prompt_id,
        )

        return state

    def evolve_generation(
        self,
        prompt_id: str,
        evaluation_context: Optional[Dict[str, Any]] = None,
    ) -> EvolutionResult:
        """
        Execute one generation of evolution.

        Args:
            prompt_id: Prompt identifier
            evaluation_context: Context for evaluation

        Returns:
            EvolutionResult with generation statistics
        """
        with self._lock:
            state = self._states.get(prompt_id)
            if not state:
                raise ValueError(f"No evolution state for {prompt_id}")

            # Phase 1: Generate - Create variants
            new_population = self._generate_variants(state)

            # Phase 2: Evaluate - Score all variants
            evaluated_population = self._evaluate_population(
                new_population,
                evaluation_context or {},
            )

            # Phase 3: Select - Keep top performers
            selected = self._select_survivors(evaluated_population)

            # Phase 4: Replace - Update state
            result = self._update_state(state, selected)

            return result

    def _generate_variants(
        self,
        state: EvolutionState,
    ) -> List[PromptGenome]:
        """Generate variant population through mutation."""
        variants: List[PromptGenome] = []
        population_size = EVOLUTION_CONFIG["population_size"]

        # Keep elite (best performer)
        if state.best_ever:
            variants.append(state.best_ever)

        # Generate mutations from current population
        for genome in state.population:
            while len(variants) < population_size:
                mutated_content, mutations = self._mutation_engine.mutate(
                    genome["content"],
                    mutation_rate=EVOLUTION_CONFIG["mutation_rate"],
                )

                if mutated_content != genome["content"]:
                    variant = self._create_genome(
                        mutated_content,
                        PromptCategory(genome["category"]),
                        version=genome["version"] + 1,
                        parent_id=genome["genome_id"],
                        mutations=[m.mutation_type.value for m in mutations],
                    )
                    variants.append(variant)

                if len(variants) >= population_size:
                    break

        return variants

    def _evaluate_population(
        self,
        population: List[PromptGenome],
        context: Dict[str, Any],
    ) -> List[PromptGenome]:
        """Evaluate fitness of all genomes."""
        for genome in population:
            fitness, metrics = self._fitness_evaluator.evaluate(
                genome["content"],
                context={**context, "prompt_id": genome["genome_id"]},
                historical_metrics=genome.get("metrics"),
            )
            genome["fitness"] = fitness
            genome["metrics"] = metrics

        return population

    def _select_survivors(
        self,
        population: List[PromptGenome],
    ) -> List[PromptGenome]:
        """Select top performers to survive."""
        # Sort by fitness descending
        sorted_pop = sorted(population, key=lambda g: g["fitness"], reverse=True)

        # Select top performers
        cutoff = int(len(sorted_pop) * float(EVOLUTION_CONFIG["selection_pressure"]))
        cutoff = max(int(EVOLUTION_CONFIG["elite_count"]), cutoff)

        return sorted_pop[:cutoff]

    def _update_state(
        self,
        state: EvolutionState,
        selected: List[PromptGenome],
    ) -> EvolutionResult:
        """Update evolution state with selected population."""
        state.current_generation += 1
        state.population = selected

        # Track best ever
        current_best = selected[0] if selected else None
        prompt_replaced = False

        if current_best:
            if not state.best_ever or current_best["fitness"] > state.best_ever["fitness"]:
                state.best_ever = current_best
                prompt_replaced = True

        # Calculate statistics
        fitnesses = [g["fitness"] for g in selected]
        best_fitness = max(fitnesses) if fitnesses else 0.0
        avg_fitness = sum(fitnesses) / len(fitnesses) if fitnesses else 0.0

        # Count mutations
        mutations_applied = sum(
            len(g.get("mutations", [])) for g in selected
        )

        # Identify improvements
        improvements: List[str] = []
        if prompt_replaced:
            improvements.append("Neue beste Variante gefunden")
        if current_best and current_best.get("metrics"):
            metrics = current_best["metrics"]
            if metrics["leak_probability"] < 0.05:
                improvements.append("Sehr geringe Leak-Wahrscheinlichkeit")
            if metrics["consistency_score"] > 0.9:
                improvements.append("Hohe Konsistenz erreicht")

        result: EvolutionResult = {
            "generation": state.current_generation,
            "best_fitness": best_fitness,
            "avg_fitness": avg_fitness,
            "mutations_applied": mutations_applied,
            "prompt_replaced": prompt_replaced,
            "improvements": improvements,
        }

        state.history.append(result)

        log.info(
            "[N4.0-PromptEvolution] Generation %d: best=%.4f, avg=%.4f",
            state.current_generation,
            best_fitness,
            avg_fitness,
        )

        return result

    def _create_genome(
        self,
        content: str,
        category: PromptCategory,
        version: int,
        parent_id: Optional[str],
        metrics: Optional[PromptMetrics] = None,
        mutations: Optional[List[str]] = None,
    ) -> PromptGenome:
        """Create a new genome."""
        genome_id = hashlib.sha256(
            f"{content}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        return {
            "genome_id": genome_id,
            "content": content,
            "category": category.value,
            "version": version,
            "fitness": 0.0,
            "metrics": metrics or {
                "leak_probability": 0.1,
                "fallback_frequency": 0.1,
                "consistency_score": 0.7,
                "narrative_depth": 0.7,
                "response_quality": 0.7,
                "execution_time_ms": 0,
            },
            "mutations": mutations or [],
            "parent_id": parent_id,
            "created_at": datetime.now().isoformat(),
        }

    def get_best_prompt(self, prompt_id: str) -> Optional[str]:
        """Get the best evolved prompt."""
        with self._lock:
            state = self._states.get(prompt_id)
            if state and state.best_ever:
                return state.best_ever["content"]
            return None

    def get_evolution_state(self, prompt_id: str) -> Optional[EvolutionState]:
        """Get current evolution state."""
        with self._lock:
            return self._states.get(prompt_id)

    def should_continue_evolution(self, prompt_id: str) -> bool:
        """Check if evolution should continue."""
        with self._lock:
            state = self._states.get(prompt_id)
            if not state:
                return False

            # Stop conditions
            if state.current_generation >= EVOLUTION_CONFIG["max_generations"]:
                return False

            if state.best_ever and state.best_ever["fitness"] >= EVOLUTION_CONFIG["fitness_threshold"]:
                return False

            return True


# =============================================================================
# PROMPT EVOLUTION ENGINE
# =============================================================================

class PromptEvolutionEngine:
    """
    Main engine for adaptive prompt evolution.

    Features:
    - Full evolution lifecycle management
    - Integration with system feedback
    - Prompt genome tracking
    - Evolution map for reporting
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._evolution_engine = EvolutionEngine(seed)
        self._prompts: Dict[str, PromptGenome] = {}
        self._lock = threading.RLock()

        log.info("[N4.0-PromptEvolution] PromptEvolutionEngine initialized")

    def register_prompt(
        self,
        prompt_id: str,
        content: str,
        category: str,
        initial_metrics: Optional[PromptMetrics] = None,
    ) -> PromptGenome:
        """
        Register a prompt for evolution.

        Args:
            prompt_id: Unique identifier
            content: Prompt text
            category: Prompt category
            initial_metrics: Optional initial performance metrics

        Returns:
            PromptGenome for the registered prompt
        """
        try:
            cat = PromptCategory(category)
        except ValueError:
            cat = PromptCategory.ANALYSIS

        state = self._evolution_engine.initialize_evolution(
            prompt_id,
            content,
            cat,
            initial_metrics,
        )

        with self._lock:
            self._prompts[prompt_id] = state.population[0]

        return state.population[0]

    def evolve_prompt(
        self,
        prompt_id: str,
        feedback: Optional[Dict[str, Any]] = None,
        max_generations: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evolve a prompt based on feedback.

        Args:
            prompt_id: Prompt identifier
            feedback: Performance feedback from system
            max_generations: Optional max generations for this run

        Returns:
            Evolution results summary
        """
        generations_run = 0
        max_gens = max_generations or EVOLUTION_CONFIG["max_generations"]

        results: List[EvolutionResult] = []

        while generations_run < max_gens:
            if not self._evolution_engine.should_continue_evolution(prompt_id):
                break

            result = self._evolution_engine.evolve_generation(
                prompt_id,
                evaluation_context=feedback,
            )
            results.append(result)
            generations_run += 1

        # Update stored prompt with best version
        best_content = self._evolution_engine.get_best_prompt(prompt_id)
        state = self._evolution_engine.get_evolution_state(prompt_id)

        if state and state.best_ever:
            with self._lock:
                self._prompts[prompt_id] = state.best_ever

        return {
            "prompt_id": prompt_id,
            "generations_run": generations_run,
            "final_fitness": results[-1]["best_fitness"] if results else 0.0,
            "improvements_found": sum(1 for r in results if r["prompt_replaced"]),
            "best_prompt": best_content,
            "evolution_history": results,
        }

    def get_prompt(self, prompt_id: str) -> Optional[str]:
        """Get current best version of a prompt."""
        with self._lock:
            genome = self._prompts.get(prompt_id)
            if genome:
                return genome["content"]
            return None

    def get_prompt_genome(self, prompt_id: str) -> Optional[PromptGenome]:
        """Get full genome for a prompt."""
        with self._lock:
            return self._prompts.get(prompt_id)

    def update_feedback(
        self,
        prompt_id: str,
        metrics: PromptMetrics,
    ) -> None:
        """
        Update feedback metrics for a prompt.

        Triggers re-evaluation and potential evolution.
        """
        with self._lock:
            if prompt_id in self._prompts:
                self._prompts[prompt_id]["metrics"] = metrics

        log.info(
            "[N4.0-PromptEvolution] Updated feedback for %s: consistency=%.2f",
            prompt_id,
            metrics.get("consistency_score", 0),
        )

    def get_prompt_evolution_map(self) -> Dict[str, Any]:
        """
        Get evolution map for all prompts.

        Returns structured data for reporting.
        """
        evolution_map: Dict[str, Any] = {
            "prompts": {},
            "statistics": {
                "total_prompts": 0,
                "evolved_prompts": 0,
                "avg_fitness": 0.0,
            },
        }

        total_fitness = 0.0

        with self._lock:
            for prompt_id, genome in self._prompts.items():
                state = self._evolution_engine.get_evolution_state(prompt_id)

                evolution_map["prompts"][prompt_id] = {
                    "category": genome["category"],
                    "version": genome["version"],
                    "fitness": genome["fitness"],
                    "generations": state.current_generation if state else 0,
                    "metrics_summary": {
                        "leak_prob": genome["metrics"]["leak_probability"],
                        "consistency": genome["metrics"]["consistency_score"],
                    },
                }

                total_fitness += genome["fitness"]
                evolution_map["statistics"]["total_prompts"] += 1

                if genome["version"] > 0:
                    evolution_map["statistics"]["evolved_prompts"] += 1

            if evolution_map["statistics"]["total_prompts"] > 0:
                evolution_map["statistics"]["avg_fitness"] = (
                    total_fitness / evolution_map["statistics"]["total_prompts"]
                )

        return evolution_map


# =============================================================================
# SINGLETON & HELPER FUNCTIONS
# =============================================================================

_evolution_instance: Optional[PromptEvolutionEngine] = None
_evolution_lock = threading.Lock()


def get_prompt_evolution_engine(seed: Optional[int] = None) -> PromptEvolutionEngine:
    """Get or create singleton prompt evolution engine."""
    global _evolution_instance

    if _evolution_instance is None:
        with _evolution_lock:
            if _evolution_instance is None:
                _evolution_instance = PromptEvolutionEngine(seed)

    return _evolution_instance


def register_prompt_for_evolution(
    prompt_id: str,
    content: str,
    category: str = "analysis",
) -> Dict[str, Any]:
    """
    Register a prompt for evolution.

    Convenience function for external use.
    """
    engine = get_prompt_evolution_engine()
    genome = engine.register_prompt(prompt_id, content, category)
    return {
        "genome_id": genome["genome_id"],
        "prompt_id": prompt_id,
        "category": genome["category"],
        "initial_fitness": genome["fitness"],
    }


def evolve_prompt(
    prompt_id: str,
    feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evolve a prompt.

    Convenience function for external use.
    """
    engine = get_prompt_evolution_engine()
    return engine.evolve_prompt(prompt_id, feedback)


def get_evolved_prompt(prompt_id: str) -> Optional[str]:
    """
    Get the current best version of a prompt.

    Convenience function for external use.
    """
    engine = get_prompt_evolution_engine()
    return engine.get_prompt(prompt_id)


def update_prompt_metrics(
    prompt_id: str,
    metrics: PromptMetrics,
) -> None:
    """
    Update performance metrics for a prompt.

    Convenience function for external use.
    """
    engine = get_prompt_evolution_engine()
    engine.update_feedback(prompt_id, metrics)


def get_prompt_evolution_map() -> Dict[str, Any]:
    """
    Get evolution map for all prompts.

    Convenience function for external use.
    """
    engine = get_prompt_evolution_engine()
    return engine.get_prompt_evolution_map()


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "PromptCategory",
    "MutationType",
    "FitnessMetric",
    "EvolutionPhase",
    # Classes
    "PromptEvolutionEngine",
    "EvolutionEngine",
    "MutationEngine",
    "FitnessEvaluator",
    # Data classes
    "MutationRecord",
    "EvaluationRecord",
    "EvolutionState",
    # Type definitions
    "PromptMetrics",
    "EvolutionResult",
    "PromptGenome",
    # Functions
    "get_prompt_evolution_engine",
    "register_prompt_for_evolution",
    "evolve_prompt",
    "get_evolved_prompt",
    "update_prompt_metrics",
    "get_prompt_evolution_map",
    # Constants
    "EVOLUTION_CONFIG",
    "FITNESS_WEIGHTS",
    "SYNONYMS",
]
