# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any
import html

BRANCHE_MAP = {
    "beratung & dienstleistungen": "beratung",
    "beratung": "beratung",
    "marketing & werbung": "marketing",
    "it & software": "it_software",
    "it/software": "it_software",
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

BUNDESLAENDER_LABELS = {
    "bw": "Baden‑Württemberg", "by": "Bayern", "be": "Berlin", "bb": "Brandenburg",
    "hb": "Bremen", "hh": "Hamburg", "he": "Hessen", "mv": "Mecklenburg‑Vorpommern",
    "ni": "Niedersachsen", "nw": "Nordrhein‑Westfalen", "rp": "Rheinland‑Pfalz",
    "sl": "Saarland", "sn": "Sachsen", "st": "Sachsen‑Anhalt",
    "sh": "Schleswig‑Holstein", "th": "Thüringen"
}
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

def _fix_utf8_mojibake(text: str) -> str:
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

def _parse_int(s, default):
    try:
        return int(str(s).strip())
    except Exception:
        return default

def normalize_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(answers or {})
    for k, v in list(out.items()):
        if isinstance(v, str):
            out[k] = _fix_utf8_mojibake(v)
        elif isinstance(v, list):
            out[k] = [_fix_utf8_mojibake(x) if isinstance(x, str) else x for x in v]

    b = str(out.get("branche", "")).strip().lower()
    out["branche"] = BRANCHE_MAP.get(b, out.get("branche", "")) or out.get("branche", "")
    g = str(out.get("unternehmensgroesse", "")).strip().lower()
    out["unternehmensgroesse"] = UNTERNEHMENSGROESSE_MAP.get(g, out.get("unternehmensgroesse", "")) or out.get("unternehmensgroesse", "")
    bl = str(out.get("bundesland", "")).strip()
    out["bundesland"] = (bl[:2].lower() if len(bl) > 2 else bl.lower()) if bl else ""

    for k in ("research_days", "tools_days", "funding_days"):
        if k in out:
            out[k] = _parse_int(out[k], 7)
    if "stundensatz_eur" in out:
        out["stundensatz_eur"] = _parse_int(out["stundensatz_eur"], 60)

    # Labels for template
    out["BRANCHE_LABEL"] = BRANCHEN_LABELS.get(out.get("branche",""), out.get("branche","") or "—")
    out["UNTERNEHMENSGROESSE_LABEL"] = UNTERNEHMENSGROESSEN_LABELS.get(out.get("unternehmensgroesse",""), out.get("unternehmensgroesse","") or "—")
    out["BUNDESLAND_LABEL"] = BUNDESLAENDER_LABELS.get(out.get("bundesland",""), out.get("bundesland","").upper() or "—")

    # Alias support
    if "ki_kompetenz" in out and "ki_knowhow" not in out:
        out["ki_knowhow"] = out["ki_kompetenz"]
    return out
