"""
G17.8-B: Funding Confidence Rebalancer

Dynamic confidence adjustment layer that rebalances funding programme priorities
based on distribution analysis and ROI tracking.

Part of the Funding Auto-Optimizer & Intelligent Rebalancing system.
"""

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration from Environment
# ============================================================================

CONFIDENCE_REBALANCING_ENABLED = os.getenv("CONFIDENCE_REBALANCING_ENABLED", "true").lower() == "true"
CONFIDENCE_REBALANCING_STORAGE_PATH = os.getenv(
    "CONFIDENCE_REBALANCING_STORAGE_PATH",
    "data/funding_rebalancing"
)
CONFIDENCE_MAX_ADJUSTMENT = float(os.getenv("CONFIDENCE_MAX_ADJUSTMENT", "0.3"))  # Max 30% adjustment
CONFIDENCE_MIN_ADJUSTMENT = float(os.getenv("CONFIDENCE_MIN_ADJUSTMENT", "-0.3"))  # Min -30% adjustment
CONFIDENCE_DECAY_RATE = float(os.getenv("CONFIDENCE_DECAY_RATE", "0.1"))  # 10% decay per cycle
CONFIDENCE_BOOST_RATE = float(os.getenv("CONFIDENCE_BOOST_RATE", "0.15"))  # 15% boost for positive ROI
CONFIDENCE_SMOOTHING_FACTOR = float(os.getenv("CONFIDENCE_SMOOTHING_FACTOR", "0.7"))  # EMA smoothing


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ConfidenceAdjustment:
    """Represents a confidence adjustment for a programme."""
    programme_id: str
    original_confidence: float
    adjusted_confidence: float
    adjustment_factor: float  # Multiplier applied (e.g., 0.85 = -15%)
    adjustment_reason: str
    adjustment_type: str  # "boost", "penalty", "decay", "reset"
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProgrammeConfidenceState:
    """Current confidence state for a programme."""
    programme_id: str
    base_confidence: float  # Original/base confidence score
    current_adjustment: float  # Current adjustment factor (1.0 = no change)
    effective_confidence: float  # base * adjustment
    adjustment_history: List[ConfidenceAdjustment] = field(default_factory=list)
    roi_score: float = 0.0  # Rolling ROI impact score
    distribution_penalty: float = 0.0  # Penalty from distribution imbalance
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "programme_id": self.programme_id,
            "base_confidence": self.base_confidence,
            "current_adjustment": self.current_adjustment,
            "effective_confidence": self.effective_confidence,
            "adjustment_history": [a.to_dict() for a in self.adjustment_history[-10:]],
            "roi_score": self.roi_score,
            "distribution_penalty": self.distribution_penalty,
            "last_updated": self.last_updated
        }


@dataclass
class RebalancingResult:
    """Result of a rebalancing operation."""
    rebalance_id: str
    timestamp: str
    programmes_adjusted: int
    total_programmes: int
    adjustments: List[ConfidenceAdjustment]
    distribution_delta_before: float
    distribution_delta_after: float  # Estimated
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rebalance_id": self.rebalance_id,
            "timestamp": self.timestamp,
            "programmes_adjusted": self.programmes_adjusted,
            "total_programmes": self.total_programmes,
            "adjustments": [a.to_dict() for a in self.adjustments],
            "distribution_delta_before": self.distribution_delta_before,
            "distribution_delta_after": self.distribution_delta_after,
            "recommendations": self.recommendations
        }


# ============================================================================
# In-Memory Storage
# ============================================================================

_confidence_states: Dict[str, ProgrammeConfidenceState] = {}
_rebalancing_history: List[RebalancingResult] = []


# ============================================================================
# Core Functions
# ============================================================================

def get_confidence_state(programme_id: str) -> Optional[ProgrammeConfidenceState]:
    """Get current confidence state for a programme."""
    return _confidence_states.get(programme_id)


def get_all_confidence_states() -> Dict[str, ProgrammeConfidenceState]:
    """Get all confidence states."""
    return _confidence_states.copy()


def initialize_confidence(
    programme_id: str,
    base_confidence: float = 1.0
) -> ProgrammeConfidenceState:
    """Initialize confidence state for a programme."""
    state = ProgrammeConfidenceState(
        programme_id=programme_id,
        base_confidence=base_confidence,
        current_adjustment=1.0,
        effective_confidence=base_confidence,
        adjustment_history=[],
        roi_score=0.0,
        distribution_penalty=0.0,
        last_updated=datetime.now(timezone.utc).isoformat()
    )
    _confidence_states[programme_id] = state
    logger.debug(f"Initialized confidence for {programme_id}: {base_confidence}")
    return state


