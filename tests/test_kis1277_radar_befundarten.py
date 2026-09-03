# -*- coding: utf-8 -*-
"""KIS-1277: Der Tool-Radar trennt "weg" von "kam nicht durch".

Der Lauf vom 03.09.2026 (Issue #1168) meldete 12 tote URLs. Vier davon
waren Adobe-Seiten mit ReadTimeout — Adobe weist den Prüfer ab, die
Seiten laufen. Ein Timeout belegt nichts, ein HTTP 404 belegt, dass die
Adresse weg ist. In einem Topf erzeugt das Befunde, die niemand
abarbeiten kann: Wolf öffnet die Seite im Browser, sie lädt, und beim
nächsten Lauf steht der Befund wieder da.

Zweiter Punkt aus demselben Lauf: Die zwölf Tavily-Suchen gingen an die
ersten zwölf Tools der Datei. Genau die Tools mit toter Trust-URL
(Topaz, iconik, Aleph Alpha) standen weiter hinten und bekamen keine.
Dabei ist eine tote URL der einzige Befund, den ein Treffer direkt
beantwortet — er nennt die neue Adresse.
"""
from __future__ import annotations

from datetime import date

import pytest

from scripts.tools_radar import check_url, collect_candidates, render_report


class _Antwort:
    def __init__(self, code: int) -> None:
        self.status_code = code


class TestBefundart:

    def test_http_404_ist_dead_url(self, monkeypatch):
        import requests
        monkeypatch.setattr(requests, "get", lambda *a, **kw: _Antwort(404))
        assert check_url("https://x.de/weg")["art"] == "dead_url"

    def test_timeout_ist_unpruefbar(self, monkeypatch):
        import requests
        def _wirft(*a, **kw):
            raise requests.exceptions.ReadTimeout("zu langsam")
        monkeypatch.setattr(requests, "get", _wirft)
        befund = check_url("https://www.adobe.com/de/privacy.html")
        assert befund["art"] == "unpruefbar"
        assert befund["detail"] == "ReadTimeout"

    def test_verbindungsabbruch_ist_unpruefbar(self, monkeypatch):
        import requests
        def _wirft(*a, **kw):
            raise requests.exceptions.ConnectionError("weg")
        monkeypatch.setattr(requests, "get", _wirft)
        assert check_url("https://x.de")["art"] == "unpruefbar"

    @pytest.mark.parametrize("code", [200, 301, 403, 405, 429])
    def test_erreichbar_ergibt_keinen_befund(self, monkeypatch, code):
        """403/405/429 ist Bot-Schutz, kein Defekt."""
        import requests
        monkeypatch.setattr(requests, "get", lambda *a, **kw: _Antwort(code))
        assert check_url("https://x.de") is None

    def test_leere_url_bleibt_dead_url(self):
        assert check_url("")["art"] == "dead_url"


class TestBerichtErklaertDenUnterschied:

    def test_hinweis_erscheint_nur_bei_unpruefbar(self):
        mit = render_report([{"type": "unpruefbar", "tool": "Adobe",
                              "detail": "url: x: ReadTimeout"}], date(2026, 9, 3))
        ohne = render_report([{"type": "stale", "tool": "X", "detail": "y"}],
                             date(2026, 9, 3))
        assert "kam nicht durch" in mit
        assert "kam nicht durch" not in ohne

    def test_tote_urls_stehen_oben(self):
        bericht = render_report([
            {"type": "stale", "tool": "A", "detail": "-"},
            {"type": "unpruefbar", "tool": "B", "detail": "-"},
            {"type": "dead_url", "tool": "C", "detail": "-"},
        ], date(2026, 9, 3))
        # Die Trennzeile beginnt mit "|-", faellt hier also schon raus;
        # uebrig bleiben Kopfzeile und Daten.
        zeilen = [z for z in bericht.splitlines() if z.startswith("| ")]
        arten = [z.split("|")[1].strip() for z in zeilen[1:]]
        assert arten == ["dead_url", "unpruefbar", "stale"]


class TestSuchenGehenZuDenTotenUrls:

    def _tools(self):
        return [{"name": f"T{i}", "url": f"https://t{i}.de"} for i in range(15)]

    def test_dead_url_tool_bekommt_eine_suche_trotz_hinterer_position(self):
        """T14 steht am Ende der Datei und wuerde ohne die Sortierung aus
        dem Limit von 12 herausfallen."""
        findings = [{"type": "stale", "tool": f"T{i}", "detail": "-"}
                    for i in range(14)]
        findings.append({"type": "dead_url", "tool": "T14", "detail": "-"})
        gesucht = []

        def _fake(name, year, api_key, *, domain="", **kw):
            gesucht.append(name)
            return [{"title": "x", "url": f"https://{domain}/p"}]

        collect_candidates(self._tools(), findings, "key", 2026, search=_fake)
        assert gesucht[0] == "T14"
        assert len(gesucht) == 12

    def test_reihenfolge_innerhalb_einer_gruppe_bleibt(self):
        findings = [{"type": "stale", "tool": "T3", "detail": "-"},
                    {"type": "stale", "tool": "T1", "detail": "-"}]
        gesucht = []
        collect_candidates(self._tools(), findings, "key", 2026,
                           search=lambda n, y, k, **kw: gesucht.append(n) or [])
        assert gesucht == ["T3", "T1"]


class TestKorrigierteTrustUrls:
    """Die zwei Adressen, die der Radar-Lauf vom 03.09.2026 selbst
    geliefert hat — beide auf der Herstellerdomain, beide als Ersatz fuer
    eine 404/401-Seite."""

    def _tool(self, name: str):
        from scripts.tools_radar import load_tools
        return next(t for t in load_tools() if t["name"] == name)

    def test_tally_zeigt_auf_die_privacy_policy(self):
        assert self._tool("Tally.so")["trust_url"] == "https://tally.so/help/privacy-policy"

    def test_notion_zeigt_auf_die_hilfeseite(self):
        """https://www.notion.so/privacy antwortete mit HTTP 401."""
        assert self._tool("Notion")["trust_url"] == "https://www.notion.so/help/privacy"

    def test_beide_bleiben_auf_der_herstellerdomain(self):
        from scripts.tools_radar import hersteller_domain
        for name in ("Tally.so", "Notion"):
            tool = self._tool(name)
            assert hersteller_domain(tool["trust_url"]) == hersteller_domain(tool["url"])
