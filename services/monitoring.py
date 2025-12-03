# -*- coding: utf-8 -*-
"""
services/monitoring.py - Zentraler Monitoring & Metrics Service

Version: 1.0.0 - POST-RELEASE MONITORING SPRINT
Features:
- System-weite Health-Checks
- Metrics Collection (PDF, Prompt, Guardrails, Persona, Funding)
- Alert-Trigger mit Schwellwerten
- Daily Report Generation
"""
from __future__ import annotations

import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal
from enum import Enum

log = logging.getLogger(__name__)


# =============================================================================
# Alert Severity Levels
# =============================================================================
class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


# =============================================================================
# Metrics Storage (Thread-Safe)
# =============================================================================
class MetricsStore:
    """Thread-safe in-memory metrics storage with rolling windows."""

    def __init__(self, window_hours: int = 24):
        self._lock = threading.RLock()
        self._window_hours = window_hours

        # Counters
        self._counters: Dict[str, int] = defaultdict(int)

        # Timed metrics (list of (timestamp, value) tuples)
        self._timed_metrics: Dict[str, List[tuple]] = defaultdict(list)

        # Last values (for gauges)
        self._gauges: Dict[str, Any] = {}

        # Alert history
        self._alerts: List[Dict[str, Any]] = []

        # Start time
        self._start_time = datetime.utcnow()

    def increment(self, metric: str, value: int = 1) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[metric] += value

    def record(self, metric: str, value: float) -> None:
        """Record a timed metric value."""
        with self._lock:
            now = datetime.utcnow()
            self._timed_metrics[metric].append((now, value))
            self._cleanup_old_metrics(metric)

    def set_gauge(self, metric: str, value: Any) -> None:
        """Set a gauge metric (current value)."""
        with self._lock:
            self._gauges[metric] = value

    def get_counter(self, metric: str) -> int:
        """Get counter value."""
        with self._lock:
            return self._counters.get(metric, 0)

    def get_gauge(self, metric: str) -> Any:
        """Get gauge value."""
        with self._lock:
            return self._gauges.get(metric)

    def get_avg(self, metric: str, window_minutes: int = 60) -> Optional[float]:
        """Get average of timed metric over window."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
            values = [v for ts, v in self._timed_metrics.get(metric, []) if ts > cutoff]
            if not values:
                return None
            return float(sum(values) / len(values))

    def get_max(self, metric: str, window_minutes: int = 60) -> Optional[float]:
        """Get max of timed metric over window."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
            values = [v for ts, v in self._timed_metrics.get(metric, []) if ts > cutoff]
            if not values:
                return None
            return float(max(values))

    def get_count(self, metric: str, window_minutes: int = 60) -> int:
        """Get count of timed metric entries over window."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
            return len([1 for ts, _ in self._timed_metrics.get(metric, []) if ts > cutoff])

    def add_alert(self, alert: Dict[str, Any]) -> None:
        """Add an alert to history."""
        with self._lock:
            alert["timestamp"] = datetime.utcnow().isoformat() + "Z"
            self._alerts.append(alert)
            # Keep last 1000 alerts
            if len(self._alerts) > 1000:
                self._alerts = self._alerts[-1000:]

    def get_alerts(self, window_hours: int = 24, severity: Optional[str] = None) -> List[Dict]:
        """Get alerts from history."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(hours=window_hours)
            alerts = [
                a for a in self._alerts
                if datetime.fromisoformat(a["timestamp"].rstrip("Z")) > cutoff
            ]
            if severity:
                alerts = [a for a in alerts if a.get("severity") == severity]
            return alerts

    def _cleanup_old_metrics(self, metric: str) -> None:
        """Remove metrics older than window."""
        cutoff = datetime.utcnow() - timedelta(hours=self._window_hours)
        self._timed_metrics[metric] = [
            (ts, v) for ts, v in self._timed_metrics[metric] if ts > cutoff
        ]

    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.utcnow() - self._start_time).total_seconds()

    def get_all_counters(self) -> Dict[str, int]:
        """Get all counter values."""
        with self._lock:
            return dict(self._counters)

    def get_all_gauges(self) -> Dict[str, Any]:
        """Get all gauge values."""
        with self._lock:
            return dict(self._gauges)

    def reset_counters(self) -> None:
        """Reset all counters (for daily reports)."""
        with self._lock:
            self._counters.clear()


# Global metrics store
_metrics = MetricsStore()


# =============================================================================
# Metric Recording Functions
# =============================================================================

