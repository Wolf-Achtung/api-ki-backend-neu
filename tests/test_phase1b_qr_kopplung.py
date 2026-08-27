# -*- coding: utf-8 -*-
"""
Phase 1b — Antwort-Knoepfe duerfen nie stillschweigend fehlen.

Screenshot-Befund 2026-08 (Wolf, Produktions-Session): Sonnet stellte die
Digitalisierungs-Frage ("Wie digital arbeiten Sie heute — von der
Tool-Landschaft bis zum KI-Einsatz im Produktionsalltag?"), aber der Zug
erreichte den Nutzer ohne die Skalen-Knoepfe aus _QR_OPTIONS. Hergang:
next_fields hing auf einem Freitextfeld (Extraktion leer bzw.
Fragen-Sequenz versetzt), der damals harte Phase-1b-Allowlist-Filter
lieferte [] — und die strukturierte Frage kam nackt an.

Zwei Korrekturen stehen hier unter Regressionsschutz:

  1. Faehigkeitsfilter statt Allowlist: Jedes Feld in next_fields mit
     _QR_OPTIONS- oder FREETEXT_SUGGESTIONS-Eintrag behaelt seine
     Knoepfe (Nachfolger der KIS-1142-Allowlist).
  2. Frage→Feld-Anker: Kommen keine Knoepfe zustande, ordnet
     _infer_p1b_asked_qr_field die fertige Sonnet-Frage einem offenen
     QR-Feld zu — konservativ, nur bei eindeutigem Treffer.
"""

from __future__ import annotations

import inspect

from routes import chat as chat_module
from routes.chat import (
    PHASE_1B_OPEN_FIELDS,
    _build_quick_replies,
    _infer_p1b_asked_qr_field,
)

P1B_QR_KANDIDATEN = ["ki_kompetenz", "digitalisierungsgrad", "ki_ziele"]


class TestFrageFeldAnker:
    def test_screenshot_frage_trifft_digitalisierungsgrad(self):
        frage = (
            "Wie digital arbeiten Sie heute — von der Tool-Landschaft "
            "bis zum KI-Einsatz im Produktionsalltag?"
        )
        assert _infer_p1b_asked_qr_field(frage, P1B_QR_KANDIDATEN) == "digitalisierungsgrad"

    def test_englische_digitalfrage(self):
        frage = "How digital is your day-to-day work, from tools to AI use?"
        assert _infer_p1b_asked_qr_field(frage, P1B_QR_KANDIDATEN) == "digitalisierungsgrad"

    def test_kompetenzfrage(self):
        frage = "Wie viel Erfahrung mit KI haben Sie und Ihr Team bisher gesammelt?"
        assert _infer_p1b_asked_qr_field(frage, P1B_QR_KANDIDATEN) == "ki_kompetenz"

    def test_zielfrage(self):
        frage = "Welche Ziele verfolgen Sie mit dem KI-Einsatz vor allem?"
        assert _infer_p1b_asked_qr_field(frage, P1B_QR_KANDIDATEN) == "ki_ziele"

    def test_mehrdeutige_frage_liefert_nichts(self):
        # "digital" UND "Ziel" — zwei Kandidaten matchen, Anker verweigert.
        frage = "Wie digital sind Ihre Ziele fuer die naechsten Jahre?"
        assert _infer_p1b_asked_qr_field(frage, P1B_QR_KANDIDATEN) is None

    def test_ohne_signal_liefert_nichts(self):
        frage = "Womit verdient Ihr Unternehmen sein Geld?"
        assert _infer_p1b_asked_qr_field(frage, P1B_QR_KANDIDATEN) is None

    def test_leere_eingaben(self):
        assert _infer_p1b_asked_qr_field("", P1B_QR_KANDIDATEN) is None
        assert _infer_p1b_asked_qr_field("Wie digital arbeiten Sie?", []) is None

    def test_bereits_erhobenes_feld_ist_kein_kandidat(self):
        # Der Aufrufer filtert collected-Felder aus der Kandidatenliste —
        # der Anker darf dann nicht mehr auf sie zeigen.
        frage = "Wie digital arbeiten Sie heute?"
        kandidaten = [f for f in P1B_QR_KANDIDATEN if f != "digitalisierungsgrad"]
        assert _infer_p1b_asked_qr_field(frage, kandidaten) is None


class TestFaehigkeitsfilterQuelle:
    """Source-Guard: Der Phase-1b-Zweig nutzt den Faehigkeitsfilter
    und den Anker — nicht wieder eine harte Feld-Allowlist."""

    def test_zweig_nutzt_faehigkeitsfilter(self):
        src = " ".join(inspect.getsource(chat_module).split())
        assert (
            "_p1b_qr_fields = [f for f in next_fields "
            "if f in _QR_OPTIONS or f in FREETEXT_SUGGESTIONS]"
        ) in src

    def test_zweig_nutzt_anker_als_fallback(self):
        src = " ".join(inspect.getsource(chat_module).split())
        assert "_infer_p1b_asked_qr_field(full_response, _p1b_offene_qr)" in src


class TestKnoepfeFuerAlleStrukturiertenP1bFelder:
    """Funktionaler Sentinel: Jedes strukturierte Phase-1b-Feld baut
    Knoepfe; nur hauptleistung bleibt bewusst frei."""

    def test_alle_qr_felder_liefern_optionen(self):
        for feld in ("ki_kompetenz", "digitalisierungsgrad", "ki_ziele"):
            replies = _build_quick_replies([feld], "r1", {})
            assert replies and replies[0].options, feld

    def test_hauptleistung_bleibt_frei(self):
        assert _build_quick_replies(["hauptleistung"], "r1", {}) == []

    def test_feldliste_unveraendert(self):
        # Aendert sich die Phase-1b-Feldliste, muss dieser Test bewusst
        # angefasst werden — er verankert die Knopf-Erwartung pro Feld.
        assert PHASE_1B_OPEN_FIELDS == [
            "hauptleistung", "ki_kompetenz", "digitalisierungsgrad", "ki_ziele",
        ]
