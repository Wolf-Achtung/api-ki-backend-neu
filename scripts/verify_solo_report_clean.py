#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-554: Solo Report Token Verification Script

Scans final HTML and/or PDF text for forbidden tokens.
Exit code: 0 = clean, 1 = violations found.

Usage:
    python scripts/verify_solo_report_clean.py path/to/report.html
    python scripts/verify_solo_report_clean.py path/to/report.pdf
    python scripts/verify_solo_report_clean.py --text "raw text to check"

Can be integrated into CI pipelines.

Version: 1.0.0 (FIX-554)
"""
from __future__ import annotations

import argparse
import re
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================================================
# CONFIGURATION
# =============================================================================

# Enterprise terms (case-insensitive, with hyphen variants)
FORBIDDEN_ENTERPRISE_TOKENS = [
    "Governance",
    "Audit-Trail",
    "Audit Trail",
    "Audit\u2011Trail",  # non-breaking hyphen
    "Audit\u2010Trail",  # hyphen
    "Stakeholder",
    "Stack",
    "Layer",
    "Architektur",
    "Rollout",
    "Roll-out",
    "Prozesslandschaft",
    "Baukasten",
]

# Duz-forms (case-insensitive, word-boundary)
FORBIDDEN_DUZ_PATTERN = re.compile(
    r"\b(du|dir|dein|deine|deinem|deinen|deiner|deines|dich|euch|euer|eure|eurem|euren|eurer|eures)\b",
    re.IGNORECASE,
)

# Quick-Wins empty check pattern
QUICKWINS_EMPTY_PATTERN = re.compile(
    r"PROBLEM:\s*\n\s*WIRKUNG:|WIRKUNG:\s*\n\s*UMSETZUNG:|UMSETZUNG:\s*\n",
    re.MULTILINE,
)


# =============================================================================
# FUNCTIONS
# =============================================================================

def extract_text_from_html(html: str) -> str:
    """Strip HTML tags to get visible text."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF (fitz) if available."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        print("WARNING: PyMuPDF (fitz) not installed. Cannot scan PDF text.", file=sys.stderr)
        print("Install with: pip install PyMuPDF", file=sys.stderr)
        return ""


def scan_forbidden_tokens(text: str) -> dict:
    """
    Scan text for all forbidden tokens.

    Returns dict with counts per category and details.
    """
    results = {
        "enterprise": [],
        "duz": [],
        "quickwins_empty": [],
        "total": 0,
        "passed": True,
    }

    # 1. Enterprise terms
    for token in FORBIDDEN_ENTERPRISE_TOKENS:
        pattern = re.compile(re.escape(token), re.IGNORECASE)
        for match in pattern.finditer(text):
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 40)
            context = text[start:end].replace("\n", " ")
            results["enterprise"].append({
                "token": token,
                "matched": match.group(0),
                "context": f"...{context}...",
                "position": match.start(),
            })

    # 2. Duz-forms
    for match in FORBIDDEN_DUZ_PATTERN.finditer(text):
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        context = text[start:end].replace("\n", " ")
        results["duz"].append({
            "token": match.group(0),
            "context": f"...{context}...",
            "position": match.start(),
        })

    # 3. Quick-Wins empty check
    for match in QUICKWINS_EMPTY_PATTERN.finditer(text):
        results["quickwins_empty"].append({
            "context": match.group(0)[:80],
            "position": match.start(),
        })

    results["total"] = (
        len(results["enterprise"]) +
        len(results["duz"]) +
        len(results["quickwins_empty"])
    )
    results["passed"] = results["total"] == 0

    return results


def print_report(results: dict, source: str) -> None:
    """Print scan results as formatted report."""
    print("=" * 70)
    print(f"FIX-554 Solo Report Token Scan: {source}")
    print("=" * 70)

    if results["passed"]:
        print("\n  PASSED - No forbidden tokens found.\n")
        return

    print(f"\n  FAILED - {results['total']} violation(s) found.\n")

    if results["enterprise"]:
        print(f"  Enterprise Terms ({len(results['enterprise'])}):")
        for v in results["enterprise"][:20]:
            print(f"    [{v['token']}] {v['context']}")

    if results["duz"]:
        print(f"\n  Duz-Forms ({len(results['duz'])}):")
        for v in results["duz"][:20]:
            print(f"    [{v['token']}] {v['context']}")

    if results["quickwins_empty"]:
        print(f"\n  Quick-Wins Empty Fields ({len(results['quickwins_empty'])}):")
        for v in results["quickwins_empty"][:10]:
            print(f"    {v['context']}")

    # Summary table
    print(f"\n  {'Category':<25} {'Count':>8}")
    print(f"  {'-'*25} {'-'*8}")
    print(f"  {'Enterprise Terms':<25} {len(results['enterprise']):>8}")
    print(f"  {'Duz-Forms':<25} {len(results['duz']):>8}")
    print(f"  {'Quick-Wins Empty':<25} {len(results['quickwins_empty']):>8}")
    print(f"  {'TOTAL':<25} {results['total']:>8}")
    print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="FIX-554: Scan solo report for forbidden tokens"
    )
    parser.add_argument(
        "file", nargs="?",
        help="Path to HTML or PDF file to scan"
    )
    parser.add_argument(
        "--text",
        help="Raw text to scan (alternative to file)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON"
    )
    args = parser.parse_args()

    if not args.file and not args.text:
        parser.error("Provide either a file path or --text")

    # Extract text
    if args.text:
        text = args.text
        source = "<inline text>"
    elif args.file.endswith(".pdf"):
        text = extract_text_from_pdf(args.file)
        source = args.file
    elif args.file.endswith((".html", ".htm")):
        with open(args.file, "r", encoding="utf-8") as f:
            html = f.read()
        text = extract_text_from_html(html)
        source = args.file
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        source = args.file

    # Scan
    results = scan_forbidden_tokens(text)

    # Output
    if args.json:
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_report(results, source)

    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
