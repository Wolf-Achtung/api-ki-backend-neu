# -*- coding: utf-8 -*-
"""KIS-1280: Geprüfte Werkzeugdaten sichtbar, Annahmen mit Zahlen.

Der Lauf KIS-1265 zeigte drei Dinge, die kein Befund gemeldet hatte:

1. Die kuratierte Liste ``data/tools_seed.json`` erreichte keinen Leser.
   ``tools_html_output.py`` hat keinen Aufrufer; der Alignment-Block
   sitzt in Anhang A12, und kein Anhang erscheint in den Berichten. Der
   Leser sah Werkzeugnamen aus dem Sprachmodell — ohne belegten Preis,
   ohne belegten Datenschutzstatus, ohne Anbieterlink.

2. Der Annahmen-Absatz des Strategieberichts stand dreimal wörtlich
   gleich: „Stabiles Marktumfeld …; aktuelle Teamgröße bleibt bestehen;
   keine regulatorischen Verschärfungen." Der Satz trägt keine einzige
   Zahl des Abschnitts.

3. Die Dünne-Seiten-Prüfung meldete die Abschluss-Seite der
   Potenzialanalyse (348 Zeichen: Ausblick plus Kontaktbox). Im Lauf
   davor waren es 790 Zeichen — dieselbe Seite, dieselbe Absicht. Eine
   Prüfung, die mal meldet und mal nicht, erzieht zum Wegsehen.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from services.tools_verified_box import (
    build_verified_tools_html,
    inject_verified_tools,
    preis_anzeige,
)

REPO = Path(__file__).resolve().parent.parent

TEXTE_DE = {"kein_preis": "siehe Anbieterseite"}

BEISPIEL = {"bundesland": "be", "branche": "medien",
            "unternehmensgroesse": "2–10",
            "hauptleistung": "Film- und TV-Produktion"}


class TestPreisNurMitPruefdatum:
    """Die Regel, die den Block von einer Behauptung unterscheidet.

    20 von 23 Einträgen haben kein ``verified_at``. Deren Preise stammen
    aus der Ersteingabe und hat niemand bestätigt. Als Tatsache gedruckt
    wären sie schlechter als der bisherige Zustand — der Leser würde
    einer ungeprüften Zahl vertrauen.
    """

    def test_ohne_pruefdatum_kein_preis(self):
        assert preis_anzeige({"price": "29 €/Monat"}, TEXTE_DE) == "siehe Anbieterseite"

    def test_leeres_pruefdatum_zaehlt_nicht(self):
        for wert in ("", None, "   ", "demnächst"):
            assert preis_anzeige({"price": "29 €", "verified_at": wert},
                                 TEXTE_DE) == "siehe Anbieterseite"

    @pytest.mark.parametrize("datum", ["2026-09-04", "04.09.2026"])
    def test_mit_pruefdatum_erscheint_der_preis(self, datum):
        assert preis_anzeige({"price": "29 €/Monat", "verified_at": datum},
                             TEXTE_DE) == "29 €/Monat"

    def test_pruefdatum_ohne_preis_bleibt_verweis(self):
        assert preis_anzeige({"price": "", "verified_at": "2026-09-04"},
                             TEXTE_DE) == "siehe Anbieterseite"

    def test_im_gerenderten_block_steht_kein_ungepruefter_preis(self):
        html = build_verified_tools_html(BEISPIEL, tools=[
            {"name": "A", "price": "999 €/Monat", "trust_url": "https://a.de/p"},
            {"name": "B", "price": "12 €/Monat", "verified_at": "2026-09-04",
             "trust_url": "https://b.de/p"},
        ])
        assert "999" not in html, "ungeprüfter Preis im Report"
        assert "12 €/Monat" in html


class TestBlockInhalt:

    def test_enthaelt_die_kuratierten_werkzeuge(self):
        html = build_verified_tools_html(BEISPIEL)
        assert "Geprüfte Werkzeug-Daten" in html
        assert html.count("<tr>") >= 3

    def test_datenschutzseite_wird_verlinkt(self):
        html = build_verified_tools_html(BEISPIEL, tools=[
            {"name": "Tally.so", "trust_url": "https://tally.so/help/privacy-policy"}])
        assert 'href="https://tally.so/help/privacy-policy"' in html

    def test_unbrauchbare_beleg_url_wird_nicht_verlinkt(self):
        html = build_verified_tools_html(BEISPIEL, tools=[
            {"name": "X", "trust_url": "javascript:alert(1)"}])
        assert "javascript:" not in html
        assert "<a " not in html

    def test_sonderzeichen_werden_maskiert(self):
        html = build_verified_tools_html(BEISPIEL, tools=[
            {"name": "<script>böse</script>", "trust_url": "https://x.de/p"}])
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_ohne_werkzeuge_bleibt_der_block_leer(self):
        """Sonst stünde eine Überschrift ohne Tabelle im Bericht."""
        assert build_verified_tools_html(BEISPIEL, tools=[]) == ""

    def test_namenlose_eintraege_fallen_raus(self):
        assert build_verified_tools_html(BEISPIEL, tools=[{"price": "1 €"}]) == ""

    def test_fusszeile_erklaert_die_luecke(self):
        html = build_verified_tools_html(BEISPIEL, tools=[
            {"name": "A", "price": "9 €", "trust_url": "https://a.de/p"}])
        assert "nur mit Prüfdatum" in html

    def test_fusszeile_nennt_das_pruefdatum(self):
        html = build_verified_tools_html(BEISPIEL, tools=[
            {"name": "A", "price": "9 €", "verified_at": "2026-09-04",
             "trust_url": "https://a.de/p"}])
        assert "04.09.2026" in html

    def test_englische_fassung(self):
        html = build_verified_tools_html(BEISPIEL, lang="en", tools=[
            {"name": "A", "trust_url": "https://a.de/p"}])
        assert "Verified tool data" in html
        assert "see vendor page" in html


class TestEinbindung:

    def test_injektion_setzt_den_schluessel(self):
        s = inject_verified_tools({}, BEISPIEL, lang="de")
        assert s["VERIFIED_TOOLS_HTML"]

    def test_fehler_lassen_den_bericht_laufen(self, monkeypatch):
        """Ein Zusatzblock darf nie einen Report scheitern lassen."""
        import services.tools_verified_box as m
        monkeypatch.setattr(m, "build_verified_tools_html",
                            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("kaputt")))
        assert inject_verified_tools({}, BEISPIEL)["VERIFIED_TOOLS_HTML"] == ""

    def test_template_zeigt_den_block(self):
        vorlage = (REPO / "templates" / "pdf_template_v7.html").read_text(encoding="utf-8")
        assert "VERIFIED_TOOLS_HTML" in vorlage

    def test_block_steht_im_werkzeug_abschnitt(self):
        """Nicht im Anhang — dort landete schon der Alignment-Block."""
        vorlage = (REPO / "templates" / "pdf_template_v7.html").read_text(encoding="utf-8")
        start = vorlage.find('id="tools-section"')
        ende = vorlage.find("</section>", start)
        assert start > 0
        assert 0 < vorlage.find("VERIFIED_TOOLS_HTML", start) < ende

    def test_pipeline_ruft_den_baustein(self):
        quelle = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        assert "inject_verified_tools" in quelle

    def test_der_abschnitt_rendert_den_block_wirklich(self):
        """Ein Platzhalter im Template beweist noch nichts — der
        Alignment-Block stand auch im Template und kam nie an."""
        import jinja2

        vorlage = (REPO / "templates" / "pdf_template_v7.html").read_text(encoding="utf-8")
        start = vorlage.find("<!-- ═══════ TOOLS & STARTER-KIT ═══════ -->")
        ende = vorlage.find("<!-- ═══════ COPY-PASTE PROMPTS ═══════ -->")
        assert 0 < start < ende, "Werkzeug-Abschnitt im Template nicht gefunden"

        env = jinja2.Environment(autoescape=False)
        env.globals["ui"] = lambda schluessel, standard="": standard
        html = env.from_string(vorlage[start:ende]).render(
            KI_STACK_SUMMARY_HTML="<p>Erzeugter Text</p>",
            VERIFIED_TOOLS_HTML=build_verified_tools_html(BEISPIEL, tools=[
                {"name": "Tally.so", "price": "29 €", "verified_at": "2026-09-04",
                 "trust_url": "https://tally.so/help/privacy-policy"}]),
            STARTER_KIT_HTML="", skip_pages=[])
        assert "Geprüfte Werkzeug-Daten" in html
        assert "tally.so/help/privacy-policy" in html
        assert "29 €" in html


class TestAnnahmenRegel:
    """Der Prompt verlangte einen Annahmen-Absatz, bekam aber eine
    Leerformel. Jetzt sagt er, was hineingehört."""

    def _prompt(self) -> str:
        return (REPO / "prompts" / "strategy_prompts.py").read_text(encoding="utf-8")

    def test_umsatzprojektion_verlangt_die_menge(self):
        text = self._prompt()
        assert "Aufträgen" in text and "Umsatzzahl ohne ihre Menge" in text

    def test_annahmen_duerfen_keine_leerformel_sein(self):
        text = self._prompt()
        assert "Stabiles Marktumfeld" in text, "Gegenbeispiel fehlt im Prompt"
        assert "Menge, Auslastung" in text


class TestPruefwerkzeug:
    """scripts/compare_reports.py — die Prüfung, die den Lauf beurteilt."""

    def test_abschluss_seite_gilt_nicht_als_duenn(self):
        from scripts.compare_reports import duenne_seiten
        abschluss = ("Ausblick\nDiese ersten Schritte legen die Basis.\n"
                     "Wolf Hohl\nWebsite besuchen\nKontakt aufnehmen")
        assert duenne_seiten([abschluss]) == []

    def test_echte_duenne_seite_wird_weiter_gemeldet(self):
        from scripts.compare_reports import duenne_seiten
        assert duenne_seiten(["Nur eine Zeile."]) == [(1, len("Nur eine Zeile."))]

    def test_wiederholte_annahmen_werden_gefunden(self):
        from scripts.compare_reports import wiederholte_annahmen
        satz = ("Annahmen: Stabiles Marktumfeld in den naechsten zwoelf Monaten "
                "und unveraenderte Teamgroesse ohne neue Auflagen. Quellen: X. ")
        treffer = wiederholte_annahmen(satz * 3)
        assert len(treffer) == 1 and treffer[0][1] == 3

    def test_verschiedene_annahmen_sind_kein_befund(self):
        from scripts.compare_reports import wiederholte_annahmen
        text = ("Annahmen: Vier Auftraege im Monat bei zwei Tagen Aufwand je "
                "Auftrag und mittlerem Abo-Preis. Quellen: X. "
                "Annahmen: Fuenfzehn Abonnenten nach sechs Monaten bei "
                "gleichbleibender Abwanderung im Bestand. Quellen: Y. ")
        assert wiederholte_annahmen(text) == []
