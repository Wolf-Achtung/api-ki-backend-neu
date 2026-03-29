# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any
import os
import html

# Canonical maps
BRANCHE_MAP = {
    "beratung & dienstleistungen": "beratung",
    "beratung": "beratung",
    "marketing & werbung": "marketing",
    "marketing": "marketing",
    "it & software": "it_software",
    "it/software": "it_software",
    "it": "it_software",
    "finanzen & versicherungen": "finanzen",
    "finanzen": "finanzen",
    "handel & e-commerce": "handel",
    "e-commerce": "handel",
    "handel": "handel",
    "bildung": "bildung",
    "verwaltung": "verwaltung",
    "gesundheit & pflege": "gesundheit",
    "gesundheit": "gesundheit",
    "bauwesen & architektur": "bau",
    "bau": "bau",
    "medien & kreativwirtschaft": "medien",
    "medien": "medien",
    "industrie & produktion": "industrie",
    "industrie": "industrie",
    "transport & logistik": "logistik",
    "logistik": "logistik",
}

UNTERNEHMENSGROESSE_MAP = {
    # Frontend V2 raw values (primary)
    "1": "solo",                                  # Raw value from questionnaire
    "2–10": "team",                               # En-dash (U+2013)
    "2-10": "team",                               # Hyphen fallback
    "11–100": "kmu",                              # En-dash (U+2013)
    "11-100": "kmu",                              # Hyphen fallback
    # FIX-SIZE-BUCKET: Non-standard ranges that map to KMU
    "11–49": "kmu",                               # En-dash (test data variant)
    "11-49": "kmu",                               # Hyphen fallback
    "50–250": "kmu",                              # En-dash (extended KMU range)
    "50-250": "kmu",                              # Hyphen fallback
    # Frontend V2 with labels
    "1 (solo-selbstständig/freiberuflich)": "solo",
    "2–10 (kleines team)": "team",
    "2-10 (kleines team)": "team",
    "11–100 (kmu)": "kmu",
    "11-100 (kmu)": "kmu",
    # Legacy normalized values
    "solo": "solo",
    "team": "team",
    "kmu": "kmu",
    "klein": "team",
    "freiberufler": "solo",
}

# Display-Labels (13 Branchen - v14.35.19)
BRANCHEN_LABELS = {
    "beratung": "Beratung & Dienstleistungen",
    "marketing": "Marketing & Werbung",
    "it_software": "IT & Software",
    "finanzen": "Finanzen & Versicherungen",
    "handel": "Handel & E-Commerce",
    "bildung": "Bildung",
    "verwaltung": "Verwaltung",
    "gesundheit": "Gesundheit & Pflege",
    "bau": "Bauwesen & Architektur",
    "medien": "Medien & Kreativwirtschaft",
    "industrie": "Industrie & Produktion",
    "logistik": "Transport & Logistik",
    "gastronomie": "Gastronomie & Tourismus",  # v14.35.19: 13. Branche hinzugefügt
}

UNTERNEHMENSGROESSEN_LABELS = {
    "solo": "Solo",
    "team": "2–10 (Kleines Team)",
    "kmu": "11–100 (KMU)",
}

BUNDESLAENDER_LABELS = {
    "bw": "Baden-Württemberg",
    "by": "Bayern",
    "be": "Berlin",
    "bb": "Brandenburg",
    "hb": "Bremen",
    "hh": "Hamburg",
    "he": "Hessen",
    "mv": "Mecklenburg-Vorpommern",
    "ni": "Niedersachsen",
    "nw": "Nordrhein-Westfalen",
    "rp": "Rheinland-Pfalz",
    "sl": "Saarland",
    "sn": "Sachsen",
    "st": "Sachsen-Anhalt",
    "sh": "Schleswig-Holstein",
    "th": "Thüringen",
}

