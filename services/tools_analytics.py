# -*- coding: utf-8 -*-
"""
Sprint B2-A: Tools Analytics Layer
==================================

Segment-based real-world statistics for Tools recommendations.

Features:
- Aggregator: Collects tool occurrences from all reports
- Stability Metrics: Segment stability (strong/medium/weak)
- Confidence Calculation: Multi-factor confidence scoring
- ToolSegmentStats: Complete statistics per tool

Based on Premium-Funding module patterns from Sprint B1.

Version: 1.0.0 (Sprint B2)
"""
from __future__ import annotations

import json
import logging
import math
import os
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION (ENV)
# =============================================================================

TOOLS_ENGINE_ENABLED = os.environ.get("TOOLS_ENGINE_ENABLED", "1") == "1"
TOOLS_CONFIDENCE_MIN = float(os.environ.get("TOOLS_CONFIDENCE_MIN", "0.35"))
TOOLS_SEGMENT_OUTLIER_STD = float(os.environ.get("TOOLS_SEGMENT_OUTLIER_STD", "2.5"))
TOOLS_MIN_SAMPLE_SIZE = int(os.environ.get("TOOLS_MIN_SAMPLE_SIZE", "5"))
TOOLS_MAX_RECOMMENDATIONS = int(os.environ.get("TOOLS_MAX_RECOMMENDATIONS", "12"))
TOOLS_REQUIRE_RELIABLE_SEGMENT = os.environ.get("TOOLS_REQUIRE_RELIABLE_SEGMENT", "1") == "1"

# Storage for analytics data
TOOLS_ANALYTICS_STORAGE_PATH = os.environ.get(
    "TOOLS_ANALYTICS_STORAGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "storage", "tools_analytics")
)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ToolOccurrence:
    """Single tool occurrence in a report."""
    tool_name: str
    report_id: str
    timestamp: str
    branch_group: str
    size_label: str  # solo, team, kmu
    ai_act_risk: str  # minimal, limited, high-risk
    co_tools: List[str] = field(default_factory=list)


@dataclass
class ToolCoOccurrence:
    """Tools that frequently appear together."""
    tool_a: str
    tool_b: str
    occurrence_count: int
    correlation_strength: float  # 0.0 - 1.0


@dataclass
class ToolSegmentStats:
    """Complete statistics for a tool within a segment context."""
    tool_name: str
    usage_count: int = 0
    segment_usage_count: Dict[str, int] = field(default_factory=dict)
    confidence: float = 0.0
    confidence_level: str = "low"  # high, medium, low
    segment_stability: str = "weak"  # strong, medium, weak
    ai_act_alignment: float = 0.0
    persona_fit_score: float = 0.0
    recommended_rank: int = 0
    co_occurrence_tools: List[str] = field(default_factory=list)
    sample_size: int = 0
    outliers_trimmed: int = 0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SegmentAnalysis:
    """Analysis for a specific segment."""
    segment_id: str
    segment_type: str  # size_label, branch_group, ai_act_risk
    segment_value: str
    tool_count: int = 0
    report_count: int = 0
    stability: str = "weak"
    sample_size: int = 0
    mean_tools_per_report: float = 0.0
    std_tools_per_report: float = 0.0
    top_tools: List[str] = field(default_factory=list)


@dataclass
class ToolsAnalyticsSnapshot:
    """Snapshot of tools analytics at a point in time."""
    snapshot_id: str
    timestamp: str
    total_reports_analyzed: int
    total_tools_tracked: int
    segment_analyses: List[SegmentAnalysis] = field(default_factory=list)
    tool_stats: List[ToolSegmentStats] = field(default_factory=list)
    co_occurrences: List[ToolCoOccurrence] = field(default_factory=list)


# =============================================================================
# AI ACT ALIGNMENT SCORING
# =============================================================================

