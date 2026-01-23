#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIX-517: Prompt Manifest Gate — Preflight check for STRICT-readiness.

Checks:
  A) Manifest Coverage: every manifest entry has a file, every top-level prompt file is in manifest
  B) Usage: every prompt key used in code exists in manifest
  C) Include-Only: all Jinja2 includes are allowlisted (no path traversal, no escapes)

Usage:
  python scripts/prompt_manifest_gate.py --strict
  python scripts/prompt_manifest_gate.py --write-usage prompts/prompt_usage_report.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Resolve paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
MANIFEST_PATH = PROMPTS_DIR / "prompt_manifest.json"
LANGS = ["de", "en"]

# Files to scan for prompt key usage
USAGE_SCAN_FILES = [
    REPO_ROOT / "gpt_analyze.py",
]
USAGE_SCAN_DIRS = [
    REPO_ROOT / "services",
]

# Regex patterns for prompt key usage in code
# Only match actual prompt-loading calls, not general variable assignments
USAGE_PATTERNS = [
    re.compile(r'load_prompt\(\s*["\']([a-zA-Z0-9_]+)["\']'),
    re.compile(r'get_prompt\(\s*["\']([a-zA-Z0-9_]+)["\']'),
]

# SECTION_OUTPUT_MAP entries: "SECTION_NAME_HTML": "section_key"
SECTION_MAP_VALUE_PATTERN = re.compile(
    r'["\'][A-Z][A-Z0-9_]*_HTML["\']\s*:\s*["\']([a-z][a-z0-9_]+)["\']'
)
# section_steps tuples: ("section_key", "SECTION_NAME_HTML") or ("section_key", "_UPPER_RAW")
SECTION_STEPS_PATTERN = re.compile(
    r'\(\s*["\']([a-z][a-z0-9_]+)["\']\s*,\s*["\'][_A-Z][A-Z0-9_]*(?:_HTML|_RAW)["\']'
)

# Internal engine/simulation files excluded from coverage (not top-level prompts)
_ENGINE_PATTERNS = re.compile(
    r'(_engine|_simulation|_engine_v\d+)\.md$'
)

# EN alias files: German-named files in prompts/en/ that are compatibility copies
# These are covered by ALIASES_EN in prompt_loader.py
_EN_ALIAS_FILES = {
    "strategie_governance.md", "wettbewerb_benchmark.md",
    "technologie_prozesse.md", "tools_empfehlungen.md",
    "foerderpotenzial.md", "ki_aktivitaeten_ziele.md",
    "monetarisierung.md", "kickoff_vorlage.md",
    "foerderprogramme.md",
}

# Jinja2 include pattern
INCLUDE_PATTERN = re.compile(r'{%[-\s]*include\s+["\']([^"\']+)["\']')

# Strip patterns (documentation/examples that shouldn't count)
STRIP_PATTERNS = [
    re.compile(r'{%\s*raw\s*%}.*?{%\s*endraw\s*%}', re.DOTALL),
    re.compile(r'<!--.*?-->', re.DOTALL),
    re.compile(r'```.*?```', re.DOTALL),
]


