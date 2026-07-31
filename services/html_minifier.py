# -*- coding: utf-8 -*-
"""
HTML & CSS Minifier for PDF Generation.

Reduces PDF file size by:
- Collapsing whitespace in HTML
- Minifying CSS (remove comments, duplicate declarations)
- Stripping unused sections and debug elements

Version: 1.1.0 PDF-SLIMDOWN + G14-D Performance
Sprint G14-D: Added compiled regex caching for performance.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Set, Pattern

log = logging.getLogger(__name__)


# =============================================================================
# SPRINT G14-D: Compiled Regex Cache
# =============================================================================
# Pre-compile frequently used regex patterns to avoid recompilation overhead.
# Using lru_cache for patterns that need dynamic flags.

@lru_cache(maxsize=64)
def _get_compiled_pattern(pattern: str, flags: int = 0) -> Pattern:
    """
    Get compiled regex pattern from cache.

    SPRINT G14-D: Caches compiled patterns to avoid repeated compilation
    overhead during high-volume PDF generation.
    """
    return re.compile(pattern, flags)


# Pre-compiled patterns for HTML compression
# KIS-1275: ksj-lang-failopen-Marker gewhitelistet — der Sanitize-Hook in
# report_renderer läuft NACH der Minifizierung und braucht den Marker, um
# fail-open-Sektionen des EN-Sprachgates zu überspringen.
_RE_HTML_COMMENTS = re.compile(r'<!--(?!\[if)(?!/?ksj-lang-failopen).*?-->', re.DOTALL)
_RE_MULTIPLE_SPACES = re.compile(r'[ \t]+')
_RE_TAG_WHITESPACE = re.compile(r'>\s+<')
_RE_LEADING_WHITESPACE = re.compile(r'^\s+', re.MULTILINE)
_RE_TRAILING_WHITESPACE = re.compile(r'\s+$', re.MULTILINE)
_RE_MULTIPLE_NEWLINES = re.compile(r'\n{2,}')
_RE_EMPTY_LINES = re.compile(r'\n\s*\n')
_RE_P_START_WHITESPACE = re.compile(r'<p>\s+')
_RE_P_END_WHITESPACE = re.compile(r'\s+</p>')
_RE_EMPTY_ID_DOUBLE = re.compile(r'\s+id="\s*"')
_RE_EMPTY_ID_SINGLE = re.compile(r"\s+id='\s*'")

# Pre-compiled patterns for CSS minification
_RE_CSS_COMMENTS = re.compile(r'/\*.*?\*/', re.DOTALL)
_RE_CSS_BRACE_OPEN = re.compile(r'\s*{\s*')
_RE_CSS_BRACE_CLOSE = re.compile(r'\s*}\s*')
_RE_CSS_SEMICOLON = re.compile(r'\s*;\s*')
_RE_CSS_COLON = re.compile(r'\s*:\s*')
_RE_CSS_MULTI_SPACE = re.compile(r'\s{2,}')
_RE_CSS_RULE = re.compile(r'([^{]+)\{([^}]*)\}')

# Pre-compiled patterns for section stripping
_RE_DEBUG_DIV = re.compile(r'<div[^>]*class="[^"]*debug[^"]*"[^>]*>.*?</div>', re.DOTALL | re.IGNORECASE)
_RE_EMPTY_SECTION = re.compile(r'<section[^>]*>\s*(<h[1-6][^>]*>\s*</h[1-6]>\s*)*\s*</section>', re.DOTALL | re.IGNORECASE)
_RE_PLACEHOLDER_DIV = re.compile(r'<div[^>]*class="[^"]*(?:placeholder|empty|unused)[^"]*"[^>]*>\s*</div>', re.DOTALL | re.IGNORECASE)
_RE_EMPTY_FUNDING = re.compile(r'<div[^>]*class="[^"]*funding[^"]*"[^>]*>\s*</div>', re.DOTALL | re.IGNORECASE)
_RE_FUNDING_PLACEHOLDER = re.compile(r'<section[^>]*>\s*\{\{FUNDING_HTML\}\}\s*</section>', re.DOTALL)
_RE_EMPTY_CHAPTER = re.compile(r'<section[^>]*class="[^"]*chapter[^"]*"[^>]*>\s*</section>', re.DOTALL | re.IGNORECASE)
_RE_CLASS_ATTR_DOUBLE = re.compile(r'class="([^"]*)"', re.IGNORECASE)
_RE_CLASS_ATTR_SINGLE = re.compile(r"class='([^']*)'", re.IGNORECASE)
_RE_STYLE_TAG = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.DOTALL | re.IGNORECASE)
_RE_CLASS_SELECTOR = re.compile(r'\.([a-zA-Z0-9_-]+)')


def compress_html(html: str) -> str:
    """
    Compress HTML by removing unnecessary whitespace and comments.

    SPRINT G14-D: Uses pre-compiled regex patterns for performance.

    Args:
        html: Raw HTML string

    Returns:
        Compressed HTML string
    """
    original_size = len(html)

    # Remove HTML comments (except conditional comments for IE)
    html = _RE_HTML_COMMENTS.sub('', html)

    # Collapse multiple consecutive spaces to single space
    html = _RE_MULTIPLE_SPACES.sub(' ', html)

    # Remove spaces around tags
    html = _RE_TAG_WHITESPACE.sub('><', html)

    # Remove leading/trailing whitespace from lines
    html = _RE_LEADING_WHITESPACE.sub('', html)
    html = _RE_TRAILING_WHITESPACE.sub('', html)

    # Collapse multiple newlines to single
    html = _RE_MULTIPLE_NEWLINES.sub('\n', html)

    # Remove empty lines
    html = _RE_EMPTY_LINES.sub('\n', html)

    # Inline normalize paragraph content
    html = _RE_P_START_WHITESPACE.sub('<p>', html)
    html = _RE_P_END_WHITESPACE.sub('</p>', html)

    # Remove unreachable id attributes (empty or whitespace-only)
    html = _RE_EMPTY_ID_DOUBLE.sub('', html)
    html = _RE_EMPTY_ID_SINGLE.sub('', html)

    new_size = len(html)
    if original_size > 0:
        savings = (1 - new_size / original_size) * 100
        log.info(f"[HTML-MINIFY] Compressed {original_size}→{new_size} bytes ({savings:.1f}% saved)")

    return html


def minify_css(css: str) -> str:
    """
    Minify CSS by removing comments, whitespace, and duplicate declarations.

    SPRINT G14-D: Uses pre-compiled regex patterns for performance.

    Args:
        css: Raw CSS string

    Returns:
        Minified CSS string
    """
    original_size = len(css)

    # Remove CSS comments
    css = _RE_CSS_COMMENTS.sub('', css)

    # Remove whitespace around selectors and braces
    css = _RE_CSS_BRACE_OPEN.sub('{', css)
    css = _RE_CSS_BRACE_CLOSE.sub('}', css)
    css = _RE_CSS_SEMICOLON.sub(';', css)
    css = _RE_CSS_COLON.sub(':', css)

    # Remove trailing semicolons before closing braces
    css = css.replace(';}', '}')

    # Collapse multiple spaces
    css = _RE_CSS_MULTI_SPACE.sub(' ', css)

    # Remove newlines
    css = css.replace('\n', '')

    # Remove !important where possible (conservative approach)
    # Only remove if it's a duplicate declaration
    css = _remove_duplicate_declarations(css)

    new_size = len(css)
    if original_size > 0:
        savings = (1 - new_size / original_size) * 100
        log.debug(f"[CSS-MINIFY] Compressed {original_size}→{new_size} bytes ({savings:.1f}% saved)")

    return css


def _remove_duplicate_declarations(css: str) -> str:
    """
    Remove duplicate CSS declarations within the same rule block.

    SPRINT G14-D: Uses pre-compiled regex pattern.

    Args:
        css: CSS string

    Returns:
        CSS with duplicates removed
    """
    def process_block(match: re.Match) -> str:
        selector = match.group(1)
        declarations = match.group(2)

        # Parse declarations
        decl_list = [d.strip() for d in declarations.split(';') if d.strip()]

        # Track seen properties (last one wins)
        seen_props: dict[str, str] = {}
        for decl in decl_list:
            if ':' in decl:
                prop, value = decl.split(':', 1)
                prop = prop.strip().lower()
                seen_props[prop] = decl

        # Reconstruct with unique declarations
        unique_decls = ';'.join(seen_props.values())
        return f'{selector}{{{unique_decls}}}'

    # Process each rule block using pre-compiled pattern
    css = _RE_CSS_RULE.sub(process_block, css)
    return css


def strip_unused_sections(html: str) -> str:
    """
    Remove empty or unused HTML sections to reduce file size.

    SPRINT G14-D: Uses pre-compiled regex patterns for performance.

    Removes:
    - Empty sections (only whitespace/headlines)
    - Debug elements
    - Unused funding blocks
    - Empty placeholder divs

    Args:
        html: HTML string

    Returns:
        HTML with unused sections removed
    """
    original_size = len(html)
    removed_count = 0

    # Remove debug elements
    html, count = _RE_DEBUG_DIV.subn('', html)
    removed_count += count

    # Remove empty sections (section tags with only whitespace or empty children)
    html, count = _RE_EMPTY_SECTION.subn('', html)
    removed_count += count

    # Remove empty divs with placeholder-like classes
    html, count = _RE_PLACEHOLDER_DIV.subn('', html)
    removed_count += count

    # Remove empty funding blocks
    html, count = _RE_EMPTY_FUNDING.subn('', html)
    removed_count += count

    # Remove sections with only FUNDING_HTML placeholder that wasn't replaced
    html, count = _RE_FUNDING_PLACEHOLDER.subn('', html)
    removed_count += count

    # Remove empty chapter sections
    html, count = _RE_EMPTY_CHAPTER.subn('', html)
    removed_count += count

    new_size = len(html)
    if removed_count > 0:
        savings = original_size - new_size
        log.info(f"[STRIP-SECTIONS] Removed {removed_count} unused sections, saved {savings} bytes")

    return html


def extract_used_css_classes(html: str) -> Set[str]:
    """
    Extract all CSS class names used in HTML.

    SPRINT G14-D: Uses pre-compiled regex patterns for performance.

    Args:
        html: HTML string

    Returns:
        Set of class names found in HTML
    """
    classes: Set[str] = set()

    # Find all class attributes using pre-compiled patterns
    class_attrs = _RE_CLASS_ATTR_DOUBLE.findall(html)
    class_attrs += _RE_CLASS_ATTR_SINGLE.findall(html)

    for attr in class_attrs:
        # Split by whitespace to get individual classes
        for cls in attr.split():
            classes.add(cls.strip())

    return classes


def remove_unused_css_classes(css: str, used_classes: Set[str]) -> str:
    """
    Remove CSS rules for classes not used in HTML.

    SPRINT G14-D: Uses pre-compiled regex patterns for performance.

    Conservative approach: only removes rules where selector starts with .classname

    Args:
        css: CSS string
        used_classes: Set of class names used in HTML

    Returns:
        CSS with unused class rules removed
    """
    original_size = len(css)

    def keep_rule(match: re.Match) -> str:
        selector = match.group(1).strip()

        # Keep if not a class selector
        if not selector.startswith('.'):
            return str(match.group(0))

        # Extract class name from selector using pre-compiled pattern
        class_match = _RE_CLASS_SELECTOR.match(selector)
        if not class_match:
            return str(match.group(0))

        class_name = class_match.group(1)

        # Keep if class is used
        if class_name in used_classes:
            return str(match.group(0))

        # Keep commonly needed utility classes
        safe_classes = {'muted', 'small', 'hidden', 'visible', 'active', 'disabled'}
        if class_name in safe_classes:
            return str(match.group(0))

        # Remove unused class rule
        log.debug(f"[CSS-TRIM] Removing unused class: .{class_name}")
        return ''

    # Process each rule using pre-compiled pattern
    css = _RE_CSS_RULE.sub(keep_rule, css)

    new_size = len(css)
    if original_size > new_size:
        savings = (1 - new_size / original_size) * 100
        log.info(f"[CSS-TRIM] Removed unused classes: {original_size}→{new_size} bytes ({savings:.1f}% saved)")

    return css


def optimize_html_for_pdf(html: str) -> str:
    """
    Full optimization pipeline for HTML before PDF generation.

    SPRINT G14-D: Uses pre-compiled regex patterns for performance.

    Combines all optimization steps:
    1. Strip unused sections
    2. Compress HTML
    3. Extract and optimize inline CSS

    Args:
        html: Raw HTML string

    Returns:
        Optimized HTML string
    """
    original_size = len(html)

    # Step 1: Remove unused sections
    html = strip_unused_sections(html)

    # Step 2: Extract used classes for CSS optimization
    used_classes = extract_used_css_classes(html)

    # Step 3: Optimize inline CSS in <style> tags
    def optimize_style_block(match: re.Match) -> str:
        style_open = match.group(1)
        css = match.group(2)
        style_close = match.group(3)

        # Minify CSS
        css = minify_css(css)

        # Remove unused class rules
        css = remove_unused_css_classes(css, used_classes)

        return f'{style_open}{css}{style_close}'

    # Use pre-compiled pattern for style tag matching
    html = _RE_STYLE_TAG.sub(optimize_style_block, html)

    # Step 4: Compress HTML
    html = compress_html(html)

    new_size = len(html)
    if original_size > 0:
        savings = (1 - new_size / original_size) * 100
        log.info(f"[PDF-OPTIMIZE] Total: {original_size}→{new_size} bytes ({savings:.1f}% saved)")

    return html


# =============================================================================
# N3.3 TASK 6: HTML Payload Reduction Engine Phase 2
# =============================================================================

# Pre-compiled patterns for section removal
_RE_SECTION_BLOCK = re.compile(r'<section[^>]*>(.*?)</section>', re.DOTALL | re.IGNORECASE)
_RE_HTML_TAGS = re.compile(r'<[^>]+>')

# Pre-compiled patterns for table compression
_RE_TABLE_BLOCK = re.compile(r'<table[^>]*>.*?</table>', re.DOTALL | re.IGNORECASE)
_RE_TABLE_ROWS = re.compile(r'<tr[^>]*>.*?</tr>', re.DOTALL | re.IGNORECASE)
_RE_TBODY_CONTENT = re.compile(r'<tbody[^>]*>(.*?)</tbody>', re.DOTALL | re.IGNORECASE)
_RE_THEAD = re.compile(r'<thead[^>]*>.*?</thead>', re.DOTALL | re.IGNORECASE)


def remove_empty_sections(html: str, min_chars: int = 50) -> str:
    """
    N3.3 TASK 6: Remove <section> blocks with less than min_chars of content.

    Removes sections that have less than the specified minimum character count
    of actual text content (excluding HTML tags).

    Args:
        html: HTML string
        min_chars: Minimum character count for content (default: 50)

    Returns:
        HTML with empty/minimal sections removed
    """
    original_size = len(html)
    removed_count = 0

    def check_section(match: re.Match[str]) -> str:
        nonlocal removed_count
        full_section: str = match.group(0)
        inner_content: str = match.group(1)

        # Extract text content (remove HTML tags)
        text_content = _RE_HTML_TAGS.sub('', inner_content)
        # Remove whitespace for char count
        text_content = text_content.strip()
        text_content = ' '.join(text_content.split())

        if len(text_content) < min_chars:
            removed_count += 1
            log.debug(
                "[N3.3-SECTION] Removing section with %d chars (min=%d)",
                len(text_content), min_chars
            )
            return ''

        return full_section

    html = _RE_SECTION_BLOCK.sub(check_section, html)

    new_size = len(html)
    if removed_count > 0:
        savings = original_size - new_size
        log.info(
            "[N3.3-SECTION] Removed %d empty sections (<%d chars), saved %d bytes",
            removed_count, min_chars, savings
        )

    return html


def compress_long_tables(html: str, max_rows: int = 30) -> str:
    """
    N3.3 TASK 6: Compress tables with more than max_rows to a summary format.

    Tables with > max_rows are compressed to:
    - First 10 rows
    - Last 5 rows
    - Summary row with "... X weitere Zeilen ..."

    Args:
        html: HTML string
        max_rows: Maximum rows before compression (default: 30)

    Returns:
        HTML with long tables compressed
    """
    original_size = len(html)
    compressed_count = 0

    def compress_table(match: re.Match[str]) -> str:
        nonlocal compressed_count
        table_html: str = match.group(0)

        # Check if table has tbody
        tbody_match = _RE_TBODY_CONTENT.search(table_html)
        if not tbody_match:
            # No tbody, check total rows
            rows = _RE_TABLE_ROWS.findall(table_html)
            # Skip header rows (usually first row without tbody)
            if len(rows) <= max_rows:
                return str(table_html)
        else:
            # Has tbody - only count body rows
            tbody_content: str = tbody_match.group(1)
            rows = _RE_TABLE_ROWS.findall(tbody_content)
            if len(rows) <= max_rows:
                return str(table_html)

        # Table exceeds max_rows - compress it
        total_rows = len(rows)
        first_10 = rows[:10]
        last_5 = rows[-5:] if total_rows > 15 else rows[10:]
        hidden_count = total_rows - len(first_10) - len(last_5)

        if hidden_count <= 0:
            return str(table_html)

        # Build summary row
        # Count columns from first row
        col_count = rows[0].count('<td') + rows[0].count('<th')
        if col_count == 0:
            col_count = 1

        summary_row = (
            f'<tr class="table-summary-row">'
            f'<td colspan="{col_count}" style="text-align:center;font-style:italic;color:#666;">'
            f'... {hidden_count} weitere Zeilen ...'
            f'</td></tr>'
        )

        # Reconstruct table
        if tbody_match:
            # Replace tbody content
            new_tbody = ''.join(first_10) + summary_row + ''.join(last_5)
            new_table = table_html[:tbody_match.start(1)] + new_tbody + table_html[tbody_match.end(1):]
        else:
            # No tbody - replace rows directly (keeping thead if present)
            thead_match = _RE_THEAD.search(table_html)
            if thead_match:
                thead = thead_match.group(0)
                # Find where tbody/rows start after thead
                after_thead = table_html[thead_match.end():]
                # Remove old rows and add compressed
                after_thead_clean = _RE_TABLE_ROWS.sub('', after_thead, count=len(rows))
                new_rows = ''.join(first_10) + summary_row + ''.join(last_5)
                # Insert before </table>
                table_end_idx = after_thead_clean.lower().rfind('</table>')
                if table_end_idx >= 0:
                    new_table = (
                        table_html[:thead_match.end()] +
                        new_rows +
                        after_thead_clean[table_end_idx:]
                    )
                else:
                    new_table = table_html[:thead_match.end()] + new_rows + after_thead_clean
            else:
                # No thead - just compress all rows
                new_rows = ''.join(first_10) + summary_row + ''.join(last_5)
                # Find table boundaries
                table_start = table_html.lower().find('<table')
                table_start_end = table_html.find('>', table_start) + 1
                table_end = table_html.lower().rfind('</table>')
                new_table = table_html[:table_start_end] + new_rows + table_html[table_end:]

        compressed_count += 1
        log.debug(
            "[N3.3-TABLE] Compressed table: %d rows → %d visible + summary",
            total_rows, len(first_10) + len(last_5)
        )
        return str(new_table)

    html = _RE_TABLE_BLOCK.sub(compress_table, html)

    new_size = len(html)
    if compressed_count > 0:
        savings = original_size - new_size
        log.info(
            "[N3.3-TABLE] Compressed %d long tables, saved %d bytes",
            compressed_count, savings
        )

    return html


def optimize_html_for_pdf_v2(html: str, min_section_chars: int = 50, max_table_rows: int = 30) -> str:
    """
    N3.3 TASK 6: Enhanced optimization pipeline with Phase 2 features.

    Combines all optimization steps including new N3.3 features:
    1. Remove empty sections (< min_chars)
    2. Compress long tables (> max_rows)
    3. Strip unused sections
    4. Compress HTML
    5. Optimize CSS

    Args:
        html: Raw HTML string
        min_section_chars: Minimum chars for section content (default: 50)
        max_table_rows: Max rows before table compression (default: 30)

    Returns:
        Optimized HTML string
    """
    original_size = len(html)

    # N3.3 Step 1: Remove empty sections
    html = remove_empty_sections(html, min_chars=min_section_chars)

    # N3.3 Step 2: Compress long tables
    html = compress_long_tables(html, max_rows=max_table_rows)

    # Original Steps 3-5: Use existing optimization
    html = optimize_html_for_pdf(html)

    new_size = len(html)
    if original_size > 0:
        savings_pct = (1 - new_size / original_size) * 100
        savings_kb = (original_size - new_size) / 1024
        log.info(
            "[N3.3-PDF-OPTIMIZE] Total: %d→%d bytes (%.1f%% saved, %.1fKB reduced)",
            original_size, new_size, savings_pct, savings_kb
        )

    return html


# =============================================================================
# N3.4 TASK 5: Semantic HTML Purifier v3
# =============================================================================

# Pre-compiled patterns for GPT HTML cleanup
_RE_NESTED_STRONG_SPAN = re.compile(
    r'<p>\s*<strong>\s*<span>([^<]*)</span>\s*</strong>\s*</p>',
    re.IGNORECASE | re.DOTALL
)
_RE_EMPTY_SPAN = re.compile(r'<span>\s*</span>', re.IGNORECASE)
_RE_SPAN_NO_STYLE = re.compile(r'<span>([^<]*)</span>', re.IGNORECASE)
_RE_EMPTY_DIV_NO_CLASS = re.compile(r'<div>\s*</div>', re.IGNORECASE)
_RE_DOUBLE_EMPTY_P = re.compile(r'(</ul>\s*)<p>\s*</p>', re.IGNORECASE)
_RE_MULTIPLE_NBSP = re.compile(r'(&nbsp;){2,}', re.IGNORECASE)


def purify_gpt_html(html: str) -> str:
    """
    N3.4 TASK 5: Remove GPT-generated HTML redundancies.

    Cleans:
    - Nested <p><strong><span>Text</span></strong></p> → <p><strong>Text</strong></p>
    - Empty <span></span>
    - <span> without style attributes
    - Empty <div> without classes
    - Double empty <p></p> after </ul>
    - Multiple &nbsp;

    Args:
        html: HTML string

    Returns:
        Purified HTML
    """
    if not html:
        return html

    original_size = len(html)
    purified = html
    cleanups = 0

    # Cleanup 1: Nested <p><strong><span>Text</span></strong></p>
    matches = _RE_NESTED_STRONG_SPAN.findall(purified)
    if matches:
        purified = _RE_NESTED_STRONG_SPAN.sub(r'<p><strong>\1</strong></p>', purified)
        cleanups += len(matches)

    # Cleanup 2: Empty <span></span>
    purified, count = _RE_EMPTY_SPAN.subn('', purified)
    cleanups += count

    # Cleanup 3: <span> without style → just text
    purified, count = _RE_SPAN_NO_STYLE.subn(r'\1', purified)
    cleanups += count

    # Cleanup 4: Empty <div></div>
    purified, count = _RE_EMPTY_DIV_NO_CLASS.subn('', purified)
    cleanups += count

    # Cleanup 5: Double empty <p> after </ul>
    purified, count = _RE_DOUBLE_EMPTY_P.subn(r'\1', purified)
    cleanups += count

    # Cleanup 6: Multiple &nbsp;
    purified, count = _RE_MULTIPLE_NBSP.subn('&nbsp;', purified)
    cleanups += count

    new_size = len(purified)
    if cleanups > 0:
        savings = original_size - new_size
        log.info(
            "[N3.4-PURIFY] Removed %d GPT HTML redundancies, saved %d bytes",
            cleanups, savings
        )

    return purified


def optimize_table_styling(html: str) -> str:
    """
    N3.4 TASK 5: Optimize table styling for minimal payload.

    Applies:
    - Right-align numeric columns
    - Harmonize column widths
    - Reduce inline styling to minimum

    Args:
        html: HTML with tables

    Returns:
        HTML with optimized tables
    """
    if not html or '<table' not in html.lower():
        return html

    # Simple optimization: remove excessive inline styles in tables
    # Replace verbose styles with minimal equivalents
    optimized = html

    # Verbose → Minimal style replacements
    style_optimizations = [
        ('style="text-align: right;"', 'style="text-align:right"'),
        ('style="text-align: left;"', 'style="text-align:left"'),
        ('style="text-align: center;"', 'style="text-align:center"'),
        ('style="vertical-align: middle;"', 'style="vertical-align:middle"'),
        ('style="vertical-align: top;"', 'style="vertical-align:top"'),
    ]

    for verbose, minimal in style_optimizations:
        optimized = optimized.replace(verbose, minimal)

    return optimized


def optimize_html_for_pdf_v3(
    html: str,
    min_section_chars: int = 50,
    max_table_rows: int = 30
) -> str:
    """
    N3.4 TASK 5: Enhanced optimization pipeline v3.

    Combines all optimizations including new N3.4 features:
    1. Purify GPT HTML redundancies
    2. Optimize table styling
    3. Remove empty sections (< min_chars)
    4. Compress long tables (> max_rows)
    5. Strip unused sections
    6. Compress HTML
    7. Optimize CSS

    Target: Payload < 300KB

    Args:
        html: Raw HTML string
        min_section_chars: Minimum chars for section content
        max_table_rows: Max rows before table compression

    Returns:
        Optimized HTML string
    """
    original_size = len(html)

    # N3.4 Step 1: Purify GPT HTML
    html = purify_gpt_html(html)

    # N3.4 Step 2: Optimize table styling
    html = optimize_table_styling(html)

    # N3.3 Steps: Use existing v2 optimization
    html = optimize_html_for_pdf_v2(html, min_section_chars, max_table_rows)

    new_size = len(html)
    if original_size > 0:
        savings_pct = (1 - new_size / original_size) * 100
        savings_kb = (original_size - new_size) / 1024

        # Check if target achieved
        target_achieved = new_size < 300 * 1024
        status = "TARGET_MET" if target_achieved else "ABOVE_TARGET"

        log.info(
            "[N3.4-PDF-OPTIMIZE-V3] %s: %d→%d bytes (%.1f%% saved, %.1fKB), %s",
            status, original_size, new_size, savings_pct, savings_kb,
            "< 300KB" if target_achieved else f"> 300KB ({new_size / 1024:.0f}KB)"
        )

    return html


# =============================================================================
# SPRINT G14-D: Cache Statistics
# =============================================================================

def get_regex_cache_stats() -> dict:
    """
    Get statistics about the regex pattern cache.

    SPRINT G14-D: Useful for monitoring cache hit rates in production.
    """
    cache_info = _get_compiled_pattern.cache_info()
    return {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "maxsize": cache_info.maxsize,
        "currsize": cache_info.currsize,
        "hit_rate": (
            cache_info.hits / (cache_info.hits + cache_info.misses)
            if (cache_info.hits + cache_info.misses) > 0 else 0.0
        ),
    }
