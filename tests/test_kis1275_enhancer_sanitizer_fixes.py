# -*- coding: utf-8 -*-
"""KIS-1275 — Adversarial-Audit nach EN-Lauf 5: Enhancer-/Sanitizer-Fixes.

Deckt ab (ohne Netzwerk/LLM):
1. [P0] html_enhancer drehte die EN-Tabellen-Kompaktierung zurück:
   harden_wide_tables markiert kompakt-gehärtete EN-Tabellen mit
   data-ksj-hardened="1"; der Enhancer respektiert dort font-size/padding
   (bestehende Werte gewinnen, Typografie wird nie ergänzt — th/td erben
   die Kompaktschrift). End-to-End-Kette harden → enhance (inkl.
   _balance_column_widths) mit den vier Lauf-5-Tabellen inkl. RECHNERISCHER
   Spaltenbreiten-Verifikation: jedes nowrap-Token (Betrag/Datum/Enum) und
   jedes Header-Wort passt mit ~15 % Marge in seine Spalte
   (Modell: 180 mm Satzspiegel, 2×6 px Padding ≈ 3,2 mm,
   ~2,1 mm/Zeichen bei 0.8em·10pt, linear in em).
2. [P1] Bare "KI-Sicherheit" überlebt sanitize_en_locale_tokens idempotent
   (Lookbehind auf der Sicherheit-Regel + LOCALE-SHIELD-Eintrag).
3. [P2] \bTag(?=\s+\d) ist case-sensitiv — "tag 10 documents" bleibt.
4. [P2] _EN_AMOUNT_RE: mo nur mit Wortgrenze ("11.9 months" wird nicht
   zerlegt, "11.9 mo." weiter gewrappt).
5. [P2] Wort-Map nur in Textknoten: <style>/<script>/Attribute unangetastet.
6. [P2/P3] NBSP-Betrag ("4.800 €") gewrappt; \bNutzung\b→use;
   _en_wrap_amounts_nowrap ist bei Direkt-Doppelanwendung idempotent.

DE-Garantie: DE-Tabellen tragen den Marker nie — die volle Kette liefert
für DE byte-genau das Legacy-Styling (font-size:10pt, padding:10px/12px).
"""
import re

import pytest

from services.html_enhancer import (
    _style_table_headers,
    enhance_kpa_html,
    enhance_strategy_html,
)
from services.html_sanitizer import sanitize_en_locale_tokens
from services.style_lint import (
    _en_wrap_amounts_nowrap,
    harden_wide_tables,
)

NOWRAP = '<span style="white-space:nowrap">'

# --------------------------------------------------------------------------- #
# Die vier Lauf-5-Tabellen                                                    #
# --------------------------------------------------------------------------- #
TOOL_TABLE_7 = """<table><thead><tr>
<th>Tool</th><th>Vendor</th><th>Function</th><th>Price</th><th>GDPR compliance</th>
<th>Integration</th><th>Rating</th>
</tr></thead><tbody>
<tr><td>Copilot</td><td>Microsoft</td><td>Meeting documentation and drafting</td>
<td>30 € per member/month</td><td>Partial, depending on tenant setup</td>
<td>Deep integration into production workflows</td><td>Recommended</td></tr>
<tr><td>Fireflies</td><td>Fireflies.ai</td><td>Transcription of production meetings</td>
<td>18 € per seat</td><td>Partial, EU hosting available</td>
<td>Works with existing calendar stack</td><td>High</td></tr>
</tbody></table>"""

ROADMAP_TABLE_7 = """<table><thead><tr>
<th>Phase</th><th>Focus</th><th>Budget</th><th>Funding rate</th><th>Deadline</th>
<th>Owner</th><th>Path</th>
</tr></thead><tbody>
<tr><td>Foundations</td><td>Data quality</td><td>4,800 €</td><td>up to 50%</td>
<td>31.12.2026</td><td>Management</td><td>Standard</td></tr>
<tr><td>Scale</td><td>Automation</td><td>10,800 €</td><td>50%</td>
<td>Check current status</td><td>High</td><td>Scale-up</td></tr>
<tr><td>Optimize</td><td>Quality gates</td><td>8,400 €</td><td>up to 40%</td>
<td>30.06.2027</td><td>Team lead</td><td>Standard</td></tr>
</tbody></table>"""

