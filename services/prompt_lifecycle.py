"""
G17.7-D – Lifecycle State Machine

Manages prompt states and transitions through the prompt management lifecycle.

States:
- ACTIVE: Prompt is in normal operation
- TUNING-OPTIMIZED: Prompt was adjusted by tuner
- REWRITE-READY: Prompt has rewrite proposal, awaiting confirmation
- GOVERNANCE-WAIT: Drift/Gate approval required
- FROZEN: Prompt is frozen
- RECOVERING: Rollback in progress
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Set
from pathlib import Path

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ENV Configuration
# ─────────────────────────────────────────────────────────────────────────────

LIFECYCLE_ENABLED = os.getenv("LIFECYCLE_ENABLED", "true").lower() == "true"
LIFECYCLE_LOG_TRANSITIONS = os.getenv("LIFECYCLE_LOG_TRANSITIONS", "true").lower() == "true"
LIFECYCLE_MAX_HISTORY = int(os.getenv("LIFECYCLE_MAX_HISTORY", "100"))

# Storage path
LIFECYCLE_STORAGE_PATH = os.getenv(
    "LIFECYCLE_STORAGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "storage", "prompt_lifecycle")
)


# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle States
# ─────────────────────────────────────────────────────────────────────────────

class LifecycleState(str, Enum):
    """Prompt lifecycle states."""
    ACTIVE = "ACTIVE"
    TUNING_OPTIMIZED = "TUNING-OPTIMIZED"
    REWRITE_READY = "REWRITE-READY"
    GOVERNANCE_WAIT = "GOVERNANCE-WAIT"
    FROZEN = "FROZEN"
    RECOVERING = "RECOVERING"

    @classmethod
    def from_string(cls, value: str) -> "LifecycleState":
        """Parse state from string."""
        normalized = value.upper().replace("_", "-")
        for state in cls:
            if state.value == normalized:
                return state
        raise ValueError(f"Unknown lifecycle state: {value}")


# ─────────────────────────────────────────────────────────────────────────────
# Valid Transitions
# ─────────────────────────────────────────────────────────────────────────────

# Define allowed state transitions
VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
    LifecycleState.ACTIVE: {
        LifecycleState.TUNING_OPTIMIZED,  # Auto-tuning applied
        LifecycleState.REWRITE_READY,      # Rewrite proposal ready
        LifecycleState.GOVERNANCE_WAIT,    # Drift/gate block
        LifecycleState.FROZEN,             # Freeze trigger
    },
    LifecycleState.TUNING_OPTIMIZED: {
        LifecycleState.ACTIVE,             # After stabilization
        LifecycleState.REWRITE_READY,      # Rewrite needed
        LifecycleState.GOVERNANCE_WAIT,    # Drift/gate block
        LifecycleState.FROZEN,             # Freeze trigger
    },
    LifecycleState.REWRITE_READY: {
        LifecycleState.ACTIVE,             # Rewrite confirmed/rejected
        LifecycleState.TUNING_OPTIMIZED,   # Tuning after rewrite
        LifecycleState.GOVERNANCE_WAIT,    # Drift/gate block
        LifecycleState.FROZEN,             # Freeze trigger
    },
    LifecycleState.GOVERNANCE_WAIT: {
        LifecycleState.ACTIVE,             # Approval granted
        LifecycleState.TUNING_OPTIMIZED,   # Re-tuning
        LifecycleState.REWRITE_READY,      # Rewrite needed
        LifecycleState.FROZEN,             # Freeze trigger
    },
    LifecycleState.FROZEN: {
        LifecycleState.RECOVERING,         # Recovery started
        LifecycleState.ACTIVE,             # Manual unfreeze
    },
    LifecycleState.RECOVERING: {
        LifecycleState.ACTIVE,             # Recovery complete
        LifecycleState.FROZEN,             # Recovery failed
        LifecycleState.GOVERNANCE_WAIT,    # Recovery needs approval
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: str
    to_state: str
    reason: str
    triggered_by: str = "system"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptLifecycle:
    """Lifecycle record for a prompt."""
    prompt_file: str
    current_state: str = LifecycleState.ACTIVE.value
    previous_state: Optional[str] = None
    state_since: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    transition_history: List[StateTransition] = field(default_factory=list)
    total_transitions: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────────────────────────────────────
# In-Memory State (with file persistence)
# ─────────────────────────────────────────────────────────────────────────────

_lifecycle_registry: Dict[str, PromptLifecycle] = {}


def _get_lifecycle_file_path(prompt_file: str) -> Path:
    """Get path for lifecycle record file."""
    safe_name = prompt_file.replace("/", "_").replace("\\", "_").replace(".", "_")
    return Path(LIFECYCLE_STORAGE_PATH) / f"lifecycle_{safe_name}.json"


def _ensure_storage_dir() -> None:
    """Ensure storage directory exists."""
    Path(LIFECYCLE_STORAGE_PATH).mkdir(parents=True, exist_ok=True)


def _load_lifecycle(prompt_file: str) -> PromptLifecycle:
    """Load lifecycle record from disk."""
    if prompt_file in _lifecycle_registry:
        return _lifecycle_registry[prompt_file]

    file_path = _get_lifecycle_file_path(prompt_file)
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                data: Dict[str, Any] = json.load(f)
                transitions = [
                    StateTransition(**t) if isinstance(t, dict) else t
                    for t in data.get("transition_history", [])
                ]
                lifecycle = PromptLifecycle(
                    prompt_file=data["prompt_file"],
                    current_state=data.get("current_state", LifecycleState.ACTIVE.value),
                    previous_state=data.get("previous_state"),
                    state_since=data.get("state_since", ""),
                    transition_history=transitions,
                    total_transitions=data.get("total_transitions", 0),
                    created_at=data.get("created_at", "")
                )
                _lifecycle_registry[prompt_file] = lifecycle
                return lifecycle
        except Exception as e:
            logger.error(f"Error loading lifecycle for {prompt_file}: {e}")

    # Create new lifecycle
    lifecycle = PromptLifecycle(prompt_file=prompt_file)
    _lifecycle_registry[prompt_file] = lifecycle
    return lifecycle


def _save_lifecycle(lifecycle: PromptLifecycle) -> bool:
    """Save lifecycle record to disk."""
    try:
        _ensure_storage_dir()
        file_path = _get_lifecycle_file_path(lifecycle.prompt_file)

        # Trim history if needed
        if len(lifecycle.transition_history) > LIFECYCLE_MAX_HISTORY:
            lifecycle.transition_history = lifecycle.transition_history[-LIFECYCLE_MAX_HISTORY:]

        data = {
            "prompt_file": lifecycle.prompt_file,
            "current_state": lifecycle.current_state,
            "previous_state": lifecycle.previous_state,
            "state_since": lifecycle.state_since,
            "transition_history": [asdict(t) for t in lifecycle.transition_history],
            "total_transitions": lifecycle.total_transitions,
            "created_at": lifecycle.created_at
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        _lifecycle_registry[lifecycle.prompt_file] = lifecycle
        return True
    except Exception as e:
        logger.error(f"Error saving lifecycle: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Transition Validation
# ─────────────────────────────────────────────────────────────────────────────

def is_valid_transition(from_state: LifecycleState, to_state: LifecycleState) -> bool:
    """
    Check if a state transition is valid.

    Args:
        from_state: Current state
        to_state: Target state

    Returns:
        True if transition is valid
    """
    if from_state == to_state:
        return True  # Same state is always valid (no-op)

    valid_targets = VALID_TRANSITIONS.get(from_state, set())
    return to_state in valid_targets


def get_valid_transitions(from_state: LifecycleState) -> List[str]:
    """
    Get list of valid target states from current state.

    Args:
        from_state: Current state

    Returns:
        List of valid target state values
    """
    valid_targets = VALID_TRANSITIONS.get(from_state, set())
    return [state.value for state in valid_targets]


# ─────────────────────────────────────────────────────────────────────────────
# Core API Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_lifecycle_state(prompt_file: str) -> Dict[str, Any]:
    """
    Get the current lifecycle state for a prompt.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        Dict with lifecycle state information
    """
    lifecycle = _load_lifecycle(prompt_file)

    try:
        current = LifecycleState.from_string(lifecycle.current_state)
        valid_next = get_valid_transitions(current)
    except ValueError:
        valid_next = []

    return {
        "prompt_file": prompt_file,
        "current_state": lifecycle.current_state,
        "previous_state": lifecycle.previous_state,
        "state_since": lifecycle.state_since,
        "valid_transitions": valid_next,
        "total_transitions": lifecycle.total_transitions,
        "created_at": lifecycle.created_at
    }


def transition_state(
    prompt_file: str,
    new_state: str,
    reason: str,
    triggered_by: str = "system",
    force: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Transition a prompt to a new lifecycle state.

    Args:
        prompt_file: Path to the prompt file
        new_state: Target state
        reason: Reason for transition
        triggered_by: Who triggered the transition
        force: Force invalid transitions (not recommended)
        metadata: Additional transition metadata

    Returns:
        Dict with transition result
    """
    if not LIFECYCLE_ENABLED:
        return {
            "success": False,
            "error": "Lifecycle management is disabled"
        }

    lifecycle = _load_lifecycle(prompt_file)

    try:
        from_state = LifecycleState.from_string(lifecycle.current_state)
        to_state = LifecycleState.from_string(new_state)
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid state: {e}"
        }

    # Same state - no-op
    if from_state == to_state:
        return {
            "success": True,
            "message": "Already in target state",
            "current_state": lifecycle.current_state
        }

    # Validate transition
    if not is_valid_transition(from_state, to_state) and not force:
        return {
            "success": False,
            "error": f"Invalid transition from {from_state.value} to {to_state.value}",
            "valid_transitions": get_valid_transitions(from_state)
        }

    # Create transition record
    transition = StateTransition(
        from_state=from_state.value,
        to_state=to_state.value,
        reason=reason,
        triggered_by=triggered_by,
        metadata=metadata or {}
    )

    # Update lifecycle
    lifecycle.previous_state = lifecycle.current_state
    lifecycle.current_state = to_state.value
    lifecycle.state_since = datetime.utcnow().isoformat()
    lifecycle.transition_history.append(transition)
    lifecycle.total_transitions += 1

    # Save
    _save_lifecycle(lifecycle)

    if LIFECYCLE_LOG_TRANSITIONS:
        logger.info(
            f"Lifecycle transition: {prompt_file} | {from_state.value} -> {to_state.value} | {reason}"
        )

    return {
        "success": True,
        "prompt_file": prompt_file,
        "from_state": from_state.value,
        "to_state": to_state.value,
        "reason": reason,
        "triggered_by": triggered_by,
        "timestamp": transition.timestamp
    }


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Transition Functions
# ─────────────────────────────────────────────────────────────────────────────

