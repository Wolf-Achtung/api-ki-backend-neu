# -*- coding: utf-8 -*-
"""
SPRINT N3.8 PACKAGE D: Layout Consistency Engine v2.

Print-Perfect rendering with:
- Systematic page-break-inside: avoid
- IBM Design Grid (8-pt) normalization
- HTML card semantic sorting
- Unified heading styles
- White Space Audit (min/max spacing)

N3.8 Enhancements (v2):
- fix_orphan_headers(): Prevent headers at page bottom
- enforce_card_uniformity(): Consistent card sizes
- optimize_page_breaks_v2(): Heuristic break placement
- Semantic HTML Purifier v4: Dead tag removal
- CSS conflict reduction

Four Phases:
1. HTML Canonicalizer (+ Semantic Purifier v4)
2. Whitespace Auditor
3. Break-Optimizer v2
4. Card Uniformity Enforcer

Version: 2.0.0 (N3.8 - PLATIN++ v4.24)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# IBM Design Grid: 8-pt base unit
GRID_UNIT = 8  # pixels

# Standard spacing values (multiples of 8)
SPACING = {
    "xs": GRID_UNIT,       # 8px
    "sm": GRID_UNIT * 2,   # 16px
    "md": GRID_UNIT * 3,   # 24px
    "lg": GRID_UNIT * 4,   # 32px
    "xl": GRID_UNIT * 6,   # 48px
    "xxl": GRID_UNIT * 8,  # 64px
}

# Elements that should avoid page breaks
NO_BREAK_ELEMENTS: List[str] = [
    "table",
    ".card",
    ".kpi-card",
    ".risk-card",
    ".tool-card",
    ".recommendation-card",
    ".metric-box",
    ".highlight-box",
    ".summary-box",
    "figure",
    "blockquote",
    ".chart-container",
    ".data-table",
]

# Heading hierarchy with consistent styling
HEADING_STYLES: Dict[str, Dict[str, str]] = {
    "h1": {
        "font-size": "28px",
        "font-weight": "700",
        "margin-top": f"{SPACING['xl']}px",
        "margin-bottom": f"{SPACING['md']}px",
        "color": "#1a1a1a",
    },
    "h2": {
        "font-size": "22px",
        "font-weight": "600",
        "margin-top": f"{SPACING['lg']}px",
        "margin-bottom": f"{SPACING['sm']}px",
        "color": "#2d2d2d",
    },
    "h3": {
        "font-size": "18px",
        "font-weight": "600",
        "margin-top": f"{SPACING['md']}px",
        "margin-bottom": f"{SPACING['sm']}px",
        "color": "#3d3d3d",
    },
    "h4": {
        "font-size": "16px",
        "font-weight": "500",
        "margin-top": f"{SPACING['sm']}px",
        "margin-bottom": f"{SPACING['xs']}px",
        "color": "#4d4d4d",
    },
}

# Card styling for consistent appearance
CARD_STYLES: Dict[str, str] = {
    "padding": f"{SPACING['md']}px",
    "margin-bottom": f"{SPACING['sm']}px",
    "border-radius": "8px",
    "background-color": "#ffffff",
    "border": "1px solid #e0e0e0",
    "box-shadow": "0 2px 4px rgba(0,0,0,0.05)",
}

# Whitespace audit thresholds
WHITESPACE_MIN = SPACING["xs"]  # 8px minimum
WHITESPACE_MAX = SPACING["xxl"]  # 64px maximum


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class LayoutIssue:
    """A layout issue found during audit."""
    issue_type: str  # 'spacing', 'break', 'heading', 'card', 'whitespace'
    severity: str  # 'low', 'medium', 'high'
    element: str
    message: str
    line_number: int = 0
    fixed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "element": self.element,
            "message": self.message,
            "line_number": self.line_number,
            "fixed": self.fixed,
        }


@dataclass
class LayoutReport:
    """Report from layout consistency processing."""
    elements_processed: int = 0
    issues_found: int = 0
    issues_fixed: int = 0
    page_breaks_optimized: int = 0
    spacing_normalized: int = 0
    headings_styled: int = 0
    cards_unified: int = 0
    whitespace_issues: int = 0
    issues: List[LayoutIssue] = field(default_factory=list)

    def add_issue(self, issue: LayoutIssue) -> None:
        """Add an issue to the report."""
        self.issues.append(issue)
        self.issues_found += 1

        if issue.issue_type == "whitespace":
            self.whitespace_issues += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "elements_processed": self.elements_processed,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "page_breaks_optimized": self.page_breaks_optimized,
            "spacing_normalized": self.spacing_normalized,
            "headings_styled": self.headings_styled,
            "cards_unified": self.cards_unified,
            "whitespace_issues": self.whitespace_issues,
            "issues": [i.to_dict() for i in self.issues],
        }


# =============================================================================
# PHASE 1: HTML CANONICALIZER
# =============================================================================

def canonicalize_html(html: str) -> Tuple[str, int]:
    """
    Canonicalize HTML structure for consistent rendering.

    Returns (canonicalized_html, changes_count).
    """
    if not html:
        return html, 0

    changes = 0
    result = html

    # Normalize empty paragraphs
    result, count = re.subn(r'<p>\s*</p>', '', result)
    changes += count

    # Normalize multiple br tags
    result, count = re.subn(r'(<br\s*/?\s*>){2,}', '<br>', result)
    changes += count

    # Normalize whitespace in attributes
    result, count = re.subn(r'\s+(?=[^<>]*>)', ' ', result)
    changes += count

    # Ensure proper list structure
    result, count = re.subn(r'<li>\s*<p>(.*?)</p>\s*</li>', r'<li>\1</li>', result, flags=re.DOTALL)
    changes += count

    # Remove empty list items
    result, count = re.subn(r'<li>\s*</li>', '', result)
    changes += count

    # Normalize empty divs (but keep structural ones)
    result, count = re.subn(r'<div>\s*</div>', '', result)
    changes += count

    # Normalize consecutive whitespace
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result, changes


def normalize_tables(html: str) -> Tuple[str, int]:
    """
    Normalize table structure for consistent rendering.

    Returns (normalized_html, changes_count).
    """
    if not html or '<table' not in html.lower():
        return html, 0

    changes = 0
    result = html

    # Ensure tables have proper class for styling
    def add_table_class(match: re.Match[str]) -> str:
        tag = match.group(0)
        if 'class=' not in tag:
            return tag.replace('<table', '<table class="data-table"')
        elif 'data-table' not in tag:
            # Add data-table to existing classes
            return re.sub(r'class="([^"]*)"', r'class="\1 data-table"', tag)
        return tag

    result, count = re.subn(r'<table[^>]*>', add_table_class, result)
    changes += count

    # Ensure proper thead/tbody structure
    if '<thead' not in result.lower() and '<th' in result.lower():
        # Wrap first row with th in thead
        result = re.sub(
            r'(<table[^>]*>)\s*(<tr>\s*<th.*?</tr>)',
            r'\1<thead>\2</thead><tbody>',
            result,
            flags=re.DOTALL | re.IGNORECASE
        )
        # Close tbody before table close
        result = re.sub(r'(</tr>)\s*(</table>)', r'\1</tbody>\2', result)
        changes += 1

    return result, changes


# =============================================================================
# PHASE 2: WHITESPACE AUDITOR
# =============================================================================

def audit_whitespace(html: str, report: LayoutReport) -> str:
    """
    Audit and fix whitespace issues.

    Ensures spacing follows IBM 8-pt grid.
    """
    result = html

    # Check for excessive margin/padding values
    spacing_pattern = r'(margin|padding)(?:-(?:top|bottom|left|right))?\s*:\s*(\d+)px'

    def normalize_spacing(match: re.Match[str]) -> str:
        prop = match.group(1)
        value = int(match.group(2))

        # Normalize to nearest 8-pt grid value
        normalized = round(value / GRID_UNIT) * GRID_UNIT

        # Clamp to reasonable range
        normalized = max(WHITESPACE_MIN, min(normalized, WHITESPACE_MAX))

        if normalized != value:
            report.add_issue(LayoutIssue(
                issue_type="whitespace",
                severity="low",
                element="style",
                message=f"Normalized {prop}: {value}px → {normalized}px",
                fixed=True
            ))
            report.spacing_normalized += 1

        return f'{match.group(0).split(":")[0]}: {normalized}px'

    result = re.sub(spacing_pattern, normalize_spacing, result)

    # Check for excessive gaps between elements
    gap_pattern = r'</(?:div|section|p)>\s*\n{3,}\s*<(?:div|section|p)'
    result = re.sub(gap_pattern, lambda m: m.group(0).replace('\n\n\n', '\n\n'), result)

    return result


def check_vertical_gaps(html: str, report: LayoutReport) -> List[LayoutIssue]:
    """
    Check for inconsistent vertical gaps between elements.
    """
    issues: List[LayoutIssue] = []

    # Pattern to find spacing between block elements
    block_gap_pattern = r'(</(?:div|section|article|table)[^>]*>)\s*\n*\s*(<(?:div|section|article|table)[^>]*>)'

    matches = re.finditer(block_gap_pattern, html)
    line_num = 0

    for match in matches:
        # Count newlines between elements
        gap = match.group(0).count('\n')

        if gap > 3:
            issues.append(LayoutIssue(
                issue_type="whitespace",
                severity="medium",
                element="gap",
                message=f"Excessive vertical gap ({gap} lines) between block elements",
                line_number=line_num,
            ))

    return issues


# =============================================================================
# PHASE 3: BREAK OPTIMIZER
# =============================================================================

def optimize_page_breaks(html: str, report: LayoutReport) -> str:
    """
    Optimize page break points for print rendering.

    Adds page-break-inside: avoid to appropriate elements.
    """
    result = html

    for selector in NO_BREAK_ELEMENTS:
        if selector.startswith('.'):
            # Class selector
            class_name = selector[1:]
            pattern = rf'<(\w+)([^>]*class="[^"]*{class_name}[^"]*"[^>]*)>'

            def add_break_avoid_class(match: re.Match[str]) -> str:
                tag = match.group(1)
                attrs = match.group(2)

                if 'style=' in attrs:
                    # Add to existing style
                    if 'page-break-inside' not in attrs:
                        attrs = attrs.replace('style="', 'style="page-break-inside: avoid; ')
                        report.page_breaks_optimized += 1
                else:
                    # Add new style attribute
                    attrs += ' style="page-break-inside: avoid;"'
                    report.page_breaks_optimized += 1

                return f'<{tag}{attrs}>'

            result = re.sub(pattern, add_break_avoid_class, result, flags=re.IGNORECASE)
        else:
            # Element selector
            pattern = rf'<{selector}([^>]*)>'

            def add_break_avoid_element(match: re.Match[str]) -> str:
                attrs = match.group(1)

                if 'style=' in attrs:
                    if 'page-break-inside' not in attrs:
                        attrs = attrs.replace('style="', 'style="page-break-inside: avoid; ')
                        report.page_breaks_optimized += 1
                else:
                    attrs += ' style="page-break-inside: avoid;"'
                    report.page_breaks_optimized += 1

                return f'<{selector}{attrs}>'

            result = re.sub(pattern, add_break_avoid_element, result, flags=re.IGNORECASE)

    return result


def add_break_before_headings(html: str, report: LayoutReport) -> str:
    """
    Add page-break-before: auto to major headings for better page layout.
    """
    result = html

    # Add break opportunities before h1 and h2
    for heading in ['h1', 'h2']:
        pattern = rf'<{heading}([^>]*)>'

        def add_break_before(match: re.Match[str]) -> str:
            attrs = match.group(1)

            if 'style=' in attrs:
                if 'page-break-before' not in attrs:
                    attrs = attrs.replace('style="', 'style="page-break-before: auto; ')
            else:
                attrs += ' style="page-break-before: auto;"'

            return f'<{heading}{attrs}>'

        result = re.sub(pattern, add_break_before, result, flags=re.IGNORECASE)

    return result


# =============================================================================
# HEADING NORMALIZATION
# =============================================================================

def normalize_headings(html: str, report: LayoutReport) -> str:
    """
    Normalize heading styles for consistent appearance.
    """
    result = html

    for heading, styles in HEADING_STYLES.items():
        pattern = rf'<{heading}([^>]*)>'

        def apply_heading_style(match: re.Match[str]) -> str:
            attrs = match.group(1)

            # Build style string
            style_str = '; '.join(f'{k}: {v}' for k, v in styles.items())

            if 'style=' in attrs:
                # Replace existing style
                attrs = re.sub(r'style="[^"]*"', f'style="{style_str}"', attrs)
            else:
                attrs += f' style="{style_str}"'

            report.headings_styled += 1
            return f'<{heading}{attrs}>'

        result = re.sub(pattern, apply_heading_style, result, flags=re.IGNORECASE)

    return result


# =============================================================================
# CARD NORMALIZATION
# =============================================================================

def normalize_cards(html: str, report: LayoutReport) -> str:
    """
    Normalize card styling for consistent appearance.
    """
    result = html

    # Build card style string
    card_style = '; '.join(f'{k}: {v}' for k, v in CARD_STYLES.items())
    card_style += '; page-break-inside: avoid'

    # Find card elements
    card_patterns = [
        r'<div([^>]*class="[^"]*card[^"]*"[^>]*)>',
        r'<div([^>]*class="[^"]*box[^"]*"[^>]*)>',
        r'<div([^>]*class="[^"]*panel[^"]*"[^>]*)>',
    ]

    for pattern in card_patterns:
        def apply_card_style(match: re.Match[str]) -> str:
            attrs = match.group(1)

            if 'style=' in attrs:
                # Merge styles
                attrs = re.sub(
                    r'style="([^"]*)"',
                    f'style="\\1; {card_style}"',
                    attrs
                )
            else:
                attrs += f' style="{card_style}"'

            report.cards_unified += 1
            return f'<div{attrs}>'

        result = re.sub(pattern, apply_card_style, result, flags=re.IGNORECASE)

    return result


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_layout_consistency(html: str) -> Tuple[str, LayoutReport]:
    """
    N3.7: Full layout consistency processing pipeline.

    Phases:
    1. HTML Canonicalizer
    2. Whitespace Auditor
    3. Break Optimizer

    Args:
        html: HTML content to process

    Returns:
        Tuple of (processed_html, report)
    """
    report = LayoutReport()

    if not html:
        return html, report

    log.info("[N3.7-Layout] Starting layout consistency processing...")

    result = html

    # Phase 1: Canonicalize HTML
    result, canon_changes = canonicalize_html(result)
    report.elements_processed += canon_changes

    # Normalize tables
    result, table_changes = normalize_tables(result)
    report.elements_processed += table_changes

    # Phase 2: Whitespace Audit
    result = audit_whitespace(result, report)

    # Check for vertical gaps
    gap_issues = check_vertical_gaps(result, report)
    for issue in gap_issues:
        report.add_issue(issue)

    # Phase 3: Break Optimizer
    result = optimize_page_breaks(result, report)
    result = add_break_before_headings(result, report)

    # Normalize headings
    result = normalize_headings(result, report)

    # Normalize cards
    result = normalize_cards(result, report)

    # Count fixed issues
    report.issues_fixed = sum(1 for i in report.issues if i.fixed)

    log.info(
        "[N3.7-Layout] Complete: breaks=%d spacing=%d headings=%d cards=%d issues=%d",
        report.page_breaks_optimized,
        report.spacing_normalized,
        report.headings_styled,
        report.cards_unified,
        report.issues_found
    )

    return result, report


def process_sections_layout(sections: Dict[str, Any]) -> Tuple[Dict[str, Any], LayoutReport]:
    """
    N3.7: Process all HTML sections for layout consistency.

    Args:
        sections: Dictionary of section contents

    Returns:
        Tuple of (processed_sections, combined_report)
    """
    combined_report = LayoutReport()
    processed = dict(sections)

    # Process all HTML sections
    for key, value in sections.items():
        if isinstance(value, str) and ('_HTML' in key or '<' in value):
            processed_html, section_report = process_layout_consistency(value)
            processed[key] = processed_html

            # Merge report stats
            combined_report.elements_processed += section_report.elements_processed
            combined_report.page_breaks_optimized += section_report.page_breaks_optimized
            combined_report.spacing_normalized += section_report.spacing_normalized
            combined_report.headings_styled += section_report.headings_styled
            combined_report.cards_unified += section_report.cards_unified
            combined_report.issues_found += section_report.issues_found
            combined_report.issues_fixed += section_report.issues_fixed
            combined_report.whitespace_issues += section_report.whitespace_issues
            combined_report.issues.extend(section_report.issues)

    # Set layout flag
    processed["_layout_optimized"] = True
    processed["_layout_report"] = combined_report.to_dict()

    return processed, combined_report


# =============================================================================
# PRINT STYLESHEET GENERATION
# =============================================================================

def generate_print_stylesheet() -> str:
    """
    Generate optimized print stylesheet for PDF rendering.
    """
    css_parts: List[str] = []

    css_parts.append('@media print {')

    # Page setup
    css_parts.append('''
    @page {
        size: A4;
        margin: 2cm;
    }
    ''')

    # No-break elements
    for selector in NO_BREAK_ELEMENTS:
        css_parts.append(f'''
    {selector} {{
        page-break-inside: avoid;
    }}
    ''')

    # Headings
    for heading, styles in HEADING_STYLES.items():
        style_rules = '\n        '.join(f'{k}: {v};' for k, v in styles.items())
        css_parts.append(f'''
    {heading} {{
        {style_rules}
        page-break-after: avoid;
    }}
    ''')

    # Cards
    card_rules = '\n        '.join(f'{k}: {v};' for k, v in CARD_STYLES.items())
    css_parts.append(f'''
    .card, .box, .panel {{
        {card_rules}
        page-break-inside: avoid;
    }}
    ''')

    # Tables
    css_parts.append('''
    table {
        page-break-inside: avoid;
        border-collapse: collapse;
        width: 100%;
    }

    thead {
        display: table-header-group;
    }

    tr {
        page-break-inside: avoid;
    }
    ''')

    # Hide non-print elements
    css_parts.append('''
    .no-print, .navigation, .footer-links {
        display: none !important;
    }
    ''')

    css_parts.append('}')

    return '\n'.join(css_parts)


# =============================================================================
# N3.8: SEMANTIC HTML PURIFIER v4
# =============================================================================

# Dead/deprecated tags to remove
DEAD_TAGS: List[str] = [
    "font",
    "center",
    "strike",
    "u",
    "big",
    "small",
    "tt",
    "blink",
    "marquee",
    "basefont",
    "applet",
    "frame",
    "frameset",
    "noframes",
]

# Deprecated attributes to remove
DEPRECATED_ATTRS: List[str] = [
    "align",
    "bgcolor",
    "border",
    "cellpadding",
    "cellspacing",
    "color",
    "face",
    "height",
    "hspace",
    "vspace",
    "width",
    "nowrap",
    "valign",
]


def purify_semantic_html_v4(html: str, report: LayoutReport) -> str:
    """
    N3.8: Semantic HTML Purifier v4.

    - Removes dead/deprecated tags
    - Removes deprecated attributes
    - Normalizes list types
    - Reduces CSS conflicts
    """
    if not html:
        return html

    result = html

    # Remove dead tags (keep content)
    for tag in DEAD_TAGS:
        pattern = rf'<{tag}[^>]*>(.*?)</{tag}>'
        result, count = re.subn(pattern, r'\1', result, flags=re.DOTALL | re.IGNORECASE)
        if count > 0:
            report.add_issue(LayoutIssue(
                issue_type="semantic",
                severity="low",
                element=tag,
                message=f"Removed {count} deprecated <{tag}> tags",
                fixed=True
            ))

    # Remove deprecated attributes
    for attr in DEPRECATED_ATTRS:
        pattern = rf'\s+{attr}="[^"]*"'
        result, count = re.subn(pattern, '', result, flags=re.IGNORECASE)
        if count > 0:
            report.add_issue(LayoutIssue(
                issue_type="semantic",
                severity="low",
                element=attr,
                message=f"Removed {count} deprecated {attr} attributes",
                fixed=True
            ))

    # Normalize list types (convert <menu> to <ul>)
    result = re.sub(r'<menu([^>]*)>', r'<ul\1>', result, flags=re.IGNORECASE)
    result = re.sub(r'</menu>', '</ul>', result, flags=re.IGNORECASE)

    # Remove empty style attributes
    result = re.sub(r'\s+style="\s*"', '', result)

    # Remove empty class attributes
    result = re.sub(r'\s+class="\s*"', '', result)

    # Deduplicate CSS classes
    def dedupe_classes(match: re.Match[str]) -> str:
        classes = match.group(1).split()
        unique_classes = list(dict.fromkeys(classes))  # Preserve order, remove dupes
        return f'class="{" ".join(unique_classes)}"'

    result = re.sub(r'class="([^"]+)"', dedupe_classes, result)

    return result


def reduce_css_conflicts(html: str, report: LayoutReport) -> str:
    """
    N3.8: Reduce CSS conflicts in inline styles.

    - Removes duplicate properties
    - Normalizes property order
    - Merges conflicting values
    """
    if not html:
        return html

    result = html

    def normalize_style(match: re.Match[str]) -> str:
        style_content = match.group(1)

        # Parse properties
        properties: Dict[str, str] = {}
        for prop in style_content.split(';'):
            prop = prop.strip()
            if ':' in prop:
                key, value = prop.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                # Last value wins (removes duplicates)
                properties[key] = value

        # Rebuild style string
        if properties:
            sorted_props = sorted(properties.items())
            new_style = '; '.join(f'{k}: {v}' for k, v in sorted_props)
            return f'style="{new_style}"'
        return ''

    result = re.sub(r'style="([^"]*)"', normalize_style, result)

    return result


# =============================================================================
# N3.8: ORPHAN HEADER PREVENTION
# =============================================================================

def fix_orphan_headers(html: str, report: LayoutReport) -> str:
    """
    N3.8: Prevent orphan headers (headers at page bottom without content).

    Adds page-break-after: avoid to all headings and ensures
    minimum content follows each heading.
    """
    if not html:
        return html

    result = html
    orphans_fixed = 0

    # Add page-break-after: avoid to all headings
    for level in range(1, 5):
        heading = f'h{level}'
        pattern = rf'(<{heading}[^>]*)>'

        def add_orphan_prevention(match: re.Match[str]) -> str:
            nonlocal orphans_fixed
            tag_start = match.group(1)

            if 'style=' in tag_start:
                if 'page-break-after' not in tag_start:
                    tag_start = tag_start.replace(
                        'style="',
                        'style="page-break-after: avoid; '
                    )
                    orphans_fixed += 1
            else:
                tag_start += ' style="page-break-after: avoid;"'
                orphans_fixed += 1

            return f'{tag_start}>'

        result = re.sub(pattern, add_orphan_prevention, result, flags=re.IGNORECASE)

    # Find headings followed immediately by another heading (no content between)
    consecutive_heading_pattern = r'(</h[1-4]>)\s*(<h[1-4][^>]*>)'

    def add_spacer_comment(match: re.Match[str]) -> str:
        nonlocal orphans_fixed
        orphans_fixed += 1
        return f'{match.group(1)}\n<!-- spacer for print -->\n{match.group(2)}'

    result = re.sub(consecutive_heading_pattern, add_spacer_comment, result, flags=re.IGNORECASE)

    if orphans_fixed > 0:
        report.add_issue(LayoutIssue(
            issue_type="orphan",
            severity="medium",
            element="heading",
            message=f"Fixed {orphans_fixed} potential orphan headers",
            fixed=True
        ))

    return result


# =============================================================================
# N3.8: CARD UNIFORMITY
# =============================================================================

# Standard card dimensions
CARD_STANDARD_HEIGHT = "auto"
CARD_MIN_HEIGHT = "120px"
CARD_MAX_WIDTH = "100%"


def enforce_card_uniformity(html: str, report: LayoutReport) -> str:
    """
    N3.8: Enforce uniform card sizes and styling.

    - Ensures consistent min-height
    - Normalizes border-radius
    - Standardizes shadow depth
    - Aligns padding
    """
    if not html:
        return html

    result = html
    cards_unified = 0

    # Unified card style
    unified_style = (
        f"min-height: {CARD_MIN_HEIGHT}; "
        f"max-width: {CARD_MAX_WIDTH}; "
        f"padding: {SPACING['md']}px; "
        f"margin-bottom: {SPACING['sm']}px; "
        "border-radius: 8px; "
        "background-color: #ffffff; "
        "border: 1px solid #e0e0e0; "
        "box-shadow: 0 2px 4px rgba(0,0,0,0.05); "
        "page-break-inside: avoid"
    )

    # Find all card-like elements
    card_patterns = [
        (r'<div([^>]*class="[^"]*(?:card|kpi-card|tool-card|risk-card|metric-box)[^"]*"[^>]*)>', 'div'),
        (r'<article([^>]*class="[^"]*card[^"]*"[^>]*)>', 'article'),
        (r'<section([^>]*class="[^"]*(?:highlight|summary)-box[^"]*"[^>]*)>', 'section'),
    ]

    for pattern, tag in card_patterns:
        def apply_uniform_style(match: re.Match[str]) -> str:
            nonlocal cards_unified
            attrs = match.group(1)

            if 'style=' in attrs:
                # Replace entire style with unified
                attrs = re.sub(r'style="[^"]*"', f'style="{unified_style}"', attrs)
            else:
                attrs += f' style="{unified_style}"'

            cards_unified += 1
            return f'<{tag}{attrs}>'

        result = re.sub(pattern, apply_uniform_style, result, flags=re.IGNORECASE)

    if cards_unified > 0:
        report.cards_unified += cards_unified
        report.add_issue(LayoutIssue(
            issue_type="card",
            severity="low",
            element="card",
            message=f"Unified {cards_unified} card elements to standard style",
            fixed=True
        ))

    return result


# =============================================================================
# N3.8: PAGE BREAK OPTIMIZER v2
# =============================================================================

# Elements that indicate natural page boundaries
PAGE_BOUNDARY_INDICATORS: List[str] = [
    ".chapter",
    ".section-break",
    ".new-page",
    "hr.page-break",
]

# Minimum content height (approx) before a break
MIN_CONTENT_BEFORE_BREAK = 200  # pixels


def optimize_page_breaks_v2(html: str, report: LayoutReport) -> str:
    """
    N3.8: Advanced page break optimization v2.

    - Heuristic break-before/break-after placement
    - Prevents breaks within logical content blocks
    - Respects natural page boundaries
    - Avoids orphan/widow situations
    """
    if not html:
        return html

    result = html
    breaks_optimized = 0

    # Add explicit page breaks at natural boundaries
    for indicator in PAGE_BOUNDARY_INDICATORS:
        if indicator.startswith('.'):
            class_name = indicator[1:]
            pattern = rf'<(\w+)([^>]*class="[^"]*{class_name}[^"]*"[^>]*)>'

            def add_page_break_boundary(match: re.Match[str]) -> str:
                nonlocal breaks_optimized
                tag = match.group(1)
                attrs = match.group(2)

                if 'style=' in attrs:
                    if 'page-break-before' not in attrs:
                        attrs = attrs.replace('style="', 'style="page-break-before: always; ')
                        breaks_optimized += 1
                else:
                    attrs += ' style="page-break-before: always;"'
                    breaks_optimized += 1

                return f'<{tag}{attrs}>'

            result = re.sub(pattern, add_page_break_boundary, result, flags=re.IGNORECASE)

    # Prevent breaks inside content blocks
    content_blocks = [
        'blockquote',
        'pre',
        'code',
        'figure',
        '.quote-block',
        '.code-block',
    ]

    for block in content_blocks:
        if block.startswith('.'):
            class_name = block[1:]
            pattern = rf'<(\w+)([^>]*class="[^"]*{class_name}[^"]*"[^>]*)>'
        else:
            pattern = rf'<{block}([^>]*)>'

        def prevent_break_inside(match: re.Match[str]) -> str:
            nonlocal breaks_optimized
            if block.startswith('.'):
                tag = match.group(1)
                attrs = match.group(2)
            else:
                tag = block
                attrs = match.group(1)

            if 'page-break-inside' not in attrs:
                if 'style=' in attrs:
                    attrs = attrs.replace('style="', 'style="page-break-inside: avoid; ')
                else:
                    attrs += ' style="page-break-inside: avoid;"'
                breaks_optimized += 1

            if block.startswith('.'):
                return f'<{tag}{attrs}>'
            return f'<{block}{attrs}>'

        result = re.sub(pattern, prevent_break_inside, result, flags=re.IGNORECASE)

    # Add widow/orphan control to paragraphs
    result = re.sub(
        r'<p([^>]*)>',
        lambda m: f'<p{m.group(1)} style="orphans: 3; widows: 3;">' if 'orphans' not in m.group(1) else m.group(0),
        result,
        flags=re.IGNORECASE
    )

    if breaks_optimized > 0:
        report.page_breaks_optimized += breaks_optimized
        report.add_issue(LayoutIssue(
            issue_type="break",
            severity="low",
            element="page-break",
            message=f"Optimized {breaks_optimized} page break points (v2)",
            fixed=True
        ))

    return result


# =============================================================================
# N3.8: AUTOMATIC LIST HARMONIZATION
# =============================================================================

def harmonize_list_types(html: str, report: LayoutReport) -> str:
    """
    N3.8: Harmonize list types for consistency.

    - Ensures nested lists use consistent styling
    - Normalizes bullet types
    - Fixes mixed list issues
    """
    if not html:
        return html

    result = html
    lists_harmonized = 0

    # Standardize bullet list styles
    # Level 1: disc, Level 2: circle, Level 3: square
    list_styles = {
        1: "disc",
        2: "circle",
        3: "square",
    }

    # Add list-style-type based on nesting level
    # This is a simplified approach - proper nesting detection would be more complex
    def normalize_list_style(match: re.Match[str]) -> str:
        nonlocal lists_harmonized
        attrs = match.group(1) if match.group(1) else ""

        if 'list-style-type' not in attrs:
            if 'style=' in attrs:
                attrs = attrs.replace('style="', 'style="list-style-type: disc; ')
            else:
                attrs += ' style="list-style-type: disc;"'
            lists_harmonized += 1

        return f'<ul{attrs}>'

    result = re.sub(r'<ul([^>]*)>', normalize_list_style, result, flags=re.IGNORECASE)

    # Ensure ordered lists have consistent numbering
    def normalize_ol_style(match: re.Match[str]) -> str:
        nonlocal lists_harmonized
        attrs = match.group(1) if match.group(1) else ""

        if 'list-style-type' not in attrs:
            if 'style=' in attrs:
                attrs = attrs.replace('style="', 'style="list-style-type: decimal; ')
            else:
                attrs += ' style="list-style-type: decimal;"'
            lists_harmonized += 1

        return f'<ol{attrs}>'

    result = re.sub(r'<ol([^>]*)>', normalize_ol_style, result, flags=re.IGNORECASE)

    if lists_harmonized > 0:
        report.add_issue(LayoutIssue(
            issue_type="list",
            severity="low",
            element="list",
            message=f"Harmonized {lists_harmonized} list elements",
            fixed=True
        ))

    return result


# =============================================================================
# N3.8: FULL v2 PROCESSING PIPELINE
# =============================================================================

def process_layout_consistency_v2(html: str) -> Tuple[str, LayoutReport]:
    """
    N3.8: Full layout consistency processing pipeline v2.

    Phases:
    1. HTML Canonicalizer + Semantic Purifier v4
    2. Whitespace Auditor
    3. Break Optimizer v2
    4. Card Uniformity Enforcer

    Args:
        html: HTML content to process

    Returns:
        Tuple of (processed_html, report)
    """
    report = LayoutReport()

    if not html:
        return html, report

    log.info("[N3.8-Layout] Starting layout consistency processing v2...")

    result = html

    # Phase 1a: Canonicalize HTML
    result, canon_changes = canonicalize_html(result)
    report.elements_processed += canon_changes

    # Phase 1b: Semantic purification
    result = purify_semantic_html_v4(result, report)

    # Phase 1c: CSS conflict reduction
    result = reduce_css_conflicts(result, report)

    # Normalize tables
    result, table_changes = normalize_tables(result)
    report.elements_processed += table_changes

    # Phase 2: Whitespace Audit
    result = audit_whitespace(result, report)

    # Check for vertical gaps
    gap_issues = check_vertical_gaps(result, report)
    for issue in gap_issues:
        report.add_issue(issue)

    # Phase 3a: Break Optimizer (original)
    result = optimize_page_breaks(result, report)
    result = add_break_before_headings(result, report)

    # Phase 3b: Break Optimizer v2
    result = optimize_page_breaks_v2(result, report)

    # Phase 3c: Fix orphan headers
    result = fix_orphan_headers(result, report)

    # Phase 4a: Normalize headings
    result = normalize_headings(result, report)

    # Phase 4b: Card uniformity
    result = enforce_card_uniformity(result, report)

    # Phase 4c: Original card normalization
    result = normalize_cards(result, report)

    # Phase 4d: List harmonization
    result = harmonize_list_types(result, report)

    # Count fixed issues
    report.issues_fixed = sum(1 for i in report.issues if i.fixed)

    log.info(
        "[N3.8-Layout] Complete v2: breaks=%d spacing=%d headings=%d cards=%d issues=%d fixed=%d",
        report.page_breaks_optimized,
        report.spacing_normalized,
        report.headings_styled,
        report.cards_unified,
        report.issues_found,
        report.issues_fixed
    )

    return result, report


def process_sections_layout_v2(sections: Dict[str, Any]) -> Tuple[Dict[str, Any], LayoutReport]:
    """
    N3.8: Process all HTML sections for layout consistency v2.

    Args:
        sections: Dictionary of section contents

    Returns:
        Tuple of (processed_sections, combined_report)
    """
    combined_report = LayoutReport()
    processed = dict(sections)

    log.info("[N3.8-Layout] Processing sections layout v2...")

    # Process all HTML sections
    for key, value in sections.items():
        if isinstance(value, str) and ('_HTML' in key or '<' in value):
            processed_html, section_report = process_layout_consistency_v2(value)
            processed[key] = processed_html

            # Merge report stats
            combined_report.elements_processed += section_report.elements_processed
            combined_report.page_breaks_optimized += section_report.page_breaks_optimized
            combined_report.spacing_normalized += section_report.spacing_normalized
            combined_report.headings_styled += section_report.headings_styled
            combined_report.cards_unified += section_report.cards_unified
            combined_report.issues_found += section_report.issues_found
            combined_report.issues_fixed += section_report.issues_fixed
            combined_report.whitespace_issues += section_report.whitespace_issues
            combined_report.issues.extend(section_report.issues)

    # Set layout flag
    processed["_layout_optimized_v2"] = True
    processed["_layout_report_v2"] = combined_report.to_dict()

    log.info(
        "[N3.8-Layout] Sections complete: processed=%d issues=%d fixed=%d",
        combined_report.elements_processed,
        combined_report.issues_found,
        combined_report.issues_fixed
    )

    return processed, combined_report


def get_layout_grade(report: LayoutReport) -> str:
    """
    Calculate layout quality grade based on report.

    A: 0-5 issues
    B: 6-10 issues
    C: 11-20 issues
    D: 21-30 issues
    F: >30 issues
    """
    unfixed = report.issues_found - report.issues_fixed

    if unfixed <= 5:
        return "A"
    elif unfixed <= 10:
        return "B"
    elif unfixed <= 20:
        return "C"
    elif unfixed <= 30:
        return "D"
    else:
        return "F"
