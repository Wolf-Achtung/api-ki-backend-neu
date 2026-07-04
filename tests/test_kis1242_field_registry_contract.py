# -*- coding: utf-8 -*-
"""KIS-1242: Registry-Kontrakt — ein Feld ist erst DANN fragbar, wenn ALLE
Register es kennen.

Drei Testlauf-Abbrüche am 04.07. hatten dieselbe Wurzel: Ein neues Feld
wurde in FIELD_REGISTRY eingetragen, aber in einem der Nebenregister
vergessen —
  1. _QR_OPTIONS fehlte  → Enum-Frage ohne Chips, Freitext-Glücksspiel
  2. ENUM_VALUES fehlte  → Chip-Klick als low confidence verworfen,
                            dieselbe Frage endlos wiederholt (7/8-Schleife)
  3. _QR_LABELS fehlte   → roher Feldname "projekte_pro_monat" in der UI

Dieser Kontrakt erzwingt Konsistenz für JEDES fragbare Feld. Dazu kommt
der Laufzeit-Fallback in routes/chat.py (KIS-1242: QR-Klick = Wahrheit),
der selbst bei einer künftigen Lücke die Endlos-Schleife verhindert.
"""
from __future__ import annotations

import pytest

from routes.chat import (
    BLOCK_FIELDS, _QR_LABELS, _QR_OPTIONS, _get_datenschutz_block_fields,
)
from services.chat_normalizer import (
    ENUM_VALUES, FIELD_REGISTRY, SECTIONS, _FIELD_LABELS,
)

# Felder mit eigenem Spezial-Normalizer (brauchen keinen ENUM_VALUES-Eintrag)
_SPECIAL_NORMALIZERS = {
    "branche", "unternehmensgroesse", "bundesland", "country", "selbststaendig",
}


def _askable_fields() -> set:
    """Alle Felder, die der R1-Chat tatsächlich stellen kann."""
    fields: set = set()
    for sec in SECTIONS:
        fields.update(sec["fields"])
    for block in BLOCK_FIELDS.values():
        fields.update(block)
    fields.update(_get_datenschutz_block_fields(""))
    fields.update(_get_datenschutz_block_fields("beratung"))
    return {f for f in fields if f in FIELD_REGISTRY}


@pytest.mark.parametrize("field", sorted(_askable_fields()))
def test_enum_fields_have_allowed_values(field):
    reg = FIELD_REGISTRY[field]
    if reg.get("type") not in ("enum", "multi"):
        pytest.skip("kein Enum-/Multi-Feld")
    if field in _SPECIAL_NORMALIZERS:
        pytest.skip("Spezial-Normalizer")
    assert field in ENUM_VALUES and ENUM_VALUES[field], (
        f"'{field}' ist als {reg['type']} fragbar, hat aber keinen "
        f"ENUM_VALUES-Eintrag — Chip-Klicks würden als low confidence "
        f"verworfen (Endlos-Schleife, siehe 3. Abbruch 04.07.)."
    )


@pytest.mark.parametrize("field", sorted(set(_QR_OPTIONS) & _askable_fields()))
def test_qr_option_values_are_normalizable(field):
    if field in _SPECIAL_NORMALIZERS:
        pytest.skip("Spezial-Normalizer")
    reg = FIELD_REGISTRY.get(field, {})
    if reg.get("type") not in ("enum", "multi"):
        pytest.skip("Freitext-Chips laufen über FREETEXT_SUGGESTIONS")
    offered = {o["value"] for o in _QR_OPTIONS[field]}
    allowed = set(ENUM_VALUES.get(field, []))
    missing = offered - allowed - {"keine_angabe"}
    assert not missing, (
        f"'{field}': Chips bieten Werte an, die der Normalizer nicht "
        f"akzeptiert: {sorted(missing)} — jeder Klick darauf würde "
        f"verworfen."
    )


@pytest.mark.parametrize("field", sorted(_askable_fields()))
def test_askable_fields_have_human_label(field):
    label = _QR_LABELS.get(field) or _FIELD_LABELS.get(field)
    assert label and "_" not in label, (
        f"'{field}' hat kein deutsches Label — die UI zeigt sonst den "
        f"rohen Feldnamen als Chip-Überschrift (Screenshot 04.07.)."
    )


def test_projekte_pro_monat_fully_registered():
    """Der konkrete Fall des 3. Abbruchs — als expliziter Regressionstest."""
    assert ENUM_VALUES["projekte_pro_monat"] == [
        "unter_2", "2_5", "6_10", "ueber_10", "keine_angabe",
    ]
    assert _QR_LABELS["projekte_pro_monat"] == "Projekte pro Monat"
    from services.chat_normalizer import normalize_field
    res = normalize_field("projekte_pro_monat", "unter_2", {}, report_type="r1")
    assert res.confidence == "high" and res.value == "unter_2"


def test_qr_click_verbatim_fallback_present():
    """Laufzeit-Netz: angebotener Chip-Wert wird IMMER persistiert."""
    src = open("routes/chat.py", encoding="utf-8").read()
    idx = src.find("KIS-1242: QR-Klick = Wahrheit")
    assert idx != -1
    block = src[idx:idx + 900]
    assert "_QR_OPTIONS.get(qr_field)" in block
    assert 'NormResult(req.quick_reply_value, "high", False)' in block
