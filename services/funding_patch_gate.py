"""
G17.8-E: Funding Patch Gate (Governance)

Governance layer that validates and approves optimization patches before
they are applied to the funding recommendation system.

Implements:
- Manual approval workflow
- Automatic safety checks
- Rollback capabilities
- Audit logging

Part of the Funding Auto-Optimizer & Intelligent Rebalancing system.
"""

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration from Environment
# ============================================================================

FUNDING_PATCH_GATE_ENABLED = os.getenv("FUNDING_PATCH_GATE_ENABLED", "true").lower() == "true"
FUNDING_PATCH_GATE_STORAGE_PATH = os.getenv(
    "FUNDING_PATCH_GATE_STORAGE_PATH",
    "data/funding_patches"
)
FUNDING_PATCH_AUTO_APPROVE = os.getenv("FUNDING_PATCH_AUTO_APPROVE", "false").lower() == "true"
FUNDING_PATCH_MAX_CHANGE_PCT = float(os.getenv("FUNDING_PATCH_MAX_CHANGE_PCT", "30.0"))
FUNDING_PATCH_MIN_CONFIDENCE = float(os.getenv("FUNDING_PATCH_MIN_CONFIDENCE", "0.6"))
FUNDING_PATCH_REQUIRE_REVIEW = os.getenv("FUNDING_PATCH_REQUIRE_REVIEW", "true").lower() == "true"
FUNDING_PATCH_ROLLBACK_WINDOW_HOURS = int(os.getenv("FUNDING_PATCH_ROLLBACK_WINDOW_HOURS", "72"))


# ============================================================================
# Enums
# ============================================================================

class PatchStatus(Enum):
    """Status of a funding patch."""
    PENDING = "pending"  # Awaiting review
    APPROVED = "approved"  # Approved for application
    APPLIED = "applied"  # Successfully applied
    REJECTED = "rejected"  # Rejected by reviewer
    ROLLED_BACK = "rolled_back"  # Applied but rolled back
    EXPIRED = "expired"  # Expired without action
    BLOCKED = "blocked"  # Blocked by safety check


class PatchType(Enum):
    """Type of funding patch."""
    PRIORITY_BOOST = "priority_boost"
    PRIORITY_REDUCTION = "priority_reduction"
    DISTRIBUTION_CORRECTION = "distribution_correction"
    ROI_ADJUSTMENT = "roi_adjustment"
    BULK_REBALANCE = "bulk_rebalance"
    EMERGENCY_OVERRIDE = "emergency_override"


class SafetyCheckResult(Enum):
    """Result of a safety check."""
    PASSED = "passed"
    WARNING = "warning"
    BLOCKED = "blocked"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SafetyCheck:
    """Result of a single safety check."""
    check_name: str
    result: SafetyCheckResult
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "result": self.result.value,
            "message": self.message,
            "details": self.details
        }


@dataclass
class FundingPatch:
    """A funding optimization patch awaiting approval."""
    patch_id: str
    created_at: str
    patch_type: PatchType
    status: PatchStatus
    source_run_id: str  # ID of the optimization run that generated this
    programme_ids: List[str]
    changes: List[Dict[str, Any]]
    total_change_impact: float  # Aggregate impact score
    confidence: float
    safety_checks: List[SafetyCheck]
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    applied_at: Optional[str] = None
    rolled_back_at: Optional[str] = None
    rollback_reason: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "created_at": self.created_at,
            "patch_type": self.patch_type.value,
            "status": self.status.value,
            "source_run_id": self.source_run_id,
            "programme_ids": self.programme_ids,
            "changes": self.changes,
            "total_change_impact": round(self.total_change_impact, 2),
            "confidence": round(self.confidence, 2),
            "safety_checks": [sc.to_dict() for sc in self.safety_checks],
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "applied_at": self.applied_at,
            "rolled_back_at": self.rolled_back_at,
            "rollback_reason": self.rollback_reason,
            "notes": self.notes
        }


@dataclass
class PatchAuditEntry:
    """Audit log entry for patch operations."""
    entry_id: str
    timestamp: str
    patch_id: str
    action: str  # created, approved, applied, rejected, rolled_back
    actor: str  # system, user_id, or auto
    previous_status: Optional[str]
    new_status: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# In-Memory Storage
# ============================================================================

_patches: Dict[str, FundingPatch] = {}
_audit_log: List[PatchAuditEntry] = []
_rollback_snapshots: Dict[str, Dict[str, Any]] = {}  # patch_id -> state before apply


# ============================================================================
# Core Functions
# ============================================================================

