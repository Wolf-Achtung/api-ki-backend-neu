# -*- coding: utf-8 -*-
"""
services/alerts.py - Alert & Notification Service

Version: 1.0.0 - POST-RELEASE MONITORING SPRINT
Features:
- PDF Alerts (size thresholds, timeouts)
- Prompt-Engine Alerts (missing sections, fallbacks)
- Guardrails Alerts (unexpected hits, high confidence)
- Persona Alerts (term mismatches, token overflow)
- Funding Alerts (routing errors, outdated programs)
- Auto-notification via Email
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

log = logging.getLogger(__name__)


# =============================================================================
# Alert Configuration
# =============================================================================

class AlertType(str, Enum):
    # PDF Alerts
    PDF_SIZE_WARNING = "pdf_size_warning"          # > 10MB
    PDF_SIZE_ALERT = "pdf_size_alert"              # > 18MB
    PDF_SIZE_BLOCK = "pdf_size_block"              # > 20MB
    PDF_TIMEOUT = "pdf_timeout"                     # > 20s

    # Prompt-Engine Alerts
    MISSING_SECTION = "missing_section"
    ZERO_WORD_RESPONSE = "zero_word_response"
    ROADMAP_12M_FALLBACK = "roadmap_12m_fallback"
    MULTIPLE_FALLBACKS = "multiple_fallbacks"       # >= 3 in one report

    # Guardrails Alerts
    UNEXPECTED_GUARDRAIL = "unexpected_guardrail"
    HIGH_CONFIDENCE_HIT = "high_confidence_hit"     # confidence > 0.9

    # Persona Alerts
    PERSONA_TERM_MISMATCH = "persona_term_mismatch"  # Solo with Team terms
    PERSONA_TOKEN_OVERFLOW = "persona_token_overflow"

    # Funding Alerts
    FUNDING_ROUTING_ERROR = "funding_routing_error"
    FUNDING_OUTDATED = "funding_outdated"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure."""
    type: AlertType
    severity: AlertSeverity
    message: str
    details: Dict[str, Any]
    timestamp: str = ""
    notified: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "notified": self.notified,
        }


# =============================================================================
# Alert Thresholds Configuration
# =============================================================================

# PDF Thresholds (in MB)
PDF_WARN_SIZE_MB = float(os.getenv("PDF_WARN_SIZE_MB", "10"))
PDF_ALERT_SIZE_MB = float(os.getenv("PDF_ALERT_SIZE_MB", "18"))
PDF_BLOCK_SIZE_MB = float(os.getenv("PDF_BLOCK_SIZE_MB", "20"))
PDF_TIMEOUT_SEC = float(os.getenv("PDF_TIMEOUT_SEC", "20"))

# Prompt-Engine Thresholds
MIN_SECTION_WORDS = int(os.getenv("MIN_SECTION_WORDS", "50"))
MAX_FALLBACKS_PER_REPORT = int(os.getenv("MAX_FALLBACKS_PER_REPORT", "3"))

# Guardrails Thresholds
HIGH_CONFIDENCE_THRESHOLD = float(os.getenv("GUARDRAIL_HIGH_CONF", "0.9"))

# Standard-Branchen (keine unerwarteten Guardrails)
STANDARD_BRANCHES = [
    "IT/Technologie",
    "Beratung",
    "Marketing",
    "E-Commerce",
    "Produktion",
    "Handel",
]

# Persona-verbotene Begriffe
SOLO_FORBIDDEN_TERMS = ["Abteilung", "Abteilungen", "Team", "Teams", "Fachbereich", "Fachbereiche", "Projektteam"]
KMU_FORBIDDEN_PRONOUNS = ["Sie"]  # Should use "Ihr Unternehmen" instead


# =============================================================================
# Alert Manager
# =============================================================================

class AlertManager:
    """Manages alert creation, storage, and notification."""

    def __init__(self):
        self._alerts: List[Alert] = []
        self._notification_handlers: List[Callable[[Alert], None]] = []
        self._max_alerts = 1000

    def register_handler(self, handler: Callable[[Alert], None]) -> None:
        """Register a notification handler."""
        self._notification_handlers.append(handler)

    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        notify: bool = True,
    ) -> Alert:
        """Create and store an alert."""
        alert = Alert(
            type=alert_type,
            severity=severity,
            message=message,
            details=details or {},
        )

        self._alerts.append(alert)

        # Trim old alerts
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts:]

        log.warning(
            "ALERT [%s] %s: %s",
            severity.value.upper(),
            alert_type.value,
            message,
        )

        # Notify if critical or alert level
        if notify and severity in (AlertSeverity.ALERT, AlertSeverity.CRITICAL):
            self._notify(alert)

        # Import and record to metrics
        try:
            from services.monitoring import _metrics
            _metrics.add_alert(alert.to_dict())
        except ImportError:
            pass

        return alert

    def _notify(self, alert: Alert) -> None:
        """Send notifications for alert."""
        for handler in self._notification_handlers:
            try:
                handler(alert)
                alert.notified = True
            except Exception as e:
                log.error("Alert notification failed: %s", e)

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """Get alerts with optional filtering."""
        alerts = self._alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if alert_type:
            alerts = [a for a in alerts if a.type == alert_type]

        return alerts[-limit:]


