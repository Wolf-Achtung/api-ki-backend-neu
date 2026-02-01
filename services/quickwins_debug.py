# -*- coding: utf-8 -*-
"""
TASK 1 (P0 FINAL): Quick Wins 4-Point Debug Pipeline

This module provides deterministic debugging for Quick Wins at 4 key points:
1. RAW JSON - directly after LLM/parsing
2. Renderer Output HTML - directly after render_quickwins_*
3. After heal_report_html(sections, segment)
4. After heal_final_html(final_html, segment)

Debug output is written to /tmp/debug_quickwins_*.{json,html} files.

Enable debugging by setting environment variable:
    QUICKWINS_DEBUG=1

Or programmatically:
    from services.quickwins_debug import enable_quickwins_debug
    enable_quickwins_debug()
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)

# Debug toggle - can be set via environment variable or programmatically
_DEBUG_ENABLED = os.environ.get("QUICKWINS_DEBUG", "").lower() in ("1", "true", "yes")

# Debug output directory
DEBUG_OUTPUT_DIR = "/tmp"

# Counter for unique dump IDs within a session
_dump_counter = 0


def enable_quickwins_debug():
    """Enable Quick Wins debug pipeline."""
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = True
    log.info("[QW-DEBUG] Quick Wins debug pipeline ENABLED")


def disable_quickwins_debug():
    """Disable Quick Wins debug pipeline."""
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = False
    log.info("[QW-DEBUG] Quick Wins debug pipeline DISABLED")


def is_debug_enabled() -> bool:
    """Check if Quick Wins debug is enabled."""
    return _DEBUG_ENABLED


def _get_dump_id() -> str:
    """Get unique dump ID for this debug session."""
    global _dump_counter
    _dump_counter += 1
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{_dump_counter:04d}"


def _safe_write(filepath: str, content: str) -> bool:
    """Safely write content to file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        log.info("[QW-DEBUG] Dumped to: %s (%d bytes)", filepath, len(content))
        return True
    except Exception as e:
        log.error("[QW-DEBUG] Failed to write %s: %s", filepath, e)
        return False


def _extract_quickwins_summary(content: str) -> Dict[str, Any]:
    """Extract summary info from Quick Wins content for logging."""
    summary = {
        "length": len(content),
        "has_problem_label": "Problem:" in content or "PROBLEM:" in content,
        "has_wirkung_label": "Wirkung:" in content or "WIRKUNG:" in content,
        "has_umsetzung_label": "Umsetzung:" in content or "UMSETZUNG:" in content,
        "quickwin_card_count": len(re.findall(r'class="quick-win', content)),
        "empty_p_tags": len(re.findall(r'<p[^>]*>\s*</p>', content)),
        "label_only_patterns": 0,
    }

    # Check for label-only patterns (label followed immediately by closing tag)
    label_only_count = 0
    for label in ["Problem:", "PROBLEM:", "Wirkung:", "WIRKUNG:", "Umsetzung:", "UMSETZUNG:"]:
        # Pattern: label immediately followed by </div> or </p> or whitespace only
        pattern = rf'{re.escape(label)}\s*(?:</(?:div|p|strong|span)[^>]*>|\s*$)'
        label_only_count += len(re.findall(pattern, content, re.IGNORECASE))
    summary["label_only_patterns"] = label_only_count

    return summary


