# -*- coding: utf-8 -*-
"""
Sprint G17.5: Auto-Learning Prompt Tuner

Automatically adjusts small, bounded prompt parameters based on G16/G17 feedback
and FT signals without requiring manual prompt text changes.

Examples of tuned parameters:
- Target word lengths
- Emphasis weights for subsections
- Redundancy sensitivity
- Persona strictness

Version: 1.0.0 (Sprint G17.5)
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
# CONFIGURATION (ENV VARIABLES)
# =============================================================================

PROMPT_TUNER_ENABLED = os.environ.get("PROMPT_TUNER_ENABLED", "1") == "1"
PROMPT_TUNER_DRY_RUN = os.environ.get("PROMPT_TUNER_DRY_RUN", "0") == "1"

TUNER_MIN_SAMPLES = int(os.environ.get("TUNER_MIN_SAMPLES", "20"))
TUNER_MIN_SEGMENT_STABILITY = os.environ.get("TUNER_MIN_SEGMENT_STABILITY", "medium")

TUNER_MAX_WORD_FACTOR = float(os.environ.get("TUNER_MAX_WORD_FACTOR", "1.30"))
TUNER_MIN_WORD_FACTOR = float(os.environ.get("TUNER_MIN_WORD_FACTOR", "0.90"))

TUNER_MAX_EMPHASIS_DELTA = float(os.environ.get("TUNER_MAX_EMPHASIS_DELTA", "0.25"))
TUNER_MAX_REDUNDANCY_SENSITIVITY = float(os.environ.get("TUNER_MAX_REDUNDANCY_SENSITIVITY", "1.5"))
TUNER_MIN_REDUNDANCY_SENSITIVITY = float(os.environ.get("TUNER_MIN_REDUNDANCY_SENSITIVITY", "0.5"))

TUNER_PERSONA_STRICTNESS_MIN = float(os.environ.get("TUNER_PERSONA_STRICTNESS_MIN", "1.0"))
TUNER_PERSONA_STRICTNESS_MAX = float(os.environ.get("TUNER_PERSONA_STRICTNESS_MAX", "1.5"))

TUNER_UPDATE_INTERVAL_MIN = int(os.environ.get("TUNER_UPDATE_INTERVAL_MIN", "60"))
TUNER_LOG_DEBUG = os.environ.get("TUNER_LOG_DEBUG", "0") == "1"

# Storage path
TUNER_STORAGE_PATH = os.environ.get("TUNER_STORAGE_PATH", "data/prompt_tuner")

# Known emphasis weight keys
KNOWN_EMPHASIS_KEYS = frozenset([
    "governance",
    "data",
    "security",
    "compliance",
    "ai_act",
    "funding",
    "roadmap",
    "quick_wins",
    "cost_benefit",
])

# Stability levels ordering
STABILITY_LEVELS = {"weak": 0, "medium": 1, "strong": 2}


# =============================================================================
# DATA MODEL
# =============================================================================

@dataclass
class TuningProfile:
    """
    Tuning profile for a specific prompt/section/segment combination.

    Contains adjustable parameters that modify prompt behavior without
    changing the actual prompt text.
    """
    prompt_file: str                           # e.g., "prompts/de/roadmap_12m.md"
    section_id: str                            # e.g., "roadmap_12m", "strategie_governance"
    segment_key: str                           # e.g., "solo|beratung|minimal|DE"
    target_word_factor: float = 1.0            # Multiplier for target length (0.9-1.3)
    emphasis_weights: Dict[str, float] = field(default_factory=dict)  # e.g., {"governance": 1.1}
    redundancy_sensitivity: float = 1.0        # 0.5-1.5, how strongly redundancy is penalized
    persona_strictness: float = 1.0            # 1.0-1.5, how strictly persona guards apply
    last_updated: datetime = field(default_factory=datetime.now)
    source: str = "default"                    # "auto", "manual", "ft_signal", "default"
    sample_count: int = 0                      # Number of samples used to build this profile
    segment_stability: str = "medium"          # "weak", "medium", "strong"


@dataclass
class TuningAdjustment:
    """Record of a tuning adjustment made to a profile."""
    profile_key: str
    parameter: str
    old_value: float
    new_value: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# IN-MEMORY STORAGE
# =============================================================================

_profiles_lock = threading.Lock()
_profiles_cache: Dict[str, TuningProfile] = {}
_adjustment_history: List[TuningAdjustment] = []
_last_update_time: Optional[datetime] = None


def _get_profile_key(prompt_file: str, section_id: str, segment_key: str) -> str:
    """Generate a unique key for a tuning profile."""
    return f"{prompt_file}|{section_id}|{segment_key}"


def _get_storage_path() -> Path:
    """Get the storage path for tuning profiles."""
    path = Path(TUNER_STORAGE_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


# =============================================================================
# CORE FUNCTIONS (G17.5-A)
# =============================================================================

def build_tuning_profile(
    prompt_file: str,
    section_id: str,
    segment_key: str,
    segment_stats: Optional[Any] = None,
    ft_signals: Optional[List[Any]] = None,
    predictive_metrics: Optional[Dict[str, Any]] = None,
    validation_warnings: Optional[List[Dict[str, Any]]] = None,
) -> TuningProfile:
    """
    Build a tuning profile based on aggregated feedback data.

    Analyzes:
    - Average word length vs SECTION_MIN_WORDS
    - Frequency of SECTION_TOO_SHORT, REDUNDANCY_DETECTED, SIZE_MISMATCH warnings
    - AI-Act weakness warnings
    - Predictive KPI drift
    - FT signals (more examples, clearer CTA, too generic)

    Args:
        prompt_file: Path to the prompt file
        section_id: Section identifier
        segment_key: Segment key (e.g., "solo|beratung|minimal|DE")
        segment_stats: Segment statistics from G17.1
        ft_signals: FT signals from G17.3
        predictive_metrics: Predictive output from G17.2
        validation_warnings: Accumulated validation warnings

    Returns:
        TuningProfile with calculated adjustments
    """
    profile = TuningProfile(
        prompt_file=prompt_file,
        section_id=section_id,
        segment_key=segment_key,
        source="auto",
    )

    signals = ft_signals or []
    warnings = validation_warnings or []

    # Extract segment stability and sample count from stats
    if segment_stats:
        profile.segment_stability = getattr(segment_stats, "stability", "medium") or "medium"
        profile.sample_count = getattr(segment_stats, "sample_count", 0) or 0

    # 1. Analyze length-related signals and warnings
    too_short_count = _count_warnings_by_pattern(warnings, ["too_short", "min-word", "section_too_short"])
    length_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "size_aware_length"]

    if too_short_count > 3 or len(length_signals) > 2:
        # Increase target word factor
        increase = min(0.05 * (too_short_count // 2), 0.20)
        profile.target_word_factor = 1.0 + increase
        if TUNER_LOG_DEBUG:
            log.debug(f"[Tuner] {segment_key}: Increasing word factor by {increase:.2f} due to {too_short_count} short warnings")

    # 2. Analyze redundancy patterns
    redundancy_count = _count_warnings_by_pattern(warnings, ["redundancy", "redundant", "wiederholung"])
    redundancy_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "redundancy_compression"]

    if redundancy_count > 3 or len(redundancy_signals) > 2:
        # Increase redundancy sensitivity
        increase = min(0.1 * (redundancy_count // 2), 0.4)
        profile.redundancy_sensitivity = 1.0 + increase
        if TUNER_LOG_DEBUG:
            log.debug(f"[Tuner] {segment_key}: Increasing redundancy sensitivity by {increase:.2f}")

    # 3. Analyze persona leaks
    persona_count = _count_warnings_by_pattern(warnings, ["persona", "team_term", "solo_term"])
    persona_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "persona_fix"]

    if persona_count > 2 or len(persona_signals) > 3:
        # Increase persona strictness (only up, never down)
        increase = min(0.1 * (persona_count // 2), 0.4)
        profile.persona_strictness = max(TUNER_PERSONA_STRICTNESS_MIN, 1.0 + increase)
        if TUNER_LOG_DEBUG:
            log.debug(f"[Tuner] {segment_key}: Increasing persona strictness by {increase:.2f}")

    # 4. Analyze emphasis weights from specific signal types
    profile.emphasis_weights = _calculate_emphasis_weights(signals, warnings)

    # 5. Apply constraints
    profile = apply_tuning_constraints(profile)

    return profile


def _count_warnings_by_pattern(warnings: List[Dict[str, Any]], patterns: List[str]) -> int:
    """Count warnings matching any of the given patterns."""
    count = 0
    for warning in warnings:
        msg = str(warning.get("message", "")).lower()
        warning_type = str(warning.get("type", "")).lower()
        for pattern in patterns:
            if pattern.lower() in msg or pattern.lower() in warning_type:
                count += 1
                break
    return count


def _calculate_emphasis_weights(
    signals: List[Any],
    warnings: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Calculate emphasis weights based on signals and warnings."""
    weights: Dict[str, float] = {}

    # AI-Act weakness signals → increase governance/compliance emphasis
    ai_act_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "ai_act_reasoning"]
    ai_act_warnings = _count_warnings_by_pattern(warnings, ["ai_act", "ai-act", "ki-verordnung"])

    if len(ai_act_signals) > 2 or ai_act_warnings > 2:
        weights["governance"] = 1.0 + min(0.1 * max(len(ai_act_signals), ai_act_warnings), TUNER_MAX_EMPHASIS_DELTA)
        weights["compliance"] = weights["governance"]
        weights["ai_act"] = weights["governance"]

    # Funding signals → increase funding emphasis
    funding_signals = [s for s in signals if hasattr(s, 'signal_type') and s.signal_type == "funding_misclassifications"]
    if len(funding_signals) > 2:
        weights["funding"] = 1.0 + min(0.1 * len(funding_signals), TUNER_MAX_EMPHASIS_DELTA)

    # Security/data signals
    security_warnings = _count_warnings_by_pattern(warnings, ["security", "sicherheit", "data_protection"])
    if security_warnings > 2:
        weights["security"] = 1.0 + min(0.1 * security_warnings, TUNER_MAX_EMPHASIS_DELTA)
        weights["data"] = weights.get("data", 1.0) + 0.05

    return weights