# Tools categorized by governance/compliance relevance
GOVERNANCE_TOOLS = {
    "high": [
        "DataDog", "Splunk", "MLflow", "DVC", "Weights & Biases",
        "Grafana", "Prometheus", "OpenTelemetry", "Seldon", "BentoML",
        "Evidently AI", "Great Expectations", "Apache Airflow", "Kubeflow",
        "TensorBoard", "Neptune.ai", "Comet", "ClearML", "Verta"
    ],
    "medium": [
        "HubSpot", "Salesforce", "Notion", "Confluence", "Jira",
        "Monday.com", "Asana", "Trello", "ClickUp", "Airtable",
        "Coda", "Linear", "Height", "Basecamp"
    ],
    "low": [
        "ChatGPT", "Claude", "Perplexity", "Midjourney", "DALL-E",
        "Canva", "Figma", "Miro", "FigJam"
    ]
}

# Tools suitable for different personas
PERSONA_FIT_TOOLS = {
    "solo": {
        "automation": ["Make (Integromat)", "Zapier", "n8n", "IFTTT", "Pipedream"],
        "productivity": ["Notion", "Obsidian", "Roam Research", "Logseq", "Craft"],
        "ai_assistants": ["ChatGPT", "Claude", "Perplexity", "Bing Chat", "Gemini"],
        "design": ["Canva", "Figma", "Adobe Express", "Looka", "Brandmark"]
    },
    "team": {
        "collaboration": ["Slack", "Microsoft Teams", "Discord", "Mattermost", "Zoom"],
        "documentation": ["Notion", "Confluence", "GitBook", "Slite", "Slab"],
        "project_mgmt": ["Jira", "Linear", "Asana", "Monday.com", "ClickUp"],
        "design": ["Figma", "Miro", "FigJam", "Lucidchart", "Whimsical"]
    },
    "kmu": {
        "data_quality": ["Great Expectations", "dbt", "Fivetran", "Airbyte", "Stitch"],
        "governance": ["Collibra", "Alation", "Atlan", "DataHub", "OpenMetadata"],
        "analytics": ["Tableau", "Power BI", "Looker", "Metabase", "Superset"],
        "security": ["Snyk", "SonarQube", "Checkmarx", "Veracode", "WhiteSource"]
    }
}


def calculate_ai_act_alignment(tool_name: str, ai_act_risk: str) -> float:
    """
    Calculate how well a tool aligns with the AI Act risk level.

    High-risk contexts need governance-heavy tools.
    Minimal-risk contexts can use lighter tools.

    Args:
        tool_name: Name of the tool
        ai_act_risk: AI Act risk classification (minimal, limited, high-risk)

    Returns:
        Alignment score 0.0 - 1.0
    """
    tool_lower = tool_name.lower()

    # Determine tool's governance level
    tool_governance = "low"
    for level, tools in GOVERNANCE_TOOLS.items():
        if any(t.lower() in tool_lower or tool_lower in t.lower() for t in tools):
            tool_governance = level
            break

    # Calculate alignment based on context
    if ai_act_risk in ("high-risk", "high"):
        # High-risk needs governance tools
        alignment_map = {"high": 1.0, "medium": 0.7, "low": 0.4}
    elif ai_act_risk == "limited":
        # Limited risk - medium tools are ideal
        alignment_map = {"high": 0.8, "medium": 1.0, "low": 0.6}
    else:  # minimal or none
        # Minimal risk - all tools acceptable
        alignment_map = {"high": 0.6, "medium": 0.8, "low": 1.0}

    return alignment_map.get(tool_governance, 0.5)


def calculate_persona_fit(tool_name: str, size_label: str) -> float:
    """
    Calculate how well a tool fits the company persona.

    Args:
        tool_name: Name of the tool
        size_label: Company size (solo, team, kmu)

    Returns:
        Persona fit score 0.0 - 1.0
    """
    size_key = size_label.lower()
    if size_key not in PERSONA_FIT_TOOLS:
        size_key = "kmu"  # Default

    tool_lower = tool_name.lower()
    persona_tools = PERSONA_FIT_TOOLS.get(size_key, {})

    # Check if tool is in the ideal list for this persona
    for category, tools in persona_tools.items():
        if any(t.lower() in tool_lower or tool_lower in t.lower() for t in tools):
            return 1.0  # Perfect fit

    # Check if tool is in other personas (partial fit)
    for other_size, other_categories in PERSONA_FIT_TOOLS.items():
        if other_size == size_key:
            continue
        for category, tools in other_categories.items():
            if any(t.lower() in tool_lower or tool_lower in t.lower() for t in tools):
                # Partial fit - tool exists but for different persona
                return 0.6

    # Unknown tool - neutral score
    return 0.5


