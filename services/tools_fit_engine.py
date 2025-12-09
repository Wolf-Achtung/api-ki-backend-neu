# -*- coding: utf-8 -*-
"""
Sprint B3-B: Tool Fit Score Engine 2.0

Multi-dimensional tool fitness scoring system.

Score Components (0.0-1.0), weighted:
- Semantic-Fit (0.25): Use case ↔ Tool similarity
- Branch-Fit (0.25): Industry profile alignment
- Size-Fit (0.20): Solo/Team/KMU specific suitability
- Funding-Fit (0.15): Funding program compatibility
- Risk-Fit (0.10): AI-Act compliance / Governance maturity
- Setup-Complexity (0.05): Implementation difficulty

Version: 1.0.0 (Sprint B3)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

TOOLS_FIT_ENABLED = os.getenv("TOOLS_FIT_ENABLED", "1").lower() in ("1", "true", "yes")
TOOLS_FIT_THRESHOLD_HIGH = float(os.getenv("TOOLS_FIT_THRESHOLD_HIGH", "0.75"))
TOOLS_FIT_THRESHOLD_MEDIUM = float(os.getenv("TOOLS_FIT_THRESHOLD_MEDIUM", "0.50"))

# Score weights (must sum to 1.0)
SCORE_WEIGHTS = {
    "semantic": 0.25,
    "branch": 0.25,
    "size": 0.20,
    "funding": 0.15,
    "risk": 0.10,
    "complexity": 0.05,
}

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ToolFitScore:
    """Complete fit score for a tool."""
    tool_name: str
    tool_id: str
    total_score: float
    fit_level: str  # "high", "medium", "low"

    # Component scores
    semantic_score: float = 0.0
    branch_score: float = 0.0
    size_score: float = 0.0
    funding_score: float = 0.0
    risk_score: float = 0.0
    complexity_score: float = 0.0

    # Metadata
    categories: List[str] = field(default_factory=list)
    description: str = ""
    setup_hint: str = ""
    fit_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FitAnalysis:
    """Analysis of fit scores for a profile."""
    branch: str
    size: str
    risk_level: str
    total_tools_analyzed: int
    high_fit_count: int
    medium_fit_count: int
    low_fit_count: int
    top_categories: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# =============================================================================
# BRANCH FIT MAPPINGS
# =============================================================================

# Tool categories that align well with each branch
BRANCH_CATEGORY_AFFINITY: Dict[str, Dict[str, float]] = {
    "beratung": {
        "content": 0.9,
        "research": 0.95,
        "analysis": 0.9,
        "meeting": 0.85,
        "presentation": 0.9,
        "crm": 0.8,
        "productivity": 0.85,
        "documentation": 0.9,
    },
    "it": {
        "coding": 1.0,
        "development": 1.0,
        "devops": 0.95,
        "automation": 0.9,
        "security": 0.85,
        "mlops": 0.9,
        "data": 0.85,
        "integration": 0.85,
    },
    "handel": {
        "customer-service": 0.95,
        "crm": 0.9,
        "marketing": 0.9,
        "analytics": 0.85,
        "automation": 0.85,
        "social-media": 0.85,
        "seo": 0.8,
        "chatbot": 0.9,
    },
    "finanzen": {
        "finance": 1.0,
        "analytics": 0.95,
        "compliance": 0.95,
        "security": 0.9,
        "reporting": 0.9,
        "automation": 0.85,
        "fintech": 0.9,
        "governance": 0.9,
    },
    "gesundheit": {
        "healthcare": 1.0,
        "compliance": 0.95,
        "documentation": 0.9,
        "security": 0.9,
        "privacy": 0.95,
        "research": 0.85,
        "analytics": 0.8,
    },
    "industrie": {
        "automation": 0.95,
        "analytics": 0.9,
        "data": 0.9,
        "integration": 0.85,
        "quality": 0.85,
        "supply-chain": 0.9,
        "ml": 0.85,
    },
    "bildung": {
        "content": 0.95,
        "video": 0.9,
        "presentation": 0.9,
        "collaboration": 0.9,
        "meeting": 0.85,
        "forms": 0.85,
        "productivity": 0.85,
    },
    "marketing": {
        "marketing": 1.0,
        "content": 0.95,
        "social-media": 0.95,
        "design": 0.9,
        "seo": 0.9,
        "analytics": 0.85,
        "video": 0.85,
        "ai-generation": 0.9,
    },
    "bauwesen_architektur": {
        "construction": 1.0,
        "project-management": 0.95,
        "documentation": 0.9,
        "bim": 1.0,
        "collaboration": 0.85,
        "quality": 0.85,
        "design": 0.8,
    },
    "verwaltung": {
        "compliance": 1.0,
        "governance": 1.0,
        "documentation": 0.95,
        "forms": 0.9,
        "customer-service": 0.85,
        "security": 0.9,
        "privacy": 0.95,
    },
    "transport_logistik": {
        "logistics": 1.0,
        "supply-chain": 1.0,
        "routing": 0.95,
        "tracking": 0.95,
        "automation": 0.9,
        "analytics": 0.85,
        "optimization": 0.95,
    },
}

# Default affinity for unknown branches
DEFAULT_BRANCH_AFFINITY: Dict[str, float] = {
    "productivity": 0.8,
    "automation": 0.75,
    "content": 0.7,
    "analytics": 0.7,
    "collaboration": 0.7,
}


# =============================================================================
# SIZE FIT MAPPINGS
# =============================================================================

# Tool suitability by company size
SIZE_FIT_CRITERIA: Dict[str, Dict[str, Any]] = {
    "solo": {
        "max_complexity": "medium",
        "preferred_pricing": ["freemium", "free", "low-cost"],
        "preferred_categories": ["content", "productivity", "automation", "marketing"],
        "avoid_categories": ["enterprise", "ats", "hcm"],
        "complexity_scores": {"low": 1.0, "medium": 0.7, "high": 0.3},
    },
    "team": {
        "max_complexity": "high",
        "preferred_pricing": ["freemium", "paid", "usage-based"],
        "preferred_categories": ["collaboration", "project-management", "crm", "automation"],
        "avoid_categories": [],
        "complexity_scores": {"low": 0.9, "medium": 1.0, "high": 0.7},
    },
    "kmu": {
        "max_complexity": "high",
        "preferred_pricing": ["paid", "enterprise", "usage-based"],
        "preferred_categories": ["enterprise", "analytics", "crm", "security", "compliance"],
        "avoid_categories": [],
        "complexity_scores": {"low": 0.7, "medium": 0.9, "high": 1.0},
    },
}


# =============================================================================
# RISK FIT MAPPINGS (AI-Act Compliance)
# =============================================================================

# Categories with higher regulatory risk
HIGH_RISK_CATEGORIES = {
    "healthcare",
    "legal",
    "hr",
    "recruitment",
    "fintech",
    "compliance",
    "security",
}

# Tools with good governance/compliance features
GOVERNANCE_COMPLIANT_TOOLS = {
    "onetrust",
    "darktrace",
    "snyk",
    "great_expectations",
    "mlflow",
    "wandb",
    "contractpod",
    "harvey",
}

# Risk level modifiers
RISK_LEVEL_MODIFIERS: Dict[str, float] = {
    "low": 1.0,      # Low risk = no penalty
    "limited": 0.95,  # Limited risk = slight preference for compliant tools
    "high": 0.85,     # High risk = prefer governance-ready tools
    "critical": 0.7,  # Critical = strong preference for compliant tools
}


# =============================================================================
# FUNDING FIT MAPPINGS
# =============================================================================

# Categories that align well with common funding programs
FUNDING_ALIGNED_CATEGORIES: Dict[str, List[str]] = {
    "digitalization": ["automation", "workflow", "integration", "productivity"],
    "innovation": ["ml", "mlops", "ai-generation", "research"],
    "security": ["security", "compliance", "governance", "privacy"],
    "efficiency": ["analytics", "data", "reporting", "optimization"],
    "customer_focus": ["crm", "customer-service", "chatbot", "marketing"],
}


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def _calculate_semantic_score(
    tool: Dict[str, Any],
    usecases: List[str],
    semantic_results: Optional[Dict[str, float]] = None,
) -> Tuple[float, str]:
    """
    Calculate semantic fit score.

    Uses pre-calculated semantic search results if available,
    otherwise falls back to keyword matching.
    """
    tool_name = tool.get("name", "")

    # Use pre-calculated semantic score if available
    if semantic_results and tool_name in semantic_results:
        score = semantic_results[tool_name]
        return score, f"Semantic match: {score:.0%}"

    # Fallback: keyword matching
    tool_usecases = set(u.lower() for u in tool.get("usecases", []))
    tool_categories = set(c.lower() for c in tool.get("categories", []))
    tool_desc = tool.get("description", "").lower()

    matches = 0
    total = max(len(usecases), 1)

    for usecase in usecases:
        usecase_lower = usecase.lower()
        usecase_words = set(usecase_lower.split())

        # Check exact match
        if usecase_lower in tool_usecases:
            matches += 1
            continue

        # Check partial match in categories
        if usecase_words & tool_categories:
            matches += 0.7
            continue

        # Check description
        if any(word in tool_desc for word in usecase_words if len(word) > 3):
            matches += 0.5

    score = min(matches / total, 1.0)
    reason = f"Use case alignment: {score:.0%}"

    return score, reason


def _calculate_branch_score(
    tool: Dict[str, Any],
    branch: str,
) -> Tuple[float, str]:
    """Calculate branch fit score based on category alignment."""
    categories = tool.get("categories", [])

    # Get branch affinity map
    affinity_map = BRANCH_CATEGORY_AFFINITY.get(branch, DEFAULT_BRANCH_AFFINITY)

    if not categories:
        return 0.5, "No category data"

    # Calculate average affinity
    scores = []
    for category in categories:
        category_lower = category.lower()
        if category_lower in affinity_map:
            scores.append(affinity_map[category_lower])
        else:
            # Check partial match
            for key, value in affinity_map.items():
                if key in category_lower or category_lower in key:
                    scores.append(value * 0.8)
                    break
            else:
                scores.append(0.5)  # Neutral for unknown

    score = sum(scores) / len(scores) if scores else 0.5
    reason = f"Branch alignment ({branch}): {score:.0%}"

    return score, reason


def _calculate_size_score(
    tool: Dict[str, Any],
    size: str,
) -> Tuple[float, str]:
    """Calculate size fit score based on complexity and pricing."""
    criteria = SIZE_FIT_CRITERIA.get(size, SIZE_FIT_CRITERIA["team"])

    complexity = tool.get("complexity", "medium")
    pricing = tool.get("pricing", "unknown")
    categories = set(c.lower() for c in tool.get("categories", []))

    score = 0.5  # Base score

    # Complexity scoring
    complexity_scores = criteria.get("complexity_scores", {})
    score = complexity_scores.get(complexity, 0.5)

    # Pricing bonus/penalty
    preferred_pricing = criteria.get("preferred_pricing", [])
    if pricing in preferred_pricing:
        score = min(score + 0.1, 1.0)

    # Category preference bonus
    preferred_categories = set(criteria.get("preferred_categories", []))
    if categories & preferred_categories:
        score = min(score + 0.1, 1.0)

    # Avoid categories penalty
    avoid_categories = set(criteria.get("avoid_categories", []))
    if categories & avoid_categories:
        score = max(score - 0.2, 0.0)

    reason = f"Size fit ({size}): {score:.0%}"
    return score, reason


def _calculate_funding_score(
    tool: Dict[str, Any],
    funding_focus: List[str] = None,
) -> Tuple[float, str]:
    """Calculate funding alignment score."""
    if not funding_focus:
        funding_focus = ["digitalization", "efficiency"]

    categories = set(c.lower() for c in tool.get("categories", []))

    aligned_count = 0
    total_focus = len(funding_focus)

    for focus in funding_focus:
        aligned_categories = set(FUNDING_ALIGNED_CATEGORIES.get(focus, []))
        if categories & aligned_categories:
            aligned_count += 1

    score = aligned_count / total_focus if total_focus > 0 else 0.5
    reason = f"Funding alignment: {score:.0%}"

    return score, reason


def _calculate_risk_score(
    tool: Dict[str, Any],
    risk_level: str = "limited",
) -> Tuple[float, str]:
    """Calculate AI-Act compliance / risk fit score."""
    tool_id = tool.get("id", "").lower()
    categories = set(c.lower() for c in tool.get("categories", []))

    # Base score from risk level
    base_modifier = RISK_LEVEL_MODIFIERS.get(risk_level, 0.9)

    # Check if tool is governance-compliant
    is_compliant = tool_id in GOVERNANCE_COMPLIANT_TOOLS

    # Check if tool is in high-risk category
    is_high_risk_category = bool(categories & HIGH_RISK_CATEGORIES)

    if is_compliant:
        score = 1.0  # Full score for compliant tools
        reason = "Governance-compliant tool"
    elif is_high_risk_category and risk_level in ("high", "critical"):
        score = 0.6 * base_modifier
        reason = f"High-risk category, risk level: {risk_level}"
    else:
        score = 0.85 * base_modifier
        reason = f"Standard risk assessment: {score:.0%}"

    return score, reason


def _calculate_complexity_score(
    tool: Dict[str, Any],
    prefer_simple: bool = True,
) -> Tuple[float, str]:
    """Calculate setup complexity score."""
    complexity = tool.get("complexity", "medium")

    if prefer_simple:
        scores = {"low": 1.0, "medium": 0.75, "high": 0.5}
    else:
        scores = {"low": 0.7, "medium": 0.9, "high": 1.0}

    score = scores.get(complexity, 0.75)
    reason = f"Setup complexity ({complexity}): {score:.0%}"

    return score, reason


def _determine_fit_level(total_score: float) -> str:
    """Determine fit level from total score."""
    if total_score >= TOOLS_FIT_THRESHOLD_HIGH:
        return "high"
    elif total_score >= TOOLS_FIT_THRESHOLD_MEDIUM:
        return "medium"
    else:
        return "low"


def _generate_setup_hint(tool: Dict[str, Any], size: str) -> str:
    """Generate setup hint based on tool and company size."""
    complexity = tool.get("complexity", "medium")
    pricing = tool.get("pricing", "unknown")

    hints = []

    if complexity == "low":
        hints.append("Quick setup (< 1 hour)")
    elif complexity == "medium":
        hints.append("Moderate setup (1-3 days)")
    else:
        hints.append("Complex setup (1-2 weeks)")

    if pricing == "freemium":
        hints.append("Start with free tier")
    elif pricing == "open-source":
        hints.append("Self-hosted option available")

    if size == "solo":
        hints.append("Single-user friendly")
    elif size == "kmu":
        hints.append("Team onboarding recommended")

    return " | ".join(hints)


# =============================================================================
# MAIN SCORING FUNCTION
# =============================================================================

def calculate_tool_fit_score(
    tool: Dict[str, Any],
    branch: str,
    size: str,
    usecases: List[str] = None,
    risk_level: str = "limited",
    funding_focus: List[str] = None,
    semantic_results: Optional[Dict[str, float]] = None,
) -> ToolFitScore:
    """
    Calculate comprehensive fit score for a tool.

    Args:
        tool: Tool data dictionary
        branch: Industry branch
        size: Company size (solo/team/kmu)
        usecases: List of use case descriptions
        risk_level: AI-Act risk level
        funding_focus: Funding program focus areas
        semantic_results: Pre-calculated semantic scores

    Returns:
        ToolFitScore with all component scores
    """
    usecases = usecases or []
    funding_focus = funding_focus or ["digitalization", "efficiency"]
    prefer_simple = size == "solo"

    # Calculate component scores
    semantic_score, semantic_reason = _calculate_semantic_score(
        tool, usecases, semantic_results
    )
    branch_score, branch_reason = _calculate_branch_score(tool, branch)
    size_score, size_reason = _calculate_size_score(tool, size)
    funding_score, funding_reason = _calculate_funding_score(tool, funding_focus)
    risk_score, risk_reason = _calculate_risk_score(tool, risk_level)
    complexity_score, complexity_reason = _calculate_complexity_score(
        tool, prefer_simple
    )

    # Calculate weighted total
    total_score = (
        semantic_score * SCORE_WEIGHTS["semantic"] +
        branch_score * SCORE_WEIGHTS["branch"] +
        size_score * SCORE_WEIGHTS["size"] +
        funding_score * SCORE_WEIGHTS["funding"] +
        risk_score * SCORE_WEIGHTS["risk"] +
        complexity_score * SCORE_WEIGHTS["complexity"]
    )

    # Determine fit level
    fit_level = _determine_fit_level(total_score)

    # Collect reasons
    fit_reasons = [
        semantic_reason,
        branch_reason,
        size_reason,
    ]
    if fit_level == "high":
        fit_reasons.append(funding_reason)

    # Generate setup hint
    setup_hint = _generate_setup_hint(tool, size)

    return ToolFitScore(
        tool_name=tool.get("name", "Unknown"),
        tool_id=tool.get("id", "unknown"),
        total_score=round(total_score, 3),
        fit_level=fit_level,
        semantic_score=round(semantic_score, 3),
        branch_score=round(branch_score, 3),
        size_score=round(size_score, 3),
        funding_score=round(funding_score, 3),
        risk_score=round(risk_score, 3),
        complexity_score=round(complexity_score, 3),
        categories=tool.get("categories", []),
        description=tool.get("description", ""),
        setup_hint=setup_hint,
        fit_reasons=fit_reasons,
    )


def calculate_fit_scores_for_profile(
    branch: str,
    size: str,
    usecases: List[str] = None,
    risk_level: str = "limited",
    funding_focus: List[str] = None,
    max_results: int = 20,
) -> Tuple[List[ToolFitScore], FitAnalysis]:
    """
    Calculate fit scores for all tools based on profile.

    Args:
        branch: Industry branch
        size: Company size
        usecases: Use case descriptions
        risk_level: AI-Act risk level
        funding_focus: Funding focus areas
        max_results: Maximum results to return

    Returns:
        Tuple of (sorted tool scores, analysis summary)
    """
    from services.tools_embedding_engine import TOOL_DATABASE, semantic_search_for_usecase

    usecases = usecases or []

    # Get semantic scores if usecases provided
    semantic_results: Dict[str, float] = {}
    if usecases:
        for usecase in usecases:
            results = semantic_search_for_usecase(usecase, k=30, branch=branch)
            for result in results:
                if result.tool_name not in semantic_results:
                    semantic_results[result.tool_name] = result.similarity_score
                else:
                    semantic_results[result.tool_name] = max(
                        semantic_results[result.tool_name],
                        result.similarity_score
                    )

    # Calculate scores for all tools
    scores = []
    for tool in TOOL_DATABASE:
        score = calculate_tool_fit_score(
            tool=tool,
            branch=branch,
            size=size,
            usecases=usecases,
            risk_level=risk_level,
            funding_focus=funding_focus,
            semantic_results=semantic_results,
        )
        scores.append(score)

    # Sort by total score
    scores.sort(key=lambda x: x.total_score, reverse=True)

    # Create analysis
    high_fit = sum(1 for s in scores if s.fit_level == "high")
    medium_fit = sum(1 for s in scores if s.fit_level == "medium")
    low_fit = sum(1 for s in scores if s.fit_level == "low")

    # Get top categories
    category_counts: Dict[str, int] = {}
    for score in scores[:max_results]:
        for cat in score.categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    top_categories = sorted(
        category_counts.keys(),
        key=lambda x: category_counts[x],
        reverse=True
    )[:5]

    # Generate recommendations
    recommendations = []
    if high_fit >= 5:
        recommendations.append(f"✅ {high_fit} Tools mit hoher Passung gefunden")
    if size == "solo" and any(s.complexity_score < 0.5 for s in scores[:10]):
        recommendations.append("⚠️ Einige Top-Tools sind komplex - auf einfache Alternativen achten")
    if risk_level in ("high", "critical"):
        compliant_count = sum(1 for s in scores[:10] if s.risk_score >= 0.9)
        recommendations.append(f"🔒 {compliant_count} von Top-10 Tools sind governance-konform")

    analysis = FitAnalysis(
        branch=branch,
        size=size,
        risk_level=risk_level,
        total_tools_analyzed=len(scores),
        high_fit_count=high_fit,
        medium_fit_count=medium_fit,
        low_fit_count=low_fit,
        top_categories=top_categories,
        recommendations=recommendations,
    )

    return scores[:max_results], analysis


def get_top_fit_tools(
    branch: str,
    size: str,
    k: int = 10,
    min_fit_level: str = "medium",
) -> List[ToolFitScore]:
    """
    Get top fitting tools for a profile.

    Args:
        branch: Industry branch
        size: Company size
        k: Number of tools to return
        min_fit_level: Minimum fit level ("high", "medium", "low")

    Returns:
        List of top fitting tools
    """
    scores, _ = calculate_fit_scores_for_profile(
        branch=branch,
        size=size,
        max_results=k * 2,
    )

    # Filter by fit level
    if min_fit_level == "high":
        filtered = [s for s in scores if s.fit_level == "high"]
    elif min_fit_level == "medium":
        filtered = [s for s in scores if s.fit_level in ("high", "medium")]
    else:
        filtered = scores

    return filtered[:k]


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[B3] Tool Fit Engine loaded - thresholds: high=%.2f, medium=%.2f",
    TOOLS_FIT_THRESHOLD_HIGH,
    TOOLS_FIT_THRESHOLD_MEDIUM,
)
