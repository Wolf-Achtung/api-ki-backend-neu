#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprint G15-B: Release R1 E2E Go-Live Checks

Automated end-to-end tests for Gold Profile validation.
Tests the three standard profiles against acceptance criteria.

Usage:
    python scripts/run_release_e2e_check.py [--base-url URL] [--mock]

Gold Profiles Tested:
1. solo_beratung_ki_assessments (DE, Solo)
2. team_finance_insurance_advisory (DE, Team, Finance - high-risk expected)
3. kmu_france_eu_core_en_gold (EN, KMU, France - EU funding)

Version: 1.0.0 (Release R1)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# =============================================================================
# TEST RESULT DATA STRUCTURES
# =============================================================================

@dataclass
class ProfileTestResult:
    """Result of testing a single gold profile."""
    profile_id: str
    status: str = "pending"  # OK, WARN, FAIL
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warned: int = 0
    messages: List[str] = field(default_factory=list)
    duration_sec: float = 0.0
    response_data: Optional[Dict[str, Any]] = None

    def add_pass(self, msg: str) -> None:
        self.checks_passed += 1
        self.messages.append(f"[PASS] {msg}")

    def add_fail(self, msg: str) -> None:
        self.checks_failed += 1
        self.messages.append(f"[FAIL] {msg}")
        self.status = "FAIL"

    def add_warn(self, msg: str) -> None:
        self.checks_warned += 1
        self.messages.append(f"[WARN] {msg}")
        if self.status != "FAIL":
            self.status = "WARN"

    def finalize(self) -> None:
        if self.status == "pending":
            if self.checks_failed > 0:
                self.status = "FAIL"
            elif self.checks_warned > 0:
                self.status = "WARN"
            else:
                self.status = "OK"


@dataclass
class E2ETestSuite:
    """Overall E2E test suite results."""
    profiles_tested: int = 0
    profiles_ok: int = 0
    profiles_warn: int = 0
    profiles_fail: int = 0
    results: List[ProfileTestResult] = field(default_factory=list)
    total_duration_sec: float = 0.0

    def add_result(self, result: ProfileTestResult) -> None:
        self.results.append(result)
        self.profiles_tested += 1
        if result.status == "OK":
            self.profiles_ok += 1
        elif result.status == "WARN":
            self.profiles_warn += 1
        else:
            self.profiles_fail += 1

    @property
    def overall_status(self) -> str:
        if self.profiles_fail > 0:
            return "FAIL"
        elif self.profiles_warn > 0:
            return "WARN"
        else:
            return "OK"


# =============================================================================
# GOLD PROFILE DEFINITIONS
# =============================================================================

GOLD_PROFILES = [
    {
        "path": "data/test_profiles_gold/solo_beratung_ki_assessments.json",
        "id": "solo_beratung_ki_assessments",
        "criteria": {
            "ai_act_risk_level": ["minimal", "none"],  # Solo should be low risk
            "size_label": "solo",
            "bc_modifiers_applied": False,  # Solo shouldn't need BC mods
            "lang": "de",
        },
    },
    {
        "path": "data/test_profiles_gold/team_finance_insurance_advisory.json",
        "id": "team_finance_insurance_advisory",
        "criteria": {
            "ai_act_risk_level": ["high-risk", "limited"],  # Finance = regulated
            "size_label": "team",
            "bc_modifiers_applied": True,  # High-risk should apply mods
            "capex_modifier_min": 1.0,  # Should have modifier >= 1.0
            "opex_modifier_min": 1.0,
            "lang": "de",
        },
    },
    {
        "path": "data/test_profiles_gold/kmu_france_eu_core_en_gold.json",
        "id": "kmu_france_eu_core_en_gold",
        "criteria": {
            "ai_act_risk_level": ["minimal", "limited"],  # Consulting = lower risk
            "size_label": "kmu",
            "lang": "en",
            "funding_scope_includes": "EU",  # Should have EU funding refs
            "country": "France",
        },
    },
]


# =============================================================================
# MOCK MODE - For testing without live API
# =============================================================================

