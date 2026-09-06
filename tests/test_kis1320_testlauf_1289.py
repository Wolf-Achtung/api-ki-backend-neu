# -*- coding: utf-8 -*-
"""KIS-1320 — Testlauf KIS1289 (06.09.2026, Build 1422, Motion-Profil nach
KIS-1319). Alle KIS-1319-Punkte im PDF, Kennzahlen unverändert, kein
Rückfall. Restbefunde im Code:

- R1 S. 18: DSGVO-Risikostufe „Mittel", Note C — Lauf KIS1288 mit identischen
  Antworten hatte „Niedrig", Note B. Der Unterschied war das Wort
  „personenbezogen" in der generierten Risiko-Sektion.
- Strategie S. 10: „Impact: ● hoch , Umsetzungskomplexität: ● mittel ." —
  Leerzeichen vor Komma und Punkt (Wächter `wort_vor_punkt_fehlt`).
- Strategie S. 21: Quellenzeile ohne Etikett „Quellen:" (zweiter Lauf).
- R1 S. 30: „nicht durch Zurückhaltation".
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class TestDsgvoAusAntworten:
    def _antworten(self) -> dict:
        p = ROOT / "data/test_profiles_gold/medien_motion_social_muenchen_testlauf.json"
        return json.loads(p.read_text(encoding="utf-8"))["answers"]

    def test_stufe_unabhaengig_vom_modelltext(self):
        from services.risk_engine_v2 import extract_dsgvo_risk_from_sections as f
        a = self._antworten()
        ohne = f({}, a)
        mit = f({"RISKS_HTML": "<p>Verarbeitung personenbezogener Daten, Auskunft</p>"}, a)
        assert ohne == mit
        assert ohne["dsgvo_risk_level"] == "mittel"
        assert any("Nutzungs" in x for x in ohne["dsgvo_risk_factors"])
        assert any("lückenhaft" in x for x in ohne["dsgvo_risk_factors"])
        assert "Verarbeitung personenbezogener Daten" not in ohne["dsgvo_risk_factors"]

    def test_saubere_organisation_ohne_personendaten_ist_niedrig(self):
        from services.risk_engine_v2 import extract_dsgvo_risk_from_sections as f
        a = {"datenquellen": ["rohmaterial_archiv"], "folgenabschaetzung": "ja", "meldewege": "ja",
             "loeschregeln": "ja", "datenschutzbeauftragter": "ja", "technische_massnahmen": "alle"}
        assert f({"RISKS_HTML": "personenbezogen"}, a)["dsgvo_risk_level"] == "niedrig"

    def test_textpfad_bleibt_ohne_antworten(self):
        from services.risk_engine_v2 import extract_dsgvo_risk_from_sections as f
        r = f({"RISKS_HTML": "<div>Verarbeitung personenbezogener Daten</div>"}, {"datentypen": ["Kundendaten"]})
        assert r["dsgvo_risk_level"] == "mittel"
        assert "Verarbeitung personenbezogener Daten" in r["dsgvo_risk_factors"]


class TestSatzzeichen:
    @pytest.mark.parametrize("vorher,nachher", [
        ('<p><strong>Impact:</strong> <span class="ampel-green">●</span> hoch , <strong>Umsetzungskomplexität:</strong> <span class="ampel-yellow">●</span> mittel .</p>',
         '<p><strong>Impact:</strong> <span class="ampel-green">●</span> hoch, <strong>Umsetzungskomplexität:</strong> <span class="ampel-yellow">●</span> mittel.</p>'),
        ('<p>Impact: <span class="ampel-green">● hoch</span> , Komplexität: <span>● mittel</span> .</p>',
         '<p>Impact: <span class="ampel-green">● hoch</span>, Komplexität: <span>● mittel</span>.</p>'),
    ])
    def test_korrigiert(self, vorher, nachher):
        from services.strategy_sanitizer import satzzeichen_abstand_korrigieren
        assert satzzeichen_abstand_korrigieren(vorher)[0] == nachher

    def test_laesst_zahlen_und_saubere_saetze(self):
        from services.strategy_sanitizer import satzzeichen_abstand_korrigieren
        html = "<p>Phase 1 . 2. Schritt: 3 , 5 % und 1.200 € . Fertig, ja.</p>"
        assert satzzeichen_abstand_korrigieren(html) == (html, 0)

    def test_laeuft_im_sanitizer(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        secs = {"S3": "<p>" + "Impact: ● hoch , Komplexität: ● mittel . " * 6 + "</p>"}
        out = sanitize_strategy_sections(secs)
        assert " ," not in out["S3"] and " ." not in out["S3"]


class TestKleinigkeiten:
    def test_zurueckhaltation(self):
        from services.content_quality_enforcer import fix_text_glitches
        assert fix_text_glitches("<p>nicht durch Zurückhaltation, sondern</p>")[0] == "<p>nicht durch Zurückhaltung, sondern</p>"

    def test_s5_prompt_nennt_quellen_etikett(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        assert "„Quellen: Unternehmensdaten, KI-Readiness Report, interne Kalkulation\"" in STRATEGY_PROMPTS["S5"]
