#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROMPT-USAGE Audit Script

Validates:
1. Every used section (from artifacts/prompt_usage_last.json) exists in prompt_manifest.json
2. Every manifest entry points to an existing file
3. Includes are valid (no path traversal, files exist)

Exit code 0 = all OK, non-zero = errors found.
Usage: python scripts/prompt_usage_audit.py
"""
import json
import sys
from pathlib import Path

# Resolve paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "prompts" / "prompt_manifest.json"
USAGE_PATH = REPO_ROOT / "artifacts" / "prompt_usage_last.json"
PROMPTS_DIR = REPO_ROOT / "prompts"

# Forbidden patterns in include paths
FORBIDDEN_INCLUDE_PATTERNS = ["..", "\\"]


def load_manifest() -> dict:
    """Load prompt_manifest.json."""
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}")
        sys.exit(2)
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("ERROR: Manifest is not a dict")
        sys.exit(2)
    return data


def load_usage() -> list:
    """Load usage artifact if available."""
    if not USAGE_PATH.exists():
        return []
    try:
        data = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"WARNING: Could not parse usage artifact: {e}")
        return []


def get_manifest_sections(manifest: dict) -> dict:
    """Extract {lang: {section: path}} from manifest."""
    result = {}
    for lang in ("de", "en"):
        lang_block = manifest.get(lang)
        if not isinstance(lang_block, dict):
            continue
        sections = {}
        for key, val in lang_block.items():
            if key.startswith("_"):
                continue  # skip meta keys
            if isinstance(val, dict):
                path = val.get("path")
                if isinstance(path, str):
                    sections[key] = path
            elif isinstance(val, str):
                sections[key] = val
        result[lang] = sections
    return result


def audit() -> int:
    """Run all audit checks. Returns number of errors."""
    errors = 0
    manifest = load_manifest()
    manifest_sections = get_manifest_sections(manifest)
    usage = load_usage()

    # CHECK 1: All manifest entries point to existing files
    print("--- CHECK 1: Manifest file existence ---")
    for lang, sections in manifest_sections.items():
        for section, rel_path in sections.items():
            full_path = PROMPTS_DIR / lang / rel_path
            if not full_path.exists():
                print(f"  ERROR: [{lang}] section={section} path={full_path} MISSING")
                errors += 1

    if errors == 0:
        print(f"  OK: All manifest entries point to existing files "
              f"(de={len(manifest_sections.get('de', {}))}, en={len(manifest_sections.get('en', {}))})")

    # CHECK 2: Used sections are in manifest
    if usage:
        print(f"\n--- CHECK 2: Usage subset of manifest (entries={len(usage)}) ---")
        for entry in usage:
            section = entry.get("section", "")
            lang = entry.get("lang", "de")
            if lang not in manifest_sections:
                print(f"  ERROR: Used lang={lang} not in manifest")
                errors += 1
                continue
            if section not in manifest_sections[lang]:
                print(f"  ERROR: Used section={section} lang={lang} NOT in manifest")
                errors += 1
        if errors == 0:
            print(f"  OK: All {len(usage)} used sections are in manifest")
    else:
        print("\n--- CHECK 2: No usage artifact found (skipped) ---")

    # CHECK 3: Includes validation
    print("\n--- CHECK 3: Include path safety ---")
    include_errors = 0
    checked = 0
    for entry in usage:
        includes = entry.get("includes", [])
        lang = entry.get("lang", "de")
        section = entry.get("section", "")
        for inc in includes:
            checked += 1
            # Path traversal check
            for forbidden in FORBIDDEN_INCLUDE_PATTERNS:
                if forbidden in inc:
                    print(f"  ERROR: [{lang}/{section}] include='{inc}' contains '{forbidden}'")
                    include_errors += 1
                    break
            # Absolute path check
            if inc.startswith("/"):
                print(f"  ERROR: [{lang}/{section}] include='{inc}' is absolute")
                include_errors += 1
            # File existence check
            inc_path = PROMPTS_DIR / lang / inc
            if not inc_path.exists():
                # Try base prompts dir
                inc_path_base = PROMPTS_DIR / inc
                if not inc_path_base.exists():
                    print(f"  WARNING: [{lang}/{section}] include='{inc}' file not found")

    errors += include_errors
    if include_errors == 0:
        print(f"  OK: {checked} includes checked, all safe")

    # CHECK 4: Static code scan for section keys used in codebase
    print("\n--- CHECK 4: Static section key scan (gpt_analyze.py) ---")
    gpt_analyze = REPO_ROOT / "gpt_analyze.py"
    if gpt_analyze.exists():
        import re
        source = gpt_analyze.read_text(encoding="utf-8")
        # Find load_prompt("section_name" patterns
        pattern = re.compile(r'load_prompt\(\s*["\']([a-zA-Z0-9_]+)["\']')
        found_sections = set(pattern.findall(source))
        all_manifest_sections = set()
        for sections in manifest_sections.values():
            all_manifest_sections.update(sections.keys())

        missing = found_sections - all_manifest_sections
        if missing:
            for s in sorted(missing):
                print(f"  WARNING: load_prompt('{s}') in gpt_analyze.py but not in manifest")
        else:
            print(f"  OK: All {len(found_sections)} load_prompt() calls match manifest")
    else:
        print("  SKIP: gpt_analyze.py not found")

    # Summary
    print(f"\n{'='*50}")
    if errors == 0:
        print("RESULT: ALL CHECKS PASSED")
    else:
        print(f"RESULT: {errors} ERROR(S) FOUND")
    return errors


if __name__ == "__main__":
    error_count = audit()
    sys.exit(1 if error_count > 0 else 0)
