"""
G17.8-A: Funding Distribution Analyzer

Analyzes funding programme distribution to detect over/under-representation
and calculate expected vs actual distributions based on segment data.

Part of the Funding Auto-Optimizer & Intelligent Rebalancing system.
"""

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration from Environment
# ============================================================================

FUNDING_DISTRIBUTION_ENABLED = os.getenv("FUNDING_DISTRIBUTION_ENABLED", "true").lower() == "true"
FUNDING_DISTRIBUTION_STORAGE_PATH = os.getenv(
    "FUNDING_DISTRIBUTION_STORAGE_PATH",
    "data/funding_distribution"
)
FUNDING_OVERREP_THRESHOLD = float(os.getenv("FUNDING_OVERREP_THRESHOLD", "1.5"))  # 50% over expected
FUNDING_UNDERREP_THRESHOLD = float(os.getenv("FUNDING_UNDERREP_THRESHOLD", "0.5"))  # 50% under expected
FUNDING_DISTRIBUTION_MIN_SAMPLES = int(os.getenv("FUNDING_DISTRIBUTION_MIN_SAMPLES", "10"))
FUNDING_REBALANCING_THRESHOLD = float(os.getenv("FUNDING_REBALANCING_THRESHOLD", "0.15"))  # 15% delta


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SegmentDefinition:
    """Definition of a business segment for expected distribution calculation."""
    segment_id: str
    name: str
    expected_share: float  # Expected percentage of all recommendations (0.0-1.0)
    applicable_programmes: List[str] = field(default_factory=list)
    weight: float = 1.0


@dataclass
class ProgrammeDistribution:
    """Distribution data for a single funding programme."""
    programme_id: str
    programme_name: str
    expected_pct: float  # Expected percentage based on segment analysis
    actual_pct: float  # Actual percentage from real recommendations
    delta_pct: float  # Difference (actual - expected)
    recommendation_count: int
    total_recommendations: int
    rebalancing_required: bool
    representation_status: str  # "overrepresented", "underrepresented", "balanced"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DistributionSnapshot:
    """Snapshot of funding distribution at a point in time."""
    snapshot_id: str
    timestamp: str
    total_recommendations: int
    programme_distributions: List[ProgrammeDistribution]
    delta_score: float  # Overall distribution delta score (0-1, 0=perfect)
    segments_analyzed: List[str]
    rebalancing_programmes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "total_recommendations": self.total_recommendations,
            "programme_distributions": [pd.to_dict() for pd in self.programme_distributions],
            "delta_score": self.delta_score,
            "segments_analyzed": self.segments_analyzed,
            "rebalancing_programmes": self.rebalancing_programmes
        }


@dataclass
class DistributionAnalysisResult:
    """Complete result of distribution analysis."""
    analysis_id: str
    timestamp: str
    enabled: bool
    total_recommendations: int
    overrepresented: List[ProgrammeDistribution]
    underrepresented: List[ProgrammeDistribution]
    balanced: List[ProgrammeDistribution]
    delta_score: float
    rebalancing_required: bool
    recommendations_for_rebalancing: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp,
            "enabled": self.enabled,
            "total_recommendations": self.total_recommendations,
            "overrepresented": [p.to_dict() for p in self.overrepresented],
            "underrepresented": [p.to_dict() for p in self.underrepresented],
            "balanced": [p.to_dict() for p in self.balanced],
            "delta_score": self.delta_score,
            "rebalancing_required": self.rebalancing_required,
            "recommendations_for_rebalancing": self.recommendations_for_rebalancing
        }


# ============================================================================
# In-Memory Storage
# ============================================================================

_recommendation_history: List[Dict[str, Any]] = []
_distribution_snapshots: List[DistributionSnapshot] = []