def create_patch_from_proposals(
    proposals: List[Dict[str, Any]],
    source_run_id: str
) -> FundingPatch:
    """
    Create a funding patch from optimization proposals.

    Args:
        proposals: List of proposal dictionaries
        source_run_id: ID of the optimization run

    Returns:
        Created FundingPatch
    """
    if not FUNDING_PATCH_GATE_ENABLED:
        raise RuntimeError("Funding Patch Gate is disabled")

    patch_id = f"patch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Determine patch type
    has_boost = any(p.get("action") == "boost_priority" for p in proposals)
    has_reduce = any(p.get("action") == "reduce_priority" for p in proposals)

    if has_boost and has_reduce:
        patch_type = PatchType.BULK_REBALANCE
    elif has_boost:
        patch_type = PatchType.PRIORITY_BOOST
    elif has_reduce:
        patch_type = PatchType.PRIORITY_REDUCTION
    else:
        patch_type = PatchType.DISTRIBUTION_CORRECTION

    # Extract programme IDs
    programme_ids = list(set(p.get("programme_id", "") for p in proposals))

    # Calculate aggregate impact
    total_impact = sum(abs(p.get("change_pct", 0)) for p in proposals)
    avg_confidence = sum(p.get("confidence", 0) for p in proposals) / len(proposals) if proposals else 0

    # Run safety checks
    safety_checks = _run_safety_checks(proposals, total_impact)

    # Determine initial status
    blocked_checks = [sc for sc in safety_checks if sc.result == SafetyCheckResult.BLOCKED]
    if blocked_checks:
        initial_status = PatchStatus.BLOCKED
    elif FUNDING_PATCH_AUTO_APPROVE and avg_confidence >= FUNDING_PATCH_MIN_CONFIDENCE:
        initial_status = PatchStatus.APPROVED
    else:
        initial_status = PatchStatus.PENDING

    patch = FundingPatch(
        patch_id=patch_id,
        created_at=timestamp,
        patch_type=patch_type,
        status=initial_status,
        source_run_id=source_run_id,
        programme_ids=programme_ids,
        changes=proposals,
        total_change_impact=total_impact,
        confidence=avg_confidence,
        safety_checks=safety_checks
    )

    _patches[patch_id] = patch
    _log_audit(patch_id, "created", "system", None, initial_status.value)
    _persist_patch(patch)

    logger.info(f"Created patch {patch_id}: {patch_type.value}, status={initial_status.value}")

    return patch


def approve_patch(
    patch_id: str,
    reviewer: str = "system",
    notes: str = ""
) -> Dict[str, Any]:
    """
    Approve a pending patch.

    Args:
        patch_id: ID of the patch to approve
        reviewer: ID/name of the reviewer
        notes: Optional approval notes

    Returns:
        Result dictionary
    """
    patch = _patches.get(patch_id)
    if not patch:
        return {"success": False, "error": f"Patch {patch_id} not found"}

    if patch.status not in [PatchStatus.PENDING, PatchStatus.BLOCKED]:
        return {"success": False, "error": f"Patch status {patch.status.value} cannot be approved"}

    # Check for blocking safety issues
    blocked = [sc for sc in patch.safety_checks if sc.result == SafetyCheckResult.BLOCKED]
    if blocked and reviewer != "admin_override":
        return {
            "success": False,
            "error": "Patch has blocking safety checks",
            "blocked_checks": [sc.to_dict() for sc in blocked]
        }

    previous_status = patch.status.value
    patch.status = PatchStatus.APPROVED
    patch.reviewed_by = reviewer
    patch.reviewed_at = datetime.now(timezone.utc).isoformat()
    patch.notes = notes

    _log_audit(patch_id, "approved", reviewer, previous_status, "approved")
    _persist_patch(patch)

    logger.info(f"Patch {patch_id} approved by {reviewer}")

    return {"success": True, "patch": patch.to_dict()}


def reject_patch(
    patch_id: str,
    reviewer: str = "system",
    reason: str = ""
) -> Dict[str, Any]:
    """Reject a pending patch."""
    patch = _patches.get(patch_id)
    if not patch:
        return {"success": False, "error": f"Patch {patch_id} not found"}

    if patch.status not in [PatchStatus.PENDING, PatchStatus.BLOCKED, PatchStatus.APPROVED]:
        return {"success": False, "error": f"Patch status {patch.status.value} cannot be rejected"}

    previous_status = patch.status.value
    patch.status = PatchStatus.REJECTED
    patch.reviewed_by = reviewer
    patch.reviewed_at = datetime.now(timezone.utc).isoformat()
    patch.notes = reason

    _log_audit(patch_id, "rejected", reviewer, previous_status, "rejected", {"reason": reason})
    _persist_patch(patch)

    logger.info(f"Patch {patch_id} rejected by {reviewer}: {reason}")

    return {"success": True, "patch": patch.to_dict()}