def record_analysis_start() -> None:
    """Record start of an analysis."""
    _metrics.increment("analysis_total")
    _metrics.increment("analysis_in_progress")


def record_analysis_complete(
    duration_ms: float,
    lang: str,
    persona: str,
    fallback_sections: int = 0,
    guardrail_hits: int = 0,
    sanitizer_recovery: bool = False,
) -> None:
    """Record completion of an analysis."""
    _metrics.increment("analysis_in_progress", -1)
    _metrics.increment("analysis_success")
    _metrics.increment(f"analysis_lang_{lang}")
    _metrics.increment(f"analysis_persona_{persona}")

    _metrics.record("analysis_duration_ms", duration_ms)

    if fallback_sections > 0:
        _metrics.increment("analysis_fallbacks_total", fallback_sections)
        _metrics.record("analysis_fallback_count", fallback_sections)

    if guardrail_hits > 0:
        _metrics.increment("guardrail_hits_total", guardrail_hits)

    if sanitizer_recovery:
        _metrics.increment("sanitizer_recovery_total")


def record_analysis_error(error_type: str = "unknown") -> None:
    """Record analysis error."""
    _metrics.increment("analysis_in_progress", -1)
    _metrics.increment("analysis_errors")
    _metrics.increment(f"analysis_error_{error_type}")


def record_pdf_generation(
    size_bytes: int,
    duration_ms: float,
    success: bool = True,
    error_type: Optional[str] = None,
) -> None:
    """Record PDF generation metrics."""
    _metrics.increment("pdf_total")

    if success:
        _metrics.increment("pdf_success")
        _metrics.record("pdf_size_bytes", size_bytes)
        _metrics.record("pdf_duration_ms", duration_ms)

        size_mb = size_bytes / (1024 * 1024)
        _metrics.set_gauge("pdf_last_size_mb", size_mb)

        # Track size distribution
        if size_mb > 18:
            _metrics.increment("pdf_size_critical")  # > 18MB
        elif size_mb > 10:
            _metrics.increment("pdf_size_warning")   # > 10MB
    else:
        _metrics.increment("pdf_errors")
        if error_type:
            _metrics.increment(f"pdf_error_{error_type}")


def record_guardrail_detection(
    hits: int,
    high_confidence: int = 0,
    lang: str = "de",
) -> None:
    """Record guardrail detection."""
    _metrics.increment("guardrail_detections")
    _metrics.increment("guardrail_hits_total", hits)
    _metrics.increment(f"guardrail_hits_{lang}", hits)

    if high_confidence > 0:
        _metrics.increment("guardrail_high_confidence", high_confidence)


def record_persona_assignment(
    persona: str,
    lang: str,
    token_budget_used: int = 0,
    token_budget_max: int = 0,
) -> None:
    """Record persona assignment."""
    _metrics.increment(f"persona_{persona}")
    _metrics.increment(f"persona_{persona}_{lang}")

    if token_budget_max > 0:
        utilization = (token_budget_used / token_budget_max) * 100
        _metrics.record("token_utilization_pct", utilization)

        if utilization > 95:
            _metrics.increment("token_budget_exceeded")


def record_funding_routing(
    scope: str,
    country: str,
    lang: str,
    program_count: int = 0,
) -> None:
    """Record funding routing decision."""
    _metrics.increment("funding_queries")
    _metrics.increment(f"funding_scope_{scope}")
    _metrics.increment(f"funding_country_{country}")
    _metrics.increment(f"funding_lang_{lang}")

    if program_count > 0:
        _metrics.record("funding_programs_returned", program_count)


def record_research_query(
    provider: str,
    success: bool,
    duration_ms: float,
    sources_count: int = 0,
) -> None:
    """Record research/search query."""
    _metrics.increment("research_queries")
    _metrics.increment(f"research_provider_{provider}")

    if success:
        _metrics.increment("research_success")
        _metrics.record("research_duration_ms", duration_ms)
        _metrics.record("research_sources", sources_count)
    else:
        _metrics.increment("research_errors")
        _metrics.increment(f"research_error_{provider}")


def record_llm_call(
    provider: str,
    model: str,
    tokens_used: int,
    duration_ms: float,
    success: bool = True,
) -> None:
    """Record LLM API call."""
    _metrics.increment("llm_calls_total")
    _metrics.increment(f"llm_provider_{provider}")

    if success:
        _metrics.increment("llm_success")
        _metrics.record("llm_duration_ms", duration_ms)
        _metrics.record("llm_tokens", tokens_used)
    else:
        _metrics.increment("llm_errors")


