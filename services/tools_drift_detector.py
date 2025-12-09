# -*- coding: utf-8 -*-
"""
Sprint B2-D: Tools Drift Detector
=================================

Detects drift in tool recommendations across reports.

Drift Dimensions:
- Tools-Diversity Drift: Sudden changes in tool variety
- Tools-Overpopulation: Too many tools (>14)
- Governance-Mismatch: Risk level vs tools-group mismatch
- Persona-Drift: Toolset inappropriate for persona

Auto-Freeze Rules:
- Freeze when tools confidence <0.20 in 2+ segments
- Freeze when drift score >75
- Recovery: revert to last stable toolset

Version: 1.0.0 (Sprint B2)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

TOOLS_DRIFT_ENABLED = os.environ.get("TOOLS_DRIFT_ENABLED", "1") == "1"
TOOLS_DRIFT_THRESHOLD_LOW = int(os.environ.get("TOOLS_DRIFT_THRESHOLD_LOW", "15"))
TOOLS_DRIFT_THRESHOLD_MEDIUM = int(os.environ.get("TOOLS_DRIFT_THRESHOLD_MEDIUM", "30"))
TOOLS_DRIFT_THRESHOLD_HIGH = int(os.environ.get("TOOLS_DRIFT_THRESHOLD_HIGH", "50"))
TOOLS_DRIFT_THRESHOLD_CRITICAL = int(os.environ.get("TOOLS_DRIFT_THRESHOLD_CRITICAL", "75"))

TOOLS_FREEZE_CONFIDENCE_THRESHOLD = float(os.environ.get("TOOLS_FREEZE_CONFIDENCE_THRESHOLD", "0.20"))
TOOLS_FREEZE_SEGMENT_COUNT = int(os.environ.get("TOOLS_FREEZE_SEGMENT_COUNT", "2"))
TOOLS_OVERPOPULATION_LIMIT = int(os.environ.get("TOOLS_OVERPOPULATION_LIMIT", "14"))

# Storage
TOOLS_DRIFT_STORAGE_PATH = os.environ.get(
    "TOOLS_DRIFT_STORAGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "storage", "tools_drift")
)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ToolsDriftResult:
    """Result of a single drift check."""
    drift_type: str
    score: int = 0  # 0-100
    issues: List[str] = field(default_factory=list)
    affected_tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolsDriftAnalysis:
    """Complete drift analysis for tools."""
    analysis_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Individual drift scores (0-100 each)
    diversity_drift_score: int = 0
    overpopulation_score: int = 0
    governance_mismatch_score: int = 0
    persona_drift_score: int = 0

    # Combined score
    total_drift_score: int = 0
    drift_category: str = "MINIMAL"  # MINIMAL, LOW, MEDIUM, HIGH, CRITICAL

    # Details
    diversity_issues: List[str] = field(default_factory=list)
    overpopulation_issues: List[str] = field(default_factory=list)
    governance_issues: List[str] = field(default_factory=list)
    persona_issues: List[str] = field(default_factory=list)

    # Flags
    requires_freeze: bool = False
    requires_review: bool = False
    auto_recovery_possible: bool = True

    # Context
    segment_context: Dict[str, str] = field(default_factory=dict)
    affected_tools: List[str] = field(default_factory=list)


@dataclass
class ToolsCheckpoint:
    """Checkpoint of stable tools configuration."""
    checkpoint_id: str
    timestamp: str
    tools: List[Dict[str, Any]]
    segment_context: Dict[str, str]
    confidence_stats: Dict[str, float]
    is_stable: bool = True


# =============================================================================
# GOVERNANCE TOOLS MAPPING
# =============================================================================

# Tools expected for different risk levels
EXPECTED_TOOLS_BY_RISK: Dict[str, Dict[str, List[str]]] = {
    "high-risk": {
        "required_categories": ["Monitoring", "Governance", "Data Quality", "ML Lifecycle"],
        "required_tools": ["MLflow", "DataDog", "Great Expectations", "Grafana"],
        "forbidden_tools": []  # No specific tools forbidden
    },
    "limited": {
        "required_categories": ["Documentation", "CRM", "Monitoring"],
        "required_tools": [],
        "forbidden_tools": []
    },
    "minimal": {
        "required_categories": [],
        "required_tools": [],
        "forbidden_tools": []
    }
}

# Tools categorized for persona checks
PERSONA_TOOLS = {
    "solo": {
        "appropriate": [
            "Tally.so", "Make (Integromat)", "Zapier", "Notion", "Obsidian",
            "ChatGPT", "Claude", "Perplexity", "Canva", "Figma"
        ],
        "inappropriate": [
            "Collibra", "Alation", "ServiceNow", "SAP MDM", "Informatica",
            "Talend", "TIBCO", "IBM DataStage"
        ]
    },
    "team": {
        "appropriate": [
            "Slack", "Microsoft Teams", "Notion", "Confluence", "Jira",
            "Asana", "Monday.com", "HubSpot", "Figma", "Miro"
        ],
        "inappropriate": [
            "Collibra", "SAP MDM", "IBM DataStage", "Informatica MDM"
        ]
    },
    "kmu": {
        "appropriate": [
            "HubSpot", "Salesforce", "DataDog", "Grafana", "Great Expectations",
            "dbt", "Airbyte", "Tableau", "Power BI", "Metabase"
        ],
        "inappropriate": []  # KMU can use most tools
    }
}


# =============================================================================
# DRIFT DETECTION FUNCTIONS
# =============================================================================

def detect_diversity_drift(
    current_tools: List[Dict[str, Any]],
    previous_tools: List[Dict[str, Any]]
) -> ToolsDriftResult:
    """
    Detect diversity drift - sudden changes in tool variety.

    Args:
        current_tools: Current tool recommendations
        previous_tools: Previous tool recommendations

    Returns:
        ToolsDriftResult with diversity drift analysis
    """
    result = ToolsDriftResult(drift_type="diversity")

    if not previous_tools:
        return result  # No baseline to compare

    current_names = set(t.get("name", "") for t in current_tools)
    previous_names = set(t.get("name", "") for t in previous_tools)

    # Calculate changes
    added = current_names - previous_names
    removed = previous_names - current_names
    unchanged = current_names & previous_names

    total_change = len(added) + len(removed)
    change_ratio = total_change / max(len(previous_names), 1)

    # Score calculation
    score = 0
    if change_ratio > 0.7:
        score = 80
        result.issues.append(f"Massive tool change: {change_ratio:.0%} of tools changed")
    elif change_ratio > 0.5:
        score = 50
        result.issues.append(f"Significant tool change: {change_ratio:.0%} of tools changed")
    elif change_ratio > 0.3:
        score = 25
        result.issues.append(f"Moderate tool change: {change_ratio:.0%} of tools changed")

    # Category diversity check
    current_cats = set(t.get("category", "") for t in current_tools)
    previous_cats = set(t.get("category", "") for t in previous_tools)

    cats_added = current_cats - previous_cats
    cats_removed = previous_cats - current_cats

    if len(cats_removed) > 2:
        score += 15
        result.issues.append(f"Lost {len(cats_removed)} tool categories")

    result.score = min(100, score)
    result.affected_tools = list(added | removed)
    result.metadata = {
        "added": list(added),
        "removed": list(removed),
        "unchanged": list(unchanged),
        "change_ratio": change_ratio
    }

    return result


def detect_overpopulation(
    tools: List[Dict[str, Any]],
    limit: int = TOOLS_OVERPOPULATION_LIMIT
) -> ToolsDriftResult:
    """
    Detect tools overpopulation (>14 tools).

    Args:
        tools: List of tool recommendations
        limit: Maximum allowed tools

    Returns:
        ToolsDriftResult with overpopulation analysis
    """
    result = ToolsDriftResult(drift_type="overpopulation")

    tool_count = len(tools)

    if tool_count <= limit:
        return result

    excess = tool_count - limit
    score = min(100, excess * 10)  # 10 points per excess tool

    result.score = score
    result.issues.append(f"Tool overpopulation: {tool_count} tools (limit: {limit})")
    result.affected_tools = [t.get("name", "") for t in tools[limit:]]
    result.metadata = {
        "tool_count": tool_count,
        "limit": limit,
        "excess": excess
    }

    return result


def detect_governance_mismatch(
    tools: List[Dict[str, Any]],
    ai_act_risk: str
) -> ToolsDriftResult:
    """
    Detect governance mismatch between risk level and recommended tools.

    Args:
        tools: List of tool recommendations
        ai_act_risk: AI Act risk classification

    Returns:
        ToolsDriftResult with governance mismatch analysis
    """
    result = ToolsDriftResult(drift_type="governance_mismatch")

    risk_key = ai_act_risk.lower()
    if risk_key not in EXPECTED_TOOLS_BY_RISK:
        risk_key = "minimal"

    expected = EXPECTED_TOOLS_BY_RISK[risk_key]
    required_cats = expected["required_categories"]
    required_tools = expected["required_tools"]

    if not required_cats and not required_tools:
        return result  # No requirements for this risk level

    # Check category coverage
    tool_cats = set(t.get("category", "") for t in tools)
    tool_names = set(t.get("name", "") for t in tools)

    missing_cats = []
    for cat in required_cats:
        if not any(cat.lower() in tc.lower() for tc in tool_cats):
            missing_cats.append(cat)

    missing_tools = []
    for tool in required_tools:
        if not any(tool.lower() in tn.lower() for tn in tool_names):
            missing_tools.append(tool)

    # Score calculation
    score = 0
    if missing_cats:
        score += len(missing_cats) * 15
        result.issues.append(f"Missing governance categories: {', '.join(missing_cats)}")

    if missing_tools:
        score += len(missing_tools) * 10
        result.issues.append(f"Missing governance tools: {', '.join(missing_tools)}")

    result.score = min(100, score)
    result.affected_tools = missing_tools
    result.metadata = {
        "risk_level": ai_act_risk,
        "missing_categories": missing_cats,
        "missing_tools": missing_tools,
        "present_categories": list(tool_cats)
    }

    return result


def detect_persona_drift(
    tools: List[Dict[str, Any]],
    size_label: str
) -> ToolsDriftResult:
    """
    Detect persona drift - toolset inappropriate for persona.

    Example: Solo profile recommending enterprise MDM tools.

    Args:
        tools: List of tool recommendations
        size_label: Company size (solo, team, kmu)

    Returns:
        ToolsDriftResult with persona drift analysis
    """
    result = ToolsDriftResult(drift_type="persona_drift")

    size_key = size_label.lower()
    if size_key not in PERSONA_TOOLS:
        size_key = "kmu"

    persona_config = PERSONA_TOOLS[size_key]
    inappropriate = persona_config.get("inappropriate", [])

    if not inappropriate:
        return result  # No inappropriate tools for this persona

    tool_names = [t.get("name", "") for t in tools]

    found_inappropriate = []
    for tool_name in tool_names:
        for inapp in inappropriate:
            if inapp.lower() in tool_name.lower():
                found_inappropriate.append(tool_name)
                break

    if found_inappropriate:
        score = len(found_inappropriate) * 25  # 25 points per inappropriate tool
        result.score = min(100, score)
        result.issues.append(
            f"Inappropriate tools for '{size_label}' persona: {', '.join(found_inappropriate)}"
        )
        result.affected_tools = found_inappropriate
        result.metadata = {
            "persona": size_label,
            "inappropriate_tools": found_inappropriate
        }

    return result


# =============================================================================
# COMBINED DRIFT ANALYSIS
# =============================================================================

def analyze_tools_drift(
    current_tools: List[Dict[str, Any]],
    previous_tools: Optional[List[Dict[str, Any]]] = None,
    size_label: str = "kmu",
    ai_act_risk: str = "minimal"
) -> ToolsDriftAnalysis:
    """
    Perform complete drift analysis on tool recommendations.

    Args:
        current_tools: Current tool recommendations
        previous_tools: Previous tool recommendations (for comparison)
        size_label: Company size
        ai_act_risk: AI Act risk level

    Returns:
        ToolsDriftAnalysis with complete analysis
    """
    analysis = ToolsDriftAnalysis(
        analysis_id=f"tools_drift_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        segment_context={
            "size_label": size_label,
            "ai_act_risk": ai_act_risk
        }
    )

    if not TOOLS_DRIFT_ENABLED:
        return analysis

    # Run all drift detections
    diversity = detect_diversity_drift(current_tools, previous_tools or [])
    overpopulation = detect_overpopulation(current_tools)
    governance = detect_governance_mismatch(current_tools, ai_act_risk)
    persona = detect_persona_drift(current_tools, size_label)

    # Collect scores
    analysis.diversity_drift_score = diversity.score
    analysis.overpopulation_score = overpopulation.score
    analysis.governance_mismatch_score = governance.score
    analysis.persona_drift_score = persona.score

    # Collect issues
    analysis.diversity_issues = diversity.issues
    analysis.overpopulation_issues = overpopulation.issues
    analysis.governance_issues = governance.issues
    analysis.persona_issues = persona.issues

    # Collect affected tools
    all_affected = set()
    for result in [diversity, overpopulation, governance, persona]:
        all_affected.update(result.affected_tools)
    analysis.affected_tools = list(all_affected)

    # Calculate total drift score (weighted average)
    total = (
        diversity.score * 0.25 +
        overpopulation.score * 0.20 +
        governance.score * 0.30 +
        persona.score * 0.25
    )
    analysis.total_drift_score = min(int(total), 100)

    # Categorize drift
    if analysis.total_drift_score >= TOOLS_DRIFT_THRESHOLD_CRITICAL:
        analysis.drift_category = "CRITICAL"
        analysis.requires_freeze = True
        analysis.requires_review = True
    elif analysis.total_drift_score >= TOOLS_DRIFT_THRESHOLD_HIGH:
        analysis.drift_category = "HIGH"
        analysis.requires_review = True
    elif analysis.total_drift_score >= TOOLS_DRIFT_THRESHOLD_MEDIUM:
        analysis.drift_category = "MEDIUM"
    elif analysis.total_drift_score >= TOOLS_DRIFT_THRESHOLD_LOW:
        analysis.drift_category = "LOW"
    else:
        analysis.drift_category = "MINIMAL"

    return analysis


# =============================================================================
# AUTO-FREEZE & RECOVERY
# =============================================================================

_tools_checkpoints: Dict[str, ToolsCheckpoint] = {}
_frozen_segments: Set[str] = set()


def check_freeze_conditions(
    segment_confidences: Dict[str, float],
    drift_analysis: ToolsDriftAnalysis
) -> Tuple[bool, str]:
    """
    Check if auto-freeze conditions are met.

    Freeze conditions:
    - Confidence <0.20 in 2+ segments
    - Drift score >75

    Args:
        segment_confidences: Dict of segment -> avg confidence
        drift_analysis: Current drift analysis

    Returns:
        Tuple of (should_freeze, reason)
    """
    # Check confidence threshold
    low_conf_segments = [
        seg for seg, conf in segment_confidences.items()
        if conf < TOOLS_FREEZE_CONFIDENCE_THRESHOLD
    ]

    if len(low_conf_segments) >= TOOLS_FREEZE_SEGMENT_COUNT:
        return True, f"Low confidence in {len(low_conf_segments)} segments: {', '.join(low_conf_segments)}"

    # Check drift score
    if drift_analysis.total_drift_score >= TOOLS_DRIFT_THRESHOLD_CRITICAL:
        return True, f"Critical drift detected: score {drift_analysis.total_drift_score}"

    return False, ""


def create_checkpoint(
    segment_id: str,
    tools: List[Dict[str, Any]],
    segment_context: Dict[str, str],
    confidence_stats: Dict[str, float]
) -> ToolsCheckpoint:
    """
    Create a stable checkpoint for tools.

    Args:
        segment_id: Segment identifier
        tools: Current tools list
        segment_context: Segment context
        confidence_stats: Confidence statistics

    Returns:
        ToolsCheckpoint
    """
    checkpoint = ToolsCheckpoint(
        checkpoint_id=f"tools_cp_{segment_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.utcnow().isoformat(),
        tools=tools,
        segment_context=segment_context,
        confidence_stats=confidence_stats
    )

    _tools_checkpoints[segment_id] = checkpoint

    # Save to disk
    _save_checkpoint(checkpoint)

    log.info(f"Created tools checkpoint: {checkpoint.checkpoint_id}")
    return checkpoint


def freeze_segment(segment_id: str, reason: str) -> Dict[str, Any]:
    """
    Freeze a segment's tools recommendations.

    Args:
        segment_id: Segment to freeze
        reason: Reason for freeze

    Returns:
        Dict with freeze status
    """
    _frozen_segments.add(segment_id)

    log.warning(f"Frozen tools segment '{segment_id}': {reason}")

    return {
        "frozen": True,
        "segment_id": segment_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }


def recover_segment(segment_id: str) -> Dict[str, Any]:
    """
    Recover a frozen segment to last stable checkpoint.

    Args:
        segment_id: Segment to recover

    Returns:
        Dict with recovery status and tools
    """
    if segment_id not in _frozen_segments:
        return {
            "recovered": False,
            "reason": "Segment not frozen"
        }

    checkpoint = _tools_checkpoints.get(segment_id)
    if not checkpoint:
        checkpoint = _load_checkpoint(segment_id)

    if not checkpoint:
        return {
            "recovered": False,
            "reason": "No checkpoint available for recovery"
        }

    _frozen_segments.discard(segment_id)

    log.info(f"Recovered tools segment '{segment_id}' from checkpoint {checkpoint.checkpoint_id}")

    return {
        "recovered": True,
        "segment_id": segment_id,
        "checkpoint_id": checkpoint.checkpoint_id,
        "tools": checkpoint.tools,
        "timestamp": datetime.utcnow().isoformat()
    }


def is_segment_frozen(segment_id: str) -> bool:
    """Check if a segment is frozen."""
    return segment_id in _frozen_segments


def get_stable_tools(segment_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get stable tools from last checkpoint.

    Args:
        segment_id: Segment identifier

    Returns:
        List of tools from checkpoint or None
    """
    checkpoint = _tools_checkpoints.get(segment_id)
    if not checkpoint:
        checkpoint = _load_checkpoint(segment_id)

    if checkpoint:
        return checkpoint.tools
    return None


