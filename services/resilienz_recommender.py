# -*- coding: utf-8 -*-
"""Resilienz V1: Empfehlungs-Bibliothek — deterministisch, SVV-Prinzip.

Pro schwachem Block ein sofort machbarer Quick Win plus eine Ausbaustufe.
Texte kommen aus data/resilienz/katalog_<lang>.json (Modul-Dokument),
dieses Modul waehlt nur aus.
"""

from __future__ import annotations

from typing import Any, Dict, List

from services.resilienz_score import load_katalog

# Ein Block gilt als schwach, wenn sein Stufen-Mittel unter 3 liegt
# (analog zur Block-Ampel: rot oder gelb).
_SCHWACH_SCHWELLE = 3.0


def build_empfehlungen(block_means: Dict[str, float], lang: str = "de") -> List[Dict[str, Any]]:
    """Empfehlungen fuer alle schwachen Bloecke, schwaechster zuerst.

    Sind alle Bloecke stark (>= 3.0), kommt trotzdem der schwaechste
    Block als einzelne Empfehlung zurueck — ein Report ohne naechsten
    Schritt ist keiner.
    """
    katalog = load_katalog(lang)
    bibliothek = katalog["empfehlungen"]
    titel = {b["id"]: b["titel"] for b in katalog["blocks"]}

    schwach = sorted(
        (bid for bid, mean in block_means.items() if mean < _SCHWACH_SCHWELLE),
        key=lambda bid: block_means[bid],
    )
    if not schwach:
        schwach = [min(block_means, key=lambda bid: block_means[bid])]

    return [
        {
            "block": bid,
            "titel": titel[bid],
            "mean": block_means[bid],
            "quick_win": bibliothek[bid]["quick_win"],
            "ausbau": bibliothek[bid]["ausbau"],
        }
        for bid in schwach
    ]
