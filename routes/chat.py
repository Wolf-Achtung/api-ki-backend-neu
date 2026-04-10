# -*- coding: utf-8 -*-
"""
routes/chat.py — Conversational AI Questionnaire

Endpoints:
  POST /api/chat/start        — Start new chat session
  POST /api/chat/message       — Process user message + stream AI response (SSE)
  GET  /api/chat/session/{id}  — Get session state (for resume / frontend init)
  POST /api/chat/complete      — Finalize session and submit to report pipeline
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

from models import Briefing, ChatSession
from routes._bootstrap import get_db
from schemas.chat import (
    ChatCompleteRequest,
    ChatCompleteResponse,
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
    STRATEGY_ENUM_VALUES,
    STRATEGY_FIELD_REGISTRY,
    STRATEGY_SECTIONS,
    calculate_progress,
    get_enum_values_for_report,
    get_missing_fields,
    get_next_fields,
    get_registry_for_report,
    get_sections_for_report,
    is_field_visible,
    is_section_complete,
    normalize_field,
)

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)

R1_WELCOME = (
    "Willkommen bei ki-sicherheit.jetzt! Ich bin ein KI-Assistent und "
    "führe Sie durch eine kurze Bestandsaufnahme Ihres Unternehmens.\n\n"
    "Lassen Sie uns mit den Grundlagen beginnen: "
    "In welcher Branche ist Ihr Unternehmen tätig? "
    "Falls Sie unsicher sind, beschreiben Sie einfach, was Sie tun "
    "— ich helfe bei der Zuordnung."
)

STRATEGY_WELCOME = (
    "Willkommen zurück! Auf Basis Ihrer KI-Readiness-Analyse erstelle ich "
    "jetzt Ihren individuellen KI-Strategiebericht.\n\n"
    "Dafür benötige ich noch einige Angaben zu Ihrer konkreten Umsetzungsplanung. "
    "Das dauert ca. 3 Minuten. Falls Sie bei einer Frage unsicher sind, "
    "fragen Sie einfach nach — ich erkläre gern.\n\n"
    "Beginnen wir: Wie hoch ist Ihr geplantes Budget speziell für die "
    "KI-Implementierung der nächsten 12 Monate?"
)


def _get_welcome(report_type: str) -> str:
    if report_type == "strategy":
        return STRATEGY_WELCOME
    return R1_WELCOME


def _get_first_qr_fields(report_type: str) -> list[str]:
    if report_type == "strategy":
        return ["s1_budget"]
    return ["branche"]


# ===========================================================================
# POST /api/chat/start
# ===========================================================================

@router.post("/start", response_model=ChatStartResponse)
async def chat_start(req: ChatStartRequest, db: Session = Depends(get_db)):
    """Start a new chat conversation."""
    if not req.consent_report:
        raise HTTPException(status_code=400, detail="consent_report must be true")

    # Strategy requires a briefing_id
    if req.report_type == "strategy":
        if not req.briefing_id:
            raise HTTPException(status_code=400, detail="briefing_id erforderlich für Strategy-Report")
        briefing = db.query(Briefing).filter(Briefing.id == req.briefing_id).first()
        if not briefing:
            raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    now = datetime.now(timezone.utc)

    session = ChatSession(
        report_type=req.report_type,
        lang=req.lang,
        consent_report=True,
        consent_at=now,
        collected_fields=req.prefill or {},
        field_meta={},
        current_section=0,
        status="active",
        messages=[],
        turn_count=0,
        briefing_id=req.briefing_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Build initial state
    state = _build_session_state(session)

    # Build welcome quick replies (first field for this report type)
    first_fields = _get_first_qr_fields(req.report_type)
    welcome_qr = _build_quick_replies(first_fields, req.report_type)
    state.quick_replies = welcome_qr

    # Save welcome message
    welcome = _get_welcome(req.report_type)
    welcome_msg = {
        "role": "assistant",
        "content": welcome,
        "timestamp": now.isoformat(),
        "turn": 0,
        "fields_extracted": None,
        "section_index": 0,
        "quick_replies": [qr.model_dump() for qr in welcome_qr] if welcome_qr else None,
    }
    session.messages = [welcome_msg]
    db.commit()

    log.info("[CHAT] Session started: %s (report_type=%s)", session.id, session.report_type)

    return ChatStartResponse(
        session_id=session.id,
        state=state,
        welcome_message=welcome,
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

    # Phase 1: Extract fields from user message
    rt = session.report_type
    registry = get_registry_for_report(rt)
    normalized = {}
    field_meta = dict(session.field_meta or {})
    collected = dict(session.collected_fields or {})

    if req.quick_reply_field and req.quick_reply_value:
        # Quick reply: normalize directly — no LLM extractor needed
        qr_field = req.quick_reply_field
        qr_result = normalize_field(qr_field, req.quick_reply_value, collected, report_type=rt)
        if qr_result.confidence != "low":
            collected[qr_field] = qr_result.value
            normalized[qr_field] = qr_result.value
            field_meta[qr_field] = {
                "confidence": qr_result.confidence,
                "source_turn": turn,
                "raw_input": req.quick_reply_value,
                "normalized": True,
                "confirmed": True,  # User clicked explicitly
            }
        log.info("[CHAT] Quick reply: %s=%s → %s", qr_field, req.quick_reply_value, qr_result.value)
    else:
        # Free text: call LLM extractor (Claude Haiku)
        from services.chat_extractor import extract_fields

        missing_req, missing_opt = get_missing_fields(collected, session.current_section, rt)
        all_missing = missing_req + missing_opt

        try:
            raw_extracted = await asyncio.wait_for(
                extract_fields(
                    req.message,
                    messages[-6:],
                    all_missing,
                    collected,
                    report_type=rt,
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
                        collected,
                        report_type=rt,
                    ),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                raw_extracted = {}
                log.error("[CHAT] Extraction timeout on retry")

        # Normalize extracted fields
        for field_name, raw_value in raw_extracted.items():
            if field_name not in registry:
                continue
            if not is_field_visible(field_name, collected):
                continue

            result = normalize_field(field_name, raw_value, collected, report_type=rt)

            if result.confidence == "low":
                log.info("[CHAT] Field %s: low confidence, skipping", field_name)
                continue

            collected[field_name] = result.value
            normalized[field_name] = result.value

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

    # Check section transition: advance if all required fields done
    section_advanced = _check_section_transition(session, collected, rt)
    if section_advanced:
        db.commit()

    # Determine next fields
    sections = get_sections_for_report(rt)
    missing_req, missing_opt = get_missing_fields(collected, session.current_section, rt)
    all_missing = missing_req + missing_opt
    next_fields = get_next_fields(collected, session.current_section, report_type=rt)
    current_section = sections[session.current_section]

    # DEBUG POINT 1: State after normalization, before streaming
    print(f"[CHAT DEBUG 1] collected_fields after update: {list(collected.keys())}")
    print(f"[CHAT DEBUG 1] next_fields for prompt: {next_fields}")
    print(f"[CHAT DEBUG 1] all_missing: {all_missing}")
    print(f"[CHAT DEBUG 1] normalized this turn: {list(normalized.keys())}")

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
                report_type=rt,
            ):
                full_response += token
                yield f"event: token\ndata: {json.dumps({'text': token})}\n\n"
        except Exception as exc:
            log.error("[CHAT] Streaming error: %s", exc, exc_info=True)
            error_msg = "Entschuldigung, es gab einen Fehler. Bitte versuchen Sie es nochmal."
            yield f"event: error\ndata: {json.dumps({'code': 'stream_error', 'message': error_msg})}\n\n"
            return

        # Build QR from the closure-captured `collected` dict — NOT from
        # session.collected_fields which may be expired after db.commit()
        # DEBUG POINT 2: Inside streaming callback, QR generation
        print(f"[CHAT DEBUG 2] QR generation - collected keys: {list(collected.keys())}")
        print(f"[CHAT DEBUG 2] session.current_section: {session.current_section}")
        qr_next = get_next_fields(collected, session.current_section, report_type=rt)
        print(f"[CHAT DEBUG 2] QR next_fields: {qr_next}")
        quick_replies = _build_quick_replies(qr_next, rt, collected)
        print(f"[CHAT DEBUG 2] QR result fields: {[r.field for r in quick_replies]}")
        print(f"[CHAT DEBUG 2] QR result options count: {[len(r.options) for r in quick_replies]}")
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

        # Send state update — pass collected explicitly to avoid
        # stale session.collected_fields after db.commit() expiry
        state = _build_session_state(session, collected_override=collected)
        state.quick_replies = quick_replies
        yield f"event: state_update\ndata: {state.model_dump_json()}\n\n"

        # Send quick replies
        if quick_replies:
            qr_data = [qr.model_dump() for qr in quick_replies]
            # DEBUG POINT 3: What we actually send over SSE
            print(f"[CHAT DEBUG 3] Sending QR event with fields: {[r['field'] for r in qr_data]}")
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

    rt = session.report_type
    state = _build_session_state(session)
    next_fields = get_next_fields(session.collected_fields, session.current_section, report_type=rt)
    state.quick_replies = _build_quick_replies(next_fields, rt, session.collected_fields)

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
# POST /api/chat/complete
# ===========================================================================

@router.post("/complete", response_model=ChatCompleteResponse)
async def chat_complete(req: ChatCompleteRequest, db: Session = Depends(get_db)):
    """Finalize chat session and submit collected data to report pipeline."""
    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session ist nicht aktiv")
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Bestätigung erforderlich")

    rt = session.report_type
    sections = get_sections_for_report(rt)

    # Idempotency: if already completed, return existing briefing_id
    if session.status == "completed" and session.briefing_id:
        redirect = _complete_redirect(rt, session.briefing_id)
        return ChatCompleteResponse(
            success=True,
            briefing_id=session.briefing_id,
            report_type=rt,
            redirect_url=redirect,
        )

    # Check all required fields (across all sections)
    collected = dict(session.collected_fields or {})
    missing_all: list[str] = []
    for section in sections:
        sec_idx: int = section["index"]
        missing_req, _ = get_missing_fields(collected, sec_idx, rt)
        missing_all.extend(missing_req)
    if missing_all:
        raise HTTPException(
            status_code=400,
            detail=f"Pflichtfelder fehlen: {', '.join(missing_all)}",
        )

    now = datetime.now(timezone.utc)

    if rt == "strategy":
        briefing_id = await _complete_strategy(session, collected, db, now)
    else:
        briefing_id = _complete_r1(session, collected, db, now)

    redirect = _complete_redirect(rt, briefing_id)

    log.info(
        "[CHAT] Session %s completed -> briefing_id=%s (report_type=%s, fields=%d)",
        session.id, briefing_id, rt, len(collected),
    )

    return ChatCompleteResponse(
        success=True,
        briefing_id=briefing_id,
        report_type=rt,
        redirect_url=redirect,
    )


# ===========================================================================
# Helpers
# ===========================================================================

def _check_section_transition(session: ChatSession, collected: dict, report_type: str = "r1") -> bool:
    """
    Check if all required fields of the current section are collected.
    If so, advance current_section. Returns True if section advanced.
    """
    sections = get_sections_for_report(report_type)
    if session.current_section >= len(sections) - 1:
        return False

    if not is_section_complete(collected, session.current_section, report_type):
        return False

    session.current_section += 1
    log.info(
        "[CHAT] Section transition: %d -> %d (%s)",
        session.current_section - 1,
        session.current_section,
        sections[session.current_section]["name"],
    )
    return True


def _complete_r1(session: ChatSession, collected: dict, db: Session, now: datetime) -> int:
    """Complete R1 chat: create a Briefing for the report pipeline."""
    answers = dict(collected)
    answers["datenschutz"] = True  # consent given at chat start

    briefing = Briefing(
        user_id=session.user_id,
        lang=session.lang,
        answers=answers,
        status="accepted",
        accepted_at=now,
    )
    db.add(briefing)
    db.flush()

    session.status = "completed"
    session.completed_at = now
    session.briefing_id = briefing.id
    session.updated_at = now
    db.commit()
    return briefing.id


async def _complete_strategy(
    session: ChatSession, collected: dict, db: Session, now: datetime,
) -> int:
    """Complete strategy chat: save questions + create strategy report entry."""
    from models import StrategyQuestion, StrategyReport

    briefing_id = session.briefing_id
    if not briefing_id:
        raise HTTPException(status_code=400, detail="Keine briefing_id in der Session")

    # Upsert strategy questions (same logic as routes/strategy.py)
    existing = db.query(StrategyQuestion).filter(
        StrategyQuestion.briefing_id == briefing_id
    ).first()

    fields = {
        "s1_budget": collected.get("s1_budget", ""),
        "s2_zeitrahmen": collected.get("s2_zeitrahmen", ""),
        "s3_prioritaeten": collected.get("s3_prioritaeten", []),
        "s4_engpass": collected.get("s4_engpass", ""),
        "s5_software": collected.get("s5_software", ""),
        "s6_foerderinteresse": collected.get("s6_foerderinteresse", ""),
        "s7_entscheidung": collected.get("s7_entscheidung", ""),
        "s8_erfahrung": collected.get("s8_erfahrung"),
        "s9_ansatz": collected.get("s9_ansatz"),
        "s10_datenschutz": collected.get("s10_datenschutz"),
        "wettbewerber_anzahl": collected.get("wettbewerber_anzahl"),
        "kundenbindung_typ": collected.get("kundenbindung_typ"),
        "datenreife": collected.get("datenreife"),
    }

    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
    else:
        sq = StrategyQuestion(briefing_id=briefing_id, **fields)
        db.add(sq)

    # Ensure strategy_reports entry exists
    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if not sr:
        sr = StrategyReport(briefing_id=briefing_id, status="pending")
        db.add(sr)

    session.status = "completed"
    session.completed_at = now
    session.updated_at = now
    db.commit()
    return briefing_id


def _complete_redirect(report_type: str, briefing_id: int) -> str:
    """Build the redirect URL after completion."""
    if report_type == "strategy":
        return f"/strategy.html?briefing_id={briefing_id}&status=generating"
    return f"/formular/status.html?id={briefing_id}"


def _build_session_state(
    session: ChatSession, collected_override: dict | None = None,
) -> ChatSessionState:
    """Build ChatSessionState from a ChatSession DB model.

    Args:
        collected_override: If provided, use this instead of session.collected_fields.
            Needed inside streaming callbacks where session attributes may be expired
            after db.commit().
    """
    rt = session.report_type
    sections = get_sections_for_report(rt)
    registry = get_registry_for_report(rt)
    collected = collected_override if collected_override is not None else (session.collected_fields or {})
    section_idx = session.current_section
    section = sections[section_idx]

    missing_req, missing_opt = get_missing_fields(collected, section_idx, rt)
    next_fields = get_next_fields(collected, section_idx, report_type=rt)

    total = len(registry)
    collected_count = len(collected)

    section_name: str = section["name"]

    return ChatSessionState(
        session_id=session.id,
        report_type=session.report_type,
        status=session.status,
        current_section=section_idx,
        current_section_name=section_name,
        total_sections=len(sections),
        progress_percent=calculate_progress(collected, rt),
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

# Maps field → quick reply options (labels from formbuilder_de_SINGLE_FULL.js)
_QR_OPTIONS: dict[str, list[dict]] = {
    # --- Sektion 0 ---
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
    # --- Sektion 1 ---
    "zielgruppen": [
        {"value": "b2b", "label": "B2B (Geschäftskunden)"},
        {"value": "b2c", "label": "B2C (Endverbraucher)"},
        {"value": "kmu", "label": "KMU"},
        {"value": "grossunternehmen", "label": "Großunternehmen"},
        {"value": "selbststaendige", "label": "Selbstständige/Freiberufler"},
        {"value": "oeffentliche_hand", "label": "Öffentliche Hand"},
        {"value": "privatpersonen", "label": "Privatpersonen"},
        {"value": "startups", "label": "Startups"},
        {"value": "andere", "label": "Andere"},
    ],
    "it_infrastruktur": [
        {"value": "cloud", "label": "Cloud-basiert (z.\u00A0B. Microsoft 365)"},
        {"value": "on_premise", "label": "Eigenes Rechenzentrum"},
        {"value": "hybrid", "label": "Hybrid (Cloud + eigene Server)"},
        {"value": "unklar", "label": "Unklar / noch offen"},
    ],
    "interne_ki_kompetenzen": [
        {"value": "ja", "label": "Ja"},
        {"value": "nein", "label": "Nein"},
        {"value": "in_planung", "label": "In Planung"},
    ],
    "datenquellen": [
        {"value": "kundendaten", "label": "Kundendaten (CRM, Service)"},
        {"value": "verkaufsdaten", "label": "Verkaufs-/Bestelldaten"},
        {"value": "produktionsdaten", "label": "Produktions-/Betriebsdaten"},
        {"value": "personaldaten", "label": "Personal-/HR-Daten"},
        {"value": "marketingdaten", "label": "Marketing-/Kampagnendaten"},
        {"value": "sonstige", "label": "Sonstige Datenquellen"},
    ],
    # --- Sektion 2 ---
    "prozesse_papierlos": [
        {"value": "0-20", "label": "0–20 %"},
        {"value": "21-50", "label": "21–50 %"},
        {"value": "51-80", "label": "51–80 %"},
        {"value": "81-100", "label": "81–100 %"},
    ],
    "automatisierungsgrad": [
        {"value": "sehr_niedrig", "label": "Sehr niedrig"},
        {"value": "eher_niedrig", "label": "Eher niedrig"},
        {"value": "mittel", "label": "Mittel"},
        {"value": "eher_hoch", "label": "Eher hoch"},
        {"value": "sehr_hoch", "label": "Sehr hoch"},
    ],
    "ki_einsatz": [
        {"value": "chatbots", "label": "Chatbots / Kundenservice"},
        {"value": "marketing", "label": "Marketing & Content"},
        {"value": "vertrieb", "label": "Vertrieb & CRM"},
        {"value": "datenanalyse", "label": "Datenanalyse"},
        {"value": "produktion", "label": "Produktion / Logistik"},
        {"value": "hr", "label": "Personalmanagement"},
        {"value": "andere", "label": "Andere Bereiche"},
        {"value": "noch_keine", "label": "Noch keine Nutzung"},
    ],
    "ki_kompetenz": [
        {"value": "hoch", "label": "Hoch"},
        {"value": "mittel", "label": "Mittel"},
        {"value": "niedrig", "label": "Niedrig"},
        {"value": "keine", "label": "Keine"},
    ],
    # --- Sektion 3 ---
    "ki_ziele": [
        {"value": "effizienz", "label": "Effizienz steigern"},
        {"value": "automatisierung", "label": "Automatisierung"},
        {"value": "neue_produkte", "label": "Neue Produkte/Services"},
        {"value": "kundenservice", "label": "Kundenservice verbessern"},
        {"value": "datenauswertung", "label": "Daten besser nutzen"},
        {"value": "kosten_senken", "label": "Kosten senken"},
        {"value": "wettbewerbsfaehigkeit", "label": "Wettbewerbsfähigkeit"},
        {"value": "keine_angabe", "label": "Noch unklar"},
    ],
    "anwendungsfaelle": [
        {"value": "chatbots", "label": "Chatbots / FAQ-Automatisierung"},
        {"value": "content_generation", "label": "Content-Generierung"},
        {"value": "datenanalyse", "label": "Datenanalyse & Reporting"},
        {"value": "dokumentation", "label": "Dokumentation & Wissen"},
        {"value": "prozess_automation", "label": "Prozessautomation"},
        {"value": "personalisierung", "label": "Personalisierung"},
        {"value": "andere", "label": "Andere"},
        {"value": "keine_angabe", "label": "Noch unklar"},
    ],
    "pilot_bereich": [
        {"value": "kundenservice", "label": "Kundenservice"},
        {"value": "marketing", "label": "Marketing / Content"},
        {"value": "vertrieb", "label": "Vertrieb"},
        {"value": "verwaltung", "label": "Verwaltung / Backoffice"},
        {"value": "produktion", "label": "Produktion / Logistik"},
        {"value": "andere", "label": "Andere"},
    ],
    # --- Sektion 4 ---
    "massnahmen_komplexitaet": [
        {"value": "niedrig", "label": "Niedrig"},
        {"value": "mittel", "label": "Mittel"},
        {"value": "hoch", "label": "Hoch"},
        {"value": "unklar", "label": "Unklar"},
    ],
    "roadmap_vorhanden": [
        {"value": "ja", "label": "Ja"},
        {"value": "teilweise", "label": "Teilweise"},
        {"value": "nein", "label": "Nein"},
    ],
    "governance_richtlinien": [
        {"value": "ja", "label": "Ja"},
        {"value": "teilweise", "label": "Teilweise"},
        {"value": "nein", "label": "Nein"},
    ],
    "change_management": [
        {"value": "sehr_hoch", "label": "Sehr hoch"},
        {"value": "hoch", "label": "Hoch"},
        {"value": "mittel", "label": "Mittel"},
        {"value": "niedrig", "label": "Niedrig"},
        {"value": "sehr_niedrig", "label": "Sehr niedrig"},
    ],
    # --- Sektion 5 ---
    "zeitbudget": [
        {"value": "unter_2", "label": "Unter 2 Stunden"},
        {"value": "2_5", "label": "2–5 Stunden"},
        {"value": "5_10", "label": "5–10 Stunden"},
        {"value": "ueber_10", "label": "Über 10 Stunden"},
    ],
    "vorhandene_tools": [
        {"value": "crm", "label": "CRM (HubSpot, Salesforce)"},
        {"value": "erp", "label": "ERP (SAP, Odoo)"},
        {"value": "projektmanagement", "label": "Projektmanagement (Asana, Trello)"},
        {"value": "marketing_automation", "label": "Marketing Automation"},
        {"value": "buchhaltung", "label": "Buchhaltungssoftware"},
        {"value": "keine", "label": "Keine / andere"},
    ],
    "trainings_interessen": [
        {"value": "prompt_engineering", "label": "Prompt Engineering"},
        {"value": "llm_basics", "label": "LLM-Grundlagen"},
        {"value": "datenqualitaet_governance", "label": "Datenqualität & Governance"},
        {"value": "automatisierung", "label": "Automatisierung & Skripte"},
        {"value": "ethik_recht", "label": "Ethische & rechtliche Grundlagen"},
        {"value": "keine", "label": "Keine / noch unklar"},
    ],
    "vision_prioritaet": [
        {"value": "gpt_services", "label": "KI-gestützte Services und Produkte"},
        {"value": "kundenservice", "label": "Optimierung Kundenservice"},
        {"value": "datenprodukte", "label": "Datenbasierte Angebote"},
        {"value": "prozessautomation", "label": "Automatisierung interner Prozesse"},
        {"value": "marktfuehrerschaft", "label": "Technologieführerschaft"},
        {"value": "keine_angabe", "label": "Noch unklar"},
    ],
    "innovationsprozess": [
        {"value": "innovationsteam", "label": "Innovationsteam"},
        {"value": "mitarbeitende", "label": "Durch Mitarbeitende"},
        {"value": "kunden", "label": "Mit Kunden"},
        {"value": "berater", "label": "Externe Berater"},
        {"value": "zufall", "label": "Zufällig"},
        {"value": "unbekannt", "label": "Keine klare Strategie"},
    ],
    "regulierte_branche": [
        {"value": "gesundheit", "label": "Gesundheit & Medizin"},
        {"value": "finanzen", "label": "Finanzen & Versicherungen"},
        {"value": "oeffentlich", "label": "Öffentlicher Sektor"},
        {"value": "recht", "label": "Rechtliche Dienstleistungen"},
        {"value": "vertraulich_nda", "label": "Vertrauliche Kundendaten / NDA"},
        {"value": "keine", "label": "Keine dieser Branchen"},
    ],
    # --- Sektion 6 ---
    "datenschutzbeauftragter": [
        {"value": "ja", "label": "Ja"},
        {"value": "nein", "label": "Nein"},
        {"value": "teilweise", "label": "Teilweise (extern/Planung)"},
    ],
    "technische_massnahmen": [
        {"value": "alle", "label": "Alle relevanten Maßnahmen"},
        {"value": "teilweise", "label": "Teilweise vorhanden"},
        {"value": "keine", "label": "Noch keine"},
    ],
    "folgenabschaetzung": [
        {"value": "ja", "label": "Ja, durchgeführt"},
        {"value": "nein", "label": "Nein, noch nicht"},
        {"value": "teilweise", "label": "In Planung"},
    ],
    "meldewege": [
        {"value": "ja", "label": "Ja, klar definiert"},
        {"value": "teilweise", "label": "Teilweise vorhanden"},
        {"value": "nein", "label": "Nein, noch nicht geregelt"},
    ],
    "loeschregeln": [
        {"value": "ja", "label": "Ja, dokumentiert"},
        {"value": "teilweise", "label": "Teilweise vorhanden"},
        {"value": "nein", "label": "Nein, noch nicht definiert"},
    ],
    "ai_act_kenntnis": [
        {"value": "sehr_gut", "label": "Sehr gut"},
        {"value": "gut", "label": "Gut"},
        {"value": "gehoert", "label": "Schon mal gehört"},
        {"value": "unbekannt", "label": "Noch nicht bekannt"},
    ],
    "ki_hemmnisse": [
        {"value": "rechtsunsicherheit", "label": "Rechtsunsicherheit"},
        {"value": "datenschutz", "label": "Datenschutz"},
        {"value": "knowhow", "label": "Fehlendes Know-how"},
        {"value": "budget", "label": "Begrenztes Budget"},
        {"value": "teamakzeptanz", "label": "Teamakzeptanz"},
        {"value": "zeitmangel", "label": "Zeitmangel"},
        {"value": "it_integration", "label": "IT-Integration"},
        {"value": "keine", "label": "Keine Hemmnisse"},
        {"value": "andere", "label": "Andere"},
    ],
    # --- Sektion 7 ---
    "bisherige_foerdermittel": [
        {"value": "ja", "label": "Ja"},
        {"value": "nein", "label": "Nein"},
    ],
    "interesse_foerderung": [
        {"value": "ja", "label": "Ja, Programme vorschlagen"},
        {"value": "nein", "label": "Kein Bedarf"},
        {"value": "unklar", "label": "Unklar, bitte beraten"},
    ],
    "erfahrung_beratung": [
        {"value": "ja", "label": "Ja"},
        {"value": "nein", "label": "Nein"},
        {"value": "unklar", "label": "Unklar"},
    ],
    "investitionsbudget": [
        {"value": "unter_2000", "label": "Unter 2.000 €"},
        {"value": "2000_10000", "label": "2.000–10.000 €"},
        {"value": "10000_50000", "label": "10.000–50.000 €"},
        {"value": "ueber_50000", "label": "Über 50.000 €"},
        {"value": "unklar", "label": "Noch unklar"},
    ],
    "marktposition": [
        {"value": "marktfuehrer", "label": "Marktführer"},
        {"value": "oberes_drittel", "label": "Oberes Drittel"},
        {"value": "mittelfeld", "label": "Mittelfeld"},
        {"value": "nachzuegler", "label": "Nachzügler"},
        {"value": "unsicher", "label": "Schwer einzuschätzen"},
    ],
    "benchmark_wettbewerb": [
        {"value": "ja", "label": "Ja, regelmäßig"},
        {"value": "nein", "label": "Nein"},
        {"value": "selten", "label": "Selten"},
    ],
    # --- Strategy Fields ---
    "s1_budget": [
        {"value": "unter_2000", "label": "Unter 2.000 €"},
        {"value": "2000_10000", "label": "2.000 – 10.000 €"},
        {"value": "10000_50000", "label": "10.000 – 50.000 €"},
        {"value": "ueber_50000", "label": "Über 50.000 €"},
        {"value": "unklar", "label": "Noch unklar"},
    ],
    "s2_zeitrahmen": [
        {"value": "Sofort (1-3 Monate)", "label": "Sofort (1–3 Monate)"},
        {"value": "Kurzfristig (3-6 Monate)", "label": "Kurzfristig (3–6 Monate)"},
        {"value": "Mittelfristig (6-12 Monate)", "label": "Mittelfristig (6–12 Monate)"},
        {"value": "Langfristig (12-18 Monate)", "label": "Langfristig (12–18 Monate)"},
    ],
    "s3_prioritaeten": [
        {"value": "Kosten senken", "label": "Kosten senken"},
        {"value": "Umsatz steigern", "label": "Umsatz steigern"},
        {"value": "Qualität verbessern", "label": "Qualität verbessern"},
        {"value": "Geschwindigkeit erhöhen", "label": "Geschwindigkeit erhöhen"},
        {"value": "Compliance sichern", "label": "Compliance sichern"},
        {"value": "Neue Geschäftsfelder", "label": "Neue Geschäftsfelder"},
        {"value": "Fachkräftemangel kompensieren", "label": "Fachkräftemangel kompensieren"},
        {"value": "Kundenerlebnis verbessern", "label": "Kundenerlebnis verbessern"},
    ],
    "s4_engpass": [
        {"value": "Zu wenig Know-how", "label": "Zu wenig Know-how"},
        {"value": "Kein Budget", "label": "Kein Budget"},
        {"value": "Fehlende Daten", "label": "Fehlende Daten"},
        {"value": "Widerstand im Team", "label": "Widerstand im Team"},
        {"value": "Regulatorische Unsicherheit", "label": "Regulatorische Unsicherheit"},
        {"value": "Kein klarer Use Case", "label": "Kein klarer Use Case"},
        {"value": "Andere", "label": "Andere"},
    ],
    "s6_foerderinteresse": [
        {"value": "Ja, dringend", "label": "Ja, dringend"},
        {"value": "Ja, wenn passend", "label": "Ja, wenn passend"},
        {"value": "Nein, eigenes Budget", "label": "Nein, eigenes Budget"},
        {"value": "Weiß nicht", "label": "Weiß nicht"},
    ],
    "s7_entscheidung": [
        {"value": "Entscheide allein", "label": "Entscheide allein"},
        {"value": "Brauche Vorlage für Geschäftsleitung", "label": "Vorlage für Geschäftsleitung"},
        {"value": "Muss Gesellschafter überzeugen", "label": "Gesellschafter überzeugen"},
        {"value": "Muss Aufsichtsrat/Beirat informieren", "label": "Aufsichtsrat/Beirat informieren"},
    ],
    "s8_erfahrung": [
        {"value": "Noch keine", "label": "Noch keine"},
        {"value": "Experimentiert", "label": "Experimentiert"},
        {"value": "Erste Tools im Einsatz", "label": "Erste Tools im Einsatz"},
        {"value": "Fortgeschritten", "label": "Fortgeschritten"},
    ],
    "s9_ansatz": [
        {"value": "Cloud-SaaS", "label": "Cloud-SaaS"},
        {"value": "On-Premise", "label": "On-Premise"},
        {"value": "Hybrid", "label": "Hybrid"},
        {"value": "Egal", "label": "Noch unklar / Egal"},
    ],
    "s10_datenschutz": [
        {"value": "Hoch", "label": "Hoch"},
        {"value": "Mittel", "label": "Mittel"},
        {"value": "Niedrig", "label": "Niedrig"},
    ],
    "wettbewerber_anzahl": [
        {"value": "wenige", "label": "Wenige (1–3)"},
        {"value": "mehrere", "label": "Mehrere (4–10)"},
        {"value": "viele", "label": "Viele (mehr als 10)"},
        {"value": "unklar", "label": "Schwer einzuschätzen"},
    ],
    "kundenbindung_typ": [
        {"value": "einmalig", "label": "Überwiegend Einmalkunden"},
        {"value": "wiederkehrend", "label": "Wiederkehrende Kunden / Verträge"},
        {"value": "gemischt", "label": "Mischung aus beidem"},
    ],
    "datenreife": [
        {"value": "keine", "label": "Kaum / keine strukturierten Daten"},
        {"value": "basis", "label": "Grundlegende Daten (CRM, Buchhaltung)"},
        {"value": "umfangreich", "label": "Umfangreiche eigene Datenbestände"},
        {"value": "unklar", "label": "Bin mir nicht sicher"},
    ],
}

# Field labels for quick replies
_QR_LABELS: dict[str, str] = {
    # Sektion 0
    "branche": "Branche", "unternehmensgroesse": "Unternehmensgröße",
    "selbststaendig": "Unternehmensform", "country": "Land",
    "bundesland": "Bundesland / Region", "hauptleistung": "Hauptleistung",
    "jahresumsatz": "Jahresumsatz",
    # Sektion 1
    "zielgruppen": "Zielgruppen", "it_infrastruktur": "IT-Infrastruktur",
    "interne_ki_kompetenzen": "Internes KI-Team", "datenquellen": "Verfügbare Daten",
    # Sektion 2
    "digitalisierungsgrad": "Digitalisierungsgrad (1–10)",
    "prozesse_papierlos": "Papierlose Prozesse", "automatisierungsgrad": "Automatisierungsgrad",
    "ki_einsatz": "Aktueller KI-Einsatz", "ki_kompetenz": "KI-Kompetenz",
    # Sektion 3
    "ki_ziele": "KI-Ziele", "anwendungsfaelle": "Anwendungsfälle",
    "ki_projekte": "Bestehende KI-Projekte", "pilot_bereich": "Pilotbereich",
    "zeitersparnis_prioritaet": "Zeitfresser", "geschaeftsmodell_evolution": "Geschäftsmodell-Ideen",
    "vision_3_jahre": "3-Jahres-Vision",
    # Sektion 4
    "strategische_ziele": "Strategische Ziele", "ki_guardrails": "KI-Leitplanken",
    "massnahmen_komplexitaet": "Einführungsaufwand", "roadmap_vorhanden": "KI-Roadmap",
    "governance_richtlinien": "Governance-Richtlinien", "change_management": "Veränderungsbereitschaft",
    # Sektion 5
    "zeitbudget": "Zeitbudget pro Woche", "vorhandene_tools": "Genutzte Systeme",
    "trainings_interessen": "Trainingsthemen", "vision_prioritaet": "Strategischer Hebel",
    "innovationsprozess": "Innovationsprozess", "regulierte_branche": "Regulierte Branche",
    # Sektion 6
    "datenschutzbeauftragter": "Datenschutzbeauftragter", "technische_massnahmen": "Schutzmaßnahmen",
    "folgenabschaetzung": "Datenschutz-Folgenabschätzung", "meldewege": "Meldewege",
    "loeschregeln": "Löschrichtlinien", "ai_act_kenntnis": "EU AI Act Kenntnis",
    "ki_hemmnisse": "KI-Hemmnisse",
    # Sektion 7
    "bisherige_foerdermittel": "Bisherige Fördermittel", "interesse_foerderung": "Förderinteresse",
    "erfahrung_beratung": "Beratungserfahrung", "investitionsbudget": "Investitionsbudget",
    "marktposition": "Marktposition", "benchmark_wettbewerb": "Wettbewerber-Vergleich",
    "risikofreude": "Risikofreude (1–5)",
    # Strategy
    "s1_budget": "KI-Implementierungsbudget", "s2_zeitrahmen": "Umsetzungszeitraum",
    "s3_prioritaeten": "Top-Prioritäten (max. 3)", "s4_engpass": "Größter Engpass",
    "s5_software": "Genutzte Software", "s5_vision": "KI-Vision",
    "s6_foerderinteresse": "Förderinteresse", "s7_entscheidung": "Entscheidungsstruktur",
    "s8_erfahrung": "KI-Erfahrung", "s9_ansatz": "Infrastruktur-Ansatz",
    "s10_datenschutz": "Datenschutz-Priorität",
    "wettbewerber_anzahl": "Wettbewerber", "kundenbindung_typ": "Kundenbeziehungen",
    "datenreife": "Datenreife",
}


def _build_quick_replies(
    next_fields: list[str],
    report_type: str = "r1",
    collected_fields: dict | None = None,
) -> list[QuickReply]:
    """Build quick reply buttons for the next enum fields."""
    registry = get_registry_for_report(report_type)
    collected = collected_fields or {}
    replies = []
    for field_name in next_fields:
        if field_name in collected:
            continue  # Already collected — no buttons

        reg = registry.get(field_name, {})
        # Only build QR for enum/multi fields with known options
        if reg.get("chat_mode") not in ("QR", "qr"):
            continue

        # Dynamic bundesland options based on collected country
        if field_name == "bundesland":
            options_data = _build_bundesland_options(collected.get("country", "DE"))
        else:
            options_data = _QR_OPTIONS.get(field_name)

        if not options_data:
            continue

        options = [
            QuickReplyOption(value=o["value"], label=o["label"], description=o.get("description"))
            for o in options_data
        ]
        label = _QR_LABELS.get(field_name, field_name)
        is_multi = reg.get("type") == "multi"
        max_sel = reg.get("max_select") if is_multi else None
        replies.append(QuickReply(
            field=field_name, label=label, options=options,
            multi_select=is_multi, max_select=max_sel,
        ))

    return replies


def _build_bundesland_options(country: str) -> list[dict]:
    """Build bundesland/region QR options for the given country."""
    codes = BUNDESLAND_VALUES.get(country, BUNDESLAND_VALUES.get("DE", []))
    return [{"value": code, "label": BUNDESLAND_LABELS.get(code, code)} for code in codes]
