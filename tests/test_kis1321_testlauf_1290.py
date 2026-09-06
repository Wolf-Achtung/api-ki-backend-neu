# -*- coding: utf-8 -*-
"""KIS-1321 — Testlauf KIS1290 (06.09.2026, Build 1510, Motion-Profil nach
KIS-1320). DSGVO-Note stabil (Mittel, C), Satzzeichen sauber, Quellen mit
Etikett, kein Wächter-Treffer. Restbefunde im Code:

- R1 S. 4: „Ihre Entscheidung in 3 Punkten." ohne die drei Punkte und ohne
  die Investitions-Zeile — das Netz aus KIS-1316 lief vor dem Healer, danach
  war der Block leer. Jetzt drei Netze: vor dem Healer, nach dem Healer, auf
  dem fertigen HTML (`_ensure_decision_block_final`).
- R1 S. 27: „Die Ablauf, die heute …" — Pipeline→Ablauf ohne Genus in zwei
  Ersetzungslisten; „die das Studio bereits nutzen".
- Strategie S. 10/19: „Vendor-Audit-Status „nicht bestanden"" — das Etikett
  aus dem Kontext, jetzt „rot (nur mit AVV und Leitplanken einsetzbar)".
"""
from __future__ import annotations

import re

import pytest


@pytest.fixture
def ga():
    import gpt_analyze
    return gpt_analyze


BOX_OK = (
    '<div class="section" id="decision"><h2>Entscheidungsvorlage</h2>'
    '<div class="exec-decision-box"><p><strong>Ihre Entscheidung in 3 Punkten</strong></p><ul>'
    '<li><strong>Tun:</strong> A.</li><li><strong>Lassen:</strong> B.</li>'
    '<li><strong>Risiko &amp; Stop-Signal:</strong> C.</li>'
    '<li><strong>Investition:</strong> Startinvestition ca. 48.000 € — Details im Business Case.</li>'
    '</ul></div><div class="confidence-card">Stand</div></div>'
)
BOX_LEER = (
    '<div class="section" id="decision"><h2>Entscheidungsvorlage</h2>'
    '<div class="exec-decision-box"><p><strong>Ihre Entscheidung in 3 Punkten.</strong></p></div>'
    '<div class="confidence-card">Stand</div></div>'
)


class TestEntscheidungsblockFinal:
    def test_volle_box_bleibt(self, ga):
        out, ersetzt = ga._ensure_decision_block_final(BOX_OK, {"zeitersparnis_prioritaet": "Untertitel"}, "de")
        assert not ersetzt and out == BOX_OK

    def test_leere_box_wird_ersetzt(self, ga):
        out, ersetzt = ga._ensure_decision_block_final(BOX_LEER, {"zeitersparnis_prioritaet": "Untertitel je Plattform"}, "de")
        assert ersetzt
        box = re.search(r'<div class="exec-decision-box".*?</div>', out, re.DOTALL).group(0)
        assert len(re.findall(r"<li\b", box)) == 3
        assert "Tun:" in box and "Lassen:" in box and "Stop-Signal" in box
        assert "Untertitel je Plattform" in box
        assert out.count("exec-decision-box") == 1 and "confidence-card" in out

    def test_investitionszeile_wird_mitgenommen(self, ga):
        html = BOX_LEER.replace(
            "</strong></p></div>",
            '</strong></p><ul><li><strong>Investition:</strong> Startinvestition ca. 48.000 €.</li></ul></div>')
        out, ersetzt = ga._ensure_decision_block_final(html, {}, "de")
        assert ersetzt
        box = re.search(r'<div class="exec-decision-box".*?</div>', out, re.DOTALL).group(0)
        assert len(re.findall(r"<li\b", box)) == 4 and "Startinvestition ca. 48.000" in box

    def test_verschachtelte_box_bleibt(self, ga):
        html = BOX_LEER.replace('<p><strong>Ihre', '<div class="x"><p><strong>Ihre')
        out, ersetzt = ga._ensure_decision_block_final(html, {}, "de")
        assert not ersetzt and out == html

    def test_englisch(self, ga):
        out, ersetzt = ga._ensure_decision_block_final(BOX_LEER, {}, "en")
        assert ersetzt and "Your decision in 3 points" in out and "Do:" in out

    def test_sektionsnetz_meldet_stufe(self, ga):
        secs = {"EXECUTIVE_DECISION_HTML": '<div class="exec-decision-box"><p><strong>Ihre Entscheidung in 3 Punkten.</strong></p></div>'}
        assert ga._ensure_decision_block(secs, "de", stage="post-healer")
        assert len(ga._DECISION_LABEL_RE.findall(secs["EXECUTIVE_DECISION_HTML"])) == 3
        assert not ga._ensure_decision_block(secs, "de", stage="post-healer")

    def test_beide_netze_im_code(self, ga):
        import inspect
        src = inspect.getsource(ga)
        assert 'stage="post-healer"' in src
        assert "_ensure_decision_block_final(final_html, sections, report_lang)" in src


class TestGenusAblauf:
    @pytest.mark.parametrize("vorher,nachher", [
        ("<p>Die Pipeline, die heute Rohschnitt erzeugt, muss laufen.</p>",
         "<p>Der Ablauf, der heute Rohschnitt erzeugt, muss laufen.</p>"),
        ("<p>eine Pipeline für den Schnitt</p>", "<p>ein Ablauf für den Schnitt</p>"),
        ("<p>den Ablauf, die Regeln und die Freigabe</p>", "<p>den Ablauf, die Regeln und die Freigabe</p>"),
    ])
    def test_grammatik(self, vorher, nachher):
        from services.content_quality_enforcer import apply_grammar_fixes
        assert apply_grammar_fixes(vorher)[0] == nachher

    def test_siezen_liste(self):
        from services.content_quality_enforcer import apply_extended_siezen
        out = apply_extended_siezen("<p>Die Pipeline, die heute läuft.</p>")
        out = out[0] if isinstance(out, tuple) else out
        assert "Der Ablauf, der heute" in out

    def test_studio_nutzen(self):
        from services.content_quality_enforcer import apply_grammar_fixes
        out, _ = apply_grammar_fixes("<p>Die Cloud-Infrastruktur, die das Studio bereits nutzen, ist kein Faktor.</p>")
        assert "die das Studio bereits nutzt," in out


class TestVendorEtikett:
    def test_mapping(self):
        import inspect
        from services import strategy_pipeline as sp
        src = inspect.getsource(sp)
        assert '"fail": "rot (nur mit AVV und Leitplanken einsetzbar)"' in src
        assert '"nicht bestanden": "rot (nur mit AVV und Leitplanken einsetzbar)"' in src
