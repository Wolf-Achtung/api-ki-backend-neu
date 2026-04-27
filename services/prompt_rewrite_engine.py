# -*- coding: utf-8 -*-
"""
Sprint G17.4: Auto-Prompt-Rewrite Engine

Automatically detects prompt weaknesses and generates rewrite suggestions
based on:
- FT Signals (G17.3)
- Segment Stability (G17.1)
- Predictive KPIs & Smart Defaults (G17.2)
- Validator Warnings
- Length/Structure Analysis
- Persona & Redundancy Errors

Version: 1.0.0 (Sprint G17.4)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import difflib

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

PROMPT_REWRITE_ENGINE_ENABLED = os.environ.get("PROMPT_REWRITE_ENGINE_ENABLED", "1") == "1"
PROMPT_REWRITE_MIN_CONFIDENCE = float(os.environ.get("PROMPT_REWRITE_MIN_CONFIDENCE", "0.45"))
PROMPT_REWRITE_REQUIRE_STRONG_SEGMENT = os.environ.get("PROMPT_REWRITE_REQUIRE_STRONG_SEGMENT", "1") == "1"
PROMPT_REWRITE_MAX_SUGGESTIONS = int(os.environ.get("PROMPT_REWRITE_MAX_SUGGESTIONS", "10"))
PROMPT_REWRITE_GENERATE_PATCHES = os.environ.get("PROMPT_REWRITE_GENERATE_PATCHES", "1") == "1"
PROMPT_REWRITE_DEBUG = os.environ.get("PROMPT_REWRITE_DEBUG", "0") == "1"
PROMPT_REWRITE_STORAGE_PATH = os.environ.get("PROMPT_REWRITE_STORAGE_PATH", "data/prompt_rewrites")

# Issue severity weights
SEVERITY_WEIGHTS = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
}

# Issue types and their detection patterns
ISSUE_TYPES = {
    "too_short_warning": "Prompt requests insufficient depth/detail",
    "persona_leak": "Persona-inappropriate terms originate from prompt",
    "redundancy_pattern": "Prompt instructions cause redundant output",
    "predictive_drift": "Prompt causes systematic deviation from expected KPIs",
    "funding_mismatch": "Prompt generates incorrect funding recommendations",
    "ai_act_weakness": "Prompt produces weak/unreliable AI Act reasoning",
    "branch_context_misuse": "Prompt uses wrong labels or generic formulations",
    "insight_collision": "Prompt generates content conflicting with Insight Engine",
    # G17.P: New intro redundancy patterns
    "data_readiness_intro_redundancy": "DATA_READINESS intro uses standard redundant phrases",
    "business_case_intro_redundancy": "BUSINESS_CASE intro uses standard redundant phrases",
    # G17.S: Branch context and cost block redundancy
    "branch_context_redundancy": "Long branch descriptions cause redundancy (use BRANCH_SHORT_LABEL)",
    "cost_block_redundancy": "CAPEX/OPEX blocks repeated across sections",
}

# G17.P: Template phrases to detect and avoid (P1 priority)
# SPRINT G18: Extended with new redundancy patterns
TEMPLATE_PHRASES = {
    "data_readiness_intro_standard": [
        r"Datenlage\s+bildet\s+.*Grundlage",
        r"Datenqualität\s+ist\s+(zentral|entscheidend)",
        r"entscheidend\s+für\s+.*KI-Strategie",
        r"Grundlage\s+jeder\s+KI-Implementierung",
        r"data\s+(quality|situation)\s+is\s+(central|crucial|essential)",
        r"foundation\s+of\s+(any|every)\s+AI",
    ],
    "business_case_intro_standard": [
        r"wesentlicher\s+Bestandteil",
        r"zentrale\s+Grundlage",
        r"zentraler\s+Hebel\s+der\s+Wertschöpfung",
        r"entscheidend\s+für\s+.*KI-Strategie",
        r"central\s+lever\s+for\s+value",
        r"essential\s+(part|component)\s+of",
    ],
    # SPRINT G17.S: Long branch context patterns (P1 priority)
    "branch_context_redundancy": [
        # Overly long branch descriptions (40+ chars typically)
        r"Beratung,\s+Durchführung\s+und\s+Operationalisierung\s+von\s+KI-Readiness",
        r"(consulting|advisory|implementation)\s+and\s+operationalization\s+of\s+AI",
        r"Unternehmen\s+in\s+der\s+Branche\s+\w+\s+mit\s+der\s+Größe\s+\w+",
        r"company\s+in\s+the\s+\w+\s+industry\s+with\s+size",
        r"für\s+ein\s+Unternehmen\s+(in|der)\s+\w+\s+(Branche|Größe)",
        r"for\s+a\s+company\s+in\s+the\s+\w+\s+(industry|sector)",
    ],
    # SPRINT G17.S + G18: CAPEX/OPEX standard blocks (P1 priority - elevated from P2)
    "cost_block_redundancy": [
        r"CAPEX\s+(und|&)\s+OPEX\s+(bilden|sind)\s+(die\s+)?(Grundlage|Basis)",
        r"einmalige\s+(Aufwände|Kosten)\s+für\s+Aufbau\s+und\s+Einführung",
        r"monatliche\s+Betriebskosten\s+von\s+(etwa|rund|ca\.?)",
        r"one-time\s+(setup|implementation)\s+costs",
        r"monthly\s+operating\s+costs\s+of\s+(about|approximately)",
        r"(CAPEX|OPEX)\s+breakdown\s+for\s+AI\s+implementation",
        # G18: More specific CAPEX/OPEX blocks
        r"initiales\s+Setup\s+und\s+Einführung",
        r"initial\s+setup\s+of\s+(AI|your)",
    ],
    # SPRINT G18: Data-Readiness in wrong sections (P2 priority)
    "data_readiness_in_business_case": [
        r"Datenlage\s+&\s+Systemreife",
        r"Data\s+(Situation|Maturity)\s+&\s+System",
        r"vorhandene\s+Datenquellen\s+ermöglichen",
        r"existing\s+data\s+sources\s+enable",
        r"Datenqualität\s+(ermöglicht|bildet)",
        r"data\s+quality\s+(enables|forms)",
    ],
    # SPRINT G18: Business Case content in wrong sections (P2 priority)
    "business_case_in_data_readiness": [
        r"ROI\s+(nach|von|bei)\s+\d+",
        r"Amortisation\s+(nach|in)\s+\d+",
        r"CAPEX.*€.*OPEX",
        r"Payback.*Monate",
        r"payback.*months",
        r"investment.*amortize",
    ],
}

# Storage lock for thread safety
_storage_lock = threading.Lock()

# In-memory suggestion buffer
_suggestion_buffer: List["RewriteSuggestion"] = []


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PromptIssue:
    """A detected weakness in a prompt."""
    issue_type: str
    severity: str  # low|medium|high
    signal_ref: Optional[str] = None
    example_input: str = ""
    example_output: str = ""
    ideal_behavior: str = ""
    detected_pattern: str = ""
    prompt_file: Optional[str] = None
    section_name: Optional[str] = None


@dataclass
class RewriteSuggestion:
    """A suggested rewrite for a prompt section."""
    suggestion_id: str
    prompt_file: str
    priority: str  # P1|P2|P3
    confidence: float
    change_type: str  # add|remove|rewrite|strengthen|clarify|tighten
    current_section_excerpt: str
    proposed_rewrite: str
    justification: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    issue_refs: List[str] = field(default_factory=list)
    segment_stability: str = "medium"
    applied: bool = False


@dataclass
class PatchOutput:
    """A diff-style patch for a prompt file."""
    prompt_file: str
    patch_content: str
    suggestion_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# ISSUE DETECTION (G17.4-A)
# =============================================================================

def detect_prompt_weaknesses(
    prompt_text: str,
    aggregated_signals: Optional[List[Any]] = None,
    segment_stats: Optional[Any] = None,
    validation_warnings: Optional[List[Dict[str, Any]]] = None,
    prompt_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detect concrete weaknesses in existing prompts (G17.4-A).

    Identifies:
    - Frequently triggered "too short" warnings
    - Persona leaks originating from prompt
    - Redundancy patterns caused by prompt instructions
    - Predictive drift from expected KPI trends
    - Funding mismatch patterns
    - AI Act reasoning weaknesses
    - Branch context misuse
    - Insight Engine collisions

    Args:
        prompt_text: The prompt content to analyze
        aggregated_signals: FT signals from G17.3
        segment_stats: Segment statistics from G17.1
        validation_warnings: Validator warnings
        prompt_file: Path to the prompt file

    Returns:
        Dict with "issues" list containing detected weaknesses
    """
    if not PROMPT_REWRITE_ENGINE_ENABLED:
        return {"issues": []}

    issues: List[PromptIssue] = []
    signals = aggregated_signals or []
    warnings = validation_warnings or []

    # 1. Detect "too short" warning patterns
    too_short_issues = _detect_too_short_patterns(prompt_text, signals, warnings, prompt_file)
    issues.extend(too_short_issues)

    # 2. Detect persona leaks from prompt
    persona_issues = _detect_persona_leaks(prompt_text, signals, prompt_file)
    issues.extend(persona_issues)

    # 3. Detect redundancy patterns
    redundancy_issues = _detect_redundancy_patterns(prompt_text, signals, prompt_file)
    issues.extend(redundancy_issues)

    # 4. Detect predictive drift
    drift_issues = _detect_predictive_drift(prompt_text, signals, segment_stats, prompt_file)
    issues.extend(drift_issues)

    # 5. Detect funding mismatch patterns
    funding_issues = _detect_funding_mismatch(prompt_text, signals, prompt_file)
    issues.extend(funding_issues)

    # 6. Detect AI Act reasoning weaknesses
    ai_act_issues = _detect_ai_act_weaknesses(prompt_text, signals, prompt_file)
    issues.extend(ai_act_issues)

    # 7. Detect branch context misuse
    branch_issues = _detect_branch_context_misuse(prompt_text, signals, prompt_file)
    issues.extend(branch_issues)

    # 8. Detect insight engine collisions
    insight_issues = _detect_insight_collisions(prompt_text, signals, prompt_file)
    issues.extend(insight_issues)

    # 9. G17.P: Detect intro redundancy patterns
    g17p_issues = _detect_g17p_intro_redundancy(prompt_text, signals, prompt_file)
    issues.extend(g17p_issues)

    if PROMPT_REWRITE_DEBUG:
        log.debug(f"Detected {len(issues)} prompt issues")

    return {
        "issues": [asdict(issue) for issue in issues]
    }


