# -*- coding: utf-8 -*-
"""
Post-processing for LLM-generated HTML to apply CSS design classes + inline styles.

The Strategy and KPA templates define rich CSS components (KPI cards, timelines,
scenario grids, etc.) but the LLM outputs plain HTML (<table>, <p>, <ul>).
This module transforms typical LLM output patterns into styled components.

Inline styles are used IN ADDITION to CSS classes for reliable Puppeteer PDF rendering.
Gold standard: Brute-force regex on final HTML (proven pattern from R1 pipeline).
"""

import re
import logging
from typing import List, Tuple
from html.parser import HTMLParser

log = logging.getLogger(__name__)

# =============================================================================
# INLINE STYLE CONSTANTS (from strategy_report.html CSS, for Puppeteer reliability)
# =============================================================================

_S_KPI_ROW = "display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:20px 0"
_S_KPI_CARD = "text-align:center;padding:16px;background:#f8fafc;border-radius:8px;border-top:3px solid #1E3A5F"
_S_KPI_VALUE = "font-family:'Playfair Display',Georgia,serif;font-size:22pt;font-weight:700;color:#1E3A5F;line-height:1.2"
_S_KPI_LABEL = "font-size:8.5pt;color:#6B7280;margin-top:4px"

_S_TIMELINE = "position:relative;padding-left:32px;margin:24px 0"
_S_TIMELINE_ITEM = "position:relative;padding:12px 0 20px;border-left:2px solid #3b82f6;padding-left:24px;margin-left:8px"
_S_TIMELINE_PHASE = "font-size:8pt;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#3b82f6"
_S_TIMELINE_TITLE = "font-size:13pt;font-weight:700;color:#1E3A5F;margin:4px 0"
_S_TIMELINE_DESC = "font-size:9.5pt;color:#374151;line-height:1.6"

_S_SCENARIO_GRID = "display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin:24px 0"
_SCENARIO_COLORS = {
    "Konservativ": ("#f59e0b", "#fffbeb"),  # amber
    "Realistisch": ("#3b82f6", "#eff6ff"),  # blue (recommended)
    "Optimistisch": ("#22c55e", "#f0fdf4"),  # green
}

_S_TABLE = "width:100%;border-collapse:collapse;border-radius:8px;overflow:hidden;margin:16px 0;font-size:9pt"
_S_TH = "background:#1E3A5F;color:#fff;padding:10px 12px;font-size:8pt;text-transform:uppercase;letter-spacing:0.05em;text-align:left"
_S_TD = "padding:8px 12px;border-bottom:1px solid #E5E7EB;vertical-align:top"

_S_SOURCES = "font-size:8pt;color:#9CA3AF;border-top:1px solid #E5E7EB;padding-top:12px;margin-top:24px"
_S_HIGHLIGHT = "background:#eff6ff;border-left:4px solid #3b82f6;padding:16px 20px;border-radius:0 8px 8px 0;margin:16px 0"

_AMPEL_STYLES = {
    "green": "display:inline-block;background:#ecfdf5;color:#047857;padding:2px 8px;border-radius:4px;font-size:8pt;font-weight:600",
    "yellow": "display:inline-block;background:#fffbeb;color:#b45309;padding:2px 8px;border-radius:4px;font-size:8pt;font-weight:600",
    "red": "display:inline-block;background:#fef2f2;color:#b91c1c;padding:2px 8px;border-radius:4px;font-size:8pt;font-weight:600",
}


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
# RULE 1: KPI Tables → KPI Cards (with inline styles)
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

    numeric_pattern = re.compile(r'[\d\u20ac%]|Monat|Jahr|Woche')
    numeric_count = sum(1 for v in values if numeric_pattern.search(v))
    if numeric_count < 2:
        return None

    cards = []
    for label, value in zip(headers, values):
        cards.append(
            f'<div class="kpi-card" style="{_S_KPI_CARD}">'
            f'<div class="kpi-value" style="{_S_KPI_VALUE}">{value}</div>'
            f'<div class="kpi-label" style="{_S_KPI_LABEL}">{label}</div>'
            f'</div>'
        )
    return f'<div class="kpi-row" style="{_S_KPI_ROW}">{"".join(cards)}</div>'


