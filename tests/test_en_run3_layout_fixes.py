# -*- coding: utf-8 -*-
"""EN-Testlauf 3 — Layout-/String-Restbefunde (KIS-EN3).

Deckt ab:
A. harden_wide_tables: Mindestbreiten + inhaltsbasierte Spalten-Klassifikation
   (Repro der vier Befund-Tabellen aus Lauf 3):
   (a) R2 Tool-Tabelle, GDPR-Spalte ("Parti al to yes, dep endi ng …")
   (b) R2 Risikotabelle, TOP-RISK-Spalte ("Confidentia l production material")
   (c) Fördertabelle, DEADLINE-Spalte ("Check curre nt status",
       "until 31.12. 2026") + Datumsschutz (non-breaking)
   (d) "FIT FOR YOUR COMPANY" vierzeilig gestapelt → Header-Kürzung "Fit"
   DE bleibt byte-identisch (lang-Gate).
B. EN-Zahlenformat: normalize_en_number_formats im Strategy-Renderer (Quelle)
   und im KPA-Renderer (render_deep_dive_html, lang=en).
C. KPA-Strings: EN-Glance-Strip ("At a glance"), Critical-Badge,
   EN-gc_*-Prompt-Korrekturen, EN-Direktive, Waisen-Überschrift.
"""
import inspect
import re
from pathlib import Path

import pytest

from services.style_lint import (
    _EN_PCT_PER_CHAR,
    _en_column_stats,
    harden_wide_tables,
)


def _colgroup_widths(html: str):
    m = re.search(r"<colgroup>(.*?)</colgroup>", html, re.DOTALL)
    assert m, "kein colgroup gefunden"
    return [float(w) for w in re.findall(r"width:([\d.]+)%", m.group(1))]


def _assert_no_fragmentation(html: str, widths):
    """Fragmentierungs-Bedingung: jede Spalte trägt ihr längstes Token.

    Spaltenbreite (in %) muss mindestens (Tokenlänge+1) × PCT_PER_CHAR
    hergeben — sonst bricht Chromium ohne Trennstelle mitten im Wort.
    Für nowrap-geschützte Daten zählt das Token ebenfalls.
    """
    table_m = re.search(r"<table\b[^>]*>[\s\S]*?</table>", html)
    assert table_m
    _, max_token = _en_column_stats(table_m.group(0), len(widths))
    for ci, w in enumerate(widths):
        need = (max_token[ci] + 1) * _EN_PCT_PER_CHAR
        assert w >= min(26.0, need) - 0.1, (
            f"Spalte {ci}: {w:.1f}% zu schmal für Token "
            f"({max_token[ci]} Zeichen braucht {need:.1f}%)"
        )


# --------------------------------------------------------------------------- #
# A(a): R2 Tool-Tabelle — GDPR-Spalte mit langer Textzelle                     #
# --------------------------------------------------------------------------- #
TOOL_TABLE = """<table><thead><tr>
<th>Use case</th><th>Tool</th><th>Vendor</th><th>Recommendation</th><th>GDPR compliance</th>
</tr></thead><tbody>
<tr><td>Script drafting</td><td>Microsoft 365 Copilot</td><td>Microsoft</td>
<td>Recommended for drafting treatments; needs an editorial review step</td>
<td>Partial to yes, depending on tenant setup and data residency configuration</td></tr>
</tbody></table>"""

# A(b): R2 Risikotabelle — TOP-RISK-Spalte
RISK_TABLE = """<table><thead><tr>
<th>Top risk</th><th>Likelihood</th><th>Impact</th><th>Mitigation</th><th>Owner</th>
</tr></thead><tbody>
<tr><td>Confidential production material</td><td>Medium</td><td>High</td>
<td>Access controls, DPA with all vendors, staff training</td><td>Management</td></tr>
</tbody></table>"""

