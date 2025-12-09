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
_RE_HTML_COMMENTS = re.compile(r'<!--(?!\[if).*?-->', re.DOTALL)
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
            return str(match.group(0))  # type: ignore[unreachable]

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
