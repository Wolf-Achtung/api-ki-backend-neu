#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-529: Open Inputs Marker System

This module provides functionality for handling placeholder markers in reports.
When data is missing from the briefing, markers can be inserted that will be
collected into a dedicated "Offene Inputs" (Open Inputs) page.

Marker Format:
    [INPUT:key|label|hint]

Examples:
    [INPUT:mitarbeiter_count|Mitarbeiterzahl|Bitte im Briefing nachreichen]
    [INPUT:umsatz_jahr|Jahresumsatz|Wird fuer ROI-Berechnung benoetigt]

The markers are:
1. Extracted from all sections
2. Deduplicated by key (first occurrence wins)
3. Rendered as inline placeholders in the text
4. Collected into OPEN_INPUTS_HTML summary page

Version: 1.0.0 (FIX-529)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# MARKER CONFIGURATION
# =============================================================================

# Marker pattern: [INPUT:key|label|hint]
# Using ASCII brackets for compatibility
MARKER_PATTERN = re.compile(
    r'\[INPUT:([a-zA-Z_][a-zA-Z0-9_]*)\|([^|\]]+)\|([^\]]+)\]',
    re.UNICODE
)

# Alternative pattern with Unicode brackets (for manual editing)
MARKER_PATTERN_UNICODE = re.compile(
    r'\u27E6INPUT:([a-zA-Z_][a-zA-Z0-9_]*)\|([^|\u27E7]+)\|([^\u27E7]+)\u27E7',
    re.UNICODE
)


@dataclass
class OpenInputMarker:
    """Represents a single open input marker."""
    key: str
    label: str
    hint: str
    section: str = ""
    line_context: str = ""

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OpenInputMarker):
            return self.key == other.key
        return False


@dataclass
class OpenInputsResult:
    """Result of open inputs extraction."""
    markers: List[OpenInputMarker] = field(default_factory=list)
    sections_with_markers: Dict[str, int] = field(default_factory=dict)
    total_marker_count: int = 0
    unique_marker_count: int = 0


# =============================================================================
# MARKER EXTRACTION
# =============================================================================

def extract_markers_from_text(
    text: str,
    section_name: str = "",
) -> List[OpenInputMarker]:
    """
    Extract all open input markers from a text string.

    Args:
        text: Text to scan for markers
        section_name: Name of the section (for context)

    Returns:
        List of OpenInputMarker objects
    """
    if not text:
        return []

    markers = []

    # Try both ASCII and Unicode patterns
    for pattern in [MARKER_PATTERN, MARKER_PATTERN_UNICODE]:
        for match in pattern.finditer(text):
            key = match.group(1)
            label = match.group(2).strip()
            hint = match.group(3).strip()

            # Get line context (surrounding text)
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].replace('\n', ' ').strip()
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."

            marker = OpenInputMarker(
                key=key,
                label=label,
                hint=hint,
                section=section_name,
                line_context=context,
            )
            markers.append(marker)

    return markers


def extract_markers_from_sections(
    sections: Dict[str, Any],
) -> OpenInputsResult:
    """
    Extract all markers from all sections.

    Args:
        sections: Dict of section_key -> content

    Returns:
        OpenInputsResult with all markers and stats
    """
    all_markers: List[OpenInputMarker] = []
    sections_with_markers: Dict[str, int] = {}

    for section_key, content in sections.items():
        if not isinstance(content, str):
            continue

        markers = extract_markers_from_text(content, section_name=section_key)
        if markers:
            all_markers.extend(markers)
            sections_with_markers[section_key] = len(markers)

    # Deduplicate by key (keep first occurrence)
    seen_keys: set[str] = set()
    unique_markers: List[OpenInputMarker] = []

    for marker in all_markers:
        if marker.key not in seen_keys:
            seen_keys.add(marker.key)
            unique_markers.append(marker)

    result = OpenInputsResult(
        markers=unique_markers,
        sections_with_markers=sections_with_markers,
        total_marker_count=len(all_markers),
        unique_marker_count=len(unique_markers),
    )

    if unique_markers:
        log.info(
            "[FIX-529][OPEN-INPUTS] Extracted %d unique markers from %d sections (total: %d)",
            len(unique_markers),
            len(sections_with_markers),
            len(all_markers),
        )

    return result


# =============================================================================
# INLINE MARKER RENDERING
# =============================================================================

def render_inline_marker(marker: OpenInputMarker) -> str:
    """
    Render a marker as an inline HTML placeholder.

    Args:
        marker: The marker to render

    Returns:
        HTML string for inline display
    """
    return f'''<span class="input-marker" data-key="{marker.key}" title="{marker.hint}">{marker.label}</span>'''


def replace_markers_with_inline(content: str) -> str:
    """
    Replace all markers in content with inline HTML placeholders.

    Args:
        content: Content with markers

    Returns:
        Content with markers replaced by HTML spans
    """
    if not content:
        return content

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        label = match.group(2).strip()
        hint = match.group(3).strip()
        marker = OpenInputMarker(key=key, label=label, hint=hint)
        return render_inline_marker(marker)

    result = MARKER_PATTERN.sub(replacer, content)
    result = MARKER_PATTERN_UNICODE.sub(replacer, result)

    return result