# =============================================================================
# STABILITY CALCULATION
# =============================================================================

def calculate_segment_stability(
    values: List[float],
    min_sample_size: int = TOOLS_MIN_SAMPLE_SIZE
) -> Tuple[str, int]:
    """
    Calculate stability of a segment based on value variance.

    Uses Winsorizing to trim outliers at TOOLS_SEGMENT_OUTLIER_STD standard deviations.

    Args:
        values: List of values to analyze
        min_sample_size: Minimum samples required for stability

    Returns:
        Tuple of (stability_label, outliers_trimmed)
    """
    if len(values) < min_sample_size:
        return "weak", 0

    # Winsorize: trim outliers beyond TOOLS_SEGMENT_OUTLIER_STD standard deviations
    outliers_trimmed = 0
    if len(values) >= 3:
        try:
            mean = statistics.mean(values)
            std = statistics.stdev(values)

            if std > 0:
                lower_bound = mean - (TOOLS_SEGMENT_OUTLIER_STD * std)
                upper_bound = mean + (TOOLS_SEGMENT_OUTLIER_STD * std)

                winsorized = []
                for v in values:
                    if v < lower_bound:
                        winsorized.append(lower_bound)
                        outliers_trimmed += 1
                    elif v > upper_bound:
                        winsorized.append(upper_bound)
                        outliers_trimmed += 1
                    else:
                        winsorized.append(v)

                values = winsorized
        except statistics.StatisticsError:
            pass

    # Calculate coefficient of variation
    try:
        mean = statistics.mean(values)
        if mean > 0:
            std = statistics.stdev(values) if len(values) > 1 else 0
            cv = std / mean

            # Classify stability
            if cv < 0.3:
                return "strong", outliers_trimmed
            elif cv < 0.6:
                return "medium", outliers_trimmed
            else:
                return "weak", outliers_trimmed
    except (statistics.StatisticsError, ZeroDivisionError):
        pass

    return "weak", outliers_trimmed


# =============================================================================
# CONFIDENCE CALCULATION
# =============================================================================

def calculate_tool_confidence(
    usage_count: int,
    segment_stability: str,
    ai_act_alignment: float,
    persona_fit: float,
    sample_size: int
) -> Tuple[float, str]:
    """
    Calculate confidence score for a tool recommendation.

    Formula: confidence = base_usage × segment_stability × ai_act_alignment × persona_fit

    Confidence levels:
    - high: >= 0.70
    - medium: 0.40 - 0.69
    - low: < 0.40

    Args:
        usage_count: Number of times tool was recommended
        segment_stability: Stability of the segment (strong/medium/weak)
        ai_act_alignment: AI Act alignment score (0-1)
        persona_fit: Persona fit score (0-1)
        sample_size: Number of reports in segment

    Returns:
        Tuple of (confidence_score, confidence_level)
    """
    # Base usage score (logarithmic scale, capped at 0.4)
    base_usage = min(0.4, 0.1 + (math.log10(usage_count + 1) * 0.15))

    # Stability multiplier
    stability_multipliers = {
        "strong": 1.0,
        "medium": 0.75,
        "weak": 0.5
    }
    stability_factor = stability_multipliers.get(segment_stability, 0.5)

    # Sample size confidence boost
    if sample_size >= 30:
        sample_boost = 1.0
    elif sample_size >= 15:
        sample_boost = 0.9
    elif sample_size >= TOOLS_MIN_SAMPLE_SIZE:
        sample_boost = 0.8
    else:
        sample_boost = 0.6

    # Calculate confidence
    confidence = (
        base_usage * 0.3 +
        stability_factor * 0.2 +
        ai_act_alignment * 0.25 +
        persona_fit * 0.15 +
        sample_boost * 0.1
    )

    # Normalize to 0-1 range
    confidence = max(0.0, min(1.0, confidence))

    # Determine level
    if confidence >= 0.70:
        level = "high"
    elif confidence >= 0.40:
        level = "medium"
    else:
        level = "low"

    return confidence, level


# =============================================================================
# IN-MEMORY STORAGE
# =============================================================================

