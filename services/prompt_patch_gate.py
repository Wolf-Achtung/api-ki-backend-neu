# -*- coding: utf-8 -*-
"""
Sprint G17.6-C: Pre-Patch Approval Engine (Patch Gate)

Controls which patches can be automatically applied based on:
- Drift score analysis
- Segment impact analysis
- Risk level matrix (Solo/Team/KMU x Branch x AI-Act Risk)

Decision outcomes:
- AUTO_APPROVE: Low drift + Low impact
- LOG_AND_APPROVE: Medium drift + Low impact
- BLOCK_FOR_REVIEW: High drift or High impact
- HARD_STOP: Critical drift

Version: 1.0.0 (Sprint G17.6)
"""
from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

PROMPT_GOVERNANCE_ENABLED = os.environ.get("PROMPT_GOVERNANCE_ENABLED", "1") == "1"
PROMPT_DRAFT_MODE = os.environ.get("PROMPT_DRAFT_MODE", "0") == "1"
PROMPT_PATCH_AUTO_APPROVE = os.environ.get("PROMPT_PATCH_AUTO_APPROVE", "1") == "1"
PROMPT_PATCH_REQUIRE_MANUAL_APPROVAL_FOR_HIGH_DRIFT = (
    os.environ.get("PROMPT_PATCH_REQUIRE_MANUAL_APPROVAL_FOR_HIGH_DRIFT", "1") == "1"
)
PROMPT_PATCH_LOG_LEVEL = os.environ.get("PROMPT_PATCH_LOG_LEVEL", "info")

# Storage path
PATCH_DECISIONS_PATH = os.environ.get("PATCH_DECISIONS_PATH", "data/patch_decisions")


# =============================================================================
# DATA MODELS
# =============================================================================

class PatchDecision:
    """Possible patch decisions."""
    AUTO_APPROVE = "AUTO_APPROVE"
    LOG_AND_APPROVE = "LOG_AND_APPROVE"
    BLOCK_FOR_REVIEW = "BLOCK_FOR_REVIEW"
    HARD_STOP = "HARD_STOP"
    APPROVED = "APPROVED"  # Manually approved
    BLOCKED = "BLOCKED"    # Manually blocked


@dataclass
class SegmentImpact:
    """Impact analysis for a segment."""
    segment_key: str
    affected_size: str  # solo, team, kmu
    affected_branch: str
    ai_act_risk: str  # minimal, moderate, high
    impact_level: str  # LOW, MEDIUM, HIGH
    affected_count: int = 0
    details: List[str] = field(default_factory=list)


@dataclass
class RiskMatrix:
    """Risk level matrix for segment impact."""
    solo_impact: str = "LOW"      # LOW, MEDIUM, HIGH
    team_impact: str = "LOW"
    kmu_impact: str = "LOW"
    branch_impacts: Dict[str, str] = field(default_factory=dict)  # branch -> impact
    ai_act_impacts: Dict[str, str] = field(default_factory=dict)  # risk_level -> impact
    overall_impact: str = "LOW"


@dataclass
class PatchEvaluation:
    """Complete evaluation result for a patch."""
    patch_id: str
    prompt_file: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Drift analysis
    drift_score: int = 0
    drift_category: str = "MINIMAL"

    # Impact analysis
    risk_matrix: Optional[RiskMatrix] = None
    segment_impacts: List[SegmentImpact] = field(default_factory=list)
    overall_impact: str = "LOW"

    # Decision
    decision: str = PatchDecision.AUTO_APPROVE
    decision_reason: str = ""
    requires_manual_review: bool = False

    # Tracking
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


@dataclass
class PendingPatch:
    """A patch pending approval."""
    patch_id: str
    prompt_file: str
    patch_content: str
    created_at: datetime = field(default_factory=datetime.now)
    source: str = "auto_rewrite"  # auto_rewrite, tuner, manual
    evaluation: Optional[PatchEvaluation] = None
    status: str = "pending"  # pending, approved, blocked, applied


# =============================================================================
# STORAGE
# =============================================================================

_storage_lock = threading.Lock()
_pending_patches: Dict[str, PendingPatch] = {}
_blocked_patches: Dict[str, PendingPatch] = {}


