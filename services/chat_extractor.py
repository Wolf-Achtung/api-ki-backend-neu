# -*- coding: utf-8 -*-
"""
Phase 1: Field extraction via Claude Haiku with tool_use.

The extractor receives the user message + recent conversation context
and returns structured fields using a tool call. It never writes to DB
directly — results go through the normalizer first.
"""
from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model Config
# ---------------------------------------------------------------------------
EXTRACTOR_MODEL = os.getenv(
    "CHAT_EXTRACTOR_MODEL", "claude-haiku-4-5-20251001"
)

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
EXTRACTOR_SYSTEM_PROMPT = """\
Du bist ein Daten-Extractor für einen KI-Readiness-Fragebogen.
Analysiere die Nutzerantwort und extrahiere strukturierte Felder
mit dem Tool update_intake_fields.

REGELN:
1. Setze NUR Felder, die der Nutzer tatsächlich genannt hat.
2. Erfinde NIEMALS Werte.
3. Wenn unsicher, setze das Feld NICHT.
4. Extrahiere auch implizite Informationen:
   - "in München" → bundesland: "München" (wird extern normalisiert)
   - "8 Mitarbeiter" → unternehmensgroesse: "8" (wird extern normalisiert)
   - "Handwerksbetrieb" → branche: "Handwerk" (wird extern normalisiert)
5. Bei Freitextfeldern (hauptleistung): den Kern der Aussage
   in 1–3 Sätzen zusammenfassen.
6. Wenn der Nutzer eine Rückfrage stellt statt zu antworten,
   rufe das Tool NICHT auf.

Aktuell fehlende Felder: {missing_fields}
Bereits erfasst: {collected_fields}"""

