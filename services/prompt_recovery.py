"""
G17.7-C – Auto-Recovery System

Automatic recovery to last stable version when prompt is frozen.
Uses checkpoint data from G17.6 for rollback operations.
"""

import os
import json
import logging
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ENV Configuration
# ─────────────────────────────────────────────────────────────────────────────

AUTO_RECOVERY_ENABLED = os.getenv("AUTO_RECOVERY_ENABLED", "true").lower() == "true"
RECOVERY_MIN_STABILITY_SCORE = int(os.getenv("RECOVERY_MIN_STABILITY_SCORE", "50"))
RECOVERY_MAX_ROLLBACK_VERSIONS = int(os.getenv("RECOVERY_MAX_ROLLBACK_VERSIONS", "5"))
RECOVERY_REQUIRE_APPROVAL = os.getenv("RECOVERY_REQUIRE_APPROVAL", "false").lower() == "true"

# Storage paths
RECOVERY_STORAGE_PATH = os.getenv(
    "RECOVERY_STORAGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "storage", "prompt_recovery")
)
CHECKPOINT_STORAGE_PATH = os.getenv(
    "CHECKPOINT_STORAGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "storage", "prompt_checkpoints")
)


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RecoveryCandidate:
    """A candidate version for recovery."""
    checkpoint_id: str
    checkpoint_path: str
    version: str
    stability_score: int
    created_at: str
    is_stable: bool
    reason_stable: str = ""