def apply_patch(patch_id: str) -> Dict[str, Any]:
    """
    Apply an approved patch to the funding system.

    Args:
        patch_id: ID of the patch to apply

    Returns:
        Result dictionary
    """
    patch = _patches.get(patch_id)
    if not patch:
        return {"success": False, "error": f"Patch {patch_id} not found"}

    if patch.status != PatchStatus.APPROVED:
        return {"success": False, "error": f"Patch must be approved first (status: {patch.status.value})"}

    # Create rollback snapshot
    try:
        _create_rollback_snapshot(patch_id)
    except Exception as e:
        logger.warning(f"Could not create rollback snapshot: {e}")

    # Apply changes
    from services.funding_confidence_rebalancer import apply_adjustment

    applied = 0
    errors = []

    for change in patch.changes:
        try:
            programme_id = change.get("programme_id")
            action = change.get("action")
            change_pct = change.get("change_pct", 0)

            if action == "boost_priority":
                factor = 1.0 + (abs(change_pct) / 100)
                apply_adjustment(programme_id, factor, f"Patch {patch_id}", "boost")
            elif action == "reduce_priority":
                factor = 1.0 - (abs(change_pct) / 100)
                apply_adjustment(programme_id, factor, f"Patch {patch_id}", "penalty")

            applied += 1
        except Exception as e:
            errors.append(f"{change.get('programme_id')}: {e}")

    # Update patch status
    previous_status = patch.status.value
    patch.status = PatchStatus.APPLIED
    patch.applied_at = datetime.now(timezone.utc).isoformat()

    _log_audit(patch_id, "applied", "system", previous_status, "applied", {
        "applied_count": applied,
        "errors": errors
    })
    _persist_patch(patch)

    logger.info(f"Patch {patch_id} applied: {applied} changes, {len(errors)} errors")

    return {
        "success": True,
        "applied_count": applied,
        "errors": errors,
        "patch": patch.to_dict()
    }


def rollback_patch(
    patch_id: str,
    reason: str = ""
) -> Dict[str, Any]:
    """
    Rollback an applied patch.

    Args:
        patch_id: ID of the patch to rollback
        reason: Reason for rollback

    Returns:
        Result dictionary
    """
    patch = _patches.get(patch_id)
    if not patch:
        return {"success": False, "error": f"Patch {patch_id} not found"}

    if patch.status != PatchStatus.APPLIED:
        return {"success": False, "error": f"Can only rollback applied patches (status: {patch.status.value})"}

    # Check rollback window
    if patch.applied_at:
        applied_time = datetime.fromisoformat(patch.applied_at.replace("Z", "+00:00"))
        window_end = applied_time + timedelta(hours=FUNDING_PATCH_ROLLBACK_WINDOW_HOURS)
        if datetime.now(timezone.utc) > window_end:
            return {
                "success": False,
                "error": f"Rollback window expired ({FUNDING_PATCH_ROLLBACK_WINDOW_HOURS}h)"
            }

    # Restore from snapshot
    snapshot = _rollback_snapshots.get(patch_id)
    if snapshot:
        try:
            _restore_from_snapshot(snapshot)
        except Exception as e:
            return {"success": False, "error": f"Rollback failed: {e}"}
    else:
        # Manual rollback by inverting changes
        from services.funding_confidence_rebalancer import apply_adjustment

        for change in patch.changes:
            programme_id = change.get("programme_id")
            action = change.get("action")
            change_pct = change.get("change_pct", 0)

            # Invert the change
            if action == "boost_priority":
                factor = 1.0 / (1.0 + (abs(change_pct) / 100))
                apply_adjustment(programme_id, factor, f"Rollback {patch_id}", "decay")
            elif action == "reduce_priority":
                factor = 1.0 / (1.0 - (abs(change_pct) / 100))
                apply_adjustment(programme_id, factor, f"Rollback {patch_id}", "boost")

    # Update patch status
    previous_status = patch.status.value
    patch.status = PatchStatus.ROLLED_BACK
    patch.rolled_back_at = datetime.now(timezone.utc).isoformat()
    patch.rollback_reason = reason

    _log_audit(patch_id, "rolled_back", "system", previous_status, "rolled_back", {"reason": reason})
    _persist_patch(patch)

    logger.info(f"Patch {patch_id} rolled back: {reason}")

    return {"success": True, "patch": patch.to_dict()}


# ============================================================================
# Safety Checks
# ============================================================================