def get_mock_response(profile_id: str) -> Dict[str, Any]:
    """
    Generate mock response for testing without live API.

    Returns simulated report metadata based on profile ID.
    """
    mock_responses = {
        "solo_beratung_ki_assessments": {
            "report_id": "mock_solo_001",
            "version": 1,
            "lang": "de",
            "size_category": "solo",
            "ai_act": {
                "AI_ACT_RISK_LEVEL": "minimal",
                "CAPEX_MODIFIER": 1.0,
                "OPEX_MODIFIER": 1.0,
            },
            "business_case": {
                "AI_ACT_BC_APPLIED": False,
                "CAPEX_REALISTISCH_EUR": 5000,
                "OPEX_REALISTISCH_EUR": 200,
                "ROI_12M": 180,
            },
            "scores": {
                "OVERALL_SCORE": 72,
                "GOVERNANCE_SCORE": 65,
                "SECURITY_SCORE": 78,
            },
        },
        "team_finance_insurance_advisory": {
            "report_id": "mock_team_002",
            "version": 1,
            "lang": "de",
            "size_category": "team",
            "ai_act": {
                "AI_ACT_RISK_LEVEL": "high-risk",
                "CAPEX_MODIFIER": 1.15,
                "OPEX_MODIFIER": 1.10,
            },
            "business_case": {
                "AI_ACT_BC_APPLIED": True,
                "AI_ACT_BC_CAPEX_FACTOR": 1.15,
                "AI_ACT_BC_OPEX_FACTOR": 1.10,
                "CAPEX_REALISTISCH_EUR": 45000,
                "OPEX_REALISTISCH_EUR": 2500,
                "ROI_12M": 95,
            },
            "scores": {
                "OVERALL_SCORE": 68,
                "GOVERNANCE_SCORE": 72,
                "SECURITY_SCORE": 70,
            },
        },
        "kmu_france_eu_core_en_gold": {
            "report_id": "mock_kmu_003",
            "version": 1,
            "lang": "en",
            "size_category": "kmu",
            "country": "France",
            "ai_act": {
                "AI_ACT_RISK_LEVEL": "limited",
                "CAPEX_MODIFIER": 1.05,
                "OPEX_MODIFIER": 1.03,
            },
            "business_case": {
                "AI_ACT_BC_APPLIED": True,
                "CAPEX_REALISTISCH_EUR": 75000,
                "OPEX_REALISTISCH_EUR": 4000,
                "ROI_12M": 120,
            },
            "funding": {
                "FUNDING_SCOPE": "EU Core - Horizon Europe, Digital Europe",
                "programs_count": 5,
            },
            "scores": {
                "OVERALL_SCORE": 75,
                "GOVERNANCE_SCORE": 78,
                "SECURITY_SCORE": 72,
            },
        },
    }
    return mock_responses.get(profile_id, {})


# =============================================================================
# LIVE API MODE
# =============================================================================