def record_section_generation(
    section: str,
    success: bool,
    is_fallback: bool = False,
    word_count: int = 0,
) -> None:
    """Record section generation."""
    _metrics.increment(f"section_{section}_total")

    if success:
        _metrics.increment(f"section_{section}_success")
        if word_count > 0:
            _metrics.record(f"section_{section}_words", word_count)
    else:
        _metrics.increment(f"section_{section}_error")

    if is_fallback:
        _metrics.increment(f"section_{section}_fallback")
        _metrics.increment("section_fallbacks_total")


# =============================================================================
# Health Check Functions
# =============================================================================

def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health status."""
    import psutil

    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
    except Exception as e:
        log.warning("Could not get system metrics: %s", e)
        cpu_percent = -1
        memory = None
        disk = None

    return {
        "status": "healthy",
        "uptime_seconds": _metrics.get_uptime_seconds(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent if memory else -1,
            "memory_available_mb": (memory.available / (1024 * 1024)) if memory else -1,
            "disk_percent": disk.percent if disk else -1,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def get_service_status() -> Dict[str, Any]:
    """Get status of all monitored services."""
    from sqlalchemy import text
    from core.db import SessionLocal

    services = {}

    # Database connectivity
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        services["database"] = {"status": "ok", "latency_ms": 0}
    except Exception as e:
        services["database"] = {"status": "error", "error": str(e)}

    # PDF service
    pdf_url = os.getenv("PDF_SERVICE_URL", "")
    if pdf_url:
        try:
            import requests
            r = requests.get(f"{pdf_url.rstrip('/')}/health", timeout=5)
            services["pdf_service"] = {
                "status": "ok" if r.ok else "degraded",
                "latency_ms": r.elapsed.total_seconds() * 1000,
            }
        except Exception as e:
            services["pdf_service"] = {"status": "error", "error": str(e)}
    else:
        services["pdf_service"] = {"status": "not_configured"}

    # Redis (optional)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            services["redis"] = {"status": "ok"}
        except Exception as e:
            services["redis"] = {"status": "error", "error": str(e)}
    else:
        services["redis"] = {"status": "not_configured"}

    return services


def get_extended_health() -> Dict[str, Any]:
    """Get extended health check with all metrics."""
    system = get_system_health()
    services = get_service_status()

    # Calculate overall status
    service_statuses = [s.get("status") for s in services.values()]
    if "error" in service_statuses:
        overall = "degraded"
    elif "degraded" in service_statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "system": system["system"],
        "services": services,
        "uptime_seconds": system["uptime_seconds"],
        "timestamp": system["timestamp"],
    }


def get_monitoring_status() -> Dict[str, Any]:
    """Get full monitoring status for /api/monitoring/status."""

    # Analysis metrics
    analysis_avg_ms = _metrics.get_avg("analysis_duration_ms", 60) or 0
    pdf_avg_mb = (_metrics.get_avg("pdf_size_bytes", 60) or 0) / (1024 * 1024)

    # Error rates (last hour)
    analysis_total = _metrics.get_count("analysis_duration_ms", 60)
    analysis_errors = _metrics.get_counter("analysis_errors")
    llm_total = _metrics.get_counter("llm_calls_total")
    llm_errors = _metrics.get_counter("llm_errors")
    research_total = _metrics.get_counter("research_queries")
    research_errors = _metrics.get_counter("research_errors")

    return {
        "system_load": get_system_health()["system"],
        "queue_length": _metrics.get_counter("analysis_in_progress"),
        "avg_analysis_time_ms": round(analysis_avg_ms, 2),
        "avg_pdf_size_mb": round(pdf_avg_mb, 2),
        "last_pdf_size_mb": _metrics.get_gauge("pdf_last_size_mb"),
        "llm_error_rate": (llm_errors / llm_total * 100) if llm_total > 0 else 0,
        "research_error_rate": (research_errors / research_total * 100) if research_total > 0 else 0,
        "funding_routing_matrix": {
            "de": _metrics.get_counter("funding_scope_de"),
            "de_en": _metrics.get_counter("funding_scope_de_en"),
            "eu_core": _metrics.get_counter("funding_scope_eu_core"),
        },
        "guardrail_hit_rate": _metrics.get_counter("guardrail_detections"),
        "persona_distribution": {
            "solo": _metrics.get_counter("persona_solo"),
            "team": _metrics.get_counter("persona_team"),
            "kmu": _metrics.get_counter("persona_kmu"),
        },
        "html_sanitizer_failures": _metrics.get_counter("sanitizer_recovery_total"),
        "missing_sections_count": _metrics.get_counter("section_fallbacks_total"),
        "counters": _metrics.get_all_counters(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def get_diagnostics() -> Dict[str, Any]:
    """Get detailed diagnostics for /api/report/diagnostics."""
    return {
        "analysis": {
            "total": _metrics.get_counter("analysis_total"),
            "success": _metrics.get_counter("analysis_success"),
            "errors": _metrics.get_counter("analysis_errors"),
            "avg_duration_ms": _metrics.get_avg("analysis_duration_ms", 60),
            "by_lang": {
                "de": _metrics.get_counter("analysis_lang_de"),
                "en": _metrics.get_counter("analysis_lang_en"),
            },
            "by_persona": {
                "solo": _metrics.get_counter("analysis_persona_solo"),
                "team": _metrics.get_counter("analysis_persona_team"),
                "kmu": _metrics.get_counter("analysis_persona_kmu"),
            },
        },
        "pdf": {
            "total": _metrics.get_counter("pdf_total"),
            "success": _metrics.get_counter("pdf_success"),
            "errors": _metrics.get_counter("pdf_errors"),
            "avg_size_mb": (_metrics.get_avg("pdf_size_bytes", 60) or 0) / (1024 * 1024),
            "max_size_mb": (_metrics.get_max("pdf_size_bytes", 60) or 0) / (1024 * 1024),
            "size_warnings": _metrics.get_counter("pdf_size_warning"),
            "size_critical": _metrics.get_counter("pdf_size_critical"),
        },
        "guardrails": {
            "detections": _metrics.get_counter("guardrail_detections"),
            "total_hits": _metrics.get_counter("guardrail_hits_total"),
            "high_confidence": _metrics.get_counter("guardrail_high_confidence"),
        },
        "sections": {
            "fallbacks_total": _metrics.get_counter("section_fallbacks_total"),
            "by_section": {
                "roadmap_12m_fallback": _metrics.get_counter("section_roadmap_12m_fallback"),
                "roadmap_90d_fallback": _metrics.get_counter("section_roadmap_90d_fallback"),
                "exec_summary_fallback": _metrics.get_counter("section_exec_summary_fallback"),
            },
        },
        "llm": {
            "total_calls": _metrics.get_counter("llm_calls_total"),
            "errors": _metrics.get_counter("llm_errors"),
            "avg_duration_ms": _metrics.get_avg("llm_duration_ms", 60),
            "avg_tokens": _metrics.get_avg("llm_tokens", 60),
        },
        "research": {
            "queries": _metrics.get_counter("research_queries"),
            "success": _metrics.get_counter("research_success"),
            "errors": _metrics.get_counter("research_errors"),
            "avg_sources": _metrics.get_avg("research_sources", 60),
        },
        "alerts_24h": len(_metrics.get_alerts(24)),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# =============================================================================
# Daily Report Generation
# =============================================================================

def generate_daily_report() -> Dict[str, Any]:
    """Generate daily monitoring report."""

    counters = _metrics.get_all_counters()

    # System KPIs
    system_kpis = {
        "reports_de": counters.get("analysis_lang_de", 0),
        "reports_en": counters.get("analysis_lang_en", 0),
        "avg_analysis_time_ms": _metrics.get_avg("analysis_duration_ms", 1440),  # 24h
        "avg_pdf_size_mb": (_metrics.get_avg("pdf_size_bytes", 1440) or 0) / (1024 * 1024),
        "pdf_success_rate": (
            counters.get("pdf_success", 0) / counters.get("pdf_total", 1) * 100
        ),
        "guardrail_hits": counters.get("guardrail_hits_total", 0),
        "fallbacks": counters.get("section_fallbacks_total", 0),
        "sanitizer_failures": counters.get("sanitizer_recovery_total", 0),
        "persona_mismatches": counters.get("persona_mismatch", 0),
    }

    # Funding KPIs
    funding_kpis = {
        "scope_distribution": {
            "de": counters.get("funding_scope_de", 0),
            "de_en": counters.get("funding_scope_de_en", 0),
            "eu_core": counters.get("funding_scope_eu_core", 0),
        },
        "total_queries": counters.get("funding_queries", 0),
    }

    # Prompt Engine KPIs
    prompt_kpis = {
        "section_calls": {k: v for k, v in counters.items() if k.startswith("section_") and k.endswith("_total")},
        "token_over_budget": counters.get("token_budget_exceeded", 0),
        "avg_token_utilization": _metrics.get_avg("token_utilization_pct", 1440),
    }

    # Alerts summary
    alerts_24h = _metrics.get_alerts(24)
    alerts_summary = {
        "total": len(alerts_24h),
        "by_severity": {
            "critical": len([a for a in alerts_24h if a.get("severity") == "critical"]),
            "alert": len([a for a in alerts_24h if a.get("severity") == "alert"]),
            "warning": len([a for a in alerts_24h if a.get("severity") == "warning"]),
            "info": len([a for a in alerts_24h if a.get("severity") == "info"]),
        },
    }

    return {
        "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "system_kpis": system_kpis,
        "funding_kpis": funding_kpis,
        "prompt_kpis": prompt_kpis,
        "alerts_summary": alerts_summary,
        "alerts_detail": alerts_24h[-20:],  # Last 20 alerts
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def format_daily_report_html(report: Dict[str, Any]) -> str:
    """Format daily report as HTML email."""
    kpis = report["system_kpis"]
    funding = report["funding_kpis"]
    alerts = report["alerts_summary"]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .kpi {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .kpi h3 {{ margin: 0 0 10px 0; color: #333; }}
            .metric {{ display: inline-block; margin: 5px 15px 5px 0; }}
            .value {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
            .label {{ font-size: 12px; color: #666; }}
            .alert-critical {{ color: #dc2626; }}
            .alert-warning {{ color: #f59e0b; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>Daily Monitoring Report</h1>
        <p>Report Date: {report['report_date']}</p>

        <div class="kpi">
            <h3>System KPIs</h3>
            <div class="metric">
                <div class="value">{kpis['reports_de'] + kpis['reports_en']}</div>
                <div class="label">Total Reports</div>
            </div>
            <div class="metric">
                <div class="value">{kpis['reports_de']} / {kpis['reports_en']}</div>
                <div class="label">DE / EN</div>
            </div>
            <div class="metric">
                <div class="value">{kpis['avg_analysis_time_ms']:.0f}ms</div>
                <div class="label">Avg Analysis Time</div>
            </div>
            <div class="metric">
                <div class="value">{kpis['avg_pdf_size_mb']:.1f}MB</div>
                <div class="label">Avg PDF Size</div>
            </div>
            <div class="metric">
                <div class="value">{kpis['pdf_success_rate']:.1f}%</div>
                <div class="label">PDF Success Rate</div>
            </div>
            <div class="metric">
                <div class="value">{kpis['fallbacks']}</div>
                <div class="label">Fallbacks</div>
            </div>
        </div>

        <div class="kpi">
            <h3>Funding KPIs</h3>
            <div class="metric">
                <div class="value">{funding['total_queries']}</div>
                <div class="label">Total Queries</div>
            </div>
            <div class="metric">
                <div class="value">{funding['scope_distribution']['de']}</div>
                <div class="label">DE Scope</div>
            </div>
            <div class="metric">
                <div class="value">{funding['scope_distribution']['de_en']}</div>
                <div class="label">DE-EN Scope</div>
            </div>
            <div class="metric">
                <div class="value">{funding['scope_distribution']['eu_core']}</div>
                <div class="label">EU Core</div>
            </div>
        </div>

        <div class="kpi">
            <h3>Alerts (24h)</h3>
            <div class="metric">
                <div class="value {'alert-critical' if alerts['by_severity']['critical'] > 0 else ''}">{alerts['by_severity']['critical']}</div>
                <div class="label">Critical</div>
            </div>
            <div class="metric">
                <div class="value {'alert-warning' if alerts['by_severity']['alert'] > 0 else ''}">{alerts['by_severity']['alert']}</div>
                <div class="label">Alert</div>
            </div>
            <div class="metric">
                <div class="value">{alerts['by_severity']['warning']}</div>
                <div class="label">Warning</div>
            </div>
            <div class="metric">
                <div class="value">{alerts['total']}</div>
                <div class="label">Total</div>
            </div>
        </div>

        <p style="color: #666; font-size: 12px;">Generated at {report['generated_at']}</p>
    </body>
    </html>
    """
    return html


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AlertSeverity",
    "MetricsStore",
    "record_analysis_start",
    "record_analysis_complete",
    "record_analysis_error",
    "record_pdf_generation",
    "record_guardrail_detection",
    "record_persona_assignment",
    "record_funding_routing",
    "record_research_query",
    "record_llm_call",
    "record_section_generation",
    "get_system_health",
    "get_service_status",
    "get_extended_health",
    "get_monitoring_status",
    "get_diagnostics",
    "generate_daily_report",
    "format_daily_report_html",
]
