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
    def test_alle_eintraege_offen_und_ohne_preis(self):
        k = _kandidaten()
        for e in k["werkzeuge"] + k["programme"]:
            assert e["bestaetigt"] is None, e.get("name") or e.get("id")
        for w in k["werkzeuge"]:
            assert w["preis"] == "" and w["host"] == "" and w["gdpr"] == ""
            assert set(w["sparten"]) <= GUELTIG and w["url"].startswith("https://")
            assert w["pruefen"], w["name"]
        for p in k["programme"]:
            assert set(p["sparten"]) <= GUELTIG and p["url"].startswith("https://")

    def test_keine_dubletten_zum_seed(self):
        seed = {t["name"].lower() for t in json.loads((REPO / "data" / "tools_seed.json").read_text(encoding="utf-8"))}
        for w in _kandidaten()["werkzeuge"]:
            assert w["name"].lower() not in seed, w["name"]


class TestUebernahme:
    @pytest.fixture
    def kopie(self, tmp_path):
        for f in ("kandidaten_stufe4.json", "tools_seed.json", "funding_programmes_core_2025.json"):
            shutil.copy(REPO / "data" / f, tmp_path / f)
        return tmp_path

    def test_nichts_bestaetigt_nichts_geschrieben(self, kopie):
        ku = _skript()
        vorher = (kopie / "tools_seed.json").read_text(encoding="utf-8")
        b = ku.uebernehmen(kandidaten=kopie / "kandidaten_stufe4.json", tools=kopie / "tools_seed.json",
                           funding=kopie / "funding_programmes_core_2025.json")
        assert b["werkzeuge"] == [] and b["programme"] == [] and len(b["offen"]) == 15
        assert (kopie / "tools_seed.json").read_text(encoding="utf-8") == vorher

    def test_bestaetigt_ohne_hostangabe_bricht_ab(self, kopie):
        ku = _skript()
        k = json.loads((kopie / "kandidaten_stufe4.json").read_text(encoding="utf-8"))
        k["werkzeuge"][0]["bestaetigt"] = True  # host/gdpr bleiben leer
        (kopie / "kandidaten_stufe4.json").write_text(json.dumps(k), encoding="utf-8")
        with pytest.raises(ValueError, match="Vermutung"):
            ku.uebernehmen(kandidaten=kopie / "kandidaten_stufe4.json", tools=kopie / "tools_seed.json",
                           funding=kopie / "funding_programmes_core_2025.json")

    def test_bestaetigt_mit_angaben_landet_im_seed(self, kopie):
        ku = _skript()
        k = json.loads((kopie / "kandidaten_stufe4.json").read_text(encoding="utf-8"))
        w = next(x for x in k["werkzeuge"] if x["name"] == "Auphonic")
        w.update({"bestaetigt": True, "host": "EU", "gdpr": "EU-Anbieter (AT), AVV verfügbar", "preis": ""})
        p = k["programme"][0]
        p.update({"bestaetigt": True, "focus": "Infrastrukturförderung für Unternehmen der Musikwirtschaft", "funding_rate": "bis 50 %"})
        (kopie / "kandidaten_stufe4.json").write_text(json.dumps(k), encoding="utf-8")
        b = ku.uebernehmen(datum="2026-09-05", kandidaten=kopie / "kandidaten_stufe4.json",
                           tools=kopie / "tools_seed.json", funding=kopie / "funding_programmes_core_2025.json")
        assert b["werkzeuge"] == ["Auphonic"] and b["programme"] == ["initiative_musik"]
        seed = json.loads((kopie / "tools_seed.json").read_text(encoding="utf-8"))
        neu = next(t for t in seed if t["name"] == "Auphonic")
        assert neu["verified_at"] == "2026-09-05" and neu["price"] == "" and neu["sparten"] == ["musik_audio", "content_creation", "produktion"]
        progs = json.loads((kopie / "funding_programmes_core_2025.json").read_text(encoding="utf-8"))
        pn = next(x for x in progs if x["id"] == "initiative_musik")
        assert pn["branch_exclusive"] is True and pn["sparten"] == ["musik_audio"] and pn["verified_at"] == "2026-09-05"
        # zweiter Lauf: idempotent
        b2 = ku.uebernehmen(datum="2026-09-05", kandidaten=kopie / "kandidaten_stufe4.json",
                            tools=kopie / "tools_seed.json", funding=kopie / "funding_programmes_core_2025.json")
        assert b2["werkzeuge"] == [] and "Auphonic" in b2["uebersprungen"]

    def test_neuer_eintrag_besteht_sparten_gate_regeln(self, kopie):
        """Ein bestätigter Eintrag ohne Preis zeigt im Report 'siehe Anbieterseite' —
        das prüft tools_verified_box.preis_anzeige, hier nur der Datensatz."""
        ku = _skript()
        e = ku.werkzeug_eintrag({"name": "X", "url": "https://x.example", "host": "EU", "gdpr": "EU", "sparten": ["games"]}, "2026-09-05")
        assert e["price"] == "" and e["best_for_industries"] == ["medien"]
