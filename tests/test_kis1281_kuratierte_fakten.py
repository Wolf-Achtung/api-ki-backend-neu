# -*- coding: utf-8 -*-
"""KIS-1281 Stufe 1: Das Modell darf keine Tatsachen mehr erfinden.

Im Report stehen zwei Sorten Aussagen, und bisher erzeugte das
Sprachmodell beide:

  * Prüfbare Tatsache — „Tally kostet 29 €/Monat", „ZIM nimmt keine
    Anträge an". Gehört aus gepflegten Daten.
  * Beratende Einordnung — „Für Ihre Postproduktion lohnt sich zuerst
    der Schnitt". Gehört zum Modell.

Weil beide aus derselben Quelle kamen, stand ZIM im Lauf KIS-1262 in der
Fördertabelle, obwohl das Programm seit 07.07.2026 pausiert, und der
Werkzeug-Abschnitt nannte im Lauf KIS-1265 Software ohne belegte
Datenschutzlage.

Die gepflegten Daten gehen jetzt als Faktenblock in die Prompts von
``tools_empfehlungen`` und ``foerderpotenzial``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from services.kuratierte_fakten import (
    build_foerder_fakten,
    build_kuratierte_grounding,
    build_tool_fakten,
    verbinde_grounding,
)

REPO = Path(__file__).resolve().parent.parent

BEISPIEL = {"bundesland": "be", "branche": "medien",
            "unternehmensgroesse": "2–10",
            "hauptleistung": "Film- und TV-Produktion"}


class TestWerkzeugFakten:

    def test_block_nennt_die_kuratierten_werkzeuge(self):
        block = build_tool_fakten(BEISPIEL)
        assert "GEPRÜFTE WERKZEUG-DATEN" in block
        assert block.count("\n- ") >= 3

    def test_keine_preise_im_faktenblock(self):
        """20 von 23 Einträgen tragen kein Prüfdatum. Was niemand
        bestätigt hat, gehört nicht in den Fließtext — die geprüften
        Angaben zeigt die Tabelle (KIS-1280)."""
        block = build_tool_fakten(BEISPIEL)
        assert "€" not in block
        assert "EUR" not in block

    def test_hosting_und_datenschutz_stehen_drin(self):
        """Genau die Angaben, die das Modell sonst raten würde."""
        assert "Hosting:" in build_tool_fakten(BEISPIEL)

    def test_regel_verbietet_erfundene_werkzeuge(self):
        block = build_tool_fakten(BEISPIEL)
        assert "AUSSCHLIESSLICH" in block
        assert "existiert für diesen Abschnitt nicht" in block

    def test_einordnung_bleibt_dem_modell(self):
        """Die Regel darf nicht so eng sein, dass der Abschnitt zur
        Aufzählung verkommt."""
        block = build_tool_fakten(BEISPIEL)
        assert "Einordnung" in block
        assert "Gattungsbegriffe" in block

    def test_ohne_werkzeuge_kein_block(self):
        assert build_tool_fakten(BEISPIEL, max_tools=0) == ""


class TestFoerderFakten:

    def test_block_nennt_programme_mit_quote_und_umfang(self):
        block = build_foerder_fakten(BEISPIEL)
        assert "GEPRÜFTE FÖRDERPROGRAMME" in block
        assert "Quote" in block

    def test_pausierte_programme_fehlen(self):
        """ZIM steht seit 07.07.2026 auf `paused`. Stünde es im
        Faktenblock, empfähle das Modell es mit bestem Gewissen."""
        assert "ZIM" not in build_foerder_fakten(BEISPIEL)

    def test_keine_doppelten_etiketten(self):
        """max_amount lautet oft schon „bis 25 Mio €" — dann darf nicht
        „bis bis 25 Mio €" herauskommen."""
        assert "bis bis" not in build_foerder_fakten(BEISPIEL)

    def test_regel_verbietet_erfundene_zahlen(self):
        block = build_foerder_fakten(BEISPIEL)
        assert "Erfinde keine Zahlen" in block

    def test_ohne_programme_kein_block(self):
        assert build_foerder_fakten(BEISPIEL, max_programme=0) == ""


class TestGrounding:

    def test_beide_sektionen_bekommen_einen_block(self):
        g = build_kuratierte_grounding(BEISPIEL)
        assert set(g) == {"tools_empfehlungen", "foerderpotenzial"}

    def test_abschaltbar(self, monkeypatch):
        import services.kuratierte_fakten as m
        monkeypatch.setattr(m, "KURATIERTE_FAKTEN_ENABLED", False)
        assert m.build_kuratierte_grounding(BEISPIEL) == {}

    def test_fehler_ergeben_ein_leeres_dict(self, monkeypatch):
        """Ein Faktenblock darf nie einen Report scheitern lassen."""
        import services.kuratierte_fakten as m
        monkeypatch.setattr(m, "build_tool_fakten",
                            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("x")))
        assert m.build_kuratierte_grounding(BEISPIEL) == {}

    def test_ohne_netz_stehen_die_fakten_trotzdem(self, monkeypatch):
        """Der Unterschied zur Live-Recherche: kein Netz nötig."""
        import services.research_clients as rc
        monkeypatch.setattr(rc, "http_get",
                            lambda *a, **kw: (_ for _ in ()).throw(OSError("kein Netz")))
        assert build_kuratierte_grounding(BEISPIEL)


class TestZusammenfuehren:
    """Kuratierte Fakten und Live-Recherche schliessen einander nicht
    aus: Die Liste sagt, WAS genannt werden darf, die Recherche liefert
    die Aktualität."""

    def test_beide_bloecke_bleiben_erhalten(self):
        zusammen = verbinde_grounding(
            {"tools_empfehlungen": "AAA"}, {"tools_empfehlungen": "BBB"})
        assert zusammen["tools_empfehlungen"] == "AAABBB"

    def test_kuratierte_fakten_stehen_zuerst(self):
        """Reihenfolge ist Rangfolge: erst die geprüfte Liste."""
        zusammen = verbinde_grounding({"s": "GEPRUEFT"}, {"s": "LIVE"})
        assert zusammen["s"].index("GEPRUEFT") < zusammen["s"].index("LIVE")

    def test_sektionen_ohne_gegenstueck_bleiben(self):
        zusammen = verbinde_grounding({"a": "1"}, {"b": "2"})
        assert zusammen == {"a": "1", "b": "2"}

    def test_leere_bloecke_verschwinden(self):
        assert verbinde_grounding({"a": ""}, {"a": "X"}) == {"a": "X"}

    def test_leere_quellen_stoeren_nicht(self):
        assert verbinde_grounding({}, None, {"a": "X"}) == {"a": "X"}


class TestEinbindung:

    def test_pipeline_verbindet_beide_quellen(self):
        quelle = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        assert "build_kuratierte_grounding" in quelle
        assert "verbinde_grounding" in quelle

    def test_die_sektionsnamen_gibt_es_wirklich(self):
        """Ein Tippfehler im Sektionsnamen liesse den Block ins Leere
        laufen — ohne Fehler, nur ohne Wirkung."""
        quelle = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        for name in build_kuratierte_grounding(BEISPIEL):
            assert f'"{name}"' in quelle or f"'{name}'" in quelle, name
