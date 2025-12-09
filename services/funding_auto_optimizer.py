"""
G17.8-D: Funding Auto-Optimizer Engine

Central orchestration engine that combines distribution analysis,
confidence rebalancing, and ROI tracking to automatically optimize
funding recommendations.

Part of the Funding Auto-Optimizer & Intelligent Rebalancing system.
"""

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration from Environment
# ============================================================================

FUNDING_OPTIMIZER_ENABLED = os.getenv("FUNDING_OPTIMIZER_ENABLED", "true").lower() == "true"
FUNDING_OPTIMIZER_STORAGE_PATH = os.getenv(
    "FUNDING_OPTIMIZER_STORAGE_PATH",
    "data/funding_optimizer"
)
FUNDING_OPTIMIZER_CYCLE_HOURS = int(os.getenv("FUNDING_OPTIMIZER_CYCLE_HOURS", "24"))
FUNDING_OPTIMIZER_MIN_RECOMMENDATIONS = int(os.getenv("FUNDING_OPTIMIZER_MIN_RECOMMENDATIONS", "20"))
FUNDING_OPTIMIZER_AUTO_APPLY = os.getenv("FUNDING_OPTIMIZER_AUTO_APPLY", "false").lower() == "true"
FUNDING_OPTIMIZER_DRY_RUN = os.getenv("FUNDING_OPTIMIZER_DRY_RUN", "true").lower() == "true"


# ============================================================================
# Enums and Constants
# ============================================================================

class OptimizationAction(Enum):
    """Types of optimization actions."""
    BOOST_PRIORITY = "boost_priority"
    REDUCE_PRIORITY = "reduce_priority"
    APPLY_ROI_BOOST = "apply_roi_boost"
    APPLY_DISTRIBUTION_CORRECTION = "apply_distribution_correction"
    RESET_TO_BASELINE = "reset_to_baseline"
    NO_ACTION = "no_action"