# Global alert manager
_alert_manager = AlertManager()


# =============================================================================
# Alert Check Functions
# =============================================================================

def check_pdf_size(size_bytes: int, report_id: str = "") -> Optional[Alert]:
    """Check PDF size and create alerts if needed."""
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > PDF_BLOCK_SIZE_MB:
        return _alert_manager.create_alert(
            AlertType.PDF_SIZE_BLOCK,
            AlertSeverity.CRITICAL,
            f"PDF blocked: {size_mb:.1f}MB exceeds {PDF_BLOCK_SIZE_MB}MB limit",
            {"size_mb": size_mb, "limit_mb": PDF_BLOCK_SIZE_MB, "report_id": report_id},
        )
    elif size_mb > PDF_ALERT_SIZE_MB:
        return _alert_manager.create_alert(
            AlertType.PDF_SIZE_ALERT,
            AlertSeverity.ALERT,
            f"PDF alert: {size_mb:.1f}MB approaching limit",
            {"size_mb": size_mb, "limit_mb": PDF_BLOCK_SIZE_MB, "report_id": report_id},
        )
    elif size_mb > PDF_WARN_SIZE_MB:
        return _alert_manager.create_alert(
            AlertType.PDF_SIZE_WARNING,
            AlertSeverity.WARNING,
            f"PDF warning: {size_mb:.1f}MB is large",
            {"size_mb": size_mb, "report_id": report_id},
            notify=False,
        )
    return None


def check_pdf_timeout(duration_ms: float, report_id: str = "") -> Optional[Alert]:
    """Check PDF generation timeout."""
    duration_sec = duration_ms / 1000

    if duration_sec > PDF_TIMEOUT_SEC:
        return _alert_manager.create_alert(
            AlertType.PDF_TIMEOUT,
            AlertSeverity.ALERT,
            f"PDF timeout: {duration_sec:.1f}s exceeds {PDF_TIMEOUT_SEC}s threshold",
            {"duration_sec": duration_sec, "threshold_sec": PDF_TIMEOUT_SEC, "report_id": report_id},
        )
    return None


def check_section_content(
    section: str,
    word_count: int,
    is_fallback: bool,
    report_id: str = "",
) -> Optional[Alert]:
    """Check section content quality."""
    if word_count == 0:
        return _alert_manager.create_alert(
            AlertType.ZERO_WORD_RESPONSE,
            AlertSeverity.ALERT,
            f"Zero-word response for section: {section}",
            {"section": section, "report_id": report_id},
        )

    if is_fallback and section == "roadmap_12m":
        return _alert_manager.create_alert(
            AlertType.ROADMAP_12M_FALLBACK,
            AlertSeverity.ALERT,
            f"Roadmap 12M fallback triggered",
            {"section": section, "report_id": report_id},
        )

    return None


def check_multiple_fallbacks(fallback_count: int, report_id: str = "") -> Optional[Alert]:
    """Check if report has too many fallbacks."""
    if fallback_count >= MAX_FALLBACKS_PER_REPORT:
        return _alert_manager.create_alert(
            AlertType.MULTIPLE_FALLBACKS,
            AlertSeverity.WARNING,
            f"Report has {fallback_count} fallbacks (threshold: {MAX_FALLBACKS_PER_REPORT})",
            {"fallback_count": fallback_count, "threshold": MAX_FALLBACKS_PER_REPORT, "report_id": report_id},
        )
    return None


def check_guardrail_hit(
    hits: List[Dict[str, Any]],
    branch: str,
    report_id: str = "",
) -> List[Alert]:
    """Check guardrail hits for unexpected patterns."""
    alerts = []

    # Check for high confidence hits
    high_conf_hits = [h for h in hits if h.get("confidence", 0) > HIGH_CONFIDENCE_THRESHOLD]
    if high_conf_hits:
        alerts.append(_alert_manager.create_alert(
            AlertType.HIGH_CONFIDENCE_HIT,
            AlertSeverity.INFO,
            f"{len(high_conf_hits)} high-confidence guardrail hits (>{HIGH_CONFIDENCE_THRESHOLD})",
            {"hits": high_conf_hits, "branch": branch, "report_id": report_id},
            notify=False,
        ))

    # Check for unexpected guardrails in standard branches
    if branch in STANDARD_BRANCHES and hits:
        alerts.append(_alert_manager.create_alert(
            AlertType.UNEXPECTED_GUARDRAIL,
            AlertSeverity.WARNING,
            f"Unexpected guardrails in standard branch: {branch}",
            {"branch": branch, "hit_count": len(hits), "report_id": report_id},
            notify=False,
        ))

    return alerts


