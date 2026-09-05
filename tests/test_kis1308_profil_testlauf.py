# -*- coding: utf-8 -*-
"""KIS-1308 — Testlauf aus einem Profil ohne Formular.

Der Replay kopiert nur bestehende Briefings; ein anderes Profil verlangte
den vollen Fragebogen im Frontend. Jetzt: ``POST /api/admin/testrun/profile``
nimmt ein Gold-Profil (answers + strategy_answers), prüft es und stellt es in
die Warteschlange; der Strategiebericht startet wie beim Replay automatisch.
Dazu ein realistisches Profil: Fachverlag in Bayern, 11–100 Mitarbeitende.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROFIL = ROOT / "data" / "test_profiles_gold" / "medien_verlag_bayern_kmu_testlauf.json"


@pytest.fixture(scope="module")
def profil():
    return json.loads(PROFIL.read_text(encoding="utf-8"))


class TestProfil:
    def test_profil_ist_einspielbar(self, profil):
        from services.profil_pruefung import profil_pruefen
        assert profil_pruefen(profil["answers"], profil["strategy_answers"]) == []

    def test_profil_ist_ein_anderer_pfad(self, profil):
        a = profil["answers"]
        assert a["medien_sparte"] == "verlag_publishing"
        assert a["unternehmensgroesse"] == "11–100"
        assert a["bundesland"] == "by"
        # FB2-Budget liegt über FB1 — die Spannungs-Box und die Budgetregel greifen
        assert a["investitionsbudget"] == "10000_50000"
        assert profil["strategy_answers"]["s1_budget"] == "ueber_50000"

    def test_kein_firmenname(self, profil):
        # CI-Invariante: Der Firmenname wird nirgends erhoben.
        text = json.dumps(profil, ensure_ascii=False).lower()
        assert not re.search(r'"(firmenname|company_name|unternehmensname|firma)"', text)

    def test_sparten_logik_greift(self, profil):
        from services.medien_sparte import aus_antworten
        assert aus_antworten(profil["answers"]) == "Verlag / Publishing / Redaktion"


class TestMotionSocialProfil:
    """KIS-1309: Motion-Design- und Social-Media-Studio in München — dritter
    Sparten-Pfad (Content Creation), Bild-/Video-Werkzeuge mit
    Kennzeichnungspflicht, Digitalbonus Bayern."""

    @pytest.fixture(scope="class")
    def motion(self):
        p = ROOT / "data" / "test_profiles_gold" / "medien_motion_social_muenchen_testlauf.json"
        return json.loads(p.read_text(encoding="utf-8"))

    def test_einspielbar(self, motion):
        from services.profil_pruefung import profil_pruefen
        assert profil_pruefen(motion["answers"], motion["strategy_answers"]) == []

    def test_pfad_und_sparte(self, motion):
        from services.medien_sparte import aus_antworten
        a = motion["answers"]
        assert aus_antworten(a) == "Content Creation / Social Media"
        assert a["bundesland"] == "by" and a["unternehmensgroesse"] == "11–100"
        assert "kennzeichnung" in a["ki_guardrails"].lower()
        assert "expected_validation" in motion

    def test_kein_firmenname(self, motion):
        text = json.dumps(motion, ensure_ascii=False).lower()
        assert not re.search(r'"(firmenname|company_name|unternehmensname|firma)"', text)


class TestPruefung:
    def test_pflichtfeld_fehlt(self, profil):
        from services.profil_pruefung import profil_pruefen
        a = dict(profil["answers"])
        a.pop("hauptleistung")
        fehler = profil_pruefen(a, None)
        assert any("hauptleistung" in f for f in fehler)

    def test_unbekannter_enum_wert(self, profil):
        from services.profil_pruefung import profil_pruefen
        a = dict(profil["answers"])
        a["bundesland"] = "bayern"
        assert any("bundesland" in f for f in profil_pruefen(a, None))

    def test_fb2_regeln(self, profil):
        from services.profil_pruefung import profil_pruefen
        s = dict(profil["strategy_answers"])
        s["s1_budget"] = "viel"
        assert any("s1_budget" in f for f in profil_pruefen(profil["answers"], s))

    def test_slider_bereich(self, profil):
        from services.profil_pruefung import profil_pruefen
        a = dict(profil["answers"])
        a["digitalisierungsgrad"] = 12
        assert any("digitalisierungsgrad" in f for f in profil_pruefen(a, None))


class TestVerdrahtung:
    def test_endpunkt_und_trigger(self):
        src = (ROOT / "routes" / "admin_testrun.py").read_text(encoding="utf-8")
        assert '@router.post("/profile")' in src
        assert 'source="admin_profile"' in src
        g = (ROOT / "gpt_analyze.py").read_text(encoding="utf-8")
        i = g.find("def _auto_trigger_strategy_replay")
        assert '"admin_profile"' in g[i:i + 1200]

    def test_skript_prueft_vor_dem_senden(self):
        src = (ROOT / "scripts" / "testlauf_profil.py").read_text(encoding="utf-8")
        assert "profil_pruefen" in src and "/api/admin/testrun/profile" in src
        assert "X-Admin-Key" in src