def dump_raw_json(raw_data: Any, context: str = "unknown") -> Optional[str]:
    """
    DUMP POINT 1: Dump raw Quick Wins JSON directly after LLM/parsing.

    Args:
        raw_data: Raw Quick Wins data (could be JSON string, dict, or list)
        context: Description of where this dump is from

    Returns:
        Filepath if dump was successful, None otherwise
    """
    if not _DEBUG_ENABLED:
        return None

    dump_id = _get_dump_id()
    filepath = os.path.join(DEBUG_OUTPUT_DIR, f"debug_quickwins_raw_{dump_id}.json")

    # Prepare content
    if isinstance(raw_data, str):
        # If it's a string, try to parse and pretty-print
        try:
            parsed = json.loads(raw_data)
            content = json.dumps({
                "meta": {
                    "dump_point": "1_RAW_JSON",
                    "context": context,
                    "timestamp": datetime.now().isoformat(),
                    "raw_type": "string_parsed",
                },
                "raw_string": raw_data,
                "parsed_data": parsed,
            }, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            content = json.dumps({
                "meta": {
                    "dump_point": "1_RAW_JSON",
                    "context": context,
                    "timestamp": datetime.now().isoformat(),
                    "raw_type": "string_unparseable",
                },
                "raw_string": raw_data,
            }, indent=2, ensure_ascii=False)
    else:
        content = json.dumps({
            "meta": {
                "dump_point": "1_RAW_JSON",
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "raw_type": type(raw_data).__name__,
            },
            "data": raw_data,
        }, indent=2, ensure_ascii=False, default=str)

    log.info(
        "[QW-DEBUG] DUMP POINT 1 (RAW JSON): context=%s, data_type=%s, len=%d",
        context, type(raw_data).__name__, len(str(raw_data))
    )

    if _safe_write(filepath, content):
        return filepath
    return None


def dump_renderer_output(html: str, renderer_name: str = "unknown") -> Optional[str]:
    """
    DUMP POINT 2: Dump renderer output HTML directly after render_quickwins_*.

    Args:
        html: Rendered HTML output
        renderer_name: Name of the renderer function

    Returns:
        Filepath if dump was successful, None otherwise
    """
    if not _DEBUG_ENABLED:
        return None

    dump_id = _get_dump_id()
    filepath = os.path.join(DEBUG_OUTPUT_DIR, f"debug_quickwins_rendered_{dump_id}.html")

    summary = _extract_quickwins_summary(html)

    # Build annotated HTML with debug header
    header = f"""<!--
==============================================================================
DUMP POINT 2: RENDERER OUTPUT
==============================================================================
Renderer: {renderer_name}
Timestamp: {datetime.now().isoformat()}
Summary:
  - Length: {summary['length']} bytes
  - QuickWin cards: {summary['quickwin_card_count']}
  - Has Problem label: {summary['has_problem_label']}
  - Has Wirkung label: {summary['has_wirkung_label']}
  - Has Umsetzung label: {summary['has_umsetzung_label']}
  - Empty <p> tags: {summary['empty_p_tags']}
  - Label-only patterns: {summary['label_only_patterns']}
==============================================================================
-->
"""
    content = header + html

    log.info(
        "[QW-DEBUG] DUMP POINT 2 (RENDERER OUTPUT): renderer=%s, cards=%d, "
        "empty_p=%d, label_only=%d",
        renderer_name, summary['quickwin_card_count'],
        summary['empty_p_tags'], summary['label_only_patterns']
    )

    if _safe_write(filepath, content):
        return filepath
    return None


def dump_after_section_heal(html: str, segment: str = "unknown") -> Optional[str]:
    """
    DUMP POINT 3: Dump after heal_report_html(sections, segment).

    Args:
        html: HTML content after section healing
        segment: Segment name (SOLO/TEAM/KMU)

    Returns:
        Filepath if dump was successful, None otherwise
    """
    if not _DEBUG_ENABLED:
        return None

    dump_id = _get_dump_id()
    filepath = os.path.join(DEBUG_OUTPUT_DIR, f"debug_quickwins_after_section_heal_{dump_id}.html")

    summary = _extract_quickwins_summary(html)

    header = f"""<!--
==============================================================================
DUMP POINT 3: AFTER SECTION HEAL
==============================================================================
Segment: {segment}
Timestamp: {datetime.now().isoformat()}
Summary:
  - Length: {summary['length']} bytes
  - QuickWin cards: {summary['quickwin_card_count']}
  - Has Problem label: {summary['has_problem_label']}
  - Has Wirkung label: {summary['has_wirkung_label']}
  - Has Umsetzung label: {summary['has_umsetzung_label']}
  - Empty <p> tags: {summary['empty_p_tags']}
  - Label-only patterns: {summary['label_only_patterns']}
==============================================================================
-->
"""
    content = header + html

    log.info(
        "[QW-DEBUG] DUMP POINT 3 (AFTER SECTION HEAL): segment=%s, cards=%d, "
        "empty_p=%d, label_only=%d",
        segment, summary['quickwin_card_count'],
        summary['empty_p_tags'], summary['label_only_patterns']
    )

    if _safe_write(filepath, content):
        return filepath
    return None


def dump_after_final_heal(html: str, segment: str = "unknown") -> Optional[str]:
    """
    DUMP POINT 4: Dump after heal_final_html(final_html, segment).

    Args:
        html: Final HTML content after all healing
        segment: Segment name (SOLO/TEAM/KMU)

    Returns:
        Filepath if dump was successful, None otherwise
    """
    if not _DEBUG_ENABLED:
        return None

    dump_id = _get_dump_id()
    filepath = os.path.join(DEBUG_OUTPUT_DIR, f"debug_quickwins_after_final_heal_{dump_id}.html")

    summary = _extract_quickwins_summary(html)

    # Also check for Governance leaks
    governance_count = len(re.findall(r'\bGovernance\b', html, re.IGNORECASE))

    header = f"""<!--
==============================================================================
DUMP POINT 4: AFTER FINAL HEAL (FINAL OUTPUT)
==============================================================================
Segment: {segment}
Timestamp: {datetime.now().isoformat()}
Summary:
  - Length: {summary['length']} bytes
  - QuickWin cards: {summary['quickwin_card_count']}
  - Has Problem label: {summary['has_problem_label']}
  - Has Wirkung label: {summary['has_wirkung_label']}
  - Has Umsetzung label: {summary['has_umsetzung_label']}
  - Empty <p> tags: {summary['empty_p_tags']}
  - Label-only patterns: {summary['label_only_patterns']}
  - Governance occurrences: {governance_count}

QUALITY CHECKS:
  - [{'PASS' if summary['empty_p_tags'] == 0 else 'FAIL'}] No empty <p> tags
  - [{'PASS' if summary['label_only_patterns'] == 0 else 'FAIL'}] No label-only patterns
  - [{'PASS' if governance_count == 0 else 'FAIL'}] No Governance leaks (SOLO)
==============================================================================
-->
"""
    content = header + html

    log.info(
        "[QW-DEBUG] DUMP POINT 4 (AFTER FINAL HEAL): segment=%s, cards=%d, "
        "empty_p=%d, label_only=%d, governance=%d",
        segment, summary['quickwin_card_count'],
        summary['empty_p_tags'], summary['label_only_patterns'],
        governance_count
    )

    # Log CRITICAL if issues found
    if summary['empty_p_tags'] > 0:
        log.error("[QW-DEBUG] CRITICAL: %d empty <p> tags still present in final output!",
                  summary['empty_p_tags'])
    if summary['label_only_patterns'] > 0:
        log.error("[QW-DEBUG] CRITICAL: %d label-only patterns still present in final output!",
                  summary['label_only_patterns'])
    if governance_count > 0:
        log.error("[QW-DEBUG] CRITICAL: %d Governance occurrences still present in final output!",
                  governance_count)

    if _safe_write(filepath, content):
        return filepath
    return None


def analyze_quickwins_field_status(html: str) -> Dict[str, Any]:
    """
    Analyze Quick Wins HTML for field completeness status.

    Returns detailed analysis of each Quick Win card's field status.
    """
    analysis = {
        "total_cards": 0,
        "cards_with_all_fields": 0,
        "cards_with_empty_fields": 0,
        "field_status": [],
        "issues": [],
    }

    # Find all Quick Win cards
    card_pattern = re.compile(
        r'<div[^>]*class="[^"]*quick-win-card[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        re.DOTALL | re.IGNORECASE
    )

    cards = card_pattern.findall(html)
    analysis["total_cards"] = len(cards)

    for i, card_html in enumerate(cards):
        card_status = {
            "card_index": i + 1,
            "problem_filled": False,
            "wirkung_filled": False,
            "umsetzung_filled": False,
            "issues": [],
        }

        # Check Problem field
        problem_match = re.search(
            r'class="quick-win-problem"[^>]*>.*?<p[^>]*>([^<]+)</p>',
            card_html, re.DOTALL | re.IGNORECASE
        )
        if problem_match and problem_match.group(1).strip():
            card_status["problem_filled"] = True
        else:
            card_status["issues"].append("Empty Problem field")

        # Check Wirkung field
        wirkung_match = re.search(
            r'class="quick-win-wirkung"[^>]*>.*?<p[^>]*>([^<]+)</p>',
            card_html, re.DOTALL | re.IGNORECASE
        )
        if wirkung_match and wirkung_match.group(1).strip():
            card_status["wirkung_filled"] = True
        else:
            card_status["issues"].append("Empty Wirkung field")

        # Check Umsetzung field
        umsetzung_match = re.search(
            r'class="quick-win-umsetzung"[^>]*>.*?<p[^>]*>([^<]+)</p>',
            card_html, re.DOTALL | re.IGNORECASE
        )
        if umsetzung_match and umsetzung_match.group(1).strip():
            card_status["umsetzung_filled"] = True
        else:
            card_status["issues"].append("Empty Umsetzung field")

        # Count complete vs incomplete
        if all([card_status["problem_filled"], card_status["wirkung_filled"], card_status["umsetzung_filled"]]):
            analysis["cards_with_all_fields"] += 1
        else:
            analysis["cards_with_empty_fields"] += 1
            analysis["issues"].extend([f"Card {i+1}: {issue}" for issue in card_status["issues"]])

        analysis["field_status"].append(card_status)

    return analysis


def get_debug_summary() -> Dict[str, Any]:
    """Get summary of debug session."""
    global _dump_counter
    return {
        "enabled": _DEBUG_ENABLED,
        "output_dir": DEBUG_OUTPUT_DIR,
        "dumps_created": _dump_counter,
    }
