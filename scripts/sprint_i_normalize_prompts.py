#!/usr/bin/env python3
"""
sprint_i_normalize_prompts.py — Sprint I: Prompt Normalization Pass

Normalizes all prompt files to PLATIN++ v5.2 standard:
- Updates header comments to v5.2 format
- Changes OUTPUT to "HTML ONLY"
- Standardizes SIZE-AWARE parameter
- Removes forbidden terms

Usage:
    python scripts/sprint_i_normalize_prompts.py [--dry-run] [--verbose]
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, TypedDict


class NormalizeResult(TypedDict):
    """Result of normalizing a single file."""
    file: str
    changes: List[str]
    warnings: List[str]
    success: bool

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"

# Target header format
HEADER_V52 = """<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: {section} -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->"""

# Mapping of filenames to section IDs
SECTION_MAP = {
    "executive_summary.md": "executive_summary",
    "quick_wins.md": "quick_wins",
    "roadmap_90d.md": "roadmap_90d",
    "roadmap_12m.md": "roadmap_12m",
    "gamechanger.md": "gamechanger",
    "tools_empfehlungen.md": "tools_empfehlungen",
    "tools_recommendations.md": "tools_recommendations",
    "recommendations.md": "recommendations",
    "business_case.md": "business_case",
    "risks.md": "risks",
    "data_readiness.md": "data_readiness",
    "foerderprogramme.md": "foerderprogramme",
    "foerderpotenzial.md": "foerderpotenzial",
    "funding.md": "funding",
    "funding_potential.md": "funding_potential",
    "funding_eu_core.md": "funding_eu_core",
    "ai_act_summary.md": "ai_act_summary",
    "transparency_box.md": "transparency_box",
    "ki_skillplan.md": "ki_skillplan",
    "costs_overview.md": "costs_overview",
    "monetarisierung.md": "monetarisierung",
    "monetization.md": "monetization",
    "strategie_governance.md": "strategie_governance",
    "strategy_governance.md": "strategy_governance",
    "org_change.md": "org_change",
    "technologie_prozesse.md": "technologie_prozesse",
    "technology_processes.md": "technology_processes",
    "wettbewerb_benchmark.md": "wettbewerb_benchmark",
    "competition_benchmark.md": "competition_benchmark",
    "unternehmensprofil_markt.md": "unternehmensprofil_markt",
    "ki_aktivitaeten_ziele.md": "ki_aktivitaeten_ziele",
    "ai_activities_goals.md": "ai_activities_goals",
    "next_actions.md": "next_actions",
    "roi_tracking.md": "roi_tracking",
    "kickoff_vorlage.md": "kickoff_vorlage",
    "kickoff_template.md": "kickoff_template",
    "ai_policy_mini.md": "ai_policy_mini",
    "templates_start.md": "templates_start",
    "prompt_framework.md": "prompt_framework",
}

# Forbidden terms to remove/flag
FORBIDDEN_TERMS = [
    "Freitextfeld",
    "Template Marker",
    "VERBOTEN",
]

# Old version patterns to update
OLD_VERSION_PATTERNS = [
    (r"<!-- VERSION: v\d+\.\d+ [^>]+ -->", ""),  # Remove old version lines
    (r"<!-- OUTPUT: HTML -->", "<!-- OUTPUT: HTML ONLY -->"),
    (r"<!-- OUTPUT: Markdown -->", "<!-- OUTPUT: HTML ONLY -->"),
    (r"<!-- SIZE-AWARE: solo/team/sme -->", "<!-- SIZE-AWARE: solo/team/kmu -->"),
]


def get_section_id(filename: str) -> str:
    """Get section ID from filename."""
    return SECTION_MAP.get(filename, filename.replace(".md", ""))


def normalize_header(content: str, filename: str) -> Tuple[str, List[str]]:
    """
    Normalize prompt header to v5.2 standard.

    Returns:
        Tuple of (normalized_content, list_of_changes)
    """
    changes = []
    section_id = get_section_id(filename)

    # Check if file starts with "Developer:"
    has_developer_prefix = content.startswith("Developer:")

    # Pattern to match old-style headers
    old_header_patterns = [
        # Standard PLATIN++ header
        r'^(Developer:\n)?<!-- PLATIN\+\+ PROMPT -->\n<!-- SECTION: \w+ -->\n<!-- VERSION: [^>]+ -->\n<!-- OUTPUT: [^>]+ -->\n<!-- SIZE-AWARE: [^>]+ -->',
        # Inline comment style (recommendations.md)
        r'^(Developer:\n)?<!-- [^-]+ – v[\d.]+ [^\n]+\n(?:[^\n]*\n)*?-->',
    ]

    # Check which pattern matches
    matched = False
    for pattern in old_header_patterns:
        match = re.match(pattern, content, re.MULTILINE)
        if match:
            matched = True
            old_header = match.group(0)

            # Create new header
            new_header = "Developer:\n" + HEADER_V52.format(section=section_id)

            if old_header != new_header:
                content = content.replace(old_header, new_header, 1)
                changes.append(f"Updated header to v5.2 format")
            break

    if not matched:
        # No recognizable header found, check if we need to add one
        if "<!-- PLATIN++" not in content[:500]:
            changes.append(f"WARNING: No recognizable header found in {filename}")

    # Apply additional pattern fixes
    for old_pattern, new_pattern in OLD_VERSION_PATTERNS:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_pattern, content)
            if new_pattern:
                changes.append(f"Fixed: {old_pattern[:30]}...")
            else:
                changes.append(f"Removed: {old_pattern[:30]}...")

    return content, changes


def check_forbidden_terms(content: str, filename: str) -> List[str]:
    """Check for forbidden terms in content."""
    found = []
    for term in FORBIDDEN_TERMS:
        if term.lower() in content.lower():
            found.append(f"Found forbidden term '{term}' in {filename}")
    return found


def normalize_file(filepath: Path, dry_run: bool = False, verbose: bool = False) -> NormalizeResult:
    """Normalize a single prompt file."""
    filename = filepath.name

    changes: List[str] = []
    warnings: List[str] = []

    result: NormalizeResult = {
        "file": str(filepath.relative_to(REPO_ROOT)),
        "changes": changes,
        "warnings": warnings,
        "success": True,
    }

    try:
        content = filepath.read_text(encoding="utf-8")
        original_content = content

        # Normalize header
        content, header_changes = normalize_header(content, filename)
        changes.extend(header_changes)

        # Check for forbidden terms
        forbidden = check_forbidden_terms(content, filename)
        warnings.extend(forbidden)

        # Write if changed and not dry run
        if content != original_content:
            if not dry_run:
                filepath.write_text(content, encoding="utf-8")
                changes.append("File updated")
            else:
                changes.append("Would update file (dry-run)")

    except Exception as e:
        result["success"] = False
        warnings.append(f"Error processing file: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Sprint I: Prompt Normalization")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", "-f", help="Process single file only")
    args = parser.parse_args()

    print("=" * 60)
    print("Sprint I - Prompt Normalization Pass")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    # Find all prompt files
    if args.file:
        prompt_files = [Path(args.file)]
    else:
        prompt_files = list(PROMPTS_DIR.glob("**/*.md"))

    print(f"Found {len(prompt_files)} prompt files")
    print()

    results = []
    files_changed = 0
    files_with_warnings = 0

    for filepath in sorted(prompt_files):
        result = normalize_file(filepath, dry_run=args.dry_run, verbose=args.verbose)
        results.append(result)

        if result["changes"]:
            files_changed += 1
        if result["warnings"]:
            files_with_warnings += 1

        if args.verbose or result["changes"] or result["warnings"]:
            print(f"\n📄 {result['file']}")
            for change in result["changes"]:
                print(f"   ✏️  {change}")
            for warning in result["warnings"]:
                print(f"   ⚠️  {warning}")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {len(results)}")
    print(f"Files changed:   {files_changed}")
    print(f"Files with warnings: {files_with_warnings}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - No files were actually modified")
    else:
        print("\n✅ Normalization complete")


if __name__ == "__main__":
    main()