# =============================================================================
# RULE 2: Phase Tables → Timeline (with inline styles)
# =============================================================================

_RE_PHASE = re.compile(r'Phase\s*(\d)', re.IGNORECASE)
_RE_MONAT_RANGE = re.compile(r'Monat\s*\d+\s*[-\u2013\u2014]\s*\d+', re.IGNORECASE)


def _try_timeline_transform(table_html: str) -> str | None:
    """Convert a table with Phase 1/2/3 rows into a timeline."""
    rows = _parse_table(table_html)
    if len(rows) < 2:
        return None

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

        first = texts[0]
        phase_match = _RE_PHASE.search(first)
        if not phase_match:
            continue

        phase_num = phase_match.group(1)
        title_parts = re.split(r'Phase\s*\d\s*[:\u2013\u2014-]\s*', first, maxsplit=1)
        title = title_parts[1].strip() if len(title_parts) > 1 else f"Phase {phase_num}"

        desc_parts = []
        for i, text in enumerate(texts[1:], 1):
            label = headers[i] if i < len(headers) else ""
            if text:
                if label and label.lower() not in text.lower():
                    desc_parts.append(f"{label}: {text}")
                else:
                    desc_parts.append(text)

        time_range = ""
        for t in texts:
            m = _RE_MONAT_RANGE.search(t)
            if m:
                time_range = m.group(0)
                break

        phase_label = f"Phase {phase_num}"
        if time_range:
            phase_label += f" \u00b7 {time_range}"

        desc_html = " \u00b7 ".join(desc_parts) if desc_parts else ""
        items.append(
            f'<div class="timeline-item" style="{_S_TIMELINE_ITEM}">'
            f'<div class="timeline-phase" style="{_S_TIMELINE_PHASE}">{phase_label}</div>'
            f'<div class="timeline-title" style="{_S_TIMELINE_TITLE}">{title}</div>'
            + (f'<div class="timeline-desc" style="{_S_TIMELINE_DESC}">{desc_html}</div>' if desc_html else '')
            + '</div>'
        )

    if len(items) < 2:
        return None
    return f'<div class="timeline" style="{_S_TIMELINE}">{"".join(items)}</div>'


# =============================================================================
# RULE 3: ROI Scenario Tables → Scenario Cards (with inline styles)
# =============================================================================

_SCENARIO_KEYWORDS = {
    "konservativ": "Konservativ",
    "realistisch": "Realistisch",
    "optimistisch": "Optimistisch",
}


def _scenario_card_html(label: str, main_value: str, desc: str) -> str:
    """Build a single scenario card with color-coded inline styles."""
    color, bg = _SCENARIO_COLORS.get(label, ("#6B7280", "#f9fafb"))
    is_rec = label == "Realistisch"
    shadow = "box-shadow:0 4px 12px rgba(59,130,246,0.15);" if is_rec else ""
    cls = "scenario-card recommended" if is_rec else "scenario-card"
    style = f"background:{bg};border:2px solid {color};border-radius:12px;padding:20px;text-align:center;{shadow}break-inside:avoid"
    return (
        f'<div class="{cls}" style="{style}">'
        f'<div class="scenario-label" style="font-size:9pt;font-weight:600;text-transform:uppercase;color:{color};letter-spacing:0.05em">{label}</div>'
        f'<div class="scenario-value" style="font-size:22pt;font-weight:700;color:{color};margin:8px 0">{main_value}</div>'
        + (f'<div class="scenario-desc" style="font-size:9pt;color:#6B7280;line-height:1.5;text-align:left;margin-top:8px">{desc}</div>' if desc else '')
        + '</div>'
    )


