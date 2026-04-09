# -*- coding: utf-8 -*-
"""
Deterministic field normalizer for the conversational AI questionnaire.

Rules:
- LLM never writes directly to DB — always through this normalizer
- Enums/normalization run deterministically, not LLM-based
- Fields with confidence "low" are NOT stored in collected_fields
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

log = logging.getLogger(__name__)


# ===========================================================================
# Normalization Result
# ===========================================================================

@dataclass
class NormResult:
    value: Any
    confidence: str          # "high" | "medium" | "low"
    needs_confirmation: bool


# ===========================================================================
# Field Registry — PoC Block 1 (Section 0) + full structure for later
# ===========================================================================

FIELD_REGISTRY: dict[str, dict] = {
    # --- Section 0: Ihr Unternehmen (PoC) ---
    "branche":              {"type": "enum",  "required": True,  "section": 0, "chat_mode": "QR"},
    "unternehmensgroesse":  {"type": "enum",  "required": True,  "section": 0, "chat_mode": "QR"},
    "selbststaendig":       {"type": "enum",  "required": False, "section": 0, "chat_mode": "QR"},
    "country":              {"type": "enum",  "required": True,  "section": 0, "chat_mode": "QR"},
    "bundesland":           {"type": "enum",  "required": True,  "section": 0, "chat_mode": "QR"},
    "hauptleistung":        {"type": "text",  "required": True,  "section": 0, "chat_mode": "FT"},
    "jahresumsatz":         {"type": "enum",  "required": False, "section": 0, "chat_mode": "QR"},
    # --- Section 1: Organisation & Datenlage ---
    "zielgruppen":          {"type": "multi", "required": False, "section": 1, "chat_mode": "QR"},
    "it_infrastruktur":     {"type": "enum",  "required": False, "section": 1, "chat_mode": "QR"},
    "interne_ki_kompetenzen": {"type": "enum", "required": False, "section": 1, "chat_mode": "QR"},
    "datenquellen":         {"type": "multi", "required": False, "section": 1, "chat_mode": "QR"},
    # --- Section 2: Digitalisierung & KI-Status ---
    "digitalisierungsgrad": {"type": "slider", "required": True,  "section": 2, "chat_mode": "SC", "min": 1, "max": 10},
    "prozesse_papierlos":   {"type": "enum",  "required": False, "section": 2, "chat_mode": "QR"},
    "automatisierungsgrad": {"type": "enum",  "required": False, "section": 2, "chat_mode": "QR"},
    "ki_einsatz":           {"type": "multi", "required": False, "section": 2, "chat_mode": "QR"},
    "ki_kompetenz":         {"type": "enum",  "required": False, "section": 2, "chat_mode": "QR"},
    # --- Section 3: Ziele & Use Cases ---
    "ki_ziele":             {"type": "multi", "required": True,  "section": 3, "chat_mode": "QR"},
    "anwendungsfaelle":     {"type": "multi", "required": False, "section": 3, "chat_mode": "QR"},
    "ki_projekte":          {"type": "text",  "required": False, "section": 3, "chat_mode": "FT"},
    "pilot_bereich":        {"type": "enum",  "required": False, "section": 3, "chat_mode": "QR"},
    "zeitersparnis_prioritaet": {"type": "text", "required": True, "section": 3, "chat_mode": "FT"},
    "geschaeftsmodell_evolution": {"type": "text", "required": False, "section": 3, "chat_mode": "FT"},
    # --- Section 4: Strategie & Governance ---
    "vision_3_jahre":       {"type": "text",  "required": True,  "section": 4, "chat_mode": "FT"},
    "strategische_ziele":   {"type": "text",  "required": True,  "section": 4, "chat_mode": "FT"},
    "ki_guardrails":        {"type": "text",  "required": False, "section": 4, "chat_mode": "FT"},
    "roadmap_vorhanden":    {"type": "enum",  "required": False, "section": 4, "chat_mode": "QR"},
    "change_management":    {"type": "enum",  "required": False, "section": 4, "chat_mode": "QR"},
    "massnahmen_komplexitaet": {"type": "enum", "required": False, "section": 4, "chat_mode": "QR"},
    "governance_richtlinien": {"type": "enum", "required": False, "section": 4, "chat_mode": "QR"},
    # --- Section 5: Ressourcen & Umsetzung ---
    "zeitbudget":           {"type": "enum",  "required": False, "section": 5, "chat_mode": "QR"},
    "vorhandene_tools":     {"type": "multi", "required": False, "section": 5, "chat_mode": "QR"},
    "trainings_interessen": {"type": "multi", "required": False, "section": 5, "chat_mode": "QR"},
    "vision_prioritaet":    {"type": "enum",  "required": False, "section": 5, "chat_mode": "QR"},
    "innovationsprozess":   {"type": "enum",  "required": False, "section": 5, "chat_mode": "QR"},
    # --- Section 6: Recht & Datenschutz ---
    "datenschutz":          {"type": "bool",  "required": True,  "section": 6, "chat_mode": "QR", "skip_in_chat": True},
    "datenschutzbeauftragter": {"type": "enum", "required": False, "section": 6, "chat_mode": "QR"},
    "technische_massnahmen": {"type": "enum", "required": False, "section": 6, "chat_mode": "QR"},
    "folgenabschaetzung":   {"type": "enum",  "required": False, "section": 6, "chat_mode": "QR"},
    "meldewege":            {"type": "enum",  "required": False, "section": 6, "chat_mode": "QR"},
    "loeschregeln":         {"type": "enum",  "required": False, "section": 6, "chat_mode": "QR"},
    "ai_act_kenntnis":      {"type": "enum",  "required": False, "section": 6, "chat_mode": "QR"},
    "regulierte_branche":   {"type": "multi", "required": False, "section": 6, "chat_mode": "QR"},
    "ki_hemmnisse":         {"type": "multi", "required": False, "section": 6, "chat_mode": "QR"},
    # --- Section 7: Förderung & Investition ---
    "bisherige_foerdermittel": {"type": "enum", "required": False, "section": 7, "chat_mode": "QR"},
    "interesse_foerderung": {"type": "enum",  "required": False, "section": 7, "chat_mode": "QR"},
    "erfahrung_beratung":   {"type": "enum",  "required": False, "section": 7, "chat_mode": "QR"},
    "investitionsbudget":   {"type": "enum",  "required": True,  "section": 7, "chat_mode": "QR"},
    "marktposition":        {"type": "enum",  "required": False, "section": 7, "chat_mode": "QR"},
    "benchmark_wettbewerb": {"type": "enum",  "required": False, "section": 7, "chat_mode": "QR"},
    "risikofreude":         {"type": "slider", "required": False, "section": 7, "chat_mode": "SC", "min": 1, "max": 5},
}


# ===========================================================================
# Sections (8 conversation sections)
# ===========================================================================

SECTIONS = [
    {
        "index": 0,
        "name": "Ihr Unternehmen",
        "fields": ["branche", "unternehmensgroesse", "selbststaendig",
                    "country", "bundesland", "hauptleistung", "jahresumsatz"],
        "intro": "Lassen Sie uns mit den Grundlagen beginnen — erzählen Sie mir von Ihrem Unternehmen.",
    },
    {
        "index": 1,
        "name": "Organisation & Datenlage",
        "fields": ["zielgruppen", "it_infrastruktur", "interne_ki_kompetenzen", "datenquellen"],
        "intro": "Wie sieht es mit Ihrer IT-Infrastruktur und Ihren Daten aus?",
    },
    {
        "index": 2,
        "name": "Digitalisierung & KI-Status",
        "fields": ["digitalisierungsgrad", "prozesse_papierlos", "automatisierungsgrad",
                    "ki_einsatz", "ki_kompetenz"],
        "intro": "Wie digital arbeiten Sie heute — und nutzen Sie bereits KI?",
    },
    {
        "index": 3,
        "name": "Ziele & Use Cases",
        "fields": ["ki_ziele", "anwendungsfaelle", "ki_projekte", "pilot_bereich",
                    "zeitersparnis_prioritaet", "geschaeftsmodell_evolution"],
        "intro": "Was erhoffen Sie sich konkret vom KI-Einsatz?",
    },
    {
        "index": 4,
        "name": "Strategie & Governance",
        "fields": ["vision_3_jahre", "strategische_ziele", "ki_guardrails",
                    "roadmap_vorhanden", "change_management", "massnahmen_komplexitaet",
                    "governance_richtlinien"],
        "intro": "Sprechen wir über Ihre strategische Ausrichtung und Leitplanken.",
    },
    {
        "index": 5,
        "name": "Ressourcen & Umsetzung",
        "fields": ["zeitbudget", "vorhandene_tools", "trainings_interessen",
                    "vision_prioritaet", "innovationsprozess"],
        "intro": "Welche Ressourcen und Werkzeuge stehen Ihnen zur Verfügung?",
    },
    {
        "index": 6,
        "name": "Recht & Datenschutz",
        "fields": ["datenschutz", "datenschutzbeauftragter", "technische_massnahmen",
                    "folgenabschaetzung", "meldewege", "loeschregeln", "ai_act_kenntnis",
                    "regulierte_branche", "ki_hemmnisse"],
        "intro": "Klären wir den Stand bei Datenschutz, Compliance und möglichen Hürden.",
    },
    {
        "index": 7,
        "name": "Förderung & Investition",
        "fields": ["bisherige_foerdermittel", "interesse_foerderung", "erfahrung_beratung",
                    "investitionsbudget", "marktposition", "benchmark_wettbewerb",
                    "risikofreude"],
        "intro": "Zum Abschluss: Budget, Fördermittel und Ihre Marktposition.",
    },
]


# ===========================================================================
# Strategy Field Registry (Report 3: KI-Strategiebericht)
# ===========================================================================

STRATEGY_FIELD_REGISTRY: dict[str, dict] = {
    # --- Sektion 0: Umsetzungsplanung ---
    "s1_budget":          {"type": "enum",  "required": True,  "section": 0, "chat_mode": "QR"},
    "s2_zeitrahmen":      {"type": "enum",  "required": True,  "section": 0, "chat_mode": "QR"},
    "s3_prioritaeten":    {"type": "multi", "required": True,  "section": 0, "chat_mode": "QR", "max_select": 3},
    "s4_engpass":         {"type": "enum",  "required": True,  "section": 0, "chat_mode": "QR"},
    "s5_software":        {"type": "text",  "required": False, "section": 0, "chat_mode": "FT"},
    "s5_vision":          {"type": "text",  "required": False, "section": 0, "chat_mode": "FT"},
    "s6_foerderinteresse": {"type": "enum", "required": True,  "section": 0, "chat_mode": "QR"},
    "s7_entscheidung":    {"type": "enum",  "required": True,  "section": 0, "chat_mode": "QR"},
    # --- Sektion 1: Erfahrung & Marktposition ---
    "s8_erfahrung":       {"type": "enum",  "required": False, "section": 1, "chat_mode": "QR"},
    "s9_ansatz":          {"type": "enum",  "required": False, "section": 1, "chat_mode": "QR"},
    "s10_datenschutz":    {"type": "enum",  "required": False, "section": 1, "chat_mode": "QR"},
    "wettbewerber_anzahl": {"type": "enum", "required": False, "section": 1, "chat_mode": "QR"},
    "kundenbindung_typ":  {"type": "enum",  "required": False, "section": 1, "chat_mode": "QR"},
    "datenreife":         {"type": "enum",  "required": False, "section": 1, "chat_mode": "QR"},
}

STRATEGY_SECTIONS = [
    {
        "index": 0,
        "name": "Umsetzungsplanung",
        "fields": ["s1_budget", "s2_zeitrahmen", "s3_prioritaeten", "s4_engpass",
                    "s5_software", "s5_vision", "s6_foerderinteresse", "s7_entscheidung"],
        "intro": "Für Ihren individuellen Strategiebericht benötige ich noch einige Angaben zu Ihrer konkreten Umsetzungsplanung.",
    },
    {
        "index": 1,
        "name": "Erfahrung & Marktposition",
        "fields": ["s8_erfahrung", "s9_ansatz", "s10_datenschutz",
                    "wettbewerber_anzahl", "kundenbindung_typ", "datenreife"],
        "intro": "Zum Abschluss: Ein paar Fragen zu Ihrer bisherigen Erfahrung und Marktposition.",
    },
]

STRATEGY_ENUM_VALUES: dict[str, list[str]] = {
    "s1_budget": ["unter_2000", "2000_10000", "10000_50000", "ueber_50000", "unklar"],
    "s2_zeitrahmen": [
        "Sofort (1-3 Monate)", "Kurzfristig (3-6 Monate)",
        "Mittelfristig (6-12 Monate)", "Langfristig (12-18 Monate)",
    ],
    "s3_prioritaeten": [
        "Kosten senken", "Umsatz steigern", "Qualität verbessern",
        "Geschwindigkeit erhöhen", "Compliance sichern", "Neue Geschäftsfelder",
        "Fachkräftemangel kompensieren", "Kundenerlebnis verbessern",
    ],
    "s4_engpass": [
        "Zu wenig Know-how", "Kein Budget", "Fehlende Daten",
        "Widerstand im Team", "Regulatorische Unsicherheit",
        "Kein klarer Use Case", "Andere",
    ],
    "s6_foerderinteresse": [
        "Ja, dringend", "Ja, wenn passend", "Nein, eigenes Budget", "Weiß nicht",
    ],
    "s7_entscheidung": [
        "Entscheide allein", "Brauche Vorlage für Geschäftsleitung",
        "Muss Gesellschafter überzeugen", "Muss Aufsichtsrat/Beirat informieren",
    ],
    "s8_erfahrung": ["Noch keine", "Experimentiert", "Erste Tools im Einsatz", "Fortgeschritten"],
    "s9_ansatz": ["Cloud-SaaS", "On-Premise", "Hybrid", "Egal"],
    "s10_datenschutz": ["Hoch", "Mittel", "Niedrig"],
    "wettbewerber_anzahl": ["wenige", "mehrere", "viele", "unklar"],
    "kundenbindung_typ": ["einmalig", "wiederkehrend", "gemischt"],
    "datenreife": ["keine", "basis", "umfangreich", "unklar"],
}


def get_registry_for_report(report_type: str) -> dict[str, dict]:
    """Get the field registry for a given report type."""
    if report_type == "strategy":
        return STRATEGY_FIELD_REGISTRY
    return FIELD_REGISTRY


def get_sections_for_report(report_type: str) -> list[dict]:
    """Get the sections list for a given report type."""
    if report_type == "strategy":
        return STRATEGY_SECTIONS
    return SECTIONS


def get_enum_values_for_report(report_type: str) -> dict[str, list[str]]:
    """Get the enum values for a given report type."""
    if report_type == "strategy":
        return STRATEGY_ENUM_VALUES
    return ENUM_VALUES
# ===========================================================================

CONDITIONALS: dict[str, dict] = {
    "selbststaendig": {
        "show_if": {"unternehmensgroesse": "1"},
        "hide_action": "delete",
    },
    "bundesland": {
        "show_if": {"country": ["DE", "AT", "CH", "GB"]},
        "hide_action": "delete",
    },
}


def is_field_visible(field_name: str, collected: dict) -> bool:
    """Check if a conditional field should be shown given current collected data."""
    cond = CONDITIONALS.get(field_name)
    if not cond:
        return True
    show_if = cond["show_if"]
    for dep_field, dep_value in show_if.items():
        current = collected.get(dep_field)
        if current is None:
            return False
        if isinstance(dep_value, list):
            if current not in dep_value:
                return False
        elif current != dep_value:
            return False
    return True


# ===========================================================================
# Verified Enum Values (from Frontend formbuilder_de_SINGLE_FULL.js)
# ===========================================================================

ENUM_VALUES: dict[str, list[str]] = {
    # --- Sektion 0 ---
    "branche": [
        "marketing", "beratung", "it", "finanzen", "handel", "bildung",
        "verwaltung", "gesundheit", "bau", "medien", "industrie",
        "logistik", "gastronomie",
    ],
    "unternehmensgroesse": ["1", "2–10", "11–100"],
    "selbststaendig": [
        "freiberufler", "kapitalgesellschaft", "einzelunternehmer", "sonstiges",
    ],
    "country": [
        "DE", "AT", "FR", "IT", "ES", "NL", "BE", "IE", "PL", "SE", "DK",
        "FI", "PT", "CZ", "GR", "HU", "RO", "other_eu",
        "GB", "CH", "NO", "IS", "LI", "other_europe",
        "other",
    ],
    "jahresumsatz": [
        "unter_100k", "100k_500k", "500k_2m", "2m_10m", "ueber_10m", "keine_angabe",
    ],
    # --- Sektion 1 ---
    "zielgruppen": [
        "b2b", "b2c", "kmu", "grossunternehmen", "selbststaendige",
        "oeffentliche_hand", "privatpersonen", "startups", "andere",
    ],
    "it_infrastruktur": ["cloud", "on_premise", "hybrid", "unklar"],
    "interne_ki_kompetenzen": ["ja", "nein", "in_planung"],
    "datenquellen": [
        "kundendaten", "verkaufsdaten", "produktionsdaten",
        "personaldaten", "marketingdaten", "sonstige",
    ],
    # --- Sektion 2 ---
    "prozesse_papierlos": ["0-20", "21-50", "51-80", "81-100"],
    "automatisierungsgrad": ["sehr_niedrig", "eher_niedrig", "mittel", "eher_hoch", "sehr_hoch"],
    "ki_einsatz": [
        "chatbots", "marketing", "vertrieb", "datenanalyse",
        "produktion", "hr", "andere", "noch_keine",
    ],
    "ki_kompetenz": ["hoch", "mittel", "niedrig", "keine"],
    # --- Sektion 3 ---
    "ki_ziele": [
        "effizienz", "automatisierung", "neue_produkte", "kundenservice",
        "datenauswertung", "kosten_senken", "wettbewerbsfaehigkeit", "keine_angabe",
    ],
    "anwendungsfaelle": [
        "chatbots", "content_generation", "datenanalyse", "dokumentation",
        "prozess_automation", "personalisierung", "andere", "keine_angabe",
    ],
    "pilot_bereich": ["kundenservice", "marketing", "vertrieb", "verwaltung", "produktion", "andere"],
    # --- Sektion 4 ---
    "massnahmen_komplexitaet": ["niedrig", "mittel", "hoch", "unklar"],
    "roadmap_vorhanden": ["ja", "teilweise", "nein"],
    "governance_richtlinien": ["ja", "teilweise", "nein"],
    "change_management": ["sehr_hoch", "hoch", "mittel", "niedrig", "sehr_niedrig"],
    # --- Sektion 5 ---
    "zeitbudget": ["unter_2", "2_5", "5_10", "ueber_10"],
    "vorhandene_tools": ["crm", "erp", "projektmanagement", "marketing_automation", "buchhaltung", "keine"],
    "trainings_interessen": [
        "prompt_engineering", "llm_basics", "datenqualitaet_governance",
        "automatisierung", "ethik_recht", "keine",
    ],
    "vision_prioritaet": [
        "gpt_services", "kundenservice", "datenprodukte",
        "prozessautomation", "marktfuehrerschaft", "keine_angabe",
    ],
    "innovationsprozess": ["innovationsteam", "mitarbeitende", "kunden", "berater", "zufall", "unbekannt"],
    "regulierte_branche": [
        "gesundheit", "finanzen", "oeffentlich", "recht", "vertraulich_nda", "keine",
    ],
    # --- Sektion 6 ---
    "datenschutzbeauftragter": ["ja", "nein", "teilweise"],
    "technische_massnahmen": ["alle", "teilweise", "keine"],
    "folgenabschaetzung": ["ja", "nein", "teilweise"],
    "meldewege": ["ja", "teilweise", "nein"],
    "loeschregeln": ["ja", "teilweise", "nein"],
    "ai_act_kenntnis": ["sehr_gut", "gut", "gehoert", "unbekannt"],
    "ki_hemmnisse": [
        "rechtsunsicherheit", "datenschutz", "knowhow", "budget",
        "teamakzeptanz", "zeitmangel", "it_integration", "keine", "andere",
    ],
    # --- Sektion 7 ---
    "bisherige_foerdermittel": ["ja", "nein"],
    "interesse_foerderung": ["ja", "nein", "unklar"],
    "erfahrung_beratung": ["ja", "nein", "unklar"],
    "investitionsbudget": ["unter_2000", "2000_10000", "10000_50000", "ueber_50000", "unklar"],
    "marktposition": ["marktfuehrer", "oberes_drittel", "mittelfeld", "nachzuegler", "unsicher"],
    "benchmark_wettbewerb": ["ja", "nein", "selten"],
}

# Bundesland codes per country (from frontend REGION_OPTIONS)
BUNDESLAND_VALUES: dict[str, list[str]] = {
    "DE": ["bw", "by", "be", "bb", "hb", "hh", "he", "mv", "ni", "nw", "rp", "sl", "sn", "st", "sh", "th"],
    "CH": ["zh", "be_ch", "lu", "ur", "sz", "ow", "nw_ch", "gl", "zg", "fr", "so", "bs", "bl", "sh_ch", "ar", "ai", "sg", "gr", "ag", "tg", "ti", "vd", "vs", "ne", "ge", "ju"],
    "AT": ["wi", "noe", "ooe", "sbg", "tir", "vbg", "ktn", "stm", "bgl"],
    "GB": ["eng", "sco", "wal", "nir"],
}

# All valid bundesland codes (flat set for quick lookup)
ALL_BUNDESLAND_CODES: set[str] = set()
for _codes in BUNDESLAND_VALUES.values():
    ALL_BUNDESLAND_CODES.update(_codes)

# Bundesland labels (code -> display name)
BUNDESLAND_LABELS: dict[str, str] = {
    # DE
    "bw": "Baden-Württemberg", "by": "Bayern", "be": "Berlin", "bb": "Brandenburg",
    "hb": "Bremen", "hh": "Hamburg", "he": "Hessen", "mv": "Mecklenburg-Vorpommern",
    "ni": "Niedersachsen", "nw": "Nordrhein-Westfalen", "rp": "Rheinland-Pfalz",
    "sl": "Saarland", "sn": "Sachsen", "st": "Sachsen-Anhalt",
    "sh": "Schleswig-Holstein", "th": "Thüringen",
    # CH
    "zh": "Zürich", "be_ch": "Bern", "lu": "Luzern", "ur": "Uri", "sz": "Schwyz",
    "ow": "Obwalden", "nw_ch": "Nidwalden", "gl": "Glarus", "zg": "Zug",
    "fr": "Freiburg", "so": "Solothurn", "bs": "Basel-Stadt", "bl": "Basel-Landschaft",
    "sh_ch": "Schaffhausen", "ar": "Appenzell Ausserrhoden", "ai": "Appenzell Innerrhoden",
    "sg": "St. Gallen", "gr": "Graubünden", "ag": "Aargau", "tg": "Thurgau",
    "ti": "Tessin", "vd": "Waadt", "vs": "Wallis", "ne": "Neuenburg",
    "ge": "Genf", "ju": "Jura",
    # AT
    "wi": "Wien", "noe": "Niederösterreich", "ooe": "Oberösterreich",
    "sbg": "Salzburg", "tir": "Tirol", "vbg": "Vorarlberg",
    "ktn": "Kärnten", "stm": "Steiermark", "bgl": "Burgenland",
    # GB
    "eng": "England", "sco": "Scotland", "wal": "Wales", "nir": "Northern Ireland",
}


# ===========================================================================
# Branch Aliases (chat free-text → canonical enum value)
# ===========================================================================

BRANCH_ALIASES: dict[str, str] = {
    # Canonical values (1:1)
    "marketing": "marketing", "beratung": "beratung", "it": "it",
    "finanzen": "finanzen", "handel": "handel", "bildung": "bildung",
    "verwaltung": "verwaltung", "gesundheit": "gesundheit", "bau": "bau",
    "medien": "medien", "industrie": "industrie", "logistik": "logistik",
    "gastronomie": "gastronomie",
    # Handwerk / Bau
    "handwerk": "bau", "bauwesen": "bau", "schreinerei": "bau",
    "tischlerei": "bau", "malerbetrieb": "bau", "elektrik": "bau",
    "sanitär": "bau", "architektur": "bau", "ingenieurbüro": "bau",
    "dachdecker": "bau", "zimmerer": "bau", "installateur": "bau",
    # Marketing
    "werbung": "marketing", "kommunikation": "marketing", "pr": "marketing",
    "public relations": "marketing", "agentur": "marketing",
    "werbeagentur": "marketing", "medienagentur": "marketing",
    # Beratung
    "consulting": "beratung", "unternehmensberatung": "beratung",
    "managementberatung": "beratung", "steuerberatung": "beratung",
    "coaching": "beratung", "dienstleistung": "beratung",
    "dienstleistungen": "beratung",
    # IT
    "software": "it", "tech": "it", "informatik": "it",
    "webentwicklung": "it", "saas": "it", "systemhaus": "it",
    "webdesign": "it", "programmierung": "it", "softwareentwicklung": "it",
    # Finanzen
    "bank": "finanzen", "versicherung": "finanzen",
    "finanzberatung": "finanzen", "wirtschaftsprüfung": "finanzen",
    "vermögensverwaltung": "finanzen", "versicherungsmakler": "finanzen",
    # Handel
    "einzelhandel": "handel", "e-commerce": "handel",
    "online-handel": "handel", "großhandel": "handel", "onlineshop": "handel",
    # Bildung
    "schule": "bildung", "universität": "bildung",
    "weiterbildung": "bildung", "sprachschule": "bildung", "nachhilfe": "bildung",
    # Verwaltung
    "behörde": "verwaltung", "öffentlicher dienst": "verwaltung",
    "kommune": "verwaltung", "verband": "verwaltung", "stiftung": "verwaltung",
    # Gesundheit
    "arztpraxis": "gesundheit", "klinik": "gesundheit",
    "pflege": "gesundheit", "apotheke": "gesundheit",
    "pflegedienst": "gesundheit", "therapie": "gesundheit",
    # Medien
    "verlag": "medien", "film": "medien", "fernsehen": "medien",
    "journalismus": "medien", "designstudio": "medien",
    "filmproduktion": "medien", "kreativwirtschaft": "medien",
    # Industrie
    "produktion": "industrie", "fertigung": "industrie",
    "maschinenbau": "industrie", "automotive": "industrie",
    "zulieferer": "industrie",
    # Logistik
    "spedition": "logistik", "transport": "logistik",
    "lager": "logistik", "kurierdienst": "logistik", "lagerhaltung": "logistik",
    # Gastronomie
    "restaurant": "gastronomie", "hotel": "gastronomie",
    "catering": "gastronomie", "café": "gastronomie",
    "tourismus": "gastronomie", "hotellerie": "gastronomie",
}


# ===========================================================================
# Company Size Aliases
# ===========================================================================

SIZE_ALIASES: dict[str, str] = {
    "1": "1", "2–10": "2–10", "2-10": "2–10",
    "11–100": "11–100", "11-100": "11–100",
    # German free-text
    "solo": "1", "allein": "1", "selbstständig": "1",
    "freelancer": "1", "einzelunternehmer": "1", "freiberufler": "1",
    "klein": "2–10", "kleines team": "2–10",
    "mittelständisch": "11–100", "mittelstand": "11–100", "kmu": "11–100",
}


def _normalize_size_from_number(n: int) -> str:
    if n == 1:
        return "1"
    if 2 <= n <= 10:
        return "2–10"
    # 11+ → cap at KMU maximum
    return "11–100"


# ===========================================================================
# City → Bundesland Code Mapping
# ===========================================================================

CITY_TO_BUNDESLAND: dict[str, str] = {
    # DE
    "münchen": "by", "nürnberg": "by", "augsburg": "by", "regensburg": "by",
    "würzburg": "by", "ingolstadt": "by",
    "stuttgart": "bw", "karlsruhe": "bw", "freiburg": "bw",
    "mannheim": "bw", "heidelberg": "bw", "ulm": "bw",
    "berlin": "be",
    "hamburg": "hh",
    "bremen": "hb",
    "frankfurt": "he", "wiesbaden": "he", "darmstadt": "he", "kassel": "he",
    "köln": "nw", "düsseldorf": "nw", "dortmund": "nw", "essen": "nw",
    "bonn": "nw", "münster": "nw", "bielefeld": "nw", "aachen": "nw",
    "hannover": "ni", "braunschweig": "ni", "osnabrück": "ni",
    "oldenburg": "ni", "göttingen": "ni",
    "dresden": "sn", "leipzig": "sn", "chemnitz": "sn",
    "kiel": "sh", "lübeck": "sh", "flensburg": "sh",
    "mainz": "rp", "koblenz": "rp", "trier": "rp",
    "saarbrücken": "sl",
    "potsdam": "bb", "cottbus": "bb",
    "schwerin": "mv", "rostock": "mv",
    "erfurt": "th", "jena": "th", "weimar": "th",
    "magdeburg": "st", "halle": "st",
    # AT
    "wien": "wi", "graz": "stm", "linz": "ooe", "salzburg": "sbg",
    "innsbruck": "tir", "klagenfurt": "ktn", "bregenz": "vbg",
    "st. pölten": "noe", "eisenstadt": "bgl",
    # CH
    "zürich": "zh", "bern": "be_ch", "basel": "bs", "genf": "ge",
    "lausanne": "vd", "luzern": "lu", "st. gallen": "sg",
    "winterthur": "zh", "lugano": "ti",
    # GB
    "london": "eng", "manchester": "eng", "birmingham": "eng",
    "liverpool": "eng", "bristol": "eng", "leeds": "eng",
    "edinburgh": "sco", "glasgow": "sco",
    "cardiff": "wal", "swansea": "wal",
    "belfast": "nir",
}

# Also map full Bundesland names → codes
_BUNDESLAND_NAME_TO_CODE: dict[str, str] = {
    v.lower(): k for k, v in BUNDESLAND_LABELS.items()
}


# ===========================================================================
# Country Aliases (chat free-text → ISO code)
# ===========================================================================

COUNTRY_ALIASES: dict[str, str] = {
    "deutschland": "DE", "germany": "DE", "de": "DE", "deutsch": "DE",
    "österreich": "AT", "austria": "AT", "at": "AT",
    "schweiz": "CH", "switzerland": "CH", "ch": "CH",
    "uk": "GB", "england": "GB", "großbritannien": "GB",
    "vereinigtes königreich": "GB", "united kingdom": "GB", "gb": "GB",
    "frankreich": "FR", "france": "FR", "fr": "FR",
    "italien": "IT", "italy": "IT", "it_country": "IT",
    "spanien": "ES", "spain": "ES", "es": "ES",
    "niederlande": "NL", "netherlands": "NL", "nl": "NL", "holland": "NL",
    "belgien": "BE", "belgium": "BE",
    "irland": "IE", "ireland": "IE",
    "polen": "PL", "poland": "PL",
    "schweden": "SE", "sweden": "SE",
    "dänemark": "DK", "denmark": "DK",
    "finnland": "FI", "finland": "FI",
    "portugal": "PT",
    "tschechien": "CZ", "czech republic": "CZ",
    "griechenland": "GR", "greece": "GR",
    "ungarn": "HU", "hungary": "HU",
    "rumänien": "RO", "romania": "RO",
    "norwegen": "NO", "norway": "NO",
    "island": "IS", "iceland": "IS",
    "liechtenstein": "LI",
}


# ===========================================================================
# Normalizer Functions
# ===========================================================================

def normalize_field(field_name: str, raw_value: Any, collected: dict, report_type: str = "r1") -> NormResult:
    """
    Normalize a single extracted field value.

    Returns NormResult with:
    - confidence "high": value is correct, store immediately
    - confidence "medium": plausible but ask for confirmation
    - confidence "low": cannot determine, do NOT store
    """
    registry = get_registry_for_report(report_type)
    enum_values = get_enum_values_for_report(report_type)

    reg = registry.get(field_name)
    if not reg:
        log.warning("[CHAT-NORM] Unknown field: %s (report_type=%s)", field_name, report_type)
        return NormResult(None, "low", True)

    # 1. Multi-fields: ensure list
    if reg["type"] == "multi" and isinstance(raw_value, str):
        raw_value = [raw_value]

    # 2. Strategy-specific: s3_prioritaeten max 3
    if field_name == "s3_prioritaeten":
        if isinstance(raw_value, str):
            raw_value = [raw_value]
        if isinstance(raw_value, list) and len(raw_value) > 3:
            raw_value = raw_value[:3]
        allowed = enum_values.get(field_name, [])
        if isinstance(raw_value, list) and allowed:
            raw_value = [v for v in raw_value if v in allowed]
        return NormResult(raw_value, "high", False) if raw_value else NormResult(None, "low", True)

    # 3. Strategy-specific: s5_software (list → comma string)
    if field_name == "s5_software":
        if isinstance(raw_value, list):
            raw_value = ", ".join(str(v) for v in raw_value)
        cleaned = str(raw_value).strip()
        return NormResult(cleaned, "high", False) if cleaned else NormResult(None, "low", True)

    # 4. R1-specific special normalizers
    if field_name == "branche":
        return _normalize_branche(raw_value)

    if field_name == "unternehmensgroesse":
        return _normalize_size(raw_value)

    if field_name == "bundesland":
        return _normalize_bundesland(raw_value, collected)

    if field_name == "country":
        return _normalize_country(raw_value)

    if field_name == "selbststaendig":
        return _normalize_selbststaendig(raw_value)

    # 5. Generic enum check
    if reg["type"] == "enum":
        allowed = enum_values.get(field_name, [])
        val = str(raw_value).strip()
        if val in allowed:
            return NormResult(val, "high", False)
        # Case-insensitive match
        val_lower = val.lower()
        for a in allowed:
            if a.lower() == val_lower:
                return NormResult(a, "high", False)
        return NormResult(None, "low", True)

    # 4. Free text
    if reg["type"] == "text":
        cleaned = str(raw_value).strip()
        if len(cleaned) < 3:
            return NormResult(None, "low", True)
        return NormResult(cleaned, "high", False)

    # 5. Bool
    if reg["type"] == "bool":
        return NormResult(bool(raw_value), "high", False)

    # 6. Slider
    if reg["type"] == "slider":
        try:
            slider_val = int(raw_value)
            mn = int(reg.get("min", 1))
            mx = int(reg.get("max", 10))
            slider_val = max(mn, min(slider_val, mx))
            return NormResult(slider_val, "high", False)
        except (ValueError, TypeError):
            return NormResult(None, "low", True)

    # 7. Multi — validate each element
    if reg["type"] == "multi":
        if not isinstance(raw_value, list):
            raw_value = [raw_value]
        return NormResult(raw_value, "high", False)

    return NormResult(raw_value, "medium", True)


# ---------------------------------------------------------------------------
# Specific normalizers
# ---------------------------------------------------------------------------

def _normalize_branche(raw: Any) -> NormResult:
    key = str(raw).lower().strip()
    # Direct alias match
    if key in BRANCH_ALIASES:
        return NormResult(BRANCH_ALIASES[key], "high", False)
    # Partial match: check if alias is contained in input or vice versa
    for alias, canonical in BRANCH_ALIASES.items():
        if len(alias) >= 4 and (alias in key or key in alias):
            return NormResult(canonical, "medium", True)
    return NormResult(None, "low", True)


def _normalize_size(raw: Any) -> NormResult:
    key = str(raw).strip()
    # Direct alias match
    if key in SIZE_ALIASES:
        return NormResult(SIZE_ALIASES[key], "high", False)
    # Case-insensitive alias
    key_lower = key.lower()
    if key_lower in SIZE_ALIASES:
        return NormResult(SIZE_ALIASES[key_lower], "high", False)
    # Extract number
    numbers = re.findall(r"\d+", str(raw))
    if numbers:
        return NormResult(_normalize_size_from_number(int(numbers[0])), "high", False)
    return NormResult(None, "low", True)


def _normalize_bundesland(raw: Any, collected: dict) -> NormResult:
    val = str(raw).strip()
    val_lower = val.lower()

    # Direct code match
    if val_lower in ALL_BUNDESLAND_CODES:
        return NormResult(val_lower, "high", False)

    # Full name → code
    if val_lower in _BUNDESLAND_NAME_TO_CODE:
        return NormResult(_BUNDESLAND_NAME_TO_CODE[val_lower], "high", False)

    # City → code
    if val_lower in CITY_TO_BUNDESLAND:
        return NormResult(CITY_TO_BUNDESLAND[val_lower], "high", False)

    # If country is known, validate against that country's codes
    country = collected.get("country")
    if country and country in BUNDESLAND_VALUES:
        valid_codes = BUNDESLAND_VALUES[country]
        if val_lower in valid_codes:
            return NormResult(val_lower, "high", False)

    return NormResult(None, "medium", True)


def _normalize_country(raw: Any) -> NormResult:
    val = str(raw).strip()
    # Direct match (ISO code)
    val_upper = val.upper()
    all_countries = set(ENUM_VALUES.get("country", []))
    if val_upper in all_countries:
        return NormResult(val_upper, "high", False)
    # Alias match
    val_lower = val.lower()
    if val_lower in COUNTRY_ALIASES:
        return NormResult(COUNTRY_ALIASES[val_lower], "high", False)
    return NormResult(None, "low", True)


def _normalize_selbststaendig(raw: Any) -> NormResult:
    val = str(raw).strip().lower()
    allowed = ENUM_VALUES["selbststaendig"]
    if val in allowed:
        return NormResult(val, "high", False)
    # Common aliases
    aliases = {
        "ja": "freiberufler", "yes": "freiberufler",
        "freiberuflich": "freiberufler", "selbstständig": "freiberufler",
        "freelancer": "freiberufler",
        "gmbh": "kapitalgesellschaft", "ug": "kapitalgesellschaft",
        "gewerbe": "einzelunternehmer",
    }
    if val in aliases:
        return NormResult(aliases[val], "high", False)
    return NormResult(None, "medium", True)


# ===========================================================================
# Helper: get missing / next fields
# ===========================================================================

def get_missing_fields(
    collected: dict, section_index: int, report_type: str = "r1",
) -> tuple[list[str], list[str]]:
    """
    Get missing required and optional fields for a given section.
    Returns (missing_required, missing_optional).
    Respects conditional logic.
    """
    sections = get_sections_for_report(report_type)
    registry = get_registry_for_report(report_type)
    section = sections[section_index]
    missing_required: list[str] = []
    missing_optional: list[str] = []
    fields: list[str] = section["fields"]  # type: ignore[assignment]

    for field_name in fields:
        if field_name in collected:
            continue
        if not is_field_visible(field_name, collected):
            continue
        reg = registry.get(field_name)
        if not reg:
            continue
        if reg.get("skip_in_chat"):
            continue
        if reg["required"]:
            missing_required.append(field_name)
        else:
            missing_optional.append(field_name)

    return missing_required, missing_optional


def get_next_fields(
    collected: dict, section_index: int, max_fields: int = 3, report_type: str = "r1",
) -> list[str]:
    """Get the next fields to ask about (max 3 at a time)."""
    missing_req, missing_opt = get_missing_fields(collected, section_index, report_type)
    next_fields = missing_req[:max_fields]
    remaining = max_fields - len(next_fields)
    if remaining > 0:
        next_fields.extend(missing_opt[:remaining])
    return next_fields


def is_section_complete(
    collected: dict, section_index: int, report_type: str = "r1",
) -> bool:
    """Check if all required fields in a section are collected."""
    missing_req, _ = get_missing_fields(collected, section_index, report_type)
    return len(missing_req) == 0


def calculate_progress(collected: dict, report_type: str = "r1") -> int:
    """Calculate overall progress percentage (0-100)."""
    registry = get_registry_for_report(report_type)
    total = 0
    filled = 0
    for field_name, reg in registry.items():
        if not reg["required"]:
            continue
        if reg.get("skip_in_chat"):
            continue
        if not is_field_visible(field_name, collected):
            continue
        total += 1
        if field_name in collected:
            filled += 1
    if total == 0:
        return 0
    return int(filled / total * 100)