# Schweiz (26 Kantone)
KANTONE_LABELS = {
    "zh": "Zürich",
    "be_ch": "Bern",
    "lu": "Luzern",
    "ur": "Uri",
    "sz": "Schwyz",
    "ow": "Obwalden",
    "nw_ch": "Nidwalden",
    "gl": "Glarus",
    "zg": "Zug",
    "fr": "Freiburg",
    "so": "Solothurn",
    "bs": "Basel-Stadt",
    "bl": "Basel-Landschaft",
    "sh_ch": "Schaffhausen",
    "ar": "Appenzell Ausserrhoden",
    "ai": "Appenzell Innerrhoden",
    "sg": "St. Gallen",
    "gr": "Graubünden",
    "ag": "Aargau",
    "tg": "Thurgau",
    "ti": "Tessin",
    "vd": "Waadt",
    "vs": "Wallis",
    "ne": "Neuenburg",
    "ge": "Genf",
    "ju": "Jura",
}

# Österreich (9 Bundesländer)
AT_BUNDESLAENDER_LABELS = {
    "wi": "Wien",
    "noe": "Niederösterreich",
    "ooe": "Oberösterreich",
    "sbg": "Salzburg",
    "tir": "Tirol",
    "vbg": "Vorarlberg",
    "ktn": "Kärnten",
    "stm": "Steiermark",
    "bgl": "Burgenland",
}

# UK (4 Nations/Regionen)
UK_REGIONS_LABELS = {
    "eng": "England",
    "sco": "Scotland",
    "wal": "Wales",
    "nir": "Northern Ireland",
    "london": "London",
}


def get_region_label(region_code: str, country: str = "DE") -> str:
    """Resolve a region code to a display label, respecting country context."""
    key = str(region_code or "").strip().lower()
    if not key:
        return ""
    country_up = str(country or "DE").strip().upper()
    if country_up == "CH":
        return KANTONE_LABELS.get(key, key)
    elif country_up == "AT":
        return AT_BUNDESLAENDER_LABELS.get(key, key)
    elif country_up == "GB":
        return UK_REGIONS_LABELS.get(key, key)
    else:
        return BUNDESLAENDER_LABELS.get(key, key)

