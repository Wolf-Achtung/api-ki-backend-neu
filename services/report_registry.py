# -*- coding: utf-8 -*-
"""
Sprint G11: Report Registry & Versioning Service

Provides:
- Automatic report versioning
- Version history management
- Report snapshot extraction from sections
- Delta preparation for comparison

Version: 1.0.0 (Sprint G11)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

REPORT_VERSIONING_ENABLED = os.getenv("REPORT_VERSIONING_ENABLED", "1").lower() in ("1", "true", "yes")
MAX_STORED_REPORTS = int(os.getenv("MAX_STORED_REPORTS", "50"))
MAX_REPORT_VERSIONS = int(os.getenv("MAX_REPORT_VERSIONS", "10"))
PDF_SNAPSHOT_ENABLED = os.getenv("PDF_SNAPSHOT_ENABLED", "1").lower() in ("1", "true", "yes")


# =============================================================================
# SECTION KEYS FOR EXTRACTION
# =============================================================================

SCORE_KEYS = [
    "GOVERNANCE_SCORE", "SECURITY_SCORE", "BENEFIT_SCORE",
    "READINESS_SCORE", "RISK_SCORE", "OVERALL_SCORE",
    "MATURITY_LEVEL", "MATURITY_LABEL",
]

BC_KEYS = [
    "CAPEX_REALISTISCH_EUR", "OPEX_REALISTISCH_EUR",
    "EINSPARUNG_MONAT_EUR", "PAYBACK_MONTHS",
    "ROI_12M", "ROI_12M_EUR",
    "AI_ACT_BC_APPLIED", "AI_ACT_BC_CAPEX_FACTOR",
    "AI_ACT_BC_OPEX_FACTOR", "AI_ACT_BC_PAYBACK_DELTA",
    "AI_ACT_BC_ORIGINAL_CAPEX", "AI_ACT_BC_ORIGINAL_OPEX",
]

AI_ACT_KEYS = [
    "AI_ACT_RISK_LEVEL", "AI_ACT_RISK_REASONING",
    "CAPEX_MODIFIER", "OPEX_MODIFIER",
    "_ai_act_bc_metrics",
]

LABEL_KEYS = [
    "BRANCH_CORE_LABEL", "BRANCH_LABEL", "BRANCHE_LABEL",
    "OFFERING_LABEL", "REGULATORY_LABEL",
    "CR_LABELS", "USE_CASE_TAGS",
]

SECTION_WORD_COUNT_KEYS = [
    "executive_summary", "roadmap_12m", "roadmap_90d",
    "quick_wins", "gamechanger", "recommendations",
    "risks", "foerderpotenzial", "unternehmensprofil_markt",
]


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_scores(sections: Dict[str, Any]) -> Dict[str, Any]:
    """Extract score-related data from sections."""
    return {k: sections.get(k) for k in SCORE_KEYS if sections.get(k) is not None}


def extract_business_case(sections: Dict[str, Any]) -> Dict[str, Any]:
    """Extract business case data from sections."""
    return {k: sections.get(k) for k in BC_KEYS if sections.get(k) is not None}


def extract_ai_act_data(sections: Dict[str, Any]) -> Dict[str, Any]:
    """Extract AI Act compliance data from sections."""
    return {k: sections.get(k) for k in AI_ACT_KEYS if sections.get(k) is not None}


def extract_labels(sections: Dict[str, Any]) -> Dict[str, Any]:
    """Extract label data from sections."""
    return {k: sections.get(k) for k in LABEL_KEYS if sections.get(k) is not None}


def extract_section_stats(sections: Dict[str, Any]) -> Dict[str, Any]:
    """Extract section word counts for delta comparison."""
    import re
    stats = {}

    for key in SECTION_WORD_COUNT_KEYS:
        # Try uppercase and lowercase variants
        content = sections.get(key.upper()) or sections.get(key) or ""
        if isinstance(content, str):
            # Strip HTML and count words
            text = re.sub(r"<[^>]+>", " ", content)
            word_count = len(text.split())
            stats[key] = {
                "word_count": word_count,
                "char_count": len(text),
            }

    return stats


# =============================================================================
# VERSIONING SERVICE
# =============================================================================

def get_next_version(db: Session, report_id: int) -> int:
    """Get the next version number for a report."""
    from models import ReportHistory

    max_version = db.query(func.max(ReportHistory.version)).filter(
        ReportHistory.report_id == report_id
    ).scalar()

    return (max_version or 0) + 1


def save_report_version(
    db: Session,
    report_id: int,
    user_id: Optional[int],
    sections: Dict[str, Any],
    html_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
    lang: str = "de",
    size_category: Optional[str] = None,
) -> Optional[int]:
    """
    Save a new version of a report to the history.

    Args:
        db: Database session
        report_id: ID of the report
        user_id: ID of the user (optional)
        sections: Full sections dict from analysis
        html_path: Path to debug HTML file
        pdf_path: Path to PDF file
        lang: Language code (de/en)
        size_category: Company size (solo/team/kmu)

    Returns:
        Version number if saved, None if versioning disabled
    """
    if not REPORT_VERSIONING_ENABLED:
        log.debug("[G11] Report versioning disabled, skipping save")
        return None

    from models import ReportHistory

    try:
        # Get next version
        version = get_next_version(db, report_id)

        # Extract data from sections
        scores = extract_scores(sections)
        bc_data = extract_business_case(sections)
        ai_act_data = extract_ai_act_data(sections)
        labels = extract_labels(sections)
        section_stats = extract_section_stats(sections)

        # Create history entry
        history = ReportHistory(
            user_id=user_id,
            report_id=report_id,
            version=version,
            scores_json=scores,
            bc_json=bc_data,
            ai_act_json=ai_act_data,
            labels_json=labels,
            section_stats_json=section_stats,
            html_path=html_path,
            pdf_path=pdf_path,
            lang=lang,
            size_category=size_category,
        )

        db.add(history)
        db.commit()

        log.info(
            "[G11] Saved report version: report_id=%d, version=%d, scores=%d, bc=%d keys",
            report_id, version, len(scores), len(bc_data)
        )

        # Cleanup old versions if needed
        _cleanup_old_versions(db, report_id, user_id)

        return version

    except Exception as e:
        log.error("[G11] Failed to save report version: %s", e)
        db.rollback()
        return None


def _cleanup_old_versions(db: Session, report_id: int, user_id: Optional[int]) -> None:
    """Remove old versions beyond MAX_REPORT_VERSIONS."""
    from models import ReportHistory

    try:
        # Count versions for this report
        count = db.query(func.count(ReportHistory.id)).filter(
            ReportHistory.report_id == report_id
        ).scalar()

        if count > MAX_REPORT_VERSIONS:
            # Get oldest versions to delete
            oldest = db.query(ReportHistory).filter(
                ReportHistory.report_id == report_id
            ).order_by(ReportHistory.version.asc()).limit(count - MAX_REPORT_VERSIONS).all()

            for old in oldest:
                db.delete(old)

            db.commit()
            log.info("[G11] Cleaned up %d old versions for report_id=%d", len(oldest), report_id)

    except Exception as e:
        log.warning("[G11] Version cleanup failed: %s", e)


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def get_report_versions(
    db: Session,
    report_id: int,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get all versions of a report."""
    from models import ReportHistory

    versions = db.query(ReportHistory).filter(
        ReportHistory.report_id == report_id
    ).order_by(desc(ReportHistory.version)).limit(limit).all()

    return [v.to_dict() for v in versions]