# =============================================================================
# PERSISTENCE
# =============================================================================

def _ensure_storage_dir() -> None:
    """Ensure storage directory exists."""
    Path(TOOLS_DRIFT_STORAGE_PATH).mkdir(parents=True, exist_ok=True)


def _get_checkpoint_path(segment_id: str) -> Path:
    """Get path for checkpoint file."""
    return Path(TOOLS_DRIFT_STORAGE_PATH) / f"checkpoint_{segment_id}.json"


def _save_checkpoint(checkpoint: ToolsCheckpoint) -> bool:
    """Save checkpoint to disk."""
    try:
        _ensure_storage_dir()
        # Extract segment_id from checkpoint_id
        parts = checkpoint.checkpoint_id.split("_")
        segment_id = parts[2] if len(parts) > 2 else "default"

        file_path = _get_checkpoint_path(segment_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(checkpoint), f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log.error(f"Error saving checkpoint: {e}")
        return False


def _load_checkpoint(segment_id: str) -> Optional[ToolsCheckpoint]:
    """Load checkpoint from disk."""
    try:
        file_path = _get_checkpoint_path(segment_id)
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ToolsCheckpoint(**data)
    except Exception as e:
        log.error(f"Error loading checkpoint: {e}")
    return None


def save_drift_analysis(analysis: ToolsDriftAnalysis) -> bool:
    """Save drift analysis to disk."""
    try:
        _ensure_storage_dir()
        file_path = Path(TOOLS_DRIFT_STORAGE_PATH) / f"drift_{analysis.analysis_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(analysis), f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log.error(f"Error saving drift analysis: {e}")
        return False


# =============================================================================
# API FUNCTIONS
# =============================================================================

def get_drift_summary(analysis: ToolsDriftAnalysis) -> Dict[str, Any]:
    """Get summary dict of drift analysis."""
    return {
        "analysis_id": analysis.analysis_id,
        "total_drift_score": analysis.total_drift_score,
        "drift_category": analysis.drift_category,
        "diversity_score": analysis.diversity_drift_score,
        "overpopulation_score": analysis.overpopulation_score,
        "governance_score": analysis.governance_mismatch_score,
        "persona_score": analysis.persona_drift_score,
        "requires_freeze": analysis.requires_freeze,
        "requires_review": analysis.requires_review,
        "affected_tools_count": len(analysis.affected_tools),
        "issue_count": (
            len(analysis.diversity_issues) +
            len(analysis.overpopulation_issues) +
            len(analysis.governance_issues) +
            len(analysis.persona_issues)
        )
    }


def get_frozen_segments() -> List[str]:
    """Get list of all frozen segments."""
    return list(_frozen_segments)


def get_drift_dashboard() -> Dict[str, Any]:
    """Get drift dashboard data."""
    return {
        "enabled": TOOLS_DRIFT_ENABLED,
        "frozen_segments": list(_frozen_segments),
        "frozen_count": len(_frozen_segments),
        "checkpoints_count": len(_tools_checkpoints),
        "thresholds": {
            "low": TOOLS_DRIFT_THRESHOLD_LOW,
            "medium": TOOLS_DRIFT_THRESHOLD_MEDIUM,
            "high": TOOLS_DRIFT_THRESHOLD_HIGH,
            "critical": TOOLS_DRIFT_THRESHOLD_CRITICAL
        },
        "freeze_config": {
            "confidence_threshold": TOOLS_FREEZE_CONFIDENCE_THRESHOLD,
            "segment_count": TOOLS_FREEZE_SEGMENT_COUNT
        }
    }