def _try_scenario_transform(table_html: str) -> str | None:
    """Convert a table with Konservativ/Realistisch/Optimistisch columns/rows to scenario cards."""
    rows = _parse_table(table_html)
    if len(rows) < 2:
        return None

    all_text = " ".join(cell[1] for row in rows for cell in row).lower()
    scenario_hits = sum(1 for kw in _SCENARIO_KEYWORDS if kw in all_text)
    if scenario_hits < 2:
        return None

    # Strategy A: Scenarios as columns
    if _is_header_row(rows[0]):
        headers_lower = [h.lower() for h in _cell_texts(rows[0])]
        scenario_cols = []
        for i, h in enumerate(headers_lower):
            for kw, label in _SCENARIO_KEYWORDS.items():
                if kw in h:
                    scenario_cols.append((i, label))
                    break

        if len(scenario_cols) >= 2:
            data_rows = rows[1:]
            cards = []
            for col_idx, scenario_label in scenario_cols:
                values = []
                for row in data_rows:
                    texts = _cell_texts(row)
                    if col_idx < len(texts) and texts[col_idx]:
                        row_label = texts[0] if col_idx > 0 else ""
                        values.append((row_label, texts[col_idx]))

                main_value = values[0][1] if values else ""
                desc_parts = [f"{lbl}: {val}" for lbl, val in values[1:] if val]
                desc = "<br>".join(desc_parts)
                cards.append(_scenario_card_html(scenario_label, main_value, desc))
            return f'<div class="scenario-grid" style="{_S_SCENARIO_GRID}">{"".join(cards)}</div>'

    # Strategy B: Scenarios as rows
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
            remaining = scenario_texts[1:]
            row_main_value = remaining[0] if remaining else ""
            row_desc_parts: list[str] = []
            for i, val in enumerate(remaining[1:], 2):
                h = headers[i] if i < len(headers) else ""
                if val:
                    row_desc_parts.append(f"{h}: {val}" if h else val)
            row_desc = "<br>".join(row_desc_parts)
            cards.append(_scenario_card_html(scenario_label, row_main_value, row_desc))
        return f'<div class="scenario-grid" style="{_S_SCENARIO_GRID}">{"".join(cards)}</div>'

    return None


# =============================================================================
# TABLE DISPATCHER: Try specific transforms, fallback to styled table
# =============================================================================

_RE_TABLE = re.compile(r'<table(?:\s[^>]*)?>.*?</table>', re.DOTALL | re.IGNORECASE)


def _style_table_headers(table_html: str) -> str:
    """Add inline styles to <th> and <td> elements in a table."""
    # Style <th> elements
    table_html = re.sub(
        r'<th(?!\s+style=)([^>]*)>',
        f'<th style="{_S_TH}"\\1>',
        table_html
    )
    # Style <td> elements
    table_html = re.sub(
        r'<td(?!\s+style=)([^>]*)>',
        f'<td style="{_S_TD}"\\1>',
        table_html
    )
    # Alternating row backgrounds
    row_idx = [0]

    def _style_tr(match: re.Match) -> str:  # type: ignore[type-arg, unused-ignore]
        row_idx[0] += 1
        bg = "#f9fafb" if row_idx[0] % 2 == 0 else "#fff"
        return f'<tr style="background:{bg}">'

    # Only style <tr> without existing style (skip header rows)
    table_html = re.sub(r'<tr>(?!.*?<th)', _style_tr, table_html)
    return table_html


def _transform_tables(html: str) -> str:
    """Apply table-specific transforms (Rules 1-3) then fallback styling (Rule 7)."""

    def _replace_table(match: re.Match) -> str:  # type: ignore[type-arg, unused-ignore]
        table_html = match.group(0)

        # Already has a class? Skip.
        if re.match(r'<table\s+class=', table_html):
            return str(table_html)

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

        # Rule 7 fallback: styled table with inline styles + class
        table_html = re.sub(
            r'^<table(?!\s+class=)',
            f'<table class="tool-comparison" style="{_S_TABLE}"',
            table_html
        )
        table_html = _style_table_headers(table_html)
        return str(table_html)

    return _RE_TABLE.sub(_replace_table, html)


# =============================================================================
# RULE 4: Quellen → sources-footer (with inline styles)
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
    if 'sources-footer' in html:
        return html

    html = _RE_QUELLEN_DIV.sub(
        f'<div class="sources-footer" style="{_S_SOURCES}"><p>\\1</p></div>',
        html
    )
    html = _RE_QUELLEN_P.sub(
        f'<div class="sources-footer" style="{_S_SOURCES}"><p>\\1</p></div>',
        html
    )
    return html


# =============================================================================
# RULE 5: Quick Win / Handlungsfeld → highlight-box (with inline styles)
# =============================================================================

