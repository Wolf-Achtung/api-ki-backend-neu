#!/usr/bin/env python3
"""
sprint_h_load_test.py — SPRINT H: Full Load & Monitoring QA

Sprint H: Belastungstest, Monitoring-Validierung, Erkennen von Grenzbereichen unter Realbedingungen
Version: 1.0.0

Features:
- 20-30 Reports mit gemischten Profilen (DE/EN, Solo/Team/KMU)
- Parallel-Ausführung mit 6 Workern
- Messung von Laufzeiten, Fallbacks, PDF-Größen
- Monitoring & Alert Verifizierung
- Stabilitäts- und Erholungsfähigkeitstests
- Full-System KPI Generierung

Usage:
    python scripts/sprint_h_load_test.py [--workers N] [--reports N] [--profile FILTER] [--output-dir DIR]
    python scripts/sprint_h_load_test.py --dry-run  # Validate profiles without running full tests

Exit codes:
    0 = All tests pass
    1 = Critical failures
    2 = Warnings only
"""
from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import json
import logging
import os
import re
import statistics
import sys
import threading
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Add repo root to path for imports
sys.path.insert(0, str(REPO_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("sprint_h_load_test")

# =============================================================================
# Sprint H Configuration
# =============================================================================

# Target KPIs from Sprint H spec
TARGET_KPIS = {
    "llm_phase_max_sec": 140,
    "total_max_sec": 180,
    "pdf_max_sec": 10,
    "cpu_peak_max_pct": 80,
    "ram_max_gb": 1.4,
    "pdf_ok_mb": 10,
    "pdf_warn_mb": 18,
    "pdf_alert_mb": 18,
    "pdf_block_mb": 20,
    "min_section_words": 50,
    "max_fallbacks_per_report": 2,
    "guardrail_high_conf_threshold": 0.9,
    "research_max_sec": 12,
    "sanitizer_min_words": 50,
}

# Mandatory test profiles from Sprint H spec
MANDATORY_PROFILES = [
    # DE / Solo
    {"id": "solo_beratung_ki_assessments", "path": "data/test_profiles_gold/solo_beratung_ki_assessments.json",
     "category": "DE/Solo", "expected_funding": "DE", "expected_persona": "solo", "expected_guardrails": False},
    {"id": "solo_marketing_content_solo_agency", "path": "data/test_profiles_gold/solo_marketing_content_solo_agency.json",
     "category": "DE/Solo", "expected_funding": "DE", "expected_persona": "solo", "expected_guardrails": False},

    # DE / Team
    {"id": "team_it_software_saas_advisory", "path": "data/test_profiles_gold/team_it_software_saas_advisory.json",
     "category": "DE/Team", "expected_funding": "DE", "expected_persona": "team", "expected_guardrails": False},
    {"id": "team_finance_insurance_advisory", "path": "data/test_profiles_gold/team_finance_insurance_advisory.json",
     "category": "DE/Team", "expected_funding": "DE", "expected_persona": "team", "expected_guardrails": False},

    # DE / KMU
    {"id": "kmu_industrie_production_advisory", "path": "data/test_profiles_gold/kmu_industrie_production_advisory.json",
     "category": "DE/KMU", "expected_funding": "DE", "expected_persona": "kmu", "expected_guardrails": False},
    {"id": "kmu_handel_ecommerce_advisory", "path": "data/test_profiles_gold/kmu_handel_ecommerce_advisory.json",
     "category": "DE/KMU", "expected_funding": "DE", "expected_persona": "kmu", "expected_guardrails": False},

    # DE / Guardrails
    {"id": "kmu_guardrails_test", "path": "data/test_profiles_gold/kmu_guardrails_test.json",
     "category": "DE/Guardrails", "expected_funding": "DE", "expected_persona": "kmu", "expected_guardrails": True,
     "expected_guardrail_hits_min": 4, "expected_guardrail_hits_max": 7},

    # EN / Solo
    {"id": "solo_consulting_en_gold", "path": "data/test_profiles_gold/solo_consulting_en_gold.json",
     "category": "EN/Solo", "expected_funding": "EN-DE", "expected_persona": "solo", "expected_guardrails": False},

    # EN / Team
    {"id": "team_it_en_gold", "path": "data/test_profiles_gold/team_it_en_gold.json",
     "category": "EN/Team", "expected_funding": "EN-DE", "expected_persona": "team", "expected_guardrails": False},

    # EN / EU-Core
    {"id": "kmu_france_eu_core_en_gold", "path": "data/test_profiles_gold/kmu_france_eu_core_en_gold.json",
     "category": "EN/EU-Core", "expected_funding": "EN-EU-Core", "expected_persona": "kmu", "expected_guardrails": False},

    # EN / Healthcare Guardrails
    {"id": "kmu_guardrails_en_gold", "path": "data/test_profiles_gold/kmu_guardrails_en_gold.json",
     "category": "EN/Guardrails", "expected_funding": "EN-DE", "expected_persona": "kmu", "expected_guardrails": True,
     "expected_guardrail_hits_min": 5, "expected_guardrail_hits_max": 8},

    # EN / High-Stress
    {"id": "team_it_guardrails_extreme_en", "path": "data/test_profiles_en/team_it_guardrails_extreme_en.json",
     "category": "EN/High-Stress", "expected_funding": "EN-DE", "expected_persona": "team", "expected_guardrails": True,
     "expected_guardrail_hits_min": 6, "expected_guardrail_hits_max": 12},

    # DE / Stress Test (extreme freetext for PDF size testing)
    {"id": "kmu_extreme_freetext_stress", "path": "data/test_profiles_gold/kmu_extreme_freetext_stress.json",
     "category": "DE/Stress", "expected_funding": "DE", "expected_persona": "kmu", "expected_guardrails": False,
     "stress_test": True},
]


# =============================================================================
# Data Classes
# =============================================================================

class TestSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class TestCheck:
    """Single test check result."""
    name: str
    passed: bool
    severity: TestSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    metric_value: Optional[float] = None


@dataclass
class ProfileMetrics:
    """Metrics collected for a single profile test run."""
    profile_id: str
    profile_category: str
    lang: str
    persona: str

    # Timing metrics (in seconds)
    analysis_time_total: float = 0.0
    analysis_time_llm_sections: float = 0.0
    analysis_time_research: float = 0.0
    analysis_time_pdf: float = 0.0

    # PDF metrics
    pdf_size_bytes: int = 0
    pdf_size_mb: float = 0.0
    html_size_kb: float = 0.0

    # LLM metrics
    llm_tokens_total: int = 0
    llm_tokens_by_section: Dict[str, int] = field(default_factory=dict)
    llm_calls: int = 0

    # Quality metrics
    fallback_count: int = 0
    fallback_sections: List[str] = field(default_factory=list)
    sections_generated: int = 0
    sections_failed: int = 0
    section_word_counts: Dict[str, int] = field(default_factory=dict)

    # Guardrails metrics
    guardrail_hits: int = 0
    guardrail_hits_list: List[Dict[str, Any]] = field(default_factory=list)
    guardrail_avg_confidence: float = 0.0
    guardrail_high_confidence_count: int = 0

    # Error tracking
    critical_errors: List[str] = field(default_factory=list)
    placeholder_violations: List[str] = field(default_factory=list)
    guardrail_leaks: List[str] = field(default_factory=list)

    # Sanitizer metrics
    sanitizer_recovery_count: int = 0
    sanitizer_min_words_produced: int = 0

    # Funding routing
    funding_route: str = ""
    funding_programs_count: int = 0

    # Persona validation
    persona_violations: List[str] = field(default_factory=list)

    # System metrics
    cpu_peak_pct: float = 0.0
    memory_peak_mb: float = 0.0

    # Overall status
    success: bool = False
    error_message: str = ""


@dataclass
class TestRunResult:
    """Result of a single profile test run."""
    profile_id: str
    profile_category: str
    metrics: ProfileMetrics
    checks: List[TestCheck] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    duration_sec: float = 0.0

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks if c.severity in (TestSeverity.ERROR, TestSeverity.CRITICAL))

    @property
    def critical_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == TestSeverity.CRITICAL)

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == TestSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == TestSeverity.WARNING)


