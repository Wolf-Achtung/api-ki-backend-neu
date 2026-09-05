# -*- coding: utf-8 -*-
"""KIS-1307 — Testlauf KIS1279 (05.09.2026, Build 1900, nach KIS-1306).

Alle sieben Punkte aus KIS-1306 sind im PDF behoben. Ein Restbefund: R1 S. 11
„… das lokale oder vertraglich abgesicherte Datenhaltung ." — das Verb fehlt.
Lokal nicht reproduzierbar (Healer und alle Enforcer geprüft); der Wächter
meldet das Muster, damit der nächste Lauf zeigt, ob es wiederkommt.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cr():
    spec = importlib.util.spec_from_file_location("compare_reports", ROOT / "scripts" / "compare_reports.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_wort_vor_punkt_fehlt(cr):
    text = ("Erfolgskriterium: Ein AVV-fähiges Verarbeitungsmodell liegt schriftlich vor, das lokale oder vertraglich\n"
            "abgesicherte Datenhaltung .\n")
    assert cr._wort_vor_punkt_fehlt(text) == "abgesicherte Datenhaltung ."


def test_kein_falschtreffer(cr):
    for t in ("Ein Satz endet normal.\n", "Frist: 31.12.2026 .\n", "Preis: 1.750 €.\n",
              "Stundensatz 95 €/h . Fertig.\n"):
        assert cr._wort_vor_punkt_fehlt(t) is None


def test_registriert(cr):
    assert "wort_vor_punkt_fehlt" in {p[0] for p in cr.PRUEFUNGEN}