class OptimizationStatus(Enum):
    """Status of an optimization run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class OptimizationProposal:
    """A proposed optimization action."""
    proposal_id: str
    programme_id: str
    programme_name: str
    action: OptimizationAction
    current_value: float
    proposed_value: float
    change_pct: float
    reason: str
    confidence: float  # How confident we are in this proposal (0-1)
    data_points: int  # Number of data points supporting this

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "programme_id": self.programme_id,
            "programme_name": self.programme_name,
            "action": self.action.value,
            "current_value": round(self.current_value, 4),
            "proposed_value": round(self.proposed_value, 4),
            "change_pct": round(self.change_pct, 2),
            "reason": self.reason,
            "confidence": round(self.confidence, 2),
            "data_points": self.data_points
        }


@dataclass
class OptimizationRun:
    """A complete optimization run."""
    run_id: str
    timestamp: str
    status: OptimizationStatus
    proposals: List[OptimizationProposal]
    applied_count: int
    skipped_count: int
    distribution_delta_before: float
    distribution_delta_after: float
    total_recommendations_analyzed: int
    dry_run: bool
    duration_ms: int
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "proposals": [p.to_dict() for p in self.proposals],
            "applied_count": self.applied_count,
            "skipped_count": self.skipped_count,
            "distribution_delta_before": round(self.distribution_delta_before, 4),
            "distribution_delta_after": round(self.distribution_delta_after, 4),
            "total_recommendations_analyzed": self.total_recommendations_analyzed,
            "dry_run": self.dry_run,
            "duration_ms": self.duration_ms,
            "errors": self.errors
        }


@dataclass
class OptimizerState:
    """Current state of the optimizer."""
    enabled: bool
    last_run_id: Optional[str]
    last_run_timestamp: Optional[str]
    last_run_status: Optional[str]
    next_scheduled_run: Optional[str]
    total_runs: int
    total_proposals_applied: int
    current_distribution_delta: float
    auto_apply_enabled: bool
    dry_run_mode: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# In-Memory Storage
# ============================================================================

_optimization_runs: List[OptimizationRun] = []
_pending_proposals: List[OptimizationProposal] = []
_last_run_timestamp: Optional[datetime] = None


# ============================================================================
# Core Optimizer Functions
# ============================================================================

def run_optimization_cycle(
    dry_run: Optional[bool] = None,
    force: bool = False
) -> OptimizationRun:
    """
    Run a complete optimization cycle.

    This is the main entry point for the optimizer. It:
    1. Analyzes current distribution
    2. Evaluates ROI performance
    3. Generates optimization proposals
    4. Applies proposals (if not dry run)
    5. Records results

    Args:
        dry_run: Override dry run setting (None = use config)
        force: Force run even if cycle interval not reached

    Returns:
        OptimizationRun with results
    """
    global _last_run_timestamp

    run_id = f"opt_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    start_time = datetime.now(timezone.utc)
    is_dry_run = dry_run if dry_run is not None else FUNDING_OPTIMIZER_DRY_RUN
    errors: List[str] = []

    # Check if optimizer is enabled
    if not FUNDING_OPTIMIZER_ENABLED:
        return OptimizationRun(
            run_id=run_id,
            timestamp=start_time.isoformat(),
            status=OptimizationStatus.SKIPPED,
            proposals=[],
            applied_count=0,
            skipped_count=0,
            distribution_delta_before=0.0,
            distribution_delta_after=0.0,
            total_recommendations_analyzed=0,
            dry_run=is_dry_run,
            duration_ms=0,
            errors=["Optimizer is disabled"]
        )

    # Check cycle interval
    if not force and _last_run_timestamp:
        hours_since_last = (start_time - _last_run_timestamp).total_seconds() / 3600
        if hours_since_last < FUNDING_OPTIMIZER_CYCLE_HOURS:
            return OptimizationRun(
                run_id=run_id,
                timestamp=start_time.isoformat(),
                status=OptimizationStatus.SKIPPED,
                proposals=[],
                applied_count=0,
                skipped_count=0,
                distribution_delta_before=0.0,
                distribution_delta_after=0.0,
                total_recommendations_analyzed=0,
                dry_run=is_dry_run,
                duration_ms=0,
                errors=[f"Cycle interval not reached ({hours_since_last:.1f}h < {FUNDING_OPTIMIZER_CYCLE_HOURS}h)"]
            )

    logger.info(f"Starting optimization cycle {run_id} (dry_run={is_dry_run})")

    try:
        # Import dependencies
        from services.funding_distribution import (
            analyze_distribution, _recommendation_history
        )
        from services.funding_confidence_rebalancer import (
            rebalance_from_distribution, get_all_confidence_states
        )
        from services.funding_recommender import (
            get_all_programme_roi_stats, ROI_TRACKING_ENABLED
        )

        # Step 1: Analyze current distribution
        distribution = analyze_distribution()
        delta_before = distribution.delta_score
        total_recs = len(_recommendation_history)

        # Check minimum recommendations
        if total_recs < FUNDING_OPTIMIZER_MIN_RECOMMENDATIONS:
            return OptimizationRun(
                run_id=run_id,
                timestamp=start_time.isoformat(),
                status=OptimizationStatus.SKIPPED,
                proposals=[],
                applied_count=0,
                skipped_count=0,
                distribution_delta_before=delta_before,
                distribution_delta_after=delta_before,
                total_recommendations_analyzed=total_recs,
                dry_run=is_dry_run,
                duration_ms=int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
                errors=[f"Insufficient data ({total_recs} < {FUNDING_OPTIMIZER_MIN_RECOMMENDATIONS})"]
            )

        # Step 2: Generate proposals
        proposals = _generate_proposals(distribution.to_dict())

        # Step 3: Enrich with ROI data
        if ROI_TRACKING_ENABLED:
            try:
                roi_stats = get_all_programme_roi_stats()
                proposals = _enrich_proposals_with_roi(proposals, roi_stats)
            except Exception as e:
                errors.append(f"ROI enrichment failed: {e}")

        # Step 4: Apply proposals (if not dry run and auto-apply enabled)
        applied_count = 0
        skipped_count = 0

        if not is_dry_run and FUNDING_OPTIMIZER_AUTO_APPLY:
            for proposal in proposals:
                if proposal.confidence >= 0.6:
                    try:
                        _apply_proposal(proposal)
                        applied_count += 1
                    except Exception as e:
                        errors.append(f"Failed to apply {proposal.proposal_id}: {e}")
                        skipped_count += 1
                else:
                    skipped_count += 1
        else:
            skipped_count = len(proposals)

        # Step 5: Calculate new distribution delta
        if applied_count > 0:
            new_distribution = analyze_distribution()
            delta_after = new_distribution.delta_score
        else:
            delta_after = delta_before

        # Record run
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        run = OptimizationRun(
            run_id=run_id,
            timestamp=start_time.isoformat(),
            status=OptimizationStatus.DRY_RUN if is_dry_run else OptimizationStatus.COMPLETED,
            proposals=proposals,
            applied_count=applied_count,
            skipped_count=skipped_count,
            distribution_delta_before=delta_before,
            distribution_delta_after=delta_after,
            total_recommendations_analyzed=total_recs,
            dry_run=is_dry_run,
            duration_ms=duration_ms,
            errors=errors
        )

        _optimization_runs.append(run)
        _last_run_timestamp = start_time
        _persist_run(run)

        logger.info(
            f"Optimization cycle {run_id} completed: "
            f"{len(proposals)} proposals, {applied_count} applied, "
            f"delta {delta_before:.4f} -> {delta_after:.4f}"
        )

        return run

    except Exception as e:
        logger.error(f"Optimization cycle failed: {e}")
        return OptimizationRun(
            run_id=run_id,
            timestamp=start_time.isoformat(),
            status=OptimizationStatus.FAILED,
            proposals=[],
            applied_count=0,
            skipped_count=0,
            distribution_delta_before=0.0,
            distribution_delta_after=0.0,
            total_recommendations_analyzed=0,
            dry_run=is_dry_run,
            duration_ms=int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
            errors=[str(e)]
        )


def _generate_proposals(
    distribution: Dict[str, Any]
) -> List[OptimizationProposal]:
    """Generate optimization proposals from distribution analysis."""
    proposals: List[OptimizationProposal] = []
    proposal_counter = 0

    # Proposals for overrepresented programmes
    for prog in distribution.get("overrepresented", []):
        if not prog.get("rebalancing_required", False):
            continue

        proposal_counter += 1
        delta = prog.get("delta_pct", 0)
        expected = prog.get("expected_pct", 0)
        actual = prog.get("actual_pct", 0)

        # Calculate reduction amount
        reduction_factor = max(0.7, 1.0 - (abs(delta) / 100))
        confidence = min(0.9, 0.5 + (prog.get("recommendation_count", 0) / 100))

        proposals.append(OptimizationProposal(
            proposal_id=f"prop_{proposal_counter:03d}",
            programme_id=prog.get("programme_id", "unknown"),
            programme_name=prog.get("programme_name", "Unknown"),
            action=OptimizationAction.REDUCE_PRIORITY,
            current_value=actual / 100 if actual else 1.0,
            proposed_value=expected / 100 if expected else reduction_factor,
            change_pct=-abs(delta),
            reason=f"Overrepresented by {delta:+.1f}% vs expected {expected:.1f}%",
            confidence=confidence,
            data_points=prog.get("recommendation_count", 0)
        ))

    # Proposals for underrepresented programmes
    for prog in distribution.get("underrepresented", []):
        if not prog.get("rebalancing_required", False):
            continue

        proposal_counter += 1
        delta = prog.get("delta_pct", 0)
        expected = prog.get("expected_pct", 0)
        actual = prog.get("actual_pct", 0)

        # Calculate boost amount
        boost_factor = min(1.3, 1.0 + (abs(delta) / 100))
        confidence = min(0.85, 0.4 + (prog.get("recommendation_count", 0) / 100))

        proposals.append(OptimizationProposal(
            proposal_id=f"prop_{proposal_counter:03d}",
            programme_id=prog.get("programme_id", "unknown"),
            programme_name=prog.get("programme_name", "Unknown"),
            action=OptimizationAction.BOOST_PRIORITY,
            current_value=actual / 100 if actual else 0.0,
            proposed_value=expected / 100 if expected else boost_factor,
            change_pct=abs(delta),
            reason=f"Underrepresented by {delta:.1f}% vs expected {expected:.1f}%",
            confidence=confidence,
            data_points=prog.get("recommendation_count", 0)
        ))

    return proposals


def _enrich_proposals_with_roi(
    proposals: List[OptimizationProposal],
    roi_stats: Dict[str, Any]
) -> List[OptimizationProposal]:
    """Enrich proposals with ROI performance data."""
    for proposal in proposals:
        stats = roi_stats.get(proposal.programme_id)
        if stats:
            # Adjust confidence based on ROI trend
            roi_boost = getattr(stats, "predictive_boost", 1.0)
            trend = getattr(stats, "trend", "stable")

            if trend == "rising" and roi_boost > 1.0:
                # ROI supports boosting - increase confidence
                if proposal.action == OptimizationAction.BOOST_PRIORITY:
                    proposal.confidence = min(0.95, proposal.confidence * 1.1)
                    proposal.reason += f" | ROI trend: {trend} (boost: {roi_boost:.2f})"
            elif trend == "declining":
                # ROI declining - adjust confidence accordingly
                if proposal.action == OptimizationAction.BOOST_PRIORITY:
                    proposal.confidence *= 0.8
                    proposal.reason += f" | Warning: ROI declining"

    return proposals


def _apply_proposal(proposal: OptimizationProposal) -> bool:
    """Apply a single optimization proposal."""
    from services.funding_confidence_rebalancer import apply_adjustment

    if proposal.action == OptimizationAction.BOOST_PRIORITY:
        boost_factor = 1.0 + (abs(proposal.change_pct) / 100)
        apply_adjustment(
            proposal.programme_id,
            boost_factor,
            f"Auto-optimizer: {proposal.reason}",
            "boost"
        )
    elif proposal.action == OptimizationAction.REDUCE_PRIORITY:
        reduction_factor = 1.0 - (abs(proposal.change_pct) / 100)
        apply_adjustment(
            proposal.programme_id,
            reduction_factor,
            f"Auto-optimizer: {proposal.reason}",
            "penalty"
        )
    else:
        return False

    logger.info(f"Applied proposal {proposal.proposal_id}: {proposal.action.value} for {proposal.programme_id}")
    return True


# ============================================================================
# Proposal Management
# ============================================================================

def get_pending_proposals() -> List[Dict[str, Any]]:
    """Get all pending (unapplied) proposals from the last run."""
    if not _optimization_runs:
        return []

    last_run = _optimization_runs[-1]
    if last_run.status == OptimizationStatus.DRY_RUN:
        return [p.to_dict() for p in last_run.proposals]
    return []


def approve_proposal(proposal_id: str) -> Dict[str, Any]:
    """Manually approve and apply a specific proposal."""
    if not _optimization_runs:
        return {"success": False, "error": "No optimization runs found"}

    last_run = _optimization_runs[-1]
    for proposal in last_run.proposals:
        if proposal.proposal_id == proposal_id:
            try:
                _apply_proposal(proposal)
                return {"success": True, "proposal": proposal.to_dict()}
            except Exception as e:
                return {"success": False, "error": str(e)}

    return {"success": False, "error": f"Proposal {proposal_id} not found"}


def reject_proposal(proposal_id: str) -> Dict[str, Any]:
    """Reject a proposal (remove from pending)."""
    global _pending_proposals
    _pending_proposals = [p for p in _pending_proposals if p.proposal_id != proposal_id]
    return {"success": True, "message": f"Proposal {proposal_id} rejected"}


def approve_all_proposals() -> Dict[str, Any]:
    """Approve and apply all pending proposals."""
    if not _optimization_runs:
        return {"success": False, "error": "No optimization runs found"}

    last_run = _optimization_runs[-1]
    if last_run.status != OptimizationStatus.DRY_RUN:
        return {"success": False, "error": "No pending proposals (last run was not dry run)"}

    applied = 0
    failed = 0
    for proposal in last_run.proposals:
        if proposal.confidence >= 0.6:
            try:
                _apply_proposal(proposal)
                applied += 1
            except Exception:
                failed += 1

    return {"success": True, "applied": applied, "failed": failed}


# ============================================================================
# State and History
# ============================================================================

def get_optimizer_state() -> OptimizerState:
    """Get current optimizer state."""
    last_run = _optimization_runs[-1] if _optimization_runs else None

    # Calculate next scheduled run
    next_run = None
    if _last_run_timestamp:
        next_time = _last_run_timestamp + timedelta(hours=FUNDING_OPTIMIZER_CYCLE_HOURS)
        if next_time > datetime.now(timezone.utc):
            next_run = next_time.isoformat()

    # Get current distribution delta
    current_delta = 0.0
    try:
        from services.funding_distribution import analyze_distribution
        dist = analyze_distribution()
        current_delta = dist.delta_score
    except Exception:
        pass

    return OptimizerState(
        enabled=FUNDING_OPTIMIZER_ENABLED,
        last_run_id=last_run.run_id if last_run else None,
        last_run_timestamp=last_run.timestamp if last_run else None,
        last_run_status=last_run.status.value if last_run else None,
        next_scheduled_run=next_run,
        total_runs=len(_optimization_runs),
        total_proposals_applied=sum(r.applied_count for r in _optimization_runs),
        current_distribution_delta=current_delta,
        auto_apply_enabled=FUNDING_OPTIMIZER_AUTO_APPLY,
        dry_run_mode=FUNDING_OPTIMIZER_DRY_RUN
    )


def get_optimization_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get history of optimization runs."""
    runs = sorted(
        _optimization_runs,
        key=lambda x: x.timestamp,
        reverse=True
    )[:limit]
    return [r.to_dict() for r in runs]


