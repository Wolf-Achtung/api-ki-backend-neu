# -*- coding: utf-8 -*-
"""KIS-1281, Stufen 2 bis 4.

**Stufe 2** — Der Radar schlägt vor, statt nur zu melden. „Preis
unbestätigt", 20-mal, jeden Monat: Eine Liste, die nur wächst, wird
nicht abgearbeitet, sondern ignoriert. Was der Radar selbst belegen
kann — alte Adresse tot, neue erreichbar, gleiche Herstellerdomain —
schlägt er als Pull Request vor. Preise bleiben aussen vor: Ein
Suchtreffer liefert eine Seite, keinen geprüften Preis.

**Stufe 3** — Eine Regel statt einer Vermutung. Der Status allein
reicht nicht: Ein Programm kann auf ``active`` stehen und trotzdem eine
abgelaufene Frist tragen. Dieselbe Fehlerklasse wie ZIM (KIS-1268), nur
an einem anderen Feld.

**Stufe 4** — Die Rückmeldung schliesst den Kreis. Zwei Freitextfelder
im Feedback, ein Auswertungsskript. Der interessanteste Wert ist nicht,
welche Empfehlung getragen hat, sondern welches Werkzeug jemand
genommen hat, das wir gar nicht empfehlen.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


# =========================================================================
# Stufe 2
# =========================================================================

class TestRadarSchlaegtVor:

    def _tools(self):
        return [{"name": "Tally.so", "url": "https://tally.so",
                 "trust_url": "https://tally.so/help/privacy"}]

    def _befund(self):
        return [{"type": "dead_url", "tool": "Tally.so",
                 "detail": "trust_url: https://tally.so/help/privacy: HTTP 404"}]

    def test_erreichbarer_ersatz_wird_vorgeschlagen(self):
        from scripts.tools_radar import schlage_url_korrekturen_vor
        v = schlage_url_korrekturen_vor(
            self._tools(), self._befund(),
            {"Tally.so": [{"url": "https://tally.so/help/privacy-policy",
                           "title": "Privacy policy"}]},
            pruefe=lambda url, **kw: None)  # erreichbar
        assert v == [{"tool": "Tally.so", "feld": "trust_url",
                      "alt": "https://tally.so/help/privacy",
                      "neu": "https://tally.so/help/privacy-policy",
                      "titel": "Privacy policy"}]

    def test_nicht_erreichbarer_ersatz_wird_verworfen(self):
        """Eine tote Adresse durch eine andere tote zu ersetzen, waere
        schlimmer als nichts zu tun."""
        from scripts.tools_radar import schlage_url_korrekturen_vor
        assert schlage_url_korrekturen_vor(
            self._tools(), self._befund(),
            {"Tally.so": [{"url": "https://tally.so/weg", "title": "x"}]},
            pruefe=lambda url, **kw: {"art": "dead_url", "detail": "HTTP 404"}) == []

    def test_fremde_domain_wird_verworfen(self):
        from scripts.tools_radar import schlage_url_korrekturen_vor
        assert schlage_url_korrekturen_vor(
            self._tools(), self._befund(),
            {"Tally.so": [{"url": "https://blog.example.com/tally-privacy",
                           "title": "Privacy"}]},
            pruefe=lambda url, **kw: None) == []

    def test_timeout_befund_aendert_nichts(self):
        """`unpruefbar` belegt nicht, dass die Seite weg ist. Vier
        Adobe-Seiten liefen so — sie funktionieren, nur der Prüfer kam
        nicht durch (KIS-1277)."""
        from scripts.tools_radar import schlage_url_korrekturen_vor
        befund = [{"type": "unpruefbar", "tool": "Tally.so",
                   "detail": "trust_url: https://tally.so/help/privacy: ReadTimeout"}]
        assert schlage_url_korrekturen_vor(
            self._tools(), befund,
            {"Tally.so": [{"url": "https://tally.so/help/privacy-policy", "title": "P"}]},
            pruefe=lambda url, **kw: None) == []

    def test_datenschutzseite_schlaegt_startseite(self):
        """Unter mehreren erreichbaren Treffern gewinnt der, der nach
        einem Datenschutz-Beleg aussieht."""
        from scripts.tools_radar import schlage_url_korrekturen_vor
        v = schlage_url_korrekturen_vor(
            self._tools(), self._befund(),
            {"Tally.so": [{"url": "https://tally.so/pricing", "title": "Pricing"},
                          {"url": "https://tally.so/help/privacy-policy",
                           "title": "Privacy policy"}]},
            pruefe=lambda url, **kw: None)
        assert v[0]["neu"] == "https://tally.so/help/privacy-policy"

    def test_schreiben_aendert_nur_die_adresse(self, tmp_path):
        """Neu serialisiertes JSON zeigte jede Zeile als geändert. Ein
        Diff, den niemand lesen kann, wird nicht geprüft."""
        from scripts.tools_radar import wende_korrekturen_an
        datei = tmp_path / "tools_seed.json"
        datei.write_text('[\n  {\n    "name": "Tally.so",\n'
                         '    "trust_url": "https://tally.so/help/privacy"\n  }\n]',
                         encoding="utf-8")
        n = wende_korrekturen_an(
            [{"tool": "Tally.so", "feld": "trust_url",
              "alt": "https://tally.so/help/privacy",
              "neu": "https://tally.so/help/privacy-policy"}], pfad=datei)
        text = datei.read_text(encoding="utf-8")
        assert n == 1
        assert "privacy-policy" in text
        assert text.count("\n") == 5, "Formatierung verändert"

    def test_ohne_vorschlaege_wird_nichts_geschrieben(self, tmp_path):
        from scripts.tools_radar import wende_korrekturen_an
        datei = tmp_path / "x.json"
        datei.write_text("[]", encoding="utf-8")
        assert wende_korrekturen_an([], pfad=datei) == 0
        assert datei.read_text(encoding="utf-8") == "[]"

    def test_workflow_oeffnet_einen_entwurf(self):
        wf = (REPO / ".github" / "workflows" / "tools-radar.yml").read_text(encoding="utf-8")
        assert "--apply-fixes" in wf
        assert "pull-requests: write" in wf
        assert "--draft" in wf, "Ein Automatik-PR gehört als Entwurf angelegt"


# =========================================================================
# Stufe 3
# =========================================================================

class TestFristRegel:

    def _heute(self):
        return date(2026, 9, 4)

    from_import = "services.funding_recommender"

    def test_verstrichene_frist_schliesst_aus(self):
        from services.funding_recommender import ist_beantragbar
        assert not ist_beantragbar({"deadline": "31.12.2020"}, self._heute())

    def test_zukuenftige_frist_bleibt(self):
        from services.funding_recommender import ist_beantragbar
        assert ist_beantragbar({"deadline": "31.12.2026"}, self._heute())

    @pytest.mark.parametrize("text", [
        "laufend", "4 Termine/Jahr", "mehrere Runden/Jahr",
        "Calls ab Herbst 2026", "15.01. und 15.07.", "Gremientermine", "",
    ])
    def test_textangaben_gelten_als_offen(self, text):
        """Wer sie als Frist liest, wirft die halbe Filmförderung raus."""
        from services.funding_recommender import ist_beantragbar
        assert ist_beantragbar({"deadline": text}, self._heute())

    @pytest.mark.parametrize("fmt,wert", [
        ("deutsch", "03.09.2026"), ("iso", "2026-09-03"), ("kurz", "03.09.26"),
    ])
    def test_datumsformate(self, fmt, wert):
        from services.funding_recommender import frist_verstrichen
        assert frist_verstrichen({"deadline": wert}, self._heute()), fmt

    def test_status_gilt_weiter(self):
        """Die Statusregel darf durch die Fristregel nicht verloren gehen."""
        from services.funding_recommender import ist_beantragbar
        assert not ist_beantragbar({"status": "paused", "deadline": "31.12.2030"},
                                   self._heute())
        assert not ist_beantragbar({"status": "expired"}, self._heute())

    def test_die_echten_daten_bleiben_vollstaendig(self):
        """Eine Regel, die heute nichts entfernt, ist genau richtig — die
        Daten sind sauber, das Netz spannt für später."""
        from services.funding_recommender import load_funding_programs
        assert len(load_funding_programs()) >= 30

    def test_regel_steht_nur_an_einer_stelle(self):
        """KIS-1270: Die Statusregel stand zweimal im Code und driftete."""
        kopien = []
        for pfad in (REPO / "services").glob("*.py"):
            if pfad.name == "funding_recommender.py":
                continue
            if "deadline" in (text := pfad.read_text(encoding="utf-8")) \
                    and "strptime" in text and "status" in text:
                kopien.append(pfad.name)
        assert not kopien, f"Eigene Fristprüfung in: {kopien}"


# =========================================================================
# Stufe 4
# =========================================================================

class TestRueckmeldung:

    def test_felder_im_schema(self):
        from routes.feedback import FeedbackPayload
        p = FeedbackPayload(tools_adopted="Notion", funding_applied="ProFIT")
        assert p.tools_adopted == "Notion"
        assert p.funding_applied == "ProFIT"

    def test_felder_bleiben_freiwillig(self):
        """Eine Pflichtfrage senkt die Rücklaufquote der ganzen Umfrage."""
        from routes.feedback import FeedbackPayload
        assert FeedbackPayload().tools_adopted is None

    @pytest.mark.parametrize("antwort,erwartet", [
        ("Notion, Make und Descript", ["notion", "make", "descript"]),
        ("notion; Frame.io", ["notion", "frame.io"]),
        ("keine", []),
        ("", []),
        (None, []),
        ("Noch nichts", []),
    ])
    def test_freitext_wird_zerlegt(self, antwort, erwartet):
        from scripts.empfehlungs_resonanz import zerlege
        assert zerlege(antwort) == erwartet

    def test_nennung_trifft_katalognamen(self):
        """Menschen tippen „make", nicht „Make (Integromat)"."""
        from scripts.empfehlungs_resonanz import auswerten
        getroffen, unbekannt, n = auswerten(
            [{"tools_adopted": "make"}], "tools_adopted", ["Make (Integromat)"])
        assert getroffen == {"Make (Integromat)": 1}
        assert unbekannt == {} and n == 1

    def test_unbekanntes_werkzeug_wird_gemeldet(self):
        """Der wertvollste Wert: was jemand STATT unserer Empfehlung nimmt."""
        from scripts.empfehlungs_resonanz import auswerten
        getroffen, unbekannt, _ = auswerten(
            [{"tools_adopted": "CapCut"}], "tools_adopted", ["Make (Integromat)"])
        assert getroffen == {} and unbekannt == {"capcut": 1}

    def test_leere_antworten_zaehlen_nicht_mit(self):
        from scripts.empfehlungs_resonanz import auswerten
        _, _, n = auswerten([{"tools_adopted": "keine"}, {}, {"tools_adopted": "Notion"}],
                            "tools_adopted", ["Notion"])
        assert n == 1

    def test_bericht_warnt_bei_zu_wenig_antworten(self, tmp_path, capsys):
        """Aus fünf Antworten lässt sich keine Empfehlung streichen."""
        from scripts.empfehlungs_resonanz import main
        datei = tmp_path / "fb.json"
        datei.write_text('[{"tools_adopted": "Notion"}]', encoding="utf-8")
        assert main(["--datei", str(datei)]) == 0
        assert "Zufall, keine Aussage" in capsys.readouterr().out

    def test_fehlende_datei_meldet_sich(self, tmp_path):
        from scripts.empfehlungs_resonanz import main
        assert main(["--datei", str(tmp_path / "gibtsnicht.json")]) == 2
