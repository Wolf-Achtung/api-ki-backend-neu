# -*- coding: utf-8 -*-
"""
config/bafa.py — Canonical BAFA funding values (single source of truth).

BAFA "Förderung von Unternehmensberatungen für KMU"
Geltungsdauer: bis 31.12.2026
Max. förderfähige Beratungskosten: 3.500 €/Beratung
Quelle: https://www.bafa.de/DE/Wirtschaft/Beratung_Finanzierung/Unternehmensberatung/unternehmensberatung_node.html

FIX-A2 / FIX-A3: Deterministic, region-aware BAFA values.
LLM darf diese Beträge NICHT frei generieren.
"""
from __future__ import annotations

# Max förderfähige Beratungskosten pro Beratung
BAFA_MAX_BERATUNGSKOSTEN = 3500

# Neue Bundesländer (erhöhte Förderquote 80%)
# Ohne Berlin (Sonderstatus) und ohne Leipzig (gehört zu Sachsen, aber Sonderregel)
NEUE_BUNDESLAENDER = frozenset({
    "Brandenburg",
    "Mecklenburg-Vorpommern",
    "Sachsen",
    "Sachsen-Anhalt",
    "Thüringen",
})

# Code → Name mapping for lookup
_CODE_TO_NAME = {
    "bb": "Brandenburg",
    "mv": "Mecklenburg-Vorpommern",
    "sn": "Sachsen",
    "st": "Sachsen-Anhalt",
    "th": "Thüringen",
}

# Berlin hat KEINEN BAFA-Sonderstatus: Es fällt unter die Standard-Regel der
# alten Bundesländer (50% / max 1.750 €). Der frühere 60%-Sonderzweig war
# sachlich falsch und wurde entfernt (FIX-1027.6.1).

# Förderquoten
FOERDERQUOTE_NEUE_BL = 80   # %
FOERDERQUOTE_ALTE_BL = 50   # %

# Abgeleitete Maximalbeträge
BAFA_MAX_NEUE_BL = int(BAFA_MAX_BERATUNGSKOSTEN * FOERDERQUOTE_NEUE_BL / 100)   # 2.800 €
BAFA_MAX_ALTE_BL = int(BAFA_MAX_BERATUNGSKOSTEN * FOERDERQUOTE_ALTE_BL / 100)    # 1.750 €


def _normalize_bundesland(bundesland: str) -> str:
    """Normalize Bundesland code or name to canonical name."""
    bl = bundesland.strip()
    # Check code mapping first
    lower = bl.lower()
    if lower in _CODE_TO_NAME:
        return _CODE_TO_NAME[lower]
    # Check direct name match (case-insensitive)
    for name in NEUE_BUNDESLAENDER:
        if name.lower() == lower:
            return name
    return bl


def is_neue_bundeslaender(bundesland: str) -> bool:
    """Check if a Bundesland qualifies for the higher BAFA rate (80%)."""
    if not bundesland:
        return False
    return _normalize_bundesland(bundesland) in NEUE_BUNDESLAENDER


def get_bafa_foerderquote(bundesland: str) -> int:
    """Return the BAFA Förderquote (%) for a given Bundesland."""
    if is_neue_bundeslaender(bundesland):
        return FOERDERQUOTE_NEUE_BL
    return FOERDERQUOTE_ALTE_BL


def get_bafa_max_foerderung(bundesland: str) -> int:
    """Return the max BAFA funding amount (€) for a given Bundesland."""
    if is_neue_bundeslaender(bundesland):
        return BAFA_MAX_NEUE_BL
    return BAFA_MAX_ALTE_BL


def get_bafa_foerderung_display(bundesland: str) -> str:
    """Return display string like 'bis 2.800 € (80%)' for a Bundesland."""
    quote = get_bafa_foerderquote(bundesland)
    max_amount = get_bafa_max_foerderung(bundesland)
    return f"bis {max_amount:,.0f} € ({quote}%)".replace(",", ".")


def get_bafa_foerderung_max_display(bundesland: str) -> str:
    """Return just the max amount like '2.800 €'."""
    max_amount = get_bafa_max_foerderung(bundesland)
    return f"{max_amount:,.0f} €".replace(",", ".")