# ---------------------------------------------------------------------------
# Tool Definition — ALL fields (Sektionen 0–7)
# ---------------------------------------------------------------------------
EXTRACTOR_TOOL: dict[str, Any] = {
    "name": "update_intake_fields",
    "description": (
        "Extrahiert strukturierte Felder aus der User-Nachricht. "
        "Nur Felder setzen, die der User tatsächlich genannt hat. "
        "Niemals Werte erfinden oder raten."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            # --- Sektion 0: Ihr Unternehmen ---
            "branche": {
                "type": "string",
                "description": "Branche des Unternehmens (z.B. bau, it, marketing, beratung, handel, gastronomie)",
            },
            "unternehmensgroesse": {
                "type": "string",
                "description": "Anzahl Mitarbeiter als Zahl oder Kategorie (z.B. '1', '8', '2-10', 'solo')",
            },
            "selbststaendig": {
                "type": "string",
                "description": "Unternehmensform bei Einzelperson: freiberufler, kapitalgesellschaft, einzelunternehmer, sonstiges",
            },
            "country": {
                "type": "string",
                "description": "Land als ISO-Code oder Name (z.B. DE, AT, CH, Deutschland, Österreich)",
            },
            "bundesland": {
                "type": "string",
                "description": "Bundesland, Kanton, Region oder Stadt (wird zu Bundesland-Code normalisiert)",
            },
            "hauptleistung": {
                "type": "string",
                "description": "Haupttätigkeit/Kernleistung des Unternehmens in 1–3 Sätzen",
            },
            "jahresumsatz": {
                "type": "string",
                "description": "Ungefährer Jahresumsatz (z.B. unter_100k, 100k_500k, 500k_2m, 2m_10m, ueber_10m)",
            },
            # --- Sektion 1: Organisation & Datenlage ---
            "zielgruppen": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Zielgruppen des Unternehmens (z.B. b2b, b2c, kmu, grossunternehmen, selbststaendige, oeffentliche_hand, privatpersonen, startups)",
            },
            "it_infrastruktur": {
                "type": "string",
                "description": "IT-Infrastruktur: cloud, on_premise, hybrid, unklar",
            },
            "interne_ki_kompetenzen": {
                "type": "string",
                "description": "Ob ein internes KI-/Digitalisierungsteam existiert: ja, nein, in_planung",
            },
            "datenquellen": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Verfügbare Datentypen (z.B. kundendaten, verkaufsdaten, produktionsdaten, personaldaten, marketingdaten, sonstige)",
            },
            # --- Sektion 2: Digitalisierung & KI-Status ---
            "digitalisierungsgrad": {
                "type": "integer",
                "description": "Digitalisierungsgrad 1–10 (1=sehr niedrig, 10=sehr hoch)",
            },
            "prozesse_papierlos": {
                "type": "string",
                "description": "Anteil papierloser Prozesse: 0-20, 21-50, 51-80, 81-100",
            },
            "automatisierungsgrad": {
                "type": "string",
                "description": "Automatisierungsgrad: sehr_niedrig, eher_niedrig, mittel, eher_hoch, sehr_hoch",
            },
            "ki_einsatz": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Bereiche mit KI-Einsatz (z.B. chatbots, marketing, vertrieb, datenanalyse, produktion, hr, andere, noch_keine)",
            },
            "ki_kompetenz": {
                "type": "string",
                "description": "KI-Kompetenz im Team: hoch, mittel, niedrig, keine",
            },
            # --- Sektion 3: Ziele & Use Cases ---
            "ki_ziele": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ziele mit KI (z.B. effizienz, automatisierung, neue_produkte, kundenservice, datenauswertung, kosten_senken, wettbewerbsfaehigkeit)",
            },
            "ki_projekte": {
                "type": "string",
                "description": "Freitext: bestehende KI-Tests, Tools oder Projekte (auch informell)",
            },
            "anwendungsfaelle": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Interessante Anwendungsfälle (z.B. chatbots, content_generation, datenanalyse, dokumentation, prozess_automation, personalisierung)",
            },
            "zeitersparnis_prioritaet": {
                "type": "string",
                "description": "Freitext: Wo frisst heute am meisten Zeit oder Nerven?",
            },
            "pilot_bereich": {
                "type": "string",
                "description": "Bester Bereich für Pilotprojekt: kundenservice, marketing, vertrieb, verwaltung, produktion, andere",
            },
            "geschaeftsmodell_evolution": {
                "type": "string",
                "description": "Freitext: Ideen wie KI das Geschäftsmodell verändern oder ergänzen könnte",
            },
            "vision_3_jahre": {
                "type": "string",
                "description": "Freitext: Wie soll das Unternehmen in 2–3 Jahren mit KI arbeiten?",
            },
            # --- Sektion 4: Strategie & Governance ---
            "strategische_ziele": {
                "type": "string",
                "description": "Freitext: Was soll KI in 6–12 Monaten konkret verbessern?",
            },
            "ki_guardrails": {
                "type": "string",
                "description": "Freitext: No-Gos oder sensible Themen beim KI-Einsatz",
            },
            "massnahmen_komplexitaet": {
                "type": "string",
                "description": "Aufwand für KI-Einführung: niedrig, mittel, hoch, unklar",
            },
            "roadmap_vorhanden": {
                "type": "string",
                "description": "KI-Roadmap/Strategie vorhanden: ja, teilweise, nein",
            },
            "governance_richtlinien": {
                "type": "string",
                "description": "KI-Governance-Richtlinien vorhanden: ja, teilweise, nein",
            },
            "change_management": {
                "type": "string",
                "description": "Veränderungsbereitschaft im Team: sehr_hoch, hoch, mittel, niedrig, sehr_niedrig",
            },
            # --- Sektion 5: Ressourcen & Umsetzung ---
            "zeitbudget": {
                "type": "string",
                "description": "Zeit pro Woche für KI-Projekte: unter_2, 2_5, 5_10, ueber_10",
            },
            "vorhandene_tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Bereits genutzte Systeme (z.B. crm, erp, projektmanagement, marketing_automation, buchhaltung, keine)",
            },
            "trainings_interessen": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Interessante KI-Trainingsthemen (z.B. prompt_engineering, llm_basics, datenqualitaet_governance, automatisierung, ethik_recht)",
            },
            "vision_prioritaet": {
                "type": "string",
                "description": "Wichtigster strategischer Hebel: gpt_services, kundenservice, datenprodukte, prozessautomation, marktfuehrerschaft, keine_angabe",
            },
            "innovationsprozess": {
                "type": "string",
                "description": "Wie entstehen Innovationen: innovationsteam, mitarbeitende, kunden, berater, zufall, unbekannt",
            },
            # --- Sektion 6: Recht & Datenschutz ---
            "datenschutzbeauftragter": {
                "type": "string",
                "description": "Datenschutzbeauftragter vorhanden: ja, nein, teilweise",
            },
            "technische_massnahmen": {
                "type": "string",
                "description": "Technische Schutzmaßnahmen: alle, teilweise, keine",
            },
            "folgenabschaetzung": {
                "type": "string",
                "description": "Datenschutz-Folgenabschätzung: ja, nein, teilweise",
            },
            "meldewege": {
                "type": "string",
                "description": "Meldewege bei Sicherheitsvorfällen: ja, teilweise, nein",
            },
            "loeschregeln": {
                "type": "string",
                "description": "Löschrichtlinien: ja, teilweise, nein",
            },
            "ai_act_kenntnis": {
                "type": "string",
                "description": "Kenntnis EU AI Act: sehr_gut, gut, gehoert, unbekannt",
            },
            "regulierte_branche": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Regulierte Branche (z.B. gesundheit, finanzen, oeffentlich, recht, vertraulich_nda, keine)",
            },
            "ki_hemmnisse": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Hemmnisse beim KI-Einsatz (z.B. rechtsunsicherheit, datenschutz, knowhow, budget, teamakzeptanz, zeitmangel, keine)",
            },
            # --- Sektion 7: Förderung & Investition ---
            "bisherige_foerdermittel": {
                "type": "string",
                "description": "Bereits Fördermittel erhalten: ja, nein",
            },
            "interesse_foerderung": {
                "type": "string",
                "description": "Interesse an Fördermöglichkeiten: ja, nein, unklar",
            },
            "erfahrung_beratung": {
                "type": "string",
                "description": "Bisherige Beratung zu Digitalisierung/KI: ja, nein, unklar",
            },
            "investitionsbudget": {
                "type": "string",
                "description": "Budget für KI nächstes Jahr: unter_2000, 2000_10000, 10000_50000, ueber_50000, unklar",
            },
            "marktposition": {
                "type": "string",
                "description": "Marktposition: marktfuehrer, oberes_drittel, mittelfeld, nachzuegler, unsicher",
            },
            "benchmark_wettbewerb": {
                "type": "string",
                "description": "Vergleich mit Wettbewerbern: ja, nein, selten",
            },
            "risikofreude": {
                "type": "integer",
                "description": "Risikofreude bei Innovation 1–5 (1=niedrig, 5=hoch)",
            },
        },
        "required": [],  # CRITICAL: extractor only sets actually mentioned fields
    },
}

