# -*- coding: utf-8 -*-
"""
Post-processing for LLM-generated HTML to apply CSS design classes.

The Strategy and KPA templates define rich CSS components (KPI cards, timelines,
scenario grids, etc.) but the LLM outputs plain HTML (<table>, <p>, <ul>).
This module transforms typical LLM output patterns into the template CSS classes.

Gold standard: Brute-force regex on final HTML (proven pattern from R1 pipeline).
"""

import re
import logging
from typing import List, Tuple
from html.parser import HTMLParser

log = logging.getLogger(__name__)


# =============================================================================
# TABLE PARSER HELPERS
# =============================================================================

class _TableParser(HTMLParser):
    """Minimal HTML parser that extracts rows/cells from a <table>."""

    def __init__(self):
        super().__init__()
        self._in_table = 0
        self._in_row = False
        self._in_cell = False
        self._cell_tag = None
        self.rows: List[List[Tuple[str, str]]] = []  # [(tag, text), ...]
        self._current_row: List[Tuple[str, str]] = []
        self._current_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table += 1
        elif tag == "tr" and self._in_table == 1:
            self._in_row = True
            self._current_row = []
        elif tag in ("td", "th") and self._in_row:
            self._in_cell = True
            self._cell_tag = tag
            self._current_text = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self._in_table -= 1
        elif tag == "tr" and self._in_row:
            self._in_row = False
            if self._current_row:
                self.rows.append(self._current_row)
        elif tag in ("td", "th") and self._in_cell:
            self._in_cell = False
            self._current_row.append((self._cell_tag, self._current_text.strip()))

    def handle_data(self, data):
        if self._in_cell:
            self._current_text += data


def _parse_table(table_html: str) -> List[List[Tuple[str, str]]]:
    """Parse a <table> into rows of (tag, text) cells."""
    parser = _TableParser()
    try:
        parser.feed(table_html)
    except Exception:
        return []
    return parser.rows


def _cell_texts(row: List[Tuple[str, str]]) -> List[str]:
    return [text for _, text in row]


def _is_header_row(row: List[Tuple[str, str]]) -> bool:
    return all(tag == "th" for tag, _ in row)


# =============================================================================
# RULE 1: KPI Tables → KPI Cards
# =============================================================================

def _try_kpi_transform(table_html: str) -> str | None:
    """Convert a 2-row table (header + values) with 2-4 numeric/currency cells to KPI cards."""
    rows = _parse_table(table_html)
    if len(rows) != 2:
        return None
    if not _is_header_row(rows[0]):
        return None
    headers = _cell_texts(rows[0])
    values = _cell_texts(rows[1])
    if len(headers) < 2 or len(headers) > 4 or len(headers) != len(values):
        return None

    # At least 2 cells should contain numeric-ish values (€, %, Monat, digits)
    numeric_pattern = re.compile(r'[\d€%]|Monat|Jahr|Woche')
    numeric_count = sum(1 for v in values if numeric_pattern.search(v))
    if numeric_count < 2:
        return None

    cards = []
    for label, value in zip(headers, values):
        cards.append(
            f'<div class="kpi-card">'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-label">{label}</div>'
            f'</div>'
        )
    return f'<div class="kpi-row">{"".join(cards)}</div>'


# =============================================================================
# RULE 2: Phase Tables → Timeline
# =============================================================================

_RE_PHASE = re.compile(r'Phase\s*(\d)', re.IGNORECASE)
_RE_MONAT_RANGE = re.compile(r'Monat\s*\d+\s*[-–—]\s*\d+', re.IGNORECASE)