def apply_adjustment(
    programme_id: str,
    adjustment_factor: float,
    reason: str,
    adjustment_type: str = "manual"
) -> ConfidenceAdjustment:
    """
    Apply a confidence adjustment to a programme.

    Args:
        programme_id: The programme to adjust
        adjustment_factor: Multiplier to apply (e.g., 0.9 = -10%, 1.1 = +10%)
        reason: Reason for the adjustment
        adjustment_type: Type of adjustment (boost, penalty, decay, reset)
    """
    if programme_id not in _confidence_states:
        initialize_confidence(programme_id)

    state = _confidence_states[programme_id]

    # Clamp adjustment factor to allowed range
    min_factor = 1.0 + CONFIDENCE_MIN_ADJUSTMENT
    max_factor = 1.0 + CONFIDENCE_MAX_ADJUSTMENT
    clamped_factor = max(min_factor, min(max_factor, adjustment_factor))

    # Apply with smoothing (exponential moving average)
    new_adjustment = (
        CONFIDENCE_SMOOTHING_FACTOR * clamped_factor +
        (1 - CONFIDENCE_SMOOTHING_FACTOR) * state.current_adjustment
    )

    original = state.effective_confidence
    state.current_adjustment = round(new_adjustment, 4)
    state.effective_confidence = round(state.base_confidence * state.current_adjustment, 4)
    state.last_updated = datetime.now(timezone.utc).isoformat()

    adjustment = ConfidenceAdjustment(
        programme_id=programme_id,
        original_confidence=original,
        adjusted_confidence=state.effective_confidence,
        adjustment_factor=clamped_factor,
        adjustment_reason=reason,
        adjustment_type=adjustment_type,
        timestamp=state.last_updated
    )
    state.adjustment_history.append(adjustment)

    # Keep history limited
    if len(state.adjustment_history) > 100:
        state.adjustment_history = state.adjustment_history[-100:]

    logger.info(
        f"Applied {adjustment_type} to {programme_id}: "
        f"{original:.3f} -> {state.effective_confidence:.3f} ({reason})"
    )

    return adjustment


def apply_distribution_penalty(
    programme_id: str,
    delta_pct: float,
    is_overrepresented: bool
) -> Optional[ConfidenceAdjustment]:
    """
    Apply penalty based on distribution imbalance.

    Overrepresented programmes get penalties, underrepresented get boosts.
    """
    if not CONFIDENCE_REBALANCING_ENABLED:
        return None

    if programme_id not in _confidence_states:
        initialize_confidence(programme_id)

    state = _confidence_states[programme_id]

    if is_overrepresented:
        # Reduce confidence for overrepresented programmes
        # Scale: 10% over -> 0.95x, 20% over -> 0.90x, etc.
        penalty = max(0.7, 1.0 - (abs(delta_pct) / 200))
        state.distribution_penalty = round(1.0 - penalty, 4)
        return apply_adjustment(
            programme_id,
            penalty,
            f"Overrepresented by {delta_pct:+.1f}%",
            "penalty"
        )
    else:
        # Boost confidence for underrepresented programmes
        # Scale: 10% under -> 1.05x, 20% under -> 1.10x, etc.
        boost = min(1.3, 1.0 + (abs(delta_pct) / 200))
        state.distribution_penalty = 0.0
        return apply_adjustment(
            programme_id,
            boost,
            f"Underrepresented by {delta_pct:.1f}%",
            "boost"
        )


def apply_roi_adjustment(
    programme_id: str,
    roi_score: float,
    rolling_window: int = 10
) -> Optional[ConfidenceAdjustment]:
    """
    Apply adjustment based on ROI performance.

    Positive ROI leads to confidence boost, negative to penalty.
    """
    if not CONFIDENCE_REBALANCING_ENABLED:
        return None

    if programme_id not in _confidence_states:
        initialize_confidence(programme_id)

    state = _confidence_states[programme_id]

    # Update rolling ROI score
    old_roi = state.roi_score
    state.roi_score = round(
        (old_roi * (rolling_window - 1) + roi_score) / rolling_window,
        4
    )

    if roi_score > 0.5:
        # Strong positive ROI - boost
        boost = 1.0 + (CONFIDENCE_BOOST_RATE * min(1.0, roi_score))
        return apply_adjustment(
            programme_id,
            boost,
            f"Positive ROI ({roi_score:.2f})",
            "boost"
        )
    elif roi_score < -0.3:
        # Negative ROI - penalty
        penalty = 1.0 - (CONFIDENCE_DECAY_RATE * min(1.0, abs(roi_score)))
        return apply_adjustment(
            programme_id,
            penalty,
            f"Negative ROI ({roi_score:.2f})",
            "penalty"
        )

    return None


