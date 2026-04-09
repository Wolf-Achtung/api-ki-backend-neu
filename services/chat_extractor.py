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
# Tool Definition — PoC Block 1 (Section 0, 7 fields)
# ---------------------------------------------------------------------------
EXTRACTOR_TOOL_POC: dict[str, Any] = {
    "name": "update_intake_fields",
    "description": (
        "Extrahiert strukturierte Felder aus der User-Nachricht. "
        "Nur Felder setzen, die der User tatsächlich genannt hat. "
        "Niemals Werte erfinden oder raten."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
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
        },
        "required": [],  # CRITICAL: extractor only sets actually mentioned fields
    },
}


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
            tools=[EXTRACTOR_TOOL_POC],
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
