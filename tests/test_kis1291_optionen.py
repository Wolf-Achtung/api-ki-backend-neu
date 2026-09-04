# -*- coding: utf-8 -*-
"""KIS-1291 (Stufe 3 des Branchen-Audits): Medien-Optionen im Fragebogen.

52 von 53 Fragen lauteten in jeder Branche gleich. Einige Optionen fuehrten
Medienkunden in die Irre: "Produktion / Logistik" meinte Fertigung; die
Werkzeugliste kannte kein Premiere, Pro Tools, Unreal; die Datenquellen
kein Rohmaterial, keine Rechte; die Trainingsthemen nicht "KI-Rechte &
Kennzeichnung", obwohl die Startseite es verspricht.

Eine Option lebt an fuenf Stellen im Backend — Registry (Label-Fallback),
Chat-Schnellwahl (DE), Chat-Anzeige (DE/EN), Normalizer (erlaubte Werte).
Dieser Test haelt alle fuenf gleich. Das Frontend (make-ki-frontend) traegt
dieselben Werte; ein Skript dort prueft die Paritaet DE/EN.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

NEU = {
    "ki_einsatz": ["redaktion", "studio_audio"],
    "pilot_bereich": ["redaktion", "studio_audio"],
    "datenquellen": ["rohmaterial_archiv", "rechte_lizenzen", "manuskripte_texte", "nutzungsdaten"],
    "anwendungsfaelle": ["transkription_untertitel", "archiv_verschlagwortung",
                         "synchron_dubbing", "lokalisierung", "vorlektorat"],
    "vorhandene_tools": ["schnitt_grading", "audio_daw", "redaktion_satz", "engine", "review_mam"],
    "trainings_interessen": ["ki_rechte_kennzeichnung", "stimme_gesicht_einwilligung"],
}
ALLE_NEU = sorted({v for vs in NEU.values() for v in vs})


def _qr_optionen():
    from routes.chat import _QR_OPTIONS
    return _QR_OPTIONS


class TestFuenfStellenGleich:

    @pytest.mark.parametrize("feld,werte", NEU.items())
    def test_chat_schnellwahl_kennt_die_werte(self, feld, werte):
        vorhanden = [o["value"] for o in _qr_optionen()[feld]]
        assert all(w in vorhanden for w in werte), (feld, vorhanden)

    @pytest.mark.parametrize("feld,werte", NEU.items())
    def test_normalizer_erlaubt_die_werte(self, feld, werte):
        from services.chat_normalizer import ENUM_VALUES as erlaubt
        assert all(w in erlaubt[feld] for w in werte), (feld, erlaubt[feld])

    @pytest.mark.parametrize("wert", ALLE_NEU)
    def test_registry_liefert_ein_label(self, wert):
        """_flat_option_label — sonst leakt der Roh-Slug in den Report."""
        import gpt_analyze as g
        label = g._flat_option_label(wert)
        assert label and label != wert and "_" not in label, (wert, label)

    @pytest.mark.parametrize("wert", ALLE_NEU)
    def test_de_und_en_anzeige(self, wert):
        conv = (REPO / "services" / "chat_conversation.py").read_text(encoding="utf-8")
        chat = (REPO / "routes" / "chat.py").read_text(encoding="utf-8")
        assert re.search(r'"%s": "[^"]+"' % wert, conv), f"DE-Anzeige fehlt: {wert}"
        assert re.search(r'"%s": "[^"]+"' % wert, chat), f"EN-Anzeige fehlt: {wert}"


class TestProduktionHeisstPostproduktion:
    """Der Wert bleibt "produktion" (Backend-Logik haengt daran), das Label
    meint jetzt die Medienproduktion — nicht mehr Fertigung und Logistik."""

    def test_kein_logistik_label_mehr(self):
        for p in ("field_registry.py", "routes/chat.py", "services/chat_conversation.py"):
            text = (REPO / p).read_text(encoding="utf-8")
            assert "Produktion / Logistik" not in text, p
            assert "Production / logistics" not in text, p

    def test_sparte_produktion_unberuehrt(self):
        """"produktion" als Sparte heisst weiter Film-/TV-Produktion."""
        from services.medien_sparte import label
        assert label("produktion") == "Film-/TV-Produktion"
        qr = _qr_optionen()["medien_sparte"]
        assert any(o["value"] == "produktion" and o["label"] == "Film-/TV-Produktion" for o in qr)


class TestSmartSkip:
    def test_neue_anwendungsfaelle_haben_einen_pilotbereich(self):
        from routes.chat import _ANWENDUNG_TO_PILOT as m
        assert m["transkription_untertitel"] == "produktion"
        assert m["synchron_dubbing"] == "studio_audio"
        assert m["vorlektorat"] == "redaktion"
        # Jeder Zielwert muss eine gueltige pilot_bereich-Option sein.
        gueltig = {o["value"] for o in _qr_optionen()["pilot_bereich"]}
        assert set(m.values()) <= gueltig, set(m.values()) - gueltig
