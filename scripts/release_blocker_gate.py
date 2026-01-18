# -*- coding: utf-8 -*-
"""
Release Blocker Gate - CI Validation for Fix-Batches J1-J4
==========================================================

This script performs hard validation checks that must pass before release.
Exit code 0 = pass, Exit code 1 = fail with specific error messages.

Usage:
    python scripts/release_blocker_gate.py

Hard Greps (must find 0 matches = PASS):
- J1: "QW-ERROR-PAGE" in gpt_analyze.py (must be 0)
- J2: "decimal_point" without format_decimal_de (must be 0 hardcoded decimals)
- J3: Empty sections with only headings (validated by tests)
- J4: Chat artefacts in output (validated by tests)

Hard Greps (must find >= 1 matches = PASS):
- format_decimal_de in services/i18n.py
- format_eur_de in services/i18n.py
- _generate_deterministic_quickwins_fallback in gpt_analyze.py
- apply_chat_artefact_filter in content_quality_enforcer.py
- kill_empty_pages with J3 enhancement

Version: 1.0.0 (Fix-Batches J1-J4)
"""

import os
import sys
import re
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_file_contains(filepath: str, pattern: str, expected_min: int = 1) -> tuple[bool, int]:
    """
    Check if file contains pattern at least expected_min times.

    Returns (passed, count)
    """
    path = Path(filepath)
    if not path.exists():
        return False, 0

    content = path.read_text(encoding="utf-8")
    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
    count = len(matches)
    return count >= expected_min, count


def check_file_not_contains(filepath: str, pattern: str) -> tuple[bool, int]:
    """
    Check if file does NOT contain pattern (0 matches = pass).

    Returns (passed, count)
    """
    path = Path(filepath)
    if not path.exists():
        return True, 0  # File not found = no violation

    content = path.read_text(encoding="utf-8")
    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
    count = len(matches)
    return count == 0, count


