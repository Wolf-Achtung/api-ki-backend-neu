#!/usr/bin/env python3
"""
Simple Phase 2 Test - No external dependencies
Tests the prompt files directly without importing gpt_analyze
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_gpt_analyze_has_new_variables():
    """Check that gpt_analyze.py has the new freetext variables"""
    gpt_analyze_path = REPO_ROOT / "gpt_analyze.py"
    content = gpt_analyze_path.read_text(encoding="utf-8")

    # Check for new variables in _build_prompt_vars
    required_vars = [
        '"ZEITERSPARNIS_PRIORITAET"',
        '"zeitersparnis_prioritaet"',
        '"VISION_3_JAHRE"',
        '"GESCHAEFTSMODELL_EVOLUTION"',
        '"KI_GUARDRAILS"',
        '"STRATEGISCHE_ZIELE"',
        '"hauptleistung"',
    ]

    missing = []
    for var in required_vars:
        if var not in content:
            missing.append(var)

    if missing:
        print(f"❌ CHECK 1 FAILED: Missing variables in gpt_analyze.py: {missing}")
        return False

    print("✅ CHECK 1 PASSED: All new freetext variables in gpt_analyze.py")
    return True


def test_executive_summary_uses_hauptleistung():
    """Check that executive_summary.md references hauptleistung"""
    prompt_path = REPO_ROOT / "prompts" / "de" / "executive_summary.md"

    if not prompt_path.exists():
        print(f"❌ CHECK 2 SKIPPED: {prompt_path} not found")
        return None

    content = prompt_path.read_text(encoding="utf-8")

    # Check for hauptleistung references
    if "{{hauptleistung}}" not in content:
        print("❌ CHECK 2 FAILED: {{hauptleistung}} not in executive_summary.md")
        return False

    if "INDIVIDUALISIERUNGS-KONTEXT" not in content:
        print("❌ CHECK 2 FAILED: INDIVIDUALISIERUNGS-KONTEXT block not in executive_summary.md")
        return False

    if "ZEITERSPARNIS_PRIORITAET" not in content:
        print("❌ CHECK 2 FAILED: ZEITERSPARNIS_PRIORITAET not in executive_summary.md")
        return False

    print("✅ CHECK 2 PASSED: executive_summary.md has individualization context")
    return True


def test_quick_wins_is_dynamic():
    """Check that quick_wins.md is dynamic, not static"""
    prompt_path = REPO_ROOT / "prompts" / "de" / "quick_wins.md"

    if not prompt_path.exists():
        print(f"❌ CHECK 3 SKIPPED: {prompt_path} not found")
        return None

    content = prompt_path.read_text(encoding="utf-8")

    # Check for dynamic generation rules
    dynamic_markers = [
        "GENERIERUNGSREGELN",
        "{{ZEITERSPARNIS_PRIORITAET}}",
        "{{hauptleistung}}",
        "score_security",
        "INDIVIDUALISIERUNGS-KONTEXT",
    ]

    found_markers = [m for m in dynamic_markers if m in content]

    if len(found_markers) < 4:
        print(f"❌ CHECK 3 FAILED: Only {len(found_markers)}/5 dynamic markers found")
        return False

    print(f"✅ CHECK 3 PASSED: quick_wins.md has {len(found_markers)}/5 dynamic markers")
    return True


def test_no_static_email_quick_win():
    """Check that hardcoded E-Mail Quick Win is removed from output"""
    prompt_path = REPO_ROOT / "prompts" / "de" / "quick_wins.md"

    if not prompt_path.exists():
        print(f"❌ CHECK 4 SKIPPED: {prompt_path} not found")
        return None

    content = prompt_path.read_text(encoding="utf-8")

    # The old static pattern was:
    # ### QUICK WIN #1: E-Mail-Entwürfe automatisieren (5-8 Std./Monat)
    # This should NOT appear as a concrete output (only as example in comments)

    # Find all lines that are NOT in comments
    lines = content.split("\n")
    in_comment = False
    static_found = False

    for i, line in enumerate(lines):
        if "<!--" in line:
            in_comment = True
        if "-->" in line:
            in_comment = False
            continue

        # Check for the old static Quick Win pattern outside comments
        if not in_comment:
            if re.search(r"### QUICK WIN #1.*E-Mail-Entwürfe automatisieren", line):
                print(f"❌ CHECK 4 FAILED: Static E-Mail Quick Win found at line {i+1}")
                print(f"   Line: {line[:80]}...")
                static_found = True

    if static_found:
        return False

    print("✅ CHECK 4 PASSED: No static E-Mail Quick Win in output section")
    return True


def test_quick_wins_uses_zeitersparnis_for_first_qw():
    """Check that Quick Win #1 must address ZEITERSPARNIS_PRIORITAET"""
    prompt_path = REPO_ROOT / "prompts" / "de" / "quick_wins.md"

    if not prompt_path.exists():
        print(f"❌ CHECK 5 SKIPPED: {prompt_path} not found")
        return None

    content = prompt_path.read_text(encoding="utf-8")

    # Look for the rule that Quick Win #1 must use ZEITERSPARNIS_PRIORITAET
    rule_patterns = [
        r"QUICK WIN #1.*MUSS.*ZEITERSPARNIS",
        r"REGEL 1.*ZEITERSPARNIS",
        r"Quick Win #1.*adressiert.*ZEITERSPARNIS",
    ]

    for pattern in rule_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            print("✅ CHECK 5 PASSED: Quick Win #1 must address ZEITERSPARNIS_PRIORITAET")
            return True

    print("❌ CHECK 5 FAILED: No rule found that Quick Win #1 must use ZEITERSPARNIS_PRIORITAET")
    return False


