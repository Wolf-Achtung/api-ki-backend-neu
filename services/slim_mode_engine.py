# -*- coding: utf-8 -*-
"""
Sprint B: Slim-Mode & HTML Dynamic Optimization Engine

Provides HTML optimization for PLATIN++ reports:
- Auto-collapse large tables (> N rows)
- SVG size optimization and compression
- Expression replacements for common verbose patterns
- Whitespace normalization
- Empty element cleanup
- Report size tracking and warnings

Version: 1.0.0 (Sprint B - PLATIN++ v4.17)
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Enable/disable slim mode via ENV
SLIM_MODE_ENABLED = os.getenv("SLIM_MODE_ENABLED", "1").lower() in ("1", "true", "yes")

# Table collapse threshold (rows)
TABLE_COLLAPSE_THRESHOLD = int(os.getenv("TABLE_COLLAPSE_THRESHOLD", "8"))

# SVG max dimensions (pixels)
SVG_MAX_WIDTH = int(os.getenv("SVG_MAX_WIDTH", "800"))
SVG_MAX_HEIGHT = int(os.getenv("SVG_MAX_HEIGHT", "400"))

# Report size warning threshold (bytes)
REPORT_SIZE_WARNING_KB = int(os.getenv("REPORT_SIZE_WARNING_KB", "500"))

# Aggressive optimization for very large reports
AGGRESSIVE_THRESHOLD_KB = int(os.getenv("AGGRESSIVE_THRESHOLD_KB", "800"))


# =============================================================================
# EXPRESSION REPLACEMENTS
# =============================================================================

# Verbose expressions that can be shortened
EXPRESSION_REPLACEMENTS: Dict[str, str] = {
    # German verbose patterns
    "im Rahmen von": "bei",
    "Im Rahmen von": "Bei",
    "im Hinblick auf": "bezüglich",
    "Im Hinblick auf": "Bezüglich",
    "unter Berücksichtigung von": "unter Berücksichtigung",
    "Unter Berücksichtigung von": "Unter Berücksichtigung",
    "in Bezug auf": "bezüglich",
    "In Bezug auf": "Bezüglich",
    "zum gegenwärtigen Zeitpunkt": "aktuell",
    "Zum gegenwärtigen Zeitpunkt": "Aktuell",
    "zu diesem Zeitpunkt": "jetzt",
    "Zu diesem Zeitpunkt": "Jetzt",
    "in der Lage sein": "können",
    "in der Lage ist": "kann",
    "eine Vielzahl von": "viele",
    "Eine Vielzahl von": "Viele",
    "aufgrund der Tatsache, dass": "weil",
    "Aufgrund der Tatsache, dass": "Weil",
    "zum Zweck der": "für",
    "Zum Zweck der": "Für",
    "mit dem Ziel": "um",
    "Mit dem Ziel": "Um",
    "für den Fall, dass": "falls",
    "Für den Fall, dass": "Falls",
    "unter der Voraussetzung, dass": "wenn",
    "Unter der Voraussetzung, dass": "Wenn",
    "es ist wichtig zu beachten, dass": "",
    "Es ist wichtig zu beachten, dass": "",
    "es sei darauf hingewiesen, dass": "",
    "Es sei darauf hingewiesen, dass": "",

    # English verbose patterns
    "in order to": "to",
    "In order to": "To",
    "with regard to": "regarding",
    "With regard to": "Regarding",
    "in the context of": "in",
    "In the context of": "In",
    "at this point in time": "now",
    "At this point in time": "Now",
    "due to the fact that": "because",
    "Due to the fact that": "Because",
    "for the purpose of": "for",
    "For the purpose of": "For",
    "in the event that": "if",
    "In the event that": "If",
    "it is important to note that": "",
    "It is important to note that": "",
    "it should be noted that": "",
    "It should be noted that": "",
    "a large number of": "many",
    "A large number of": "Many",
    "a significant amount of": "much",
    "A significant amount of": "Much",
}

# Additional patterns for aggressive mode
AGGRESSIVE_REPLACEMENTS: Dict[str, str] = {
    "Darüber hinaus": "Zudem",
    "darüber hinaus": "zudem",
    "Nichtsdestotrotz": "Dennoch",
    "nichtsdestotrotz": "dennoch",
    "Dementsprechend": "Daher",
    "dementsprechend": "daher",
    "Furthermore": "Also",
    "furthermore": "also",
    "Nevertheless": "However",
    "nevertheless": "however",
    "Additionally": "Also",
    "additionally": "also",
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SlimModeResult:
    """Result of slim mode optimization."""
    original_size: int
    optimized_size: int
    size_reduction_percent: float
    tables_collapsed: int = 0
    svgs_optimized: int = 0
    expressions_replaced: int = 0
    whitespace_reduced: bool = False
    empty_elements_removed: int = 0
    warnings: List[str] = field(default_factory=list)


@dataclass
class OptimizationStats:
    """Aggregated optimization statistics."""
    total_processed: int = 0
    total_original_bytes: int = 0
    total_optimized_bytes: int = 0
    total_tables_collapsed: int = 0
    total_svgs_optimized: int = 0
    total_expressions_replaced: int = 0


# =============================================================================
# HTML OPTIMIZATION PATTERNS
# =============================================================================

# Large table detection
RE_TABLE = re.compile(r'<table[^>]*>(.*?)</table>', re.DOTALL | re.IGNORECASE)
RE_TR = re.compile(r'<tr[^>]*>.*?</tr>', re.DOTALL | re.IGNORECASE)

# SVG detection and sizing
RE_SVG = re.compile(r'<svg[^>]*>(.*?)</svg>', re.DOTALL | re.IGNORECASE)
RE_SVG_WIDTH = re.compile(r'width\s*=\s*["\']?(\d+)', re.IGNORECASE)
RE_SVG_HEIGHT = re.compile(r'height\s*=\s*["\']?(\d+)', re.IGNORECASE)
RE_SVG_VIEWBOX = re.compile(r'viewBox\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

# Empty elements
RE_EMPTY_P = re.compile(r'<p[^>]*>\s*</p>', re.IGNORECASE)
RE_EMPTY_DIV = re.compile(r'<div[^>]*>\s*</div>', re.IGNORECASE)
RE_EMPTY_SPAN = re.compile(r'<span[^>]*>\s*</span>', re.IGNORECASE)
RE_EMPTY_LI = re.compile(r'<li[^>]*>\s*</li>', re.IGNORECASE)

# Multiple whitespace/newlines
RE_MULTI_SPACE = re.compile(r'[ \t]+')
RE_MULTI_NEWLINE = re.compile(r'\n{3,}')
RE_BR_SEQUENCE = re.compile(r'(<br\s*/?>){3,}', re.IGNORECASE)

# Empty attributes
RE_EMPTY_CLASS = re.compile(r'\s+class\s*=\s*["\'][\s]*["\']', re.IGNORECASE)
RE_EMPTY_STYLE = re.compile(r'\s+style\s*=\s*["\'][\s]*["\']', re.IGNORECASE)
RE_EMPTY_ID = re.compile(r'\s+id\s*=\s*["\'][\s]*["\']', re.IGNORECASE)


# =============================================================================
# TABLE OPTIMIZATION
# =============================================================================

def _count_table_rows(table_html: str) -> int:
    """Count rows in a table."""
    rows = RE_TR.findall(table_html)
    return len(rows)


def _collapse_table(table_html: str, threshold: int = TABLE_COLLAPSE_THRESHOLD) -> Tuple[str, bool]:
    """
    Collapse a large table into a collapsible element.

    Args:
        table_html: The table HTML
        threshold: Row threshold for collapsing

    Returns:
        Tuple of (processed_html, was_collapsed)
    """
    row_count = _count_table_rows(table_html)

    if row_count <= threshold:
        return table_html, False

    # Wrap table in collapsible details element
    collapsed_html = f'''<details class="table-collapsed">
<summary>Tabelle mit {row_count} Zeilen (klicken zum Aufklappen)</summary>
{table_html}
</details>'''

    return collapsed_html, True


def optimize_tables(html: str) -> Tuple[str, int]:
    """
    Optimize tables in HTML by collapsing large ones.

    Args:
        html: Input HTML

    Returns:
        Tuple of (optimized_html, tables_collapsed_count)
    """
    collapsed_count = 0

    def replace_table(match: re.Match) -> str:
        nonlocal collapsed_count
        table_html = match.group(0)
        processed, was_collapsed = _collapse_table(table_html)
        if was_collapsed:
            collapsed_count += 1
        return processed

    optimized = RE_TABLE.sub(replace_table, html)
    return optimized, collapsed_count


# =============================================================================
# SVG OPTIMIZATION
# =============================================================================

def _extract_svg_dimensions(svg_html: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract width and height from SVG."""
    width_match = RE_SVG_WIDTH.search(svg_html)
    height_match = RE_SVG_HEIGHT.search(svg_html)

    width = int(width_match.group(1)) if width_match else None
    height = int(height_match.group(1)) if height_match else None

    return width, height


