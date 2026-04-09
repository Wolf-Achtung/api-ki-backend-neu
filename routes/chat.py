# -*- coding: utf-8 -*-
"""
routes/chat.py — Conversational AI Questionnaire (PoC Block 1)

Endpoints:
  POST /api/chat/start      — Start new chat session
  POST /api/chat/message     — Process user message + stream AI response (SSE)
  GET  /api/chat/session/{id} — Get session state (for resume / frontend init)
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models import ChatSession
from routes._bootstrap import get_db
from schemas.chat import (
    ChatMessage,
    ChatMessageRequest,
    ChatSessionResponse,
    ChatSessionState,
    ChatStartRequest,
    ChatStartResponse,
    QuickReply,
    QuickReplyOption,
)
from services.chat_normalizer import (
    BUNDESLAND_LABELS,
    BUNDESLAND_VALUES,
    ENUM_VALUES,
    FIELD_REGISTRY,
    SECTIONS,
    calculate_progress,
    get_missing_fields,
    get_next_fields,
    is_field_visible,
    is_section_complete,
    normalize_field,
)

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
POC_SECTION = 0  # Only section 0 in PoC

WELCOME_MESSAGE = (
    "Willkommen bei ki-sicherheit.jetzt! Ich bin ein KI-Assistent und "
    "führe Sie durch eine kurze Bestandsaufnahme Ihres Unternehmens.\n\n"
    "Lassen Sie uns mit den Grundlagen beginnen: "
    "In welcher Branche ist Ihr Unternehmen tätig? "
    "Falls Sie unsicher sind, beschreiben Sie einfach, was Sie tun "
    "— ich helfe bei der Zuordnung."
)


# ===========================================================================
# POST /api/chat/start
# ===========================================================================

@router.post("/start", response_model=ChatStartResponse)
async def chat_start(req: ChatStartRequest, db: Session = Depends(get_db)):
    """Start a new chat conversation."""
    if not req.consent_report:
        raise HTTPException(status_code=400, detail="consent_report must be true")

    now = datetime.now(timezone.utc)

    session = ChatSession(
        report_type=req.report_type,
        lang=req.lang,
        consent_report=True,
        consent_at=now,
        collected_fields=req.prefill or {},
        field_meta={},
        current_section=POC_SECTION,
        status="active",
        messages=[],
        turn_count=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Build initial state
    state = _build_session_state(session)

    # Build welcome quick replies (branche)
    welcome_qr = _build_quick_replies(["branche"])
    state.quick_replies = welcome_qr

    # Save welcome message
    welcome_msg = {
        "role": "assistant",
        "content": WELCOME_MESSAGE,
        "timestamp": now.isoformat(),
        "turn": 0,
        "fields_extracted": None,
        "section_index": POC_SECTION,
        "quick_replies": [qr.model_dump() for qr in welcome_qr] if welcome_qr else None,
    }
    session.messages = [welcome_msg]
    db.commit()

    log.info("[CHAT] Session started: %s (report_type=%s)", session.id, session.report_type)

    return ChatStartResponse(
        session_id=session.id,
        state=state,
        welcome_message=WELCOME_MESSAGE,
    )


# ===========================================================================
# POST /api/chat/message
# ===========================================================================

@router.post("/message")
async def chat_message(req: ChatMessageRequest, db: Session = Depends(get_db)):
    """Process user message, extract fields, stream AI response via SSE."""
    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session ist nicht aktiv")

    now = datetime.now(timezone.utc)
    session.turn_count += 1
    turn = session.turn_count

    # Save user message
    user_msg = {
        "role": "user",
        "content": req.message,
        "timestamp": now.isoformat(),
        "turn": turn,
    }
    messages = list(session.messages or [])
    messages.append(user_msg)
    session.messages = messages
    session.last_activity_at = now
    session.updated_at = now
    db.commit()

    # Handle quick reply shortcut
    if req.quick_reply_field and req.quick_reply_value:
        raw_extracted = {req.quick_reply_field: req.quick_reply_value}
    else:
        # Phase 1: Extraction (Claude Haiku)
        from services.chat_extractor import extract_fields

        missing_req, missing_opt = get_missing_fields(
            session.collected_fields, session.current_section
        )
        all_missing = missing_req + missing_opt

        try:
            raw_extracted = await asyncio.wait_for(
                extract_fields(
                    req.message,
                    messages[-6:],
                    all_missing,
                    session.collected_fields,
                ),
                timeout=30,
            )
        except asyncio.TimeoutError:
            log.warning("[CHAT] Extraction timeout, retrying once...")
            try:
                raw_extracted = await asyncio.wait_for(
                    extract_fields(
                        req.message,
                        messages[-6:],
                        all_missing,
                        session.collected_fields,
                    ),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                raw_extracted = {}
                log.error("[CHAT] Extraction timeout on retry")

    # Phase 1b: Normalize extracted fields
    normalized = {}
    field_meta = dict(session.field_meta or {})
    collected = dict(session.collected_fields or {})

    for field_name, raw_value in raw_extracted.items():
        if field_name not in FIELD_REGISTRY:
            continue
        # Skip fields not visible due to conditionals
        if not is_field_visible(field_name, collected):
            continue

        result = normalize_field(field_name, raw_value, collected)

        if result.confidence == "low":
            log.info("[CHAT] Field %s: low confidence, skipping", field_name)
            continue

        # Store in collected_fields
        collected[field_name] = result.value
        normalized[field_name] = result.value

        # Store metadata
        field_meta[field_name] = {
            "confidence": result.confidence,
            "source_turn": turn,
            "raw_input": str(raw_value),
            "normalized": True,
            "confirmed": False,
        }

    # Update session state
    session.collected_fields = collected
    session.field_meta = field_meta
    session.updated_at = now

    # Evaluate conditionals: remove hidden fields
    for cond_field in ["selbststaendig", "bundesland"]:
        if cond_field in collected and not is_field_visible(cond_field, collected):
            del collected[cond_field]
            if cond_field in field_meta:
                del field_meta[cond_field]
            session.collected_fields = collected
            session.field_meta = field_meta

    db.commit()

    # Determine next fields
    missing_req, missing_opt = get_missing_fields(collected, session.current_section)
    all_missing = missing_req + missing_opt
    next_fields = get_next_fields(collected, session.current_section)
    current_section = SECTIONS[session.current_section]

    # Phase 2: Conversation (Claude Sonnet streaming)
    from services.chat_conversation import generate_response

    async def event_stream():
        # Heartbeat while processing
        yield f"event: heartbeat\ndata: {{}}\n\n"

        # Stream tokens
        full_response = ""
        try:
            async for token in generate_response(
                session_messages=list(session.messages),
                collected_fields=collected,
                missing_fields=all_missing,
                next_fields=next_fields,
                section=current_section,
            ):
                full_response += token
                yield f"event: token\ndata: {json.dumps({'text': token})}\n\n"
        except Exception as exc:
            log.error("[CHAT] Streaming error: %s", exc, exc_info=True)
            error_msg = "Entschuldigung, es gab einen Fehler. Bitte versuchen Sie es nochmal."
            yield f"event: error\ndata: {json.dumps({'code': 'stream_error', 'message': error_msg})}\n\n"
            return

        # Save assistant message
        quick_replies = _build_quick_replies(next_fields)
        assistant_msg = {
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "turn": turn,
            "fields_extracted": normalized if normalized else None,
            "section_index": session.current_section,
            "quick_replies": [qr.model_dump() for qr in quick_replies] if quick_replies else None,
        }
        msgs = list(session.messages)
        msgs.append(assistant_msg)
        session.messages = msgs
        session.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Send state update
        state = _build_session_state(session)
        state.quick_replies = quick_replies
        yield f"event: state_update\ndata: {state.model_dump_json()}\n\n"

        # Send quick replies
        if quick_replies:
            qr_data = [qr.model_dump() for qr in quick_replies]
            yield f"event: quick_replies\ndata: {json.dumps(qr_data)}\n\n"

        # Done signal
        yield f"event: done\ndata: {json.dumps({'turn': turn})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ===========================================================================
# GET /api/chat/session/{session_id}
# ===========================================================================

@router.get("/session/{session_id}", response_model=ChatSessionResponse)
async def chat_session_get(session_id: UUID, db: Session = Depends(get_db)):
    """Get session state and recent messages (for resume / frontend init)."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    state = _build_session_state(session)
    next_fields = get_next_fields(session.collected_fields, session.current_section)
    state.quick_replies = _build_quick_replies(next_fields)

    # Last 10 messages
    all_msgs = session.messages or []
    recent_msgs = all_msgs[-10:]
    chat_messages = []
    for m in recent_msgs:
        chat_messages.append(ChatMessage(
            role=m["role"],
            content=m["content"],
            timestamp=m.get("timestamp", session.created_at.isoformat()),
            turn=m.get("turn", 0),
            fields_extracted=m.get("fields_extracted"),
            section_index=m.get("section_index"),
            quick_replies=m.get("quick_replies"),
        ))

    resumable = session.status == "active"

    return ChatSessionResponse(
        state=state,
        messages=chat_messages,
        resumable=resumable,
        last_activity=session.last_activity_at,
    )


