# -*- coding: utf-8 -*-
"""KIS-1265: Restbefunde aus dem Gastronomie-Replay-Lauf KIS-1243 (briefing 1126).

Der Lauf bestätigte KIS-1264 (Judge direkt GRÜN ohne Heal, Budget-Box im
gerenderten PDF, S.5/S.31-Waisen weg) — mit zwei Restbefunden:

(1) S.3 trug WEITERHIN genau eine übergelaufene TOC-Zeile (97 Zeichen,
"STRATEGIE Nächste Schritte & Kontakt") — die 3px-Kompaktierung reichte
nicht. Stufe 2: Entry-Padding 2px + Level-Header enger (spart über
20 Einträge + 3 Header hinweg ~2,5 Zeilen — Puffer statt Punktlandung).

(2) Der R1-Haftungsausschluss sagte "Dieses PROJEKT dient ausschließlich
der Information" — gemeint ist das Dokument (KIS-1255-Klasse: das Wort
"Projekt" hat im Report nichts verloren, wo keins gemeint ist).
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


class TestTocCompactionStage2:

    def test_entry_padding_2px(self):
        src = _read("templates/pdf_template_v7.html")
        idx = src.find(".toc-entry {")
        assert "padding: 2px 0;" in src[idx:idx + 500]

    def test_level_header_compacted(self):
        src = _read("templates/pdf_template_v7.html")
        idx = src.find(".toc-level-header {")
        block = src[idx:idx + 400]
        assert "padding: 3px 0 2px;" in block
        assert "margin-top: 4px;" in block


class TestDisclaimerWording:

    def test_no_projekt_in_disclaimer(self):
        src = _read("templates/pdf_template_v7.html")
        assert "Dieses Projekt dient" not in src
        assert "Dieser Report dient ausschließlich der Information." in src

    def test_strategy_and_gamechanger_unchanged(self):
        # Beide waren korrekt formuliert — Regressionsanker.
        assert ("Dieser KI-Strategiebericht dient ausschließlich"
                in _read("templates/strategy_report.html"))
        assert ("Dieses Dokument dient ausschlie"
                in _read("templates/gamechanger_deep_dive_v1.html"))


class TestScoreLabelThreshold:
    """KIS-1266: 'exzellent' erst ab 85 — Entscheidung Wolf 2026-07-05.

    Lauf 1126: Qualitäts-Bonus hob 78 auf 80 und flippte das Label
    gut→exzellent, während der Branchen-Benchmark Grade C zeigte."""

    def test_80_is_gut_not_exzellent(self):
        from services.extra_sections import get_score_label
        assert get_score_label(80, "de") == "gut"
        assert get_score_label(80, "en") == "good"
        assert get_score_label(84, "de") == "gut"

    def test_85_is_exzellent(self):
        from services.extra_sections import get_score_label
        assert get_score_label(85, "de") == "exzellent"
        assert get_score_label(85, "en") == "excellent"

    def test_lower_bands_unchanged(self):
        from services.extra_sections import get_score_label
        assert get_score_label(65, "de") == "gut"
        assert get_score_label(50, "de") == "solide"
        assert get_score_label(35, "de") == "ausbaufähig"
        assert get_score_label(0, "de") == "kritisch"