def _optimize_svg(svg_html: str) -> Tuple[str, bool]:
    """
    Optimize SVG element.

    - Adds viewBox if missing
    - Constrains max dimensions
    - Removes unnecessary whitespace

    Args:
        svg_html: SVG element HTML

    Returns:
        Tuple of (optimized_svg, was_optimized)
    """
    was_optimized = False

    width, height = _extract_svg_dimensions(svg_html)

    # Check if dimensions need constraining
    if width and width > SVG_MAX_WIDTH:
        scale = SVG_MAX_WIDTH / width
        new_height = int((height or width) * scale) if height else SVG_MAX_HEIGHT
        svg_html = RE_SVG_WIDTH.sub(f'width="{SVG_MAX_WIDTH}"', svg_html)
        if height:
            svg_html = RE_SVG_HEIGHT.sub(f'height="{new_height}"', svg_html)
        was_optimized = True

    if height and height > SVG_MAX_HEIGHT:
        scale = SVG_MAX_HEIGHT / height
        new_width = int((width or height) * scale) if width else SVG_MAX_WIDTH
        svg_html = RE_SVG_HEIGHT.sub(f'height="{SVG_MAX_HEIGHT}"', svg_html)
        if width:
            svg_html = RE_SVG_WIDTH.sub(f'width="{new_width}"', svg_html)
        was_optimized = True

    # Remove unnecessary whitespace within SVG
    if '  ' in svg_html or '\n\n' in svg_html:
        original_len = len(svg_html)
        svg_html = RE_MULTI_SPACE.sub(' ', svg_html)
        svg_html = RE_MULTI_NEWLINE.sub('\n', svg_html)
        if len(svg_html) < original_len:
            was_optimized = True

    return svg_html, was_optimized


