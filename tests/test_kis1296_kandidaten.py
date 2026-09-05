# -*- coding: utf-8 -*-
"""KIS-1296: Handprüfung Stufe 4 — Kandidatenliste und Übernahme-Skript.

Der Egress-Proxy blockt jede Anbieterseite; nachlesen kann nur Wolf. Das
Skript nimmt nur bestätigte Zeilen und verweigert Vermutungen: Ein
Werkzeug ohne von Hand eingetragenes ``host``/``gdpr`` kommt nicht in
die Daten.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GUELTIG = {"produktion", "post_vfx", "games", "verlag_publishing", "musik_audio", "agentur_design", "content_creation"}


def _skript():
    spec = importlib.util.spec_from_file_location("ku", REPO / "scripts" / "kandidaten_uebernehmen.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def _kandidaten():
    return json.loads((REPO / "data" / "kandidaten_stufe4.json").read_text(encoding="utf-8"))


class TestKandidatenliste:
    def test_jeder_eintrag_ist_entschieden(self):
        """Faktencheck vom 05.09.2026 (Perplexity, nur Anbieterseiten) ist
        eingearbeitet: jede Zeile traegt ein Urteil, abgelehnte eine Begruendung,
        aufgenommene die belegten Felder."""
        k = _kandidaten()
        for e in k["werkzeuge"] + k["programme"]:
            assert e["bestaetigt"] in (True, False), e.get("name") or e.get("id")
            if e["bestaetigt"] is False:
                assert e.get("_entscheidung"), e.get("name") or e.get("id")
        for w in k["werkzeuge"]:
            assert set(w["sparten"]) <= GUELTIG and w["url"].startswith("https://")
            if w["bestaetigt"]:
                assert w["host"] and w["gdpr"], w["name"]
        for p in k["programme"]:
            assert set(p["sparten"]) <= GUELTIG and p["url"].startswith("https://")
            if p["bestaetigt"]:
                assert p["focus"] and p["funding_rate"], p["id"]

    def test_aufgenommene_stehen_im_seed_mit_pruefdatum(self):
        seed = {t["name"].lower(): t for t in json.loads((REPO / "data" / "tools_seed.json").read_text(encoding="utf-8"))}
        alias = {"deepl write": "deepl write pro"}
        for w in _kandidaten()["werkzeuge"]:
            name = alias.get(w["name"].lower(), w["name"].lower())
            if w["bestaetigt"]:
                assert name in seed, w["name"]
                assert seed[name]["verified_at"] == "2026-09-05" and seed[name]["sparten"], w["name"]
            else:
                assert name not in seed, w["name"]

    def test_abgelehnte_programme_fehlen_und_digitalbonus_ist_aktiv(self):
        progs = {p["id"]: p for p in json.loads((REPO / "data" / "funding_programmes_core_2025.json").read_text(encoding="utf-8"))}
        assert "musikfonds" not in progs
        assert progs["initiative_musik"]["sparten"] == ["musik_audio"] and progs["initiative_musik"]["branch_exclusive"] is True
        assert progs["deutscher_verlagspreis"]["funding_type"] == "Preisgeld"
        # Entscheidung Wolf 05.09.2026: bis zur Wiedervorlage 01.06.2027 pausiert
        assert progs["deutscher_verlagspreis"]["status"] == "paused"
        assert progs["deutscher_verlagspreis"]["recheck_after"] == "2027-06-01"
        assert progs["digitalbonus_bayern"]["status"] == "active" and progs["digitalbonus_bayern"]["deadline"] == "31.12.2027"


class TestUebernahme:
    @pytest.fixture
    def kopie(self, tmp_path):
        """Eigene Kandidatenliste mit zwei offenen Zeilen — die echte Liste
        ist seit dem Faktencheck entschieden und taugt nicht mehr als Fixture."""
        for f in ("tools_seed.json", "funding_programmes_core_2025.json"):
            shutil.copy(REPO / "data" / f, tmp_path / f)
        kand = {
            "werkzeuge": [
                {"name": "Testwerkzeug", "url": "https://x.example", "trust_url": "https://x.example/privacy",
                 "category": "Test", "sparten": ["games"], "host": "", "gdpr": "", "preis": "", "bestaetigt": None},
            ],
            "programme": [
                {"id": "testprogramm", "title": "Testprogramm", "url": "https://y.example", "provider": "Test",
                 "region": "Deutschland (bundesweit)", "sparten": ["musik_audio"],
                 "funding_rate": "", "max_amount": "", "deadline": "", "focus": "", "bestaetigt": None},
            ],
        }
        (tmp_path / "kandidaten.json").write_text(json.dumps(kand), encoding="utf-8")
        return tmp_path

    def _lauf(self, ku, kopie, **kw):
        return ku.uebernehmen(kandidaten=kopie / "kandidaten.json", tools=kopie / "tools_seed.json",
                              funding=kopie / "funding_programmes_core_2025.json", **kw)

    def test_nichts_bestaetigt_nichts_geschrieben(self, kopie):
        ku = _skript()
        vorher = (kopie / "tools_seed.json").read_text(encoding="utf-8")
        b = self._lauf(ku, kopie)
        assert b["werkzeuge"] == [] and b["programme"] == [] and len(b["offen"]) == 2
        assert (kopie / "tools_seed.json").read_text(encoding="utf-8") == vorher

    def test_bestaetigt_ohne_hostangabe_bricht_ab(self, kopie):
        ku = _skript()
        k = json.loads((kopie / "kandidaten.json").read_text(encoding="utf-8"))
        k["werkzeuge"][0]["bestaetigt"] = True  # host/gdpr bleiben leer
        (kopie / "kandidaten.json").write_text(json.dumps(k), encoding="utf-8")
        with pytest.raises(ValueError, match="Vermutung"):
            self._lauf(ku, kopie)

    def test_bestaetigt_mit_angaben_landet_im_seed(self, kopie):
        ku = _skript()
        k = json.loads((kopie / "kandidaten.json").read_text(encoding="utf-8"))
        k["werkzeuge"][0].update({"bestaetigt": True, "host": "EU", "gdpr": "EU-Anbieter (AT), AVV verfügbar", "preis": ""})
        k["programme"][0].update({"bestaetigt": True, "focus": "Testförderung", "funding_rate": "bis 50 %"})
        (kopie / "kandidaten.json").write_text(json.dumps(k), encoding="utf-8")
        b = self._lauf(ku, kopie, datum="2026-09-05")
        assert b["werkzeuge"] == ["Testwerkzeug"] and b["programme"] == ["testprogramm"]
        seed = json.loads((kopie / "tools_seed.json").read_text(encoding="utf-8"))
        neu = next(t for t in seed if t["name"] == "Testwerkzeug")
        assert neu["verified_at"] == "2026-09-05" and neu["price"] == "" and neu["sparten"] == ["games"]
        progs = json.loads((kopie / "funding_programmes_core_2025.json").read_text(encoding="utf-8"))
        pn = next(x for x in progs if x["id"] == "testprogramm")
        assert pn["branch_exclusive"] is True and pn["sparten"] == ["musik_audio"] and pn["verified_at"] == "2026-09-05"
        # zweiter Lauf: idempotent
        b2 = self._lauf(ku, kopie, datum="2026-09-05")
        assert b2["werkzeuge"] == [] and "Testwerkzeug" in b2["uebersprungen"]

    def test_neuer_eintrag_besteht_sparten_gate_regeln(self, kopie):
        """Ein bestätigter Eintrag ohne Preis zeigt im Report 'siehe Anbieterseite' —
        das prüft tools_verified_box.preis_anzeige, hier nur der Datensatz."""
        ku = _skript()
        e = ku.werkzeug_eintrag({"name": "X", "url": "https://x.example", "host": "EU", "gdpr": "EU", "sparten": ["games"]}, "2026-09-05")
        assert e["price"] == "" and e["best_for_industries"] == ["medien"]
