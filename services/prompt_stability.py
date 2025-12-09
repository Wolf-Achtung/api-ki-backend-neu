# -*- coding: utf-8 -*-
"""
Sprint G17.7-A: Prompt Stability Score Engine

Calculates stability scores (0-100) for prompt files based on:
- Drift history from G17.6 snapshots
- Rewrite acceptance rate
- Fallback regression rate
- Persona leak scores (weight x3)
- AI-Act conflict hits (weight x4)
- Redundancy trendline
- Tuning profile stability from G17.5

Score < 40 = unstable, Score < 20 = freeze recommended

Version: 1.0.0 (Sprint G17.7)
"""
from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

STABILITY_SCORING_ENABLED = os.environ.get("STABILITY_SCORING_ENABLED", "1") == "1"
PROMPT_STABILITY_ENABLED = STABILITY_SCORING_ENABLED  # Alias for compatibility
PROMPT_STABILITY_MIN_SCORE = int(os.environ.get("PROMPT_STABILITY_MIN_SCORE", "40"))
PROMPT_STABILITY_FREEZE_SCORE = int(os.environ.get("PROMPT_STABILITY_FREEZE_SCORE", "20"))

PROMPT_DRIFT_HISTORY_WINDOW = int(os.environ.get("PROMPT_DRIFT_HISTORY_WINDOW", "10"))
PROMPT_REGRESSION_MAX_ALLOWED = int(os.environ.get("PROMPT_REGRESSION_MAX_ALLOWED", "2"))

# Storage path
STABILITY_SCORES_PATH = os.environ.get("STABILITY_SCORES_PATH", "data/stability_scores")


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class StabilityMetrics:
    """Metrics contributing to stability score."""
    drift_history_score: float = 100.0      # Lower drift history = higher score
    rewrite_acceptance_rate: float = 100.0  # Higher acceptance = higher score
    fallback_regression_rate: float = 100.0 # Lower regression = higher score
    persona_leak_score: float = 100.0       # Lower leaks = higher score (weight x3)
    ai_act_conflict_score: float = 100.0    # Lower conflicts = higher score (weight x4)
    redundancy_trend_score: float = 100.0   # Stable/declining = higher score
    tuning_stability_score: float = 100.0   # Stable tuning = higher score


