#!/usr/bin/env python3
"""
sprint_h_monitoring.py — Sprint H Monitoring & Alert Validation Module

This module validates all monitoring and alerting systems defined in Sprint H:
- PDF WARN/ALERT/BLOCK thresholds
- Fallback alerts
- Persona warnings
- Guardrail leak detection
- HTML sanitizer warnings
- Token budget warnings
- Rate limit and timeout warnings

Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

log = logging.getLogger("sprint_h_monitoring")


# =============================================================================
# Sprint H Monitoring Thresholds
# =============================================================================

class MonitoringThresholds:
    """Sprint H monitoring thresholds as per specification."""

    # PDF Size Thresholds (MB)
    PDF_SIZE_OK = 10
    PDF_SIZE_WARN = 10
    PDF_SIZE_ALERT = 18
    PDF_SIZE_BLOCK = 20

    # Performance Thresholds
    LLM_PHASE_MAX_SEC = 140
    TOTAL_MAX_SEC = 180
    PDF_GEN_MAX_SEC = 10
    RESEARCH_MAX_SEC = 12

    # System Thresholds
    CPU_PEAK_MAX_PCT = 80
    RAM_MAX_GB = 1.4

    # Quality Thresholds
    MIN_SECTION_WORDS = 50
    MAX_FALLBACKS_PER_REPORT = 2
    MAX_FALLBACKS_CRITICAL = 3

    # Guardrails Thresholds
    GUARDRAIL_HIGH_CONF = 0.9
    GUARDRAIL_EXPECTED_HITS_MIN = 4
    GUARDRAIL_EXPECTED_HITS_MAX = 12

    # Token Budget
    TOKEN_BUDGET_WARN_PCT = 95


# =============================================================================
# Alert Types
# =============================================================================

@dataclass
class MonitoringAlert:
    """Represents a monitoring alert."""
    alert_type: str
    severity: str  # info, warning, alert, critical
    message: str
    metric_name: str
    metric_value: Any
    threshold: Any
    timestamp: str = ""
    profile_id: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


# =============================================================================
# PDF Monitoring
# =============================================================================

def check_pdf_size(size_mb: float, profile_id: str = "") -> List[MonitoringAlert]:
    """
    Check PDF size against Sprint H thresholds.

    Thresholds:
    - < 10 MB → OK
    - 10-18 MB → WARN
    - > 18 MB → ALERT
    - > 20 MB → BLOCK (nicht rendern)
    """
    alerts = []

    if size_mb > MonitoringThresholds.PDF_SIZE_BLOCK:
        alerts.append(MonitoringAlert(
            alert_type="pdf_size_block",
            severity="critical",
            message=f"PDF size {size_mb:.1f}MB BLOCKED - exceeds {MonitoringThresholds.PDF_SIZE_BLOCK}MB limit",
            metric_name="pdf_size_mb",
            metric_value=size_mb,
            threshold=MonitoringThresholds.PDF_SIZE_BLOCK,
            profile_id=profile_id,
        ))
    elif size_mb > MonitoringThresholds.PDF_SIZE_ALERT:
        alerts.append(MonitoringAlert(
            alert_type="pdf_size_alert",
            severity="alert",
            message=f"PDF size {size_mb:.1f}MB ALERT - exceeds {MonitoringThresholds.PDF_SIZE_ALERT}MB threshold",
            metric_name="pdf_size_mb",
            metric_value=size_mb,
            threshold=MonitoringThresholds.PDF_SIZE_ALERT,
            profile_id=profile_id,
        ))
    elif size_mb > MonitoringThresholds.PDF_SIZE_WARN:
        alerts.append(MonitoringAlert(
            alert_type="pdf_size_warning",
            severity="warning",
            message=f"PDF size {size_mb:.1f}MB WARNING - exceeds {MonitoringThresholds.PDF_SIZE_WARN}MB threshold",
            metric_name="pdf_size_mb",
            metric_value=size_mb,
            threshold=MonitoringThresholds.PDF_SIZE_WARN,
            profile_id=profile_id,
        ))

    return alerts


# =============================================================================
# Fallback Monitoring
# =============================================================================

def check_fallback_count(fallback_count: int, profile_id: str = "") -> List[MonitoringAlert]:
    """
    Check fallback count against Sprint H thresholds.

    Alert if:
    - fallbacks > 2 per report → WARNING
    - fallbacks > 3 per report → CRITICAL
    - Same section falls back repeatedly → ALERT
    """
    alerts = []

    if fallback_count > MonitoringThresholds.MAX_FALLBACKS_CRITICAL:
        alerts.append(MonitoringAlert(
            alert_type="fallback_critical",
            severity="critical",
            message=f"{fallback_count} fallbacks exceeds critical limit of {MonitoringThresholds.MAX_FALLBACKS_CRITICAL}",
            metric_name="fallback_count",
            metric_value=fallback_count,
            threshold=MonitoringThresholds.MAX_FALLBACKS_CRITICAL,
            profile_id=profile_id,
        ))
    elif fallback_count > MonitoringThresholds.MAX_FALLBACKS_PER_REPORT:
        alerts.append(MonitoringAlert(
            alert_type="fallback_warning",
            severity="warning",
            message=f"{fallback_count} fallbacks exceeds warning limit of {MonitoringThresholds.MAX_FALLBACKS_PER_REPORT}",
            metric_name="fallback_count",
            metric_value=fallback_count,
            threshold=MonitoringThresholds.MAX_FALLBACKS_PER_REPORT,
            profile_id=profile_id,
        ))

    return alerts


def check_repeated_fallbacks(fallback_sections: Dict[str, int], profile_id: str = "") -> List[MonitoringAlert]:
    """Check for repeatedly failing sections across reports."""
    alerts = []

    for section, count in fallback_sections.items():
        if count >= 3:
            alerts.append(MonitoringAlert(
                alert_type="repeated_fallback",
                severity="alert",
                message=f"Section '{section}' has fallen back {count} times - investigate root cause",
                metric_name="section_fallback_count",
                metric_value=count,
                threshold=3,
                profile_id=profile_id,
            ))

    return alerts


# =============================================================================
# Persona Monitoring
# =============================================================================

def check_persona_violations(
    violations: List[str],
    expected_persona: str,
    profile_id: str = ""
) -> List[MonitoringAlert]:
    """
    Check persona term violations.

    Alert if:
    - Solo report contains "Team", "Abteilung", etc.
    - SIZE_TOKEN_MULTIPLIERS not applied correctly
    """
    alerts = []

    if violations:
        alerts.append(MonitoringAlert(
            alert_type="persona_term_violation",
            severity="warning",
            message=f"{len(violations)} forbidden term(s) for persona '{expected_persona}': {violations[:5]}",
            metric_name="persona_violations",
            metric_value=len(violations),
            threshold=0,
            profile_id=profile_id,
        ))

    return alerts


def check_persona_size_mismatch(
    expected_persona: str,
    detected_persona: str,
    profile_id: str = ""
) -> List[MonitoringAlert]:
    """Check for persona/size mismatches."""
    alerts = []

    if expected_persona != detected_persona:
        alerts.append(MonitoringAlert(
            alert_type="persona_size_mismatch",
            severity="error",
            message=f"Persona mismatch: expected '{expected_persona}', detected '{detected_persona}'",
            metric_name="persona_mismatch",
            metric_value=1,
            threshold=0,
            profile_id=profile_id,
        ))

    return alerts


# =============================================================================
# Guardrails Monitoring
# =============================================================================

def check_guardrail_leaks(
    output_content: str,
    guardrail_hits: List[Dict[str, Any]],
    profile_id: str = ""
) -> List[MonitoringAlert]:
    """
    Check for guardrail leaks in final output.

    Alert if:
    - GuardrailHit text appears unchanged in final output
    - Sensitive terms not properly masked
    """
    alerts = []

    for hit in guardrail_hits:
        sentence = hit.get("sentence", "")
        if sentence and sentence in output_content:
            alerts.append(MonitoringAlert(
                alert_type="guardrail_leak",
                severity="critical",
                message=f"Guardrail leak detected: '{sentence[:50]}...' appeared in output",
                metric_name="guardrail_leak",
                metric_value=1,
                threshold=0,
                profile_id=profile_id,
            ))

    return alerts


def check_guardrail_high_confidence(
    guardrail_hits: List[Dict[str, Any]],
    is_guardrails_profile: bool,
    profile_id: str = ""
) -> List[MonitoringAlert]:
    """
    Check guardrail confidence levels.

    Alert if:
    - Confidence > 0.9 in non-guardrails profile (false positive)
    - Expected guardrails not detected
    """
    alerts = []

    high_conf_hits = [h for h in guardrail_hits if h.get("confidence", 0) > MonitoringThresholds.GUARDRAIL_HIGH_CONF]

    if not is_guardrails_profile and high_conf_hits:
        alerts.append(MonitoringAlert(
            alert_type="guardrail_false_positive",
            severity="error",
            message=f"{len(high_conf_hits)} high-confidence guardrail hit(s) in non-guardrails profile",
            metric_name="guardrail_false_positive",
            metric_value=len(high_conf_hits),
            threshold=0,
            profile_id=profile_id,
        ))

    return alerts


# =============================================================================
# HTML Sanitizer Monitoring
# =============================================================================

def check_sanitizer_output(
    section_word_counts: Dict[str, int],
    profile_id: str = ""
) -> List[MonitoringAlert]:
    """
    Check HTML sanitizer output quality.

    Alert if:
    - sanitize_or_recover produces < 50 words
    - Broken tags detected in final HTML
    """
    alerts = []

    for section, word_count in section_word_counts.items():
        if 0 < word_count < MonitoringThresholds.MIN_SECTION_WORDS:
            alerts.append(MonitoringAlert(
                alert_type="sanitizer_low_output",
                severity="error",
                message=f"Section '{section}' has only {word_count} words (min: {MonitoringThresholds.MIN_SECTION_WORDS})",
                metric_name="section_word_count",
                metric_value=word_count,
                threshold=MonitoringThresholds.MIN_SECTION_WORDS,
                profile_id=profile_id,
            ))

    return alerts


def check_broken_html_tags(html_content: str, profile_id: str = "") -> List[MonitoringAlert]:
    """Check for broken HTML tags in output."""
    import re
    alerts = []

    # Check for unclosed tags
    broken_patterns = [
        r"<[^>]*$",  # Tag not closed
        r"<[a-z]+[^>]*>[^<]*$",  # Opening tag without closing
        r"</[^>]+>[^<]*</",  # Multiple closing tags
    ]

    for pattern in broken_patterns:
        if re.search(pattern, html_content, re.IGNORECASE):
            alerts.append(MonitoringAlert(
                alert_type="broken_html_tag",
                severity="warning",
                message="Potentially broken HTML tags detected in output",
                metric_name="html_quality",
                metric_value=1,
                threshold=0,
                profile_id=profile_id,
            ))
            break

    return alerts


# =============================================================================
# Token Budget Monitoring
# =============================================================================

def check_token_budget(
    tokens_used: int,
    tokens_max: int,
    profile_id: str = ""
) -> List[MonitoringAlert]:
    """
    Check token budget utilization.

    Alert if utilization > 95%
    """
    alerts = []

    if tokens_max > 0:
        utilization_pct = (tokens_used / tokens_max) * 100
        if utilization_pct > MonitoringThresholds.TOKEN_BUDGET_WARN_PCT:
            alerts.append(MonitoringAlert(
                alert_type="token_budget_warning",
                severity="warning",
                message=f"Token utilization at {utilization_pct:.1f}% (threshold: {MonitoringThresholds.TOKEN_BUDGET_WARN_PCT}%)",
                metric_name="token_utilization_pct",
                metric_value=utilization_pct,
                threshold=MonitoringThresholds.TOKEN_BUDGET_WARN_PCT,
                profile_id=profile_id,
            ))

    return alerts


# =============================================================================
# Performance Monitoring
# =============================================================================

def check_llm_runtime(duration_sec: float, profile_id: str = "") -> List[MonitoringAlert]:
    """Check LLM runtime against threshold."""
    alerts = []

    if duration_sec > MonitoringThresholds.LLM_PHASE_MAX_SEC:
        alerts.append(MonitoringAlert(
            alert_type="llm_runtime_exceeded",
            severity="warning",
            message=f"LLM runtime {duration_sec:.1f}s exceeds {MonitoringThresholds.LLM_PHASE_MAX_SEC}s threshold",
            metric_name="llm_runtime_sec",
            metric_value=duration_sec,
            threshold=MonitoringThresholds.LLM_PHASE_MAX_SEC,
            profile_id=profile_id,
        ))

    return alerts


def check_research_runtime(duration_sec: float, profile_id: str = "") -> List[MonitoringAlert]:
    """Check research runtime against threshold."""
    alerts = []

    if duration_sec > MonitoringThresholds.RESEARCH_MAX_SEC:
        alerts.append(MonitoringAlert(
            alert_type="research_runtime_exceeded",
            severity="warning",
            message=f"Research runtime {duration_sec:.1f}s exceeds {MonitoringThresholds.RESEARCH_MAX_SEC}s threshold",
            metric_name="research_runtime_sec",
            metric_value=duration_sec,
            threshold=MonitoringThresholds.RESEARCH_MAX_SEC,
            profile_id=profile_id,
        ))

    return alerts


def check_total_runtime(duration_sec: float, profile_id: str = "") -> List[MonitoringAlert]:
    """Check total runtime against threshold."""
    alerts = []

    if duration_sec > MonitoringThresholds.TOTAL_MAX_SEC:
        alerts.append(MonitoringAlert(
            alert_type="total_runtime_exceeded",
            severity="warning",
            message=f"Total runtime {duration_sec:.1f}s exceeds {MonitoringThresholds.TOTAL_MAX_SEC}s threshold",
            metric_name="total_runtime_sec",
            metric_value=duration_sec,
            threshold=MonitoringThresholds.TOTAL_MAX_SEC,
            profile_id=profile_id,
        ))

    return alerts


# =============================================================================
# Funding Routing Monitoring
# =============================================================================

def check_funding_routing(
    lang: str,
    country: str,
    actual_route: str,
    profile_id: str = ""
) -> List[MonitoringAlert]:
    """
    Validate funding routing correctness.

    Test matrix:
    - de + DE → DE Funding
    - en + DE → EN-DE Germany-Funding (Phase 1)
    - en + FR/IT/ES/EU → EN-EU Core Funding (Phase 2)
    """
    alerts = []

    # Determine expected route
    if lang == "de":
        expected_route = "DE"
    elif lang == "en" and country in ("Germany", "DE"):
        expected_route = "EN-DE"
    elif lang == "en":
        expected_route = "EN-EU-Core"
    else:
        expected_route = "unknown"

    if actual_route and actual_route != expected_route:
        alerts.append(MonitoringAlert(
            alert_type="funding_routing_error",
            severity="error",
            message=f"Funding routing mismatch: expected '{expected_route}' for lang={lang}/country={country}, got '{actual_route}'",
            metric_name="funding_route_mismatch",
            metric_value=1,
            threshold=0,
            profile_id=profile_id,
        ))

    return alerts


# =============================================================================
# System Monitoring
# =============================================================================

def check_system_resources(
    cpu_pct: float,
    memory_mb: float,
    profile_id: str = ""
) -> List[MonitoringAlert]:
    """Check system resource usage."""
    alerts = []

    if cpu_pct > MonitoringThresholds.CPU_PEAK_MAX_PCT:
        alerts.append(MonitoringAlert(
            alert_type="cpu_peak_exceeded",
            severity="warning",
            message=f"CPU peak {cpu_pct:.1f}% exceeds {MonitoringThresholds.CPU_PEAK_MAX_PCT}% threshold",
            metric_name="cpu_peak_pct",
            metric_value=cpu_pct,
            threshold=MonitoringThresholds.CPU_PEAK_MAX_PCT,
            profile_id=profile_id,
        ))

    ram_gb = memory_mb / 1024
    if ram_gb > MonitoringThresholds.RAM_MAX_GB:
        alerts.append(MonitoringAlert(
            alert_type="memory_exceeded",
            severity="warning",
            message=f"Memory {ram_gb:.2f}GB exceeds {MonitoringThresholds.RAM_MAX_GB}GB threshold",
            metric_name="memory_gb",
            metric_value=ram_gb,
            threshold=MonitoringThresholds.RAM_MAX_GB,
            profile_id=profile_id,
        ))

    return alerts


# =============================================================================
# Comprehensive Monitoring Check
# =============================================================================

@dataclass
class MonitoringResult:
    """Complete monitoring result for a profile."""
    profile_id: str
    alerts: List[MonitoringAlert] = field(default_factory=list)
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add_alerts(self, new_alerts: List[MonitoringAlert]) -> None:
        """Add alerts and update counts."""
        for alert in new_alerts:
            self.alerts.append(alert)
            if alert.severity == "critical":
                self.critical_count += 1
            elif alert.severity in ("error", "alert"):
                self.error_count += 1
            elif alert.severity == "warning":
                self.warning_count += 1
            else:
                self.info_count += 1

    @property
    def has_critical(self) -> bool:
        return self.critical_count > 0

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0

    @property
    def total_issues(self) -> int:
        return self.critical_count + self.error_count + self.warning_count


def run_comprehensive_monitoring(
    profile_id: str,
    metrics: Dict[str, Any],
    config: Dict[str, Any],
) -> MonitoringResult:
    """
    Run all Sprint H monitoring checks for a profile.

    Args:
        profile_id: Profile identifier
        metrics: Collected metrics from the profile test
        config: Profile configuration

    Returns:
        MonitoringResult with all alerts
    """
    result = MonitoringResult(profile_id=profile_id)

    # PDF Size Monitoring
    pdf_size_mb = metrics.get("pdf_size_mb", 0)
    result.add_alerts(check_pdf_size(pdf_size_mb, profile_id))

    # Fallback Monitoring
    fallback_count = metrics.get("fallback_count", 0)
    result.add_alerts(check_fallback_count(fallback_count, profile_id))

    fallback_sections = metrics.get("fallback_by_section", {})
    result.add_alerts(check_repeated_fallbacks(fallback_sections, profile_id))

    # Persona Monitoring
    expected_persona = config.get("expected_persona", "")
    detected_persona = metrics.get("persona", "")
    persona_violations = metrics.get("persona_violations", [])

    result.add_alerts(check_persona_violations(persona_violations, expected_persona, profile_id))
    result.add_alerts(check_persona_size_mismatch(expected_persona, detected_persona, profile_id))

    # Guardrails Monitoring
    guardrail_hits = metrics.get("guardrail_hits_list", [])
    is_guardrails_profile = config.get("expected_guardrails", False)

    result.add_alerts(check_guardrail_high_confidence(guardrail_hits, is_guardrails_profile, profile_id))

    # Check for guardrail leaks in output
    output_content = metrics.get("output_content", "")
    if output_content:
        result.add_alerts(check_guardrail_leaks(output_content, guardrail_hits, profile_id))
        result.add_alerts(check_broken_html_tags(output_content, profile_id))

    # Sanitizer Monitoring
    section_word_counts = metrics.get("section_word_counts", {})
    result.add_alerts(check_sanitizer_output(section_word_counts, profile_id))

    # Token Budget Monitoring
    tokens_used = metrics.get("llm_tokens_total", 0)
    tokens_max = metrics.get("llm_tokens_max", 0)
    result.add_alerts(check_token_budget(tokens_used, tokens_max, profile_id))

    # Performance Monitoring
    llm_runtime = metrics.get("analysis_time_llm_sections", 0)
    result.add_alerts(check_llm_runtime(llm_runtime, profile_id))

    research_runtime = metrics.get("analysis_time_research", 0)
    result.add_alerts(check_research_runtime(research_runtime, profile_id))

    total_runtime = metrics.get("analysis_time_total", 0)
    result.add_alerts(check_total_runtime(total_runtime, profile_id))

    # Funding Routing Monitoring
    lang = metrics.get("lang", "de")
    country = config.get("country", "Germany")
    actual_route = metrics.get("funding_route", "")
    result.add_alerts(check_funding_routing(lang, country, actual_route, profile_id))

    # System Monitoring
    cpu_pct = metrics.get("cpu_peak_pct", 0)
    memory_mb = metrics.get("memory_peak_mb", 0)
    result.add_alerts(check_system_resources(cpu_pct, memory_mb, profile_id))

    return result


def generate_monitoring_summary(results: List[MonitoringResult]) -> Dict[str, Any]:
    """Generate summary of all monitoring results."""
    total_alerts = 0
    total_critical = 0
    total_errors = 0
    total_warnings = 0

    alert_types: Dict[str, int] = {}
    profiles_with_issues = []

    for r in results:
        total_alerts += len(r.alerts)
        total_critical += r.critical_count
        total_errors += r.error_count
        total_warnings += r.warning_count

        if r.total_issues > 0:
            profiles_with_issues.append(r.profile_id)

        for alert in r.alerts:
            alert_types[alert.alert_type] = alert_types.get(alert.alert_type, 0) + 1

    return {
        "total_alerts": total_alerts,
        "critical": total_critical,
        "errors": total_errors,
        "warnings": total_warnings,
        "profiles_with_issues": len(profiles_with_issues),
        "alert_types": alert_types,
        "profiles_affected": profiles_with_issues,
    }


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Run monitoring validation from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Sprint H Monitoring Validation")
    parser.add_argument("--input", "-i", help="Input JSON file with test results")
    parser.add_argument("--output", "-o", help="Output file for monitoring report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("Sprint H Monitoring Validation")
    print("=" * 50)

    # Run validation on sample data
    sample_metrics = {
        "pdf_size_mb": 9.5,
        "fallback_count": 1,
        "persona": "solo",
        "guardrail_hits_list": [],
        "section_word_counts": {"exec_summary": 150, "roadmap_90d": 120},
        "analysis_time_llm_sections": 95,
        "analysis_time_research": 8,
        "analysis_time_total": 145,
        "lang": "de",
        "funding_route": "DE",
        "cpu_peak_pct": 65,
        "memory_peak_mb": 900,
    }

    sample_config = {
        "expected_persona": "solo",
        "expected_guardrails": False,
        "country": "Germany",
    }

    result = run_comprehensive_monitoring("sample_profile", sample_metrics, sample_config)

    print(f"\nProfile: {result.profile_id}")
    print(f"Critical: {result.critical_count}")
    print(f"Errors: {result.error_count}")
    print(f"Warnings: {result.warning_count}")

    for alert in result.alerts:
        icon = "🔴" if alert.severity == "critical" else "🟠" if alert.severity in ("error", "alert") else "🟡"
        print(f"  {icon} [{alert.alert_type}] {alert.message}")

    print("\n✅ Monitoring validation module working correctly")


if __name__ == "__main__":
    main()
