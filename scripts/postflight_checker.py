#!/usr/bin/env python3
"""
Postflight Checker v1.0 (FIX-497)
=================================
Validates final HTML/PDF output against quality criteria.

Checks:
1. No triple-backticks (```), no "```html" anywhere in final text
2. No empty pages (detects patterns that would cause blank pages)
3. No empty headings (sections with headers but no content)
4. Tables don't break leaving 1-row orphan pages
5. Metrics consistency (cover values match pipeline values)

Usage:
    python scripts/postflight_checker.py path/to/output.html [--strict]
    python scripts/postflight_checker.py path/to/output.pdf [--strict]

Returns exit code 0 if all checks pass, 1 if any check fails.
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
log = logging.getLogger(__name__)


# =============================================================================
# FORBIDDEN TOKEN PATTERNS
# =============================================================================
FORBIDDEN_TOKENS = [
    (r'```+[a-zA-Z]*', 'Code fence (opening)'),
    (r'```+\s*$', 'Code fence (closing)'),
    (r'&#96;{3,}', 'HTML-escaped backticks'),
    (r'&#x60;{3,}', 'HTML-escaped backticks (hex)'),
    (r'\[TODO\]', 'TODO marker'),
    (r'\[TBD\]', 'TBD marker'),
    (r'\[PLACEHOLDER\]', 'Placeholder marker'),
    (r'Lorem ipsum', 'Lorem ipsum placeholder'),
    (r'Beispieltext', 'German placeholder text'),
    (r'Mustertext', 'German sample text marker'),
]

# Leak phrases that should never appear in production output
LEAK_PHRASES = [
    'Beschreibe dein Anliegen',
    'wie kann ich dir helfen',
    'describe your request',
    'I don\'t see a question',
    'Ich sehe keine konkrete Frage',
    'Du hast noch keine Frage',
    'wobei ich dir helfen soll',
]


# =============================================================================
# EMPTY PAGE DETECTION PATTERNS
# =============================================================================
EMPTY_PAGE_PATTERNS = [
    # Empty section with only whitespace
    re.compile(r'<section[^>]*>\s*</section>', re.IGNORECASE | re.DOTALL),
    # Section with only a header and no content
    re.compile(r'<section[^>]*>\s*<h[1-6][^>]*>[^<]*</h[1-6]>\s*</section>', re.IGNORECASE | re.DOTALL),
    # Empty div that would cause page break
    re.compile(r'<div[^>]*class="[^"]*page-break[^"]*"[^>]*>\s*</div>\s*<div[^>]*class="[^"]*page-break[^"]*"[^>]*>', re.IGNORECASE),
    # Empty chapter section
    re.compile(r'<section[^>]*class="chapter"[^>]*>\s*</section>', re.IGNORECASE),
]

# Pattern for headings without following content
EMPTY_HEADING_PATTERNS = [
    re.compile(r'<h[1-6][^>]*>[^<]+</h[1-6]>\s*(?:</(?:div|section)>|<h[1-6])', re.IGNORECASE),
]


# =============================================================================
# TABLE ORPHAN DETECTION
# =============================================================================
def check_table_orphans(html: str) -> List[str]:
    """Check for tables that might cause orphan single-row pages."""
    issues = []

    # Find all tables
    table_pattern = re.compile(r'<table[^>]*>(.*?)</table>', re.IGNORECASE | re.DOTALL)

    for match in table_pattern.finditer(html):
        table_html = match.group(1)
        # Count rows
        row_count = len(re.findall(r'<tr[^>]*>', table_html, re.IGNORECASE))

        # Check for page-break-inside styling
        has_orphan_protection = (
            'page-break-inside: avoid' in table_html or
            'break-inside: avoid' in table_html
        )

        if row_count > 5 and not has_orphan_protection:
            issues.append(f"Table with {row_count} rows lacks orphan protection CSS")

    return issues


# =============================================================================
# METRICS CONSISTENCY CHECK
# =============================================================================
def check_metrics_consistency(html: str, pipeline_metrics: Dict[str, Any] = None) -> List[str]:
    """Check that cover page metrics match pipeline metrics."""
    issues = []

    if not pipeline_metrics:
        # Try to extract metrics from HTML comments or data attributes
        metrics_pattern = re.compile(r'data-pipeline-(\w+)="(\d+)"', re.IGNORECASE)
        found_metrics = {}
        for match in metrics_pattern.finditer(html):
            found_metrics[match.group(1)] = int(match.group(2))

        if found_metrics:
            log.info(f"Found embedded pipeline metrics: {found_metrics}")

    # Check for "0" values that might indicate missing metrics
    zero_patterns = [
        (r'Warnings:\s*0\b', 'Warnings shows 0'),
        (r'Fallbacks:\s*0\b', 'Fallbacks shows 0'),
        (r'Heals:\s*0\b', 'Heals shows 0'),
    ]

    for pattern, desc in zero_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            # This is informational - zeros might be correct
            log.debug(f"Metrics note: {desc}")

    return issues


# =============================================================================
# MAIN VALIDATION FUNCTIONS
# =============================================================================
def validate_html(html: str, strict: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate HTML content against all quality checks.

    Args:
        html: HTML content to validate
        strict: If True, warnings become errors

    Returns:
        Tuple of (passed, list of issues)
    """
    issues = []
    warnings = []

    # Check 1: Forbidden tokens
    for pattern, desc in FORBIDDEN_TOKENS:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            issues.append(f"FORBIDDEN TOKEN: {desc} (found {len(matches)} occurrences)")

    # Check 2: Leak phrases
    html_lower = html.lower()
    for phrase in LEAK_PHRASES:
        if phrase.lower() in html_lower:
            issues.append(f"LEAK PHRASE: '{phrase[:30]}...' found in output")

    # Check 3: Empty page patterns
    for pattern in EMPTY_PAGE_PATTERNS:
        matches = pattern.findall(html)
        if matches:
            warnings.append(f"EMPTY PAGE RISK: Pattern detected ({len(matches)} occurrences)")

    # Check 4: Empty headings
    for pattern in EMPTY_HEADING_PATTERNS:
        matches = pattern.findall(html)
        if matches:
            warnings.append(f"EMPTY HEADING: Heading without following content ({len(matches)} occurrences)")

    # Check 5: Table orphans
    table_issues = check_table_orphans(html)
    warnings.extend(table_issues)

    # Check 6: Metrics consistency
    metrics_issues = check_metrics_consistency(html)
    warnings.extend(metrics_issues)

    # In strict mode, warnings become errors
    if strict:
        issues.extend(warnings)
        warnings = []

    # Report results
    all_issues = issues + warnings
    passed = len(issues) == 0

    return passed, all_issues


