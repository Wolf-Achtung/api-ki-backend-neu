# -*- coding: utf-8 -*-
"""
SPRINT N3.9 PACKAGE B: Audit & Traceability Layer (KI-Act / ISO 42001).

Enterprise audit trail for AI operations:
- Complete reasoning graph for all engines
- SHA256 hash chain for immutability
- Input/output data hashing
- Model parameters tracking
- Compliance-ready audit reports

Version: 1.0.0 (N3.9 - PLATIN++ v4.28)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# Type aliases
AuditDict = Dict[str, Any]
HashValue = str


# =============================================================================
# CONFIGURATION
# =============================================================================

class AuditLevel(Enum):
    """Audit detail level."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    FULL = "full"


class EngineType(Enum):
    """Types of engines that can be audited."""
    LLM_CALL = "llm_call"
    CONSISTENCY_CHECK = "consistency_check"
    INTEGRITY_VALIDATION = "integrity_validation"
    NARRATIVE_ANALYSIS = "narrative_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    TENANT_PROCESSING = "tenant_processing"
    SAFETY_TUNING = "safety_tuning"
    REDUNDANCY_DETECTION = "redundancy_detection"
    LAYOUT_PROCESSING = "layout_processing"
    BUSINESS_CASE = "business_case"
    RISK_ANALYSIS = "risk_analysis"
    RESEARCH = "research"


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    KI_ACT = "ki_act"
    ISO_42001 = "iso_42001"
    GDPR = "gdpr"
    SOC2 = "soc2"


# Audit configuration
AUDIT_CONFIG: AuditDict = {
    "hash_algorithm": "sha256",
    "chain_validation_enabled": True,
    "max_reasoning_length": 10000,
    "retention_days": 365,
    "compress_large_entries": True,
    "compression_threshold_bytes": 50000,
}

# Fields to exclude from hashing (sensitive/variable data)
HASH_EXCLUDE_FIELDS = [
    "timestamp",
    "duration_ms",
    "trace_id",
    "parent_hash",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class AuditEntry:
    """Single audit trail entry."""
    entry_id: str
    engine_type: EngineType
    engine_name: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Input/Output tracking
    input_data_hash: HashValue = ""
    output_data_hash: HashValue = ""
    input_size_bytes: int = 0
    output_size_bytes: int = 0

    # Model parameters (for LLM calls)
    model_used: str = ""
    model_version: str = ""
    temperature: float = 0.0
    max_tokens: int = 0
    top_p: float = 1.0

    # Reasoning and results
    reasoning_summary: str = ""
    reasoning_length: int = 0
    result_status: str = "success"
    error_message: str = ""

    # Quality metrics
    consistency_alignment_score: float = 100.0
    confidence_score: float = 100.0

    # Fallback and healing
    fallback_used: bool = False
    fallback_reason: str = ""
    healing_steps: List[str] = field(default_factory=list)
    healing_count: int = 0

    # Chain
    parent_hash: HashValue = ""
    entry_hash: HashValue = ""

    # Metadata
    duration_ms: int = 0
    trace_id: str = ""
    tenant_id: str = ""

    def compute_hash(self) -> HashValue:
        """Compute SHA256 hash of this entry."""
        # Serialize entry data (excluding variable fields)
        data = {
            "entry_id": self.entry_id,
            "engine_type": self.engine_type.value,
            "engine_name": self.engine_name,
            "input_data_hash": self.input_data_hash,
            "output_data_hash": self.output_data_hash,
            "model_used": self.model_used,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "result_status": self.result_status,
            "fallback_used": self.fallback_used,
            "healing_steps": self.healing_steps,
            "parent_hash": self.parent_hash,
        }

        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def to_dict(self) -> AuditDict:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "engine_type": self.engine_type.value,
            "engine_name": self.engine_name,
            "timestamp": self.timestamp,
            "input_data_hash": self.input_data_hash,
            "output_data_hash": self.output_data_hash,
            "input_size_bytes": self.input_size_bytes,
            "output_size_bytes": self.output_size_bytes,
            "model_used": self.model_used,
            "model_version": self.model_version,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "reasoning_summary": self.reasoning_summary,
            "reasoning_length": self.reasoning_length,
            "result_status": self.result_status,
            "error_message": self.error_message,
            "consistency_alignment_score": self.consistency_alignment_score,
            "confidence_score": self.confidence_score,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "healing_steps": self.healing_steps,
            "healing_count": self.healing_count,
            "parent_hash": self.parent_hash,
            "entry_hash": self.entry_hash,
            "duration_ms": self.duration_ms,
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
        }


