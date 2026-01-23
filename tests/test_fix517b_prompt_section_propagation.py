"""
FIX-517B Regression Guard: Ensure _interpolate call passes section + lang.

This test prevents regression of the root cause identified in STATE-AUDIT-517A:
gpt_analyze.py called _interpolate(enhanced_prompt, vars_dict) WITHOUT section/lang,
causing section="unknown" default → ValueError in STRICT mode → legacy fallback →
SECTION_TOO_SHORT for tools_empfehlungen + gamechanger.

The fix (1 line): pass section=prompt_key, lang=prompt_lang to _interpolate.
"""

import re
from pathlib import Path

GPT_ANALYZE_PATH = Path(__file__).parent.parent / "gpt_analyze.py"


def test_interpolate_call_passes_section_and_lang():
    """Guard: _interpolate in Enhanced-Path MUST pass section=prompt_key and lang=prompt_lang."""
    source = GPT_ANALYZE_PATH.read_text(encoding="utf-8")

    # Find the _interpolate call in the Enhanced-Path (after enhance_prompt)
    # Pattern: _interpolate(enhanced_prompt, vars_dict, lang=prompt_lang, section=prompt_key)
    pattern = r"_interpolate\(\s*enhanced_prompt\s*,\s*vars_dict\s*,\s*lang\s*=\s*prompt_lang\s*,\s*section\s*=\s*prompt_key\s*\)"
    matches = re.findall(pattern, source)
    assert len(matches) >= 1, (
        "REGRESSION: _interpolate(enhanced_prompt, vars_dict) must include "
        "lang=prompt_lang, section=prompt_key — otherwise section defaults to 'unknown' "
        "and STRICT mode raises ValueError (see STATE-AUDIT-517A)"
    )


def test_platin_min_words_includes_tools_empfehlungen():
    """Guard: platin_min_words must have an entry for tools_empfehlungen."""
    source = GPT_ANALYZE_PATH.read_text(encoding="utf-8")

    # Verify tools_empfehlungen appears in platin_min_words dict
    pattern = r'"tools_empfehlungen"\s*:\s*\d+'
    # Find it within the platin_min_words block
    platin_block_match = re.search(
        r"platin_min_words\s*=\s*\{([^}]+)\}", source, re.DOTALL
    )
    assert platin_block_match, "platin_min_words dict not found in gpt_analyze.py"

    block_content = platin_block_match.group(1)
    assert re.search(pattern, block_content), (
        "REGRESSION: platin_min_words must include 'tools_empfehlungen' entry — "
        "otherwise short content passes generator check but fails validator "
        "(see STATE-AUDIT-517A section_too_short)"
    )


def test_no_bare_interpolate_call_without_section():
    """Guard: no _interpolate(enhanced_prompt, vars_dict) call without section= param."""
    source = GPT_ANALYZE_PATH.read_text(encoding="utf-8")

    # Find bare calls: _interpolate(enhanced_prompt, vars_dict) without section=
    bare_pattern = r"_interpolate\(\s*enhanced_prompt\s*,\s*vars_dict\s*\)"
    bare_matches = re.findall(bare_pattern, source)
    assert len(bare_matches) == 0, (
        f"REGRESSION: Found {len(bare_matches)} bare _interpolate(enhanced_prompt, vars_dict) "
        "call(s) without section= parameter. This causes section='unknown' in STRICT mode."
    )