def test_score_based_prioritization():
    """Check that scores are used for Quick Win prioritization"""
    prompt_path = REPO_ROOT / "prompts" / "de" / "quick_wins.md"

    if not prompt_path.exists():
        print(f"❌ CHECK 6 SKIPPED: {prompt_path} not found")
        return None

    content = prompt_path.read_text(encoding="utf-8")

    # Check for score-based rules
    if "score_security" not in content:
        print("❌ CHECK 6 FAILED: score_security not in quick_wins.md")
        return False

    if "score_governance" not in content:
        print("❌ CHECK 6 FAILED: score_governance not in quick_wins.md")
        return False

    # Check for prioritization logic
    if "< 50" not in content and "<50" not in content:
        print("❌ CHECK 6 FAILED: No score threshold logic (< 50) found")
        return False

    print("✅ CHECK 6 PASSED: Score-based prioritization in quick_wins.md")
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 2 INDIVIDUALISIERUNG - SIMPLE TEST SUITE")
    print("=" * 70)
    print()

    results = []

    results.append(("Check 1: New variables in gpt_analyze.py", test_gpt_analyze_has_new_variables()))
    results.append(("Check 2: Executive Summary individualization", test_executive_summary_uses_hauptleistung()))
    results.append(("Check 3: Quick Wins dynamic generation", test_quick_wins_is_dynamic()))
    results.append(("Check 4: Static E-Mail Quick Win removed", test_no_static_email_quick_win()))
    results.append(("Check 5: Quick Win #1 uses ZEITERSPARNIS", test_quick_wins_uses_zeitersparnis_for_first_qw()))
    results.append(("Check 6: Score-based prioritization", test_score_based_prioritization()))

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results:
        if result is True:
            passed += 1
            status = "✅ PASSED"
        elif result is False:
            failed += 1
            status = "❌ FAILED"
        else:
            skipped += 1
            status = "⏭️ SKIPPED"

        print(f"  {status}: {name}")

    print()
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print()
        print("🎉 ALL TESTS PASSED!")
        exit(0)
    else:
        print()
        print("❌ SOME TESTS FAILED")
        exit(1)