@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt."""
    attempt_id: str
    prompt_file: str
    from_version: str
    to_version: str
    checkpoint_used: str
    status: str  # PENDING, IN_PROGRESS, SUCCESS, FAILED, ROLLED_BACK
    triggered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    triggered_by: str = "auto"
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    rollback_reason: Optional[str] = None
    approval_status: Optional[str] = None  # None, PENDING, APPROVED, REJECTED


@dataclass
class RecoveryHistory:
    """History of recovery attempts for a prompt."""
    prompt_file: str
    attempts: List[RecoveryAttempt] = field(default_factory=list)
    last_successful_recovery: Optional[str] = None
    total_recoveries: int = 0
    total_failures: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# In-Memory State (with file persistence)
# ─────────────────────────────────────────────────────────────────────────────

_recovery_history: Dict[str, RecoveryHistory] = {}
_pending_recoveries: Dict[str, RecoveryAttempt] = {}


def _get_recovery_file_path(prompt_file: str) -> Path:
    """Get path for recovery history file."""
    safe_name = prompt_file.replace("/", "_").replace("\\", "_").replace(".", "_")
    return Path(RECOVERY_STORAGE_PATH) / f"recovery_{safe_name}.json"


def _ensure_storage_dir() -> None:
    """Ensure storage directory exists."""
    Path(RECOVERY_STORAGE_PATH).mkdir(parents=True, exist_ok=True)


def _generate_attempt_id() -> str:
    """Generate a unique attempt ID."""
    import uuid
    return f"recovery_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _load_recovery_history(prompt_file: str) -> RecoveryHistory:
    """Load recovery history from disk."""
    if prompt_file in _recovery_history:
        return _recovery_history[prompt_file]

    file_path = _get_recovery_file_path(prompt_file)
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                data: Dict[str, Any] = json.load(f)
                attempts = [
                    RecoveryAttempt(**a) if isinstance(a, dict) else a
                    for a in data.get("attempts", [])
                ]
                history = RecoveryHistory(
                    prompt_file=data["prompt_file"],
                    attempts=attempts,
                    last_successful_recovery=data.get("last_successful_recovery"),
                    total_recoveries=data.get("total_recoveries", 0),
                    total_failures=data.get("total_failures", 0)
                )
                _recovery_history[prompt_file] = history
                return history
        except Exception as e:
            logger.error(f"Error loading recovery history for {prompt_file}: {e}")

    # Create new history
    history = RecoveryHistory(prompt_file=prompt_file)
    _recovery_history[prompt_file] = history
    return history


def _save_recovery_history(history: RecoveryHistory) -> bool:
    """Save recovery history to disk."""
    try:
        _ensure_storage_dir()
        file_path = _get_recovery_file_path(history.prompt_file)

        data = {
            "prompt_file": history.prompt_file,
            "attempts": [asdict(a) for a in history.attempts],
            "last_successful_recovery": history.last_successful_recovery,
            "total_recoveries": history.total_recoveries,
            "total_failures": history.total_failures
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        _recovery_history[history.prompt_file] = history
        return True
    except Exception as e:
        logger.error(f"Error saving recovery history: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Checkpoint Integration (from G17.6)
# ─────────────────────────────────────────────────────────────────────────────

def _get_checkpoint_path(prompt_file: str) -> Path:
    """Get checkpoint directory for a prompt."""
    safe_name = prompt_file.replace("/", "_").replace("\\", "_").replace(".", "_")
    return Path(CHECKPOINT_STORAGE_PATH) / safe_name


def _list_checkpoints(prompt_file: str) -> List[Dict[str, Any]]:
    """List all available checkpoints for a prompt."""
    checkpoint_dir = _get_checkpoint_path(prompt_file)
    checkpoints: List[Dict[str, Any]] = []

    if not checkpoint_dir.exists():
        return checkpoints

    try:
        for checkpoint_file in sorted(checkpoint_dir.glob("*.json"), reverse=True):
            try:
                with open(checkpoint_file, "r") as f:
                    data: Dict[str, Any] = json.load(f)
                    checkpoints.append({
                        "checkpoint_id": checkpoint_file.stem,
                        "checkpoint_path": str(checkpoint_file),
                        "version": data.get("version", "unknown"),
                        "created_at": data.get("created_at", ""),
                        "stability_score": data.get("stability_score", 0),
                        "hash": data.get("hash", ""),
                        "metadata": data.get("metadata", {})
                    })
            except Exception as e:
                logger.warning(f"Error reading checkpoint {checkpoint_file}: {e}")
    except Exception as e:
        logger.error(f"Error listing checkpoints: {e}")

    return checkpoints


def _load_checkpoint_content(checkpoint_path: str) -> Optional[Dict[str, Any]]:
    """Load the full content of a checkpoint."""
    try:
        with open(checkpoint_path, "r") as f:
            data: Dict[str, Any] = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Error loading checkpoint {checkpoint_path}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Recovery Candidate Selection
# ─────────────────────────────────────────────────────────────────────────────

def find_recovery_candidates(
    prompt_file: str,
    min_stability: Optional[int] = None
) -> List[RecoveryCandidate]:
    """
    Find suitable recovery candidates from checkpoints.

    Args:
        prompt_file: Path to the prompt file
        min_stability: Minimum stability score required (default from ENV)

    Returns:
        List of RecoveryCandidate sorted by stability (highest first)
    """
    min_score = min_stability if min_stability is not None else RECOVERY_MIN_STABILITY_SCORE
    checkpoints = _list_checkpoints(prompt_file)
    candidates: List[RecoveryCandidate] = []

    for cp in checkpoints[:RECOVERY_MAX_ROLLBACK_VERSIONS]:
        stability = cp.get("stability_score", 0)
        is_stable = stability >= min_score

        candidate = RecoveryCandidate(
            checkpoint_id=cp["checkpoint_id"],
            checkpoint_path=cp["checkpoint_path"],
            version=cp["version"],
            stability_score=stability,
            created_at=cp["created_at"],
            is_stable=is_stable,
            reason_stable=f"Score {stability} >= {min_score}" if is_stable else f"Score {stability} < {min_score}"
        )
        candidates.append(candidate)

    # Sort by stability score (highest first)
    candidates.sort(key=lambda c: c.stability_score, reverse=True)

    return candidates


def get_best_recovery_candidate(prompt_file: str) -> Optional[RecoveryCandidate]:
    """
    Get the best candidate for recovery.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        Best RecoveryCandidate or None if no suitable candidate
    """
    candidates = find_recovery_candidates(prompt_file)

    # Find first stable candidate
    for candidate in candidates:
        if candidate.is_stable:
            return candidate

    # No stable candidate found
    logger.warning(f"No stable recovery candidate found for {prompt_file}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Core Recovery Operations
# ─────────────────────────────────────────────────────────────────────────────

def trigger_auto_recovery(
    prompt_file: str,
    triggered_by: str = "auto",
    force: bool = False
) -> Dict[str, Any]:
    """
    Trigger automatic recovery to last stable version.

    Args:
        prompt_file: Path to the prompt file
        triggered_by: Who triggered the recovery
        force: Force recovery even if approval is required

    Returns:
        Dict with recovery attempt details
    """
    if not AUTO_RECOVERY_ENABLED and not force:
        return {
            "success": False,
            "error": "Auto-recovery is disabled",
            "prompt_file": prompt_file
        }

    # Find best candidate
    candidate = get_best_recovery_candidate(prompt_file)
    if not candidate:
        return {
            "success": False,
            "error": "No stable recovery candidate available",
            "prompt_file": prompt_file,
            "candidates_checked": RECOVERY_MAX_ROLLBACK_VERSIONS
        }

    # Get current version
    current_version = "current"  # Would be determined from actual prompt file

    # Create recovery attempt
    attempt = RecoveryAttempt(
        attempt_id=_generate_attempt_id(),
        prompt_file=prompt_file,
        from_version=current_version,
        to_version=candidate.version,
        checkpoint_used=candidate.checkpoint_path,
        status="PENDING" if RECOVERY_REQUIRE_APPROVAL and not force else "IN_PROGRESS",
        triggered_by=triggered_by,
        approval_status="PENDING" if RECOVERY_REQUIRE_APPROVAL and not force else None
    )

    # Store pending recovery
    _pending_recoveries[attempt.attempt_id] = attempt

    if RECOVERY_REQUIRE_APPROVAL and not force:
        logger.info(f"Recovery {attempt.attempt_id} awaiting approval")
        return {
            "success": True,
            "status": "PENDING_APPROVAL",
            "attempt_id": attempt.attempt_id,
            "prompt_file": prompt_file,
            "target_version": candidate.version,
            "stability_score": candidate.stability_score,
            "message": "Recovery awaiting approval"
        }

    # Execute recovery
    return _execute_recovery(attempt, candidate)


def _execute_recovery(
    attempt: RecoveryAttempt,
    candidate: RecoveryCandidate
) -> Dict[str, Any]:
    """
    Execute the actual recovery operation.

    Args:
        attempt: The recovery attempt record
        candidate: The recovery candidate to apply

    Returns:
        Dict with recovery result
    """
    attempt.status = "IN_PROGRESS"
    history = _load_recovery_history(attempt.prompt_file)

    try:
        # Load checkpoint content
        checkpoint_content = _load_checkpoint_content(candidate.checkpoint_path)
        if not checkpoint_content:
            raise ValueError(f"Failed to load checkpoint: {candidate.checkpoint_path}")

        # Get the prompt content from checkpoint
        prompt_content = checkpoint_content.get("content")
        if not prompt_content:
            raise ValueError("Checkpoint does not contain prompt content")

        # Backup current version before recovery
        backup_path = _backup_current_prompt(attempt.prompt_file)

        # Apply recovery
        recovery_success = _apply_recovered_content(attempt.prompt_file, prompt_content)

        if recovery_success:
            attempt.status = "SUCCESS"
            attempt.completed_at = datetime.utcnow().isoformat()
            history.total_recoveries += 1
            history.last_successful_recovery = attempt.completed_at

            logger.info(f"Recovery {attempt.attempt_id} completed successfully")
        else:
            raise ValueError("Failed to apply recovered content")

    except Exception as e:
        attempt.status = "FAILED"
        attempt.completed_at = datetime.utcnow().isoformat()
        attempt.error_message = str(e)
        history.total_failures += 1

        logger.error(f"Recovery {attempt.attempt_id} failed: {e}")

    # Save attempt to history
    history.attempts.append(attempt)
    _save_recovery_history(history)

    # Clean up pending
    if attempt.attempt_id in _pending_recoveries:
        del _pending_recoveries[attempt.attempt_id]

    return {
        "success": attempt.status == "SUCCESS",
        "status": attempt.status,
        "attempt_id": attempt.attempt_id,
        "prompt_file": attempt.prompt_file,
        "from_version": attempt.from_version,
        "to_version": attempt.to_version,
        "completed_at": attempt.completed_at,
        "error": attempt.error_message
    }


def _backup_current_prompt(prompt_file: str) -> Optional[str]:
    """
    Create a backup of the current prompt before recovery.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        Path to backup file or None if backup failed
    """
    try:
        backup_dir = Path(RECOVERY_STORAGE_PATH) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        safe_name = prompt_file.replace("/", "_").replace("\\", "_").replace(".", "_")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{safe_name}_backup_{timestamp}.json"

        # Read current content if file exists
        prompt_path = Path(prompt_file)
        if prompt_path.exists():
            shutil.copy2(prompt_path, backup_path)
            return str(backup_path)

        # If prompt file doesn't exist, create empty backup marker
        with open(backup_path, "w") as f:
            json.dump({"original_missing": True, "timestamp": timestamp}, f)

        return str(backup_path)
    except Exception as e:
        logger.error(f"Failed to backup prompt {prompt_file}: {e}")
        return None


def _apply_recovered_content(prompt_file: str, content: Any) -> bool:
    """
    Apply recovered content to the prompt file.

    Args:
        prompt_file: Path to the prompt file
        content: Content to apply

    Returns:
        True if successful, False otherwise
    """
    try:
        prompt_path = Path(prompt_file)
        prompt_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, dict):
            with open(prompt_path, "w") as f:
                json.dump(content, f, indent=2)
        else:
            with open(prompt_path, "w") as f:
                f.write(str(content))

        logger.info(f"Applied recovered content to {prompt_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to apply recovered content: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Approval Workflow
# ─────────────────────────────────────────────────────────────────────────────

def approve_recovery(attempt_id: str, approved_by: str = "manual") -> Dict[str, Any]:
    """
    Approve a pending recovery attempt.

    Args:
        attempt_id: ID of the recovery attempt
        approved_by: Who approved the recovery

    Returns:
        Dict with approval result
    """
    attempt = _pending_recoveries.get(attempt_id)
    if not attempt:
        return {
            "success": False,
            "error": f"No pending recovery found with ID {attempt_id}"
        }

    if attempt.approval_status != "PENDING":
        return {
            "success": False,
            "error": f"Recovery is not pending approval (status: {attempt.approval_status})"
        }

    attempt.approval_status = "APPROVED"

    # Get candidate and execute
    candidate = get_best_recovery_candidate(attempt.prompt_file)
    if not candidate:
        return {
            "success": False,
            "error": "Recovery candidate no longer available"
        }

    return _execute_recovery(attempt, candidate)


def reject_recovery(
    attempt_id: str,
    rejected_by: str = "manual",
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reject a pending recovery attempt.

    Args:
        attempt_id: ID of the recovery attempt
        rejected_by: Who rejected the recovery
        reason: Reason for rejection

    Returns:
        Dict with rejection result
    """
    attempt = _pending_recoveries.get(attempt_id)
    if not attempt:
        return {
            "success": False,
            "error": f"No pending recovery found with ID {attempt_id}"
        }

    attempt.approval_status = "REJECTED"
    attempt.status = "FAILED"
    attempt.completed_at = datetime.utcnow().isoformat()
    attempt.error_message = reason or "Recovery rejected"

    # Save to history
    history = _load_recovery_history(attempt.prompt_file)
    history.attempts.append(attempt)
    history.total_failures += 1
    _save_recovery_history(history)

    # Clean up pending
    del _pending_recoveries[attempt_id]

    return {
        "success": True,
        "status": "REJECTED",
        "attempt_id": attempt_id,
        "rejected_by": rejected_by,
        "reason": reason
    }


