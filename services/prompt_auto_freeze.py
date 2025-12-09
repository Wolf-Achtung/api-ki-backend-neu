"""
G17.7-B – Auto-Freeze Mechanism

Automatic prompt freezing based on stability thresholds and risk indicators.

Freeze Rules:
- Stability Score < 20
- OR Drift > HIGH in 2 consecutive versions
- OR Simulation regresses in ≥3 categories
- OR AI-Act Conflict Severity ≥ Major
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ENV Configuration
# ─────────────────────────────────────────────────────────────────────────────

AUTO_FREEZE_ENABLED = os.getenv("AUTO_FREEZE_ENABLED", "true").lower() == "true"
FREEZE_STABILITY_THRESHOLD = int(os.getenv("FREEZE_STABILITY_THRESHOLD", "20"))
FREEZE_CONSECUTIVE_HIGH_DRIFT = int(os.getenv("FREEZE_CONSECUTIVE_HIGH_DRIFT", "2"))
FREEZE_SIMULATION_REGRESSION_CATEGORIES = int(os.getenv("FREEZE_SIMULATION_REGRESSION_CATEGORIES", "3"))
FREEZE_AI_ACT_SEVERITY_THRESHOLD = os.getenv("FREEZE_AI_ACT_SEVERITY_THRESHOLD", "major").lower()

# Storage path
FREEZE_STORAGE_PATH = os.getenv(
    "FREEZE_STORAGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "storage", "prompt_freeze")
)


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FreezeReason:
    """Reason for freezing a prompt."""
    rule: str  # LOW_STABILITY, CONSECUTIVE_HIGH_DRIFT, SIMULATION_REGRESSION, AI_ACT_CONFLICT
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    triggered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class FreezeRecord:
    """Record of a frozen prompt."""
    prompt_file: str
    frozen: bool = True
    freeze_reasons: List[FreezeReason] = field(default_factory=list)
    frozen_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    frozen_by: str = "auto"
    unfrozen_at: Optional[str] = None
    unfrozen_by: Optional[str] = None
    freeze_count: int = 1
    history: List[Dict[str, Any]] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# In-Memory State (with file persistence)
# ─────────────────────────────────────────────────────────────────────────────

_freeze_registry: Dict[str, FreezeRecord] = {}


def _get_freeze_file_path(prompt_file: str) -> Path:
    """Get path for freeze record file."""
    safe_name = prompt_file.replace("/", "_").replace("\\", "_").replace(".", "_")
    return Path(FREEZE_STORAGE_PATH) / f"freeze_{safe_name}.json"


def _ensure_storage_dir() -> None:
    """Ensure storage directory exists."""
    Path(FREEZE_STORAGE_PATH).mkdir(parents=True, exist_ok=True)


def _load_freeze_record(prompt_file: str) -> Optional[FreezeRecord]:
    """Load freeze record from disk."""
    if prompt_file in _freeze_registry:
        return _freeze_registry[prompt_file]

    file_path = _get_freeze_file_path(prompt_file)
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                data: Dict[str, Any] = json.load(f)
                # Reconstruct FreezeReason objects
                freeze_reasons = [
                    FreezeReason(**r) if isinstance(r, dict) else r
                    for r in data.get("freeze_reasons", [])
                ]
                record = FreezeRecord(
                    prompt_file=data["prompt_file"],
                    frozen=data.get("frozen", True),
                    freeze_reasons=freeze_reasons,
                    frozen_at=data.get("frozen_at", ""),
                    frozen_by=data.get("frozen_by", "auto"),
                    unfrozen_at=data.get("unfrozen_at"),
                    unfrozen_by=data.get("unfrozen_by"),
                    freeze_count=data.get("freeze_count", 1),
                    history=data.get("history", [])
                )
                _freeze_registry[prompt_file] = record
                return record
        except Exception as e:
            logger.error(f"Error loading freeze record for {prompt_file}: {e}")
    return None


def _save_freeze_record(record: FreezeRecord) -> bool:
    """Save freeze record to disk."""
    try:
        _ensure_storage_dir()
        file_path = _get_freeze_file_path(record.prompt_file)

        # Convert to serializable dict
        data = {
            "prompt_file": record.prompt_file,
            "frozen": record.frozen,
            "freeze_reasons": [asdict(r) for r in record.freeze_reasons],
            "frozen_at": record.frozen_at,
            "frozen_by": record.frozen_by,
            "unfrozen_at": record.unfrozen_at,
            "unfrozen_by": record.unfrozen_by,
            "freeze_count": record.freeze_count,
            "history": record.history
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        _freeze_registry[record.prompt_file] = record
        return True
    except Exception as e:
        logger.error(f"Error saving freeze record: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Freeze Rule Checks
# ─────────────────────────────────────────────────────────────────────────────

def check_stability_threshold(stability_score: int) -> Optional[FreezeReason]:
    """
    Rule 1: Stability Score < FREEZE_STABILITY_THRESHOLD (default 20)
    """
    if stability_score < FREEZE_STABILITY_THRESHOLD:
        return FreezeReason(
            rule="LOW_STABILITY",
            description=f"Stability score ({stability_score}) below threshold ({FREEZE_STABILITY_THRESHOLD})",
            details={
                "score": stability_score,
                "threshold": FREEZE_STABILITY_THRESHOLD
            }
        )
    return None


def check_consecutive_high_drift(drift_history: List[Dict[str, Any]]) -> Optional[FreezeReason]:
    """
    Rule 2: Drift > HIGH in N consecutive versions (default 2)
    """
    if len(drift_history) < FREEZE_CONSECUTIVE_HIGH_DRIFT:
        return None

    # Check last N entries
    recent = drift_history[-FREEZE_CONSECUTIVE_HIGH_DRIFT:]
    high_drift_count = sum(
        1 for entry in recent
        if entry.get("drift_level", "").upper() in ("HIGH", "CRITICAL")
    )

    if high_drift_count >= FREEZE_CONSECUTIVE_HIGH_DRIFT:
        return FreezeReason(
            rule="CONSECUTIVE_HIGH_DRIFT",
            description=f"High drift detected in {high_drift_count} consecutive versions",
            details={
                "consecutive_count": high_drift_count,
                "threshold": FREEZE_CONSECUTIVE_HIGH_DRIFT,
                "recent_drift_levels": [e.get("drift_level") for e in recent]
            }
        )
    return None


def check_simulation_regression(simulation_results: Dict[str, Any]) -> Optional[FreezeReason]:
    """
    Rule 3: Simulation regresses in ≥N categories (default 3)
    """
    regression_categories: List[str] = []

    # Check various regression indicators
    metrics = simulation_results.get("metrics", {})

    # Check quality regression
    if metrics.get("quality_regression", False):
        regression_categories.append("quality")

    # Check fallback regression
    if metrics.get("fallback_rate_increase", 0) > 0.1:  # >10% increase
        regression_categories.append("fallback_rate")

    # Check persona leak regression
    if metrics.get("persona_leak_increase", 0) > 0.05:  # >5% increase
        regression_categories.append("persona_leak")

    # Check AI-Act compliance regression
    if metrics.get("ai_act_regression", False):
        regression_categories.append("ai_act_compliance")

    # Check redundancy regression
    if metrics.get("redundancy_increase", 0) > 0.15:  # >15% increase
        regression_categories.append("redundancy")

    # Check instruction clarity regression
    if metrics.get("instruction_clarity_decrease", 0) > 0.1:  # >10% decrease
        regression_categories.append("instruction_clarity")

    # Check overall score regression
    if metrics.get("overall_score_decrease", 0) > 0.2:  # >20% decrease
        regression_categories.append("overall_score")

    if len(regression_categories) >= FREEZE_SIMULATION_REGRESSION_CATEGORIES:
        return FreezeReason(
            rule="SIMULATION_REGRESSION",
            description=f"Simulation shows regression in {len(regression_categories)} categories",
            details={
                "regression_categories": regression_categories,
                "threshold": FREEZE_SIMULATION_REGRESSION_CATEGORIES,
                "metrics": metrics
            }
        )
    return None


def check_ai_act_conflict_severity(conflict_data: Dict[str, Any]) -> Optional[FreezeReason]:
    """
    Rule 4: AI-Act Conflict Severity ≥ Major
    """
    severity = conflict_data.get("severity", "none").lower()
    severity_levels = ["none", "minor", "moderate", "major", "critical"]

    try:
        current_level = severity_levels.index(severity)
        threshold_level = severity_levels.index(FREEZE_AI_ACT_SEVERITY_THRESHOLD)

        if current_level >= threshold_level:
            return FreezeReason(
                rule="AI_ACT_CONFLICT",
                description=f"AI-Act conflict severity ({severity}) at or above threshold ({FREEZE_AI_ACT_SEVERITY_THRESHOLD})",
                details={
                    "severity": severity,
                    "threshold": FREEZE_AI_ACT_SEVERITY_THRESHOLD,
                    "conflict_details": conflict_data.get("details", {})
                }
            )
    except ValueError:
        logger.warning(f"Unknown severity level: {severity}")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Core API Functions
# ─────────────────────────────────────────────────────────────────────────────

def should_auto_freeze(
    prompt_file: str,
    stability_score: Optional[int] = None,
    drift_history: Optional[List[Dict[str, Any]]] = None,
    simulation_results: Optional[Dict[str, Any]] = None,
    ai_act_conflict: Optional[Dict[str, Any]] = None
) -> List[FreezeReason]:
    """
    Check if a prompt should be automatically frozen based on all rules.

    Args:
        prompt_file: Path to the prompt file
        stability_score: Current stability score (0-100)
        drift_history: List of drift records
        simulation_results: Results from rollout simulation
        ai_act_conflict: AI-Act conflict data

    Returns:
        List of FreezeReason objects (empty if no freeze needed)
    """
    if not AUTO_FREEZE_ENABLED:
        return []

    reasons: List[FreezeReason] = []

    # Rule 1: Low stability
    if stability_score is not None:
        reason = check_stability_threshold(stability_score)
        if reason:
            reasons.append(reason)

    # Rule 2: Consecutive high drift
    if drift_history:
        reason = check_consecutive_high_drift(drift_history)
        if reason:
            reasons.append(reason)

    # Rule 3: Simulation regression
    if simulation_results:
        reason = check_simulation_regression(simulation_results)
        if reason:
            reasons.append(reason)

    # Rule 4: AI-Act conflict
    if ai_act_conflict:
        reason = check_ai_act_conflict_severity(ai_act_conflict)
        if reason:
            reasons.append(reason)

    return reasons


def freeze_prompt(
    prompt_file: str,
    reason: str,
    frozen_by: str = "auto",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Freeze a prompt with a given reason.

    Args:
        prompt_file: Path to the prompt file
        reason: Human-readable reason for freezing
        frozen_by: Who initiated the freeze (auto/manual/system)
        details: Additional details about the freeze

    Returns:
        Dict with freeze status and record
    """
    existing = _load_freeze_record(prompt_file)

    freeze_reason = FreezeReason(
        rule="MANUAL" if frozen_by != "auto" else "AUTO",
        description=reason,
        details=details or {}
    )

    if existing and existing.frozen:
        # Already frozen - add reason to list
        existing.freeze_reasons.append(freeze_reason)
        _save_freeze_record(existing)
        logger.info(f"Prompt {prompt_file} already frozen - added new reason")
        return {
            "success": True,
            "already_frozen": True,
            "prompt_file": prompt_file,
            "freeze_count": existing.freeze_count,
            "reasons": len(existing.freeze_reasons)
        }

    if existing:
        # Re-freezing
        existing.frozen = True
        existing.frozen_at = datetime.utcnow().isoformat()
        existing.frozen_by = frozen_by
        existing.freeze_reasons = [freeze_reason]
        existing.unfrozen_at = None
        existing.unfrozen_by = None
        existing.freeze_count += 1
        existing.history.append({
            "action": "freeze",
            "at": existing.frozen_at,
            "by": frozen_by,
            "reason": reason
        })
        _save_freeze_record(existing)
    else:
        # New freeze record
        record = FreezeRecord(
            prompt_file=prompt_file,
            frozen=True,
            freeze_reasons=[freeze_reason],
            frozen_at=datetime.utcnow().isoformat(),
            frozen_by=frozen_by,
            freeze_count=1,
            history=[{
                "action": "freeze",
                "at": datetime.utcnow().isoformat(),
                "by": frozen_by,
                "reason": reason
            }]
        )
        _save_freeze_record(record)

    logger.warning(f"Prompt {prompt_file} has been FROZEN. Reason: {reason}")

    return {
        "success": True,
        "already_frozen": False,
        "prompt_file": prompt_file,
        "frozen_at": datetime.utcnow().isoformat(),
        "frozen_by": frozen_by,
        "reason": reason
    }


