# -*- coding: utf-8 -*-
"""
Sprint G9.1: AI-Act Business-Case Monitoring Layer

This module provides structured metrics tracking for AI Act compliance
adjustments to business cases, enabling monitoring, alerting, and analytics.

Features:
- AIActBCMetrics dataclass for structured tracking
- Integration hook for apply_ai_act_modifiers_to_business_case()
- Metrics storage in sections["_ai_act_bc_metrics"]
- Summary statistics and anomaly detection

Version: 1.0.0 (Sprint G9)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# =============================================================================
# G9.1: AI ACT BUSINESS CASE METRICS
# =============================================================================

@dataclass
class AIActBCMetrics:
    """
    Structured metrics for AI Act Business Case modifications.

    Tracks before/after values for CAPEX, OPEX, Payback, and ROI
    along with modifiers applied and timing information.
    """
    # Risk classification
    risk_level: str = "minimal"

    # CAPEX tracking
    capex_before: float = 0.0
    capex_after: float = 0.0
    capex_modifier: float = 1.0
    capex_delta_abs: float = 0.0
    capex_delta_pct: float = 0.0

    # OPEX tracking
    opex_before: float = 0.0
    opex_after: float = 0.0
    opex_modifier: float = 1.0
    opex_delta_abs: float = 0.0
    opex_delta_pct: float = 0.0

    # Payback tracking
    payback_before: Optional[float] = None
    payback_after: Optional[float] = None
    payback_delta_months: float = 0.0

    # ROI tracking
    roi_before: Optional[float] = None
    roi_after: Optional[float] = None
    roi_delta_pct: Optional[float] = None

    # Modifiers applied
    modifiers_applied: bool = False
    modifier_source: str = "ai_act_module"

    # Timing
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processing_ms: float = 0.0

    # Validation
    warnings: List[str] = field(default_factory=list)
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for storage."""
        return asdict(self)

    def get_summary(self) -> str:
        """Get human-readable summary of modifications."""
        if not self.modifiers_applied:
            return f"[AI-ACT-BC] No modifiers applied (risk_level={self.risk_level})"

        parts = [f"[AI-ACT-BC] Risk: {self.risk_level}"]

        if self.capex_modifier != 1.0:
            parts.append(f"CAPEX: €{self.capex_before:,.0f}→€{self.capex_after:,.0f} ({self.capex_delta_pct:+.1f}%)")

        if self.opex_modifier != 1.0:
            parts.append(f"OPEX: €{self.opex_before:,.0f}→€{self.opex_after:,.0f} ({self.opex_delta_pct:+.1f}%)")

        if self.payback_delta_months > 0:
            parts.append(f"Payback: +{self.payback_delta_months:.1f} months")

        if self.warnings:
            parts.append(f"Warnings: {len(self.warnings)}")

        return " | ".join(parts)


# =============================================================================
# METRICS CALCULATION
# =============================================================================