def _try_timeline_transform(table_html: str) -> str | None:
    """Convert a table with Phase 1/2/3 rows into a timeline."""
    rows = _parse_table(table_html)
    if len(rows) < 2:
        return None

    # Check if first column contains "Phase N" patterns
    data_rows = rows[1:] if _is_header_row(rows[0]) else rows
    phase_count = sum(1 for row in data_rows if row and _RE_PHASE.search(row[0][1]))
    if phase_count < 2:
        return None

    headers = _cell_texts(rows[0]) if _is_header_row(rows[0]) else []
    items = []
    for row in data_rows:
        texts = _cell_texts(row)
        if not texts:
            continue

        # First cell: "Phase N: Title" or just "Phase N"
        first = texts[0]
        phase_match = _RE_PHASE.search(first)
        if not phase_match:
            continue

        # Extract phase number and title
        phase_num = phase_match.group(1)
        # Try to split "Phase 1: Quick Wins" → title = "Quick Wins"
        title_parts = re.split(r'Phase\s*\d\s*[:–—-]\s*', first, maxsplit=1)
        title = title_parts[1].strip() if len(title_parts) > 1 else f"Phase {phase_num}"

        # Remaining cells as description
        desc_parts = []
        for i, text in enumerate(texts[1:], 1):
            label = headers[i] if i < len(headers) else ""
            if text:
                if label and label.lower() not in text.lower():
                    desc_parts.append(f"{label}: {text}")
                else:
                    desc_parts.append(text)

        # Look for "Monat X-Y" in any cell
        time_range = ""
        for t in texts:
            m = _RE_MONAT_RANGE.search(t)
            if m:
                time_range = m.group(0)
                break

        phase_label = f"Phase {phase_num}"
        if time_range:
            phase_label += f" · {time_range}"

        desc_html = " · ".join(desc_parts) if desc_parts else ""
        items.append(
            f'<div class="timeline-item">'
            f'<div class="timeline-phase">{phase_label}</div>'
            f'<div class="timeline-title">{title}</div>'
            + (f'<div class="timeline-desc">{desc_html}</div>' if desc_html else '')
            + '</div>'
        )

    if len(items) < 2:
        return None
    return f'<div class="timeline">{"".join(items)}</div>'


# =============================================================================
# RULE 3: ROI Scenario Tables → Scenario Cards
# =============================================================================

_SCENARIO_KEYWORDS = {
    "konservativ": "Konservativ",
    "realistisch": "Realistisch",
    "optimistisch": "Optimistisch",
}


def _try_scenario_transform(table_html: str) -> str | None:
    """Convert a table with Konservativ/Realistisch/Optimistisch columns/rows to scenario cards."""
    rows = _parse_table(table_html)
    if len(rows) < 2:
        return None

    # Check for scenario keywords in headers (columns) or first column (rows)
    all_text = " ".join(cell[1] for row in rows for cell in row).lower()
    scenario_hits = sum(1 for kw in _SCENARIO_KEYWORDS if kw in all_text)
    if scenario_hits < 2:
        return None

    # Strategy A: Scenarios as columns (headers contain keywords)
    if _is_header_row(rows[0]):
        headers_lower = [h.lower() for h in _cell_texts(rows[0])]
        scenario_cols = []
        for i, h in enumerate(headers_lower):
            for kw, label in _SCENARIO_KEYWORDS.items():
                if kw in h:
                    scenario_cols.append((i, label))
                    break

        if len(scenario_cols) >= 2:
            # Build cards from columns
            data_rows = rows[1:]
            row_labels = _cell_texts(rows[0])
            cards = []
            for col_idx, scenario_label in scenario_cols:
                values = []
                for row in data_rows:
                    texts = _cell_texts(row)
                    if col_idx < len(texts) and texts[col_idx]:
                        row_label = texts[0] if col_idx > 0 else ""
                        values.append((row_label, texts[col_idx]))

                # First value as main, rest as description
                main_value = values[0][1] if values else ""
                desc_parts = [f"{lbl}: {val}" for lbl, val in values[1:] if val]
                desc = "<br>".join(desc_parts)

                is_recommended = scenario_label == "Realistisch"
                cls = 'scenario-card recommended' if is_recommended else 'scenario-card'
                cards.append(
                    f'<div class="{cls}">'
                    f'<div class="scenario-label">{scenario_label}</div>'
                    f'<div class="scenario-value">{main_value}</div>'
                    + (f'<div class="scenario-desc">{desc}</div>' if desc else '')
                    + '</div>'
                )
            return f'<div class="scenario-grid">{"".join(cards)}</div>'

    # Strategy B: Scenarios as rows (first column contains keywords)
    scenario_rows = []
    for row in rows:
        texts = _cell_texts(row)
        if not texts:
            continue
        first_lower = texts[0].lower()
        for kw, label in _SCENARIO_KEYWORDS.items():
            if kw in first_lower:
                scenario_rows.append((label, texts))
                break

    if len(scenario_rows) >= 2:
        headers = _cell_texts(rows[0]) if _is_header_row(rows[0]) else []
        cards = []
        for scenario_label, scenario_texts in scenario_rows:
            remaining = scenario_texts[1:]  # skip first column (scenario name)
            row_main_value = remaining[0] if remaining else ""
            row_desc_parts: list[str] = []
            for i, val in enumerate(remaining[1:], 2):
                h = headers[i] if i < len(headers) else ""
                if val:
                    row_desc_parts.append(f"{h}: {val}" if h else val)
            row_desc = "<br>".join(row_desc_parts)

            is_recommended = scenario_label == "Realistisch"
            cls = 'scenario-card recommended' if is_recommended else 'scenario-card'
            cards.append(
                f'<div class="{cls}">'
                f'<div class="scenario-label">{scenario_label}</div>'
                f'<div class="scenario-value">{row_main_value}</div>'
                + (f'<div class="scenario-desc">{row_desc}</div>' if row_desc else '')
                + '</div>'
            )
        return f'<div class="scenario-grid">{"".join(cards)}</div>'

    return None


