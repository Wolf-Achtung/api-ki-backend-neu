# -*- coding: utf-8 -*-
"""KIS-1322 — Testlauf KIS1291 (06.09.2026, Build 1544, Motion-Profil nach
KIS-1321). Entscheidungsblock mit vier Punkten (Log: DECISION-FINAL li=4),
Genus „Der Ablauf, der", Vendor-Etikett „rot (nur mit AVV …)", DSGVO-Note
stabil, kein Wächter-Treffer. Restbefunde im Code:

- R1 S. 27: „ein stabile Ablauf" — die Genus-Regel setzte den Artikel, nicht
  die Adjektiv-Endung.
- R1 S. 26: „für den Motion Designer, der Runway für Hintergrund-Loops nutzen"
  — Relativsatz mit „der" ist Singular.
- R1 S. 25: „Return on Investment (ROI (siehe Business Case) nach 12 Monaten"
  — der ROI-Ersatz zerriss die Klammer.
- Strategie S. 14: Quellenblock ohne Etikett („Metricool 2026 …; EU AI Act").
"""
from __future__ import annotations

import pytest


class TestGenusAdjektiv:
    @pytest.mark.parametrize("fn", ["apply_grammar_fixes", "apply_extended_siezen"])
    def test_ein_stabiler_ablauf(self, fn):
        from services import content_quality_enforcer as c
        out = getattr(c, fn)("<p>ist eine stabile Pipeline für zwei Kanäle.</p>")
        out = out[0] if isinstance(out, tuple) else out
        assert "ein stabiler Ablauf" in out

    def test_bestimmter_artikel_bleibt(self):
        from services.content_quality_enforcer import apply_grammar_fixes
        assert "Der stabile Ablauf" in apply_grammar_fixes("<p>Die stabile Pipeline läuft.</p>")[0]


class TestRelativsatz:
    def test_der_nutzen_wird_nutzt(self):
        from services.content_quality_enforcer import apply_grammar_fixes
        out, _ = apply_grammar_fixes("<p>für den Motion Designer, der Runway für Hintergrund-Loops nutzen, schafft eine Schulung.</p>")
        assert "der Runway für Hintergrund-Loops nutzt," in out

    def test_plural_bleibt(self):
        from services.content_quality_enforcer import apply_grammar_fixes
        html = "<p>Die Regeln, die Kunden nutzen, sind klar. Werkzeuge, die alle nutzen.</p>"
        assert apply_grammar_fixes(html)[0] == html


class TestRoiKlammer:
    def test_klammer_bleibt_ganz(self):
        from services.content_quality_enforcer import remove_roi_from_section
        html = "<p>" + "x" * 60 + " Return on Investment (ROI) von 22 % nach 12 Monaten.</p>"
        out, n = remove_roi_from_section(html, "FOERDERPOTENZIAL_HTML")
        assert n == 1 and "ROI (siehe Business Case) nach 12 Monaten" in out and "(ROI (" not in out

    def test_offene_klammer(self):
        from services.content_quality_enforcer import remove_roi_from_section
        html = "<p>" + "x" * 60 + " Die (ROI von 22 % nach 12 Monaten) sind solide.</p>"
        out, n = remove_roi_from_section(html, "FOERDERPOTENZIAL_HTML")
        assert n == 1 and "(ROI, siehe Business Case nach 12 Monaten)" in out


class TestQuellenEtikett:
    def test_block_ohne_etikett(self):
        from services.html_enhancer import _transform_sources
        out = _transform_sources('<div class="sources">Metricool 2026 Social Media Trendbericht; interne Analyse KI-Readiness Report; EU AI Act</div>')
        assert "<strong>Quellen:</strong> Metricool 2026" in out

    def test_block_mit_etikett_bleibt(self):
        from services.html_enhancer import _transform_sources
        out = _transform_sources('<div class="sources"><p>Quellen: Metricool 2026</p></div>')
        assert out.count("Quellen") == 1

    def test_englisch(self):
        from services.html_enhancer import _transform_sources
        out = _transform_sources('<div class="sources">Metricool 2026 market report; internal analysis</div>')
        assert "<strong>Sources:</strong>" in out