def calculate_bc_metrics(
    original_bc: Dict[str, Any],
    adjusted_bc: Dict[str, Any],
    risk_level: str,
    modifiers: Dict[str, Any],
    processing_ms: float = 0.0
) -> AIActBCMetrics:
    """
    Calculate comprehensive metrics from BC modification.

    Args:
        original_bc: Original business case before AI Act adjustment
        adjusted_bc: Business case after AI Act adjustment
        risk_level: AI Act risk classification
        modifiers: Dict with CAPEX_MODIFIER, OPEX_MODIFIER
        processing_ms: Time taken for modification in milliseconds

    Returns:
        AIActBCMetrics with all tracking fields populated
    """
    # Extract before values
    capex_before = float(original_bc.get("CAPEX_REALISTISCH_EUR", 0))
    opex_before = float(original_bc.get("OPEX_REALISTISCH_EUR", 0))
    payback_before = original_bc.get("PAYBACK_MONTHS")
    roi_before = original_bc.get("ROI_12M")

    # Extract after values
    capex_after = float(adjusted_bc.get("CAPEX_REALISTISCH_EUR", 0))
    opex_after = float(adjusted_bc.get("OPEX_REALISTISCH_EUR", 0))
    payback_after = adjusted_bc.get("PAYBACK_MONTHS")
    roi_after = adjusted_bc.get("ROI_12M")

    # Get modifiers
    capex_modifier = float(modifiers.get("CAPEX_MODIFIER", 1.0))
    opex_modifier = float(modifiers.get("OPEX_MODIFIER", 1.0))

    # Calculate deltas
    capex_delta_abs = capex_after - capex_before
    capex_delta_pct = ((capex_after / capex_before) - 1) * 100 if capex_before > 0 else 0.0

    opex_delta_abs = opex_after - opex_before
    opex_delta_pct = ((opex_after / opex_before) - 1) * 100 if opex_before > 0 else 0.0

    # Payback delta
    payback_delta = 0.0
    if payback_before is not None and payback_after is not None:
        payback_delta = payback_after - payback_before

    # ROI delta
    roi_delta = None
    if roi_before is not None and roi_after is not None:
        roi_delta = roi_after - roi_before

    # Check for modifiers actually applied
    modifiers_applied = capex_modifier != 1.0 or opex_modifier != 1.0

    # Collect warnings
    warnings = []
    is_anomaly = False
    anomaly_reason = None

    # Anomaly detection
    if capex_after < 0:
        warnings.append("Negative CAPEX after adjustment")
        is_anomaly = True
        anomaly_reason = "Negative CAPEX"

    if opex_after < 0:
        warnings.append("Negative OPEX after adjustment")
        is_anomaly = True
        anomaly_reason = "Negative OPEX"

    if payback_after is not None and payback_after > 60:
        warnings.append(f"Extremely long payback: {payback_after:.1f} months")
        is_anomaly = True
        anomaly_reason = "Payback > 5 years"

    if risk_level == "high-risk" and roi_after is not None and roi_after > 300:
        warnings.append(f"Unusually high ROI for high-risk: {roi_after:.1f}%")

    if capex_modifier > 1.5:
        warnings.append(f"High CAPEX modifier: {capex_modifier:.2f}")

    return AIActBCMetrics(
        risk_level=risk_level,
        capex_before=capex_before,
        capex_after=capex_after,
        capex_modifier=capex_modifier,
        capex_delta_abs=capex_delta_abs,
        capex_delta_pct=capex_delta_pct,
        opex_before=opex_before,
        opex_after=opex_after,
        opex_modifier=opex_modifier,
        opex_delta_abs=opex_delta_abs,
        opex_delta_pct=opex_delta_pct,
        payback_before=payback_before,
        payback_after=payback_after,
        payback_delta_months=payback_delta,
        roi_before=roi_before,
        roi_after=roi_after,
        roi_delta_pct=roi_delta,
        modifiers_applied=modifiers_applied,
        modifier_source="ai_act_module",
        processing_ms=processing_ms,
        warnings=warnings,
        is_anomaly=is_anomaly,
        anomaly_reason=anomaly_reason,
    )


# =============================================================================
# INTEGRATION HOOK
# =============================================================================