# =============================================================================
# TABLE DISPATCHER: Try specific transforms, fallback to styled table
# =============================================================================

_RE_TABLE = re.compile(r'<table(?:\s[^>]*)?>.*?</table>', re.DOTALL | re.IGNORECASE)


def _transform_tables(html: str) -> str:
    """Apply table-specific transforms (Rules 1-3) then fallback styling (Rule 7)."""

    def _replace_table(match):
        table_html = match.group(0)

        # Already has a class? Skip.
        if re.match(r'<table\s+class=', table_html):
            return table_html

        # Try specific transforms in order
        result = _try_kpi_transform(table_html)
        if result:
            return result

        result = _try_timeline_transform(table_html)
        if result:
            return result

        result = _try_scenario_transform(table_html)
        if result:
            return result

        # Rule 7 fallback: add tool-comparison class for styled tables
        return re.sub(r'^<table(?!\s+class=)', '<table class="tool-comparison"', table_html)

    return _RE_TABLE.sub(_replace_table, html)


# =============================================================================
# RULE 4: Quellen → sources-footer
# =============================================================================

_RE_QUELLEN_P = re.compile(
    r'<p>\s*(Quellen?:\s*.*?)</p>',
    re.DOTALL | re.IGNORECASE
)

_RE_QUELLEN_DIV = re.compile(
    r'<div\s+class="sources">\s*(.*?)</div>',
    re.DOTALL | re.IGNORECASE
)


def _transform_sources(html: str) -> str:
    """Wrap Quellen paragraphs and <div class="sources"> in sources-footer."""
    # Already using sources-footer? Skip.
    if 'sources-footer' in html:
        return html

    # Transform <div class="sources">...</div> → <div class="sources-footer">...</div>
    html = _RE_QUELLEN_DIV.sub(
        r'<div class="sources-footer"><p>\1</p></div>',
        html
    )

    # Transform <p>Quellen: ...</p> → <div class="sources-footer"><p>Quellen: ...</p></div>
    html = _RE_QUELLEN_P.sub(
        r'<div class="sources-footer"><p>\1</p></div>',
        html
    )
    return html


# =============================================================================
# RULE 5: Quick Win / Handlungsfeld → highlight-box
# =============================================================================

_RE_HIGHLIGHT_H3 = re.compile(
    r'(<h3[^>]*>(?:Handlungsfeld\s*\d+[:\s]*)?Quick\s*Win[^<]*</h3>\s*(?:<p>.*?</p>\s*)*)',
    re.DOTALL | re.IGNORECASE
)


def _transform_highlight_boxes(html: str) -> str:
    """Wrap Quick Win sections in highlight-box."""
    def _wrap(match):
        content = match.group(0)
        if 'highlight-box' in content:
            return content
        return f'<div class="highlight-box">{content}</div>'
    return _RE_HIGHLIGHT_H3.sub(_wrap, html)


# =============================================================================
# RULE 6: Impact/Ampel markers → colored badges
# =============================================================================

