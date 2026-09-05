# -*- coding: utf-8 -*-
"""KIS-1297: Förder-Frischecheck an der wirksamen Datei, DFFF/GMPF-Antragsstopp.

Die monatliche Routine (05.09.2026) pflegte ``data/funding/funding_de.json``
— eine Datei, die kein Report las. Die wirksame Quelle der deutschen
Reports, ``data/funding_programmes_core_2025.json``, kannte das
Frischecheck-Skript nicht. So blieb DFFF/GMPF dort auf „laufend", obwohl
die FFA seit dem 20.08.2026 keine Anträge für Drehbeginn 2026 mehr annimmt
(belegt am 05.09.2026 auf ffa.de, siehe docs/FOERDER_VERIFIKATION_2026-09-05.md).

Regeln:
  * Das Skript prüft core_2025 (``verified_at``) und die beiden EN-Dateien
    (``last_verified``). Die toten Dateien funding_de/eu.json sind weg,
    ebenso services/funding_service.py, der einzige Leser.
  * DFFF und GMPF: ``paused`` mit Wiedervorlage 01.11.2026 — in beiden
    Datenwelten. Der Radar erinnert ab diesem Tag.
  * Der EN-Pfad wendet dieselbe Statusregel an wie der deutsche
    (``ist_beantragbar``); vorher stand ZIM trotz Antragsstopp in der
    englischen Förderbox.
"""
from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
KERN = json.loads((REPO / "data" / "funding_programmes_core_2025.json").read_text(encoding="utf-8"))
DE_EN = json.loads((REPO / "data" / "funding" / "funding_de_en.json").read_text(encoding="utf-8"))["programmes"]
HEUTE = date(2026, 9, 5)


def _kern(pid: str) -> dict:
    return next(p for p in KERN if p["id"] == pid)


def _de_en(pid: str) -> dict:
    return next(p for p in DE_EN if p["id"] == pid)


