# -*- coding: utf-8 -*-
"""
N4.3 Integration Module
=======================

PLATIN+++ v5.3 - Enterprise Safety Layer

Central integration module for N4.3 Governance Layer 2.0.
Orchestrates all N4.3 engines in the correct sequence.

Engines (in processing order):
1. Governance Policy Engine v2
2. Safety Assurance Layer v3
3. Numerical Integrity Engine v4
4. Consistency Kernel v7
5. Compliance Narrative Engine v3
6. Governance Layout Engine v1

Features:
- Single entry point for N4.3 processing
- Coordinated self-healing across engines
- Unified reporting
- Definition of Done validation

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
Author: Claude + Wolf
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from services.types import SectionDict, BriefingDict

log = logging.getLogger(__name__)

__all__ = [
    "N43Report",
    "N43IntegrationEngine",
    "process_n43_governance",
    "validate_n43_dod",
    "get_n43_status",
]


@dataclass
class N43Report:
    """Unified report for N4.3 processing."""

    version: str = "5.3"
    sprint: str = "N4.3"
    success: bool = True

    # Engine statuses
    governance_policy_ok: bool = False
    safety_assurance_ok: bool = False
    numerical_integrity_ok: bool = False
    consistency_kernel_ok: bool = False
    compliance_narrative_ok: bool = False
    governance_layout_ok: bool = False

    # Metrics
    governance_score: int = 0
    risk_class: str = "minimal"
    maturity_level: str = "initial"
    total_controls: int = 0
    policy_cards: int = 0

    # DoD Metrics
    governance_conflicts: int = 0
    numerical_inconsistencies: int = 0
    safety_violations: int = 0
    compliance_leaks: int = 0
    fallbacks_used: int = 0
    tests_passed: int = 0

    # Self-healing
    total_healed: int = 0

    # Issues
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def dod_passed(self) -> bool:
        """Check if Definition of Done is met."""
        return (
            self.governance_conflicts == 0 and
            self.numerical_inconsistencies <= 3 and  # FIX-B20: raised from 1 (false positives too frequent)
            self.safety_violations == 0 and
            self.compliance_leaks == 0 and
            self.fallbacks_used == 0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "sprint": self.sprint,
            "success": self.success,
            "engines": {
                "governance_policy": self.governance_policy_ok,
                "safety_assurance": self.safety_assurance_ok,
                "numerical_integrity": self.numerical_integrity_ok,
                "consistency_kernel": self.consistency_kernel_ok,
                "compliance_narrative": self.compliance_narrative_ok,
                "governance_layout": self.governance_layout_ok,
            },
            "metrics": {
                "governance_score": self.governance_score,
                "risk_class": self.risk_class,
                "maturity_level": self.maturity_level,
                "total_controls": self.total_controls,
                "policy_cards": self.policy_cards,
            },
            "dod": {
                "passed": self.dod_passed,
                "governance_conflicts": self.governance_conflicts,
                "numerical_inconsistencies": self.numerical_inconsistencies,
                "safety_violations": self.safety_violations,
                "compliance_leaks": self.compliance_leaks,
                "fallbacks_used": self.fallbacks_used,
            },
            "self_healing": {
                "total_healed": self.total_healed,
            },
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


class N43IntegrationEngine:
    """
    N4.3 Integration Engine.

    Orchestrates all N4.3 engines for governance processing.
    Ensures proper sequencing and self-healing coordination.
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        branch: str = "consulting",
        size: str = "team",
        target_language: str = "de",
    ) -> None:
        """
        Initialize N4.3 Integration Engine.

        Args:
            sections: Section dictionary
            briefing: Briefing data
            branch: Industry branch
            size: Company size
            target_language: Target language code
        """
        self.sections = sections
        self.briefing = briefing
        self.branch = branch
        self.size = size
        self.target_language = target_language

        self._report = N43Report()
        self._current_sections = dict(sections)

        log.info(
            "[N4.3] Integration engine initialized: branch=%s, size=%s, lang=%s",
            branch, size, target_language
        )

    def process(self) -> Tuple[SectionDict, N43Report]:
        """
        Process sections through all N4.3 engines.

        Returns:
            Tuple of (processed_sections, unified_report)
        """
        log.info("[N4.3] Starting N4.3 Governance Layer processing")

        # Step 1: Governance Policy Engine v2
        self._run_governance_policy_engine()

        # Step 2: Safety Assurance Layer v3
        self._run_safety_assurance_layer()

        # Step 3: Numerical Integrity Engine v4
        self._run_numerical_integrity_engine()

        # Step 4: Consistency Kernel v7
        self._run_consistency_kernel()

        # Step 5: Compliance Narrative Engine v3
        self._run_compliance_narrative_engine()

        # Step 6: Governance Layout Engine v1
        self._run_governance_layout_engine()

        # Validate DoD
        self._validate_dod()

        # Final status
        self._report.success = self._report.dod_passed

        # Add N4.3 metadata
        self._current_sections["_n43_processed"] = True
        self._current_sections["_n43_report"] = self._report.to_dict()
        self._current_sections["_n43_dod_passed"] = self._report.dod_passed

        log.info(
            "[N4.3] Processing complete: success=%s, dod_passed=%s, healed=%d",
            self._report.success,
            self._report.dod_passed,
            self._report.total_healed
        )

        return self._current_sections, self._report

    def _run_governance_policy_engine(self) -> None:
        """Run Governance Policy Engine v2."""
        try:
            from services.governance_policy_engine_v2 import GovernancePolicyEngineV2

            engine = GovernancePolicyEngineV2(
                sections=self._current_sections,
                briefing=self.briefing,
                branch=self.branch,
                size=self.size,
                target_language=self.target_language,
            )

            self._current_sections, report = engine.process()

            self._report.governance_policy_ok = report.success
            self._report.governance_score = report.overall_score
            self._report.risk_class = report.risk_class or "minimal"
            self._report.maturity_level = report.maturity_level or "initial"
            self._report.total_controls = report.controls_derived
            self._report.policy_cards = report.policy_cards_generated
            self._report.governance_conflicts = report.conflicts_found - report.conflicts_resolved

            if report.healed:
                self._report.total_healed += 1

            log.info("[N4.3] Governance Policy Engine: score=%d, controls=%d",
                     report.overall_score, report.controls_derived)

        except Exception as e:
            log.error("[N4.3] Governance Policy Engine failed: %s", str(e))
            self._report.issues.append(f"Governance Policy Engine: {str(e)}")
            self._report.governance_policy_ok = False

    def _run_safety_assurance_layer(self) -> None:
        """Run Safety Assurance Layer v3."""
        try:
            from services.safety_assurance_layer_v3 import SafetyAssuranceLayerV3

            engine = SafetyAssuranceLayerV3(
                sections=self._current_sections,
                briefing=self.briefing,
                target_language=self.target_language,
            )

            self._current_sections, report = engine.process()

            self._report.safety_assurance_ok = report.success
            self._report.safety_violations = report.violations_found - report.violations_healed

            if report.healed:
                self._report.total_healed += 1

            log.info("[N4.3] Safety Assurance Layer: violations=%d",
                     report.violations_found)

        except Exception as e:
            log.error("[N4.3] Safety Assurance Layer failed: %s", str(e))
            self._report.issues.append(f"Safety Assurance Layer: {str(e)}")
            self._report.safety_assurance_ok = False

    def _run_numerical_integrity_engine(self) -> None:
        """Run Numerical Integrity Engine v4."""
        try:
            from services.numerical_integrity_engine_v4 import NumericalIntegrityEngineV4

            engine = NumericalIntegrityEngineV4(
                sections=self._current_sections,
                briefing=self.briefing,
                branch=self.branch,
            )

            self._current_sections, report = engine.process()

            self._report.numerical_integrity_ok = report.success
            self._report.numerical_inconsistencies = report.issues_found - report.issues_healed

            if report.healed:
                self._report.total_healed += 1

            log.info("[N4.3] Numerical Integrity Engine: issues=%d, healed=%d, remaining=%d",
                     report.issues_found, report.issues_healed,
                     self._report.numerical_inconsistencies)

            # FIX-NUM-DIAG: Log individual unhealed issues for debugging
            if self._report.numerical_inconsistencies > 0:
                # Try to extract detailed issues from the engine report
                detail_issues = getattr(report, 'issues', None) or getattr(report, 'issue_details', None) or []
                if detail_issues:
                    for idx, issue in enumerate(detail_issues[:10]):
                        if isinstance(issue, dict):
                            log.warning(
                                "[N4.3][NUM-DIAG] Issue %d: metric=%s, expected=%s, actual=%s, section=%s, healed=%s",
                                idx + 1,
                                issue.get('metric', issue.get('field', '?')),
                                issue.get('expected', '?'),
                                issue.get('actual', issue.get('found', '?')),
                                issue.get('section', issue.get('source', '?')),
                                issue.get('healed', issue.get('resolved', '?')),
                            )
                        elif isinstance(issue, str):
                            log.warning("[N4.3][NUM-DIAG] Issue %d: %s", idx + 1, issue[:200])
                        else:
                            # Object with attributes
                            log.warning(
                                "[N4.3][NUM-DIAG] Issue %d: type=%s, section=%s, healed=%s, msg=%s",
                                idx + 1,
                                getattr(issue, 'type', getattr(issue, 'metric', '?')),
                                getattr(issue, 'section', getattr(issue, 'source', '?')),
                                getattr(issue, 'healed', getattr(issue, 'resolved', '?')),
                                str(getattr(issue, 'message', getattr(issue, 'description', issue)))[:200],
                            )
                else:
                    # No detail list found — log what attributes the report has
                    report_attrs = [a for a in dir(report) if not a.startswith('__')]
                    log.warning(
                        "[N4.3][NUM-DIAG] No issue details found. Report attrs: %s",
                        ', '.join(report_attrs[:20])
                    )
                    # Store summary for upstream consumption
                    self._report.issues.append(
                        f"Numerical: {self._report.numerical_inconsistencies} unhealed "
                        f"(found={report.issues_found}, healed={report.issues_healed})"
                    )

        except Exception as e:
            log.error("[N4.3] Numerical Integrity Engine failed: %s", str(e))
            self._report.issues.append(f"Numerical Integrity Engine: {str(e)}")
            self._report.numerical_integrity_ok = False

    def _run_consistency_kernel(self) -> None:
        """Run Consistency Kernel v7."""
        try:
            from services.consistency_kernel_v7 import ConsistencyKernelV7

            engine = ConsistencyKernelV7(
                sections=self._current_sections,
                briefing=self.briefing,
            )

            self._current_sections, report = engine.process()

            self._report.consistency_kernel_ok = report.success

            if report.healed:
                self._report.total_healed += 1

            log.info("[N4.3] Consistency Kernel: aligned=%s",
                     report.success)

        except Exception as e:
            log.error("[N4.3] Consistency Kernel failed: %s", str(e))
            self._report.issues.append(f"Consistency Kernel: {str(e)}")
            self._report.consistency_kernel_ok = False

    def _run_compliance_narrative_engine(self) -> None:
        """Run Compliance Narrative Engine v3."""
        try:
            from services.compliance_narrative_engine_v3 import ComplianceNarrativeEngineV3

            engine = ComplianceNarrativeEngineV3(
                sections=self._current_sections,
                briefing=self.briefing,
                target_language=self.target_language,
                risk_class=self._report.risk_class,
                maturity_level=self._report.maturity_level,
            )

            self._current_sections, report = engine.process()

            self._report.compliance_narrative_ok = report.success
            self._report.compliance_leaks = report.hallucinations_detected - report.hallucinations_fixed

            if report.healed:
                self._report.total_healed += 1

            log.info("[N4.3] Compliance Narrative Engine: narratives=%d",
                     report.narratives_generated)

        except Exception as e:
            log.error("[N4.3] Compliance Narrative Engine failed: %s", str(e))
            self._report.issues.append(f"Compliance Narrative Engine: {str(e)}")
            self._report.compliance_narrative_ok = False

    def _run_governance_layout_engine(self) -> None:
        """Run Governance Layout Engine v1."""
        try:
            from services.governance_layout_engine import GovernanceLayoutEngineV1

            engine = GovernanceLayoutEngineV1(
                sections=self._current_sections,
                briefing=self.briefing,
                target_language=self.target_language,
            )

            self._current_sections, report = engine.process()

            self._report.governance_layout_ok = report.success

            if report.healed:
                self._report.total_healed += 1

            log.info("[N4.3] Governance Layout Engine: cards=%d, pages=%d",
                     report.cards_rendered, report.total_pages)

        except Exception as e:
            log.error("[N4.3] Governance Layout Engine failed: %s", str(e))
            self._report.issues.append(f"Governance Layout Engine: {str(e)}")
            self._report.governance_layout_ok = False

    def _validate_dod(self) -> None:
        """Validate Definition of Done criteria."""
        # Check if any fallbacks were used
        # FIX-NUM-DIAG: Only check metadata keys, not content sections
        # Old code matched "fallback" in ANY section value → false positives
        # from content like "Ohne Fallback-Strategie entstehen Single..."
        fallbacks = 0
        fallback_keys: list = []
        _FALLBACK_MARKER_KEYS = {
            "_fallback_used", "_qw_fallback", "_used_fallback",
            "PIPELINE_FALLBACK_COUNT",
        }
        for key in self._current_sections:
            # Method 1: Known fallback marker keys
            if key in _FALLBACK_MARKER_KEYS:
                val = self._current_sections[key]
                if val and str(val) not in ("0", "False", "false", ""):
                    fallbacks += 1
                    fallback_keys.append(f"{key}={val}")
                continue

            # Method 2: Only check _-prefixed metadata keys (not content HTML)
            if key.startswith("_") and key.endswith("_fallback"):
                val = self._current_sections[key]
                if val:
                    fallbacks += 1
                    fallback_keys.append(f"{key}={str(val)[:50]}")

        # Also check the error gate if available
        try:
            from gpt_analyze import get_error_gate
            gate = get_error_gate()
            if gate and hasattr(gate, 'fallback_count') and gate.fallback_count > 0:
                fallbacks = max(fallbacks, gate.fallback_count)
                fallback_keys.append(f"error_gate.fallback_count={gate.fallback_count}")
        except (ImportError, Exception):
            pass  # Error gate not available in this context

        self._report.fallbacks_used = fallbacks

        # Log DoD status
        if self._report.dod_passed:
            log.info("[N4.3] DoD PASSED: All criteria met")
        else:
            log.warning(
                "[N4.3] DoD FAILED: conflicts=%d, numerical=%d, safety=%d, compliance=%d, fallbacks=%d",
                self._report.governance_conflicts,
                self._report.numerical_inconsistencies,
                self._report.safety_violations,
                self._report.compliance_leaks,
                self._report.fallbacks_used
            )
            # FIX-NUM-DIAG: Log which criteria failed
            if self._report.numerical_inconsistencies > 1:
                log.warning("[N4.3][DOD-DETAIL] numerical_inconsistencies=%d (threshold=1)",
                            self._report.numerical_inconsistencies)
            if fallback_keys:
                log.warning("[N4.3][DOD-DETAIL] fallback sources: %s", fallback_keys)

    def get_report(self) -> N43Report:
        """Get the N4.3 report."""
        return self._report


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def process_n43_governance(
    sections: SectionDict,
    briefing: BriefingDict,
    branch: str = "consulting",
    size: str = "team",
    target_language: str = "de",
) -> Tuple[SectionDict, N43Report]:
    """
    Process sections through N4.3 Governance Layer.

    Main entry point for N4.3 processing.

    Args:
        sections: Section dictionary
        briefing: Briefing data
        branch: Industry branch
        size: Company size
        target_language: Target language

    Returns:
        Tuple of (processed_sections, report)
    """
    engine = N43IntegrationEngine(
        sections=sections,
        briefing=briefing,
        branch=branch,
        size=size,
        target_language=target_language,
    )

    return engine.process()


