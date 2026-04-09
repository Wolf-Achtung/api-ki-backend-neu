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
    "branche": "Branche des Unternehmens (13 Optionen: Marketing, Beratung, IT, Finanzen, Handel, Bildung, Verwaltung, Gesundheit, Bau, Medien, Industrie, Logistik, Gastronomie)",
    "unternehmensgroesse": "Unternehmensgröße (1 Person / 2–10 / 11–100 Mitarbeiter)",
    "selbststaendig": "Unternehmensform bei Einzelperson (Freiberufler, Kapitalgesellschaft, Einzelunternehmer, Sonstiges)",
    "country": "Land des Unternehmens (Deutschland, Österreich, Schweiz, UK oder anderes)",
    "bundesland": "Bundesland / Kanton / Region (für regionale Fördermöglichkeiten)",
    "hauptleistung": "Hauptdienstleistung oder wichtigstes Produkt (Freitext, 2–3 Sätze)",
    "jahresumsatz": "Geschätzter Jahresumsatz (bis 100T€ / 100–500T€ / 500T€–2Mio / 2–10Mio / >10Mio / keine Angabe)",
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

    system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
        section_name=section["name"],
        section_number=section["index"] + 1,
        total_sections=8,
        collected_fields_summary=_format_collected_summary(collected_fields),
        missing_in_section=", ".join(missing_fields) if missing_fields else "alle erfasst",
        next_fields_with_descriptions=_format_next_fields(next_fields),
    )

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
