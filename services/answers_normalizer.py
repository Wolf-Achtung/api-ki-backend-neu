# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any
import os, html

# Canonical maps
BRANCHE_MAP = {
    "beratung & dienstleistungen":"beratung", "beratung":"beratung",
    "marketing & werbung":"marketing", "marketing":"marketing",
    "it & software":"it_software", "it/software":"it_software", "it":"it_software",
    "finanzen & versicherungen":"finanzen", "finanzen":"finanzen",
    "handel & e-commerce":"handel", "e-commerce":"handel", "handel":"handel",
    "bildung":"bildung", "verwaltung":"verwaltung", "gesundheit & pflege":"gesundheit", "gesundheit":"gesundheit",
    "bauwesen & architektur":"bau", "bau":"bau", "medien & kreativwirtschaft":"medien", "medien":"medien",
    "industrie & produktion":"industrie", "industrie":"industrie", "transport & logistik":"logistik", "logistik":"logistik",
}
UNTERNEHMENSGROESSE_MAP = {
    "1 (solo-selbstständig/freiberuflich)":"solo", "solo":"solo",
    "2–10 (kleines team)":"team_2_10","2-10":"team_2_10","team":"team_2_10",
    "11–100 (kmu)":"kmu_11_100","11-100":"kmu_11_100","kmu":"kmu_11_100",
}

# Display labels
BRANCHEN_LABELS = {
    "beratung":"Beratung & Dienstleistungen","marketing":"Marketing & Werbung","it_software":"IT & Software",
    "finanzen":"Finanzen & Versicherungen","handel":"Handel & E‑Commerce","bildung":"Bildung","verwaltung":"Verwaltung",
    "gesundheit":"Gesundheit & Pflege","bau":"Bauwesen & Architektur","medien":"Medien & Kreativwirtschaft",
    "industrie":"Industrie & Produktion","logistik":"Transport & Logistik",
}
UNTERNEHMENSGROESSEN_LABELS = {"solo":"Solo","team_2_10":"2–10 (Kleines Team)","kmu_11_100":"11–100 (KMU)"}
BUNDESLAENDER_LABELS = {
    "bw":"Baden‑Württemberg","by":"Bayern","be":"Berlin","bb":"Brandenburg","hb":"Bremen","hh":"Hamburg","he":"Hessen",
    "mv":"Mecklenburg‑Vorpommern","ni":"Niedersachsen","nw":"Nordrhein‑Westfalen","rp":"Rheinland‑Pfalz","sl":"Saarland",
    "sn":"Sachsen","st":"Sachsen‑Anhalt","sh":"Schleswig‑Holstein","th":"Thüringen"
}
UMSATZ_LABELS = {
    "unter_100k": "unter 100 T€",
    "100k_500k": "100 T€ – 500 T€",
    "500k_2m": "0,5 – 2 Mio. €",
    "2m_10m": "2 – 10 Mio. €",
    "ueber_10m": "> 10 Mio. €",
    "keine_angabe": "keine Angabe",
}

def _fix_utf8_mojibake(text: str) -> str:
    if not text or not isinstance(text, str): return text
    if 'Ã' not in text and 'â' not in text: return text
    try: return text.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
    except Exception:
        try: return html.unescape(text)
        except Exception: return text

def _parse_int(s, default): 
    try: return int(str(s).strip())
    except Exception: return default

# Branch-Benchmark (sensibel → kein exakter Kundensatz nötig)
DEFAULT_RATE = int(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60"))
BRANCH_RATE = {
    "beratung": 90, "marketing": 75, "it_software": 95, "finanzen": 100, "handel": 60,
    "bildung": 55, "verwaltung": 55, "gesundheit": 70, "bau": 65, "medien": 70, "industrie": 80, "logistik": 65
}
SIZE_MULT = {"solo": 0.9, "team_2_10": 1.0, "kmu_11_100": 1.1}

def _derive_rate(branche: str, groesse: str, band: str|None) -> int:
    if band:
        # Erwartet Codes wie "40_60", "60_90"
        try:
            lo, hi = band.replace(" ", "").split("_", 1)
            return int(round((int(lo) + int(hi)) / 2.0))
        except Exception:
            pass
    base = BRANCH_RATE.get(branche or "", DEFAULT_RATE)
    mult = SIZE_MULT.get(groesse or "", 1.0)
    return max(30, int(round(base * mult)))

def normalize_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(answers or {})
    # Mojibake fix
    for k,v in list(out.items()):
        if isinstance(v, str): out[k] = _fix_utf8_mojibake(v)
        elif isinstance(v, list): out[k] = [_fix_utf8_mojibake(x) if isinstance(x,str) else x for x in v]

    # Canonicalize
    b = str(out.get("branche","")).strip().lower()
    out["branche"] = BRANCHE_MAP.get(b, out.get("branche","")) or out.get("branche","")
    g = str(out.get("unternehmensgroesse","")).strip().lower()
    out["unternehmensgroesse"] = UNTERNEHMENSGROESSE_MAP.get(g, out.get("unternehmensgroesse","")) or out.get("unternehmensgroesse","")
    bl = str(out.get("bundesland","")).strip()
    out["bundesland"] = (bl[:2].lower() if len(bl)>2 else bl.lower()) if bl else ""

    # Numeric coercions
    for k in ("research_days","tools_days","funding_days"):
        if k in out: out[k] = _parse_int(out[k], 30)

    # Stundensatz – Benchmark
    band = out.get("stundensatz_band")  # optionales Feld (Bandbreite, nicht exakt)
    if not out.get("stundensatz_eur"):
        out["stundensatz_eur"] = _derive_rate(out.get("branche"), out.get("unternehmensgroesse"), band)

    # Labels
    out["BRANCHE_LABEL"] = BRANCHEN_LABELS.get(out.get("branche",""), out.get("branche","") or "—")
    out["UNTERNEHMENSGROESSE_LABEL"] = UNTERNEHMENSGROESSEN_LABELS.get(out.get("unternehmensgroesse",""), out.get("unternehmensgroesse","") or "—")
    out["BUNDESLAND_LABEL"] = BUNDESLAENDER_LABELS.get(out.get("bundesland",""), out.get("bundesland","").upper() or "—")
    rev = str(out.get("jahresumsatz","") or "").strip().lower()
    out["JAHRESUMSATZ_LABEL"] = UMSATZ_LABELS.get(rev, out.get("jahresumsatz","") or "—")

    # Alias: ki_knowhow
    if "ki_kompetenz" in out and "ki_knowhow" not in out:
        out["ki_knowhow"] = out["ki_kompetenz"]
    return out