def apply_tuning_constraints(profile: TuningProfile) -> TuningProfile:
    """
    Apply constraints to ensure tuning values stay within safe bounds.

    Constraints:
    - 0.9 <= target_word_factor <= 1.3
    - 0.5 <= redundancy_sensitivity <= 1.5
    - Persona strictness only increases, never decreases (min 1.0)
    - Emphasis weight deltas limited to +/- 25%
    - No updates for weak segment stability
    - No updates below minimum sample count
    """
    # Clamp target_word_factor
    profile.target_word_factor = max(
        TUNER_MIN_WORD_FACTOR,
        min(TUNER_MAX_WORD_FACTOR, profile.target_word_factor)
    )

    # Clamp redundancy_sensitivity
    profile.redundancy_sensitivity = max(
        TUNER_MIN_REDUNDANCY_SENSITIVITY,
        min(TUNER_MAX_REDUNDANCY_SENSITIVITY, profile.redundancy_sensitivity)
    )

    # Persona strictness: only increase, never below min
    profile.persona_strictness = max(
        TUNER_PERSONA_STRICTNESS_MIN,
        min(TUNER_PERSONA_STRICTNESS_MAX, profile.persona_strictness)
    )

    # Clamp emphasis weights
    for key in list(profile.emphasis_weights.keys()):
        if key not in KNOWN_EMPHASIS_KEYS:
            del profile.emphasis_weights[key]
            continue
        value = profile.emphasis_weights[key]
        # Clamp to 1.0 +/- MAX_EMPHASIS_DELTA
        profile.emphasis_weights[key] = max(
            1.0 - TUNER_MAX_EMPHASIS_DELTA,
            min(1.0 + TUNER_MAX_EMPHASIS_DELTA, value)
        )

    return profile


