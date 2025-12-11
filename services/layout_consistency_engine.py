# -*- coding: utf-8 -*-
"""
SPRINT N3.7 PACKAGE C: Layout Consistency Engine.

Print-Perfect rendering with:
- Systematic page-break-inside: avoid
- IBM Design Grid (8-pt) normalization
- HTML card semantic sorting
- Unified heading styles
- White Space Audit (min/max spacing)

Three Phases:
1. HTML Canonicalizer
2. Whitespace Auditor
3. Break-Optimizer

Version: 1.0.0 (N3.7 - PLATIN++ v4.23 RC)
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
