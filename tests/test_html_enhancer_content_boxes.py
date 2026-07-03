# -*- coding: utf-8 -*-
"""Unit tests for html_enhancer content box patterns (Rules 8-14)."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.html_enhancer import _transform_content_boxes


class TestAufEinenBlick:
    """2A: 'Auf einen Blick:' → blue highlight box."""

    def test_basic(self):
        html = '<p><strong>Auf einen Blick:</strong> Dies ist eine Zusammenfassung.</p>'
        result = _transform_content_boxes(html)
        assert 'background:#ebf5fb' in result
        assert 'border-left:4px solid #2e86c1' in result
        assert '<strong>Auf einen Blick:</strong>' in result
        assert 'Dies ist eine Zusammenfassung.' in result
        assert '<p>' not in result  # replaced with <div>

    def test_without_colon(self):
        html = '<p><strong>Auf einen Blick</strong> Kurzfassung hier.</p>'
        result = _transform_content_boxes(html)
        assert 'background:#ebf5fb' in result


class TestTippBox:
    """2B: 'Tipp/Praxis-Tipp/Hinweis:' → green tip box."""

    def test_tipp(self):
        html = '<p><strong>Tipp:</strong> Starten Sie mit einem Pilotprojekt.</p>'
        result = _transform_content_boxes(html)
        assert 'background:#f0fdf4' in result
        assert 'border:1px solid #bbf7d0' in result
        assert '<strong>Tipp:</strong>' in result

    def test_praxis_tipp(self):
        html = '<p><strong>Praxis-Tipp:</strong> Nutzen Sie bestehende Workflows.</p>'
        result = _transform_content_boxes(html)
        assert 'background:#f0fdf4' in result

    def test_hinweis(self):
        html = '<p><strong>Hinweis:</strong> Beachten Sie die DSGVO-Anforderungen.</p>'
        result = _transform_content_boxes(html)
        assert 'background:#f0fdf4' in result


class TestWarnungBox:
    """2C: 'Wichtig/Achtung/Warnung:' → yellow warning box."""

    def test_wichtig(self):
        html = '<p><strong>Wichtig:</strong> Ohne Datenschutzkonzept drohen Bußgelder.</p>'
        result = _transform_content_boxes(html)
        assert 'background:#fffbeb' in result
        assert 'border:1px solid #fde68a' in result

    def test_achtung(self):
        html = '<p><strong>Achtung:</strong> EU AI Act Frist beachten.</p>'
        result = _transform_content_boxes(html)
        assert 'background:#fffbeb' in result

    def test_warnung(self):
        html = '<p><strong>Warnung:</strong> Hohes Risiko bei fehlender Compliance.</p>'
        result = _transform_content_boxes(html)
        assert 'background:#fffbeb' in result


class TestEmpfehlungBox:
    """2D: 'Empfehlung/Investitionsempfehlung/Handlungsempfehlung:' → blue gradient box."""

    def test_empfehlung(self):
        html = '<p><strong>Empfehlung:</strong> Investieren Sie in KI-Schulungen.</p>'
        result = _transform_content_boxes(html)
        assert 'background:linear-gradient(135deg,#eff6ff,#e0f2fe)' in result
        assert 'border-left:4px solid #2563eb' in result

    def test_investitionsempfehlung(self):
        html = '<p><strong>Investitionsempfehlung:</strong> Budget von 48.000 € einplanen.</p>'
        result = _transform_content_boxes(html)
        assert 'background:linear-gradient(135deg,#eff6ff,#e0f2fe)' in result

    def test_handlungsempfehlung(self):
        html = '<p><strong>Handlungsempfehlung:</strong> Sofort mit Phase 1 beginnen.</p>'
        result = _transform_content_boxes(html)
        assert '#2563eb' in result


class TestAmpelBadgesInTd:
    """2E: Ampel keywords in <td> → colored badges."""

    def test_hoch(self):
        html = '<td>Hoch </td>'
        result = _transform_content_boxes(html)
        assert 'background:#ecfdf5' in result
        assert 'color:#047857' in result
        assert '>Hoch</span>' in result

    def test_mittel(self):
        html = '<td>Mittel </td>'
        result = _transform_content_boxes(html)
        assert 'background:#fffbeb' in result
        assert 'color:#b45309' in result
        assert '>Mittel</span>' in result

    def test_niedrig(self):
        html = '<td>Niedrig </td>'
        result = _transform_content_boxes(html)
        assert 'background:#fef2f2' in result
        assert 'color:#b91c1c' in result
        assert '>Niedrig</span>' in result

    def test_with_strong(self):
        html = '<td><strong>Hoch</strong> </td>'
        result = _transform_content_boxes(html)
        assert '>Hoch</span>' in result

    def test_td_with_attrs(self):
        html = '<td style="padding:8px">Mittel </td>'
        result = _transform_content_boxes(html)
        assert '>Mittel</span>' in result


class TestQuickWinBadge:
    """2F: 'Quick Win' → blue inline badge."""

    def test_prose_mention_stays_plain(self):
        # KIS-1235: Badge mitten im Satz war semantisch schief ("Der [Quick
        # Win] liegt darin…") — Fließtext-Erwähnungen bleiben jetzt Text.
        html = '<p>Dies ist ein Quick Win für Ihr Unternehmen.</p>'
        result = _transform_content_boxes(html)
        assert result == html

    def test_element_initial_gets_badge(self):
        html = '<td>Quick Win</td>'
        result = _transform_content_boxes(html)
        assert 'background:#dbeafe' in result
        assert '>Quick Win</span>' in result

    def test_not_in_class_attr(self):
        html = '<div class="quick-win-card">Content</div>'
        result = _transform_content_boxes(html)
        # Should NOT match inside attribute values
        assert result == html


class TestQuellenFooter:
    """2G: 'Quellen:' → dezenter footer."""

    def test_basic(self):
        html = '<p><strong>Quellen:</strong> McKinsey 2025, Gartner 2024</p>'
        result = _transform_content_boxes(html)
        assert 'font-size:8pt' in result
        assert 'color:#9CA3AF' in result
        assert 'border-top:1px solid #E5E7EB' in result
        assert 'McKinsey 2025' in result

    def test_quelle_singular(self):
        html = '<p><strong>Quelle:</strong> Bitkom 2025</p>'
        result = _transform_content_boxes(html)
        assert 'font-size:8pt' in result


class TestNoFalsePositives:
    """Ensure patterns don't match where they shouldn't."""

    def test_normal_paragraph_unchanged(self):
        html = '<p>Ein normaler Absatz ohne spezielle Keywords.</p>'
        result = _transform_content_boxes(html)
        assert result == html

    def test_table_content_unchanged(self):
        html = '<table><tr><th>Header</th></tr><tr><td>Normal content </td></tr></table>'
        result = _transform_content_boxes(html)
        # "Normal content" should not be transformed
        assert 'Normal content' in result
