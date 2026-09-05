# -*- coding: utf-8 -*-
"""KIS-1268: Tote Förder-URLs ersetzt, ZIM als pausiert gekennzeichnet.

Der Förder-Radar-Lauf vom 03.09.2026 meldete zehn tote URLs. Parallel
zeigte die Recherche: ZIM hat seit dem 07.07.2026 einen befristeten
Antragsstopp — der Lauf KIS-1262 empfahl das Programm trotzdem als Weg
für größere Entwicklungsprojekte.

Jede URL hier wurde am 03.09.2026 gegen die offizielle Programmseite
geprüft. Der Radar prüft die Erreichbarkeit fortlaufend weiter.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
KERN = REPO / "data" / "funding_programmes_core_2025.json"
FALLBACK = REPO / "data" / "funding_programs.json"
# KIS-1297: data/funding/funding_de.json las kein Report — geloescht. Die
# zweite gepflegte Datei ist jetzt die englische Programmliste.
DE = REPO / "data" / "funding" / "funding_de_en.json"


def _progs(pfad: Path):
    roh = json.loads(pfad.read_text(encoding="utf-8"))
    if isinstance(roh, list):
        return roh
    return roh.get("programmes") or roh.get("programs") or []


ALLE_DATEIEN = [KERN, FALLBACK, DE]

# Die zehn URLs aus der Radar-Mail vom 03.09.2026.
TOTE_URLS = {
    "https://www.aws.at/digitalisierung/",
    "https://www.bmdw.gv.at/Digitalisierung/KMUDigital.html",
    "https://www.kfw.de/inlandsfoerderung/Unternehmen/Digitalisierung-Innovation/",
    "https://www.stmwi.bayern.de/digitalisierung/digitalbonus/",
    "https://www.baden-wuerttemberg.de/de/service/foerderprogramme/invest-bw",
    "https://www.ibb.de/de/foerderprogramme/profit.html",
    "https://www.bmas.de/DE/Arbeit/Aus-und-Weiterbildung/Weiterbildungsrepublik/KOMPASS/kompass.html",
    "https://www.berlin.de/sen/wirtschaft/wirtschaft/foerderprogramme/transfer-bonus/",
    "https://www.ibb.de/de/foerderprogramme/pro-fit",
    "https://www.bayern-innovativ.de/innovationsgutschein",
}


class TestKeineTotenUrls:

    @pytest.mark.parametrize("pfad", ALLE_DATEIEN, ids=lambda p: p.name)
    def test_gemeldete_urls_kommen_nicht_mehr_vor(self, pfad):
        vorhanden = {p.get("url") for p in _progs(pfad)}
        treffer = vorhanden & TOTE_URLS
        assert not treffer, f"{pfad.name} enthält noch tote URLs: {treffer}"

    def test_korrigierte_eintraege_zeigen_auf_eine_programmseite(self):
        """"https://www.ibb.de" als Programm-URL ist keine Programmseite —
        der Leser landet auf der Startseite und sucht selbst. Geprueft nur
        fuer die hier korrigierten Eintraege; die uebrigen Altdaten sind
        Sache des Radars, nicht dieses PRs."""
        korrigiert = {"profit_berlin", "kfw_digital_innovation", "kompass",
                      "invest_bw_digital_ki", "digi4kmu_at", "aws_digi_invest",
                      "digitalbonus_bayern", "zim"}
        for p in _progs(KERN):
            if p["id"] not in korrigiert:
                continue
            url = (p.get("url") or "").rstrip("/")
            # invest-bw.de ist selbst die Programmseite des Programms.
            if url == "https://invest-bw.de":
                continue
            assert url.count("/") > 2, f"{p['id']}: nackte Domain {url}"


class TestZimAntragsstopp:
    """ZIM ist nicht beendet, sondern pausiert: Antragsstopp seit
    07.07.2026, neue Anträge frühestens Anfang 2027, bereits gestellte
    Anträge laufen weiter."""

    def _zim(self, pfad: Path):
        for p in _progs(pfad):
            if "ZIM" in str(p.get("title") or p.get("name") or p.get("name_de") or ""):
                return p
        return None

    @pytest.mark.parametrize("pfad", [KERN, DE], ids=lambda p: p.name)
    def test_status_ist_paused(self, pfad):
        zim = self._zim(pfad)
        assert zim is not None, f"ZIM fehlt in {pfad.name}"
        assert zim["status"] == "paused"

    def test_status_ist_nicht_expired(self):
        """'expired' waere die falsche Kategorie — das Programm kehrt zurueck."""
        assert self._zim(KERN)["status"] != "expired"

    def test_notiz_nennt_stopp_und_rueckkehr(self):
        notiz = self._zim(KERN)["notes"]
        assert "07.07.2026" in notiz
        assert "2027" in notiz
        assert "Antragsstopp" in notiz

    def test_url_zeigt_auf_die_amtliche_meldung(self):
        assert "antragsstopp" in self._zim(KERN)["url"].lower()


class TestRecommenderFiltertPausierte:

    def test_paused_wird_nicht_empfohlen(self):
        from services.funding_recommender import load_funding_programs
        titel = [p.get("title", "") for p in load_funding_programs()]
        assert not any("ZIM" in t for t in titel), (
            "ZIM steht trotz Antragsstopp in den Empfehlungen"
        )

    def test_aktive_programme_bleiben(self):
        from services.funding_recommender import load_funding_programs
        progs = load_funding_programs()
        assert len(progs) > 10
        assert all(p.get("status", "active") not in ("expired", "paused")
                   for p in progs)


class TestPruefdatumGesetzt:

    def test_geaenderte_eintraege_tragen_das_pruefdatum(self):
        geaendert = {"profit_berlin", "kfw_digital_innovation", "kompass",
                     "invest_bw_digital_ki", "digi4kmu_at", "aws_digi_invest", "zim"}
        for p in _progs(KERN):
            if p["id"] in geaendert:
                assert p["verified_at"] == "2026-09-03", p["id"]
            # KIS-1296: Digitalbonus Bayern am 05.09.2026 nachgeprueft — laeuft
            # wieder (Laufzeit bis 31.12.2027, monatliches Kontingent).
            if p["id"] == "digitalbonus_bayern":
                assert p["verified_at"] == "2026-09-05" and p["status"] == "active"


class TestRadarBleibtRuhigUndErinnert:
    """Ein dokumentierter Antragsstopp ist kein Pflegerückstand — aber er
    darf auch nicht für immer verstummen."""

    def test_paused_erzeugt_heute_keinen_befund(self):
        from datetime import date
        from scripts.funding_radar import check_program
        zim = next(p for p in _progs(KERN) if "ZIM" in p["title"])
        assert check_program(zim, date(2026, 9, 3)) == []

    def test_ab_wiedervorlage_meldet_der_radar_wieder(self):
        from datetime import date
        from scripts.funding_radar import check_program
        zim = next(p for p in _progs(KERN) if "ZIM" in p["title"])
        befunde = check_program(zim, date(2027, 1, 15))
        assert len(befunde) == 1
        assert befunde[0]["type"] == "recheck"

    def test_wiedervorlage_ist_gesetzt(self):
        zim = next(p for p in _progs(KERN) if "ZIM" in p["title"])
        assert zim["recheck_after"] == "2027-01-15"

    def test_paused_ohne_wiedervorlage_bleibt_still(self):
        from datetime import date
        from scripts.funding_radar import check_program
        assert check_program({"title": "X", "status": "paused"}, date(2030, 1, 1)) == []


class TestEineRegelFuerAllePfade:
    """KIS-1270: Der Lauf KIS-1264 zeigte ZIM trotz Antragsstopp weiter in
    der R1-Foerdertabelle, waehrend der Strategiebericht es korrekt
    weglies. Grund: Die Statusregel stand zweimal im Code, und KIS-1268
    hatte nur eine der beiden Stellen ergaenzt."""

    def test_regel_kennt_beide_stati(self):
        from services.funding_recommender import NICHT_BEANTRAGBAR_STATUS
        assert NICHT_BEANTRAGBAR_STATUS == frozenset({"expired", "paused"})

    def test_ist_beantragbar_urteilt_richtig(self):
        from services.funding_recommender import ist_beantragbar
        assert ist_beantragbar({"status": "active"})
        assert ist_beantragbar({})  # ohne Angabe gilt aktiv
        assert not ist_beantragbar({"status": "paused"})
        assert not ist_beantragbar({"status": "expired"})
        assert not ist_beantragbar({"status": "  PAUSED "})  # tolerant

    def test_r1_foerdertabelle_zeigt_kein_zim(self):
        """Der Pfad, der im Lauf KIS-1264 durchgerutscht ist."""
        from services.extra_sections import build_core_funding_table_html
        html = build_core_funding_table_html({
            "BRANCHE_LABEL": "Medien & Kreativwirtschaft",
            "BUNDESLAND_LABEL": "Berlin",
            "UNTERNEHMENSGROESSE_LABEL": "2-10 (Kleines Team)",
        })
        assert "ZIM" not in html
        assert len(html) > 200, "Tabelle unerwartet leer — Filter zu scharf?"

    def test_keine_zweite_kopie_der_statusregel(self):
        """Wer die Regel erneut ausschreibt, bricht sie beim naechsten Mal
        wieder auseinander."""
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        kopien = []
        for pfad in list((repo / "services").glob("*.py")):
            if pfad.name == "funding_recommender.py":
                continue
            text = pfad.read_text(encoding="utf-8")
            if 'status", "active") != "expired"' in text:
                kopien.append(pfad.name)
        assert not kopien, f"Eigene Statusregel in: {kopien}"
