# -*- coding: utf-8 -*-
"""
routes/monitoring.py - Monitoring & Health Check Endpoints

Version: 1.0.0 - POST-RELEASE MONITORING SPRINT
Endpoints:
- GET /api/healthz/extended - Extended health check
- GET /api/report/diagnostics - Detailed diagnostics
- GET /api/monitoring/status - Full monitoring status
- GET /api/monitoring/alerts - Alert history
- POST /api/monitoring/daily-report - Trigger daily report
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from services.monitoring import (
    get_extended_health,
    get_monitoring_status,
    get_diagnostics,
    generate_daily_report,
    format_daily_report_html,
)
from services.alerts import get_alert_manager, AlertSeverity

log = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Health Check Endpoints
# =============================================================================

@router.get("/healthz/extended", response_class=JSONResponse)
async def healthz_extended() -> JSONResponse:
    """
    Extended health check with service status.

    Returns system health, service connectivity, and uptime.
    """
    try:
        health = get_extended_health()
        status_code = 200 if health["status"] == "healthy" else 503
        return JSONResponse(
            content=health,
            status_code=status_code,
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        log.exception("Extended health check failed: %s", e)
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            status_code=500,
            media_type="application/json; charset=utf-8",
        )


@router.get("/report/diagnostics", response_class=JSONResponse)
async def report_diagnostics() -> JSONResponse:
    """
    Detailed diagnostics for report generation.

    Returns metrics for analysis, PDF, guardrails, sections, LLM, and research.
    """
    try:
        diagnostics = get_diagnostics()
        return JSONResponse(
            content=diagnostics,
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        log.exception("Diagnostics failed: %s", e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
            media_type="application/json; charset=utf-8",
        )


# =============================================================================
# Monitoring Endpoints
# =============================================================================

@router.get("/monitoring/status", response_class=JSONResponse)
async def monitoring_status() -> JSONResponse:
    """
    Full monitoring status.

    Returns:
    - system_load: CPU, memory, disk usage
    - queue_length: Active analysis queue
    - avg_analysis_time_ms: Average analysis duration
    - avg_pdf_size_mb: Average PDF size
    - llm_error_rate: LLM API error percentage
    - research_error_rate: Research API error percentage
    - funding_routing_matrix: Funding scope distribution
    - guardrail_hit_rate: Total guardrail detections
    - persona_distribution: Solo/Team/KMU counts
    - html_sanitizer_failures: Recovery count
    - missing_sections_count: Total fallbacks
    """
    try:
        status = get_monitoring_status()
        return JSONResponse(
            content=status,
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        log.exception("Monitoring status failed: %s", e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
            media_type="application/json; charset=utf-8",
        )


@router.get("/monitoring/alerts", response_class=JSONResponse)
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, alert, critical"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum alerts to return"),
) -> JSONResponse:
    """
    Get alert history.

    Query params:
    - severity: Filter by severity level
    - hours: Time window (default 24h, max 168h/7 days)
    - limit: Max alerts to return (default 100)
    """
    try:
        manager = get_alert_manager()

        # Parse severity filter
        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid severity. Must be one of: info, warning, alert, critical",
                )

        alerts = manager.get_alerts(severity=severity_filter, limit=limit)

        # Filter by time window
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        alerts = [
            a for a in alerts
            if datetime.fromisoformat(a.timestamp.rstrip("Z")) > cutoff
        ]

        return JSONResponse(
            content={
                "alerts": [a.to_dict() for a in alerts],
                "count": len(alerts),
                "window_hours": hours,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            media_type="application/json; charset=utf-8",
        )
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Get alerts failed: %s", e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
            media_type="application/json; charset=utf-8",
        )


# =============================================================================
# Daily Report Endpoint
# =============================================================================

@router.post("/monitoring/daily-report", response_class=JSONResponse)
async def trigger_daily_report(
    background: BackgroundTasks,
    send_email: bool = Query(True, description="Send report via email"),
) -> JSONResponse:
    """
    Trigger daily monitoring report generation.

    If send_email=True, sends report to ADMIN_NOTIFY_EMAIL and ADMIN_FEEDBACK_EMAIL.
    """
    try:
        report = generate_daily_report()

        if send_email:
            background.add_task(_send_daily_report_email, report)

        return JSONResponse(
            content={
                "status": "generated",
                "email_queued": send_email,
                "report": report,
            },
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        log.exception("Daily report generation failed: %s", e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
            media_type="application/json; charset=utf-8",
        )


async def _send_daily_report_email(report: Dict[str, Any]) -> None:
    """Send daily report via email."""
    import asyncio

    admin_notify = os.getenv("ADMIN_NOTIFY_EMAIL")
    admin_feedback = os.getenv("ADMIN_FEEDBACK_EMAIL")

    recipients = [e for e in [admin_notify, admin_feedback] if e]
    if not recipients:
        log.warning("No admin email configured, skipping daily report email")
        return

    try:
        from services.mailer import Mailer
        from settings import get_settings

        mailer = Mailer.from_settings(get_settings())
        html_content = format_daily_report_html(report)

        subject = f"[KI-Backend] Daily Monitoring Report - {report['report_date']}"

        # Plain text summary
        kpis = report["system_kpis"]
        text = f"""