@dataclass
class AuditReport:
    """Complete audit report for a report generation."""
    report_id: str
    tenant_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: str = ""

    # Entries
    entries: List[AuditEntry] = field(default_factory=list)
    entry_count: int = 0

    # Chain integrity
    chain_valid: bool = True
    chain_root_hash: HashValue = ""
    chain_final_hash: HashValue = ""

    # Summary statistics
    total_llm_calls: int = 0
    total_fallbacks: int = 0
    total_healing_operations: int = 0
    total_duration_ms: int = 0

    # Quality summary
    average_consistency_score: float = 100.0
    average_confidence_score: float = 100.0
    min_consistency_score: float = 100.0

    # Models used
    models_used: List[str] = field(default_factory=list)

    # Compliance
    compliance_frameworks: List[str] = field(default_factory=list)
    compliance_status: str = "compliant"
    compliance_notes: List[str] = field(default_factory=list)

    def add_entry(self, entry: AuditEntry) -> None:
        """Add an entry to the audit report."""
        # Set parent hash for chain
        if self.entries:
            entry.parent_hash = self.entries[-1].entry_hash
        else:
            entry.parent_hash = "genesis"

        # Compute entry hash
        entry.entry_hash = entry.compute_hash()

        self.entries.append(entry)
        self.entry_count = len(self.entries)

        # Update statistics
        if entry.engine_type == EngineType.LLM_CALL:
            self.total_llm_calls += 1
        if entry.fallback_used:
            self.total_fallbacks += 1
        self.total_healing_operations += entry.healing_count
        self.total_duration_ms += entry.duration_ms

        # Update model list
        if entry.model_used and entry.model_used not in self.models_used:
            self.models_used.append(entry.model_used)

        # Update chain hashes
        if not self.chain_root_hash:
            self.chain_root_hash = entry.entry_hash
        self.chain_final_hash = entry.entry_hash

        log.debug("[N3.9-Audit] Added entry: %s (%s)", entry.entry_id, entry.engine_name)

    def validate_chain(self) -> Tuple[bool, str]:
        """
        Validate the hash chain integrity.

        Returns:
            Tuple of (valid: bool, message: str)
        """
        if not self.entries:
            return True, "No entries to validate"

        # Check genesis
        if self.entries[0].parent_hash != "genesis":
            return False, "Invalid genesis entry"

        # Validate chain
        for i, entry in enumerate(self.entries):
            # Recompute hash
            computed_hash = entry.compute_hash()
            if computed_hash != entry.entry_hash:
                return False, f"Hash mismatch at entry {i}: {entry.entry_id}"

            # Check parent link
            if i > 0:
                if entry.parent_hash != self.entries[i - 1].entry_hash:
                    return False, f"Chain break at entry {i}: {entry.entry_id}"

        self.chain_valid = True
        return True, "Chain valid"

    def compute_statistics(self) -> None:
        """Compute summary statistics from entries."""
        if not self.entries:
            return

        consistency_scores = [e.consistency_alignment_score for e in self.entries]
        confidence_scores = [e.confidence_score for e in self.entries]

        self.average_consistency_score = sum(consistency_scores) / len(consistency_scores)
        self.average_confidence_score = sum(confidence_scores) / len(confidence_scores)
        self.min_consistency_score = min(consistency_scores)

    def finalize(self) -> None:
        """Finalize the audit report."""
        self.completed_at = datetime.utcnow().isoformat()
        self.compute_statistics()
        valid, _ = self.validate_chain()
        self.chain_valid = valid

    def to_dict(self) -> AuditDict:
        """Convert to dictionary for JSON serialization."""
        return {
            "report_id": self.report_id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "entry_count": self.entry_count,
            "entries": [e.to_dict() for e in self.entries],
            "chain_valid": self.chain_valid,
            "chain_root_hash": self.chain_root_hash,
            "chain_final_hash": self.chain_final_hash,
            "total_llm_calls": self.total_llm_calls,
            "total_fallbacks": self.total_fallbacks,
            "total_healing_operations": self.total_healing_operations,
            "total_duration_ms": self.total_duration_ms,
            "average_consistency_score": round(self.average_consistency_score, 2),
            "average_confidence_score": round(self.average_confidence_score, 2),
            "min_consistency_score": round(self.min_consistency_score, 2),
            "models_used": self.models_used,
            "compliance_frameworks": self.compliance_frameworks,
            "compliance_status": self.compliance_status,
            "compliance_notes": self.compliance_notes,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# =============================================================================
# HASH UTILITIES
# =============================================================================

def compute_data_hash(data: Any) -> HashValue:
    """
    Compute SHA256 hash of any data.

    Args:
        data: Data to hash (will be JSON serialized)

    Returns:
        SHA256 hash string
    """
    if data is None:
        return hashlib.sha256(b"null").hexdigest()

    try:
        if isinstance(data, str):
            json_str = data
        elif isinstance(data, bytes):
            return hashlib.sha256(data).hexdigest()
        else:
            json_str = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    except Exception as e:
        log.warning("[N3.9-Audit] Hash computation failed: %s", e)
        return hashlib.sha256(str(data).encode("utf-8")).hexdigest()


def compute_data_size(data: Any) -> int:
    """
    Compute size of data in bytes.

    Args:
        data: Data to measure

    Returns:
        Size in bytes
    """
    if data is None:
        return 0
    try:
        if isinstance(data, str):
            return len(data.encode("utf-8"))
        elif isinstance(data, bytes):
            return len(data)
        else:
            return len(json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"))
    except Exception:
        return 0


# =============================================================================
# AUDIT TRACE ENGINE
# =============================================================================

class AuditTraceEngine:
    """
    Central audit trace engine.

    Manages audit reports and provides hooks for engine integration.
    """

    _instance: Optional["AuditTraceEngine"] = None
    _active_reports: Dict[str, AuditReport] = {}
    _completed_reports: Dict[str, AuditReport] = {}
    _entry_counter: int = 0

    def __new__(cls) -> "AuditTraceEngine":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active_reports = {}
            cls._instance._completed_reports = {}
            cls._instance._entry_counter = 0
        return cls._instance

    def start_report(self, report_id: str, tenant_id: str = "") -> AuditReport:
        """
        Start a new audit report.

        Args:
            report_id: Report identifier
            tenant_id: Optional tenant identifier

        Returns:
            New AuditReport instance
        """
        report = AuditReport(report_id=report_id, tenant_id=tenant_id)
        self._active_reports[report_id] = report
        log.info("[N3.9-Audit] Started audit report: %s", report_id)
        return report

    def get_active_report(self, report_id: str) -> Optional[AuditReport]:
        """Get an active audit report by ID."""
        return self._active_reports.get(report_id)

    def create_entry(
        self,
        report_id: str,
        engine_type: EngineType,
        engine_name: str,
        input_data: Any = None,
        trace_id: str = "",
    ) -> AuditEntry:
        """
        Create a new audit entry.

        Args:
            report_id: Report identifier
            engine_type: Type of engine
            engine_name: Name of the engine
            input_data: Input data for hashing
            trace_id: Optional trace identifier

        Returns:
            New AuditEntry instance
        """
        self._entry_counter += 1
        entry_id = f"{report_id}_{self._entry_counter:04d}"

        entry = AuditEntry(
            entry_id=entry_id,
            engine_type=engine_type,
            engine_name=engine_name,
            input_data_hash=compute_data_hash(input_data),
            input_size_bytes=compute_data_size(input_data),
            trace_id=trace_id,
        )

        report = self._active_reports.get(report_id)
        if report:
            entry.tenant_id = report.tenant_id

        return entry

    def complete_entry(
        self,
        report_id: str,
        entry: AuditEntry,
        output_data: Any = None,
        reasoning: str = "",
        duration_ms: int = 0,
    ) -> None:
        """
        Complete an audit entry and add to report.

        Args:
            report_id: Report identifier
            entry: Audit entry to complete
            output_data: Output data for hashing
            reasoning: Reasoning summary
            duration_ms: Duration in milliseconds
        """
        entry.output_data_hash = compute_data_hash(output_data)
        entry.output_size_bytes = compute_data_size(output_data)
        entry.reasoning_summary = reasoning[:AUDIT_CONFIG["max_reasoning_length"]]
        entry.reasoning_length = len(reasoning)
        entry.duration_ms = duration_ms

        report = self._active_reports.get(report_id)
        if report:
            report.add_entry(entry)
        else:
            log.warning("[N3.9-Audit] No active report for: %s", report_id)

    def record_llm_call(
        self,
        report_id: str,
        model: str,
        input_data: Any,
        output_data: Any,
        temperature: float = 0.0,
        max_tokens: int = 0,
        duration_ms: int = 0,
        reasoning: str = "",
    ) -> None:
        """
        Record an LLM call for audit.

        Args:
            report_id: Report identifier
            model: Model name/version
            input_data: Input to the model
            output_data: Output from the model
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            duration_ms: Call duration
            reasoning: Optional reasoning summary
        """
        entry = self.create_entry(
            report_id=report_id,
            engine_type=EngineType.LLM_CALL,
            engine_name=f"llm_{model}",
            input_data=input_data,
        )

        entry.model_used = model
        entry.temperature = temperature
        entry.max_tokens = max_tokens

        self.complete_entry(
            report_id=report_id,
            entry=entry,
            output_data=output_data,
            reasoning=reasoning,
            duration_ms=duration_ms,
        )

    def record_fallback(
        self,
        report_id: str,
        engine_name: str,
        reason: str,
        fallback_data: Any = None,
    ) -> None:
        """
        Record a fallback event.

        Args:
            report_id: Report identifier
            engine_name: Engine that triggered fallback
            reason: Reason for fallback
            fallback_data: Fallback data used
        """
        entry = self.create_entry(
            report_id=report_id,
            engine_type=EngineType.LLM_CALL,
            engine_name=f"fallback_{engine_name}",
        )

        entry.fallback_used = True
        entry.fallback_reason = reason
        entry.result_status = "fallback"

        self.complete_entry(
            report_id=report_id,
            entry=entry,
            output_data=fallback_data,
            reasoning=f"Fallback triggered: {reason}",
        )

    def record_healing(
        self,
        report_id: str,
        engine_name: str,
        healing_steps: List[str],
        before_data: Any = None,
        after_data: Any = None,
    ) -> None:
        """
        Record a healing operation.

        Args:
            report_id: Report identifier
            engine_name: Engine that performed healing
            healing_steps: List of healing steps performed
            before_data: Data before healing
            after_data: Data after healing
        """
        entry = self.create_entry(
            report_id=report_id,
            engine_type=EngineType.CONSISTENCY_CHECK,
            engine_name=f"healing_{engine_name}",
            input_data=before_data,
        )

        entry.healing_steps = healing_steps
        entry.healing_count = len(healing_steps)

        self.complete_entry(
            report_id=report_id,
            entry=entry,
            output_data=after_data,
            reasoning=f"Healing performed: {', '.join(healing_steps)}",
        )

    def record_consistency_check(
        self,
        report_id: str,
        engine_name: str,
        input_data: Any,
        score: float,
        issues: List[str],
        duration_ms: int = 0,
    ) -> None:
        """
        Record a consistency check.

        Args:
            report_id: Report identifier
            engine_name: Engine name
            input_data: Data checked
            score: Consistency score
            issues: List of issues found
            duration_ms: Check duration
        """
        entry = self.create_entry(
            report_id=report_id,
            engine_type=EngineType.CONSISTENCY_CHECK,
            engine_name=engine_name,
            input_data=input_data,
        )

        entry.consistency_alignment_score = score

        self.complete_entry(
            report_id=report_id,
            entry=entry,
            output_data={"score": score, "issues": issues},
            reasoning=f"Consistency check: {len(issues)} issues, score={score}",
            duration_ms=duration_ms,
        )

    def finalize_report(self, report_id: str) -> Optional[AuditReport]:
        """
        Finalize an audit report.

        Args:
            report_id: Report identifier

        Returns:
            Finalized AuditReport or None if not found
        """
        report = self._active_reports.pop(report_id, None)
        if report:
            report.finalize()
            self._completed_reports[report_id] = report
            log.info(
                "[N3.9-Audit] Finalized report %s: %d entries, chain_valid=%s",
                report_id,
                report.entry_count,
                report.chain_valid,
            )
            return report
        return None

    def get_completed_report(self, report_id: str) -> Optional[AuditReport]:
        """Get a completed audit report."""
        return self._completed_reports.get(report_id)

    def export_report(self, report_id: str, path: str) -> bool:
        """
        Export audit report to file.

        Args:
            report_id: Report identifier
            path: Output file path

        Returns:
            True if exported successfully
        """
        report = self._completed_reports.get(report_id) or self._active_reports.get(report_id)
        if not report:
            log.warning("[N3.9-Audit] Report not found: %s", report_id)
            return False

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report.to_json())
            log.info("[N3.9-Audit] Exported report to: %s", path)
            return True
        except Exception as e:
            log.error("[N3.9-Audit] Export failed: %s", e)
            return False


# Singleton instance
_engine = AuditTraceEngine()


def get_audit_engine() -> AuditTraceEngine:
    """Get the global audit trace engine instance."""
    return _engine


# =============================================================================
# COMPLIANCE HELPERS
# =============================================================================

def check_ki_act_compliance(report: AuditReport) -> Tuple[bool, List[str]]:
    """
    Check KI-Act compliance for an audit report.

    Args:
        report: Audit report to check

    Returns:
        Tuple of (compliant: bool, notes: List[str])
    """
    notes: List[str] = []

    # Check chain integrity
    if not report.chain_valid:
        notes.append("KI-ACT-001: Hash chain integrity check failed")

    # Check reasoning documentation
    entries_without_reasoning = [
        e for e in report.entries
        if e.engine_type == EngineType.LLM_CALL and not e.reasoning_summary
    ]
    if entries_without_reasoning:
        notes.append(f"KI-ACT-002: {len(entries_without_reasoning)} LLM calls without reasoning documentation")

    # Check fallback documentation
    fallbacks_without_reason = [
        e for e in report.entries
        if e.fallback_used and not e.fallback_reason
    ]
    if fallbacks_without_reason:
        notes.append(f"KI-ACT-003: {len(fallbacks_without_reason)} fallbacks without documented reason")

    # Check model transparency
    if not report.models_used:
        notes.append("KI-ACT-004: No models documented in audit trail")

    compliant = len(notes) == 0
    return compliant, notes


def check_iso_42001_compliance(report: AuditReport) -> Tuple[bool, List[str]]:
    """
    Check ISO 42001 compliance for an audit report.

    Args:
        report: Audit report to check

    Returns:
        Tuple of (compliant: bool, notes: List[str])
    """
    notes: List[str] = []

    # Check completeness
    if report.entry_count == 0:
        notes.append("ISO-42001-001: No audit entries recorded")

    # Check timestamps
    entries_without_timestamp = [
        e for e in report.entries if not e.timestamp
    ]
    if entries_without_timestamp:
        notes.append(f"ISO-42001-002: {len(entries_without_timestamp)} entries without timestamps")

    # Check data hashing
    entries_without_hash = [
        e for e in report.entries
        if not e.input_data_hash or not e.output_data_hash
    ]
    if entries_without_hash:
        notes.append(f"ISO-42001-003: {len(entries_without_hash)} entries with incomplete data hashing")

    compliant = len(notes) == 0
    return compliant, notes


def generate_compliance_report(
    audit_report: AuditReport,
    frameworks: Optional[List[ComplianceFramework]] = None,
) -> AuditDict:
    """
    Generate a compliance report for specified frameworks.

    Args:
        audit_report: Audit report to analyze
        frameworks: List of compliance frameworks to check

    Returns:
        Compliance report dictionary
    """
    if frameworks is None:
        frameworks = [ComplianceFramework.KI_ACT, ComplianceFramework.ISO_42001]

    result: AuditDict = {
        "report_id": audit_report.report_id,
        "checked_at": datetime.utcnow().isoformat(),
        "frameworks": {},
        "overall_compliant": True,
    }

    for framework in frameworks:
        if framework == ComplianceFramework.KI_ACT:
            compliant, notes = check_ki_act_compliance(audit_report)
        elif framework == ComplianceFramework.ISO_42001:
            compliant, notes = check_iso_42001_compliance(audit_report)
        else:
            compliant, notes = True, []

        result["frameworks"][framework.value] = {
            "compliant": compliant,
            "notes": notes,
        }

        if not compliant:
            result["overall_compliant"] = False

    return result


# =============================================================================
# CONTEXT MANAGER FOR AUDITING
# =============================================================================

class AuditContext:
    """
    Context manager for auditing engine operations.

    Usage:
        with AuditContext(report_id, EngineType.LLM_CALL, "gpt4") as ctx:
            result = call_llm(...)
            ctx.set_output(result)
            ctx.set_model("gpt-4", temperature=0.1)
    """

    def __init__(
        self,
        report_id: str,
        engine_type: EngineType,
        engine_name: str,
        input_data: Any = None,
    ):
        self.report_id = report_id
        self.engine_type = engine_type
        self.engine_name = engine_name
        self.input_data = input_data
        self.entry: Optional[AuditEntry] = None
        self.output_data: Any = None
        self.reasoning: str = ""
        self.start_time: float = 0

    def __enter__(self) -> "AuditContext":
        engine = get_audit_engine()
        self.entry = engine.create_entry(
            report_id=self.report_id,
            engine_type=self.engine_type,
            engine_name=self.engine_name,
            input_data=self.input_data,
        )
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.entry:
            duration_ms = int((time.time() - self.start_time) * 1000)

            if exc_type:
                self.entry.result_status = "error"
                self.entry.error_message = str(exc_val)

            engine = get_audit_engine()
            engine.complete_entry(
                report_id=self.report_id,
                entry=self.entry,
                output_data=self.output_data,
                reasoning=self.reasoning,
                duration_ms=duration_ms,
            )

    def set_output(self, data: Any) -> None:
        """Set output data."""
        self.output_data = data

    def set_reasoning(self, reasoning: str) -> None:
        """Set reasoning summary."""
        self.reasoning = reasoning

    def set_model(
        self,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 0,
    ) -> None:
        """Set model parameters."""
        if self.entry:
            self.entry.model_used = model
            self.entry.temperature = temperature
            self.entry.max_tokens = max_tokens

    def set_fallback(self, reason: str) -> None:
        """Mark as fallback."""
        if self.entry:
            self.entry.fallback_used = True
            self.entry.fallback_reason = reason
            self.entry.result_status = "fallback"

    def add_healing_step(self, step: str) -> None:
        """Add a healing step."""
        if self.entry:
            self.entry.healing_steps.append(step)
            self.entry.healing_count = len(self.entry.healing_steps)

    def set_score(self, consistency: float, confidence: float = 100.0) -> None:
        """Set quality scores."""
        if self.entry:
            self.entry.consistency_alignment_score = consistency
            self.entry.confidence_score = confidence


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AuditLevel",
    "EngineType",
    "ComplianceFramework",
    # Data classes
    "AuditEntry",
    "AuditReport",
    # Engine
    "AuditTraceEngine",
    "get_audit_engine",
    # Utilities
    "compute_data_hash",
    "compute_data_size",
    # Compliance
    "check_ki_act_compliance",
    "check_iso_42001_compliance",
    "generate_compliance_report",
    # Context manager
    "AuditContext",
]