def unfreeze_prompt(
    prompt_file: str,
    unfrozen_by: str = "manual",
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unfreeze a previously frozen prompt.

    Args:
        prompt_file: Path to the prompt file
        unfrozen_by: Who initiated the unfreeze
        reason: Optional reason for unfreezing

    Returns:
        Dict with unfreeze status
    """
    record = _load_freeze_record(prompt_file)

    if not record or not record.frozen:
        return {
            "success": False,
            "error": "Prompt is not frozen",
            "prompt_file": prompt_file
        }

    record.frozen = False
    record.unfrozen_at = datetime.utcnow().isoformat()
    record.unfrozen_by = unfrozen_by
    record.history.append({
        "action": "unfreeze",
        "at": record.unfrozen_at,
        "by": unfrozen_by,
        "reason": reason or "Manual unfreeze"
    })

    _save_freeze_record(record)

    logger.info(f"Prompt {prompt_file} has been UNFROZEN by {unfrozen_by}")

    return {
        "success": True,
        "prompt_file": prompt_file,
        "unfrozen_at": record.unfrozen_at,
        "unfrozen_by": unfrozen_by,
        "freeze_count": record.freeze_count,
        "was_frozen_since": record.frozen_at
    }


def is_prompt_frozen(prompt_file: str) -> bool:
    """
    Check if a prompt is currently frozen.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        True if prompt is frozen, False otherwise
    """
    record = _load_freeze_record(prompt_file)
    return record.frozen if record else False


def get_freeze_record(prompt_file: str) -> Optional[Dict[str, Any]]:
    """
    Get the complete freeze record for a prompt.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        Freeze record as dict, or None if not found
    """
    record = _load_freeze_record(prompt_file)
    if not record:
        return None

    return {
        "prompt_file": record.prompt_file,
        "frozen": record.frozen,
        "freeze_reasons": [asdict(r) for r in record.freeze_reasons],
        "frozen_at": record.frozen_at,
        "frozen_by": record.frozen_by,
        "unfrozen_at": record.unfrozen_at,
        "unfrozen_by": record.unfrozen_by,
        "freeze_count": record.freeze_count,
        "history": record.history
    }


def get_all_frozen_prompts() -> List[Dict[str, Any]]:
    """
    Get all currently frozen prompts.

    Returns:
        List of freeze records for all frozen prompts
    """
    frozen: List[Dict[str, Any]] = []

    # Check in-memory registry
    for prompt_file, record in _freeze_registry.items():
        if record.frozen:
            frozen.append(get_freeze_record(prompt_file) or {})

    # Also check files on disk
    try:
        storage_path = Path(FREEZE_STORAGE_PATH)
        if storage_path.exists():
            for file_path in storage_path.glob("freeze_*.json"):
                try:
                    with open(file_path, "r") as f:
                        data: Dict[str, Any] = json.load(f)
                        prompt_file = data.get("prompt_file", "")
                        if data.get("frozen") and prompt_file not in _freeze_registry:
                            frozen.append(data)
                except Exception as e:
                    logger.error(f"Error reading freeze file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error listing frozen prompts: {e}")

    return frozen


def auto_freeze_check_and_apply(
    prompt_file: str,
    stability_score: Optional[int] = None,
    drift_history: Optional[List[Dict[str, Any]]] = None,
    simulation_results: Optional[Dict[str, Any]] = None,
    ai_act_conflict: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Check if prompt should be frozen and apply freeze if needed.

    This is the main entry point for automatic freeze checks.

    Args:
        prompt_file: Path to the prompt file
        stability_score: Current stability score (0-100)
        drift_history: List of drift records
        simulation_results: Results from rollout simulation
        ai_act_conflict: AI-Act conflict data

    Returns:
        Dict with check results and any freeze action taken
    """
    reasons = should_auto_freeze(
        prompt_file=prompt_file,
        stability_score=stability_score,
        drift_history=drift_history,
        simulation_results=simulation_results,
        ai_act_conflict=ai_act_conflict
    )

    if not reasons:
        return {
            "should_freeze": False,
            "prompt_file": prompt_file,
            "reasons": []
        }

    # Apply freeze
    combined_reason = "; ".join([r.description for r in reasons])
    freeze_result = freeze_prompt(
        prompt_file=prompt_file,
        reason=combined_reason,
        frozen_by="auto",
        details={
            "all_reasons": [asdict(r) for r in reasons],
            "trigger_count": len(reasons)
        }
    )

    return {
        "should_freeze": True,
        "prompt_file": prompt_file,
        "reasons": [asdict(r) for r in reasons],
        "freeze_applied": freeze_result.get("success", False),
        "freeze_result": freeze_result
    }


def get_freeze_statistics() -> Dict[str, Any]:
    """
    Get overall freeze statistics.

    Returns:
        Dict with freeze statistics
    """
    all_frozen = get_all_frozen_prompts()

    # Count by rule
    rule_counts: Dict[str, int] = {}
    for record in all_frozen:
        for reason in record.get("freeze_reasons", []):
            rule = reason.get("rule", "UNKNOWN")
            rule_counts[rule] = rule_counts.get(rule, 0) + 1

    return {
        "total_frozen": len(all_frozen),
        "freeze_by_rule": rule_counts,
        "auto_freeze_enabled": AUTO_FREEZE_ENABLED,
        "thresholds": {
            "stability_threshold": FREEZE_STABILITY_THRESHOLD,
            "consecutive_high_drift": FREEZE_CONSECUTIVE_HIGH_DRIFT,
            "simulation_regression_categories": FREEZE_SIMULATION_REGRESSION_CATEGORIES,
            "ai_act_severity_threshold": FREEZE_AI_ACT_SEVERITY_THRESHOLD
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# Integration Helpers
# ─────────────────────────────────────────────────────────────────────────────

def block_if_frozen(prompt_file: str) -> Optional[Dict[str, Any]]:
    """
    Helper to block operations on frozen prompts.

    Use this in other services to prevent modifications to frozen prompts.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        None if not frozen, or a block response dict if frozen
    """
    if not is_prompt_frozen(prompt_file):
        return None

    record = get_freeze_record(prompt_file)
    return {
        "blocked": True,
        "reason": "Prompt is frozen",
        "prompt_file": prompt_file,
        "frozen_at": record.get("frozen_at") if record else None,
        "freeze_reasons": record.get("freeze_reasons", []) if record else [],
        "action_required": "Unfreeze prompt before making changes"
    }