def submit_profile_to_api(profile_data: Dict, base_url: str) -> Dict[str, Any]:
    """
    Submit a profile to the live API and get the report.

    Args:
        profile_data: The profile JSON data
        base_url: API base URL

    Returns:
        Report metadata dict
    """
    import requests

    # Submit briefing
    submit_url = f"{base_url}/api/briefings/submit"
    log.info(f"Submitting to {submit_url}")

    try:
        response = requests.post(
            submit_url,
            json=profile_data.get("answers", profile_data),
            headers={"Content-Type": "application/json"},
            timeout=180,  # 3 minutes for report generation
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log.error(f"API request failed: {e}")
        return {"error": str(e)}


# =============================================================================
# VALIDATION LOGIC
# =============================================================================

def validate_profile(
    profile_config: Dict,
    response_data: Dict,
    result: ProfileTestResult
) -> None:
    """
    Validate response data against profile criteria.

    Args:
        profile_config: Profile configuration with criteria
        response_data: API response or mock data
        result: ProfileTestResult to populate
    """
    criteria = profile_config.get("criteria", {})

    # Check for API error
    if response_data.get("error"):
        result.add_fail(f"API Error: {response_data['error']}")
        return

    # Extract data
    ai_act = response_data.get("ai_act", {})
    bc = response_data.get("business_case", {})
    funding = response_data.get("funding", {})

    # 1. Check AI Act Risk Level
    if "ai_act_risk_level" in criteria:
        actual_risk = ai_act.get("AI_ACT_RISK_LEVEL", "unknown")
        expected_risks = criteria["ai_act_risk_level"]
        if actual_risk in expected_risks:
            result.add_pass(f"AI_ACT_RISK_LEVEL={actual_risk} (expected: {expected_risks})")
        else:
            result.add_fail(f"AI_ACT_RISK_LEVEL={actual_risk} (expected: {expected_risks})")

    # 2. Check Size Label
    if "size_label" in criteria:
        actual_size = response_data.get("size_category", "unknown")
        expected_size = criteria["size_label"]
        if actual_size == expected_size:
            result.add_pass(f"size_category={actual_size}")
        else:
            result.add_warn(f"size_category={actual_size} (expected: {expected_size})")

    # 3. Check BC Modifiers Applied
    if "bc_modifiers_applied" in criteria:
        actual_applied = bc.get("AI_ACT_BC_APPLIED", False)
        expected_applied = criteria["bc_modifiers_applied"]
        if actual_applied == expected_applied:
            result.add_pass(f"AI_ACT_BC_APPLIED={actual_applied}")
        else:
            if expected_applied:
                result.add_fail(f"AI_ACT_BC_APPLIED={actual_applied} (expected True)")
            else:
                result.add_warn(f"AI_ACT_BC_APPLIED={actual_applied} (expected False)")

    # 4. Check CAPEX Modifier
    if "capex_modifier_min" in criteria:
        actual_mod = ai_act.get("CAPEX_MODIFIER", 1.0)
        expected_min = criteria["capex_modifier_min"]
        if actual_mod >= expected_min:
            result.add_pass(f"CAPEX_MODIFIER={actual_mod:.2f} >= {expected_min}")
        else:
            result.add_fail(f"CAPEX_MODIFIER={actual_mod:.2f} < {expected_min}")

    # 5. Check OPEX Modifier
    if "opex_modifier_min" in criteria:
        actual_mod = ai_act.get("OPEX_MODIFIER", 1.0)
        expected_min = criteria["opex_modifier_min"]
        if actual_mod >= expected_min:
            result.add_pass(f"OPEX_MODIFIER={actual_mod:.2f} >= {expected_min}")
        else:
            result.add_fail(f"OPEX_MODIFIER={actual_mod:.2f} < {expected_min}")

    # 6. Check Language
    if "lang" in criteria:
        actual_lang = response_data.get("lang", "unknown")
        expected_lang = criteria["lang"]
        if actual_lang == expected_lang:
            result.add_pass(f"lang={actual_lang}")
        else:
            result.add_fail(f"lang={actual_lang} (expected: {expected_lang})")

    # 7. Check Funding Scope (for EU profiles)
    if "funding_scope_includes" in criteria:
        funding_scope = funding.get("FUNDING_SCOPE", "")
        expected_keyword = criteria["funding_scope_includes"]
        if expected_keyword.lower() in funding_scope.lower():
            result.add_pass(f"FUNDING_SCOPE includes '{expected_keyword}'")
        else:
            result.add_warn(f"FUNDING_SCOPE does not include '{expected_keyword}'")

    # 8. Check Country
    if "country" in criteria:
        actual_country = response_data.get("country", "unknown")
        expected_country = criteria["country"]
        if actual_country == expected_country:
            result.add_pass(f"country={actual_country}")
        else:
            result.add_warn(f"country={actual_country} (expected: {expected_country})")

    # Finalize result
    result.finalize()


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_e2e_tests(
    base_url: Optional[str] = None,
    mock_mode: bool = True,
) -> E2ETestSuite:
    """
    Run E2E tests for all gold profiles.

    Args:
        base_url: API base URL (required for live mode)
        mock_mode: If True, use mock responses instead of live API

    Returns:
        E2ETestSuite with all results
    """
    suite = E2ETestSuite()
    start_time = time.time()

    log.info("=" * 78)
    log.info("G15-B: RELEASE R1 E2E GO-LIVE CHECKS")
    log.info("=" * 78)
    log.info(f"Mode: {'MOCK' if mock_mode else 'LIVE'}")
    if base_url:
        log.info(f"Base URL: {base_url}")
    log.info("")

    for profile_config in GOLD_PROFILES:
        profile_id = profile_config["id"]
        profile_path = PROJECT_ROOT / profile_config["path"]

        log.info(f"Testing: {profile_id}")
        log.info("-" * 40)

        result = ProfileTestResult(profile_id=profile_id)
        profile_start = time.time()

        try:
            # Load profile data
            if profile_path.exists():
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
            else:
                result.add_fail(f"Profile file not found: {profile_path}")
                result.finalize()
                suite.add_result(result)
                continue

            # Get response (mock or live)
            if mock_mode:
                response_data = get_mock_response(profile_id)
            else:
                if not base_url:
                    result.add_fail("No base URL provided for live mode")
                    result.finalize()
                    suite.add_result(result)
                    continue
                response_data = submit_profile_to_api(profile_data, base_url)

            result.response_data = response_data

            # Validate
            validate_profile(profile_config, response_data, result)

        except Exception as e:
            result.add_fail(f"Exception: {e}")
            result.finalize()

        result.duration_sec = time.time() - profile_start
        suite.add_result(result)

        # Print results
        for msg in result.messages:
            log.info(f"   {msg}")
        log.info(f"   Status: {result.status} ({result.duration_sec:.1f}s)")
        log.info("")

    suite.total_duration_sec = time.time() - start_time

    # Print summary
    print_summary(suite)

    return suite


def print_summary(suite: E2ETestSuite) -> None:
    """Print test suite summary."""
    log.info("=" * 78)
    log.info("E2E TEST SUMMARY")
    log.info("=" * 78)
    log.info(f"Profiles Tested: {suite.profiles_tested}")
    log.info(f"  OK:   {suite.profiles_ok}")
    log.info(f"  WARN: {suite.profiles_warn}")
    log.info(f"  FAIL: {suite.profiles_fail}")
    log.info(f"Total Duration: {suite.total_duration_sec:.1f}s")
    log.info("-" * 78)
    log.info(f"OVERALL STATUS: {suite.overall_status}")
    log.info("=" * 78)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="G15-B: Release R1 E2E Go-Live Checks"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Use mock mode (default: True)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live API mode",
    )
    args = parser.parse_args()

    mock_mode = not args.live

    suite = run_e2e_tests(
        base_url=args.base_url,
        mock_mode=mock_mode,
    )

    # Exit code based on result
    if suite.overall_status == "FAIL":
        sys.exit(1)
    elif suite.overall_status == "WARN":
        sys.exit(0)  # Warnings are acceptable for R1
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