def get_pending_recoveries() -> List[Dict[str, Any]]:
    """
    Get all pending recovery attempts.

    Returns:
        List of pending recovery attempts
    """
    return [asdict(a) for a in _pending_recoveries.values()]


# ─────────────────────────────────────────────────────────────────────────────
# History & Reporting
# ─────────────────────────────────────────────────────────────────────────────

def get_recovery_history(prompt_file: str) -> Dict[str, Any]:
    """
    Get recovery history for a prompt.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        Dict with recovery history
    """
    history = _load_recovery_history(prompt_file)

    return {
        "prompt_file": history.prompt_file,
        "total_recoveries": history.total_recoveries,
        "total_failures": history.total_failures,
        "last_successful_recovery": history.last_successful_recovery,
        "attempts": [asdict(a) for a in history.attempts[-10:]],  # Last 10 attempts
        "success_rate": (
            history.total_recoveries / (history.total_recoveries + history.total_failures)
            if (history.total_recoveries + history.total_failures) > 0
            else 1.0
        )
    }


def get_recovery_statistics() -> Dict[str, Any]:
    """
    Get overall recovery statistics.

    Returns:
        Dict with global recovery statistics
    """
    total_recoveries = 0
    total_failures = 0
    prompts_with_recovery: List[str] = []

    # Check files on disk
    try:
        storage_path = Path(RECOVERY_STORAGE_PATH)
        if storage_path.exists():
            for file_path in storage_path.glob("recovery_*.json"):
                try:
                    with open(file_path, "r") as f:
                        data: Dict[str, Any] = json.load(f)
                        total_recoveries += data.get("total_recoveries", 0)
                        total_failures += data.get("total_failures", 0)
                        if data.get("total_recoveries", 0) > 0:
                            prompts_with_recovery.append(data.get("prompt_file", ""))
                except Exception as e:
                    logger.warning(f"Error reading recovery file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error collecting recovery statistics: {e}")

    return {
        "total_recoveries": total_recoveries,
        "total_failures": total_failures,
        "success_rate": (
            total_recoveries / (total_recoveries + total_failures)
            if (total_recoveries + total_failures) > 0
            else 1.0
        ),
        "prompts_recovered_count": len(prompts_with_recovery),
        "pending_recoveries": len(_pending_recoveries),
        "auto_recovery_enabled": AUTO_RECOVERY_ENABLED,
        "require_approval": RECOVERY_REQUIRE_APPROVAL,
        "settings": {
            "min_stability_score": RECOVERY_MIN_STABILITY_SCORE,
            "max_rollback_versions": RECOVERY_MAX_ROLLBACK_VERSIONS
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rollback Support
# ─────────────────────────────────────────────────────────────────────────────

def rollback_recovery(attempt_id: str, reason: str = "Manual rollback") -> Dict[str, Any]:
    """
    Rollback a completed recovery to restore previous state.

    Args:
        attempt_id: ID of the recovery attempt to rollback
        reason: Reason for rollback

    Returns:
        Dict with rollback result
    """
    # Find the attempt in history
    for prompt_file, history in _recovery_history.items():
        for attempt in history.attempts:
            if attempt.attempt_id == attempt_id:
                if attempt.status != "SUCCESS":
                    return {
                        "success": False,
                        "error": "Can only rollback successful recoveries"
                    }

                # Find backup file
                backup_dir = Path(RECOVERY_STORAGE_PATH) / "backups"
                safe_name = prompt_file.replace("/", "_").replace("\\", "_").replace(".", "_")

                # Look for backup created around the same time
                try:
                    backups = list(backup_dir.glob(f"{safe_name}_backup_*.json"))
                    if not backups:
                        return {
                            "success": False,
                            "error": "No backup found for rollback"
                        }

                    # Use most recent backup
                    backup_file = sorted(backups)[-1]

                    # Restore from backup
                    with open(backup_file, "r") as f:
                        backup_data: Dict[str, Any] = json.load(f)

                    if backup_data.get("original_missing"):
                        # Original was missing, remove restored file
                        prompt_path = Path(prompt_file)
                        if prompt_path.exists():
                            prompt_path.unlink()
                    else:
                        # Copy backup back
                        shutil.copy2(backup_file, prompt_file)

                    # Update attempt status
                    attempt.status = "ROLLED_BACK"
                    attempt.rollback_reason = reason
                    _save_recovery_history(history)

                    return {
                        "success": True,
                        "status": "ROLLED_BACK",
                        "attempt_id": attempt_id,
                        "prompt_file": prompt_file,
                        "reason": reason
                    }

                except Exception as e:
                    logger.error(f"Rollback failed: {e}")
                    return {
                        "success": False,
                        "error": str(e)
                    }

    return {
        "success": False,
        "error": f"Recovery attempt {attempt_id} not found"
    }
