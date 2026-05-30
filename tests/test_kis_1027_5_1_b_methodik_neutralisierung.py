# -*- coding: utf-8 -*-
"""FIX-KIS-1027.5.1-B: R1 S.10 Methodik-Hinweis neutralisieren.

KIS-1200-Verdikt: Der 5-A-Methodik-Hinweis behauptete falsche Konsistenz:
"Der KI-Strategiebericht (sofern beauftragt) nutzt die Gesamt-Sicht;
daher erscheinen die beiden ROI-Zahlen dort konsistent zur Gesamt-Sicht hier."

Tatsaechlich:
- R1 CAPEX-Sicht:         8% ROI (Basis 12.000 EUR CAPEX)
- R1 Gesamt-Sicht:         7% ROI (Basis 13.440 EUR = CAPEX + OPEX 1.440 EUR)
- Strategy realistisch:   20% ROI (Basis 12.000 EUR Gesamt-TCO, OPEX 300 EUR/Mon)
- Strategy mit Foerderung: 300% ROI (Basis 3.600 EUR Netto)

Strategy nutzt eine eigene Kostenstruktur (inkl. Implementierung, Schulung,
Koordination), nicht "die Gesamt-Sicht von R1". Die behauptete Konsistenz
existiert nicht.

Fix: Text-Patch im Methodik-Hinweis-Block. KEINE Aenderung an ROI-Werten,
R1-Tabelle, Strategy-Werten.
"""
from __future__ import annotations

import os
import re

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
    "pdf_template_v7.html",
)


def _read_template() -> str:
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        return f.read()


def test_methodik_hinweis_does_not_claim_konsistenz():
    """Die falsche Konsistenz-Behauptung ist entfernt."""
    tpl = _read_template()
    assert "konsistent zur Gesamt-Sicht hier" not in tpl, (
        "Alte falsche Konsistenz-Behauptung ist noch im Template."
    )


def test_methodik_hinweis_uses_neutral_tco_wording():
    """Neuer Text betont eigene TCO-Methodik der Strategy mit anderer "
    "Kostenstruktur und 'methodisch bedingt abweichend'."""
    tpl = _read_template()
    assert "12-Monats-TCO-Methodik" in tpl, (
        "Neuer TCO-Methodik-Begriff fehlt im Methodik-Hinweis."
    )
    assert "andere" in tpl.lower() and "Kostenstruktur" in tpl
    assert "methodisch bedingt" in tpl
    assert "abweichend, nicht widersprüchlich" in tpl


def test_methodik_hinweis_mentions_implementation_schulung_koordination():
    """Konkrete Kostenkomponenten der Strategy-Methodik werden genannt."""
    tpl = _read_template()
    # Klammer-Liste im neuen Text
    assert "Implementierung" in tpl
    assert "Schulung" in tpl
    assert "Koordination" in tpl


def test_roi_views_table_block_intact():
    """Der eingebettende roi-views-table-Block bleibt strukturell unveraendert."""
    tpl = _read_template()
    # Block-Marker aus 5-A muss noch da sein
    assert "roi-views-table" in tpl
    assert "ROI_12M_GESAMT_DISPLAY_DE" in tpl
    assert "CAPEX-Sicht" in tpl
    assert "Gesamt-Sicht" in tpl
    # Methodik-Hinweis steht im Block (heuristisch: zwischen den ROI-Sichten
    # und dem closing </div> des Blocks)
    block_match = re.search(
        r'<div class="roi-views-table".*?</div>',
        tpl,
        re.DOTALL,
    )
    assert block_match, "roi-views-table-Block nicht gefunden"
    block = block_match.group(0)
    assert "12-Monats-TCO-Methodik" in block