def apply_decay() -> List[ConfidenceAdjustment]:
    """
    Apply natural decay to all adjustments, moving them toward neutral (1.0).

    This prevents permanent biases and allows the system to self-correct.
    """
    if not CONFIDENCE_REBALANCING_ENABLED:
        return []

    adjustments: List[ConfidenceAdjustment] = []

    for programme_id, state in _confidence_states.items():
        if abs(state.current_adjustment - 1.0) > 0.01:
            # Decay toward 1.0
            decay_amount = (state.current_adjustment - 1.0) * CONFIDENCE_DECAY_RATE
            new_adjustment = state.current_adjustment - decay_amount

            if abs(new_adjustment - 1.0) > 0.01:
                adj = apply_adjustment(
                    programme_id,
                    new_adjustment / state.current_adjustment,  # Relative adjustment
                    "Natural decay toward neutral",
                    "decay"
                )
                adjustments.append(adj)

    return adjustments


def reset_confidence(programme_id: str) -> Optional[ConfidenceAdjustment]:
    """Reset a programme's confidence to base level."""
    if programme_id not in _confidence_states:
        return None

    state = _confidence_states[programme_id]

    if abs(state.current_adjustment - 1.0) < 0.01:
        return None  # Already at base

    return apply_adjustment(
        programme_id,
        1.0 / state.current_adjustment,  # Reset to 1.0
        "Manual reset to base confidence",
        "reset"
    )


def reset_all_confidence() -> int:
    """Reset all programmes to base confidence. Returns count reset."""
    count = 0
    for programme_id in list(_confidence_states.keys()):
        if reset_confidence(programme_id):
            count += 1
    return count


def rebalance_from_distribution(
    distribution_analysis: Dict[str, Any]
) -> RebalancingResult:
    """
    Perform rebalancing based on distribution analysis results.

    Takes the output from funding_distribution.analyze_distribution().
    """
    rebalance_id = f"rebal_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now(timezone.utc).isoformat()

    adjustments: List[ConfidenceAdjustment] = []
    recommendations: List[str] = []

    delta_before = distribution_analysis.get("delta_score", 0.0)

    # Process overrepresented programmes
    for prog in distribution_analysis.get("overrepresented", []):
        prog_id = prog.get("programme_id", prog.get("program"))
        delta_pct = prog.get("delta_pct", prog.get("delta"))
        if prog_id and delta_pct:
            adj = apply_distribution_penalty(prog_id, delta_pct, is_overrepresented=True)
            if adj:
                adjustments.append(adj)

    # Process underrepresented programmes
    for prog in distribution_analysis.get("underrepresented", []):
        prog_id = prog.get("programme_id", prog.get("program"))
        delta_pct = prog.get("delta_pct", prog.get("delta"))
        if prog_id and delta_pct:
            adj = apply_distribution_penalty(prog_id, abs(delta_pct), is_overrepresented=False)
            if adj:
                adjustments.append(adj)

    # Generate recommendations
    if len(adjustments) > 5:
        recommendations.append("Multiple programmes adjusted - consider reviewing recommendation algorithm")
    if delta_before > 0.4:
        recommendations.append("High distribution imbalance detected - monitor closely")

    # Estimate new delta (rough approximation)
    delta_after = delta_before * 0.7 if adjustments else delta_before

    result = RebalancingResult(
        rebalance_id=rebalance_id,
        timestamp=timestamp,
        programmes_adjusted=len(adjustments),
        total_programmes=len(_confidence_states),
        adjustments=adjustments,
        distribution_delta_before=delta_before,
        distribution_delta_after=delta_after,
        recommendations=recommendations
    )

    _rebalancing_history.append(result)
    _persist_rebalancing_result(result)

    logger.info(
        f"Rebalancing complete: {len(adjustments)} adjustments, "
        f"delta {delta_before:.3f} -> {delta_after:.3f}"
    )

    return result


def get_effective_confidence(
    programme_id: str,
    base_confidence: float = 1.0
) -> float:
    """
    Get effective confidence for a programme, applying all adjustments.

    This is the main entry point for the recommendation system to get
    adjusted confidence scores.
    """
    if not CONFIDENCE_REBALANCING_ENABLED:
        return base_confidence

    state = _confidence_states.get(programme_id)
    if not state:
        return base_confidence

    # Apply base confidence if provided
    if base_confidence != 1.0 and state.base_confidence == 1.0:
        state.base_confidence = base_confidence
        state.effective_confidence = round(base_confidence * state.current_adjustment, 4)

    return state.effective_confidence