def mark_tuning_optimized(
    prompt_file: str,
    tuning_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Transition to TUNING-OPTIMIZED state after auto-tuning."""
    return transition_state(
        prompt_file=prompt_file,
        new_state=LifecycleState.TUNING_OPTIMIZED.value,
        reason="Auto-tuning applied",
        triggered_by="tuner",
        metadata=tuning_details
    )


def mark_rewrite_ready(
    prompt_file: str,
    rewrite_proposal: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Transition to REWRITE-READY state when rewrite is proposed."""
    return transition_state(
        prompt_file=prompt_file,
        new_state=LifecycleState.REWRITE_READY.value,
        reason="Rewrite proposal ready",
        triggered_by="rewrite-engine",
        metadata=rewrite_proposal
    )


def mark_governance_wait(
    prompt_file: str,
    governance_reason: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Transition to GOVERNANCE-WAIT state when approval is needed."""
    return transition_state(
        prompt_file=prompt_file,
        new_state=LifecycleState.GOVERNANCE_WAIT.value,
        reason=governance_reason,
        triggered_by="governance",
        metadata=details
    )


def mark_frozen(
    prompt_file: str,
    freeze_reason: str,
    freeze_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Transition to FROZEN state."""
    return transition_state(
        prompt_file=prompt_file,
        new_state=LifecycleState.FROZEN.value,
        reason=freeze_reason,
        triggered_by="auto-freeze",
        metadata=freeze_details
    )


def mark_recovering(
    prompt_file: str,
    recovery_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Transition to RECOVERING state when recovery starts."""
    return transition_state(
        prompt_file=prompt_file,
        new_state=LifecycleState.RECOVERING.value,
        reason="Recovery initiated",
        triggered_by="recovery-system",
        metadata=recovery_details
    )


def mark_active(
    prompt_file: str,
    reason: str = "Returned to active state",
    triggered_by: str = "system"
) -> Dict[str, Any]:
    """Transition to ACTIVE state."""
    return transition_state(
        prompt_file=prompt_file,
        new_state=LifecycleState.ACTIVE.value,
        reason=reason,
        triggered_by=triggered_by
    )


# ─────────────────────────────────────────────────────────────────────────────
# History & Reporting
# ─────────────────────────────────────────────────────────────────────────────

def get_transition_history(
    prompt_file: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get transition history for a prompt.

    Args:
        prompt_file: Path to the prompt file
        limit: Maximum number of records to return

    Returns:
        List of transition records
    """
    lifecycle = _load_lifecycle(prompt_file)
    history = lifecycle.transition_history[-limit:]
    return [asdict(t) for t in history]


def get_state_duration(prompt_file: str) -> Dict[str, Any]:
    """
    Get how long prompt has been in current state.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        Dict with duration information
    """
    lifecycle = _load_lifecycle(prompt_file)

    try:
        state_since = datetime.fromisoformat(lifecycle.state_since.replace('Z', '+00:00'))
        now = datetime.utcnow()
        duration = now - state_since.replace(tzinfo=None)

        return {
            "prompt_file": prompt_file,
            "current_state": lifecycle.current_state,
            "state_since": lifecycle.state_since,
            "duration_seconds": int(duration.total_seconds()),
            "duration_human": str(duration)
        }
    except Exception as e:
        logger.error(f"Error calculating state duration: {e}")
        return {
            "prompt_file": prompt_file,
            "current_state": lifecycle.current_state,
            "error": str(e)
        }


def get_prompts_by_state(state: str) -> List[str]:
    """
    Get all prompts in a given state.

    Args:
        state: The lifecycle state to filter by

    Returns:
        List of prompt file paths
    """
    prompts: List[str] = []

    # Check files on disk
    try:
        storage_path = Path(LIFECYCLE_STORAGE_PATH)
        if storage_path.exists():
            for file_path in storage_path.glob("lifecycle_*.json"):
                try:
                    with open(file_path, "r") as f:
                        data: Dict[str, Any] = json.load(f)
                        if data.get("current_state", "").upper() == state.upper():
                            prompts.append(data.get("prompt_file", ""))
                except Exception as e:
                    logger.warning(f"Error reading lifecycle file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error listing prompts by state: {e}")

    return prompts


def get_lifecycle_statistics() -> Dict[str, Any]:
    """
    Get overall lifecycle statistics.

    Returns:
        Dict with lifecycle statistics
    """
    state_counts: Dict[str, int] = {state.value: 0 for state in LifecycleState}
    total_prompts = 0
    total_transitions = 0

    # Check files on disk
    try:
        storage_path = Path(LIFECYCLE_STORAGE_PATH)
        if storage_path.exists():
            for file_path in storage_path.glob("lifecycle_*.json"):
                try:
                    with open(file_path, "r") as f:
                        data: Dict[str, Any] = json.load(f)
                        current_state = data.get("current_state", "ACTIVE")
                        if current_state in state_counts:
                            state_counts[current_state] += 1
                        total_prompts += 1
                        total_transitions += data.get("total_transitions", 0)
                except Exception as e:
                    logger.warning(f"Error reading lifecycle file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error collecting lifecycle statistics: {e}")

    return {
        "total_prompts_tracked": total_prompts,
        "total_transitions": total_transitions,
        "state_distribution": state_counts,
        "lifecycle_enabled": LIFECYCLE_ENABLED,
        "available_states": [state.value for state in LifecycleState]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle Dashboard Data
# ─────────────────────────────────────────────────────────────────────────────

def get_lifecycle_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive lifecycle dashboard data.

    Returns:
        Dict with dashboard data
    """
    stats = get_lifecycle_statistics()

    # Find prompts needing attention
    frozen_prompts = get_prompts_by_state(LifecycleState.FROZEN.value)
    governance_waiting = get_prompts_by_state(LifecycleState.GOVERNANCE_WAIT.value)
    recovering = get_prompts_by_state(LifecycleState.RECOVERING.value)

    return {
        "statistics": stats,
        "attention_required": {
            "frozen_count": len(frozen_prompts),
            "frozen_prompts": frozen_prompts[:10],  # First 10
            "governance_waiting_count": len(governance_waiting),
            "governance_waiting": governance_waiting[:10],
            "recovering_count": len(recovering),
            "recovering": recovering[:10]
        },
        "state_transitions": {
            state.value: get_valid_transitions(state)
            for state in LifecycleState
        },
        "enabled": LIFECYCLE_ENABLED
    }