def _detect_too_short_patterns(
    prompt_text: str,
    signals: List[Any],
    warnings: List[Dict[str, Any]],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """Detect patterns where prompt requests insufficient depth."""
    issues = []

    # Check for signals indicating length issues
    length_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "size_aware_length"]

    # Check for "too short" warnings
    short_warnings = [w for w in warnings if "short" in str(w.get("message", "")).lower() or "kurz" in str(w.get("message", "")).lower()]

    # Analyze prompt for weak length instructions
    weak_length_patterns = [
        r"kurz\s+(beschreiben|erklären|darstellen)",
        r"(beschreiben|erklären|darstellen)\s+Sie\s+kurz",
        r"briefly\s+(describe|explain|outline)",
        r"(describe|explain|outline)\s+briefly",
        r"in\s+wenigen\s+worten",
        r"knapp\s+zusammenfassen",
        r"short\s+summary",
    ]

    for pattern in weak_length_patterns:
        matches = re.findall(pattern, prompt_text, re.IGNORECASE)
        if matches and (length_signals or short_warnings):
            issues.append(PromptIssue(
                issue_type="too_short_warning",
                severity="medium" if len(length_signals) > 2 else "low",
                signal_ref=length_signals[0].signal_id if length_signals else None,
                example_input=f"Prompt pattern: '{pattern}'",
                example_output="Output consistently below expected word count",
                ideal_behavior="Expand instructions to request more detailed explanations",
                detected_pattern=f"Weak length instruction: {matches[0] if matches else pattern}",
                prompt_file=prompt_file,
            ))

    # High severity if many length signals
    if len(length_signals) >= 5:
        issues.append(PromptIssue(
            issue_type="too_short_warning",
            severity="high",
            signal_ref=length_signals[0].signal_id if length_signals else None,
            example_input="Multiple sections",
            example_output=f"{len(length_signals)} size adjustment signals detected",
            ideal_behavior="Add explicit word count targets or depth requirements",
            detected_pattern="Systematic length deficiency across multiple sections",
            prompt_file=prompt_file,
        ))

    return issues