# ===========================================================================
# Helpers
# ===========================================================================

def _build_session_state(session: ChatSession) -> ChatSessionState:
    """Build ChatSessionState from a ChatSession DB model."""
    collected = session.collected_fields or {}
    section_idx = session.current_section
    section = SECTIONS[section_idx]

    missing_req, missing_opt = get_missing_fields(collected, section_idx)
    next_fields = get_next_fields(collected, section_idx)

    # Count total fields (across all sections)
    total = len(FIELD_REGISTRY)
    collected_count = len(collected)

    section_name: str = section["name"]  # type: ignore[assignment]

    return ChatSessionState(
        session_id=session.id,
        report_type=session.report_type,
        status=session.status,
        current_section=section_idx,
        current_section_name=section_name,
        total_sections=len(SECTIONS),
        progress_percent=calculate_progress(collected),
        collected_fields=collected,
        collected_count=collected_count,
        missing_required=missing_req,
        missing_optional=missing_opt,
        total_fields=total,
        next_fields=next_fields,
        is_completable=len(missing_req) == 0,
    )


# ---------------------------------------------------------------------------
# Quick Reply Builder
# ---------------------------------------------------------------------------

# Maps field → quick reply options (for enum fields in PoC)
_QR_OPTIONS: dict[str, list[dict]] = {
    "branche": [
        {"value": "marketing", "label": "Marketing & Werbung"},
        {"value": "beratung", "label": "Beratung & Dienstleistungen"},
        {"value": "it", "label": "IT & Software"},
        {"value": "finanzen", "label": "Finanzen & Versicherungen"},
        {"value": "handel", "label": "Handel & E-Commerce"},
        {"value": "bildung", "label": "Bildung"},
        {"value": "verwaltung", "label": "Verwaltung"},
        {"value": "gesundheit", "label": "Gesundheit & Pflege"},
        {"value": "bau", "label": "Bauwesen & Architektur"},
        {"value": "medien", "label": "Medien & Kreativwirtschaft"},
        {"value": "industrie", "label": "Industrie & Produktion"},
        {"value": "logistik", "label": "Transport & Logistik"},
        {"value": "gastronomie", "label": "Gastronomie & Tourismus"},
    ],
    "unternehmensgroesse": [
        {"value": "1", "label": "1 (Solo/Freiberuflich)"},
        {"value": "2–10", "label": "2–10 (Kleines Team)"},
        {"value": "11–100", "label": "11–100 (KMU)"},
    ],
    "selbststaendig": [
        {"value": "freiberufler", "label": "Freiberuflich/Selbstständig"},
        {"value": "kapitalgesellschaft", "label": "1-Personen-GmbH/UG"},
        {"value": "einzelunternehmer", "label": "Einzelunternehmer (Gewerbe)"},
        {"value": "sonstiges", "label": "Sonstiges"},
    ],
    "country": [
        {"value": "DE", "label": "Deutschland"},
        {"value": "AT", "label": "Österreich"},
        {"value": "CH", "label": "Schweiz"},
        {"value": "GB", "label": "Vereinigtes Königreich"},
    ],
    "jahresumsatz": [
        {"value": "unter_100k", "label": "Bis 100.000 €"},
        {"value": "100k_500k", "label": "100.000–500.000 €"},
        {"value": "500k_2m", "label": "500.000–2 Mio. €"},
        {"value": "2m_10m", "label": "2–10 Mio. €"},
        {"value": "ueber_10m", "label": "Über 10 Mio. €"},
        {"value": "keine_angabe", "label": "Keine Angabe"},
    ],
}

# Field labels for quick replies
_QR_LABELS: dict[str, str] = {
    "branche": "Branche",
    "unternehmensgroesse": "Unternehmensgröße",
    "selbststaendig": "Unternehmensform",
    "country": "Land",
    "bundesland": "Bundesland / Region",
    "hauptleistung": "Hauptleistung",
    "jahresumsatz": "Jahresumsatz",
}


def _build_quick_replies(next_fields: list[str]) -> list[QuickReply]:
    """Build quick reply buttons for the next enum fields."""
    replies = []
    for field_name in next_fields:
        reg = FIELD_REGISTRY.get(field_name, {})
        # Only build QR for enum fields with known options
        if reg.get("chat_mode") != "QR":
            continue

        options_data = _QR_OPTIONS.get(field_name)
        if not options_data:
            continue

        options = [
            QuickReplyOption(value=o["value"], label=o["label"], description=o.get("description"))
            for o in options_data
        ]
        label = _QR_LABELS.get(field_name, field_name)
        replies.append(QuickReply(field=field_name, label=label, options=options))

    return replies
