# -*- coding: utf-8 -*-
"""KIS-1278: Die zweite Tool-Liste, die der Radar nicht sieht.

Der Tool-Radar prueft ``data/tools_seed.json``. Danebem liegt in
``services/tools_recommender.py`` eine zweite, handgepflegte Liste
(``DEFAULT_TOOLS``) als Ausweichquelle. Sie enthielt am 03.09.2026
genau die Adresse, die der Radar in der Seed-Datei als tot gemeldet
hatte: ``https://tally.so/help/privacy`` (HTTP 404). Dazu
``https://mistral.ai/legal/privacy/`` (HTTP 404).

Diese Adressen landen als Link "Trust Center" im Report
(tools_recommender.py, ``_link("Trust&nbsp;Center", ...)``). Ein Leser,
der die Datenschutzlage eines empfohlenen Werkzeugs pruefen will,
landet auf einer Fehlerseite — im Beratungsbericht das Gegenteil dessen,
was der Link verspricht.

Zweiter Punkt: Der Pfad zur Seed-Datei war relativ. Steht das
Arbeitsverzeichnis des Prozesses woanders, greift still die
Ausweichliste — 12 statt 23 Tools, ohne Fehler im Log.

Dieselbe Klasse Fehler wie KIS-1270 (Statusregel zweimal im Code) und
KIS-1273 (dritte Programmliste): Zwei Quellen fuer dieselbe Sache
driften auseinander, und die Pruefung kennt nur eine davon.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SEED = REPO / "data" / "tools_seed.json"

# Die Adressen aus der Radar-Mail vom 03.09.2026, die HTTP 404/401 gaben.
TOTE_URLS = {
    "https://tally.so/help/privacy",
    "https://www.notion.so/privacy",
    "https://mistral.ai/legal/privacy/",
    "https://www.topazlabs.com/privacy",
    "https://www.simonsaysai.com/privacy",
    "https://www.iconik.io/legal",
    "https://aleph-alpha.com/privacy",
}


def _seed():
    return json.loads(SEED.read_text(encoding="utf-8"))


def _fallback():
    from services.tools_recommender import DEFAULT_TOOLS
    return DEFAULT_TOOLS


class TestKeineTotenUrlsInBeidenListen:

    @pytest.mark.parametrize("quelle", ["seed", "fallback"])
    def test_gemeldete_urls_kommen_nicht_mehr_vor(self, quelle):
        tools = _seed() if quelle == "seed" else _fallback()
        treffer = {t.get("trust_url") for t in tools} & TOTE_URLS
        assert not treffer, f"{quelle} enthaelt noch tote URLs: {treffer}"

    @pytest.mark.parametrize("quelle", ["seed", "fallback"])
    def test_auch_die_produkt_urls_sind_sauber(self, quelle):
        tools = _seed() if quelle == "seed" else _fallback()
        treffer = {t.get("url") for t in tools} & TOTE_URLS
        assert not treffer, f"{quelle}: {treffer}"


class TestBeideListenStimmenUeberein:
    """Wo beide Listen dasselbe Werkzeug fuehren, muss die Adresse
    dieselbe sein. Sonst haengt es vom Zufall ab, welche der Leser sieht."""

    def _gemeinsam(self):
        seed = {t["name"]: t for t in _seed()}
        return [(name, tool, seed[name])
                for name, tool in ((t["name"], t) for t in _fallback())
                if name in seed]

    def test_es_gibt_ueberhaupt_ueberschneidungen(self):
        """Ohne Ueberschneidung waere der Vergleich unten wirkungslos."""
        assert len(self._gemeinsam()) >= 5

    def test_trust_urls_sind_gleich(self):
        abweichungen = [
            f"{name}: Ausweichliste {fb.get('trust_url')} != Seed {sd.get('trust_url')}"
            for name, fb, sd in self._gemeinsam()
            if fb.get("trust_url") != sd.get("trust_url")
        ]
        assert not abweichungen, "\n".join(abweichungen)

    def test_produkt_urls_sind_gleich(self):
        abweichungen = [
            f"{name}: {fb.get('url')} != {sd.get('url')}"
            for name, fb, sd in self._gemeinsam()
            if fb.get("url") != sd.get("url")
        ]
        assert not abweichungen, "\n".join(abweichungen)


class TestSeedPfadHaengtNichtAmArbeitsverzeichnis:

    def test_seed_wird_auch_aus_einem_anderen_ordner_gefunden(self, tmp_path, monkeypatch):
        """Der eigentliche Fehler: Path("data/tools_seed.json") ist
        relativ. Aus einem anderen Arbeitsverzeichnis griff still die
        Ausweichliste."""
        from services.tools_recommender import _load_seed
        monkeypatch.chdir(tmp_path)
        tools = _load_seed()
        assert len(tools) == len(_seed())
        assert len(tools) > len(_fallback()), (
            "Ausweichliste statt Seed-Datei geladen — Pfad wieder relativ?"
        )

    def test_kein_relativer_datenpfad_mehr_im_dienst(self):
        """services/funding_parser.py hatte denselben Fehler und wurde
        mit KIS-1278 geloescht (kein Aufrufer, 101 Zeilen)."""
        treffer = []
        for ordner in ("services", "routes", "core", "workers"):
            for pfad in (REPO / ordner).rglob("*.py"):
                text = pfad.read_text(encoding="utf-8")
                if 'Path("data/' in text or "Path('data/" in text:
                    treffer.append(str(pfad.relative_to(REPO)))
        assert not treffer, f"Relativer Datenpfad in: {treffer}"


class TestGeloeschterToterCode:

    def test_funding_parser_ist_weg(self):
        assert not (REPO / "services" / "funding_parser.py").exists()

    def test_niemand_importiert_ihn_noch(self):
        treffer = []
        for ordner in ("services", "routes", "core", "workers", "scripts"):
            for pfad in (REPO / ordner).rglob("*.py"):
                if "funding_parser" in pfad.read_text(encoding="utf-8"):
                    treffer.append(str(pfad.relative_to(REPO)))
        assert not treffer, treffer

    def test_die_fallback_datei_bleibt(self):
        """data/funding_programs.json liest services/research_pipeline.py
        weiter — nur der Parser war tot, nicht die Daten."""
        assert (REPO / "data" / "funding_programs.json").exists()