def get_tuning_profile(
    prompt_file: str,
    section_id: str,
    segment_key: str,
) -> TuningProfile:
    """
    Get the active tuning profile for a prompt/section/segment combination.

    Falls back to default profile if no specific tuning exists.

    Args:
        prompt_file: Path to the prompt file
        section_id: Section identifier
        segment_key: Segment key

    Returns:
        TuningProfile (either cached/stored or default)
    """
    if not PROMPT_TUNER_ENABLED:
        return _get_default_profile(prompt_file, section_id, segment_key)

    profile_key = _get_profile_key(prompt_file, section_id, segment_key)

    with _profiles_lock:
        # Check in-memory cache first
        if profile_key in _profiles_cache:
            return _profiles_cache[profile_key]

        # Try to load from storage
        profile = _load_profile_from_storage(profile_key)
        if profile:
            _profiles_cache[profile_key] = profile
            return profile

    # Return default profile
    return _get_default_profile(prompt_file, section_id, segment_key)


def _get_default_profile(prompt_file: str, section_id: str, segment_key: str) -> TuningProfile:
    """Get a default tuning profile with neutral values."""
    return TuningProfile(
        prompt_file=prompt_file,
        section_id=section_id,
        segment_key=segment_key,
        target_word_factor=1.0,
        emphasis_weights={},
        redundancy_sensitivity=1.0,
        persona_strictness=1.0,
        source="default",
    )