FUNDING_TABLE_7 = """<table><thead><tr>
<th>Program</th><th>Funding body</th><th>Fit for your company</th><th>Funding rate</th>
<th>Max amount</th><th>Deadline</th><th>Path</th>
</tr></thead><tbody>
<tr><td>Digital Jetzt</td><td>BMWK</td><td>High</td><td>up to 50%</td>
<td>50.000 EUR</td><td>31.12.2026</td><td>Standard</td></tr>
<tr><td>go-digital</td><td>BMWK</td><td>Medium</td><td>50%</td>
<td>16.500 EUR</td><td>Check current status</td><td>Standard</td></tr>
</tbody></table>"""

PRIORITY_TABLE_5 = """<table><thead><tr>
<th>Action area</th><th>Impact</th><th>Effort</th><th>Priority</th><th>Timeline</th>
</tr></thead><tbody>
<tr><td>Automated transcription</td><td>High</td><td>Medium</td><td>1</td>
<td>Month 1-2</td></tr>
<tr><td>Rights clearance workflow</td><td>High</td><td>High</td><td>2</td>
<td>Month 3-4</td></tr>
<tr><td>Archive tagging</td><td>Medium</td><td>Low</td><td>3</td>
<td>Month 5-6</td></tr>
</tbody></table>"""

ALL_TABLES = {
    "tool": TOOL_TABLE_7,
    "roadmap": ROADMAP_TABLE_7,
    "funding": FUNDING_TABLE_7,
    "priority": PRIORITY_TABLE_5,
}

# --------------------------------------------------------------------------- #
# Rechenmodell (identisch zur Kalibrierung in style_lint):                    #
# 180 mm Satzspiegel, 2×6 px Zell-Padding ≈ 3,2 mm, ~2,1 mm/Zeichen bei      #
# font-size 0.8em auf 10-pt-Basis (linear in em), Sicherheitsmarge 15 %.     #
# --------------------------------------------------------------------------- #
PAGE_MM = 180.0
PAD_MM = 3.2
CHAR_MM_08 = 2.1
MARGIN = 1.15
EPS_MM = 0.2  # Rundung der colgroup-Prozente auf 0.1 (≈0.09 mm)

_ROW_RE = re.compile(r"<tr\b[^>]*>([\s\S]*?)</tr>", re.IGNORECASE)
_CELL_RE = re.compile(r"<t([dh])\b[^>]*>([\s\S]*?)</t\1[^>]*>", re.IGNORECASE)
_STRIP_RE = re.compile(r"<[^>]+>")
_NOWRAP_RE = re.compile(
    r'<span style="white-space:nowrap">([\s\S]*?)</span>', re.IGNORECASE
)


def _first_table(html: str) -> str:
    m = re.search(r"<table\b[^>]*>[\s\S]*?</table>", html, re.IGNORECASE)
    assert m, "keine Tabelle im Ergebnis"
    return m.group(0)


def _colgroup_widths(table: str):
    m = re.search(r"<colgroup>(.*?)</colgroup>", table, re.DOTALL)
    assert m, "kein colgroup gefunden"
    return [float(w) for w in re.findall(r"width:([\d.]+)%", m.group(1))]


def _table_font_em(table: str) -> float:
    open_tag = re.match(r"<table\b[^>]*>", table, re.IGNORECASE).group(0)
    m = re.search(r"font-size:([\d.]+)em", open_tag)
    assert m, f"Kompaktschrift fehlt am <table>: {open_tag}"
    return float(m.group(1))


