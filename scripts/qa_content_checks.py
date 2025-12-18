#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA Content Checks - Lightweight scan for EN/DE locale compliance.

Usage:
    python scripts/qa_content_checks.py <html_file> [--lang en|de]
    python scripts/qa_content_checks.py reports/kmu_france.html --lang en

Checks performed:
1. German tokens in EN reports (locale contamination)
2. Prompt leak phrases (LLM assistant patterns)
3. Badge population verification

Exit codes:
    0 = All checks pass
    1 = Warnings only (soft fail)
    2 = Hard failures detected
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------------
# German token patterns (common DE words that shouldn't appear in EN reports)
# ---------------------------------------------------------------------------
DE_TOKENS: List[Tuple[str, str]] = [
    (r"\bUnternehmen\b", "Company"),
    (r"\bBranche\b", "Industry"),
    (r"\bStandort\b", "Location"),
    (r"\bMitarbeiter\b", "Employees"),
    (r"\bUmsatz\b", "Revenue"),
    (r"\bZusammenfassung\b", "Summary"),
    (r"\bEmpfehlung(?:en)?\b", "Recommendation(s)"),
    (r"\bÜberblick\b", "Overview"),
    (r"\bNächste Schritte\b", "Next Steps"),
    (r"\bSchnellgewinne\b", "Quick Wins"),
    (r"\bPotenzial\b", "Potential"),
    (r"\bKosten\b", "Costs"),
    (r"\bNutzen\b", "Benefit/Value"),
    (r"\bRisiko\b", "Risk"),
    (r"\bStrategie\b", "Strategy"),
    (r"\bProzess(?:e)?\b", "Process(es)"),
    (r"\bDaten\b", "Data"),
    (r"\bSicherheit\b", "Security"),
    (r"\bDatenschutz\b", "Data Protection"),
    (r"\bFörder(?:ung|programme)\b", "Funding"),
    (r"\bWettbewerb\b", "Competition"),
    (r"\bZiel(?:e)?\b", "Goal(s)"),
    (r"\bMaßnahme(?:n)?\b", "Measure(s)"),
    (r"\bBewertung\b", "Assessment"),
    (r"\bAnalyse\b", "Analysis"),
    (r"\bErgebnis(?:se)?\b", "Result(s)"),
    (r"\bzeit(?:punkt|raum|horizont)\b", "time(point/frame/horizon)", re.I),
    (r"\bMonat(?:e)?\b", "Month(s)"),
    (r"\bJahr(?:e)?\b", "Year(s)"),
    (r"\bWoche(?:n)?\b", "Week(s)"),
]

# ---------------------------------------------------------------------------
# Prompt leak patterns (LLM assistant phrases that shouldn't appear in output)
# ---------------------------------------------------------------------------
PROMPT_LEAK_PATTERNS: List[str] = [
    r"(?i)ich bin ein\s+(KI|AI|Assistent|Sprach)",
    r"(?i)als KI-?(Assistent|Sprachmodell|System)",
    r"(?i)hier ist (dein|Ihr|ein)\s+\w+:?$",
    r"(?i)gerne!?\s*(hier|ich)",
    r"(?i)natürlich!?\s*(hier|ich)",
    r"(?i)ich kann dir\s+(helfen|zeigen|erklären)",
    r"(?i)du hast (noch keine|keine) frage",
    r"(?i)bitte beschreibe,?\s+wobei",
    r"(?i)how can I (help|assist)",
    r"(?i)I('m| am) (a|an) (AI|language model|assistant)",
    r"(?i)as an? (AI|language model)",
    r"(?i)here('s| is) (your|the) \w+:?$",
    r"(?i)sure!?\s*(here|I)",
    r"(?i)certainly!?\s*(here|I)",
]

# ---------------------------------------------------------------------------
# Badge CSS classes expected in rendered HTML
# These are the actual CSS classes in pdf_template_en.html, not variable names
# ---------------------------------------------------------------------------
EXPECTED_BADGE_CLASSES = ["badge-eu", "badge-dsgvo", "badge-risk", "badge-time"]


def scan_de_tokens(html: str) -> List[Tuple[str, str, int]]:
    """Scan for German tokens in HTML content.

    Returns list of (pattern, replacement, count) tuples.
    """
    findings = []
    for item in DE_TOKENS:
        if len(item) == 3:
            pattern, replacement, flags = item
        else:
            pattern, replacement = item
            flags = 0
        matches = re.findall(pattern, html, flags)
        if matches:
            findings.append((pattern, replacement, len(matches)))
    return findings


def scan_prompt_leaks(html: str) -> List[Tuple[str, int]]:
    """Scan for prompt leak patterns in HTML.

    Returns list of (pattern, count) tuples.
    """
    findings = []
    for pattern in PROMPT_LEAK_PATTERNS:
        matches = re.findall(pattern, html)
        if matches:
            findings.append((pattern[:50] + "...", len(matches)))
    return findings


def check_badges(html: str) -> List[str]:
    """Check for expected badge CSS classes in rendered HTML.

    Returns list of missing badge class names.
    """
    missing = []
    for badge_class in EXPECTED_BADGE_CLASSES:
        # Check for badge CSS class in HTML (e.g., class="badge badge-eu")
        if badge_class not in html:
            missing.append(badge_class)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="QA Content Checks for EN/DE locale compliance"
    )
    parser.add_argument("html_file", help="Path to HTML file to check")
    parser.add_argument(
        "--lang", default="en", choices=["en", "de"],
        help="Expected language (default: en)"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as errors"
    )
    args = parser.parse_args()

    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"ERROR: File not found: {html_path}")
        return 2

    html = html_path.read_text(encoding="utf-8")
    exit_code = 0

    print(f"=== QA Content Checks: {html_path.name} (lang={args.lang}) ===\n")

    # 1. German tokens check (EN reports only)
    if args.lang == "en":
        de_findings = scan_de_tokens(html)
        if de_findings:
            total = sum(f[2] for f in de_findings)
            print(f"[WARN] German tokens found: {total} instances")
            for pattern, replacement, count in de_findings[:10]:
                print(f"  - {pattern} ({count}x) → should be: {replacement}")
            if len(de_findings) > 10:
                print(f"  ... and {len(de_findings) - 10} more patterns")
            if args.strict:
                exit_code = max(exit_code, 2)
            else:
                exit_code = max(exit_code, 1)
        else:
            print("[PASS] No German tokens detected")

    # 2. Prompt leak check (both languages)
    leak_findings = scan_prompt_leaks(html)
    if leak_findings:
        total = sum(f[1] for f in leak_findings)
        print(f"\n[FAIL] Prompt leaks detected: {total} instances")
        for pattern, count in leak_findings:
            print(f"  - {pattern} ({count}x)")
        exit_code = max(exit_code, 2)
    else:
        print("[PASS] No prompt leaks detected")

    # 3. Badge check (informational)
    missing_badges = check_badges(html)
    if missing_badges:
        print(f"\n[INFO] Missing badges: {', '.join(missing_badges)}")
        # Badges are informational only, don't affect exit code
    else:
        print("[PASS] All expected badges present")

    print(f"\n=== Result: {'PASS' if exit_code == 0 else 'WARN' if exit_code == 1 else 'FAIL'} ===")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