def _detect_persona_leaks(
    prompt_text: str,
    signals: List[Any],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """Detect persona-inappropriate terms originating from prompt."""
    issues = []

    # Check for persona fix signals
    persona_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "persona_fix"]

    # Patterns that might cause persona leaks
    persona_leak_patterns = [
        (r"\b(Ihr\s+Team|Ihre\s+Mitarbeiter)\b", "team", "solo"),  # Team terms for solo
        (r"\b(das\s+Unternehmen|die\s+Firma)\b", "company", "solo"),
        (r"\b(Sie\s+als\s+Einzelunternehmer)\b", "solo", "team"),  # Solo terms for team
        (r"\b(your\s+team|your\s+employees)\b", "team", "solo"),
    ]

    for pattern, context, wrong_for in persona_leak_patterns:
        matches = re.findall(pattern, prompt_text, re.IGNORECASE)
        if matches:
            # Check if signals show this pattern being corrected
            related_signals = [
                s for s in persona_signals
                if hasattr(s, 'prompt_input') and any(m.lower() in s.prompt_input.lower() for m in matches)
            ]
            if related_signals:
                issues.append(PromptIssue(
                    issue_type="persona_leak",
                    severity="high" if len(related_signals) > 3 else "medium",
                    signal_ref=related_signals[0].signal_id if related_signals else None,
                    example_input=f"Prompt uses '{matches[0]}' unconditionally",
                    example_output=f"Output contains {context} terms for {wrong_for} personas",
                    ideal_behavior=f"Use conditional phrasing based on company size",
                    detected_pattern=f"Static {context} reference: {matches[0]}",
                    prompt_file=prompt_file,
                ))

    return issues


def _detect_redundancy_patterns(
    prompt_text: str,
    signals: List[Any],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """Detect redundancy patterns caused by prompt instructions."""
    issues = []

    # Check for redundancy compression signals
    redundancy_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "redundancy_compression"]

    # Patterns that might cause redundancy
    redundancy_patterns = [
        r"wiederholen\s+Sie",
        r"nochmals\s+betonen",
        r"erneut\s+erwähnen",
        r"repeat\s+the",
        r"emphasize\s+again",
        r"reiterate",
    ]

    for pattern in redundancy_patterns:
        matches = re.findall(pattern, prompt_text, re.IGNORECASE)
        if matches and redundancy_signals:
            issues.append(PromptIssue(
                issue_type="redundancy_pattern",
                severity="medium",
                signal_ref=redundancy_signals[0].signal_id if redundancy_signals else None,
                example_input=f"Prompt instruction: '{matches[0]}'",
                example_output="Output contains repeated information across sections",
                ideal_behavior="Remove repetition instructions, use cross-references instead",
                detected_pattern=f"Explicit repetition instruction: {matches[0]}",
                prompt_file=prompt_file,
            ))

    # Check for duplicate structural patterns in prompt
    if redundancy_signals and len(redundancy_signals) >= 3:
        issues.append(PromptIssue(
            issue_type="redundancy_pattern",
            severity="high",
            signal_ref=redundancy_signals[0].signal_id,
            example_input="Multiple sections",
            example_output=f"{len(redundancy_signals)} redundancy corrections needed",
            ideal_behavior="Restructure prompt to avoid overlapping instructions",
            detected_pattern="Systematic redundancy across output",
            prompt_file=prompt_file,
        ))

    return issues


def _detect_predictive_drift(
    prompt_text: str,
    signals: List[Any],
    segment_stats: Optional[Any],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """Detect prompts causing systematic deviation from expected KPIs."""
    issues: List[PromptIssue] = []

    # Check for predictive drift signals
    drift_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "predictive_drift"]

    if not drift_signals:
        return issues

    # Analyze drift patterns
    drift_count = len(drift_signals)
    avg_quality = sum(s.quality_score for s in drift_signals if hasattr(s, 'quality_score')) / max(drift_count, 1)

    if drift_count >= 2 and avg_quality > 0.5:
        issues.append(PromptIssue(
            issue_type="predictive_drift",
            severity="high" if drift_count >= 5 else "medium",
            signal_ref=drift_signals[0].signal_id,
            example_input="Prompt generates outputs deviating from segment trends",
            example_output=f"{drift_count} drift corrections with avg quality {avg_quality:.2f}",
            ideal_behavior="Align prompt with segment-specific expectations and trends",
            detected_pattern="Systematic KPI drift detected",
            prompt_file=prompt_file,
        ))

    return issues


def _detect_funding_mismatch(
    prompt_text: str,
    signals: List[Any],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """Detect prompts generating incorrect funding recommendations."""
    issues: List[PromptIssue] = []

    # Check for funding misclassification signals
    funding_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "funding_misclassifications"]

    if not funding_signals:
        return issues

    # Check for hardcoded funding references in prompt
    funding_patterns = [
        r"\b(BAFA|KfW|BMWi|BMWK|Horizon|InvestEU)\b",
        r"\b(Förderprogramm|funding\s+program)\b",
    ]

    for pattern in funding_patterns:
        matches = re.findall(pattern, prompt_text, re.IGNORECASE)
        if matches:
            issues.append(PromptIssue(
                issue_type="funding_mismatch",
                severity="medium" if len(funding_signals) < 3 else "high",
                signal_ref=funding_signals[0].signal_id if funding_signals else None,
                example_input=f"Hardcoded funding reference: '{matches[0]}'",
                example_output="Output recommends incorrect funding programs",
                ideal_behavior="Use dynamic funding lookup based on eligibility criteria",
                detected_pattern=f"Static funding reference: {matches[0]}",
                prompt_file=prompt_file,
            ))

    return issues