def _column_requirements(table: str, ncols: int):
    """(Beschreibung, Zeichenlänge) des härtesten unteilbaren Inhalts je Spalte.

    Unteilbar sind: nowrap-Spans (Beträge/Daten/Enum-Zellen) und Header-
    Wörter (th trägt hyphens:none). Parser-basiert, keine Augenmaß-Werte."""
    hardest = [("", 0)] * ncols
    for row_inner in _ROW_RE.findall(table):
        cells = _CELL_RE.findall(row_inner)
        if len(cells) != ncols:
            continue
        for ci, (tag, cell) in enumerate(cells):
            candidates = []
            for span_inner in _NOWRAP_RE.findall(cell):
                text = " ".join(_STRIP_RE.sub(" ", span_inner).split())
                candidates.append(text)
            if tag.lower() == "h":
                text = " ".join(_STRIP_RE.sub(" ", cell).split())
                candidates.extend(text.replace("­", "").split())
            for cand in candidates:
                if len(cand) > hardest[ci][1]:
                    hardest[ci] = (cand, len(cand))
    return hardest


def _run_chain(table_html: str, enhancer=enhance_strategy_html) -> str:
    hardened, n = harden_wide_tables(table_html, lang="en")
    assert n >= 1
    return enhancer(hardened)


def _verify_columns_fit(final_html: str, label: str):
    table = _first_table(final_html)
    widths = _colgroup_widths(table)
    em = _table_font_em(table)
    char_mm = CHAR_MM_08 * em / 0.8
    hardest = _column_requirements(table, len(widths))
    for ci, w in enumerate(widths):
        token, n = hardest[ci]
        if not n:
            continue
        have_mm = w / 100.0 * PAGE_MM - PAD_MM
        need_mm = n * char_mm * MARGIN
        assert have_mm + EPS_MM >= need_mm, (
            f"[{label}] Spalte {ci} ('{token}', {n} Zeichen): "
            f"{have_mm:.1f} mm verfügbar < {need_mm:.1f} mm benötigt "
            f"(Breite {w:.1f} %, Schrift {em}em)"
        )


# --------------------------------------------------------------------------- #
# 1. E2E-Kette: harden → enhance (inkl. _balance_column_widths)               #
# --------------------------------------------------------------------------- #
class TestEndToEndChainEn:
    @pytest.mark.parametrize("label", list(ALL_TABLES))
    def test_compact_styles_survive_enhancer(self, label):
        out = _run_chain(ALL_TABLES[label])
        table = _first_table(out)
        open_tag = re.match(r"<table\b[^>]*>", table).group(0)
        # Kompaktschrift überlebt; Enhancer-Legacy-Typografie taucht nicht auf
        assert re.search(r"font-size:0\.8(?:6)?em", open_tag), open_tag
        assert "data-ksj-hardened" in open_tag
        assert "font-size:10pt" not in table
        assert "font-size:9pt" not in table
        assert "padding:10px 12px" not in table
        assert "padding:8px 12px" not in table
        # Kompakt-Padding + Hyphen-Regeln der Härtung bleiben erhalten
        assert "padding:4px 6px" in table
        assert "hyphens:none" in table    # th
        assert "hyphens:auto" in table    # td
        # Enhancer-Kosmetik (Farben/Borders) darf weiterhin dazu kommen
        assert "background:#1E3A5F" in table
        assert "border-bottom:1px solid #E5E7EB" in table

    @pytest.mark.parametrize("label", list(ALL_TABLES))
    def test_colgroup_survives_and_sums_100(self, label):
        out = _run_chain(ALL_TABLES[label])
        widths = _colgroup_widths(_first_table(out))
        assert len(widths) == (5 if label == "priority" else 7)
        assert round(sum(widths), 1) == 100.0
        # _balance_column_widths darf das colgroup nicht ersetzen (Guard)
        assert _first_table(out).count("<colgroup>") == 1

    @pytest.mark.parametrize("label", list(ALL_TABLES))
    def test_columns_carry_hard_tokens_with_margin(self, label):
        """Rechnerische Verifikation: jedes nowrap-Token und jedes Header-
        Wort passt mit ~15 % Marge in seine Spalte (Modell s. Kopf)."""
        out = _run_chain(ALL_TABLES[label])
        _verify_columns_fit(out, label)

    def test_kpa_chain_identical_guarantees(self):
        # KPA-Pfad: harden in render_deep_dive_html → enhance_kpa_html
        out = _run_chain(ROADMAP_TABLE_7, enhancer=enhance_kpa_html)
        table = _first_table(out)
        assert "font-size:10pt" not in table
        assert "padding:10px 12px" not in table
        assert "padding:4px 6px" in table
        _verify_columns_fit(out, "roadmap-kpa")

    def test_nowrap_amounts_dates_enums_survive_chain(self):
        out = _run_chain(ROADMAP_TABLE_7)
        assert f"{NOWRAP}10,800 €</span>" in out
        assert f"{NOWRAP}4,800 €</span>" in out
        assert f"{NOWRAP}31.12.2026</span>" in out
        assert f"{NOWRAP}Standard</span>" in out
        assert f"{NOWRAP}High</span>" in out

    def test_second_harden_pass_is_noop(self):
        # Strategy-Pfad härtet nach dem Enhancer erneut (colgroup-Guard)
        out = _run_chain(ROADMAP_TABLE_7)
        again, _ = harden_wide_tables(out, lang="en")
        assert again == out


