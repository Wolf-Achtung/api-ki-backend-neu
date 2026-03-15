# -*- coding: utf-8 -*-
"""Tests for FIX-HE1: Style-merge in html_enhancer.py.

Ensures no duplicate style attributes on HTML elements after enhancement.
"""

import re
from services.html_enhancer import enhance_strategy_html, _style_table_headers


class TestNoDuplicateStyleAttributes:
    """Enhanced HTML must never have two style attributes on one element."""

    def test_th_with_existing_style_merged(self):
        """<th> with existing style must get styles merged, not duplicated."""
        html = '<table><tr><th style="padding:8px;text-align:left">Header</th></tr></table>'
        result = _style_table_headers(html)
        th_tag = re.search(r'<th[^>]*>', result)
        assert th_tag is not None
        assert th_tag.group(0).count('style=') == 1

    def test_td_with_existing_style_merged(self):
        """<td> with existing style must get styles merged, not duplicated."""
        html = '<table><tr><td style="padding:8px;text-align:left">Data</td></tr></table>'
        result = _style_table_headers(html)
        td_tag = re.search(r'<td[^>]*>', result)
        assert td_tag is not None
        assert td_tag.group(0).count('style=') == 1
        # Original styles must still be present
        assert 'padding:8px' in td_tag.group(0)

    def test_th_without_style_gets_new_style(self):
        """<th> without style gets a new style attribute."""
        html = '<table><tr><th>Header</th></tr></table>'
        result = _style_table_headers(html)
        th_tag = re.search(r'<th[^>]*>', result)
        assert th_tag is not None
        assert 'style=' in th_tag.group(0)
        assert th_tag.group(0).count('style=') == 1

    def test_full_enhance_no_double_styles(self):
        """Full enhance_strategy_html must not produce double style attributes."""
        html = (
            '<table>'
            '<tr><th style="padding:8px;text-align:left;border-bottom:2px solid #cbd5e1">Kategorie</th>'
            '<th style="padding:8px">Wert</th></tr>'
            '<tr><td style="font-weight:bold">ROI</td><td>239%</td></tr>'
            '</table>'
        )
        result = enhance_strategy_html(html)
        # Find all tags and check none have duplicate style=
        all_tags = re.findall(r'<(?:th|td|tr|table|div)[^>]*>', result)
        for tag in all_tags:
            assert tag.count('style=') <= 1, f"Duplicate style= in: {tag}"