def _run_safety_checks(
    proposals: List[Dict[str, Any]],
    total_impact: float
) -> List[SafetyCheck]:
    """Run all safety checks on proposals."""
    checks: List[SafetyCheck] = []

    # Check 1: Maximum change percentage
    max_change = max((abs(p.get("change_pct", 0)) for p in proposals), default=0)
    if max_change > FUNDING_PATCH_MAX_CHANGE_PCT:
        checks.append(SafetyCheck(
            check_name="max_change_limit",
            result=SafetyCheckResult.BLOCKED,
            message=f"Change of {max_change:.1f}% exceeds limit of {FUNDING_PATCH_MAX_CHANGE_PCT}%",
            details={"max_change": max_change, "limit": FUNDING_PATCH_MAX_CHANGE_PCT}
        ))
    else:
        checks.append(SafetyCheck(
            check_name="max_change_limit",
            result=SafetyCheckResult.PASSED,
            message=f"Maximum change {max_change:.1f}% within limit",
            details={"max_change": max_change}
        ))

    # Check 2: Minimum confidence
    min_confidence = min((p.get("confidence", 0) for p in proposals), default=0)
    if min_confidence < FUNDING_PATCH_MIN_CONFIDENCE:
        checks.append(SafetyCheck(
            check_name="min_confidence",
            result=SafetyCheckResult.WARNING,
            message=f"Some proposals have low confidence ({min_confidence:.2f})",
            details={"min_confidence": min_confidence, "threshold": FUNDING_PATCH_MIN_CONFIDENCE}
        ))
    else:
        checks.append(SafetyCheck(
            check_name="min_confidence",
            result=SafetyCheckResult.PASSED,
            message=f"All proposals meet confidence threshold",
            details={"min_confidence": min_confidence}
        ))

    # Check 3: Total impact threshold
    if total_impact > 100:
        checks.append(SafetyCheck(
            check_name="total_impact",
            result=SafetyCheckResult.WARNING,
            message=f"High total impact ({total_impact:.1f}%)",
            details={"total_impact": total_impact}
        ))
    else:
        checks.append(SafetyCheck(
            check_name="total_impact",
            result=SafetyCheckResult.PASSED,
            message=f"Total impact within normal range",
            details={"total_impact": total_impact}
        ))

    # Check 4: Proposal count
    if len(proposals) > 10:
        checks.append(SafetyCheck(
            check_name="proposal_count",
            result=SafetyCheckResult.WARNING,
            message=f"Large batch of {len(proposals)} proposals",
            details={"count": len(proposals)}
        ))
    else:
        checks.append(SafetyCheck(
            check_name="proposal_count",
            result=SafetyCheckResult.PASSED,
            message=f"Proposal count acceptable",
            details={"count": len(proposals)}
        ))

    # Check 5: Data points
    low_data = [p for p in proposals if p.get("data_points", 0) < 5]
    if low_data:
        checks.append(SafetyCheck(
            check_name="data_quality",
            result=SafetyCheckResult.WARNING,
            message=f"{len(low_data)} proposals have insufficient data",
            details={"low_data_count": len(low_data)}
        ))
    else:
        checks.append(SafetyCheck(
            check_name="data_quality",
            result=SafetyCheckResult.PASSED,
            message="All proposals have sufficient data",
            details={}
        ))

    return checks


# ============================================================================
# Snapshots and Rollback
# ============================================================================

def _create_rollback_snapshot(patch_id: str) -> None:
    """Create a snapshot of current state for rollback."""
    from services.funding_confidence_rebalancer import get_all_confidence_states

    states = get_all_confidence_states()
    _rollback_snapshots[patch_id] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence_states": {k: v.to_dict() for k, v in states.items()}
    }


def _restore_from_snapshot(snapshot: Dict[str, Any]) -> None:
    """Restore state from a snapshot."""
    from services.funding_confidence_rebalancer import (
        _confidence_states, ProgrammeConfidenceState, ConfidenceAdjustment
    )

    states_data = snapshot.get("confidence_states", {})
    for prog_id, state_data in states_data.items():
        history = [
            ConfidenceAdjustment(**adj)
            for adj in state_data.get("adjustment_history", [])
        ]
        _confidence_states[prog_id] = ProgrammeConfidenceState(
            programme_id=prog_id,
            base_confidence=state_data.get("base_confidence", 1.0),
            current_adjustment=state_data.get("current_adjustment", 1.0),
            effective_confidence=state_data.get("effective_confidence", 1.0),
            adjustment_history=history,
            roi_score=state_data.get("roi_score", 0.0),
            distribution_penalty=state_data.get("distribution_penalty", 0.0),
            last_updated=state_data.get("last_updated", "")
        )


