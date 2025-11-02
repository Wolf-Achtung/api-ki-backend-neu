# -*- coding: utf-8 -*-
"""
services/answers_normalizer.py - Gold-Standard+
-----------------------------------------------
- Normalisiert Fragebogen-Antworten
- Behebt gängige UTF-8 Mojibake
- Liefert zusätzlich sprechende Label-Felder für Template/Reporting
"""
from __future__ import annotations
from typing import Dict, Any
import html

# Kanonische Mappings (Codes)
BRANCHE_MAP = {
    "beratung & dienstleistungen": "beratung",
    "beratung": "beratung",
    "marketing & werbung": "marketing",
    "it & software": "it_software",
    "it/software": "it_software",
    "finanzen & versicherungen": "finanzen",
    "handel & e-commerce": "handel",
    "e-commerce": "handel",
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

# Anzeige-Labels für Template
BRANCHEN_LABELS = {
    "beratung": "Beratung & Dienstleistungen",
    "marketing": "Marketing & Werbung",
    "it_software": "IT & Software",
    "finanzen": "Finanzen & Versicherungen",
    "handel": "Handel & E‑Commerce",
    "bildung": "Bildung",
    "verwaltung": "Verwaltung",
    "gesundheit": "Gesundheit & Pflege",
    "bau": "Bauwesen & Architektur",
    "medien": "Medien & Kreativwirtschaft",
    "industrie": "Industrie & Produktion",
    "logistik": "Transport & Logistik",
}
UNTERNEHMENSGROESSEN_LABELS = {
    "solo": "Solo",
    "team_2_10": "2–10 (Kleines Team)",
    "kmu_11_100": "11–100 (KMU)",
}
BUNDESLAENDER_LABELS = {
    "bw": "Baden‑Württemberg", "by": "Bayern", "be": "Berlin", "bb": "Brandenburg",
    "hb": "Bremen", "hh": "Hamburg", "he": "Hessen", "mv": "Mecklenburg‑Vorpommern",
    "ni": "Niedersachsen", "nw": "Nordrhein‑Westfalen", "rp": "Rheinland‑Pfalz",
    "sl": "Saarland", "sn": "Sachsen", "st": "Sachsen‑Anhalt",
    "sh": "Schleswig‑Holstein", "th": "Thüringen"
}

def _fix_utf8_mojibake(text: str) -> str:
    """
    Fixt UTF‑8 Mojibake (z. B. 'FragebÃ¶gen' → 'Fragebögen').
    Strategie: Latin‑1 → UTF‑8 re‑decode; Fallback: HTML‑Unescape.
    """
    if not text or not isinstance(text, str):
        return text
    if 'Ã' not in text and 'â' not in text:
        return text
    try:
        return text.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
    except Exception:
        try:
            return html.unescape(text)
        except Exception:
            return text

def _parse_int(s: Any, default: int) -> int:
    try:
        return int(str(s).strip())
    except Exception:
        return default

def normalize_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalisiert Antworten + UTF‑8 Fix + Label‑Felder.
    """
    out = dict(answers or {})

    # UTF‑8 Mojibake für alle Strings beheben
    for k, v in list(out.items()):
        if isinstance(v, str):
            out[k] = _fix_utf8_mojibake(v)
        elif isinstance(v, list):
            out[k] = [_fix_utf8_mojibake(x) if isinstance(x, str) else x for x in v]

    # Branche normalisieren
    b = str(out.get("branche", "")).strip().lower()
    out["branche"] = BRANCHE_MAP.get(b, out.get("branche", "")).lower() if b else out.get("branche", "")
    # Unternehmensgröße normalisieren
    g = str(out.get("unternehmensgroesse", "")).strip().lower()
    out["unternehmensgroesse"] = UNTERNEHMENSGROESSE_MAP.get(g, out.get("unternehmensgroesse", "")).lower() if g else out.get("unternehmensgroesse", "")
    # Bundesland 2‑Buchstaben
    bl = str(out.get("bundesland", "")).strip()
    out["bundesland"] = (bl[:2].lower() if len(bl) > 2 else bl.lower()) if bl else ""

    # Research‑Zeitfenster (UI: 7/30/60) → int
    for k in ("research_days", "tools_days", "funding_days"):
        if k in out:
            out[k] = _parse_int(out[k], 7)

    # Stundensatz (falls vorhanden) → int
    if "stundensatz_eur" in out:
        out["stundensatz_eur"] = _parse_int(out["stundensatz_eur"], 60)

    # Label‑Felder für das Template
    bcode = out.get("branche") or ""
    gcode = out.get("unternehmensgroesse") or ""
    blcode = out.get("bundesland") or ""
    out["BRANCHE_LABEL"] = BRANCHEN_LABELS.get(bcode, bcode or "—")
    out["UNTERNEHMENSGROESSE_LABEL"] = UNTERNEHMENSGROESSEN_LABELS.get(gcode, gcode or "—")
    out["BUNDESLAND_LABEL"] = BUNDESLAENDER_LABELS.get(blcode, blcode.upper() or "—")

    # Alias: ki_knowhow → ki_kompetenz (falls nötig)
    if "ki_kompetenz" in out and "ki_knowhow" not in out:
        out["ki_knowhow"] = out["ki_kompetenz"]

    return out
