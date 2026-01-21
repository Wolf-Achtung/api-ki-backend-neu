#!/usr/bin/env python3
"""
FIX-505: Prompt Cycle Preflight Checker

This script checks prompt templates for include cycles BEFORE runtime,
allowing CI/CD pipelines to catch template errors early.

Usage:
    python scripts/prompt_cycle_checker.py [--strict] [--json]

Exit codes:
    0 - No cycles detected
    1 - Cycles detected (or other errors in strict mode)

Version: 1.0.0 (FIX-505)
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.prompt_loader import check_prompt_cycles, BASE_DIR

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='FIX-505: Check prompt templates for include cycles'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code on any warnings'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--prompts-dir',
        type=str,
        default=None,
        help='Override prompts directory (default: auto-detect)'
    )
    parser.add_argument(
        '--langs',
        type=str,
        default='de,en',
        help='Comma-separated list of languages to check (default: de,en)'
    )

    args = parser.parse_args()

    # Determine prompts directory
    prompts_dir = Path(args.prompts_dir) if args.prompts_dir else BASE_DIR
    langs = [l.strip() for l in args.langs.split(',')]

    if not args.json:
        print(f"\n{'='*60}")
        print("FIX-505: Prompt Cycle Preflight Check")
        print(f"{'='*60}")
        print(f"Prompts directory: {prompts_dir}")
        print(f"Languages: {langs}")
        print(f"Mode: {'STRICT' if args.strict else 'NORMAL'}")
        print(f"{'='*60}\n")

    # Run cycle check
    try:
        result = check_prompt_cycles(base_dir=prompts_dir, langs=langs)
    except Exception as e:
        if args.json:
            print(json.dumps({
                "error": str(e),
                "passed": False,
            }, indent=2))
        else:
            log.error(f"Error during cycle check: {e}")
        sys.exit(1)

    # Output results
    cycles = result.get('cycles', [])
    warnings = result.get('warnings', [])
    checked_files = result.get('checked_files', 0)

    has_cycles = len(cycles) > 0
    has_warnings = len(warnings) > 0
    passed = not has_cycles and (not has_warnings or not args.strict)

    if args.json:
        output = {
            "passed": passed,
            "cycles_found": len(cycles),
            "warnings": len(warnings),
            "files_checked": checked_files,
            "cycles": cycles,
            "warning_messages": warnings,
            "graph": result.get('graph', {}),
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Files checked: {checked_files}")
        print(f"Cycles found: {len(cycles)}")
        print(f"Warnings: {len(warnings)}")

        if cycles:
            print(f"\n{'!'*60}")
            print("CYCLES DETECTED:")
            print(f"{'!'*60}")
            for i, cycle in enumerate(cycles, 1):
                cycle_str = ' -> '.join(cycle)
                print(f"  {i}. {cycle_str}")
            print()

        if warnings:
            print(f"\n{'-'*60}")
            print("WARNINGS:")
            print(f"{'-'*60}")
            for warning in warnings:
                print(f"  - {warning}")
            print()

        print(f"{'='*60}")
        if passed:
            print("✅ PREFLIGHT CHECK PASSED")
        else:
            print("❌ PREFLIGHT CHECK FAILED")
        print(f"{'='*60}\n")

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