# --------------------------------------------------------------------------- #
# 1b. Marker-Respekt des Enhancers (Unit)                                     #
# --------------------------------------------------------------------------- #
class TestMarkerRespect:
    def test_marked_cells_keep_font_and_padding(self):
        html = ('<table style="font-size:0.86em" data-ksj-hardened="1">'
                '<tr><th style="padding:4px 6px">A</th></tr>'
                '<tr><td style="padding:4px 6px">B</td></tr></table>')
        out = _style_table_headers(html, respect_existing=True)
        assert "padding:4px 6px" in out
        assert "padding:10px 12px" not in out
        assert "font-size:9pt" not in out
        # Kosmetik kommt trotzdem dazu
        assert "background:#1E3A5F" in out

    def test_unmarked_cells_get_legacy_styles(self):
        html = ('<table><tr><th style="padding:4px 6px">A</th></tr>'
                '<tr><td>B</td></tr></table>')
        out = _style_table_headers(html)
        # Legacy-Semantik (FIX-HE1): NEUE Properties gewinnen
        assert "padding:10px 12px" in out
        assert "padding:4px 6px" not in out
        assert "font-size:9pt" in out

    def test_only_compact_tables_carry_marker(self):
        # Kompakt (5+ Spalten) → Marker, KIS-1284 auch auf Deutsch
        out_en, _ = harden_wide_tables(PRIORITY_TABLE_5, lang="en")
        assert 'data-ksj-hardened="1"' in out_en
        out_de, _ = harden_wide_tables(PRIORITY_TABLE_5, lang="de")
        assert 'data-ksj-hardened="1"' in out_de
        # 4 Spalten (keine Kompaktierung) → kein Marker
        four = """<table><tr><th>Tool</th><th>Vendor</th><th>Function</th><th>Rating</th></tr>
<tr><td>Copilot</td><td>Microsoft</td><td>Drafting</td><td>Good</td></tr></table>"""
        out4, _ = harden_wide_tables(four, lang="en")
        assert "data-ksj-hardened" not in out4
        out4_de, _ = harden_wide_tables(four, lang="de")
        assert "data-ksj-hardened" not in out4_de

    def test_marker_not_duplicated_on_second_pass(self):
        out1, _ = harden_wide_tables(PRIORITY_TABLE_5, lang="en")
        out2, _ = harden_wide_tables(out1, lang="en")
        assert out2.count("data-ksj-hardened") == 1