_tool_occurrences: List[ToolOccurrence] = []
_tools_snapshot: Optional[ToolsAnalyticsSnapshot] = None


def _ensure_storage_dir() -> None:
    """Ensure analytics storage directory exists."""
    Path(TOOLS_ANALYTICS_STORAGE_PATH).mkdir(parents=True, exist_ok=True)


def _get_snapshot_path() -> Path:
    """Get path to current snapshot file."""
    return Path(TOOLS_ANALYTICS_STORAGE_PATH) / "tools_analytics_snapshot.json"


def _load_snapshot() -> Optional[ToolsAnalyticsSnapshot]:
    """Load existing analytics snapshot."""
    global _tools_snapshot

    if _tools_snapshot is not None:
        return _tools_snapshot

    snapshot_path = _get_snapshot_path()
    if snapshot_path.exists():
        try:
            with open(snapshot_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Reconstruct dataclasses
                segment_analyses = [
                    SegmentAnalysis(**sa) for sa in data.get("segment_analyses", [])
                ]
                tool_stats = [
                    ToolSegmentStats(**ts) for ts in data.get("tool_stats", [])
                ]
                co_occurrences = [
                    ToolCoOccurrence(**co) for co in data.get("co_occurrences", [])
                ]

                _tools_snapshot = ToolsAnalyticsSnapshot(
                    snapshot_id=data.get("snapshot_id", ""),
                    timestamp=data.get("timestamp", ""),
                    total_reports_analyzed=data.get("total_reports_analyzed", 0),
                    total_tools_tracked=data.get("total_tools_tracked", 0),
                    segment_analyses=segment_analyses,
                    tool_stats=tool_stats,
                    co_occurrences=co_occurrences
                )
                return _tools_snapshot
        except Exception as e:
            log.error(f"Error loading tools analytics snapshot: {e}")

    return None


def _save_snapshot(snapshot: ToolsAnalyticsSnapshot) -> bool:
    """Save analytics snapshot to disk."""
    global _tools_snapshot

    try:
        _ensure_storage_dir()
        snapshot_path = _get_snapshot_path()

        data = {
            "snapshot_id": snapshot.snapshot_id,
            "timestamp": snapshot.timestamp,
            "total_reports_analyzed": snapshot.total_reports_analyzed,
            "total_tools_tracked": snapshot.total_tools_tracked,
            "segment_analyses": [asdict(sa) for sa in snapshot.segment_analyses],
            "tool_stats": [asdict(ts) for ts in snapshot.tool_stats],
            "co_occurrences": [asdict(co) for co in snapshot.co_occurrences]
        }

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        _tools_snapshot = snapshot
        return True
    except Exception as e:
        log.error(f"Error saving tools analytics snapshot: {e}")
        return False


# =============================================================================
# AGGREGATOR
# =============================================================================

def record_tool_occurrence(
    tool_name: str,
    report_id: str,
    branch_group: str,
    size_label: str,
    ai_act_risk: str,
    co_tools: Optional[List[str]] = None
) -> None:
    """
    Record a tool occurrence from a report.

    Args:
        tool_name: Name of the tool
        report_id: Unique report identifier
        branch_group: Industry/branch group
        size_label: Company size (solo, team, kmu)
        ai_act_risk: AI Act risk level
        co_tools: Other tools recommended in the same report
    """
    if not TOOLS_ENGINE_ENABLED:
        return

    occurrence = ToolOccurrence(
        tool_name=tool_name,
        report_id=report_id,
        timestamp=datetime.utcnow().isoformat(),
        branch_group=branch_group,
        size_label=size_label.lower(),
        ai_act_risk=ai_act_risk,
        co_tools=co_tools or []
    )

    _tool_occurrences.append(occurrence)
    log.debug(f"Recorded tool occurrence: {tool_name} in report {report_id}")


def aggregate_tools_statistics(
    occurrences: Optional[List[ToolOccurrence]] = None,
    size_label_filter: Optional[str] = None,
    branch_group_filter: Optional[str] = None,
    ai_act_risk_filter: Optional[str] = None
) -> ToolsAnalyticsSnapshot:
    """
    Aggregate tool occurrences into segment statistics.

    Args:
        occurrences: List of tool occurrences (uses global if None)
        size_label_filter: Filter by company size
        branch_group_filter: Filter by branch group
        ai_act_risk_filter: Filter by AI Act risk level

    Returns:
        ToolsAnalyticsSnapshot with aggregated statistics
    """
    if occurrences is None:
        occurrences = _tool_occurrences

    # Apply filters
    filtered = occurrences
    if size_label_filter:
        filtered = [o for o in filtered if o.size_label == size_label_filter.lower()]
    if branch_group_filter:
        filtered = [o for o in filtered if o.branch_group == branch_group_filter]
    if ai_act_risk_filter:
        filtered = [o for o in filtered if o.ai_act_risk == ai_act_risk_filter]

    # Count unique reports
    unique_reports = set(o.report_id for o in filtered)

    # Aggregate by tool
    tool_data: Dict[str, Dict[str, Any]] = {}
    for occ in filtered:
        if occ.tool_name not in tool_data:
            tool_data[occ.tool_name] = {
                "count": 0,
                "by_size": {},
                "by_branch": {},
                "by_risk": {},
                "co_tools": {},
                "reports": set()
            }

        data = tool_data[occ.tool_name]
        data["count"] += 1
        data["reports"].add(occ.report_id)

        # Count by segment
        data["by_size"][occ.size_label] = data["by_size"].get(occ.size_label, 0) + 1
        data["by_branch"][occ.branch_group] = data["by_branch"].get(occ.branch_group, 0) + 1
        data["by_risk"][occ.ai_act_risk] = data["by_risk"].get(occ.ai_act_risk, 0) + 1

        # Count co-occurrences
        for co_tool in occ.co_tools:
            if co_tool != occ.tool_name:
                data["co_tools"][co_tool] = data["co_tools"].get(co_tool, 0) + 1

    # Build segment analyses
    segment_analyses: List[SegmentAnalysis] = []

    # Analyze by size_label
    for size_label in ["solo", "team", "kmu"]:
        size_filtered = [o for o in filtered if o.size_label == size_label]
        if size_filtered:
            tools_per_report: Dict[str, int] = {}
            for occ in size_filtered:
                tools_per_report[occ.report_id] = tools_per_report.get(occ.report_id, 0) + 1

            values = list(tools_per_report.values())
            stability, _ = calculate_segment_stability(values)

            top_tools_in_segment = sorted(
                [(name, data["by_size"].get(size_label, 0)) for name, data in tool_data.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]

            segment_analyses.append(SegmentAnalysis(
                segment_id=f"size_{size_label}",
                segment_type="size_label",
                segment_value=size_label,
                tool_count=len(set(o.tool_name for o in size_filtered)),
                report_count=len(set(o.report_id for o in size_filtered)),
                stability=stability,
                sample_size=len(values),
                mean_tools_per_report=statistics.mean(values) if values else 0,
                std_tools_per_report=statistics.stdev(values) if len(values) > 1 else 0,
                top_tools=[t[0] for t in top_tools_in_segment]
            ))

    # Build tool statistics
    tool_stats: List[ToolSegmentStats] = []

    # Determine context for alignment/fit calculation
    context_size = size_label_filter or "kmu"
    context_risk = ai_act_risk_filter or "minimal"

    for tool_name, data in tool_data.items():
        # Calculate segment stability for this tool
        usage_values = list(data["by_size"].values())
        stability, outliers = calculate_segment_stability(usage_values)

        # Calculate scores
        ai_alignment = calculate_ai_act_alignment(tool_name, context_risk)
        persona_fit = calculate_persona_fit(tool_name, context_size)

        # Calculate confidence
        confidence, confidence_level = calculate_tool_confidence(
            usage_count=data["count"],
            segment_stability=stability,
            ai_act_alignment=ai_alignment,
            persona_fit=persona_fit,
            sample_size=len(data["reports"])
        )

        # Get top co-occurring tools
        top_co_tools = sorted(
            data["co_tools"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        tool_stats.append(ToolSegmentStats(
            tool_name=tool_name,
            usage_count=data["count"],
            segment_usage_count=data["by_size"],
            confidence=round(confidence, 3),
            confidence_level=confidence_level,
            segment_stability=stability,
            ai_act_alignment=round(ai_alignment, 3),
            persona_fit_score=round(persona_fit, 3),
            co_occurrence_tools=[t[0] for t in top_co_tools],
            sample_size=len(data["reports"]),
            outliers_trimmed=outliers
        ))

    # Sort by confidence and assign ranks
    tool_stats.sort(key=lambda x: x.confidence, reverse=True)
    for i, ts in enumerate(tool_stats):
        ts.recommended_rank = i + 1

    # Build co-occurrence list
    co_occurrences: List[ToolCoOccurrence] = []
    processed_pairs: Set[Tuple[str, str]] = set()

    for tool_name, data in tool_data.items():
        for co_tool, count in data["co_tools"].items():
            pair = tuple(sorted([tool_name, co_tool]))
            if pair not in processed_pairs:
                processed_pairs.add(pair)

                # Calculate correlation strength
                tool_a_count = tool_data.get(tool_name, {}).get("count", 1)
                tool_b_count = tool_data.get(co_tool, {}).get("count", 1)
                expected = (tool_a_count * tool_b_count) / max(len(unique_reports), 1)
                correlation = min(1.0, count / max(expected, 1))

                co_occurrences.append(ToolCoOccurrence(
                    tool_a=pair[0],
                    tool_b=pair[1],
                    occurrence_count=count,
                    correlation_strength=round(correlation, 3)
                ))

    # Sort co-occurrences by count
    co_occurrences.sort(key=lambda x: x.occurrence_count, reverse=True)

    # Create snapshot
    snapshot = ToolsAnalyticsSnapshot(
        snapshot_id=f"tools_snap_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.utcnow().isoformat(),
        total_reports_analyzed=len(unique_reports),
        total_tools_tracked=len(tool_stats),
        segment_analyses=segment_analyses,
        tool_stats=tool_stats,
        co_occurrences=co_occurrences[:50]  # Top 50 co-occurrences
    )

    # Save snapshot
    _save_snapshot(snapshot)

    return snapshot


# =============================================================================
# QUERY API
# =============================================================================

def get_tool_stats(
    tool_name: str,
    size_label: Optional[str] = None
) -> Optional[ToolSegmentStats]:
    """
    Get statistics for a specific tool.

    Args:
        tool_name: Name of the tool
        size_label: Optional size label filter

    Returns:
        ToolSegmentStats or None
    """
    snapshot = _load_snapshot()
    if not snapshot:
        return None

    for ts in snapshot.tool_stats:
        if ts.tool_name.lower() == tool_name.lower():
            return ts

    return None


def get_top_tools(
    size_label: Optional[str] = None,
    ai_act_risk: Optional[str] = None,
    min_confidence: float = TOOLS_CONFIDENCE_MIN,
    limit: int = TOOLS_MAX_RECOMMENDATIONS
) -> List[ToolSegmentStats]:
    """
    Get top recommended tools.

    Args:
        size_label: Filter by company size
        ai_act_risk: Filter by AI Act risk level
        min_confidence: Minimum confidence threshold
        limit: Maximum number of tools to return

    Returns:
        List of ToolSegmentStats
    """
    snapshot = _load_snapshot()
    if not snapshot:
        return []

    tools = snapshot.tool_stats

    # Filter by confidence
    tools = [t for t in tools if t.confidence >= min_confidence]

    # If filtering by size, recalculate persona fit and re-sort
    if size_label:
        for tool in tools:
            tool.persona_fit_score = calculate_persona_fit(tool.tool_name, size_label)

    # If filtering by risk, recalculate alignment
    if ai_act_risk:
        for tool in tools:
            tool.ai_act_alignment = calculate_ai_act_alignment(tool.tool_name, ai_act_risk)

    # Re-sort by combined score
    tools.sort(
        key=lambda t: t.confidence * t.persona_fit_score * t.ai_act_alignment,
        reverse=True
    )

    return tools[:limit]


def get_segment_analysis(segment_type: str, segment_value: str) -> Optional[SegmentAnalysis]:
    """
    Get analysis for a specific segment.

    Args:
        segment_type: Type of segment (size_label, branch_group, ai_act_risk)
        segment_value: Value of the segment

    Returns:
        SegmentAnalysis or None
    """
    snapshot = _load_snapshot()
    if not snapshot:
        return None

    for sa in snapshot.segment_analyses:
        if sa.segment_type == segment_type and sa.segment_value == segment_value:
            return sa

    return None


def get_co_occurring_tools(tool_name: str, limit: int = 5) -> List[Tuple[str, int]]:
    """
    Get tools that frequently co-occur with a given tool.

    Args:
        tool_name: Name of the tool
        limit: Maximum number of co-occurring tools

    Returns:
        List of (tool_name, occurrence_count) tuples
    """
    snapshot = _load_snapshot()
    if not snapshot:
        return []

    co_tools: List[Tuple[str, int]] = []
    for co in snapshot.co_occurrences:
        if co.tool_a.lower() == tool_name.lower():
            co_tools.append((co.tool_b, co.occurrence_count))
        elif co.tool_b.lower() == tool_name.lower():
            co_tools.append((co.tool_a, co.occurrence_count))

    co_tools.sort(key=lambda x: x[1], reverse=True)
    return co_tools[:limit]


def get_analytics_overview() -> Dict[str, Any]:
    """
    Get overview of tools analytics.

    Returns:
        Dict with analytics overview
    """
    snapshot = _load_snapshot()

    if not snapshot:
        return {
            "enabled": TOOLS_ENGINE_ENABLED,
            "has_data": False,
            "message": "No analytics data available"
        }

    # Calculate confidence distribution
    confidence_dist = {"high": 0, "medium": 0, "low": 0}
    for ts in snapshot.tool_stats:
        confidence_dist[ts.confidence_level] += 1

    # Calculate stability distribution
    stability_dist = {"strong": 0, "medium": 0, "weak": 0}
    for ts in snapshot.tool_stats:
        stability_dist[ts.segment_stability] += 1

    return {
        "enabled": TOOLS_ENGINE_ENABLED,
        "has_data": True,
        "snapshot_id": snapshot.snapshot_id,
        "timestamp": snapshot.timestamp,
        "total_reports_analyzed": snapshot.total_reports_analyzed,
        "total_tools_tracked": snapshot.total_tools_tracked,
        "segment_count": len(snapshot.segment_analyses),
        "confidence_distribution": confidence_dist,
        "stability_distribution": stability_dist,
        "top_5_tools": [ts.tool_name for ts in snapshot.tool_stats[:5]],
        "config": {
            "min_confidence": TOOLS_CONFIDENCE_MIN,
            "min_sample_size": TOOLS_MIN_SAMPLE_SIZE,
            "outlier_std": TOOLS_SEGMENT_OUTLIER_STD,
            "max_recommendations": TOOLS_MAX_RECOMMENDATIONS
        }
    }


# =============================================================================
# SAMPLE DATA GENERATOR (for testing/demo)
# =============================================================================

def generate_sample_data(num_reports: int = 100) -> None:
    """
    Generate sample tool occurrence data for testing.

    Args:
        num_reports: Number of sample reports to generate
    """
    import random

    sample_tools = [
        "Notion", "Make (Integromat)", "Zapier", "Slack", "HubSpot",
        "ChatGPT", "Claude", "Perplexity", "Figma", "Canva",
        "Jira", "Asana", "Monday.com", "Linear", "ClickUp",
        "DataDog", "Grafana", "Great Expectations", "dbt", "Airbyte"
    ]

    size_labels = ["solo", "team", "kmu"]
    branch_groups = ["beratung", "it", "handel", "dienstleistungen", "manufacturing"]
    ai_act_risks = ["minimal", "limited", "high-risk"]

    for i in range(num_reports):
        report_id = f"sample_report_{i:04d}"
        size_label = random.choice(size_labels)
        branch_group = random.choice(branch_groups)
        ai_act_risk = random.choice(ai_act_risks)

        # Select 3-7 tools for this report
        num_tools = random.randint(3, 7)
        selected_tools = random.sample(sample_tools, num_tools)

        for tool in selected_tools:
            co_tools = [t for t in selected_tools if t != tool]
            record_tool_occurrence(
                tool_name=tool,
                report_id=report_id,
                branch_group=branch_group,
                size_label=size_label,
                ai_act_risk=ai_act_risk,
                co_tools=co_tools
            )

    log.info(f"Generated {num_reports} sample reports with tool data")
