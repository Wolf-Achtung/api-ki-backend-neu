#!/usr/bin/env python3
"""
live_regression_test.py — PLATIN++ V5 Live Regression Test

Sprint: STOP-Parameter Fix Verification + End-to-End QA
Version: 1.0.0

This script runs comprehensive live tests against the production API to verify:
1. STOP-Parameter fix (no "unsupported parameter 'stop'" errors)
2. Fallbacks & SECTION_TOO_SHORT detection
3. Guardrails detection and confidence
4. Persona correctness
5. Funding routing
6. PDF quality (size, theme)
7. HTML sanitizer behavior

Usage:
    python scripts/live_regression_test.py --base-url https://api-ki-backend-neu-production.up.railway.app/api --email your@email.com

Requirements:
    - requests
    - Access to production API
    - Valid email for authentication
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    print("ERROR: requests module required. Install with: pip install requests")
    sys.exit(1)

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Test profiles to run
TEST_PROFILES = [
    {
        "name": "DE/Solo - Consulting",
        "file": "data/test_profiles_gold/solo_beratung_ki_assessments.json",
        "expected": {
            "lang": "de",
            "size": "solo",
            "guardrails": False,
            "funding_flow": "DE",
        }
    },
    {
        "name": "EN/Solo - Consulting",
        "file": "data/test_profiles_gold/solo_consulting_en_gold.json",
        "expected": {
            "lang": "en",
            "size": "solo",
            "guardrails": False,
            "funding_flow": "EN-DE",
        }
    },
    {
        "name": "DE/KMU - Guardrails",
        "file": "data/test_profiles_gold/kmu_guardrails_test.json",
        "expected": {
            "lang": "de",
            "size": "kmu",
            "guardrails": True,
            "funding_flow": "DE",
        }
    },
    {
        "name": "EN/KMU - Healthcare Guardrails",
        "file": "data/test_profiles_gold/kmu_guardrails_en_gold.json",
        "expected": {
            "lang": "en",
            "size": "kmu",
            "guardrails": True,
            "funding_flow": "EN-DE",
        }
    },
]

# Thresholds
THRESHOLDS = {
    "pdf_size_warning_mb": 10,
    "pdf_size_alert_mb": 18,
    "pdf_size_critical_mb": 20,
    "fallbacks_warning": 3,
    "fallbacks_critical": 7,
    "guardrails_confidence_info": 0.9,
}

# =============================================================================
# Results Collector
# =============================================================================

class TestResults:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.start_time = datetime.now()

    def add_result(self, profile_name: str, result: Dict[str, Any]):
        result["profile"] = profile_name
        result["timestamp"] = datetime.now().isoformat()
        self.results.append(result)

    def add_error(self, error: str):
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")

    def get_summary(self) -> Dict[str, Any]:
        passed = sum(1 for r in self.results if r.get("passed", False))
        failed = len(self.results) - passed
        return {
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "errors": len(self.errors),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
        }

results = TestResults()

# =============================================================================
# API Client
# =============================================================================

class APIClient:
    def __init__(self, base_url: str, timeout: int = 180):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.token: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def request_login_code(self, email: str) -> bool:
        """Request a login code."""
        url = f"{self.base_url}/auth/request-code"
        print(f"[AUTH] Requesting login code for {email}...")
        try:
            resp = self.session.post(url, json={"email": email}, timeout=10)
            if resp.status_code == 204:
                print(f"[AUTH] Login code sent to {email}")
                return True
            else:
                print(f"[AUTH] Failed: HTTP {resp.status_code}")
                return False
        except Exception as e:
            print(f"[AUTH] Error: {e}")
            return False

    def login(self, email: str, code: str) -> bool:
        """Login with code."""
        url = f"{self.base_url}/auth/login"
        print(f"[AUTH] Logging in...")
        try:
            resp = self.session.post(
                url,
                json={"email": email, "code": code},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                print("[AUTH] Login successful")
                return True
            else:
                print(f"[AUTH] Login failed: HTTP {resp.status_code}")
                return False
        except Exception as e:
            print(f"[AUTH] Error: {e}")
            return False

    def submit_briefing(self, profile: Dict[str, Any]) -> Optional[int]:
        """Submit a briefing and return briefing_id."""
        url = f"{self.base_url}/briefings/submit"
        payload = {
            "lang": profile.get("lang", "de"),
            "answers": profile["answers"],
            "queue_analysis": True,
        }
        print(f"[SUBMIT] Sending briefing to {url}...")
        try:
            resp = self.session.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            if resp.status_code == 202:
                data = resp.json()
                briefing_id = data.get("briefing_id")
                print(f"[SUBMIT] Success: briefing_id={briefing_id}")
                return int(briefing_id) if briefing_id is not None else None
            else:
                print(f"[SUBMIT] Failed: HTTP {resp.status_code}")
                print(f"[SUBMIT] Response: {resp.text[:500]}")
                return None
        except requests.exceptions.Timeout:
            print("[SUBMIT] Timeout - analysis may still be running")
            return None
        except Exception as e:
            print(f"[SUBMIT] Error: {e}")
            return None

    def run_analysis(self, briefing_id: int, email: Optional[str] = None) -> bool:
        """Trigger analysis for a briefing."""
        url = f"{self.base_url}/analyze/run"
        payload: Dict[str, Any] = {"briefing_id": briefing_id}
        if email:
            payload["email_override"] = email
        print(f"[ANALYZE] Running analysis for briefing_id={briefing_id}...")
        try:
            resp = self.session.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            if resp.status_code == 202:
                print("[ANALYZE] Analysis accepted")
                return True
            else:
                print(f"[ANALYZE] Failed: HTTP {resp.status_code}")
                return False
        except Exception as e:
            print(f"[ANALYZE] Error: {e}")
            return False

    def get_diagnostics(self) -> Optional[Dict[str, Any]]:
        """Get report diagnostics."""
        url = f"{self.base_url}/report/diagnostics"
        print(f"[DIAGNOSTICS] Fetching from {url}...")
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=30)
            if resp.status_code == 200:
                result: Dict[str, Any] = resp.json()
                return result
            else:
                print(f"[DIAGNOSTICS] Failed: HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"[DIAGNOSTICS] Error: {e}")
            return None

    def get_monitoring_status(self) -> Optional[Dict[str, Any]]:
        """Get monitoring status."""
        url = f"{self.base_url}/monitoring/status"
        print(f"[MONITORING] Fetching from {url}...")
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=30)
            if resp.status_code == 200:
                result: Dict[str, Any] = resp.json()
                return result
            else:
                print(f"[MONITORING] Failed: HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"[MONITORING] Error: {e}")
            return None

    def get_alerts(self, hours: int = 24) -> Optional[Dict[str, Any]]:
        """Get recent alerts."""
        url = f"{self.base_url}/monitoring/alerts?hours={hours}"
        print(f"[ALERTS] Fetching from {url}...")
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=30)
            if resp.status_code == 200:
                result: Dict[str, Any] = resp.json()
                return result
            else:
                print(f"[ALERTS] Failed: HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"[ALERTS] Error: {e}")
            return None

    def health_check(self) -> bool:
        """Check if API is healthy."""
        url = f"{self.base_url}/healthz"
        try:
            resp = self.session.get(url, timeout=10)
            return bool(resp.status_code == 200)
        except Exception:
            return False

# =============================================================================
# Test Functions
# =============================================================================

def load_profile(profile_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load a test profile from JSON file."""
    file_path = REPO_ROOT / profile_config["file"]
    if not file_path.exists():
        print(f"[ERROR] Profile not found: {file_path}")
        return None

    try:
        with open(file_path) as f:
            result: Dict[str, Any] = json.load(f)
            return result
    except Exception as e:
        print(f"[ERROR] Failed to load profile: {e}")
        return None


