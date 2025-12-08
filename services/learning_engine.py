# -*- coding: utf-8 -*-
"""
Sprint G16-D: Learning Engine

Generates prioritized action items from feedback analysis.
Identifies patterns that require attention and suggests fixes.

Version: 1.0.0
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# =============================================================================
# ACTION ITEM DATA STRUCTURE
# =============================================================================

@dataclass
class ActionItem:
    """Prioritized action item from learning engine."""
    priority: str  # high, medium, low
    category: str  # persona, ai-act, research, warnings, performance
    title: str
    description: str
    affected_count: int = 0
    suggested_fix: Optional[str] = None
    related_files: List[str] = field(default_factory=list)


# =============================================================================
# THRESHOLDS
# =============================================================================

# Thresholds for generating action items
WARNING_HIGH_THRESHOLD = 10  # More than this triggers high priority
WARNING_MEDIUM_THRESHOLD = 5

PERSONA_HIGH_THRESHOLD = 5  # Persona leaks
PERSONA_MEDIUM_THRESHOLD = 3

DEGRADATION_THRESHOLD = 0.4  # Research coverage below this is critical
DEGRADATION_TREND_THRESHOLD = -20  # Trend % decline

MISMATCH_THRESHOLD = 3  # AI-Act mismatches to flag


# =============================================================================
# ACTION ITEM GENERATORS
# =============================================================================

def generate_action_items(days: int = 7) -> List[ActionItem]:
    """
    Generate prioritized action items from feedback analysis.

    Args:
        days: Analysis period in days

    Returns:
        List of ActionItem objects sorted by priority
    """
    from services.feedback_analyzer import run_full_analysis

    analysis = run_full_analysis(days=days, include_previous=True)
    action_items: List[ActionItem] = []

    # Generate items from each analysis area
    action_items.extend(_generate_warning_actions(analysis))
    action_items.extend(_generate_persona_actions(analysis))
    action_items.extend(_generate_research_actions(analysis))
    action_items.extend(_generate_ai_act_actions(analysis))
    action_items.extend(_generate_performance_actions(days))

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    action_items.sort(key=lambda x: priority_order.get(x.priority, 2))

    log.info(f"Learning engine generated {len(action_items)} action items")

    return action_items


def _generate_warning_actions(analysis: Any) -> List[ActionItem]:
    """Generate action items from warning patterns."""
    items: List[ActionItem] = []

    for pattern in analysis.warning_patterns:
        if pattern.occurrence_count >= WARNING_HIGH_THRESHOLD:
            priority = "high"
        elif pattern.occurrence_count >= WARNING_MEDIUM_THRESHOLD:
            priority = "medium"
        else:
            continue  # Skip low-count patterns

        # Generate specific suggestions based on warning type
        suggested_fix = _get_warning_fix_suggestion(pattern.warning_type, pattern.section)

        items.append(ActionItem(
            priority=priority,
            category="warnings",
            title=f"Recurring {pattern.warning_type} warnings in {pattern.section}",
            description=(
                f"Warning type '{pattern.warning_type}' has occurred {pattern.occurrence_count} times "
                f"in section '{pattern.section}'. Trend: {pattern.trend}."
            ),
            affected_count=pattern.occurrence_count,
            suggested_fix=suggested_fix,
            related_files=_get_related_files_for_warning(pattern.warning_type),
        ))

    return items


def _generate_persona_actions(analysis: Any) -> List[ActionItem]:
    """Generate action items from persona leak patterns."""
    items: List[ActionItem] = []

    for pattern in analysis.persona_leak_patterns:
        if pattern.occurrence_count >= PERSONA_HIGH_THRESHOLD:
            priority = "high"
        elif pattern.occurrence_count >= PERSONA_MEDIUM_THRESHOLD:
            priority = "medium"
        else:
            continue

        # Get most common leaked terms
        top_terms = sorted(
            pattern.leaked_terms.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]
        terms_str = ", ".join(f"'{t[0]}' ({t[1]}x)" for t in top_terms)

        suggested_fix = (
            f"Add terms to FORBIDDEN_TERMS_{pattern.source_persona.upper()} in "
            f"services/prompt_enhancer.py and add replacements to "
            f"{pattern.source_persona.upper()}_PHRASE_REPLACEMENTS."
        )

        items.append(ActionItem(
            priority=priority,
            category="persona",
            title=f"Persona leaks in {pattern.source_persona} reports",
            description=(
                f"{pattern.occurrence_count} persona leaks detected in {pattern.source_persona} reports "
                f"across {len(pattern.affected_reports)} reports. "
                f"Top leaked terms: {terms_str if terms_str else 'unknown'}."
            ),
            affected_count=pattern.occurrence_count,
            suggested_fix=suggested_fix,
            related_files=[
                "services/prompt_enhancer.py",
                "services/report_validator.py",
            ],
        ))

    return items


def _generate_research_actions(analysis: Any) -> List[ActionItem]:
    """Generate action items from research degradation."""
    items: List[ActionItem] = []

    for degradation in analysis.research_degradations:
        if not degradation.is_degraded:
            continue

        # Determine priority
        if degradation.current_coverage < 0.3:
            priority = "high"
        elif degradation.current_coverage < DEGRADATION_THRESHOLD:
            priority = "medium"
        elif degradation.trend_pct < DEGRADATION_TREND_THRESHOLD:
            priority = "medium"
        else:
            priority = "low"

        suggested_fix = _get_research_fix_suggestion(degradation.source)

        items.append(ActionItem(
            priority=priority,
            category="research",
            title=f"Research coverage degradation: {degradation.source}",
            description=(
                f"Coverage for '{degradation.source}' has dropped to {degradation.current_coverage:.1%} "
                f"(was {degradation.previous_coverage:.1%}, trend: {degradation.trend_pct:+.1f}%). "
                f"Circuit breaker opens: {degradation.circuit_breaker_opens}."
            ),
            affected_count=degradation.circuit_breaker_opens,
            suggested_fix=suggested_fix,
            related_files=_get_related_files_for_research(degradation.source),
        ))

    return items


def _generate_ai_act_actions(analysis: Any) -> List[ActionItem]:
    """Generate action items from AI-Act mismatches."""
    items: List[ActionItem] = []

    if len(analysis.ai_act_mismatches) >= MISMATCH_THRESHOLD:
        # Group by mismatch direction
        under_classified = []
        over_classified = []

        risk_order = {"none": 0, "minimal": 1, "limited": 2, "high-risk": 3}

        for mismatch in analysis.ai_act_mismatches:
            expected_val = risk_order.get(mismatch.expected_risk, 1)
            actual_val = risk_order.get(mismatch.actual_risk, 1)

            if expected_val > actual_val:
                under_classified.append(mismatch)
            else:
                over_classified.append(mismatch)

        if under_classified:
            items.append(ActionItem(
                priority="high",
                category="ai-act",
                title="AI-Act under-classification detected",
                description=(
                    f"{len(under_classified)} reports may have AI-Act risk levels that are too low. "
                    f"This could result in compliance issues."
                ),
                affected_count=len(under_classified),
                suggested_fix=(
                    "Review determine_risk_level() in scripts/validate_profiles_g15_2.py. "
                    "Check HIGH_RISK_INDICATORS and ensure finance/insurance branches are properly detected."
                ),
                related_files=[
                    "scripts/validate_profiles_g15_2.py",
                    "services/feedback_analyzer.py",
                ],
            ))

        if over_classified:
            items.append(ActionItem(
                priority="medium",
                category="ai-act",
                title="AI-Act over-classification detected",
                description=(
                    f"{len(over_classified)} reports may have AI-Act risk levels that are too high. "
                    f"This could result in unnecessary compliance burden."
                ),
                affected_count=len(over_classified),
                suggested_fix=(
                    "Review ai_act_override_risk_level in profile JSON files. "
                    "Check if profiles are correctly setting override levels."
                ),
                related_files=[
                    "data/test_profiles_gold/",
                    "scripts/validate_profiles_g15_2.py",
                ],
            ))

    return items


def _generate_performance_actions(days: int) -> List[ActionItem]:
    """Generate action items from performance metrics."""
    from services.feedback_loop import get_recent_feedback

    items: List[ActionItem] = []
    entries = get_recent_feedback(days=days)

    if not entries:
        return items

    # Check for timeout issues
    total_timeouts = sum(e.llm_timeouts for e in entries)
    avg_timeouts = total_timeouts / len(entries)

    if avg_timeouts > 2:
        items.append(ActionItem(
            priority="high" if avg_timeouts > 5 else "medium",
            category="performance",
            title="High LLM timeout rate",
            description=(
                f"Average of {avg_timeouts:.1f} LLM timeouts per report over {len(entries)} reports. "
                f"Total timeouts: {total_timeouts}."
            ),
            affected_count=total_timeouts,
            suggested_fix=(
                "Increase LLM_TIMEOUT in environment variables. "
                "Consider implementing request chunking or reducing prompt complexity."
            ),
            related_files=[
                "services/gpt_analyze.py",
                ".env.example",
            ],
        ))

    # Check for high fallback rates
    avg_fallback = sum(e.fallback_rate for e in entries) / len(entries)

    if avg_fallback > 0.3:
        items.append(ActionItem(
            priority="high" if avg_fallback > 0.5 else "medium",
            category="performance",
            title="High fallback content rate",
            description=(
                f"Average fallback rate of {avg_fallback:.1%} across {len(entries)} reports. "
                f"This indicates research or generation failures."
            ),
            affected_count=int(avg_fallback * len(entries)),
            suggested_fix=(
                "Check API connectivity (Tavily, Perplexity). "
                "Review circuit breaker settings and retry logic."
            ),
            related_files=[
                "services/web_research.py",
                "services/gpt_analyze.py",
            ],
        ))

    # Check for slow generation times
    avg_time = sum(e.generation_time_sec for e in entries) / len(entries)

    if avg_time > 120:  # More than 2 minutes average
        items.append(ActionItem(
            priority="medium",
            category="performance",
            title="Slow report generation",
            description=(
                f"Average generation time of {avg_time:.0f} seconds. "
                f"Target is under 120 seconds."
            ),
            affected_count=len([e for e in entries if e.generation_time_sec > 120]),
            suggested_fix=(
                "Consider parallel section generation. "
                "Review and optimize prompt lengths. "
                "Enable caching for repeated research queries."
            ),
            related_files=[
                "services/gpt_analyze.py",
                "services/web_research.py",
            ],
        ))

    return items


# =============================================================================
# SUGGESTION HELPERS
# =============================================================================

def _get_warning_fix_suggestion(warning_type: str, section: str) -> str:
    """Get fix suggestion for warning type."""
    suggestions = {
        "min-word": (
            f"Extend prompt template for {section}. "
            f"Add more specific questions or requirements to increase output length."
        ),
        "redundancy": (
            f"Review {section} template for duplicate instructions. "
            f"Ensure different sections have distinct scope."
        ),
        "persona-leak": (
            "Add terms to forbidden list and phrase replacements in prompt_enhancer.py."
        ),
        "placeholder": (
            f"Check {section} template for missing variable substitutions. "
            f"Verify all placeholders are being replaced."
        ),
        "fallback": (
            "Check API connectivity and circuit breaker status. "
            "Review retry logic in web_research.py."
        ),
        "ai-act": (
            "Review AI-Act classification logic in validate_profiles_g15_2.py."
        ),
    }

    return suggestions.get(warning_type, f"Review {section} generation logic.")


def _get_related_files_for_warning(warning_type: str) -> List[str]:
    """Get related files for warning type."""
    files = {
        "min-word": ["prompts/", "services/gpt_analyze.py"],
        "redundancy": ["services/report_validator.py", "prompts/"],
        "persona-leak": ["services/prompt_enhancer.py", "services/report_validator.py"],
        "placeholder": ["services/gpt_analyze.py", "services/template_renderer.py"],
        "fallback": ["services/web_research.py", "services/gpt_analyze.py"],
        "ai-act": ["scripts/validate_profiles_g15_2.py"],
    }

    return files.get(warning_type, ["services/gpt_analyze.py"])


def _get_research_fix_suggestion(source: str) -> str:
    """Get fix suggestion for research source."""
    suggestions = {
        "tools": "Check Tavily API connectivity and rate limits.",
        "funding": "Verify funding database URLs and API keys.",
        "competitor": "Check market research API configuration.",
        "market_insights": "Review Perplexity API status and quotas.",
        "api_reliability": (
            "Increase timeout values. "
            "Implement exponential backoff. "
            "Consider fallback providers."
        ),
    }

    return suggestions.get(source, "Review API configuration and connectivity.")


def _get_related_files_for_research(source: str) -> List[str]:
    """Get related files for research source."""
    files = {
        "tools": ["services/web_research.py", "services/tavily_search.py"],
        "funding": ["services/funding_search.py", "data/funding_programs/"],
        "competitor": ["services/web_research.py"],
        "market_insights": ["services/perplexity_search.py"],
        "api_reliability": ["services/web_research.py", ".env.example"],
    }

    return files.get(source, ["services/web_research.py"])


# =============================================================================
# EXPORT SUMMARY
# =============================================================================

def get_learning_summary(days: int = 7) -> Dict[str, Any]:
    """
    Get a summary of learning insights.

    Args:
        days: Analysis period in days

    Returns:
        Dictionary with summary statistics
    """
    action_items = generate_action_items(days=days)

    # Count by category
    by_category: Dict[str, int] = {}
    for item in action_items:
        cat = item.category
        by_category[cat] = by_category.get(cat, 0) + 1

    summary: Dict[str, Any] = {
        "period_days": days,
        "total_action_items": len(action_items),
        "by_priority": {
            "high": len([a for a in action_items if a.priority == "high"]),
            "medium": len([a for a in action_items if a.priority == "medium"]),
            "low": len([a for a in action_items if a.priority == "low"]),
        },
        "by_category": by_category,
        "top_issues": [],
    }

    # Get top 3 issues
    summary["top_issues"] = [
        {"title": item.title, "priority": item.priority, "affected": item.affected_count}
        for item in action_items[:3]
    ]

    return summary