def _skript():
    spec = importlib.util.spec_from_file_location("cff", REPO / "scripts" / "check_funding_freshness.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


class TestAntragsstoppDfffGmpf:
    @pytest.mark.parametrize("pid", ["dfff", "gmpf"])
    def test_beide_datenwelten_kennen_den_stopp(self, pid):
        for p in (_kern(pid), _de_en(pid)):
            assert p["status"] == "paused", pid
            assert p["recheck_after"] == "2026-11-01", pid
        assert _kern(pid)["verified_at"] == "2026-09-05"
        assert _de_en(pid)["last_verified"] == "2026-09-05"

    @pytest.mark.parametrize("pid", ["dfff", "gmpf"])
    def test_notiz_traegt_beleg_und_rueckkehr(self, pid):
        notiz = _kern(pid)["notes"]
        assert "20.08.2026" in notiz and "ffa.de" in notiz
        assert "November 2026" in notiz
        # Die angekündigte Fusion kam nicht — beide bleiben getrennte Programme.
        assert "Keine Fusion" in notiz
        assert "Fusion Mitte 2026 angekündigt" not in notiz

    def test_en_urls_zeigen_auf_die_ffa(self):
        assert _de_en("dfff")["url"].startswith("https://www.ffa.de/")
        assert _de_en("gmpf")["url"].startswith("https://www.ffa.de/")

    @pytest.mark.parametrize("pid", ["dfff", "gmpf"])
    def test_radar_schweigt_heute_und_erinnert_im_november(self, pid):
        from scripts.funding_radar import check_program
        assert check_program(_kern(pid), HEUTE) == []
        befunde = check_program(_kern(pid), date(2026, 11, 1))
        assert len(befunde) == 1 and befunde[0]["type"] == "recheck"

    def test_deutscher_report_empfiehlt_keinen_dfff(self):
        from services.funding_recommender import get_filtered_funding_programs
        namen = [p["name"] for p in get_filtered_funding_programs(
            bundesland="be", size="team", branch="medien", limit=40, sparte="produktion")]
        assert namen
        assert not any("DFFF" in n or "GMPF" in n for n in namen), namen

    def test_r1_tabelle_zeigt_keinen_dfff(self):
        from services.extra_sections import build_core_funding_table_html
        html = build_core_funding_table_html({
            "BRANCHE_LABEL": "Medien & Kreativwirtschaft", "BUNDESLAND_LABEL": "Berlin",
            "UNTERNEHMENSGROESSE_LABEL": "Team (2-10)", "country": "DE",
            "MEDIEN_SPARTE_LABEL": "Film-/TV-Produktion",
        })
        assert "<table" in html
        # KIS-1298: Die Tabelle selbst bleibt frei von pausierten Programmen;
        # darunter steht ein Hinweis mit Wiedervorlage (kein Betrag, keine Quote).
        tabelle, _, hinweis = html.partition('class="small muted funding-paused-note"')
        assert "DFFF" not in tabelle and "GMPF" not in tabelle
        assert "DFFF" in hinweis and "01.11.2026" in hinweis and "€" not in hinweis


class TestEnPfadKenntDieStatusregel:
    """Vor KIS-1297 hatte funding_de_en.json kein Statusfeld; der EN-Pfad
    zeigte ZIM (Antragsstopp seit 07.07.2026) mit priority 3 weiter an."""

    def test_zim_traegt_status_in_der_en_datei(self):
        zim = _de_en("zim")
        assert zim["status"] == "paused" and zim["recheck_after"] == "2027-01-15"

    def test_match_filtert_pausierte(self):
        from services.funding_service_en import _match_programmes
        progs = [
            {"id": "a", "suitable_for": ["team"], "status": "paused"},
            {"id": "b", "suitable_for": ["team"], "status": "expired"},
            {"id": "c", "suitable_for": ["team"]},
        ]
        assert [p["id"] for p in _match_programmes(progs, "team")] == ["c"]

    def test_eu_core_filtert_pausierte(self):
        from services.funding_service_en import _match_eu_core_programmes
        progs = [
            {"id": "a", "target_groups_en": ["SMEs"], "status": "paused"},
            {"id": "c", "target_groups_en": ["SMEs"]},
        ]
        assert [p["id"] for p in _match_eu_core_programmes(progs, "sme")] == ["c"]

    def test_englischer_filmkunde_sieht_weder_dfff_noch_zim(self):
        from services.funding_service_en import get_funding_for_germany_en
        r = get_funding_for_germany_en({"unternehmensgroesse": "team", "bundesland": "BE", "branche": "medien"})
        ids = [p["id"] for p in r.programmes]
        assert ids, "EN-Foerderbox leer"
        assert not ({"dfff", "gmpf", "zim"} & set(ids)), ids


class TestFrischecheckSkript:
    def test_prueft_die_wirksame_datei(self):
        cff = _skript()
        namen = [p.name for p, _, _ in cff.QUELLEN]
        assert namen == ["funding_programmes_core_2025.json", "funding_de_en.json", "funding_eu_core_en.json"]
        assert all(p.exists() for p, _, _ in cff.QUELLEN)

    def test_tote_dateien_und_ihr_leser_sind_weg(self):
        assert not (REPO / "data" / "funding" / "funding_de.json").exists()
        assert not (REPO / "data" / "funding" / "funding_eu.json").exists()
        assert not (REPO / "data" / "funding" / "config.json").exists()
        assert not (REPO / "services" / "funding_service.py").exists()

    def test_core_eintraege_landen_im_befund(self):
        cff = _skript()
        fresh, stale = cff.pruefe(max_age_days=30, today=HEUTE)
        ids = {pid for d, pid, *_ in stale if d == "funding_programmes_core_2025.json"}
        erwartet = {p["id"] for p in KERN if (p.get("verified_at") or "9999") < "2026-08-06"}
        assert erwartet and erwartet <= ids, erwartet - ids
        # frisch geprueft (05.09.2026) faellt nicht auf
        assert "dfff" not in ids and "gmpf" not in ids

    def test_branchenfilter_versteht_beide_feldnamen(self):
        cff = _skript()
        _, alle = cff.pruefe(max_age_days=30, today=HEUTE)
        _, medien = cff.pruefe(max_age_days=30, branche="medien", today=HEUTE)
        assert 0 < len(medien) <= len(alle)

    def test_heute_sind_nur_drei_offen(self):
        """Die drei Eintraege ohne Pruefdatum, die schon die Routine vom 05.09.
        meldete — bewusst zurueckgestellt (Sammel-/Rahmenprogramme)."""
        cff = _skript()
        _, stale = cff.pruefe(max_age_days=90, today=HEUTE)
        assert {pid for _, pid, *_ in stale} == {"digital_verwaltung_itsec", "esf_plus_digital_skills", "interreg"}