# A(c)+(d): Fördertabelle — DEADLINE-Kurzphrasen/Datum + FIT-Header
FUNDING_TABLE = """<table><thead><tr>
<th>Program</th><th>Funding body</th><th>Fit for your company</th><th>Funding rate</th>
<th>Max amount</th><th>Deadline</th><th>Link</th>
</tr></thead><tbody>
<tr><td>Digital Jetzt</td><td>BMWK</td><td>High</td><td>up to 50%</td>
<td>50.000 EUR</td><td>Check current status</td><td>example.org</td></tr>
<tr><td>go-digital</td><td>BMWK</td><td>Medium</td><td>50%</td>
<td>16.500 EUR</td><td>until 31.12.2026</td><td>example.org</td></tr>
</tbody></table>"""


class TestColumnMinWidthsEn:
    def test_gdpr_text_column_classified_wide(self):
        out, n = harden_wide_tables(TOOL_TABLE, lang="en")
        assert n >= 1
        widths = _colgroup_widths(out)
        # Text-lastige Spalte (>40 Zeichen) → mindestens 18 %
        assert widths[4] >= 18.0
        _assert_no_fragmentation(out, widths)

    def test_top_risk_column_carries_confidential(self):
        out, n = harden_wide_tables(RISK_TABLE, lang="en")
        assert n >= 1
        widths = _colgroup_widths(out)
        # "Confidential" (12 Zeichen) darf nicht fragmentieren
        assert widths[0] >= (12 + 1) * _EN_PCT_PER_CHAR - 0.1
        _assert_no_fragmentation(out, widths)

    def test_deadline_column_and_date_protection(self):
        out, n = harden_wide_tables(FUNDING_TABLE, lang="en")
        assert n >= 1
        widths = _colgroup_widths(out)
        # "Check current status": kein Buchstabenumbruch ("curre nt")
        assert widths[5] >= (7 + 1) * _EN_PCT_PER_CHAR - 0.1
        # Datumsschutz: 31.12.2026 non-breaking
        assert '<span style="white-space:nowrap">31.12.2026</span>' in out
        _assert_no_fragmentation(out, widths)

    def test_fit_header_shortened(self):
        out, _ = harden_wide_tables(FUNDING_TABLE, lang="en")
        assert "Fit for your company" not in out
        assert ">Fit<" in out or ">Fit</th>" in out.replace("\n", "")

    def test_base_minimum_widths(self):
        # ≤5 Spalten → min 10 %, 6+ Spalten → min 8 %
        out5, _ = harden_wide_tables(TOOL_TABLE, lang="en")
        assert min(_colgroup_widths(out5)) >= 10.0 - 0.05
        out7, _ = harden_wide_tables(FUNDING_TABLE, lang="en")
        assert min(_colgroup_widths(out7)) >= 8.0 - 0.05

    def test_widths_sum_to_100(self):
        for table in (TOOL_TABLE, RISK_TABLE, FUNDING_TABLE):
            out, _ = harden_wide_tables(table, lang="en")
            assert sum(_colgroup_widths(out)) == pytest.approx(100.0, abs=0.5)


class TestDeByteIdentity:
    DE_TABLE = """<table><thead><tr>
<th>Handlungsfeld</th><th>Impact</th><th>Aufwand</th><th>Priorität</th><th>Frist</th>
</tr></thead><tbody>
<tr><td>Prozesse automatisieren</td><td>hoch</td><td>mittel</td><td>1</td>
<td>bis 31.12.2026</td></tr>
</tbody></table>"""

    def test_de_default_and_explicit_identical(self):
        o1, n1 = harden_wide_tables(self.DE_TABLE)
        o2, n2 = harden_wide_tables(self.DE_TABLE, lang="de")
        assert o1 == o2 and n1 == n2

    def test_de_widths_respect_content(self):
        """KIS-1284: Die alte DE-Formel leitete die Breite allein aus der
        Kopfzeile ab und liess 6-%-Spalten zu — rund vier Zeichen breit.
        Jetzt traegt jede Spalte ihren laengsten unteilbaren Inhalt."""
        out, _ = harden_wide_tables(self.DE_TABLE, lang="de")
        widths = _colgroup_widths(out)
        assert len(widths) == 5
        assert sum(widths) == pytest.approx(100.0, abs=0.2)
        # "bis 31.12.2026" (10 Zeichen nowrap) braucht ~15 %.
        assert widths[4] >= 15.0, widths

    def test_de_date_is_nowrap(self):
        """Lauf 1268 druckte "Bis 31.1 2.20 26" (Strategie S. 30)."""
        out, _ = harden_wide_tables(self.DE_TABLE, lang="de")
        assert '<span style="white-space:nowrap">31.12.2026</span>' in out