def check_persona_terms(
    persona: str,
    content: str,
    section: str,
    report_id: str = "",
) -> Optional[Alert]:
    """Check for persona term mismatches."""
    if persona == "solo":
        for term in SOLO_FORBIDDEN_TERMS:
            if term.lower() in content.lower():
                return _alert_manager.create_alert(
                    AlertType.PERSONA_TERM_MISMATCH,
                    AlertSeverity.WARNING,
                    f"Solo report contains forbidden term: '{term}' in {section}",
                    {"persona": persona, "term": term, "section": section, "report_id": report_id},
                    notify=False,
                )
    return None


def check_token_budget(
    tokens_used: int,
    tokens_max: int,
    persona: str,
    report_id: str = "",
) -> Optional[Alert]:
    """Check token budget utilization."""
    if tokens_max > 0 and tokens_used > tokens_max:
        return _alert_manager.create_alert(
            AlertType.PERSONA_TOKEN_OVERFLOW,
            AlertSeverity.WARNING,
            f"Token overflow: {tokens_used} > {tokens_max} for persona {persona}",
            {"tokens_used": tokens_used, "tokens_max": tokens_max, "persona": persona, "report_id": report_id},
            notify=False,
        )
    return None


def check_funding_routing(
    country: str,
    lang: str,
    scope: str,
    branch: str,
    report_id: str = "",
) -> Optional[Alert]:
    """Check funding routing consistency."""
    # DE country but EU-Core routing
    if country == "DE" and scope == "eu_core":
        return _alert_manager.create_alert(
            AlertType.FUNDING_ROUTING_ERROR,
            AlertSeverity.WARNING,
            f"Funding routing mismatch: country=DE but scope=eu_core",
            {"country": country, "scope": scope, "lang": lang, "branch": branch, "report_id": report_id},
            notify=False,
        )

    # EU-Core scope but DE branch hints
    if scope == "eu_core" and branch in ["Handwerk", "Mittelstand", "Freiberufler"]:
        return _alert_manager.create_alert(
            AlertType.FUNDING_ROUTING_ERROR,
            AlertSeverity.WARNING,
            f"EU-Core scope but DE-specific branch: {branch}",
            {"country": country, "scope": scope, "branch": branch, "report_id": report_id},
            notify=False,
        )

    return None


# =============================================================================
# Email Notification Handler
# =============================================================================

async def send_alert_email(alert: Alert) -> None:
    """Send alert notification email."""
    admin_email = os.getenv("ADMIN_NOTIFY_EMAIL")
    if not admin_email:
        log.warning("ADMIN_NOTIFY_EMAIL not set, skipping alert notification")
        return

    try:
        from services.mailer import Mailer
        from settings import get_settings

        mailer = Mailer.from_settings(get_settings())

        subject = f"[{alert.severity.value.upper()}] KI-Backend Alert: {alert.type.value}"

        body = f"""
Alert Type: {alert.type.value}
Severity: {alert.severity.value}
Timestamp: {alert.timestamp}

Message: {alert.message}

Details:
{_format_details(alert.details)}

---
KI-Backend Monitoring System
        """

        html = f"""
        <html>
        <body style="font-family: sans-serif;">
            <h2 style="color: {'#dc2626' if alert.severity == AlertSeverity.CRITICAL else '#f59e0b'};">
                [{alert.severity.value.upper()}] {alert.type.value}
            </h2>
            <p><strong>Message:</strong> {alert.message}</p>
            <p><strong>Timestamp:</strong> {alert.timestamp}</p>
            <h3>Details</h3>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">
{_format_details(alert.details)}
            </pre>
            <hr>
            <p style="color: #666; font-size: 12px;">KI-Backend Monitoring System</p>
        </body>
        </html>
        """

        await mailer.send(to=admin_email, subject=subject, text=body, html=html)
        log.info("Alert email sent to %s", admin_email)

    except Exception as e:
        log.error("Failed to send alert email: %s", e)


def _format_details(details: Dict[str, Any]) -> str:
    """Format details dict as readable string."""
    lines = []
    for key, value in details.items():
        if isinstance(value, (list, dict)):
            import json
            value = json.dumps(value, indent=2, ensure_ascii=False)
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


# =============================================================================
# Register Email Handler
# =============================================================================

def setup_email_notifications() -> None:
    """Setup email notifications for alerts."""
    import asyncio

    def sync_handler(alert: Alert) -> None:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            asyncio.ensure_future(send_alert_email(alert))
        else:
            loop.run_until_complete(send_alert_email(alert))

    _alert_manager.register_handler(sync_handler)
    log.info("Email alert notifications registered")


# =============================================================================
# Exports
# =============================================================================

def get_alert_manager() -> AlertManager:
    """Get the global alert manager."""
    return _alert_manager


__all__ = [
    "AlertType",
    "AlertSeverity",
    "Alert",
    "AlertManager",
    "get_alert_manager",
    "check_pdf_size",
    "check_pdf_timeout",
    "check_section_content",
    "check_multiple_fallbacks",
    "check_guardrail_hit",
    "check_persona_terms",
    "check_token_budget",
    "check_funding_routing",
    "send_alert_email",
    "setup_email_notifications",
]
