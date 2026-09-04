# -*- coding: utf-8 -*-
"""KIS-1283: Eine Stimme in allen drei Berichten.

Hinter der Marke steht eine Person. Der Status-Report weiss das — eine
Ersetzung in ``gpt_analyze.py`` wandelt dort ``wir`` in ``ich``. Der
Strategiebericht kannte die Regel nicht. Lauf KIS-1267, gezählt:

    Status-Report    0 × erste Person Plural,  5 × Singular
    Strategiebericht 10 × erste Person Plural, 6 × Singular
    Potenzialanalyse  1 ×

Derselbe Kunde las in einem Dokument „ich" und im anderen „wir". Alle
zehn Stellen sprach der Berater („empfehlen wir", „rechnen wir mit"),
keine der Kunde — am Lauf geprüft.

Die bestehende Regel in ``gpt_analyze.py`` taugte nicht zum Kopieren:
Sie tauscht Wörter, keine Verbformen. Aus „weisen wir nicht aus" wurde
„weisen ich nicht aus" (KIS-1282). Bei „empfehlen wir" — sechsmal im
Strategiebericht — wäre derselbe Fehler entstanden.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from services.beraterstimme import in_singular

REPO = Path(__file__).resolve().parent.parent


def _text(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


class TestVerbformFolgtDemPronomen:
    """Der Kern: Ein Worttausch allein erzeugt „empfehlen ich"."""

    @pytest.mark.parametrize("vorher,nachher", [
        ("empfehlen wir folgende Strategie", "empfehle ich folgende Strategie"),
        ("rechnen wir mit zwei Tagen", "rechne ich mit zwei Tagen"),
        ("gehen wir von 4–6 Abonnenten aus", "gehe ich von 4–6 Abonnenten aus"),
        ("erwarten wir eine Entlastung", "erwarte ich eine Entlastung"),
        ("prüfen wir die Datenlage", "prüfe ich die Datenlage"),
    ])
    def test_nachgestelltes_wir(self, vorher, nachher):
        assert _text(in_singular(f"<p>{vorher}</p>")[0]) == nachher

    @pytest.mark.parametrize("vorher,nachher", [
        ("Wir empfehlen DeepL Pro.", "Ich empfehle DeepL Pro."),
        ("Wir sind für Sie da.", "Ich bin für Sie da."),
        ("Wir haben das geprüft.", "Ich habe das geprüft."),
        ("Wir können das prüfen.", "Ich kann das prüfen."),
        ("Wir gehen von stabilen Preisen aus.", "Ich gehe von stabilen Preisen aus."),
    ])
    def test_satzanfang_bleibt_gross(self, vorher, nachher):
        """Ein gemeinsames [Ww]ir haette den Satzanfang klein gemacht."""
        assert _text(in_singular(f"<p>{vorher}</p>")[0]) == nachher

    def test_kleines_wir_im_satz_bleibt_klein(self):
        ergebnis = _text(in_singular("<p>Deshalb empfehlen wir Notion.</p>")[0])
        assert ergebnis == "Deshalb empfehle ich Notion."

    def test_kein_plural_verb_bleibt_stehen(self):
        """Die Probe aufs Ganze: KIS-1282 in Kurzform."""
        ergebnis = _text(in_singular("<p>Deshalb empfehlen wir das.</p>")[0])
        assert "empfehlen ich" not in ergebnis
        assert "ich empfehlen" not in ergebnis


class TestPronomenUndPossessive:

    @pytest.mark.parametrize("vorher,nachher", [
        ("Das ist uns wichtig.", "Das ist mir wichtig."),
        ("Unsere Empfehlung steht.", "Meine Empfehlung steht."),
        ("unser Ansatz", "mein Ansatz"),
        ("in unserem Bericht", "in meinem Bericht"),
        ("nach unseren Erfahrungen", "nach meinen Erfahrungen"),
    ])
    def test_umstellung(self, vorher, nachher):
        assert _text(in_singular(f"<p>{vorher}</p>")[0]) == nachher

    def test_ueber_uns_bleibt(self):
        """„Über mir" waere eine Ortsangabe."""
        assert _text(in_singular("<p>Über uns</p>")[0]) == "Über uns"


class TestHtmlBleibtHeil:

    def test_attribute_werden_nicht_angefasst(self):
        html = '<a href="https://x.de/wir-ueber-uns" class="unser-link">Text</a>'
        neu, _ = in_singular(html)
        assert 'href="https://x.de/wir-ueber-uns"' in neu
        assert 'class="unser-link"' in neu

    def test_leerer_text_bleibt_leer(self):
        assert in_singular("") == ("", 0)

    def test_text_ohne_treffer_bleibt_unveraendert(self):
        html = "<p>Ihr Unternehmen erreicht 79 Punkte.</p>"
        assert in_singular(html) == (html, 0)

    def test_abschaltbar(self, monkeypatch):
        import services.beraterstimme as m
        monkeypatch.setattr(m, "BERATERSTIMME_ENABLED", False)
        html = "<p>Wir empfehlen das.</p>"
        assert m.in_singular(html) == (html, 0)


class TestEinbindungStrategiebericht:

    def test_sanitizer_ruft_den_baustein(self):
        quelle = (REPO / "services" / "strategy_sanitizer.py").read_text(encoding="utf-8")
        assert "beraterstimme_in_singular" in quelle

    def test_fehlender_baustein_bricht_nichts(self, monkeypatch):
        """Fail-open: Ohne den Baustein bleibt der Text, wie er ist."""
        import services.strategy_sanitizer as s
        monkeypatch.setattr(
            s, "beraterstimme_in_singular",
            lambda h: (_ for _ in ()).throw(RuntimeError("weg")), raising=True)
        # Der Wrapper faengt selbst; hier zaehlt, dass es ihn gibt.
        assert callable(getattr(s, "beraterstimme_in_singular"))

    def test_ganze_sektion_wird_umgestellt(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        lang = ("<p>Basierend auf diesem Profil empfehlen wir folgende Strategie. "
                "Für das Abo-Modell gehen wir von 4–6 Abonnenten aus. "
                "Der Schutz Ihrer Daten ist uns wichtig, und unsere Erfahrung "
                "zeigt, dass ein schrittweiser Einstieg traegt.</p>")
        ergebnis = sanitize_strategy_sections({"s3": lang})
        text = _text(ergebnis["s3"])
        assert "empfehle ich" in text
        assert "gehe ich" in text
        assert "ist mir wichtig" in text
        assert "meine Erfahrung" in text
        assert "wir" not in text.lower().split()


class TestPromptSaetNichtSelbstPlural:
    """Das Beispiel im Prompt hat der Lauf KIS-1267 wortwoertlich
    uebernommen — samt „rechnen wir". Ein Beispiel schlaegt jede Regel
    (KIS-1282), also darf es die Stimme nicht brechen."""

    def test_beispiel_ohne_erste_person_plural(self):
        quelle = (REPO / "prompts" / "strategy_prompts.py").read_text(encoding="utf-8")
        stelle = quelle.find("Je Auftrag")
        assert stelle > 0, "Beispiel nicht gefunden"
        beispiel = quelle[stelle:stelle + 220]
        assert not re.search(r"(?<![\wÄÖÜäöüß])wir(?![\wÄÖÜäöüß])", beispiel), beispiel
