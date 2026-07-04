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
# KIS-1161: Freitext-Quality-Validator
#
# Rejects degenerate answers on freetext ("text" / chat_mode="FT") fields so
# the chat re-asks instead of silently incrementing progress with placeholder
# content. Does NOT fire on enum / bool / slider / multi — those handle their
# own canonicalisation, and short tokens like "ja", "nein" or "5" are valid
# for those types.
# ===========================================================================

# Pointer markers — canonical user-typed spellings. Compared after both
# sides are normalised by ``_normalise_for_marker`` (lower-case, strip
# whitespace + trailing ASCII punctuation). The pre-computed
# ``_MARKERS_NORMALISED`` set is what membership checks actually use.
_LOW_QUALITY_TEXT_MARKERS: frozenset[str] = frozenset({
    "siehe oben",
    "s.o.",
    "s. o.",
    "wie oben",
    "dito",
    "idem",
    "ebenso",
})


def _normalise_for_marker(text: str) -> str:
    """Lower-case, strip whitespace, then strip trailing ASCII punctuation.

    Used on both marker definitions and incoming messages so dot-bearing
    abbreviations like "s.o." compare equal to "S.O." or "s.o" after a
    user's stray comma.
    """
    return text.strip().lower().rstrip(" .!?,;:")


_MARKERS_NORMALISED: frozenset[str] = frozenset(
    _normalise_for_marker(m) for m in _LOW_QUALITY_TEXT_MARKERS
)


def is_pointer_phrase(message: str) -> bool:
    """True when *message* (lower + trailing punctuation stripped) exactly
    matches a pointer marker like "siehe oben" / "s.o." / "dito".

    Used as a pre-Haiku guard in routes/chat.py so the extractor never gets a
    chance to silently resolve the pointer against the conversation context
    and substitute substantive content from an earlier turn. The normalizer
    sees the raw value too, so this acts as defense-in-depth — but the
    normalizer alone cannot stop Haiku from resolving the pointer first.
    """
    if not message:
        return False
    normalised = _normalise_for_marker(str(message))
    if not normalised:
        return False
    return normalised in _MARKERS_NORMALISED


def is_low_quality_text(raw: str, min_words: int = 3) -> bool:
    """Return True if *raw* should be rejected as a substantive freetext answer.

    A value is "low quality" when it either
      1. exactly matches one of ``_LOW_QUALITY_TEXT_MARKERS`` (case-insensitive,
         after stripping trailing punctuation/whitespace), or
      2. has fewer than ``min_words`` whitespace-separated tokens.

    Exact-match (no prefix-match) on purpose — sentences that *start* with a
    pointer phrase but continue substantively (e.g. "Dito wie bei X, plus …")
    must pass through. The word-count rule still catches stubby variants.
    """
    if raw is None:
        return True
    cleaned = str(raw).strip()
    if not cleaned:
        return True

    normalised = _normalise_for_marker(cleaned)
    if normalised in _MARKERS_NORMALISED:
        return True

    if len(cleaned.split()) < min_words:
        return True
    return False


# ===========================================================================
# KIS-1136 rest-fix (Option 6): strategy freetext fields that must be OMITTED
# (absent from `collected`/`answers`) on skip signals, never written as "".
# Writing an empty string would bypass the `_chat_partially_surveyed` marker
# (routes/chat.py `field not in answers` check) and feed a meaningless empty
# value into the report pipeline. Mirrors the force-default skip in
# routes/chat.py (_FORCE_DEFAULT_SKIP) so both safeguards stay in sync.
# ===========================================================================

_FT_OMIT_ON_SKIP: frozenset[str] = frozenset({
    "vision_3_jahre",
    "strategische_ziele",
    "ki_guardrails",
    "geschaeftsmodell_evolution",
})


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
    # KIS-1235-P3: Wirtschafts-Kontext für präzisere Business Cases
    "projekte_pro_monat":   {"type": "enum",  "required": False, "section": 0, "chat_mode": "QR"},
    "durchschnittshonorar": {"type": "enum",  "required": False, "section": 0, "chat_mode": "QR"},
    # --- Section 1: Organisation & Datenlage ---
    "zielgruppen":          {"type": "multi", "required": False, "section": 1, "chat_mode": "QR"},
    "it_infrastruktur":     {"type": "enum",  "required": False, "section": 1, "chat_mode": "QR"},
    "interne_ki_kompetenzen": {"type": "enum", "required": False, "section": 1, "chat_mode": "QR"},
    "datenquellen":         {"type": "multi", "required": False, "section": 1, "chat_mode": "QR"},
    # --- Section 2: Digitalisierung & KI-Status ---
    "digitalisierungsgrad": {"type": "slider", "required": True,  "section": 2, "chat_mode": "QR", "min": 1, "max": 10},
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
    # KIS-1235-P3: konkrete Zeitfresser als Quick-Win-Anker
    "top_zeitfresser":      {"type": "text",  "required": False, "section": 3, "chat_mode": "FT"},
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
    "risikofreude":         {"type": "slider", "required": False, "section": 7, "chat_mode": "QR", "min": 1, "max": 5},
}


