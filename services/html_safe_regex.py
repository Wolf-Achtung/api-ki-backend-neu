"""
HTML-safe regex substitution — KIS-1019 Phase 2 Root-Cause-Fix.

Problem: re.sub(r'\\bwir\\b', 'ich', html) treats HTML tag boundaries (<, >)
as word boundaries, so <b>wir</b>tschaftlich → <b>ich</b>tschaftlich.

Solution: Strip tags → run regex on plaintext → map matches back to HTML
positions → replace in original HTML while preserving all tags.
"""

import re
from typing import List, Tuple, Optional

# Matches HTML tags including attributes, self-closing, comments
_TAG_RE = re.compile(r'<[^>]+>')

# Tags that act as word separators (block-level + break elements)
_BREAK_TAG_RE = re.compile(
    r'</?(?:br|p|div|li|ul|ol|tr|td|th|table|h[1-6]|hr|blockquote|section|article|header|footer|nav|dd|dt|dl)\b[^>]*/?>',
    re.IGNORECASE,
)


def _build_offset_map(html: str) -> Tuple[str, List[Tuple[int, int, int, int]]]:
    """
    Extract plaintext from HTML and build a position mapping.

    Returns:
        plaintext: The visible text with all tags removed.
        offset_map: List of (plain_start, plain_end, html_start, html_end)
                     for each contiguous text segment.
    """
    segments = []   # (html_start, html_end, is_break_tag) for text and break-tag segments
    last_end = 0

    for m in _TAG_RE.finditer(html):
        if m.start() > last_end:
            segments.append((last_end, m.start(), False))
        # Break tags (br, p, div, etc.) insert a space as word separator
        if _BREAK_TAG_RE.match(m.group()):
            segments.append((m.start(), m.end(), True))
        last_end = m.end()
    if last_end < len(html):
        segments.append((last_end, len(html), False))

    plaintext_parts = []
    plain_len = 0
    offset_map = []
    for html_start, html_end, is_break in segments:
        if is_break:
            # Break tag → space in plaintext (not mapped back to HTML)
            plaintext_parts.append(' ')
            plain_len += 1
        else:
            text = html[html_start:html_end]
            plain_start = plain_len
            plaintext_parts.append(text)
            plain_len += len(text)
            offset_map.append((plain_start, plain_len, html_start, html_end))

    plaintext = ''.join(plaintext_parts)
    return plaintext, offset_map


def _plain_to_html_pos(plain_pos: int, offset_map: List[Tuple[int, int, int, int]]) -> Optional[int]:
    """Map a position in plaintext back to its position in the original HTML."""
    for plain_start, plain_end, html_start, html_end in offset_map:
        if plain_start <= plain_pos <= plain_end:
            return html_start + (plain_pos - plain_start)
    return None


def html_safe_sub(pattern: str, replacement: str, html: str, flags: int = 0) -> str:
    """
    Like re.sub(), but matches only against visible plaintext.

    HTML tags are stripped before matching, so \\b never triggers at tag
    boundaries. After matching, replacements are mapped back to the
    original HTML string, preserving all tags in their correct positions.

    If the match spans across tag boundaries in the original HTML, the
    tags that fall within the matched region are preserved and re-inserted
    into the replacement text at proportional positions.
    """
    plaintext, offset_map = _build_offset_map(html)

    if not offset_map:
        return html

    compiled = re.compile(pattern, flags)
    matches = list(compiled.finditer(plaintext))

    if not matches:
        return html

    # Process matches in reverse order so positions don't shift
    result = html
    for m in reversed(matches):
        match_start_plain = m.start()
        match_end_plain = m.end()

        html_start = _plain_to_html_pos(match_start_plain, offset_map)
        html_end = _plain_to_html_pos(match_end_plain, offset_map)

        if html_start is None or html_end is None:
            continue

        # Collect any HTML tags that fall within the matched region
        matched_html = result[html_start:html_end]
        inner_tags = list(_TAG_RE.finditer(matched_html))

        # Build the replacement string with group references resolved
        expanded = m.expand(replacement)

        if inner_tags:
            # Re-insert tags into the replacement at proportional positions
            # This handles cases like <b>wir</b> haben → <b>ich</b> haben
            original_text_len = match_end_plain - match_start_plain
            new_text_len = len(expanded)

            # Build result by interleaving replacement text and preserved tags
            # First, compute tag positions relative to the plaintext match
            tag_positions = []  # (position_in_plaintext_match, tag_text)
            plain_cursor = 0
            last_tag_end = 0
            for tag_m in inner_tags:
                # Text before this tag in the matched HTML region
                text_before_tag = _TAG_RE.sub('', matched_html[last_tag_end:tag_m.start()])
                plain_cursor += len(text_before_tag)
                tag_positions.append((plain_cursor, tag_m.group()))
                last_tag_end = tag_m.end()

            # Map tag positions from original plaintext match to new replacement
            pieces = []
            prev_pos = 0
            for plain_pos, tag_text in tag_positions:
                if original_text_len > 0:
                    # Proportional mapping
                    new_pos = int(round(plain_pos * new_text_len / original_text_len))
                else:
                    new_pos = 0
                new_pos = max(prev_pos, min(new_pos, new_text_len))
                pieces.append(expanded[prev_pos:new_pos])
                pieces.append(tag_text)
                prev_pos = new_pos
            pieces.append(expanded[prev_pos:])
            expanded_with_tags = ''.join(pieces)
        else:
            expanded_with_tags = expanded

        result = result[:html_start] + expanded_with_tags + result[html_end:]

    return result
