# -*- coding: utf-8 -*-
"""KIS-1274: Die ENV-Pruefung haelt ihren vier blinden Flecken stand.

Am 03.09.2026 stand eine Loeschliste mit 37 Variablen im Repo. In
Railway existierte davon genau eine. Die Liste war gegen den Code
geprueft — aber mit einem Verfahren, das viermal danebengriff:

  1. Nur nach ``os.getenv("NAME")`` gesucht. Namen, die ueber eine
     Konstante weitergereicht werden, galten als ungenutzt.
  2. Zusammengesetzte Namen (``f"OPENAI_MAX_TOKENS_{sektion}"``) stehen
     nirgends woertlich im Code.
  3. Teilzeichenketten: ``RATE_LIMIT_PER_MINUTE`` traf in
     ``REPORT_RATE_LIMIT_PER_MINUTE`` — der Code liest aber nur den
     langen Namen. Das drehte die Bewertung ins Gegenteil.
  4. Helfer statt ``os.getenv``: ``_bool_env("X")``, ``get_bool("X")``,
     ``_truthy("X")``.

Jeder dieser Faelle bekommt hier einen Test. Wer das Verfahren aendert
und einen davon wieder aufreisst, sieht es sofort.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.env_unused import lies_namen, pruefe, wortgrenze


class TestWortgrenze:
    """Blinder Fleck 3 — der teuerste, weil er die Antwort umdreht."""

    def test_langer_name_ist_kein_treffer_fuer_den_kurzen(self):
        muster = wortgrenze("RATE_LIMIT_PER_MINUTE")
        assert not muster.search('os.getenv("REPORT_RATE_LIMIT_PER_MINUTE")')

    def test_exakter_name_trifft(self):
        muster = wortgrenze("RATE_LIMIT_PER_MINUTE")
        assert muster.search('os.getenv("RATE_LIMIT_PER_MINUTE", "5")')

    def test_anhang_ist_kein_treffer(self):
        assert not wortgrenze("TAVILY_KEY").search("TAVILY_KEY_ALT = 1")

    def test_unterstrich_zaehlt_als_wortzeichen(self):
        r"""``\b`` allein trennt hier nicht — deshalb die eigene Klasse."""
        assert not wortgrenze("MODE").search("AI_ACT_MODE")


class TestKonstantenUndHelfer:
    """Blinde Flecken 1 und 4 — beide loest die Suche nach dem nackten
    Namen statt nach einem festen Zugriffsmuster."""

    @pytest.mark.parametrize("zeile", [
        'MODE = os.getenv("AI_ACT_MODE", "off")',
        'ENABLED = _bool_env("AI_ACT_MODE")',
        'flag = get_bool("AI_ACT_MODE", False)',
        'if _truthy("AI_ACT_MODE"):',
        'os.environ.get("AI_ACT_MODE")',
    ])
    def test_jede_zugriffsform_wird_gefunden(self, zeile):
        assert wortgrenze("AI_ACT_MODE").search(zeile)


class TestGegenDenEchtenCode:
    """Die Stellen, an denen das Verfahren am 03.09. gemessen wurde."""

    def test_naming_falle_wird_als_loeschbar_erkannt(self):
        """Der Code liest REPORT_RATE_LIMIT_PER_MINUTE."""
        assert pruefe(["RATE_LIMIT_PER_MINUTE"])["RATE_LIMIT_PER_MINUTE"]["art"] \
            == "loeschbar"

    def test_der_gelesene_lange_name_bleibt(self):
        art = pruefe(["REPORT_RATE_LIMIT_PER_MINUTE"])["REPORT_RATE_LIMIT_PER_MINUTE"]["art"]
        assert art == "gelesen"

    def test_alias_ohne_env_zugriff_faellt_auf(self):
        """PROMPT_STABILITY_ENABLED ist ein Python-Alias auf
        STABILITY_SCORING_ENABLED. Der Name steht im Code, wird aber nie
        aus der Umgebung gelesen."""
        assert pruefe(["PROMPT_STABILITY_ENABLED"])["PROMPT_STABILITY_ENABLED"]["art"] \
            == "nur_bezeichner"

    def test_der_wirklich_gelesene_alias_ist_gelesen(self):
        assert pruefe(["STABILITY_SCORING_ENABLED"])["STABILITY_SCORING_ENABLED"]["art"] \
            == "gelesen"

    def test_worker_liest_nur_den_praefigierten_namen(self):
        ergebnis = pruefe(["POLL_INTERVAL", "WORKER_POLL_INTERVAL"])
        assert ergebnis["POLL_INTERVAL"]["art"] == "nur_bezeichner"
        assert ergebnis["WORKER_POLL_INTERVAL"]["art"] == "gelesen"

    def test_dynamischer_name_landet_nicht_bei_loeschbar(self):
        """Blinder Fleck 2: Diesen Namen setzt der Code zur Laufzeit
        zusammen, er steht nirgends woertlich."""
        art = pruefe(["OPENAI_MAX_TOKENS_QUICK_WINS"])["OPENAI_MAX_TOKENS_QUICK_WINS"]["art"]
        assert art in ("dynamisch", "gelesen")

    def test_woertlicher_treffer_schlaegt_das_praefix(self):
        """ANTHROPIC_MODEL_FALLBACK passt auf ein Praefix, wird aber
        woertlich gelesen. Wer zuerst das Praefix prueft, versteckt ihn."""
        assert pruefe(["ANTHROPIC_MODEL_FALLBACK"])["ANTHROPIC_MODEL_FALLBACK"]["art"] \
            == "gelesen"

    def test_nur_diagnosewerkzeug_ist_kein_laufzeit_leser(self):
        ergebnis = pruefe(["CORS_ALLOW_CREDENTIALS"])["CORS_ALLOW_CREDENTIALS"]
        assert ergebnis["art"] == "nur_nebenpfad"
        assert any("tools/" in t for t in ergebnis["treffer"])

    def test_erfundener_name_ist_loeschbar(self):
        assert pruefe(["GIBT_ES_NICHT_XYZ"])["GIBT_ES_NICHT_XYZ"]["art"] == "loeschbar"

    def test_nur_in_settings_eingelesen_faellt_auf(self):
        """Blinder Fleck 5: settings.py liest RESEARCH_LANG in
        research.lang ein. Niemand liest dieses Feld — die Variable ist
        wirkungslos, obwohl sie im Code vorkommt."""
        assert pruefe(["RESEARCH_LANG"])["RESEARCH_LANG"]["art"] == "nur_settings"

    def test_direkt_gelesener_name_bleibt_gelesen(self):
        """Gegenprobe: RESEARCH_PROVIDER liest gpt_analyze.py selbst."""
        assert pruefe(["RESEARCH_PROVIDER"])["RESEARCH_PROVIDER"]["art"] == "gelesen"

    def test_cache_falle_wird_erkannt(self):
        """Railway hat RESEARCH_CACHE_TTL, services/research_cache.py
        liest RESEARCH_CACHE_TTL_DAYS."""
        ergebnis = pruefe(["RESEARCH_CACHE_TTL", "RESEARCH_CACHE_TTL_DAYS"])
        assert ergebnis["RESEARCH_CACHE_TTL"]["art"] == "nur_settings"
        assert ergebnis["RESEARCH_CACHE_TTL_DAYS"]["art"] == "gelesen"


class TestEinlesen:
    """Railway zeigt die Namen in Spalten — der Einleser darf daran nicht
    scheitern."""

    def test_leerzeichen_und_zeilen_gemischt(self, tmp_path: Path):
        datei = tmp_path / "vars.txt"
        datei.write_text("A_EINS A_ZWEI\nA_DREI,A_VIER\n\n  A_FUENF  \n",
                         encoding="utf-8")
        assert lies_namen(datei) == ["A_EINS", "A_ZWEI", "A_DREI", "A_VIER", "A_FUENF"]

    def test_doppelte_verschwinden_reihenfolge_bleibt(self, tmp_path: Path):
        datei = tmp_path / "vars.txt"
        datei.write_text("B_EINS B_ZWEI B_EINS", encoding="utf-8")
        assert lies_namen(datei) == ["B_EINS", "B_ZWEI"]

    def test_kleinschreibung_wird_ignoriert(self, tmp_path: Path):
        datei = tmp_path / "vars.txt"
        datei.write_text("echter_name ECHTER_NAME 123 x", encoding="utf-8")
        assert lies_namen(datei) == ["ECHTER_NAME"]


class TestSkriptPruefstSichNichtSelbst:

    def test_eigene_beispielnamen_zaehlen_nicht(self):
        """Das Skript nennt RATE_LIMIT_PER_MINUTE in seiner eigenen
        Erklaerung. Ohne Selbstausschluss meldete es den Namen als
        benutzt — und widerlegte damit sein eigenes Ergebnis."""
        assert pruefe(["RATE_LIMIT_PER_MINUTE"])["RATE_LIMIT_PER_MINUTE"]["treffer"] == []
