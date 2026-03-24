"""
FIX-503A: Metrics Unification Issue Documentation

This file documents the two separate warning systems that cause
Pipeline grade=A while 70+ actual warnings exist.
"""

# =============================================================================
# SYSTEM 1: ReportErrorGate (Pipeline Errors)
# Source: gpt_analyze.py:638-785
# =============================================================================

class ReportErrorGate:
    """
    Tracks errors during report GENERATION:
    - Fallback usage (when LLM fails)
    - Heals (when text healing is applied)
    - Location removals
    - Prompt failures

    THIS is what's used for PIPELINE_GRADE!
    """
    def __init__(self):
        self.warnings = []  # ← These warnings go to PIPELINE_WARNINGS_COUNT
        self.fallback_count = 0
        self.heals_count = 0
        # ...

# gpt_analyze.py:13867-13884 - Pipeline Grade Calculation
"""
sections["PIPELINE_WARNINGS_COUNT"] = len(error_gate.warnings)  # ← Only pipeline warnings!
sections["PIPELINE_GRADE"] = "A" if (
    len(error_gate.warnings) == 0 and
    error_gate.fallback_count == 0 and
    error_gate.heals_count == 0
) else "B" if ... else "C"
"""

# =============================================================================
# SYSTEM 2: ReportValidator (Content Quality)
# Source: services/report_validator.py:615-1137
# =============================================================================

class ReportValidator:
    """
    Validates CONTENT quality after generation:
    - Section word counts
    - Placeholder detection
    - Template phrase detection
    - Redundancy checks

    These warnings are NOT included in PIPELINE_GRADE!
    """
    def __init__(self, sections, company_size):
        self.errors = []  # ← These errors NOT in pipeline metrics!

    def validate(self):
        self._check_empty_or_short_sections()  # Generates SECTION_TOO_SHORT
        self._check_placeholders()
        # ...

# =============================================================================
# SYSTEM 3: ConsistencyEngine (G22)
# Source: services/consistency_engine.py:130-252
# =============================================================================

class ConsistencyReport:
    """
    Cross-section consistency validation:
    - KPI consistency (ROI, Payback, Time Savings)
    - Tools consistency
    - Narrative coherence

    Grade D/F NOT reflected in PIPELINE_GRADE!
    """
    issues: list  # ← Not in pipeline metrics (ConsistencyIssue defined elsewhere)
    grade: str  # "A" to "F"

# =============================================================================
# THE FIX: Unified QualityMetrics
# =============================================================================

from dataclasses import dataclass

@dataclass
class QualityMetrics:
    """
    Unified quality metrics aggregating all sources.
    """
    # Pipeline (error_gate)
    pipeline_warnings: int = 0
    pipeline_fallbacks: int = 0
    pipeline_heals: int = 0

    # Validator (ReportValidator)
    validator_warnings: int = 0
    validator_errors: int = 0

    # Consistency (G22)
    consistency_score: float = 100.0
    consistency_grade: str = "A"

    @property
    def total_warnings(self) -> int:
        return self.pipeline_warnings + self.validator_warnings

    @property
    def overall_grade(self) -> str:
        """
        Calculate unified grade considering ALL sources.
        """
        # Hard fail conditions
        if self.validator_errors > 0:
            return "F"
        if self.consistency_grade in ("D", "F"):
            return max("C", self.consistency_grade)  # At least C

        # Warning-based grading
        if self.total_warnings == 0 and self.consistency_grade == "A":
            return "A"
        elif self.total_warnings <= 5 and self.consistency_grade in ("A", "B"):
            return "B"
        elif self.total_warnings <= 20:
            return "C"
        else:
            return "D"

# Integration point in gpt_analyze.py:
"""
# After validation, BEFORE setting PIPELINE_GRADE:

validator = ReportValidator(sections, company_size)
validator.validate()

consistency_report = check_consistency(sections, briefing)

# Create unified metrics
quality = QualityMetrics(
    pipeline_warnings=len(error_gate.warnings),
    pipeline_fallbacks=error_gate.fallback_count,
    pipeline_heals=error_gate.heals_count,
    validator_warnings=sum(1 for e in validator.errors if e.severity == "WARNING"),
    validator_errors=sum(1 for e in validator.errors if e.severity == "ERROR"),
    consistency_score=consistency_report.score,
    consistency_grade=consistency_report.grade,
)

# Use unified grade
sections["PIPELINE_GRADE"] = quality.overall_grade
sections["PIPELINE_WARNINGS_COUNT"] = quality.total_warnings
"""
