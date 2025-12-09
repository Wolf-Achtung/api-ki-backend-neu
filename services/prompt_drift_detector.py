# -*- coding: utf-8 -*-
"""
Sprint G17.6-B: Prompt Drift Detector

Detects various types of drift between prompt versions:
- Structural Drift: New/removed H2/H3 structures, missing sections
- Instruction Drift: Persona guards, anti-redundancy rules, segment rules
- Semantic Drift: Tone changes from tuning/rewrite
- Fallback Risk Drift: Changes that may trigger more fallbacks

Version: 1.0.0 (Sprint G17.6)
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

PROMPT_GOVERNANCE_ENABLED = os.environ.get("PROMPT_GOVERNANCE_ENABLED", "1") == "1"

# Drift thresholds (imported from checkpoint but defined here too for independence)
PROMPT_DRIFT_THRESHOLD_LOW = int(os.environ.get("PROMPT_DRIFT_THRESHOLD_LOW", "15"))
PROMPT_DRIFT_THRESHOLD_MEDIUM = int(os.environ.get("PROMPT_DRIFT_THRESHOLD_MEDIUM", "30"))
PROMPT_DRIFT_THRESHOLD_HIGH = int(os.environ.get("PROMPT_DRIFT_THRESHOLD_HIGH", "50"))
PROMPT_DRIFT_THRESHOLD_CRITICAL = int(os.environ.get("PROMPT_DRIFT_THRESHOLD_CRITICAL", "70"))


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class DriftAnalysis:
    """Complete drift analysis result."""
    prompt_file: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Individual drift scores (0-100 each)
    structural_drift_score: int = 0
    instruction_drift_score: int = 0
    semantic_drift_score: int = 0
    fallback_risk_score: int = 0

    # Combined score
    total_drift_score: int = 0
    drift_category: str = "MINIMAL"  # MINIMAL, LOW, MEDIUM, HIGH, CRITICAL

    # Details
    structural_changes: List[str] = field(default_factory=list)
    instruction_changes: List[str] = field(default_factory=list)
    semantic_changes: List[str] = field(default_factory=list)
    fallback_risks: List[str] = field(default_factory=list)

    # Flags
    requires_manual_review: bool = False
    auto_stop: bool = False


@dataclass
class StructuralDriftResult:
    """Result of structural drift analysis."""
    score: int = 0
    changes: List[str] = field(default_factory=list)

    # Detailed changes
    added_h1: List[str] = field(default_factory=list)
    removed_h1: List[str] = field(default_factory=list)
    added_h2: List[str] = field(default_factory=list)
    removed_h2: List[str] = field(default_factory=list)
    added_h3: List[str] = field(default_factory=list)
    removed_h3: List[str] = field(default_factory=list)
    block_changes: int = 0


@dataclass
class InstructionDriftResult:
    """Result of instruction drift analysis."""
    score: int = 0
    changes: List[str] = field(default_factory=list)

    # Detailed changes
    persona_guard_changes: List[str] = field(default_factory=list)
    anti_redundancy_changes: List[str] = field(default_factory=list)
    segment_rule_changes: List[str] = field(default_factory=list)
    length_constraint_changes: List[str] = field(default_factory=list)


@dataclass
class SemanticDriftResult:
    """Result of semantic drift analysis."""
    score: int = 0
    changes: List[str] = field(default_factory=list)

    # Tone indicators
    formality_shift: str = "none"  # more_formal, less_formal, none
    directive_shift: str = "none"  # more_directive, less_directive, none
    complexity_shift: str = "none"  # more_complex, less_complex, none


@dataclass
class FallbackRiskResult:
    """Result of fallback risk analysis."""
    score: int = 0
    risks: List[str] = field(default_factory=list)

    # Risk categories
    stricter_constraints: int = 0
    removed_fallbacks: int = 0
    narrower_conditions: int = 0


# =============================================================================
# STRUCTURAL DRIFT DETECTION
# =============================================================================

def detect_structural_drift(
    prompt_before: str,
    prompt_after: str,
) -> StructuralDriftResult:
    """
    Detect structural drift between two prompt versions.

    Analyzes:
    - H1/H2/H3 header changes
    - Block additions/removals
    - Section reordering

    Args:
        prompt_before: Previous prompt content
        prompt_after: New prompt content

    Returns:
        StructuralDriftResult with score and changes
    """
    result = StructuralDriftResult()

    # Extract headers
    def extract_headers(content: str) -> Dict[str, List[str]]:
        headers: Dict[str, List[str]] = {"h1": [], "h2": [], "h3": []}
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("### "):
                headers["h3"].append(line[4:].strip())
            elif line.startswith("## "):
                headers["h2"].append(line[3:].strip())
            elif line.startswith("# "):
                headers["h1"].append(line[2:].strip())
        return headers

    before_headers = extract_headers(prompt_before)
    after_headers = extract_headers(prompt_after)

    # Compare H1
    before_h1 = set(before_headers["h1"])
    after_h1 = set(after_headers["h1"])
    result.added_h1 = list(after_h1 - before_h1)
    result.removed_h1 = list(before_h1 - after_h1)

    # Compare H2
    before_h2 = set(before_headers["h2"])
    after_h2 = set(after_headers["h2"])
    result.added_h2 = list(after_h2 - before_h2)
    result.removed_h2 = list(before_h2 - after_h2)

    # Compare H3
    before_h3 = set(before_headers["h3"])
    after_h3 = set(after_headers["h3"])
    result.added_h3 = list(after_h3 - before_h3)
    result.removed_h3 = list(before_h3 - after_h3)

    # Count block changes (code blocks, lists, etc.)
    before_blocks = len(re.findall(r"```[\s\S]*?```", prompt_before))
    after_blocks = len(re.findall(r"```[\s\S]*?```", prompt_after))
    result.block_changes = abs(after_blocks - before_blocks)

    # Calculate score
    score = 0
    score += len(result.added_h1) * 10 + len(result.removed_h1) * 15  # H1 changes are significant
    score += len(result.added_h2) * 5 + len(result.removed_h2) * 8
    score += len(result.added_h3) * 3 + len(result.removed_h3) * 4
    score += result.block_changes * 2

    result.score = min(score, 100)

    # Collect changes
    if result.added_h1:
        result.changes.append(f"Added H1 sections: {', '.join(result.added_h1)}")
    if result.removed_h1:
        result.changes.append(f"Removed H1 sections: {', '.join(result.removed_h1)}")
    if result.added_h2:
        result.changes.append(f"Added H2 sections: {', '.join(result.added_h2)}")
    if result.removed_h2:
        result.changes.append(f"Removed H2 sections: {', '.join(result.removed_h2)}")
    if result.added_h3:
        result.changes.append(f"Added H3 sections: {', '.join(result.added_h3)}")
    if result.removed_h3:
        result.changes.append(f"Removed H3 sections: {', '.join(result.removed_h3)}")
    if result.block_changes > 0:
        result.changes.append(f"Code block changes: {result.block_changes}")

    return result


# =============================================================================
# INSTRUCTION DRIFT DETECTION
# =============================================================================

def detect_instruction_drift(
    prompt_before: str,
    prompt_after: str,
) -> InstructionDriftResult:
    """
    Detect instruction drift between two prompt versions.

    Analyzes changes in:
    - Persona Guards
    - Anti-Redundancy Rules
    - Segment Rules
    - Length Constraints

    Args:
        prompt_before: Previous prompt content
        prompt_after: New prompt content

    Returns:
        InstructionDriftResult with score and changes
    """
    result = InstructionDriftResult()

    # Persona guard patterns
    persona_patterns = [
        r"\[PERSONA[:\s]*.+?\]",
        r"{{#if.*persona.*}}",
        r"(?:solo|team|kmu)[\s-](?:anrede|persona|guard)",
        r"(?:du-form|sie-form|anrede)",
    ]

    # Anti-redundancy patterns
    redundancy_patterns = [
        r"\[(?:NO[_-])?REDUNDAN(?:CY|Z)[:\s]*.+?\]",
        r"(?:vermeide|avoid)\s+(?:wiederholung|redundanz)",
        r"(?:nicht|kein).*wiederholen",
    ]

    # Segment rule patterns
    segment_patterns = [
        r"\[SEGMENT[:\s]*.+?\]",
        r"{{#if.*(?:branche|size|risk).*}}",
        r"(?:branch|segment|size)[\s-]specific",
    ]

    # Length constraint patterns
    length_patterns = [
        r"(?:mindestens|minimum|min)\s+\d+\s*(?:wörter|words)",
        r"(?:maximal|maximum|max)\s+\d+\s*(?:wörter|words)",
        r"SECTION_MIN_WORDS",
        r"\[LENGTH[:\s]*.+?\]",
    ]

    def find_all_patterns(content: str, patterns: List[str]) -> List[str]:
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            matches.extend([m[:100] if isinstance(m, str) else str(m)[:100] for m in found])
        return matches

    # Find instructions in both versions
    before_persona = set(find_all_patterns(prompt_before, persona_patterns))
    after_persona = set(find_all_patterns(prompt_after, persona_patterns))

    before_redundancy = set(find_all_patterns(prompt_before, redundancy_patterns))
    after_redundancy = set(find_all_patterns(prompt_after, redundancy_patterns))

    before_segment = set(find_all_patterns(prompt_before, segment_patterns))
    after_segment = set(find_all_patterns(prompt_after, segment_patterns))

    before_length = set(find_all_patterns(prompt_before, length_patterns))
    after_length = set(find_all_patterns(prompt_after, length_patterns))

    # Calculate changes
    result.persona_guard_changes = list(
        (after_persona - before_persona) | (before_persona - after_persona)
    )
    result.anti_redundancy_changes = list(
        (after_redundancy - before_redundancy) | (before_redundancy - after_redundancy)
    )
    result.segment_rule_changes = list(
        (after_segment - before_segment) | (before_segment - after_segment)
    )
    result.length_constraint_changes = list(
        (after_length - before_length) | (before_length - after_length)
    )

    # Calculate score
    score = 0
    score += len(result.persona_guard_changes) * 8
    score += len(result.anti_redundancy_changes) * 5
    score += len(result.segment_rule_changes) * 6
    score += len(result.length_constraint_changes) * 4

    result.score = min(score, 100)

    # Collect changes
    if result.persona_guard_changes:
        result.changes.append(f"Persona guard changes: {len(result.persona_guard_changes)}")
    if result.anti_redundancy_changes:
        result.changes.append(f"Anti-redundancy rule changes: {len(result.anti_redundancy_changes)}")
    if result.segment_rule_changes:
        result.changes.append(f"Segment rule changes: {len(result.segment_rule_changes)}")
    if result.length_constraint_changes:
        result.changes.append(f"Length constraint changes: {len(result.length_constraint_changes)}")

    return result


# =============================================================================
# SEMANTIC DRIFT DETECTION
# =============================================================================

def detect_semantic_drift(
    prompt_before: str,
    prompt_after: str,
    llm_embedder: Optional[Any] = None,
) -> SemanticDriftResult:
    """
    Detect semantic/tone drift between two prompt versions.

    Analyzes:
    - Formality shift
    - Directive tone shift
    - Complexity shift

    Note: LLM embedder is optional - if not provided, uses heuristic analysis.

    Args:
        prompt_before: Previous prompt content
        prompt_after: New prompt content
        llm_embedder: Optional LLM embedder for semantic comparison

    Returns:
        SemanticDriftResult with score and changes
    """
    result = SemanticDriftResult()

    # Formality indicators
    formal_words = ["Sie", "Ihnen", "bitte", "geehrte", "höflich", "freundlich"]
    informal_words = ["du", "dir", "dein", "mal", "einfach", "kurz"]

    before_formal = sum(1 for w in formal_words if w in prompt_before)
    after_formal = sum(1 for w in formal_words if w in prompt_after)
    before_informal = sum(1 for w in informal_words if w.lower() in prompt_before.lower())
    after_informal = sum(1 for w in informal_words if w.lower() in prompt_after.lower())

    formality_before = before_formal - before_informal
    formality_after = after_formal - after_informal

    if formality_after > formality_before + 2:
        result.formality_shift = "more_formal"
        result.changes.append("Tone shift: More formal language detected")
    elif formality_after < formality_before - 2:
        result.formality_shift = "less_formal"
        result.changes.append("Tone shift: Less formal language detected")

    # Directive indicators
    directive_words = ["muss", "müssen", "immer", "niemals", "zwingend", "unbedingt", "stets"]
    suggestive_words = ["könnte", "sollte", "empfehlen", "vorschlagen", "optional", "möglich"]

    before_directive = sum(1 for w in directive_words if w.lower() in prompt_before.lower())
    after_directive = sum(1 for w in directive_words if w.lower() in prompt_after.lower())
    before_suggestive = sum(1 for w in suggestive_words if w.lower() in prompt_before.lower())
    after_suggestive = sum(1 for w in suggestive_words if w.lower() in prompt_after.lower())

    directive_before = before_directive - before_suggestive
    directive_after = after_directive - after_suggestive

    if directive_after > directive_before + 2:
        result.directive_shift = "more_directive"
        result.changes.append("Tone shift: More directive language detected")
    elif directive_after < directive_before - 2:
        result.directive_shift = "less_directive"
        result.changes.append("Tone shift: Less directive language detected")

    # Complexity indicators (avg sentence length, technical terms)
    def avg_sentence_length(text: str) -> float:
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0
        return sum(len(s.split()) for s in sentences) / len(sentences)

    before_complexity = avg_sentence_length(prompt_before)
    after_complexity = avg_sentence_length(prompt_after)

    if after_complexity > before_complexity * 1.3:
        result.complexity_shift = "more_complex"
        result.changes.append("Complexity shift: Longer sentences detected")
    elif after_complexity < before_complexity * 0.7:
        result.complexity_shift = "less_complex"
        result.changes.append("Complexity shift: Shorter sentences detected")

    # Calculate score
    score = 0
    if result.formality_shift != "none":
        score += 15
    if result.directive_shift != "none":
        score += 20
    if result.complexity_shift != "none":
        score += 10

    result.score = min(score, 100)

    return result


# =============================================================================
# FALLBACK RISK DETECTION
# =============================================================================

def detect_fallback_risk(
    prompt_before: str,
    prompt_after: str,
) -> FallbackRiskResult:
    """
    Detect changes that may trigger more fallbacks.

    Analyzes:
    - Stricter constraints
    - Removed fallback paths
    - Narrower conditions

    Args:
        prompt_before: Previous prompt content
        prompt_after: New prompt content

    Returns:
        FallbackRiskResult with score and risks
    """
    result = FallbackRiskResult()

    # Constraint patterns
    strict_patterns = [
        r"(?:muss|müssen|zwingend|unbedingt|immer)",
        r"(?:niemals|nie|keinesfalls|auf keinen fall)",
        r"(?:genau|exakt|präzise)\s+\d+",
    ]

    fallback_patterns = [
        r"{{else}}",
        r"(?:falls nicht|wenn nicht|andernfalls|sonst)",
        r"(?:default|fallback|standard)",
        r"\[FALLBACK[:\s]*.+?\]",
    ]

    condition_patterns = [
        r"{{#if\s+.+?}}",
        r"(?:wenn|falls|sofern)\s+.+?(?:dann|:)",
    ]

    def count_patterns(content: str, patterns: List[str]) -> int:
        total = 0
        for pattern in patterns:
            total += len(re.findall(pattern, content, re.IGNORECASE))
        return total

    # Count patterns
    before_strict = count_patterns(prompt_before, strict_patterns)
    after_strict = count_patterns(prompt_after, strict_patterns)

    before_fallback = count_patterns(prompt_before, fallback_patterns)
    after_fallback = count_patterns(prompt_after, fallback_patterns)

    before_conditions = count_patterns(prompt_before, condition_patterns)
    after_conditions = count_patterns(prompt_after, condition_patterns)

    # Analyze changes
    if after_strict > before_strict:
        result.stricter_constraints = after_strict - before_strict
        result.risks.append(f"Added {result.stricter_constraints} stricter constraints")

    if after_fallback < before_fallback:
        result.removed_fallbacks = before_fallback - after_fallback
        result.risks.append(f"Removed {result.removed_fallbacks} fallback paths")

    if after_conditions > before_conditions * 1.5:
        result.narrower_conditions = after_conditions - before_conditions
        result.risks.append(f"Added {result.narrower_conditions} additional conditions")

    # Calculate score
    score = 0
    score += result.stricter_constraints * 8
    score += result.removed_fallbacks * 12
    score += result.narrower_conditions * 5

    result.score = min(score, 100)

    return result


# =============================================================================
# COMBINED DRIFT ANALYSIS
# =============================================================================

def analyze_drift(
    prompt_file: str,
    prompt_before: str,
    prompt_after: str,
    llm_embedder: Optional[Any] = None,
) -> DriftAnalysis:
    """
    Perform complete drift analysis between two prompt versions.

    Args:
        prompt_file: Name/path of the prompt file
        prompt_before: Previous prompt content
        prompt_after: New prompt content
        llm_embedder: Optional LLM embedder for semantic analysis

    Returns:
        Complete DriftAnalysis with all drift types
    """
    analysis = DriftAnalysis(prompt_file=prompt_file)

    # Run all drift detections
    structural = detect_structural_drift(prompt_before, prompt_after)
    instruction = detect_instruction_drift(prompt_before, prompt_after)
    semantic = detect_semantic_drift(prompt_before, prompt_after, llm_embedder)
    fallback = detect_fallback_risk(prompt_before, prompt_after)

    # Collect scores
    analysis.structural_drift_score = structural.score
    analysis.instruction_drift_score = instruction.score
    analysis.semantic_drift_score = semantic.score
    analysis.fallback_risk_score = fallback.score

    # Collect changes
    analysis.structural_changes = structural.changes
    analysis.instruction_changes = instruction.changes
    analysis.semantic_changes = semantic.changes
    analysis.fallback_risks = fallback.risks

    # Calculate total drift score (weighted average)
    total = (
        structural.score * 0.35 +
        instruction.score * 0.30 +
        semantic.score * 0.15 +
        fallback.score * 0.20
    )
    analysis.total_drift_score = min(int(total), 100)

    # Categorize drift
    if analysis.total_drift_score >= PROMPT_DRIFT_THRESHOLD_CRITICAL:
        analysis.drift_category = "CRITICAL"
        analysis.auto_stop = True
        analysis.requires_manual_review = True
    elif analysis.total_drift_score >= PROMPT_DRIFT_THRESHOLD_HIGH:
        analysis.drift_category = "HIGH"
        analysis.requires_manual_review = True
    elif analysis.total_drift_score >= PROMPT_DRIFT_THRESHOLD_MEDIUM:
        analysis.drift_category = "MEDIUM"
    elif analysis.total_drift_score >= PROMPT_DRIFT_THRESHOLD_LOW:
        analysis.drift_category = "LOW"
    else:
        analysis.drift_category = "MINIMAL"

    return analysis


def is_critical_drift(analysis: DriftAnalysis) -> bool:
    """Check if drift analysis indicates critical drift requiring auto-stop."""
    return analysis.drift_category == "CRITICAL" or analysis.auto_stop


def get_drift_summary(analysis: DriftAnalysis) -> Dict[str, Any]:
    """Get a summary dict of drift analysis for reporting."""
    return {
        "prompt_file": analysis.prompt_file,
        "total_drift_score": analysis.total_drift_score,
        "drift_category": analysis.drift_category,
        "structural_score": analysis.structural_drift_score,
        "instruction_score": analysis.instruction_drift_score,
        "semantic_score": analysis.semantic_drift_score,
        "fallback_risk_score": analysis.fallback_risk_score,
        "requires_manual_review": analysis.requires_manual_review,
        "auto_stop": analysis.auto_stop,
        "change_count": (
            len(analysis.structural_changes) +
            len(analysis.instruction_changes) +
            len(analysis.semantic_changes) +
            len(analysis.fallback_risks)
        ),
    }