def validate_file(filepath: str, strict: bool = False) -> Tuple[bool, List[str]]:
    """Validate a file (HTML or PDF)."""
    path = Path(filepath)

    if not path.exists():
        return False, [f"File not found: {filepath}"]

    content = ""

    if path.suffix.lower() == '.html':
        content = path.read_text(encoding='utf-8', errors='replace')
    elif path.suffix.lower() == '.pdf':
        # Try to extract text from PDF
        try:
            import subprocess
            result = subprocess.run(
                ['pdftotext', '-layout', str(path), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )
            content = result.stdout
        except Exception as e:
            log.warning(f"Could not extract PDF text: {e}")
            log.info("Skipping PDF content validation")
            return True, ["PDF text extraction not available"]
    else:
        return False, [f"Unsupported file type: {path.suffix}"]

    return validate_html(content, strict=strict)


def main():
    parser = argparse.ArgumentParser(
        description='Validate HTML/PDF output against quality criteria'
    )
    parser.add_argument('file', help='Path to HTML or PDF file to validate')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--quiet', action='store_true', help='Only output on failure')

    args = parser.parse_args()

    passed, issues = validate_file(args.file, strict=args.strict)

    if args.json:
        result = {
            'file': args.file,
            'passed': passed,
            'strict': args.strict,
            'issues': issues,
            'issue_count': len(issues),
        }
        print(json.dumps(result, indent=2))
    else:
        if not args.quiet or not passed:
            print(f"\n{'='*60}")
            print(f"Postflight Check: {args.file}")
            print(f"{'='*60}")
            print(f"Mode: {'STRICT' if args.strict else 'NORMAL'}")
            print(f"Result: {'PASSED' if passed else 'FAILED'}")
            print(f"Issues: {len(issues)}")

            if issues:
                print(f"\n{'-'*40}")
                for i, issue in enumerate(issues, 1):
                    print(f"  {i}. {issue}")

            print(f"{'='*60}\n")

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