# ---------------------------------------------------------------------------
# Tool Definition — Strategy (Report 3, 14 fields)
# ---------------------------------------------------------------------------
EXTRACTOR_TOOL_STRATEGY: dict[str, Any] = {
    "name": "update_intake_fields",
    "description": (
        "Extrahiert Strategy-Felder aus der Nutzerantwort. "
        "Nur Felder setzen, die der User tatsächlich genannt hat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "s1_budget": {
                "type": "string",
                "description": "KI-Budget nächste 12 Monate: unter_2000, 2000_10000, 10000_50000, ueber_50000, unklar",
            },
            "s2_zeitrahmen": {
                "type": "string",
                "description": "Umsetzungszeitraum: Sofort (1-3 Monate), Kurzfristig (3-6 Monate), Mittelfristig (6-12 Monate), Langfristig (12-18 Monate)",
            },
            "s3_prioritaeten": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Top 3 Prioritäten beim KI-Einsatz (max 3): Kosten senken, Umsatz steigern, Qualität verbessern, Geschwindigkeit erhöhen, Compliance sichern, Neue Geschäftsfelder, Fachkräftemangel kompensieren, Kundenerlebnis verbessern",
            },
            "s4_engpass": {
                "type": "string",
                "description": "Größter einzelner Engpass: Zu wenig Know-how, Kein Budget, Fehlende Daten, Widerstand im Team, Regulatorische Unsicherheit, Kein klarer Use Case, Andere",
            },
            "s5_software": {
                "type": "string",
                "description": "Kommagetrennte Liste aktuell genutzter Software und Tools im Tagesgeschäft",
            },
            "s5_vision": {
                "type": "string",
                "description": "Persönliche KI-Vision für das Unternehmen (Freitext)",
            },
            "s6_foerderinteresse": {
                "type": "string",
                "description": "Interesse an Fördermitteln: Ja, dringend / Ja, wenn passend / Nein, eigenes Budget / Weiß nicht",
            },
            "s7_entscheidung": {
                "type": "string",
                "description": "Entscheidungsstruktur: Entscheide allein / Brauche Vorlage für Geschäftsleitung / Muss Gesellschafter überzeugen / Muss Aufsichtsrat/Beirat informieren",
            },
            "s8_erfahrung": {
                "type": "string",
                "description": "Bisherige KI-Erfahrung: Noch keine, Experimentiert, Erste Tools im Einsatz, Fortgeschritten",
            },
            "s9_ansatz": {
                "type": "string",
                "description": "Bevorzugter Infrastruktur-Ansatz: Cloud-SaaS, On-Premise, Hybrid, Egal",
            },
            "s10_datenschutz": {
                "type": "string",
                "description": "Datenschutz-Priorität: Hoch, Mittel, Niedrig",
            },
            "wettbewerber_anzahl": {
                "type": "string",
                "description": "Anzahl direkter Wettbewerber: wenige, mehrere, viele, unklar",
            },
            "kundenbindung_typ": {
                "type": "string",
                "description": "Art der Kundenbeziehungen: einmalig, wiederkehrend, gemischt",
            },
            "datenreife": {
                "type": "string",
                "description": "Verfügbarkeit eigener Datenbestände: keine, basis, umfangreich, unklar",
            },
        },
        "required": [],
    },
}