# ===========================================================================
# Sections (8 conversation sections)
# ===========================================================================

SECTIONS = [
    {
        "index": 0,
        "name": "Ihr Unternehmen",
        "fields": ["branche", "unternehmensgroesse", "selbststaendig",
                    "country", "bundesland", "hauptleistung", "jahresumsatz",
                    # KIS-1240: durchschnittshonorar wird nicht mehr GEFRAGT
                    # (Registry-Eintrag bleibt für Alt-Daten) — Ableitung aus
                    # Jahresumsatz × Projekte/Monat in gpt_analyze.
                    "projekte_pro_monat"],
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
                    "zeitersparnis_prioritaet", "top_zeitfresser",
                    "geschaeftsmodell_evolution"],
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
    "s5_software":        {"type": "multi", "required": False, "section": 0, "chat_mode": "QR"},
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
# User Profile Detection (for context-aware UX)
# ===========================================================================

def compute_user_profile(collected: dict) -> dict:
    """
    Derive user profile flags from collected fields.

    Returns dict with:
      - is_solo: True if unternehmensgroesse == "1"
      - is_small_team: True if unternehmensgroesse == "2–10"
      - is_kmu: True if unternehmensgroesse == "11–100"
      - is_expert: True if 2+ expert signals detected
      - is_intermediate: True if exactly 1 expert signal
      - expert_signals: int count (0-4)

    Used by chat.py to filter QR options, adapt labels, and skip
    irrelevant fields.
    """
    size = collected.get("unternehmensgroesse")
    is_solo = size == "1"
    is_small_team = size in ("2–10", "2-10")
    is_kmu = size == "11–100" or size == "11-100"

    expert_signals = 0

    # Signal (a): ki_einsatz has 3+ active areas
    ki_einsatz = collected.get("ki_einsatz", [])
    if isinstance(ki_einsatz, list):
        active = [x for x in ki_einsatz if x != "noch_keine"]
        if len(active) >= 3:
            expert_signals += 1

    # Signal (b): ki_kompetenz is high
    if collected.get("ki_kompetenz") in ("hoch", "sehr_hoch"):
        expert_signals += 1

    # Signal (c): hauptleistung mentions KI/API/LLM
    hl = str(collected.get("hauptleistung", "")).lower()
    ki_keywords = ("ki", " ai ", "api", "llm", "machine learning",
                   "automation", "künstliche intelligenz", "deep learning",
                   "prompt", "chatgpt", "anthropic", "openai")
    if any(kw in hl for kw in ki_keywords):
        expert_signals += 1

    # Signal (d): digitalisierungsgrad >= 8
    dg = collected.get("digitalisierungsgrad")
    if isinstance(dg, (int, float)) and dg >= 8:
        expert_signals += 1

    return {
        "is_solo": is_solo,
        "is_small_team": is_small_team,
        "is_kmu": is_kmu,
        "is_expert": expert_signals >= 2,
        "is_intermediate": expert_signals == 1,
        "expert_signals": expert_signals,
    }
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
    # Section 6: Compliance fields
    # FIX-KIS-1153: technische_massnahmen, meldewege and loeschregeln apply
    # to every branche under DSGVO (Art. 32 / 33 / 17) — gating them on
    # regulated branches left non-regulated users with uncomputed security
    # scores (KIS-1153 Solo Beratung hit 40/100 because these fields never
    # reached the scorer). Only the Datenschutz-Folgenabschätzung (Art. 35)
    # remains regulated-only, as it targets Hoch-Risiko-Verarbeitungen.
    "folgenabschaetzung": {
        "show_if": {"branche": ["gesundheit", "finanzen", "verwaltung"]},
        "hide_action": "skip",
    },
    "regulierte_branche": {
        "show_if": {"branche": ["gesundheit", "finanzen", "verwaltung"]},
        "hide_action": "skip",
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
    # KIS-1242: fehlte — Chip-Klicks wurden als low confidence verworfen,
    # die Frage wiederholte sich endlos (3. Testlauf-Abbruch 04.07.).
    "projekte_pro_monat": ["unter_2", "2_5", "6_10", "ueber_10", "keine_angabe"],
    # Nur für Alt-Daten-Normalisierung — die Frage wird nicht mehr gestellt.
    "durchschnittshonorar": ["unter_1k", "1k_5k", "5k_20k", "ueber_20k", "keine_angabe"],
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


# ---------------------------------------------------------------------------
# KIS-1124 Testrun 6 Fix 1: Synonym mapping for enum fields
# Maps free-text user answers to canonical enum values.
# ---------------------------------------------------------------------------

_ENUM_SYNONYMS: dict[str, dict[str, str]] = {
    "marktposition": {
        "im aufbau": "nachzuegler",
        "noch im aufbau": "nachzuegler",
        "aufbau": "nachzuegler",
        "testphase": "nachzuegler",
        "gerade erst gestartet": "nachzuegler",
        "gerade erst angefangen": "nachzuegler",
        "ganz am anfang": "nachzuegler",
        "neu am markt": "nachzuegler",
        "start": "nachzuegler",
        "startup": "nachzuegler",
        "anfang": "nachzuegler",
        "etabliert": "oberes_drittel",
        "gut aufgestellt": "oberes_drittel",
        "stark": "oberes_drittel",
        "vorreiter": "marktfuehrer",
        "pionier": "marktfuehrer",
        "marktführer": "marktfuehrer",
        "nummer eins": "marktfuehrer",
        "führend": "marktfuehrer",
        "durchschnitt": "mittelfeld",
        "mittel": "mittelfeld",
        "normal": "mittelfeld",
        "keine ahnung": "unsicher",
        "weiß nicht": "unsicher",
        "schwer zu sagen": "unsicher",
        "kann ich nicht sagen": "unsicher",
        "schwer einzuschätzen": "unsicher",
    },
    "benchmark_wettbewerb": {
        "manchmal": "selten",
        "gelegentlich": "selten",
        "ab und zu": "selten",
        "nicht wirklich": "nein",
        "nie": "nein",
        "gar nicht": "nein",
        "regelmäßig": "ja",
        "immer": "ja",
        "oft": "ja",
    },
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

    # 1. Multi-fields: ensure list (but DON'T split commas yet — special cases handle that)
    if reg["type"] == "multi" and isinstance(raw_value, str) and "," not in raw_value:
        raw_value = [raw_value]

    # 2. Strategy-specific: s3_prioritaeten max 3
    if field_name == "s3_prioritaeten":
        if isinstance(raw_value, str):
            # Handle comma-separated string: "Kosten senken, Umsatz steigern"
            if "," in raw_value:
                raw_value = [v.strip() for v in raw_value.split(",") if v.strip()]
            else:
                raw_value = [raw_value]
        if isinstance(raw_value, list) and len(raw_value) > 3:
            raw_value = raw_value[:3]
        allowed = enum_values.get(field_name, [])
        if isinstance(raw_value, list) and allowed:
            # Case-insensitive matching against allowed values
            allowed_lower = {v.lower(): v for v in allowed}
            raw_value = [allowed_lower[v.lower()] for v in raw_value if v.lower() in allowed_lower]
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

    # 5. Field-specific synonym mapping (before generic enum check)
    if field_name in _ENUM_SYNONYMS:
        val_lower = str(raw_value).strip().lower()
        synonyms = _ENUM_SYNONYMS[field_name]
        # Exact match first
        if val_lower in synonyms:
            return NormResult(synonyms[val_lower], "high", False)
        # Substring match (e.g. "im aufbau" matches "aufbau")
        for synonym, canonical in synonyms.items():
            if synonym in val_lower or val_lower in synonym:
                return NormResult(canonical, "high", False)

    # 6. Generic enum check
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
        # "keine_angabe" is a valid skip for optional text fields
        if cleaned.lower() in ("keine_angabe", "keine angabe"):
            # KIS-1136 rest-fix: for strategy FT fields the skip must OMIT
            # the field (not write ""), so the partially-surveyed marker in
            # routes/chat.py sees `field not in answers` and shortens the
            # report section cleanly.
            if field_name in _FT_OMIT_ON_SKIP:
                return NormResult(None, "low", True)
            return NormResult("", "high", False)
        if len(cleaned) < 3:
            return NormResult(None, "low", True)
        # KIS-1161: reject "siehe oben" / "dito" / <3-word stubs so the chat
        # re-asks instead of silently accepting a non-answer. Only freetext
        # fields (chat_mode="FT") — enums/bools/sliders are unaffected.
        if reg.get("chat_mode") == "FT" and is_low_quality_text(cleaned):
            log.info(
                "[CHAT-NORM] Low-quality freetext for %s: %r — re-ask",
                field_name, cleaned,
            )
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

    # 7. Multi — validate each element, handle comma-separated strings
    if reg["type"] == "multi":
        if isinstance(raw_value, str):
            if "," in raw_value:
                raw_value = [v.strip() for v in raw_value.split(",") if v.strip()]
            else:
                raw_value = [raw_value]
        allowed = enum_values.get(field_name, [])
        if isinstance(raw_value, list) and allowed:
            allowed_lower = {v.lower(): v for v in allowed}
            raw_value = [allowed_lower.get(v.lower(), v) for v in raw_value]
        return NormResult(raw_value, "high", False) if raw_value else NormResult(None, "low", True)

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
    fields: list[str] = section["fields"]

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
    collected: dict, section_index: int, max_fields: int = 1, report_type: str = "r1",
) -> list[str]:
    """Get the next field(s) to ask about. Default: 1 field for focused conversation."""
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


# Human-readable field labels (field_name → short German label)
_FIELD_LABELS: dict[str, str] = {
    "branche": "Branche",
    "unternehmensgroesse": "Unternehmensgröße",
    "selbststaendig": "Unternehmensform",
    "country": "Land",
    "bundesland": "Bundesland",
    "hauptleistung": "Hauptdienstleistung",
    "jahresumsatz": "Jahresumsatz",
    "projekte_pro_monat": "Projekte pro Monat",
    # KIS-1242: vom Registry-Kontrakt-Test gefundene Label-Lücken
    "top_zeitfresser": "Top-Zeitfresser",
    "datenschutz": "Datenschutz-Einwilligung",
    "zielgruppen": "Zielgruppen",
    "it_infrastruktur": "IT-Infrastruktur",
    "interne_ki_kompetenzen": "KI-Kompetenzen",
    "datenquellen": "Datenquellen",
    "digitalisierungsgrad": "Digitalisierungsgrad",
    "prozesse_papierlos": "Papierlose Prozesse",
    "automatisierungsgrad": "Automatisierungsgrad",
    "ki_einsatz": "KI-Einsatzbereiche",
    "ki_kompetenz": "KI-Kompetenz im Team",
    "ki_ziele": "KI-Ziele",
    "ki_projekte": "Bestehende KI-Projekte",
    "anwendungsfaelle": "KI-Anwendungsfälle",
    "zeitersparnis_prioritaet": "Zeitersparnis-Priorität",
    "pilot_bereich": "Pilotprojekt-Bereich",
    "geschaeftsmodell_evolution": "Geschäftsmodell-Evolution",
    "vision_3_jahre": "3-Jahres-Vision",
    "strategische_ziele": "Strategische Ziele",
    "ki_guardrails": "KI-Guardrails",
    "massnahmen_komplexitaet": "Aufwand KI-Einführung",
    "roadmap_vorhanden": "KI-Roadmap",
    "governance_richtlinien": "Governance-Richtlinien",
    "change_management": "Veränderungsbereitschaft",
    "zeitbudget": "Zeitbudget für KI",
    "vorhandene_tools": "Vorhandene Tools",
    "trainings_interessen": "Trainings-Interessen",
    "vision_prioritaet": "Strategischer Hebel",
    "innovationsprozess": "Innovationsprozess",
    "datenschutzbeauftragter": "Datenschutzbeauftragter",
    "technische_massnahmen": "Technische Schutzmaßnahmen",
    "folgenabschaetzung": "Datenschutz-Folgenabschätzung",
    "meldewege": "Meldewege Sicherheitsvorfälle",
    "loeschregeln": "Löschrichtlinien",
    "ai_act_kenntnis": "EU AI Act Kenntnis",
    "regulierte_branche": "Regulierte Branche",
    "ki_hemmnisse": "KI-Hemmnisse",
    "bisherige_foerdermittel": "Bisherige Fördermittel",
    "interesse_foerderung": "Interesse Förderung",
    "erfahrung_beratung": "Beratungserfahrung",
    "investitionsbudget": "Investitionsbudget",
    "marktposition": "Marktposition",
    "benchmark_wettbewerb": "Wettbewerbs-Benchmark",
    "risikofreude": "Risikofreude",
    # Strategy fields
    "s1_budget": "KI-Budget",
    "s2_zeitrahmen": "Umsetzungszeitraum",
    "s3_prioritaeten": "KI-Prioritäten",
    "s4_engpass": "Größter Engpass",
    "s5_software": "Genutzte Software",
    "s5_vision": "KI-Vision",
    "s6_foerderinteresse": "Förderinteresse",
    "s7_entscheidung": "Entscheidungsstruktur",
    "s8_erfahrung": "KI-Erfahrung",
    "s9_ansatz": "Infrastruktur-Ansatz",
    "s10_datenschutz": "Datenschutz-Priorität",
    "wettbewerber_anzahl": "Wettbewerber-Anzahl",
    "kundenbindung_typ": "Kundenbindung",
    "datenreife": "Datenreife",
}


def get_field_label(field_name: str, report_type: str = "r1") -> str:
    """Return a human-readable German label for a field name.

    Uses the _FIELD_LABELS lookup. Falls back to title-cased field name.
    """
    label = _FIELD_LABELS.get(field_name)
    if label:
        return label
    # Fallback: "geschaeftsmodell_evolution" → "Geschaeftsmodell Evolution"
    return field_name.replace("_", " ").title()