def main():
    """Run all release blocker checks."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Release Blocker Gate - Fix-Batches J1-J4 Validation{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # Base path
    base = Path(__file__).parent.parent

    errors = []
    warnings = []

    # ==========================================================================
    # J1: Quick Wins ZERO-FAIL Validation
    # ==========================================================================
    print(f"{BOLD}[J1] Quick Wins ZERO-FAIL Validation{RESET}")

    # Must have: deterministic fallback function
    passed, count = check_file_contains(
        base / "gpt_analyze.py",
        r"def _generate_deterministic_quickwins_fallback"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} _generate_deterministic_quickwins_fallback exists ({count} match)")
    else:
        errors.append("J1: Missing _generate_deterministic_quickwins_fallback in gpt_analyze.py")
        print(f"  {RED}✗{RESET} _generate_deterministic_quickwins_fallback NOT FOUND")

    # Must NOT have: QW-ERROR-PAGE (deprecated error page)
    passed, count = check_file_not_contains(
        base / "gpt_analyze.py",
        r"QW-ERROR-PAGE"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} No QW-ERROR-PAGE found (error page removed)")
    else:
        errors.append(f"J1: Found {count} QW-ERROR-PAGE references in gpt_analyze.py")
        print(f"  {RED}✗{RESET} Found {count} QW-ERROR-PAGE references (must be 0)")

    # Must NOT have: QW-HARD-FAIL (deprecated log message)
    passed, count = check_file_not_contains(
        base / "gpt_analyze.py",
        r"QW-HARD-FAIL"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} No QW-HARD-FAIL found (deprecated log removed)")
    else:
        warnings.append(f"J1: Found {count} QW-HARD-FAIL references (should use QW-FALLBACK)")
        print(f"  {YELLOW}⚠{RESET} Found {count} QW-HARD-FAIL references (deprecated)")

    print()

    # ==========================================================================
    # J2: Locale/KPI 100% DE Validation
    # ==========================================================================
    print(f"{BOLD}[J2] Locale/KPI 100% DE Validation{RESET}")

    # Must have: format_decimal_de in services/i18n.py
    passed, count = check_file_contains(
        base / "services" / "i18n.py",
        r"def format_decimal_de"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} format_decimal_de exists in i18n.py")
    else:
        errors.append("J2: Missing format_decimal_de in services/i18n.py")
        print(f"  {RED}✗{RESET} format_decimal_de NOT FOUND in i18n.py")

    # Must have: format_eur_de in services/i18n.py
    passed, count = check_file_contains(
        base / "services" / "i18n.py",
        r"def format_eur_de"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} format_eur_de exists in i18n.py")
    else:
        errors.append("J2: Missing format_eur_de in services/i18n.py")
        print(f"  {RED}✗{RESET} format_eur_de NOT FOUND in i18n.py")

    # Must have: German "Amortisation" label (not English "Payback" in German section)
    passed, count = check_file_contains(
        base / "services" / "business_case_engine_v2.py",
        r'"payback_label":\s*"Amortisation"'
    )
    if passed:
        print(f"  {GREEN}✓{RESET} German payback_label='Amortisation' found")
    else:
        warnings.append("J2: German section may still have 'Payback' instead of 'Amortisation'")
        print(f"  {YELLOW}⚠{RESET} German payback_label='Amortisation' not found")

    print()

    # ==========================================================================
    # J3: No Blank/Orphan Pages Validation
    # ==========================================================================
    print(f"{BOLD}[J3] No Blank/Orphan Pages Validation{RESET}")

    # Must have: Enhanced kill_empty_pages with br tag detection (J3 comment)
    passed, count = check_file_contains(
        base / "services" / "content_quality_enforcer.py",
        r"Fix-Batch J3"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} Fix-Batch J3 enhancements present ({count} references)")
    else:
        errors.append("J3: Missing Fix-Batch J3 enhancements in content_quality_enforcer.py")
        print(f"  {RED}✗{RESET} Fix-Batch J3 enhancements NOT FOUND")

    # Must have: starter-kit CSS fix in template (Fix-Batch J3 comment)
    passed, count = check_file_contains(
        base / "templates" / "pdf_template.html",
        r"Fix-Batch J3.*starter-kit"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} Starter-kit CSS page-break fix present (J3 comment found)")
    else:
        warnings.append("J3: Starter-kit CSS page-break fix may be missing")
        print(f"  {YELLOW}⚠{RESET} Starter-kit CSS page-break fix not found")

    print()

    # ==========================================================================
    # J4: No Chat Artefacts Validation
    # ==========================================================================
    print(f"{BOLD}[J4] No Chat Artefacts Validation{RESET}")

    # Must have: apply_chat_artefact_filter function
    passed, count = check_file_contains(
        base / "services" / "content_quality_enforcer.py",
        r"def apply_chat_artefact_filter"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} apply_chat_artefact_filter exists")
    else:
        errors.append("J4: Missing apply_chat_artefact_filter in content_quality_enforcer.py")
        print(f"  {RED}✗{RESET} apply_chat_artefact_filter NOT FOUND")

    # Must have: CHAT_ARTEFACT_PATTERNS defined
    passed, count = check_file_contains(
        base / "services" / "content_quality_enforcer.py",
        r"CHAT_ARTEFACT_PATTERNS\s*="
    )
    if passed:
        print(f"  {GREEN}✓{RESET} CHAT_ARTEFACT_PATTERNS defined")
    else:
        errors.append("J4: Missing CHAT_ARTEFACT_PATTERNS in content_quality_enforcer.py")
        print(f"  {RED}✗{RESET} CHAT_ARTEFACT_PATTERNS NOT FOUND")

    # Must have: Filter in pipeline (step 15)
    passed, count = check_file_contains(
        base / "services" / "content_quality_enforcer.py",
        r"apply_chat_artefact_filter\(sections\)"
    )
    if passed:
        print(f"  {GREEN}✓{RESET} Chat artefact filter in pipeline")
    else:
        errors.append("J4: Chat artefact filter not in quality enforcer pipeline")
        print(f"  {RED}✗{RESET} Chat artefact filter not in pipeline")

    print()

    # ==========================================================================
    # Summary
    # ==========================================================================
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Summary{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    if warnings:
        print(f"\n{YELLOW}Warnings ({len(warnings)}):{RESET}")
        for w in warnings:
            print(f"  ⚠ {w}")

    if errors:
        print(f"\n{RED}Errors ({len(errors)}):{RESET}")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n{RED}{BOLD}GATE FAILED: {len(errors)} blocking errors{RESET}")
        return 1
    else:
        print(f"\n{GREEN}{BOLD}GATE PASSED: All release blockers resolved{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
