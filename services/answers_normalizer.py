# -*- coding: utf-8 -*-
"""
services/answers_normalizer.py - FIXED VERSION
----------------------------------------------
Normalisiert Fragebogen-Antworten + UTF-8 Decoding Fix
"""
from __future__ import annotations
from typing import Dict
import html

# Kanonische Mappings (unverändert)
BRANCHE_MAP = {
    "beratung & dienstleistungen": "beratung",
    "beratung": "beratung",
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


def _fix_utf8_mojibake(text: str) -> str:
    """
    Fixt UTF-8 Mojibake (z.B. 'FragebÃ¶gen' → 'Fragebögen')
    
    Problem: JSON wurde als Latin-1 encodiert, dann als UTF-8 gelesen
    Lösung: Re-encode als Latin-1, decode als UTF-8
    """
    if not text or not isinstance(text, str):
        return text
    
    # Check ob Mojibake vorhanden (heuristic)
    if 'Ã' not in text and 'â' not in text:
        return text
    
    try:
        # Re-encode als Latin-1, dann decode als UTF-8
        fixed = text.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
        return fixed
    except Exception:
        # Fallback: HTML-Unescape (falls doppelt escaped)
        try:
            return html.unescape(text)
        except Exception:
            return text


def normalize_answers(answers: Dict) -> Dict:
    """
    Normalisiert Antworten + UTF-8 Fix
    
    Args:
        answers: Rohe Antworten aus Fragebogen
        
    Returns:
        Dict mit normalisierten + UTF-8-korrigierten Werten
    """
    out = dict(answers or {})
    
    # ✅ FIX 1: UTF-8 Mojibake für alle String-Werte beheben
    for key, value in out.items():
        if isinstance(value, str):
            out[key] = _fix_utf8_mojibake(value)
        elif isinstance(value, list):
            out[key] = [_fix_utf8_mojibake(v) if isinstance(v, str) else v for v in value]
    
    # Branche normalisieren
    b = str(out.get("branche", "")).strip().lower()
    if b in BRANCHE_MAP:
        out["branche"] = BRANCHE_MAP[b]
    
    # Unternehmensgröße normalisieren
    g = str(out.get("unternehmensgroesse", "")).strip().lower()
    if g in UNTERNEHMENSGROESSE_MAP:
        out["unternehmensgroesse"] = UNTERNEHMENSGROESSE_MAP[g]
    
    # Bundesland auf 2-Buchstaben klein
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