# --------------------------------------------------------------------------- #
# B: EN-Zahlenformat im Strategy- und KPA-Renderer                             #
# --------------------------------------------------------------------------- #
class TestEnNumberFormat:
    def test_strategy_renderer_calls_normalizer_for_en(self):
        from services.strategy_renderer import render_strategy_html
        src = inspect.getsource(render_strategy_html)
        assert "normalize_en_number_formats" in src
        # Gate auf EN (DE byte-identisch)
        assert "if _ctx_en:" in src

    def test_kpa_render_en_normalizes_numbers(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        sections = {
            'GC_BRUCHPUNKT_HTML': '<p>Section 1</p>',
            'GC_IMPL_PLAN_HTML': '<p>Section 2</p>',
            'BC_DEEP_DIVE_HTML': '<p>Section 3</p>',
            'GC_RISK_HTML': '<p>Investment of 24.000 € with 28.500 € upside.</p>',
            'GC_NEXT_STEPS_HTML': '<p>Section 5</p>',
        }
        context = {
            'LANG': 'en', 'lang': 'en', 'COMPANY_SIZE': 'team',
            'UNTERNEHMENSGROESSE_LABEL': 'Team (2–10 Mitarbeitende)',
            'BRANCHE_LABEL': 'Medien & Kreativwirtschaft',
            'HAUPTLEISTUNG': 'Filmproduktion', 'kundencode': 'TEST-1',
            'briefing_id': 4711, 'score_gesamt': 55,
        }
        html = render_deep_dive_html(dict(sections), dict(context))
        assert '24,000 €' in html
        assert '28,500 €' in html
        assert '24.000 €' not in html

    def test_kpa_render_de_keeps_german_format(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        sections = {
            'GC_BRUCHPUNKT_HTML': '<p>Abschnitt 1</p>',
            'GC_IMPL_PLAN_HTML': '<p>Abschnitt 2</p>',
            'BC_DEEP_DIVE_HTML': '<p>Abschnitt 3</p>',
            'GC_RISK_HTML': '<p>Investition von 24.000 € geplant.</p>',
            'GC_NEXT_STEPS_HTML': '<p>Abschnitt 5</p>',
        }
        context = {
            'LANG': 'de', 'lang': 'de', 'COMPANY_SIZE': 'team',
            'UNTERNEHMENSGROESSE_LABEL': 'Team (2–10 Mitarbeitende)',
            'BRANCHE_LABEL': 'Medien & Kreativwirtschaft',
            'HAUPTLEISTUNG': 'Filmproduktion', 'kundencode': 'TEST-1',
            'briefing_id': 4711, 'score_gesamt': 55,
        }
        html = render_deep_dive_html(dict(sections), dict(context))
        assert '24.000 €' in html
        assert '24,000 €' not in html


# --------------------------------------------------------------------------- #
# C: KPA-String-Fixes                                                          #
# --------------------------------------------------------------------------- #
class TestGlanceStripEn:
    def test_en_at_a_glance_stripped(self):
        from services.gamechanger_deep_dive import _strip_leading_glance_box
        html = ('<p><strong>At a glance:</strong> Core message here.</p>'
                '<p>Real content.</p>')
        assert _strip_leading_glance_box(html) == '<p>Real content.</p>'

    def test_de_auf_einen_blick_still_stripped(self):
        from services.gamechanger_deep_dive import _strip_leading_glance_box
        html = ('<p><strong>Auf einen Blick:</strong> Kernbotschaft.</p>'
                '<p>Inhalt.</p>')
        assert _strip_leading_glance_box(html) == '<p>Inhalt.</p>'

    def test_mid_document_glance_kept(self):
        from services.gamechanger_deep_dive import _strip_leading_glance_box
        html = '<p>Intro.</p><p><strong>At a glance:</strong> later box.</p>'
        assert _strip_leading_glance_box(html) == html


class TestCriticalBadge:
    def test_whole_cell_critical_becomes_red_badge(self):
        from services.html_enhancer import _transform_content_boxes
        html = '<table><tr><td>Critical</td></tr></table>'
        out = _transform_content_boxes(html)
        assert '>Critical</span>' in out
        assert '#b91c1c' in out

    def test_range_value_stays_text(self):
        from services.html_enhancer import _transform_content_boxes
        html = '<table><tr><td>Medium to high</td></tr></table>'
        out = _transform_content_boxes(html)
        assert 'Medium to high' in out
        # kein Badge um den Wertebereich
        assert '>Medium</span> to high' not in out


class TestEnGcPrompts:
    PROMPTS = [
        Path('prompts/en/gc_strategic_analysis.md'),
        Path('prompts/en/gc_implementation_plan.md'),
        Path('prompts/en/gc_risk_assessment.md'),
        Path('prompts/en/gc_next_steps.md'),
    ]

    def test_no_german_regulation_parenthesis(self):
        for p in self.PROMPTS:
            text = p.read_text(encoding='utf-8')
            assert 'KI-Verordnung' not in text, p
            assert "the EU's AI regulation" not in text, p
            if 'EU AI Act' in text:
                assert 'the EU AI regulation' in text, p

    def test_no_dsgvo_parenthesis(self):
        text = self.PROMPTS[0].read_text(encoding='utf-8')
        assert 'GDPR (DSGVO)' not in text

    def test_tool_lowercase_rule(self):
        for p in self.PROMPTS:
            text = p.read_text(encoding='utf-8')
            assert '"Tool" = software' not in text, p
            assert '"tool" = software' in text, p
            assert 'tool, not Tool' in text, p

    def test_en_directive_translation_list(self):
        from services.gamechanger_deep_dive import _generate_gc_section
        src = inspect.getsource(_generate_gc_section)
        assert 'EU AI regulation' in src
        assert 'GDPR-related' in src
        assert 'not Tool' in src or "'tool', not 'Tool'" in src


class TestOrphanHeadingEn:
    SECTIONS = {
        'GC_BRUCHPUNKT_HTML': ('<p>Analysis text.</p>'
                               '<p><strong>First concrete step</strong></p>'
                               '<p>Start with a two-week pilot.</p>'),
        'GC_IMPL_PLAN_HTML': '<p>Section 2</p>',
        'BC_DEEP_DIVE_HTML': '<p>Section 3</p>',
        'GC_RISK_HTML': '<p>Section 4</p>',
        'GC_NEXT_STEPS_HTML': '<p>Section 5</p>',
    }
    CONTEXT = {
        'COMPANY_SIZE': 'team',
        'UNTERNEHMENSGROESSE_LABEL': 'Team (2–10 Mitarbeitende)',
        'BRANCHE_LABEL': 'Medien & Kreativwirtschaft',
        'HAUPTLEISTUNG': 'Filmproduktion', 'kundencode': 'TEST-1',
        'briefing_id': 4711, 'score_gesamt': 55,
    }

    def test_en_pseudo_heading_gets_break_avoid(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        ctx = dict(self.CONTEXT, LANG='en', lang='en')
        html = render_deep_dive_html(dict(self.SECTIONS), ctx)
        assert ('<p style="break-after:avoid;page-break-after:avoid">'
                '<strong>First concrete step</strong></p>') in html

    def test_label_paragraph_untouched(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        sections = dict(self.SECTIONS)
        sections['GC_RISK_HTML'] = ('<p><strong>Important:</strong> check the '
                                    'DPA first.</p><p>More.</p>')
        ctx = dict(self.CONTEXT, LANG='en', lang='en')
        html = render_deep_dive_html(sections, ctx)
        assert '<p><strong>Important:</strong> check the DPA first.</p>' in html

    def test_de_render_unchanged(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        sections = dict(self.SECTIONS)
        sections['GC_BRUCHPUNKT_HTML'] = (
            '<p>Text.</p><p><strong>Erster konkreter Schritt</strong></p>'
            '<p>Start.</p>')
        ctx = dict(self.CONTEXT, LANG='de', lang='de')
        html = render_deep_dive_html(sections, ctx)
        assert 'break-after:avoid"><strong>Erster konkreter Schritt' not in html
        assert '<p><strong>Erster konkreter Schritt</strong></p>' in html
