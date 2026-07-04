# -*- coding: utf-8 -*-
"""
FIX-KIS-1188-ITEM3: 8.400 € Förder-Cap-Herleitung must be visible.

The cap originates from a code-level plausibility rule in
services.strategy_renderer (KIS-1110-P3):
    _foerder_capped = min(_foerder, int(_gesamt * 0.7))

Previously the PDF Executive Summary only showed the result, not the
70%-derivation, which made the figure look arbitrary. Per Wolf's
sprint-1026.3 decision the "Mit Förderung" box must now:
  1. State the 70 % derivation
  2. Reference Kapitel 7 (Fördermittel & Finanzierung)
  3. Name typical programmes: BAFA, KOMPASS, regionale Digitalprämien
"""
from __future__ import annotations

from services.strategy_renderer import render_strategy_html  # smoke import
from services import strategy_renderer
import inspect


def _decoded_source() -> str:
    """Source of strategy_renderer with `\\uXXXX` escape sequences resolved.

    inspect.getsource returns the raw file bytes — the string literals in
    the file use `\\u00a0`, `\\u20ac`, etc. We decode those so the test
    assertions can use natural German text rather than escape-soup.
    """
    raw = inspect.getsource(strategy_renderer)
    return raw.encode("ascii", "backslashreplace").decode("unicode_escape")


def test_cap_box_explains_70_percent_derivation():
    src = _decoded_source()
    # NBSP between 70 and %
    assert "bis zu 70 %" in src or "bis zu 70 %" in src or "bis zu 70%" in src


def test_cap_box_references_kapitel_7():
    src = _decoded_source()
    assert "Kapitel 7" in src or "Kapitel 7" in src
    assert "Fördermittel" in src


def test_cap_box_mentions_concrete_programmes():
    # KIS-1237: KOMPASS entfernt — richtet sich an Solo-Selbstständige und
    # stand im KMU-Lauf 1119 nie in Kapitel 7; die Exec Summary verwies
    # damit auf ein unbelegtes Programm. Jetzt segmentneutral
    # (Bundes- plus Landesförderung).
    src = _decoded_source()
    assert "BAFA" in src
    assert "KOMPASS" not in src
    assert "Digitalprämien" in src
    assert "Bundes- mit einer" in src


def test_cap_box_marker_present():
    """Code marker so future audits can locate the Wolf-decision'd block."""
    src = inspect.getsource(strategy_renderer)
    assert "FIX-KIS-1188-ITEM3" in src


def test_cap_logic_uses_70_percent_of_gesamt():
    """The numeric cap rule itself must stay at 70% of gesamt — the box
    text would lie about the derivation otherwise."""
    src = inspect.getsource(strategy_renderer)
    # services/strategy_renderer.py:321 (KIS-1110-P3)
    assert "min(_foerder, int(_gesamt * 0.7))" in src
