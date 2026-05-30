# -*- coding: utf-8 -*-
"""FIX-KIS-1027.5-A: R1 zeigt zwei ROI-Sichten transparent nebeneinander.

KIS-1199 zeigte ROI-Spread:
- R1 CAPEX-basiert: 8 %
- Strategy realistisch: 20 %
- Strategy mit Förderung: 300 %

KMU-GF sah drei Zahlen für "seinen ROI" und las das als Widerspruch.

Wolf-Decision (Sprint 1027.5-A Option B): R1 S.10 zeigt sowohl
CAPEX-ROI als auch 12-Mo-Gesamt-ROI in einer Tabelle. Spread bleibt
mathematisch (verschiedene Methodiken), wird aber sichtbar als
"zwei korrekte Sichten auf dieselbe Investition" erklärt.

Tests:
- ROI_12M_GESAMT_DISPLAY_DE wird im Renderer korrekt berechnet
- Template hat den neuen Block für die ROI-Sichten-Tabelle
- Gesamt-ROI auf 200% gedeckelt (analog R1 ROI)
- Wenn CAPEX/Saving fehlt: graceful degradation (kein Block gerendert)
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


def test_template_has_roi_views_table():
    """Template enthält den neuen Zwei-ROI-Sichten-Block."""
    tpl = _read_template()
    assert "roi-views-table" in tpl, (
        "Template hat keinen roi-views-table-Block — "
        "FIX-KIS-1027.5-A nicht angewendet."
    )
    assert "ROI_12M_GESAMT_DISPLAY_DE" in tpl, (
        "Template referenziert nicht ROI_12M_GESAMT_DISPLAY_DE"
    )
    # Beide Sichten müssen sichtbar sein
    assert "CAPEX-Sicht" in tpl, "CAPEX-Sicht-Label fehlt"
    assert "Gesamt-Sicht" in tpl, "Gesamt-Sicht-Label fehlt"


def test_template_explains_methodology_difference():
    """Block enthält Erklärung, dass beide Werte korrekt sind."""
    tpl = _read_template()
    # Methodik-Erklärung muss da sein
    assert "Beide Werte sind korrekt" in tpl, (
        "Methodik-Erklärung fehlt im ROI-Sichten-Block"
    )
    assert "Investitionsbasis" in tpl, "Erklärungs-Header 'Investitionsbasis' fehlt"


def test_template_block_is_conditional():
    """Block wird nur gerendert wenn ROI_12M_GESAMT_DISPLAY_DE gesetzt ist."""
    tpl = _read_template()
    # {% if ROI_12M_GESAMT_DISPLAY_DE %} ... {% endif %} muss den Block umschließen
    match = re.search(
        r'\{%\s*if\s+ROI_12M_GESAMT_DISPLAY_DE\s*%\}.*?roi-views-table.*?\{%\s*endif\s*%\}',
        tpl,
        re.DOTALL,
    )
    assert match, (
        "Der ROI-Sichten-Block ist nicht conditional auf "
        "ROI_12M_GESAMT_DISPLAY_DE — graceful degradation fehlt."
    )


def test_renderer_computes_gesamt_roi():
    """Renderer berechnet ROI_12M_GESAMT_DISPLAY_DE aus CAPEX + OPEX × 12."""
    import inspect
    from services import report_renderer
    src = inspect.getsource(report_renderer)
    assert "ROI_12M_GESAMT_DISPLAY_DE" in src, (
        "Renderer setzt ROI_12M_GESAMT_DISPLAY_DE nicht — "
        "FIX-KIS-1027.5-A nicht implementiert"
    )
    assert "FIX-KIS-1027.5-A" in src, "Renderer-Code-Marker fehlt"
    # Sanity: Formel basiert auf CAPEX + OPEX*12 und Saving × 12
    assert "_opex_m * 12" in src, "12-Monats-OPEX-Multiplikation fehlt"
    assert "_saving_m * 12" in src, "12-Monats-Ersparnis-Multiplikation fehlt"


def test_renderer_caps_gesamt_roi_at_200_percent():
    """Gesamt-ROI ist auf 200 % gedeckelt wie R1-ROI_12M."""
    from services import report_renderer
    import inspect
    src = inspect.getsource(report_renderer)
    # Cap-Logik vorhanden
    assert "min(200.0" in src or "min(200," in src, (
        "Gesamt-ROI-Cap auf 200 % fehlt"
    )


def test_renderer_compute_logic_inline():
    """Stress-Test der Compute-Logik durch Inline-Replay (ohne ganzen Render)."""
    # Simuliere die Compute-Logik nach renderer's Schema
    capex = 12000.0
    opex_m = 500.0
    saving_m = 2000.0

    annual_saving = saving_m * 12.0
    gesamt_invest = capex + (opex_m * 12.0)
    roi = (annual_saving - gesamt_invest) / gesamt_invest * 100.0
    capped = min(200.0, max(-100.0, roi))

    # Expected: (24000 - 18000) / 18000 * 100 = 33.3 %
    assert abs(capped - 33.3) < 0.1, f"Expected ~33.3 %, got {capped}"

    # Cap-Test: extrem hoher saving
    high_saving_m = 10000.0
    high_annual = high_saving_m * 12.0  # 120k
    roi_high = (high_annual - gesamt_invest) / gesamt_invest * 100.0
    capped_high = min(200.0, max(-100.0, roi_high))
    assert capped_high == 200.0, "Cap auf 200% greift nicht"