# --------------------------------------------------------------------------- #
# 1c. DE-Kette: ab 5 Spalten gehaertet (KIS-1284), darunter Legacy-Styling    #
# --------------------------------------------------------------------------- #
DE_TABLE_7 = """<table><thead><tr>
<th>Phase</th><th>Fokus</th><th>Budget</th><th>Förderquote</th><th>Frist</th>
<th>Verantwortlich</th><th>Pfad</th>
</tr></thead><tbody>
<tr><td>Grundlagen</td><td>Datenqualität</td><td>4.800 €</td><td>bis 50%</td>
<td>31.12.2026</td><td>Geschäftsführung</td><td>Standard</td></tr>
<tr><td>Skalierung</td><td>Automatisierung</td><td>10.800 €</td><td>50%</td>
<td>Status prüfen</td><td>hoch</td><td>Scale-up</td></tr>
</tbody></table>"""


DE_TABLE_4 = """<table><thead><tr>
<th>Phase</th><th>Fokus</th><th>Budget</th><th>Pfad</th>
</tr></thead><tbody>
<tr><td>Grundlagen</td><td>Datenqualität</td><td>4.800 €</td><td>Standard</td></tr>
<tr><td>Skalierung</td><td>Automatisierung</td><td>10.800 €</td><td>Scale-up</td></tr>
</tbody></table>"""


class TestDeByteIdentity:
    def test_de_chain_survives_enhancer(self):
        """KIS-1284: Der Marker muss auch auf Deutsch halten.

        Ohne ihn setzt der Enhancer font-size:10pt und padding:10px/12px
        zurueck — genau die Werte, auf die die Spalten-Minima NICHT
        kalibriert sind (KIS-1275, Aufgabe 1a).
        """
        hardened, _ = harden_wide_tables(DE_TABLE_7, lang="de")
        out = enhance_strategy_html(hardened)
        table = _first_table(out)
        open_tag = re.match(r"<table\b[^>]*>", table).group(0)
        assert 'data-ksj-hardened="1"' in open_tag
        assert "font-size:0.8" in open_tag
        assert "font-size:10pt" not in open_tag
        assert "padding:4px 6px" in table
        # Deutsch trennt nur an gesetzten &shy;-Stellen.
        assert "hyphens:manual" in table
        assert "hyphens:auto" not in table
        # Das Datum bleibt am Stueck.
        assert '<span style="white-space:nowrap">31.12.2026</span>' in out

    def test_de_four_cols_keep_legacy_styling(self):
        """Unter fuenf Spalten aendert KIS-1284 nichts."""
        hardened, _ = harden_wide_tables(DE_TABLE_4, lang="de")
        out = enhance_strategy_html(hardened)
        assert "data-ksj-hardened" not in out
        assert "font-size:10pt" in out
        assert "padding:4px 6px" not in out
        assert "hyphens" not in out
        assert "nowrap" not in out

    def test_de_harden_default_and_explicit_identical(self):
        o1, n1 = harden_wide_tables(DE_TABLE_7)
        o2, n2 = harden_wide_tables(DE_TABLE_7, lang="de")
        assert o1 == o2 and n1 == n2

    def test_legacy_merge_semantics_new_wins_without_marker(self):
        # KIS-1275 (1d): Default-Semantik des Enhancers bleibt "neue gewinnen"
        # (DE byte-identisch) — nur der Marker schaltet auf respect_existing.
        html = ('<table style="font-size:12pt"><tr><th>A</th><th>B</th></tr>'
                '<tr><td>1</td><td>x</td></tr><tr><td>2</td><td>y</td></tr></table>')
        out = enhance_strategy_html(html)
        assert "font-size:10pt" in out
        assert "font-size:12pt" not in out


