# -*- coding: utf-8 -*-
"""
Sprint G11: Dashboard API Routes

Provides endpoints for frontend dashboard:
- Overview with latest scores and KPIs
- Trends analysis
- AI Act compliance summary

Version: 1.0.0 (Sprint G11)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from core.db import get_session

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

ENABLE_DASHBOARD_API = os.getenv("ENABLE_DASHBOARD_API", "1").lower() in ("1", "true", "yes")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _check_enabled():
    """Check if dashboard API is enabled."""
    if not ENABLE_DASHBOARD_API:
        raise HTTPException(status_code=503, detail="Dashboard API disabled")


def _get_score_trend(versions: List[Dict]) -> Dict[str, Any]:
    """Calculate score trend from version history."""
    if len(versions) < 2:
        return {"trend": "stable", "change": 0}

    latest = versions[0].get("scores", {}).get("OVERALL_SCORE", 0) or 0
    previous = versions[1].get("scores", {}).get("OVERALL_SCORE", 0) or 0

    delta = latest - previous

    if delta > 5:
        trend = "improving"
    elif delta < -5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "change": round(delta, 1),
        "latest": latest,
        "previous": previous,
    }


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/overview")
async def get_overview(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get dashboard overview with aggregated KPIs.

    Returns:
    - Latest scores
    - Score development (last 3 versions)
    - Business case modifications
    - High-risk flag
    - Active reports count
    - Top 3 quick wins
    - KPI matrix
    """
    _check_enabled()

    try:
        from models import ReportHistory
        from services.report_registry import get_user_reports

        # Get latest reports
        if user_id:
            reports = get_user_reports(db, user_id, limit=10)
        else:
            subq = db.query(
                ReportHistory.report_id,
                func.max(ReportHistory.version).label("max_version")
            ).group_by(ReportHistory.report_id).subquery()

            latest_versions = db.query(ReportHistory).join(
                subq,
                (ReportHistory.report_id == subq.c.report_id) &
                (ReportHistory.version == subq.c.max_version)
            ).order_by(desc(ReportHistory.created_at)).limit(10).all()

            reports = [v.to_dict() for v in latest_versions]

        if not reports:
            return {
                "has_data": False,
                "message": "No reports found",
            }

        # Latest report data
        latest_report = reports[0]
        latest_scores = latest_report.get("scores", {})
        latest_bc = latest_report.get("business_case", {})
        latest_ai_act = latest_report.get("ai_act", {})

        # Score trend (last 3 versions)
        score_trend = _get_score_trend(reports[:3])

        # AI Act modifications
        ai_act_applied = latest_bc.get("AI_ACT_BC_APPLIED", False)
        risk_level = latest_ai_act.get("AI_ACT_RISK_LEVEL", "minimal")
        is_high_risk = risk_level == "high-risk"

        # BC modifications summary
        bc_mods = {}
        if ai_act_applied:
            bc_mods = {
                "capex_factor": latest_bc.get("AI_ACT_BC_CAPEX_FACTOR", 1.0),
                "opex_factor": latest_bc.get("AI_ACT_BC_OPEX_FACTOR", 1.0),
                "payback_delta": latest_bc.get("AI_ACT_BC_PAYBACK_DELTA", 0),
                "original_capex": latest_bc.get("AI_ACT_BC_ORIGINAL_CAPEX"),
                "original_opex": latest_bc.get("AI_ACT_BC_ORIGINAL_OPEX"),
            }

        # KPI matrix
        kpi_matrix = {
            "governance_score": latest_scores.get("GOVERNANCE_SCORE"),
            "security_score": latest_scores.get("SECURITY_SCORE"),
            "benefit_score": latest_scores.get("BENEFIT_SCORE"),
            "readiness_score": latest_scores.get("READINESS_SCORE"),
            "overall_score": latest_scores.get("OVERALL_SCORE"),
            "maturity_level": latest_scores.get("MATURITY_LEVEL"),
            "roi_12m": latest_bc.get("ROI_12M"),
            "payback_months": latest_bc.get("PAYBACK_MONTHS"),
            "capex": latest_bc.get("CAPEX_REALISTISCH_EUR"),
            "opex_monthly": latest_bc.get("OPEX_REALISTISCH_EUR"),
        }

        return {
            "has_data": True,
            "active_reports": len(reports),
            "latest_report": {
                "report_id": latest_report.get("report_id"),
                "version": latest_report.get("version"),
                "created_at": latest_report.get("created_at"),
                "lang": latest_report.get("lang"),
                "size_category": latest_report.get("size_category"),
            },
            "scores": latest_scores,
            "score_trend": score_trend,
            "business_case": {
                "capex": latest_bc.get("CAPEX_REALISTISCH_EUR"),
                "opex": latest_bc.get("OPEX_REALISTISCH_EUR"),
                "roi_12m": latest_bc.get("ROI_12M"),
                "payback": latest_bc.get("PAYBACK_MONTHS"),
                "ai_act_applied": ai_act_applied,
                "modifications": bc_mods,
            },
            "ai_act": {
                "risk_level": risk_level,
                "is_high_risk": is_high_risk,
                "capex_modifier": latest_ai_act.get("CAPEX_MODIFIER", 1.0),
                "opex_modifier": latest_ai_act.get("OPEX_MODIFIER", 1.0),
            },
            "kpi_matrix": kpi_matrix,
        }

    except Exception as e:
        log.error("[G11-Dashboard] Overview failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_trends(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(20, ge=5, le=50),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get trend analysis across reports.

    Returns:
    - Tools cluster (frequency in reports)
    - Risk trends
    - Industry trends
    - Funding hit rate
    """
    _check_enabled()

    try:
        from models import ReportHistory

        # Get report history
        query = db.query(ReportHistory)
        if user_id:
            query = query.filter(ReportHistory.user_id == user_id)
        history = query.order_by(desc(ReportHistory.created_at)).limit(limit).all()

        if not history:
            return {
                "has_data": False,
                "message": "No reports found for trend analysis",
            }

        # Analyze labels and scores
        branch_counts: Dict[str, int] = {}
        risk_levels: List[str] = []
        score_history: List[Dict] = []
        size_distribution: Dict[str, int] = {}

        for h in history:
            # Branch distribution
            labels = h.labels_json or {}
            branch = labels.get("BRANCH_CORE_LABEL") or labels.get("BRANCH_LABEL")
            if branch:
                branch_counts[branch] = branch_counts.get(branch, 0) + 1

            # Risk level tracking
            ai_act = h.ai_act_json or {}
            risk = ai_act.get("AI_ACT_RISK_LEVEL")
            if risk:
                risk_levels.append(risk)

            # Score history
            scores = h.scores_json or {}
            if scores.get("OVERALL_SCORE"):
                score_history.append({
                    "version": h.version,
                    "overall": scores.get("OVERALL_SCORE"),
                    "governance": scores.get("GOVERNANCE_SCORE"),
                    "security": scores.get("SECURITY_SCORE"),
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                })

            # Size distribution
            if h.size_category:
                size_distribution[h.size_category] = size_distribution.get(h.size_category, 0) + 1

        # Risk distribution
        risk_distribution: Dict[str, int] = {}
        for r in risk_levels:
            risk_distribution[r] = risk_distribution.get(r, 0) + 1

        # Top branches
        top_branches = sorted(branch_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "has_data": True,
            "reports_analyzed": len(history),
            "branch_distribution": dict(top_branches),
            "risk_distribution": risk_distribution,
            "size_distribution": size_distribution,
            "score_history": score_history[:10],  # Last 10 for chart
            "average_scores": {
                "overall": sum(s.get("overall", 0) for s in score_history) / len(score_history) if score_history else 0,
                "governance": sum(s.get("governance", 0) or 0 for s in score_history) / len(score_history) if score_history else 0,
                "security": sum(s.get("security", 0) or 0 for s in score_history) / len(score_history) if score_history else 0,
            },
        }

    except Exception as e:
        log.error("[G11-Dashboard] Trends failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-act-summary")
async def get_ai_act_summary(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get AI Act compliance summary.

    Returns:
    - Risk level
    - Required obligations
    - BC cost impacts
    - Alerts/gaps
    """
    _check_enabled()

    try:
        from models import ReportHistory

        # Get latest report
        query = db.query(ReportHistory)
        if user_id:
            query = query.filter(ReportHistory.user_id == user_id)
        latest = query.order_by(desc(ReportHistory.created_at)).first()

        if not latest:
            return {
                "has_data": False,
                "message": "No reports found",
            }

        ai_act = latest.ai_act_json or {}
        bc = latest.bc_json or {}

        risk_level = ai_act.get("AI_ACT_RISK_LEVEL", "minimal")

        # Determine obligations based on risk level
        obligations = _get_obligations_for_risk(risk_level)

        # BC cost impacts
        bc_impact = {}
        if bc.get("AI_ACT_BC_APPLIED"):
            capex_factor = bc.get("AI_ACT_BC_CAPEX_FACTOR", 1.0)
            opex_factor = bc.get("AI_ACT_BC_OPEX_FACTOR", 1.0)
            original_capex = bc.get("AI_ACT_BC_ORIGINAL_CAPEX", 0)
            original_opex = bc.get("AI_ACT_BC_ORIGINAL_OPEX", 0)

            bc_impact = {
                "capex_increase": f"+{int((capex_factor - 1) * 100)}%",
                "opex_increase": f"+{int((opex_factor - 1) * 100)}%",
                "capex_delta": bc.get("CAPEX_REALISTISCH_EUR", 0) - original_capex if original_capex else 0,
                "opex_delta": bc.get("OPEX_REALISTISCH_EUR", 0) - original_opex if original_opex else 0,
                "payback_delta_months": bc.get("AI_ACT_BC_PAYBACK_DELTA", 0),
            }

        # Alerts based on risk level
        alerts = []
        if risk_level == "high-risk":
            alerts.append({
                "severity": "high",
                "message": "Hochrisiko-KI erfordert Konformitätsbewertung",
                "action": "CE-Kennzeichnung und technische Dokumentation erforderlich",
            })
        elif risk_level == "limited":
            alerts.append({
                "severity": "medium",
                "message": "Transparenzpflichten beachten",
                "action": "Nutzer über KI-Interaktion informieren",
            })

        return {
            "has_data": True,
            "risk_level": risk_level,
            "risk_level_label": _get_risk_label(risk_level),
            "obligations": obligations,
            "bc_impact": bc_impact,
            "alerts": alerts,
            "metrics": ai_act.get("_ai_act_bc_metrics", {}),
        }

    except Exception as e:
        log.error("[G11-Dashboard] AI Act summary failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


def _get_obligations_for_risk(risk_level: str) -> List[Dict[str, Any]]:
    """Get list of obligations based on risk level."""
    if risk_level == "high-risk":
        return [
            {"id": "rms", "name": "Risikomanagementsystem", "required": True},
            {"id": "doc", "name": "Technische Dokumentation", "required": True},
            {"id": "log", "name": "Automatisches Logging", "required": True},
            {"id": "trans", "name": "Transparenz für Nutzer", "required": True},
            {"id": "human", "name": "Menschliche Aufsicht", "required": True},
            {"id": "accuracy", "name": "Genauigkeit & Robustheit", "required": True},
            {"id": "ce", "name": "CE-Konformitätsbewertung", "required": True},
        ]
    elif risk_level == "limited":
        return [
            {"id": "trans", "name": "Transparenz für Nutzer", "required": True},
            {"id": "label", "name": "KI-Kennzeichnung", "required": True},
        ]
    else:
        return [
            {"id": "best", "name": "Best Practices empfohlen", "required": False},
        ]


def _get_risk_label(risk_level: str) -> Dict[str, str]:
    """Get localized risk level labels."""
    labels = {
        "high-risk": {"de": "Hochrisiko", "en": "High Risk"},
        "limited": {"de": "Begrenztes Risiko", "en": "Limited Risk"},
        "minimal": {"de": "Minimales Risiko", "en": "Minimal Risk"},
        "none": {"de": "Kein Risiko", "en": "No Risk"},
    }
    return labels.get(risk_level, {"de": risk_level, "en": risk_level})


# =============================================================================
# SPRINT G15-C: RELEASE HEALTH ENDPOINT
# =============================================================================

@router.get("/release-health")
async def get_release_health(
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    G15-C: Get release health status for operator monitoring.

    Returns:
    - reports_last_24h: Number of reports generated in last 24 hours
    - avg_generation_time_sec: Average report generation time
    - fallback_rate_pct: Percentage of sections using fallback
    - ai_act_high_risk_share_pct: Percentage of high-risk reports
    - pdf_error_rate_pct: Percentage of PDF generation failures
    - circuit_breaker_status: Status of circuit breakers (G14)
    - overall_status: green/yellow/red based on thresholds
    """
    _check_enabled()

    try:
        from datetime import datetime, timedelta
        from models import ReportHistory

        # Import G14 metrics if available
        try:
            from services.provider_perplexity import get_circuit_status as get_pplx_circuit
            pplx_circuit = get_pplx_circuit()
        except ImportError:
            pplx_circuit = None

        try:
            from services.html_minifier import get_regex_cache_stats
            regex_cache = get_regex_cache_stats()
        except ImportError:
            regex_cache = None

        # Import release config thresholds
        try:
            from services.config_release import RELEASE_HEALTH_THRESHOLDS
            thresholds = RELEASE_HEALTH_THRESHOLDS
        except ImportError:
            thresholds = {
                "fallback_rate_pct": {"warn": 10.0, "critical": 25.0},
                "pdf_error_rate_pct": {"warn": 5.0, "critical": 15.0},
                "ai_act_high_risk_share_pct": {"warn": 50.0, "critical": 80.0},
            }

        # Get reports from last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_reports = db.query(ReportHistory).filter(
            ReportHistory.created_at >= cutoff
        ).all()

        reports_last_24h = len(recent_reports)

        # Calculate metrics from recent reports
        total_generation_time = 0.0
        fallback_count = 0
        high_risk_count = 0
        pdf_error_count = 0
        total_sections = 0

        for report in recent_reports:
            # Generation time (if available in metadata)
            meta = report.meta_json or {}
            gen_time = meta.get("generation_time_sec", 0)
            total_generation_time += gen_time

            # AI Act risk level
            ai_act = report.ai_act_json or {}
            risk_level = ai_act.get("AI_ACT_RISK_LEVEL", "minimal")
            if risk_level == "high-risk":
                high_risk_count += 1

            # Fallback tracking (if available)
            fallbacks = meta.get("fallback_sections", [])
            sections_count = meta.get("sections_generated", 10)  # default estimate
            fallback_count += len(fallbacks)
            total_sections += sections_count

            # PDF errors (if tracked)
            if meta.get("pdf_error"):
                pdf_error_count += 1

        # Calculate rates
        avg_generation_time_sec = (
            total_generation_time / reports_last_24h
            if reports_last_24h > 0 else 0.0
        )

        fallback_rate_pct = (
            (fallback_count / total_sections * 100)
            if total_sections > 0 else 0.0
        )

        ai_act_high_risk_share_pct = (
            (high_risk_count / reports_last_24h * 100)
            if reports_last_24h > 0 else 0.0
        )

        pdf_error_rate_pct = (
            (pdf_error_count / reports_last_24h * 100)
            if reports_last_24h > 0 else 0.0
        )

        # Determine overall status
        alerts = []
        overall_status = "green"

        # Check fallback rate
        if fallback_rate_pct >= thresholds["fallback_rate_pct"]["critical"]:
            overall_status = "red"
            alerts.append({
                "level": "critical",
                "metric": "fallback_rate_pct",
                "message": f"Fallback rate {fallback_rate_pct:.1f}% exceeds critical threshold",
            })
        elif fallback_rate_pct >= thresholds["fallback_rate_pct"]["warn"]:
            if overall_status != "red":
                overall_status = "yellow"
            alerts.append({
                "level": "warning",
                "metric": "fallback_rate_pct",
                "message": f"Fallback rate {fallback_rate_pct:.1f}% exceeds warning threshold",
            })

        # Check PDF error rate
        if pdf_error_rate_pct >= thresholds["pdf_error_rate_pct"]["critical"]:
            overall_status = "red"
            alerts.append({
                "level": "critical",
                "metric": "pdf_error_rate_pct",
                "message": f"PDF error rate {pdf_error_rate_pct:.1f}% exceeds critical threshold",
            })
        elif pdf_error_rate_pct >= thresholds["pdf_error_rate_pct"]["warn"]:
            if overall_status != "red":
                overall_status = "yellow"
            alerts.append({
                "level": "warning",
                "metric": "pdf_error_rate_pct",
                "message": f"PDF error rate {pdf_error_rate_pct:.1f}% exceeds warning threshold",
            })

        # Check high-risk share
        if ai_act_high_risk_share_pct >= thresholds["ai_act_high_risk_share_pct"]["critical"]:
            if overall_status != "red":
                overall_status = "yellow"  # Not critical, just informational
            alerts.append({
                "level": "info",
                "metric": "ai_act_high_risk_share_pct",
                "message": f"High-risk reports at {ai_act_high_risk_share_pct:.1f}%",
            })

        # Check circuit breaker status
        circuit_breaker_status = {}
        circuit_breaker_open_count = 0

        if pplx_circuit:
            circuit_breaker_status["perplexity"] = pplx_circuit
            if pplx_circuit.get("is_open"):
                circuit_breaker_open_count += 1
                alerts.append({
                    "level": "warning",
                    "metric": "circuit_breaker",
                    "message": "Perplexity circuit breaker is OPEN",
                })

        if circuit_breaker_open_count > 0 and overall_status != "red":
            overall_status = "yellow"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "reports_last_24h": reports_last_24h,
                "avg_generation_time_sec": round(avg_generation_time_sec, 1),
                "fallback_rate_pct": round(fallback_rate_pct, 1),
                "ai_act_high_risk_share_pct": round(ai_act_high_risk_share_pct, 1),
                "pdf_error_rate_pct": round(pdf_error_rate_pct, 1),
                "circuit_breaker_open_count": circuit_breaker_open_count,
            },
            "thresholds": thresholds,
            "alerts": alerts,
            "circuit_breakers": circuit_breaker_status,
            "cache_stats": {
                "regex_cache": regex_cache,
            },
            "release": {
                "version": "R1",
                "sprint": "G15",
            },
        }

    except Exception as e:
        log.error("[G15-C] Release health check failed: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() if "datetime" in dir() else None,
        }


@router.get("/config-validation")
async def get_config_validation() -> Dict[str, Any]:
    """
    G15-A: Get configuration validation results.

    Returns release configuration validation status.
    """
    _check_enabled()

    try:
        from services.config_validation import validate_release_config

        result = validate_release_config()
        return result.to_dict()

    except Exception as e:
        log.error("[G15-A] Config validation failed: %s", e)
        return {
            "is_valid": False,
            "errors": [str(e)],
            "warnings": [],
            "info": [],
        }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G11/G15] Dashboard API routes loaded - enabled=%s", ENABLE_DASHBOARD_API)
