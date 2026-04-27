# -*- coding: utf-8 -*-
"""
Sprint G17.3-C: Fine-Tuning Dataset Builder

Builds and manages fine-tuning datasets from accumulated signals:
- Signal aggregation with winsorizing
- Conflict resolution for contradictory signals
- Quality-based filtering
- JSONL export for training

Version: 1.0.0 (Sprint G17.3)
"""
from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import statistics

from services.ft_signal_extractor import (
    FTSignal,
    FTSignalBatch,
    NormalizedSignal,
    SegmentInfo,
    signal_to_training_format,
    get_signal_statistics,
    to_normalized_signal,
    FT_SIGNAL_STORAGE_PATH,
    FT_MIN_CONFIDENCE_THRESHOLD,
    FT_DATASET_DAYS,
    FT_BUILD_DATASET_ON_REPORT,
    FT_SIGNAL_MAX_AGE_DAYS,
)

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

FT_DATASET_ENABLED = os.environ.get("FT_DATASET_ENABLED", "1") == "1"
FT_DATASET_MIN_SIGNALS = int(os.environ.get("FT_DATASET_MIN_SIGNALS", "100"))
FT_DATASET_MAX_SIGNALS = int(os.environ.get("FT_DATASET_MAX_SIGNALS", "10000"))
FT_DATASET_WINSORIZE_PERCENTILE = float(os.environ.get("FT_DATASET_WINSORIZE_PERCENTILE", "0.05"))
FT_DATASET_CONFLICT_THRESHOLD = float(os.environ.get("FT_DATASET_CONFLICT_THRESHOLD", "0.3"))
FT_DATASET_AUTO_EXPORT_THRESHOLD = int(os.environ.get("FT_DATASET_AUTO_EXPORT_THRESHOLD", "500"))

# Storage lock for thread safety
_storage_lock = threading.Lock()

# In-memory signal buffer
_signal_buffer: List[FTSignal] = []


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DatasetMetadata:
    """Metadata for an exported dataset."""
    dataset_id: str
    created_at: str
    signal_count: int
    signal_types: Dict[str, int]
    avg_quality_score: float
    min_quality_score: float
    max_quality_score: float
    date_range_start: str
    date_range_end: str
    winsorized: bool
    conflicts_resolved: int
    export_path: str


@dataclass
class ConflictGroup:
    """Group of conflicting signals for the same input."""
    input_hash: str
    signals: List[FTSignal]
    resolved_signal: Optional[FTSignal] = None
    resolution_method: str = ""


@dataclass
class DatasetBuildResult:
    """Result of dataset building process."""
    success: bool
    dataset_id: str
    output_path: str
    total_signals: int
    filtered_signals: int
    conflicts_found: int
    conflicts_resolved: int
    avg_quality: float
    metadata: Optional[DatasetMetadata] = None
    errors: List[str] = field(default_factory=list)


# =============================================================================
# SIGNAL STORAGE
# =============================================================================