# --------------------------------------------------------------------------- #
# 2. "KI-Sicherheit" (bare) überlebt idempotent                               #
# --------------------------------------------------------------------------- #
class TestKiSicherheitIdempotent:
    def test_three_passes_byte_identical(self):
        html = ("<p>Die KI-Sicherheit hat Priorität. Mehr auf "
                "KI-Sicherheit.jetzt oder kontakt@ki-sicherheit.jetzt. "
                "KI im Alltag, Sicherheit zuerst.</p>")
        o1 = sanitize_en_locale_tokens(html, "en")
        o2 = sanitize_en_locale_tokens(o1, "en")
        o3 = sanitize_en_locale_tokens(o2, "en")
        assert o1 == o2 == o3
        assert "KI-Sicherheit " in o1 or "KI-Sicherheit." in o1
        assert "AI-Security" not in o1
        assert "KI-Security" not in o1
        assert "KI-Sicherheit.jetzt" in o1
        assert "kontakt@ki-sicherheit.jetzt" in o1
        # freistehende Tokens weiterhin übersetzt
        assert "AI im Alltag" in o1
        assert "Security zuerst" in o1

    def test_lowercase_brand_form_untouched(self):
        html = "<p>ki-sicherheit bleibt ki-sicherheit</p>"
        out = sanitize_en_locale_tokens(html, "en")
        assert "ki-Security" not in out
        assert "AI-Security" not in out

    def test_compound_not_broken(self):
        out = sanitize_en_locale_tokens("<p>Die KI-Sicherheitsstrategie</p>", "en")
        assert "KI-Sicherheitsstrategie" in out

    def test_de_unchanged(self):
        html = "<p>KI-Sicherheit und Sicherheit</p>"
        assert sanitize_en_locale_tokens(html, "de") == html


# --------------------------------------------------------------------------- #
# 3. tag/Tag case-sensitiv                                                    #
# --------------------------------------------------------------------------- #
class TestTagCaseSensitive:
    def test_lowercase_verb_before_number_untouched(self):
        html = "<p>Please tag 10 documents per week.</p>"
        assert sanitize_en_locale_tokens(html, "en") == html

    def test_uppercase_day_still_translated(self):
        out = sanitize_en_locale_tokens("<p>Tag 3: Kickoff</p>", "en")
        assert "Day 3: Kickoff" in out

    def test_verb_without_number_untouched(self):
        html = "<p>Tag existing transcripts.</p>"
        assert sanitize_en_locale_tokens(html, "en") == html

    def test_de_unchanged(self):
        html = "<p>tag 10 documents, Tag 3</p>"
        assert sanitize_en_locale_tokens(html, "de") == html


# --------------------------------------------------------------------------- #
# 4. months/mo-Spans                                                          #
# --------------------------------------------------------------------------- #
class TestMonthsNotSplit:
    def test_months_not_span_split(self):
        table = "<table><tr><td>11.9 months payback</td></tr></table>"
        out, n = _en_wrap_amounts_nowrap(table)
        assert "mo</span>nths" not in out
        assert f"{NOWRAP}11.9 mo" not in out

    def test_mo_dot_still_wrapped(self):
        table = "<table><tr><td>11.9 mo. payback</td></tr></table>"
        out, n = _en_wrap_amounts_nowrap(table)
        assert n == 1
        assert f"{NOWRAP}11.9 mo.</span>" in out

    def test_h_per_mo_still_wrapped(self):
        table = "<table><tr><td>25 h/mo. saved</td></tr></table>"
        out, n = _en_wrap_amounts_nowrap(table)
        assert n == 1
        assert f"{NOWRAP}25 h/mo.</span>" in out

    def test_months_via_harden_chain(self):
        table = ROADMAP_TABLE_7.replace("Check current status", "11.9 months")
        out, _ = harden_wide_tables(table, lang="en")
        assert "mo</span>nths" not in out


