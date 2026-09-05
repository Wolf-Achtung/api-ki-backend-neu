# -*- coding: utf-8 -*-
"""KIS-1295 (Stufe 6 des Branchen-Audits): Ein Gold-Profil je Sparte.

Der laute Prüfer, der Stufe 1 bis 4 gegen Rückfall sichert. Sieben
deterministische Profile (data/test_profiles_gold/medien_<sparte>_sparte.json)
mit gesetztem ``medien_sparte`` laufen durch alles, was ohne Netz und
ohne Modell entscheidet:

  * Label (KIS-1288) — nie der Roh-Slug
  * Fallstudie (KIS-1292) — Verlag, Tonstudio, Content Creation eigen
  * Fördertabelle R1 (KIS-1293) — Kinofilm nur für Film-Sparten
  * Werkzeugliste und Faktenblock (KIS-1292/1293) — Sparten-Werkzeug vorn
  * System-Prompt (KIS-1288) — Sparten-Satz haengt dran
  * Optionen (KIS-1291) — jeder neue Wert hat ein Label
  * Platin-Kette (KIS-1261) — 0 Befunde wie im Referenz-Gate

Kein Netz, kein LLM, keine DB.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from services.medien_sparte import SPARTEN, LABELS_DE, aus_antworten, label

REPO = Path(__file__).resolve().parents[2]
PROFIL_DIR = REPO / "data" / "test_profiles_gold"

# Erwartetes Sparten-Werkzeug unter den ersten acht Empfehlungen
SPARTEN_WERKZEUG = {
    "produktion": ("Amberscript", "Frame.io (Adobe)", "Simon Says"),
    "post_vfx": ("Topaz Video AI", "Frame.io (Adobe)", "Runway"),
    "games": ("ElevenLabs", "DeepL Pro", "Adobe Firefly"),
    "verlag_publishing": ("DeepL Pro", "Aleph Alpha PhariaAI", "Adobe Firefly"),
    "musik_audio": ("ElevenLabs", "Descript", "Amberscript"),
    "agentur_design": ("Adobe Firefly", "Runway", "Frame.io (Adobe)"),
    "content_creation": ("Descript", "Runway", "Adobe Firefly"),
}
FILM_SPARTEN = {"produktion", "post_vfx"}
LISTENFELDER = ("ki_einsatz", "datenquellen", "anwendungsfaelle", "vorhandene_tools", "trainings_interessen")

# KIS-1297: Der Film-Marker kommt aus den Daten, nicht aus dem Test. Bis zum
# 20.08.2026 war das der DFFF; seit dem Antragsstopp (paused bis zur
# Wiedervorlage 01.11.2026) tragen andere Film-Programme die Pruefung.
FUND = json.loads((REPO / "data" / "funding_programmes_core_2025.json").read_text(encoding="utf-8"))


def _beantragbar(p: dict) -> bool:
    from services.funding_recommender import ist_beantragbar
    return ist_beantragbar(p)


PAUSIERT_TITEL = [p["title"] for p in FUND if not _beantragbar(p)]


def _exklusiv_passend(sparte: str) -> list:
    """Beantragbare exklusive Programme, die die Sparte nennen."""
    return [p["title"] for p in FUND if p.get("branch_exclusive") and p.get("sparten")
            and sparte in p["sparten"] and _beantragbar(p)]


def _exklusiv_fremd(sparte: str) -> list:
    """Exklusive Programme, die die Sparte NICHT nennen — duerfen nie erscheinen."""
    return [p["title"] for p in FUND if p.get("branch_exclusive") and p.get("sparten")
            and sparte not in p["sparten"]]


def _profil(sparte: str) -> dict:
    return json.loads((PROFIL_DIR / f"medien_{sparte}_sparte.json").read_text(encoding="utf-8"))


def _referenz_gate():
    spec = importlib.util.spec_from_file_location(
        "referenz_gate", Path(__file__).with_name("test_golden_reference_gate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("sparte", SPARTEN)
class TestSpartenGate:

    def test_profil_ist_vollstaendig_und_gueltig(self, sparte):
        from services.chat_normalizer import ENUM_VALUES
        p = _profil(sparte)
        a = p["answers"]
        assert a["medien_sparte"] == sparte and a["branche"] == "medien"
        assert p["MEDIEN_SPARTE_LABEL"] == LABELS_DE[sparte]
        for feld in LISTENFELDER:
            assert a[feld], feld
            fremd = [v for v in a[feld] if v not in ENUM_VALUES[feld]]
            assert not fremd, (feld, fremd)
        assert a["pilot_bereich"] in ENUM_VALUES["pilot_bereich"]

    def test_label_nie_roh_slug(self, sparte):
        a = _profil(sparte)["answers"]
        assert aus_antworten(a) == LABELS_DE[sparte]
        assert label(a["medien_sparte"], "en") and "_" not in label(a["medien_sparte"], "en")

    def test_optionen_haben_labels(self, sparte):
        import gpt_analyze as g
        a = _profil(sparte)["answers"]
        for feld in LISTENFELDER:
            for wert in a[feld]:
                lbl = g._label_for(feld, wert)
                assert lbl and lbl != wert and "_" not in lbl, (feld, wert, lbl)
        assert g._label_for("pilot_bereich", a["pilot_bereich"]) != a["pilot_bereich"]

    def test_fallstudie_passt_zur_sparte(self, sparte):
        from services.sofort_start_generator import _pick_medien_fallstudie
        a = _profil(sparte)["answers"]
        size = {"1": "solo", "2–10": "team", "11–100": "kmu"}[a["unternehmensgroesse"]]
        titel = _pick_medien_fallstudie(a["medien_sparte"], size)["titel"]
        erwartet = {
            "produktion": "Doku-Produktion", "post_vfx": "Doku-Produktion", "games": "Games-Studio",
            "verlag_publishing": "Fachverlag", "musik_audio": "Tonstudio",
            "agentur_design": "Werbefilm-Studio", "content_creation": "Content-Team",
        }[sparte]
        assert erwartet in titel, titel

    def test_foerdertabelle_r1_filtert(self, sparte):
        from services.extra_sections import build_core_funding_table_html
        p = _profil(sparte)
        html = build_core_funding_table_html({
            "BRANCHE_LABEL": p["BRANCHE_LABEL"], "BUNDESLAND_LABEL": p["answers"]["bundesland"],
            "UNTERNEHMENSGROESSE_LABEL": p["UNTERNEHMENSGROESSE_LABEL"], "country": "DE",
            "MEDIEN_SPARTE_LABEL": p["MEDIEN_SPARTE_LABEL"],
        })
        assert "<table" in html
        # KIS-1298: Hinweiszeile zu ausgesetzten Programmen der eigenen Sparte
        # steht unter der Tabelle und zaehlt hier nicht als Empfehlung.
        html = html.partition('class="small muted funding-paused-note"')[0]
        fremd = [t for t in _exklusiv_fremd(sparte) if t in html]
        assert not fremd, (sparte, fremd)
        if sparte in FILM_SPARTEN:
            assert any(t in html for t in _exklusiv_passend(sparte)), (sparte, _exklusiv_passend(sparte))
        # Antragsstopp (DFFF/GMPF seit 20.08.2026, ZIM) erscheint nirgends
        assert not any(t in html for t in PAUSIERT_TITEL), sparte
        if sparte == "games":
            assert "Games-Förderung" in html
        else:
            assert "Games-Förderung" not in html

    def test_foerderempfehlung_filtert(self, sparte):
        from services.funding_recommender import get_filtered_funding_programs
        a = _profil(sparte)["answers"]
        size = {"1": "solo", "2–10": "team", "11–100": "kmu"}[a["unternehmensgroesse"]]
        namen = [x["name"] for x in get_filtered_funding_programs(
            bundesland=a["bundesland"], size=size, branch="medien", limit=40, sparte=sparte)]
        assert namen
        fremd = set(namen) & set(_exklusiv_fremd(sparte))
        assert not fremd, (sparte, fremd)
        assert not any(n in PAUSIERT_TITEL for n in namen), namen

    def test_werkzeuge_und_faktenblock(self, sparte):
        from services.tools_recommender import recommend_tools
        from services.kuratierte_fakten import build_tool_fakten_strategie, tool_namen_strategie
        a = _profil(sparte)["answers"]
        vorn = [t["name"] for t in recommend_tools(a, max_tools=8)]
        assert set(vorn) & set(SPARTEN_WERKZEUG[sparte]), (sparte, vorn)
        block = build_tool_fakten_strategie(a, lang="de")
        assert "GEPRÜFTE WERKZEUG-DATEN" in block and "https://" in block
        assert any(w in tool_namen_strategie(a) for w in SPARTEN_WERKZEUG[sparte])

    def test_system_prompt_traegt_die_sparte(self, sparte):
        from services.medien_sparte_prompt import persona_und_sparte
        prompt = persona_und_sparte("Du bist ein KI-Berater.\nRegeln folgen.", sparte=LABELS_DE[sparte], lang="de")
        assert LABELS_DE[sparte] in prompt

    def test_platin_kette_null_befunde(self, sparte):
        from services.platin_qa import scan_sections
        gate = _referenz_gate()
        a = _profil(sparte)["answers"]
        healed = gate._run_platin_chain(gate.build_raw_sections(a), a)
        assert scan_sections(healed, a) == []


class TestSpartenGateVollstaendig:
    def test_alle_sieben_sparten_haben_ein_profil(self):
        fehlend = [s for s in SPARTEN if not (PROFIL_DIR / f"medien_{s}_sparte.json").exists()]
        assert not fehlend, fehlend

    def test_fallstudien_sind_eigen(self):
        from services.sofort_start_generator import _pick_medien_fallstudie
        titel = {s: _pick_medien_fallstudie(s, "team")["titel"] for s in SPARTEN}
        eigen = {k: v for k, v in titel.items() if k != "post_vfx"}
        assert len(set(eigen.values())) == len(eigen), eigen