# ============================================================================
# Query Functions
# ============================================================================

def get_patch(patch_id: str) -> Optional[Dict[str, Any]]:
    """Get a patch by ID."""
    patch = _patches.get(patch_id)
    return patch.to_dict() if patch else None


def get_pending_patches() -> List[Dict[str, Any]]:
    """Get all pending patches awaiting review."""
    pending = [p for p in _patches.values() if p.status == PatchStatus.PENDING]
    return [p.to_dict() for p in sorted(pending, key=lambda x: x.created_at, reverse=True)]


def get_patch_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent patch history."""
    patches = sorted(_patches.values(), key=lambda x: x.created_at, reverse=True)[:limit]
    return [p.to_dict() for p in patches]


def get_audit_log(patch_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Get audit log entries."""
    entries = _audit_log
    if patch_id:
        entries = [e for e in entries if e.patch_id == patch_id]
    return [e.to_dict() for e in sorted(entries, key=lambda x: x.timestamp, reverse=True)[:limit]]


def get_patch_gate_status() -> Dict[str, Any]:
    """Get current status of the patch gate."""
    pending_count = sum(1 for p in _patches.values() if p.status == PatchStatus.PENDING)
    blocked_count = sum(1 for p in _patches.values() if p.status == PatchStatus.BLOCKED)

    return {
        "enabled": FUNDING_PATCH_GATE_ENABLED,
        "auto_approve": FUNDING_PATCH_AUTO_APPROVE,
        "require_review": FUNDING_PATCH_REQUIRE_REVIEW,
        "total_patches": len(_patches),
        "pending_count": pending_count,
        "blocked_count": blocked_count,
        "rollback_window_hours": FUNDING_PATCH_ROLLBACK_WINDOW_HOURS,
        "max_change_pct": FUNDING_PATCH_MAX_CHANGE_PCT,
        "min_confidence": FUNDING_PATCH_MIN_CONFIDENCE
    }


# ============================================================================
# Audit Logging
# ============================================================================

def _log_audit(
    patch_id: str,
    action: str,
    actor: str,
    previous_status: Optional[str],
    new_status: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log an audit entry."""
    entry = PatchAuditEntry(
        entry_id=f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        patch_id=patch_id,
        action=action,
        actor=actor,
        previous_status=previous_status,
        new_status=new_status,
        details=details or {}
    )
    _audit_log.append(entry)


# ============================================================================
# Persistence
# ============================================================================

def _persist_patch(patch: FundingPatch) -> None:
    """Persist patch to filesystem."""
    try:
        storage_path = Path(FUNDING_PATCH_GATE_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)

        filepath = storage_path / f"{patch.patch_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(patch.to_dict(), f, indent=2, ensure_ascii=False)

        logger.debug(f"Persisted patch: {filepath}")
    except Exception as e:
        logger.error(f"Failed to persist patch: {e}")


def load_patches_from_storage() -> int:
    """Load patches from storage. Returns count loaded."""
    global _patches

    storage_path = Path(FUNDING_PATCH_GATE_STORAGE_PATH)
    if not storage_path.exists():
        return 0

    loaded = 0
    for filepath in storage_path.glob("patch_*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            safety_checks = [
                SafetyCheck(
                    check_name=sc["check_name"],
                    result=SafetyCheckResult(sc["result"]),
                    message=sc["message"],
                    details=sc.get("details", {})
                )
                for sc in data.get("safety_checks", [])
            ]

            patch = FundingPatch(
                patch_id=data["patch_id"],
                created_at=data["created_at"],
                patch_type=PatchType(data["patch_type"]),
                status=PatchStatus(data["status"]),
                source_run_id=data["source_run_id"],
                programme_ids=data["programme_ids"],
                changes=data["changes"],
                total_change_impact=data["total_change_impact"],
                confidence=data["confidence"],
                safety_checks=safety_checks,
                reviewed_by=data.get("reviewed_by"),
                reviewed_at=data.get("reviewed_at"),
                applied_at=data.get("applied_at"),
                rolled_back_at=data.get("rolled_back_at"),
                rollback_reason=data.get("rollback_reason"),
                notes=data.get("notes", "")
            )
            _patches[patch.patch_id] = patch
            loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load patch {filepath}: {e}")

    logger.info(f"Loaded {loaded} patches from storage")
    return loaded


# ============================================================================
# Module Initialization
# ============================================================================

def _initialize_module() -> None:
    """Initialize module on import."""
    if FUNDING_PATCH_GATE_ENABLED:
        try:
            load_patches_from_storage()
        except Exception as e:
            logger.warning(f"Could not load patches: {e}")


_initialize_module()