# --------------------------------------------------------------------------- #
# 5. Wort-Map nur in Textknoten (Tag-Split-Schutz)                            #
# --------------------------------------------------------------------------- #
class TestTagSplitProtection:
    def test_style_block_untouched(self):
        html = ("<style>.risiko{color:red}.ki-card{border:1px}</style>"
                "<p>Das Risiko im Umgang mit KI</p>")
        out = sanitize_en_locale_tokens(html, "en")
        assert ".risiko{color:red}" in out
        assert ".ki-card{border:1px}" in out
        assert "Risk" in out and "AI" in out

    def test_script_block_untouched(self):
        html = ("<script>var risiko = 'Daten';</script>"
                "<p>Risiko und Daten</p>")
        out = sanitize_en_locale_tokens(html, "en")
        assert "var risiko = 'Daten';" in out
        assert "Risk" in out and "Data" in out

    def test_attributes_untouched(self):
        html = ('<div class="ki-card risiko-box" data-risiko="hoch" '
                'id="analyse-1"><p>Analyse des Risiko</p></div>')
        out = sanitize_en_locale_tokens(html, "en")
        assert 'class="ki-card risiko-box"' in out
        assert 'data-risiko="hoch"' in out
        assert 'id="analyse-1"' in out
        assert "Analysis" in out and "Risk" in out

    def test_alt_title_no_longer_translated(self):
        # BEWUSSTE Nebenwirkung des Tag-Splits (dokumentiert): sichtbare
        # Attributtexte (alt/title) werden nicht mehr übersetzt.
        html = '<img alt="Risiko Matrix" title="Analyse">'
        out = sanitize_en_locale_tokens(html, "en")
        assert 'alt="Risiko Matrix"' in out
        assert 'title="Analyse"' in out

    def test_tag_context_rules_still_work(self):
        out = sanitize_en_locale_tokens(
            "<h4>Empfehlungen</h4><td>Nutzen</td><td> Unternehmen </td>", "en")
        assert ">Recommendations<" in out
        assert ">Benefits<" in out
        assert "> Company <" in out

    def test_shield_still_works_after_split(self):
        html = ('<p>Besuchen Sie https://ki-sicherheit.jetzt/de und schreiben '
                'Sie an kontakt@ki-sicherheit.jetzt</p>')
        out = sanitize_en_locale_tokens(html, "en")
        assert "https://ki-sicherheit.jetzt/de" in out
        assert "kontakt@ki-sicherheit.jetzt" in out

    def test_de_unchanged(self):
        html = ('<style>.risiko{}</style><div class="ki-card">'
                '<p>Risiko</p></div>')
        assert sanitize_en_locale_tokens(html, "de") == html


# --------------------------------------------------------------------------- #
# 6. NBSP-Betrag, Nutzung-Mapping, Doppelanwendungs-Guard                     #
# --------------------------------------------------------------------------- #
class TestSmallFixes:
    def test_nbsp_amount_wrapped(self):
        table = "<table><tr><td>4.800 € budget</td></tr></table>"
        out, n = _en_wrap_amounts_nowrap(table)
        assert n == 1
        assert f"{NOWRAP}4.800 €</span>" in out

    def test_nbsp_entity_amount_wrapped(self):
        table = "<table><tr><td>4.800&nbsp;€ budget</td></tr></table>"
        out, n = _en_wrap_amounts_nowrap(table)
        assert n == 1
        assert f"{NOWRAP}4.800&nbsp;€</span>" in out

    def test_nutzung_mapping(self):
        out = sanitize_en_locale_tokens(
            "<p>DSGVO-konforme Nutzung von Tools</p>", "en")
        assert "GDPR-compliant use" in out
        assert "Nutzung" not in out

    def test_nutzung_compound_untouched(self):
        out = sanitize_en_locale_tokens("<p>Die Nutzungsrechte</p>", "en")
        assert "Nutzungsrechte" in out

    def test_amount_wrap_direct_double_application_idempotent(self):
        table = ('<table><tr><td>10,800 € and 31.12.2026 and '
                 '<span style="white-space:nowrap">4,800 €</span></td>'
                 '<td>Medium</td></tr></table>')
        once, _ = _en_wrap_amounts_nowrap(table)
        twice, n2 = _en_wrap_amounts_nowrap(once)
        assert twice == once
        assert f"{NOWRAP}{NOWRAP}" not in twice


