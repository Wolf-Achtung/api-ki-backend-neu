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
    "2–10 (kleines team)":"team","2-10":"team","team":"team",
    "11–100 (kmu)":"kmu","11-100":"kmu","kmu":"kmu",
}

# Display labels
BRANCHEN_LABELS = {
    "beratung":"Beratung & Dienstleistungen","marketing":"Marketing & Werbung","it_software":"IT & Software",
    "finanzen":"Finanzen & Versicherungen","handel":"Handel & E‑Commerce","bildung":"Bildung","verwaltung":"Verwaltung",
    "gesundheit":"Gesundheit & Pflege","bau":"Bauwesen & Architektur","medien":"Medien & Kreativwirtschaft",
    "industrie":"Industrie & Produktion","logistik":"Transport & Logistik",
}
UNTERNEHMENSGROESSEN_LABELS = {"solo":"Solo","team":"2–10 (Kleines Team)","kmu":"11–100 (KMU)"}
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
IT_INFRASTRUKTUR_LABELS = {
    "cloud": "Cloud",
    "on_premise": "On-Premise",
    "hybrid": "Hybrid (Cloud + On-Premise)",
}
PROZESSE_PAPIERLOS_LABELS = {
    "0-20": "0–20%",
    "21-40": "21–40%",
    "41-60": "41–60%",
    "61-80": "61–80%",
    "81-100": "81–100%",
}
AUTOMATISIERUNGSGRAD_LABELS = {
    "eher_niedrig": "Eher niedrig",
    "mittel": "Mittel",
    "eher_hoch": "Eher hoch",
}
YESNO_LABELS = {
    "ja": "Ja",
    "nein": "Nein",
    "teilweise": "Teilweise",
    "unklar": "Unklar",
}
LEVEL_LABELS = {
    "niedrig": "Niedrig",
    "mittel": "Mittel",
    "hoch": "Hoch",
    "sehr_hoch": "Sehr hoch",
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

    # Additional labels for all fields used in templates
    out["HAUPTLEISTUNG"] = out.get("hauptleistung", "") or "—"
    out["IT_INFRASTRUKTUR_LABEL"] = IT_INFRASTRUKTUR_LABELS.get(out.get("it_infrastruktur", ""), out.get("it_infrastruktur", "") or "—")
    out["PROZESSE_PAPIERLOS_LABEL"] = PROZESSE_PAPIERLOS_LABELS.get(out.get("prozesse_papierlos", ""), out.get("prozesse_papierlos", "") or "—")
    out["AUTOMATISIERUNGSGRAD_LABEL"] = AUTOMATISIERUNGSGRAD_LABELS.get(out.get("automatisierungsgrad", ""), out.get("automatisierungsgrad", "") or "—")
    out["ROADMAP_VORHANDEN_LABEL"] = YESNO_LABELS.get(out.get("roadmap_vorhanden", ""), out.get("roadmap_vorhanden", "") or "—")
    out["GOVERNANCE_RICHTLINIEN_LABEL"] = YESNO_LABELS.get(out.get("governance_richtlinien", ""), out.get("governance_richtlinien", "") or "—")
    out["CHANGE_MANAGEMENT_LABEL"] = LEVEL_LABELS.get(out.get("change_management", ""), out.get("change_management", "") or "—")
    out["MELDEWEGE_LABEL"] = YESNO_LABELS.get(out.get("meldewege", ""), out.get("meldewege", "") or "—")
    out["DATENSCHUTZ_LABEL"] = YESNO_LABELS.get(str(out.get("datenschutz", "")).lower() if out.get("datenschutz") is not None else "", "—")
    out["LOESCHREGELN_LABEL"] = YESNO_LABELS.get(out.get("loeschregeln", ""), out.get("loeschregeln", "") or "—")
    out["DATENSCHUTZBEAUFTRAGTER_LABEL"] = YESNO_LABELS.get(out.get("datenschutzbeauftragter", ""), out.get("datenschutzbeauftragter", "") or "—")
    out["FOLGENABSCHAETZUNG_LABEL"] = YESNO_LABELS.get(out.get("folgenabschaetzung", ""), out.get("folgenabschaetzung", "") or "—")
    out["INTERNE_KI_KOMPETENZEN_LABEL"] = YESNO_LABELS.get(out.get("interne_ki_kompetenzen", ""), out.get("interne_ki_kompetenzen", "") or "—")

    # Freitext fields (pass through as-is)
    out["STRATEGISCHE_ZIELE"] = out.get("strategische_ziele", "") or "—"
    out["GESCHAEFTSMODELL_EVOLUTION"] = out.get("geschaeftsmodell_evolution", "") or "—"
    out["ZEITERSPARNIS_PRIORITAET"] = out.get("zeitersparnis_prioritaet", "") or "—"
    out["KI_PROJEKTE"] = out.get("ki_projekte", "") or "—"
    out["VISION_3_JAHRE"] = out.get("vision_3_jahre", "") or "—"
    out["MITARBEITER_LABEL"] = out.get("unternehmensgroesse", "") or "—"  # Alias for employee count
    out["UMSATZ_LABEL"] = out.get("JAHRESUMSATZ_LABEL", "—")  # Alias

    # Alias: ki_knowhow
    if "ki_kompetenz" in out and "ki_knowhow" not in out:
        out["ki_knowhow"] = out["ki_kompetenz"]
    return out