def _load_profile_from_storage(profile_key: str) -> Optional[TuningProfile]:
    """Load a tuning profile from persistent storage."""
    try:
        storage_path = _get_storage_path()
        # Use hash of key for filename to avoid path issues
        filename = f"profile_{hash(profile_key) & 0xFFFFFFFF:08x}.json"
        file_path = storage_path / filename

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verify the key matches
        if data.get("_key") != profile_key:
            return None

        # Parse datetime
        last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))

        return TuningProfile(
            prompt_file=data.get("prompt_file", ""),
            section_id=data.get("section_id", ""),
            segment_key=data.get("segment_key", ""),
            target_word_factor=data.get("target_word_factor", 1.0),
            emphasis_weights=data.get("emphasis_weights", {}),
            redundancy_sensitivity=data.get("redundancy_sensitivity", 1.0),
            persona_strictness=data.get("persona_strictness", 1.0),
            last_updated=last_updated,
            source=data.get("source", "auto"),
            sample_count=data.get("sample_count", 0),
            segment_stability=data.get("segment_stability", "medium"),
        )
    except Exception as e:
        if TUNER_LOG_DEBUG:
            log.debug(f"Failed to load profile {profile_key}: {e}")
        return None


def _save_profile_to_storage(profile: TuningProfile) -> bool:
    """Save a tuning profile to persistent storage."""
    if PROMPT_TUNER_DRY_RUN:
        if TUNER_LOG_DEBUG:
            log.debug(f"[Tuner DRY-RUN] Would save profile for {profile.segment_key}")
        return False

    try:
        storage_path = _get_storage_path()
        profile_key = _get_profile_key(profile.prompt_file, profile.section_id, profile.segment_key)
        filename = f"profile_{hash(profile_key) & 0xFFFFFFFF:08x}.json"
        file_path = storage_path / filename

        data = asdict(profile)
        data["_key"] = profile_key
        data["last_updated"] = profile.last_updated.isoformat()

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        log.error(f"Failed to save profile: {e}")
        return False


