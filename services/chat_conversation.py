# -*- coding: utf-8 -*-
"""
Phase 2: Conversational response generation via Claude Sonnet with streaming.

Generates the next AI response based on current session state.
Streams tokens via an async generator for SSE delivery.
"""
from __future__ import annotations

import logging
import os
from typing import AsyncGenerator

from services.chat_normalizer import (
    FIELD_REGISTRY,
    SECTIONS,
    BUNDESLAND_LABELS,
    ENUM_VALUES,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model Config
# ---------------------------------------------------------------------------
CONVERSATION_MODEL = os.getenv(
    "CHAT_CONVERSATION_MODEL", "claude-sonnet-4-20250514"
)

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
CONVERSATION_SYSTEM_PROMPT = """\
Sie sind ein KI-Assistent von ki-sicherheit.jetzt und führen
Nutzerinnen und Nutzer in deutscher Sprache durch eine professionelle
Bestandsaufnahme zur KI-Readiness ihres Unternehmens.

IHRE ROLLE:
Sie sind ein kompetenter, freundlicher Berater — kein Chatbot.
Sie siezen durchgehend. Sie erklären Fachbegriffe proaktiv.
Sie bleiben effizient und respektieren die Zeit des Nutzers.

TRANSPARENZ:
Sie sind ein KI-Assistent. Machen Sie das zu Gesprächsbeginn
transparent und weisen Sie darauf hin, dass die Angaben zur
Erstellung eines individuellen KI-Reports verarbeitet werden.

REGELN:
1. Bestätigen Sie zuerst, was Sie verstanden haben.
2. Stellen Sie dann maximal 2–3 thematisch zusammenhängende Fragen.
3. Bei Auswahlfeldern nennen Sie die Optionen als nummerierte Liste.
4. Bei Fachbegriffen geben Sie in 1–2 Sätzen eine verständliche \
Erklärung mit einem konkreten Beispiel aus der Branche des Nutzers.
5. Erfinden Sie keine Angaben.
6. Keine unnötig langen Antworten.
7. Keine juristischen Zusicherungen.
8. Keine technischen Interna erwähnen.
9. Fragen Sie NUR nach Feldern, die noch nicht erfasst sind. \
Bereits erfasste Felder nicht erneut als Optionsliste anzeigen. \
Bestätigen Sie kurz, was Sie verstanden haben, und fragen Sie \
direkt nach den nächsten fehlenden Feldern. Halten Sie die \
Antworten kompakt — maximal 2–3 fehlende Felder pro Turn.
10. Wenn der Nutzer unsicher ist oder eine Rückfrage stellt \
(z.B. „Welche Branche passt bei mir?"), beantworten Sie die \
Frage verständlich mit Beispielen aus der Praxis. Weisen Sie bei \
Auswahlfeldern proaktiv darauf hin: „Falls keine Option genau \
passt, beschreiben Sie einfach, was Sie tun — ich ordne das \
dann zu."

AKTUELLER STAND:
- Abschnitt: {section_name} (Schritt {section_number} von {total_sections})
- Bereits erfasst: {collected_fields_summary}
- In diesem Abschnitt noch offen: {missing_in_section}

ALS NÄCHSTES ERFRAGEN:
{next_fields_with_descriptions}

ABSCHLUSS DIESES ABSCHNITTS:
Wenn alle Felder dieses Abschnitts erfasst sind, fassen Sie die \
Angaben kurz zusammen und fragen: "Ist das so korrekt?"
"""

# ---------------------------------------------------------------------------
# Async Anthropic Client (shares singleton with extractor)
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
        log.error("[CHAT-CONV] anthropic SDK not installed")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("[CHAT-CONV] ANTHROPIC_API_KEY not set")
        return None

    timeout = float(os.getenv("ANTHROPIC_TIMEOUT", "120"))
    _async_client = anthropic.AsyncAnthropic(
        api_key=api_key,
        timeout=timeout,
    )
    log.info("[CHAT-CONV] AsyncAnthropic client initialized (model=%s)", CONVERSATION_MODEL)
    return _async_client


# ---------------------------------------------------------------------------
# Context Building
# ---------------------------------------------------------------------------

def build_conversation_messages(messages: list[dict]) -> list[dict]:
    """
    Build messages for the conversation model.
    Uses last 6 messages (3 turns). If more exist, prepends a summary stub.
    """
    result: list[dict] = []

    if len(messages) > 6:
        # Compact summary for earlier messages
        result.append({
            "role": "user",
            "content": "[Bisheriger Gesprächsverlauf: Die Bestandsaufnahme hat bereits begonnen. "
                       "Einige Felder wurden bereits erfasst — siehe AKTUELLER STAND im System-Prompt.]",
        })
        result.append({
            "role": "assistant",
            "content": "Verstanden, ich setze die Bestandsaufnahme fort.",
        })

    # Last 6 messages (3 turns)
    recent = messages[-6:] if len(messages) > 6 else messages
    for msg in recent:
        result.append({"role": msg["role"], "content": msg["content"]})

    return result


# ---------------------------------------------------------------------------
# Field Descriptions for Prompt
# ---------------------------------------------------------------------------

FIELD_DESCRIPTIONS: dict[str, str] = {
    # Sektion 0
    "branche": "Branche des Unternehmens (13 Optionen: Marketing, Beratung, IT, Finanzen, Handel, Bildung, Verwaltung, Gesundheit, Bau, Medien, Industrie, Logistik, Gastronomie)",
    "unternehmensgroesse": "Unternehmensgröße (1 Person / 2–10 / 11–100 Mitarbeiter)",
    "selbststaendig": "Unternehmensform bei Einzelperson (Freiberufler, Kapitalgesellschaft, Einzelunternehmer, Sonstiges)",
    "country": "Land des Unternehmens (Deutschland, Österreich, Schweiz, UK oder anderes)",
    "bundesland": "Bundesland / Kanton / Region (für regionale Fördermöglichkeiten)",
    "hauptleistung": "Hauptdienstleistung oder wichtigstes Produkt (Freitext, 2–3 Sätze)",
    "jahresumsatz": "Geschätzter Jahresumsatz (bis 100T€ / 100–500T€ / 500T€–2Mio / 2–10Mio / >10Mio / keine Angabe)",
    # Sektion 1
    "zielgruppen": "Zielgruppen (Mehrfachauswahl: B2B, B2C, KMU, Großunternehmen, Öffentliche Hand, etc.)",
    "it_infrastruktur": "IT-Infrastruktur (Cloud / On-Premise / Hybrid / Unklar)",
    "interne_ki_kompetenzen": "Internes KI-/Digitalisierungsteam vorhanden (Ja / Nein / In Planung)",
    "datenquellen": "Verfügbare Datentypen für KI (Kundendaten, Verkaufsdaten, Produktionsdaten, etc.)",
    # Sektion 2
    "digitalisierungsgrad": "Digitalisierungsgrad der internen Prozesse (Skala 1–10)",
    "prozesse_papierlos": "Anteil papierloser Prozesse (0–20% / 21–50% / 51–80% / 81–100%)",
    "automatisierungsgrad": "Automatisierungsgrad (Sehr niedrig bis Sehr hoch)",
    "ki_einsatz": "Wo wird KI bereits eingesetzt (Mehrfachauswahl, auch 'noch keine')",
    "ki_kompetenz": "KI-Kompetenz im Team (Hoch / Mittel / Niedrig / Keine)",
    # Sektion 3
    "ki_ziele": "Ziele mit KI in den nächsten 3–6 Monaten (Mehrfachauswahl)",
    "ki_projekte": "Bestehende KI-Tests, Tools oder Projekte — auch informell (Freitext)",
    "anwendungsfaelle": "Interessante KI-Anwendungsfälle (Mehrfachauswahl)",
    "zeitersparnis_prioritaet": "Wo frisst heute am meisten Zeit oder Nerven? (Freitext)",
    "pilot_bereich": "Bester Bereich für ein Pilotprojekt (Kundenservice, Marketing, Vertrieb, etc.)",
    "geschaeftsmodell_evolution": "Ideen, wie KI das Geschäftsmodell verändern könnte (Freitext)",
    "vision_3_jahre": "Wie soll das Unternehmen in 2–3 Jahren mit KI arbeiten? (Freitext)",
    # Sektion 4
    "strategische_ziele": "Was soll KI in 6–12 Monaten konkret verbessern? (Freitext)",
    "ki_guardrails": "No-Gos oder sensible Themen beim KI-Einsatz (Freitext)",
    "massnahmen_komplexitaet": "Geschätzter Aufwand für KI-Einführung (Niedrig / Mittel / Hoch / Unklar)",
    "roadmap_vorhanden": "KI-Roadmap/Strategie vorhanden (Ja / Teilweise / Nein)",
    "governance_richtlinien": "KI-Governance-Richtlinien vorhanden (Ja / Teilweise / Nein)",
    "change_management": "Veränderungsbereitschaft im Team (Sehr hoch bis Sehr niedrig)",
    # Sektion 5
    "zeitbudget": "Zeit pro Woche für KI-Projekte (Unter 2h / 2–5h / 5–10h / Über 10h)",
    "vorhandene_tools": "Bereits genutzte Systeme (CRM, ERP, Projektmanagement, etc.)",
    "trainings_interessen": "Interessante KI-Trainingsthemen (Prompt Engineering, LLM-Basics, etc.)",
    "vision_prioritaet": "Wichtigster strategischer Hebel (KI-Services, Kundenservice, Datenprodukte, etc.)",
    "innovationsprozess": "Wie entstehen Innovationen (Team, Mitarbeitende, Kunden, Berater, etc.)",
    # Sektion 6
    "datenschutzbeauftragter": "Datenschutzbeauftragter vorhanden (Ja / Nein / Teilweise)",
    "technische_massnahmen": "Technische Schutzmaßnahmen (Alle / Teilweise / Keine)",
    "folgenabschaetzung": "Datenschutz-Folgenabschätzung durchgeführt (Ja / Nein / In Planung)",
    "meldewege": "Meldewege bei Sicherheitsvorfällen definiert (Ja / Teilweise / Nein)",
    "loeschregeln": "Lösch- und Anonymisierungsrichtlinien (Ja / Teilweise / Nein)",
    "ai_act_kenntnis": "Kenntnisse zum EU AI Act (Sehr gut / Gut / Gehört / Unbekannt)",
    "regulierte_branche": "Regulierte Branche (Gesundheit, Finanzen, Öffentlich, Recht, etc.)",
    "ki_hemmnisse": "Hemmnisse beim KI-Einsatz (Rechtsunsicherheit, Budget, Know-how, etc.)",
    # Sektion 7
    "bisherige_foerdermittel": "Bereits Fördermittel erhalten (Ja / Nein)",
    "interesse_foerderung": "Interesse an Fördermöglichkeiten (Ja / Nein / Unklar)",
    "erfahrung_beratung": "Bisherige Beratung zu Digitalisierung/KI (Ja / Nein / Unklar)",
    "investitionsbudget": "Budget für KI nächstes Jahr (Unter 2.000€ bis Über 50.000€)",
    "marktposition": "Marktposition (Marktführer bis Nachzügler)",
    "benchmark_wettbewerb": "Regelmäßiger Vergleich mit Wettbewerbern (Ja / Nein / Selten)",
    "risikofreude": "Risikofreude bei Innovation (Skala 1–5)",
}


# ---------------------------------------------------------------------------
# Section-specific conversation hints
# ---------------------------------------------------------------------------
SECTION_HINTS: dict[int, str] = {
    0: "",
    1: "Fragen Sie nach IT-Infrastruktur und Datenquellen pragmatisch. Viele kleine Unternehmen haben keine klare Antwort — 'unklar' ist völlig ok.",
    2: "Der Digitalisierungsgrad ist eine Selbsteinschätzung 1–10. Geben Sie Orientierung: 1–3 = überwiegend papierbasiert, 4–6 = teilweise digital, 7–10 = weitgehend digital. Bei ki_einsatz: 'noch_keine' ist die häufigste Antwort bei KMU — normalisieren Sie das.",
    3: "Dies ist der wichtigste Abschnitt für die Report-Qualität. Freitextfelder (ki_projekte, zeitersparnis_prioritaet, vision_3_jahre) sollten möglichst konkrete Antworten enthalten. Ermutigen Sie: 'Stichworte und kurze Sätze reichen völlig.'",
    4: "Viele KMU haben noch keine formelle KI-Strategie — das ist normal. Vermitteln Sie: 'Nein' bei Roadmap oder Governance ist eine absolut valide Antwort.",
    5: "Halten Sie diesen Abschnitt kurz. Zeitbudget und Tools sind schnell erfasst.",
    6: "Datenschutz-Fragen verunsichern viele KMU-Geschäftsführer. Machen Sie deutlich: Ehrliche Antworten helfen, den tatsächlichen Handlungsbedarf realistisch einzuschätzen. 'Nein' oder 'noch nicht' ist kein Problem.",
    7: "Letzter Abschnitt — fast geschafft. Förderung und Budget zügig abfragen, dann zur Zusammenfassung überleiten.",
}


def _format_next_fields(field_names: list[str]) -> str:
    """Format field descriptions for the system prompt."""
    if not field_names:
        return "Alle Felder dieses Abschnitts sind erfasst."
    lines = []
    for name in field_names:
        desc = FIELD_DESCRIPTIONS.get(name, name)
        reg = FIELD_REGISTRY.get(name, {})
        pflicht = "Pflicht" if reg.get("required") else "Optional"
        lines.append(f"- {name} ({pflicht}): {desc}")
    return "\n".join(lines)


def _format_collected_summary(collected: dict) -> str:
    """Format collected fields for display in the system prompt."""
    if not collected:
        return "noch keine Angaben"
    parts = []
    for k, v in collected.items():
        # Make bundesland human-readable
        if k == "bundesland" and isinstance(v, str):
            label = BUNDESLAND_LABELS.get(v, v)
            parts.append(f"{k}: {label}")
        else:
            parts.append(f"{k}: {v}")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Streaming Response Generator
# ---------------------------------------------------------------------------

async def generate_response(
    session_messages: list[dict],
    collected_fields: dict,
    missing_fields: list[str],
    next_fields: list[str],
    section: dict,
) -> AsyncGenerator[str, None]:
    """
    Generate streaming AI response.

    Yields text tokens as they arrive from Claude Sonnet.
    """
    client = _get_async_client()
    if client is None:
        yield "Entschuldigung, ich bin gerade nicht erreichbar. Bitte versuchen Sie es gleich nochmal."
        return

    section_index: int = section["index"]
    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        section_name=section["name"],
        section_number=section_index + 1,
        total_sections=8,
        collected_fields_summary=_format_collected_summary(collected_fields),
        missing_in_section=", ".join(missing_fields) if missing_fields else "alle erfasst",
        next_fields_with_descriptions=_format_next_fields(next_fields),
    )

    # Inject section-specific hint
    hint = SECTION_HINTS.get(section_index, "")
    if hint:
        system_prompt += f"\n\nHINWEIS FÜR DIESEN ABSCHNITT:\n{hint}"

    messages = build_conversation_messages(session_messages)

    try:
        async with client.messages.stream(
            model=CONVERSATION_MODEL,
            max_tokens=800,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as exc:
        log.error("[CHAT-CONV] Streaming failed: %s", exc, exc_info=True)
        yield "Entschuldigung, es gab einen Verbindungsfehler. Könnten Sie das bitte nochmal versuchen?"


# ===========================================================================
# Template-based summary (no LLM — deterministic)
# ===========================================================================

# Display labels for enum values (value -> German label)
_ENUM_DISPLAY: dict[str, dict[str, str]] = {
    "branche": {
        "marketing": "Marketing & Werbung", "beratung": "Beratung & Dienstleistungen",
        "it": "IT & Software", "finanzen": "Finanzen & Versicherungen",
        "handel": "Handel & E-Commerce", "bildung": "Bildung", "verwaltung": "Verwaltung",
        "gesundheit": "Gesundheit & Pflege", "bau": "Bauwesen & Architektur",
        "medien": "Medien & Kreativwirtschaft", "industrie": "Industrie & Produktion",
        "logistik": "Transport & Logistik", "gastronomie": "Gastronomie & Tourismus",
    },
    "unternehmensgroesse": {"1": "1 (Solo)", "2–10": "2–10 (Kleines Team)", "11–100": "11–100 (KMU)"},
}


def build_summary(collected_fields: dict) -> str:
    """
    Build a structured, template-based summary of all collected fields.
    No LLM involved — purely deterministic from collected data.
    """
    lines = ["**Zusammenfassung Ihrer Angaben:**\n"]

    for section in SECTIONS:
        section_lines: list[str] = []
        section_fields: list[str] = section["fields"]  # type: ignore[assignment]
        for field_name in section_fields:
            if field_name not in collected_fields:
                continue
            value = collected_fields[field_name]
            label = FIELD_DESCRIPTIONS.get(field_name, field_name).split("(")[0].strip()
            display = _format_value_for_display(field_name, value)
            section_lines.append(f"- {label}: {display}")

        if section_lines:
            lines.append(f"\n**{section['name']}**")
            lines.extend(section_lines)

    lines.append("\n\nSind alle Angaben korrekt? Dann starte ich die Auswertung.")
    return "\n".join(lines)


def _format_value_for_display(field_name: str, value: object) -> str:
    """Format a field value for human-readable display."""
    reg = FIELD_REGISTRY.get(field_name, {})
    field_type = reg.get("type", "text")

    # Enum: use display label
    if field_type == "enum":
        str_val = str(value)
        enum_labels = _ENUM_DISPLAY.get(field_name)
        if enum_labels and str_val in enum_labels:
            return enum_labels[str_val]
        # Bundesland code → label
        if field_name == "bundesland":
            return BUNDESLAND_LABELS.get(str_val, str_val)
        return str_val

    # Multi: comma-separated
    if field_type == "multi" and isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "–"

    # Slider: number with context
    if field_type == "slider":
        mx = reg.get("max", 10)
        return f"{value} von {mx}"

    # Bool
    if field_type == "bool":
        return "Ja" if value else "Nein"

    # Text: truncate
    if field_type == "text":
        text = str(value).strip()
        if len(text) > 100:
            return text[:97] + "..."
        return text

    return str(value)
