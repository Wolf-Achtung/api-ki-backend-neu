# -*- coding: utf-8 -*-
"""KIS-1292 (Stufe 4 des Branchen-Audits): Sparten-Feld in den Daten.

Bis hierher kannten Werkzeug- und Foerderauswahl nur ``branche``. Ein
Tonstudio bekam deshalb dieselbe Werkzeugliste wie ein Games-Studio und
eine Foerdertabelle voller Kinofilm-Programme (DFFF, GMPF), die es nie
beantragen kann. Die Fallstudie fuer Verlag, Tonstudio und Content
Creation war das Werbefilm-Studio.

Regeln:
  * ``sparten`` ist optional. Fehlt es, aendert sich nichts (None).
  * Werkzeuge: Treffer steigt auf, kein Treffer faellt nicht heraus.
  * Foerderung: Treffer ×1.2; kein Treffer bei ``branch_exclusive`` → raus,
    sonst ×0.8. Ohne Kunden-Sparte bleibt alles wie bisher.
  * Jede Sparte im Datensatz ist ein gueltiger Slug aus medien_sparte.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.medien_sparte import SPARTEN, passt_zur_sparte, slug_aus_antworten

REPO = Path(__file__).resolve().parent.parent
TOOLS = json.loads((REPO / "data" / "tools_seed.json").read_text(encoding="utf-8"))
FUND = json.loads((REPO / "data" / "funding_programmes_core_2025.json").read_text(encoding="utf-8"))


class TestHelfer:
    def test_ohne_feld_keine_aussage(self):
        assert passt_zur_sparte({"name": "x"}, "games") is None
        assert passt_zur_sparte({"sparten": []}, "games") is None
        assert passt_zur_sparte({"sparten": ["games"]}, "") is None
        assert passt_zur_sparte(None, "games") is None

    def test_treffer_und_fehltreffer(self):
        assert passt_zur_sparte({"sparten": ["games", "post_vfx"]}, "games") is True
        assert passt_zur_sparte({"sparten": ["games"]}, "verlag_publishing") is False

    def test_label_wird_verstanden(self):
        from services.medien_sparte import LABELS_DE
        assert passt_zur_sparte({"sparten": ["musik_audio"]}, LABELS_DE["musik_audio"]) is True

    def test_slug_aus_antworten(self):
        assert slug_aus_antworten({"medien_sparte": "games"}) == "games"
        assert slug_aus_antworten({"medien_sparte": "unbekannt"}) == ""
        assert slug_aus_antworten({}) == ""


class TestDatenSindKonsistent:
    @pytest.mark.parametrize("eintrag", [t for t in TOOLS if "sparten" in t], ids=lambda t: t["name"])
    def test_werkzeug_sparten_gueltig(self, eintrag):
        assert eintrag["sparten"], eintrag["name"]
        assert set(eintrag["sparten"]) <= set(SPARTEN), eintrag["name"]
        assert "medien" in eintrag.get("best_for_industries", []), eintrag["name"]

    @pytest.mark.parametrize("prog", [p for p in FUND if "sparten" in p], ids=lambda p: p["id"])
    def test_programm_sparten_gueltig(self, prog):
        assert prog["sparten"], prog["id"]
        assert set(prog["sparten"]) <= set(SPARTEN), prog["id"]
        assert prog.get("branch_exclusive") is True, prog["id"]

    def test_jedes_medien_werkzeug_ist_getaggt(self):
        """Werkzeuge, die nur fuer Medien gelistet sind, brauchen die Sparte."""
        fehlend = [t["name"] for t in TOOLS
                   if t.get("best_for_industries") == ["medien"] and not t.get("sparten")]
        assert not fehlend, fehlend

    def test_jedes_exklusive_medienprogramm_ist_getaggt(self):
        fehlend = [p["id"] for p in FUND
                   if p.get("branch_exclusive") and p.get("branches") == ["medien"]
                   and not p.get("sparten")]
        assert not fehlend, fehlend

    def test_generische_eintraege_bleiben_ohne_sparte(self):
        assert not any("sparten" in p for p in FUND if p.get("branches") in (None, ["all"]))


def _tools(sparte: str = "", **extra):
    from services.tools_recommender import recommend_tools
    b = {"branche": "medien", "unternehmensgroesse": "team", "medien_sparte": sparte}
    b.update(extra)
    return [t["name"] for t in recommend_tools(b, max_tools=23)]


class TestWerkzeuge:
    def test_ohne_sparte_unveraendert_zur_reihenfolge_ohne_feld(self, monkeypatch):
        """Ohne Kunden-Sparte darf das neue Feld die Reihenfolge nicht bewegen."""
        import services.tools_recommender as tr
        mit = _tools("")
        ohne_feld = [dict(t, sparten=None) for t in tr._load_seed()]
        monkeypatch.setattr(tr, "_load_seed", lambda: ohne_feld)
        assert _tools("") == mit

    def test_games_studio_sieht_seine_werkzeuge_vorn(self):
        namen = _tools("games")
        for w in ("ElevenLabs", "DeepL Pro", "Adobe Firefly"):
            assert namen.index(w) < namen.index("Topaz Video AI"), (w, namen)

    def test_tonstudio_sieht_audio_vorn(self):
        namen = _tools("musik_audio")
        assert namen.index("ElevenLabs") < namen.index("Frame.io (Adobe)"), namen
        assert namen.index("Descript") < namen.index("iconik"), namen

    def test_kein_werkzeug_faellt_heraus(self):
        assert len(_tools("verlag_publishing")) == len(_tools(""))

    def test_label_statt_slug_wirkt_gleich(self):
        assert _tools("Games") == _tools("games")


def _programme(sparte: str = "", bundesland: str = "nw", size: str = "team"):
    from services.funding_recommender import get_filtered_funding_programs
    return [p["name"] for p in get_filtered_funding_programs(
        bundesland=bundesland, size=size, branch="medien", limit=40, sparte=sparte)]


def _film_only() -> set:
    """KIS-1297: Marker aus den Daten — DFFF/GMPF stehen seit dem Antragsstopp
    vom 20.08.2026 auf paused und tragen die Pruefung nicht mehr."""
    from services.funding_recommender import ist_beantragbar
    return {p["title"] for p in FUND if p.get("branch_exclusive") and p.get("sparten")
            and set(p["sparten"]) <= {"produktion", "post_vfx"} and ist_beantragbar(p)}


class TestFoerderung:
    def test_ohne_sparte_bleibt_alles(self):
        namen = _programme("")
        assert _film_only() & set(namen), (namen, _film_only())
        assert "Games-Förderung des Bundes (BMFTR)" in namen

    def test_tonstudio_bekommt_keine_kinofilmfoerderung(self):
        namen = _programme("musik_audio")
        assert not (_film_only() & set(namen)), namen
        assert "Games-Förderung des Bundes (BMFTR)" not in namen
        # NRW nennt Audio/Podcast ausdruecklich — bleibt fuer den Tonstudio-Kunden
        assert "Film- und Medienstiftung NRW" in namen

    def test_games_studio_behaelt_games_und_verliert_kinofilm(self):
        namen = _programme("games", bundesland="by")
        assert "Games-Förderung des Bundes (BMFTR)" in namen
        assert "FFF Bayern – Film-, Games- und XR-Förderung" in namen
        assert not (_film_only() & set(namen)), namen

    def test_verlag_bekommt_nur_passende_exklusive_programme(self):
        """Seit dem Faktencheck 05.09.2026 gibt es ein Verlags-Programm
        (Deutscher Verlagspreis). Exklusive Programme ohne Verlags-Sparte
        (Filmförderung) bleiben draussen."""
        namen = _programme("verlag_publishing")
        fremd = {p["title"] for p in FUND if p.get("sparten") and "verlag_publishing" not in p["sparten"]}
        assert not (set(namen) & fremd), set(namen) & fremd
        assert namen, "generische Programme muessen bleiben"

    def test_generische_programme_ungeruehrt(self):
        mit = set(_programme("verlag_publishing"))
        ohne = set(_programme(""))
        generisch = {p["title"] for p in FUND if not p.get("sparten")}
        assert (mit & generisch) == (ohne & generisch)

    def test_treffer_hebt_score_und_fehltreffer_filtert(self):
        """Synthetisches Programm, damit der Score nicht schon am Deckel 1.0 liegt
        (games_bund steht dort bereits ohne Sparte)."""
        from services.funding_recommender import calculate_relevance_score
        prog = {"id": "x", "name": "x", "country_code": "DE", "regions": ["DE"],
                "size_match": ["team"], "branches": ["medien"], "branch_exclusive": True,
                "sparten": ["games"], "ki_relevance": "low"}
        args = ("medien", "", "team", 2, "minimal", 0.0)
        neutral = calculate_relevance_score(prog, *args)
        assert 0 < neutral < 0.8, neutral
        assert calculate_relevance_score(prog, *args, sparte="games") == pytest.approx(neutral * 1.2)
        assert calculate_relevance_score(prog, *args, sparte="verlag_publishing") == -1.0

    def test_echtes_programm_faellt_bei_fremder_sparte(self):
        from services.funding_recommender import calculate_relevance_score, load_funding_programs
        prog = next(p for p in load_funding_programs() if p["id"] == "games_bund")
        args = ("medien", "by", "team", 2, "minimal", 0.0)
        assert calculate_relevance_score(prog, *args, sparte="games") > 0
        assert calculate_relevance_score(prog, *args, sparte="verlag_publishing") == -1.0

    def test_nicht_exklusives_programm_wird_nur_gedaempft(self):
        from services.funding_recommender import calculate_relevance_score
        prog = {"id": "x", "name": "x", "country_code": "DE", "regions": ["DE"],
                "size_match": ["team"], "branches": ["all"], "sparten": ["games"],
                "ki_relevance": "medium"}
        args = ("medien", "by", "team", 2, "minimal", 0.0)
        neutral = calculate_relevance_score(prog, *args)
        assert calculate_relevance_score(prog, *args, sparte="verlag_publishing") == pytest.approx(neutral * 0.8)


class TestFallstudien:
    @pytest.mark.parametrize("lang", ["de", "en"])
    def test_jede_sparte_hat_einen_eigenen_fall(self, lang):
        from services.sofort_start_generator import _pick_medien_fallstudie
        titel = {s: _pick_medien_fallstudie(s, "team", lang=lang)["titel"] for s in SPARTEN}
        # produktion und post_vfx teilen sich den Doku-Fall — alle anderen sind eigen
        assert titel["produktion"] == titel["post_vfx"]
        eigen = {k: v for k, v in titel.items() if k != "post_vfx"}
        assert len(set(eigen.values())) == len(eigen), eigen

    def test_verlag_tonstudio_content_nicht_mehr_beim_werbefilm(self):
        from services.sofort_start_generator import _pick_medien_fallstudie
        werbefilm = _pick_medien_fallstudie("agentur_design", "team")["titel"]
        for s in ("verlag_publishing", "musik_audio", "content_creation"):
            assert _pick_medien_fallstudie(s, "team")["titel"] != werbefilm, s

    def test_label_und_slug_liefern_denselben_fall(self):
        from services.sofort_start_generator import _pick_medien_fallstudie
        assert (_pick_medien_fallstudie("Film-/TV-Produktion", "team")["titel"]
                == _pick_medien_fallstudie("produktion", "team")["titel"])

    def test_solo_variante_vorhanden(self):
        from services.sofort_start_generator import _pick_medien_fallstudie
        for s in ("verlag_publishing", "musik_audio", "content_creation"):
            team = _pick_medien_fallstudie(s, "team")["unternehmen"]
            solo = _pick_medien_fallstudie(s, "solo")["unternehmen"]
            assert team != solo, s

    def test_de_und_en_pool_gleich_lang_und_gleiche_stichworte(self):
        from services.sofort_start_generator import FALLSTUDIEN_MEDIEN, FALLSTUDIEN_MEDIEN_EN
        assert [c["keywords"] for c in FALLSTUDIEN_MEDIEN] == [c["keywords"] for c in FALLSTUDIEN_MEDIEN_EN]