# =============================================================================
# OPEN INPUTS PAGE GENERATION
# =============================================================================

def generate_open_inputs_html(
    result: OpenInputsResult,
    include_section_info: bool = True,
) -> str:
    """
    Generate the OPEN_INPUTS_HTML summary page.

    Args:
        result: OpenInputsResult from extraction
        include_section_info: Whether to include which section each marker is from

    Returns:
        HTML string for the Open Inputs page
    """
    if not result.markers:
        return ""

    # Section labels for display
    section_labels = {
        "EXECUTIVE_SUMMARY_HTML": "Management Summary",
        "QUICK_WINS_HTML": "Quick Wins",
        "ROADMAP_90D_HTML": "90-Tage-Plan",
        "RISKS_HTML": "Risiken",
        "RISKS_LIGHT_HTML": "Risiken",
        "BUSINESS_CASE_HTML": "Business Case",
        "ROI_HTML": "ROI-Berechnung",
    }

    # Build table rows
    rows = []
    for marker in result.markers:
        section_display = section_labels.get(
            marker.section,
            marker.section.replace("_HTML", "").replace("_", " ").title()
        )

        row = f'''
        <tr>
            <td class="label-cell">
                <span class="marker-pill">{marker.label}</span>
            </td>
            <td class="hint-cell">{marker.hint}</td>
            {"<td class='section-cell'>" + section_display + "</td>" if include_section_info else ""}
        </tr>
        '''
        rows.append(row)

    # Build the complete HTML
    section_header = '<th>Sektion</th>' if include_section_info else ''

    html = f'''
    <section class="open-inputs chapter" id="open-inputs">
        <h2>Offene Inputs</h2>
        <p class="section-intro">
            Die folgenden Informationen wurden im Briefing nicht vollstaendig angegeben.
            Bitte ergaenzen Sie diese Daten, um die Analyse zu vervollstaendigen.
        </p>

        <table class="open-inputs-table">
            <thead>
                <tr>
                    <th>Angabe</th>
                    <th>Hinweis</th>
                    {section_header}
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>

        <p class="section-footer">
            Anzahl offener Eingaben: {result.unique_marker_count}
        </p>
    </section>
    '''

    return html


# =============================================================================
# INTEGRATION FUNCTION
# =============================================================================

def process_open_inputs(
    sections: Dict[str, Any],
) -> Tuple[Dict[str, Any], OpenInputsResult]:
    """
    FIX-529: Main integration function for open inputs processing.

    1. Extracts all markers from sections
    2. Replaces markers with inline HTML placeholders
    3. Generates OPEN_INPUTS_HTML page
    4. Returns updated sections and extraction result

    Args:
        sections: Original sections dict

    Returns:
        Tuple of (updated_sections, OpenInputsResult)
    """
    # Step 1: Extract markers
    result = extract_markers_from_sections(sections)

    # Step 2: Replace markers with inline HTML in all sections
    updated = dict(sections)
    for key, content in sections.items():
        if isinstance(content, str) and ('[INPUT:' in content or '\u27E6INPUT:' in content):
            updated[key] = replace_markers_with_inline(content)

    # Step 3: Generate OPEN_INPUTS_HTML if markers exist
    if result.markers:
        updated["OPEN_INPUTS_HTML"] = generate_open_inputs_html(result)
        log.info(
            "[FIX-529][OPEN-INPUTS] Generated OPEN_INPUTS_HTML with %d items",
            result.unique_marker_count
        )
    else:
        # No markers - remove any existing OPEN_INPUTS_HTML
        if "OPEN_INPUTS_HTML" in updated:
            del updated["OPEN_INPUTS_HTML"]
            log.info("[FIX-529][OPEN-INPUTS] No markers found, removed OPEN_INPUTS_HTML")

    return updated, result


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_marker(key: str, label: str, hint: str) -> str:
    """
    Create a marker string for use in content.

    Args:
        key: Unique key for the input
        label: Display label
        hint: Hint text explaining what's needed

    Returns:
        Marker string in the format [INPUT:key|label|hint]
    """
    # Validate key format
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
        raise ValueError(f"Invalid marker key: {key}")

    return f"[INPUT:{key}|{label}|{hint}]"


def has_markers(content: str) -> bool:
    """
    Check if content contains any markers.

    Args:
        content: Text to check

    Returns:
        True if markers are present
    """
    if not content:
        return False
    return bool(MARKER_PATTERN.search(content) or MARKER_PATTERN_UNICODE.search(content))


# =============================================================================
# INITIALIZATION
# =============================================================================

log.info(
    "[FIX-529] open_inputs_marker loaded: extract_markers_from_sections, "
    "process_open_inputs, create_marker"
)