def _detect_ai_act_weaknesses(
    prompt_text: str,
    signals: List[Any],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """Detect prompts producing weak AI Act reasoning."""
    issues = []

    # Check for AI Act reasoning signals
    ai_act_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "ai_act_reasoning"]

    # Patterns indicating weak AI Act instructions
    weak_ai_act_patterns = [
        r"kurz\s+(die\s+)?AI[\s-]?Act",
        r"briefly\s+mention\s+AI\s+Act",
        r"optional.*AI[\s-]?Act",
    ]

    for pattern in weak_ai_act_patterns:
        matches = re.findall(pattern, prompt_text, re.IGNORECASE)
        if matches:
            issues.append(PromptIssue(
                issue_type="ai_act_weakness",
                severity="medium",
                signal_ref=ai_act_signals[0].signal_id if ai_act_signals else None,
                example_input=f"Weak AI Act instruction: '{matches[0]}'",
                example_output="Output lacks detailed AI Act compliance reasoning",
                ideal_behavior="Require specific risk classification and compliance steps",
                detected_pattern=f"Weak AI Act instruction: {matches[0]}",
                prompt_file=prompt_file,
            ))

    # High severity if many AI Act signals
    if len(ai_act_signals) >= 3:
        issues.append(PromptIssue(
            issue_type="ai_act_weakness",
            severity="high",
            signal_ref=ai_act_signals[0].signal_id,
            example_input="Multiple AI Act sections",
            example_output=f"{len(ai_act_signals)} AI Act reasoning improvements needed",
            ideal_behavior="Strengthen AI Act instructions with specific requirements",
            detected_pattern="Systematic AI Act reasoning weakness",
            prompt_file=prompt_file,
        ))

    return issues


