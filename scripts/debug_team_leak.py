#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Script: Teams → Kapazitäten Forensik

Traces the transformation of "Microsoft Teams" through the pipeline
to identify where it gets replaced with "Microsoft Kapazitäten".

Usage:
    python scripts/debug_team_leak.py

Author: Claude Code Forensics
Version: 1.0.0 (v14.35.19+)
"""
from __future__ import annotations

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Callable, List, Tuple

# Test cases
TEST_CASES = [
    "Zoom / Microsoft Teams für Online-Meetings",
    "Microsoft Teams",
    "MS Teams",
    "Nutzen Sie Teams für die Kommunikation.",  # Should be replaced
    "Das Team arbeitet zusammen.",  # Should be replaced
]


def trace_transformation(
    text: str,
    stages: List[Tuple[str, Callable[[str], str]]]
) -> None:
    """Traces text through multiple transformation stages."""
    print(f"\n{'='*70}")
    print(f"INPUT: {text!r}")
    print(f"{'='*70}")

    current = text
    changed_in = None

    for stage_name, stage_fn in stages:
        try:
            after = stage_fn(current)
            if after != current:
                print(f"\n⚠️  CHANGED IN: {stage_name}")
                print(f"    BEFORE: {current!r}")
                print(f"    AFTER:  {after!r}")

                # Highlight the specific change
                if "Teams" in current and "Teams" not in after:
                    print(f"    🔴 'Teams' was REMOVED/REPLACED!")
                if "Kapazitäten" in after and "Kapazitäten" not in current:
                    print(f"    🔴 'Kapazitäten' was ADDED!")

                changed_in = stage_name
                current = after
            else:
                print(f"✓ {stage_name}: no change")
        except Exception as e:
            print(f"✗ {stage_name}: ERROR - {e}")

    print(f"\n{'─'*70}")
    print(f"FINAL OUTPUT: {current!r}")
    if changed_in:
        print(f"⚠️  TEXT WAS MODIFIED (last change in: {changed_in})")
    else:
        print("✓ TEXT UNCHANGED through all stages")


def main():
    print("=" * 70)
    print("FORENSIK: Teams → Kapazitäten Debug Script")
    print("=" * 70)

    # Import transformation functions
    stages: List[Tuple[str, Callable[[str], str]]] = []

    # Stage 1: Solo Persona Filter (main suspect)
    try:
        from services.prompt_enhancer import apply_solo_persona_filter
        stages.append(("prompt_enhancer.apply_solo_persona_filter", apply_solo_persona_filter))
    except ImportError as e:
        print(f"⚠️ Could not import apply_solo_persona_filter: {e}")

    # Stage 2: Simplify Solo Governance
    try:
        from services.prompt_enhancer import simplify_solo_governance
        # Wrap to pass company_size="solo"
        stages.append(("prompt_enhancer.simplify_solo_governance(solo)",
                       lambda t: simplify_solo_governance(t, "solo")))
    except ImportError as e:
        print(f"⚠️ Could not import simplify_solo_governance: {e}")

    # Stage 3: Grammar Fixer
    try:
        from services.content_quality_enforcer import apply_grammar_fixes
        stages.append(("content_quality_enforcer.apply_grammar_fixes",
                       lambda t: apply_grammar_fixes(t)[0]))
    except ImportError as e:
        print(f"⚠️ Could not import apply_grammar_fixes: {e}")

    # Stage 4: Text Healing
    try:
        from services.text_healing import heal_text_block
        stages.append(("text_healing.heal_text_block", heal_text_block))
    except ImportError as e:
        print(f"⚠️ Could not import heal_text_block: {e}")

    # Stage 5: Micro Correction Engine (if exists)
    try:
        from services.micro_correction_engine import apply_micro_corrections
        stages.append(("micro_correction_engine.apply_micro_corrections", apply_micro_corrections))
    except ImportError as e:
        print(f"⚠️ Could not import apply_micro_corrections: {e}")

    print(f"\nLoaded {len(stages)} transformation stages:")
    for name, _ in stages:
        print(f"  • {name}")

    # Run test cases
    for test_case in TEST_CASES:
        trace_transformation(test_case, stages)

    # Additional deep investigation of the Solo Persona Filter
    print("\n" + "=" * 70)
    print("DEEP INVESTIGATION: Solo Persona Filter Internals")
    print("=" * 70)

    try:
        from services.prompt_enhancer import (
            SOLO_PHRASE_REPLACEMENTS,
            SOLO_GOVERNANCE_REPLACEMENTS,
            PROTECTED_PRODUCT_NAMES,
        )

        print("\n📋 PROTECTED_PRODUCT_NAMES:")
        for name in PROTECTED_PRODUCT_NAMES:
            print(f"  ✓ {name!r}")

        print("\n📋 SOLO_GOVERNANCE_REPLACEMENTS (Teams-related):")
        for key, value in SOLO_GOVERNANCE_REPLACEMENTS.items():
            if "team" in key.lower() or "kapazität" in value.lower():
                print(f"  • {key!r} → {value!r}")

        print("\n📋 SOLO_PHRASE_REPLACEMENTS (Teams-related):")
        for key, value in SOLO_PHRASE_REPLACEMENTS.items():
            if "team" in key.lower() or "kapazität" in value.lower():
                print(f"  • {key!r} → {value!r}")

    except ImportError as e:
        print(f"⚠️ Could not import constants: {e}")

    # Step-by-step trace of apply_solo_persona_filter
    print("\n" + "=" * 70)
    print("STEP-BY-STEP TRACE: apply_solo_persona_filter")
    print("=" * 70)

    test_input = "Zoom / Microsoft Teams für Online-Meetings"
    print(f"\nInput: {test_input!r}")

    try:
        import re
        from services.prompt_enhancer import (
            SOLO_PHRASE_REPLACEMENTS,
            SOLO_GOVERNANCE_REPLACEMENTS,
            PROTECTED_PRODUCT_NAMES,
        )

        result = test_input
        print("\n--- Step 1: Protect product names ---")
        protected_map = {}
        for i, product_name in enumerate(PROTECTED_PRODUCT_NAMES):
            placeholder = f"__PROTECTED_PRODUCT_{i}__"
            if product_name.lower() in result.lower():
                pattern = re.compile(re.escape(product_name), re.IGNORECASE)
                match = pattern.search(result)
                if match:
                    original = match.group(0)
                    protected_map[placeholder] = original
                    result = pattern.sub(placeholder, result)
                    print(f"  ✓ Protected: {product_name!r} → {placeholder}")

        print(f"  After protection: {result!r}")
        print(f"  Protected map: {protected_map}")

        print("\n--- Step 2: Apply phrase replacements ---")
        for phrase, replacement in SOLO_PHRASE_REPLACEMENTS.items():
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            if pattern.search(result):
                new_result = pattern.sub(replacement, result)
                if new_result != result:
                    print(f"  🔴 REPLACED: {phrase!r} → {replacement!r}")
                    print(f"     Before: {result!r}")
                    print(f"     After:  {new_result!r}")
                    result = new_result

        print(f"  After phrase replacements: {result!r}")

        print("\n--- Step 3: Apply word-based replacements ---")
        sorted_replacements = sorted(
            SOLO_GOVERNANCE_REPLACEMENTS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for term, replacement in sorted_replacements:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            if pattern.search(result):
                new_result = pattern.sub(replacement, result)
                if new_result != result:
                    print(f"  🔴 REPLACED: {term!r} → {replacement!r}")
                    print(f"     Before: {result!r}")
                    print(f"     After:  {new_result!r}")
                    result = new_result

        print(f"  After word replacements: {result!r}")

        print("\n--- Step 4: Restore protected names ---")
        for placeholder, original in protected_map.items():
            if placeholder in result:
                result = result.replace(placeholder, original)
                print(f"  ✓ Restored: {placeholder} → {original!r}")
            else:
                print(f"  ⚠️ Placeholder {placeholder} NOT FOUND in result!")

        print(f"\n  FINAL: {result!r}")

    except Exception as e:
        print(f"⚠️ Error during step-by-step trace: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