Daily Monitoring Report - {report['report_date']}

System KPIs:
- Total Reports: {kpis['reports_de'] + kpis['reports_en']} (DE: {kpis['reports_de']}, EN: {kpis['reports_en']})
- Avg Analysis Time: {kpis['avg_analysis_time_ms']:.0f}ms
- Avg PDF Size: {kpis['avg_pdf_size_mb']:.1f}MB
- PDF Success Rate: {kpis['pdf_success_rate']:.1f}%
- Fallbacks: {kpis['fallbacks']}
- Guardrail Hits: {kpis['guardrail_hits']}

Alerts (24h): {report['alerts_summary']['total']}
- Critical: {report['alerts_summary']['by_severity']['critical']}
- Alert: {report['alerts_summary']['by_severity']['alert']}
- Warning: {report['alerts_summary']['by_severity']['warning']}

Generated at {report['generated_at']}
        """

        for recipient in recipients:
            try:
                await mailer.send(to=recipient, subject=subject, text=text, html=html_content)
                log.info("Daily report sent to %s", recipient)
            except Exception as e:
                log.error("Failed to send daily report to %s: %s", recipient, e)

    except Exception as e:
        log.exception("Daily report email failed: %s", e)


# =============================================================================
# Metrics Endpoint (Prometheus-compatible format)
# =============================================================================

@router.get("/monitoring/metrics", response_class=JSONResponse)
async def get_metrics() -> JSONResponse:
    """
    Get metrics in a structured format.

    Returns all counters and gauges for external monitoring integration.
    """
    try:
        from services.monitoring import _metrics

        return JSONResponse(
            content={
                "counters": _metrics.get_all_counters(),
                "gauges": _metrics.get_all_gauges(),
                "uptime_seconds": _metrics.get_uptime_seconds(),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        log.exception("Get metrics failed: %s", e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
            media_type="application/json; charset=utf-8",
        )


# =============================================================================
# Prometheus Text Format (optional)
# =============================================================================

@router.get("/monitoring/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics() -> PlainTextResponse:
    """
    Get metrics in Prometheus text exposition format.
    """
    try:
        from services.monitoring import _metrics

        lines: list[str] = []
        counters = _metrics.get_all_counters()
        gauges = _metrics.get_all_gauges()

        # Counters
        for name, value in counters.items():
            metric_name = f"kibackend_{name}"
            lines.append(f"# TYPE {metric_name} counter")
            lines.append(f"{metric_name} {value}")

        # Gauges
        for name, value in gauges.items():
            if isinstance(value, (int, float)):
                metric_name = f"kibackend_{name}"
                lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f"{metric_name} {value}")

        # Uptime
        lines.append("# TYPE kibackend_uptime_seconds gauge")
        lines.append(f"kibackend_uptime_seconds {_metrics.get_uptime_seconds():.0f}")

        return PlainTextResponse(
            content="\n".join(lines),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    except Exception as e:
        log.exception("Prometheus metrics failed: %s", e)
        return PlainTextResponse(content=f"# Error: {e}", status_code=500)
