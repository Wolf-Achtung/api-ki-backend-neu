# -*- coding: utf-8 -*-
"""
Sprint G25: Tools Engine 4.0 – Cost, Complexity & Compliance Upgrade
=====================================================================

Extends the existing Tools Engine 3.0 to a multi-dimensional decision engine:
- Cost Layer (licensing costs)
- Complexity Layer (setup/integration difficulty)
- Maturity Layer (tool maturity/market presence)
- Compliance Layer (AI Act + GDPR)
- Vendor Layer (vendor risk, hosting, EU conformity)
- Fit Layer (Solo / Team / KMU fit scores)

Version: 4.0.0 (Sprint G25)
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

log = logging.getLogger(__name__)

__all__ = [
    "ToolProfile",
    "evaluate_tool_v4",
    "rank_tools_v4",
    "get_tool_profile_defaults",
    "generate_tool_badges_html",
    "TOOLS_ENGINE_V4_ENABLED",
]

# =============================================================================
# CONFIGURATION (ENV)
# =============================================================================

TOOLS_ENGINE_V4_ENABLED = os.getenv("TOOLS_ENGINE_V4_ENABLED", "1").lower() in ("1", "true", "yes")

# Weights for ranking algorithm
WEIGHT_FIT = float(os.getenv("TOOLS_V4_WEIGHT_FIT", "0.30"))
WEIGHT_SCORE = float(os.getenv("TOOLS_V4_WEIGHT_SCORE", "0.25"))
WEIGHT_COMPLIANCE = float(os.getenv("TOOLS_V4_WEIGHT_COMPLIANCE", "0.20"))
WEIGHT_COST = float(os.getenv("TOOLS_V4_WEIGHT_COST", "0.15"))
WEIGHT_VENDOR = float(os.getenv("TOOLS_V4_WEIGHT_VENDOR", "0.10"))


# =============================================================================
# DATA MODEL: ToolProfile
# =============================================================================

@dataclass
class ToolProfile:
    """
    Complete tool profile with multi-dimensional scoring.

    Score interpretation:
    - cost_level: 1=very cheap/free, 5=expensive enterprise
    - complexity_level: 1=plug-and-play, 5=complex integration
    - maturity_level: 1=new/experimental, 5=market leader
    - compliance_score: 1=EU-friendly/GDPR-ok, 5=compliance risk
    - vendor_risk: 1=low risk (EU vendor), 5=high risk (unclear policies)
    - fit_*: 0.0-1.0 where 1.0 = perfect fit
    """
    name: str
    category: str
    score: float = 0.0  # Legacy score from v3

    # NEW G25 Fields
    cost_level: int = 3  # 1-5
    complexity_level: int = 3  # 1-5
    maturity_level: int = 3  # 1-5
    compliance_score: int = 3  # 1-5
    vendor_risk: int = 3  # 1-5
    eu_hosting: Optional[bool] = None  # True/False/None(Unknown)

    # Fit scores (0.0 - 1.0)
    fit_solo: float = 0.5
    fit_team: float = 0.5
    fit_kmu: float = 0.5

    # Metadata
    url: str = ""
    trust_url: str = ""
    price: str = ""
    gdpr: str = ""
    host: str = ""

    # Computed fields (set by engine)
    composite_score: float = 0.0
    rank: int = 0
    badges: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolProfile":
        """Create from dictionary."""
        # Handle eu_hosting conversion
        eu_hosting = data.get("eu_hosting")
        if isinstance(eu_hosting, str):
            eu_hosting = eu_hosting.lower() == "true" if eu_hosting.lower() != "unknown" else None

        return cls(
            name=data.get("name", ""),
            category=data.get("category", ""),
            score=float(data.get("score", 0.0)),
            cost_level=int(data.get("cost_level", 3)),
            complexity_level=int(data.get("complexity_level", 3)),
            maturity_level=int(data.get("maturity_level", 3)),
            compliance_score=int(data.get("compliance_score", 3)),
            vendor_risk=int(data.get("vendor_risk", 3)),
            eu_hosting=eu_hosting,
            fit_solo=float(data.get("fit_solo", 0.5)),
            fit_team=float(data.get("fit_team", 0.5)),
            fit_kmu=float(data.get("fit_kmu", 0.5)),
            url=data.get("url", ""),
            trust_url=data.get("trust_url", ""),
            price=data.get("price", ""),
            gdpr=data.get("gdpr", ""),
            host=data.get("host", ""),
            composite_score=float(data.get("composite_score", 0.0)),
            rank=int(data.get("rank", 0)),
            badges=data.get("badges", []),
        )


# =============================================================================
# HEURISTIC RULES DATABASE
# =============================================================================

# Cost level heuristics based on pricing patterns
COST_HEURISTICS: Dict[str, int] = {
    # Free or very cheap
    "free": 1, "kostenlos": 1, "0 €": 1, "0€": 1, "$0": 1,
    "0-": 1, "ab 0": 1, "gratis": 1,
    # Cheap
    "5 €": 2, "9 €": 2, "10 €": 2, "ab 5": 2, "ab 9": 2,
    # Moderate
    "20 €": 3, "30 €": 3, "50 €": 3, "ab 20": 3, "ab 30": 3,
    # Expensive
    "100 €": 4, "200 €": 4, "ab 100": 4, "enterprise": 4,
    # Very expensive
    "500 €": 5, "1000 €": 5, "custom": 5, "auf anfrage": 5,
}

# Complexity heuristics based on category
COMPLEXITY_BY_CATEGORY: Dict[str, int] = {
    # Easy - plug and play
    "fragebogen": 1, "intake": 1, "forms": 1,
    "ai-assistent": 1, "chatbot": 1,
    "design": 2, "canva": 1,
    # Medium
    "wissensmanagement": 2, "docs": 2, "notion": 2,
    "crm": 2, "sales": 2,
    "collaboration": 2, "kommunikation": 2,
    # Complex
    "automation": 3, "workflow": 3, "integromat": 3, "make": 3, "zapier": 3,
    "api": 3, "ki-api": 3, "openai": 3,
    # Very complex
    "ml": 4, "machine learning": 4, "mlops": 4,
    "data quality": 4, "governance": 4,
    "monitoring": 4, "observability": 4,
    # Expert level
    "infrastructure": 5, "kubernetes": 5, "deployment": 5,
}

# Maturity heuristics based on known tools
MATURITY_SCORES: Dict[str, int] = {
    # Market leaders (very mature)
    "salesforce": 5, "hubspot": 5, "microsoft": 5, "google": 5,
    "slack": 5, "notion": 5, "jira": 5, "confluence": 5,
    "datadog": 5, "splunk": 5, "tableau": 5, "power bi": 5,
    # Established players
    "make": 4, "integromat": 4, "zapier": 4, "airtable": 4,
    "monday": 4, "asana": 4, "trello": 4, "clickup": 4,
    "openai": 4, "anthropic": 4, "claude": 4,
    # Growing tools
    "n8n": 3, "tally": 3, "typeform": 3, "linear": 3,
    "perplexity": 3, "cursor": 3, "github copilot": 3,
    # Newer tools
    "railway": 2, "vercel": 3, "supabase": 3,
    # Experimental
    "experimental": 1, "beta": 1, "alpha": 1,
}

# Compliance heuristics
COMPLIANCE_HEURISTICS: Dict[str, int] = {
    # EU-friendly (low compliance risk)
    "eu-server": 1, "eu-option": 1, "eu hosting": 1,
    "gdpr-konform": 1, "dsgvo-konform": 1,
    "avv verfügbar": 1, "dpa verfügbar": 1,
    # Moderate
    "eu/us": 2, "soc2": 2, "iso 27001": 2,
    # Needs assessment
    "us (dpa)": 3, "vendor-assessment": 3,
    # Higher risk
    "us": 4, "us-only": 4,
    # Unknown/risky
    "unknown": 5, "unklar": 5, "prüfen": 5,
}

# Vendor risk based on hosting/region
VENDOR_RISK_HEURISTICS: Dict[str, int] = {
    # Low risk - EU vendors
    "eu": 1, "deutschland": 1, "germany": 1, "de": 1,
    "eu-server": 1, "eu hosting": 1,
    # Low-medium
    "eu-option": 2, "eu/us": 2,
    # Medium
    "us (dpa)": 3, "us (avv)": 3,
    # Higher risk
    "us": 4, "us-only": 4,
    # High risk
    "unknown": 5, "china": 5, "cn": 5,
}

# Fit heuristics by size
FIT_BY_SIZE: Dict[str, Dict[str, float]] = {
    # Tools particularly good for solo
    "solo_friendly": {
        "tally": 0.95, "notion": 0.9, "canva": 0.95,
        "chatgpt": 0.9, "claude": 0.9, "perplexity": 0.9,
        "make": 0.85, "zapier": 0.85, "n8n": 0.8,
    },
    # Tools particularly good for teams
    "team_friendly": {
        "slack": 0.95, "notion": 0.9, "confluence": 0.9,
        "jira": 0.85, "asana": 0.9, "monday": 0.9,
        "hubspot": 0.8, "linear": 0.9,
    },
    # Tools particularly good for KMU
    "kmu_friendly": {
        "salesforce": 0.9, "hubspot": 0.95, "datadog": 0.85,
        "mlflow": 0.8, "confluence": 0.85, "jira": 0.9,
        "power bi": 0.9, "tableau": 0.85,
    },
}


# =============================================================================
# EVALUATION FUNCTIONS
# =============================================================================

def _estimate_cost_level(tool_name: str, price: str, category: str) -> int:
    """Estimate cost level from price string and category."""
    price_lower = price.lower() if price else ""
    name_lower = tool_name.lower()

    # Check direct price patterns
    for pattern, level in COST_HEURISTICS.items():
        if pattern in price_lower:
            return level

    # Enterprise tools tend to be expensive
    if "enterprise" in name_lower or "enterprise" in category.lower():
        return 4

    # API-based tools are usage-based (moderate)
    if "api" in category.lower() or "usage" in price_lower:
        return 3

    return 3  # Default moderate


def _estimate_complexity_level(tool_name: str, category: str) -> int:
    """Estimate complexity from category and tool name."""
    name_lower = tool_name.lower()
    cat_lower = category.lower()

    # Check category patterns
    for pattern, level in COMPLEXITY_BY_CATEGORY.items():
        if pattern in cat_lower or pattern in name_lower:
            return level

    return 3  # Default moderate


def _estimate_maturity_level(tool_name: str) -> int:
    """Estimate maturity from tool name."""
    name_lower = tool_name.lower()

    for pattern, level in MATURITY_SCORES.items():
        if pattern in name_lower:
            return level

    return 3  # Default moderate


def _estimate_compliance_score(gdpr: str, host: str) -> int:
    """Estimate compliance score from GDPR and hosting info."""
    gdpr_lower = (gdpr or "").lower()
    host_lower = (host or "").lower()

    # Check GDPR patterns first
    for pattern, score in COMPLIANCE_HEURISTICS.items():
        if pattern in gdpr_lower:
            return score

    # Then check hosting
    for pattern, score in COMPLIANCE_HEURISTICS.items():
        if pattern in host_lower:
            return score

    return 3  # Default moderate


def _estimate_vendor_risk(host: str, gdpr: str) -> int:
    """Estimate vendor risk from hosting location."""
    host_lower = (host or "").lower()
    gdpr_lower = (gdpr or "").lower()

    for pattern, risk in VENDOR_RISK_HEURISTICS.items():
        if pattern in host_lower or pattern in gdpr_lower:
            return risk

    return 3  # Default moderate


def _estimate_eu_hosting(host: str, gdpr: str) -> Optional[bool]:
    """Determine if EU hosting is available."""
    host_lower = (host or "").lower()
    gdpr_lower = (gdpr or "").lower()

    if "eu" in host_lower and "us" not in host_lower:
        return True
    if "eu-server" in gdpr_lower or "eu-option" in gdpr_lower:
        return True
    if host_lower in ("us", "us-only") and "eu" not in gdpr_lower:
        return False

    return None  # Unknown


def _estimate_fit_scores(
    tool_name: str,
    category: str,
    best_for_size: Optional[List[str]] = None,
    cost_level: int = 3,
    complexity_level: int = 3,
) -> Tuple[float, float, float]:
    """
    Estimate fit scores for Solo/Team/KMU.

    Returns: (fit_solo, fit_team, fit_kmu)
    """
    name_lower = tool_name.lower()

    # Start with base scores from known tools
    fit_solo = FIT_BY_SIZE["solo_friendly"].get(name_lower, 0.5)
    fit_team = FIT_BY_SIZE["team_friendly"].get(name_lower, 0.5)
    fit_kmu = FIT_BY_SIZE["kmu_friendly"].get(name_lower, 0.5)

    # Adjust based on best_for_size if provided
    if best_for_size:
        if "solo" in best_for_size:
            fit_solo = max(fit_solo, 0.75)
        if "team" in best_for_size:
            fit_team = max(fit_team, 0.75)
        if "kmu" in best_for_size or "enterprise" in best_for_size:
            fit_kmu = max(fit_kmu, 0.75)

    # Adjust based on cost (solo prefers cheap, kmu can afford expensive)
    if cost_level <= 2:
        fit_solo = min(1.0, fit_solo + 0.15)
    elif cost_level >= 4:
        fit_solo = max(0.1, fit_solo - 0.2)
        fit_kmu = min(1.0, fit_kmu + 0.1)

    # Adjust based on complexity (solo prefers simple)
    if complexity_level <= 2:
        fit_solo = min(1.0, fit_solo + 0.1)
    elif complexity_level >= 4:
        fit_solo = max(0.1, fit_solo - 0.15)
        fit_kmu = min(1.0, fit_kmu + 0.1)

    # Ensure bounds
    return (
        round(max(0.0, min(1.0, fit_solo)), 2),
        round(max(0.0, min(1.0, fit_team)), 2),
        round(max(0.0, min(1.0, fit_kmu)), 2),
    )


def evaluate_tool_v4(
    tool_name: str,
    category: str,
    context: Optional[Dict[str, Any]] = None,
    existing_data: Optional[Dict[str, Any]] = None,
) -> ToolProfile:
    """
    Evaluate a tool and generate a complete ToolProfile with all v4 scores.

    Args:
        tool_name: Name of the tool
        category: Tool category (e.g., "Automation", "CRM")
        context: Optional context with branch, size_label, etc.
        existing_data: Optional existing tool data (url, price, etc.)

    Returns:
        ToolProfile with all dimensions evaluated
    """
    if not TOOLS_ENGINE_V4_ENABLED:
        log.debug("[G25] Tools Engine v4 disabled, returning minimal profile")
        return ToolProfile(name=tool_name, category=category)

    context = context or {}
    existing_data = existing_data or {}

    # Extract existing data
    price = existing_data.get("price", "")
    gdpr = existing_data.get("gdpr", "")
    host = existing_data.get("host", "")
    best_for_size = existing_data.get("best_for_size", [])
    legacy_score = existing_data.get("score", existing_data.get("final_score", 0.0))

    # Evaluate all dimensions
    cost_level = _estimate_cost_level(tool_name, price, category)
    complexity_level = _estimate_complexity_level(tool_name, category)
    maturity_level = _estimate_maturity_level(tool_name)
    compliance_score = _estimate_compliance_score(gdpr, host)
    vendor_risk = _estimate_vendor_risk(host, gdpr)
    eu_hosting = _estimate_eu_hosting(host, gdpr)

    fit_solo, fit_team, fit_kmu = _estimate_fit_scores(
        tool_name, category, best_for_size, cost_level, complexity_level
    )

    # Generate badges
    badges = _generate_badges(cost_level, complexity_level, compliance_score, vendor_risk, eu_hosting)

    profile = ToolProfile(
        name=tool_name,
        category=category,
        score=float(legacy_score),
        cost_level=cost_level,
        complexity_level=complexity_level,
        maturity_level=maturity_level,
        compliance_score=compliance_score,
        vendor_risk=vendor_risk,
        eu_hosting=eu_hosting,
        fit_solo=fit_solo,
        fit_team=fit_team,
        fit_kmu=fit_kmu,
        url=existing_data.get("url", ""),
        trust_url=existing_data.get("trust_url", ""),
        price=price,
        gdpr=gdpr,
        host=host,
        badges=badges,
    )

    log.debug(
        "[G25] Evaluated tool '%s': cost=%d, complexity=%d, maturity=%d, compliance=%d, vendor_risk=%d",
        tool_name, cost_level, complexity_level, maturity_level, compliance_score, vendor_risk
    )

    return profile


def _generate_badges(
    cost_level: int,
    complexity_level: int,
    compliance_score: int,
    vendor_risk: int,
    eu_hosting: Optional[bool],
) -> List[str]:
    """Generate badge identifiers based on scores."""
    badges = []

    # Cost badges
    if cost_level == 1:
        badges.append("cost-free")
    elif cost_level == 2:
        badges.append("cost-low")
    elif cost_level >= 4:
        badges.append("cost-high")

    # Complexity badges
    if complexity_level <= 2:
        badges.append("easy-setup")
    elif complexity_level >= 4:
        badges.append("complex-setup")

    # Compliance badges
    if compliance_score == 1:
        badges.append("eu-compliant")
    elif compliance_score >= 4:
        badges.append("compliance-risk")

    # EU hosting badge
    if eu_hosting is True:
        badges.append("eu-hosting")

    # Vendor risk badges
    if vendor_risk <= 2:
        badges.append("low-vendor-risk")
    elif vendor_risk >= 4:
        badges.append("high-vendor-risk")

    return badges


# =============================================================================
# RANKING FUNCTIONS
# =============================================================================

def _calculate_composite_score(
    profile: ToolProfile,
    size_label: str = "team",
) -> float:
    """
    Calculate composite score for ranking.

    The composite score considers:
    - Fit for company size (weighted highest)
    - Legacy score
    - Compliance (inverted - lower is better)
    - Cost (inverted - lower is better for solo/team)
    - Vendor risk (inverted - lower is better)
    """
    # Get fit score for the target size
    fit_score = {
        "solo": profile.fit_solo,
        "team": profile.fit_team,
        "kmu": profile.fit_kmu,
    }.get(size_label.lower(), profile.fit_team)

    # Normalize legacy score (assume 0-100 scale -> 0-1)
    normalized_score = min(1.0, profile.score / 100.0) if profile.score > 0 else 0.5

    # Invert compliance score (1 is best -> 1.0, 5 is worst -> 0.2)
    compliance_factor = (6 - profile.compliance_score) / 5.0

    # Invert cost (depends on size - solo/team prefer cheaper)
    if size_label.lower() == "solo":
        cost_factor = (6 - profile.cost_level) / 5.0
    elif size_label.lower() == "team":
        cost_factor = (6 - profile.cost_level) / 5.0 * 0.8 + 0.2
    else:  # KMU can afford more
        cost_factor = 0.5 + (6 - profile.cost_level) / 10.0

    # Invert vendor risk
    vendor_factor = (6 - profile.vendor_risk) / 5.0

    # Weighted composite
    composite = (
        WEIGHT_FIT * fit_score +
        WEIGHT_SCORE * normalized_score +
        WEIGHT_COMPLIANCE * compliance_factor +
        WEIGHT_COST * cost_factor +
        WEIGHT_VENDOR * vendor_factor
    )

    return round(composite, 4)


def rank_tools_v4(
    tools: List[ToolProfile],
    size_label: str = "team",
    branch: Optional[str] = None,
    prioritize_compliance: bool = False,
    prioritize_cost: bool = False,
) -> List[ToolProfile]:
    """
    Rank tools based on multi-dimensional scores.

    Args:
        tools: List of ToolProfile objects
        size_label: Company size ("solo", "team", "kmu")
        branch: Optional branch for context
        prioritize_compliance: If True, heavily weight compliance
        prioritize_cost: If True, heavily weight cost

    Returns:
        Sorted list of ToolProfile objects with ranks assigned
    """
    if not tools:
        return []

    # Calculate composite scores
    for tool in tools:
        tool.composite_score = _calculate_composite_score(tool, size_label)

    # Apply priority adjustments
    if prioritize_compliance:
        for tool in tools:
            if tool.compliance_score <= 2:
                tool.composite_score *= 1.2
            elif tool.compliance_score >= 4:
                tool.composite_score *= 0.7

    if prioritize_cost:
        for tool in tools:
            if tool.cost_level <= 2:
                tool.composite_score *= 1.15
            elif tool.cost_level >= 4:
                tool.composite_score *= 0.8

    # Sort by composite score (descending)
    sorted_tools = sorted(tools, key=lambda t: t.composite_score, reverse=True)

    # Assign ranks
    for i, tool in enumerate(sorted_tools, 1):
        tool.rank = i

    log.debug("[G25] Ranked %d tools for size '%s'", len(sorted_tools), size_label)

    return sorted_tools


# =============================================================================
# BATCH EVALUATION
# =============================================================================

def evaluate_tools_batch(
    tools_data: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
) -> List[ToolProfile]:
    """
    Evaluate multiple tools from raw data.

    Args:
        tools_data: List of tool dictionaries
        context: Optional context

    Returns:
        List of ToolProfile objects
    """
    profiles = []
    for tool in tools_data:
        profile = evaluate_tool_v4(
            tool_name=tool.get("name", ""),
            category=tool.get("category", ""),
            context=context,
            existing_data=tool,
        )
        profiles.append(profile)

    return profiles


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_tool_badges_html(profile: ToolProfile, compact: bool = False) -> str:
    """
    Generate HTML badges for a tool profile.

    Args:
        profile: ToolProfile object
        compact: If True, use compact badge format

    Returns:
        HTML string with badges
    """
    if not profile.badges:
        return ""

    badge_html_map = {
        # Cost badges
        "cost-free": ('<span class="tool-badge cost-level-1">Free</span>', "Free"),
        "cost-low": ('<span class="tool-badge cost-level-2">€</span>', "€"),
        "cost-high": ('<span class="tool-badge cost-level-4">€€€</span>', "€€€"),
        # Complexity badges
        "easy-setup": ('<span class="tool-badge complexity-1">Easy</span>', "Easy"),
        "complex-setup": ('<span class="tool-badge complexity-4">Complex</span>', "Adv"),
        # Compliance badges
        "eu-compliant": ('<span class="tool-badge compliance-1">EU-OK</span>', "EU"),
        "compliance-risk": ('<span class="tool-badge compliance-4">Risk</span>', "!"),
        # EU hosting
        "eu-hosting": ('<span class="tool-badge eu-hosting">EU</span>', "EU"),
        # Vendor risk
        "low-vendor-risk": ('<span class="tool-badge vendor-1">Safe</span>', "OK"),
        "high-vendor-risk": ('<span class="tool-badge vendor-4">Caution</span>', "!"),
    }

    badges_html = []
    for badge in profile.badges[:3]:  # Limit to 3 badges
        if badge in badge_html_map:
            full_badge, compact_badge = badge_html_map[badge]
            if compact:
                badges_html.append(f'<span class="tool-badge-compact">{compact_badge}</span>')
            else:
                badges_html.append(full_badge)

    return " ".join(badges_html)


def get_tool_profile_defaults() -> Dict[str, Any]:
    """Get default values for ToolProfile fields (for validation)."""
    return {
        "cost_level": {"min": 1, "max": 5, "default": 3},
        "complexity_level": {"min": 1, "max": 5, "default": 3},
        "maturity_level": {"min": 1, "max": 5, "default": 3},
        "compliance_score": {"min": 1, "max": 5, "default": 3},
        "vendor_risk": {"min": 1, "max": 5, "default": 3},
        "eu_hosting": {"type": "bool_or_null", "default": None},
        "fit_solo": {"min": 0.0, "max": 1.0, "default": 0.5},
        "fit_team": {"min": 0.0, "max": 1.0, "default": 0.5},
        "fit_kmu": {"min": 0.0, "max": 1.0, "default": 0.5},
    }


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def enhance_tool_recommendation(
    tool_data: Dict[str, Any],
    size_label: str = "team",
) -> Dict[str, Any]:
    """
    Enhance a legacy tool recommendation with v4 profile data.

    Args:
        tool_data: Legacy tool data dict
        size_label: Company size

    Returns:
        Enhanced tool data with v4 fields
    """
    profile = evaluate_tool_v4(
        tool_name=tool_data.get("name", tool_data.get("tool_name", "")),
        category=tool_data.get("category", ""),
        existing_data=tool_data,
    )

    # Calculate composite score
    profile.composite_score = _calculate_composite_score(profile, size_label)

    # Merge profile data into tool_data
    enhanced = {**tool_data, **profile.to_dict()}
    enhanced["badges_html"] = generate_tool_badges_html(profile)

    return enhanced


def get_top_tools_v4(
    tools: List[Dict[str, Any]],
    size_label: str = "team",
    limit: int = 3,
    prioritize_compliance: bool = False,
) -> List[ToolProfile]:
    """
    Get top N tools with v4 ranking.

    Args:
        tools: List of tool data dicts
        size_label: Company size
        limit: Number of tools to return
        prioritize_compliance: Prioritize compliance in ranking

    Returns:
        List of top ToolProfile objects
    """
    profiles = evaluate_tools_batch(tools)
    ranked = rank_tools_v4(
        profiles,
        size_label=size_label,
        prioritize_compliance=prioritize_compliance,
    )
    return ranked[:limit]