def _get_decisions_path() -> Path:
    """Get the patch decisions storage path."""
    path = Path(PATCH_DECISIONS_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _store_evaluation(evaluation: PatchEvaluation) -> bool:
    """Store patch evaluation to persistent storage."""
    if PROMPT_DRAFT_MODE:
        return False

    try:
        with _storage_lock:
            decisions_path = _get_decisions_path()
            filename = f"eval_{evaluation.patch_id}.json"
            file_path = decisions_path / filename

            data = asdict(evaluation)
            data["timestamp"] = evaluation.timestamp.isoformat()
            if evaluation.reviewed_at:
                data["reviewed_at"] = evaluation.reviewed_at.isoformat()
            if evaluation.risk_matrix:
                data["risk_matrix"] = asdict(evaluation.risk_matrix)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

    except Exception as e:
        log.error(f"Failed to store evaluation: {e}")
        return False


# =============================================================================
# IMPACT ANALYSIS
# =============================================================================

# Branch groups for impact analysis
BRANCH_GROUPS = {
    "advisory": ["beratung", "consulting", "recht"],
    "technical": ["it_software", "industrie", "energie"],
    "financial": ["finanzen", "versicherung"],
    "consumer": ["handel", "gastronomie", "tourismus"],
    "healthcare": ["gesundheit"],
    "creative": ["marketing", "medien"],
    "other": ["bildung", "immobilien", "logistik", "handwerk", "landwirtschaft"],
}


def _analyze_segment_impacts(
    prompt_file: str,
    drift_score: int,
    segment_data: Optional[Dict[str, Any]] = None,
) -> Tuple[List[SegmentImpact], RiskMatrix]:
    """
    Analyze impact on different segments.

    Args:
        prompt_file: Prompt file being patched
        drift_score: Calculated drift score
        segment_data: Optional segment statistics from G17.x

    Returns:
        Tuple of (list of segment impacts, risk matrix)
    """
    impacts: List[SegmentImpact] = []
    matrix = RiskMatrix()

    # Determine base impact from drift score
    if drift_score >= 50:
        base_impact = "HIGH"
    elif drift_score >= 30:
        base_impact = "MEDIUM"
    else:
        base_impact = "LOW"

    # Analyze by company size
    for size in ["solo", "team", "kmu"]:
        impact_level = base_impact

        # Solo has higher sensitivity to changes
        if size == "solo" and drift_score >= 25:
            impact_level = "MEDIUM" if base_impact == "LOW" else base_impact

        impacts.append(SegmentImpact(
            segment_key=f"{size}|*|*|*",
            affected_size=size,
            affected_branch="*",
            ai_act_risk="*",
            impact_level=impact_level,
            details=[f"Base drift impact: {base_impact}"],
        ))

        setattr(matrix, f"{size}_impact", impact_level)

    # Analyze by branch groups
    for group_name, branches in BRANCH_GROUPS.items():
        group_impact = base_impact

        # Healthcare and financial have stricter requirements
        if group_name in ["healthcare", "financial"] and drift_score >= 20:
            group_impact = "MEDIUM" if base_impact == "LOW" else "HIGH"

        matrix.branch_impacts[group_name] = group_impact

    # Analyze by AI-Act risk level
    for risk_level in ["minimal", "moderate", "high"]:
        ai_impact = base_impact

        # High AI-Act risk has stricter requirements
        if risk_level == "high" and drift_score >= 15:
            ai_impact = "MEDIUM" if base_impact == "LOW" else "HIGH"
        elif risk_level == "moderate" and drift_score >= 25:
            ai_impact = "MEDIUM" if base_impact == "LOW" else base_impact

        matrix.ai_act_impacts[risk_level] = ai_impact

    # Calculate overall impact
    all_impacts = [
        matrix.solo_impact, matrix.team_impact, matrix.kmu_impact
    ] + list(matrix.branch_impacts.values()) + list(matrix.ai_act_impacts.values())

    if "HIGH" in all_impacts:
        matrix.overall_impact = "HIGH"
    elif "MEDIUM" in all_impacts:
        matrix.overall_impact = "MEDIUM"
    else:
        matrix.overall_impact = "LOW"

    return impacts, matrix


# Needed for type hints
from typing import Tuple


# =============================================================================
# DECISION LOGIC
# =============================================================================

def evaluate_patch_and_decide(
    prompt_file: str,
    patch_content: str,
    drift_score: int,
    drift_category: str,
    patch_id: Optional[str] = None,
    segment_data: Optional[Dict[str, Any]] = None,
) -> PatchEvaluation:
    """
    Evaluate a patch and decide on approval.

    Decision matrix:
    | Drift    | Impact | Outcome          |
    |----------|--------|------------------|
    | LOW      | LOW    | AUTO_APPROVE     |
    | MEDIUM   | LOW    | LOG_AND_APPROVE  |
    | HIGH     | ANY    | BLOCK_FOR_REVIEW |
    | CRITICAL | ANY    | HARD_STOP        |

    Args:
        prompt_file: Prompt file being patched
        patch_content: The patch content
        drift_score: Calculated drift score
        drift_category: Drift category (MINIMAL/LOW/MEDIUM/HIGH/CRITICAL)
        patch_id: Optional patch ID (generated if not provided)
        segment_data: Optional segment statistics

    Returns:
        PatchEvaluation with decision
    """
    # Generate patch ID if not provided
    if not patch_id:
        import hashlib
        patch_hash = hashlib.sha256(patch_content.encode()).hexdigest()[:12]
        patch_id = f"patch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{patch_hash}"

    evaluation = PatchEvaluation(
        patch_id=patch_id,
        prompt_file=prompt_file,
        drift_score=drift_score,
        drift_category=drift_category,
    )

    # Analyze segment impacts
    impacts, risk_matrix = _analyze_segment_impacts(
        prompt_file, drift_score, segment_data
    )
    evaluation.segment_impacts = impacts
    evaluation.risk_matrix = risk_matrix
    evaluation.overall_impact = risk_matrix.overall_impact

    # Make decision based on matrix
    if drift_category == "CRITICAL":
        evaluation.decision = PatchDecision.HARD_STOP
        evaluation.decision_reason = "Critical drift detected - automatic hard stop"
        evaluation.requires_manual_review = True

    elif drift_category == "HIGH":
        if PROMPT_PATCH_REQUIRE_MANUAL_APPROVAL_FOR_HIGH_DRIFT:
            evaluation.decision = PatchDecision.BLOCK_FOR_REVIEW
            evaluation.decision_reason = "High drift requires manual review"
            evaluation.requires_manual_review = True
        else:
            evaluation.decision = PatchDecision.LOG_AND_APPROVE
            evaluation.decision_reason = "High drift auto-approved (manual review disabled)"

    elif drift_category in ["MEDIUM", "LOW"] and risk_matrix.overall_impact == "HIGH":
        evaluation.decision = PatchDecision.BLOCK_FOR_REVIEW
        evaluation.decision_reason = "High segment impact requires manual review"
        evaluation.requires_manual_review = True

    elif drift_category == "MEDIUM":
        if PROMPT_PATCH_AUTO_APPROVE:
            evaluation.decision = PatchDecision.LOG_AND_APPROVE
            evaluation.decision_reason = "Medium drift auto-approved with logging"
        else:
            evaluation.decision = PatchDecision.BLOCK_FOR_REVIEW
            evaluation.decision_reason = "Medium drift blocked (auto-approve disabled)"
            evaluation.requires_manual_review = True

    else:  # LOW or MINIMAL
        if PROMPT_PATCH_AUTO_APPROVE:
            evaluation.decision = PatchDecision.AUTO_APPROVE
            evaluation.decision_reason = "Low drift - automatically approved"
        else:
            evaluation.decision = PatchDecision.BLOCK_FOR_REVIEW
            evaluation.decision_reason = "Auto-approve disabled - requires manual review"
            evaluation.requires_manual_review = True

    # Store evaluation
    _store_evaluation(evaluation)

    # Log decision
    log_level = logging.INFO if PROMPT_PATCH_LOG_LEVEL == "info" else logging.DEBUG
    log.log(
        log_level,
        f"[PatchGate] {patch_id}: {evaluation.decision} - {evaluation.decision_reason}"
    )

    return evaluation


def block_patch(
    prompt_file: str,
    patch_id: str,
    reason: str,
    blocked_by: Optional[str] = None,
) -> bool:
    """
    Manually block a patch.

    Args:
        prompt_file: Prompt file
        patch_id: Patch ID to block
        reason: Reason for blocking
        blocked_by: Who blocked it

    Returns:
        True if successfully blocked
    """
    try:
        # Check if patch exists in pending
        if patch_id in _pending_patches:
            patch = _pending_patches.pop(patch_id)
            patch.status = "blocked"
            if patch.evaluation:
                patch.evaluation.decision = PatchDecision.BLOCKED
                patch.evaluation.decision_reason = reason
                patch.evaluation.reviewed_by = blocked_by
                patch.evaluation.reviewed_at = datetime.now()
                patch.evaluation.review_notes = reason
                _store_evaluation(patch.evaluation)
            _blocked_patches[patch_id] = patch

        # Store block record
        if not PROMPT_DRAFT_MODE:
            with _storage_lock:
                decisions_path = _get_decisions_path()
                block_file = decisions_path / f"block_{patch_id}.json"
                with open(block_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "patch_id": patch_id,
                        "prompt_file": prompt_file,
                        "reason": reason,
                        "blocked_by": blocked_by,
                        "blocked_at": datetime.now().isoformat(),
                    }, f, indent=2)

        log.info(f"[PatchGate] Blocked patch {patch_id}: {reason}")
        return True

    except Exception as e:
        log.error(f"Failed to block patch {patch_id}: {e}")
        return False


