# -*- coding: utf-8 -*-
"""KIS-1308/1309: Prüfung eines Testlauf-Profils (Format der Gold-Profile).

Absichtlich ohne FastAPI und ohne App-Settings — das Skript
``scripts/testlauf_profil.py`` läuft damit auf jedem Rechner mit Python 3,
auch ohne installierte Abhängigkeiten des Backends. Denselben Code nutzt
der Endpunkt ``POST /api/admin/testrun/profile`` (routes/admin_testrun.py).

Geprüft werden: Pflichtfelder aus dem Registry, Enum-Werte gegen
``ENUM_VALUES``, der Bundesland-Code, die Slider-Bereiche und — wenn die
Fragebogen-2-Route ladbar ist — die FB2-Regeln. Ohne App-Settings (lokal)
prüft der Endpunkt Fragebogen 2 selbst.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

FB2_FELDER = [
    "s1_budget", "s2_zeitrahmen", "s3_prioritaeten", "s4_engpass",
    "s5_software", "s6_foerderinteresse", "s7_entscheidung",
    "s8_erfahrung", "s9_ansatz", "s10_datenschutz",
    "wettbewerber_anzahl", "kundenbindung_typ", "datenreife", "s5_vision",
]


def profil_pruefen(answers: Dict[str, Any], strategy_answers: Optional[Dict[str, Any]]) -> List[str]:
    """Liefert eine Liste von Fehlern; leer heißt einspielbar."""
    from services.chat_normalizer import ENUM_VALUES, FIELD_REGISTRY

    fehler: List[str] = []
    if not isinstance(answers, dict) or not answers:
        return ["answers fehlt oder ist leer"]
    for feld, spec in FIELD_REGISTRY.items():
        if spec.get("required") and answers.get(feld) in (None, "", []):
            fehler.append(f"Pflichtfeld fehlt: {feld}")
    for feld, erlaubt in ENUM_VALUES.items():
        wert = answers.get(feld)
        if wert in (None, "", []):
            continue
        werte = wert if isinstance(wert, list) else [wert]
        for w in werte:
            if str(w) not in erlaubt:
                fehler.append(f"Unbekannter Wert für {feld}: {w!r}")
    # Bundesland steht nicht in ENUM_VALUES (der Chat normalisiert Freitext);
    # ein Profil trägt den Code, nie den Namen.
    if str(answers.get("country", "DE")).upper() == "DE":
        from services.live_data_integration import BUNDESLAND_MAPPING
        bl = str(answers.get("bundesland", "") or "").lower()
        if bl and bl not in BUNDESLAND_MAPPING:
            fehler.append(f"Unbekannter Wert für bundesland: {bl!r} (Code wie 'by', 'be', 'nw')")
    for feld in ("digitalisierungsgrad", "risikofreude"):
        wert = answers.get(feld)
        if wert in (None, ""):
            continue
        spec = FIELD_REGISTRY.get(feld, {})
        try:
            n = int(wert)
        except (TypeError, ValueError):
            fehler.append(f"{feld} ist keine Zahl: {wert!r}")
            continue
        if not spec.get("min", 1) <= n <= spec.get("max", 10):
            fehler.append(f"{feld} außerhalb {spec.get('min')}–{spec.get('max')}: {n}")
    if strategy_answers:
        try:
            from routes.strategy import StrategyQuestionsCreate, _validate_questions
        except Exception as exc:  # pragma: no cover — lokal ohne App-Settings/FastAPI
            log.warning("[PROFIL] FB2-Prüfung übersprungen (routes.strategy nicht ladbar): %s",
                        str(exc).splitlines()[0][:120])
            return fehler
        try:
            q = StrategyQuestionsCreate(**{k: v for k, v in strategy_answers.items() if k in FB2_FELDER})
        except Exception as exc:  # pydantic
            fehler.append(f"FB2 unvollständig: {exc}")
        else:
            msg = _validate_questions(q)
            if msg:
                fehler.append(f"FB2: {msg}")
    return fehler