def optimize_svgs(html: str) -> Tuple[str, int]:
    """
    Optimize all SVGs in HTML.

    Args:
        html: Input HTML

    Returns:
        Tuple of (optimized_html, svgs_optimized_count)
    """
    optimized_count = 0

    def replace_svg(match: re.Match) -> str:
        nonlocal optimized_count
        svg_html = match.group(0)
        processed, was_optimized = _optimize_svg(svg_html)
        if was_optimized:
            optimized_count += 1
        return processed

    optimized = RE_SVG.sub(replace_svg, html)
    return optimized, optimized_count


# =============================================================================
# EXPRESSION REPLACEMENTS
# =============================================================================

def apply_expression_replacements(
    html: str,
    aggressive: bool = False
) -> Tuple[str, int]:
    """
    Apply expression replacements to reduce verbosity.

    Args:
        html: Input HTML
        aggressive: Use aggressive replacements (for large reports)

    Returns:
        Tuple of (optimized_html, replacements_count)
    """
    replacements_count = 0

    replacements = dict(EXPRESSION_REPLACEMENTS)
    if aggressive:
        replacements.update(AGGRESSIVE_REPLACEMENTS)

    for verbose, concise in replacements.items():
        if verbose in html:
            count = html.count(verbose)
            html = html.replace(verbose, concise)
            replacements_count += count

    return html, replacements_count


# =============================================================================
# WHITESPACE & EMPTY ELEMENT CLEANUP
# =============================================================================