def _get_tool_for_report(report_type: str) -> dict[str, Any]:
    """Select the right extractor tool schema for a report type."""
    if report_type == "strategy":
        return EXTRACTOR_TOOL_STRATEGY
    return EXTRACTOR_TOOL


# ---------------------------------------------------------------------------
# Async Anthropic Client (singleton)
# ---------------------------------------------------------------------------
_async_client = None


def _get_async_client():
    """Lazy-initialize async Anthropic client."""
    global _async_client
    if _async_client is not None:
        return _async_client

    try:
        import anthropic
    except ImportError:
        log.error("[CHAT-EXTRACT] anthropic SDK not installed")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("[CHAT-EXTRACT] ANTHROPIC_API_KEY not set")
        return None

    timeout = float(os.getenv("ANTHROPIC_TIMEOUT", "60"))
    _async_client = anthropic.AsyncAnthropic(
        api_key=api_key,
        timeout=timeout,
    )
    log.info("[CHAT-EXTRACT] AsyncAnthropic client initialized (model=%s)", EXTRACTOR_MODEL)
    return _async_client


# ---------------------------------------------------------------------------
# Main Extraction Function
# ---------------------------------------------------------------------------

async def extract_fields(
    user_message: str,
    conversation_context: list[dict],
    missing_fields: list[str],
    collected_fields: dict,
    report_type: str = "r1",
) -> dict:
    """
    Call Claude Haiku with tool_use to extract structured fields.

    Args:
        user_message: The current user message
        conversation_context: Last 6 messages (3 turns) for context
        missing_fields: Fields still needed
        collected_fields: Already collected field values

    Returns:
        Dict of extracted fields (may be empty if user asked a question).
    """
    client = _get_async_client()
    if client is None:
        log.error("[CHAT-EXTRACT] No async client available")
        return {}

    # Build messages: recent context + current message
    messages: list[dict] = []
    for turn in conversation_context[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    # Format system prompt with current state
    system = EXTRACTOR_SYSTEM_PROMPT.format(
        missing_fields=", ".join(missing_fields) if missing_fields else "keine",
        collected_fields=_format_collected(collected_fields),
    )

    try:
        response = await client.messages.create(
            model=EXTRACTOR_MODEL,
            max_tokens=500,
            system=system,
            messages=messages,
            tools=[_get_tool_for_report(report_type)],
            tool_choice={"type": "auto"},  # auto: no tool call if user asks question
        )

        # Extract tool result
        for block in response.content:
            if block.type == "tool_use" and block.name == "update_intake_fields":
                extracted: dict = block.input
                log.info(
                    "[CHAT-EXTRACT] Extracted %d fields: %s",
                    len(extracted),
                    list(extracted.keys()),
                )
                return extracted

        # No tool call — user probably asked a question
        log.info("[CHAT-EXTRACT] No fields extracted (user question or off-topic)")
        return {}

    except Exception as exc:
        log.error("[CHAT-EXTRACT] Extraction failed: %s", exc, exc_info=True)
        return {}


def _format_collected(collected: dict) -> str:
    """Format collected fields for the system prompt."""
    if not collected:
        return "keine"
    parts = []
    for k, v in collected.items():
        parts.append(f"{k}={v!r}")
    return ", ".join(parts)
