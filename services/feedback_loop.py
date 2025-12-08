# -*- coding: utf-8 -*-
"""
Sprint G16-A: Real-World Feedback Collector

Captures production feedback data for continuous improvement analysis.
Stores metrics per report: warnings, fallback rates, AI-Act risk levels,
funding sources, generation times, and research coverage.

Version: 1.0.0
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

FEEDBACK_LOOP_ENABLED = os.environ.get("FEEDBACK_LOOP_ENABLED", "1") == "1"
FEEDBACK_RETENTION_DAYS = int(os.environ.get("FEEDBACK_RETENTION_DAYS", "90"))


# =============================================================================
# FEEDBACK DATA STRUCTURES
# =============================================================================

@dataclass
class WarningInfo:
    """Structured warning information."""
    warning_type: str  # min-word, redundancy, persona-leak, placeholder, etc.
    section: str
    message: str
    severity: str = "WARNING"  # WARNING, CRITICAL


@dataclass
class FeedbackEntry:
    """Complete feedback entry for a report."""
    report_id: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Warning metrics
    total_warnings: int = 0
    warning_types: Dict[str, int] = field(default_factory=dict)
    warnings_detail: List[WarningInfo] = field(default_factory=list)

    # AI-Act metrics
    ai_act_risk_level: str = "unknown"
    ai_act_override_used: bool = False
    capex_modifier: float = 1.0
    opex_modifier: float = 1.0

    # Fallback & Research metrics
    fallback_rate: float = 0.0  # 0.0 - 1.0
    sections_with_fallback: List[str] = field(default_factory=list)
    research_coverage: Dict[str, int] = field(default_factory=dict)

    # Funding metrics
    funding_source: str = "DE"  # DE, EU-CORE, EN-DE
    funding_programs_count: int = 0

    # Size & Persona
    size_label: str = "unknown"  # solo, team, kmu
    persona_leaks_detected: int = 0

    # Performance metrics
    generation_time_sec: float = 0.0
    llm_timeouts: int = 0
    api_retries: int = 0
    pdf_render_time_sec: float = 0.0
    pdf_retries: int = 0

    # Section word counts
    section_word_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "total_warnings": self.total_warnings,
            "warning_types": self.warning_types,
            "ai_act_risk_level": self.ai_act_risk_level,
            "ai_act_override_used": self.ai_act_override_used,
            "capex_modifier": self.capex_modifier,
            "opex_modifier": self.opex_modifier,
            "fallback_rate": self.fallback_rate,
            "sections_with_fallback": self.sections_with_fallback,
            "research_coverage": self.research_coverage,
            "funding_source": self.funding_source,
            "funding_programs_count": self.funding_programs_count,
            "size_label": self.size_label,
            "persona_leaks_detected": self.persona_leaks_detected,
            "generation_time_sec": self.generation_time_sec,
            "llm_timeouts": self.llm_timeouts,
            "api_retries": self.api_retries,
            "pdf_render_time_sec": self.pdf_render_time_sec,
            "pdf_retries": self.pdf_retries,
            "section_word_counts": self.section_word_counts,
        }


# =============================================================================
# IN-MEMORY FEEDBACK STORE (for environments without DB)
# =============================================================================

_feedback_store: List[FeedbackEntry] = []


def get_feedback_store() -> List[FeedbackEntry]:
    """Get the in-memory feedback store."""
    return _feedback_store


def clear_feedback_store() -> None:
    """Clear the in-memory feedback store (for testing)."""
    global _feedback_store
    _feedback_store = []


# =============================================================================
# FEEDBACK CAPTURE FUNCTIONS
# =============================================================================

def capture_realworld_feedback(
    report_id: int,
    warnings: List[Dict[str, Any]],
    ai_act_risk_level: str,
    fallback_rate: float,
    funding_source: str,
    size_label: str,
    generation_time_sec: float = 0.0,
    sections_data: Optional[Dict[str, Any]] = None,
    research_coverage: Optional[Dict[str, int]] = None,
    llm_timeouts: int = 0,
    api_retries: int = 0,
    pdf_render_time_sec: float = 0.0,
    pdf_retries: int = 0,
    ai_act_override_used: bool = False,
    capex_modifier: float = 1.0,
    opex_modifier: float = 1.0,
) -> Optional[FeedbackEntry]:
    """
    Capture real-world feedback for a generated report.

    This is the main entry point called after report validation.

    Args:
        report_id: The report ID
        warnings: List of validation warnings
        ai_act_risk_level: Determined AI-Act risk level
        fallback_rate: Rate of fallback content (0.0-1.0)
        funding_source: Funding source used (DE, EU-CORE, etc.)
        size_label: Company size (solo, team, kmu)
        generation_time_sec: Total generation time
        sections_data: Section content for word count analysis
        research_coverage: Coverage metrics (tools, funding, competitor, etc.)
        llm_timeouts: Number of LLM timeouts
        api_retries: Number of API retries
        pdf_render_time_sec: PDF render time
        pdf_retries: Number of PDF retries
        ai_act_override_used: Whether override was used
        capex_modifier: Applied CAPEX modifier
        opex_modifier: Applied OPEX modifier

    Returns:
        FeedbackEntry if capture successful, None otherwise
    """
    if not FEEDBACK_LOOP_ENABLED:
        log.debug("Feedback loop disabled, skipping capture")
        return None

    try:
        entry = FeedbackEntry(
            report_id=report_id,
            ai_act_risk_level=ai_act_risk_level,
            ai_act_override_used=ai_act_override_used,
            capex_modifier=capex_modifier,
            opex_modifier=opex_modifier,
            fallback_rate=fallback_rate,
            funding_source=funding_source,
            size_label=size_label,
            generation_time_sec=generation_time_sec,
            llm_timeouts=llm_timeouts,
            api_retries=api_retries,
            pdf_render_time_sec=pdf_render_time_sec,
            pdf_retries=pdf_retries,
            research_coverage=research_coverage or {},
        )

        # Process warnings
        entry.total_warnings = len(warnings)
        warning_type_counts: Dict[str, int] = {}
        fallback_sections: List[str] = []
        persona_leaks = 0

        for w in warnings:
            w_type = _classify_warning(w)
            warning_type_counts[w_type] = warning_type_counts.get(w_type, 0) + 1

            # Track specific warning types
            if w_type == "persona-leak":
                persona_leaks += 1
            elif w_type == "fallback":
                section = w.get("section", "unknown")
                if section not in fallback_sections:
                    fallback_sections.append(section)

            # Store warning detail
            entry.warnings_detail.append(WarningInfo(
                warning_type=w_type,
                section=w.get("section", "unknown"),
                message=w.get("message", str(w)),
                severity=w.get("severity", "WARNING"),
            ))

        entry.warning_types = warning_type_counts
        entry.sections_with_fallback = fallback_sections
        entry.persona_leaks_detected = persona_leaks

        # Calculate section word counts
        if sections_data:
            entry.section_word_counts = _calculate_word_counts(sections_data)

        # Store in memory
        _feedback_store.append(entry)

        # Also try to store in database
        _store_to_database(entry)

        log.info(
            f"📊 Feedback captured for report {report_id}: "
            f"{entry.total_warnings} warnings, {entry.fallback_rate:.1%} fallback, "
            f"risk={entry.ai_act_risk_level}, size={entry.size_label}"
        )

        return entry

    except Exception as e:
        log.error(f"Failed to capture feedback for report {report_id}: {e}")
        return None


def _classify_warning(warning: Dict[str, Any]) -> str:
    """Classify a warning into a category."""
    message = str(warning.get("message", "")).lower()
    w_type = warning.get("type", "").lower()

    if "min" in message and "word" in message:
        return "min-word"
    elif "redundan" in message:
        return "redundancy"
    elif "persona" in message or "leak" in message or "size_mismatch" in w_type:
        return "persona-leak"
    elif "placeholder" in message:
        return "placeholder"
    elif "fallback" in message:
        return "fallback"
    elif "ai_act" in message or "ai-act" in message:
        return "ai-act"
    elif "funding" in message:
        return "funding"
    else:
        return "other"


def _calculate_word_counts(sections: Dict[str, Any]) -> Dict[str, int]:
    """Calculate word counts for each section."""
    import re

    word_counts: Dict[str, int] = {}

    for section_key, content in sections.items():
        if isinstance(content, str) and content.strip():
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', content)
            # Count words
            words = text.split()
            word_counts[section_key] = len(words)

    return word_counts


def _store_to_database(entry: FeedbackEntry) -> bool:
    """Store feedback entry to database (if available)."""
    try:
        # Try to import database session
        from core.db import get_session
        from sqlalchemy import text
        import json

        session = get_session()
        if session is None:
            return False

        # Check if table exists, create if not
        _ensure_feedback_table(session)

        # Insert feedback
        insert_sql = text("""
            INSERT INTO realworld_feedback_log (
                report_id, timestamp, total_warnings, warning_types_json,
                ai_act_risk_level, ai_act_override_used, capex_modifier, opex_modifier,
                fallback_rate, sections_with_fallback_json, research_coverage_json,
                funding_source, funding_programs_count, size_label, persona_leaks_detected,
                generation_time_sec, llm_timeouts, api_retries,
                pdf_render_time_sec, pdf_retries, section_word_counts_json
            ) VALUES (
                :report_id, :timestamp, :total_warnings, :warning_types_json,
                :ai_act_risk_level, :ai_act_override_used, :capex_modifier, :opex_modifier,
                :fallback_rate, :sections_with_fallback_json, :research_coverage_json,
                :funding_source, :funding_programs_count, :size_label, :persona_leaks_detected,
                :generation_time_sec, :llm_timeouts, :api_retries,
                :pdf_render_time_sec, :pdf_retries, :section_word_counts_json
            )
        """)

        session.execute(insert_sql, {
            "report_id": entry.report_id,
            "timestamp": entry.timestamp,
            "total_warnings": entry.total_warnings,
            "warning_types_json": json.dumps(entry.warning_types),
            "ai_act_risk_level": entry.ai_act_risk_level,
            "ai_act_override_used": entry.ai_act_override_used,
            "capex_modifier": entry.capex_modifier,
            "opex_modifier": entry.opex_modifier,
            "fallback_rate": entry.fallback_rate,
            "sections_with_fallback_json": json.dumps(entry.sections_with_fallback),
            "research_coverage_json": json.dumps(entry.research_coverage),
            "funding_source": entry.funding_source,
            "funding_programs_count": entry.funding_programs_count,
            "size_label": entry.size_label,
            "persona_leaks_detected": entry.persona_leaks_detected,
            "generation_time_sec": entry.generation_time_sec,
            "llm_timeouts": entry.llm_timeouts,
            "api_retries": entry.api_retries,
            "pdf_render_time_sec": entry.pdf_render_time_sec,
            "pdf_retries": entry.pdf_retries,
            "section_word_counts_json": json.dumps(entry.section_word_counts),
        })
        session.commit()
        return True

    except Exception as e:
        log.debug(f"Database storage skipped: {e}")
        return False


def _ensure_feedback_table(session: Any) -> None:
    """Ensure the feedback table exists."""
    from sqlalchemy import text

    create_sql = text("""
        CREATE TABLE IF NOT EXISTS realworld_feedback_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            timestamp DATETIME NOT NULL,
            total_warnings INTEGER DEFAULT 0,
            warning_types_json TEXT,
            ai_act_risk_level VARCHAR(32),
            ai_act_override_used BOOLEAN DEFAULT FALSE,
            capex_modifier FLOAT DEFAULT 1.0,
            opex_modifier FLOAT DEFAULT 1.0,
            fallback_rate FLOAT DEFAULT 0.0,
            sections_with_fallback_json TEXT,
            research_coverage_json TEXT,
            funding_source VARCHAR(32),
            funding_programs_count INTEGER DEFAULT 0,
            size_label VARCHAR(16),
            persona_leaks_detected INTEGER DEFAULT 0,
            generation_time_sec FLOAT DEFAULT 0.0,
            llm_timeouts INTEGER DEFAULT 0,
            api_retries INTEGER DEFAULT 0,
            pdf_render_time_sec FLOAT DEFAULT 0.0,
            pdf_retries INTEGER DEFAULT 0,
            section_word_counts_json TEXT
        )
    """)

    try:
        session.execute(create_sql)
        session.commit()
    except Exception:
        pass  # Table may already exist


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def get_recent_feedback(
    days: int = 7,
    size_label: Optional[str] = None,
    min_warnings: int = 0,
) -> List[FeedbackEntry]:
    """
    Get recent feedback entries.

    Args:
        days: Number of days to look back
        size_label: Filter by size (solo, team, kmu)
        min_warnings: Minimum number of warnings

    Returns:
        List of matching FeedbackEntry objects
    """
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    results = []
    for entry in _feedback_store:
        if entry.timestamp < cutoff:
            continue
        if size_label and entry.size_label != size_label:
            continue
        if entry.total_warnings < min_warnings:
            continue
        results.append(entry)

    return results


def get_feedback_stats(days: int = 7) -> Dict[str, Any]:
    """
    Get aggregated feedback statistics.

    Args:
        days: Number of days to analyze

    Returns:
        Dictionary with aggregated statistics
    """
    entries = get_recent_feedback(days=days)

    if not entries:
        return {
            "period_days": days,
            "total_reports": 0,
            "avg_warnings": 0.0,
            "avg_fallback_rate": 0.0,
            "avg_generation_time": 0.0,
            "warning_type_totals": {},
            "size_distribution": {},
            "risk_level_distribution": {},
            "funding_source_distribution": {},
        }

    total = len(entries)

    # Aggregate warning types
    warning_totals: Dict[str, int] = {}
    for entry in entries:
        for w_type, count in entry.warning_types.items():
            warning_totals[w_type] = warning_totals.get(w_type, 0) + count

    # Size distribution
    size_dist: Dict[str, int] = {}
    for entry in entries:
        size_dist[entry.size_label] = size_dist.get(entry.size_label, 0) + 1

    # Risk level distribution
    risk_dist: Dict[str, int] = {}
    for entry in entries:
        risk_dist[entry.ai_act_risk_level] = risk_dist.get(entry.ai_act_risk_level, 0) + 1

    # Funding distribution
    funding_dist: Dict[str, int] = {}
    for entry in entries:
        funding_dist[entry.funding_source] = funding_dist.get(entry.funding_source, 0) + 1

    return {
        "period_days": days,
        "total_reports": total,
        "avg_warnings": sum(e.total_warnings for e in entries) / total,
        "avg_fallback_rate": sum(e.fallback_rate for e in entries) / total,
        "avg_generation_time": sum(e.generation_time_sec for e in entries) / total,
        "warning_type_totals": warning_totals,
        "size_distribution": size_dist,
        "risk_level_distribution": risk_dist,
        "funding_source_distribution": funding_dist,
    }