def track_bc_modification(
    sections: Dict[str, Any],
    original_bc: Dict[str, Any],
    adjusted_bc: Dict[str, Any],
    risk_level: str,
    modifiers: Dict[str, Any],
    processing_ms: float = 0.0
) -> AIActBCMetrics:
    """
    Integration hook to track BC modification and store metrics in sections.

    Call this after apply_ai_act_modifiers_to_business_case() to record metrics.

    Args:
        sections: Report sections dict (will be mutated to add _ai_act_bc_metrics)
        original_bc: Original business case before adjustment
        adjusted_bc: Business case after adjustment
        risk_level: AI Act risk level
        modifiers: Dict with CAPEX_MODIFIER, OPEX_MODIFIER
        processing_ms: Processing time in milliseconds

    Returns:
        AIActBCMetrics object
    """
    import time
    start = time.perf_counter()

    # Calculate metrics
    metrics = calculate_bc_metrics(
        original_bc=original_bc,
        adjusted_bc=adjusted_bc,
        risk_level=risk_level,
        modifiers=modifiers,
        processing_ms=processing_ms
    )

    # Calculate our own processing time if not provided
    if processing_ms == 0.0:
        metrics.processing_ms = (time.perf_counter() - start) * 1000

    # Store in sections
    sections["_ai_act_bc_metrics"] = metrics.to_dict()

    # Log summary
    log.info(metrics.get_summary())

    # Log warnings if any
    for warning in metrics.warnings:
        log.warning("[AI-ACT-BC-MONITOR] %s", warning)

    # Log anomalies
    if metrics.is_anomaly:
        log.error(
            "[AI-ACT-BC-ANOMALY] Detected anomaly: %s (risk_level=%s)",
            metrics.anomaly_reason,
            metrics.risk_level
        )

    return metrics


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

def get_bc_metrics_summary(sections: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get stored BC metrics from sections if available.

    Returns None if no metrics were stored.
    """
    return sections.get("_ai_act_bc_metrics")


def format_metrics_for_log(metrics: Dict[str, Any]) -> str:
    """
    Format metrics dict for structured logging.

    Args:
        metrics: Metrics dict from AIActBCMetrics.to_dict()

    Returns:
        Formatted string for logging
    """
    if not metrics:
        return "[AI-ACT-BC] No metrics available"

    risk = metrics.get("risk_level", "unknown")
    capex_before = metrics.get("capex_before", 0)
    capex_after = metrics.get("capex_after", 0)
    opex_before = metrics.get("opex_before", 0)
    opex_after = metrics.get("opex_after", 0)
    modifiers_applied = metrics.get("modifiers_applied", False)

    if not modifiers_applied:
        return f"[AI-ACT-BC] Risk={risk} | No modifiers applied"

    return (
        f"[AI-ACT-BC] Risk={risk} | "
        f"CAPEX: €{capex_before:,.0f}→€{capex_after:,.0f} | "
        f"OPEX: €{opex_before:,.0f}→€{opex_after:,.0f}"
    )


# =============================================================================
# RISK LEVEL VALIDATORS
# =============================================================================

VALID_RISK_LEVELS = frozenset(["none", "minimal", "limited", "high-risk"])


def normalize_risk_level(risk_level: str) -> str:
    """
    Normalize risk level string to canonical form.

    Args:
        risk_level: Raw risk level string

    Returns:
        Normalized risk level (minimal if invalid)
    """
    if not risk_level:
        return "minimal"

    normalized = risk_level.lower().strip()

    # Handle variations
    if normalized in ("high", "hoch", "high-risk", "high_risk", "highrisk"):
        return "high-risk"
    elif normalized in ("limited", "begrenzt", "beschränkt"):
        return "limited"
    elif normalized in ("minimal", "gering", "niedrig"):
        return "minimal"
    elif normalized in ("none", "keine", "kein", "no"):
        return "none"

    # Unknown - default to minimal
    log.warning("[AI-ACT-BC-MONITOR] Unknown risk level '%s', defaulting to 'minimal'", risk_level)
    return "minimal"


def get_expected_modifiers(risk_level: str) -> Dict[str, float]:
    """
    Get expected CAPEX/OPEX modifiers for a risk level.

    Args:
        risk_level: Normalized risk level

    Returns:
        Dict with expected CAPEX_MODIFIER and OPEX_MODIFIER
    """
    normalized = normalize_risk_level(risk_level)

    if normalized == "high-risk":
        return {"CAPEX_MODIFIER": 1.25, "OPEX_MODIFIER": 1.15}
    elif normalized == "limited":
        return {"CAPEX_MODIFIER": 1.10, "OPEX_MODIFIER": 1.05}
    else:
        return {"CAPEX_MODIFIER": 1.0, "OPEX_MODIFIER": 1.0}


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G9.1] monitoring_ai_act.py loaded - AI Act BC monitoring enabled")
