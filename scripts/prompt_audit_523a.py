#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-523A: Prompt Hygiene Audit Script

Audits all prompt files for potential issues:
1. Code fences (``` or ~~~)
2. Explicit chat phrases
3. Explicit forbidden token lists (blacklists naming forbidden words)
4. Placeholder bait ([1 Satz], {variable}, {{token}} in examples)
5. HTML entity artifacts (&uuml; etc.) and typographic quotes („")
6. Unresolved/missing template variables

Usage:
    python scripts/prompt_audit_523a.py [--strict] [--output-json artifacts/prompt_audit_523a.json]

Exit codes:
    0 - No violations (or --strict not specified)
    1 - Violations found in strict mode
"""

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Directories to scan for prompt files
PROMPT_DIRS = [
    "prompts/de",
    "prompts/en",
]

# File patterns to audit
PROMPT_PATTERNS = ["*.md", "*.txt"]

# Allowed template variables (Jinja2 style)
ALLOWED_VARS = {
    # Core fields
    "BRANCHE", "branche", "BRANCHE_LABEL", "BRANCH_CORE_LABEL", "BRANCH_CONTEXT_LABEL",
    "UNTERNEHMENSGROESSE", "unternehmensgroesse", "UNTERNEHMENSGROESSE_LABEL",
    "COMPANY_SIZE", "company_size",
    "BUNDESLAND", "bundesland", "BUNDESLAND_LABEL",
    "hauptleistung", "HAUPTLEISTUNG", "HAUPTUMSATZTREIBER", "OFFERING_LABEL",
    # Goldnuggets
    "ZEITERSPARNIS_PRIORITAET", "ZEITERSPARNIS_PRIORITAET_SAFE",
    "KI_PROJEKTE", "KI_PROJEKTE_SAFE", "ki_projekte",
    "KI_GUARDRAILS", "ki_guardrails",
    "VISION_3_JAHRE", "VISION_3_JAHRE_SAFE", "vision_3_jahre",
    # Scores
    "score_security", "score_governance", "score_maturity", "score_readiness",
    "score_innovation", "score_data_readiness", "score_process_automation",
    # Dates and meta
    "TODAY", "heute_iso", "DATE_30D", "report_date", "report_year",
    "next_year", "next_year_short",
    # Other common vars
    "JAHRESUMSATZ_LABEL", "INVESTITIONSBUDGET",
    "IT_INFRASTRUKTUR_LABEL", "PROZESSE_PAPIERLOS_LABEL",
    "AUTOMATISIERUNGSGRAD_LABEL", "INTERNE_KI_KOMPETENZEN_LABEL",
    "ROADMAP_VORHANDEN_LABEL", "GOVERNANCE_RICHTLINIEN_LABEL",
    "CHANGE_MANAGEMENT_LABEL", "INTERESSE_FOERDERUNG_LABEL",
    "MARKTPOSITION_LABEL", "BENCHMARK_WETTBEWERB_LABEL",
    "SELBSTSTAENDIG_LABEL", "ZIELGRUPPEN_LABELS",
    "KI_ZIELE_LABELS", "KI_HEMMNISSE_LABELS",
    "ANWENDUNGSFAELLE_LABELS", "DATENQUELLEN_LABELS",
    "VORHANDENE_TOOLS_LABELS", "REGULIERTE_BRANCHE_LABELS",
    "TRAININGS_INTERESSEN_LABELS",
}

# Chat phrases that should not appear in prompts
CHAT_PHRASES = [
    r"\bwie kann ich (?:dir|Ihnen) helfen\b",
    r"\bgern(?:e)? geschehen\b",
    r"\bnatürlich(?:,| )(?:hier|gerne)\b",
    r"\bhier (?:sind|ist|haben Sie)\b",
    r"\bbitte beschreib(?:e|en)\b",
    r"\bfrag(?:e|en Sie) (?:mich|uns)\b",
    r"\bkann ich (?:dir|Ihnen) (?:noch|weiter)\b",
    r"\blass(?:en Sie)? mich wissen\b",
    r"\bstehe(?:n Sie)? (?:gerne |)zur Verfügung\b",
    r"\bwenn Sie (?:noch |weitere )?Fragen haben\b",
    r"\bzögern Sie nicht\b",
    r"\bich helfe (?:dir|Ihnen) gerne\b",
]

# Forbidden token blacklist patterns (explicit naming of forbidden words)
BLACKLIST_PATTERNS = [
    r"(?:HARD |STRICT )?BLACKLIST[:\s]",
    r"VERBOTENE?\s+(?:WÖRTER|BEGRIFFE|TOKEN)[:\s]",
    r"FORBIDDEN\s+(?:WORDS|TOKENS|TERMS)[:\s]",
    r"(?:NICHT|NEVER)\s+(?:VERWENDEN|USE)[:\s].*(?:Rollout|Stack|Skalierung|Stakeholder|Dashboard|Pipeline|Module)",
]

# HTML entity patterns that should not appear
ENTITY_PATTERNS = [
    r"&uuml;", r"&ouml;", r"&auml;",
    r"&Uuml;", r"&Ouml;", r"&Auml;",
    r"&szlig;", r"&amp;(?:uuml|ouml|auml|Uuml|Ouml|Auml|szlig);",
]

# Typographic quote patterns
TYPO_QUOTE_PATTERNS = [
    r"„", r""", r""",  # German quotes
    r"'", r"'",  # Smart single quotes
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Violation:
    """Represents a single audit violation."""
    category: str
    line_number: int
    line_content: str
    description: str


@dataclass
class FileAuditResult:
    """Audit result for a single file."""
    file_path: str
    violations: List[Violation] = field(default_factory=list)
    code_fence_count: int = 0
    chat_phrase_count: int = 0
    blacklist_count: int = 0
    placeholder_bait_count: int = 0
    entity_artifact_count: int = 0
    typo_quote_count: int = 0
    unresolved_vars: List[str] = field(default_factory=list)

    @property
    def total_violations(self) -> int:
        return len(self.violations)

    @property
    def is_clean(self) -> bool:
        return self.total_violations == 0


@dataclass
class AuditSummary:
    """Summary of the entire audit."""
    total_files: int = 0
    clean_files: int = 0
    files_with_violations: int = 0
    total_violations: int = 0
    violations_by_category: Dict[str, int] = field(default_factory=dict)
    file_results: List[FileAuditResult] = field(default_factory=list)


# =============================================================================
# AUDIT FUNCTIONS
# =============================================================================

def audit_file(file_path: Path) -> FileAuditResult:
    """
    Audit a single prompt file for violations.

    Args:
        file_path: Path to the prompt file

    Returns:
        FileAuditResult with all found violations
    """
    result = FileAuditResult(file_path=str(file_path))

    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        result.violations.append(Violation(
            category="READ_ERROR",
            line_number=0,
            line_content="",
            description=f"Failed to read file: {e}"
        ))
        return result

    lines = content.split('\n')

    for line_num, line in enumerate(lines, start=1):
        # Skip HTML comments (they're not rendered to LLM)
        if line.strip().startswith('<!--') or line.strip().startswith('-->'):
            continue
        # Check if we're in an HTML comment block
        # (simplified check - doesn't handle all edge cases)

        # 1. Code fences
        if re.search(r'^```|^~~~', line.strip()):
            result.code_fence_count += 1
            result.violations.append(Violation(
                category="CODE_FENCE",
                line_number=line_num,
                line_content=line[:100],
                description="Code fence found - may prime LLM to output code blocks"
            ))

        # 2. Chat phrases
        for pattern in CHAT_PHRASES:
            if re.search(pattern, line, re.IGNORECASE):
                result.chat_phrase_count += 1
                result.violations.append(Violation(
                    category="CHAT_PHRASE",
                    line_number=line_num,
                    line_content=line[:100],
                    description=f"Chat phrase pattern found: {pattern}"
                ))
                break  # Only count once per line

        # 3. Explicit forbidden token blacklists
        for pattern in BLACKLIST_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                result.blacklist_count += 1
                result.violations.append(Violation(
                    category="EXPLICIT_BLACKLIST",
                    line_number=line_num,
                    line_content=line[:100],
                    description="Explicit blacklist naming forbidden words - may prime those words"
                ))
                break

        # 4. Placeholder bait (but not in HTML comments)
        placeholder_patterns = [
            r'\[1 Satz\]', r'\[Max\. \d', r'\[Bezug zu',
            r'\{variable\}', r'\{\{token\}\}',
            r'\[konkret', r'\[hier ', r'\[ein ',
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Skip if in HTML comment
                if '<!--' in line or '-->' in line:
                    continue
                result.placeholder_bait_count += 1
                result.violations.append(Violation(
                    category="PLACEHOLDER_BAIT",
                    line_number=line_num,
                    line_content=line[:100],
                    description=f"Placeholder pattern in non-comment: {pattern}"
                ))
                break

        # 5. HTML entity artifacts
        for pattern in ENTITY_PATTERNS:
            if re.search(pattern, line):
                result.entity_artifact_count += 1
                result.violations.append(Violation(
                    category="HTML_ENTITY",
                    line_number=line_num,
                    line_content=line[:100],
                    description=f"HTML entity artifact: {pattern}"
                ))
                break

        # 6. Typographic quotes
        for pattern in TYPO_QUOTE_PATTERNS:
            if pattern in line:
                # Skip in HTML comments
                if '<!--' in line or '-->' in line:
                    continue
                result.typo_quote_count += 1
                result.violations.append(Violation(
                    category="TYPO_QUOTE",
                    line_number=line_num,
                    line_content=line[:100],
                    description=f"Typographic quote found: {pattern}"
                ))
                break

    # 7. Check for unresolved template variables
    all_vars = set(re.findall(r'\{\{(\w+)\}\}', content))
    unresolved = all_vars - ALLOWED_VARS
    if unresolved:
        result.unresolved_vars = list(unresolved)
        # Don't add as violations - just informational

    return result


def run_audit(prompt_dirs: List[str], strict: bool = False) -> AuditSummary:
    """
    Run the full audit across all prompt directories.

    Args:
        prompt_dirs: List of directories to scan
        strict: If True, code_fence in examples (not output sections) is not a violation

    Returns:
        AuditSummary with all results
    """
    summary = AuditSummary()

    for prompt_dir in prompt_dirs:
        dir_path = Path(prompt_dir)
        if not dir_path.exists():
            log.warning(f"Prompt directory not found: {prompt_dir}")
            continue

        for pattern in PROMPT_PATTERNS:
            for file_path in dir_path.glob(pattern):
                result = audit_file(file_path)
                summary.file_results.append(result)
                summary.total_files += 1

                if result.is_clean:
                    summary.clean_files += 1
                else:
                    summary.files_with_violations += 1
                    summary.total_violations += result.total_violations

                    # Count by category
                    for v in result.violations:
                        summary.violations_by_category[v.category] = \
                            summary.violations_by_category.get(v.category, 0) + 1

    return summary


def generate_markdown_report(summary: AuditSummary) -> str:
    """Generate a Markdown report from the audit summary."""
    lines = [
        "# FIX-523A Prompt Audit Report",
        "",
        "## Summary",
        "",
        f"- **Total files scanned:** {summary.total_files}",
        f"- **Clean files:** {summary.clean_files}",
        f"- **Files with violations:** {summary.files_with_violations}",
        f"- **Total violations:** {summary.total_violations}",
        "",
    ]

    if summary.violations_by_category:
        lines.append("### Violations by Category")
        lines.append("")
        for cat, count in sorted(summary.violations_by_category.items()):
            lines.append(f"- **{cat}:** {count}")
        lines.append("")

    if summary.files_with_violations > 0:
        lines.append("## Files with Violations")
        lines.append("")

        for result in summary.file_results:
            if not result.is_clean:
                lines.append(f"### {result.file_path}")
                lines.append("")
                lines.append(f"**Violations:** {result.total_violations}")
                lines.append("")

                for v in result.violations:
                    lines.append(f"- **Line {v.line_number}** [{v.category}]: {v.description}")
                    lines.append(f"  ```")
                    lines.append(f"  {v.line_content}")
                    lines.append(f"  ```")
                lines.append("")

                if result.unresolved_vars:
                    lines.append(f"**Unresolved variables:** {', '.join(result.unresolved_vars)}")
                    lines.append("")

    lines.append("## Fix Hints")
    lines.append("")
    lines.append("- **CODE_FENCE:** Remove code fences from prompt output examples; describe structure in prose")
    lines.append("- **CHAT_PHRASE:** Remove conversational language from prompts")
    lines.append("- **EXPLICIT_BLACKLIST:** Replace explicit forbidden-word lists with general rules")
    lines.append("- **PLACEHOLDER_BAIT:** Replace [placeholder] patterns with concrete descriptions")
    lines.append("- **HTML_ENTITY:** Replace &uuml; etc. with actual UTF-8 characters (ü)")
    lines.append("- **TYPO_QUOTE:** Replace „ " " with ASCII quotes (\")")
    lines.append("")

    return "\n".join(lines)


def generate_json_report(summary: AuditSummary) -> dict:
    """Generate a JSON-serializable report from the audit summary."""
    return {
        "summary": {
            "total_files": summary.total_files,
            "clean_files": summary.clean_files,
            "files_with_violations": summary.files_with_violations,
            "total_violations": summary.total_violations,
            "violations_by_category": summary.violations_by_category,
        },
        "files": [
            {
                "path": r.file_path,
                "violations": [asdict(v) for v in r.violations],
                "counts": {
                    "code_fence": r.code_fence_count,
                    "chat_phrase": r.chat_phrase_count,
                    "blacklist": r.blacklist_count,
                    "placeholder_bait": r.placeholder_bait_count,
                    "entity_artifact": r.entity_artifact_count,
                    "typo_quote": r.typo_quote_count,
                },
                "unresolved_vars": r.unresolved_vars,
            }
            for r in summary.file_results
        ]
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="FIX-523A: Prompt Hygiene Audit"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any violations found"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="artifacts/prompt_audit_523a.json",
        help="Path to output JSON report"
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="docs/PROMPT_AUDIT_523A.md",
        help="Path to output Markdown report"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output JSON summary to stdout only (for preflight checks)"
    )
    args = parser.parse_args()

    log.info("[FIX-523A] Starting prompt hygiene audit...")

    # Run audit
    summary = run_audit(PROMPT_DIRS, strict=args.strict)

    # JSON-only mode for preflight checks
    if args.json_only:
        compact_summary = {
            "total_files": summary.total_files,
            "total_violations": summary.total_violations,
            "by_type": summary.violations_by_category,
            "status": "FAIL" if summary.total_violations > 0 else "PASS"
        }
        print(json.dumps(compact_summary))
        sys.exit(1 if summary.total_violations > 0 else 0)

    # Generate reports
    md_report = generate_markdown_report(summary)
    json_report = generate_json_report(summary)

    # Write reports
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(md_report, encoding='utf-8')
    log.info(f"[FIX-523A] Markdown report written to: {args.output_md}")

    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(
        json.dumps(json_report, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    log.info(f"[FIX-523A] JSON report written to: {args.output_json}")

    # Print summary
    print("\n" + "=" * 60)
    print("FIX-523A PROMPT AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total files:          {summary.total_files}")
    print(f"Clean files:          {summary.clean_files}")
    print(f"Files with issues:    {summary.files_with_violations}")
    print(f"Total violations:     {summary.total_violations}")
    print("=" * 60)

    if summary.violations_by_category:
        print("\nViolations by category:")
        for cat, count in sorted(summary.violations_by_category.items()):
            print(f"  {cat}: {count}")

    # Exit code
    if args.strict and summary.total_violations > 0:
        log.error(f"[FIX-523A] STRICT MODE: {summary.total_violations} violations found - FAIL")
        sys.exit(1)
    else:
        log.info("[FIX-523A] Audit complete")
        sys.exit(0)


if __name__ == "__main__":
    main()