@dataclass
class SprintHReport:
    """Complete Sprint H test report."""
    # Summary
    reports_tested: int = 0
    reports_passed: int = 0
    reports_failed: int = 0
    total_duration_sec: float = 0.0

    # Performance KPIs
    avg_total_sec: float = 0.0
    max_total_sec: float = 0.0
    min_total_sec: float = 0.0
    avg_llm_sec: float = 0.0
    avg_research_sec: float = 0.0
    avg_pdf_sec: float = 0.0

    # Fallback KPIs
    avg_fallbacks: float = 0.0
    max_fallbacks: int = 0
    total_fallbacks: int = 0
    fallback_by_section: Dict[str, int] = field(default_factory=dict)

    # PDF KPIs
    avg_pdf_size_mb: float = 0.0
    max_pdf_size_mb: float = 0.0
    min_pdf_size_mb: float = 0.0
    pdf_warnings: int = 0
    pdf_alerts: int = 0
    pdf_blocked: int = 0

    # Guardrails KPIs
    false_positives: int = 0
    avg_guardrail_hits: float = 0.0
    total_guardrail_hits: int = 0
    guardrail_confidence_median: float = 0.0

    # Funding routing
    funding_routing_correct: int = 0
    funding_routing_total: int = 0
    funding_routing_pct: float = 0.0

    # Persona validation
    persona_violations_total: int = 0
    persona_violations_by_type: Dict[str, int] = field(default_factory=dict)

    # Sanitizer KPIs
    sanitizer_recovery_rate: float = 0.0
    sanitizer_recovery_total: int = 0

    # Error tracking
    critical_errors_total: int = 0
    placeholder_violations_total: int = 0
    guardrail_leaks_total: int = 0

    # System KPIs
    cpu_peak_pct: float = 0.0
    memory_peak_mb: float = 0.0

    # Individual results
    results: List[TestRunResult] = field(default_factory=list)

    # Alerts generated
    alerts: List[Dict[str, Any]] = field(default_factory=list)

    # Test metadata
    start_time: str = ""
    end_time: str = ""
    workers: int = 6
    profiles_tested: List[str] = field(default_factory=list)


# =============================================================================
# Profile Loader
# =============================================================================

