# -*- coding: utf-8 -*-
"""
HTML & CSS Minifier for PDF Generation.

Reduces PDF file size by:
- Collapsing whitespace in HTML
- Minifying CSS (remove comments, duplicate declarations)
- Stripping unused sections and debug elements

Version: 1.0.0 PDF-SLIMDOWN
"""
from __future__ import annotations

import logging
import re
from typing import Set

log = logging.getLogger(__name__)


def compress_html(html: str) -> str:
    """
    Compress HTML by removing unnecessary whitespace and comments.

    Args:
        html: Raw HTML string

    Returns:
        Compressed HTML string
    """
    original_size = len(html)

    # Remove HTML comments (except conditional comments for IE)
    html = re.sub(r'<!--(?!\[if).*?-->', '', html, flags=re.DOTALL)

    # Collapse multiple consecutive spaces to single space
    html = re.sub(r'[ \t]+', ' ', html)

    # Remove spaces around tags
    html = re.sub(r'>\s+<', '><', html)

    # Remove leading/trailing whitespace from lines
    html = re.sub(r'^\s+', '', html, flags=re.MULTILINE)
    html = re.sub(r'\s+$', '', html, flags=re.MULTILINE)

    # Collapse multiple newlines to single
    html = re.sub(r'\n{2,}', '\n', html)

    # Remove empty lines
    html = re.sub(r'\n\s*\n', '\n', html)

    # Inline normalize paragraph content
    html = re.sub(r'<p>\s+', '<p>', html)
    html = re.sub(r'\s+</p>', '</p>', html)

    # Remove unreachable id attributes (empty or whitespace-only)
    html = re.sub(r'\s+id="\s*"', '', html)
    html = re.sub(r"\s+id='\s*'", '', html)

    new_size = len(html)
    if original_size > 0:
        savings = (1 - new_size / original_size) * 100
        log.info(f"[HTML-MINIFY] Compressed {original_size}→{new_size} bytes ({savings:.1f}% saved)")

    return html


def minify_css(css: str) -> str:
    """
    Minify CSS by removing comments, whitespace, and duplicate declarations.

    Args:
        css: Raw CSS string

    Returns:
        Minified CSS string
    """
    original_size = len(css)

    # Remove CSS comments
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)

    # Remove whitespace around selectors and braces
    css = re.sub(r'\s*{\s*', '{', css)
    css = re.sub(r'\s*}\s*', '}', css)
    css = re.sub(r'\s*;\s*', ';', css)
    css = re.sub(r'\s*:\s*', ':', css)

    # Remove trailing semicolons before closing braces
    css = re.sub(r';}', '}', css)

    # Collapse multiple spaces
    css = re.sub(r'\s{2,}', ' ', css)

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

    # Process each rule block
    css = re.sub(r'([^{]+)\{([^}]*)\}', process_block, css)
    return css


def strip_unused_sections(html: str) -> str:
    """
    Remove empty or unused HTML sections to reduce file size.

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
    html, count = re.subn(r'<div[^>]*class="[^"]*debug[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL | re.IGNORECASE)
    removed_count += count

    # Remove empty sections (section tags with only whitespace or empty children)
    html, count = re.subn(
        r'<section[^>]*>\s*(<h[1-6][^>]*>\s*</h[1-6]>\s*)*\s*</section>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    removed_count += count

    # Remove empty divs with placeholder-like classes
    html, count = re.subn(
        r'<div[^>]*class="[^"]*(?:placeholder|empty|unused)[^"]*"[^>]*>\s*</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    removed_count += count

    # Remove empty funding blocks
    html, count = re.subn(
        r'<div[^>]*class="[^"]*funding[^"]*"[^>]*>\s*</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    removed_count += count

    # Remove sections with only FUNDING_HTML placeholder that wasn't replaced
    html, count = re.subn(
        r'<section[^>]*>\s*\{\{FUNDING_HTML\}\}\s*</section>',
        '',
        html,
        flags=re.DOTALL
    )
    removed_count += count

    # Remove empty chapter sections
    html, count = re.subn(
        r'<section[^>]*class="[^"]*chapter[^"]*"[^>]*>\s*</section>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    removed_count += count

    new_size = len(html)
    if removed_count > 0:
        savings = original_size - new_size
        log.info(f"[STRIP-SECTIONS] Removed {removed_count} unused sections, saved {savings} bytes")

    return html


def extract_used_css_classes(html: str) -> Set[str]:
    """
    Extract all CSS class names used in HTML.

    Args:
        html: HTML string

    Returns:
        Set of class names found in HTML
    """
    classes: Set[str] = set()

    # Find all class attributes
    class_attrs = re.findall(r'class="([^"]*)"', html, re.IGNORECASE)
    class_attrs += re.findall(r"class='([^']*)'", html, re.IGNORECASE)

    for attr in class_attrs:
        # Split by whitespace to get individual classes
        for cls in attr.split():
            classes.add(cls.strip())

    return classes


def remove_unused_css_classes(css: str, used_classes: Set[str]) -> str:
    """
    Remove CSS rules for classes not used in HTML.

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

        # Extract class name from selector
        class_match = re.match(r'\.([a-zA-Z0-9_-]+)', selector)
        if not class_match:  # defensive: edge case like "." or non-ASCII after dot
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

    # Process each rule
    css = re.sub(r'([^{]+)\{[^}]*\}', keep_rule, css)

    new_size = len(css)
    if original_size > new_size:
        savings = (1 - new_size / original_size) * 100
        log.info(f"[CSS-TRIM] Removed unused classes: {original_size}→{new_size} bytes ({savings:.1f}% saved)")

    return css


def optimize_html_for_pdf(html: str) -> str:
    """
    Full optimization pipeline for HTML before PDF generation.

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

    html = re.sub(
        r'(<style[^>]*>)(.*?)(</style>)',
        optimize_style_block,
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Step 4: Compress HTML
    html = compress_html(html)

    new_size = len(html)
    if original_size > 0:
        savings = (1 - new_size / original_size) * 100
        log.info(f"[PDF-OPTIMIZE] Total: {original_size}→{new_size} bytes ({savings:.1f}% saved)")

    return html