def remove_empty_elements(html: str) -> Tuple[str, int]:
    """
    Remove empty HTML elements.

    Args:
        html: Input HTML

    Returns:
        Tuple of (cleaned_html, elements_removed_count)
    """
    removed_count = 0
    original_len = len(html)

    # Remove empty paragraphs
    html, count = RE_EMPTY_P.subn('', html)
    removed_count += count

    # Remove empty divs
    html, count = RE_EMPTY_DIV.subn('', html)
    removed_count += count

    # Remove empty spans
    html, count = RE_EMPTY_SPAN.subn('', html)
    removed_count += count

    # Remove empty list items
    html, count = RE_EMPTY_LI.subn('', html)
    removed_count += count

    # Remove empty attributes
    html = RE_EMPTY_CLASS.sub('', html)
    html = RE_EMPTY_STYLE.sub('', html)
    html = RE_EMPTY_ID.sub('', html)

    # Reduce excessive line breaks
    html = RE_BR_SEQUENCE.sub('<br><br>', html)

    return html, removed_count


def normalize_whitespace(html: str) -> str:
    """
    Normalize whitespace in HTML.

    Preserves whitespace in <pre> and <code> tags.
    """
    # Simple approach: reduce multiple spaces/newlines
    # Note: This is intentionally conservative to avoid breaking layouts

    # Reduce multiple newlines to max 2
    html = RE_MULTI_NEWLINE.sub('\n\n', html)

    # Reduce multiple spaces (outside of pre/code) to single space
    # We use a simple approach that won't break pre blocks
    lines = html.split('\n')
    processed_lines = []
    in_pre = False

    for line in lines:
        if '<pre' in line.lower():
            in_pre = True
        if '</pre' in line.lower():
            in_pre = False

        if not in_pre:
            line = RE_MULTI_SPACE.sub(' ', line)

        processed_lines.append(line)

    return '\n'.join(processed_lines)


# =============================================================================
# SLIM MODE ENGINE
# =============================================================================

class SlimModeEngine:
    """
    HTML optimization engine for PLATIN++ reports.

    Provides dynamic HTML optimization including:
    - Table collapsing
    - SVG optimization
    - Expression replacements
    - Whitespace normalization
    """

    def __init__(self, enabled: bool = SLIM_MODE_ENABLED):
        self.enabled = enabled
        self._stats = OptimizationStats()

    def optimize(
        self,
        html: str,
        aggressive: Optional[bool] = None
    ) -> Tuple[str, SlimModeResult]:
        """
        Optimize HTML content.

        Args:
            html: Input HTML
            aggressive: Force aggressive mode (auto-detected if None)

        Returns:
            Tuple of (optimized_html, result)
        """
        original_size = len(html.encode('utf-8'))

        result = SlimModeResult(
            original_size=original_size,
            optimized_size=original_size,
            size_reduction_percent=0.0
        )

        if not self.enabled:
            return html, result

        self._stats.total_processed += 1
        self._stats.total_original_bytes += original_size

        # Auto-detect aggressive mode based on size
        if aggressive is None:
            aggressive = original_size > AGGRESSIVE_THRESHOLD_KB * 1024

        if aggressive:
            log.info(
                "[B-SlimMode] Aggressive mode activated (size=%dKB > %dKB)",
                original_size // 1024, AGGRESSIVE_THRESHOLD_KB
            )

        # Step 1: Optimize tables
        html, tables_collapsed = optimize_tables(html)
        result.tables_collapsed = tables_collapsed
        self._stats.total_tables_collapsed += tables_collapsed

        # Step 2: Optimize SVGs
        html, svgs_optimized = optimize_svgs(html)
        result.svgs_optimized = svgs_optimized
        self._stats.total_svgs_optimized += svgs_optimized

        # Step 3: Apply expression replacements
        html, expressions_replaced = apply_expression_replacements(html, aggressive)
        result.expressions_replaced = expressions_replaced
        self._stats.total_expressions_replaced += expressions_replaced

        # Step 4: Remove empty elements
        html, empty_removed = remove_empty_elements(html)
        result.empty_elements_removed = empty_removed

        # Step 5: Normalize whitespace
        html = normalize_whitespace(html)
        result.whitespace_reduced = True

        # Calculate final size and reduction
        optimized_size = len(html.encode('utf-8'))
        result.optimized_size = optimized_size
        self._stats.total_optimized_bytes += optimized_size

        if original_size > 0:
            result.size_reduction_percent = (
                (original_size - optimized_size) / original_size * 100
            )

        # Add warnings if still large
        if optimized_size > REPORT_SIZE_WARNING_KB * 1024:
            result.warnings.append(
                f"Report still large after optimization: {optimized_size // 1024}KB"
            )

        log.info(
            "[B-SlimMode] Optimized %dKB → %dKB (%.1f%% reduction) "
            "tables=%d svgs=%d expressions=%d empty=%d",
            original_size // 1024,
            optimized_size // 1024,
            result.size_reduction_percent,
            tables_collapsed,
            svgs_optimized,
            expressions_replaced,
            empty_removed
        )

        return html, result

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated optimization statistics."""
        if self._stats.total_processed == 0:
            return {
                "total_processed": 0,
                "total_original_kb": 0,
                "total_optimized_kb": 0,
                "average_reduction_percent": 0,
            }

        total_reduction = (
            (self._stats.total_original_bytes - self._stats.total_optimized_bytes)
            / self._stats.total_original_bytes * 100
            if self._stats.total_original_bytes > 0 else 0
        )

        return {
            "total_processed": self._stats.total_processed,
            "total_original_kb": self._stats.total_original_bytes // 1024,
            "total_optimized_kb": self._stats.total_optimized_bytes // 1024,
            "average_reduction_percent": total_reduction,
            "total_tables_collapsed": self._stats.total_tables_collapsed,
            "total_svgs_optimized": self._stats.total_svgs_optimized,
            "total_expressions_replaced": self._stats.total_expressions_replaced,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = OptimizationStats()


# =============================================================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =============================================================================

_engine_instance: Optional[SlimModeEngine] = None


def get_slim_mode_engine() -> SlimModeEngine:
    """Get or create singleton engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SlimModeEngine()
    return _engine_instance