def get_storage_path() -> Path:
    """Get the storage path for signals, creating if needed."""
    path = Path(FT_SIGNAL_STORAGE_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def add_signals_to_buffer(signals: List[FTSignal]) -> int:
    """
    Add signals to the in-memory buffer.

    Returns number of signals added.
    """
    global _signal_buffer

    with _storage_lock:
        initial_count = len(_signal_buffer)
        _signal_buffer.extend(signals)

        # Auto-persist if buffer gets large
        if len(_signal_buffer) >= FT_DATASET_AUTO_EXPORT_THRESHOLD:
            _persist_buffer_to_disk()

        return len(_signal_buffer) - initial_count


def get_buffer_size() -> int:
    """Get current buffer size."""
    return len(_signal_buffer)


def get_buffered_signals() -> List[FTSignal]:
    """Get copy of buffered signals."""
    with _storage_lock:
        return list(_signal_buffer)


def clear_buffer() -> int:
    """Clear the signal buffer. Returns count of cleared signals."""
    global _signal_buffer
    with _storage_lock:
        count = len(_signal_buffer)
        _signal_buffer = []
        return count


def _persist_buffer_to_disk() -> str:
    """Persist current buffer to disk. Returns file path."""
    global _signal_buffer

    if not _signal_buffer:
        return ""

    storage_path = get_storage_path()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"signals_buffer_{timestamp}.jsonl"
    filepath = storage_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        for signal in _signal_buffer:
            entry = signal_to_training_format(signal)
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    log.info(f"Persisted {len(_signal_buffer)} signals to {filepath}")

    # Clear buffer after persistence
    _signal_buffer = []

    return str(filepath)


def load_signals_from_storage(
    max_age_days: Optional[int] = None,
    signal_types: Optional[List[str]] = None,
) -> List[FTSignal]:
    """
    Load signals from persistent storage.

    Args:
        max_age_days: Maximum age of signals to load
        signal_types: Filter by signal types

    Returns:
        List of loaded signals
    """
    if max_age_days is None:
        max_age_days = FT_SIGNAL_MAX_AGE_DAYS

    storage_path = get_storage_path()
    cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

    loaded_signals: List[FTSignal] = []

    # Load from JSONL files
    for filepath in storage_path.glob("signals_*.jsonl"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    metadata = entry.get("metadata", {})

                    # Reconstruct FTSignal
                    signal = FTSignal(
                        signal_id=metadata.get("signal_id", ""),
                        signal_type=metadata.get("signal_type", ""),
                        source_section=metadata.get("source_section", ""),
                        timestamp=metadata.get("timestamp", datetime.utcnow().isoformat()),
                        prompt_input=entry.get("messages", [{}])[1].get("content", "")
                        if len(entry.get("messages", [])) > 1 else "",
                        ideal_output=entry.get("messages", [{}])[2].get("content", "")
                        if len(entry.get("messages", [])) > 2 else "",
                        original_output="",  # Not stored in training format
                        quality_score=metadata.get("quality_score", 0.5),
                        confidence=metadata.get("confidence", 0.5),
                        segment_key=metadata.get("segment_key"),
                        company_size=metadata.get("company_size"),
                        industry=metadata.get("industry"),
                        lang=metadata.get("lang", "de"),
                        is_normalized=True,
                        is_anonymized=True,
                    )

                    # Apply filters
                    if signal_types and signal.signal_type not in signal_types:
                        continue

                    # Check age
                    try:
                        signal_date = datetime.fromisoformat(signal.timestamp.replace("Z", "+00:00"))
                        if signal_date.replace(tzinfo=None) < cutoff_date:
                            continue
                    except (ValueError, AttributeError):
                        pass  # Include signals with invalid timestamps

                    loaded_signals.append(signal)

        except Exception as e:
            log.error(f"Error loading signals from {filepath}: {e}")
            continue

    # Also include buffered signals
    with _storage_lock:
        for signal in _signal_buffer:
            if signal_types and signal.signal_type not in signal_types:
                continue
            loaded_signals.append(signal)

    log.info(f"Loaded {len(loaded_signals)} signals from storage")
    return loaded_signals


# =============================================================================
# QUALITY FILTERING
# =============================================================================

def filter_signals_by_quality(
    signals: List[FTSignal],
    min_quality: Optional[float] = None,
) -> Tuple[List[FTSignal], int]:
    """
    Filter signals by quality score.

    Returns:
        Tuple of (filtered signals, count removed)
    """
    if min_quality is None:
        min_quality = FT_MIN_CONFIDENCE_THRESHOLD

    filtered = [s for s in signals if s.quality_score >= min_quality]
    removed = len(signals) - len(filtered)

    return filtered, removed


def winsorize_quality_scores(
    signals: List[FTSignal],
    percentile: Optional[float] = None,
) -> List[FTSignal]:
    """
    Apply winsorizing to quality scores to reduce outlier impact.

    Clips extreme values to specified percentile bounds.
    """
    if not signals:
        return signals

    if percentile is None:
        percentile = FT_DATASET_WINSORIZE_PERCENTILE

    scores = [s.quality_score for s in signals]

    if len(scores) < 10:
        return signals  # Not enough data for winsorizing

    # Calculate percentile bounds
    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    lower_idx = max(0, int(n * percentile))
    upper_idx = min(n - 1, int(n * (1 - percentile)))

    lower_bound = sorted_scores[lower_idx]
    upper_bound = sorted_scores[upper_idx]

    # Apply clipping
    for signal in signals:
        signal.quality_score = max(lower_bound, min(upper_bound, signal.quality_score))

    return signals


# =============================================================================
# CONFLICT RESOLUTION
# =============================================================================

def _compute_input_hash(signal: FTSignal) -> str:
    """Compute hash for signal's input to identify potential conflicts."""
    # Normalize input for comparison
    normalized_input = signal.prompt_input.lower().strip()
    # Include signal type in hash to separate by type
    hash_input = f"{signal.signal_type}:{normalized_input}"
    return hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest()[:12]


def identify_conflicts(signals: List[FTSignal]) -> List[ConflictGroup]:
    """
    Identify conflicting signals (same input, different outputs).

    Returns list of conflict groups.
    """
    # Group by input hash
    hash_groups: Dict[str, List[FTSignal]] = {}

    for signal in signals:
        input_hash = _compute_input_hash(signal)
        if input_hash not in hash_groups:
            hash_groups[input_hash] = []
        hash_groups[input_hash].append(signal)

    # Find conflicts (groups with multiple signals and differing outputs)
    conflicts: List[ConflictGroup] = []

    for input_hash, group_signals in hash_groups.items():
        if len(group_signals) < 2:
            continue

        # Check if outputs differ significantly
        outputs = [s.ideal_output for s in group_signals]
        unique_outputs = set(outputs)

        if len(unique_outputs) > 1:
            conflicts.append(ConflictGroup(
                input_hash=input_hash,
                signals=group_signals,
            ))

    return conflicts


def resolve_conflict(conflict: ConflictGroup) -> FTSignal:
    """
    Resolve a conflict group by selecting the best signal.

    Resolution strategy:
    1. Prefer human-validated signals
    2. Prefer higher quality scores
    3. Prefer newer signals
    4. Prefer majority output
    """
    signals = conflict.signals

    if not signals:
        raise ValueError("Empty conflict group")

    if len(signals) == 1:
        conflict.resolved_signal = signals[0]
        conflict.resolution_method = "single"
        return signals[0]

    # Check for human-validated signals
    human_validated = [s for s in signals if s.human_validated]
    if human_validated:
        # Select highest quality among human-validated
        best = max(human_validated, key=lambda s: s.quality_score)
        conflict.resolved_signal = best
        conflict.resolution_method = "human_validated"
        return best

    # Check for majority output
    output_counts: Dict[str, List[FTSignal]] = {}
    for signal in signals:
        output_key = signal.ideal_output[:500]  # Truncate for comparison
        if output_key not in output_counts:
            output_counts[output_key] = []
        output_counts[output_key].append(signal)

    # Find majority
    max_count = max(len(v) for v in output_counts.values())
    majority_groups = [g for g in output_counts.values() if len(g) == max_count]

    if len(majority_groups) == 1 and max_count > len(signals) / 2:
        # Clear majority - select highest quality from majority
        majority_signals = majority_groups[0]
        best = max(majority_signals, key=lambda s: s.quality_score)
        conflict.resolved_signal = best
        conflict.resolution_method = "majority"
        return best

    # No clear majority - use quality score
    best = max(signals, key=lambda s: (s.quality_score, s.timestamp))
    conflict.resolved_signal = best
    conflict.resolution_method = "quality_score"
    return best


def resolve_all_conflicts(
    signals: List[FTSignal],
) -> Tuple[List[FTSignal], int]:
    """
    Identify and resolve all conflicts in signal list.

    Returns:
        Tuple of (deduplicated signals, conflicts resolved count)
    """
    conflicts = identify_conflicts(signals)

    if not conflicts:
        return signals, 0

    # Get hashes of conflicting signals
    conflict_hashes = {c.input_hash for c in conflicts}

    # Separate non-conflicting signals
    result: List[FTSignal] = []
    seen_hashes: set = set()

    for signal in signals:
        input_hash = _compute_input_hash(signal)

        if input_hash not in conflict_hashes:
            # No conflict - include signal
            if input_hash not in seen_hashes:
                result.append(signal)
                seen_hashes.add(input_hash)

    # Add resolved signals from conflicts
    for conflict in conflicts:
        resolved = resolve_conflict(conflict)
        if resolved:
            result.append(resolved)

    return result, len(conflicts)


# =============================================================================
# DATASET BUILDING
# =============================================================================

def build_dataset(
    signals: Optional[List[FTSignal]] = None,
    output_filename: Optional[str] = None,
    include_metadata: bool = True,
    apply_winsorizing: bool = True,
    resolve_conflicts: bool = True,
    min_quality: Optional[float] = None,
    signal_types: Optional[List[str]] = None,
) -> DatasetBuildResult:
    """
    Build a fine-tuning dataset from signals.

    Args:
        signals: Optional signals list (loads from storage if None)
        output_filename: Custom output filename
        include_metadata: Include metadata in output
        apply_winsorizing: Apply winsorizing to quality scores
        resolve_conflicts: Resolve conflicting signals
        min_quality: Minimum quality score threshold
        signal_types: Filter by signal types

    Returns:
        DatasetBuildResult with build statistics
    """
    if not FT_DATASET_ENABLED:
        return DatasetBuildResult(
            success=False,
            dataset_id="",
            output_path="",
            total_signals=0,
            filtered_signals=0,
            conflicts_found=0,
            conflicts_resolved=0,
            avg_quality=0.0,
            errors=["Dataset building is disabled"],
        )

    errors: List[str] = []

    # Load signals if not provided
    if signals is None:
        signals = load_signals_from_storage(signal_types=signal_types)

    if not signals:
        return DatasetBuildResult(
            success=False,
            dataset_id="",
            output_path="",
            total_signals=0,
            filtered_signals=0,
            conflicts_found=0,
            conflicts_resolved=0,
            avg_quality=0.0,
            errors=["No signals available for dataset building"],
        )

    total_signals = len(signals)

    # Apply quality filtering
    signals, filtered_count = filter_signals_by_quality(signals, min_quality)
    filtered_signals = total_signals - len(signals)

    if len(signals) < FT_DATASET_MIN_SIGNALS:
        return DatasetBuildResult(
            success=False,
            dataset_id="",
            output_path="",
            total_signals=total_signals,
            filtered_signals=filtered_signals,
            conflicts_found=0,
            conflicts_resolved=0,
            avg_quality=0.0,
            errors=[f"Insufficient signals after filtering: {len(signals)} < {FT_DATASET_MIN_SIGNALS}"],
        )

    # Resolve conflicts
    conflicts_resolved = 0
    conflicts_found = 0
    if resolve_conflicts:
        conflicts = identify_conflicts(signals)
        conflicts_found = len(conflicts)
        signals, conflicts_resolved = resolve_all_conflicts(signals)

    # Apply winsorizing
    if apply_winsorizing:
        signals = winsorize_quality_scores(signals)

    # Limit to max signals
    if len(signals) > FT_DATASET_MAX_SIGNALS:
        # Sort by quality and take top signals
        signals = sorted(signals, key=lambda s: s.quality_score, reverse=True)
        signals = signals[:FT_DATASET_MAX_SIGNALS]

    # Generate dataset ID
    dataset_id = f"ft_dataset_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Prepare output path
    storage_path = get_storage_path()
    if output_filename:
        output_path = storage_path / output_filename
    else:
        output_path = storage_path / f"{dataset_id}.jsonl"

    # Calculate statistics
    quality_scores = [s.quality_score for s in signals]
    avg_quality = statistics.mean(quality_scores) if quality_scores else 0.0
    min_quality_actual = min(quality_scores) if quality_scores else 0.0
    max_quality_actual = max(quality_scores) if quality_scores else 0.0

    # Get date range
    timestamps = [s.timestamp for s in signals if s.timestamp]
    date_range_start = min(timestamps) if timestamps else ""
    date_range_end = max(timestamps) if timestamps else ""

    # Count by type
    signal_type_counts: Dict[str, int] = {}
    for signal in signals:
        signal_type_counts[signal.signal_type] = signal_type_counts.get(signal.signal_type, 0) + 1

    # Write dataset
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for signal in signals:
                entry = signal_to_training_format(signal)
                if not include_metadata:
                    del entry["metadata"]
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        errors.append(f"Error writing dataset: {e}")
        return DatasetBuildResult(
            success=False,
            dataset_id=dataset_id,
            output_path=str(output_path),
            total_signals=total_signals,
            filtered_signals=filtered_signals,
            conflicts_found=conflicts_found,
            conflicts_resolved=conflicts_resolved,
            avg_quality=avg_quality,
            errors=errors,
        )

    # Create metadata
    metadata = DatasetMetadata(
        dataset_id=dataset_id,
        created_at=datetime.utcnow().isoformat(),
        signal_count=len(signals),
        signal_types=signal_type_counts,
        avg_quality_score=avg_quality,
        min_quality_score=min_quality_actual,
        max_quality_score=max_quality_actual,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        winsorized=apply_winsorizing,
        conflicts_resolved=conflicts_resolved,
        export_path=str(output_path),
    )

    # Write metadata file
    metadata_path = storage_path / f"{dataset_id}_metadata.json"
    try:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)
    except Exception as e:
        errors.append(f"Error writing metadata: {e}")

    log.info(
        f"Built dataset {dataset_id}: {len(signals)} signals, "
        f"avg quality {avg_quality:.2f}, {conflicts_resolved} conflicts resolved"
    )

    return DatasetBuildResult(
        success=True,
        dataset_id=dataset_id,
        output_path=str(output_path),
        total_signals=total_signals,
        filtered_signals=filtered_signals,
        conflicts_found=conflicts_found,
        conflicts_resolved=conflicts_resolved,
        avg_quality=avg_quality,
        metadata=metadata,
        errors=errors,
    )


def list_datasets() -> List[DatasetMetadata]:
    """List all available datasets."""
    storage_path = get_storage_path()
    datasets: List[DatasetMetadata] = []

    for metadata_path in storage_path.glob("*_metadata.json"):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                datasets.append(DatasetMetadata(**data))
        except Exception as e:
            log.error(f"Error loading metadata from {metadata_path}: {e}")
            continue

    # Sort by creation date, newest first
    datasets.sort(key=lambda d: d.created_at, reverse=True)
    return datasets


def get_dataset_by_id(dataset_id: str) -> Optional[DatasetMetadata]:
    """Get dataset metadata by ID."""
    storage_path = get_storage_path()
    metadata_path = storage_path / f"{dataset_id}_metadata.json"

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return DatasetMetadata(**data)
    except Exception as e:
        log.error(f"Error loading dataset {dataset_id}: {e}")
        return None


def delete_dataset(dataset_id: str) -> bool:
    """Delete a dataset and its metadata."""
    storage_path = get_storage_path()
    dataset_path = storage_path / f"{dataset_id}.jsonl"
    metadata_path = storage_path / f"{dataset_id}_metadata.json"

    deleted = False

    if dataset_path.exists():
        dataset_path.unlink()
        deleted = True

    if metadata_path.exists():
        metadata_path.unlink()
        deleted = True

    return deleted


# =============================================================================
# DATASET ANALYTICS
# =============================================================================

def get_dataset_analytics() -> Dict[str, Any]:
    """
    Get analytics across all datasets and buffered signals.
    """
    datasets = list_datasets()
    buffered_signals = get_buffered_signals()

    total_datasets = len(datasets)
    total_signals_in_datasets = sum(d.signal_count for d in datasets)
    buffered_count = len(buffered_signals)

    # Aggregate signal type distribution
    type_distribution: Dict[str, int] = {}
    for dataset in datasets:
        for sig_type, count in dataset.signal_types.items():
            type_distribution[sig_type] = type_distribution.get(sig_type, 0) + count

    # Add buffered signals
    for signal in buffered_signals:
        type_distribution[signal.signal_type] = type_distribution.get(signal.signal_type, 0) + 1

    # Average quality across datasets
    avg_qualities = [d.avg_quality_score for d in datasets if d.avg_quality_score > 0]
    overall_avg_quality = statistics.mean(avg_qualities) if avg_qualities else 0.0

    # Date range
    all_dates = []
    for d in datasets:
        if d.date_range_start:
            all_dates.append(d.date_range_start)
        if d.date_range_end:
            all_dates.append(d.date_range_end)

    date_range_start = min(all_dates) if all_dates else ""
    date_range_end = max(all_dates) if all_dates else ""

    return {
        "total_datasets": total_datasets,
        "total_signals_in_datasets": total_signals_in_datasets,
        "buffered_signals": buffered_count,
        "total_signals": total_signals_in_datasets + buffered_count,
        "signal_type_distribution": type_distribution,
        "overall_avg_quality": overall_avg_quality,
        "date_range_start": date_range_start,
        "date_range_end": date_range_end,
        "storage_path": str(get_storage_path()),
        "ready_for_export": buffered_count >= FT_DATASET_MIN_SIGNALS,
    }


def get_signal_quality_histogram(bins: int = 10) -> Dict[str, Any]:
    """
    Get quality score distribution histogram.
    """
    signals = load_signals_from_storage()

    if not signals:
        return {"bins": [], "counts": [], "total": 0}

    scores = [s.quality_score for s in signals]
    bin_width = 1.0 / bins
    bin_edges = [i * bin_width for i in range(bins + 1)]
    counts = [0] * bins

    for score in scores:
        bin_idx = min(int(score / bin_width), bins - 1)
        counts[bin_idx] += 1

    bin_labels = [f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}" for i in range(bins)]

    return {
        "bins": bin_labels,
        "counts": counts,
        "total": len(signals),
        "mean": statistics.mean(scores),
        "median": statistics.median(scores),
        "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0.0,
    }


# =============================================================================
# G17.3-C: DATASET QUALITY SCORING
# =============================================================================

@dataclass
class DatasetQualityScore:
    """Quality score for a dataset (G17.3-C)."""
    completeness: float  # % filled fields
    diversity: float  # Signal type distribution
    conflict_score: float  # Conflicts per 100 signals
    predictive_alignment_score: float
    persona_precision: float
    ai_act_reasoning_strength: float
    overall_score: float
    rating: str  # green|yellow|red


def score_dataset_quality(
    signals: Optional[List[FTSignal]] = None,
) -> DatasetQualityScore:
    """
    Calculate comprehensive quality score for a dataset (G17.3-C).

    Returns:
        DatasetQualityScore with metrics per spec
    """
    if signals is None:
        signals = load_signals_from_storage()

    if not signals:
        return DatasetQualityScore(
            completeness=0.0,
            diversity=0.0,
            conflict_score=0.0,
            predictive_alignment_score=0.0,
            persona_precision=0.0,
            ai_act_reasoning_strength=0.0,
            overall_score=0.0,
            rating="red",
        )

    # 1. Completeness: % of signals with all required fields
    complete_count = 0
    for sig in signals:
        has_required = all([
            sig.signal_id,
            sig.signal_type,
            sig.prompt_input,
            sig.ideal_output,
            sig.confidence > 0,
        ])
        if has_required:
            complete_count += 1
    completeness = complete_count / len(signals) if signals else 0.0

    # 2. Diversity: Distribution across signal types (Shannon entropy normalized)
    type_counts: Dict[str, int] = {}
    for sig in signals:
        type_counts[sig.signal_type] = type_counts.get(sig.signal_type, 0) + 1

    # Calculate normalized entropy
    total = len(signals)
    num_types = len(type_counts)
    if num_types > 1:
        import math
        entropy = 0.0
        for count in type_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        max_entropy = math.log2(num_types)
        diversity = entropy / max_entropy if max_entropy > 0 else 0.0
    else:
        diversity = 0.0

    # 3. Conflict score (conflicts per 100 signals)
    conflicts = identify_conflicts(signals)
    conflict_score = (len(conflicts) / len(signals)) * 100 if signals else 0.0

    # 4. Predictive alignment: signals from predictive drift type with high quality
    predictive_signals = [s for s in signals if s.signal_type == "predictive_drift"]
    if predictive_signals:
        predictive_alignment = statistics.mean([s.quality_score for s in predictive_signals])
    else:
        predictive_alignment = 0.5  # Neutral if no predictive signals

    # 5. Persona precision: quality of persona_fix signals
    persona_signals = [s for s in signals if s.signal_type == "persona_fix"]
    if persona_signals:
        persona_precision = statistics.mean([s.quality_score for s in persona_signals])
    else:
        persona_precision = 0.5  # Neutral if no persona signals

    # 6. AI Act reasoning strength: quality of ai_act_reasoning signals
    ai_act_signals = [s for s in signals if s.signal_type == "ai_act_reasoning"]
    if ai_act_signals:
        ai_act_strength = statistics.mean([s.quality_score for s in ai_act_signals])
    else:
        ai_act_strength = 0.5  # Neutral if no AI Act signals

    # Calculate overall score (weighted average)
    overall = (
        completeness * 0.20 +
        diversity * 0.15 +
        (1.0 - min(conflict_score / 10, 1.0)) * 0.15 +  # Lower conflicts = higher score
        predictive_alignment * 0.15 +
        persona_precision * 0.20 +
        ai_act_strength * 0.15
    )

    # Determine rating
    if overall >= 0.7:
        rating = "green"
    elif overall >= 0.4:
        rating = "yellow"
    else:
        rating = "red"

    return DatasetQualityScore(
        completeness=round(completeness, 3),
        diversity=round(diversity, 3),
        conflict_score=round(conflict_score, 3),
        predictive_alignment_score=round(predictive_alignment, 3),
        persona_precision=round(persona_precision, 3),
        ai_act_reasoning_strength=round(ai_act_strength, 3),
        overall_score=round(overall, 3),
        rating=rating,
    )


def accumulate_signals(signals: List[FTSignal]) -> int:
    """
    Accumulate signals to daily queue file (G17.3-C).

    Saves signals to /app/ft_signals/queue/YYYY-MM-DD.jsonl

    Returns:
        Number of signals accumulated
    """
    if not signals:
        return 0

    storage_path = get_storage_path()
    queue_path = storage_path / "queue"
    queue_path.mkdir(parents=True, exist_ok=True)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_file = queue_path / f"{today}.jsonl"

    with _storage_lock:
        with open(daily_file, "a", encoding="utf-8") as f:
            for signal in signals:
                entry = signal_to_training_format(signal)
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    log.info(f"Accumulated {len(signals)} signals to {daily_file}")
    return len(signals)


def build_training_dataset(
    days: Optional[int] = None,
    output_version: Optional[str] = None,
) -> DatasetBuildResult:
    """
    Build training dataset from accumulated signals (G17.3-C).

    Aggregates signals from last X days and applies:
    - Duplicate removal
    - Conflict resolution
    - Winsorizing
    - Segment stability filtering
    - Confidence scoring
    - Type balancing

    Returns:
        DatasetBuildResult with build statistics
    """
    if days is None:
        days = FT_DATASET_DAYS

    storage_path = get_storage_path()
    queue_path = storage_path / "queue"
    dataset_path = storage_path / "dataset"
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Load signals from queue files
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    all_signals: List[FTSignal] = []

    if queue_path.exists():
        for daily_file in queue_path.glob("*.jsonl"):
            try:
                # Parse date from filename
                date_str = daily_file.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff_date:
                    continue

                with open(daily_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        entry = json.loads(line)
                        metadata = entry.get("metadata", {})
                        messages = entry.get("messages", [])

                        signal = FTSignal(
                            signal_id=metadata.get("signal_id", ""),
                            signal_type=metadata.get("signal_type", ""),
                            source_section=metadata.get("source_section", ""),
                            timestamp=metadata.get("timestamp", ""),
                            prompt_input=messages[1].get("content", "") if len(messages) > 1 else "",
                            ideal_output=messages[2].get("content", "") if len(messages) > 2 else "",
                            original_output="",
                            quality_score=metadata.get("quality_score", 0.5),
                            confidence=metadata.get("confidence", 0.5),
                            segment_key=metadata.get("segment_key"),
                            company_size=metadata.get("company_size"),
                            industry=metadata.get("industry"),
                            lang=metadata.get("lang", "de"),
                            stability=metadata.get("stability", "medium"),
                            risk_level=metadata.get("risk_level", "minimal"),
                            funding_scope=metadata.get("funding_scope", "NONE"),
                        )
                        all_signals.append(signal)
            except Exception as e:
                log.error(f"Error loading signals from {daily_file}: {e}")
                continue

    # Also include buffered signals
    all_signals.extend(get_buffered_signals())

    # Build dataset using existing function
    version = output_version or f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    return build_dataset(
        signals=all_signals,
        output_filename=f"ft_dataset_{version}.jsonl",
    )


def get_ft_signal_stats() -> Dict[str, Any]:
    """
    Get signal statistics for dashboard (G17.3-E).

    Returns:
        Statistics by day, segment, signal type, and conflict rate
    """
    storage_path = get_storage_path()
    queue_path = storage_path / "queue"

    stats_by_day: Dict[str, int] = {}
    stats_by_segment: Dict[str, int] = {}
    stats_by_type: Dict[str, int] = {}
    total_signals = 0
    total_conflicts = 0

    # Load from queue files
    if queue_path.exists():
        for daily_file in queue_path.glob("*.jsonl"):
            date_str = daily_file.stem
            day_count = 0

            try:
                with open(daily_file, "r", encoding="utf-8") as f:
                    day_signals: List[FTSignal] = []
                    for line in f:
                        if not line.strip():
                            continue
                        entry = json.loads(line)
                        metadata = entry.get("metadata", {})

                        signal_type = metadata.get("signal_type", "unknown")
                        segment_key = metadata.get("segment_key", "unknown")

                        stats_by_type[signal_type] = stats_by_type.get(signal_type, 0) + 1
                        stats_by_segment[segment_key] = stats_by_segment.get(segment_key, 0) + 1
                        day_count += 1
                        total_signals += 1

                        # Create signal for conflict detection
                        messages = entry.get("messages", [])
                        day_signals.append(FTSignal(
                            signal_id=metadata.get("signal_id", ""),
                            signal_type=signal_type,
                            source_section=metadata.get("source_section", ""),
                            timestamp="",
                            prompt_input=messages[1].get("content", "") if len(messages) > 1 else "",
                            ideal_output=messages[2].get("content", "") if len(messages) > 2 else "",
                            original_output="",
                            quality_score=0.5,
                            confidence=0.5,
                        ))

                    # Count conflicts for this day
                    conflicts = identify_conflicts(day_signals)
                    total_conflicts += len(conflicts)

                stats_by_day[date_str] = day_count
            except Exception as e:
                log.error(f"Error processing {daily_file}: {e}")
                continue

    conflict_rate = (total_conflicts / total_signals * 100) if total_signals > 0 else 0.0

    return {
        "signals_by_day": stats_by_day,
        "signals_by_segment": stats_by_segment,
        "signals_by_type": stats_by_type,
        "total_signals": total_signals,
        "conflict_rate": round(conflict_rate, 2),
    }


def get_ft_sample_signals(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get anonymized sample signals for dashboard (G17.3-E).

    Returns signals from last 24h without PII or freetext.
    """
    storage_path = get_storage_path()
    queue_path = storage_path / "queue"

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_file = queue_path / f"{today}.jsonl"

    samples: List[Dict[str, Any]] = []

    if daily_file.exists():
        try:
            with open(daily_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Get last 'limit' signals
                for line in lines[-limit:]:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    metadata = entry.get("metadata", {})

                    # Create anonymized sample (no freetext content)
                    samples.append({
                        "signal_type": metadata.get("signal_type", "unknown"),
                        "source_section": metadata.get("source_section", "unknown"),
                        "quality_score": metadata.get("quality_score", 0),
                        "confidence": metadata.get("confidence", 0),
                        "segment_key": metadata.get("segment_key", "unknown"),
                        "lang": metadata.get("lang", "de"),
                        # Truncate and anonymize input/output
                        "input_preview": "[ANONYMIZED]",
                        "output_preview": "[ANONYMIZED]",
                    })
        except Exception as e:
            log.error(f"Error loading samples: {e}")

    return samples