# Default segment definitions based on German funding landscape
_default_segments: List[SegmentDefinition] = [
    SegmentDefinition(
        segment_id="solo",
        name="Solo/Freelancer",
        expected_share=0.25,
        applicable_programmes=["go_digital", "coaching_bonus_berlin", "exist", "digitalbonus_bayern"],
        weight=1.0
    ),
    SegmentDefinition(
        segment_id="team",
        name="Small Team (2-10)",
        expected_share=0.35,
        applicable_programmes=[
            "go_digital", "digitalbonus_bayern", "invest_bw",
            "profit_berlin", "innovationsgutschein_bayern", "zim", "exist"
        ],
        weight=1.2
    ),
    SegmentDefinition(
        segment_id="kmu",
        name="SME (11-250)",
        expected_share=0.30,
        applicable_programmes=[
            "kfw_digital_innovation", "invest_bw", "profit_berlin",
            "transfer_bonus_berlin", "zim", "digital_verwaltung_itsec"
        ],
        weight=1.3
    ),
    SegmentDefinition(
        segment_id="enterprise",
        name="Enterprise (250+)",
        expected_share=0.10,
        applicable_programmes=["kfw_digital_innovation", "digital_verwaltung_itsec"],
        weight=0.8
    )
]


# ============================================================================
# Core Functions
# ============================================================================