# --------------------------------------------------------------------------- #
# 7. Fail-open-Sektionen des Sprachgates (Marker des Parallel-Agents)         #
# --------------------------------------------------------------------------- #
FAILOPEN = "<!--ksj-lang-failopen-->"


class TestFailopenSkip:
    def test_marker_matches_language_sweep_constant(self):
        import gpt_analyze as g
        from services import html_sanitizer as hs
        assert hs._LANG_FAILOPEN_MARKER == g._LANG_SWEEP_FAILOPEN_MARKER

    def test_failopen_section_untouched_others_sanitized(self):
        html = (
            '<section><p>Das Risiko steigt.</p></section>'
            f'<section>{FAILOPEN}<p>Das Risiko und die Daten. 24.000 €.</p>'
            '</section>'
            '<section><p>Die Daten fehlen.</p></section>'
        )
        out = sanitize_en_locale_tokens(html, "en")
        # fail-open-Bereich: byte-identisch inkl. Marker + DE-Zahlenformat
        assert f'{FAILOPEN}<p>Das Risiko und die Daten. 24.000 €.</p>' in out
        # Sektionen davor/danach werden weiter sanitisiert
        assert "Das Risk steigt." in out
        assert "Die Data fehlen." in out

    def test_explicit_end_marker_supported(self):
        html = (
            f'<p>{FAILOPEN}Risiko<!--/ksj-lang-failopen--> und Risiko</p>'
        )
        out = sanitize_en_locale_tokens(html, "en")
        assert f"{FAILOPEN}Risiko<!--/ksj-lang-failopen-->" in out
        assert "und Risk" in out

    def test_failopen_without_section_end_runs_to_string_end(self):
        html = f'<p>Daten zuerst.</p>{FAILOPEN}<p>Daten danach.</p>'
        out = sanitize_en_locale_tokens(html, "en")
        assert "Data zuerst." in out
        assert f"{FAILOPEN}<p>Daten danach.</p>" in out

    def test_idempotent(self):
        html = (
            f'<section>{FAILOPEN}<p>Das Projekt trägt sich.</p></section>'
            '<section><p>Risiko</p></section>'
        )
        o1 = sanitize_en_locale_tokens(html, "en")
        o2 = sanitize_en_locale_tokens(o1, "en")
        assert o1 == o2
        assert "Das Projekt trägt sich." in o1
        assert ">Risk<" in o1

    def test_de_unchanged(self):
        html = f'<section>{FAILOPEN}<p>Daten</p></section>'
        assert sanitize_en_locale_tokens(html, "de") == html


class TestMinifierKeepsFailopenMarker:
    """KIS-1275 Handoff: compress_html darf die Sprachgate-Marker nicht
    strippen — der Renderer-Sanitize-Hook läuft nach der Minifizierung."""

    def test_failopen_markers_survive_compress(self):
        from services.html_minifier import compress_html
        html = ('<div><!--ksj-lang-failopen--><p>Deutscher Text bleibt.</p>'
                '<!--/ksj-lang-failopen--><!-- normaler kommentar --></div>')
        out = compress_html(html)
        assert '<!--ksj-lang-failopen-->' in out
        assert '<!--/ksj-lang-failopen-->' in out
        assert 'normaler kommentar' not in out

    def test_conditional_comments_still_kept(self):
        from services.html_minifier import compress_html
        html = '<!--[if IE]>x<![endif]--><!-- drop -->'
        out = compress_html(html)
        assert '[if IE]' in out
        assert 'drop' not in out