def approve_patch(
    prompt_file: str,
    patch_id: str,
    approved_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> bool:
    """
    Manually approve a blocked or pending patch.

    Args:
        prompt_file: Prompt file
        patch_id: Patch ID to approve
        approved_by: Who approved it
        notes: Optional approval notes

    Returns:
        True if successfully approved
    """
    try:
        # Find patch in pending or blocked
        patch = _pending_patches.get(patch_id) or _blocked_patches.get(patch_id)

        if patch:
            patch.status = "approved"
            if patch.evaluation:
                patch.evaluation.decision = PatchDecision.APPROVED
                patch.evaluation.decision_reason = notes or "Manually approved"
                patch.evaluation.reviewed_by = approved_by
                patch.evaluation.reviewed_at = datetime.now()
                patch.evaluation.review_notes = notes
                patch.evaluation.requires_manual_review = False
                _store_evaluation(patch.evaluation)

            # Move from blocked to approved
            if patch_id in _blocked_patches:
                del _blocked_patches[patch_id]

        # Store approval record
        if not PROMPT_DRAFT_MODE:
            with _storage_lock:
                decisions_path = _get_decisions_path()
                approve_file = decisions_path / f"approve_{patch_id}.json"
                with open(approve_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "patch_id": patch_id,
                        "prompt_file": prompt_file,
                        "approved_by": approved_by,
                        "approved_at": datetime.now().isoformat(),
                        "notes": notes,
                    }, f, indent=2)

        log.info(f"[PatchGate] Approved patch {patch_id}")
        return True

    except Exception as e:
        log.error(f"Failed to approve patch {patch_id}: {e}")
        return False