def adjust_recommendation_scores(
    recommendations: List[Dict[str, Any]],
    score_key: str = "confidence"
) -> List[Dict[str, Any]]:
    """
    Adjust confidence scores for a list of recommendations.

    Modifies recommendations in-place and returns them.
    """
    if not CONFIDENCE_REBALANCING_ENABLED:
        return recommendations

    for rec in recommendations:
        programme_id = rec.get("programme_id") or rec.get("id")
        if programme_id:
            original_score = rec.get(score_key, 1.0)
            adjusted_score = get_effective_confidence(programme_id, original_score)
            rec[score_key] = adjusted_score
            rec["_original_" + score_key] = original_score
            rec["_adjustment_applied"] = True

    # Re-sort by adjusted score
    recommendations.sort(key=lambda x: x.get(score_key, 0), reverse=True)

    return recommendations


def get_rebalancing_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get history of rebalancing operations."""
    history = sorted(
        _rebalancing_history,
        key=lambda x: x.timestamp,
        reverse=True
    )[:limit]
    return [r.to_dict() for r in history]


def get_adjustment_summary() -> Dict[str, Any]:
    """Get summary of all current adjustments."""
    if not _confidence_states:
        return {
            "enabled": CONFIDENCE_REBALANCING_ENABLED,
            "total_programmes": 0,
            "boosted_count": 0,
            "penalized_count": 0,
            "neutral_count": 0,
            "average_adjustment": 1.0,
            "max_boost": 0.0,
            "max_penalty": 0.0
        }

    boosted = []
    penalized = []
    neutral = []

    for state in _confidence_states.values():
        if state.current_adjustment > 1.02:
            boosted.append(state)
        elif state.current_adjustment < 0.98:
            penalized.append(state)
        else:
            neutral.append(state)

    adjustments = [s.current_adjustment for s in _confidence_states.values()]

    return {
        "enabled": CONFIDENCE_REBALANCING_ENABLED,
        "total_programmes": len(_confidence_states),
        "boosted_count": len(boosted),
        "penalized_count": len(penalized),
        "neutral_count": len(neutral),
        "average_adjustment": round(sum(adjustments) / len(adjustments), 4),
        "max_boost": max(adjustments) if adjustments else 1.0,
        "max_penalty": min(adjustments) if adjustments else 1.0,
        "boosted_programmes": [s.programme_id for s in boosted[:5]],
        "penalized_programmes": [s.programme_id for s in penalized[:5]]
    }


# ============================================================================
# Persistence
# ============================================================================

def _persist_rebalancing_result(result: RebalancingResult) -> None:
    """Persist rebalancing result to filesystem."""
    try:
        storage_path = Path(CONFIDENCE_REBALANCING_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)

        filepath = storage_path / f"{result.rebalance_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        logger.debug(f"Persisted rebalancing result: {filepath}")
    except Exception as e:
        logger.error(f"Failed to persist rebalancing result: {e}")


def persist_confidence_states() -> None:
    """Persist all confidence states to filesystem."""
    try:
        storage_path = Path(CONFIDENCE_REBALANCING_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)

        filepath = storage_path / "confidence_states.json"
        states_dict = {k: v.to_dict() for k, v in _confidence_states.items()}

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(states_dict, f, indent=2, ensure_ascii=False)

        logger.debug(f"Persisted {len(states_dict)} confidence states")
    except Exception as e:
        logger.error(f"Failed to persist confidence states: {e}")


def load_confidence_states() -> int:
    """Load confidence states from storage. Returns count loaded."""
    global _confidence_states

    storage_path = Path(CONFIDENCE_REBALANCING_STORAGE_PATH)
    filepath = storage_path / "confidence_states.json"

    if not filepath.exists():
        return 0

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            states_dict = json.load(f)

        for prog_id, state_data in states_dict.items():
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

        logger.info(f"Loaded {len(_confidence_states)} confidence states")
        return len(_confidence_states)
    except Exception as e:
        logger.warning(f"Failed to load confidence states: {e}")
        return 0


# ============================================================================
# Module Initialization
# ============================================================================

def _initialize_module() -> None:
    """Initialize module on import."""
    if CONFIDENCE_REBALANCING_ENABLED:
        try:
            load_confidence_states()
        except Exception as e:
            logger.warning(f"Could not load confidence states: {e}")


_initialize_module()