UMSATZ_LABELS = {
    "unter_100k": "unter 100 T€",
    "100k_500k": "100 T€ – 500 T€",
    "500k_2m": "0,5 – 2 Mio. €",
    "2m_10m": "2 – 10 Mio. €",
    "ueber_10m": "> 10 Mio. €",
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
    if not text or not isinstance(text, str):
        return text
    if "Ã" not in text and "â" not in text:
        return text
    try:
        return text.encode("latin-1", errors="ignore").decode(
            "utf-8", errors="ignore"
        )
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


# Branch-Benchmark (sensibel → kein exakter Kundensatz nötig)
DEFAULT_RATE = int(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60"))
BRANCH_RATE = {
    "beratung": 90,
    "marketing": 75,
    "it_software": 95,
    "finanzen": 100,
    "handel": 60,
    "bildung": 55,
    "verwaltung": 55,
    "gesundheit": 70,
    "bau": 65,
    "medien": 70,
    "industrie": 80,
    "logistik": 65,
}
SIZE_MULT = {"solo": 0.9, "team": 1.0, "kmu": 1.1}


def _derive_rate(branche: str, groesse: str, band: str | None) -> int:
    if band:
        try:
            lo, hi = band.replace(" ", "").split("_", 1)
            return int(round((int(lo) + int(hi)) / 2.0))
        except Exception:
            pass
    base = BRANCH_RATE.get(branche or "", DEFAULT_RATE)
    mult = SIZE_MULT.get(groesse or "", 1.0)
    return max(30, int(round(base * mult)))


def _shorten_hauptleistung(text: str, max_len: int = 200) -> str:  # L1: was 80
    if not text:
        return "—"
    txt = str(text).strip()
    if len(txt) <= max_len:
        return txt
    for sep in [".", ";", " – "]:
        if sep in txt:
            txt = txt.split(sep, 1)[0]
            break
    if len(txt) > max_len:
        txt = txt[:max_len]
    return txt.rstrip(" ,;") + "…"


def _generate_hauptleistung_synonyme(text: str, lang: str = "de") -> str:
    """
    Generate synonym phrases for hauptleistung to enable natural variation.

    FIX-HAUPTLEISTUNG-FIRST: Provides alternatives to avoid repetition.
    Returns comma-separated synonyms that can be used interchangeably.
    """
    if not text or text == "—":
        if lang == "en":
            return "your core service, your main offering, this service"
        return "Ihr Kerngeschäft, Ihre Hauptleistung, dieser Service"

    # German synonyms
    if lang == "de":
        return f'"{text}", Ihr Kerngeschäft, diese Leistung, Ihr Angebot'
    # English synonyms
    return f'"{text}", your core service, this offering, your business'


def _generate_hauptleistung_workflow_hint(text: str, lang: str = "de") -> str:
    """
    Generate a brief workflow hint based on hauptleistung.

    FIX-HAUPTLEISTUNG-FIRST: Provides context for typical workflow steps.
    """
    if not text or text == "—":
        if lang == "en":
            return "typical daily tasks and customer interactions"
        return "typische Alltagsaufgaben und Kundeninteraktionen"

    # Extract key action words (verbs/nouns) from hauptleistung
    keywords = []
    action_indicators_de = ["beratung", "entwicklung", "erstellung", "analyse", "verkauf",
                            "training", "coaching", "design", "planung", "umsetzung",
                            "service", "support", "management", "produktion"]
    action_indicators_en = ["consulting", "development", "creation", "analysis", "sales",
                            "training", "coaching", "design", "planning", "implementation",
                            "service", "support", "management", "production"]

    text_lower = text.lower()
    indicators = action_indicators_de if lang == "de" else action_indicators_en

    for indicator in indicators:
        if indicator in text_lower:
            keywords.append(indicator)

    if not keywords:
        if lang == "en":
            return f"the core steps of '{text[:50]}...'" if len(text) > 50 else f"the core steps of '{text}'"
        return f"die Kernschritte von '{text[:50]}...'" if len(text) > 50 else f"die Kernschritte von '{text}'"

    # Build workflow hint from found keywords
    if lang == "de":
        return f"Arbeitsschritte rund um {', '.join(keywords[:3])}"
    return f"workflow steps around {', '.join(keywords[:3])}"


def normalize_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(answers or {})

    for k, v in list(out.items()):
        if isinstance(v, str):
            out[k] = _fix_utf8_mojibake(v)
        elif isinstance(v, list):
            out[k] = [
                _fix_utf8_mojibake(x) if isinstance(x, str) else x for x in v
            ]

    b_raw = str(out.get("branche", "")).strip().lower()
    out["branche"] = (
        BRANCHE_MAP.get(b_raw, out.get("branche", "")) or out.get("branche", "")
    )

    g_raw = str(out.get("unternehmensgroesse", "")).strip().lower()
    out["unternehmensgroesse"] = (
        UNTERNEHMENSGROESSE_MAP.get(g_raw, out.get("unternehmensgroesse", ""))
        or out.get("unternehmensgroesse", "")
    )

    bl_raw = str(out.get("bundesland", "")).strip()
    if bl_raw:
        if len(bl_raw) > 2:
            bl_key = bl_raw[:2].lower()
        else:
            bl_key = bl_raw.lower()
        out["bundesland"] = bl_key
    else:
        out["bundesland"] = ""

    for k in ("research_days", "tools_days", "funding_days"):
        if k in out:
            out[k] = _parse_int(out[k], 30)

    band = out.get("stundensatz_band")
    if not out.get("stundensatz_eur"):
        out["stundensatz_eur"] = _derive_rate(
            out.get("branche"), out.get("unternehmensgroesse"), band
        )

    out["BRANCHE_LABEL"] = BRANCHEN_LABELS.get(
        out.get("branche", ""),
        out.get("branche", "") or "—",
    )
    out["UNTERNEHMENSGROESSE_LABEL"] = UNTERNEHMENSGROESSEN_LABELS.get(
        out.get("unternehmensgroesse", ""),
        out.get("unternehmensgroesse", "") or "—",
    )
    out["BUNDESLAND_LABEL"] = BUNDESLAENDER_LABELS.get(
        out.get("bundesland", ""),
        out.get("bundesland", "").upper() or "—",
    )
    rev = str(out.get("jahresumsatz", "") or "").strip().lower()
    out["JAHRESUMSATZ_LABEL"] = UMSATZ_LABELS.get(
        rev, out.get("jahresumsatz", "") or "—"
    )

    out["HAUPTLEISTUNG"] = out.get("hauptleistung", "") or "—"
    out["HAUPTLEISTUNG_SHORT"] = _shorten_hauptleistung(out["HAUPTLEISTUNG"])
    # FIX-HAUPTLEISTUNG-FIRST: Add synonym and workflow hint derivatives
    report_lang = str(out.get("lang", "") or out.get("sprache", "") or "de").lower()[:2]
    out["HAUPTLEISTUNG_SYNONYME"] = _generate_hauptleistung_synonyme(
        out["HAUPTLEISTUNG"], lang=report_lang
    )
    out["HAUPTLEISTUNG_WORKFLOW_HINT"] = _generate_hauptleistung_workflow_hint(
        out["HAUPTLEISTUNG"], lang=report_lang
    )
    out["IT_INFRASTRUKTUR_LABEL"] = IT_INFRASTRUKTUR_LABELS.get(
        out.get("it_infrastruktur", ""),
        out.get("it_infrastruktur", "") or "—",
    )
    out["PROZESSE_PAPIERLOS_LABEL"] = PROZESSE_PAPIERLOS_LABELS.get(
        out.get("prozesse_papierlos", ""),
        out.get("prozesse_papierlos", "") or "—",
    )
    out["AUTOMATISIERUNGSGRAD_LABEL"] = AUTOMATISIERUNGSGRAD_LABELS.get(
        out.get("automatisierungsgrad", ""),
        out.get("automatisierungsgrad", "") or "—",
    )
    out["ROADMAP_VORHANDEN_LABEL"] = YESNO_LABELS.get(
        out.get("roadmap_vorhanden", ""),
        out.get("roadmap_vorhanden", "") or "—",
    )
    out["GOVERNANCE_RICHTLINIEN_LABEL"] = YESNO_LABELS.get(
        out.get("governance_richtlinien", ""),
        out.get("governance_richtlinien", "") or "—",
    )
    out["CHANGE_MANAGEMENT_LABEL"] = LEVEL_LABELS.get(
        out.get("change_management", ""),
        out.get("change_management", "") or "—",
    )
    out["MELDEWEGE_LABEL"] = YESNO_LABELS.get(
        out.get("meldewege", ""), out.get("meldewege", "") or "—"
    )
    out["DATENSCHUTZ_LABEL"] = YESNO_LABELS.get(
        str(out.get("datenschutz", "")).lower()
        if out.get("datenschutz") is not None
        else "",
        "—",
    )
    out["LOESCHREGELN_LABEL"] = YESNO_LABELS.get(
        out.get("loeschregeln", ""), out.get("loeschregeln", "") or "—"
    )
    out["DATENSCHUTZBEAUFTRAGTER_LABEL"] = YESNO_LABELS.get(
        out.get("datenschutzbeauftragter", ""),
        out.get("datenschutzbeauftragter", "") or "—",
    )
    out["FOLGENABSCHAETZUNG_LABEL"] = YESNO_LABELS.get(
        out.get("folgenabschaetzung", ""),
        out.get("folgenabschaetzung", "") or "—",
    )
    out["INTERNE_KI_KOMPETENZEN_LABEL"] = YESNO_LABELS.get(
        out.get("interne_ki_kompetenzen", ""),
        out.get("interne_ki_kompetenzen", "") or "—",
    )

    out["STRATEGISCHE_ZIELE"] = out.get("strategische_ziele", "") or "—"
    out["GESCHAEFTSMODELL_EVOLUTION"] = (
        out.get("geschaeftsmodell_evolution", "") or "—"
    )
    out["ZEITERSPARNIS_PRIORITAET"] = (
        out.get("zeitersparnis_prioritaet", "") or "—"
    )
    out["KI_PROJEKTE"] = out.get("ki_projekte", "") or "—"
    out["VISION_3_JAHRE"] = out.get("vision_3_jahre", "") or "—"
    out["KI_GUARDRAILS"] = out.get("ki_guardrails", "") or "—"
    out["MITARBEITER_LABEL"] = out.get("unternehmensgroesse", "") or "—"
    out["UMSATZ_LABEL"] = out.get("JAHRESUMSATZ_LABEL", "—")

    if "ki_kompetenz" in out and "ki_knowhow" not in out:
        out["ki_knowhow"] = out["ki_kompetenz"]

    return out