_RE_HIGHLIGHT_H3 = re.compile(
    r'(<h3[^>]*>(?:Handlungsfeld\s*\d+[:\s]*)?Quick\s*Win[^<]*</h3>\s*(?:<p>.*?</p>\s*)*)',
    re.DOTALL | re.IGNORECASE
)


def _transform_highlight_boxes(html: str) -> str:
    """Wrap Quick Win sections in highlight-box."""
    def _wrap(match: re.Match) -> str:  # type: ignore[type-arg, unused-ignore]
        content = match.group(0)
        if 'highlight-box' in content:
            return str(content)
        return f'<div class="highlight-box" style="{_S_HIGHLIGHT}">{content}</div>'
    return str(_RE_HIGHLIGHT_H3.sub(_wrap, html))


# =============================================================================
# RULE 6: Impact/Ampel markers → colored badges (with inline styles)
# =============================================================================

_AMPEL_PATTERNS = [
    (re.compile(r'Impact:\s*(hoch)', re.IGNORECASE),
     f'Impact: <span class="ampel-green" style="{_AMPEL_STYLES["green"]}">\u25cf \\1</span>'),
    (re.compile(r'Impact:\s*(mittel)', re.IGNORECASE),
     f'Impact: <span class="ampel-yellow" style="{_AMPEL_STYLES["yellow"]}">\u25cf \\1</span>'),
    (re.compile(r'Impact:\s*(niedrig|gering)', re.IGNORECASE),
     f'Impact: <span class="ampel-red" style="{_AMPEL_STYLES["red"]}">\u25cf \\1</span>'),
    (re.compile(r'Komplexit\u00e4t:\s*(niedrig|gering)', re.IGNORECASE),
     f'Komplexit\u00e4t: <span class="ampel-green" style="{_AMPEL_STYLES["green"]}">\u25cf \\1</span>'),
    (re.compile(r'Komplexit\u00e4t:\s*(mittel)', re.IGNORECASE),
     f'Komplexit\u00e4t: <span class="ampel-yellow" style="{_AMPEL_STYLES["yellow"]}">\u25cf \\1</span>'),
    (re.compile(r'Komplexit\u00e4t:\s*(hoch)', re.IGNORECASE),
     f'Komplexit\u00e4t: <span class="ampel-red" style="{_AMPEL_STYLES["red"]}">\u25cf \\1</span>'),
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
    """Convert standalone key-value paragraphs (Gesamtinvestition: 48.000\u20ac) to KPI cards."""
    matches = list(_RE_INLINE_KPI.finditer(html))
    if not matches:
        return html

    # Group consecutive matches (within 10 chars of each other)
    groups: list[list[re.Match]] = []  # type: ignore[type-arg, unused-ignore]
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
            continue
        cards = []
        for m in group:
            label = m.group(1)
            value = m.group(2).strip()
            cards.append(
                f'<div class="kpi-card" style="{_S_KPI_CARD}">'
                f'<div class="kpi-value" style="{_S_KPI_VALUE}">{value}</div>'
                f'<div class="kpi-label" style="{_S_KPI_LABEL}">{label}</div>'
                f'</div>'
            )
        replacement = f'<div class="kpi-row" style="{_S_KPI_ROW}">{"".join(cards)}</div>'
        start = group[0].start()
        end = group[-1].end()
        html = html[:start] + replacement + html[end:]

    return html


# =============================================================================
# PUBLIC API
# =============================================================================

def enhance_strategy_html(html: str) -> str:
    """Post-process Strategy report HTML to use CSS classes + inline styles.

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

    log.info("[HTML-ENHANCE] Strategy: %d \u2192 %d chars", original_len, len(html))
    return html


def enhance_kpa_html(html: str) -> str:
    """Post-process KPA (Gamechanger Deep Dive) HTML to use CSS classes + inline styles.

    Same core transforms as Strategy but simpler (fewer section types).
    """
    original_len = len(html)

    # 1. Table styling
    html = _transform_tables(html)

    # 2. Sources footer
    html = _transform_sources(html)

    # 3. Ampel badges
    html = _transform_ampel_badges(html)

    log.info("[HTML-ENHANCE] KPA: %d \u2192 %d chars", original_len, len(html))
    return html
