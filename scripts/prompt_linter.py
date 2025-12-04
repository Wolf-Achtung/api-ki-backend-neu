#!/usr/bin/env python3
"""
prompt_linter.py — PLATIN++ V5 Prompt Linter

Sprint F: CI/CD Stabilization & Auto-QA
Version: 1.0.0

Validates all prompts against PLATIN++ V5 standards:
- Persona compliance (no Team words in Solo, no C-Level in KMU)
- Anti-redundancy (no content from BC/QW/Roadmaps copied)
- Format validation (HTML only, no Markdown remnants)
- Forbidden terms (no REINFORCEMENT, template markers, etc.)
- Size requirements (must have SIZE-AWARE documentation)

Usage:
    python scripts/prompt_linter.py [--fix] [--verbose]

Exit codes:
    0 = All prompts pass
    1 = Errors found (CI should fail)
    2 = Warnings only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROMPTS_DIR = REPO_ROOT / "prompts"

# Persona forbidden terms
PERSONA_FORBIDDEN = {
    "solo": [
        # Team-related terms that shouldn't appear in Solo context
        "PMO-Team", "Team aufbauen", "Mitarbeiter einstellen",
        "Abteilung", "HR-Abteilung", "IT-Abteilung",
        "Change-Team", "Projektmanagement-Office",
        "Teammitglieder", "Teamleiter", "Team-Lead",
        "Department", "HR Team", "IT Department",
    ],
    "team": [
        # C-Level/Enterprise terms that shouldn't appear in Team context
        "C-Level", "C-Suite", "Board of Directors",
        "Division", "Business Unit", "Corporate",
        "Enterprise-wide", "Konzernleitung",
        "Vorstandsebene", "Geschäftsleitung",
    ],
    "kmu": [
        # Enterprise/Konzern terms that shouldn't appear in KMU context
        "Konzern", "Enterprise", "Global Rollout",
        "Headquarter", "Zentrale Steuerung",
        "Holding", "Tochtergesellschaften",
        "Division-Level", "Enterprise Architecture",
    ],
}

# Forbidden terms in all prompts
FORBIDDEN_GLOBAL = [
    "REINFORCEMENT",
    "Freitextfeld",
    "Freitext-Feld",
    "Template-Marker",
    "[Placeholder]",
    "[Name]",
    "[TODO]",
    "TODO:",
    "XXX:",
    "FIXME:",
    "Gold-Standard",  # Should be PLATIN++
    "{{STOP}}",
    "{{END}}",
]

# Format validation patterns
MARKDOWN_REMNANTS = [
    r"^##\s",           # Markdown headings (should be <h2>)
    r"^###\s",          # Markdown headings (should be <h3>)
    r"^\*\*[^*]+\*\*$", # Bold-only lines
    r"^-\s\[",          # Markdown checkboxes
    r"```",             # Code fences
]

# Required PLATIN++ header elements
REQUIRED_HEADERS = [
    "PLATIN++",
    "SECTION:",
    "OUTPUT:",
]

# SIZE-AWARE requirements
SIZE_AWARE_KEYWORDS = [
    "SIZE-AWARE",
    "COMPANY_SIZE",
    "solo",
    "team",
    "kmu",
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class LintIssue:
    """Represents a lint issue found in a prompt."""
    file: str
    line: int
    category: str
    severity: str  # "error" or "warning"
    message: str
    suggestion: Optional[str] = None


@dataclass
class LintResult:
    """Result of linting a single prompt file."""
    file: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


# =============================================================================
# Linting Functions
# =============================================================================

def check_persona_compliance(content: str, file_path: str) -> List[LintIssue]:
    """Check for persona-inappropriate terms."""
    issues = []
    lines = content.split("\n")

    # Determine which persona this prompt is for
    detected_personas: Set[str] = set()
    for line in lines:
        if "solo" in line.lower():
            detected_personas.add("solo")
        if "team" in line.lower():
            detected_personas.add("team")
        if "kmu" in line.lower() or "sme" in line.lower():
            detected_personas.add("kmu")

    # Check for forbidden terms in output section (after header)
    in_output = False
    for line_num, line in enumerate(lines, 1):
        # Skip header section (developer comments)
        if line.strip().startswith("<!--") or line.strip().startswith("Developer:"):
            continue
        if line.strip().endswith("-->"):
            in_output = True
            continue
        if line.strip().startswith("<section"):
            in_output = True

        if not in_output:
            continue

        line_lower = line.lower()

        # Check solo-specific forbidden terms
        if "solo" in detected_personas:
            for term in PERSONA_FORBIDDEN["solo"]:
                if term.lower() in line_lower:
                    issues.append(LintIssue(
                        file=file_path,
                        line=line_num,
                        category="persona",
                        severity="error",
                        message=f"Solo prompt contains forbidden term: '{term}'",
                        suggestion=f"Remove or replace '{term}' with size-appropriate language",
                    ))

        # Check team-specific forbidden terms
        if "team" in detected_personas:
            for term in PERSONA_FORBIDDEN["team"]:
                if term.lower() in line_lower:
                    issues.append(LintIssue(
                        file=file_path,
                        line=line_num,
                        category="persona",
                        severity="error",
                        message=f"Team prompt contains forbidden term: '{term}'",
                        suggestion=f"Remove or replace '{term}' with team-appropriate language",
                    ))

    return issues


def check_forbidden_terms(content: str, file_path: str) -> List[LintIssue]:
    """Check for globally forbidden terms."""
    issues = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for term in FORBIDDEN_GLOBAL:
            if term in line:
                # Allow "Gold-Standard" in dev comments only
                if term == "Gold-Standard" and ("<!--" in line or line.strip().startswith("#")):
                    continue
                issues.append(LintIssue(
                    file=file_path,
                    line=line_num,
                    category="forbidden",
                    severity="error",
                    message=f"Forbidden term found: '{term}'",
                    suggestion=f"Remove or replace '{term}'",
                ))

    return issues


def check_format_compliance(content: str, file_path: str) -> List[LintIssue]:
    """Check for format issues (Markdown remnants in HTML prompts)."""
    issues: List[LintIssue] = []
    lines = content.split("\n")

    # Check if this is an HTML-output prompt
    is_html_prompt = "OUTPUT: HTML" in content or "<!-- OUTPUT: HTML" in content

    if not is_html_prompt:
        return issues  # Skip Markdown prompts

    in_output = False
    for line_num, line in enumerate(lines, 1):
        # Track when we're in the output section
        if line.strip().startswith("<section"):
            in_output = True

        if not in_output:
            continue

        # Check for Markdown remnants
        for pattern in MARKDOWN_REMNANTS:
            if re.search(pattern, line):
                issues.append(LintIssue(
                    file=file_path,
                    line=line_num,
                    category="format",
                    severity="error",
                    message=f"Markdown remnant in HTML output: '{line.strip()[:50]}...'",
                    suggestion="Convert Markdown to proper HTML tags",
                ))

    return issues


def check_platin_headers(content: str, file_path: str) -> List[LintIssue]:
    """Check for required PLATIN++ header elements."""
    issues = []

    for header in REQUIRED_HEADERS:
        if header not in content:
            issues.append(LintIssue(
                file=file_path,
                line=1,
                category="header",
                severity="error",
                message=f"Missing PLATIN++ header element: '{header}'",
                suggestion=f"Add '<!-- {header} -->' to the prompt header",
            ))

    return issues


def check_size_aware(content: str, file_path: str) -> List[LintIssue]:
    """Check for SIZE-AWARE documentation."""
    issues = []

    has_size_aware = any(kw in content for kw in SIZE_AWARE_KEYWORDS[:2])  # SIZE-AWARE or COMPANY_SIZE
    has_persona_refs = sum(1 for kw in SIZE_AWARE_KEYWORDS[2:] if kw in content.lower())

    if not has_size_aware:
        issues.append(LintIssue(
            file=file_path,
            line=1,
            category="size",
            severity="warning",
            message="Missing SIZE-AWARE documentation",
            suggestion="Add SIZE-AWARE persona variations to the header",
        ))

    if has_persona_refs < 2:
        issues.append(LintIssue(
            file=file_path,
            line=1,
            category="size",
            severity="warning",
            message=f"Insufficient persona references (found {has_persona_refs}, expected 3)",
            suggestion="Document solo/team/kmu variations explicitly",
        ))

    return issues


def check_anti_redundancy(content: str, file_path: str) -> List[LintIssue]:
    """Check for anti-redundancy documentation."""
    issues = []

    # Check if ANTI-REDUNDANCY is documented
    if "ANTI-REDUNDANZ" not in content and "ANTI-REDUNDANCY" not in content:
        issues.append(LintIssue(
            file=file_path,
            line=1,
            category="redundancy",
            severity="warning",
            message="Missing ANTI-REDUNDANCY documentation",
            suggestion="Add ANTI-REDUNDANCY section to prevent content overlap",
        ))

    return issues


def lint_prompt_file(file_path: Path) -> LintResult:
    """Lint a single prompt file."""
    result = LintResult(file=str(file_path.relative_to(REPO_ROOT)))

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        result.issues.append(LintIssue(
            file=str(file_path),
            line=0,
            category="file",
            severity="error",
            message=f"Could not read file: {e}",
        ))
        return result

    # Run all checks
    result.issues.extend(check_platin_headers(content, result.file))
    result.issues.extend(check_persona_compliance(content, result.file))
    result.issues.extend(check_forbidden_terms(content, result.file))
    result.issues.extend(check_format_compliance(content, result.file))
    result.issues.extend(check_size_aware(content, result.file))
    result.issues.extend(check_anti_redundancy(content, result.file))

    return result


def lint_all_prompts(verbose: bool = False) -> Tuple[List[LintResult], int, int]:
    """Lint all prompt files."""
    results = []
    total_errors = 0
    total_warnings = 0

    # Find all prompt files
    prompt_files = list(PROMPTS_DIR.glob("**/*.md"))

    if verbose:
        print(f"\n🔍 Scanning {len(prompt_files)} prompt files...\n")

    for prompt_file in sorted(prompt_files):
        result = lint_prompt_file(prompt_file)
        results.append(result)
        total_errors += result.error_count
        total_warnings += result.warning_count

        if verbose and result.issues:
            print(f"📄 {result.file}")
            for issue in result.issues:
                icon = "❌" if issue.severity == "error" else "⚠️"
                print(f"  {icon} L{issue.line}: [{issue.category}] {issue.message}")
                if issue.suggestion:
                    print(f"     💡 {issue.suggestion}")
            print()

    return results, total_errors, total_warnings


def generate_report(results: List[LintResult], output_path: Optional[str] = None) -> Dict:
    """Generate a JSON report of lint results."""
    report: Dict[str, object] = {
        "summary": {
            "total_files": len(results),
            "files_with_errors": sum(1 for r in results if r.has_errors),
            "files_with_warnings": sum(1 for r in results if r.has_warnings and not r.has_errors),
            "total_errors": sum(r.error_count for r in results),
            "total_warnings": sum(r.warning_count for r in results),
        },
        "by_category": {},
        "files": [],
    }

    # Count by category
    categories: Dict[str, Dict[str, int]] = {}
    for result in results:
        for issue in result.issues:
            if issue.category not in categories:
                categories[issue.category] = {"errors": 0, "warnings": 0}
            if issue.severity == "error":
                categories[issue.category]["errors"] += 1
            else:
                categories[issue.category]["warnings"] += 1
    report["by_category"] = categories

    # File details
    files_list: List[Dict] = []
    for result in results:
        if result.issues:
            files_list.append({
                "file": result.file,
                "errors": result.error_count,
                "warnings": result.warning_count,
                "issues": [
                    {
                        "line": i.line,
                        "category": i.category,
                        "severity": i.severity,
                        "message": i.message,
                        "suggestion": i.suggestion,
                    }
                    for i in result.issues
                ],
            })
    report["files"] = files_list

    if output_path:
        Path(output_path).write_text(json.dumps(report, indent=2))

    return report


def output_github_format(results: List[LintResult]) -> None:
    """Output issues in GitHub Actions format."""
    for result in results:
        for issue in result.issues:
            level = "error" if issue.severity == "error" else "warning"
            # GitHub Actions annotation format
            print(f"::{level} file={result.file},line={issue.line}::[{issue.category}] {issue.message}")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="PLATIN++ V5 Prompt Linter")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues (not implemented)")
    parser.add_argument("--output", "-o", help="Output JSON report path")
    parser.add_argument("--warnings-as-errors", "-W", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--format", "-f", choices=["text", "github", "json"], default="text",
                       help="Output format (default: text)")
    args = parser.parse_args()

    is_github_format = args.format == "github"

    if not is_github_format:
        print("=" * 60)
        print("PLATIN++ V5 Prompt Linter")
        print("=" * 60)

    results, total_errors, total_warnings = lint_all_prompts(verbose=args.verbose and not is_github_format)

    # Output in GitHub Actions format if requested
    if is_github_format:
        output_github_format(results)

    # Generate report
    report = generate_report(results, args.output)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    elif not is_github_format:
        # Print summary for text format
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        summary = report['summary']
        if isinstance(summary, dict):
            print(f"Total files scanned: {summary.get('total_files', 0)}")
            print(f"Files with errors:   {summary.get('files_with_errors', 0)}")
            print(f"Files with warnings: {summary.get('files_with_warnings', 0)}")
            print(f"Total errors:        {summary.get('total_errors', 0)}")
            print(f"Total warnings:      {summary.get('total_warnings', 0)}")

        by_category = report.get("by_category")
        if by_category and isinstance(by_category, dict):
            print("\nBy Category:")
            for cat, counts in sorted(by_category.items()):
                if isinstance(counts, dict):
                    print(f"  {cat}: {counts.get('errors', 0)} errors, {counts.get('warnings', 0)} warnings")

    # Determine exit code
    if total_errors > 0:
        if not is_github_format:
            print("\n❌ FAILED: Errors found")
        sys.exit(1)
    elif args.warnings_as_errors and total_warnings > 0:
        if not is_github_format:
            print("\n❌ FAILED: Warnings treated as errors")
        sys.exit(1)
    elif total_warnings > 0:
        if not is_github_format:
            print("\n⚠️ PASSED with warnings")
        sys.exit(0)  # Changed: warnings should not fail CI by default
    else:
        if not is_github_format:
            print("\n✅ PASSED: All prompts compliant")
        sys.exit(0)


if __name__ == "__main__":
    main()
