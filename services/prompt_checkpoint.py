# -*- coding: utf-8 -*-
"""
Sprint G17.6-A: Prompt Checkpointing Layer

Manages prompt snapshots for governance, drift detection, and rollback capability.
Enables version control of prompts with hash verification and structured diffing.

Version: 1.0.0 (Sprint G17.6)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from difflib import unified_diff
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

PROMPT_GOVERNANCE_ENABLED = os.environ.get("PROMPT_GOVERNANCE_ENABLED", "1") == "1"
PROMPT_DRAFT_MODE = os.environ.get("PROMPT_DRAFT_MODE", "0") == "1"

# Storage paths
PROMPT_SNAPSHOTS_PATH = os.environ.get("PROMPT_SNAPSHOTS_PATH", "data/prompt_snapshots")
DRIFT_RESULTS_PATH = os.environ.get("DRIFT_RESULTS_PATH", "data/drift_results")

# Drift thresholds
PROMPT_DRIFT_THRESHOLD_LOW = int(os.environ.get("PROMPT_DRIFT_THRESHOLD_LOW", "15"))
PROMPT_DRIFT_THRESHOLD_MEDIUM = int(os.environ.get("PROMPT_DRIFT_THRESHOLD_MEDIUM", "30"))
PROMPT_DRIFT_THRESHOLD_HIGH = int(os.environ.get("PROMPT_DRIFT_THRESHOLD_HIGH", "50"))
PROMPT_DRIFT_THRESHOLD_CRITICAL = int(os.environ.get("PROMPT_DRIFT_THRESHOLD_CRITICAL", "70"))


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class PromptSnapshot:
    """A versioned snapshot of a prompt file."""
    prompt_file: str
    content: str
    content_hash: str
    commit_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Extracted structure
    sections: List[str] = field(default_factory=list)
    token_count: int = 0
    persona_instructions: List[str] = field(default_factory=list)
    length_rules: List[str] = field(default_factory=list)
    system_rules: List[str] = field(default_factory=list)


@dataclass
class SnapshotDiff:
    """Structured difference between two prompt snapshots."""
    prompt_file: str
    old_version: int
    new_version: int

    # Section changes
    added_sections: List[str] = field(default_factory=list)
    removed_sections: List[str] = field(default_factory=list)
    modified_sections: List[str] = field(default_factory=list)

    # Token changes
    old_token_count: int = 0
    new_token_count: int = 0
    token_variance: float = 0.0

    # Instruction drift
    persona_instruction_changes: List[str] = field(default_factory=list)
    length_rule_changes: List[str] = field(default_factory=list)
    system_rule_changes: List[str] = field(default_factory=list)

    # Unified diff
    unified_diff: str = ""

    # Summary
    total_changes: int = 0


@dataclass
class DriftResult:
    """Result of drift analysis between snapshots."""
    prompt_file: str
    drift_score: int  # 0-100
    drift_category: str  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: datetime = field(default_factory=datetime.now)
    diff_summary: Dict[str, Any] = field(default_factory=dict)
    details: List[str] = field(default_factory=list)


# =============================================================================
# STORAGE HELPERS
# =============================================================================

_storage_lock = threading.Lock()


def _get_snapshots_path() -> Path:
    """Get the snapshots storage path."""
    path = Path(PROMPT_SNAPSHOTS_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_drift_results_path() -> Path:
    """Get the drift results storage path."""
    path = Path(DRIFT_RESULTS_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _compute_hash(content: str) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _sanitize_filename(prompt_file: str) -> str:
    """Convert prompt file path to safe filename."""
    # Replace path separators and special chars
    safe = prompt_file.replace("/", "_").replace("\\", "_").replace(".", "_")
    return safe


# =============================================================================
# CONTENT EXTRACTION
# =============================================================================

def _extract_sections(content: str) -> List[str]:
    """Extract section headers from prompt content."""
    sections = []

    # Match H1, H2, H3 headers
    h1_pattern = r"^#\s+(.+)$"
    h2_pattern = r"^##\s+(.+)$"
    h3_pattern = r"^###\s+(.+)$"

    for line in content.split("\n"):
        line = line.strip()
        for pattern in [h1_pattern, h2_pattern, h3_pattern]:
            match = re.match(pattern, line)
            if match:
                sections.append(match.group(1).strip())
                break

    return sections


def _extract_persona_instructions(content: str) -> List[str]:
    """Extract persona-related instructions from content."""
    instructions = []

    patterns = [
        r"(?:persona|anrede|du-form|sie-form|solo|team|kmu)[:\s]+(.+)",
        r"{{#if.*persona.*}}(.+?){{/if}}",
        r"(?:verwende|nutze|beachte).*(?:anrede|persona).*",
    ]

    content_lower = content.lower()
    for pattern in patterns:
        matches = re.findall(pattern, content_lower, re.IGNORECASE | re.DOTALL)
        instructions.extend([m.strip()[:100] for m in matches if m.strip()])

    return instructions[:20]  # Limit to 20


def _extract_length_rules(content: str) -> List[str]:
    """Extract length-related rules from content."""
    rules = []

    patterns = [
        r"(?:mindestens|minimum|min)\s+(\d+)\s*(?:wörter|words|zeichen)",
        r"(?:maximal|maximum|max)\s+(\d+)\s*(?:wörter|words|zeichen)",
        r"(?:länge|length)[:\s]+(.+)",
        r"SECTION_MIN_WORDS[:\s=]+(\d+)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        rules.extend([str(m).strip()[:50] for m in matches])

    return rules[:10]


def _extract_system_rules(content: str) -> List[str]:
    """Extract system rules and constraints from content."""
    rules = []

    patterns = [
        r"(?:regel|rule|constraint)[:\s]+(.+)",
        r"(?:vermeide|avoid|nicht verwenden)[:\s]+(.+)",
        r"(?:immer|always|stets)[:\s]+(.+)",
        r"(?:niemals|never|nie)[:\s]+(.+)",
        r"\[SYSTEM[:\s]+(.+?)\]",
        r"\[GUARD[:\s]+(.+?)\]",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        rules.extend([m.strip()[:100] for m in matches if m.strip()])

    return rules[:20]


def _estimate_token_count(content: str) -> int:
    """Estimate token count (roughly 4 chars per token for German)."""
    return len(content) // 4


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def load_prompt_snapshot(prompt_file: str) -> Optional[PromptSnapshot]:
    """
    Load the last approved snapshot for a prompt file.

    Args:
        prompt_file: Path to the prompt file

    Returns:
        PromptSnapshot or None if not found
    """
    if not PROMPT_GOVERNANCE_ENABLED:
        return None

    try:
        snapshots_path = _get_snapshots_path()
        safe_name = _sanitize_filename(prompt_file)
        snapshot_file = snapshots_path / f"{safe_name}_latest.json"

        if not snapshot_file.exists():
            return None

        with open(snapshot_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return PromptSnapshot(
            prompt_file=data.get("prompt_file", prompt_file),
            content=data.get("content", ""),
            content_hash=data.get("content_hash", ""),
            commit_id=data.get("commit_id"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
            sections=data.get("sections", []),
            token_count=data.get("token_count", 0),
            persona_instructions=data.get("persona_instructions", []),
            length_rules=data.get("length_rules", []),
            system_rules=data.get("system_rules", []),
        )

    except Exception as e:
        log.warning(f"Failed to load snapshot for {prompt_file}: {e}")
        return None


def create_prompt_snapshot(
    prompt_file: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    commit_id: Optional[str] = None,
) -> PromptSnapshot:
    """
    Create and store a new prompt snapshot.

    Args:
        prompt_file: Path to the prompt file
        content: Prompt content
        metadata: Optional metadata dict
        commit_id: Optional git commit ID

    Returns:
        Created PromptSnapshot
    """
    # Load existing snapshot to get version
    existing = load_prompt_snapshot(prompt_file)
    new_version = (existing.version + 1) if existing else 1

    # Extract structure
    sections = _extract_sections(content)
    persona_instructions = _extract_persona_instructions(content)
    length_rules = _extract_length_rules(content)
    system_rules = _extract_system_rules(content)
    token_count = _estimate_token_count(content)

    snapshot = PromptSnapshot(
        prompt_file=prompt_file,
        content=content,
        content_hash=_compute_hash(content),
        commit_id=commit_id,
        timestamp=datetime.now(),
        version=new_version,
        metadata=metadata or {},
        sections=sections,
        token_count=token_count,
        persona_instructions=persona_instructions,
        length_rules=length_rules,
        system_rules=system_rules,
    )

    # Store snapshot
    if not PROMPT_DRAFT_MODE:
        _store_snapshot(snapshot)

    return snapshot


def _store_snapshot(snapshot: PromptSnapshot) -> bool:
    """Store a snapshot to persistent storage."""
    try:
        with _storage_lock:
            snapshots_path = _get_snapshots_path()
            safe_name = _sanitize_filename(snapshot.prompt_file)

            # Store as latest
            latest_file = snapshots_path / f"{safe_name}_latest.json"

            # Also store versioned copy
            versioned_file = snapshots_path / f"{safe_name}_v{snapshot.version}.json"

            data = asdict(snapshot)
            data["timestamp"] = snapshot.timestamp.isoformat()

            for file_path in [latest_file, versioned_file]:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            return True

    except Exception as e:
        log.error(f"Failed to store snapshot: {e}")
        return False


def compare_snapshots(old: PromptSnapshot, new: PromptSnapshot) -> SnapshotDiff:
    """
    Compare two snapshots and generate structured diff.

    Args:
        old: Previous snapshot
        new: New snapshot

    Returns:
        SnapshotDiff with detailed changes
    """
    diff = SnapshotDiff(
        prompt_file=new.prompt_file,
        old_version=old.version,
        new_version=new.version,
        old_token_count=old.token_count,
        new_token_count=new.token_count,
    )

    # Calculate token variance
    if old.token_count > 0:
        diff.token_variance = (new.token_count - old.token_count) / old.token_count

    # Section changes
    old_sections = set(old.sections)
    new_sections = set(new.sections)

    diff.added_sections = list(new_sections - old_sections)
    diff.removed_sections = list(old_sections - new_sections)
    diff.modified_sections = list(old_sections & new_sections)  # Sections in both

    # Instruction drift
    old_persona = set(old.persona_instructions)
    new_persona = set(new.persona_instructions)
    diff.persona_instruction_changes = list(
        (new_persona - old_persona) | (old_persona - new_persona)
    )

    old_length = set(old.length_rules)
    new_length = set(new.length_rules)
    diff.length_rule_changes = list(
        (new_length - old_length) | (old_length - new_length)
    )

    old_system = set(old.system_rules)
    new_system = set(new.system_rules)
    diff.system_rule_changes = list(
        (new_system - old_system) | (old_system - new_system)
    )

    # Generate unified diff
    old_lines = old.content.splitlines(keepends=True)
    new_lines = new.content.splitlines(keepends=True)

    unified = list(unified_diff(
        old_lines, new_lines,
        fromfile=f"v{old.version}",
        tofile=f"v{new.version}",
    ))
    diff.unified_diff = "".join(unified[:500])  # Limit size

    # Count total changes
    diff.total_changes = (
        len(diff.added_sections) +
        len(diff.removed_sections) +
        len(diff.persona_instruction_changes) +
        len(diff.length_rule_changes) +
        len(diff.system_rule_changes)
    )

    return diff


def calculate_drift_score(diff_result: SnapshotDiff) -> int:
    """
    Calculate drift score from 0-100.

    Scoring factors:
    - Section changes: High weight
    - Token variance: Medium weight
    - Instruction changes: High weight
    - System rule changes: Very high weight

    Args:
        diff_result: SnapshotDiff to analyze

    Returns:
        Drift score 0-100 (0 = no change, 100 = radical rewrite)
    """
    score = 0.0

    # Section changes (max 30 points)
    section_score = (
        len(diff_result.added_sections) * 5 +
        len(diff_result.removed_sections) * 8  # Removals are more impactful
    )
    score += min(section_score, 30)

    # Token variance (max 15 points)
    variance_abs = abs(diff_result.token_variance)
    if variance_abs > 0.5:  # >50% change
        score += 15
    elif variance_abs > 0.25:  # >25% change
        score += 10
    elif variance_abs > 0.1:  # >10% change
        score += 5

    # Persona instruction changes (max 20 points)
    persona_score = len(diff_result.persona_instruction_changes) * 4
    score += min(persona_score, 20)

    # Length rule changes (max 15 points)
    length_score = len(diff_result.length_rule_changes) * 3
    score += min(length_score, 15)

    # System rule changes (max 20 points)
    system_score = len(diff_result.system_rule_changes) * 5
    score += min(system_score, 20)

    return min(int(score), 100)


def categorize_drift(score: int) -> str:
    """Categorize drift score into severity levels."""
    if score >= PROMPT_DRIFT_THRESHOLD_CRITICAL:
        return "CRITICAL"
    elif score >= PROMPT_DRIFT_THRESHOLD_HIGH:
        return "HIGH"
    elif score >= PROMPT_DRIFT_THRESHOLD_MEDIUM:
        return "MEDIUM"
    elif score >= PROMPT_DRIFT_THRESHOLD_LOW:
        return "LOW"
    else:
        return "MINIMAL"


def store_drift_result(
    prompt_file: str,
    drift_score: int,
    diff_summary: Optional[Dict[str, Any]] = None,
    details: Optional[List[str]] = None,
) -> DriftResult:
    """
    Store drift analysis result for dashboard and monitoring.

    Args:
        prompt_file: Prompt file that was analyzed
        drift_score: Calculated drift score
        diff_summary: Optional summary of differences
        details: Optional list of detail messages

    Returns:
        Stored DriftResult
    """
    result = DriftResult(
        prompt_file=prompt_file,
        drift_score=drift_score,
        drift_category=categorize_drift(drift_score),
        timestamp=datetime.now(),
        diff_summary=diff_summary or {},
        details=details or [],
    )

    if not PROMPT_DRAFT_MODE:
        _store_drift_result(result)

    return result


def _store_drift_result(result: DriftResult) -> bool:
    """Store drift result to persistent storage."""
    try:
        with _storage_lock:
            drift_path = _get_drift_results_path()
            safe_name = _sanitize_filename(result.prompt_file)

            # Store latest result
            latest_file = drift_path / f"{safe_name}_drift_latest.json"

            # Store timestamped result
            ts = result.timestamp.strftime("%Y%m%d_%H%M%S")
            history_file = drift_path / f"{safe_name}_drift_{ts}.json"

            data = asdict(result)
            data["timestamp"] = result.timestamp.isoformat()

            for file_path in [latest_file, history_file]:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            return True

    except Exception as e:
        log.error(f"Failed to store drift result: {e}")
        return False


def get_latest_drift_result(prompt_file: str) -> Optional[DriftResult]:
    """Get the latest drift result for a prompt file."""
    try:
        drift_path = _get_drift_results_path()
        safe_name = _sanitize_filename(prompt_file)
        latest_file = drift_path / f"{safe_name}_drift_latest.json"

        if not latest_file.exists():
            return None

        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return DriftResult(
            prompt_file=data.get("prompt_file", prompt_file),
            drift_score=data.get("drift_score", 0),
            drift_category=data.get("drift_category", "MINIMAL"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            diff_summary=data.get("diff_summary", {}),
            details=data.get("details", []),
        )

    except Exception as e:
        log.warning(f"Failed to load drift result for {prompt_file}: {e}")
        return None


def get_all_drift_results() -> List[DriftResult]:
    """Get all latest drift results."""
    results = []

    try:
        drift_path = _get_drift_results_path()
        for file_path in drift_path.glob("*_drift_latest.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            results.append(DriftResult(
                prompt_file=data.get("prompt_file", ""),
                drift_score=data.get("drift_score", 0),
                drift_category=data.get("drift_category", "MINIMAL"),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
                diff_summary=data.get("diff_summary", {}),
                details=data.get("details", []),
            ))

    except Exception as e:
        log.error(f"Failed to load drift results: {e}")

    return results


def rollback_to_snapshot(prompt_file: str, version: int) -> Optional[PromptSnapshot]:
    """
    Rollback a prompt to a previous snapshot version.

    Args:
        prompt_file: Prompt file to rollback
        version: Version number to rollback to

    Returns:
        The restored snapshot or None if not found
    """
    try:
        snapshots_path = _get_snapshots_path()
        safe_name = _sanitize_filename(prompt_file)
        versioned_file = snapshots_path / f"{safe_name}_v{version}.json"

        if not versioned_file.exists():
            log.warning(f"Snapshot version {version} not found for {prompt_file}")
            return None

        with open(versioned_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        snapshot = PromptSnapshot(
            prompt_file=data.get("prompt_file", prompt_file),
            content=data.get("content", ""),
            content_hash=data.get("content_hash", ""),
            commit_id=data.get("commit_id"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            version=data.get("version", version),
            metadata=data.get("metadata", {}),
            sections=data.get("sections", []),
            token_count=data.get("token_count", 0),
            persona_instructions=data.get("persona_instructions", []),
            length_rules=data.get("length_rules", []),
            system_rules=data.get("system_rules", []),
        )

        # Set as latest
        if not PROMPT_DRAFT_MODE:
            latest_file = snapshots_path / f"{safe_name}_latest.json"
            with open(latest_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        log.info(f"Rolled back {prompt_file} to version {version}")
        return snapshot

    except Exception as e:
        log.error(f"Failed to rollback {prompt_file}: {e}")
        return None