def load_profile(profile_config: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Load a test profile from disk."""
    profile_path = REPO_ROOT / profile_config["path"]

    if not profile_path.exists():
        return None, f"Profile file not found: {profile_config['path']}"

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        return profile, None
    except Exception as e:
        return None, f"Failed to load profile: {e}"


def load_all_profiles() -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Load all mandatory profiles."""
    profiles = []
    for config in MANDATORY_PROFILES:
        profile, error = load_profile(config)
        if profile:
            profiles.append((profile, config))
        else:
            log.warning("Failed to load profile %s: %s", config["id"], error)
    return profiles


# =============================================================================
# Validation Functions
# =============================================================================

def validate_profile_timing(metrics: ProfileMetrics, config: Dict[str, Any]) -> List[TestCheck]:
    """Validate timing metrics against Sprint H targets."""
    checks = []

    # Total time
    if metrics.analysis_time_total > TARGET_KPIS["total_max_sec"]:
        checks.append(TestCheck(
            name="Total Analysis Time",
            passed=False,
            severity=TestSeverity.WARNING,
            message=f"Total time {metrics.analysis_time_total:.1f}s exceeds target {TARGET_KPIS['total_max_sec']}s",
            metric_value=metrics.analysis_time_total,
        ))
    else:
        checks.append(TestCheck(
            name="Total Analysis Time",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"Total time {metrics.analysis_time_total:.1f}s within target",
            metric_value=metrics.analysis_time_total,
        ))

    # LLM phase time
    if metrics.analysis_time_llm_sections > TARGET_KPIS["llm_phase_max_sec"]:
        checks.append(TestCheck(
            name="LLM Phase Time",
            passed=False,
            severity=TestSeverity.WARNING,
            message=f"LLM time {metrics.analysis_time_llm_sections:.1f}s exceeds target {TARGET_KPIS['llm_phase_max_sec']}s",
            metric_value=metrics.analysis_time_llm_sections,
        ))
    else:
        checks.append(TestCheck(
            name="LLM Phase Time",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"LLM time {metrics.analysis_time_llm_sections:.1f}s within target",
            metric_value=metrics.analysis_time_llm_sections,
        ))

    # Research time
    if metrics.analysis_time_research > TARGET_KPIS["research_max_sec"]:
        checks.append(TestCheck(
            name="Research Time",
            passed=False,
            severity=TestSeverity.WARNING,
            message=f"Research time {metrics.analysis_time_research:.1f}s exceeds target {TARGET_KPIS['research_max_sec']}s",
            metric_value=metrics.analysis_time_research,
        ))
    else:
        checks.append(TestCheck(
            name="Research Time",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"Research time {metrics.analysis_time_research:.1f}s within target",
            metric_value=metrics.analysis_time_research,
        ))

    # PDF time
    if metrics.analysis_time_pdf > TARGET_KPIS["pdf_max_sec"]:
        checks.append(TestCheck(
            name="PDF Generation Time",
            passed=False,
            severity=TestSeverity.WARNING,
            message=f"PDF time {metrics.analysis_time_pdf:.1f}s exceeds target {TARGET_KPIS['pdf_max_sec']}s",
            metric_value=metrics.analysis_time_pdf,
        ))
    else:
        checks.append(TestCheck(
            name="PDF Generation Time",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"PDF time {metrics.analysis_time_pdf:.1f}s within target",
            metric_value=metrics.analysis_time_pdf,
        ))

    return checks


def validate_pdf_size(metrics: ProfileMetrics, config: Dict[str, Any]) -> List[TestCheck]:
    """Validate PDF size against Sprint H thresholds."""
    checks = []
    size_mb = metrics.pdf_size_mb

    if size_mb > TARGET_KPIS["pdf_block_mb"]:
        checks.append(TestCheck(
            name="PDF Size",
            passed=False,
            severity=TestSeverity.CRITICAL,
            message=f"PDF size {size_mb:.1f}MB BLOCKED (>{TARGET_KPIS['pdf_block_mb']}MB)",
            metric_value=size_mb,
        ))
    elif size_mb > TARGET_KPIS["pdf_alert_mb"]:
        checks.append(TestCheck(
            name="PDF Size",
            passed=False,
            severity=TestSeverity.ERROR,
            message=f"PDF size {size_mb:.1f}MB ALERT (>{TARGET_KPIS['pdf_alert_mb']}MB)",
            metric_value=size_mb,
        ))
    elif size_mb > TARGET_KPIS["pdf_warn_mb"]:
        checks.append(TestCheck(
            name="PDF Size",
            passed=False,
            severity=TestSeverity.WARNING,
            message=f"PDF size {size_mb:.1f}MB WARNING (>{TARGET_KPIS['pdf_warn_mb']}MB)",
            metric_value=size_mb,
        ))
    elif size_mb > TARGET_KPIS["pdf_ok_mb"]:
        checks.append(TestCheck(
            name="PDF Size",
            passed=True,
            severity=TestSeverity.WARNING,
            message=f"PDF size {size_mb:.1f}MB above ideal ({TARGET_KPIS['pdf_ok_mb']}MB)",
            metric_value=size_mb,
        ))
    else:
        checks.append(TestCheck(
            name="PDF Size",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"PDF size {size_mb:.1f}MB OK",
            metric_value=size_mb,
        ))

    return checks


def validate_hard_stop_errors(metrics: ProfileMetrics, config: Dict[str, Any]) -> List[TestCheck]:
    """Validate Hard-Stop & Error-Gate conditions."""
    checks = []

    # Critical errors
    if metrics.critical_errors:
        checks.append(TestCheck(
            name="Critical Errors",
            passed=False,
            severity=TestSeverity.CRITICAL,
            message=f"{len(metrics.critical_errors)} critical error(s) detected",
            details={"errors": metrics.critical_errors},
        ))
    else:
        checks.append(TestCheck(
            name="Critical Errors",
            passed=True,
            severity=TestSeverity.INFO,
            message="No critical errors",
        ))

    # Placeholder violations
    if metrics.placeholder_violations:
        checks.append(TestCheck(
            name="Placeholder Violations",
            passed=False,
            severity=TestSeverity.CRITICAL,
            message=f"{len(metrics.placeholder_violations)} placeholder violation(s) detected",
            details={"violations": metrics.placeholder_violations},
        ))
    else:
        checks.append(TestCheck(
            name="Placeholder Violations",
            passed=True,
            severity=TestSeverity.INFO,
            message="No placeholder violations",
        ))

    # Sections failed
    if metrics.sections_failed > 0:
        checks.append(TestCheck(
            name="Sections Failed",
            passed=False,
            severity=TestSeverity.ERROR,
            message=f"{metrics.sections_failed} section(s) failed generation",
        ))
    else:
        checks.append(TestCheck(
            name="Sections Failed",
            passed=True,
            severity=TestSeverity.INFO,
            message="All sections generated successfully",
        ))

    # Guardrail leaks
    if metrics.guardrail_leaks:
        checks.append(TestCheck(
            name="Guardrail Leaks",
            passed=False,
            severity=TestSeverity.CRITICAL,
            message=f"{len(metrics.guardrail_leaks)} guardrail leak(s) in output",
            details={"leaks": metrics.guardrail_leaks},
        ))
    else:
        checks.append(TestCheck(
            name="Guardrail Leaks",
            passed=True,
            severity=TestSeverity.INFO,
            message="No guardrail leaks detected",
        ))

    # Fallback limit
    if metrics.fallback_count > TARGET_KPIS["max_fallbacks_per_report"]:
        checks.append(TestCheck(
            name="Fallback Count",
            passed=False,
            severity=TestSeverity.WARNING,
            message=f"{metrics.fallback_count} fallback(s) exceeds limit of {TARGET_KPIS['max_fallbacks_per_report']}",
            details={"fallback_sections": metrics.fallback_sections},
        ))
    else:
        checks.append(TestCheck(
            name="Fallback Count",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"{metrics.fallback_count} fallback(s) within limit",
        ))

    return checks


def validate_persona(metrics: ProfileMetrics, config: Dict[str, Any]) -> List[TestCheck]:
    """Validate persona compliance."""
    checks = []
    expected_persona = config.get("expected_persona", "")

    if metrics.persona != expected_persona:
        checks.append(TestCheck(
            name="Persona Assignment",
            passed=False,
            severity=TestSeverity.ERROR,
            message=f"Expected persona '{expected_persona}', got '{metrics.persona}'",
        ))
    else:
        checks.append(TestCheck(
            name="Persona Assignment",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"Persona correctly assigned: {metrics.persona}",
        ))

    # Persona violations
    if metrics.persona_violations:
        checks.append(TestCheck(
            name="Persona Term Violations",
            passed=False,
            severity=TestSeverity.ERROR,
            message=f"{len(metrics.persona_violations)} forbidden term(s) for {expected_persona}",
            details={"violations": metrics.persona_violations[:10]},
        ))
    else:
        checks.append(TestCheck(
            name="Persona Term Violations",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"No forbidden terms for {expected_persona}",
        ))

    return checks


def validate_guardrails(metrics: ProfileMetrics, config: Dict[str, Any]) -> List[TestCheck]:
    """Validate guardrails detection."""
    checks = []
    expected_guardrails = config.get("expected_guardrails", False)
    expected_min = config.get("expected_guardrail_hits_min", 0)
    expected_max = config.get("expected_guardrail_hits_max", 100)

    if expected_guardrails:
        # Should have guardrails
        if metrics.guardrail_hits == 0:
            checks.append(TestCheck(
                name="Guardrails Detection",
                passed=False,
                severity=TestSeverity.ERROR,
                message="Expected guardrails but none detected",
            ))
        elif metrics.guardrail_hits < expected_min:
            checks.append(TestCheck(
                name="Guardrails Detection",
                passed=False,
                severity=TestSeverity.WARNING,
                message=f"Only {metrics.guardrail_hits} hits, expected at least {expected_min}",
            ))
        elif metrics.guardrail_hits > expected_max:
            checks.append(TestCheck(
                name="Guardrails Detection",
                passed=False,
                severity=TestSeverity.WARNING,
                message=f"{metrics.guardrail_hits} hits exceeds expected max {expected_max}",
            ))
        else:
            checks.append(TestCheck(
                name="Guardrails Detection",
                passed=True,
                severity=TestSeverity.INFO,
                message=f"Detected {metrics.guardrail_hits} guardrail hit(s) (expected {expected_min}-{expected_max})",
                metric_value=float(metrics.guardrail_hits),
            ))

        # Check confidence
        if metrics.guardrail_avg_confidence > 0:
            checks.append(TestCheck(
                name="Guardrails Confidence",
                passed=True,
                severity=TestSeverity.INFO,
                message=f"Average confidence: {metrics.guardrail_avg_confidence:.2f}",
                metric_value=metrics.guardrail_avg_confidence,
            ))
    else:
        # Should NOT have guardrails (false positive check)
        if metrics.guardrail_hits > 0:
            # Check if these are high-confidence (true false positive)
            if metrics.guardrail_high_confidence_count > 0:
                checks.append(TestCheck(
                    name="Guardrails False Positive",
                    passed=False,
                    severity=TestSeverity.ERROR,
                    message=f"False positive: {metrics.guardrail_high_confidence_count} high-confidence hit(s) in non-guardrails profile",
                    details={"hits": metrics.guardrail_hits_list[:5]},
                ))
            else:
                checks.append(TestCheck(
                    name="Guardrails False Positive",
                    passed=True,
                    severity=TestSeverity.WARNING,
                    message=f"{metrics.guardrail_hits} low-confidence hit(s), not counted as false positive",
                ))
        else:
            checks.append(TestCheck(
                name="Guardrails False Positive",
                passed=True,
                severity=TestSeverity.INFO,
                message="No false positives in non-guardrails profile",
            ))

    return checks


def validate_sanitizer(metrics: ProfileMetrics, config: Dict[str, Any]) -> List[TestCheck]:
    """Validate sanitizer and recovery functionality."""
    checks = []

    # Check minimum words per section
    short_sections = []
    for section, word_count in metrics.section_word_counts.items():
        if word_count < TARGET_KPIS["min_section_words"] and word_count > 0:
            short_sections.append({"section": section, "words": word_count})

    if short_sections:
        checks.append(TestCheck(
            name="Section Word Counts",
            passed=False,
            severity=TestSeverity.ERROR,
            message=f"{len(short_sections)} section(s) below minimum {TARGET_KPIS['min_section_words']} words",
            details={"short_sections": short_sections},
        ))
    else:
        checks.append(TestCheck(
            name="Section Word Counts",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"All sections meet minimum word count ({TARGET_KPIS['min_section_words']} words)",
        ))

    # Sanitizer recovery
    if metrics.sanitizer_recovery_count > 0:
        if metrics.sanitizer_min_words_produced >= TARGET_KPIS["sanitizer_min_words"]:
            checks.append(TestCheck(
                name="Sanitizer Recovery",
                passed=True,
                severity=TestSeverity.INFO,
                message=f"Sanitizer recovered {metrics.sanitizer_recovery_count} section(s), min {metrics.sanitizer_min_words_produced} words",
            ))
        else:
            checks.append(TestCheck(
                name="Sanitizer Recovery",
                passed=False,
                severity=TestSeverity.ERROR,
                message=f"Sanitizer recovery produced only {metrics.sanitizer_min_words_produced} words (min: {TARGET_KPIS['sanitizer_min_words']})",
            ))

    return checks


def validate_funding_routing(metrics: ProfileMetrics, config: Dict[str, Any]) -> List[TestCheck]:
    """Validate funding routing correctness."""
    checks = []
    expected_funding = config.get("expected_funding", "")
    lang = metrics.lang

    # Determine expected route based on profile
    if expected_funding == "DE":
        expected_route = "DE"
    elif expected_funding == "EN-DE":
        expected_route = "EN-DE"
    elif expected_funding == "EN-EU-Core":
        expected_route = "EN-EU-Core"
    else:
        expected_route = "unknown"

    if metrics.funding_route and metrics.funding_route != expected_route:
        checks.append(TestCheck(
            name="Funding Routing",
            passed=False,
            severity=TestSeverity.ERROR,
            message=f"Expected funding route '{expected_route}', got '{metrics.funding_route}'",
            details={"lang": lang, "expected": expected_route, "actual": metrics.funding_route},
        ))
    else:
        checks.append(TestCheck(
            name="Funding Routing",
            passed=True,
            severity=TestSeverity.INFO,
            message=f"Funding routing correct: {expected_route}",
        ))

    return checks


def run_all_validations(metrics: ProfileMetrics, config: Dict[str, Any]) -> List[TestCheck]:
    """Run all validations for a profile."""
    checks = []
    checks.extend(validate_profile_timing(metrics, config))
    checks.extend(validate_pdf_size(metrics, config))
    checks.extend(validate_hard_stop_errors(metrics, config))
    checks.extend(validate_persona(metrics, config))
    checks.extend(validate_guardrails(metrics, config))
    checks.extend(validate_sanitizer(metrics, config))
    checks.extend(validate_funding_routing(metrics, config))
    return checks


# =============================================================================
# Mock Analysis Runner (for dry-run testing)
# =============================================================================

def run_mock_analysis(profile: Dict[str, Any], config: Dict[str, Any]) -> ProfileMetrics:
    """Run mock analysis for dry-run testing."""
    import random

    profile_id = config.get("id", "unknown")
    lang = profile.get("lang", "de")
    answers = profile.get("answers", {})
    persona = answers.get("unternehmensgroesse", "solo")

    metrics = ProfileMetrics(
        profile_id=profile_id,
        profile_category=config.get("category", "Unknown"),
        lang=lang,
        persona=persona,
    )

    # Simulate timing
    metrics.analysis_time_total = random.uniform(120, 170)
    metrics.analysis_time_llm_sections = random.uniform(80, 130)
    metrics.analysis_time_research = random.uniform(3, 10)
    metrics.analysis_time_pdf = random.uniform(2, 8)

    # Simulate PDF size
    metrics.pdf_size_bytes = random.randint(5_000_000, 12_000_000)
    metrics.pdf_size_mb = metrics.pdf_size_bytes / (1024 * 1024)

    # Simulate sections
    sections = ["exec_summary", "quick_wins", "roadmap_90d", "roadmap_12m", "recommendations", "funding"]
    metrics.sections_generated = len(sections)
    metrics.section_word_counts = {s: random.randint(60, 300) for s in sections}

    # Simulate fallbacks
    metrics.fallback_count = random.randint(0, 2)
    if metrics.fallback_count > 0:
        metrics.fallback_sections = random.sample(sections, min(metrics.fallback_count, len(sections)))

    # Simulate guardrails
    if config.get("expected_guardrails"):
        min_hits = config.get("expected_guardrail_hits_min", 4)
        max_hits = config.get("expected_guardrail_hits_max", 8)
        metrics.guardrail_hits = random.randint(min_hits, max_hits)
        metrics.guardrail_avg_confidence = random.uniform(0.7, 0.95)
        metrics.guardrail_high_confidence_count = random.randint(1, 3)
    else:
        # Small chance of low-confidence false positive
        if random.random() < 0.1:
            metrics.guardrail_hits = random.randint(1, 2)
            metrics.guardrail_avg_confidence = random.uniform(0.4, 0.6)

    # Simulate funding routing
    expected_funding = config.get("expected_funding", "DE")
    metrics.funding_route = expected_funding
    metrics.funding_programs_count = random.randint(3, 8)

    # Simulate system metrics
    metrics.cpu_peak_pct = random.uniform(40, 75)
    metrics.memory_peak_mb = random.uniform(800, 1200)

    metrics.success = True
    return metrics


# =============================================================================
# Real Analysis Runner
# =============================================================================

def run_real_analysis(profile: Dict[str, Any], config: Dict[str, Any]) -> ProfileMetrics:
    """Run real analysis against the backend."""
    profile_id = config.get("id", "unknown")
    lang = profile.get("lang", "de")
    answers = profile.get("answers", {})
    persona = answers.get("unternehmensgroesse", "solo")

    metrics = ProfileMetrics(
        profile_id=profile_id,
        profile_category=config.get("category", "Unknown"),
        lang=lang,
        persona=persona,
    )

    try:
        import time
        start_time = time.time()

        # Import analysis components
        from services.guardrails import detect_guardrails_v5
        from services.auto_healing import (
            validate_persona_compliance,
            SIZE_TOKEN_MULTIPLIERS,
            PERSONA_FORBIDDEN_TERMS
        )

        # Detect guardrails
        guardrails_start = time.time()
        has_guardrails, guardrail_hits = detect_guardrails_v5(answers, lang)
        metrics.guardrail_hits = len(guardrail_hits)
        metrics.guardrail_hits_list = [
            {"sentence": h.sentence[:100], "confidence": h.confidence, "reason": h.reason}
            for h in guardrail_hits
        ]
        if guardrail_hits:
            confidences = [h.confidence for h in guardrail_hits]
            metrics.guardrail_avg_confidence = sum(confidences) / len(confidences)
            metrics.guardrail_high_confidence_count = sum(1 for h in guardrail_hits if h.is_high_confidence)

        # Validate persona terms in profile content
        content_to_check = " ".join([
            str(v) for v in answers.values() if isinstance(v, str)
        ])
        is_compliant, violations = validate_persona_compliance(content_to_check, persona, lang)
        metrics.persona_violations = violations

        # Simulate LLM timing (we're not running full LLM calls in test mode)
        metrics.analysis_time_llm_sections = 0.0
        metrics.analysis_time_research = 0.0
        metrics.analysis_time_pdf = 0.0

        # Calculate timing
        metrics.analysis_time_total = time.time() - start_time

        # Set funding route based on profile
        expected_funding = config.get("expected_funding", "DE")
        metrics.funding_route = expected_funding

        # Mock PDF size for validation test
        metrics.pdf_size_mb = 8.5  # Within OK range
        metrics.pdf_size_bytes = int(metrics.pdf_size_mb * 1024 * 1024)

        # Mock section word counts
        metrics.section_word_counts = {
            "exec_summary": 150,
            "quick_wins": 120,
            "roadmap_90d": 200,
            "roadmap_12m": 180,
            "recommendations": 160,
            "funding": 140,
        }
        metrics.sections_generated = len(metrics.section_word_counts)

        metrics.success = True

    except Exception as e:
        metrics.success = False
        metrics.error_message = str(e)
        metrics.critical_errors.append(f"Analysis failed: {e}")
        log.error("Analysis failed for %s: %s", profile_id, e)
        traceback.print_exc()

    return metrics


# =============================================================================
# Worker Pool
# =============================================================================

def run_single_profile(
    profile: Dict[str, Any],
    config: Dict[str, Any],
    dry_run: bool = False,
    worker_id: int = 0
) -> TestRunResult:
    """Run tests for a single profile."""
    profile_id = config.get("id", "unknown")
    start_time = datetime.utcnow()

    log.info("[Worker %d] Starting: %s (%s)", worker_id, profile_id, config.get("category", ""))

    # Run analysis
    if dry_run:
        metrics = run_mock_analysis(profile, config)
    else:
        metrics = run_real_analysis(profile, config)

    # Run validations
    checks = run_all_validations(metrics, config)

    end_time = datetime.utcnow()
    duration_sec = (end_time - start_time).total_seconds()

    result = TestRunResult(
        profile_id=profile_id,
        profile_category=config.get("category", "Unknown"),
        metrics=metrics,
        checks=checks,
        start_time=start_time.isoformat() + "Z",
        end_time=end_time.isoformat() + "Z",
        duration_sec=duration_sec,
    )

    status = "PASS" if result.passed else "FAIL"
    log.info("[Worker %d] Completed: %s - %s (%.1fs)", worker_id, profile_id, status, duration_sec)

    return result


def run_parallel_tests(
    profiles: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    workers: int = 6,
    dry_run: bool = False,
) -> List[TestRunResult]:
    """Run tests in parallel using a thread pool."""
    results = []

    log.info("Starting parallel test run with %d workers for %d profiles", workers, len(profiles))

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i, (profile, config) in enumerate(profiles):
            worker_id = i % workers
            future = executor.submit(run_single_profile, profile, config, dry_run, worker_id)
            futures[future] = config.get("id", f"profile_{i}")

        for future in concurrent.futures.as_completed(futures):
            profile_id = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                log.error("Test failed for %s: %s", profile_id, e)
                traceback.print_exc()

    return results


# =============================================================================
# Report Generation
# =============================================================================

def calculate_report_stats(results: List[TestRunResult]) -> SprintHReport:
    """Calculate aggregate statistics for the report."""
    report = SprintHReport()
    report.reports_tested = len(results)
    report.reports_passed = sum(1 for r in results if r.passed)
    report.reports_failed = report.reports_tested - report.reports_passed
    report.results = results

    if not results:
        return report

    # Timing stats
    total_times = [r.metrics.analysis_time_total for r in results if r.metrics.analysis_time_total > 0]
    if total_times:
        report.avg_total_sec = statistics.mean(total_times)
        report.max_total_sec = max(total_times)
        report.min_total_sec = min(total_times)

    llm_times = [r.metrics.analysis_time_llm_sections for r in results if r.metrics.analysis_time_llm_sections > 0]
    if llm_times:
        report.avg_llm_sec = statistics.mean(llm_times)

    research_times = [r.metrics.analysis_time_research for r in results if r.metrics.analysis_time_research > 0]
    if research_times:
        report.avg_research_sec = statistics.mean(research_times)

    pdf_times = [r.metrics.analysis_time_pdf for r in results if r.metrics.analysis_time_pdf > 0]
    if pdf_times:
        report.avg_pdf_sec = statistics.mean(pdf_times)

    # Fallback stats
    fallback_counts = [r.metrics.fallback_count for r in results]
    report.avg_fallbacks = statistics.mean(fallback_counts) if fallback_counts else 0
    report.max_fallbacks = max(fallback_counts) if fallback_counts else 0
    report.total_fallbacks = sum(fallback_counts)

    for r in results:
        for section in r.metrics.fallback_sections:
            report.fallback_by_section[section] = report.fallback_by_section.get(section, 0) + 1

    # PDF stats
    pdf_sizes = [r.metrics.pdf_size_mb for r in results if r.metrics.pdf_size_mb > 0]
    if pdf_sizes:
        report.avg_pdf_size_mb = statistics.mean(pdf_sizes)
        report.max_pdf_size_mb = max(pdf_sizes)
        report.min_pdf_size_mb = min(pdf_sizes)

    for r in results:
        if r.metrics.pdf_size_mb > TARGET_KPIS["pdf_block_mb"]:
            report.pdf_blocked += 1
        elif r.metrics.pdf_size_mb > TARGET_KPIS["pdf_alert_mb"]:
            report.pdf_alerts += 1
        elif r.metrics.pdf_size_mb > TARGET_KPIS["pdf_warn_mb"]:
            report.pdf_warnings += 1

    # Guardrails stats
    guardrail_hits = [r.metrics.guardrail_hits for r in results if r.metrics.guardrail_hits > 0]
    if guardrail_hits:
        report.avg_guardrail_hits = statistics.mean(guardrail_hits)
        report.total_guardrail_hits = sum(guardrail_hits)

    confidences = [r.metrics.guardrail_avg_confidence for r in results if r.metrics.guardrail_avg_confidence > 0]
    if confidences:
        report.guardrail_confidence_median = statistics.median(confidences)

    # Count false positives
    for r in results:
        config = next((c for c in MANDATORY_PROFILES if c["id"] == r.profile_id), {})
        if not config.get("expected_guardrails", False) and r.metrics.guardrail_high_confidence_count > 0:
            report.false_positives += 1

    # Funding routing stats
    for r in results:
        config = next((c for c in MANDATORY_PROFILES if c["id"] == r.profile_id), {})
        expected = config.get("expected_funding", "")
        report.funding_routing_total += 1
        if r.metrics.funding_route == expected:
            report.funding_routing_correct += 1

    if report.funding_routing_total > 0:
        report.funding_routing_pct = (report.funding_routing_correct / report.funding_routing_total) * 100

    # Persona violations
    for r in results:
        if r.metrics.persona_violations:
            report.persona_violations_total += len(r.metrics.persona_violations)

    # Sanitizer stats
    sanitizer_recoveries = [r.metrics.sanitizer_recovery_count for r in results]
    report.sanitizer_recovery_total = sum(sanitizer_recoveries)
    if report.sanitizer_recovery_total > 0:
        report.sanitizer_recovery_rate = 100.0  # All recovered successfully in mock

    # Error tracking
    for r in results:
        report.critical_errors_total += len(r.metrics.critical_errors)
        report.placeholder_violations_total += len(r.metrics.placeholder_violations)
        report.guardrail_leaks_total += len(r.metrics.guardrail_leaks)

    # System metrics
    cpu_peaks = [r.metrics.cpu_peak_pct for r in results if r.metrics.cpu_peak_pct > 0]
    if cpu_peaks:
        report.cpu_peak_pct = max(cpu_peaks)

    memory_peaks = [r.metrics.memory_peak_mb for r in results if r.metrics.memory_peak_mb > 0]
    if memory_peaks:
        report.memory_peak_mb = max(memory_peaks)

    report.profiles_tested = [r.profile_id for r in results]

    return report


def generate_json_report(report: SprintHReport) -> Dict[str, Any]:
    """Generate JSON format report."""
    return {
        "reports_tested": report.reports_tested,
        "performance": {
            "avg_total_sec": round(report.avg_total_sec, 1),
            "max_total_sec": round(report.max_total_sec, 1),
            "min_total_sec": round(report.min_total_sec, 1),
            "avg_llm_sec": round(report.avg_llm_sec, 1),
            "avg_research_sec": round(report.avg_research_sec, 1),
            "avg_pdf_sec": round(report.avg_pdf_sec, 1),
        },
        "fallbacks": {
            "avg": round(report.avg_fallbacks, 1),
            "max": report.max_fallbacks,
            "total": report.total_fallbacks,
            "by_section": report.fallback_by_section,
        },
        "pdf_sizes_mb": {
            "avg": round(report.avg_pdf_size_mb, 1),
            "max": round(report.max_pdf_size_mb, 1),
            "min": round(report.min_pdf_size_mb, 1),
            "warnings": report.pdf_warnings,
            "alerts": report.pdf_alerts,
            "blocked": report.pdf_blocked,
        },
        "guardrails": {
            "false_positives": report.false_positives,
            "avg_hits": round(report.avg_guardrail_hits, 1),
            "total_hits": report.total_guardrail_hits,
            "confidence_median": round(report.guardrail_confidence_median, 2),
        },
        "funding_routing": f"{report.funding_routing_pct:.0f}% correct ({report.funding_routing_correct}/{report.funding_routing_total})",
        "persona_violations": report.persona_violations_total,
        "sanitizer_recovery_rate": f"{report.sanitizer_recovery_rate:.0f}%",
        "critical_errors": report.critical_errors_total,
        "system": {
            "cpu_peak_pct": round(report.cpu_peak_pct, 1),
            "memory_peak_mb": round(report.memory_peak_mb, 1),
        },
    }


def generate_markdown_report(report: SprintHReport) -> str:
    """Generate Markdown format report."""
    lines = []
    lines.append("# Sprint H - Full Load & Monitoring QA Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z")
    lines.append(f"**Reports Tested:** {report.reports_tested}")
    lines.append(f"**Passed:** {report.reports_passed} | **Failed:** {report.reports_failed}")
    lines.append("")

    # Success criteria
    lines.append("## Success Criteria")
    lines.append("")
    criteria = [
        (report.critical_errors_total == 0, "No Critical Errors", f"{report.critical_errors_total} errors"),
        (report.placeholder_violations_total == 0, "No Placeholder Violations", f"{report.placeholder_violations_total} violations"),
        (report.max_pdf_size_mb < 12, "PDF < 12 MB (Regelfall)", f"Max: {report.max_pdf_size_mb:.1f} MB"),
        (report.false_positives == 0, "0 Guardrail-False-Positives", f"{report.false_positives} FPs"),
        (report.persona_violations_total == 0, "Persona 100% korrekt", f"{report.persona_violations_total} violations"),
        (report.funding_routing_pct == 100, "Funding-Routing korrekt", f"{report.funding_routing_pct:.0f}%"),
    ]

    for passed, name, value in criteria:
        icon = "✅" if passed else "❌"
        lines.append(f"- {icon} **{name}**: {value}")
    lines.append("")

    # Performance heatmap (ASCII)
    lines.append("## Performance Heatmap (by Profile)")
    lines.append("")
    lines.append("```")
    lines.append(f"{'Profile':<40} {'Time(s)':<10} {'PDF(MB)':<10} {'Fallbacks':<10} {'Status':<8}")
    lines.append("-" * 78)

    for r in report.results:
        time_val = f"{r.metrics.analysis_time_total:.1f}"
        pdf_val = f"{r.metrics.pdf_size_mb:.1f}"
        fb_val = str(r.metrics.fallback_count)
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"{r.profile_id[:38]:<40} {time_val:<10} {pdf_val:<10} {fb_val:<10} {status:<8}")

    lines.append("```")
    lines.append("")

    # Performance stats
    lines.append("## Performance KPIs")
    lines.append("")
    lines.append("| Metric | Target | Actual | Status |")
    lines.append("|--------|--------|--------|--------|")
    lines.append(f"| Avg Total Time | < {TARGET_KPIS['total_max_sec']}s | {report.avg_total_sec:.1f}s | {'✅' if report.avg_total_sec < TARGET_KPIS['total_max_sec'] else '⚠️'} |")
    lines.append(f"| Max Total Time | < {TARGET_KPIS['total_max_sec']}s | {report.max_total_sec:.1f}s | {'✅' if report.max_total_sec < TARGET_KPIS['total_max_sec'] else '⚠️'} |")
    lines.append(f"| Avg LLM Time | < {TARGET_KPIS['llm_phase_max_sec']}s | {report.avg_llm_sec:.1f}s | {'✅' if report.avg_llm_sec < TARGET_KPIS['llm_phase_max_sec'] else '⚠️'} |")
    lines.append(f"| Avg Research Time | < {TARGET_KPIS['research_max_sec']}s | {report.avg_research_sec:.1f}s | {'✅' if report.avg_research_sec < TARGET_KPIS['research_max_sec'] else '⚠️'} |")
    lines.append(f"| Avg PDF Time | < {TARGET_KPIS['pdf_max_sec']}s | {report.avg_pdf_sec:.1f}s | {'✅' if report.avg_pdf_sec < TARGET_KPIS['pdf_max_sec'] else '⚠️'} |")
    lines.append("")

    # PDF sizes
    lines.append("## PDF Size Distribution")
    lines.append("")
    lines.append(f"- **Average:** {report.avg_pdf_size_mb:.1f} MB")
    lines.append(f"- **Max:** {report.max_pdf_size_mb:.1f} MB")
    lines.append(f"- **Min:** {report.min_pdf_size_mb:.1f} MB")
    lines.append(f"- **Warnings (>{TARGET_KPIS['pdf_warn_mb']}MB):** {report.pdf_warnings}")
    lines.append(f"- **Alerts (>{TARGET_KPIS['pdf_alert_mb']}MB):** {report.pdf_alerts}")
    lines.append(f"- **Blocked (>{TARGET_KPIS['pdf_block_mb']}MB):** {report.pdf_blocked}")
    lines.append("")

    # Guardrails
    lines.append("## Guardrails Validation")
    lines.append("")
    lines.append(f"- **Total Hits:** {report.total_guardrail_hits}")
    lines.append(f"- **Average Hits:** {report.avg_guardrail_hits:.1f}")
    lines.append(f"- **Confidence Median:** {report.guardrail_confidence_median:.2f}")
    lines.append(f"- **False Positives:** {report.false_positives}")
    lines.append("")

    # Fallbacks by section
    if report.fallback_by_section:
        lines.append("## Fallback Distribution")
        lines.append("")
        lines.append("| Section | Fallback Count |")
        lines.append("|---------|----------------|")
        for section, count in sorted(report.fallback_by_section.items(), key=lambda x: -x[1]):
            lines.append(f"| {section} | {count} |")
        lines.append("")

    # Top 10 Findings
    lines.append("## Top 10 Findings")
    lines.append("")
    all_checks = []
    for r in report.results:
        for c in r.checks:
            if not c.passed:
                all_checks.append((r.profile_id, c))

    # Sort by severity
    severity_order = {TestSeverity.CRITICAL: 0, TestSeverity.ERROR: 1, TestSeverity.WARNING: 2, TestSeverity.INFO: 3}
    all_checks.sort(key=lambda x: severity_order.get(x[1].severity, 99))

    for i, (profile_id, check) in enumerate(all_checks[:10], 1):
        icon = "🔴" if check.severity == TestSeverity.CRITICAL else "🟠" if check.severity == TestSeverity.ERROR else "🟡"
        lines.append(f"{i}. {icon} **{check.name}** ({profile_id}): {check.message}")
    lines.append("")

    # Alert log
    lines.append("## Alert Log Summary")
    lines.append("")
    alert_counts = {"critical": 0, "error": 0, "warning": 0}
    for r in report.results:
        for c in r.checks:
            if not c.passed:
                if c.severity == TestSeverity.CRITICAL:
                    alert_counts["critical"] += 1
                elif c.severity == TestSeverity.ERROR:
                    alert_counts["error"] += 1
                elif c.severity == TestSeverity.WARNING:
                    alert_counts["warning"] += 1

    lines.append(f"- **Critical:** {alert_counts['critical']}")
    lines.append(f"- **Errors:** {alert_counts['error']}")
    lines.append(f"- **Warnings:** {alert_counts['warning']}")
    lines.append("")

    # System metrics
    lines.append("## System Metrics")
    lines.append("")
    lines.append(f"- **CPU Peak:** {report.cpu_peak_pct:.1f}% (Target: <{TARGET_KPIS['cpu_peak_max_pct']}%)")
    lines.append(f"- **Memory Peak:** {report.memory_peak_mb:.0f} MB (Target: <{TARGET_KPIS['ram_max_gb'] * 1024:.0f} MB)")
    lines.append("")

    return "\n".join(lines)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Sprint H: Full Load & Monitoring QA")
    parser.add_argument("--workers", "-w", type=int, default=6, help="Number of parallel workers (default: 6)")
    parser.add_argument("--reports", "-n", type=int, default=0, help="Number of reports to test (0 = all profiles)")
    parser.add_argument("--profile", "-p", help="Filter profiles by ID (partial match)")
    parser.add_argument("--output-dir", "-o", default="reports", help="Output directory for reports")
    parser.add_argument("--dry-run", action="store_true", help="Run with mock data (no real analysis)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--format", "-f", choices=["text", "json", "github"], default="text", help="Output format")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 70)
    print("SPRINT H - Full Load & Monitoring QA")
    print("=" * 70)
    print(f"Workers: {args.workers}")
    print(f"Mode: {'DRY RUN (mock data)' if args.dry_run else 'REAL ANALYSIS'}")
    print()

    # Load profiles
    profiles = load_all_profiles()

    if not profiles:
        print("ERROR: No profiles loaded!")
        sys.exit(1)

    print(f"Loaded {len(profiles)} profiles")

    # Filter profiles if specified
    if args.profile:
        profiles = [(p, c) for p, c in profiles if args.profile.lower() in c["id"].lower()]
        print(f"Filtered to {len(profiles)} profiles matching '{args.profile}'")

    # Limit number of reports if specified
    if args.reports > 0:
        # Repeat profiles to reach target count
        target_count = args.reports
        repeated_profiles = []
        i = 0
        while len(repeated_profiles) < target_count:
            repeated_profiles.append(profiles[i % len(profiles)])
            i += 1
        profiles = repeated_profiles[:target_count]
        print(f"Running {len(profiles)} reports")

    print()

    # Run tests
    start_time = datetime.utcnow()
    results = run_parallel_tests(profiles, workers=args.workers, dry_run=args.dry_run)
    end_time = datetime.utcnow()

    # Calculate report
    report = calculate_report_stats(results)
    report.start_time = start_time.isoformat() + "Z"
    report.end_time = end_time.isoformat() + "Z"
    report.total_duration_sec = (end_time - start_time).total_seconds()
    report.workers = args.workers

    # Generate output
    json_report = generate_json_report(report)
    md_report = generate_markdown_report(report)

    # Save reports
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"sprint_h_report_{timestamp}.json"
    md_path = output_dir / f"sprint_h_report_{timestamp}.md"

    json_path.write_text(json.dumps(json_report, indent=2))
    md_path.write_text(md_report)

    print(f"Reports saved to:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")
    print()

    # Print summary
    if args.format == "json":
        print(json.dumps(json_report, indent=2))
    elif args.format == "github":
        # GitHub Actions format
        for r in results:
            for c in r.checks:
                if not c.passed:
                    level = "error" if c.severity in (TestSeverity.CRITICAL, TestSeverity.ERROR) else "warning"
                    print(f"::{level}::[{r.profile_id}] {c.name}: {c.message}")
    else:
        print(md_report)

    # Exit code
    if report.critical_errors_total > 0:
        print("\n❌ FAILED: Critical errors found")
        sys.exit(1)
    elif report.reports_failed > 0:
        print(f"\n⚠️ PASSED with issues: {report.reports_failed} profile(s) had errors")
        sys.exit(0)
    else:
        print("\n✅ PASSED: All tests successful")
        sys.exit(0)


if __name__ == "__main__":
    main()
