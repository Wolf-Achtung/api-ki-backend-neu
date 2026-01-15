#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate Script: Validate Report Output Quality
===========================================

v14.35.22 - Report 468 Gold Standard Gate

This script validates the final HTML/PDF output against quality criteria:
1. No "Microsoft Kapazitäten" (product name mutation)
2. No open "(z.B." or "(z. B." patterns at sentence ends
3. No "KI-Skill-Fahrplan 2025" or "Kreativ-Tools 2025" (year audit)
4. KPI consistency checks (optional)

Exit Codes:
- 0: All checks passed
- 1: One or more checks failed
- 2: File not found or error

Usage:
    python scripts/gate_report_output.py artifacts/debug_final.html
    python scripts/gate_report_output.py --pdf path/to/report.pdf
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


class GateChecker:
    """Report output quality gate checker."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.failures: List[str] = []
        self.warnings: List[str] = []

    def log(self, message: str) -> None:
        """Log message if verbose."""
        if self.verbose:
            print(f"  {message}")

    def check_product_name_mutations(self, content: str) -> bool:
        """
        G1: Check for product name mutations like 'Microsoft Kapazitäten'.

        Returns True if clean, False if mutation found.
        """
        mutations = [
            r"Microsoft\s+Kapazitäten",
            r"MS\s+Kapazitäten",
            r"Google\s+Kapazitäten",
        ]

        for pattern in mutations:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                self.failures.append(f"Product name mutation: {matches[0]}")
                return False

        self.log("✓ No product name mutations found")
        return True

    def check_open_example_parens(self, content: str) -> bool:
        """
        G2: Check for open '(z.B.' or '(z. B.' patterns.

        Returns True if clean, False if open pattern found.
        """
        patterns = [
            # Open at end of line/tag
            r'\(z\.\s*[Bb]\.\s*(?=<|$|\n)',
            # Open at sentence end
            r'\(z\.\s*[Bb]\.\s*[^)]*?(?=\.|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            # Filter out complete examples like "(z.B. Templates)"
            real_matches = [m for m in matches if not re.search(r'\([^)]+\)', m)]
            if real_matches:
                self.failures.append(f"Open example paren: '{real_matches[0][:50]}...'")
                return False

        self.log("✓ No open example parens found")
        return True

    def check_year_audit(self, content: str) -> bool:
        """
        G3: Check for hardcoded 2025 in headings.

        Returns True if clean, False if hardcoded year found.
        """
        patterns = [
            r"KI-Skill-Fahrplan\s+2025",
            r"Kreativ-Tools\s+2025",
            r"AI\s+Skills\s+Roadmap\s+2025",
            r"Creative\s+Tools\s+2025",
            # Also check for Trends (but allow in data tables)
            r"<h[23][^>]*>[^<]*2025/26[^<]*</h[23]>",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                self.failures.append(f"Year audit fail: '{matches[0][:60]}...'")
                return False

        self.log("✓ No hardcoded 2025 in headings")
        return True

    def check_kpi_consistency(self, content: str) -> bool:
        """
        G4: Check for KPI inconsistencies (optional, warning only).

        Looks for conflicting hour values like "18 Std./Monat" and "20 Stunden".
        """
        # Extract all hour values mentioned
        hour_patterns = [
            r'(\d+)\s*(?:Std\.|Stunden?|h)\s*/\s*(?:Monat|Woche)',
            r'(\d+)\s*(?:hours?)\s*/\s*(?:month|week)',
        ]

        hour_values = set()
        for pattern in hour_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    hour_values.add(int(match))
                except ValueError:
                    pass

        # If multiple distinct values, warn
        if len(hour_values) > 2:
            self.warnings.append(
                f"KPI consistency warning: Multiple hour values found: {sorted(hour_values)}"
            )
            return False

        self.log("✓ KPI values appear consistent")
        return True

    def run_all_checks(self, content: str) -> bool:
        """
        Run all gate checks on content.

        Returns True if all critical checks pass, False otherwise.
        """
        results = [
            ("Product Name Gate", self.check_product_name_mutations(content)),
            ("Open Paren Gate", self.check_open_example_parens(content)),
            ("Year Audit Gate", self.check_year_audit(content)),
        ]

        # KPI check is warning only
        self.check_kpi_consistency(content)

        all_passed = all(result for _, result in results)
        return all_passed


def read_html_file(path: Path) -> str:
    """Read HTML file content."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return path.read_text(encoding="utf-8", errors="replace")


def read_pdf_file(path: Path) -> str:
    """Extract text from PDF file (requires pdfminer or similar)."""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(path))
    except ImportError:
        raise ImportError(
            "PDF reading requires pdfminer.six. Install with: pip install pdfminer.six"
        )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Gate script for report output quality validation"
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to HTML or PDF file to validate"
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Treat input as PDF file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("Report Output Gate - v14.35.22")
    print(f"{'='*60}")
    print(f"File: {args.file}")
    print()

    try:
        if args.pdf:
            content = read_pdf_file(args.file)
        else:
            content = read_html_file(args.file)
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}")
        return 2
    except ImportError as e:
        print(f"❌ ERROR: {e}")
        return 2

    checker = GateChecker(verbose=args.verbose)
    passed = checker.run_all_checks(content)

    print()
    if checker.failures:
        print("❌ FAILURES:")
        for failure in checker.failures:
            print(f"   - {failure}")

    if checker.warnings:
        print("⚠️  WARNINGS:")
        for warning in checker.warnings:
            print(f"   - {warning}")

    print()
    if passed:
        print("✅ ALL GATES PASSED")
        return 0
    else:
        print("❌ GATE FAILED - Report does not meet Gold Standard")
        return 1


if __name__ == "__main__":
    sys.exit(main())