def get_optimization_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific optimization run by ID."""
    for run in _optimization_runs:
        if run.run_id == run_id:
            return run.to_dict()
    return None


def get_optimization_summary() -> Dict[str, Any]:
    """Get summary of all optimization activity."""
    if not _optimization_runs:
        return {
            "enabled": FUNDING_OPTIMIZER_ENABLED,
            "total_runs": 0,
            "successful_runs": 0,
            "total_proposals": 0,
            "total_applied": 0,
            "average_improvement": 0.0
        }

    successful = [r for r in _optimization_runs if r.status == OptimizationStatus.COMPLETED]

    # Calculate average improvement
    improvements = []
    for run in successful:
        if run.distribution_delta_before > 0:
            improvement = (run.distribution_delta_before - run.distribution_delta_after) / run.distribution_delta_before
            improvements.append(improvement)

    avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0

    return {
        "enabled": FUNDING_OPTIMIZER_ENABLED,
        "total_runs": len(_optimization_runs),
        "successful_runs": len(successful),
        "total_proposals": sum(len(r.proposals) for r in _optimization_runs),
        "total_applied": sum(r.applied_count for r in _optimization_runs),
        "average_improvement": round(avg_improvement * 100, 2),
        "last_run": _optimization_runs[-1].to_dict() if _optimization_runs else None
    }


# ============================================================================
# Persistence
# ============================================================================

def _persist_run(run: OptimizationRun) -> None:
    """Persist optimization run to filesystem."""
    try:
        storage_path = Path(FUNDING_OPTIMIZER_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)

        filepath = storage_path / f"{run.run_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(run.to_dict(), f, indent=2, ensure_ascii=False)

        logger.debug(f"Persisted optimization run: {filepath}")
    except Exception as e:
        logger.error(f"Failed to persist optimization run: {e}")


def load_optimization_history() -> int:
    """Load optimization history from storage. Returns count loaded."""
    global _optimization_runs

    storage_path = Path(FUNDING_OPTIMIZER_STORAGE_PATH)
    if not storage_path.exists():
        return 0

    loaded = 0
    for filepath in storage_path.glob("opt_*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            proposals = [
                OptimizationProposal(
                    proposal_id=p["proposal_id"],
                    programme_id=p["programme_id"],
                    programme_name=p["programme_name"],
                    action=OptimizationAction(p["action"]),
                    current_value=p["current_value"],
                    proposed_value=p["proposed_value"],
                    change_pct=p["change_pct"],
                    reason=p["reason"],
                    confidence=p["confidence"],
                    data_points=p["data_points"]
                )
                for p in data.get("proposals", [])
            ]

            run = OptimizationRun(
                run_id=data["run_id"],
                timestamp=data["timestamp"],
                status=OptimizationStatus(data["status"]),
                proposals=proposals,
                applied_count=data["applied_count"],
                skipped_count=data["skipped_count"],
                distribution_delta_before=data["distribution_delta_before"],
                distribution_delta_after=data["distribution_delta_after"],
                total_recommendations_analyzed=data["total_recommendations_analyzed"],
                dry_run=data["dry_run"],
                duration_ms=data["duration_ms"],
                errors=data.get("errors", [])
            )
            _optimization_runs.append(run)
            loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load optimization run {filepath}: {e}")

    logger.info(f"Loaded {loaded} optimization runs from storage")
    return loaded


# ============================================================================
# Module Initialization
# ============================================================================

def _initialize_module() -> None:
    """Initialize module on import."""
    if FUNDING_OPTIMIZER_ENABLED:
        try:
            load_optimization_history()
        except Exception as e:
            logger.warning(f"Could not load optimization history: {e}")


_initialize_module()