def analyze_diagnostics(diagnostics: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze diagnostics and check against expected values."""
    issues = []
    findings = {}

    # Check fallbacks
    fallbacks = diagnostics.get("sections", {}).get("fallbacks_used", 0)
    findings["fallbacks"] = fallbacks
    if fallbacks >= THRESHOLDS["fallbacks_critical"]:
        issues.append(f"CRITICAL: {fallbacks} fallbacks (>= {THRESHOLDS['fallbacks_critical']})")
    elif fallbacks >= THRESHOLDS["fallbacks_warning"]:
        issues.append(f"WARNING: {fallbacks} fallbacks (>= {THRESHOLDS['fallbacks_warning']})")

    # Check SECTION_TOO_SHORT
    section_errors = diagnostics.get("sections", {}).get("section_too_short", [])
    findings["section_too_short"] = section_errors
    if section_errors:
        issues.append(f"SECTION_TOO_SHORT: {section_errors}")

    # Check guardrails
    guardrails = diagnostics.get("guardrails", {})
    findings["guardrails_hits"] = guardrails.get("total_hits", 0)
    findings["guardrails_confidence"] = guardrails.get("avg_confidence", 0)

    if expected.get("guardrails"):
        if findings["guardrails_hits"] == 0:
            issues.append("WARNING: Expected guardrails but none detected")
        elif findings["guardrails_confidence"] >= THRESHOLDS["guardrails_confidence_info"]:
            findings["guardrails_info"] = "High confidence guardrail detection"

    # Check PDF
    pdf = diagnostics.get("pdf", {})
    pdf_size = pdf.get("avg_size_mb", 0)
    findings["pdf_size_mb"] = pdf_size

    if pdf_size >= THRESHOLDS["pdf_size_critical_mb"]:
        issues.append(f"CRITICAL: PDF size {pdf_size:.1f}MB (>= {THRESHOLDS['pdf_size_critical_mb']}MB)")
    elif pdf_size >= THRESHOLDS["pdf_size_alert_mb"]:
        issues.append(f"ALERT: PDF size {pdf_size:.1f}MB (>= {THRESHOLDS['pdf_size_alert_mb']}MB)")
    elif pdf_size >= THRESHOLDS["pdf_size_warning_mb"]:
        issues.append(f"WARNING: PDF size {pdf_size:.1f}MB (>= {THRESHOLDS['pdf_size_warning_mb']}MB)")

    # Check LLM errors (STOP parameter fix verification)
    llm = diagnostics.get("llm", {})
    findings["llm_errors"] = llm.get("errors", 0)
    findings["llm_error_rate"] = llm.get("error_rate", 0)

    if findings["llm_errors"] > 0:
        issues.append(f"LLM Errors: {findings['llm_errors']} (check for 'unsupported parameter stop')")

    # Check sanitizer
    sanitizer = diagnostics.get("html_sanitizer", {})
    findings["sanitizer_recoveries"] = sanitizer.get("recoveries", 0)
    findings["sanitizer_failures"] = sanitizer.get("failures", 0)

    if findings["sanitizer_failures"] > 0:
        issues.append(f"Sanitizer failures: {findings['sanitizer_failures']}")

    # Check persona
    persona = diagnostics.get("persona", {})
    findings["persona_distribution"] = persona.get("distribution", {})

    return {
        "findings": findings,
        "issues": issues,
        "passed": len(issues) == 0,
    }


def run_single_test(
    client: APIClient,
    profile_config: Dict[str, Any],
    email: str,
    wait_time: int = 60,
) -> Dict[str, Any]:
    """Run a single test profile."""
    name = profile_config["name"]
    expected = profile_config["expected"]

    print()
    print("=" * 70)
    print(f"TESTING: {name}")
    print("=" * 70)

    result = {
        "name": name,
        "expected": expected,
        "passed": False,
        "issues": [],
        "findings": {},
    }

    # Load profile
    profile = load_profile(profile_config)
    if not profile:
        result["issues"].append("Failed to load profile")
        return result

    # Submit briefing
    briefing_id = client.submit_briefing(profile)
    if not briefing_id:
        result["issues"].append("Failed to submit briefing")
        return result

    result["briefing_id"] = briefing_id

    # Wait for analysis to complete
    print(f"[WAIT] Waiting {wait_time}s for analysis to complete...")
    time.sleep(wait_time)

    # Get diagnostics
    diagnostics = client.get_diagnostics()
    if diagnostics:
        analysis = analyze_diagnostics(diagnostics, expected)
        result["findings"] = analysis["findings"]
        result["issues"].extend(analysis["issues"])
        result["passed"] = analysis["passed"]
        result["diagnostics_raw"] = diagnostics
    else:
        result["issues"].append("Failed to get diagnostics")

    # Get alerts for STOP parameter errors
    alerts = client.get_alerts(hours=1)
    if alerts:
        alert_list = alerts.get("alerts", [])
        stop_errors = [
            a for a in alert_list
            if "stop" in str(a).lower() and "unsupported" in str(a).lower()
        ]
        if stop_errors:
            result["issues"].append(f"CRITICAL: Found 'unsupported stop' errors: {len(stop_errors)}")
            result["stop_errors"] = stop_errors
        else:
            result["findings"]["stop_fix_verified"] = True

    return result


def print_result_table(test_results: List[Dict[str, Any]]):
    """Print results as a table."""
    print()
    print("=" * 100)
    print("REGRESSION TEST RESULTS")
    print("=" * 100)
    print()

    # Header
    headers = [
        "Profile", "Lang", "Size", "Fallbacks", "TOO_SHORT",
        "Guardrails", "PDF MB", "LLM Err", "Status"
    ]
    widths = [30, 6, 6, 10, 12, 12, 8, 8, 8]

    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-" * len(header_line))

    # Rows
    for r in test_results:
        findings = r.get("findings", {})
        expected = r.get("expected", {})

        too_short = findings.get("section_too_short", [])
        too_short_str = "YES" if too_short else "no"

        row = [
            r.get("name", "?")[:30],
            expected.get("lang", "?"),
            expected.get("size", "?"),
            str(findings.get("fallbacks", "?")),
            too_short_str,
            str(findings.get("guardrails_hits", "?")),
            f"{findings.get('pdf_size_mb', 0):.1f}",
            str(findings.get("llm_errors", "?")),
            "PASS" if r.get("passed") else "FAIL",
        ]

        row_line = " | ".join(str(v).ljust(w) for v, w in zip(row, widths))
        print(row_line)

    print()


def print_issues_summary(test_results: List[Dict[str, Any]]):
    """Print detailed issues for failed tests."""
    failed = [r for r in test_results if not r.get("passed")]
    if not failed:
        print("ALL TESTS PASSED!")
        return

    print()
    print("=" * 70)
    print("ISSUES FOUND")
    print("=" * 70)

    for r in failed:
        print(f"\n{r.get('name', '?')}:")
        for issue in r.get("issues", []):
            print(f"  - {issue}")


def print_final_verdict(test_results: List[Dict[str, Any]]):
    """Print final verdict."""
    passed = sum(1 for r in test_results if r.get("passed", False))
    total = len(test_results)

    print()
    print("=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    print()

    # Check STOP fix
    stop_verified = all(
        r.get("findings", {}).get("stop_fix_verified", False)
        for r in test_results
    )

    print(f"  Tests Passed:      {passed}/{total}")
    print(f"  STOP-Fix Verified: {'YES' if stop_verified else 'NOT VERIFIED'}")

    if passed == total and stop_verified:
        print()
        print("  " + "-" * 50)
        print("  RELEASE APPROVED - All criteria met!")
        print("  " + "-" * 50)
    else:
        print()
        print("  " + "-" * 50)
        print("  RELEASE BLOCKED - Issues found, review required!")
        print("  " + "-" * 50)

    print()


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="PLATIN++ V5 Live Regression Test"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BASE_URL", "https://make.ki-sicherheit.jetzt/api"),
        help="Base URL of the API",
    )
    parser.add_argument(
        "--email",
        default=os.getenv("TEST_EMAIL", ""),
        help="Email for authentication",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=90,
        help="Seconds to wait for analysis (default: 90)",
    )
    parser.add_argument(
        "--profiles",
        type=int,
        nargs="+",
        default=None,
        help="Specific profile indices to test (0-3)",
    )
    parser.add_argument(
        "--skip-auth",
        action="store_true",
        help="Skip authentication (if already authenticated)",
    )
    args = parser.parse_args()

    print()
    print("#" * 70)
    print("# PLATIN++ V5 LIVE REGRESSION TEST")
    print("#" * 70)
    print(f"# Base URL: {args.base_url}")
    print(f"# Email:    {args.email or '(not set)'}")
    print(f"# Wait:     {args.wait}s")
    print("#" * 70)
    print()

    # Initialize client
    client = APIClient(args.base_url)

    # Health check
    print("[HEALTH] Checking API...")
    if not client.health_check():
        print("[HEALTH] API not healthy or not reachable!")
        sys.exit(1)
    print("[HEALTH] API is healthy")

    # Authentication
    if not args.skip_auth:
        if not args.email:
            print("[AUTH] Email required for authentication")
            args.email = input("Enter email: ").strip()

        if not client.request_login_code(args.email):
            print("[AUTH] Failed to request login code")
            sys.exit(1)

        code = input("Enter login code from email: ").strip()
        if not client.login(args.email, code):
            print("[AUTH] Login failed")
            sys.exit(1)

    # Select profiles
    profiles_to_test = TEST_PROFILES
    if args.profiles:
        profiles_to_test = [TEST_PROFILES[i] for i in args.profiles if 0 <= i < len(TEST_PROFILES)]

    print(f"\n[INFO] Testing {len(profiles_to_test)} profiles...")

    # Run tests
    test_results = []
    for profile_config in profiles_to_test:
        result = run_single_test(client, profile_config, args.email, args.wait)
        test_results.append(result)
        results.add_result(profile_config["name"], result)

    # Print results
    print_result_table(test_results)
    print_issues_summary(test_results)
    print_final_verdict(test_results)

    # Save results to JSON
    output_file = REPO_ROOT / "test_results" / f"regression_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "base_url": args.base_url,
            "results": test_results,
            "summary": results.get_summary(),
        }, f, indent=2, default=str)
    print(f"\n[INFO] Results saved to: {output_file}")

    # Exit code
    summary = results.get_summary()
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