def record_recommendation(
    programme_id: str,
    segment_id: str,
    country: str = "DE",
    region: Optional[str] = None,
    confidence: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Record a funding recommendation for distribution tracking."""
    if not FUNDING_DISTRIBUTION_ENABLED:
        return

    record = {
        "programme_id": programme_id,
        "segment_id": segment_id,
        "country": country,
        "region": region,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }
    _recommendation_history.append(record)
    logger.debug(f"Recorded recommendation: {programme_id} for segment {segment_id}")


def calculate_expected_distribution(
    segments: Optional[List[SegmentDefinition]] = None,
    country: str = "DE"
) -> Dict[str, float]:
    """
    Calculate expected programme distribution based on segment sizes.

    Returns a dict mapping programme_id -> expected_percentage (0-100).
    """
    if segments is None:
        segments = _default_segments

    programme_scores: Dict[str, float] = defaultdict(float)
    total_weight = 0.0

    for segment in segments:
        segment_weight = segment.expected_share * segment.weight
        total_weight += segment_weight

        # Distribute segment weight across applicable programmes
        if segment.applicable_programmes:
            per_programme = segment_weight / len(segment.applicable_programmes)
            for prog_id in segment.applicable_programmes:
                programme_scores[prog_id] += per_programme

    # Normalize to percentages
    expected_distribution: Dict[str, float] = {}
    if total_weight > 0:
        for prog_id, score in programme_scores.items():
            expected_distribution[prog_id] = round((score / total_weight) * 100, 2)

    return expected_distribution


def calculate_actual_distribution(
    country: Optional[str] = None,
    region: Optional[str] = None,
    time_window_days: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate actual programme distribution from recorded recommendations.

    Returns a dict mapping programme_id -> actual_percentage (0-100).
    """
    if not _recommendation_history:
        return {}

    # Filter recommendations
    filtered = _recommendation_history.copy()

    if country:
        filtered = [r for r in filtered if r.get("country") == country]

    if region:
        filtered = [r for r in filtered if r.get("region") == region]

    if time_window_days:
        cutoff = datetime.now(timezone.utc).timestamp() - (time_window_days * 86400)
        filtered = [
            r for r in filtered
            if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")).timestamp() >= cutoff
        ]

    if not filtered:
        return {}

    # Count programmes
    programme_counts: Dict[str, int] = defaultdict(int)
    for rec in filtered:
        programme_counts[rec["programme_id"]] += 1

    # Convert to percentages
    total = len(filtered)
    actual_distribution: Dict[str, float] = {}
    for prog_id, count in programme_counts.items():
        actual_distribution[prog_id] = round((count / total) * 100, 2)

    return actual_distribution


def distribution_delta_score(
    expected: Dict[str, float],
    actual: Dict[str, float]
) -> float:
    """
    Calculate overall distribution delta score (0-1).

    0.0 = Perfect match between expected and actual
    1.0 = Maximum deviation

    Uses mean absolute deviation normalized by maximum possible deviation.
    """
    if not expected:
        return 0.0

    all_programmes = set(expected.keys()) | set(actual.keys())
    if not all_programmes:
        return 0.0

    total_deviation = 0.0
    for prog_id in all_programmes:
        exp_pct = expected.get(prog_id, 0.0)
        act_pct = actual.get(prog_id, 0.0)
        total_deviation += abs(exp_pct - act_pct)

    # Maximum possible deviation is 200 (all in one programme vs spread)
    # But practical max is around 100, so we normalize by that
    max_deviation = 100.0
    delta_score = min(1.0, total_deviation / max_deviation)

    return round(delta_score, 4)


def detect_overrepresented_programmes(
    expected: Optional[Dict[str, float]] = None,
    actual: Optional[Dict[str, float]] = None,
    threshold: float = FUNDING_OVERREP_THRESHOLD
) -> List[ProgrammeDistribution]:
    """
    Detect programmes that are recommended more than expected.

    A programme is overrepresented if actual/expected > threshold.
    """
    if expected is None:
        expected = calculate_expected_distribution()
    if actual is None:
        actual = calculate_actual_distribution()

    total_recs = len(_recommendation_history)
    overrepresented: List[ProgrammeDistribution] = []

    for prog_id, exp_pct in expected.items():
        act_pct = actual.get(prog_id, 0.0)

        if exp_pct > 0 and act_pct > 0:
            ratio = act_pct / exp_pct
            if ratio > threshold:
                delta = act_pct - exp_pct
                rec_count = int((act_pct / 100) * total_recs) if total_recs > 0 else 0

                overrepresented.append(ProgrammeDistribution(
                    programme_id=prog_id,
                    programme_name=_get_programme_name(prog_id),
                    expected_pct=exp_pct,
                    actual_pct=act_pct,
                    delta_pct=round(delta, 2),
                    recommendation_count=rec_count,
                    total_recommendations=total_recs,
                    rebalancing_required=abs(delta) > (FUNDING_REBALANCING_THRESHOLD * 100),
                    representation_status="overrepresented"
                ))

    # Sort by delta (highest overrepresentation first)
    overrepresented.sort(key=lambda x: x.delta_pct, reverse=True)
    return overrepresented


def detect_underrepresented_programmes(
    expected: Optional[Dict[str, float]] = None,
    actual: Optional[Dict[str, float]] = None,
    threshold: float = FUNDING_UNDERREP_THRESHOLD
) -> List[ProgrammeDistribution]:
    """
    Detect programmes that are recommended less than expected.

    A programme is underrepresented if actual/expected < threshold.
    """
    if expected is None:
        expected = calculate_expected_distribution()
    if actual is None:
        actual = calculate_actual_distribution()

    total_recs = len(_recommendation_history)
    underrepresented: List[ProgrammeDistribution] = []

    for prog_id, exp_pct in expected.items():
        act_pct = actual.get(prog_id, 0.0)

        # Programme is underrepresented if actual is much less than expected
        if exp_pct > 0:
            ratio = act_pct / exp_pct if act_pct > 0 else 0.0
            if ratio < threshold:
                delta = act_pct - exp_pct
                rec_count = int((act_pct / 100) * total_recs) if total_recs > 0 else 0

                underrepresented.append(ProgrammeDistribution(
                    programme_id=prog_id,
                    programme_name=_get_programme_name(prog_id),
                    expected_pct=exp_pct,
                    actual_pct=act_pct,
                    delta_pct=round(delta, 2),
                    recommendation_count=rec_count,
                    total_recommendations=total_recs,
                    rebalancing_required=abs(delta) > (FUNDING_REBALANCING_THRESHOLD * 100),
                    representation_status="underrepresented"
                ))

    # Sort by delta (most underrepresented first, i.e., most negative delta)
    underrepresented.sort(key=lambda x: x.delta_pct)
    return underrepresented


def analyze_distribution(
    country: str = "DE",
    region: Optional[str] = None,
    segments: Optional[List[SegmentDefinition]] = None
) -> DistributionAnalysisResult:
    """
    Perform complete distribution analysis.

    Returns comprehensive analysis including over/under-represented programmes
    and recommendations for rebalancing.
    """
    analysis_id = f"dist_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now(timezone.utc).isoformat()

    if not FUNDING_DISTRIBUTION_ENABLED:
        return DistributionAnalysisResult(
            analysis_id=analysis_id,
            timestamp=timestamp,
            enabled=False,
            total_recommendations=0,
            overrepresented=[],
            underrepresented=[],
            balanced=[],
            delta_score=0.0,
            rebalancing_required=False,
            recommendations_for_rebalancing=[]
        )

    expected = calculate_expected_distribution(segments, country)
    actual = calculate_actual_distribution(country, region)

    overrep = detect_overrepresented_programmes(expected, actual)
    underrep = detect_underrepresented_programmes(expected, actual)

    # Find balanced programmes
    overrep_ids = {p.programme_id for p in overrep}
    underrep_ids = {p.programme_id for p in underrep}
    total_recs = len(_recommendation_history)

    balanced: List[ProgrammeDistribution] = []
    for prog_id in expected.keys():
        if prog_id not in overrep_ids and prog_id not in underrep_ids:
            exp_pct = expected[prog_id]
            act_pct = actual.get(prog_id, 0.0)
            rec_count = int((act_pct / 100) * total_recs) if total_recs > 0 else 0

            balanced.append(ProgrammeDistribution(
                programme_id=prog_id,
                programme_name=_get_programme_name(prog_id),
                expected_pct=exp_pct,
                actual_pct=act_pct,
                delta_pct=round(act_pct - exp_pct, 2),
                recommendation_count=rec_count,
                total_recommendations=total_recs,
                rebalancing_required=False,
                representation_status="balanced"
            ))

    delta_score = distribution_delta_score(expected, actual)

    # Generate rebalancing recommendations
    recommendations = _generate_rebalancing_recommendations(overrep, underrep, delta_score)
    rebalancing_required = any(p.rebalancing_required for p in overrep + underrep)

    result = DistributionAnalysisResult(
        analysis_id=analysis_id,
        timestamp=timestamp,
        enabled=True,
        total_recommendations=total_recs,
        overrepresented=overrep,
        underrepresented=underrep,
        balanced=balanced,
        delta_score=delta_score,
        rebalancing_required=rebalancing_required,
        recommendations_for_rebalancing=recommendations
    )

    # Persist snapshot
    _save_distribution_snapshot(result)

    return result


def get_distribution_history(
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get history of distribution snapshots."""
    snapshots = sorted(
        _distribution_snapshots,
        key=lambda x: x.timestamp,
        reverse=True
    )[:limit]
    return [s.to_dict() for s in snapshots]


def get_programme_trend(
    programme_id: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get historical trend for a specific programme."""
    trend: List[Dict[str, Any]] = []

    for snapshot in sorted(_distribution_snapshots, key=lambda x: x.timestamp)[-limit:]:
        for pd in snapshot.programme_distributions:
            if pd.programme_id == programme_id:
                trend.append({
                    "timestamp": snapshot.timestamp,
                    "actual_pct": pd.actual_pct,
                    "expected_pct": pd.expected_pct,
                    "delta_pct": pd.delta_pct,
                    "status": pd.representation_status
                })
                break

    return trend


def clear_recommendation_history() -> int:
    """Clear recommendation history. Returns count of cleared records."""
    global _recommendation_history
    count = len(_recommendation_history)
    _recommendation_history = []
    logger.info(f"Cleared {count} recommendation records")
    return count


# ============================================================================
# Helper Functions
# ============================================================================

def _get_programme_name(programme_id: str) -> str:
    """Get human-readable programme name."""
    programme_names = {
        "go_digital": "go-digital",
        "kfw_digital_innovation": "KfW Digital & Innovation",
        "digitalbonus_bayern": "Digitalbonus Bayern",
        "invest_bw": "Invest BW",
        "profit_berlin": "ProFIT Berlin",
        "coaching_bonus_berlin": "Coaching BONUS Berlin",
        "transfer_bonus_berlin": "Transfer BONUS Berlin",
        "innovationsgutschein_bayern": "Innovationsgutschein Bayern",
        "zim": "ZIM",
        "exist": "EXIST",
        "digital_verwaltung_itsec": "Digitalisierung & IT-Sicherheit"
    }
    return programme_names.get(programme_id, programme_id)


def _generate_rebalancing_recommendations(
    overrep: List[ProgrammeDistribution],
    underrep: List[ProgrammeDistribution],
    delta_score: float
) -> List[Dict[str, Any]]:
    """Generate actionable rebalancing recommendations."""
    recommendations: List[Dict[str, Any]] = []

    # Recommendations for overrepresented programmes
    for prog in overrep:
        if prog.rebalancing_required:
            recommendations.append({
                "type": "reduce_priority",
                "programme_id": prog.programme_id,
                "programme_name": prog.programme_name,
                "action": f"Reduce recommendation priority by {min(30, int(prog.delta_pct))}%",
                "reason": f"Overrepresented by {prog.delta_pct:+.1f}% vs expected",
                "severity": "high" if prog.delta_pct > 20 else "medium"
            })

    # Recommendations for underrepresented programmes
    for prog in underrep:
        if prog.rebalancing_required:
            recommendations.append({
                "type": "increase_priority",
                "programme_id": prog.programme_id,
                "programme_name": prog.programme_name,
                "action": f"Increase recommendation priority by {min(30, int(abs(prog.delta_pct)))}%",
                "reason": f"Underrepresented by {prog.delta_pct:.1f}% vs expected",
                "severity": "high" if prog.delta_pct < -20 else "medium"
            })

    # Overall recommendation
    if delta_score > 0.3:
        recommendations.append({
            "type": "system_review",
            "programme_id": None,
            "programme_name": None,
            "action": "Review recommendation algorithm for systematic bias",
            "reason": f"Overall distribution delta score ({delta_score:.2f}) indicates significant imbalance",
            "severity": "high"
        })

    return recommendations


def _save_distribution_snapshot(result: DistributionAnalysisResult) -> None:
    """Save distribution snapshot to storage."""
    all_distributions = result.overrepresented + result.underrepresented + result.balanced
    rebalancing_progs = [
        p.programme_id for p in all_distributions if p.rebalancing_required
    ]

    snapshot = DistributionSnapshot(
        snapshot_id=result.analysis_id,
        timestamp=result.timestamp,
        total_recommendations=result.total_recommendations,
        programme_distributions=all_distributions,
        delta_score=result.delta_score,
        segments_analyzed=["solo", "team", "kmu", "enterprise"],
        rebalancing_programmes=rebalancing_progs
    )
    _distribution_snapshots.append(snapshot)

    # Persist to disk
    _persist_snapshot(snapshot)


def _persist_snapshot(snapshot: DistributionSnapshot) -> None:
    """Persist snapshot to filesystem."""
    try:
        storage_path = Path(FUNDING_DISTRIBUTION_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)

        filepath = storage_path / f"{snapshot.snapshot_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)

        logger.debug(f"Persisted distribution snapshot: {filepath}")
    except Exception as e:
        logger.error(f"Failed to persist distribution snapshot: {e}")


def load_snapshots_from_storage() -> int:
    """Load snapshots from persistent storage. Returns count loaded."""
    global _distribution_snapshots

    storage_path = Path(FUNDING_DISTRIBUTION_STORAGE_PATH)
    if not storage_path.exists():
        return 0

    loaded = 0
    for filepath in storage_path.glob("dist_*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct snapshot
            distributions = [
                ProgrammeDistribution(**pd) for pd in data.get("programme_distributions", [])
            ]
            snapshot = DistributionSnapshot(
                snapshot_id=data["snapshot_id"],
                timestamp=data["timestamp"],
                total_recommendations=data["total_recommendations"],
                programme_distributions=distributions,
                delta_score=data["delta_score"],
                segments_analyzed=data.get("segments_analyzed", []),
                rebalancing_programmes=data.get("rebalancing_programmes", [])
            )
            _distribution_snapshots.append(snapshot)
            loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load snapshot {filepath}: {e}")

    logger.info(f"Loaded {loaded} distribution snapshots from storage")
    return loaded


# ============================================================================
# Module Initialization
# ============================================================================

def _initialize_module() -> None:
    """Initialize module on import."""
    if FUNDING_DISTRIBUTION_ENABLED:
        try:
            load_snapshots_from_storage()
        except Exception as e:
            logger.warning(f"Could not load distribution snapshots: {e}")


_initialize_module()