def load_manifest() -> Dict:
    """Load and return the prompt manifest."""
    if not MANIFEST_PATH.exists():
        print(f"FAIL: Manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print(f"FAIL: Manifest is not a JSON object", file=sys.stderr)
        sys.exit(1)
    return data


def get_manifest_sections(manifest: Dict, lang: str) -> Dict[str, str]:
    """Get {section_key: path} for a language from manifest."""
    lang_block = manifest.get(lang, {})
    if not isinstance(lang_block, dict):
        return {}
    sections = {}
    for key, entry in lang_block.items():
        if key.startswith("_"):
            continue  # Skip meta keys
        if isinstance(entry, dict):
            path = entry.get("path")
            if path:
                sections[key] = str(path)
        elif isinstance(entry, str):
            sections[key] = entry
    return sections


def check_manifest_coverage(manifest: Dict) -> List[str]:
    """A) Check manifest coverage: files exist and top-level prompts are referenced."""
    errors: List[str] = []

    for lang in LANGS:
        sections = get_manifest_sections(manifest, lang)
        lang_dir = PROMPTS_DIR / lang

        if not lang_dir.exists():
            errors.append(f"[COVERAGE] Language directory missing: {lang_dir}")
            continue

        # A1: Every manifest entry points to an existing file
        for section_key, rel_path in sections.items():
            full_path = lang_dir / rel_path
            if not full_path.exists():
                errors.append(
                    f"[COVERAGE] Manifest entry [{lang}]{section_key} -> {rel_path} "
                    f"but file not found: {full_path}"
                )

        # A2: Every non-underscore .md file is referenced in manifest
        # (excluding engine/internal files and EN alias duplicates)
        manifest_paths = set(sections.values())
        for md_file in sorted(lang_dir.glob("*.md")):
            fname = md_file.name
            if fname.startswith("_"):
                continue  # Underscore partials are exempt
            if _ENGINE_PATTERNS.search(fname):
                continue  # Engine/simulation files are internal
            if lang == "en" and fname in _EN_ALIAS_FILES:
                continue  # EN alias duplicates (backward compat)
            if fname not in manifest_paths:
                errors.append(
                    f"[COVERAGE] File {lang}/{fname} exists but is NOT in manifest "
                    f"(add entry or prefix with _ if it's a partial)"
                )

    return errors


def check_usage(manifest: Dict) -> List[str]:
    """B) Check that all prompt keys used in code exist in manifest."""
    errors: List[str] = []

    # Collect all known manifest keys (across all languages)
    all_keys: Set[str] = set()
    for lang in LANGS:
        all_keys.update(get_manifest_sections(manifest, lang).keys())

    # Scan source files for prompt key usage
    used_keys: Set[str] = set()
    files_to_scan: List[Path] = list(USAGE_SCAN_FILES)
    for scan_dir in USAGE_SCAN_DIRS:
        if scan_dir.exists():
            files_to_scan.extend(scan_dir.rglob("*.py"))

    for src_file in files_to_scan:
        if not src_file.exists():
            continue
        try:
            content = src_file.read_text(encoding="utf-8")
        except Exception:
            continue

        # Match direct load_prompt/get_prompt calls (definitive usage)
        for pattern in USAGE_PATTERNS:
            for match in pattern.finditer(content):
                key = match.group(1)
                if key.startswith("_") or key.isupper():
                    continue
                used_keys.add(key)

        # Match section_steps tuples: ("section_key", "SECTION_NAME_HTML")
        # These are sections that get loaded via load_prompt in the section loop
        for match in SECTION_STEPS_PATTERN.finditer(content):
            key = match.group(1)
            if key.startswith("_") or key.isupper():
                continue
            used_keys.add(key)

    # Also scan for prompt_map entries: "section_key": "manifest_key"
    # Virtual sections that map to real manifest keys don't need their own entry
    prompt_map_pattern = re.compile(
        r'["\']([a-z][a-z0-9_]+)["\']\s*:\s*["\']([a-z][a-z0-9_]+)["\']'
    )
    mapped_keys: Set[str] = set()
    for src_file in files_to_scan:
        if not src_file.exists():
            continue
        try:
            content = src_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in prompt_map_pattern.finditer(content):
            src_key, dst_key = match.group(1), match.group(2)
            if dst_key in all_keys:
                mapped_keys.add(src_key)

    # Check: every used key must be in manifest or be a mapped virtual section
    for key in sorted(used_keys):
        if key in all_keys:
            continue
        if key in mapped_keys:
            continue
        # Engine files like "risk_engine_v3" are not in manifest by design
        if "_engine" in key or key.endswith("_strict"):
            continue
        # Skip section_name variable (it's the variable, not a literal key)
        if key == "section_name":
            continue
        errors.append(
            f"[USAGE] Key '{key}' used in code but NOT in manifest"
        )

    return errors


def check_includes(manifest: Dict) -> List[str]:
    """C) Check that all Jinja2 includes are allowlisted."""
    errors: List[str] = []

    for lang in LANGS:
        lang_dir = PROMPTS_DIR / lang
        if not lang_dir.exists():
            continue

        sections = get_manifest_sections(manifest, lang)

        # Build allowlist: manifest files + underscore partials
        allowed_templates: Set[str] = set()
        for rel_path in sections.values():
            allowed_templates.add(rel_path)
        for md_file in lang_dir.glob("_*.md"):
            allowed_templates.add(md_file.name)

        # Scan all manifest files AND underscore partials for includes
        files_to_check: List[Path] = []
        for rel_path in sections.values():
            p = lang_dir / rel_path
            if p.exists():
                files_to_check.append(p)
        for md_file in lang_dir.glob("_*.md"):
            files_to_check.append(md_file)

        for check_file in files_to_check:
            try:
                content = check_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Strip documentation blocks
            stripped = content
            for pat in STRIP_PATTERNS:
                stripped = pat.sub('', stripped)

            for match in INCLUDE_PATTERN.finditer(stripped):
                target = match.group(1)
                fname = check_file.name
                rel_src = f"{lang}/{fname}"

                # Check forbidden patterns
                if ".." in target:
                    errors.append(
                        f"[INCLUDE] {rel_src}: illegal include '{target}' "
                        f"reason=path_traversal (..)"
                    )
                    continue
                if target.startswith("/"):
                    errors.append(
                        f"[INCLUDE] {rel_src}: illegal include '{target}' "
                        f"reason=absolute_path"
                    )
                    continue
                if "\\" in target:
                    errors.append(
                        f"[INCLUDE] {rel_src}: illegal include '{target}' "
                        f"reason=backslash"
                    )
                    continue

                # Check allowlist
                if target not in allowed_templates:
                    errors.append(
                        f"[INCLUDE] {rel_src}: include '{target}' "
                        f"not in allowlist (not a manifest file or _partial)"
                    )

    return errors


def write_usage_report(manifest: Dict, output_path: Path) -> None:
    """Write a usage report to a markdown file."""
    lines = [
        "# Prompt Usage Report (FIX-517)\n",
        "",
        "## Manifest Sections\n",
        "",
    ]

    for lang in LANGS:
        sections = get_manifest_sections(manifest, lang)
        lines.append(f"### {lang.upper()} ({len(sections)} sections)\n")
        lines.append("")
        lines.append("| Section | Path | Exists |")
        lines.append("|---------|------|--------|")
        for key, path in sorted(sections.items()):
            exists = (PROMPTS_DIR / lang / path).exists()
            lines.append(f"| `{key}` | `{path}` | {'yes' if exists else 'NO'} |")
        lines.append("")

    lines.append("## Orphaned Files (not in manifest)\n")
    lines.append("")
    for lang in LANGS:
        sections = get_manifest_sections(manifest, lang)
        manifest_paths = set(sections.values())
        lang_dir = PROMPTS_DIR / lang
        if not lang_dir.exists():
            continue
        orphans = []
        for md_file in sorted(lang_dir.glob("*.md")):
            if not md_file.name.startswith("_") and md_file.name not in manifest_paths:
                orphans.append(md_file.name)
        if orphans:
            lines.append(f"### {lang.upper()}\n")
            for o in orphans:
                lines.append(f"- `{o}`")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Usage report written to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FIX-517: Prompt Manifest Gate (preflight check)"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 on any failure (CI mode)"
    )
    parser.add_argument(
        "--write-usage", type=str, default=None,
        help="Write usage report to given path"
    )
    args = parser.parse_args()

    manifest = load_manifest()

    # Run all checks
    all_errors: List[str] = []

    print("=" * 60)
    print("FIX-517: Prompt Manifest Gate")
    print("=" * 60)

    # A) Coverage
    coverage_errors = check_manifest_coverage(manifest)
    all_errors.extend(coverage_errors)
    if coverage_errors:
        print(f"\n[A] COVERAGE: {len(coverage_errors)} error(s)")
        for e in coverage_errors:
            print(f"  - {e}")
    else:
        print("\n[A] COVERAGE: OK")

    # B) Usage
    usage_errors = check_usage(manifest)
    all_errors.extend(usage_errors)
    if usage_errors:
        print(f"\n[B] USAGE: {len(usage_errors)} error(s)")
        for e in usage_errors:
            print(f"  - {e}")
    else:
        print("\n[B] USAGE: OK")

    # C) Includes
    include_errors = check_includes(manifest)
    all_errors.extend(include_errors)
    if include_errors:
        print(f"\n[C] INCLUDES: {len(include_errors)} error(s)")
        for e in include_errors:
            print(f"  - {e}")
    else:
        print("\n[C] INCLUDES: OK")

    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"RESULT: FAIL ({len(all_errors)} error(s))")
    else:
        print("RESULT: PASS")
    print("=" * 60)

    # Optional: write usage report
    if args.write_usage:
        write_usage_report(manifest, Path(args.write_usage))

    # Exit code
    if args.strict and all_errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