def update_tuning_profiles_from_feedback(
    feedback_snapshot: Dict[str, Any],
    ft_signals: Optional[List[Any]] = None,
    validation_warnings: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """
    Update tuning profiles based on aggregated feedback data.

    Called periodically by G16/G17 feedback loop.

    Only updates profiles for segments that:
    - Have enough data points (>= TUNER_MIN_SAMPLES)
    - Have stable segments (>= TUNER_MIN_SEGMENT_STABILITY)
    - Show recurring patterns

    Args:
        feedback_snapshot: Snapshot from feedback analyzer
        ft_signals: Optional list of FT signals
        validation_warnings: Optional list of validation warnings

    Returns:
        Number of profiles updated
    """
    global _last_update_time

    if not PROMPT_TUNER_ENABLED:
        return 0

    # Check update interval
    if _last_update_time:
        elapsed = (datetime.now() - _last_update_time).total_seconds()
        if elapsed < TUNER_UPDATE_INTERVAL_MIN:
            if TUNER_LOG_DEBUG:
                log.debug(f"[Tuner] Skipping update, only {elapsed:.0f}s since last update")
            return 0

    updated_count = 0
    min_stability_level = STABILITY_LEVELS.get(TUNER_MIN_SEGMENT_STABILITY, 1)

    for segment_key, stats in feedback_snapshot.items():
        # Check sample count
        sample_count = getattr(stats, "sample_count", 0) or 0
        if sample_count < TUNER_MIN_SAMPLES:
            continue

        # Check stability
        stability = getattr(stats, "stability", "medium") or "medium"
        stability_level = STABILITY_LEVELS.get(stability.lower(), 0)
        if stability_level < min_stability_level:
            continue

        # Get prompt file and section from segment or use defaults
        prompt_file = getattr(stats, "prompt_file", "prompts/de/default.md")
        section_id = getattr(stats, "section_id", "default")

        # Get relevant warnings for this segment
        segment_warnings = [
            w for w in (validation_warnings or [])
            if w.get("segment_key", "") == segment_key
        ]

        # Get relevant signals for this segment
        segment_signals = [
            s for s in (ft_signals or [])
            if getattr(s, "segment_key", "") == segment_key
        ]

        # Build new profile
        new_profile = build_tuning_profile(
            prompt_file=prompt_file,
            section_id=section_id,
            segment_key=segment_key,
            segment_stats=stats,
            ft_signals=segment_signals,
            validation_warnings=segment_warnings,
        )

        # Get existing profile for comparison
        profile_key = _get_profile_key(prompt_file, section_id, segment_key)

        with _profiles_lock:
            existing = _profiles_cache.get(profile_key)

            # Check if update is meaningful
            if existing and not _profile_changed_significantly(existing, new_profile):
                continue

            # Record adjustments
            if existing:
                _record_adjustments(profile_key, existing, new_profile)

            # Update cache
            _profiles_cache[profile_key] = new_profile

            # Persist (respects dry-run mode)
            _save_profile_to_storage(new_profile)

            updated_count += 1

            if TUNER_LOG_DEBUG:
                log.debug(f"[Tuner] Updated profile for {segment_key}")

    _last_update_time = datetime.now()

    if updated_count > 0:
        log.info(f"[Tuner] Updated {updated_count} tuning profiles")

    return updated_count


def _profile_changed_significantly(old: TuningProfile, new: TuningProfile) -> bool:
    """Check if a profile has changed significantly enough to warrant an update."""
    threshold = 0.02  # 2% change threshold

    if abs(old.target_word_factor - new.target_word_factor) > threshold:
        return True
    if abs(old.redundancy_sensitivity - new.redundancy_sensitivity) > threshold:
        return True
    if abs(old.persona_strictness - new.persona_strictness) > threshold:
        return True

    # Check emphasis weights
    all_keys = set(old.emphasis_weights.keys()) | set(new.emphasis_weights.keys())
    for key in all_keys:
        old_val = old.emphasis_weights.get(key, 1.0)
        new_val = new.emphasis_weights.get(key, 1.0)
        if abs(old_val - new_val) > threshold:
            return True

    return False


def _record_adjustments(profile_key: str, old: TuningProfile, new: TuningProfile) -> None:
    """Record adjustment history for audit trail."""
    adjustments = []

    if old.target_word_factor != new.target_word_factor:
        adjustments.append(TuningAdjustment(
            profile_key=profile_key,
            parameter="target_word_factor",
            old_value=old.target_word_factor,
            new_value=new.target_word_factor,
            reason="Auto-adjusted based on length feedback",
        ))

    if old.redundancy_sensitivity != new.redundancy_sensitivity:
        adjustments.append(TuningAdjustment(
            profile_key=profile_key,
            parameter="redundancy_sensitivity",
            old_value=old.redundancy_sensitivity,
            new_value=new.redundancy_sensitivity,
            reason="Auto-adjusted based on redundancy feedback",
        ))

    if old.persona_strictness != new.persona_strictness:
        adjustments.append(TuningAdjustment(
            profile_key=profile_key,
            parameter="persona_strictness",
            old_value=old.persona_strictness,
            new_value=new.persona_strictness,
            reason="Auto-adjusted based on persona feedback",
        ))

    _adjustment_history.extend(adjustments)


# =============================================================================
# ROLLBACK FUNCTIONALITY (G17.5-C)
# =============================================================================

def reset_tuning_profiles(segment_filter: Optional[str] = None) -> int:
    """
    Reset tuning profiles to defaults.

    Args:
        segment_filter: Optional segment key to reset only matching profiles.
                       If None, resets all profiles.

    Returns:
        Number of profiles reset
    """
    global _profiles_cache

    reset_count = 0

    with _profiles_lock:
        if segment_filter:
            # Reset only matching profiles
            keys_to_reset = [
                k for k in _profiles_cache.keys()
                if segment_filter in k
            ]
        else:
            keys_to_reset = list(_profiles_cache.keys())

        for key in keys_to_reset:
            old_profile = _profiles_cache.pop(key, None)
            if old_profile and not PROMPT_TUNER_DRY_RUN:
                # Delete from storage
                try:
                    storage_path = _get_storage_path()
                    filename = f"profile_{hash(key) & 0xFFFFFFFF:08x}.json"
                    file_path = storage_path / filename
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    log.warning(f"Failed to delete profile file: {e}")
            reset_count += 1

    if reset_count > 0:
        log.info(f"[Tuner] Reset {reset_count} tuning profiles")

    return reset_count


def get_all_profiles(segment_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all tuning profiles, optionally filtered by segment.

    Args:
        segment_filter: Optional segment key to filter profiles

    Returns:
        List of profile dictionaries
    """
    result: List[Dict[str, Any]] = []

    with _profiles_lock:
        for key, profile in _profiles_cache.items():
            if segment_filter and segment_filter not in key:
                continue

            profile_dict = asdict(profile)
            profile_dict["last_updated"] = profile.last_updated.isoformat()
            profile_dict["_key"] = key

            # Calculate diff from defaults
            profile_dict["_diff"] = {
                "target_word_factor": round(profile.target_word_factor - 1.0, 3),
                "redundancy_sensitivity": round(profile.redundancy_sensitivity - 1.0, 3),
                "persona_strictness": round(profile.persona_strictness - 1.0, 3),
                "emphasis_weights": {
                    k: round(v - 1.0, 3)
                    for k, v in profile.emphasis_weights.items()
                },
            }

            result.append(profile_dict)

    return result


def get_tuner_status() -> Dict[str, Any]:
    """
    Get overall tuner status for dashboard.

    Returns:
        Status dictionary with profile counts and stability breakdown
    """
    profiles = get_all_profiles()

    by_stability: Dict[str, int] = {"strong": 0, "medium": 0, "weak": 0}
    for profile in profiles:
        stability = profile.get("segment_stability", "medium")
        by_stability[stability] = by_stability.get(stability, 0) + 1

    return {
        "enabled": PROMPT_TUNER_ENABLED,
        "dry_run": PROMPT_TUNER_DRY_RUN,
        "profiles_total": len(profiles),
        "by_segment_stability": by_stability,
        "last_update": _last_update_time.isoformat() if _last_update_time else None,
        "config": {
            "min_samples": TUNER_MIN_SAMPLES,
            "min_segment_stability": TUNER_MIN_SEGMENT_STABILITY,
            "max_word_factor": TUNER_MAX_WORD_FACTOR,
            "min_word_factor": TUNER_MIN_WORD_FACTOR,
            "update_interval_min": TUNER_UPDATE_INTERVAL_MIN,
        },
    }


def get_adjustment_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent adjustment history for audit purposes."""
    history = _adjustment_history[-limit:] if limit else _adjustment_history
    return [
        {
            "profile_key": adj.profile_key,
            "parameter": adj.parameter,
            "old_value": adj.old_value,
            "new_value": adj.new_value,
            "reason": adj.reason,
            "timestamp": adj.timestamp.isoformat(),
        }
        for adj in reversed(history)
    ]