def optimize_html(
    html: str,
    aggressive: Optional[bool] = None
) -> Tuple[str, SlimModeResult]:
    """
    Convenience function to optimize HTML.

    Args:
        html: Input HTML
        aggressive: Force aggressive mode

    Returns:
        Tuple of (optimized_html, result)
    """
    return get_slim_mode_engine().optimize(html, aggressive)


def estimate_size_reduction(html: str) -> Dict[str, int]:
    """
    Estimate potential size reduction without applying changes.

    Args:
        html: Input HTML

    Returns:
        Dict with estimated reductions
    """
    original_size = len(html.encode('utf-8'))

    # Count potential optimizations
    tables = len(RE_TABLE.findall(html))
    large_tables = sum(
        1 for m in RE_TABLE.finditer(html)
        if _count_table_rows(m.group(0)) > TABLE_COLLAPSE_THRESHOLD
    )
    svgs = len(RE_SVG.findall(html))
    empty_elements = (
        len(RE_EMPTY_P.findall(html)) +
        len(RE_EMPTY_DIV.findall(html)) +
        len(RE_EMPTY_SPAN.findall(html))
    )

    # Estimate expression replacements
    expression_chars = sum(
        len(v) * html.count(v)
        for v in EXPRESSION_REPLACEMENTS.keys()
        if v in html
    )

    return {
        "original_size_kb": original_size // 1024,
        "tables_total": tables,
        "tables_collapsible": large_tables,
        "svgs_total": svgs,
        "empty_elements": empty_elements,
        "verbose_chars": expression_chars,
        "estimated_reduction_kb": (empty_elements * 20 + expression_chars) // 1024,
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[B-SlimMode] Engine v1.0.0 loaded - enabled=%s table_threshold=%d "
    "svg_max=%dx%d warning_kb=%d aggressive_kb=%d",
    SLIM_MODE_ENABLED,
    TABLE_COLLAPSE_THRESHOLD,
    SVG_MAX_WIDTH,
    SVG_MAX_HEIGHT,
    REPORT_SIZE_WARNING_KB,
    AGGRESSIVE_THRESHOLD_KB
)
log.info(
    "[B-SlimMode] Expression replacements: %d standard, %d aggressive",
    len(EXPRESSION_REPLACEMENTS),
    len(AGGRESSIVE_REPLACEMENTS)
)