def get_report_version(
    db: Session,
    report_id: int,
    version: int
) -> Optional[Dict[str, Any]]:
    """Get a specific version of a report."""
    from models import ReportHistory

    history = db.query(ReportHistory).filter(
        ReportHistory.report_id == report_id,
        ReportHistory.version == version
    ).first()

    if history:
        result: Dict[str, Any] = history.to_dict()
        return result
    return None


def get_user_reports(
    db: Session,
    user_id: int,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get all reports for a user with latest version info."""
    from models import ReportHistory, Report

    # Subquery for max version per report
    subq = db.query(
        ReportHistory.report_id,
        func.max(ReportHistory.version).label("max_version")
    ).filter(
        ReportHistory.user_id == user_id
    ).group_by(ReportHistory.report_id).subquery()

    # Get latest versions
    latest = db.query(ReportHistory).join(
        subq,
        (ReportHistory.report_id == subq.c.report_id) &
        (ReportHistory.version == subq.c.max_version)
    ).order_by(desc(ReportHistory.created_at)).limit(limit).all()

    return [v.to_dict() for v in latest]


def delete_report_version(
    db: Session,
    report_id: int,
    version: int
) -> bool:
    """Delete a specific version of a report."""
    from models import ReportHistory

    try:
        history = db.query(ReportHistory).filter(
            ReportHistory.report_id == report_id,
            ReportHistory.version == version
        ).first()

        if history:
            db.delete(history)
            db.commit()
            log.info("[G11] Deleted version %d of report %d", version, report_id)
            return True
        return False

    except Exception as e:
        log.error("[G11] Failed to delete version: %s", e)
        db.rollback()
        return False


def get_versions_for_comparison(
    db: Session,
    report_id: int,
    version_from: int,
    version_to: int
) -> tuple:
    """Get two versions for delta comparison."""
    v1 = get_report_version(db, report_id, version_from)
    v2 = get_report_version(db, report_id, version_to)
    return v1, v2


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G11] Report Registry loaded - versioning=%s, max_versions=%d",
         REPORT_VERSIONING_ENABLED, MAX_REPORT_VERSIONS)