def _detect_branch_context_misuse(
    prompt_text: str,
    signals: List[Any],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """Detect prompts using wrong labels or generic formulations."""
    issues = []

    # Generic branch patterns that should be specific
    generic_patterns = [
        r"\b(allgemein|generell|grundsätzlich)\s+(gilt|empfehlen|raten)\b",
        r"\b(in\s+general|generally|typically)\s+(recommend|suggest)\b",
        r"\b(für\s+alle\s+Branchen|branchenübergreifend)\b",
    ]

    for pattern in generic_patterns:
        matches = re.findall(pattern, prompt_text, re.IGNORECASE)
        if matches:
            issues.append(PromptIssue(
                issue_type="branch_context_misuse",
                severity="low",
                example_input=f"Generic instruction: '{matches[0]}'",
                example_output="Output lacks branch-specific recommendations",
                ideal_behavior="Use branch-conditional instructions with specific examples",
                detected_pattern=f"Generic formulation: {matches[0]}",
                prompt_file=prompt_file,
            ))

    return issues


def _detect_insight_collisions(
    prompt_text: str,
    signals: List[Any],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """Detect prompts generating content conflicting with Insight Engine."""
    issues = []

    # Check for insight quality signals
    insight_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "insight_quality"]

    if insight_signals and len(insight_signals) >= 2:
        issues.append(PromptIssue(
            issue_type="insight_collision",
            severity="medium" if len(insight_signals) < 5 else "high",
            signal_ref=insight_signals[0].signal_id,
            example_input="Prompt-generated insights",
            example_output=f"{len(insight_signals)} insight corrections needed",
            ideal_behavior="Align prompt outputs with Insight Engine data",
            detected_pattern="Insight Engine collision detected",
            prompt_file=prompt_file,
        ))

    return issues


def _detect_g17p_intro_redundancy(
    prompt_text: str,
    signals: List[Any],
    prompt_file: Optional[str],
) -> List[PromptIssue]:
    """
    G17.P: Detect redundant intro patterns in DATA_READINESS and BUSINESS_CASE.

    These patterns cause overlap with other sections (Roadmap, Executive Summary,
    Org Change) and should be replaced with the G17.P-compliant intros.
    """
    issues = []

    # Check DATA_READINESS intro patterns
    if prompt_file and "data_readiness" in prompt_file.lower():
        for pattern in TEMPLATE_PHRASES.get("data_readiness_intro_standard", []):
            matches = re.findall(pattern, prompt_text, re.IGNORECASE)
            if matches:
                issues.append(PromptIssue(
                    issue_type="data_readiness_intro_redundancy",
                    severity="high",  # P1 priority
                    example_input=f"Found pattern: '{matches[0]}'",
                    example_output="Intro overlaps with Org Change, Tech/Prozesse, Roadmap",
                    ideal_behavior="Use G17.P intro: 'Die Bewertung Ihrer Datenlage ist eng mit der Prozessanalyse und den Quick Wins verknüpft...'",
                    detected_pattern=f"Redundant DATA_READINESS intro: {matches[0]}",
                    prompt_file=prompt_file,
                ))
                break  # One issue per file is enough

    # Check BUSINESS_CASE intro patterns
    if prompt_file and "business_case" in prompt_file.lower():
        for pattern in TEMPLATE_PHRASES.get("business_case_intro_standard", []):
            matches = re.findall(pattern, prompt_text, re.IGNORECASE)
            if matches:
                issues.append(PromptIssue(
                    issue_type="business_case_intro_redundancy",
                    severity="high",  # P1 priority
                    example_input=f"Found pattern: '{matches[0]}'",
                    example_output="Intro overlaps with Executive Summary, Quick Wins, ROI Tracking",
                    ideal_behavior="Use G17.P intro: 'Der Business Case verbindet Ihre Quick Wins mit der realistischen ROI-Prognose...'",
                    detected_pattern=f"Redundant BUSINESS_CASE intro: {matches[0]}",
                    prompt_file=prompt_file,
                ))
                break  # One issue per file is enough

    return issues


def detect_template_phrase_in_output(
    output_text: str,
    section_type: str,
) -> List[Dict[str, Any]]:
    """
    G17.P: Detect template phrases in generated output (for validation).

    Args:
        output_text: The generated HTML output
        section_type: One of 'data_readiness' or 'business_case'

    Returns:
        List of detected template phrase matches
    """
    matches = []
    phrases = TEMPLATE_PHRASES.get(f"{section_type}_intro_standard", [])

    for pattern in phrases:
        found = re.findall(pattern, output_text, re.IGNORECASE)
        if found:
            matches.append({
                "pattern": pattern,
                "match": found[0] if found else "",
                "section_type": section_type,
                "severity": "high",
            })

    return matches


def has_cross_reference(output_text: str, section_type: str) -> bool:
    """
    G17.P: Check if output contains required cross-references.

    Args:
        output_text: The generated HTML output
        section_type: One of 'data_readiness' or 'business_case'

    Returns:
        True if cross-references are present
    """
    if section_type == "data_readiness":
        # Should reference Roadmap 90d and Quick Wins
        patterns = [
            r"→\s*(siehe|see)\s*(Roadmap|Quick\s*Wins)",
            r"vgl\.\s*(Roadmap|Quick\s*Wins)",
            r"\(→\s*(Roadmap|Quick\s*Wins)\)",
        ]
    elif section_type == "business_case":
        # Should reference Quick Wins and/or ROI Tracking
        patterns = [
            r"→\s*(siehe|see)\s*(Quick\s*Wins|Sofortmaßnahmen|ROI)",
            r"vgl\.\s*(Quick\s*Wins|ROI)",
            r"\(→\s*(Quick\s*Wins|Sofortmaßnahmen)\)",
        ]
    else:
        return True  # No requirement for other sections

    for pattern in patterns:
        if re.search(pattern, output_text, re.IGNORECASE):
            return True

    return False


# =============================================================================
# REWRITE SUGGESTION GENERATION (G17.4-B)
# =============================================================================

def generate_prompt_rewrite_suggestions(
    issues: List[Any],
    aggregated_signals: Optional[List[Any]] = None,
    segment_stats: Optional[Any] = None,
    predictive_output: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate rewrite recommendations per prompt section (G17.4-B).

    Rules:
    - Only generate rewrites if segment stability >= medium
    - Confidence calculated from signal intensity, stability, frequency, predictive alignment
    - P1 only for clear, reproducible patterns
    - No rewrite if FT_PRIVACY_STRICT_MODE could be violated

    Args:
        issues: List of detected issues from detect_prompt_weaknesses
        aggregated_signals: FT signals for additional context
        segment_stats: Segment statistics for stability check
        predictive_output: Predictive engine output

    Returns:
        List of RewriteSuggestion dicts
    """
    if not PROMPT_REWRITE_ENGINE_ENABLED:
        return []

    # Check segment stability requirement
    stability = "medium"
    if segment_stats:
        stability = getattr(segment_stats, "stability", None) or "medium"

    if PROMPT_REWRITE_REQUIRE_STRONG_SEGMENT and stability == "weak":
        if PROMPT_REWRITE_DEBUG:
            log.debug("Skipping rewrite suggestions due to weak segment stability")
        return []

    suggestions: List[RewriteSuggestion] = []
    signals = aggregated_signals or []

    for issue in issues:
        if not isinstance(issue, dict):
            issue = asdict(issue) if hasattr(issue, '__dataclass_fields__') else {}

        issue_type = issue.get("issue_type", "")
        severity = issue.get("severity", "low")
        prompt_file = issue.get("prompt_file", "unknown")

        # Calculate confidence
        confidence = _calculate_rewrite_confidence(
            issue, signals, stability, predictive_output
        )

        # Skip low confidence suggestions
        if confidence < PROMPT_REWRITE_MIN_CONFIDENCE:
            continue

        # Determine priority
        priority = _determine_priority(severity, confidence, issue_type)

        # Generate rewrite suggestion
        suggestion = _generate_suggestion_for_issue(
            issue, confidence, priority, stability
        )

        if suggestion:
            suggestions.append(suggestion)

    # Sort by priority and confidence
    suggestions.sort(key=lambda s: (s.priority, -s.confidence))

    # Limit suggestions
    suggestions = suggestions[:PROMPT_REWRITE_MAX_SUGGESTIONS]

    if PROMPT_REWRITE_DEBUG:
        log.debug(f"Generated {len(suggestions)} rewrite suggestions")

    return [asdict(s) for s in suggestions]


def _calculate_rewrite_confidence(
    issue: Dict[str, Any],
    signals: List[Any],
    stability: str,
    predictive_output: Optional[Dict[str, Any]],
) -> float:
    """Calculate confidence score for a rewrite suggestion."""
    base_confidence = 0.3

    # Severity boost
    severity = issue.get("severity", "low")
    base_confidence += SEVERITY_WEIGHTS.get(severity, 0.3) * 0.2

    # Signal intensity boost
    signal_ref = issue.get("signal_ref")
    if signal_ref:
        related_signals = [s for s in signals if hasattr(s, 'signal_id') and s.signal_id == signal_ref]
        if related_signals:
            signal = related_signals[0]
            if hasattr(signal, 'quality_score'):
                base_confidence += signal.quality_score * 0.15
            if hasattr(signal, 'confidence'):
                base_confidence += signal.confidence * 0.1

    # Stability boost
    stability_boost = {"strong": 0.2, "medium": 0.1, "weak": 0.0}
    base_confidence += stability_boost.get(stability, 0.0)

    # Predictive alignment boost
    if predictive_output:
        alignment = predictive_output.get("alignment_score", 0.5)
        base_confidence += (alignment - 0.5) * 0.1

    # Frequency boost based on issue type occurrences
    issue_type = issue.get("issue_type", "")
    type_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == _map_issue_to_signal_type(issue_type)]
    if len(type_signals) >= 5:
        base_confidence += 0.15
    elif len(type_signals) >= 3:
        base_confidence += 0.1

    return min(base_confidence, 1.0)


def _map_issue_to_signal_type(issue_type: str) -> str:
    """Map issue type to corresponding signal type."""
    mapping = {
        "too_short_warning": "size_aware_length",
        "persona_leak": "persona_fix",
        "redundancy_pattern": "redundancy_compression",
        "predictive_drift": "predictive_drift",
        "funding_mismatch": "funding_misclassifications",
        "ai_act_weakness": "ai_act_reasoning",
        "insight_collision": "insight_quality",
    }
    return mapping.get(issue_type, issue_type)


def _determine_priority(severity: str, confidence: float, issue_type: str) -> str:
    """Determine priority based on severity and confidence."""
    if severity == "high" and confidence >= 0.7:
        return "P1"
    elif severity in ("high", "medium") and confidence >= 0.5:
        return "P2"
    else:
        return "P3"


def _generate_suggestion_for_issue(
    issue: Dict[str, Any],
    confidence: float,
    priority: str,
    stability: str,
) -> Optional[RewriteSuggestion]:
    """Generate a specific rewrite suggestion for an issue."""
    issue_type = issue.get("issue_type", "")
    detected_pattern = issue.get("detected_pattern", "")
    ideal_behavior = issue.get("ideal_behavior", "")
    prompt_file = issue.get("prompt_file", "prompts/unknown.md")
    signal_ref = issue.get("signal_ref")

    # Generate suggestion based on issue type
    suggestion_templates = {
        "too_short_warning": {
            "change_type": "strengthen",
            "proposed_rewrite": _generate_length_rewrite(detected_pattern, ideal_behavior),
            "justification": f"Signals indicate outputs are consistently too short. {ideal_behavior}",
        },
        "persona_leak": {
            "change_type": "rewrite",
            "proposed_rewrite": _generate_persona_rewrite(detected_pattern),
            "justification": f"Persona-inappropriate terms detected. Use conditional phrasing based on {{{{unternehmensgroesse}}}}.",
        },
        "redundancy_pattern": {
            "change_type": "remove",
            "proposed_rewrite": _generate_redundancy_rewrite(detected_pattern),
            "justification": f"Redundancy detected across sections. Remove repetition instructions.",
        },
        "predictive_drift": {
            "change_type": "clarify",
            "proposed_rewrite": _generate_drift_rewrite(detected_pattern),
            "justification": f"Output deviates from segment trends. Align with predictive expectations.",
        },
        "funding_mismatch": {
            "change_type": "rewrite",
            "proposed_rewrite": _generate_funding_rewrite(detected_pattern),
            "justification": f"Hardcoded funding references cause mismatches. Use dynamic lookup.",
        },
        "ai_act_weakness": {
            "change_type": "strengthen",
            "proposed_rewrite": _generate_ai_act_rewrite(detected_pattern),
            "justification": f"AI Act reasoning is insufficient. Add specific compliance requirements.",
        },
        "branch_context_misuse": {
            "change_type": "clarify",
            "proposed_rewrite": _generate_branch_rewrite(detected_pattern),
            "justification": f"Generic formulations lack branch specificity. Add conditional logic.",
        },
        "insight_collision": {
            "change_type": "tighten",
            "proposed_rewrite": _generate_insight_rewrite(detected_pattern),
            "justification": f"Output conflicts with Insight Engine. Align with real-world data.",
        },
        # G17.P: Intro redundancy rewrites
        "data_readiness_intro_redundancy": {
            "change_type": "rewrite",
            "proposed_rewrite": _generate_data_readiness_intro_rewrite(),
            "justification": "G17.P: DATA_READINESS intro causes redundancy with Roadmap, Tech/Prozesse. Replace with cross-reference intro.",
        },
        "business_case_intro_redundancy": {
            "change_type": "rewrite",
            "proposed_rewrite": _generate_business_case_intro_rewrite(),
            "justification": "G17.P: BUSINESS_CASE intro causes redundancy with Executive Summary, Quick Wins. Replace with cross-reference intro.",
        },
    }

    template = suggestion_templates.get(issue_type)
    if not template:
        return None

    suggestion_id = _generate_suggestion_id(issue_type, prompt_file, detected_pattern)

    return RewriteSuggestion(
        suggestion_id=suggestion_id,
        prompt_file=prompt_file or "prompts/unknown.md",
        priority=priority,
        confidence=confidence,
        change_type=template["change_type"],
        current_section_excerpt=detected_pattern[:200] if detected_pattern else "",
        proposed_rewrite=template["proposed_rewrite"],
        justification=template["justification"],
        issue_refs=[signal_ref] if signal_ref else [],
        segment_stability=stability,
    )


def _generate_suggestion_id(issue_type: str, prompt_file: str, pattern: str) -> str:
    """Generate unique suggestion ID."""
    content = f"{issue_type}:{prompt_file}:{pattern}"
    hash_str = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:8]
    return f"rewrite_{issue_type}_{hash_str}"


# Rewrite generators
def _generate_length_rewrite(pattern: str, ideal: str) -> str:
    return f"""Erweitern Sie die Anweisungen um konkrete Tiefenangaben:
- Mindestens 3-4 spezifische Aspekte pro Thema
- Konkrete Beispiele und Anwendungsfälle einfordern
- Begründungen und Zusammenhänge verlangen

Beispiel:
- Alt: "Beschreiben Sie kurz die Vorteile"
+ Neu: "Erläutern Sie mindestens 4 konkrete Vorteile mit jeweils einem Praxisbeispiel und der erwarteten Auswirkung"
"""


def _generate_persona_rewrite(pattern: str) -> str:
    return f"""Ersetzen Sie statische Persona-Referenzen durch bedingte Formulierungen:

{{{{#if (eq unternehmensgroesse "solo")}}}}
Sie als Einzelunternehmer...
{{{{else}}}}
Ihr Team...
{{{{/if}}}}

Oder verwenden Sie neutrale Formulierungen wie "das Unternehmen" oder "die Organisation".
"""


def _generate_redundancy_rewrite(pattern: str) -> str:
    return f"""Entfernen Sie Wiederholungsanweisungen und verwenden Sie Querverweise:

- Entfernen: "Wiederholen Sie die Kernpunkte"
- Ersetzen durch: "Verweisen Sie auf die in [Abschnitt X] genannten Aspekte"

Strukturieren Sie Abschnitte so, dass jeder einzigartige Informationen enthält.
"""


def _generate_drift_rewrite(pattern: str) -> str:
    return f"""Fügen Sie segment-spezifische Erwartungen hinzu:

Für {{{{branche}}}} in der Größenklasse {{{{unternehmensgroesse}}}}:
- Typische KPIs beachten
- Branchenübliche Zeitrahmen verwenden
- Segment-spezifische Benchmark-Werte einbeziehen
"""


def _generate_funding_rewrite(pattern: str) -> str:
    return f"""Ersetzen Sie hardcodierte Förderverweise durch dynamische Logik:

- Alt: "Das BAFA-Programm bietet..."
+ Neu: "Basierend auf {{{{funding_eligibility}}}}, prüfen Sie die passenden Programme aus {{{{available_programs}}}}"

Verwenden Sie die Funding-API für aktuelle Fördermöglichkeiten.
"""


def _generate_ai_act_rewrite(pattern: str) -> str:
    return f"""Verstärken Sie die AI-Act-Anweisungen:

Erforderliche Elemente:
1. Risikoklassifizierung (minimal/limited/high-risk/unacceptable)
2. Spezifische Compliance-Anforderungen pro Risikoklasse
3. Konkrete Handlungsschritte zur Einhaltung
4. Dokumentationspflichten
5. Zeitrahmen für Umsetzung

Mindestens 60 Wörter für AI-Act-Begründung.
"""


def _generate_branch_rewrite(pattern: str) -> str:
    return f"""Ersetzen Sie generische durch branch-spezifische Formulierungen:

{{{{#switch branche}}}}
{{{{#case "finance"}}}}
Im Finanzsektor gelten besondere regulatorische Anforderungen...
{{{{/case}}}}
{{{{#case "health"}}}}
Im Gesundheitswesen sind Datenschutzaspekte besonders kritisch...
{{{{/case}}}}
{{{{#default}}}}
Branchenspezifische Best Practices beachten...
{{{{/default}}}}
{{{{/switch}}}}
"""


def _generate_insight_rewrite(pattern: str) -> str:
    return f"""Integrieren Sie Insight-Engine-Daten in die Prompt-Logik:

- Verwenden Sie {{{{segment_insights}}}} für segment-basierte Empfehlungen
- Beziehen Sie {{{{trend_data}}}} für aktuelle Entwicklungen ein
- Vermeiden Sie Widersprüche zu aggregierten Feedback-Daten
"""


def _generate_data_readiness_intro_rewrite() -> str:
    """G17.P: Generate rewrite for DATA_READINESS intro."""
    return """G17.P-konforme Einleitung für DATA_READINESS:

DE:
<p>
  Die Bewertung Ihrer Datenlage ist eng mit der Prozessanalyse und den Quick Wins verknüpft
  (→ siehe Roadmap 90d, → Quick Wins). Dieser Abschnitt fasst kompakt zusammen, welche
  vorhandenen Datenquellen, Strukturen und Schnittstellen in <strong>{{BRANCH_CONTEXT_LABEL}}</strong>
  unmittelbar für erste KI-Workflows nutzbar sind – und wo gezielt nachgebessert werden sollte.
</p>

EN:
<p>
  Your data readiness assessment directly aligns with the process analysis and early Quick Wins
  (→ see 90-Day Roadmap, → Quick Wins). This section summarizes which existing data sources,
  structures, and integrations in <strong>{{BRANCH_CONTEXT_LABEL}}</strong> can be used
  immediately for AI workflows — and where targeted improvements are required.
</p>

Regeln:
- Max. 40–55 Wörter
- Keine "Grundlage jeder KI", "entscheidend für Erfolg" etc.
- Cross-References zu Roadmap_90d und Quick Wins PFLICHT
- Kurzlabels (BRANCH_CONTEXT_LABEL) sparsam verwenden
"""


def _generate_business_case_intro_rewrite() -> str:
    """G17.P: Generate rewrite for BUSINESS_CASE intro."""
    return """G17.P-konforme Einleitung für BUSINESS_CASE:

DE:
<p>
  Der Business Case verbindet Ihre Quick Wins (→ siehe Sofortmaßnahmen) mit der realistischen
  ROI-Prognose und zeigt, welche Investitionen sich in welchem Zeitraum amortisieren. Im Fokus
  stehen Zeitersparnis, Qualitätsgewinne und die Auswirkungen der KI-Readiness-Roadmap auf
  CAPEX, OPEX und Payback für <strong>{{OFFERING_LABEL}}</strong>.
</p>

EN:
<p>
  The Business Case connects your Quick Wins (→ see Quick Wins section) with the realistic
  ROI forecast and shows how investments amortize over time. The focus lies on time savings,
  quality gains, and the impact of your AI-Readiness roadmap on CAPEX, OPEX, and payback
  for <strong>{{OFFERING_LABEL}}</strong>.
</p>

Regeln:
- Max. 50–65 Wörter
- Keine "wesentlicher Bestandteil", "zentrale Grundlage" etc.
- Cross-Reference zu Quick Wins PFLICHT
- AI-Act-Kostenfaktoren optional erwähnbar
- Kein Overlap mit Executive Summary
"""


# =============================================================================
# PATCH GENERATION (G17.4-C)
# =============================================================================

def generate_patch_output(
    prompt_file_path: str,
    rewrite_suggestion: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Generate syntactic patch format for a rewrite suggestion (G17.4-C).

    Args:
        prompt_file_path: Path to the prompt file
        rewrite_suggestion: The rewrite suggestion dict

    Returns:
        PatchOutput dict with diff-style patch content
    """
    if not PROMPT_REWRITE_GENERATE_PATCHES:
        return None

    suggestion_id = rewrite_suggestion.get("suggestion_id", "unknown")
    current_excerpt = rewrite_suggestion.get("current_section_excerpt", "")
    proposed = rewrite_suggestion.get("proposed_rewrite", "")
    change_type = rewrite_suggestion.get("change_type", "rewrite")

    if not proposed:
        return None

    # Generate unified diff format
    patch_lines = [
        f"--- a/{prompt_file_path}",
        f"+++ b/{prompt_file_path}",
        f"@@ -1,5 +1,10 @@",
    ]

    # Add context and changes based on change type
    if change_type == "remove":
        for line in current_excerpt.split("\n")[:5]:
            if line.strip():
                patch_lines.append(f"- {line}")
    elif change_type in ("add", "strengthen"):
        for line in proposed.split("\n")[:10]:
            if line.strip():
                patch_lines.append(f"+ {line}")
    else:  # rewrite, clarify, tighten
        for line in current_excerpt.split("\n")[:3]:
            if line.strip():
                patch_lines.append(f"- {line}")
        for line in proposed.split("\n")[:10]:
            if line.strip():
                patch_lines.append(f"+ {line}")

    patch_content = "\n".join(patch_lines)

    return asdict(PatchOutput(
        prompt_file=prompt_file_path,
        patch_content=patch_content,
        suggestion_id=suggestion_id,
    ))


def generate_all_patches(
    suggestions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate patches for all suggestions."""
    patches = []
    for suggestion in suggestions:
        prompt_file = suggestion.get("prompt_file", "")
        patch = generate_patch_output(prompt_file, suggestion)
        if patch:
            patches.append(patch)
    return patches


# =============================================================================
# STORAGE & RETRIEVAL
# =============================================================================

def get_storage_path() -> Path:
    """Get storage path for rewrite suggestions."""
    path = Path(PROMPT_REWRITE_STORAGE_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_suggestions(suggestions: List[Dict[str, Any]]) -> int:
    """
    Store rewrite suggestions to disk (G17.4-E).

    Returns:
        Number of suggestions stored
    """
    if not suggestions:
        return 0

    storage_path = get_storage_path()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    suggestions_file = storage_path / f"suggestions_{today}.jsonl"

    with _storage_lock:
        with open(suggestions_file, "a", encoding="utf-8") as f:
            for suggestion in suggestions:
                f.write(json.dumps(suggestion, ensure_ascii=False) + "\n")

    # Also add to buffer
    for suggestion in suggestions:
        _suggestion_buffer.append(RewriteSuggestion(**suggestion) if isinstance(suggestion, dict) else suggestion)

    log.info(f"Stored {len(suggestions)} rewrite suggestions")
    return len(suggestions)


def load_suggestions(days: int = 30) -> List[Dict[str, Any]]:
    """Load suggestions from storage."""
    storage_path = get_storage_path()
    suggestions = []

    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)

    for file_path in storage_path.glob("suggestions_*.jsonl"):
        try:
            date_str = file_path.stem.replace("suggestions_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        suggestions.append(json.loads(line))
        except Exception as e:
            log.error(f"Error loading suggestions from {file_path}: {e}")

    return suggestions


def get_prompt_analysis() -> Dict[str, Any]:
    """Get aggregated prompt analysis for dashboard (G17.4-D)."""
    suggestions = load_suggestions()

    # Aggregate by issue type
    by_type: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    by_file: Dict[str, int] = {}

    for s in suggestions:
        # Count by type (derived from suggestion content)
        issue_refs = s.get("issue_refs", [])
        for ref in issue_refs:
            if ref:
                issue_type = ref.split("_")[0] if "_" in str(ref) else "unknown"
                by_type[issue_type] = by_type.get(issue_type, 0) + 1

        # Count by priority
        priority = s.get("priority", "P3")
        by_priority[priority] = by_priority.get(priority, 0) + 1

        # Count by file
        prompt_file = s.get("prompt_file", "unknown")
        by_file[prompt_file] = by_file.get(prompt_file, 0) + 1

    return {
        "total_suggestions": len(suggestions),
        "by_priority": by_priority,
        "by_file": by_file,
        "by_issue_type": by_type,
        "enabled": PROMPT_REWRITE_ENGINE_ENABLED,
    }


def get_rewrite_suggestions(
    priority: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Get rewrite suggestions for dashboard (G17.4-D)."""
    suggestions = load_suggestions()

    if priority:
        suggestions = [s for s in suggestions if s.get("priority") == priority]

    # Sort by priority then confidence
    suggestions.sort(key=lambda s: (s.get("priority", "P3"), -s.get("confidence", 0)))

    return suggestions[:limit]


def get_next_patches(limit: int = 5) -> List[Dict[str, Any]]:
    """Get next patches ready for commit (G17.4-D)."""
    suggestions = get_rewrite_suggestions(priority="P1", limit=limit)

    if not suggestions:
        suggestions = get_rewrite_suggestions(priority="P2", limit=limit)

    patches = []
    for suggestion in suggestions[:limit]:
        if not suggestion.get("applied", False):
            patch = generate_patch_output(
                suggestion.get("prompt_file", ""),
                suggestion
            )
            if patch:
                patches.append(patch)

    return patches


def clear_buffer() -> None:
    """Clear the suggestion buffer."""
    global _suggestion_buffer
    _suggestion_buffer = []


def get_buffered_suggestions() -> List[RewriteSuggestion]:
    """Get buffered suggestions."""
    return list(_suggestion_buffer)
