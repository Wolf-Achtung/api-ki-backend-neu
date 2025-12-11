# -*- coding: utf-8 -*-
"""
SPRINT N3.6 PACKAGE A: Shared Type Definitions.

Provides consistent type definitions across all engines to ensure
mypy stability and reduce type-related inconsistencies.

Version: 1.0.0 (N3.6 - PLATIN++ v4.21)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# =============================================================================
# CORE TYPE ALIASES
# =============================================================================

# Universal section dictionary type - accepts any value type
# Used across all engines for section content storage
SectionDict = Dict[str, Any]

# Briefing dictionary - company/context data
BriefingDict = Dict[str, Any]

# LLM response dictionary
LLMResponseDict = Dict[str, Any]

# Engine output with report metadata
EngineResult = Tuple[SectionDict, "EngineReport"]


# =============================================================================
# ENGINE REPORT DATACLASS
# =============================================================================

@dataclass
class EngineReport:
    """
    Standard report structure for all engines.

    Provides consistent metadata across engine outputs for
    monitoring, debugging, and quality assurance.
    """
    engine_id: str
    success: bool = True
    sections_processed: int = 0
    sections_healed: int = 0
    issues_found: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    healing_applied: bool = False

    def add_issue(self, issue: str) -> None:
        """Add an issue to the report."""
        self.issues_found.append(issue)

    def add_warning(self, warning: str) -> None:
        """Add a warning to the report."""
        self.warnings.append(warning)

    def set_metric(self, key: str, value: Any) -> None:
        """Set a metric value."""
        self.metrics[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "sections_processed": self.sections_processed,
            "sections_healed": self.sections_healed,
            "issues_found": self.issues_found,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "healing_applied": self.healing_applied,
        }


# =============================================================================
# HEALING FLAGS STRUCTURE
# =============================================================================

# Engine IDs for healing flags
ENGINE_ID_BC = "BC"  # Business Case
ENGINE_ID_RECO = "RECO"  # Recommendations
ENGINE_ID_RISK = "RISK"  # Risk Analysis
ENGINE_ID_VENDOR = "VENDOR"  # Vendor Audit
ENGINE_ID_AUTO = "AUTO"  # Automation/Roadmap
ENGINE_ID_BENCH = "BENCH"  # Benchmark
ENGINE_ID_TONE = "TONE"  # Tone Harmonizer

# All engine IDs
ALL_ENGINE_IDS = [
    ENGINE_ID_BC,
    ENGINE_ID_RECO,
    ENGINE_ID_RISK,
    ENGINE_ID_VENDOR,
    ENGINE_ID_AUTO,
    ENGINE_ID_BENCH,
    ENGINE_ID_TONE,
]


@dataclass
class HealingFlags:
    """
    N3.6: Unified healing flags structure.

    Tracks which engines have performed healing operations
    to prevent G22 from re-flagging healed issues.
    """
    BC: bool = False
    RECO: bool = False
    RISK: bool = False
    VENDOR: bool = False
    AUTO: bool = False
    BENCH: bool = False
    TONE: bool = False

    def set_healed(self, engine_id: str) -> None:
        """Mark an engine as having performed healing."""
        if hasattr(self, engine_id):
            setattr(self, engine_id, True)

    def is_healed(self, engine_id: str) -> bool:
        """Check if an engine has performed healing."""
        return getattr(self, engine_id, False)

    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary."""
        return {
            "BC": self.BC,
            "RECO": self.RECO,
            "RISK": self.RISK,
            "VENDOR": self.VENDOR,
            "AUTO": self.AUTO,
            "BENCH": self.BENCH,
            "TONE": self.TONE,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> "HealingFlags":
        """Create from dictionary."""
        flags = cls()
        for key, value in data.items():
            if hasattr(flags, key):
                setattr(flags, key, value)
        return flags


def get_healing_flags(sections: SectionDict) -> HealingFlags:
    """
    N3.6: Extract healing flags from sections dict.

    Supports both legacy format (_bc_healed, _reco_healed) and
    new unified format (_healed dict).

    Args:
        sections: Section dictionary

    Returns:
        HealingFlags instance
    """
    flags = HealingFlags()

    # Check for unified _healed dict (N3.6+)
    healed_dict = sections.get("_healed", {})
    if isinstance(healed_dict, dict):
        flags = HealingFlags.from_dict(healed_dict)

    # Also check legacy flags for backwards compatibility
    if sections.get("_bc_healed"):
        flags.BC = True
    if sections.get("_reco_healed"):
        flags.RECO = True
    if sections.get("_bc_consistency_normalized"):
        flags.BC = True

    return flags


def set_healing_flag(
    sections: SectionDict,
    engine_id: str,
    healed: bool = True
) -> None:
    """
    N3.6: Set a healing flag in sections dict.

    Sets both unified format and legacy format for compatibility.

    Args:
        sections: Section dictionary to modify
        engine_id: Engine ID (BC, RECO, RISK, etc.)
        healed: Whether healing was performed
    """
    # Ensure _healed dict exists
    if "_healed" not in sections:
        sections["_healed"] = {}

    # Set in unified format
    if isinstance(sections["_healed"], dict):
        sections["_healed"][engine_id] = healed

    # Also set legacy flags for backwards compatibility
    if engine_id == ENGINE_ID_BC:
        sections["_bc_healed"] = healed
        sections["_bc_consistency_normalized"] = healed
    elif engine_id == ENGINE_ID_RECO:
        sections["_reco_healed"] = healed


# =============================================================================
# EXTENSION CONFIGURATION
# =============================================================================

@dataclass
class ExtensionConfig:
    """
    Configuration for section extension operations.

    Used by extension_manager to control how sections are expanded.
    """
    target_words: int = 200
    min_words: int = 100
    max_words: int = 500
    style: str = "consulting_structured"
    depth_level: int = 2
    branch: str = ""
    company_size: str = "team"
    tone: str = "analytical_decisive"
    allow_fallback: bool = True
    remove_gpt_flair: bool = True


# =============================================================================
# CONSISTENCY VALIDATION
# =============================================================================

@dataclass
class ConsistencyIssue:
    """
    Represents a consistency issue found during validation.
    """
    code: str  # e.g., "BC_001", "RECO_002"
    severity: str  # "error", "warning", "info"
    message: str
    section: str = ""
    can_heal: bool = False
    healed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "section": self.section,
            "can_heal": self.can_heal,
            "healed": self.healed,
        }