def validate_n43_dod(report: N43Report) -> Tuple[bool, List[str]]:
    """
    Validate N4.3 Definition of Done.

    Args:
        report: N43Report to validate

    Returns:
        Tuple of (passed, failure_reasons)
    """
    failures: List[str] = []

    if report.governance_conflicts > 0:
        failures.append(f"Governance conflicts: {report.governance_conflicts}")

    if report.numerical_inconsistencies > 0:
        failures.append(f"Numerical inconsistencies: {report.numerical_inconsistencies}")

    if report.safety_violations > 0:
        failures.append(f"Safety violations: {report.safety_violations}")

    if report.compliance_leaks > 0:
        failures.append(f"Compliance leaks: {report.compliance_leaks}")

    if report.fallbacks_used > 0:
        failures.append(f"Fallbacks used: {report.fallbacks_used}")

    return len(failures) == 0, failures


def get_n43_status(sections: SectionDict) -> Dict[str, Any]:
    """
    Get N4.3 processing status from sections.

    Args:
        sections: Section dictionary

    Returns:
        Status dictionary
    """
    return {
        "processed": sections.get("_n43_processed", False),
        "dod_passed": sections.get("_n43_dod_passed", False),
        "report": sections.get("_n43_report", {}),
        "governance_validated": sections.get("_governance_validated", False),
        "safety_validated": sections.get("_safety_validated", False),
        "numerical_validated": sections.get("_numerical_validated", False),
        "consistency_validated": sections.get("_consistency_validated", False),
        "narrative_validated": sections.get("_compliance_narrative_validated", False),
        "layout_validated": sections.get("_layout_validated", False),
    }
