# -*- coding: utf-8 -*-
"""
services/answers_normalizer.py
------------------------------
Normalisiert Fragebogen-Antworten auf kanonische Werte, damit
Downstream-Logik (Scoring, Playbooks, KPIs) stabil arbeitet.

Public:
    normalize_answers(answers: dict) -> dict
"""
from __future__ import annotations
from typing import Dict

# Kanonische Mappings
BRANCHE_MAP = {
    # UI-Labels → Token
    "beratung & dienstleistungen": "beratung",
    "marketing & werbung": "marketing",
    "it & software": "it_software",
    "finanzen & versicherungen": "finanzen",
    "handel & e-commerce": "handel",
    "bildung": "bildung",
    "verwaltung": "verwaltung",
    "gesundheit & pflege": "gesundheit",
    "bauwesen & architektur": "bau",
    "medien & kreativwirtschaft": "medien",
    "industrie & produktion": "industrie",
    "transport & logistik": "logistik",
}
UNTERNEHMENSGROESSE_MAP = {
    "1 (solo-selbstständig/freiberuflich)": "solo",
    "solo": "solo",
    "2–10 (kleines team)": "team_2_10",
    "2-10": "team_2_10",
    "11–100 (kmu)": "kmu_11_100",
    "11-100": "kmu_11_100",
}

def normalize_answers(answers: Dict) -> Dict:
    out = dict(answers or {})
    # Branche
    b = str(out.get("branche", "")).strip().lower()
    if b in BRANCHE_MAP:
        out["branche"] = BRANCHE_MAP[b]
    # Unternehmensgröße
    g = str(out.get("unternehmensgroesse", "")).strip().lower()
    if g in UNTERNEHMENSGROESSE_MAP:
        out["unternehmensgroesse"] = UNTERNEHMENSGROESSE_MAP[g]
    # Bundesland auf 2-Buchstaben klein (falls UI volle Namen liefert)
    bl = str(out.get("bundesland", "")).strip()
    if len(bl) > 2:
        out["bundesland"] = bl[:2].lower()
    else:
        out["bundesland"] = bl.lower()
    # Research-Zeitfenster (UI: 7/30/60) → int
    for k in ("research_days", "tools_days", "funding_days"):
        if k in out:
            try:
                out[k] = int(str(out[k]).strip())
            except Exception:
                pass
    return out