_AMPEL_PATTERNS = [
    (re.compile(r'Impact:\s*(hoch)', re.IGNORECASE),
     'Impact: <span class="ampel-green">\u25cf \\1</span>'),
    (re.compile(r'Impact:\s*(mittel)', re.IGNORECASE),
     'Impact: <span class="ampel-yellow">\u25cf \\1</span>'),
    (re.compile(r'Impact:\s*(niedrig|gering)', re.IGNORECASE),
     'Impact: <span class="ampel-red">\u25cf \\1</span>'),
    (re.compile(r'Komplexit(?:ä|ae)t:\s*(niedrig|gering)', re.IGNORECASE),
     'Komplexit\u00e4t: <span class="ampel-green">\u25cf \\1</span>'),
    (re.compile(r'Komplexit(?:ä|ae)t:\s*(mittel)', re.IGNORECASE),
     'Komplexit\u00e4t: <span class="ampel-yellow">\u25cf \\1</span>'),
    (re.compile(r'Komplexit(?:ä|ae)t:\s*(hoch)', re.IGNORECASE),
     'Komplexit\u00e4t: <span class="ampel-red">\u25cf \\1</span>'),
]


def _transform_ampel_badges(html: str) -> str:
    """Add colored badges for Impact/Complexity markers."""
    for pattern, replacement in _AMPEL_PATTERNS:
        html = pattern.sub(replacement, html)
    return html


# =============================================================================
# INLINE KPI PATTERNS (standalone "Label: Value" lines with € or %)
# =============================================================================

_RE_INLINE_KPI = re.compile(
    r'<p>\s*'
    r'(?:<strong>)?\s*'
    r'(Gesamtinvestition|Gesamtbudget|ROI|Break-Even|Amortisation|Payback|Einsparpotenzial|Einsparungen|Netto-Nutzen|Investitionssumme)'
    r'\s*(?:Jahr\s*\d+)?\s*'
    r'(?:</strong>)?\s*'
    r'[:]\s*'
    r'(?:<strong>)?\s*'
    r'([^<]{2,40})'
    r'(?:</strong>)?\s*'
    r'</p>',
    re.IGNORECASE
)


def _transform_inline_kpis(html: str) -> str:
    """Convert standalone key-value paragraphs (Gesamtinvestition: 48.000€) to KPI cards.
    Collects consecutive matches into a single kpi-row."""
    # Find all matches with positions
    matches = list(_RE_INLINE_KPI.finditer(html))
    if not matches:
        return html

    # Group consecutive matches (within 10 chars of each other)
    groups = []
    current_group = [matches[0]]
    for m in matches[1:]:
        prev = current_group[-1]
        if m.start() - prev.end() < 10:
            current_group.append(m)
        else:
            groups.append(current_group)
            current_group = [m]
    groups.append(current_group)

    # Replace groups (reverse order to preserve positions)
    for group in reversed(groups):
        if len(group) < 2:
            continue  # Only convert groups of 2+
        cards = []
        for m in group:
            label = m.group(1)
            value = m.group(2).strip()
            cards.append(
                f'<div class="kpi-card">'
                f'<div class="kpi-value">{value}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'</div>'
            )
        replacement = f'<div class="kpi-row">{"".join(cards)}</div>'
        start = group[0].start()
        end = group[-1].end()
        html = html[:start] + replacement + html[end:]

    return html


# =============================================================================
# PUBLIC API
# =============================================================================

def enhance_strategy_html(html: str) -> str:
    """Post-process Strategy report HTML to use CSS design classes.

    Applied AFTER template rendering, BEFORE budget enforcement.
    Order matters: specific table transforms before fallback styling.
    """
    original_len = len(html)

    # 1. Specific table transforms (Rules 1-3) + fallback styling (Rule 7)
    html = _transform_tables(html)

    # 2. Inline KPI patterns
    html = _transform_inline_kpis(html)

    # 3. Sources footer (Rule 4)
    html = _transform_sources(html)

    # 4. Highlight boxes (Rule 5)
    html = _transform_highlight_boxes(html)

    # 5. Ampel badges (Rule 6)
    html = _transform_ampel_badges(html)

    log.info("[HTML-ENHANCE] Strategy: %d → %d chars", original_len, len(html))
    return html


def enhance_kpa_html(html: str) -> str:
    """Post-process KPA (Gamechanger Deep Dive) HTML to use CSS design classes.

    Same core transforms as Strategy but simpler (fewer section types).
    """
    original_len = len(html)

    # 1. Table styling (KPA uses simpler tables — just add class)
    html = _transform_tables(html)

    # 2. Sources footer
    html = _transform_sources(html)

    # 3. Ampel badges
    html = _transform_ampel_badges(html)

    log.info("[HTML-ENHANCE] KPA: %d → %d chars", original_len, len(html))
    return html