@dataclass
class PromptStabilityResult:
    """Complete stability analysis result for a prompt file."""
    prompt_file: str
    stability_score: int  # 0-100
    stability_category: str  # STABLE, UNSTABLE, CRITICAL, FROZEN
    metrics: StabilityMetrics = field(default_factory=StabilityMetrics)
    timestamp: datetime = field(default_factory=datetime.now)

    # Aliases for dashboard compatibility
    @property
    def stability_label(self) -> str:
        """Alias for stability_category for dashboard compatibility."""
        label_map = {"CRITICAL": "CRITICAL", "UNSTABLE": "POOR", "STABLE": "GOOD"}
        if self.stability_score >= 80:
            return "EXCELLENT"
        return label_map.get(self.stability_category, self.stability_category)

    @property
    def requires_attention(self) -> bool:
        """Check if prompt requires attention."""
        return self.stability_score < PROMPT_STABILITY_MIN_SCORE

    @property
    def calculated_at(self) -> str:
        """Return timestamp as ISO string."""
        return self.timestamp.isoformat() if self.timestamp else None

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Return stability history for this prompt."""
        return get_stability_history(self.prompt_file)

    # Detailed breakdown
    drift_history: List[int] = field(default_factory=list)  # Recent drift scores
    rewrite_stats: Dict[str, int] = field(default_factory=dict)  # accepted/rejected/pending
    regression_count: int = 0
    persona_leak_incidents: int = 0
    ai_act_conflicts: int = 0
    redundancy_trend: str = "stable"  # increasing, stable, decreasing

    # Recommendations
    should_freeze: bool = False
    should_recover: bool = False
    recommendations: List[str] = field(default_factory=list)


@dataclass
class StabilityHistoryEntry:
    """Historical stability score entry."""
    prompt_file: str
    score: int
    category: str
    timestamp: datetime
    trigger: str = "scheduled"  # scheduled, drift, rewrite, manual


# =============================================================================
# STORAGE
# =============================================================================

_stability_lock = threading.Lock()
_stability_cache: Dict[str, PromptStabilityResult] = {}
_stability_history: Dict[str, List[StabilityHistoryEntry]] = {}


def _get_stability_path() -> Path:
    """Get the stability scores storage path."""
    path = Path(STABILITY_SCORES_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_filename(prompt_file: str) -> str:
    """Convert prompt file path to safe filename."""
    safe = prompt_file.replace("/", "_").replace("\\", "_").replace(".", "_")
    return safe


# =============================================================================
# METRIC CALCULATIONS
# =============================================================================

def _calculate_drift_history_score(prompt_file: str) -> tuple[float, List[int]]:
    """
    Calculate stability score based on drift history.

    Looks at last N drift scores from G17.6 and calculates average.
    Lower average drift = higher stability score.
    """
    drift_scores: List[int] = []

    try:
        from services.prompt_checkpoint import get_all_drift_results

        all_results = get_all_drift_results()
        prompt_results = [r for r in all_results if r.prompt_file == prompt_file]

        # Get most recent N scores
        recent = sorted(prompt_results, key=lambda x: x.timestamp, reverse=True)
        drift_scores = [r.drift_score for r in recent[:PROMPT_DRIFT_HISTORY_WINDOW]]

    except ImportError:
        pass

    if not drift_scores:
        return 100.0, []

    # Average drift score, inverted (low drift = high stability)
    avg_drift = sum(drift_scores) / len(drift_scores)
    stability = max(0, 100 - avg_drift)

    # Penalize high variance
    if len(drift_scores) >= 3:
        variance = sum((d - avg_drift) ** 2 for d in drift_scores) / len(drift_scores)
        if variance > 400:  # High variance penalty
            stability *= 0.8

    return stability, drift_scores


def _calculate_rewrite_acceptance_score(prompt_file: str) -> tuple[float, Dict[str, int]]:
    """
    Calculate stability score based on rewrite acceptance rate.

    High acceptance rate = stable prompt that doesn't need many changes.
    """
    stats = {"accepted": 0, "rejected": 0, "pending": 0}

    try:
        from services.prompt_patch_gate import get_pending_patches, get_blocked_patches

        pending = get_pending_patches()
        blocked = get_blocked_patches()

        stats["pending"] = len([p for p in pending if p.get("prompt_file") == prompt_file])
        stats["rejected"] = len([p for p in blocked if p.get("prompt_file") == prompt_file])

        # Calculate from stored approvals (simplified)
        total = stats["accepted"] + stats["rejected"] + stats["pending"]
        if total > 0:
            # If many pending/rejected, lower stability
            acceptance_rate = stats["accepted"] / max(total, 1)
            return acceptance_rate * 100, stats

    except ImportError:
        pass

    return 100.0, stats


def _calculate_fallback_regression_score(prompt_file: str) -> tuple[float, int]:
    """
    Calculate stability based on fallback regression rate from simulator.

    High regression count = unstable prompt.
    """
    regression_count = 0

    try:
        # Check recent simulations for this prompt
        stability_path = _get_stability_path()
        sim_files = list(stability_path.glob(f"*{_sanitize_filename(prompt_file)}*_sim.json"))

        for sim_file in sim_files[-5:]:  # Last 5 simulations
            with open(sim_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                regression_count += data.get("total_regressions", 0)

    except Exception:
        pass

    # More regressions = lower stability
    if regression_count >= PROMPT_REGRESSION_MAX_ALLOWED * 2:
        return 30.0, regression_count
    elif regression_count >= PROMPT_REGRESSION_MAX_ALLOWED:
        return 60.0, regression_count
    elif regression_count > 0:
        return 80.0, regression_count

    return 100.0, regression_count


def _calculate_persona_leak_score(prompt_file: str) -> tuple[float, int]:
    """
    Calculate stability based on persona leak incidents.

    Weight x3: Persona consistency is critical for report quality.
    """
    leak_count = 0

    try:
        from services.prompt_rewrite_engine import get_rewrite_suggestions

        suggestions = get_rewrite_suggestions(priority=None, limit=100)
        persona_issues = [
            s for s in suggestions
            if s.get("prompt_file") == prompt_file and
            "persona" in s.get("issue_refs", [])
        ]
        leak_count = len(persona_issues)

    except ImportError:
        pass

    # Persona leaks are heavily penalized (weight x3)
    if leak_count >= 5:
        return 20.0, leak_count
    elif leak_count >= 3:
        return 50.0, leak_count
    elif leak_count >= 1:
        return 75.0, leak_count

    return 100.0, leak_count


def _calculate_ai_act_conflict_score(prompt_file: str) -> tuple[float, int]:
    """
    Calculate stability based on AI-Act conflicts.

    Weight x4: AI-Act compliance is critical.
    """
    conflict_count = 0

    try:
        from services.prompt_rewrite_engine import get_rewrite_suggestions

        suggestions = get_rewrite_suggestions(priority=None, limit=100)
        ai_act_issues = [
            s for s in suggestions
            if s.get("prompt_file") == prompt_file and
            "ai_act" in str(s.get("issue_refs", [])).lower()
        ]
        conflict_count = len(ai_act_issues)

    except ImportError:
        pass

    # AI-Act conflicts are very heavily penalized (weight x4)
    if conflict_count >= 3:
        return 10.0, conflict_count
    elif conflict_count >= 2:
        return 40.0, conflict_count
    elif conflict_count >= 1:
        return 70.0, conflict_count

    return 100.0, conflict_count


def _calculate_redundancy_trend_score(prompt_file: str) -> tuple[float, str]:
    """
    Calculate stability based on redundancy trend.

    Increasing redundancy = less stable.
    """
    trend = "stable"

    try:
        from services.prompt_rewrite_engine import get_rewrite_suggestions

        suggestions = get_rewrite_suggestions(priority=None, limit=100)
        redundancy_issues = [
            s for s in suggestions
            if s.get("prompt_file") == prompt_file and
            "redundancy" in str(s.get("issue_refs", [])).lower()
        ]

        count = len(redundancy_issues)
        if count >= 5:
            trend = "increasing"
            return 50.0, trend
        elif count >= 2:
            trend = "stable"
            return 80.0, trend

    except ImportError:
        pass

    return 100.0, trend


def _calculate_tuning_stability_score(prompt_file: str) -> float:
    """
    Calculate stability based on tuning profile stability from G17.5.

    Stable tuning profiles = stable prompt.
    """
    try:
        from services.prompt_tuner import get_all_profiles

        profiles = get_all_profiles()
        prompt_profiles = [p for p in profiles if prompt_file in p.get("prompt_file", "")]

        if not prompt_profiles:
            return 100.0

        # Check if profiles have changed significantly
        changes = 0
        for profile in prompt_profiles:
            diff = profile.get("_diff", {})
            if abs(diff.get("target_word_factor", 0)) > 0.1:
                changes += 1
            if abs(diff.get("redundancy_sensitivity", 0)) > 0.1:
                changes += 1
            if abs(diff.get("persona_strictness", 0)) > 0.1:
                changes += 1

        if changes >= 5:
            return 50.0
        elif changes >= 2:
            return 75.0

    except ImportError:
        pass

    return 100.0


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def calculate_prompt_stability(prompt_file: str) -> PromptStabilityResult:
    """
    Calculate comprehensive stability score for a prompt file.

    Combines multiple metrics with appropriate weights:
    - Drift history: 15%
    - Rewrite acceptance: 10%
    - Fallback regression: 15%
    - Persona leaks: 20% (weight x3)
    - AI-Act conflicts: 25% (weight x4)
    - Redundancy trend: 5%
    - Tuning stability: 10%

    Args:
        prompt_file: Path to the prompt file

    Returns:
        PromptStabilityResult with score and recommendations
    """
    if not PROMPT_STABILITY_ENABLED:
        return PromptStabilityResult(
            prompt_file=prompt_file,
            stability_score=100,
            stability_category="STABLE",
        )

    # Calculate individual metrics
    drift_score, drift_history = _calculate_drift_history_score(prompt_file)
    rewrite_score, rewrite_stats = _calculate_rewrite_acceptance_score(prompt_file)
    fallback_score, regression_count = _calculate_fallback_regression_score(prompt_file)
    persona_score, persona_leaks = _calculate_persona_leak_score(prompt_file)
    ai_act_score, ai_act_conflicts = _calculate_ai_act_conflict_score(prompt_file)
    redundancy_score, redundancy_trend = _calculate_redundancy_trend_score(prompt_file)
    tuning_score = _calculate_tuning_stability_score(prompt_file)

    # Store metrics
    metrics = StabilityMetrics(
        drift_history_score=drift_score,
        rewrite_acceptance_rate=rewrite_score,
        fallback_regression_rate=fallback_score,
        persona_leak_score=persona_score,
        ai_act_conflict_score=ai_act_score,
        redundancy_trend_score=redundancy_score,
        tuning_stability_score=tuning_score,
    )

    # Calculate weighted total
    weighted_score = (
        drift_score * 0.15 +
        rewrite_score * 0.10 +
        fallback_score * 0.15 +
        persona_score * 0.20 +    # Weight x3 effect
        ai_act_score * 0.25 +     # Weight x4 effect
        redundancy_score * 0.05 +
        tuning_score * 0.10
    )

    stability_score = int(weighted_score)

    # Determine category
    if stability_score < PROMPT_STABILITY_FREEZE_SCORE:
        category = "CRITICAL"
    elif stability_score < PROMPT_STABILITY_MIN_SCORE:
        category = "UNSTABLE"
    else:
        category = "STABLE"

    # Build result
    result = PromptStabilityResult(
        prompt_file=prompt_file,
        stability_score=stability_score,
        stability_category=category,
        metrics=metrics,
        drift_history=drift_history,
        rewrite_stats=rewrite_stats,
        regression_count=regression_count,
        persona_leak_incidents=persona_leaks,
        ai_act_conflicts=ai_act_conflicts,
        redundancy_trend=redundancy_trend,
    )

    # Generate recommendations
    if stability_score < PROMPT_STABILITY_FREEZE_SCORE:
        result.should_freeze = True
        result.recommendations.append("CRITICAL: Prompt should be frozen immediately")

    if stability_score < PROMPT_STABILITY_MIN_SCORE:
        result.should_recover = True
        result.recommendations.append("Consider recovering to last stable version")

    if persona_leaks > 2:
        result.recommendations.append("Address persona leak issues before further changes")

    if ai_act_conflicts > 0:
        result.recommendations.append("AI-Act compliance issues require immediate attention")

    if regression_count >= PROMPT_REGRESSION_MAX_ALLOWED:
        result.recommendations.append("High regression count - review recent changes")

    # Cache result
    with _stability_lock:
        _stability_cache[prompt_file] = result

    return result


def update_prompt_stability_index(prompt_file: str, score: int, trigger: str = "manual") -> bool:
    """
    Update the stability score index for a prompt file.

    Args:
        prompt_file: Path to the prompt file
        score: New stability score
        trigger: What triggered the update

    Returns:
        True if successfully updated
    """
    try:
        # Add to history
        entry = StabilityHistoryEntry(
            prompt_file=prompt_file,
            score=score,
            category=_categorize_score(score),
            timestamp=datetime.now(),
            trigger=trigger,
        )

        with _stability_lock:
            if prompt_file not in _stability_history:
                _stability_history[prompt_file] = []
            _stability_history[prompt_file].append(entry)

            # Keep only last 100 entries
            _stability_history[prompt_file] = _stability_history[prompt_file][-100:]

        # Persist to storage
        _store_stability_score(prompt_file, score, trigger)

        return True

    except Exception as e:
        log.error(f"Failed to update stability index: {e}")
        return False


def _categorize_score(score: int) -> str:
    """Categorize a stability score."""
    if score < PROMPT_STABILITY_FREEZE_SCORE:
        return "CRITICAL"
    elif score < PROMPT_STABILITY_MIN_SCORE:
        return "UNSTABLE"
    else:
        return "STABLE"


def _store_stability_score(prompt_file: str, score: int, trigger: str) -> bool:
    """Store stability score to persistent storage."""
    try:
        stability_path = _get_stability_path()
        safe_name = _sanitize_filename(prompt_file)
        file_path = stability_path / f"{safe_name}_stability.json"

        data = {
            "prompt_file": prompt_file,
            "score": score,
            "category": _categorize_score(score),
            "trigger": trigger,
            "timestamp": datetime.now().isoformat(),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        log.error(f"Failed to store stability score: {e}")
        return False


def get_prompt_stability(prompt_file: str) -> Optional[PromptStabilityResult]:
    """
    Get the current stability result for a prompt file.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        PromptStabilityResult or None if not calculated
    """
    # Check cache first
    with _stability_lock:
        if prompt_file in _stability_cache:
            return _stability_cache[prompt_file]

    # Try to load from storage
    try:
        stability_path = _get_stability_path()
        safe_name = _sanitize_filename(prompt_file)
        file_path = stability_path / f"{safe_name}_stability.json"

        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = PromptStabilityResult(
                prompt_file=data.get("prompt_file", prompt_file),
                stability_score=data.get("score", 100),
                stability_category=data.get("category", "STABLE"),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            )

            with _stability_lock:
                _stability_cache[prompt_file] = result

            return result

    except Exception as e:
        log.warning(f"Failed to load stability score: {e}")

    return None


def get_global_prompt_stability_dashboard() -> Dict[str, Any]:
    """
    Get global stability dashboard data.

    Returns:
        Dashboard data with overall statistics
    """
    # Gather all stability results
    all_results: List[Dict[str, Any]] = []

    try:
        stability_path = _get_stability_path()
        for file_path in stability_path.glob("*_stability.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_results.append(data)

    except Exception as e:
        log.error(f"Failed to load stability dashboard: {e}")

    # Calculate statistics
    total = len(all_results)
    stable_count = sum(1 for r in all_results if r.get("category") == "STABLE")
    unstable_count = sum(1 for r in all_results if r.get("category") == "UNSTABLE")
    critical_count = sum(1 for r in all_results if r.get("category") == "CRITICAL")

    avg_score = sum(r.get("score", 100) for r in all_results) / max(total, 1) if total > 0 else 0.0

    # Get prompts requiring attention (score below threshold)
    attention_required = [
        r.get("prompt_file")
        for r in all_results
        if r.get("score", 100) < PROMPT_STABILITY_MIN_SCORE
    ]

    # Calculate label distribution
    by_label: Dict[str, int] = {
        "EXCELLENT": sum(1 for r in all_results if r.get("score", 0) >= 80),
        "GOOD": sum(1 for r in all_results if 60 <= r.get("score", 0) < 80),
        "FAIR": sum(1 for r in all_results if 40 <= r.get("score", 0) < 60),
        "POOR": sum(1 for r in all_results if 20 <= r.get("score", 0) < 40),
        "CRITICAL": sum(1 for r in all_results if r.get("score", 0) < 20),
    }

    return {
        "enabled": PROMPT_STABILITY_ENABLED,
        "total_prompts": total,
        "total_prompts_tracked": total,  # Alias for dashboard
        "stable_count": stable_count,
        "unstable_count": unstable_count,
        "critical_count": critical_count,
        "average_score": round(avg_score, 1),
        "avg_stability_score": round(avg_score, 1),  # Alias for dashboard
        "by_label": by_label,
        "attention_required": attention_required,
        "thresholds": {
            "min_stable": PROMPT_STABILITY_MIN_SCORE,
            "freeze_threshold": PROMPT_STABILITY_FREEZE_SCORE,
        },
        "prompts": [
            {
                "prompt_file": r.get("prompt_file"),
                "score": r.get("score"),
                "category": r.get("category"),
                "timestamp": r.get("timestamp"),
            }
            for r in sorted(all_results, key=lambda x: x.get("score", 100))
        ],
    }


def get_stability_history(prompt_file: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get stability history for a prompt file."""
    with _stability_lock:
        history = _stability_history.get(prompt_file, [])

    return [
        {
            "score": h.score,
            "category": h.category,
            "timestamp": h.timestamp.isoformat(),
            "trigger": h.trigger,
        }
        for h in history[-limit:]
    ]
