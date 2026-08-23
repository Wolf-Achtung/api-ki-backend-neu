# -*- coding: utf-8 -*-
"""Resilienz V1: deterministisches Scoring — kein LLM.

Fachliche Referenz: resilienz-check-modul.md / data/resilienz/katalog_de.json.
Drei Regeln, die es im restlichen Scoring des Projekts bewusst NICHT gibt:

1. Gewichteter Score: weighted_mean(block_means) * 25  -> 0..100
2. Min-Regel (Reaktionsluecke): min(B2, C1, C2, C3, C4) -> Band 1..4.
   Der langsamste Faktor bestimmt das System, nicht der Durchschnitt.
3. Deckelregel: Die Gesamtampel ist nie besser als der schwaechste Block
   (und nie besser als die Reaktionsluecken-Ampel).

Mehrsprachigkeit: Der Katalog ist pro Sprache eine Datei
(katalog_<lang>.json) mit identischen IDs/Gewichten; dieses Modul liest
Struktur und Regeln, nie Texte — es ist sprachneutral.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, List

_KATALOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "resilienz")

REAKTIONSLUECKE_FIELDS = ("B2", "C1", "C2", "C3", "C4")

# Ampel-Ordnung fuer die Deckelregel (schlechter = kleinerer Index)
_AMPEL_ORDER = ["rot", "gelb", "gruen"]


@lru_cache(maxsize=4)
def load_katalog(lang: str = "de") -> Dict[str, Any]:
    """Katalog fuer eine Sprache laden. Kein Fallback DE<->andere Sprachen:
    eine fehlende Sprachdatei ist ein Fehler, kein stilles Downgrade."""
    path = os.path.join(_KATALOG_DIR, f"katalog_{lang}.json")
    with open(path, encoding="utf-8") as fh:
        katalog: Dict[str, Any] = json.load(fh)
    return katalog


def all_question_ids(lang: str = "de") -> List[str]:
    return [q["id"] for b in load_katalog(lang)["blocks"] for q in b["questions"]]


def _block_ampel(mean: float) -> str:
    """Block-Ampel aus dem Stufen-Mittel (1..4).

    Technische Auslegung der Deckelregel (Modul-Dokument nennt nur
    'min(block_means) -> cap(gesamt)'): unter 2 = rot (ueberwiegend
    Stufe-1-Antworten), unter 3 = gelb, ab 3 = gruen.
    """
    if mean < 2.0:
        return "rot"
    if mean < 3.0:
        return "gelb"
    return "gruen"


def _worst_ampel(*ampeln: str) -> str:
    return min(ampeln, key=_AMPEL_ORDER.index)


def calculate_resilienz(answers: Dict[str, int], lang: str = "de") -> Dict[str, Any]:
    """Kernberechnung. `answers` = {frage_id: stufe 1..4}, vollstaendig.

    Liefert:
      score            0..100 (gerundet)
      block_means      {block_id: mean}
      block_ampeln     {block_id: rot|gelb|gruen}
      schwaechster_block  block_id mit dem niedrigsten Mittel
      reaktionsluecke  {min_stufe, label, ampel, aussage, treiber}
      ampel            Gesamtampel nach Deckelregel
      gedeckelt        True, wenn die Deckelregel die Ampel verschlechtert hat
    """
    katalog = load_katalog(lang)

    expected = set(all_question_ids(lang))
    got = set(answers.keys())
    missing = sorted(expected - got)
    if missing:
        raise ValueError(f"Antworten unvollstaendig, es fehlen: {', '.join(missing)}")
    for qid in expected:
        stufe = answers[qid]
        if not isinstance(stufe, int) or not 1 <= stufe <= 4:
            raise ValueError(f"Ungueltige Stufe fuer {qid}: {stufe!r} (erlaubt: 1..4)")

    block_means: Dict[str, float] = {}
    weighted_sum = 0.0
    weight_sum = 0.0
    for block in katalog["blocks"]:
        values = [answers[q["id"]] for q in block["questions"]]
        mean = sum(values) / len(values)
        block_means[block["id"]] = mean
        weighted_sum += mean * block["weight"]
        weight_sum += block["weight"]

    # Gewichteter Mittelwert der Blockmittel (1..4), normiert auf 0..100.
    score = round((weighted_sum / weight_sum) * 25)

    # Min-Regel: der langsamste Entscheidungs-/Alarmfaktor bestimmt das Band.
    min_stufe = min(answers[f] for f in REAKTIONSLUECKE_FIELDS)
    treiber = sorted(f for f in REAKTIONSLUECKE_FIELDS if answers[f] == min_stufe)
    band = next(b for b in katalog["reaktionsluecke_bands"] if b["min_stufe"] == min_stufe)

    # Deckelregel: Gesamtampel <= schwaechster Block, <= Reaktionsluecke.
    block_ampeln = {bid: _block_ampel(m) for bid, m in block_means.items()}
    schwaechster_block = min(block_means, key=lambda bid: block_means[bid])
    ampel = _worst_ampel(band["ampel"], *block_ampeln.values())
    gedeckelt = _AMPEL_ORDER.index(ampel) < _AMPEL_ORDER.index(_block_ampel(weighted_sum / weight_sum))

    return {
        "score": score,
        "block_means": block_means,
        "block_ampeln": block_ampeln,
        "schwaechster_block": schwaechster_block,
        "reaktionsluecke": {
            "min_stufe": min_stufe,
            "label": band["label"],
            "ampel": band["ampel"],
            "aussage": band["aussage"],
            "treiber": treiber,
        },
        "ampel": ampel,
        "gedeckelt": gedeckelt,
    }