def add_pending_patch(
    prompt_file: str,
    patch_content: str,
    source: str = "auto_rewrite",
    patch_id: Optional[str] = None,
) -> PendingPatch:
    """
    Add a patch to the pending queue.

    Args:
        prompt_file: Prompt file being patched
        patch_content: The patch content
        source: Source of the patch
        patch_id: Optional patch ID

    Returns:
        Created PendingPatch
    """
    if not patch_id:
        import hashlib
        patch_hash = hashlib.sha256(patch_content.encode()).hexdigest()[:12]
        patch_id = f"patch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{patch_hash}"

    patch = PendingPatch(
        patch_id=patch_id,
        prompt_file=prompt_file,
        patch_content=patch_content,
        source=source,
    )

    _pending_patches[patch_id] = patch
    return patch


def get_pending_patches() -> List[Dict[str, Any]]:
    """Get all pending patches."""
    return [
        {
            "patch_id": p.patch_id,
            "prompt_file": p.prompt_file,
            "created_at": p.created_at.isoformat(),
            "source": p.source,
            "status": p.status,
            "decision": p.evaluation.decision if p.evaluation else None,
            "drift_score": p.evaluation.drift_score if p.evaluation else None,
        }
        for p in _pending_patches.values()
    ]


def get_blocked_patches() -> List[Dict[str, Any]]:
    """Get all blocked patches."""
    return [
        {
            "patch_id": p.patch_id,
            "prompt_file": p.prompt_file,
            "created_at": p.created_at.isoformat(),
            "source": p.source,
            "status": p.status,
            "decision": p.evaluation.decision if p.evaluation else None,
            "decision_reason": p.evaluation.decision_reason if p.evaluation else None,
            "drift_score": p.evaluation.drift_score if p.evaluation else None,
        }
        for p in _blocked_patches.values()
    ]


def can_auto_approve(evaluation: PatchEvaluation) -> bool:
    """Check if a patch evaluation allows auto-approval."""
    return evaluation.decision in [
        PatchDecision.AUTO_APPROVE,
        PatchDecision.LOG_AND_APPROVE,
        PatchDecision.APPROVED,
    ]


def is_hard_stop(evaluation: PatchEvaluation) -> bool:
    """Check if evaluation is a hard stop."""
    return evaluation.decision == PatchDecision.HARD_STOP
