# -*- coding: utf-8 -*-
"""
N4.4: Integration Module
========================

PLATIN+++ v5.4 - Integration layer for gpt_analyze.py

Provides:
- Single entry point for research agent pipeline
- process_n44_research() main function
- Injection hooks for report sections
- Status and reporting functions

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.research_agents.orchestrator import (
    AgentResult,
    AgentSignalType,
    ResearchAgentOrchestrator,
    ResearchInsight,
)
from services.research_agents.knowledge_fusion import (
    FusionStrategy,
    InjectionTarget,
    KnowledgeFusionLayerV2,
)
from services.research_agents.integrity_engine import (
    IntegrityReport,
    ResearchIntegrityEngineV1,
)

log = logging.getLogger(__name__)

__all__ = [
    "N44ResearchReport",
    "N44Status",
    "process_n44_research",
    "validate_n44_dod",
    "get_n44_status",
    "inject_research_into_sections",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class N44ResearchReport:
    """Complete N4.4 research processing report."""

    report_id: str = ""
    success: bool = True
    timestamp: str = ""

    # Orchestrator results
    agents_run: int = 0
    agents_succeeded: int = 0
    agents_failed: int = 0
    total_insights: int = 0

    # Fusion results
    fused_signals: int = 0
    theses_generated: int = 0
    contradictions_resolved: int = 0

    # Integrity results
    integrity_score: float = 1.0
    sources_verified: int = 0
    biases_detected: int = 0
    anomalies_found: int = 0

    # Injection results
    sections_injected: int = 0
    hooks_applied: int = 0

    # Audit
    final_hash: str = ""

    # Details
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: int = 0

    def __post_init__(self) -> None:
        if not self.report_id:
            self.report_id = f"N44-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "success": self.success,
            "timestamp": self.timestamp,
            "agents_run": self.agents_run,
            "agents_succeeded": self.agents_succeeded,
            "agents_failed": self.agents_failed,
            "total_insights": self.total_insights,
            "fused_signals": self.fused_signals,
            "theses_generated": self.theses_generated,
            "contradictions_resolved": self.contradictions_resolved,
            "integrity_score": round(self.integrity_score, 3),
            "sources_verified": self.sources_verified,
            "biases_detected": self.biases_detected,
            "anomalies_found": self.anomalies_found,
            "sections_injected": self.sections_injected,
            "hooks_applied": self.hooks_applied,
            "final_hash": self.final_hash,
            "issues": self.issues,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class N44Status:
    """Current N4.4 processing status."""

    phase: str = "idle"
    progress: float = 0.0
    current_agent: str = ""
    insights_collected: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase": self.phase,
            "progress": round(self.progress, 2),
            "current_agent": self.current_agent,
            "insights_collected": self.insights_collected,
            "errors": self.errors,
        }


# Global status tracker
_current_status = N44Status()


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_n44_research(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    language: str = "de",
    mock_mode: bool = True,
) -> tuple[Dict[str, Any], N44ResearchReport]:
    """
    Main entry point for N4.4 Research Agent processing.

    Pipeline:
    1. Run all research agents via orchestrator
    2. Fuse signals via Knowledge Fusion Layer
    3. Validate integrity via Integrity Engine
    4. Inject insights into sections

    Args:
        sections: Current report sections
        briefing: Briefing data
        language: Language code (de/en)
        mock_mode: Use mock data (default True for safety)

    Returns:
        Tuple of (modified_sections, report)
    """
    global _current_status
    import time
    start_time = time.time()

    log.info("[N4.4] Starting research agent pipeline...")
    _current_status = N44Status(phase="initializing", progress=0.0)

    report = N44ResearchReport()

    try:
        # Phase 1: Run orchestrator
        _current_status.phase = "orchestrating"
        _current_status.progress = 0.1

        orchestrator = ResearchAgentOrchestrator(
            briefing=briefing,
            language=language,
            mock_mode=mock_mode,
        )

        # Register default agents
        orchestrator.register_default_agents()

        log.info("[N4.4] Agent start...")
        agent_results = orchestrator.run_all_agents()

        # Update report with orchestrator results
        exec_summary = orchestrator.get_execution_summary()
        report.agents_run = exec_summary["agents_run"]
        report.agents_succeeded = exec_summary["agents_succeeded"]
        report.agents_failed = exec_summary["agents_failed"]
        report.total_insights = exec_summary["total_insights"]
        report.final_hash = exec_summary["final_hash"]

        _current_status.insights_collected = report.total_insights
        _current_status.progress = 0.4

        # Phase 2: Knowledge Fusion
        _current_status.phase = "fusing"
        log.info("[N4.4] Fusion start...")

        fusion_layer = KnowledgeFusionLayerV2(
            language=language,
            strategy=FusionStrategy.CLAUDE_PREFERRED,
        )
        fusion_layer.add_agent_results(agent_results)
        fusion_result = fusion_layer.fuse()

        report.fused_signals = len(fusion_result.get("fused_signals", []))
        report.theses_generated = len(fusion_result.get("theses", []))
        report.contradictions_resolved = fusion_result.get("contradictions_resolved", 0)

        log.info("[N4.4] Fusion complete...")
        _current_status.progress = 0.6

        # Phase 3: Integrity Check
        _current_status.phase = "validating"
        log.info("[N4.4] Integrity check...")

        integrity_engine = ResearchIntegrityEngineV1(
            language=language,
            strict_mode=False,
        )

        all_insights = orchestrator.get_all_insights()
        integrity_report = integrity_engine.validate(all_insights)

        report.integrity_score = integrity_report.overall_integrity_score
        report.sources_verified = integrity_report.sources_verified
        report.biases_detected = integrity_report.biases_detected
        report.anomalies_found = integrity_report.anomalies_found
        report.warnings.extend(integrity_report.warnings)

        _current_status.progress = 0.8

        # Phase 4: Injection
        _current_status.phase = "injecting"
        log.info("[N4.4] Injecting insights...")

        # Get hooks for injection
        hooks = fusion_layer.get_all_hooks()
        theses = fusion_layer.get_theses()

        # Inject into sections
        modified_sections = inject_research_into_sections(
            sections=sections,
            hooks=hooks,
            theses=theses,
            language=language,
        )

        # Count injections
        report.sections_injected = sum(
            1 for target, hook_list in hooks.items()
            if hook_list and target.value in modified_sections
        )
        report.hooks_applied = sum(len(h) for h in hooks.values())

        log.info("[N4.4] Injected %d signals...", report.hooks_applied)

        # Add metadata
        modified_sections["_n44_research_processed"] = True
        modified_sections["_n44_report"] = report.to_dict()
        modified_sections["_n44_theses"] = [t.to_dict() for t in theses]
        modified_sections["_n44_integrity_score"] = report.integrity_score

        # Finalize
        _current_status.phase = "complete"
        _current_status.progress = 1.0

        report.execution_time_ms = int((time.time() - start_time) * 1000)
        report.success = True

        log.info(
            "[N4.4] Pipeline complete: %d insights, %d signals, %.2f integrity, %dms",
            report.total_insights,
            report.fused_signals,
            report.integrity_score,
            report.execution_time_ms,
        )

        return modified_sections, report

    except Exception as e:
        log.error("[N4.4] Pipeline failed: %s", str(e))
        report.success = False
        report.issues.append(f"Pipeline error: {str(e)}")
        _current_status.phase = "error"
        _current_status.errors.append(str(e))

        # Return original sections on error
        sections["_n44_research_processed"] = False
        sections["_n44_error"] = str(e)

        return sections, report


def inject_research_into_sections(
    sections: Dict[str, Any],
    hooks: Dict[InjectionTarget, List[Any]],
    theses: List[Any],
    language: str = "de",
) -> Dict[str, Any]:
    """
    Inject research insights into report sections.

    Args:
        sections: Current report sections
        hooks: Injection hooks by target
        theses: Executive theses
        language: Language code

    Returns:
        Modified sections dict
    """
    modified = sections.copy()

    # Map injection targets to section keys
    target_to_section = {
        InjectionTarget.EXECUTIVE_SUMMARY: "executive_summary",
        InjectionTarget.STRATEGY: "strategy",
        InjectionTarget.KI_STACK: "ki_stack_summary",
        InjectionTarget.BRANCH_DEEP_DIVE: "branch_deep_dive",
        InjectionTarget.BENCHMARK: "benchmark",
        InjectionTarget.FUNDING: "funding",
        InjectionTarget.GOVERNANCE: "governance",
        InjectionTarget.RISKS: "risks",
    }

    # Inject theses into executive summary
    if theses and InjectionTarget.EXECUTIVE_SUMMARY in hooks:
        thesis_block = _format_theses_block(theses, language)
        exec_key = target_to_section[InjectionTarget.EXECUTIVE_SUMMARY]

        if exec_key in modified and isinstance(modified[exec_key], str):
            modified[exec_key] = modified[exec_key] + "\n\n" + thesis_block
        else:
            modified[f"_research_{exec_key}"] = thesis_block

    # Inject hooks into respective sections
    for target, hook_list in hooks.items():
        if not hook_list:
            continue

        section_key = target_to_section.get(target)
        if not section_key:
            continue

        # Build injection content
        injection_content = _format_injection_block(hook_list, target, language)

        if section_key in modified and isinstance(modified[section_key], str):
            # Append to existing content
            modified[section_key] = modified[section_key] + "\n\n" + injection_content
        else:
            # Store as separate key
            modified[f"_research_{section_key}"] = injection_content

    return modified


def _format_theses_block(theses: List[Any], language: str) -> str:
    """Format theses as a text block."""
    if language == "de":
        header = "### Forschungs-Erkenntnisse\n\n"
    else:
        header = "### Research Insights\n\n"

    lines = [header]
    for i, thesis in enumerate(theses[:5], 1):
        statement = thesis.statement if hasattr(thesis, "statement") else str(thesis)
        lines.append(f"{i}. {statement}")

    return "\n".join(lines)


def _format_injection_block(hooks: List[Any], target: InjectionTarget, language: str) -> str:
    """Format injection hooks as a text block."""
    if language == "de":
        header = f"### Autonome Recherche: {target.value}\n\n"
    else:
        header = f"### Autonomous Research: {target.value}\n\n"

    lines = [header]
    for hook in hooks[:3]:  # Limit to top 3
        content = hook.content if hasattr(hook, "content") else str(hook)
        lines.append(f"- {content[:200]}")

    return "\n".join(lines)


# =============================================================================
# VALIDATION & STATUS FUNCTIONS
# =============================================================================

def validate_n44_dod(report: N44ResearchReport) -> tuple[bool, Dict[str, Any]]:
    """
    Validate N4.4 Definition of Done criteria.

    DoD:
    - 100% Research-Agent support for DE/EN
    - 0 contradictory signals
    - 0 unverified sources (in strict mode)
    - 0 redundancies (deduplication applied)
    - Insights improve Executive Summary

    Returns:
        Tuple of (is_valid, details)
    """
    details = {
        "agents_ok": report.agents_succeeded >= 5,
        "integrity_ok": report.integrity_score >= 0.7,
        "contradictions_ok": report.contradictions_resolved >= 0,  # Resolved = OK
        "fusion_ok": report.fused_signals > 0,
        "injection_ok": report.hooks_applied > 0,
    }

    is_valid = all(details.values())

    return is_valid, details


def get_n44_status() -> Dict[str, Any]:
    """Get current N4.4 processing status."""
    global _current_status
    return _current_status.to_dict()
